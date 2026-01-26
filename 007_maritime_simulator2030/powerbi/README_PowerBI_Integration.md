# Power BI 연동 가이드
## 2030 Maritime Communication Simulator

---

## 📊 개요

이 가이드는 Maritime Simulator의 실시간 선박 데이터를 Power BI로 시각화하는 방법을 설명합니다.

---

## 🗂️ 폴더 구조

```
007_maritime_simulator2030/powerbi/
├── datasets/                       # CSV 데이터 저장소
│   ├── maritime_data_latest.csv   # 최신 데이터 (PowerBI 연동용)
│   └── maritime_data_YYYYMMDD_HHMMSS.csv  # 히스토리 데이터
├── dashboards/                     # PowerBI 대시보드 파일 (.pbix)
│   └── Maritime_Fleet_Monitoring.pbix
└── README_PowerBI_Integration.md   # 이 파일
```

---

## 📥 데이터 내보내기

### 1. Streamlit 앱에서 데이터 내보내기

1. Streamlit 앱 실행: `streamlit run src/app.py`
2. **실시간 지도** 탭으로 이동
3. 시뮬레이션 시작 (AIS 연결 및 선박 추적 활성화)
4. 선박 목록 하단의 **"📊 PowerBI용 데이터 내보내기"** 버튼 클릭

### 2. 내보낸 데이터 확인

- **경로**: `powerbi/datasets/maritime_data_latest.csv`
- **형식**: UTF-8 with BOM (한글 지원)

---

## 📋 데이터 스키마

| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `timestamp` | datetime | 데이터 생성 시각 | 2026-01-25 01:30:00 |
| `vessel_id` | string | 선박 고유 ID (MMSI) | 257646000 |
| `vessel_name` | string | 선박명 | Yara Birkeland |
| `mmsi` | string | MMSI 번호 | 257646000 |
| `vessel_type` | string | 선박 타입 | Container Ship |
| `latitude` | decimal | 위도 | 59.1234 |
| `longitude` | decimal | 경도 | 10.5678 |
| `speed_knots` | decimal | 속도 (노트) | 12.5 |
| `course_deg` | decimal | 침로 (도) | 240.0 |
| `comm_type` | string | 통신 타입 | AIS / AMMONIA_SIM / SMR_SIM / SATELLITE_PRED |
| `comm_status` | string | 통신 상태 | Connected / Normal / Predicted |
| `data_source` | string | 데이터 소스 | AIS / SIMULATION / PREDICTED |
| `color_code` | string | 색상 코드 | Black / Green / Red / LightBlue |
| `last_update` | datetime | 최종 업데이트 시각 | 2026-01-25 01:30:00 |

---

## 🎨 통신 타입별 색상 코드

| 통신 타입 | 색상 | 설명 | Power BI 표시 |
|-----------|------|------|---------------|
| **AIS** | Black (⚫) | 실시간 AIS 신호 | 검정색 마커 |
| **AMMONIA_SIM** | Green (🟢) | 암모니아 선박 시뮬레이션 | 녹색 마커 |
| **SMR_SIM** | Red (🔴) | SMR 원자력 선박 시뮬레이션 | 빨간색 마커 |
| **SATELLITE_PRED** | LightBlue (🔵) | 위성 예상 위치 | 하늘색 마커 |

---

## 🔧 Power BI 설정 방법

### 방법 1: CSV 파일 연동 (간단)

1. **Power BI Desktop 실행**
2. **홈** → **데이터 가져오기** → **텍스트/CSV**
3. `maritime_data_latest.csv` 파일 선택
4. **로드** 클릭

#### 데이터 새로고침
- Streamlit에서 새 데이터 내보내기
- Power BI에서 **홈** → **새로 고침** 클릭

---

### 방법 2: 폴더 연동 (자동 새로고침)

1. **Power BI Desktop 실행**
2. **홈** → **데이터 가져오기** → **폴더**
3. `powerbi/datasets/` 폴더 경로 입력
4. **결합** → **결합 및 변환**
5. 필터: 파일명이 `maritime_data_` 로 시작하는 파일만 선택

#### 장점
- 여러 파일을 자동으로 병합
- 히스토리 데이터 분석 가능

---

### 방법 3: Streaming Dataset (실시간) ⚠️ 고급

> **주의**: REST API 개발 필요 (향후 구현 예정)

1. Power BI Service 로그인
2. 작업 영역 → **스트리밍 데이터 세트** 생성
3. Streamlit 앱에서 REST API로 데이터 전송
4. 실시간 대시보드 구성

---

## 📊 Power BI 대시보드 구성 예시

### 1️⃣ 상단 KPI (카드 비주얼)

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 총 선박 수   │ AIS 연결    │ 위성 통신    │ 예상 위치    │
│    5척      │    3척      │    0척      │    2척      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**측정값 (DAX)**:
```dax
총 선박 수 = DISTINCTCOUNT(maritime_data[vessel_id])
AIS 연결 = CALCULATE(DISTINCTCOUNT(maritime_data[vessel_id]), maritime_data[comm_type] = "AIS")
위성 통신 = CALCULATE(DISTINCTCOUNT(maritime_data[vessel_id]), maritime_data[comm_type] = "SATELLITE_PRED")
```

