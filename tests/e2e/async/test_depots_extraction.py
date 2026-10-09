# import json

import pytest
from playwright.async_api import expect

from app.services.depots_crawler import DepotCrawler
from app.utils.browser import BrowserManager

DEPOT_DETAIL_URLS = [
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311502140&SVCSBR_CD=344&NAME=%E3%81%A1%E3%82%83%E3%81%8A%E6%9D%89%E4%B8%A6%E5%92%8C%E6%B3%89%EF%BC%8F%E3%81%A1%E3%82%83%E3%81%8A%E6%9D%89%E4%B8%A6%E5%92%8C%E6%B3%89&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311000598&SVCSBR_CD=031&NAME=%E3%82%A2%E3%82%B9%E3%82%AF%E3%83%90%E3%82%A4%E3%83%AA%E3%83%B3%E3%82%AC%E3%83%AB%E4%BF%9D%E8%82%B2%E5%9C%92%E3%82%84%E3%81%8F%E3%82%82&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311001038&SVCSBR_CD=031&NAME=%E3%81%84%E3%81%84%E3%81%BB%E3%81%84%E3%81%8F%E3%81%88%E3%82%93%E8%87%AA%E7%94%B1%E3%81%8C%E4%B8%98&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1321100159&SVCSBR_CD=113&NAME=%E9%BB%8E%E6%98%8E%E5%AF%AE&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311001028&SVCSBR_CD=031&NAME=%E3%81%97%E3%81%84%E3%81%AE%E3%81%8D%E4%BF%9D%E8%82%B2%E5%9C%92&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311000291&SVCSBR_CD=114&NAME=%E6%9D%B1%E3%81%8C%E4%B8%98%E8%8D%98&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311901242&SVCSBR_CD=342&NAME=%E6%9D%B1%E4%BA%AC%E9%83%BD%E6%9D%BF%E6%A9%8B%E5%8C%BA%E7%AB%8B%E8%B5%A4%E5%A1%9A%E7%A6%8F%E7%A5%89%E5%9C%92&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1310300981&SVCSBR_CD=411&NAME=%E3%83%A1%E3%83%AB%E3%82%B1%E3%82%A2%E3%81%BF%E3%81%AA%E3%81%A8%E3%82%BB%E3%83%B3%E3%82%BF%E3%83%BC&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
    "https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1310200210&SVCSBR_CD=001&NAME=%E7%89%B9%E5%88%A5%E9%A4%8A%E8%AD%B7%E8%80%81%E4%BA%BA%E3%83%9B%E3%83%BC%E3%83%A0%E6%99%B4%E6%B5%B7%E8%8B%91&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=",
]


