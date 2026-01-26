# Power BI 대시보드 구성 가이드
## 배달 관제 스타일 Maritime Fleet Monitoring

---

## 🎯 최종 결과 미리보기

```
┌──────────────────────────────────────────────────────────────────────┐
│  🚢 MARITIME FLEET MONITORING 2030                   [새로고침: 1분전]  │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┤
│   총 선박    │  AIS 연결   │  위성 통신   │   예상 위치  │   평균 속도  │
│     5       │      3      │      0      │      2      │   15.2kn    │
│    척       │     척      │     척      │     척      │             │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘

┌──────────────┐  ┌──────────────────────────────────────────────────┐
│  선박 리스트  │  │                                                  │
├──────────────┤  │                                                  │
│ 🔍 검색      │  │                                                  │
│ 🎛️ 필터     │  │                                                  │
├──────────────┤  │                                                  │
│ ⚫ 74829     │  │           🌍 글로벌 선박 위치 지도                │
│ Yara         │  │                                                  │
│ 12.5kn       │  │         (Azure Maps / Icon Map)                  │
│ 59.12°N      │  │                                                  │
│              │  │                                                  │
│ ⚫ 74828     │  │                                                  │
│ Therese      │  │                                                  │
│ 8.3kn        │  │                                                  │
│ 60.45°N      │  │                                                  │
│              │  │                                                  │
│ 🔵 64802     │  │                                                  │
│ Prism        │  │                                                  │
│ 19.0kn       │  │                                                  │
│ 0.00°N       │  │                                                  │
│              │  └──────────────────────────────────────────────────┘
└──────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  통신 타입 분포                    │  시간대별 선박 활동              │
│  ────────────────                  │  ─────────────────              │
│  ⚫ AIS: 3척 (60%)                 │  [시계열 차트]                   │
│  🟢 암모니아: 0척 (0%)              │                                 │
│  🔴 SMR: 0척 (0%)                  │                                 │
│  🔵 예상: 2척 (40%)                 │                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Step-by-Step 구성 가이드

### 1단계: 데이터 준비

#### 1-1. CSV 데이터 가져오기

1. **Power BI Desktop** 실행
2. **홈** 탭 → **데이터 가져오기** → **텍스트/CSV**
3. 파일 선택: `powerbi/datasets/maritime_data_latest.csv`
4. 미리보기 확인 후 **로드** 클릭

#### 1-2. 데이터 변환 (Power Query)

**홈** → **데이터 변환** 클릭

##### 데이터 타입 설정:
```
timestamp       → 날짜/시간
vessel_id       → 텍스트
vessel_name     → 텍스트
mmsi            → 텍스트
vessel_type     → 텍스트
latitude        → 10진수
longitude       → 10진수
speed_knots     → 10진수
course_deg      → 10진수
comm_type       → 텍스트
comm_status     → 텍스트
data_source     → 텍스트
color_code      → 텍스트
last_update     → 날짜/시간
```

##### 사용자 지정 열 추가 (선택):

**열 추가** → **사용자 지정 열**

```
// 통신 상태 이모지
comm_emoji =
  if [color_code] = "Black" then "⚫"
  else if [color_code] = "Green" then "🟢"
  else if [color_code] = "Red" then "🔴"
  else if [color_code] = "LightBlue" then "🔵"
  else "⚪"

// 위치 표시 (위도/경도)
position_display =
  Text.From([latitude], "0.00") & "°N, " &
  Text.From([longitude], "0.00") & "°E"

// 속도 표시
speed_display =
  Text.From([speed_knots], "0.0") & "kn"
```

**닫기 및 적용** 클릭

---

### 2단계: 측정값 (DAX) 생성

**모델링** 탭 → **새 측정값** 클릭

#### 기본 측정값:

```dax
// 총 선박 수
총 선박 수 = DISTINCTCOUNT(maritime_data[vessel_id])

// AIS 연결 선박
AIS 연결 =
CALCULATE(
    DISTINCTCOUNT(maritime_data[vessel_id]),
    maritime_data[comm_type] = "AIS"
)

// 위성 통신 선박
위성 통신 =
CALCULATE(
    DISTINCTCOUNT(maritime_data[vessel_id]),
    maritime_data[comm_type] = "SATELLITE_PRED"
)

// 암모니아 선박
암모니아 선박 =
CALCULATE(
    DISTINCTCOUNT(maritime_data[vessel_id]),
    maritime_data[comm_type] = "AMMONIA_SIM"
)

// SMR 선박
SMR 선박 =
CALCULATE(
    DISTINCTCOUNT(maritime_data[vessel_id]),
    maritime_data[comm_type] = "SMR_SIM"
)

// 평균 속도
평균 속도 = AVERAGE(maritime_data[speed_knots])

