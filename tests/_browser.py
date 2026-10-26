"""Open a Playwright page in Chrome/Chromium.

Uses $CDP_URL if set (attach to a running Chrome), else $CHROME or the first
google-chrome / chromium on PATH, else Playwright's bundled Chromium.
"""
import os, shutil
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright

@asynccontextmanager
async def open_page():
    async with async_playwright() as pw:
        if os.environ.get("CDP_URL"):
            browser = await pw.chromium.connect_over_cdp(os.environ["CDP_URL"])
            page = await browser.contexts[0].new_page()
        else:
            exe = os.environ.get("CHROME") or next(
                (p for p in map(shutil.which, ["google-chrome", "chromium", "chromium-browser"]) if p), None)
            browser = await pw.chromium.launch(executable_path=exe) if exe else await pw.chromium.launch()
            page = await browser.new_page()
        try:
            yield page
        finally:
            await page.close()
            if not os.environ.get("CDP_URL"):
                await browser.close()
