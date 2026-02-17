# ArcGIS 인터랙티브 지도 구현 가이드
## Phase 2: 중국(동아시아) - 항만 - 새만금 물류 이동 지도

---

## 개요
006_Panama_ArcGIS 프로젝트의 구현 패턴을 재활용하여
서해안 해상 물류 루트를 Power BI ArcGIS Maps로 시각화

### 지도 범위
- 중심: 서해(Yellow Sea) / 동중국해
- 영역: 위도 20°~42°N, 경도 105°~142°E
- 줌 레벨: 4~5 (동아시아 전체 조망)

---

## 레이어 구성

### Layer 1: 항만 마커 (Point Layer)
- **데이터**: `port_markers.csv`
- **스타일**:
  - 도착항(destination): ⭐ 노란 별 (size 30) — 군산항, 새만금항
  - 출발항(origin): 🔵 파란 원 (size 20) — 중국/일본/베트남
- **툴팁**: 항구명, 국가, 유형

### Layer 2: 해상 루트 (Line Layer)
- **데이터**: `sea_routes.csv`
- **XY to Line**: sequence 순서로 연결
- **색상**: route_id별 다른 색상
  - 중국→군산: 파란 계열 (#0078D4)
  - 중국→새만금: 초록 계열 (#107C10)
  - 일본→: 주황 (#FFB900)
  - 베트남→: 보라 (#5C2D91)
- **두께**: 2~3px
- **투명도**: 70%

### Layer 3: 새만금 물류 구역 (Point/Polygon Layer)
- **데이터**: `logistics_zones.csv`
- **스타일**: zone_type별 아이콘
  - 산업단지: 🏭
  - 물류센터: 📦
  - 자유무역: 🏢
  - 항만터미널: ⚓

### Layer 4: 실시간 선박 위치 (선택)
- **데이터**: `inbound_shipments.csv` → 항해중 선박만 필터
- **계산**: 출발시각/ETA/현재시간으로 현재 위치 보간
- **아이콘**: 🚢 선박 (상태별 색상)

---

## Power BI DAX - 선박 현재 위치 계산

```dax
// 항해 진행률 (0~1)
VoyageProgress =
VAR DepartDT = inbound_shipments[departure_dt]
VAR ArrivalDT = inbound_shipments[eta_actual]
VAR CurrentDT = NOW()
VAR TotalHours = DATEDIFF(DepartDT, ArrivalDT, HOUR)
VAR ElapsedHours = DATEDIFF(DepartDT, CurrentDT, HOUR)
RETURN
    IF(TotalHours > 0, MIN(1, MAX(0, ElapsedHours / TotalHours)), 0)

// 현재 위도 (선형 보간)
CurrentLatitude =
VAR Progress = [VoyageProgress]
VAR OriginLat = RELATED(port_markers[latitude])  // 출발항
VAR DestLat = 35.9  // 군산항/새만금항 근사값
RETURN
    OriginLat + (DestLat - OriginLat) * Progress

// 현재 경도
CurrentLongitude =
VAR Progress = [VoyageProgress]
VAR OriginLon = RELATED(port_markers[longitude])
VAR DestLon = 126.7  // 군산항/새만금항 근사값
RETURN
    OriginLon + (DestLon - OriginLon) * Progress
```

---

## ArcGIS Maps for Power BI 설정

### 1. Map 비주얼 추가
- 시각화 → ArcGIS Maps for Power BI
- 크기: 페이지 전체 또는 절반

### 2. 레이어 설정
```
Location: latitude, longitude
Size: marker_size
Color: port_type 또는 route_id
Tooltips: port_name, distance_nm, status
```

### 3. 베이스맵 선택
- **추천**: Navigation (Dark) — 해상 루트 가시성 최적
- **대안**: Oceans — 해양 데이터 특화

### 4. 참조 레이어
- World Countries (국가 경계)
- Major Ports (글로벌 항만)

---

## 인터랙티브 기능

### 슬라이서 연동
- 출발항 선택 → 해당 루트만 하이라이트
- 원자재 선택 → 관련 선적만 표시
- 날짜 범위 → 기간 필터

### 드릴다운
1. 지도에서 선박 클릭 → 선적 상세
2. 항만 클릭 → 입출항 현황
3. 새만금 구역 클릭 → 재고/생산 현황

### 툴팁 페이지
별도 Power BI 툴팁 페이지로 선박/항만 상세 정보 표시

---

## 서해 루트 특이사항

### 조석 / 기상 영향
- 서해는 조석간만의 차가 크므로 입항 시간 영향
- 겨울철 서해 기상 악화 → ETA 지연 빈도 증가

### 루트 패턴
```
상하이 → 서해 중앙 → 군산항: ~520 NM (약 29시간 @18kn)
칭다오 → 서해 직항 → 군산항: ~380 NM (약 21시간 @18kn)
닝보 → 동중국해 → 서해 → 군산항: ~560 NM (약 31시간)
톈진 → 발해만 → 서해 → 군산항: ~480 NM (약 27시간)
다롄 → 서해 북부 → 군산항: ~420 NM (약 23시간)
```

### 내륙 운송 구간 표시
```
군산항 → 새만금 물류센터: ~25km (트럭 30분)
새만금항 → 새만금 물류센터: ~5km (트럭 10분)
```
