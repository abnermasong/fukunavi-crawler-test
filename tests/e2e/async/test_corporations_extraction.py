# import json

import pytest
from playwright.async_api import expect

from app.services.corporations_crawler import CorporationCrawler
from app.utils.browser import BrowserManager

CORPORATION_DETAIL_URLS = [
    "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=206201016&SVCSBR_CD=001",
    "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=900003723&SVCSBR_CD=001",
    "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=900009926&SVCSBR_CD=001",
    "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=107201005&SVCSBR_CD=001",
    "https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=102201001&SVCSBR_CD=001",
]


@pytest.mark.asyncio
async def test_corporations_crawler_extraction():
    async with BrowserManager(headless=True) as browser_context:
        page = await browser_context.new_page()
        crawler = CorporationCrawler.__new__(CorporationCrawler)

        records = []
        for url in CORPORATION_DETAIL_URLS:
            await page.goto(url)

            await page.wait_for_selector("th:has-text('法人名')")
            await expect(page.locator("th:has-text('法人名')")).to_be_visible()

            record = await crawler._extract_corporation_data(page)
            records.append(record)

            # add -s flag to command to print the record
            # print(json.dumps(record, ensure_ascii=False, indent=2))

        # https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=206201016&SVCSBR_CD=001
        assert records[0]["corporation_name"] == "社会福祉法人多摩同胞会"
        assert records[0]["corporation_type"] == "社会福祉法人"
        assert (
            records[0]["address"] == "183-0042 東京都府中市武蔵台1丁目10番1号"
        )  # (183-0042\xa0\xa0 東京都府中市武蔵台1丁目10番1号) Remove whitespace
        assert records[0]["phone_number"] == "042-367-8801"
        assert records[0]["update_date"] == "2025年7月18日"

        # https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=900003723&SVCSBR_CD=001
        assert records[1]["corporation_name"] == "社会福祉法人カメリア会"
        assert records[1]["corporation_type"] == "社会福祉法人"
        assert records[1]["address"] == "東京都"
        assert records[1]["phone_number"] == ""
        assert records[1]["update_date"] == "2025年7月9日"

        # https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=900009926&SVCSBR_CD=001
        assert records[2]["corporation_name"] == "社会福祉法人平成会"
        assert records[2]["corporation_type"] == "社会福祉法人"
        assert (
            records[2]["address"] == "102-0084 東京都千代田区二番町7番地6"
        )  # (102-0084\xa0\xa0 東京都千代田区二番町7番地6) Remove whitespace
        assert records[2]["phone_number"] == "03-3238-0088"
        assert records[2]["update_date"] == "2025年10月6日"

        # https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=107201005&SVCSBR_CD=001
        assert records[3]["corporation_name"] == "社会福祉法人賛育会"
        assert records[3]["corporation_type"] == "社会福祉法人"
        assert (
            records[3]["address"] == "130-0012 東京都墨田区太平3丁目17番8号"
        )  # (130-0012\xa0\xa0 東京都墨田区太平3丁目17番8号) Remove whitespace
        assert records[3]["phone_number"] == "03-3622-7614"
        assert records[3]["update_date"] == "2025年7月22日"

        # https://www.fukunavi.or.jp/fukunavi/controller?cmd=sbrhjn_dt&actionID=jgyhjn&HJN_CD=102201001&SVCSBR_CD=001
        assert records[4]["corporation_name"] == "社会福祉法人シルヴァーウィング"
        assert records[4]["corporation_type"] == "社会福祉法人"
        assert (
            records[4]["address"] == "104-0041 東京都中央区新富1丁目4番6号"
        )  # (104-0041\xa0\xa0 東京都中央区新富1丁目4番6号) Remove whitespace
        assert records[4]["phone_number"] == "03-3553-5228"
        assert records[4]["update_date"] == "2020年3月5日"
