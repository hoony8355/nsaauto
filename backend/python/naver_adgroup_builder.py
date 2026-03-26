"""Naver NCC API hierarchy helper with easy preview-first workflow.

사용자 관점에서 쉽게 구조를 잡을 수 있도록:
1) 템플릿 선택
2) 체크박스 수준의 분기 옵션 입력
3) 트리 미리보기 확인
4) 확정 후 API 실행

주의:
- 실제 엔드포인트/필드는 NCC API 최신 문서 기준으로 확인해야 합니다.
- 운영 환경에서는 인증키를 안전하게 주입(시크릿 매니저)하세요.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from itertools import product
from typing import Iterable


AGE_CODE_MAP = {
    "10": "AGE_10",
    "20": "AGE_20",
    "30": "AGE_30",
    "40": "AGE_40",
    "50": "AGE_50",
    "60+": "AGE_60_UP",
}

TEMPLATE_PRESETS = {
    "brand_general": {
        "intents": ["BRAND", "GENERAL"],
        "devices": ["PC", "MOBILE"],
    },
    "device_specific": {
        "intents": ["MIXED"],
        "devices": ["PC", "MOBILE"],
    },
    "shopping_focus": {
        "intents": ["SHOPPING"],
        "devices": ["MOBILE"],
    },
}


@dataclass
class NaverAuth:
    access_license: str
    secret_key: str
    customer_id: str


@dataclass
class HierarchyOptions:
    categories: list[str]
    genders: list[str]
    regions: list[str]
    ages_to_exclude: list[str]
    template: str


def _generate_signature(timestamp: str, method: str, uri: str, secret_key: str) -> str:
    message = f"{timestamp}.{method}.{uri}"
    signed = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(signed).decode("utf-8")


def _build_headers(auth: NaverAuth, method: str, uri: str) -> dict[str, str]:
    timestamp = str(int(time.time() * 1000))
    signature = _generate_signature(timestamp, method, uri, auth.secret_key)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": auth.access_license,
        "X-Customer": auth.customer_id,
        "X-Signature": signature,
    }


def build_age_target(exclude_ages: Iterable[str]) -> dict:
    excluded_codes = [AGE_CODE_MAP[a] for a in exclude_ages if a in AGE_CODE_MAP]
    included_codes = [code for code in AGE_CODE_MAP.values() if code not in excluded_codes]
    return {"age": {"include": included_codes, "exclude": excluded_codes}}


def build_hierarchy_preview(options: HierarchyOptions) -> dict:
    preset = TEMPLATE_PRESETS[options.template]
    preview: dict = {"template": options.template, "campaigns": []}

    for category, device, intent in product(options.categories, preset["devices"], preset["intents"]):
        campaign_name = f"{category}_{intent}_{device}"
        campaign = {
            "campaignName": campaign_name,
            "category": category,
            "device": device,
            "intent": intent,
            "adgroups": [],
        }

        for gender, region in product(options.genders, options.regions):
            adgroup_name = f"{campaign_name}_{gender}_{region}"
            campaign["adgroups"].append(
                {
                    "adgroupName": adgroup_name,
                    "targets": {
                        **build_age_target(options.ages_to_exclude),
                        "gender": gender,
                        "region": region,
                    },
                }
            )

        preview["campaigns"].append(campaign)

    preview["summary"] = {
        "total_campaigns": len(preview["campaigns"]),
        "total_adgroups": sum(len(c["adgroups"]) for c in preview["campaigns"]),
    }
    return preview


def render_preview_tree(preview: dict) -> str:
    lines = [
        f"Template: {preview['template']}",
        f"Campaigns: {preview['summary']['total_campaigns']}, AdGroups: {preview['summary']['total_adgroups']}",
    ]
    for campaign in preview["campaigns"]:
        lines.append(f"└─ Campaign: {campaign['campaignName']}")
        for adgroup in campaign["adgroups"]:
            ex_ages = ",".join(adgroup["targets"]["age"]["exclude"]) or "없음"
            lines.append(
                "   └─ AdGroup: "
                f"{adgroup['adgroupName']} | gender={adgroup['targets']['gender']} | "
                f"region={adgroup['targets']['region']} | exclude_age={ex_ages}"
            )
    return "\n".join(lines)


def create_adgroup(
    base_url: str,
    auth: NaverAuth,
    campaign_id: str,
    adgroup_name: str,
    gender: str,
    region: str,
    exclude_ages: Iterable[str],
) -> dict:
    uri = "/ncc/adgroups"
    payload = {
        "campaignId": campaign_id,
        "name": adgroup_name,
        "targets": {
            **build_age_target(exclude_ages),
            "gender": gender,
            "region": region,
        },
    }
    import requests

    response = requests.post(
        f"{base_url}{uri}",
        headers=_build_headers(auth, "POST", uri),
        data=json.dumps(payload),
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def parse_csv(raw: str) -> list[str]:
    return [token.strip() for token in raw.split(",") if token.strip()]


def run_interactive_wizard() -> HierarchyOptions:
    print("\n[Hierarchy Wizard] 아래 질문에 답하면 트리 미리보기를 자동 생성합니다.\n")
    template = input("템플릿 (brand_general/device_specific/shopping_focus) [brand_general]: ").strip() or "brand_general"
    categories = parse_csv(input("카테고리 (쉼표 구분, 예: shoes,bag): ")) or ["default"]
    genders = parse_csv(input("성별 (MALE,FEMALE,ALL 중 쉼표 구분) [ALL]: ")) or ["ALL"]
    regions = parse_csv(input("지역 (쉼표 구분, 예: 전국,서울) [전국]: ")) or ["전국"]
    ages_to_exclude = parse_csv(input("제외 연령 (10,20,30,40,50,60+ 중 쉼표 구분): "))
    return HierarchyOptions(categories, genders, regions, ages_to_exclude, template)


def main() -> None:
    parser = argparse.ArgumentParser(description="Naver hierarchy preview-first helper")
    parser.add_argument("--wizard", action="store_true", help="대화형 입력으로 손쉽게 구조 생성")
    parser.add_argument("--template", default="brand_general", choices=list(TEMPLATE_PRESETS.keys()))
    parser.add_argument("--categories", default="default")
    parser.add_argument("--genders", default="ALL")
    parser.add_argument("--regions", default="전국")
    parser.add_argument("--exclude-ages", default="")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    options = (
        run_interactive_wizard()
        if args.wizard
        else HierarchyOptions(
            categories=parse_csv(args.categories),
            genders=parse_csv(args.genders),
            regions=parse_csv(args.regions),
            ages_to_exclude=parse_csv(args.exclude_ages),
            template=args.template,
        )
    )

    preview = build_hierarchy_preview(options)
    print(render_preview_tree(preview))

    if args.print_json:
        print("\n--- preview json ---")
        print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
