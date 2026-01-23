
```markdown
# 📊 Food Delivery Apps VOC Dashboard (Power BI)

## 📌 프로젝트 개요
음식 배달 앱 리뷰 데이터를 기반으로 **VOC(Voice of Customer) 분석**을 수행한 Power BI 대시보드입니다.  
이 대시보드는 키워드 빈도, 긍정/부정 키워드, K-RDI Score, 리뷰 건수, 평균 평점 등을 시각화하여  
앱별/플랫폼별 고객 경험을 비교할 수 있도록 구성되었습니다.

---

## 🖥️ 대시보드 주요 구성

### 1. KPI 카드
- **전체 리뷰 건수**: 데이터셋 전체 리뷰 수
- **플랫폼별 리뷰 건수**: App Store, Google Play 등 플랫폼별 리뷰 수
- **앱별 리뷰 건수**: Uber Eats, Grubhub, Wolt, Glovo, Bolt Food 등 앱별 리뷰 수
- **평균 평점**: 전체 리뷰의 평균 평점

### 2. 키워드 분석
- **TopKeywords**: 리뷰에서 가장 많이 등장한 상위 15개 키워드
- **BottomKeywords**: 리뷰에서 가장 적게 등장한 하위 15개 키워드
- **BadKeywordSummary / BottomBadKeywords**: 부정 키워드 사전 기반 Top/Bottom 15 추출

### 3. VOC 강도 (연도별/플랫폼별)
- 연도별 VOC 강도 추이
- 플랫폼별 VOC 강도 비교

### 4. K-RDI Score 추이
- 연도별 K-RDI Score 변화 (2015–2024)
- VOC Spike 이벤트 표시

### 5. 앱별 비교
- 앱별 K-RDI Score 비교 바 차트

---

## ⚙️ 주요 DAX 코드

### 전체 리뷰 건수
```DAX
TotalReviews :=
COUNTROWS(food_delivery_apps)
```

### 플랫폼별 리뷰 건수
```DAX
PlatformReviewCount :=
SUMMARIZE(
    food_delivery_apps,
    food_delivery_apps[platform],
    "ReviewCount", COUNTROWS(food_delivery_apps)
)
```

### 앱별 리뷰 건수
```DAX
AppReviewCount :=
SUMMARIZE(
    food_delivery_apps,
    food_delivery_apps[app_name],
    "ReviewCount", COUNTROWS(food_delivery_apps)
)
```

### 평균 평점
```DAX
AverageRating :=
AVERAGE(food_delivery_apps[rating])
```

---

## 🔗 관계 설정 (Model View)
- **food_delivery_apps[content] → BottomBadKeywords[content]**
- **Cardinality:** Many-to-One  
- **Cross filter direction:** Single (단방향)

---

## 🚀 사용 방법
1. Power BI Desktop에서 데이터셋(`food_delivery_apps`) 불러오기  
2. 위 DAX 식을 새 테이블/측정값으로 추가  
3. 모델 보기에서 관계 설정 (다대일, 단방향)  
4. 시각화에 KPI 카드, Top/Bottom 키워드, 리뷰 건수, 평균 평점 등을 연결  
5. 대시보드 실행 후 VOC 분석 결과 확인

---

## 🎯 요약
- 리뷰 데이터를 기반으로 **전체 리뷰 건수, 플랫폼별/앱별 리뷰 건수, 평균 평점**을 KPI로 제공  
- **긍정/부정 키워드 Top/Bottom 15** 시각화  
- **K-RDI Score 추이와 VOC Spike 이벤트** 분석  
- 관계는 **다대일, 단방향**으로 설정해야 원하는 결과가 정확히 표시됨
```

