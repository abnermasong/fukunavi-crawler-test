from playwright.sync_api import Page, expect

from app.constants import CORPORATION_BASE_URL, DEPOT_EVALUATION_BASE_URL


def test_depot_index_page_pagination(page: Page):

    # Search Area Page → Depot Index Page
    page.goto(CORPORATION_BASE_URL)

    page.select_option("select[name='AREA1']", value="0")  # "0": "東京都２３区内"

    search_btn = page.locator("input[onclick='doJgySearch();']")
    expect(search_btn).to_be_visible()
    search_btn.click()

    # Depot Index Page
    expect(page.locator("table.ichiranTable")).to_be_visible()

    next_btn = page.get_by_role("link", name="次ページに進む >>", exact=True).first
    next_btn.click()

    # Verify next page button updates page number to 2
    expect(page.locator("font.blues:has-text('2')").first).to_be_visible()

    continue_btn = page.get_by_role("link", name="進む>>>", exact=True).first
    continue_btn.click()

    # Verify continue button updates page number to 12
    expect(page.locator("font.blues:has-text('12')").first).to_be_visible()


def test_evaluation_index_page_pagination(page: Page):

    # Category Selection Page → Service Selection Page
    page.goto(DEPOT_EVALUATION_BASE_URL)

    page.get_by_role("link", name="高齢者", exact=True).first.click()  # "21": "高齢者"

    # Service Selection Page → Search Area Page
    select_service_breadcrumb = page.locator("text=サービスを選択").first
    expect(select_service_breadcrumb).to_be_visible()

    service_checkbox = page.locator(
        "input[name='STEP_SVCSBRCD'][value='001']"
    )  # "001": "指定介護老人福祉施設【特別養護老人ホーム】"
    expect(service_checkbox).to_be_visible()
    service_checkbox.check()

    search_btn = page.locator("input[onclick='doSearch();']")
    expect(search_btn).to_be_visible()
    search_btn.click()

    # Search Area Page → Evaluation Index Page
    expect(
        page.locator("font.text:has-text('【地域を選択してください】')")
    ).to_be_visible()

    area_checkbox = page.locator(
        "input[name='MLT_AREA'][value='3']"
    )  # "3": "東京都全域"
    expect(area_checkbox).to_be_visible()
    area_checkbox.check()
    search_btn.click()

    # Evaluation Index Page
    expect(page.locator("font.cha2:has-text('◆評価結果一覧◆')")).to_be_visible()

    next_btn = page.get_by_role("link", name="次ページに進む >>", exact=True).first
    next_btn.click()

    # Verify next page button updates page number to 2
    expect(page.locator("td[colspan='3']:has-text('2／')")).to_be_visible()

    continue_btn = page.get_by_role("link", name="進む >>", exact=True).first
    continue_btn.click()

    # Verify continue button updates page number to 12
    expect(page.locator("td[colspan='3']:has-text('12／')")).to_be_visible()
