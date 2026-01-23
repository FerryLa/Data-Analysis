# HMM 파나마운하 물류비용 분석 - Power BI 구현 가이드

## 📊 개요
이 문서는 Python으로 생성한 차트를 Power BI에서 재구현하기 위한 가이드입니다.

---

## 1️⃣ 데이터 모델 구조

### 테이블 1: `CostComparison` (비용 비교)
```
Cost_Category        | Panama_Route_USD | SouthAmerica_Route_USD
---------------------|------------------|------------------------
연료비               | 450              | 780
운하통행료           | 180              | 0
인건비               | 120              | 200
항만료               | 80               | 100
기타                 | 70               | 120
```

### 테이블 2: `MonthlyCostTrend` (월별 추이)
```
Month      | Panama_Route_USD | SouthAmerica_Route_USD
-----------|------------------|------------------------
2024-01    | 830.61           | 1204.96
2024-02    | 839.58           | 1181.06
...        | ...              | ...
```

---

## 2️⃣ DAX 측정값 (Measures)

### 📌 기본 측정값
```dax
// 파나마 총비용
Total_Panama_Cost = SUM(CostComparison[Panama_Route_USD])

// 남미우회 총비용
Total_SouthAmerica_Cost = SUM(CostComparison[SouthAmerica_Route_USD])

// 비용 차이 (절대값)
Cost_Difference = [Total_SouthAmerica_Cost] - [Total_Panama_Cost]

// 비용 차이율 (%)
Cost_Difference_Pct = 
    DIVIDE(
        [Cost_Difference],
        [Total_SouthAmerica_Cost],
        0
    ) * 100

// 파나마 경로 평균 (월별)
Panama_Monthly_Avg = AVERAGE(MonthlyCostTrend[Panama_Route_USD])

// 남미 경로 평균 (월별)
SouthAmerica_Monthly_Avg = AVERAGE(MonthlyCostTrend[SouthAmerica_Route_USD])

// 연간 절감액 (10,000 TEU 기준)
Annual_Savings_10K_TEU = 
    ([SouthAmerica_Monthly_Avg] - [Panama_Monthly_Avg]) * 10000 * 12
```

### 📌 KPI 카드용 측정값
```dax
// KPI: 평균 거리 절감 (km)
KPI_Distance_Savings = 7800  // 고정값 또는 계산식

// KPI: 비용 절감 ($)
KPI_Cost_Savings = [Cost_Difference]

// KPI: 마진 개선 (%)
KPI_Margin_Improvement = [Cost_Difference_Pct]

// KPI: TEU 단가 ($)
KPI_TEU_Unit_Price = [Total_Panama_Cost]
```

---

## 3️⃣ 시각화 구성

### 🔵 차트 1: 항로별 물류비 비교 (Clustered Bar Chart)

**Visual Type**: 묶은 세로 막대형 차트

**설정**:
- **X축**: `Cost_Category` (연료비, 운하통행료, 인건비, 항만료, 기타)
- **Y축**: 
  - `Panama_Route_USD`
  - `SouthAmerica_Route_USD`
- **데이터 레이블**: 표시 (값 위에 표시)
- **범례**: 상단 또는 우측 배치
- **색상**:
  - 파나마 경유: `#0066CC` (파란색)
  - 남미 우회: `#FF6B35` (주황색)

**서식 설정**:
```
제목: "항로별 물류비 비교 (TEU당 비용 분해)"
Y축 제목: "Cost per TEU (USD)"
그리드선: Y축만 표시
데이터 레이블: 글꼴 크기 10pt, 굵게
```

**추가 텍스트 상자** (왼쪽 상단):
```
Panama Total: $900/TEU
South America Total: $1,200/TEU
Cost Difference: $300/TEU (33.3%)
```

---

### 🔴 차트 2: 월별 물류비 추이 (Line Chart)

**Visual Type**: 꺾은선형 차트

**설정**:
- **X축**: `Month` (2024-01 ~ 2024-12)
- **Y축**:
  - `Panama_Route_USD` (선)
  - `SouthAmerica_Route_USD` (선)
- **마커**: 원형(파나마), 사각형(남미)
- **선 스타일**: 실선, 두께 2.5pt
- **범례**: 좌측 상단

**색상**:
- 파나마 경유: `#0066CC`
- 남미 우회: `#FF6B35`

**서식 설정**:
```
제목: "월별 물류비 추이 (2024년 1-12월)"
X축 제목: "Month (2024)"
Y축 제목: "Cost per TEU (USD)"
Y축 범위: 750 ~ 1,350
그리드선: 전체 표시
```

