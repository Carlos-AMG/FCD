from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import asyncio
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List
import aiohttp
from pathlib import Path
import re


from playwright.async_api import async_playwright, Page, BrowserContext
import asyncio
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Optional
from pathlib import Path
import re
import aiohttp

# Import your classes
from app.automations.comic_issue import Comic_Issue_Automation
from app.dataclasses.comic import *


class Comic_Downloader:
    def __init__(self, url: str, downloads_directory: Path, max_concurrent_issues: int = 3):
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
        sanitized_series_name = re.sub(r'[<>:"/\\|?*]', '', series_name)
        slug = sanitized_series_name.replace(" ", "-")
        return self._base_url + "/Comic/" + slug
    
    async def get_issues_from_series(self, page: Page, series_url: str) -> List[Comic_Issue]:
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

async def main():
    downloader = Comic_Downloader("https://readcomiconline.li", Path("./my_comics"))
    series_name = "Rick and Morty Ricklemania"
    print(downloader._convert_to_url(series_name))
    async with async_playwright() as plw:
        browser = await plw.chromium.launch(headless=False)
        # make this configurable
        browser_context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await browser.new_page()
        issues = await downloader.get_issues_from_series(page, downloader._convert_to_url(series_name))
        print(issues)

if __name__ == "__main__":
    asyncio.run(main())