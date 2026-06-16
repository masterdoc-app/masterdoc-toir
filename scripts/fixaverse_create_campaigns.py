#!/usr/bin/env python3
"""Create Fixaverse Direct experiment campaigns: copy A/B + creative A/B."""
from __future__ import annotations

import base64
import io
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DIRECT_ROOT = ROOT.parent.parent / "Direct"
load_dotenv(DIRECT_ROOT / ".env")
load_dotenv(ROOT / ".env")

TOKEN = os.getenv("YANDEX_DIRECT_TOKEN", "").strip()
CLIENT_LOGIN = os.getenv("YANDEX_DIRECT_CLIENT_LOGIN", "").strip()
BASE = (
    "https://api-sandbox.direct.yandex.com/json/v5"
    if os.getenv("YANDEX_DIRECT_SANDBOX", "").lower() in ("1", "true", "yes")
    else "https://api.direct.yandex.com/json/v5"
)

TEMPLATE_CID = 710364627
METRIKA_COUNTER = 109561586
GOAL_DEMO = 564496375
WEEKLY_RUB = 3500
AVG_CPC_RUB = 120
REGION_IDS = [225]

ASSETS = ROOT / "landing" / "assets"

NEGATIVES_CAMPAIGN = list(dict.fromkeys([
    "бесплатно", "скачать", "курс", "обучение", "ваканс", "резюме", "диплом",
    "своими руками", "видео", "youtube", "автомобил", "легков", "грузовик",
    "огнетушител", "лифт", "стиральн", "кондиционер быт", "ремонт телефон",
    "зарплат", "гост р", "норма времени", "журнал excel", "шаблон", "бланк",
    # wave 2 from search queries (710364627)
    "журнал", "образец", "гост", "акт ", "должностная", "инструкция",
    "автосервис", "выставка", "ibm", "maximo", "erp",
    "купить", "аналог", "бесплатная", "оргтехник", "рейтинг",
    "грузовых автомобил", "проката",
    # wave 3 from SQR Copy AB 12–14.06 (autotargeting noise)
    "5s", "lean", "атп", "авторемонт", "методичка", "норматив", "паспорт",
    "технологическая карта", "шиноремонт", "карев",
    "бережлив", "6s", "tpm", "стоа", "шиномонтаж", "двигател", "электродвигател",
    "змз", "нормочас", "турбо", "какова", "что такое", "основные положения",
    "методы ремонта", "виды ремонтов", "по какому", "нормативному", "техкарт",
    "дефектная", "енир", "mes", "cimco", "harvesting", "охрана труда",
    "генератор", "микас", "rbm",
    # wave 4 SQR 15.06 (1с/пиратка/учеба)
    "торрент", "торр", "кряк", "расшифровка", "вятгсха", "что это", "книга",
    "пират", "скачать бесплатно",
]))

KEYWORDS = [
    "система тоир",
    "программа тоир",
    "программа учета ремонтов",
    "программа учета ремонта оборудования",
    "автоматизация технического обслуживания и ремонта",
    "программа для обслуживания оборудования",
    "системы управления техническим обслуживанием и ремонтами",
    "программа тоир для предприятия",
    "программа автоматизации технического обслуживания",
    "программы учета ремонта оборудования",
    "система контроля простоя оборудования",
]

AD_COPY = {
    "Title": "Система ТОиР на основе ИИ",
    "Title2": "Программа учёта ремонтов",
    "Text": "Fixaverse: ТОиР на заводе. Заказ-наряды, учёт ремонтов и ИИ-copilot.",
    "Mobile": "YES",
}

COPY_ADS = [
    {"slug": "A0-control", "suffix": ""},
    {"slug": "A1-toir", "suffix": "?copy=toir"},
    {"slug": "A2-uchet", "suffix": "?copy=uchet"},
    {"slug": "A3-auto", "suffix": "?copy=auto"},
]

CREATIVE_ADS = [
    {"slug": "C1-square-trucks", "image": ASSETS / "ad-direct-1080x1080.png"},
    {"slug": "C2-wide-trucks", "image": ASSETS / "ad-direct-1080x607.png"},
    {"slug": "C3-square-copilot", "image": None},  # built at runtime
]

