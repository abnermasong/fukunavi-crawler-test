import asyncio
import random
import re
from datetime import UTC, datetime

from playwright.async_api import BrowserContext, Locator, Page

from app.constants import (
    ADDRESS_COL,
    CERT_NUMBER_COL,
    CORPORATION_AGENCY_AREA_CODE_TO_NAME,
    CORPORATION_AGENCY_AREA_CODES,
    EVALUATION_AGENCY_BASE_URL,
    IS_ACCEPTING_COL,
    IS_SOCIAL_CARE_COL,
    PHONE_NUMBER_COL,
    TARGET_CATEGORIES_COL,
)
from app.utils.cancellation import CancellationFlagManager
from app.utils.checkpoint import CheckpointManager
from app.utils.hashing import generate_data_hash
from app.utils.loggers import log
from app.utils.ndjson import append_ndjson, start_ndjson_file
from app.utils.resume import ResumeManager
from app.utils.retry import retry_async
from app.utils.runtime_guard import RuntimeGuardManager


class EvaluationAgencyCrawler:
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

        checkpoint_file_name = f"{worker_id}_evaluation_agency_checkpoint"
        self.checkpoint_manager = CheckpointManager(checkpoint_file_name)
        self._output_file: str | None = None

        self.records: list[dict] = []

    async def crawl(
        self,
        browser_context: BrowserContext,
        *,
        output_file: str | None = None,
        target_area_codes: list[str] | None = None,
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
                "area_code", target_area_codes or CORPORATION_AGENCY_AREA_CODES
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
        Search Area Page → Evaluation Agency Index Page

        Iterate through each area code one at a time.
        """

        area_name = CORPORATION_AGENCY_AREA_CODE_TO_NAME.get(area_code)

        log(
            f"Area: {area_name} ({area_code})",
            component=__name__,
            worker_id=self.worker_id,
        )

        async def _load_eval_agency_index_page() -> None:
            await static_page.goto(EVALUATION_AGENCY_BASE_URL)
            # Select area from dropdown
            await static_page.select_option("select[name='AREA1']", value=area_code)
            # Click search button
            await asyncio.sleep(random.uniform(0.3, 0.9))
            await static_page.locator("input[onclick='doSearch(1);']").click()
            await static_page.wait_for_selector("font.cha2:has-text('◆評価機関一覧◆')")
            await asyncio.sleep(random.uniform(0.3, 0.9))

        await retry_async(
            _load_eval_agency_index_page,
            runtime_guard=self.runtime_guard,
            worker_id=self.worker_id,
        )
        await self._crawl_eval_agency_index(static_page, extraction_page, area_code)

        log(
            f"Area: {area_name} ({area_code}) - COMPLETED",
            component=__name__,
            worker_id=self.worker_id,
        )

    async def _crawl_eval_agency_index(
        self, static_page: Page, extraction_page: Page, area_code: str
    ) -> None:
        """
        Evaluation Agency Index Page → Evaluation Agency Detail Page → Data Extraction
        """

        no_data = static_page.locator("text=該当するデータはありませんでした。")
        if await no_data.count() > 0:
            log(
                "No data found for this area.",
                component=__name__,
                worker_id=self.worker_id,
            )
            return

        # Target evaluation agency table header since there's no table class identifier
        table_selector = "table:has(th.pink2:has-text('認証番号'))"
        await static_page.wait_for_selector(table_selector)

        table = static_page.locator(table_selector)

        eval_agency_rows = table.locator("tbody > tr:has(td)")
        total_eval_agencies = await eval_agency_rows.count()

        log(
            f"{total_eval_agencies} evaluation agencies found",
            component=__name__,
            worker_id=self.worker_id,
        )

        for row_index in self.resume_manager.continue_from_checkpoint(
            "row_index", range(total_eval_agencies)
        ):
            self.runtime_guard.check()
            self.cancellation_flag.check()

            log(
                f"Extracting evaluation agency data - {row_index + 1}/{total_eval_agencies}",
                component=__name__,
                worker_id=self.worker_id,
            )

            eval_agency_row = eval_agency_rows.nth(row_index)

            evaluation_agency_link = eval_agency_row.locator("td").nth(1).locator("a")

            # javascript:showDetail('0012')
            evaluation_agency_href = await evaluation_agency_link.get_attribute("href")
            eval_agency_detail_url = static_page.url

            if evaluation_agency_href and evaluation_agency_href.startswith(
                "javascript:"
            ):
                static_page_url = static_page.url
                # javascript:showDetail('0012') → showDetail('0012')
                eval_agency_detail_script = evaluation_agency_href.removeprefix(
                    "javascript:"
                )

                async def _crawl_evaluation_agency_detail_page() -> None:
                    await extraction_page.goto(static_page_url)  # noqa: B023 - retry_async is awaited before the loop advances
                    await asyncio.sleep(random.uniform(0.3, 0.9))
                    # Execute JS: showDetail('0012')
                    await extraction_page.evaluate(
                        f"() => {{ {eval_agency_detail_script} }}"  # noqa: B023 - retry_async is awaited before the loop advances
                    )
                    await extraction_page.wait_for_selector(
                        "font.green1:has-text('◆評価機関情報◆')"
                    )
                    await asyncio.sleep(random.uniform(0.3, 0.9))

                await retry_async(
                    _crawl_evaluation_agency_detail_page,
                    runtime_guard=self.runtime_guard,
                    worker_id=self.worker_id,
                )
                eval_agency_detail_url = extraction_page.url

            record = await self._extract_evaluation_agency_data(
                eval_agency_row,
                source_url=eval_agency_detail_url,
                extraction_page=extraction_page,
            )
            self.records.append(record)

            if self._output_file is not None:
                append_ndjson(record, self._output_file)

            self.checkpoint_manager.save_progress(
                {
                    "area_code": area_code,
                    "row_index": row_index,
                }
            )

    async def _extract_evaluation_agency_data(
        self,
        eval_agency_row: Locator,
        *,
        source_url: str,
        extraction_page: Page,
    ) -> dict:

        # Source: Evaluation Agency Index Page
        address = await self._extract_address(eval_agency_row)

        phone_number = await self._extract_phone_number(eval_agency_row)

        certification_number = await self._extract_certification_number(eval_agency_row)

        target_categories = await self._extract_target_categories(eval_agency_row)

        is_accepting = await self._extract_is_accepting(eval_agency_row)

        is_social_care = await self._extract_is_social_care(eval_agency_row)

        is_active = await self._extract_is_active(eval_agency_row)

        # Source: Evaluation Agency Detail Page
        agency_name = await self._extract_agency_name(extraction_page)

        agency_type = self._extract_agency_type(agency_name)

        hp = await self._extract_hp(extraction_page)

        record = {
            "agency_name": agency_name,
            "certification_number": certification_number,
            "agency_type": agency_type,
            "address": address,
            "phone_number": phone_number,
            "hp": hp,
            "target_categories": target_categories,
            "is_accepting": is_accepting,
            "is_social_care": is_social_care,
            "is_active": is_active,
            "source_url": source_url,
            "created_at": datetime.now(UTC).isoformat(),
        }

        record["data_hash"] = generate_data_hash(record)
        return record

    async def _extract_text_from_col(self, row: Locator, column_index: int) -> str:

        row = row.locator("td").nth(column_index)
        return (await row.inner_text()).strip()

    async def _extract_address(self, row: Locator) -> str:
        """
        Label: 所在地
        """

        return await self._extract_text_from_col(row, ADDRESS_COL)

    async def _extract_phone_number(self, row: Locator) -> str:
        """
        Label: 電話番号
        """

        return await self._extract_text_from_col(row, PHONE_NUMBER_COL)

    async def _extract_certification_number(self, row: Locator) -> str:
        """
        Label: 認証番号
        """

        return await self._extract_text_from_col(row, CERT_NUMBER_COL)

    async def _extract_target_categories(self, row) -> str:
        """
        Label:

        対応可能な
        \n評価分野

        Example:

        生活保護 \\n女性 \\n子ども・ひとり親 \\n子ども（保育） \\n障害児・者（在宅） \\n障害児・者（入所）
        - → 生活保護
          - 女性
          - 子ども・ひとり親
          - 子ども（保育）
          - 障害児・者（在宅）
          - 障害児・者（入所）
        """

        text = await self._extract_text_from_col(row, TARGET_CATEGORIES_COL)

        target_categories = [line.strip() for line in text.splitlines() if line.strip()]

        return "\n".join(target_categories)

    async def _extract_is_accepting(self, row) -> bool:
        """
        Label: 評価実施

        If it does not contain "契約受付中" or "本年度は締切" then return False.
        """

        text = await self._extract_text_from_col(row, IS_ACCEPTING_COL)

        return "契約受付中" in text or "本年度は締切" in text

    async def _extract_is_social_care(self, row) -> bool:
        """
        Label:

        社会的養護関係施設評価機関
        \n（「更新回数」は2016年度以降に更新した回数）

        If empty then return False.
        """

        text = await self._extract_text_from_col(row, IS_SOCIAL_CARE_COL)
        return bool(text.strip())

    async def _extract_is_active(self, row: Locator) -> bool:
        """
        Label: 評価機関名

        If it contains "迄の評価機関" then return False.
        """

        text = await row.inner_text()

        return "迄の評価機関" not in text

    async def _extract_agency_name(self, page: Page) -> str:
        """
        Label: 評価機関名
        """

        agency_name_cell = (
            page.locator("tr")
            .filter(has=page.locator("td:first-child:has-text('評価機関名')"))
            .locator(":scope > td:nth-child(2)")
            .first
        )

        text = await agency_name_cell.inner_text()
        return self._normalize_spaces(text)

    def _extract_agency_type(self, agency_name: str) -> str:
        """
        Label: 評価機関名

        First word only.

        Example:

        agency_name: 株式会社　ノンフィクションチャネル（平成17年10月31日迄の評価機関）
        - → 株式会社
        """

        normalized_name = self._normalize_spaces(agency_name)
        agency_name_parts = normalized_name.split(" ", 1)

        return agency_name_parts[0] if agency_name_parts else ""

    async def _extract_hp(self, page: Page) -> str:
        """
        Label: ホームページ
        """

        hp_link = (
            page.locator("tr")
            .filter(
                has=page.locator("td:first-child table td:has-text('（ホームページ）')")
            )
            .locator(":scope > td:nth-child(2) a")
            .first
        )

        if await hp_link.count() == 0:
            return ""

        return (await hp_link.inner_text()).strip()

    def _normalize_spaces(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()
