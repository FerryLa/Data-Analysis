# 대한민국 조선소·항만·도크 인터랙티브 지도

## 📋 프로젝트 개요

이 프로젝트는 대한민국 전역의 조선소, 항만, 도크 시설을 시각화한 인터랙티브 지도입니다.

### 포함 시설
- **대형 조선소**: HD현대중공업, 삼성중공업, 한화오션, HD현대삼호, HD현대미포
- **중소 조선소**: 케이조선, HJ중공업, 대선조선, 대한조선, HSG성동조선, SK오션플랜트 등
- **주요 항만**: 부산항, 인천항, 울산항, 광양항, 평택·당진항 등 무역항 및 연안항
- **도크**: 주요 조선소 내 건도크 시설

---

## 📁 파일 구성

```
📦 프로젝트 폴더
├── korea_shipyard_map.html     # 인터랙티브 지도 (메인 파일)
├── korea_shipyard_data.csv     # 데이터 파일 (CSV 형식)
├── korea_shipyard_data.geojson # 데이터 파일 (GeoJSON 형식)
└── README.md                   # 이 문서
```

---

## 📊 데이터 구조 설명

### CSV 파일 컬럼 정의

| 컬럼명 | 데이터 타입 | 설명 | 예시 |
|--------|------------|------|------|
| `id` | Integer | 고유 식별자 | 1, 2, 3... |
| `name` | String | 시설명 | HD현대중공업 울산조선소 |
| `category` | String | 대분류 | 조선소, 항만, 도크 |
| `subcategory` | String | 소분류 | 대형, 중소, 무역항, 연안항, 건도크 |
| `region` | String | 광역 행정구역 | 울산광역시, 경상남도 |
| `city` | String | 기초 행정구역 | 동구, 거제시 |
| `latitude` | Float | 위도 (WGS84) | 35.5089 |
| `longitude` | Float | 경도 (WGS84) | 129.4208 |
| `note` | String | 비고/특이사항 | 세계 최대 단일 조선소 |
| `data_source` | String | 데이터 출처 | 공식 홈페이지/위키피디아 |

### GeoJSON 구조

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 1,
        "name": "HD현대중공업 울산조선소",
        "category": "조선소",
        "subcategory": "대형",
        "region": "울산광역시",
        "city": "동구",
        "note": "세계 최대 단일 조선소"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [129.4208, 35.5089]  // [경도, 위도]
      }
    }
  ]
}
```

---

## 📍 데이터 출처 요약

| 출처 유형 | 상세 | 활용 데이터 |
|----------|------|------------|
| **공식 홈페이지** | 각 조선사·항만공사 웹사이트 | 주소, 시설 규모, 도크 사양 |
| **위키피디아** | 한국어/영어 위키백과 | 기업 연혁, 좌표 확인 |
| **해양수산부** | 항만편람, 항만정보 공개데이터 | 무역항/연안항 목록, 위치 |
| **언론보도** | 경제신문, 지역신문 | 최근 동향, 시설 변경사항 |
| **나무위키** | 조선업/조선소 문서 | 세부 사양, 역사적 맥락 |

### ⚠️ 좌표 정확도 안내
- **확인된 좌표**: 공식 주소 기반 지오코딩 또는 위성사진 확인
- **추정 좌표**: 조선소 내부 도크의 경우 대략적 위치 추정 (비고란에 [추정좌표] 표기)

---

## 🚀 사용 방법

### 1. 웹에서 바로 띄우기 (가장 간단)

#### 방법 A: 로컬 파일 열기
```
1. korea_shipyard_map.html 파일을 다운로드
2. 웹 브라우저(Chrome, Firefox, Edge 등)로 파일 열기
3. 인터넷 연결 필요 (OpenStreetMap 타일 로드)
```

#### 방법 B: 로컬 웹 서버 실행
```bash
# Python 3 사용
cd [프로젝트 폴더]
python -m http.server 8000

