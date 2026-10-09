import pytest
from playwright.sync_api import Page, expect

CRAWLER_TIMEOUT_MS = 60000  # Same with production configuration


def pytest_configure(config: pytest.Config) -> None:
    """Set default timeout for Playwright expect assertions."""

    expect.set_options(timeout=CRAWLER_TIMEOUT_MS)


@pytest.fixture(autouse=True)
def set_default_timeout(page: Page):
    """Set default timeout for Playwright page actions."""

    page.set_default_timeout(CRAWLER_TIMEOUT_MS)
