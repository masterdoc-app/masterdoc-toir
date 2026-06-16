#!/usr/bin/env python3
"""One search campaign with Intent H1–H3 ad groups (replaces 3 separate Intent campaigns)."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "fixa", ROOT / "scripts" / "fixaverse_create_campaigns.py"
)
fixa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixa)

G4_IMAGE = ROOT / "landing" / "assets" / "ad-proposals-v2" / "g4-brand-minimal-1080x1080.png"

CAMPAIGN_NAME = "fixaverse | Search | Intent Unified | 2026-06-16"
WEEKLY_RUB = 1500

OLD_INTENT_IDS = [710732017, 710732021, 710732026]

BASE_NEGATIVES = list(dict.fromkeys([
    "бесплатно", "скачать", "курс", "обучение", "ваканс", "резюме", "диплом",
    "своими руками", "видео", "youtube", "автомобил", "легков", "грузовик",
    "огнетушител", "лифт", "стиральн", "кондиционер быт", "ремонт телефон",
    "зарплат", "гост р", "норма времени", "журнал excel", "шаблон", "бланк",
    "журнал", "образец", "гост", "акт ", "должностная", "инструкция",
    "автосервис", "выставка", "ibm", "maximo", "erp",
    "аналог", "бесплатная", "оргтехник", "рейтинг",
    "грузовых автомобил", "проката",
    "атп", "авторемонт", "шиноремонт", "методичка", "карев",
    "технологическая карта", "паспорт", "норматив", "lean", "5s",
    "бережлив", "6s", "tpm", "стоа", "шиномонтаж", "двигател", "электродвигател",
    "змз", "нормочас", "турбо", "какова", "что такое", "основные положения",
    "методы ремонта", "виды ремонтов", "по какому", "нормативному", "техкарт",
    "дефектная", "енир", "mes", "cimco", "harvesting", "охрана труда",
    "генератор", "микас", "rbm",
    "торрент", "торр", "кряк", "расшифровка", "вятгсха", "что это", "книга",
    "пират", "скачать бесплатно",
    # wave 5 SQR academic noise
    "алгоритм", "колобродов", "трансформатор", "для чего нужно", "ответ",
    "уточненный", "холодильн", "электротехническ", "вопрос",
    # group extras merged at campaign level
    "башенный", "кран", "электротал", "excel", "оргтехник", "медицинск",
    "1с", "1c", "деснол", "купить",
]))

GROUPS = [
    {
        "slug": "planning",
        "group": "Intent | H2 planning",
        "hypothesis": "H2 — планирование ППР и графики ремонтов",
        "keywords": [
            "планирование ремонтов оборудования",
            "планирование технического обслуживания и ремонта оборудования",
            "система планирования тоир",
            "организация планирования ремонтов оборудования",
        ],
        "copy": "toir",
        "ad": {
            "Title": "График ППР и планирование ремонтов",
            "Title2": "Система ТОиР на основе ИИ",
            "Text": "Fixaverse: планирование ТО и ремонтов. Заказ-наряды, учёт и ИИ-copilot.",
        },
    },
    {
        "slug": "uchet",
        "group": "Intent | H1 uchet",
        "hypothesis": "H1 — учёт ТО и обслуживания (замена Excel)",
        "keywords": [
            "учет технического обслуживания оборудования",
            "учет технического обслуживания и ремонта оборудования",
            "программа для обслуживания оборудования",
            "программа для ремонтов и обслуживания оборудования",
        ],
        "copy": "uchet",
        "ad": {
            "Title": "Программа учёта ремонтов",
            "Title2": "Система ТОиР на заводе",
            "Text": "Fixaverse: учёт ремонтов и ТО оборудования. Заказ-наряды и ИИ-copilot в цеху.",
        },
    },
    {
        "slug": "buy",
        "group": "Intent | H3 buy",
        "hypothesis": "H3 — внедрение / покупка / цифровизация",
        "keywords": [
            "внедрение системы тоир",
            "цифровизация тоир",
            "автоматизация тоир",
            "автоматизированная система тоир",
        ],
        "copy": "auto",
        "ad": {
            "Title": "Внедрение и цифровизация ТОиР",
            "Title2": "Автоматизация обслуживания",
            "Text": "Fixaverse: внедрение ТОиР на предприятии. Copilot для техников, on-premise.",
        },
    },
]


def ensure_ad_group_named(campaign_id: int, name: str) -> int:
    got = fixa.call(
        "adgroups",
        "get",
        {
            "SelectionCriteria": {"CampaignIds": [campaign_id]},
            "FieldNames": ["Id", "Name"],
        },
    )
    for g in got.get("AdGroups", []):
        if g.get("Name") == name:
            return g["Id"]

    add = fixa.call(
        "adgroups",
        "add",
        {
            "AdGroups": [{
                "Name": name,
                "CampaignId": campaign_id,
                "RegionIds": fixa.REGION_IDS,
            }]
        },
    )
    row = add["AddResults"][0]
    if row.get("Errors"):
        raise RuntimeError(f"adgroups.add: {row['Errors']}")
    return row["Id"]


def create_unified_campaign(template: dict) -> int:
    existing = fixa.find_campaign(CAMPAIGN_NAME)
    if existing:
        return existing

    today = date.today().isoformat()
    settings = [
        s for s in template["TextCampaign"]["Settings"]
        if s["Option"] in fixa.ALLOWED_SETTINGS
    ]
    for s in settings:
        if s["Option"] == "ADD_METRICA_TAG":
            s["Value"] = "NO"

    body = {
        "Name": CAMPAIGN_NAME,
        "StartDate": today,
        "TimeZone": template["TimeZone"],
        "TimeTargeting": template["TimeTargeting"],
        "NegativeKeywords": {"Items": BASE_NEGATIVES},
        "TextCampaign": {
            "BiddingStrategy": {
                "Search": {
                    "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                    "WbMaximumClicks": {
                        "WeeklySpendLimit": fixa.rub_to_micros(WEEKLY_RUB),
                        "BidCeiling": fixa.rub_to_micros(fixa.AVG_CPC_RUB),
                    },
                },
                "Network": {"BiddingStrategyType": "SERVING_OFF"},
            },
            "CounterIds": {"Items": [fixa.METRIKA_COUNTER]},
            "Settings": settings,
            "TrackingParams": (
                "utm_source=yandex&utm_medium=cpc"
                "&utm_campaign={campaign_id}&utm_content={ad_id}&utm_term={keyword}"
            ),
        },
    }
    add = fixa.call("campaigns", "add", {"Campaigns": [body]})
    row = add["AddResults"][0]
    if row.get("Errors"):
        raise RuntimeError(f"campaigns.add: {row['Errors']}")
    return row["Id"]


def ensure_keywords(ad_group_id: int, keywords: list[str]) -> None:
    kws = fixa.call(
        "keywords",
        "get",
        {
            "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
            "FieldNames": ["Keyword"],
        },
    )
    existing = {k["Keyword"] for k in kws.get("Keywords", [])}
    missing = [k for k in keywords if k not in existing]
    if missing:
        fixa.call(
            "keywords",
            "add",
            {"Keywords": [{"AdGroupId": ad_group_id, "Keyword": k} for k in missing]},
        )
    fixa.restrict_autotargeting(ad_group_id)


def add_ad(ad_group_id: int, href: str, image_hash: str, ad: dict) -> int:
    fields = {
        "Title": ad["Title"],
        "Title2": ad["Title2"],
        "Text": ad["Text"],
        "Href": href,
        "Mobile": "YES",
        "AdImageHash": image_hash,
    }
    add = fixa.call("ads", "add", {"Ads": [{"AdGroupId": ad_group_id, "TextAd": fields}]})
    row = add["AddResults"][0]
    if row.get("Errors"):
        raise RuntimeError(f"ads.add: {row['Errors']}")
    return row["Id"]


def setup_group(campaign_id: int, spec: dict, image_hash: str) -> dict:
    agid = ensure_ad_group_named(campaign_id, spec["group"])
    ensure_keywords(agid, spec["keywords"])

    suffix = f"?copy={spec['copy']}"
    href = fixa.landing_href(suffix, campaign_id)

    ads = fixa.list_ads(agid)
    if ads:
        ad_id = ads[0]["Id"]
    else:
        ad_id = add_ad(agid, href, image_hash, spec["ad"])
        fixa.call("ads", "moderate", {"SelectionCriteria": {"Ids": [ad_id]}})

    return {
        "slug": spec["slug"],
        "hypothesis": spec["hypothesis"],
        "adGroupId": agid,
        "adGroupName": spec["group"],
        "adId": ad_id,
        "href": href,
        "keywords": spec["keywords"],
        "ad": spec["ad"],
    }


def suspend_old_intent() -> list[dict]:
    res = fixa.call("campaigns", "suspend", {"SelectionCriteria": {"Ids": OLD_INTENT_IDS}})
    out = []
    for row in res.get("SuspendResults", []):
        out.append({"campaignId": row["Id"], "errors": row.get("Errors", [])})
    return out


def main() -> None:
    if not fixa.TOKEN:
        print("ERROR: YANDEX_DIRECT_TOKEN missing", file=sys.stderr)
        sys.exit(1)

    template = fixa.get_template()
    image_hash = fixa.upload_image(G4_IMAGE, "fixaverse-g4-intent-unified")

    campaign_id = create_unified_campaign(template)
    groups = [setup_group(campaign_id, spec, image_hash) for spec in GROUPS]

    fixa.call("campaigns", "resume", {"SelectionCriteria": {"Ids": [campaign_id]}})
    suspended = suspend_old_intent()

    result = {
        "campaign": {
            "name": CAMPAIGN_NAME,
            "campaignId": campaign_id,
            "weeklyBudgetRub": WEEKLY_RUB,
            "imageHash": image_hash,
            "negativeKeywordsCount": len(BASE_NEGATIVES),
        },
        "groups": groups,
        "suspendedOldIntent": suspended,
        "replacedCampaignIds": OLD_INTENT_IDS,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
