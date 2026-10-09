from playwright.async_api import async_playwright

from app.config import CRAWLER_TIMEOUT_MS


class BrowserManager:
    """
    An asynchronous context manager to handle the lifecycle of a Playwright browser instance.
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """
        Starts Playwright, launches the browser, and returns the browser context for page creation.
        """

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 800},
        )

        self.context.set_default_timeout(CRAWLER_TIMEOUT_MS)

        return self.context

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Cleans up Playwright resources in reverse order of creation.
        """

        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
