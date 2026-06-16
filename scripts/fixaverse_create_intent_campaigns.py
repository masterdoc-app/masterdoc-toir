#!/usr/bin/env python3
"""Create Fixaverse Intent hypothesis campaigns (500 RUB/week each)."""
from __future__ import annotations

import base64
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

COPY_AB_ID = 710704384
COPY_AB_WEEKLY_RUB = 1000
INTENT_WEEKLY_RUB = 500
G4_IMAGE = ROOT / "landing" / "assets" / "ad-proposals-v2" / "g4-brand-minimal-1080x1080.png"

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
    # wave 3 SQR 12–14.06
    "бережлив", "6s", "tpm", "стоа", "шиномонтаж", "двигател", "электродвигател",
    "змз", "нормочас", "турбо", "какова", "что такое", "основные положения",
    "методы ремонта", "виды ремонтов", "по какому", "нормативному", "техкарт",
    "дефектная", "енир", "mes", "cimco", "harvesting", "охрана труда",
    "генератор", "микас", "rbm",
    # wave 4 SQR 15.06
    "торрент", "торр", "кряк", "расшифровка", "вятгсха", "что это", "книга",
    "пират", "скачать бесплатно",
]))

INTENT_CAMPAIGNS = [
    {
        "slug": "planning",
        "name": "fixaverse | Search | Intent Planning | 2026-06-14",
        "group": "Intent | H2 planning",
        "hypothesis": "H2 — планирование ППР и графики ремонтов",
        "keywords": [
            "планирование ремонт оборудования",
            "планирование технического обслуживания и ремонта оборудования",
            "система планирования тоир",
            "организация планирования ремонтов оборудования",
        ],
        "extra_negatives": ["башенный", "кран", "электротал", "шиноремонт"],
        "allow_kupit": False,
    },
    {
        "slug": "uchet",
        "name": "fixaverse | Search | Intent Uchet | 2026-06-14",
        "group": "Intent | H1 uchet",
        "hypothesis": "H1 — учёт ТО и обслуживания (замена Excel)",
        "keywords": [
            "учет технического обслуживания оборудования",
            "учет технического обслуживания и ремонта оборудования",
            "программа для обслуживания оборудования",
            "программа для ремонтов и обслуживания оборудования",
        ],
        "extra_negatives": ["excel", "оргтехник", "медицинск"],
        "allow_kupit": False,
    },
    {
        "slug": "buy",
        "name": "fixaverse | Search | Intent Buy | 2026-06-14",
        "group": "Intent | H3 buy",
        "hypothesis": "H3 — внедрение / покупка / цифровизация",
        "keywords": [
            "внедрение системы тоир",
            "цифровизация тоир",
            "автоматизация тоир",
            "автоматизированная система тоир",
        ],
        "extra_negatives": ["1с", "1c", "деснол"],
        "allow_kupit": True,
    },
]


def negatives_for(spec: dict) -> list[str]:
    items = list(BASE_NEGATIVES)
    if not spec["allow_kupit"]:
        items.append("купить")
    items.extend(spec["extra_negatives"])
    return list(dict.fromkeys(items))


def create_intent_campaign(template: dict, spec: dict, weekly_rub: int) -> int:
    existing = fixa.find_campaign(spec["name"])
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
        "Name": spec["name"],
        "StartDate": today,
        "TimeZone": template["TimeZone"],
        "TimeTargeting": template["TimeTargeting"],
        "NegativeKeywords": {"Items": negatives_for(spec)},
        "TextCampaign": {
            "BiddingStrategy": {
                "Search": {
                    "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                    "WbMaximumClicks": {
                        "WeeklySpendLimit": fixa.rub_to_micros(weekly_rub),
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


def setup_intent(template: dict, spec: dict, image_hash: str) -> dict:
    cid = create_intent_campaign(template, spec, INTENT_WEEKLY_RUB)
    agid = fixa.ensure_ad_group(cid, spec["group"])
    ensure_keywords(agid, spec["keywords"])

    ads = fixa.list_ads(agid)
    if ads:
        ad_id = ads[0]["Id"]
    else:
        href = fixa.landing_href("", cid)
        ad_id = fixa.add_ad(agid, href, image_hash)
        fixa.call("ads", "moderate", {"SelectionCriteria": {"Ids": [ad_id]}})

    fixa.call("campaigns", "resume", {"SelectionCriteria": {"Ids": [cid]}})
    return {
        "slug": spec["slug"],
        "hypothesis": spec["hypothesis"],
        "campaignId": cid,
        "adGroupId": agid,
        "adId": ad_id,
        "keywords": spec["keywords"],
        "weeklyBudgetRub": INTENT_WEEKLY_RUB,
        "name": spec["name"],
    }


def reduce_copy_ab_budget() -> dict:
    micros = fixa.rub_to_micros(COPY_AB_WEEKLY_RUB)
    body = {
        "Id": COPY_AB_ID,
        "TextCampaign": {
            "BiddingStrategy": {
                "Search": {
                    "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                    "WbMaximumClicks": {
                        "WeeklySpendLimit": micros,
                        "BidCeiling": fixa.rub_to_micros(fixa.AVG_CPC_RUB),
                    },
                },
                "Network": {"BiddingStrategyType": "SERVING_OFF"},
            }
        },
    }
    res = fixa.call("campaigns", "update", {"Campaigns": [body]})
    row = res["UpdateResults"][0]
    if row.get("Errors"):
        raise RuntimeError(row["Errors"])
    return {"campaignId": COPY_AB_ID, "weeklyBudgetRub": COPY_AB_WEEKLY_RUB}


def main() -> None:
    if not fixa.TOKEN:
        print("ERROR: YANDEX_DIRECT_TOKEN missing", file=sys.stderr)
        sys.exit(1)

    template = fixa.get_template()
    image_hash = fixa.upload_image(G4_IMAGE, "fixaverse-g4-intent")

    results = {
        "note": "Intent campaigns test keywords; landing fixaverse.ru/ unchanged",
        "copyAbBudget": reduce_copy_ab_budget(),
        "intentCampaigns": [setup_intent(template, spec, image_hash) for spec in INTENT_CAMPAIGNS],
        "totalWeeklyRub": COPY_AB_WEEKLY_RUB + INTENT_WEEKLY_RUB * len(INTENT_CAMPAIGNS),
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
