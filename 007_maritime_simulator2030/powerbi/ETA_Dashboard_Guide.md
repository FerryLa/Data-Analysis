# Power BI ETA 대시보드 가이드
## 선박 예상 도착 시간(ETA) 시각화

---

## 📊 개요

이 가이드는 Maritime Simulator의 **ETA (Estimated Time of Arrival)** 데이터를 Power BI로 시각화하는 방법을 설명합니다.

**주요 기능**:
- 출발지 → 도착지 항로 표시
- 예상 도착 시간 (년-월-일-시)
- 항해 진행률 (%)
- 남은 거리 및 시간

---

## 📋 ETA 데이터 스키마

### 기본 선박 정보
| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `vessel_name` | string | 선박명 | Yara Birkeland |
| `mmsi` | string | MMSI 번호 | 257646000 |
| `latitude` | decimal | 현재 위도 | 59.1234 |
| `longitude` | decimal | 현재 경도 | 10.5678 |
| `speed_knots` | decimal | 현재 속도 (노트) | 12.5 |

### 항로 정보
| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `departure_port` | string | 출발지 항구 | Brevik |
| `arrival_port` | string | 도착지 항구 | Porsgrunn |

### ETA 계산 결과
| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `distance_remaining_nm` | decimal | 남은 거리 (해리) | 125.50 |
| `eta` | datetime | 예상 도착 시간 | 2026-01-25 15:30:00 |
| `eta_formatted` | string | 포맷된 ETA | 2026-01-25 15시 |
| `voyage_progress_pct` | decimal | 항해 진행률 (%) | 75.25 |
| `time_elapsed` | string | 경과 시간 | 1일 5시간 30분 |
| `time_remaining` | string | 남은 시간 | 10시간 15분 |

---

## 🎨 Power BI 대시보드 레이아웃 (ETA 중심)

```
┌──────────────────────────────────────────────────────────────────────┐
│  ⏱️ MARITIME ETA DASHBOARD                      [최종 업데이트: ...]  │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┤
│   총 항해    │   진행 중   │   지연 위험  │  정시 도착   │   평균 진행률│
│     5       │      5      │      1      │      4      │   65.5%     │
│    건       │     건      │     건      │     건      │             │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  📋 ETA 현황 테이블                                                   │
├──────┬────────┬────────┬────────┬──────┬──────┬─────────────────────┤
│ 선박  │ 출발지  │ 도착지  │ 남은거리│ 진행률│ 남은시간│      ETA          │
├──────┼────────┼────────┼────────┼──────┼──────┼─────────────────────┤
│ Yara │ Brevik │Porsgrun│  5.2nm │ 95%  │ 25분 │ 2026-01-25 15시    │
│Therese│Bergen │ Florø  │ 50.1nm │ 70%  │4시간 │ 2026-01-25 20시    │
│Prism │Sabine  │Pyeong  │4520nm  │ 48%  │10일  │ 2026-02-04 12시    │
└──────┴────────┴────────┴────────┴──────┴──────┴─────────────────────┘

┌────────────────────────────┐  ┌─────────────────────────────────────┐
│  항해 진행률 (%)            │  │  ETA 타임라인 (간트 차트)            │
│                            │  │                                     │
│  Yara     █████████▌95%   │  │  Yara    ███████████▌|              │
│  Therese  ███████░░ 70%   │  │  Therese ████████░░░░░|             │
│  Marit    ████████░ 80%   │  │  Marit   █████████░░░|              │
│  Prism    █████░░░░ 48%   │  │  Prism   ████░░░░░░░░░░░░░░░|       │
│  HMM      ███░░░░░░ 35%   │  │  HMM     ███░░░░░░░░░░░░░░░░░░|     │
│                            │  │                                     │
└────────────────────────────┘  └─────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  🗺️ 항로 지도 (출발지 → 도착지 라인)                                  │
│                                                                      │
│         Brevik ─────► Porsgrunn (Yara)                              │
│                                                                      │
│    Sabine Pass ═════════════════════► Pyeongtaek (Prism)            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Power BI 구성 단계

### 1단계: 데이터 가져오기

1. **Power BI Desktop** 실행
2. **홈** → **데이터 가져오기** → **텍스트/CSV**
3. `powerbi/datasets/maritime_data_latest.csv` 선택
4. **로드** 클릭

---

### 2단계: 측정값 (DAX) 생성

#### 기본 측정값

```dax
// 총 항해 건수
총 항해 = DISTINCTCOUNT(maritime_data[vessel_id])