// 최종 업데이트 시간
최종 업데이트 = MAX(maritime_data[timestamp])
```

---

### 3단계: 페이지 레이아웃 설정

#### 3-1. 캔버스 설정

1. **보기** 탭 → **페이지 보기** → **16:9**
2. **서식** → **캔버스 배경** → 색상: `#F5F5F5` (연한 회색)

---

### 4단계: KPI 카드 만들기 (상단)

#### 4-1. 카드 비주얼 삽입

**시각화** → **카드** 선택 (5개 생성)

| 카드 | 측정값 | 위치 | 크기 |
|------|--------|------|------|
| 카드 1 | 총 선박 수 | X: 0, Y: 50 | W: 200, H: 120 |
| 카드 2 | AIS 연결 | X: 220, Y: 50 | W: 200, H: 120 |
| 카드 3 | 위성 통신 | X: 440, Y: 50 | W: 200, H: 120 |
| 카드 4 | 암모니아 선박 + SMR 선박 | X: 660, Y: 50 | W: 200, H: 120 |
| 카드 5 | 평균 속도 | X: 880, Y: 50 | W: 200, H: 120 |

#### 4-2. 카드 서식 설정

각 카드 선택 → **서식** 탭:

```
데이터 레이블:
  - 색: #1E3A8A (진한 파랑)
  - 글꼴 크기: 48
  - 글꼴: Segoe UI Semibold

범주 레이블:
  - 표시: 켜기
  - 색: #6B7280 (회색)
  - 글꼴 크기: 14

배경:
  - 색: 흰색 (#FFFFFF)
  - 투명도: 0%

테두리:
  - 색: #E5E7EB
  - 반경: 8
```

---

### 5단계: 왼쪽 패널 - 선박 리스트 (테이블)

#### 5-1. 테이블 비주얼 삽입

**시각화** → **테이블** 선택

**필드 추가**:
- `comm_emoji` (사용자 지정 열)
- `vessel_name`
- `vessel_type`
- `mmsi`
- `position_display`
- `speed_display`
- `comm_status`

#### 5-2. 위치 및 크기

```
X: 0
Y: 200
Width: 300
Height: 500
```

#### 5-3. 조건부 서식

**comm_status** 열 선택 → **조건부 서식** → **배경색**

규칙:
```
if comm_type = "AIS"           → 배경색: #1F2937 (검정), 글꼴: 흰색
if comm_type = "AMMONIA_SIM"   → 배경색: #10B981 (녹색), 글꼴: 흰색
if comm_type = "SMR_SIM"       → 배경색: #EF4444 (빨강), 글꼴: 흰색
if comm_type = "SATELLITE_PRED"→ 배경색: #3B82F6 (파랑), 글꼴: 흰색
```

#### 5-4. 테이블 서식

```
그리드:
  - 가로선: 켜기, 색: #E5E7EB
  - 세로선: 끄기

열 머리글:
  - 배경색: #F3F4F6
  - 글꼴 크기: 12
  - 글꼴: Segoe UI Semibold

값:
  - 글꼴 크기: 11
  - 맞춤: 왼쪽
```

---

### 6단계: 중앙 - 지도 시각화

#### 옵션 1: Azure Maps Visual (권장)

##### 6-1. Azure Maps 설치

1. **시각화** → **추가 시각적 개체 가져오기**
2. 검색: **Azure Maps**
3. **추가** 클릭

##### 6-2. 지도 구성

**Azure Maps** 비주얼 선택

**필드 설정**:
```
위치: latitude, longitude
범례: color_code 또는 comm_type
크기: speed_knots (선택 사항)
도구 설명:
  - vessel_name
  - vessel_type
  - speed_knots
  - course_deg
  - comm_status
  - position_display
```

##### 6-3. 위치 및 크기

```
X: 320
Y: 200
Width: 760
Height: 500
```

##### 6-4. 서식 설정

```
지도 스타일: Road (또는 Satellite)
확대/축소: 자동
컨트롤:
  - 확대/축소 컨트롤: 켜기
  - 나침반: 켜기
  - 피치 컨트롤: 끄기

버블:
  - 최소 반경: 5
  - 최대 반경: 20
  - 투명도: 80%

범례 (색상):
  - Black: #000000
  - Green: #10B981
  - Red: #EF4444
  - LightBlue: #3B82F6
```

---

#### 옵션 2: Icon Map (대안)

##### 6-1. Icon Map 설치

1. **시각화** → **추가 시각적 개체 가져오기**
2. 검색: **Icon Map**
3. **추가** 클릭

##### 6-2. 필드 설정

```
위치: latitude, longitude
범례: comm_type
크기: speed_knots
아이콘: 선박 아이콘 (커스텀 이미지 업로드)
```

---

### 7단계: 하단 - 통신 타입 분포 (도넛 차트)

#### 7-1. 도넛 차트 삽입

