# Phase 1 + n8n 통합 리포트

**실행일**: 2026-02-08
**실행 환경**: Windows / Python 3.13.12 / SQLite 3

---

## 1. 데이터 수집 결과

### 총 수집 리뷰: 6,505개

| 앱 | 수집(원본) | 필터 후 | 평균 평점 | 평균 길이 |
|---|---|---|---|---|
| 쿠팡 | 2,000 | 1,513 | 1.65 | 58자 |
| 11번가 | 1,859 | 1,247 | 3.06 | 43자 |
| 네이버쇼핑 | 1,000 | 877 | 1.79 | 74자 |
| 무신사 | 1,500 | 935 | 3.44 | 41자 |
| 지마켓 | 1,500 | 1,005 | 4.00 | 42자 |
| 당근마켓 | 1,000 | 928 | 1.99 | 97자 |

> 마켓컬리(`com.dmp.market.kurly`)는 Play Store에서 리뷰 0개 반환으로 무신사/지마켓/당근마켓으로 대체

### 수집 파일 (data/bronze/playstore/)
- `reviews_coupang_20260208.csv` (304.2 KB)
- `reviews_11st_20260208.csv` (208.4 KB)
- `reviews_navershopping_20260208.csv` (223.0 KB)
- `reviews_musinsa_20260208.csv` (152.8 KB)
- `reviews_gmarket_20260208.csv` (165.5 KB)
- `reviews_daangn_20260208.csv` (278.5 KB)

---

## 2. 데이터 검증

### 컬럼 구조
`review_id, source, created_date, review_content, rating, author_masked, product_category`

### NULL 값: 전체 파일 0개

### 유머/긍정 키워드 분석

| 앱 | 유머 키워드 | 긍정 키워드 |
|---|---|---|
| 쿠팡 | 77개 (5.1%) | 79개 (5.2%) |
| 11번가 | 72개 (5.8%) | 226개 (18.1%) |
| 네이버쇼핑 | 24개 (2.7%) | 79개 (9.0%) |
| 무신사 | 50개 (5.3%) | 210개 (22.5%) |
| 지마켓 | 28개 (2.8%) | 339개 (33.7%) |
| 당근마켓 | 39개 (4.2%) | 80개 (8.6%) |
| **합계** | **290개** | **1,013개** |

---

## 3. 데이터베이스

### DB 파일: `review.db`

### 테이블 (7개)
| 테이블 | 컬럼 수 | 설명 |
|---|---|---|
| raw_reviews | 9 | 원본 리뷰 |
| cleaned_reviews | 7 | 정제된 리뷰 |
| filtered_reviews | 6 | 필터링 결과 |
| scored_reviews | 6 | LLM 점수화 |
| morning_messages | 8 | 아침 메시지 |
| evening_messages | 8 | 저녁 메시지 |
| audit_log | 6 | 감사 로그 |

### raw_reviews 적재 결과
- 총 적재: **6,505건**
- 중복/스킵: 0건
- 앱별 분포: 쿠팡 1,513 / 11번가 1,247 / 지마켓 1,005 / 무신사 935 / 당근마켓 928 / 네이버쇼핑 877

---

## 4. n8n 워크플로우

### 워크플로우 3개 생성 완료

| # | 파일 | 트리거 | 설명 |
|---|---|---|---|
| 1 | `001_morning_message.json` | Cron 07:00 | 어제 유머 리뷰 -> 아침 메시지 |
| 2 | `002_evening_message.json` | Cron 17:00 | 오늘 긍정 리뷰 -> 저녁 메시지 |
| 3 | `003_csv_loader.json` | Manual | CSV -> DB 적재 |

### 워크플로우 노드 구조

**아침 메시지**:
```
Cron(7AM) -> SQLite Query(어제 리뷰)
  -> Code(유머 필터) -> Claude API(점수 0-100)
  -> Code(Top5 랜덤 선택) -> Claude API(메시지 포맷)
  -> Code(INSERT 준비) -> SQLite INSERT(morning_messages)
```

**저녁 메시지**:
```
Cron(5PM) -> SQLite Query(오늘 긍정 리뷰)
  -> Code(긍정 필터) -> Claude API(점수 0-100)
  -> Code(Top5 랜덤 선택) -> Claude API(메시지 포맷)
  -> Code(INSERT 준비) -> SQLite INSERT(evening_messages)
```

### n8n 설치 (사용자 수동)
- Docker 컨테이너 실행 필요
- Anthropic API Key 등록 필요
- 워크플로우 Import 후 Active 토글 ON

---

## 5. 발견된 이슈 및 해결

| # | 이슈 | 원인 | 해결 |
|---|---|---|---|
| 1 | 마켓컬리 리뷰 0개 | Play Store API에서 빈 결과 반환 | 무신사/지마켓/당근마켓으로 대체 |
| 2 | 11번가 목표 미달 (1,859/2,000) | 전체 리뷰 수 부족 | 보충 앱으로 총량 확보 |
| 3 | 11번가 패키지명 | 기존 코드의 `com.skeletonapp.skplanet11st` 부정확 | `com.elevenst.deals`로 수정 |
| 4 | DDL 누락 테이블 | `filtered_reviews`, `audit_log` 미포함 | DDL 파일에 추가 |
| 5 | 콘솔 한글 깨짐 | Git Bash UTF-8 인코딩 이슈 | 기능에는 영향 없음 (CSV/DB는 정상) |

---

## 6. 다음 단계 권장사항

1. **n8n 설치 및 테스트**: Docker 컨테이너 실행 후 워크플로우 Import/테스트
2. **Phase 2 - 데이터 정제**: `cleaned_reviews` 테이블 파이프라인 구축
3. **Phase 3 - LLM 점수화**: Claude API로 유머/긍정 점수 일괄 산정
4. **Tableau/Redash 연동**: morning_messages/evening_messages 테이블 시각화
5. **Slack Webhook 연동**: 메시지 자동 발송 채널 설정
6. **데이터 보강**: 마켓컬리 대체로 배달의민족, 오늘의집 등 추가 검토

---

## 7. 파일 구조 요약

```
008_best-ecomerce-review/
  data/bronze/playstore/
    reviews_coupang_20260208.csv
    reviews_11st_20260208.csv
    reviews_navershopping_20260208.csv
    reviews_musinsa_20260208.csv
    reviews_gmarket_20260208.csv
    reviews_daangn_20260208.csv
  review.db                          (SQLite, 6,505 rows)
  sql/ddl/01_create_tables.sql       (7 tables)
  n8n_workflows/
    morning/001_morning_message.json
    evening/002_evening_message.json
    loader/003_csv_loader.json
  src/etl/extractors/
    collect_all_reviews.py
    collect_supplementary.py
    validate_all_csvs.py
    load_csvs_to_db.py
```