// 진행 중인 항해
진행 중 항해 =
CALCULATE(
    DISTINCTCOUNT(maritime_data[vessel_id]),
    maritime_data[voyage_progress_pct] < 100
)

// 평균 진행률
평균 진행률 = AVERAGE(maritime_data[voyage_progress_pct])

// 지연 위험 (진행률 < 50% 이고 ETA가 24시간 이내)
지연 위험 =
CALCULATE(
    DISTINCTCOUNT(maritime_data[vessel_id]),
    maritime_data[voyage_progress_pct] < 50,
    maritime_data[eta] < NOW() + 1
)

// 정시 도착 예상 (진행률 >= 70%)
정시 도착 =
CALCULATE(
    DISTINCTCOUNT(maritime_data[vessel_id]),
    maritime_data[voyage_progress_pct] >= 70
)
```

#### ETA 관련 측정값

```dax
// 가장 빠른 ETA
최소 ETA = MIN(maritime_data[eta])

// 가장 늦은 ETA
최대 ETA = MAX(maritime_data[eta])

// 평균 남은 거리
평균 남은 거리 = AVERAGE(maritime_data[distance_remaining_nm])

// 총 남은 거리
총 남은 거리 = SUM(maritime_data[distance_remaining_nm])
```

---

### 3단계: 상단 KPI 카드 구성

**5개 카드 생성**:

| 카드 | 측정값 | 색상 |
|------|--------|------|
| 총 항해 | 총 항해 | 파랑 (#1E3A8A) |
| 진행 중 | 진행 중 항해 | 초록 (#10B981) |
| 지연 위험 | 지연 위험 | 빨강 (#EF4444) |
| 정시 도착 | 정시 도착 | 초록 (#10B981) |
| 평균 진행률 | 평균 진행률 | 파랑 (#3B82F6) |

**서식 설정**:
```
데이터 레이블:
  - 글꼴 크기: 48
  - 색: 각 카드별 색상

범주 레이블:
  - 글꼴 크기: 14
  - 색: #6B7280 (회색)
```

---

### 4단계: ETA 현황 테이블

**테이블 비주얼 삽입**

**필드**:
- `vessel_name` (선박)
- `departure_port` (출발지)
- `arrival_port` (도착지)
- `distance_remaining_nm` (남은 거리)
- `voyage_progress_pct` (진행률)
- `time_remaining` (남은 시간)
- `eta_formatted` (ETA)

**조건부 서식**:

##### 진행률 (데이터 막대)
- 최소값: 0
- 최대값: 100
- 색상: 파랑 그라데이션

##### ETA (배경색)
- 24시간 이내: 빨강 (#FEE2E2)
- 24-48시간: 노랑 (#FEF3C7)
- 48시간 이상: 초록 (#D1FAE5)

---

### 5단계: 항해 진행률 바 차트

**막대형 차트** 선택 (가로)

**필드**:
```
Y축: vessel_name
X축: voyage_progress_pct
도구 설명:
  - departure_port
  - arrival_port
  - time_remaining
  - eta_formatted
