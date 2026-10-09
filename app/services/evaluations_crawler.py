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


class EvaluationCrawler:
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

        checkpoint_file_name = f"{worker_id}_evaluation_checkpoint"
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

                            await checkpoint_page_link.first.click()
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
                    f"Processing evaluation data in row - {row_index + 1}/{total_evaluations}",
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
                    eval_result_script = eval_result_ref.removeprefix("javascript:")

                    async def _load_evaluation_detail_page() -> None:
                        await asyncio.sleep(random.uniform(0.3, 0.6))
                        await extraction_page.goto(
                            static_page_url,  # noqa: B023 - retry_async is awaited before the loop advances
                            wait_until="domcontentloaded",
                        )
                        # Execute JS: showDetail('113','2026002732','1')
                        await extraction_page.evaluate(
                            f"() => {{ {eval_result_script} }}"  # noqa: B023 - retry_async is awaited before the loop advances
                        )
                        await asyncio.sleep(random.uniform(0.3, 0.6))

                    await retry_async(
                        _load_evaluation_detail_page,
                        runtime_guard=self.runtime_guard,
                        worker_id=self.worker_id,
                    )

                    await self._crawl_evaluation_detail(
                        extraction_page,
                        category_code=category_code,
                        area_code=area_code,
                        page_num=page_num,
                        row_index=row_index,
                    )

                self.checkpoint_manager.save_progress(
                    {
                        "category_code": category_code,
                        "area_code": area_code,
                        "page_num": page_num,
                        "row_index": row_index,
                        "year_index": 0,
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

    async def _crawl_evaluation_detail(
        self,
        page: Page,
        *,
        category_code: str,
        area_code: str,
        page_num: int,
        row_index: int,
    ) -> None:
        """
        Evaluation Detail Page → Data Extraction

        Iterate through each evaluation year option for the evaluation.
        """

        await page.wait_for_selector(
            "#evaluation-year-select",
        )

        year_select = page.locator("#evaluation-year-select")
        option_count = await year_select.locator("option").count()

        if option_count == 0:
            log(
                "No evaluation year options found, skipping",
                component=__name__,
                worker_id=self.worker_id,
            )
            return

        # Collect values first before page transitions
        eval_years_options: list[str] = []
        for i in range(option_count):
            value = await year_select.locator("option").nth(i).get_attribute("value")
            if value:
                eval_years_options.append(value)

        for year_index in self.resume_manager.continue_from_checkpoint(
            "year_index", range(len(eval_years_options))
        ):
            eval_year = eval_years_options[year_index]

            eval_year_only = eval_year.split(",")[0] if "," in eval_year else eval_year

            log(
                f"Extracting evaluation data - {eval_year_only} ({year_index + 1}/{len(eval_years_options)})",
                component=__name__,
                worker_id=self.worker_id,
            )

            year_select = page.locator("#evaluation-year-select")
            current_value = await year_select.input_value()

            # First loaded year is already on screen
            if eval_year != current_value:
                await asyncio.sleep(random.uniform(0.3, 0.6))
                await year_select.select_option(value=eval_year)

                await page.wait_for_selector(
                    "#evaluation-year-select",
                )

            record = await self._extract_evaluation_data(page)
            self.records.append(record)

            if self._output_file is not None:
                append_ndjson(record, self._output_file)

            self.checkpoint_manager.save_progress(
                {
                    "category_code": category_code,
                    "area_code": area_code,
                    "page_num": page_num,
                    "row_index": row_index,
                    "year_index": year_index,
                }
            )

    async def _extract_evaluation_data(self, page: Page) -> dict:

        depot_name = await self._extract_depot_name(page)

        evaluation_agency_name = await self._extract_table_row_value(
            page, "evaluator-info", "【評価機関名】"
        )

        evaluation_year_value = await page.locator(
            "#evaluation-year-select"
        ).input_value()
        evaluation_year = self._parse_evaluation_year(evaluation_year_value)

        period_raw = await self._extract_table_row_value(
            page, "evaluator-info", "【評価実施期間】"
        )
        start_date, end_date = self._parse_jp_date_range(period_raw)

        record = {
            "depot_name": depot_name,
            "evaluation_agency_name": evaluation_agency_name,
            "evaluation_year": evaluation_year,
            "evaluation_date": start_date,
            "evaluation_end_date": end_date,
            "source_url": page.url,
            "created_at": datetime.now(UTC).isoformat(),
        }

        record["data_hash"] = generate_data_hash(record)
        return record

    async def _extract_text_from_selector(self, page: Page, selector: str) -> str:

        loc = page.locator(selector).first
        return (await loc.inner_text()).strip()

    async def _extract_table_row_value(
        self, page: Page, section: str, header: str
    ) -> str:

        selector = f"section#{section} .info-card:has(p:has-text('{header}')) p.data"
        return await self._extract_text_from_selector(page, selector)

    async def _extract_depot_name(self, page: Page) -> str:
        """
        Label: 【事業所名称】

        Example:
        なないろ／なないろ   他1ユニット    他ユニットを表示
        - → なないろ／なないろ
        """

        selector = "section#info .info-card:has(p:has-text('【事業所名称】')) p.data"

        if await page.locator(f"{selector} > a").count() > 0:
            return await self._extract_text_from_selector(page, f"{selector} > a")

        # Plain text fallback: keep only the name
        text = await self._extract_text_from_selector(page, selector)
        return re.split(r"\s{2,}|\n", text)[0].strip()

    def _parse_evaluation_year(self, text: str) -> int:
        """
        Parse evaluation year from dropdown value format.

        Example:

        2025,2026002031
        - → 2025
        """

        match = re.match(r"^(\d{4}),", text.strip())
        if not match:
            return 0

        return int(match.group(1))

    def _parse_jp_date(self, text: str) -> str:
        """
        Parse Japanese date from text.

        Example:

        2025年3月18日
        - → 2025-03-18
        """

        match = re.search(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", text)

        if not match:
            return ""

        year, month, day = map(int, match.groups())

        return f"{year:04d}-{month:02d}-{day:02d}"

    def _parse_jp_date_range(self, text: str) -> tuple[str, str]:
        """
        Parse Japanese date range from text.

        Example:

        2025年3月18日～2026年1月19日
        - → ("2025-03-18", "2026-01-19")
        """

        date_parts = [
            part.strip() for part in re.split(r"～|~|-", text) if part.strip()
        ]

        if len(date_parts) == 1:
            start_date = self._parse_jp_date(date_parts[0])
            return start_date, ""

        start_date = self._parse_jp_date(date_parts[0])
        end_date = self._parse_jp_date(date_parts[1])

        return start_date, end_date
