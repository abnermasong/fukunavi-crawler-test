from playwright.sync_api import Page, expect

from app.constants import CORPORATION_AGENCY_AREA_CODES, CORPORATION_BASE_URL


def test_corporation_crawler_navigation(page: Page):

    # Search Area Page → Depot Index Page
    page.goto(CORPORATION_BASE_URL)
    page.wait_for_selector("h1:has-text('事業所情報')")
    expect(page.locator("h1:has-text('事業所情報')")).to_be_visible()

    page.select_option("select[name='AREA1']", value=CORPORATION_AGENCY_AREA_CODES[0])

    search_btn = page.locator("input[onclick='doJgySearch();']")
    expect(search_btn).to_be_visible()
    search_btn.click()

    # Depot Index Page → Category Filter → Service Filter → Filtered Depot Index
    page.wait_for_selector("table.ichiranTable")
    expect(page.locator("table.ichiranTable")).to_be_visible()

    page.wait_for_selector("h2.ichiranTitle:has-text('検索した事業所の一覧')")
    expect(
        page.locator("h2.ichiranTitle:has-text('検索した事業所の一覧')")
    ).to_be_visible()

    category_code = "21"  # "21": "高齢者"
    service_value = "001"
    service_name = "指定介護老人福祉施設"

    page.select_option("select[name='SVCDBRCD']", value=category_code)
    service_dropdown = page.locator("select[name='SCHSVCSBRCD1']").first
    service_dropdown.select_option(value=service_value)
    search_btn.click()

    expect(page.locator("select[name='SVCDBRCD']")).to_have_value(category_code)
    expect(service_dropdown).to_have_value(service_value)

    service_type_row = page.locator(
        f"table.ichiranTable tbody > tr:has(td:nth-child(4):has-text('{service_name}'))"
    ).first
    expect(service_type_row).to_be_visible()

    # Depot Index Page → Depot Detail Page
    depot_link = service_type_row.locator(
        "td:first-child > a[href^='javascript:showDetail']"
    )

    depot_link.wait_for(state="visible")
    expect(depot_link).to_be_visible()
    depot_link.click()

    # Depot Detail Page → Corporation Detail Page
    page.wait_for_selector("h4.resultTitle:has-text('１ 基本情報')")
    expect(page.locator("h4.resultTitle:has-text('１ 基本情報')")).to_be_visible()

    corp_link = page.locator("tr:has(th:has-text('経営法人')) a[href*='cmd=sbrhjn_dt']")
    expect(corp_link).to_be_visible()
    corp_link.click()

    # Corporation Detail Page
    page.wait_for_selector("th:has-text('法人名')")
    expect(page.locator("th:has-text('法人名')")).to_be_visible()

    corporation_name = page.locator("tr:has(th:has-text('法人名')) > td")
    corporation_type = page.locator("tr:has(th:has-text('法人種別')) > td")
    address = page.locator("tr:has(th:has-text('所在地')) > td")
    phone_number = page.locator("tr:has(th:has-text('電話番号')) > td")
    update_date = page.locator("div.koushin")

    expect(corporation_name).to_be_visible()
    expect(corporation_type).to_be_visible()
    expect(address).to_be_visible()
    expect(phone_number).to_be_visible()
    expect(update_date).to_be_visible()