@pytest.mark.asyncio
async def test_depots_crawler_extraction():
    async with BrowserManager(headless=True) as browser_context:
        page = await browser_context.new_page()
        crawler = DepotCrawler.__new__(DepotCrawler)

        records = []
        for url in DEPOT_DETAIL_URLS:
            await page.goto(url)

            await page.wait_for_selector("h4.resultTitle:has-text('１ 基本情報')")
            await expect(
                page.locator("h4.resultTitle:has-text('１ 基本情報')")
            ).to_be_visible()

            record = await crawler._extract_depot_data(page)
            records.append(record)

            # add -s flag to command to print the record
            # print(json.dumps(record, ensure_ascii=False, indent=2))

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311502140&SVCSBR_CD=344&NAME=%E3%81%A1%E3%82%83%E3%81%8A%E6%9D%89%E4%B8%A6%E5%92%8C%E6%B3%89%EF%BC%8F%E3%81%A1%E3%82%83%E3%81%8A%E6%9D%89%E4%B8%A6%E5%92%8C%E6%B3%89&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[0]["corporation_name"] == "株式会社はっぴーライフ"
        assert records[0]["depot_name"] == "ちゃお杉並和泉／ちゃお杉並和泉"
        assert records[0]["depot_code"] == 1321503094
        assert records[0]["address"] == "東京都杉並区＊"
        assert records[0]["city"] == "杉並区"
        assert records[0]["phone_number"] == "0422-28-5051"
        assert records[0]["fax_number"] == "0422-28-5052"
        assert records[0]["hp"] == ""
        assert (
            records[0]["service_type"] == "共同生活援助（グループホーム）[総合支援法]"
        )
        assert records[0]["capacity"] == 7  # Single capacity with text suffix
        assert records[0]["staff_count"] == 0
        assert records[0]["opened_date"] == "2019-10-01"
        assert records[0]["is_active"] is True
        assert records[0]["update_date"] == "2021年11月9日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311000598&SVCSBR_CD=031&NAME=%E3%82%A2%E3%82%B9%E3%82%AF%E3%83%90%E3%82%A4%E3%83%AA%E3%83%B3%E3%82%AC%E3%83%AB%E4%BF%9D%E8%82%B2%E5%9C%92%E3%82%84%E3%81%8F%E3%82%82&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[1]["corporation_name"] == "株式会社日本保育サービス"
        assert records[1]["depot_name"] == "アスクバイリンガル保育園やくも"
        assert records[1]["depot_code"] == 0  # 事業所番号 is missing
        assert (
            records[1]["address"]
            == "152-0023 東京都目黒区八雲3丁目12番10号 パークヴィラ八雲101号室"
        )  # (152-0023 東京都目黒区八雲3丁目12番10号 \xa0\xa0パークヴィラ八雲101号室) Remove whitespace
        assert records[1]["city"] == "目黒区"
        assert records[1]["phone_number"] == "03-5731-0315"
        assert records[1]["fax_number"] == "03-6421-3253"
        assert records[1]["hp"] == "https://www.nihonhoiku.co.jp"
        assert records[1]["service_type"] == "保育所(認可保育所)"
        assert records[1]["capacity"] == 80  # Categorized capacity with text suffix
        assert records[1]["staff_count"] == 25
        assert records[1]["opened_date"] == "2010-04-01"
        assert records[1]["is_active"] is True
        assert records[1]["update_date"] == "2024年7月31日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311001038&SVCSBR_CD=031&NAME=%E3%81%84%E3%81%84%E3%81%BB%E3%81%84%E3%81%8F%E3%81%88%E3%82%93%E8%87%AA%E7%94%B1%E3%81%8C%E4%B8%98&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[2]["corporation_name"] == "アイカタ株式会社"
        assert records[2]["depot_name"] == "いいほいくえん自由が丘"
        assert records[2]["depot_code"] == 0  # 事業所番号 is missing
        assert records[2]["address"] == "152-0034 東京都目黒区緑が丘2丁目16番11号"
        assert records[2]["city"] == "目黒区"
        assert records[2]["phone_number"] == "03-5731-4040"
        assert records[2]["fax_number"] == "03-5731-4041"
        assert records[2]["hp"] == ""
        assert records[2]["service_type"] == "保育所(認可保育所)"
        assert records[2]["capacity"] == 50
        assert records[2]["staff_count"] == 22  # 合計: 21 (incorrect total)
        assert records[2]["opened_date"] == "2019-04-01"
        assert records[2]["is_active"] is True
        assert records[2]["update_date"] == "2019年10月17日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1321100159&SVCSBR_CD=113&NAME=%E9%BB%8E%E6%98%8E%E5%AF%AE&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[3]["corporation_name"] == "社会福祉法人黎明会"
        assert records[3]["depot_name"] == "黎明寮"
        assert records[3]["depot_code"] == 0  # 事業所番号 is missing
        assert records[3]["address"] == "187-0032 東京都小平市小川町1丁目485番"
        assert records[3]["city"] == "小平市"
        assert records[3]["phone_number"] == "042-341-0336"
        assert records[3]["fax_number"] == "042-345-5463"
        assert records[3]["hp"] == ""
        assert records[3]["service_type"] == "救護施設"
        assert records[3]["capacity"] == 100
        assert records[3]["staff_count"] == 40  # 合計 is missing
        assert records[3]["opened_date"] == "1957-10-01"
        assert records[3]["is_active"] is True
        assert records[3]["update_date"] == "2003年3月13日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311001028&SVCSBR_CD=031&NAME=%E3%81%97%E3%81%84%E3%81%AE%E3%81%8D%E4%BF%9D%E8%82%B2%E5%9C%92&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[4]["corporation_name"] == "社会福祉法人さがみ愛育会"
        assert records[4]["depot_name"] == "しいのき保育園"
        assert records[4]["depot_code"] == 0  # 事業所番号 is missing
        assert records[4]["address"] == "153-0053 東京都目黒区五本木2丁目20番20号"
        assert records[4]["city"] == "目黒区"
        assert records[4]["phone_number"] == "03-5725-1733"
        assert records[4]["fax_number"] == "03-5722-0311"
        assert records[4]["hp"] == ""
        assert records[4]["service_type"] == "保育所(認可保育所)"
        assert records[4]["capacity"] == 146
        assert records[4]["staff_count"] == 45  # Only 合計 is present
        assert records[4]["opened_date"] == "2019-04-01"
        assert records[4]["is_active"] is True
        assert records[4]["update_date"] == "2025年12月23日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311000291&SVCSBR_CD=114&NAME=%E6%9D%B1%E3%81%8C%E4%B8%98%E8%8D%98&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[5]["corporation_name"] == "社会福祉法人東京援護協会"
        assert records[5]["depot_name"] == "東が丘荘"
        assert records[5]["depot_code"] == 0  # 事業所番号 is missing
        assert records[5]["address"] == "東京都目黒区＊"
        assert records[5]["city"] == "目黒区"  # 目黒区＊ (with special character)
        assert records[5]["phone_number"] == ""
        assert records[5]["fax_number"] == ""
        assert records[5]["hp"] == ""
        assert records[5]["service_type"] == "更生施設"
        assert records[5]["capacity"] == 0  # 定員 is missing
        assert records[5]["staff_count"] == 0  # 職員数 is missing
        assert records[5]["opened_date"] is None
        assert records[5]["is_active"] is True
        assert records[5]["update_date"] == "2023年6月22日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1311901242&SVCSBR_CD=342&NAME=%E6%9D%B1%E4%BA%AC%E9%83%BD%E6%9D%BF%E6%A9%8B%E5%8C%BA%E7%AB%8B%E8%B5%A4%E5%A1%9A%E7%A6%8F%E7%A5%89%E5%9C%92&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[6]["corporation_name"] == "社会福祉法人嬉泉"
        assert records[6]["depot_name"] == "東京都板橋区立赤塚福祉園"
        assert records[6]["depot_code"] == 1311900052  # 事業所指定番号等 header
        assert records[6]["address"] == "175-0092 東京都板橋区赤塚6丁目19番14号"
        assert records[6]["city"] == "板橋区"
        assert records[6]["phone_number"] == "03-5383-5741"
        assert records[6]["fax_number"] == "03-5383-5749"
        assert records[6]["hp"] == ""
        assert records[6]["service_type"] == "就労継続支援（Ｂ型）[総合支援法]"
        assert records[6]["capacity"] == 40
        assert records[6]["staff_count"] == 8
        assert (
            records[6]["opened_date"] == "1993-04-01"
        )  # 平成5年4月1日設立 (Era Format)
        assert records[6]["is_active"] is True
        assert records[6]["update_date"] == "2020年10月12日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1310300981&SVCSBR_CD=411&NAME=%E3%83%A1%E3%83%AB%E3%82%B1%E3%82%A2%E3%81%BF%E3%81%AA%E3%81%A8%E3%82%BB%E3%83%B3%E3%82%BF%E3%83%BC&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert (
            records[7]["corporation_name"] == "特定非営利活動法人メルケアみなとセンター"
        )
        assert records[7]["depot_name"] == "メルケアみなとセンター"
        assert records[7]["depot_code"] == 1350300370  # 事業所指定番号等 header
        assert (
            records[7]["address"] == "105-0004 東京都港区新橋4丁目27番4号 新橋吉樹ビル"
        )
        assert records[7]["city"] == "港区"
        assert records[7]["phone_number"] == "03-6205-4077"  # 事業所電話 header
        assert records[7]["fax_number"] == "03-6205-4070"  # 事業所FAX header
        assert records[7]["hp"] == "https://www.melcare.jp/"
        assert records[7]["service_type"] == "児童発達支援[児童福祉法]"
        assert records[7]["capacity"] == 0
        assert records[7]["staff_count"] == 0
        assert records[7]["opened_date"] == "2019-04-01"
        assert records[7]["is_active"] is True
        assert records[7]["update_date"] == "2023年10月4日"

        # https://www.fukunavi.or.jp/fukunavi/controller?actionID=jgytik&cmd=jgy_dt&JGY_CD=1310200210&SVCSBR_CD=001&NAME=%E7%89%B9%E5%88%A5%E9%A4%8A%E8%AD%B7%E8%80%81%E4%BA%BA%E3%83%9B%E3%83%BC%E3%83%A0%E6%99%B4%E6%B5%B7%E8%8B%91&AREA1=&AREA2=&AREA3=&NAME2=&AREA4=&AREA5=&AREA6=&HYK_FLG=&SCHSVCSBRCD1=&SCHSVCSBRCD2=&SCHSVCSBRCD3=&SVCDBRCD=&SVCSBRCDALL=&STEP_SVCSBRCD=&SLFHYK_FLG=&SVCPLN_FLG=&beforeID=&SLFHYK_FLG=&AREA=&JOIN_FL=&DVSSUB_CD=&MODE=&COUNT=&OCP_FL=&EMP_FL=&STENO=
        assert records[8]["corporation_name"] == "社会福祉法人トーリケアネット"
        assert records[8]["depot_name"] == "特別養護老人ホーム晴海苑"
        assert records[8]["depot_code"] == 1370201368  # 指定番号(介護) header
        assert records[8]["address"] == "104-0053 東京都中央区晴海1丁目1番26号"
        assert records[8]["city"] == "中央区"
        assert records[8]["phone_number"] == "03-3533-7148"  # 事業所電話番号 header
        assert records[8]["fax_number"] == "03-3533-7149"  # 事業所FAX番号 header
        assert records[8]["hp"] == "https://www.harumien.or.jp"
        assert records[8]["service_type"] == "指定介護老人福祉施設"
        assert records[8]["capacity"] == 45
        assert records[8]["staff_count"] == 27  # Incorrect 合計
        assert records[8]["opened_date"] == "2007-05-01"
        assert records[8]["is_active"] is True
        assert records[8]["update_date"] == "2026年5月1日"
