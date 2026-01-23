# HMM 파나마운하 물류 분석 - Power BI 시각화 가이드

## 📊 프로젝트 개요

**목적**: HMM(현대상선) 아시아-북미 항로의 파나마운하 경유/우회 시나리오 비교 분석  
**데이터 기간**: 2024년 1월~12월  
**분석 대상**: 24,000 TEU급 메가맥스 컨테이너선  
**핵심 질문**: 파나마운하 통행료를 지불해도 남미 우회보다 경제적인가?

---

## 📁 데이터 파일 구조

### 1. `HMM_Panama_Canal_Analysis.xlsx`
Power BI에서 바로 연결 가능한 통합 Excel 파일

**시트 구성**:
- `Routes_Cost`: 항로별 비용 상세 데이터 (24개 레코드)
- `Timeseries`: 월별 추이 데이터 (24개 레코드)
- `Route_Coordinates`: 지도 시각화용 경로 좌표 (7개 레코드)
- `KPI`: 주요 성과 지표 (1개 레코드)

### 2. CSV 파일들
개별 분석용 (Python/SQL 추가 분석 시 활용)
- `routes_cost.csv`
- `timeseries.csv`
- `route_coordinates.csv`
- `kpi.csv`

---

## 🎨 Power BI 대시보드 구성

### 레이아웃 구조 (권장)

```
┌─────────────────────────────────────────────────────────────┐
│  HMM 파나마운하 물류 비용 분석                               │
│  아시아-북미 항로 비교 (2024년 기준)                         │
├─────────────────────────────────────────────────────────────┤
│  [KPI 카드 영역]                                             │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │
│  │평균거리│  │비용절감│  │마진개선│  │TEU단가 │           │
│  │절감(km)│  │  ($)   │  │  (%)   │  │  ($)   │           │
│  └────────┘  └────────┘  └────────┘  └────────┘           │
├─────────────────────────────────────────────────────────────┤
│  [지도 시각화]                        [비용 비교 차트]       │
│  ┌──────────────────────┐            ┌──────────────────┐  │
│  │                      │            │                  │  │
│  │  선박 이동 경로      │            │  항로별 물류비   │  │
│  │  파나마 vs 남미우회  │            │  Clustered Bar   │  │
│  │                      │            │                  │  │
│  └──────────────────────┘            └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  [시계열 추이]                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  월별 물류비 추이 (Line Chart)                           ││
│  │  파나마 경유 vs 남미 우회                                ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Power BI 구현 단계

### Step 1: 데이터 연결

1. Power BI Desktop 실행
2. **홈 → 데이터 가져오기 → Excel**
3. `HMM_Panama_Canal_Analysis.xlsx` 선택
4. 모든 시트 체크 후 **로드**

### Step 2: 데이터 모델링 (관계 설정)

**Power BI는 자동으로 관계를 인식하지만 수동 확인 필요**

1. **모델링 탭** → 관계 보기
2. 필요 시 관계 생성:
   - `Routes_Cost[route_name]` ↔ `Timeseries[route_name]`
   - `Routes_Cost[scenario]` ↔ `Timeseries[scenario]`

### Step 3: 측정값(Measure) 생성

**새 측정값 만들기**를 클릭하여 DAX 수식 입력:

```dax
-- 1. 평균 거리 절감
평균 거리 절감 (km) = 
CALCULATE(
    AVERAGE(Routes_Cost[distance_km]),
    Routes_Cost[via_panama] = FALSE
) - 
CALCULATE(
    AVERAGE(Routes_Cost[distance_km]),
    Routes_Cost[via_panama] = TRUE
)

-- 2. 평균 비용 절감
평균 비용 절감 ($) = 
CALCULATE(
    AVERAGE(Routes_Cost[total_cost]),
    Routes_Cost[via_panama] = FALSE
) - 
CALCULATE(
    AVERAGE(Routes_Cost[total_cost]),
    Routes_Cost[via_panama] = TRUE
)

-- 3. 마진 개선율
마진 개선율 (%) = 
DIVIDE(
    [평균 비용 절감 ($)],
    CALCULATE(
        AVERAGE(Routes_Cost[total_cost]),
        Routes_Cost[via_panama] = FALSE
    ),
    0
) * 100

-- 4. 파나마 경유 평균 TEU 단가
파나마 TEU당 비용 ($) = 
CALCULATE(
    AVERAGE(Routes_Cost[cost_per_teu]),
    Routes_Cost[via_panama] = TRUE
)

-- 5. 남미 우회 평균 TEU 단가
우회 TEU당 비용 ($) = 
CALCULATE(
    AVERAGE(Routes_Cost[cost_per_teu]),
    Routes_Cost[via_panama] = FALSE
)
```

---

## 📈 시각화 구현 가이드

### 4.1 KPI 카드 영역

**시각화 유형**: 카드(Card)

**카드 1 - 평균 거리 절감**
- 필드: `평균 거리 절감 (km)` [측정값]
- 서식: 
  - 데이터 레이블 형식: `#,##0` km
  - 범주 레이블: "평균 거리 절감"
  - 배경색: 연한 파란색

