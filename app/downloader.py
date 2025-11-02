from playwright.async_api import async_playwright, Page, BrowserContext
import asyncio
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Optional
from pathlib import Path
import re
import aiohttp

from app.automations.comic_issue_automation import Comic_Issue_Automation
from app.dataclasses.comic import Comic_Issue


class Comic_Downloader:
    def __init__(
        self, url: str, downloads_directory: Path, max_concurrent_issues: int = 3
    ):
        """
        Args:
            downloads_directory: Base directory for all downloads
            max_concurrent_issues: Maximum number of issues to process simultaneously
        """
        self._base_url = url
        self._downloads_directory = downloads_directory
        self._max_concurrent_issues = max_concurrent_issues

        # Create downloads directory if it doesn't exist
        self._downloads_directory.mkdir(parents=True, exist_ok=True)

    def _convert_to_url(self, series_name: str) -> str:
        """Sanitize and build series name url"""
        sanitized_series_name = re.sub(r'[<>:"/\\|?*]', "", series_name)
        slug = sanitized_series_name.replace(" ", "-")
        return self._base_url + "/Comic/" + slug
    
    def _sanitize_title(self, title: str) -> str:
        """Sanitize title for use as a directory name."""
        # Remove invalid characters
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        # Remove leading/trailing spaces and dots
        title = title.strip(". ")
        # Limit length
        if len(title) > 100:
            title = title[:100]
        return title

    async def get_issues_from_series(
        self, page: Page, series_url: str
    ) -> List[Comic_Issue]:
        """
        Scrape all issue links from a series page.

        Args:
            page: Playwright page object
            series_url: URL of the series page

        Returns:
            List of Comic_Issue objects
        """
        print(f"Loading series page: {series_url}")
        await page.goto(series_url, wait_until="domcontentloaded")

        # Wait a bit for dynamic content
        await page.wait_for_selector("table.listing", timeout=10000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        table = soup.select_one("table.listing")

        if not table:
            print("❌ Couldn't find a listing table")
            return []

        issues = []
        for row in table.select("tr td a[href]"):
            href = row["href"].strip()
            title = row.get_text(strip=True)
            issue_url = urljoin(self._base_url, href)
            issues.append(Comic_Issue(title=title, url=issue_url))

        print(f"✓ Found {len(issues)} issues")
        return issues

    async def process_issue(
        self, 
        comic_issue: Comic_Issue,
        browser_context: BrowserContext,
        http_session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        series_dir: Path
    ) -> Optional[Path]:
        """
        Process a single issue with semaphore control.
        
        Args:
            comic_issue: The comic issue to process
            browser_context: Browser context for creating pages
            http_session: aiohttp session for downloading images
            semaphore: Semaphore to limit concurrent processing
            series_dir: Directory for the series
            
        Returns:
            Path to created CBZ file or None if failed
        """
        async with semaphore:
            # Create issue-specific directory
            issue_dir = series_dir / self._sanitize_title(comic_issue.title)
            issue_dir.mkdir(parents=True, exist_ok=True)
            
            automation = Comic_Issue_Automation(
                browser_context, 
                comic_issue, 
                issue_dir, 
                http_session
            )
            
            try:
                cbz_path = await automation.run()
                return cbz_path
            except Exception as e:
                print(f"❌ Failed to process {comic_issue.title}: {e}")
                return None
            
    async def download(self, series_name: str, limit: Optional[int] = None):
        """
        Download all issues from a series.
        
        Args:
            series_name: Name of the comic series
            limit: Optional limit on number of issues to download (for testing)
        """
        series_url = self._convert_to_url(series_name)

        # Create series directory
        series_dir = self._downloads_directory / self._sanitize_title(series_name)
        series_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Starting download for: {series_name}")
        print(f"Output directory: {series_dir}")
        print(f"{'='*60}\n")

        async with async_playwright() as plw:
            # Launch browser
            browser = await plw.chromium.launch(headless=False)
            browser_context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # Get list of issues
            page = await browser_context.new_page()
            comic_issues = await self.get_issues_from_series(page, series_url)
            await page.close()

            if not comic_issues:
                print("No issues found!")
                await browser.close()
                return
            
            # Apply limit if specified (for testing)
            if limit:
                comic_issues = comic_issues[:limit]
                print(f"Limiting to first {limit} issue(s) for testing\n")

            # Create semaphore to limit concurrent downloads
            semaphore = asyncio.Semaphore(self._max_concurrent_issues)

            # Process all issues with shared aiohttp session
            async with aiohttp.ClientSession() as http_session:
                # Create tasks for all issues
                tasks = [
                    self.process_issue(
                        comic_issue,
                        browser_context,
                        http_session,
                        semaphore,
                        series_dir
                    )
                    for comic_issue in comic_issues
                ]

                # Wait for all tasks to complete
                print(f"Processing {len(tasks)} issue(s) with max {self._max_concurrent_issues} concurrent downloads...\n")
                cbz_paths = await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    downloader = Comic_Downloader("https://readcomiconline.li", Path("./my_comics"))
    series_name = "Rick and Morty Ricklemania"
    await downloader.download(series_name)


if __name__ == "__main__":
    asyncio.run(main())
