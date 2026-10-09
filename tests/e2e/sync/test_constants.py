from playwright.sync_api import Page, expect

from app.constants import (
    CORPORATION_AGENCY_AREA_CODE_TO_NAME,
    CORPORATION_AGENCY_AREA_CODES,
    CORPORATION_BASE_URL,
    CORPORATION_CATEGORY_CODES,
    CORPORATION_CATEGORY_SERVICE_FILTER,
    DEPOT_EVALUATION_BASE_URL,
    DEPOT_EVALUATION_CATEGORY_CODES,
    DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER,
    EVALUATION_AGENCY_BASE_URL,
)


def test_corporation_search_area_page_dropdowns(page: Page):

    page.goto(CORPORATION_BASE_URL)

    dropdown = page.locator("select[name='AREA1']")
    expect(dropdown).to_be_visible()

    # Verify all area codes exist as dropdown options with correct area names
    for area_code in CORPORATION_AGENCY_AREA_CODES:
        area_name = CORPORATION_AGENCY_AREA_CODE_TO_NAME.get(area_code, "")

        dropdown.select_option(value=area_code)

        selected_option = dropdown.locator(f"option[value='{area_code}']")
        expect(selected_option).to_have_text(area_name)


def test_corporation_category_and_target_service_dropdowns(page: Page):

    # Verify all category codes exist as dropdown options with correct category names
    for category_code in CORPORATION_CATEGORY_CODES:
        page.goto(CORPORATION_BASE_URL)
        page.select_option(
            "select[name='AREA1']", value=CORPORATION_AGENCY_AREA_CODES[0]
        )
        page.locator("input[onclick='doJgySearch();']").click()
        expect(
            page.locator("h2.ichiranTitle:has-text('検索した事業所の一覧')")
        ).to_be_visible()

        category = CORPORATION_CATEGORY_SERVICE_FILTER[category_code]
        category_dropdown = page.locator("select[name='SVCDBRCD']")
        expect(category_dropdown).to_be_visible()
        expect(
            category_dropdown.locator(f"option[value='{category_code}']")
        ).to_have_text(category["name"])
        category_dropdown.select_option(value=category_code)
        expect(category_dropdown).to_have_value(category_code)

        service_dropdown = page.locator("select[name='SCHSVCSBRCD1']").first
        expect(service_dropdown).to_be_visible()

        # Verify all target services for this category code exist as dropdown options with correct service names
        for service_value, service_name in category["services"].items():
            service_dropdown.select_option(value=service_value)
            expect(service_dropdown).to_have_value(service_value)
            expect(
                service_dropdown.locator(f"option[value='{service_value}']")
            ).to_have_text(service_name)


def test_evaluation_agency_search_page_area_dropdowns(page: Page):

    page.goto(EVALUATION_AGENCY_BASE_URL)

    dropdown = page.locator("select[name='AREA1']")
    expect(dropdown).to_be_visible()

    # Verify all area codes exist as dropdown options with correct area names
    for area_code in CORPORATION_AGENCY_AREA_CODES:
        area_name = CORPORATION_AGENCY_AREA_CODE_TO_NAME.get(area_code, "")

        dropdown.select_option(value=area_code)

        selected_option = dropdown.locator(f"option[value='{area_code}']")
        expect(selected_option).to_have_text(area_name)


def test_depot_evaluation_category_and_target_service_selection_pages(page: Page):

    for category_code in DEPOT_EVALUATION_CATEGORY_CODES:
        page.goto(DEPOT_EVALUATION_BASE_URL)

        expect(page.locator("text=サービスの分類を選択してください。")).to_be_visible()

        category = DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER[category_code]

        category_name = category.get("name")

        category_btn = page.locator(
            f"a[href=\"javascript:doSearch('{category_code}');\"]"
        )

        # Verify category code exist with correct category names
        expect(category_btn).to_be_visible()
        expect(category_btn).to_have_text(category_name)

        page.get_by_role("link", name=category_name, exact=True).first.click()

        select_service_breadcrumb = page.locator("text=サービスを選択").first
        expect(select_service_breadcrumb).to_be_visible()

        target_services = category.get("services", {})

        # Verify all target services for this category code exist with correct service names
        for service_value, service_name in target_services.items():
            service_checkbox = page.locator(
                f"input[name='STEP_SVCSBRCD'][value='{service_value}']"
            ).first

            expect(service_checkbox).to_be_attached()

            service_checkbox.check()

            service_label = page.locator(
                f"td:has(input[name='STEP_SVCSBRCD'][value='{service_value}'])"
            ).first

            expect(service_label).to_contain_text(service_name)
