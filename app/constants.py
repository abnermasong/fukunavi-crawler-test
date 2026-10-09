# CORPORATION CRAWLER CONSTANTS

CORPORATION_BASE_URL = (
    "https://www.fukunavi.or.jp/fukunavi/controller?cmd=jgy&actionID=jgyhjn"
)

CORPORATION_CATEGORY_SERVICE_FILTER = {
    "21": {
        "name": "高齢者",
        "services": {
            "001": "指定介護老人福祉施設",
            "002": "介護老人保健施設",
            "009": "通所介護（介護予防）",
            "011": "短期入所生活介護（介護予防）",
            "013": "認知症対応型共同生活介護（介護予防）",
            "327": "認知症対応型通所介護",
            "328": "小規模多機能型居宅介護",
            "017": "養護老人ホーム",
        },
    },
    "22": {
        "name": "子ども・ひとり親",
        "services": {
            "031": "保育所(認可保育所)",
            "032": "認証保育所（Ａ・Ｂ型）",
            "332": "認定こども園",
            "448": "社会的養護自立支援拠点",
            "036": "母子生活支援施設",
            "040": "学童クラブ",
        },
    },
    "23": {
        "name": "障害者・児",
        "services": {
            "234": "居宅介護[総合支援法]",
            "235": "ショートステイ[総合支援法]",
            "337": "生活介護[総合支援法]",
            "340": "就労移行支援（一般型）[総合支援法]",
            "341": "就労継続支援（Ａ型）[総合支援法]",
            "342": "就労継続支援（Ｂ型）[総合支援法]",
            "344": "共同生活援助（グループホーム）[総合支援法]",
        },
    },
}

## ["21", "22", "23"]
CORPORATION_CATEGORY_CODES = list(CORPORATION_CATEGORY_SERVICE_FILTER.keys())

# EVALUATION AGENCY CRAWLER CONSTANTS

EVALUATION_AGENCY_BASE_URL = "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kknlst&pageId=before&HYKKKN_ID=&ROW=0&BNYCD=&AREA1=&AREA2=&AREA3=&NAME=&ORDERBY=1&ORDER=1&NSYKKN_NO1=&NSYKKN_NO2=&HYK_CHK=&HYK_SU=&HYK_SU_OLD=&HYK_SU_CHILD=&HYK_SU_HANDI=&HYK_SU_FEMALE=&HYK_SU_WELAARE=&NSY_CHK=&KYK_CHK="

## Column indices for evaluation agency index page table
CERT_NUMBER_COL = 0
ADDRESS_COL = 2
PHONE_NUMBER_COL = 3
TARGET_CATEGORIES_COL = 5
IS_ACCEPTING_COL = 7
IS_SOCIAL_CARE_COL = 6

# CORPORATION & EVALUATION AGENCY CRAWLER - SHARED CONSTANTS

CORPORATION_AGENCY_AREA_CODE_TO_NAME = {
    "0": "東京都２３区内",
    "1": "東京都市町村",
    "2": "東京都以外",
    "13361": "大島町",
    "13362": "利島村",
    "13363": "新島村",
    "13364": "神津島村",
    "13381": "三宅村",
    "13382": "御蔵島村",
    "13401": "八丈町",
    "13402": "青ヶ島村",
    "13421": "小笠原村",
}

## ["0", "1", "2", "13361", "13362", "13363", "13364", "13381", "13382", "13401", "13402", "13421"]
CORPORATION_AGENCY_AREA_CODES = list(CORPORATION_AGENCY_AREA_CODE_TO_NAME.keys())

# DEPOT & EVALUATION CRAWLER - SHARED CONSTANTS

DEPOT_EVALUATION_BASE_URL = "https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyksearch&cmd=svcdbr&S_MODE=service&MLT_AREA=&H_NAME=&J_NAME="

DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER = {
    "21": {
        "name": "高齢者",
        "services": {
            "001": "指定介護老人福祉施設【特別養護老人ホーム】",
            "013": "認知症対応型共同生活介護【認知症高齢者グループホーム】（介護予防含む）",
            "017": "養護老人ホーム",
            "019": "軽費老人ホーム(Ａ型)",
        },
    },
    "22": {
        "name": "子ども・ひとり親",
        "services": {
            "031": "認可保育所",
            "035": "乳児院",
            "036": "母子生活支援施設",
            "037": "児童養護施設",
            "042": "児童自立生活援助事業【自立援助ホーム】",
        },
    },
    "23": {
        "name": "障害者・児",
        "services": {
            "342": "就労継続支援Ｂ型",
            "344": "共同生活援助（グループホーム）",
            "415": "放課後等デイサービス",
            "427": "福祉型障害児入所施設（旧ろうあ児施設）",
            "428": "福祉型障害児入所施設（旧知的障害児施設）",
            "429": "福祉型障害児入所施設（旧第二種自閉症児施設）",
            "430": "医療型障害児入所施設（旧肢体不自由児施設）",
            "431": "医療型障害児入所施設（旧重症心身障害児施設）",
            "433": "宿泊型自立訓練",
            "998": "障害者支援施設",
        },
    },
    "24": {
        "name": "女性",
        "services": {"060": "女性自立支援施設"},
    },
    "25": {
        "name": "生活保護",
        "services": {"113": "救護施設"},
    },
}

## ["21", "22", "23", "24", "25"]
DEPOT_EVALUATION_CATEGORY_CODES = list(DEPOT_EVALUATION_CATEGORY_SERVICE_FILTER.keys())

BROAD_AREA_CODES_TO_SKIP = {
    "3": "東京都全域",
    "0": "東京都23区内",
    "1": "東京都市町村",
    "2": "東京都以外",
    "99999": "住所非公開",
}
