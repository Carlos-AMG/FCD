from playwright.async_api import Page, BrowserContext
from typing import List, Optional, Tuple
import asyncio
from pathlib import Path
import aiohttp
import aiofiles
import zipfile
import shutil
import re
from app.dataclasses.comic import Comic_Issue


class Comic_Issue_Automation:
    """Automation class that abstracts the way we render and download issues. It will take a context browser so that it runs in a new page, it also takes an aiohttp session to download the images.
    Automation process:
        1) Render the whole page (load all images)
        2) From images div (list) extract all CDN image urls
        3) Concurrently (with a semaphore limiting concurrency) download all images using GET requests
        4) Save all images and compress them into a .cbz file
    We can maybe later make this automation something like a strategy so that we can also have automation for downloading from other sites or even other types of contents
    """

    def __init__(
        self,
        context_browser: BrowserContext,
        comic_issue: Comic_Issue,
        directory: Path,
        http_session: aiohttp.ClientSession,
    ):
        self._browser_context = context_browser
        self._comic_issue = comic_issue
        self._directory = directory
        self._images_directory = directory / "images"
        self._http_session = http_session

        self._images_directory.mkdir(exist_ok=True, parents=True)

    # Maybe we can later make this configurable so that users can configure if they want high or low quality
    async def open_issue(self, page: Page) -> None:
        """Open the comic issue page and configure reading settings."""
        print(f"Opening {self._comic_issue.title}...")
        await page.goto(self._comic_issue.url, wait_until="domcontentloaded")

        # Wait for the select elements to be available
        all_pages_select = page.locator("select[id='selectReadType']")
        quality_select = page.locator("select[id='selectQuality']")

        await all_pages_select.wait_for(timeout=10000)
        await quality_select.wait_for(timeout=10000)

        # Select all pages and high quality
        await all_pages_select.select_option("1")  # 1 for all; 0 for single
        await quality_select.select_option(
            "hq"
        )  # hq for high quality; lq for low quality

        # Wait for the page to reload after changing settings
        await asyncio.sleep(2)  # Additional wait for JavaScript to initialize
        print("Page loaded with All Pages and High Quality settings")

    def cleanup(self) -> None:
        """Remove the temporary images directory."""
        if self._images_directory.exists():
            shutil.rmtree(self._images_directory)
            print("  ✓ Cleaned up temporary files")

    async def run(self):
        """
        Main execution method that orchestrates the entire comic download process.
        Returns the path to the created CBZ file, or None if failed.
        """
        page = await self._browser_context.new_page()
        cbz_path = None
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {self._comic_issue.title}")
            print(f"URL: {self._comic_issue.url}")
            print(f"{'='*60}")

            # Step 1: Open issue and select high quality and all pages
            await self.open_issue(page)

            # Step 2: Extract all CDN image URLs IN ORDER

            # Step 3: Download all images (concurrently but track order)

            # Step 4: Create CBZ file with images in correct order

            # Step 5: Cleanup temporary files

            return cbz_path
        except Exception as e:
            print(f"\n❌ Error processing {self._comic_issue.title}: {e}")
            import traceback
            traceback.print_exc()
            # Cleanup on error
            try:
                self.cleanup()
            except:
                pass
            return None

        finally:
            await page.close()

async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as plw:
        browser = await plw.chromium.launch(headless=False)
        # make this configurable
        browser_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = await browser_context.new_page()
        comic_issue = Comic_Issue(
            title="Rick and Morty: Ricklemania Issue #1",
            url="https://readcomiconline.li/Comic/Rick-and-Morty-Ricklemania/Issue-1?id=237074",
        )
        async with aiohttp.ClientSession() as session:
            comic_issue_automation = Comic_Issue_Automation(
                browser_context, comic_issue, Path("./my_comics"), session
            )
            await comic_issue_automation.open_issue(page)


if __name__ == "__main__":
    asyncio.run(main())