**시각화** → **도넛형 차트** 선택

**필드**:
```
범례: comm_type
값: 총 선박 수 (측정값)
```

#### 7-2. 위치 및 크기

```
X: 0
Y: 720
Width: 500
Height: 250
```

#### 7-3. 서식 설정

```
데이터 색:
  - AIS: #1F2937 (검정)
  - AMMONIA_SIM: #10B981 (녹색)
  - SMR_SIM: #EF4444 (빨강)
  - SATELLITE_PRED: #3B82F6 (파랑)

세부 정보 레이블:
  - 범주: 켜기
  - 값: 켜기 (백분율)
  - 글꼴 크기: 12

범례:
  - 위치: 오른쪽
  - 글꼴 크기: 11
```

---

### 8단계: 하단 우측 - 시간대별 활동 (선택 사항)

#### 8-1. 꺾은선형 차트 삽입

**시각화** → **꺾은선형 차트** 선택

**필드**:
```
축: timestamp (시간별로 그룹화)
값: 총 선박 수
범례: comm_type
```

#### 8-2. 위치 및 크기

```
X: 520
Y: 720
Width: 560
Height: 250
```

---

### 9단계: 제목 및 헤더

#### 9-1. 텍스트 상자 추가

**홈** → **텍스트 상자** 클릭

**텍스트**:
```
🚢 MARITIME FLEET MONITORING 2030
```

**서식**:
```
글꼴 크기: 24
글꼴: Segoe UI Bold
색: #1E3A8A
맞춤: 왼쪽
배경: 흰색
```

**위치**:
```
X: 0
Y: 0
Width: 1080
Height: 40
```

---

### 10단계: 슬라이서 (필터) 추가

#### 10-1. 슬라이서 비주얼 삽입

**시각화** → **슬라이서** 선택

**필드**: `comm_type`

**위치**:
```
X: 10
Y: 180
Width: 280
```

**서식**:
```
스타일: 타일
선택: 다중 선택 (Ctrl 모드)
```

---

## 🎨 색상 팔레트

```
# 브랜드 색상
Primary Blue:   #1E3A8A
Secondary Blue: #3B82F6

# 통신 타입 색상
AIS (Black):    #1F2937
Ammonia (Green):#10B981
SMR (Red):      #EF4444
Predicted (Blue):#3B82F6

# 배경 색상
Canvas:         #F5F5F5
Card:           #FFFFFF
Border:         #E5E7EB

# 텍스트 색상
Primary Text:   #111827
Secondary Text: #6B7280
```

---

## 📊 상호작용 설정

### 1. 크로스 필터링

**서식** → **상호 작용 편집**

- **선박 리스트** 클릭 → 지도 하이라이트
- **도넛 차트** 클릭 → 지도 필터링
- **슬라이서** 선택 → 전체 필터링

### 2. 드릴스루 (선택 사항)

선박 상세 페이지 생성:
- 페이지 2: 개별 선박 상세 정보
- 드릴스루 필드: `vessel_id`

---

## 🔄 자동 새로고침

### Power BI Desktop:
1. **파일** → **옵션 및 설정** → **옵션**
2. **미리보기 기능** → **자동 페이지 새로 고침** 활성화
3. **시각화** 서식 → **페이지 새로 고침** → **자동** 선택
4. 간격: **1분**

### Power BI Service (게시 후):
1. 작업 영역에서 데이터 세트 선택
2. **예약된 새로 고침** → 활성화
3. 빈도: **매 15분** (Pro) / **매 5분** (Premium)

---

## ✅ 체크리스트

- [ ] CSV 데이터 가져오기 완료
- [ ] 데이터 타입 변환 완료
- [ ] 측정값 (DAX) 생성 완료
- [ ] KPI 카드 5개 배치 완료
- [ ] 선박 리스트 테이블 생성 완료
- [ ] 지도 시각화 (Azure Maps) 완료
- [ ] 도넛 차트 생성 완료
- [ ] 색상 조건부 서식 적용 완료
- [ ] 제목 및 헤더 추가 완료
- [ ] 슬라이서 필터 추가 완료
- [ ] 자동 새로고침 설정 완료

---

## 💾 저장 및 게시

### 1. 로컬 저장
**파일** → **다른 이름으로 저장**
- 파일명: `Maritime_Fleet_Monitoring.pbix`
- 경로: `powerbi/dashboards/`

### 2. Power BI Service 게시
**홈** → **게시**
- 작업 영역 선택
- **게시** 클릭

---

## 🚀 완성!

이제 실시간 선박 관제 대시보드가 완성되었습니다!

**다음 단계**:
1. Streamlit 앱에서 데이터 내보내기
2. Power BI에서 **새로 고침** 클릭
3. 실시간 선박 위치 확인

---

**작성일**: 2026-01-25
**버전**: 1.0
