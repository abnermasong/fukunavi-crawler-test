from playwright.sync_api import Page, expect

from app.constants import (
    DEPOT_EVALUATION_BASE_URL,
    DEPOT_EVALUATION_CATEGORY_CODES,
    DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER,
)


def test_evaluations_crawler_navigation(page: Page):

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

    # Evaluation Detail Page
    page.wait_for_selector("#evaluation-year-select")
    year_select = page.locator("#evaluation-year-select")
    expect(year_select).to_be_visible()

    option_count = year_select.locator("option").count()

    for i in range(option_count):
        year_value = year_select.locator("option").nth(i).get_attribute("value")
        year_select.select_option(value=year_value)
        expect(year_select).to_have_value(str(year_value))

    depot_name = page.locator(
        "section#info .info-card:has(p:has-text('【事業所名称】')) p.data > a"
    ).first
    evaluation_agency_name = page.locator(
        "section#evaluator-info .info-card:has(p:has-text('【評価機関名】')) p.data"
    )
    evaluation_date = page.locator(
        "section#evaluator-info .info-card:has(p:has-text('【評価実施期間】')) p.data"
    )
    evaluation_year_value = year_select

    expect(depot_name).to_be_visible()
    expect(evaluation_agency_name).to_be_visible()
    expect(evaluation_date).to_be_visible()
    expect(evaluation_year_value).to_be_visible()