ALLOWED_SETTINGS = {
    "EXCLUDE_PAUSED_COMPETING_ADS", "ADD_OPENSTAT_TAG", "ADD_METRICA_TAG",
    "ADD_TO_FAVORITES", "ENABLE_AREA_OF_INTEREST_TARGETING",
    "ENABLE_CURRENT_AREA_TARGETING", "ENABLE_REGULAR_AREA_TARGETING",
    "ENABLE_SITE_MONITORING", "ENABLE_BEHAVIORAL_TARGETING", "ENABLE_AUTOFOCUS",
    "REQUIRE_SERVICING", "ENABLE_RELATED_KEYWORDS", "ENABLE_EXTENDED_AD_TITLE",
    "MAINTAIN_NETWORK_CPC", "ENABLE_COMPANY_INFO",
    "CAMPAIGN_EXACT_PHRASE_MATCHING_ENABLED", "ALTERNATIVE_TEXTS_ENABLED",
}


def headers() -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    if CLIENT_LOGIN:
        h["Client-Login"] = CLIENT_LOGIN
    return h


def call(service: str, method: str, params: dict) -> dict:
    r = requests.post(
        f"{BASE}/{service}",
        headers=headers(),
        json={"method": method, "params": params},
        timeout=90,
    )
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"{service}.{method}: {data['error']}")
    result = data.get("result", {})
    if result.get("Errors"):
        raise RuntimeError(f"{service}.{method} Errors: {result['Errors']}")
    return result


def rub_to_micros(rub: float) -> int:
    return int(round(rub * 1_000_000))


def find_campaign(name: str) -> int | None:
    got = call(
        "campaigns",
        "get",
        {
            "SelectionCriteria": {"States": ["ON", "OFF", "SUSPENDED"]},
            "FieldNames": ["Id", "Name"],
        },
    )
    for c in got.get("Campaigns", []):
        if c.get("Name") == name:
            return c["Id"]
    return None


def build_time_targeting(start_hour: int = 8, end_hour: int = 20) -> dict:
    """Mon–Fri business hours only; no nights or weekends."""
    def day_line(day: int) -> str:
        hours = [0] * 24
        if day <= 5:
            for h in range(start_hour, end_hour):
                hours[h] = 100
        return f"{day}," + ",".join(str(x) for x in hours)

    return {
        "Schedule": {"Items": [day_line(d) for d in range(1, 8)]},
        "ConsiderWorkingWeekends": "NO",
        "HolidaysSchedule": {
            "SuspendOnHolidays": "NO",
            "BidPercent": 100,
            "StartHour": start_hour,
            "EndHour": end_hour,
        },
    }


def get_template() -> dict:
    got = call(
        "campaigns",
        "get",
        {
            "SelectionCriteria": {"Ids": [TEMPLATE_CID]},
            "FieldNames": ["TimeZone"],
            "TextCampaignFieldNames": ["Settings"],
        },
    )
    campaign = got["Campaigns"][0]
    campaign["TimeTargeting"] = build_time_targeting()
    return campaign


def build_copilot_square(path: Path) -> None:
    from PIL import Image

    src = ASSETS / "hero-cmms.webp"
    if not src.exists():
        raise FileNotFoundError(src)
    hero = Image.open(src).convert("RGB")
    out_w = out_h = 1080
    bg = (10, 22, 40)
    canvas = Image.new("RGB", (out_w, out_h), bg)
    margin = int(out_w * 0.06)
    max_h = out_h - 2 * margin
    max_w = out_w - 2 * margin
    r = hero.width / hero.height
    nh = max_h
    nw = int(nh * r)
    if nw > max_w:
        nw = max_w
        nh = int(nw / r)
    im = hero.resize((nw, nh), Image.Resampling.LANCZOS)
    x, y = (out_w - nw) // 2, (out_h - nh) // 2
    canvas.paste(im, (x, y))
    canvas.save(path, "PNG", optimize=True)


def upload_image(path: Path, name: str) -> str:
    raw = path.read_bytes()
    # Direct accepts PNG/JPEG base64
    add = call(
        "adimages",
        "add",
        {"AdImages": [{"ImageData": base64.b64encode(raw).decode("ascii"), "Name": name}]},
    )
    row = add["AddResults"][0]
    if row.get("Errors"):
        raise RuntimeError(f"adimages.add: {row['Errors']}")
    return row["AdImageHash"]


