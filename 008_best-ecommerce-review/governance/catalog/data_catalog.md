# 데이터 카탈로그

## 데이터셋 목록

| ID | Name | Layer | Source | Frequency |
|----|------|-------|--------|-----------|
| DS001 | raw_reviews | Bronze | CSV/API | Daily |
| DS002 | cleaned_reviews | Silver | DS001 | Daily |
| DS003 | scored_reviews | Silver | DS002 | Daily |
| DS004 | morning_messages | Gold | DS003 | Daily |
| DS005 | evening_messages | Gold | DS003 | Daily |

## 테이블 스키마

### raw_reviews
- id: 기본키
- review_id: 원본 리뷰 ID (UNIQUE)
- source: 출처 (smartstore, coupang, 11st, amazon, appstore)
- created_date: 작성일
- review_content: 리뷰 본문
- rating: 평점 (1.0~5.0)
- author_masked: 마스킹된 작성자
- loaded_at: 적재 시각