**카드 2 - 비용 절감**
- 필드: `평균 비용 절감 ($)` [측정값]
- 서식:
  - 데이터 레이블 형식: `$#,##0`
  - 범주 레이블: "항차당 비용 절감"
  - 배경색: 연한 초록색

**카드 3 - 마진 개선율**
- 필드: `마진 개선율 (%)` [측정값]
- 서식:
  - 데이터 레이블 형식: `0.00%`
  - 범주 레이블: "마진 개선율"
  - 배경색: 연한 주황색

**카드 4 - TEU당 비용 비교**
- 다중 행 카드(Multi-row card) 사용
- 필드:
  - `파나마 TEU당 비용 ($)` [측정값]
  - `우회 TEU당 비용 ($)` [측정값]
- 서식:
  - 데이터 레이블 형식: `$0.00`

---

### 4.2 지도 시각화

**시각화 유형**: 지도(Map) 또는 ArcGIS Maps

**옵션 1: 기본 지도 (Map Visual)**

1. 시각화 → 지도(Map)
2. 필드 할당:
   - **위도**: `Route_Coordinates[lat]`
   - **경도**: `Route_Coordinates[lon]`
   - **범례**: `Route_Coordinates[route]`
   - **크기**: `Route_Coordinates[seq]` (경로 순서)
3. 서식 설정:
   - 데이터 색: 파나마(파란색), 남미우회(빨간색)
   - 거품 크기: 20-30
   - 지도 스타일: 항공

**옵션 2: 향상된 지도 (ArcGIS Maps - 권장)**

1. AppSource에서 ArcGIS Maps 다운로드
2. 시각화 → ArcGIS Maps
3. 경로 레이어 추가:
   - 레이어 1: 부산→뉴욕(파나마) - 파란색 선
   - 레이어 2: 부산→뉴욕(남미우회) - 빨간색 선
4. 주요 항구 마커:
   - 부산, 상하이, 뉴욕, 로스앤젤레스 - 노란색 별
   - 파나마운하 - 초록색 마커

**주요 항구 좌표 (수동 입력 시)**:
```
부산: 35.1796, 129.0756
상하이: 31.2304, 121.4737
로스앤젤레스: 33.7175, -118.2699
뉴욕: 40.6643, -74.0395
파나마운하: 8.9139, -79.5733
```

---

### 4.3 비용 비교 차트

**시각화 유형**: 묶은 세로 막대형 차트(Clustered Column Chart)

1. 시각화 → 묶은 세로 막대형 차트
2. 필드 할당:
   - **X축**: `Routes_Cost[route_name]`
   - **Y축**: `Routes_Cost[total_cost]`
   - **범례**: `Routes_Cost[scenario]`
3. 필터 설정:
   - `route_type` = "USEC" (북미 동안 항로만 표시)
   - 또는 슬라이서로 사용자 선택 가능하게
4. 서식 설정:
   - 데이터 레이블: 표시 (상단)
   - 형식: `$#,##0K`
   - 색상: 파나마 경유(파란색), 남미 우회(빨간색)
   - Y축 제목: "물류비 ($)"
   - X축 제목: "항로"

**추가 인사이트 표시**:
- 차트 위에 텍스트 상자 추가
- 내용: "파나마 경유 시 평균 32.5% 비용 절감"

---

### 4.4 시계열 추이 차트

**시각화 유형**: 꺾은선형 차트(Line Chart)

1. 시각화 → 꺾은선형 차트
2. 필드 할당:
   - **X축**: `Timeseries[date]`
   - **Y축**: `Timeseries[total_cost]`
   - **범례**: `Timeseries[scenario]`
3. 서식 설정:
   - 데이터 레이블: 표시 안 함 (선택)
   - 선 스타일: 실선, 두께 3
   - 색상: 파나마 경유(파란색), 남미 우회(빨간색)
   - Y축 제목: "물류비 ($)"
   - X축 제목: "월"
   - X축 형식: "2024년 1월" 형태

**추가 분석 레이어**:
- 추세선 추가: 분석 → 추세선
- 평균선 추가: 분석 → 평균선

---

## 🎯 인터랙티브 요소 추가

### 슬라이서(Slicer) 구성

**슬라이서 1 - 항로 유형**
- 필드: `Routes_Cost[route_type]`
- 옵션: USWC(서안), USEC(동안)
- 스타일: 타일

**슬라이서 2 - 출발 항구**
- 필드: `Routes_Cost[origin]`
- 옵션: 부산, 상하이, 닝보
- 스타일: 드롭다운

**슬라이서 3 - 목적지 항구**
- 필드: `Routes_Cost[destination]`
- 스타일: 드롭다운

