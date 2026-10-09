# import json

import pytest
from playwright.async_api import expect

from app.services.evaluation_agencies_crawler import EvaluationAgencyCrawler
from app.utils.browser import BrowserManager

EVALUATION_AGENCY_INDEX_URL = "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kknlst&BNYCD=&AREA1=0&AREA2=&AREA3=&NAME=&ROW=0&ORDERBY=1&ORDER=1&NSYKKN_NO1=&NSYKKN_NO2=&HYK_CHK=&HYK_SU=&HYK_SU_OLD=&HYK_SU_CHILD=&HYK_SU_HANDI=&HYK_SU_FEMALE=&HYK_SU_WELAARE=&NSY_CHK=&KYK_CHK="
EVALUATION_AGENCY_DETAIL_URLS = [
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0001&ROW=0",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0002&ROW=0",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0003&ROW=0",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0004&ROW=0",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0005&ROW=0",
]


@pytest.mark.asyncio
async def test_evaluation_agencies_crawler_extraction():
    async with BrowserManager(headless=True) as browser_context:
        static_page = await browser_context.new_page()
        extraction_page = await browser_context.new_page()
        crawler = EvaluationAgencyCrawler.__new__(EvaluationAgencyCrawler)

        await static_page.goto(EVALUATION_AGENCY_INDEX_URL)

        await static_page.wait_for_selector("font.cha2:has-text('◆評価機関一覧◆')")
        await expect(
            static_page.locator("font.cha2:has-text('◆評価機関一覧◆')")
        ).to_be_visible()

        table_selector = "table:has(th.pink2:has-text('認証番号'))"
        await static_page.wait_for_selector(table_selector)
        await expect(static_page.locator(table_selector)).to_be_visible()
        table = static_page.locator(table_selector)
        eval_agency_rows = table.locator("tbody > tr:has(td)")

        records = []
        for row_index, detail_url in enumerate(EVALUATION_AGENCY_DETAIL_URLS):
            eval_agency_row = eval_agency_rows.nth(row_index)
            await extraction_page.goto(detail_url)

            await extraction_page.wait_for_selector(
                "font.green1:has-text('◆評価機関情報◆')"
            )

            record = await crawler._extract_evaluation_agency_data(
                eval_agency_row,
                source_url=detail_url,
                extraction_page=extraction_page,
            )
            records.append(record)

            # add -s flag to command to print the record
            # print(json.dumps(record, ensure_ascii=False, indent=2))

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0001&ROW=0
        assert (
            records[0]["agency_name"]
            == "株式会社 ノンフィクションチャネル（平成17年10月31日迄の評価機関）"
        )  # (株式会社　ノンフィクションチャネル（平成17年10月31日迄の評価機関）) Remove whitespace
        assert records[0]["certification_number"] == "機構02-001"
        assert records[0]["agency_type"] == "株式会社"
        assert records[0]["address"] == "千代田区"
        assert records[0]["phone_number"] == "03-5217-3201"
        assert records[0]["hp"] == ""
        assert records[0]["target_categories"] == ""
        assert records[0]["is_accepting"] is False
        assert records[0]["is_social_care"] is False
        assert records[0]["is_active"] is False

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0002&ROW=0
        assert (
            records[1]["agency_name"] == "株式会社 地域計画連合"
        )  # (株式会社　地域計画連合) Remove whitespace
        assert records[1]["certification_number"] == "機構02-002"
        assert records[1]["agency_type"] == "株式会社"
        assert records[1]["address"] == "豊島区"
        assert records[1]["phone_number"] == "03-5974-2021"
        assert records[1]["hp"] == "http://www.rpi-h.co.jp"
        assert (
            records[1]["target_categories"]
            == "生活保護\n女性\n子ども・ひとり親\n子ども（保育）\n障害児・者（在宅）\n障害児・者（入所）\n認知症高齢者GH\n高齢者（在宅）\n高齢者（入所）"
        )
        assert records[1]["is_accepting"] is True
        assert records[1]["is_social_care"] is True
        assert records[1]["is_active"] is True

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0003&ROW=0
        assert (
            records[2]["agency_name"]
            == "特定非営利活動法人 市民シンクタンクひと・まち社"
        )  # (特定非営利活動法人　市民シンクタンクひと・まち社) Remove whitespace
        assert records[2]["certification_number"] == "機構02-003"
        assert records[2]["agency_type"] == "特定非営利活動法人"
        assert records[2]["address"] == "新宿区"
        assert records[2]["phone_number"] == "03-3204-4342"
        assert records[2]["hp"] == "http://www.hitomachi.org"
        assert (
            records[2]["target_categories"]
            == "生活保護\n女性\n子ども・ひとり親\n子ども（保育）\n障害児・者（在宅）\n障害児・者（入所）\n認知症高齢者GH\n高齢者（在宅）\n高齢者（入所）"
        )
        assert records[2]["is_accepting"] is True
        assert records[2]["is_social_care"] is True
        assert records[2]["is_active"] is True

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0004&ROW=0
        assert (
            records[3]["agency_name"] == "特定非営利活動法人 メイアイヘルプユー"
        )  # (特定非営利活動法人　メイアイヘルプユー) Remove whitespace
        assert records[3]["certification_number"] == "機構02-004"
        assert records[3]["agency_type"] == "特定非営利活動法人"
        assert records[3]["address"] == "品川区"
        assert records[3]["phone_number"] == "03-3494-9033"
        assert records[3]["hp"] == "http://www.meiai.org/##"
        assert (
            records[3]["target_categories"]
            == "女性\n子ども・ひとり親\n子ども（保育）\n障害児・者（在宅）\n障害児・者（入所）\n認知症高齢者GH\n高齢者（在宅）\n高齢者（入所）"
        )
        assert records[3]["is_accepting"] is True
        assert records[3]["is_social_care"] is True
        assert records[3]["is_active"] is True

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kkndtl&HYKKKN_ID=0005&ROW=0
        assert (
            records[4]["agency_name"] == "特定非営利活動法人 ＮＰＯ人材開発機構"
        )  # (特定非営利活動法人　ＮＰＯ人材開発機構) Remove whitespace
        assert records[4]["certification_number"] == "機構02-005"
        assert records[4]["agency_type"] == "特定非営利活動法人"
        assert records[4]["address"] == "新宿区"
        assert records[4]["phone_number"] == "03-5206-7831"
        assert records[4]["hp"] == "http://www.npo-jinzai.or.jp"
        assert (
            records[4]["target_categories"]
            == "生活保護\n女性\n子ども・ひとり親\n子ども（保育）\n障害児・者（在宅）\n障害児・者（入所）\n認知症高齢者GH\n高齢者（在宅）\n高齢者（入所）"
        )
        assert records[4]["is_accepting"] is True
        assert records[4]["is_social_care"] is False
        assert records[4]["is_active"] is True