**추가 요소**:
1. **평균선** (상수선 추가):
   - 파나마 평균: $877 (점선)
   - 남미 평균: $1,188 (점선)

2. **주석** (9월 위치):
   ```
   "Canal Fee Increase (Sep 2024)"
   수직선: 빨간색 점선
   ```

---

## 4️⃣ KPI 카드 배치

```
┌─────────────────────────────────────────────────────────┐
│  [KPI 1]         [KPI 2]         [KPI 3]      [KPI 4]   │
│  평균 거리 절감   비용 절감        마진 개선    TEU 단가  │
│  7,800 km        $311 /TEU       26.2%        $877      │
└─────────────────────────────────────────────────────────┘
```

**Visual Type**: 카드

**DAX 표현식**:
- KPI 1: `KPI_Distance_Savings`
- KPI 2: `KPI_Cost_Savings`
- KPI 3: `KPI_Margin_Improvement`
- KPI 4: `KPI_TEU_Unit_Price`

**서식**:
- 글꼴 크기: 제목 14pt, 값 24pt
- 색상: 제목(회색), 값(파란색)
- 단위 표시: km, $, %, $ 자동 추가

---

## 5️⃣ 색상 테마 (Color Palette)

### 권장 색상 코드
```
파나마 경유 (Primary):   #0066CC (Blue)
남미 우회 (Secondary):   #FF6B35 (Orange)
배경색:                 #FFFFFF (White)
그리드선:               #E0E0E0 (Light Gray)
텍스트:                 #333333 (Dark Gray)
강조색 (경고):          #FF0000 (Red)
```

### Power BI 테마 JSON (선택사항)
```json
{
  "name": "HMM Logistics Theme",
  "dataColors": ["#0066CC", "#FF6B35", "#28A745", "#FFC107"],
  "background": "#FFFFFF",
  "foreground": "#333333",
  "tableAccent": "#0066CC"
}
```

---

## 6️⃣ 데이터 새로 고침 설정

### Power Query 변환 단계
1. **CSV 파일 가져오기**:
   - `cost_comparison.csv`
   - `monthly_cost_trend.csv`

2. **데이터 형식 변환**:
   ```m
   // Month 열을 Date 형식으로 변환
   = Table.TransformColumnTypes(
       Source,
       {{"Month", type date}}
   )
   ```

3. **열 이름 표준화**:
   - `Panama_Route_USD` → 데이터 형식: 10진수
   - `SouthAmerica_Route_USD` → 데이터 형식: 10진수

---

## 7️⃣ 인터랙티브 기능 (선택사항)

### 슬라이서 추가
- **기간 필터**: 월별 슬라이서 (2024-01 ~ 2024-12)
- **비용 카테고리 필터**: 다중 선택 슬라이서

### 드릴스루 페이지
- 특정 월 클릭 시 상세 비용 분해 페이지로 이동

### 툴팁 커스터마이징
```
"파나마 경유 비용: $XXX"
"남미 우회 비용: $XXX"
"절감액: $XXX (XX%)"
```

---

## 8️⃣ 성능 최적화

### 권장사항
1. **DirectQuery 대신 Import 모드 사용**
2. **불필요한 열 제거** (데이터 로딩 시)
3. **측정값 단순화** (중첩 계산 최소화)
4. **시각화 개수 제한** (페이지당 5-7개 이하)

---

## 9️⃣ 배포 전 체크리스트

- [ ] 데이터 소스 연결 확인
- [ ] DAX 측정값 정확성 검증
- [ ] 색상 테마 일관성 확인
- [ ] 모바일 레이아웃 최적화
- [ ] 데이터 새로 고침 스케줄 설정
- [ ] 접근 권한 설정 (보안)

---

## 📚 참고 자료

### Power BI 공식 문서
- DAX 함수 레퍼런스: https://learn.microsoft.com/dax/
- 시각화 모범 사례: https://learn.microsoft.com/power-bi/

### 컴플라이언스 & 거버넌스
- 데이터 분류: **내부용(Internal Use Only)**
- 민감도 레이블: **일반(General)**
- 데이터 보관 기간: **1년**

---

## 🔒 보안 고려사항

1. **행 수준 보안 (RLS)**:
   ```dax
   // 사용자별 데이터 접근 제한 (필요 시)
   [Department] = USERPRINCIPALNAME()
   ```

2. **데이터 마스킹**:
   - 민감한 비용 정보는 역할별로 마스킹 처리

3. **감사 로그**:
   - Power BI Service에서 활동 로그 활성화

---

**작성일**: 2024-01-20
**작성자**: FerryLa
**버전**: 1.0
