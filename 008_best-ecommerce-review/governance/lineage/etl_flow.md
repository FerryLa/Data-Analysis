# 데이터 계보 (Data Lineage)

## ETL 플로우

```
[Source] → [Extract] → [Transform] → [Load] → [Target]

CSV Files      →  Extractors  →  Transformers  →  Loaders  →  Database
  ├─ 스마트스토어                  ├─ Cleaning                  ├─ raw_reviews
  ├─ 오픈마켓                      ├─ Filtering                 ├─ cleaned_reviews
  ├─ Amazon API                   ├─ Scoring                   ├─ scored_reviews
  └─ AppStore API                 └─ Message Gen               └─ messages
```

## 변환 이력
- Bronze → Silver: 정제, 필터링, 점수화
- Silver → Gold: 메시지 생성 및 포맷팅