```

**서식**:
```
데이터 색:
  - 조건부 서식 활성화
  - 진행률 >= 80%: 초록 (#10B981)
  - 진행률 50-79%: 파랑 (#3B82F6)
  - 진행률 < 50%: 빨강 (#EF4444)

X축:
  - 최소값: 0
  - 최대값: 100
  - 제목: "진행률 (%)"
```

---

### 6단계: ETA 타임라인 (간트 차트)

**사용자 지정 비주얼 설치**:
1. **시각화** → **추가 시각적 개체 가져오기**
2. 검색: **Gantt Chart**
3. **추가** 클릭

**필드 설정**:
```
작업: vessel_name
시작 날짜: timestamp (현재 시간)
종료 날짜: eta
범례: departure_port
```

**서식**:
```
막대 색상: 선박별 구분
축: 날짜/시간 형식
```

---

### 7단계: 항로 지도 (출발지 → 도착지)

**Azure Maps Visual** 선택

##### 레이어 1: 출발지 마커
```
위치: departure_lat, departure_lon
레이블: departure_port
아이콘: 🟢 초록 원
크기: 고정 (작음)
```

##### 레이어 2: 도착지 마커
```
위치: arrival_lat, arrival_lon
레이블: arrival_port
아이콘: 🔴 빨강 원
크기: 고정 (중간)
```

##### 레이어 3: 항로 라인 (선택 사항)
> **주의**: Azure Maps는 두 점을 직선으로 연결 불가. 대안:
> - **Shape Map** 비주얼 사용
> - 또는 **Icon Map** 사용

---

## 🔄 자동 새로고침

### Power BI Desktop:
1. **파일** → **옵션 및 설정** → **옵션**
2. **미리보기 기능** → **자동 페이지 새로 고침** 활성화
3. **페이지 새로 고침** 간격: **5분**

### Power BI Service:
1. 데이터 세트 → **예약된 새로 고침**
2. 빈도: **15분** (Pro) / **5분** (Premium)

---

## 📊 샘플 데이터 (5척)

| 선박 | 출발지 | 도착지 | 남은 거리 | 진행률 | ETA |
|------|--------|--------|-----------|--------|-----|
| Yara Birkeland | Brevik | Porsgrunn | 5.2 nm | 95% | 2026-01-25 15시 |
| Therese | Bergen | Florø | 50.1 nm | 70% | 2026-01-25 20시 |
| Marit | Ålesund | Molde | 30.5 nm | 80% | 2026-01-25 18시 |
| Prism Courage | Sabine Pass | Pyeongtaek | 4,520 nm | 48% | 2026-02-04 12시 |
| HMM Algeciras | Busan | Rotterdam | 8,850 nm | 35% | 2026-02-15 08시 |

---

## 🎯 핵심 인사이트 표시

### 1. 지연 위험 알림

**카드 비주얼** 사용:
```dax
지연 위험 메시지 =
VAR DelayRisk = [지연 위험]
RETURN
IF(
    DelayRisk > 0,
    "⚠️ " & DelayRisk & "척 지연 위험",
    "✅ 모든 선박 정시 도착 예상"
)
```

### 2. 가장 빠른 도착 예정

```dax
다음 도착 선박 =
VAR NextETA = [최소 ETA]
VAR NextVessel =
CALCULATE(
    FIRSTNONBLANK(maritime_data[vessel_name], 1),
    maritime_data[eta] = NextETA
)
RETURN
NextVessel & " - " & FORMAT(NextETA, "MM/DD HH시")
```

---

## ✅ 체크리스트

- [ ] CSV 데이터 ETA 정보 포함 확인
- [ ] Power BI에 데이터 로드 완료
- [ ] DAX 측정값 생성 (총 항해, 진행률 등)
- [ ] 상단 KPI 카드 5개 배치
- [ ] ETA 현황 테이블 생성
- [ ] 항해 진행률 바 차트 생성
- [ ] ETA 타임라인 (간트 차트) 생성
- [ ] 항로 지도 (출발지/도착지) 생성
- [ ] 조건부 서식 적용 (진행률, ETA)
- [ ] 자동 새로고침 설정

---

## 💾 저장

**파일명**: `Maritime_ETA_Dashboard.pbix`
**경로**: `powerbi/dashboards/`

---

## 🚀 완성!

출발지에서 도착지까지의 ETA를 한눈에 확인할 수 있는 대시보드가 완성되었습니다!

**활용 방법**:
1. Streamlit 앱 실행 → ETA 현황 탭 확인
2. PowerBI용 데이터 내보내기
3. Power BI에서 새로 고침
4. 실시간 ETA 확인 및 지연 위험 모니터링

---

**작성일**: 2026-01-25
**버전**: 1.0
