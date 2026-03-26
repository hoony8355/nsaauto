"""Naver NCC API adgroup creation example with age exclusion targeting.

주의:
- 실제 엔드포인트/필드는 NCC API 최신 문서 기준으로 확인해야 합니다.
- 본 코드는 구조 예시이며 운영 전 인증/오류처리/재시도 보강이 필요합니다.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Iterable

import requests

AGE_CODE_MAP = {
    "10": "AGE_10",
    "20": "AGE_20",
    "30": "AGE_30",
    "40": "AGE_40",
    "50": "AGE_50",
    "60+": "AGE_60_UP",
}


@dataclass
class NaverAuth:
    access_license: str
    secret_key: str
    customer_id: str


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
    """exclude_ages 예: ["10", "20"]"""
    excluded_codes = [AGE_CODE_MAP[a] for a in exclude_ages if a in AGE_CODE_MAP]
    included_codes = [code for code in AGE_CODE_MAP.values() if code not in excluded_codes]

    return {
        "age": {
            "include": included_codes,
            "exclude": excluded_codes,
        }
    }


def create_adgroup_excluding_ages(
    base_url: str,
    auth: NaverAuth,
    campaign_id: str,
    adgroup_name: str,
    gender: str,
    exclude_ages: Iterable[str],
) -> dict:
    uri = "/ncc/adgroups"
    endpoint = f"{base_url}{uri}"

    targets = {
        **build_age_target(exclude_ages),
        "gender": gender,
    }

    payload = {
        "campaignId": campaign_id,
        "name": adgroup_name,
        "targets": targets,
    }

    response = requests.post(
        endpoint,
        headers=_build_headers(auth, "POST", uri),
        data=json.dumps(payload),
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # 예시: 10대와 20대를 제외한 광고그룹 생성
    auth = NaverAuth(
        access_license="YOUR_ACCESS_LICENSE",
        secret_key="YOUR_SECRET_KEY",
        customer_id="YOUR_CUSTOMER_ID",
    )

    result = create_adgroup_excluding_ages(
        base_url="https://api.searchad.naver.com",
        auth=auth,
        campaign_id="cmp-xxxxxxxx",
        adgroup_name="MOBILE_GENERAL_EXCEPT_10_20",
        gender="ALL",
        exclude_ages=["10", "20"],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