### 도구 설명(Tooltip) 커스터마이징

1. 새 페이지 생성 → 이름: "Tooltip_Route_Details"
2. 페이지 정보 → 도구 설명으로 사용
3. 소형 카드 배치:
   - 항로명
   - 거리(km)
   - 항해일수
   - 연료비
   - 인건비
   - 통행료

---

## 📊 DAX 고급 분석 예시

### 비용 구성 분석

```dax
-- 연료비 비중
연료비 비중 (%) = 
DIVIDE(
    AVERAGE(Routes_Cost[fuel_cost]),
    AVERAGE(Routes_Cost[total_cost]),
    0
) * 100

-- 통행료 대비 절감액
통행료 ROI = 
DIVIDE(
    [평균 비용 절감 ($)],
    AVERAGE(Routes_Cost[panama_toll]),
    0
)

-- 항해일수 절감
평균 항해일수 절감 = 
CALCULATE(
    AVERAGE(Routes_Cost[days_at_sea]),
    Routes_Cost[via_panama] = FALSE
) - 
CALCULATE(
    AVERAGE(Routes_Cost[days_at_sea]),
    Routes_Cost[via_panama] = TRUE
)
```

### 시나리오 분석

```dax
-- 유가 변동 시나리오 (+20%)
유가상승_시나리오 = 
AVERAGE(Routes_Cost[total_cost]) * 1.15

-- TEU 가동률 70% 시나리오
가동률_조정_비용 = 
AVERAGE(Routes_Cost[cost_per_teu]) / 0.7
```

---

## 🎨 색상 테마 (일관성 유지)

### 권장 색상 팔레트

```
파나마 경유: #0078D4 (Microsoft Blue)
남미 우회: #D13438 (Red)
배경: #F3F2F1 (Light Gray)
강조: #FFB900 (Yellow)
텍스트: #323130 (Dark Gray)
```

### 서식 설정 팁

1. **보기 → 테마 → 사용자 지정 테마**
2. 아래 JSON을 업로드:

```json
{
  "name": "Panama Canal Analysis",
  "dataColors": ["#0078D4", "#D13438", "#FFB900", "#107C10", "#5C2D91"],
  "background": "#F3F2F1",
  "foreground": "#323130",
  "tableAccent": "#0078D4"
}
```

---

## 📱 모바일 레이아웃

Power BI Mobile용 최적화:

1. **보기 → 모바일 레이아웃**
2. 우선순위:
   - KPI 카드 (상단)
   - 비용 비교 차트 (중간)
   - 시계열 차트 (하단)
3. 지도는 모바일에서 제외 (성능 이슈)

---

## 🚀 배포 및 공유

### Power BI Service 게시

1. **홈 → 게시**
2. 작업 영역 선택
3. URL 공유 또는 보고서 포함

### 자동 새로고침 설정

1. Power BI Service → 데이터 세트 설정
2. 새로고침 일정: 매일 오전 6시
3. 실패 시 이메일 알림 설정

---

## 📋 체크리스트

시각화 완료 후 확인 사항:

- [ ] 모든 측정값이 올바르게 계산되는가?
- [ ] 색상이 일관되게 적용되었는가?
- [ ] 데이터 레이블 형식이 통일되었는가? ($, km, %)
- [ ] 슬라이서가 모든 차트에 연동되는가?
- [ ] 도구 설명이 정보를 명확히 전달하는가?
- [ ] 모바일 레이아웃이 사용 가능한가?
- [ ] 성능(로딩 시간)이 3초 이내인가?

---

## 💡 추가 분석 아이디어

### 고급 시나리오

1. **유가 변동 시뮬레이션**
   - 유가 ±20% 변동 시 비용 영향
   - What-If 파라미터 활용

2. **가동률 최적화**
   - TEU 가동률 70%, 80%, 90% 비교
   - 손익분기점 분석

3. **경쟁사 벤치마킹**
   - Maersk, MSC, COSCO 비교 (데이터 추가 시)

4. **계절성 분석**
   - 성수기/비수기 물류비 변동
   - 파나마운하 혼잡도 반영

---

## 🔗 참고 자료

- [Power BI 공식 문서](https://docs.microsoft.com/power-bi/)
- [DAX 함수 레퍼런스](https://dax.guide/)
- [파나마운하청 공식 통계](https://pancanal.com/statistics/)
- [HMM 공식 웹사이트](https://www.hmm21.com/)

---

**작성일**: 2025-01-19  
**버전**: 1.0  
**작성자**: Data Analytics Team

---

## 📧 문의

추가 분석이나 커스터마이징이 필요하시면 언제든 요청해주세요.

```
다음 단계: Looking Ahead 섹션의 상세 분석 구현
- 이동거리 계산 수식 (Haversine 공식 설명)
- 비용 감산 모델 (세부 구성요소 분석)
- 이커머스 가격 전략 적용 (실제 상품 케이스 스터디)
```
