# Power BI ArcGIS Maps 경로 선 그리기 완벽 가이드

## 📂 필요한 데이터 파일

1. **route_line_segments.csv** - 선(Line) 그리기용
2. **route_points_enhanced.csv** - 점 연결용 (대안)
3. **port_markers.csv** - 항구 마커용

---

## 🗺️ 방법 1: XY to Line (권장) ⭐

### Step 1: Power BI에 데이터 로드

1. **홈 → 데이터 가져오기 → 텍스트/CSV**
2. `route_line_segments.csv` 선택 → 로드
3. `port_markers.csv` 선택 → 로드

### Step 2: ArcGIS Maps 비주얼 추가

1. **시각화 → ArcGIS Maps for Power BI** 클릭
2. 캔버스에 비주얼 배치

### Step 3: 경로 선 설정

#### 레이어 1: 파나마 경유 (파란색 선)

1. **레이어 추가 (+ 버튼)**
2. **레이어 유형**: Reference Layer → **XY to Line** 선택
3. **데이터 필드 매핑**:
   ```
   Start Point X: origin_lon
   Start Point Y: origin_lat
   End Point X: dest_lon
   End Point Y: dest_lat
   ```
4. **필터**: `route_type = "파나마 경유"`
5. **스타일**:
   - 선 색상: 파란색 (#0078D4)
   - 선 두께: 3-4px
   - 선 스타일: 실선 (Solid)

#### 레이어 2: 남미 우회 (빨간색 선)

1. **레이어 추가 (+ 버튼)**
2. **레이어 유형**: Reference Layer → **XY to Line** 선택
3. **데이터 필드 매핑**:
   ```
   Start Point X: origin_lon
   Start Point Y: origin_lat
   End Point X: dest_lon
   End Point Y: dest_lat
   ```
4. **필터**: `route_type = "남미 우회"`
5. **스타일**:
   - 선 색상: 빨간색 (#D13438)
   - 선 두께: 3-4px
   - 선 스타일: 실선 (Solid)

#### 레이어 3: 주요 항구 마커

1. **레이어 추가 (+ 버튼)**
2. **레이어 유형**: Location → **Coordinates** 선택
3. **데이터**: `port_markers` 테이블
4. **필드 매핑**:
   ```
   Latitude: lat
   Longitude: lon
   ```
5. **스타일**:
   - 마커 크기: 12-15
   - 마커 색상: 노란색 (주요 항구), 초록색 (파나마운하)
   - 마커 모양: 별(star) 또는 원(circle)

---

## 🗺️ 방법 2: 점 연결 (대안)

ArcGIS에 "XY to Line" 기능이 없다면 이 방법을 사용하세요.

### Step 1: 데이터 로드

`route_points_enhanced.csv` 파일 로드

### Step 2: ArcGIS Maps 설정

1. **Location → Coordinates**
2. **필드 매핑**:
   ```
   Latitude: lat
   Longitude: lon
   Group By: route
   ```
3. **Sort By**: `seq` (오름차순)

### Step 3: 점을 선으로 표시

1. **스타일 → 점 유형**: "경로(Path)" 선택
2. **선 연결**: 자동으로 seq 순서대로 연결됨
3. **색상 구분**:
   - 범례 필드: `route`
   - 파나마 경유: 파란색
   - 남미 우회: 빨간색

---

## 🗺️ 방법 3: 기본 Map Visual 사용 (가장 간단)

ArcGIS가 복잡하다면 Power BI 기본 지도를 사용하세요.

### Step 1: Map Visual 추가

1. **시각화 → Map (기본 지도)**
2. 캔버스에 배치

### Step 2: 포인트 표시

1. **Location**: `lat`, `lon` (자동 인식)
2. **Legend**: `route`
3. **Size**: 고정값 또는 `seq`
4. **Tooltip**: `location`, `route`

### Step 3: 선 연결 (제한적)

- Map visual은 선을 직접 그릴 수 없음
- 점만 표시되며, 사용자가 시각적으로 경로 파악

---

## 🎨 스타일링 팁

### 선 스타일

```
파나마 경유:
- 색상: #0078D4 (파란색)
- 두께: 4px
- 투명도: 80%
- 스타일: 실선

남미 우회:
- 색상: #D13438 (빨간색)
- 두께: 4px
- 투명도: 80%
- 스타일: 실선
```

### 마커 스타일

```
주요 항구:
- 색상: #FFB900 (노란색)
- 크기: 15
- 모양: 별(star)

파나마운하:
- 색상: #107C10 (초록색)
- 크기: 12
- 모양: 원(circle)
```

### 배경 지도

- **지도 스타일**: Dark Gray Canvas (어두운 배경)
- **줌 레벨**: 전 세계가 보이도록 (Zoom level 2-3)
- **중심점**: 태평양 중앙 (lat: 0, lon: -150)

---

## 🔧 문제 해결 (Troubleshooting)

### 문제 1: 선이 안 그려져요

**원인**: XY to Line 기능이 없거나 데이터 매핑 오류

**해결**:
1. ArcGIS Maps 버전 확인 (최신 버전 사용)
2. 필드 매핑 재확인:
   - Start X/Y: 출발 좌표
   - End X/Y: 도착 좌표
3. 데이터 타입 확인 (숫자여야 함)

### 문제 2: 선이 이상하게 그려져요

**원인**: 경도/위도 순서 혼동

**해결**:
- X축 = 경도 (Longitude, -180 ~ 180)
- Y축 = 위도 (Latitude, -90 ~ 90)

### 문제 3: 지도가 안 보여요

**원인**: ArcGIS 계정 필요 또는 네트워크 문제

**해결**:
1. ArcGIS 계정 로그인
2. Power BI Service에서는 Premium 필요 (Desktop은 무료)
3. 대안: 기본 Map visual 사용

### 문제 4: 선이 너무 직선이에요

**원인**: 대권항로(Great Circle) 표시 안 됨

**해결**:
- ArcGIS는 측지선(Geodesic line) 옵션 사용
- 설정 → Line Type → Geodesic

---

## 📊 데이터 필드 설명

### route_line_segments.csv

| 필드 | 설명 | 예시 |
|------|------|------|
| route_type | 항로 유형 | "파나마 경유" |
| segment_num | 구간 번호 | 1, 2, 3 |
| origin | 출발지 | "부산" |
| destination | 도착지 | "파나마운하_태평양" |
| origin_lat | 출발 위도 | 35.1796 |
| origin_lon | 출발 경도 | 129.0756 |
| dest_lat | 도착 위도 | 8.9139 |
| dest_lon | 도착 경도 | -79.5733 |
| color | 선 색상 | "blue" |

### port_markers.csv

| 필드 | 설명 | 예시 |
|------|------|------|
| port | 항구명 | "부산" |
| lat | 위도 | 35.1796 |
| lon | 경도 | 129.0756 |
| type | 항구 유형 | "출발지" |
| marker_color | 마커 색상 | "yellow" |
| marker_symbol | 마커 모양 | "star" |

---

## 🚀 추천 워크플로우

### 초보자용 (5분)

1. `port_markers.csv`만 로드
2. 기본 Map visual 사용
3. 점만 표시 (경로는 사용자 상상)

### 중급자용 (15분)

1. `route_points_enhanced.csv` 로드
2. ArcGIS Maps 사용
3. 점 연결 기능으로 경로 표시

### 고급자용 (30분)

1. `route_line_segments.csv` + `port_markers.csv` 로드
2. ArcGIS Maps - XY to Line
3. 레이어별 스타일링
4. 인터랙티브 툴팁 추가

---

## 💡 Pro Tips

1. **선 애니메이션**: ArcGIS Premium 기능으로 선이 움직이게 표시 가능
2. **3D 지구본**: ArcGIS 3D 모드로 전환하여 입체감 추가
3. **히트맵 추가**: 항로별 물동량을 히트맵으로 표시
4. **시간 슬라이더**: 월별 데이터와 연동하여 시간 경과 표시

---

## 📚 참고 자료

- [ArcGIS Maps for Power BI 공식 문서](https://doc.arcgis.com/en/power-bi/)
- [Power BI Map Visual 가이드](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-map-tips-and-tricks)

---

## ✅ 최종 체크리스트

- [ ] route_line_segments.csv 로드됨
- [ ] port_markers.csv 로드됨
- [ ] ArcGIS Maps 비주얼 추가됨
- [ ] XY to Line 레이어 생성됨 (파나마 경유)
- [ ] XY to Line 레이어 생성됨 (남미 우회)
- [ ] 항구 마커 레이어 추가됨
- [ ] 선 색상 구분됨 (파란색/빨간색)
- [ ] 지도 줌 레벨 조정됨
- [ ] 툴팁 설정 완료

---

**작성일**: 2025-01-19  
**버전**: 1.0  
**난이도**: 중급
