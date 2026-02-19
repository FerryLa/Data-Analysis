# Digital Twin 파이프라인 가이드
> Phase 4: AIS 수집 + SimPy 시뮬레이션 + Redash 대시보드

## 아키텍처

```
[AIS 샘플 데이터]          [날씨 샘플 데이터]
 collect_ais_weather.py  ─────────────────────┐
        │                                     │
        ▼                                     ▼
  ship_tracking (DB)              weather_data (DB)
        │                                     │
        └──────────────┬──────────────────────┘
                       ▼
              simulate_port.py (SimPy)
                       │
                       ▼
          simulation_results (DB)
                       │
                       ▼
            Redash 대시보드
       Dashboard 4: 선박 추적
       Dashboard 5: 시뮬레이션 KPI
```

## 실행 방법

### 1. Docker 시작
```bash
cd docker
docker compose up -d
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 디지털 트윈 실행

```bash
# 1회 전체 파이프라인 (스키마 → 수집 → 시뮬레이션)
python scripts/run_digital_twin.py --mode once

# 10분 주기 반복 실행
python scripts/run_digital_twin.py --mode loop

# 단계별 실행
python scripts/run_digital_twin.py --mode schema    # DB 스키마만
python scripts/run_digital_twin.py --mode collect   # AIS+날씨 수집만
python scripts/run_digital_twin.py --mode simulate  # 시뮬레이션만
```

## 생성 파일

| 파일 | 역할 |
|------|------|
| `scripts/collect_ais_weather.py` | AIS 선박 위치 + 서해 기상 수집기 |
| `scripts/simulate_port.py` | SimPy 항만 입출항 시뮬레이션 |
| `scripts/run_digital_twin.py` | 통합 실행기 |
| `scripts/init_digital_twin.sql` | DB 스키마 (테이블 3개 + 뷰 4개) |
| `redash/queries.sql` | Redash 쿼리 (Q4-1~Q4-4, Q5-1~Q5-4) |

## DB 테이블

| 테이블 | 설명 | 주기 |
|--------|------|------|
| `ship_tracking` | AIS 선박 위치 (8척) | 10분 |
| `weather_data` | 서해 기상 (관측 5포인트) | 10분 |
| `simulation_results` | SimPy 예측 결과 | 수집마다 |

## DB 뷰 (Redash 연결용)

| 뷰 | 설명 |
|----|------|
| `v_ship_positions` | 현재 선박 위치 최신 스냅샷 |
| `v_port_eta` | AIS ETA vs SimPy ETA 비교 (핵심!) |
| `v_sim_kpi` | 항만별 일별 KPI 집계 |
| `v_twin_dashboard` | 통합 현황판 단일 행 KPI |

## Redash 대시보드 쿼리

### Dashboard 4: 선박 실시간 추적
- **Q4-1** `v_ship_positions` → 선박 위치 + 기상 등급 테이블
- **Q4-2** `v_port_eta` → AIS ETA vs 시뮬레이션 ETA 비교표
- **Q4-3** `weather_data` → 관측 포인트별 기상 현황
- **Q4-4** `weather_data` → 24시간 풍속/파고 시계열 차트

### Dashboard 5: 시뮬레이션 KPI
- **Q5-1** `v_sim_kpi` → 항만별 일별 처리량
- **Q5-2** `simulation_results` → 선박별 상세 결과
- **Q5-3** `v_twin_dashboard` → 통합 현황판 KPI
- **Q5-4** `simulation_results` → 선종별 효율 비교

## 실제 API 연동 포인트

### AIS (collect_ais_weather.py)
```python
# AISDataCollector.fetch() 메서드를 교체
import requests
url = "https://services.marinetraffic.com/api/exportvessel/v:8/{API_KEY}"
response = requests.get(url, params={"MMSI": mmsi, "protocol": "json"})
```
- **MarineTraffic**: https://www.marinetraffic.com/en/ais-api-services (유료)
- **AISHub**: https://www.aishub.net/api (무료 티어)

### 날씨 (collect_ais_weather.py)
```python
# WeatherDataCollector.fetch() 메서드를 교체
import requests
url = "https://marine-api.open-meteo.com/v1/marine"
params = {
    "latitude": 35.83, "longitude": 126.0,
    "hourly": "wave_height,wind_speed_10m,ocean_current_velocity"
}
response = requests.get(url, params=params)
```
- **OpenMeteo Marine**: https://open-meteo.com/en/docs/marine-weather-api (무료)

## 시뮬레이션 파라미터

### 항만 설정 (simulate_port.py → PORT_CONFIG)
| 항만 | 선석 수 | 크레인 | 처리율(TEU/hr) | 벌크(톤/hr) |
|------|---------|--------|----------------|-------------|
| 새만금항 | 4선석 | 6대 | 25 TEU/hr | 1,200 톤/hr |
| 군산항 | 6선석 | 8대 | 22 TEU/hr | 1,500 톤/hr |

### 날씨 영향 (지연 배율)
| 조건 | 배율 |
|------|------|
| 정상 | 1.0× |
| 풍속 > 14kn | 1.25× |
| 풍속 > 20kn (작업 중단 기준) | 1.8× |
| 파고 > 1.6m | 1.2× |
| 파고 > 2.0m (작업 중단 기준) | 1.6× |
