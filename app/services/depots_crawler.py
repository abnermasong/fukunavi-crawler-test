import asyncio
import random
import re
from datetime import UTC, datetime

from playwright.async_api import BrowserContext, Page

from app.constants import (
    BROAD_AREA_CODES_TO_SKIP,
    DEPOT_EVALUATION_BASE_URL,
    DEPOT_EVALUATION_CATEGORY_CODES,
    DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER,
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


class DepotCrawler:
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

        checkpoint_file_name = f"{worker_id}_depot_checkpoint"
        self.checkpoint_manager = CheckpointManager(checkpoint_file_name)
        self._output_file: str | None = None

        self.records: list[dict] = []

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

            for category_code in self.resume_manager.continue_from_checkpoint(
                "category_code", DEPOT_EVALUATION_CATEGORY_CODES
            ):
                self.runtime_guard.check()
                await self._crawl_category(static_page, extraction_page, category_code)
        finally:
            self._output_file = None
            await extraction_page.close()
            await static_page.close()

        self.checkpoint_manager.clear_progress()

        return self.records

    async def _crawl_category(
        self, static_page: Page, extraction_page: Page, category_code: str
    ) -> None:
        """
        Category Selection Page → Service Selection Page → Search Area Page

        Iterate through each category code one at a time.
        """

        category = DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER[category_code]

        category_name = category.get("name")

        log(
            f"Category: {category_name} ({category_code})",
            component=__name__,
            worker_id=self.worker_id,
        )

        async def _load_service_selection_page() -> None:
            await static_page.goto(DEPOT_EVALUATION_BASE_URL)
            await static_page.wait_for_selector(
                "font.chas:has-text('サービスの分類を選択してください。')"
            )
            # Select category and trigger search
            await static_page.get_by_role(
                "link", name=category_name, exact=True
            ).first.click()
            await static_page.wait_for_selector(
                "font.chas:has-text('サービスを選択して、検索ボタンを押してください。（複数選択可能）')"
            )
            await asyncio.sleep(random.uniform(0.3, 0.6))

        await retry_async(
            _load_service_selection_page,
            runtime_guard=self.runtime_guard,
            worker_id=self.worker_id,
        )

        # Filter result by selecting target services for the category
        target_services = category.get("services", {})

        for service_value, service_name in target_services.items():
            service_checkbox = static_page.locator(
                f"input[name='STEP_SVCSBRCD'][value='{service_value}']"
            ).first

            if not await service_checkbox.is_checked():
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await service_checkbox.check()

                log(
                    f"Selected service: {service_name} ({service_value})",
                    component=__name__,
                    worker_id=self.worker_id,
                )

        async def _load_search_area_page() -> None:
            # Click search button
            await asyncio.sleep(random.uniform(0.3, 0.6))
            await static_page.locator("input[onclick='doSearch();']").click()
            await static_page.wait_for_selector(
                "font.text:has-text('【地域を選択してください】')"
            )
            await asyncio.sleep(random.uniform(0.3, 0.6))

        await retry_async(
            _load_search_area_page,
            runtime_guard=self.runtime_guard,
            worker_id=self.worker_id,
        )

        area_selection_url = static_page.url

        # Collect area codes and names for iteration, exclude broad and disabled options, deduplicating while preserving order
        area_inputs = static_page.locator("input[name='MLT_AREA']")
        area_count = await area_inputs.count()

        area_codes: list[str] = []
        area_code_to_name: dict[str, str] = {}

        for i in range(area_count):
            area_input = area_inputs.nth(i)

            if await area_input.is_disabled():
                continue

            area_code = await area_input.get_attribute("value")

            if not area_code or area_code in BROAD_AREA_CODES_TO_SKIP:
                continue

            if area_code not in area_code_to_name:
                area_name = (
                    await static_page.locator(
                        f"td:has(input[name='MLT_AREA'][value='{area_code}']) + td"
                    ).first.inner_text()
                ).strip()

                area_codes.append(area_code)
                area_code_to_name[area_code] = area_name

        # Partition by Area
        # Example:
        # Worker 0: Category code: 21 → Area codes: 13101, 13104, 13107, 13110, 13113
        # Worker 1: Category code: 21 → Area codes: 13102, 13105, 13108, 13111, 13114
        # Worker 2: Category code: 21 → Area codes: 13103, 13106, 13109, 13112, 13115
        assigned_area_codes = partition(area_codes, self.worker_count)[self.worker_id]

        log(
            f"Assigned {len(assigned_area_codes)} area codes: [{', '.join(assigned_area_codes)}]",
            component=__name__,
            worker_id=self.worker_id,
        )

        for area_code in self.resume_manager.continue_from_checkpoint(
            "area_code", assigned_area_codes
        ):
            self.runtime_guard.check()

            area_index = assigned_area_codes.index(area_code) + 1
            total_areas = len(assigned_area_codes)

            area_name = area_code_to_name.get(area_code, "")

            log(
                f"Area: {area_name} ({area_code}) - {area_index}/{total_areas}",
                component=__name__,
                worker_id=self.worker_id,
            )

            await self._crawl_area(
                static_page,
                extraction_page,
                area_selection_url,
                category_code=category_code,
                area_code=area_code,
                area_name=area_name,
            )

        log(
            f"Category: {category_name} ({category_code}) - COMPLETED",
            component=__name__,
            worker_id=self.worker_id,
        )

    async def _crawl_area(
        self,
        static_page: Page,
        extraction_page: Page,
        area_selection_url: str,
        *,
        category_code: str,
        area_code: str,
        area_name: str,
    ) -> None:
        """
        Search Area Page → Evaluation Index Page

        Iterate through each area code one at a time.
        """

        await static_page.goto(
            area_selection_url,
            wait_until="domcontentloaded",
        )
        await static_page.wait_for_selector(
            "font.text:has-text('【地域を選択してください】')",
        )
        await asyncio.sleep(random.uniform(0.3, 0.6))

        target_area = static_page.locator(
            f"input[name='MLT_AREA'][value='{area_code}']"
        )

        await target_area.first.check()
        # Click search button
        await static_page.locator("input[onclick='doSearch();']").click()

        await static_page.wait_for_selector("font.cha2:has-text('◆評価結果一覧◆')")

        await self._crawl_evaluation_index(
            static_page,
            extraction_page,
            category_code=category_code,
            area_code=area_code,
        )

        log(
            f"Area: {area_name} ({area_code}) - COMPLETED",
            component=__name__,
            worker_id=self.worker_id,
        )

    async def _crawl_evaluation_index(
        self,
        static_page: Page,
        extraction_page: Page,
        *,
        category_code: str,
        area_code: str,
    ) -> None:
        """
        Evaluation Index Page → Evaluation Detail Page
        """

        page_num = 1

        while True:
            await static_page.wait_for_selector("font.cha2:has-text('◆評価結果一覧◆')")

            first_eval_result_link = static_page.locator(
                "table:has(th.pink2) tr:has(td) td:nth-child(2) a"
            ).first

            await first_eval_result_link.wait_for(state="visible")

            # Pagination-level resume
            if self.resume_manager.is_resuming():
                checkpoint_page_num = self.resume_manager.get_saved_value("page_num")

                if checkpoint_page_num is not None and page_num <= checkpoint_page_num:
                    # Iterate through pagination until reaching the checkpoint_page_num
                    while page_num < checkpoint_page_num:
                        self.runtime_guard.check()

                        # <a href="javascript:showNextPage(160, true);">5</a>
                        # name = str(checkpoint_page_num) = "5"
                        checkpoint_page_link = static_page.get_by_role(
                            "link",
                            name=str(checkpoint_page_num),
                            exact=True,
                        ).first

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
                                f"td[colspan='3']:has-text('{checkpoint_page_num}／')"
                            )

                            page_num = checkpoint_page_num
                            break

                        # checkpoint_page_num is not yet visible
                        # go to the next pagination group of 10 pages
                        # <a href="javascript:showNextPage(400, true);">進む >></a>
                        next_10_link = static_page.get_by_role(
                            "link",
                            name="進む >>",
                            exact=True,
                        ).first

                        expected_page_num = page_num + 10

                        log(
                            f"Page {checkpoint_page_num} is not yet visible, advancing pagination by 10 pages from page {page_num}",
                            component=__name__,
                            worker_id=self.worker_id,
                        )

                        await next_10_link.click()
                        await asyncio.sleep(random.uniform(0.3, 0.9))
                        await static_page.wait_for_selector(
                            f"td[colspan='3']:has-text('{expected_page_num}／')"
                        )

                        page_num = expected_page_num

                    # Clear checkpoint_page_num after reaching the correct page
                    self.resume_manager.clear_key("page_num")
                    continue

            # Target results table rows (skip header)
            eval_result_rows = static_page.locator("table:has(th.pink2) tr:has(td)")
            total_evaluations = await eval_result_rows.count()

            log(
                f"Page {page_num}: {total_evaluations} Evaluation results found",
                component=__name__,
                worker_id=self.worker_id,
            )

            for row_index in self.resume_manager.continue_from_checkpoint(
                "row_index", range(total_evaluations)
            ):
                self.runtime_guard.check()
                self.cancellation_flag.check()

                log(
                    f"Extracting depot data - {row_index + 1}/{total_evaluations}",
                    component=__name__,
                    worker_id=self.worker_id,
                )

                # Re-locate row each iteration to avoid stale references
                eval_result_rows = static_page.locator("table:has(th.pink2) tr:has(td)")
                row = eval_result_rows.nth(row_index)
                eval_result_link = row.locator("td").nth(1).locator("a")

                # javascript:showDetail('113','2026002732','1')
                eval_result_ref = await eval_result_link.first.get_attribute("href")

                if eval_result_ref and eval_result_ref.startswith("javascript:"):
                    static_page_url = static_page.url
                    # javascript:showDetail('113','2026002732','1') → showDetail('113','2026002732','1')
                    eval_detail_script = eval_result_ref.removeprefix("javascript:")

                    async def _load_evaluation_detail_page() -> None:
                        await asyncio.sleep(random.uniform(0.3, 0.6))
                        await extraction_page.goto(
                            static_page_url,  # noqa: B023 - retry_async is awaited before the loop advances
                            wait_until="domcontentloaded",
                        )
                        # Execute JS: showDetail('113','2026002732','1')
                        await extraction_page.evaluate(
                            f"() => {{ {eval_detail_script} }}"  # noqa: B023 - retry_async is awaited before the loop advances
                        )
                        await extraction_page.wait_for_selector(
                            "h1.main-title:has-text('評価結果')"
                        )
                        await asyncio.sleep(random.uniform(0.3, 0.6))

                    await retry_async(
                        _load_evaluation_detail_page,
                        runtime_guard=self.runtime_guard,
                        worker_id=self.worker_id,
                    )
                    await self._crawl_depot_detail(extraction_page)

                self.checkpoint_manager.save_progress(
                    {
                        "category_code": category_code,
                        "area_code": area_code,
                        "page_num": page_num,
                        "row_index": row_index,
                    }
                )

            # <a href="javascript:showNextPage(40, true);">次ページに進む >></a>
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
                f"td[colspan='3']:has-text('{expected_page_num}／')"
            )

            page_num = expected_page_num

    async def _crawl_depot_detail(self, page: Page) -> None:
        """
        Depot Detail Page → Data Extraction
        """

        depot_link = page.locator("a[href*='showJgy(']")

        if await depot_link.count() == 0:
            log(
                "Depot link does not exist, skipping",
                component=__name__,
                worker_id=self.worker_id,
            )
            return

        async with page.expect_navigation(wait_until="domcontentloaded"):
            await depot_link.first.click()

        broken_page_message = page.locator(
            "font.cha:has-text('現在ページを表示することができません。')"
        )

        if await broken_page_message.count() > 0:
            log(
                "Depot link for this evaluation is not working, skipping",
                component=__name__,
                worker_id=self.worker_id,
            )
            return

        await page.wait_for_selector("h4.resultTitle:has-text('１ 基本情報')")

        record = await self._extract_depot_data(page)
        self.records.append(record)

        if self._output_file is not None:
            append_ndjson(record, self._output_file)

    async def _extract_depot_data(self, page: Page) -> dict:

        depot_name = await self._extract_table_row_value(page, "事業所名")

        phone_number = await self._extract_table_row_value(page, "事業所電話")

        fax_number = await self._extract_table_row_value(page, "事業所FAX")

        service_type = await self._extract_table_row_value(page, "サービス種別")

        opened_date_raw = await self._extract_table_row_value(page, "設立")
        opened_date = self._parse_opened_date(opened_date_raw)

        capacity = await self._extract_capacity(page)

        corporation_name = await self._extract_corporation_name(page)

        update_date = await self._extract_update_block(page)

        depot_code = await self._extract_depot_code(page)

        address = await self._extract_address(page)

        city = self._extract_city(address)

        staff_count = await self._extract_staff_count(page)

        hp = await self._extract_hp(page)

        record = {
            "corporation_name": corporation_name,
            "depot_name": depot_name,
            "depot_code": depot_code,
            "address": address,
            "city": city,
            "phone_number": phone_number,
            "fax_number": fax_number,
            "hp": hp,
            "service_type": service_type,
            "capacity": capacity,
            "staff_count": staff_count,
            "opened_date": opened_date,
            "is_active": True,  # Temporarily set to True
            "source_url": page.url,
            "update_date": update_date,
            "created_at": datetime.now(UTC).isoformat(),
        }

        record["data_hash"] = generate_data_hash(record)

        return record

    async def _extract_text_from_selector(self, page: Page, selector: str) -> str:

        loc = page.locator(selector).first
        return (await loc.inner_text()).strip()

    async def _extract_table_row_value(self, page: Page, header: str) -> str:

        selector = f"tr:has(th:has-text('{header}')) > td"
        return await self._extract_text_from_selector(page, selector)

    async def _extract_corporation_name(self, page: Page) -> str:
        """
        Label: 経営法人

        Example:

        社会福祉法人カメリア会 \t法人が運営している事業所一覧
        - → 社会福祉法人カメリア会
        """

        text = await self._extract_table_row_value(page, "経営法人")

        normalized = text.replace("\u00a0", " ").strip()
        return normalized.split("\t", 1)[0].strip()

    async def _extract_update_block(self, page: Page) -> str:
        """
        Label:
        - 更新日 → update_date

        Example:

        更新日 2025年9月5日
        \n001-1310100110
        - update_date → 2025年9月5日
        """

        block = page.locator("div.koushin")

        text = await block.first.inner_text()
        lines = text.split("\n")

        update_date = lines[0].replace("更新日", "").strip()
        return update_date

    async def _extract_depot_code(self, page: Page) -> int:
        """
        Label: 事業所番号

        Example:

        1351700198&nbsp;
        - → 1351700198
        """

        depot_code_cell = page.locator(
            "table.resultTable3 td:text-is('事業所番号') + td"
        ).first

        # 事業所番号 is sometimes missing
        if await depot_code_cell.count() == 0:
            return 0

        text = await depot_code_cell.inner_text()
        return int(text.strip())

    async def _extract_address(self, page: Page) -> str:
        """
        Label: 所在地

        Example:

        101-0063
        \n東京都千代田区神田淡路町2丁目8番1号
        - → 101-0063 東京都千代田区神田淡路町2丁目8番1号
        """

        address = await self._extract_table_row_value(page, "所在地")
        return re.sub(r"\s+", " ", address).strip()  # remove whitespace

    def _extract_city(self, address: str) -> str:
        """
        Source: 所在地

        ([Prefecture][City/Ward/Town/Village][Rest of address] ex: 東京都 + (市 / 区 / 町 / 村) + remaining)

        Example:

        101-0063 東京都千代田区神田淡路町2丁目8番1号
        - → 千代田区
        """

        address = re.sub(r"[＊※*]", "", address)  # remove special markers

        # Extract city
        match = re.search(r"東京都(.+?[市区町村])", address)

        return match.group(1) if match else ""

    async def _extract_hp(self, page: Page) -> str:
        """
        Label: ホームページ
        """

        link = page.locator("tr:has(th:has-text('ホームページ')) > td a")

        if await link.count() == 0:
            return ""

        href = await link.get_attribute("href")
        return href or ""

    async def _extract_capacity(self, page: Page) -> int:
        """
        Extract capacity from either a single capacity or categorized capacity format.

        - For categorized capacity, sum category values when at least one category has value.
        - Use `合計` only when all category values are blank.
        """

        capacity_cell = page.locator("tr:has(th:has-text('定員')) > td").first

        # 定員 is sometimes missing
        if await capacity_cell.count() == 0:
            return 0

        capacity_table = capacity_cell.locator(":scope > table").first

        # Format 1: Single capacity
        # label | value
        if await capacity_table.count() == 0:
            capacity_text = await capacity_cell.inner_text()
            return self._extract_first_int(capacity_text)

        # Format 2: Categorized capacity
        # label | label | label | label | label | label | label
        # value | value | value | value | value | value | value
        rows = capacity_table.locator(":scope > tbody > tr")
        category_cells = rows.nth(0).locator(":scope > td")
        value_cells = rows.nth(1).locator(":scope > td")

        capacity = 0
        total = 0
        category_value_count = 0

        for column_index in range(await category_cells.count()):
            category = (await category_cells.nth(column_index).inner_text()).strip()
            value_text = (await value_cells.nth(column_index).inner_text()).strip()
            value = self._extract_first_int(value_text)

            # 合計 is present. Keep it as fallback when all categories are blank
            if category == "合計":
                total = value
                continue

            normalized_value = self._normalize_full_width_numbers(value_text)

            # category has a value, use category values instead of 合計
            if re.search(r"\d+", normalized_value):
                category_value_count += 1
                capacity += value

        # all categories are blank, use 合計
        if category_value_count == 0:
            return total

        # at least one category has a value, return summed category values
        return capacity

    async def _extract_staff_count(self, page: Page) -> int:
        """
        Label: 職員数

        - Sum category values when at least one category has a numeric value.
        - Use `合計` only when all category values are blank.
        """

        staff_count_cell = page.locator("tr:has(th:has-text('職員数')) > td").first

        # 職員数 is sometimes missing
        if await staff_count_cell.count() == 0:
            return 0

        staff_row = staff_count_cell.locator(":scope > table > tbody > tr").first

        # Labels and values are stored in alternating cells:
        # label | value | label | value | label | value
        label_cells = staff_row.locator(":scope > td:nth-child(odd)")
        value_cells = staff_row.locator(":scope > td:nth-child(even)")

        staff_count = 0
        total = 0
        category_value_count = 0

        for column_index in range(await label_cells.count()):
            label = (await label_cells.nth(column_index).inner_text()).strip()
            value_text = (await value_cells.nth(column_index).inner_text()).strip()
            value = self._extract_first_int(value_text)

            # 合計 is present. Keep it as fallback when all categories are blank
            if label == "合計":
                total = value
                continue

            normalized_value = self._normalize_full_width_numbers(value_text)

            # category has a value, use category values instead of 合計
            if re.search(r"\d+", normalized_value):
                category_value_count += 1
                staff_count += value

        # all categories are blank, use 合計
        if category_value_count == 0:
            return total

        # at least one category has a value, return summed category values
        return staff_count

    def _extract_first_int(self, text: str) -> int:
        """
        Extract the first integer from text, returns 0 if no integer is found.

        Example:

        7名（女性棟）
        - → 7
        """

        normalized_text = self._normalize_full_width_numbers(text)
        match = re.search(r"\d+", normalized_text)

        return int(match.group()) if match else 0

    def _parse_opened_date(self, text: str) -> str | None:
        """
        Convert Japanese opened_date text to ISO format (YYYY-MM-DD), returns None if parsing fails.

        Example:

        2004年4月1日設立
        - → 2004-04-01

        昭和11年12月5日設立
        - → 1936-12-05
        """

        if not text:
            return None

        # normalize full-width numbers
        text = self._normalize_full_width_numbers(text)

        # remove 設立
        text = text.replace("設立", "").strip()

        # Japanese era support
        era_map = {
            "令和": 2018,
            "平成": 1988,
            "昭和": 1925,
        }

        for era, offset in era_map.items():
            m = re.search(rf"{era}\s*(\d+)年\s*(\d{{1,2}})月\s*(\d{{1,2}})?", text)
            if m:
                year = offset + int(m.group(1))
                month = int(m.group(2))
                day = int(m.group(3)) if m.group(3) else 1
                return f"{year:04d}-{month:02d}-{day:02d}"

        # Gregorian full date
        m = re.search(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", text)
        if m:
            year, month, day = map(int, m.groups())
            return f"{year:04d}-{month:02d}-{day:02d}"

        # Gregorian year + month only
        m = re.search(r"(\d{4})年\s*(\d{1,2})月", text)
        if m:
            year, month = map(int, m.groups())
            return f"{year:04d}-{month:02d}-01"

        return None

    def _normalize_full_width_numbers(self, text: str) -> str:

        return text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
