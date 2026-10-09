from playwright.sync_api import Page, expect

from app.constants import (
    DEPOT_EVALUATION_BASE_URL,
    DEPOT_EVALUATION_CATEGORY_CODES,
    DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER,
)


def test_depot_crawler_navigation(page: Page):

    # Category Selection Page → Service Selection Page
    page.goto(DEPOT_EVALUATION_BASE_URL)
    page.wait_for_selector("font.chas:has-text('サービスの分類を選択してください。')")
    expect(
        page.locator("font.chas:has-text('サービスの分類を選択してください。')")
    ).to_be_visible()

    category = DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER[
        DEPOT_EVALUATION_CATEGORY_CODES[0]
    ]
    category_name = category.get("name")
    page.get_by_role("link", name=category_name, exact=True).first.click()

    # Service Selection Page → Search Area Page
    page.wait_for_selector(
        "font.chas:has-text('サービスを選択して、検索ボタンを押してください。（複数選択可能）')"
    )
    expect(
        page.locator(
            "font.chas:has-text('サービスを選択して、検索ボタンを押してください。（複数選択可能）')"
        )
    ).to_be_visible()

    service_checkbox = page.locator(
        "input[name='STEP_SVCSBRCD'][value='001']"
    )  # "001": "指定介護老人福祉施設【特別養護老人ホーム】"
    expect(service_checkbox).to_be_visible()
    service_checkbox.check()

    page.wait_for_selector(
        "input[onclick='doSearch();']"
    )  # Substitute for asyncio.sleep
    search_btn = page.locator("input[onclick='doSearch();']")
    expect(search_btn).to_be_visible()
    search_btn.click()

    # Search Area Page → Evaluation Index Page
    page.wait_for_selector("font.text:has-text('【地域を選択してください】')")
    expect(
        page.locator("font.text:has-text('【地域を選択してください】')")
    ).to_be_visible()

    target = page.locator("input[name='MLT_AREA'][value='3']")  # "3": "東京都全域"
    expect(target).to_be_visible()
    target.check()
    search_btn.click()

    # Evaluation Index Page → Evaluation Detail Page
    page.wait_for_selector("font.cha2:has-text('◆評価結果一覧◆')")
    expect(page.locator("font.cha2:has-text('◆評価結果一覧◆')")).to_be_visible()

    first_eval_result_link = page.locator(
        "table:has(th.pink2) tr:has(td) td:nth-child(2) a"
    ).first
    first_eval_result_link.wait_for(state="visible")
    expect(first_eval_result_link).to_be_visible()

    eval_result_rows = page.locator("table:has(th.pink2) tr:has(td)")
    row = eval_result_rows.first
    eval_result_link = row.locator("td").nth(1).locator("a")
    eval_result_link.click()

    # Evaluation Detail Page → Depot Detail Page
    page.wait_for_selector("h1.main-title:has-text('評価結果')")
    expect(page.locator("h1.main-title:has-text('評価結果')")).to_be_visible()

    depot_link = page.locator("a[href*='showJgy(']")
    depot_link.first.click()

    # Depot Detail Page
    page.wait_for_selector("h4.resultTitle:has-text('１ 基本情報')")
    expect(page.locator("h4.resultTitle:has-text('１ 基本情報')")).to_be_visible()

    depot_name = page.locator("tr:has(th:has-text('事業所名')) > td")
    phone_number = page.locator("tr:has(th:has-text('事業所電話')) > td")
    fax_number = page.locator("tr:has(th:has-text('事業所FAX')) > td")
    service_type = page.locator("tr:has(th:has-text('サービス種別')) > td").first
    opened_date_raw = page.locator("tr:has(th:has-text('設立')) > td")
    capacity = page.locator("tr:has(th:has-text('定員')) > td").first
    corporation_name = page.locator("tr:has(th:has-text('経営法人')) > td")
    update_date = page.locator("div.koushin")
    depot_code = page.locator("table.resultTable3 td:text-is('事業所番号') + td").first
    address_and_city = page.locator("tr:has(th:has-text('所在地')) > td")
    staff_count = page.locator("tr:has(th:has-text('職員数')) > td").first

    hp = page.locator("tr:has(th:has-text('ホームページ')) > td a")

    expect(depot_name).to_be_visible()
    expect(phone_number).to_be_visible()
    expect(fax_number).to_be_visible()
    expect(service_type).to_be_visible()
    expect(opened_date_raw).to_be_visible()
    expect(corporation_name).to_be_visible()
    expect(update_date).to_be_visible()
    expect(address_and_city).to_be_visible()
    if depot_code.count() > 0:
        expect(depot_code).to_be_visible()
    if capacity.count() > 0:
        expect(capacity).to_be_visible()
    if staff_count.count() > 0:
        expect(staff_count).to_be_visible()
    if hp.count() > 0:
        expect(hp).to_be_visible()
