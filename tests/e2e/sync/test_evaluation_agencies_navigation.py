from playwright.sync_api import Page, expect

from app.constants import (
    ADDRESS_COL,
    CERT_NUMBER_COL,
    CORPORATION_AGENCY_AREA_CODES,
    EVALUATION_AGENCY_BASE_URL,
    IS_ACCEPTING_COL,
    IS_SOCIAL_CARE_COL,
    PHONE_NUMBER_COL,
    TARGET_CATEGORIES_COL,
)


def test_evaluation_agency_crawler_navigation(page: Page):

    # Search Area Page → Evaluation Agency Index Page
    page.goto(EVALUATION_AGENCY_BASE_URL)

    page.select_option("select[name='AREA1']", value=CORPORATION_AGENCY_AREA_CODES[0])

    search_btn = page.locator("input[onclick='doSearch(1);']")
    expect(search_btn).to_be_visible()
    search_btn.click()

    page.wait_for_selector("font.cha2:has-text('◆評価機関一覧◆')")
    expect(page.locator("font.cha2:has-text('◆評価機関一覧◆')")).to_be_visible()

    table_selector = "table:has(th.pink2:has-text('認証番号'))"
    page.wait_for_selector(table_selector)
    table = page.locator(table_selector)
    eval_agency_row = table.locator("tbody > tr:has(td)").first

    certification_number = eval_agency_row.locator("td").nth(CERT_NUMBER_COL)
    address = eval_agency_row.locator("td").nth(ADDRESS_COL)
    phone_number = eval_agency_row.locator("td").nth(PHONE_NUMBER_COL)
    target_categories = eval_agency_row.locator("td").nth(TARGET_CATEGORIES_COL)
    is_active = eval_agency_row
    is_social_care = eval_agency_row.locator("td").nth(IS_SOCIAL_CARE_COL)
    is_accepting = eval_agency_row.locator("td").nth(IS_ACCEPTING_COL)

    expect(certification_number).to_be_visible()
    expect(address).to_be_visible()
    expect(phone_number).to_be_visible()
    expect(target_categories).to_be_visible()
    expect(is_active).to_be_visible()
    expect(is_social_care).to_be_visible()
    expect(is_accepting).to_be_visible()

    # Evaluation Agency Index Page → Evaluation Agency Detail Page
    evaluation_agency_link = eval_agency_row.locator("td").nth(1).locator("a")
    evaluation_agency_link.click()

    # Evaluation Agency Detail Page
    page.wait_for_selector("font.green1:has-text('◆評価機関情報◆')")
    expect(page.locator("font.green1:has-text('◆評価機関情報◆')")).to_be_visible()

    agency_name_and_agency_type = (
        page.locator("tr")
        .filter(has=page.locator("td:first-child:has-text('評価機関名')"))
        .locator(":scope > td:nth-child(2)")
        .first
    )

    expect(agency_name_and_agency_type).to_be_visible()

    hp = (
        page.locator("tr")
        .filter(
            has=page.locator("td:first-child table td:has-text('（ホームページ）')")
        )
        .locator(":scope > td:nth-child(2) a")
        .first
    )

    if hp.count() > 0:
        expect(hp).to_be_visible()