---

### 2️⃣ 중앙 지도 (Azure Maps / Icon Map)

#### Azure Maps Visual 설정:
1. **시각화** → **Azure Maps** 선택
2. **위치**: `latitude`, `longitude`
3. **범례**: `color_code` 또는 `comm_type`
4. **크기**: `speed_knots` (속도에 비례)
5. **도구 설명**:
   - `vessel_name`
   - `vessel_type`
   - `speed_knots`
   - `course_deg`
   - `comm_status`

#### 조건부 서식:
- **색상 규칙**:
  - `color_code = "Black"` → 검정색
  - `color_code = "Green"` → 녹색
  - `color_code = "Red"` → 빨간색
  - `color_code = "LightBlue"` → 하늘색

---

### 3️⃣ 왼쪽 패널 - 선박 리스트 (테이블)

#### 컬럼 구성:
| 선박명 | 타입 | MMSI | 통신상태 | 위치 | 속도 |
|--------|------|------|----------|------|------|
| Yara Birkeland | Container Ship | 257646000 | ⚫ AIS | 59.12N, 10.56E | 12.5kn |
| Prism Courage | LNG Tanker | 352986205 | 🔵 예상 | 0.00N, -140.00W | 19.0kn |

#### 조건부 서식:
- **통신상태** 컬럼:
  - `comm_type = "AIS"` → ⚫ 검정 배경
  - `comm_type = "AMMONIA_SIM"` → 🟢 녹색 배경
  - `comm_type = "SMR_SIM"` → 🔴 빨간 배경
  - `comm_type = "SATELLITE_PRED"` → 🔵 파란 배경

---

### 4️⃣ 하단 - 통신 상태 분포 (도넛 차트)

**측정값**:
```dax
AIS = COUNTROWS(FILTER(maritime_data, maritime_data[comm_type] = "AIS"))
암모니아 = COUNTROWS(FILTER(maritime_data, maritime_data[comm_type] = "AMMONIA_SIM"))
SMR = COUNTROWS(FILTER(maritime_data, maritime_data[comm_type] = "SMR_SIM"))
예상 위치 = COUNTROWS(FILTER(maritime_data, maritime_data[comm_type] = "SATELLITE_PRED"))
```

---

## 🎯 레이아웃 예시 (배달 관제 스타일)

```
┌───────────────────────────────────────────────────────────────┐
│  🚢 2030 Maritime Fleet Monitoring Dashboard                  │
├───────────┬───────────┬───────────┬───────────────────────────┤
│  총 선박   │  AIS 연결  │  위성 통신 │  예상 위치               │
│    5척    │    3척    │    0척    │    2척                    │
├───────────┴───────────┴───────────┴───────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌─────────────────────────────────────┐   │
│  │ 선박 리스트   │  │                                     │   │
│  ├──────────────┤  │                                     │   │
│  │ ⚫ Yara       │  │         🗺️ 지도 (Azure Maps)        │   │
│  │ ⚫ Therese    │  │                                     │   │
│  │ ⚫ Marit      │  │                                     │   │
│  │ 🔵 Prism     │  │                                     │   │
│  │ 🔵 HMM       │  │                                     │   │
│  └──────────────┘  └─────────────────────────────────────┘   │
│                                                                │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  통신 타입 분포 (도넛 차트)                             │   │
│  │  ⚫ AIS: 60%  🟢 암모니아: 0%  🔴 SMR: 0%  🔵 예상: 40% │   │
│  └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔄 자동 새로고침 설정

### Power BI Desktop:
1. **파일** → **옵션 및 설정** → **옵션**
2. **데이터 로드** → **백그라운드 새로 고침 간격** 설정
3. 최소 **1분** 간격 권장

### Power BI Service (Pro/Premium):
1. 데이터 세트 → **예약된 새로 고침** 활성화
2. 간격: **15분** ~ **1시간**

---

## ⚠️ 주의사항

### 1. CSV 파일 크기 제한
- Power BI Desktop: 최대 **1GB**
- Power BI Service: 최대 **250MB** (Import 모드)

→ 해결책: 오래된 데이터 정리 또는 DirectQuery 사용

### 2. 한글 깨짐 방지
- CSV 저장 시 **UTF-8 with BOM** 인코딩 사용 (이미 적용됨)

### 3. 실시간 제약
- CSV 방식은 **준실시간** (새로고침 필요)
- 완전 실시간: REST API + Streaming Dataset 사용 권장

---

## 🚀 향후 개선 계획

### Phase 1 (현재) ✅
- [x] CSV export 기능
- [x] PowerBI 연동 가이드

### Phase 2 (예정)
- [ ] REST API 엔드포인트 개발
- [ ] Power BI Streaming Dataset 연동
- [ ] 실시간 알림 기능

### Phase 3 (예정)
- [ ] Azure SQL Database 연동
- [ ] DirectQuery 성능 최적화
- [ ] 이동 궤적 히스토리 시각화

---

## 📞 문의

문제가 발생하면 이슈를 등록해주세요:
- GitHub Issues: [Project Repository]

---

**마지막 업데이트**: 2026-01-25
**작성자**: Claude Sonnet 4.5