# 브라우저에서 접속
http://localhost:8000/korea_shipyard_map.html
```

#### 방법 C: VS Code Live Server
```
1. VS Code에서 Live Server 확장 설치
2. HTML 파일 우클릭 → "Open with Live Server"
```

---

### 2. QGIS에서 활용하기

#### GeoJSON 파일 불러오기
```
1. QGIS 실행
2. 레이어 → 레이어 추가 → 벡터 레이어 추가
3. korea_shipyard_data.geojson 선택
4. 좌표계: EPSG:4326 (WGS84) 확인
5. 추가 클릭
```

#### 스타일 설정
```
1. 레이어 패널에서 레이어 우클릭 → 속성
2. 심볼 탭에서 "범주형" 선택
3. 컬럼: category 또는 subcategory 선택
4. 분류 클릭 → 색상 지정
```

#### CSV 파일 불러오기
```
1. 레이어 → 레이어 추가 → 구분자로 분리된 텍스트 레이어 추가
2. korea_shipyard_data.csv 선택
3. 파일 형식: CSV
4. X 필드: longitude
5. Y 필드: latitude
6. 좌표계: EPSG:4326
7. 추가 클릭
```

---

### 3. Google My Maps에서 활용하기

#### CSV 가져오기
```
1. Google My Maps (https://www.google.com/mymaps) 접속
2. 새 지도 만들기
3. 가져오기 클릭
4. korea_shipyard_data.csv 업로드
5. 위치 열 선택: latitude, longitude
6. 마커 제목 열 선택: name
```

#### 스타일 지정
```
1. 개별 스타일 → 열별 스타일 지정
2. 그룹화 기준: category
3. 각 카테고리별 색상/아이콘 선택
```

---

### 4. Python에서 활용하기

#### 데이터 로드
```python
import pandas as pd
import geopandas as gpd

# CSV 로드
df = pd.read_csv('korea_shipyard_data.csv')

# GeoJSON 로드
gdf = gpd.read_file('korea_shipyard_data.geojson')

# 조선소만 필터링
shipyards = df[df['category'] == '조선소']

# 지역별 집계
region_stats = df.groupby('region').size()
```

#### Folium으로 시각화
```python
import folium

m = folium.Map(location=[36.0, 127.5], zoom_start=7)

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=8,
        popup=row['name'],
        color='red' if row['category'] == '조선소' else 'blue'
    ).add_to(m)

m.save('folium_map.html')
```

---

## 🔧 지도 기능 안내

### 레이어 컨트롤 (우측 상단)
- ✅ 대형 조선소 표시/숨김
- ✅ 중소 조선소 표시/숨김
- ✅ 무역항 표시/숨김
- ✅ 연안항 표시/숨김
- ✅ 도크 표시/숨김

### 검색 기능 (좌측 상단)
- 시설명 입력 시 자동 이동
- 2글자 이상 입력 필요

### 베이스맵 전환 (우측 하단)
- 밝은 지도 (기본)
- 어두운 지도
- OpenStreetMap

### 통계 패널 (좌측 하단)
- 전체 시설 수
- 카테고리별 집계

---

## 📜 라이선스 및 저작권

### 지도 데이터
- OpenStreetMap © OpenStreetMap contributors
- CARTO © CARTO

### 시설 데이터
- 공개적으로 확인 가능한 자료만 사용
- 군사·보안 시설 관련 정보 제외
- 상업적 활용 시 각 출처 확인 필요

---

## 📧 문의 및 업데이트

### 데이터 수정/추가 요청
- 새로운 조선소/항만 정보
- 좌표 오류 수정
- 폐업/신규 시설 반영

### 버전 정보
- 최초 작성: 2025년 1월
- 데이터 기준일: 2025년 1월

---

## 🗺️ 주요 조선소 위치 요약

| 조선소 | 위치 | 주요 특징 |
|--------|------|----------|
| HD현대중공업 | 울산 동구 | 세계 최대 단일 조선소, 드라이도크 9기 |
| 삼성중공업 | 거제 장평동 | 3도크, 세계적 규모 (640m×97.5m) |
| 한화오션 | 거제 옥포동 | 구 대우조선해양, LNG선 강자 |
| HD현대삼호 | 영암 삼호읍 | 호남권 유일 대형 조선소 |
| HD현대미포 | 울산 동구 | 중형선 세계 1위 |

---

*이 문서는 대한민국 조선·해양 산업 GIS 데이터 프로젝트의 일부입니다.*
