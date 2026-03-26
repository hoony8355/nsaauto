# 네이버 검색광고 하이어라키 자동 생성 툴

네이버 검색광고(NCC API)에서 캠페인 → 광고그룹 → 키워드/소재 구조를 자동으로 생성하는 웹 서비스의 초기 설계 문서와 샘플 코드를 포함합니다.

## 포함 내용
- 제품 기획/아키텍처 문서 (`docs/architecture.md`)
- React + Node.js 기준 DB 스키마 (`db/schema.sql`)
- 연령 제외 타겟팅 광고그룹 생성 Python 예시 (`backend/python/naver_adgroup_builder.py`)

## 핵심 목표
- 운영 자동화로 광고 세팅 시간 단축
- 반복 업무에서 발생하는 휴먼 에러 최소화
- API 실행 전 Preview/검증 단계 제공