def restrict_autotargeting(ad_group_id: int) -> None:
    """Search-only: нельзя suspend/delete ---autotargeting; оставляем только целевые запросы."""
    kws = call(
        "keywords",
        "get",
        {
            "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
            "FieldNames": ["Id", "Keyword"],
        },
    )
    auto_ids = [k["Id"] for k in kws.get("Keywords", []) if k.get("Keyword") == "---autotargeting"]
    for kid in auto_ids:
        call(
            "keywords",
            "update",
            {
                "Keywords": [{
                    "Id": kid,
                    "AutotargetingSettings": {
                        "Categories": {
                            "Exact": "YES",
                            "Narrow": "NO",
                            "Alternative": "NO",
                            "Accessory": "NO",
                            "Broader": "NO",
                        },
                        "BrandOptions": {
                            "WithoutBrands": "NO",
                            "WithAdvertiserBrand": "YES",
                            "WithCompetitorsBrand": "NO",
                        },
                    },
                }]
            },
        )


def landing_href(suffix: str, campaign_id: int) -> str:
    base = "https://fixaverse.ru/"
    utm = (
        "utm_source=yandex&utm_medium=cpc"
        f"&utm_campaign={campaign_id}"
        "&utm_content={ad_id}&utm_term={keyword}"
    )
    if suffix:
        q = suffix.lstrip("?")
        return f"{base}?{q}&{utm}"
    return f"{base}?{utm}"


def create_campaign_shell(name: str, template: dict) -> int:
    existing = find_campaign(name)
    if existing:
        return existing

    today = date.today().isoformat()
    settings = [
        s for s in template["TextCampaign"]["Settings"]
        if s["Option"] in ALLOWED_SETTINGS
    ]
    # Prefer no auto metrica tag duplication (site has tag)
    for s in settings:
        if s["Option"] == "ADD_METRICA_TAG":
            s["Value"] = "NO"

    body = {
        "Name": name,
        "StartDate": today,
        "TimeZone": template["TimeZone"],
        "TimeTargeting": template["TimeTargeting"],
        "NegativeKeywords": {"Items": NEGATIVES_CAMPAIGN},
        "TextCampaign": {
            "BiddingStrategy": {
                "Search": {
                    "BiddingStrategyType": "WB_MAXIMUM_CLICKS",
                    "WbMaximumClicks": {
                        "WeeklySpendLimit": rub_to_micros(WEEKLY_RUB),
                        "BidCeiling": rub_to_micros(AVG_CPC_RUB),
                    },
                },
                "Network": {"BiddingStrategyType": "SERVING_OFF"},
            },
            "CounterIds": {"Items": [METRIKA_COUNTER]},
            "Settings": settings,
            "TrackingParams": (
                "utm_source=yandex&utm_medium=cpc"
                "&utm_campaign={campaign_id}&utm_content={ad_id}&utm_term={keyword}"
            ),
        },
    }
    add = call("campaigns", "add", {"Campaigns": [body]})
    row = add["AddResults"][0]
    if row.get("Errors"):
        raise RuntimeError(f"campaigns.add: {row['Errors']}")
    return row["Id"]


def ensure_ad_group(campaign_id: int, name: str) -> int:
    got = call(
        "adgroups",
        "get",
        {
            "SelectionCriteria": {"CampaignIds": [campaign_id]},
            "FieldNames": ["Id", "Name"],
        },
    )
    groups = got.get("AdGroups", [])
    if groups:
        return groups[0]["Id"]

    add = call(
        "adgroups",
        "add",
        {
            "AdGroups": [{
                "Name": name,
                "CampaignId": campaign_id,
                "RegionIds": REGION_IDS,
            }]
        },
    )
    row = add["AddResults"][0]
    if row.get("Errors"):
        raise RuntimeError(f"adgroups.add: {row['Errors']}")
    return row["Id"]


