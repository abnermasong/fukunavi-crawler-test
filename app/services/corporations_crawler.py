import asyncio
import random
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

from playwright.async_api import BrowserContext, Page

from app.constants import (
    CORPORATION_AGENCY_AREA_CODE_TO_NAME,
    CORPORATION_AGENCY_AREA_CODES,
    CORPORATION_BASE_URL,
    CORPORATION_CATEGORY_CODES,
    CORPORATION_CATEGORY_SERVICE_FILTER,
)
from app.utils.cancellation import CancellationFlagManager
from app.utils.checkpoint import CheckpointManager
from app.utils.hashing import generate_data_hash
from app.utils.loggers import log
from app.utils.ndjson import append_ndjson, start_ndjson_file
from app.utils.partition import partition
from app.utils.resume import ResumeManager
from app.utils.retry import retry_async
from app.utils.runtime_guard import RuntimeGuardManager


class CorporationCrawler:
    def __init__(
        self,
        worker_id: int,
        worker_count: int,
        runtime_guard: RuntimeGuardManager,
        cancellation_flag: CancellationFlagManager,
    ) -> None:

        self.worker_id = worker_id
        self.worker_count = worker_count

        self.runtime_guard = runtime_guard
        self.cancellation_flag = cancellation_flag

        checkpoint_file_name = f"{worker_id}_corporation_checkpoint"
        self.checkpoint_manager = CheckpointManager(checkpoint_file_name)
        self._output_file: str | None = None

        self.records: list[dict] = []
        self._seen_hjn_codes: set[str] = set()

    async def crawl(
        self,
        browser_context: BrowserContext,
        *,
        output_file: str | None = None,
    ) -> list[dict]:

        self.resume_manager = ResumeManager(self.checkpoint_manager.load_progress())

        static_page = await browser_context.new_page()
        extraction_page = await browser_context.new_page()

        try:
            self._output_file = output_file

            # Start with a clean output file when no checkpoint is being resumed
            # File: {stage_name}_worker_{worker_id}.ndjson
            if self._output_file and not self.resume_manager.is_resuming():
                start_ndjson_file(self._output_file)

            for area_code in self.resume_manager.continue_from_checkpoint(
                "area_code", CORPORATION_AGENCY_AREA_CODES
            ):
                self.runtime_guard.check()
                await self._crawl_area(static_page, extraction_page, area_code)
        finally:
            self._output_file = None
            await extraction_page.close()
            await static_page.close()

        self.checkpoint_manager.clear_progress()

        return self.records

    async def _crawl_area(
        self, static_page: Page, extraction_page: Page, area_code: str
    ) -> None:
        """
        Search Area Page → Select Category Filter → Select Service Filter → Apply Filter → Depot Index Page
        """

        area_name = CORPORATION_AGENCY_AREA_CODE_TO_NAME.get(area_code)

        log(
            f"Area: {area_name} ({area_code})",
            component=__name__,
            worker_id=self.worker_id,
        )

        async def _load_depot_index_page() -> None:
            await static_page.goto(CORPORATION_BASE_URL)
            await static_page.wait_for_selector("h1:has-text('事業所情報')")
            # Select area from dropdown
            await static_page.select_option("select[name='AREA1']", value=area_code)
            await asyncio.sleep(random.uniform(0.3, 0.9))
            # Click search button
            await static_page.locator("input[onclick='doJgySearch();']").click()
            await static_page.wait_for_selector("table.ichiranTable")
            await asyncio.sleep(random.uniform(0.3, 0.9))

        await retry_async(
            _load_depot_index_page,
            runtime_guard=self.runtime_guard,
            worker_id=self.worker_id,
        )

        selected_area_depot_index_url = static_page.url

        for category_code in self.resume_manager.continue_from_checkpoint(
            "category_code", CORPORATION_CATEGORY_CODES
        ):
            self.runtime_guard.check()

            category = CORPORATION_CATEGORY_SERVICE_FILTER[category_code]

            category_name = category.get("name")
            target_services = category.get("services", {})
            service_values = list(target_services.keys())

            # Partition by Service Types
            # Worker 0: Category code: 21 → Service type: 001, 011, 328
            # Worker 1: Category code: 21 → Service type: 002, 013, 017
            # Worker 2: Category code: 21 → Service type: 009, 327
            assigned_service_values = partition(service_values, self.worker_count)[
                self.worker_id
            ]

            log(
                f"Category: {category_name} ({category_code}) - Assigned {len(assigned_service_values)} services: [{', '.join(assigned_service_values)}]",
                component=__name__,
                worker_id=self.worker_id,
            )

            for service_value in self.resume_manager.continue_from_checkpoint(
                "service_value", assigned_service_values
            ):
                self.runtime_guard.check()

                service_index = assigned_service_values.index(service_value) + 1
                total_services = len(assigned_service_values)

                service_name = target_services.get(service_value)

                log(
                    f"Service: {service_name} ({service_value}) - {service_index}/{total_services}",
                    component=__name__,
                    worker_id=self.worker_id,
                )

                async def _apply_service_filter_and_reload_index() -> None:
                    await static_page.goto(selected_area_depot_index_url)

                    await static_page.wait_for_selector(
                        "h2.ichiranTitle:has-text('検索した事業所の一覧')"
                    )

                    # Category filter
                    await static_page.select_option(
                        "select[name='SVCDBRCD']",
                        value=category_code,  # noqa: B023 - retry_async is awaited before the loop advances
                    )
                    await asyncio.sleep(random.uniform(0.3, 0.9))

                    # Service type filter
                    service_select = static_page.locator(
                        "select[name='SCHSVCSBRCD1']"
                    ).first
                    await service_select.select_option(value=service_value)  # noqa: B023 - retry_async is awaited before the loop advances
                    await asyncio.sleep(random.uniform(0.3, 0.9))

                    await static_page.locator("input[onclick='doJgySearch();']").click()
                    await asyncio.sleep(random.uniform(0.3, 0.9))

                    service_type_row = static_page.locator(
                        f"table.ichiranTable tbody > tr:has(td:nth-child(4):has-text('{service_name}'))"  # noqa: B023 - retry_async is awaited before the loop advances
                    ).first

                    no_data = static_page.get_by_text(
                        "該当するデータはありませんでした"
                    ).first

                    await service_type_row.or_(no_data).first.wait_for(state="visible")

                await retry_async(
                    _apply_service_filter_and_reload_index,
                    runtime_guard=self.runtime_guard,
                    worker_id=self.worker_id,
                )

                await self._crawl_depot_index(
                    static_page,
                    extraction_page,
                    area_code=area_code,
                    category_code=category_code,
                    service_value=service_value,
                )

                log(
                    f"Service: {service_name} ({service_value}) - {service_index}/{total_services} - COMPLETED",
                    component=__name__,
                    worker_id=self.worker_id,
                )

            log(
                f"Category: {category_name} ({category_code}) - Assigned {len(assigned_service_values)} services: [{', '.join(assigned_service_values)}] - COMPLETED",
                component=__name__,
                worker_id=self.worker_id,
            )

        log(
            f"Area: {area_name} ({area_code}) - COMPLETED",
            component=__name__,
            worker_id=self.worker_id,
        )

    async def _crawl_depot_index(
        self,
        static_page: Page,
        extraction_page: Page,
        *,
        area_code: str,
        category_code: str,
        service_value: str,
    ) -> None:
        """
        Depot Index Page (with pagination) → Depot Detail Page → Corporation Detail Page
        """

        no_data = static_page.get_by_text("該当するデータはありませんでした").first

        if await no_data.is_visible():
            log(
                "No depots found",
                component=__name__,
                worker_id=self.worker_id,
            )
            return

        page_num = 1

        while True:
            depot_links = static_page.locator(
                "table.ichiranTable tbody > tr > td:first-child > a[href^='javascript:showDetail']"
            )

            await static_page.wait_for_selector(
                "h2.ichiranTitle:has-text('検索した事業所の一覧')"
            )

            await depot_links.first.wait_for(state="visible")

            # Pagination-level resume
            if self.resume_manager.is_resuming():
                checkpoint_page_num = self.resume_manager.get_saved_value("page_num")

                if checkpoint_page_num is not None and page_num <= checkpoint_page_num:
                    # Iterate through pagination until reaching the checkpoint_page_num
                    while page_num < checkpoint_page_num:
                        self.runtime_guard.check()

                        # <a href="javascript:showNextPage(160);">5</a>
                        # name = str(checkpoint_page_num) = "5"
                        checkpoint_page_link = (
                            static_page.locator(".ichiranPage")
                            .get_by_role(
                                "link",
                                name=str(checkpoint_page_num),
                                exact=True,
                            )
                            .first
                        )

                        # checkpoint_page_num is visible
                        # pagination is grouped by 10 pages
                        if await checkpoint_page_link.count() > 0:
                            log(
                                f"Resuming page {checkpoint_page_num}",
                                component=__name__,
                                worker_id=self.worker_id,
                            )

                            await checkpoint_page_link.click()
                            await asyncio.sleep(random.uniform(0.3, 0.9))
                            await static_page.wait_for_selector(
                                f"font.blues:has-text('{checkpoint_page_num}')"
                            )

                            page_num = checkpoint_page_num
                            break

                        # checkpoint_page_num is not yet visible
                        # go to the next pagination group of 10 pages
                        # <a href="javascript:showNextPage(400);">進む>>></a>
                        next_10_link = (
                            static_page.locator(".ichiranPage")
                            .get_by_role(
                                "link",
                                name="進む>>>",
                                exact=True,
                            )
                            .first
                        )

                        expected_page_num = page_num + 10

                        log(
                            f"Page {checkpoint_page_num} is not yet visible, advancing pagination by 10 pages from page {page_num}",
                            component=__name__,
                            worker_id=self.worker_id,
                        )

                        await next_10_link.click()
                        await asyncio.sleep(random.uniform(0.3, 0.9))
                        await static_page.wait_for_selector(
                            f"font.blues:has-text('{expected_page_num}')"
                        )

                        page_num = expected_page_num

                    # Clear checkpoint_page_num after reaching the correct page
                    self.resume_manager.clear_key("page_num")
                    continue

            total_depots = await depot_links.count()

            log(
                f"Page {page_num}: {total_depots} depots found",
                component=__name__,
                worker_id=self.worker_id,
            )

            for row_index in self.resume_manager.continue_from_checkpoint(
                "row_index", range(total_depots)
            ):
                self.runtime_guard.check()
                self.cancellation_flag.check()

                depot_link = depot_links.nth(row_index)

                log(
                    f"Extracting corporation data - {row_index + 1}/{total_depots}",
                    component=__name__,
                    worker_id=self.worker_id,
                )

                # javascript:showDetail('1310100110', '001')
                depot_detail_href = await depot_link.get_attribute("href")

                if depot_detail_href and depot_detail_href.startswith("javascript:"):
                    static_page_url = static_page.url
                    # javascript:showDetail('1310100110', '001') → showDetail('1310100110', '001')
                    depot_detail_script = depot_detail_href.removeprefix("javascript:")

                    async def _load_depot_detail_page() -> None:
                        await asyncio.sleep(random.uniform(0.3, 0.9))
                        await extraction_page.goto(static_page_url)  # noqa: B023 - retry_async is awaited before the loop advances
                        # Execute JS: showDetail('1310100110', '001')
                        await extraction_page.evaluate(
                            f"() => {{ {depot_detail_script} }}"  # noqa: B023 - retry_async is awaited before the loop advances
                        )
                        await extraction_page.wait_for_selector(
                            "h4.resultTitle:has-text('１ 基本情報')"
                        )
                        await asyncio.sleep(random.uniform(0.3, 0.9))

                    await retry_async(
                        _load_depot_detail_page,
                        runtime_guard=self.runtime_guard,
                        worker_id=self.worker_id,
                    )

                await self._crawl_corporation_detail(extraction_page)

                self.checkpoint_manager.save_progress(
                    {
                        "area_code": area_code,
                        "category_code": category_code,
                        "service_value": service_value,
                        "page_num": page_num,
                        "row_index": row_index,
                    }
                )

            # <a href="javascript:showNextPage(40, true);">次ページに進む >></a>
            next_btn_link = static_page.get_by_role(
                "link", name="次ページに進む >>", exact=True
            ).first

            if await next_btn_link.count() == 0:
                log(
                    f"No more pages, completed {page_num} pages",
                    component=__name__,
                    worker_id=self.worker_id,
                )
                break

            self.runtime_guard.check()

            expected_page_num = page_num + 1

            await next_btn_link.click()
            await static_page.wait_for_selector(
                f"font.blues:has-text('{expected_page_num}')"
            )

            page_num = expected_page_num

    async def _crawl_corporation_detail(self, page: Page) -> None:
        """
        Corporation Detail Page → Data Extraction
        """

        corp_link = page.locator(
            "tr:has(th:has-text('経営法人')) a[href*='cmd=sbrhjn_dt']"
        )

        if await corp_link.count() == 0:
            log(
                "Corporation link does not exist, skipping",
                component=__name__,
                worker_id=self.worker_id,
            )
            return

        corp_href = await corp_link.first.get_attribute("href") or ""
        hjn_cd = self._extract_hjn_cd(corp_href)
        if hjn_cd and hjn_cd in self._seen_hjn_codes:
            log(
                f"Corporation data with hjn code of {hjn_cd} is already recorded, skipping",
                component=__name__,
                worker_id=self.worker_id,
            )
            return

        await corp_link.first.click()

        await page.wait_for_selector("th:has-text('法人名')")
        await asyncio.sleep(random.uniform(0.3, 0.9))

        record = await self._extract_corporation_data(page)
        self.records.append(record)

        if self._output_file is not None:
            append_ndjson(record, self._output_file)

        if hjn_cd:
            self._seen_hjn_codes.add(hjn_cd)

    async def _extract_corporation_data(self, page: Page) -> dict:

        corporation_name = await self._extract_table_row_value(page, "法人名")

        corporation_type = await self._extract_table_row_value(page, "法人種別")

        address = await self._extract_table_row_value(page, "所在地")

        phone_number = await self._extract_table_row_value(page, "電話番号")

        update_date = await self._extract_update_date(page)

        record = {
            "corporation_name": corporation_name,
            "corporation_type": corporation_type,
            "address": address,
            "phone_number": phone_number,
            "update_date": update_date,
            "source_url": page.url,
            "created_at": datetime.now(UTC).isoformat(),
        }

        record["data_hash"] = generate_data_hash(record)
        return record

    async def _extract_text_from_selector(self, page: Page, selector: str) -> str:

        loc = page.locator(selector).first
        text = await loc.inner_text()
        return self._normalize_spaces(text)

    async def _extract_table_row_value(self, page: Page, header: str) -> str:

        selector = f"tr:has(th:has-text('{header}')) > td"
        return await self._extract_text_from_selector(page, selector)

    async def _extract_update_date(self, page: Page) -> str:
        """
        Remove 更新日 prefix.

        Example:

        更新日 2025年7月18日
        - → 2025年7月18日
        """

        loc = page.locator("div.koushin")

        text = await loc.inner_text()
        return text.replace("更新日", "").strip()

    def _normalize_spaces(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _extract_hjn_cd(self, href: str) -> str:
        """
        Extract HJN_CD from corporation href.

        Example:

        controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=206201016&SVCSBR_CD=001
        - → 206201016
        """

        parsed_url = urlparse(href)
        query_params = parse_qs(parsed_url.query)

        return query_params.get("HJN_CD", [""])[0]
