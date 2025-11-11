# authentication/base_browser.py
import json
import asyncio
import random
from typing import Optional, Tuple
from patchright.async_api import async_playwright, Browser, BrowserContext, Page, ElementHandle
from logs.logs import logger


class BaseBrowser:
    """
        Handles authentication to a website using Playwright.

        Provides an active Browser, BrowserContext, and Page for further automation tasks.

        Attributes:
            base_url (str): URL of the website for login.
            email (str): User email for login.
            password (str): User password for login.
            cookies_file (str): Path to save/load cookies.
            headless (bool): Whether to run browser in headless mode.
            browser (Optional[Browser]): Playwright Browser instance.
            context (Optional[BrowserContext]): BrowserContext instance for session handling.
            page (Optional[Page]): Page instance for automation tasks.
        """

    def __init__(self, base_url: str, email: str, password: str, cookies_file: str, headless: bool = True) -> None:
        self.email: str = email
        self.password: str = password
        self.headless: bool = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies_file = cookies_file
        self.base_url = base_url

    async def save_cookies(self) -> None:
        """
        Saves cookies from the current browser context to a JSON file.

        If the browser context is not initialized, logs a warning.
        """
        try:
            if self.context:
                cookies = await self.context.cookies()
                with open(self.cookies_file, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                logger.info("✅ Cookies saved to {}", self.cookies_file)
            else:
                logger.warning("⚠️ Cannot save cookies: browser context is None")
        except Exception as e:
            logger.exception("❌ Error saving cookies: {}", e)

    @staticmethod
    async def human_type(element: ElementHandle, text: str, min_delay: float = 0.03, max_delay: float = 0.12) -> None:
        """
        Types text into an input element simulating human behavior.

        Args:
            element (ElementHandle): Playwright element to type into.
            text (str): Text to type.
            min_delay (float): Minimum delay between keystrokes in seconds.
            max_delay (float): Maximum delay between keystrokes in seconds.
        """
        try:
            await element.fill("")  # Clear input
        except Exception:
            # Fallback: click + backspace
            try:
                await element.click(click_count=3)
                await element.press("Backspace")
            except Exception as e:
                logger.warning("⚠️ Unable to clear element: {}", e)

        # Type text character by character
        for ch in text:
            try:
                await element.type(ch)
                await asyncio.sleep(random.uniform(min_delay, max_delay))
            except Exception as e:
                logger.warning("⚠️ Failed typing character '{}': {}", ch, e)

    async def verify_human(self) -> Tuple[Optional[Browser], Optional[BrowserContext], Optional[Page]]:
        """
        Opens the page and attempts to pass bot-screening (Cloudflare challenge).

        Performs the following:
        - Launches Playwright browser and context
        - Navigates to the base URL
        - Detects Cloudflare challenge frames
        - Clicks on challenge checkbox to verify human
        - Returns active browser, context, and page for further automation

        Returns:
            Tuple containing Browser, BrowserContext, and Page objects. If initialization fails, returns (None, None, None).
        """
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                channel='chrome',
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(self.base_url)

            bounding_box = None
            await asyncio.sleep(10)
            for _ in range(25):
                await asyncio.sleep(1)

                for frame in self.page.frames:
                    if frame.url.startswith('https://challenges.cloudflare.com'):
                        frame_element = await frame.frame_element()
                        bounding_box = await frame_element.bounding_box()
                        if bounding_box:
                            break
                    if bounding_box:
                        break
                coord_x = bounding_box['x']
                coord_y = bounding_box['y']

                width = bounding_box['width']
                height = bounding_box['height']

                checkbox_x = coord_x + width / 9
                checkbox_y = coord_y + height / 2

                await self.page.mouse.click(x=checkbox_x, y=checkbox_y)

            logger.info("🌐 Navigated to {}", self.base_url)
        except Exception as e:
            logger.exception("❌ Failed to launch browser or open page: {}", e)
            return None, None, None


        return self.browser, self.context, self.page