def ensure_keywords(ad_group_id: int) -> None:
    kws = call(
        "keywords",
        "get",
        {
            "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
            "FieldNames": ["Keyword"],
        },
    )
    existing = {k["Keyword"] for k in kws.get("Keywords", [])}
    missing = [k for k in KEYWORDS if k not in existing]
    if missing:
        call(
            "keywords",
            "add",
            {"Keywords": [{"AdGroupId": ad_group_id, "Keyword": k} for k in missing]},
        )
    restrict_autotargeting(ad_group_id)


def list_ads(ad_group_id: int) -> list[dict]:
    got = call(
        "ads",
        "get",
        {
            "SelectionCriteria": {"AdGroupIds": [ad_group_id]},
            "FieldNames": ["Id", "AdGroupId", "Status", "State"],
            "TextAdFieldNames": ["Title", "Href", "AdImageHash"],
        },
    )
    return got.get("Ads", [])


def add_ad(ad_group_id: int, href: str, image_hash: str | None = None) -> int:
    fields = dict(AD_COPY)
    fields["Href"] = href
    if image_hash:
        fields["AdImageHash"] = image_hash
    add = call("ads", "add", {"Ads": [{"AdGroupId": ad_group_id, "TextAd": fields}]})
    row = add["AddResults"][0]
    if row.get("Errors"):
        raise RuntimeError(f"ads.add: {row['Errors']}")
    return row["Id"]


def setup_copy_campaign(template: dict, image_hash: str) -> dict:
    name = "fixaverse | Search | Copy AB | 2026-06-12"
    cid = create_campaign_shell(name, template)
    agid = ensure_ad_group(cid, "TOiR core | copy test")
    ensure_keywords(agid)

    existing = list_ads(agid)
    ads_out = []
    if len(existing) >= len(COPY_ADS):
        ads_out = [{"adId": a["Id"], "href": a.get("TextAd", {}).get("Href")} for a in existing]
    else:
        for spec in COPY_ADS:
            href = landing_href(spec["suffix"], cid)
            ad_id = add_ad(agid, href, image_hash)
            call("ads", "moderate", {"SelectionCriteria": {"Ids": [ad_id]}})
            ads_out.append({"slug": spec["slug"], "adId": ad_id, "href": href})

    call("campaigns", "resume", {"SelectionCriteria": {"Ids": [cid]}})
    return {"campaignId": cid, "adGroupId": agid, "ads": ads_out, "name": name}


def setup_creative_campaign(template: dict) -> dict:
    name = "fixaverse | Search | Creative AB | 2026-06-12"
    cid = create_campaign_shell(name, template)
    agid = ensure_ad_group(cid, "TOiR core | creative test")
    ensure_keywords(agid)

    copilot_path = ASSETS / "ad-direct-copilot-1080x1080.png"
    build_copilot_square(copilot_path)
    CREATIVE_ADS[2]["image"] = copilot_path

    existing = list_ads(agid)
    ads_out = []
    if len(existing) >= len(CREATIVE_ADS):
        ads_out = [{"adId": a["Id"]} for a in existing]
    else:
        href = landing_href("", cid)
        for spec in CREATIVE_ADS:
            img_hash = upload_image(spec["image"], f"fixaverse-{spec['slug']}")
            ad_id = add_ad(agid, href, img_hash)
            call("ads", "moderate", {"SelectionCriteria": {"Ids": [ad_id]}})
            ads_out.append({
                "slug": spec["slug"],
                "adId": ad_id,
                "href": href,
                "adImageHash": img_hash,
                "image": str(spec["image"].name),
            })

    call("campaigns", "resume", {"SelectionCriteria": {"Ids": [cid]}})
    return {"campaignId": cid, "adGroupId": agid, "ads": ads_out, "name": name}


def main() -> None:
    if not TOKEN:
        print("ERROR: YANDEX_DIRECT_TOKEN missing", file=sys.stderr)
        sys.exit(1)

    template = get_template()
    shared_hash = upload_image(ASSETS / "ad-direct-1080x1080.png", "fixaverse-copy-ab-square")

    results = {
        "copyAb": setup_copy_campaign(template, shared_hash),
        "creativeAb": setup_creative_campaign(template),
        "wordstatNote": "Keywords validated via Wordstat MCP 2026-06-12",
        "weeklyBudgetRub": WEEKLY_RUB,
        "avgCpcRub": AVG_CPC_RUB,
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
