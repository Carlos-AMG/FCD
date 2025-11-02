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
    
    def __init__(self, context_browser: BrowserContext, comic_issue: Comic_Issue, directory: Path, http_session: aiohttp.ClientSession):
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
        await quality_select.select_option("hq")   # hq for high quality; lq for low quality

        # Wait for the page to reload after changing settings
        await asyncio.sleep(2)  # Additional wait for JavaScript to initialize
        print("Page loaded with All Pages and High Quality settings")
    