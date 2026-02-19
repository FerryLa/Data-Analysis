# -*- coding: utf-8 -*-
"""
AIS 선박 위치 + 날씨 데이터 수집기
- 실제 AIS API (MarineTraffic / AISHub) 구조 기반 샘플 데이터 생성
- 실제 날씨 API (OpenMeteo Marine) 구조 기반 샘플 데이터 생성
- PostgreSQL (scm-postgres) 저장

실제 운영 시 교체 포인트:
  - AIS: https://www.marinetraffic.com/en/ais-api-services  (유료)
          https://www.aishub.net/api  (무료 티어)
  - 날씨: https://open-meteo.com/en/docs/marine-weather-api  (무료)
"""

import os
import math
import random
import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ============================================================
# DB 연결 설정
# ============================================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5900")),
    "dbname": os.getenv("DB_NAME", "supply_chain_db"),
    "user": os.getenv("DB_USER", "n8n_user"),
    "password": os.getenv("DB_PASS", "n8n_pass"),
}

# ============================================================
# 서해안 항로 정의 (실제 AIS 좌표 기반)
# ============================================================
PORT_COORDS = {
    "KRSMG": {"lat": 35.8300, "lon": 126.6100, "name": "새만금항"},
    "KRGUN": {"lat": 35.9823, "lon": 126.7161, "name": "군산항"},
    "CNSHA": {"lat": 31.2304, "lon": 121.4737, "name": "상하이항"},
    "CNDLC": {"lat": 38.9140, "lon": 121.6147, "name": "다롄항"},
    "CNQDG": {"lat": 36.0671, "lon": 120.3826, "name": "칭다오항"},
    "CNNBO": {"lat": 29.8683, "lon": 121.5440, "name": "닝보항"},
    "CNTXG": {"lat": 39.0042, "lon": 117.7149, "name": "톈진항"},
    "VNHPH": {"lat": 20.8449, "lon": 106.6881, "name": "하이퐁항"},
}

# 서해 (Yellow Sea) 중간 웨이포인트 (실제 항로 기반)
WAYPOINTS = {
    "CNSHA_KRSMG": [
        (31.50, 122.50), (32.00, 123.50), (33.00, 124.00),
        (34.00, 124.50), (35.00, 125.50), (35.50, 126.20),
    ],
    "CNDLC_KRSMG": [
        (38.50, 122.00), (37.50, 123.00), (36.50, 124.00),
        (35.50, 125.50), (35.50, 126.20),
    ],
    "CNQDG_KRGUN": [
        (36.00, 121.00), (36.00, 122.50), (36.00, 124.00),
        (36.00, 125.50), (35.98, 126.50),
    ],
}

# 선박 마스터 데이터 (실제 IMO 번호 형식)
VESSEL_FLEET = [
    {"imo": "9800005", "mmsi": "440123456", "name": "SUNRISE JEONBUK",   "type": "Bulk Carrier",      "flag": "KR", "length": 189, "beam": 28, "max_speed": 14.5},
    {"imo": "9800006", "mmsi": "440234567", "name": "DONGBANG EXPRESS",  "type": "Container Ship",    "flag": "KR", "length": 220, "beam": 32, "max_speed": 18.0},
    {"imo": "9800007", "mmsi": "440345678", "name": "WEST SEA PRIDE",    "type": "Bulk Carrier",      "flag": "KR", "length": 195, "beam": 30, "max_speed": 13.8},
    {"imo": "9800008", "mmsi": "440456789", "name": "SAEMANGEUM STAR",   "type": "General Cargo",     "flag": "KR", "length": 145, "beam": 22, "max_speed": 12.5},
    {"imo": "9800009", "mmsi": "412567890", "name": "CHINA PROSPERITY",  "type": "Container Ship",    "flag": "CN", "length": 260, "beam": 40, "max_speed": 20.0},
    {"imo": "9800010", "mmsi": "412678901", "name": "YELLOW SEA GIANT",  "type": "Bulk Carrier",      "flag": "CN", "length": 210, "beam": 32, "max_speed": 13.0},
    {"imo": "9800011", "mmsi": "440789012", "name": "GUNSAN GLORY",      "type": "Container Ship",    "flag": "KR", "length": 175, "beam": 26, "max_speed": 16.0},
    {"imo": "9800012", "mmsi": "440890123", "name": "NEW JEONBUK",       "type": "RoRo Cargo",        "flag": "KR", "length": 165, "beam": 25, "max_speed": 15.5},
]

# ============================================================
# 유틸리티
# ============================================================
def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """두 좌표 간 거리 (해리, nm)"""
    R = 3440.065  # 지구 반경 (nm)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def interpolate_position(lat1, lon1, lat2, lon2, fraction: float):
    """두 좌표 간 선형 보간"""
    lat = lat1 + (lat2 - lat1) * fraction
    lon = lon1 + (lon2 - lon1) * fraction
    return lat, lon


def calc_bearing(lat1, lon1, lat2, lon2) -> float:
    """진행 방위각 (도)"""
    dlon = math.radians(lon2 - lon1)
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    x = math.sin(dlon) * math.cos(lat2r)
    y = math.cos(lat1r)*math.sin(lat2r) - math.sin(lat1r)*math.cos(lat2r)*math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


# ============================================================
# AIS 샘플 데이터 생성 (실제 MarineTraffic API 응답 구조)
# ============================================================
class AISDataCollector:
    """
    실제 AIS API 응답 구조를 재현한 샘플 데이터 생성기.

    실제 API 연동 시:
        import requests
        url = "https://services.marinetraffic.com/api/exportvessel/v:8/{API_KEY}"
        params = {"MMSI": mmsi, "protocol": "json"}
        response = requests.get(url, params=params)
        data = response.json()
    """

    def __init__(self):
        self.active_voyages = self._init_voyages()

    def _init_voyages(self) -> list:
        """활성 항해 상태 초기화 (각 선박의 현재 위치 추정)"""
        now = datetime.now()
        voyages = []

        routes = [
            ("CNSHA", "KRSMG", "SH-1003"),
            ("CNDLC", "KRSMG", "SH-1001"),
            ("CNQDG", "KRGUN", "SH-1002"),
            ("CNNBO", "KRSMG", "SH-1005"),
            ("CNTXG", "KRSMG", "SH-1006"),
            ("CNDLC", "KRGUN", "SH-1007"),
            ("CNSHA", "KRSMG", "SH-1008"),
            ("CNQDG", "KRSMG", "SH-1009"),
        ]

        for i, (vessel, (origin, dest, ship_id)) in enumerate(
            zip(VESSEL_FLEET, routes)
        ):
            origin_c = PORT_COORDS[origin]
            dest_c = PORT_COORDS[dest]
            total_dist = haversine_distance(
                origin_c["lat"], origin_c["lon"],
                dest_c["lat"], dest_c["lon"]
            )
            speed = vessel["max_speed"] * random.uniform(0.75, 0.92)
            total_hours = total_dist / speed
            elapsed_pct = random.uniform(0.1, 0.9)

            depart_dt = now - timedelta(hours=total_hours * elapsed_pct)
            eta_dt = depart_dt + timedelta(hours=total_hours)

            voyages.append({
                "vessel": vessel,
                "ship_id": ship_id,
                "origin": origin,
                "dest": dest,
                "speed_kn": speed,
                "total_dist_nm": total_dist,
                "total_hours": total_hours,
                "elapsed_pct": elapsed_pct,
                "depart_dt": depart_dt,
                "eta_dt": eta_dt,
                "status": "underway",
            })

        return voyages

    def fetch(self) -> list:
        """
        AIS 위치 데이터 수집 (샘플).
        실제 API 연동 시 이 메서드를 교체.

        반환 형식은 AISHub / MarineTraffic 공통 스키마 준수:
        {
            "mmsi", "imo", "vessel_name", "vessel_type",
            "latitude", "longitude", "speed_kn", "course_deg",
            "heading_deg", "nav_status", "destination",
            "eta_utc", "timestamp_utc"
        }
        """
        now = datetime.utcnow()
        records = []

        for voyage in self.active_voyages:
            vessel = voyage["vessel"]
            origin = PORT_COORDS[voyage["origin"]]
            dest   = PORT_COORDS[voyage["dest"]]

            # 경과 시간으로 현재 위치 계산
            elapsed_hours = (now - voyage["depart_dt"].replace(tzinfo=None)).total_seconds() / 3600
            elapsed_pct = min(elapsed_hours / voyage["total_hours"], 1.0)

            lat, lon = interpolate_position(
                origin["lat"], origin["lon"],
                dest["lat"],   dest["lon"],
                elapsed_pct
            )

            # 실제 AIS 노이즈 시뮬레이션 (GPS 오차 ±0.002도 ≈ 200m)
            lat += random.gauss(0, 0.002)
            lon += random.gauss(0, 0.002)

            bearing = calc_bearing(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
            speed = voyage["speed_kn"] * random.uniform(0.97, 1.03)

            # 날씨 영향: 풍속 > 20kn 시 감속
            nav_status = "underway_engine"
            if elapsed_pct >= 0.98:
                nav_status = "moored"
                speed = 0.0

            eta_remaining = max(voyage["total_hours"] - elapsed_hours, 0)
            eta_utc = now + timedelta(hours=eta_remaining)

            records.append({
                "mmsi": vessel["mmsi"],
                "imo": vessel["imo"],
                "vessel_name": vessel["name"],
                "vessel_type": vessel["type"],
                "flag": vessel["flag"],
                "length_m": vessel["length"],
                "beam_m": vessel["beam"],
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "speed_kn": round(speed, 1),
                "course_deg": round(bearing, 1),
                "heading_deg": round(bearing + random.uniform(-5, 5), 1),
                "nav_status": nav_status,
                "destination": voyage["dest"],
                "destination_name": PORT_COORDS[voyage["dest"]]["name"],
                "eta_utc": eta_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "origin_port": voyage["origin"],
                "ship_id": voyage["ship_id"],
                "dist_to_dest_nm": round(haversine_distance(lat, lon, dest["lat"], dest["lon"]), 1),
                "voyage_progress_pct": round(elapsed_pct * 100, 1),
                "timestamp_utc": now.strftime("%Y-%m-%d %H:%M:%S"),
            })

        return records


# ============================================================
# 날씨 데이터 생성 (OpenMeteo Marine API 구조)
# ============================================================
class WeatherDataCollector:
    """
    서해 기상 데이터 수집기.

    실제 API 연동 시 (OpenMeteo - 무료):
        import requests
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": 35.5, "longitude": 124.0,
            "hourly": "wave_height,wind_speed_10m,ocean_current_velocity",
            "timezone": "Asia/Seoul"
        }
        response = requests.get(url, params=params)
    """

    # 서해 관측 포인트 (실제 기상청 해양기상부이 위치 기반)
    OBSERVATION_POINTS = [
        {"point_id": "WP-01", "name": "군산 서방 해상",  "lat": 35.80, "lon": 125.50},
        {"point_id": "WP-02", "name": "새만금 인근",     "lat": 35.83, "lon": 126.00},
        {"point_id": "WP-03", "name": "서해 중부",       "lat": 34.50, "lon": 124.50},
        {"point_id": "WP-04", "name": "서해 북부",       "lat": 37.00, "lon": 123.50},
        {"point_id": "WP-05", "name": "군산항 입구",     "lat": 35.95, "lon": 126.50},
    ]

    def fetch(self) -> list:
        """
        기상 데이터 수집 (샘플).
        겨울/봄 서해 실측값 범위 기준:
          - 풍속: 5~25 m/s (겨울 북서풍 계절풍)
          - 파고: 0.3~3.5 m
          - 조류 유속: 0.5~2.5 knot
          - 기온: -2~12 °C (2월)
          - 해수온: 4~10 °C
        """
        now = datetime.utcnow()
        records = []

        # 겨울 서해 계절풍 패턴 (북서풍 우세)
        hour = now.hour
        base_wind = 8 + 6 * math.sin(math.pi * hour / 12)  # 주간 변동
        tide_phase = (now.minute / 60) * 2 * math.pi       # 조석 위상

        for pt in self.OBSERVATION_POINTS:
            # 관측 포인트별 미세 차이
            wind_noise = random.gauss(0, 1.5)
            wave_noise = random.gauss(0, 0.15)

            wind_speed = max(0, base_wind + wind_noise)
            wind_dir   = 315 + random.uniform(-30, 30)  # 북서풍 (NW)
            wave_height = max(0.1, 0.5 + wind_speed * 0.08 + wave_noise)
            wave_period = max(3, 4 + wave_height * 1.5)

            # 조류 (태안반도 ~ 군산 구간 최대 4kn)
            tidal_current = 1.5 + 1.0 * math.sin(tide_phase)
            current_dir   = 180 + 90 * math.sin(tide_phase)  # 남북 조류

            # 가시거리 (안개/황사 시즌)
            visibility_km = random.choices(
                [1, 3, 5, 10, 20],
                weights=[5, 10, 15, 40, 30]
            )[0]

            # 항행 안전 등급
            if wind_speed > 20 or wave_height > 3.0:
                nav_safety = "DANGER"
            elif wind_speed > 14 or wave_height > 2.0:
                nav_safety = "CAUTION"
            else:
                nav_safety = "SAFE"

            records.append({
                "point_id": pt["point_id"],
                "point_name": pt["name"],
                "latitude": pt["lat"],
                "longitude": pt["lon"],
                "wind_speed_ms": round(wind_speed, 1),
                "wind_speed_kn": round(wind_speed * 1.944, 1),
                "wind_direction_deg": round(wind_dir % 360, 1),
                "wave_height_m": round(wave_height, 2),
                "wave_period_s": round(wave_period, 1),
                "tidal_current_kn": round(tidal_current, 2),
                "current_direction_deg": round(current_dir % 360, 1),
                "water_temp_c": round(random.uniform(4, 9), 1),
                "air_temp_c": round(random.uniform(-2, 12), 1),
                "visibility_km": visibility_km,
                "pressure_hpa": round(random.uniform(1005, 1025), 1),
                "nav_safety": nav_safety,
                "source": "OpenMeteo-Marine-Sample",
                "timestamp_utc": now.strftime("%Y-%m-%d %H:%M:%S"),
            })

        return records


# ============================================================
# PostgreSQL 저장
# ============================================================
class DataLoader:

    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def save_ais(self, records: list) -> int:
        """ship_tracking 테이블에 upsert"""
        if not records:
            return 0

        sql = """
        INSERT INTO ship_tracking (
            mmsi, imo, vessel_name, vessel_type, flag, length_m, beam_m,
            latitude, longitude, speed_kn, course_deg, heading_deg,
            nav_status, destination, destination_name, eta_utc,
            origin_port, ship_id, dist_to_dest_nm,
            voyage_progress_pct, timestamp_utc
        ) VALUES %s
        ON CONFLICT (mmsi, timestamp_utc) DO UPDATE SET
            latitude            = EXCLUDED.latitude,
            longitude           = EXCLUDED.longitude,
            speed_kn            = EXCLUDED.speed_kn,
            course_deg          = EXCLUDED.course_deg,
            nav_status          = EXCLUDED.nav_status,
            dist_to_dest_nm     = EXCLUDED.dist_to_dest_nm,
            voyage_progress_pct = EXCLUDED.voyage_progress_pct
        """

        rows = [
            (
                r["mmsi"], r["imo"], r["vessel_name"], r["vessel_type"],
                r["flag"], r["length_m"], r["beam_m"],
                r["latitude"], r["longitude"], r["speed_kn"],
                r["course_deg"], r["heading_deg"], r["nav_status"],
                r["destination"], r["destination_name"], r["eta_utc"],
                r["origin_port"], r["ship_id"], r["dist_to_dest_nm"],
                r["voyage_progress_pct"], r["timestamp_utc"],
            )
            for r in records
        ]

        with self._connect() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, rows)
        return len(rows)

    def save_weather(self, records: list) -> int:
        """weather_data 테이블에 insert"""
        if not records:
            return 0

        sql = """
        INSERT INTO weather_data (
            point_id, point_name, latitude, longitude,
            wind_speed_ms, wind_speed_kn, wind_direction_deg,
            wave_height_m, wave_period_s,
            tidal_current_kn, current_direction_deg,
            water_temp_c, air_temp_c, visibility_km, pressure_hpa,
            nav_safety, source, timestamp_utc
        ) VALUES %s
        ON CONFLICT (point_id, timestamp_utc) DO UPDATE SET
            wind_speed_ms      = EXCLUDED.wind_speed_ms,
            wind_speed_kn      = EXCLUDED.wind_speed_kn,
            wave_height_m      = EXCLUDED.wave_height_m,
            tidal_current_kn   = EXCLUDED.tidal_current_kn,
            nav_safety         = EXCLUDED.nav_safety
        """

        rows = [
            (
                r["point_id"], r["point_name"], r["latitude"], r["longitude"],
                r["wind_speed_ms"], r["wind_speed_kn"], r["wind_direction_deg"],
                r["wave_height_m"], r["wave_period_s"],
                r["tidal_current_kn"], r["current_direction_deg"],
                r["water_temp_c"], r["air_temp_c"], r["visibility_km"],
                r["pressure_hpa"], r["nav_safety"], r["source"], r["timestamp_utc"],
            )
            for r in records
        ]

        with self._connect() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, rows)
        return len(rows)


# ============================================================
# 메인 수집 루프
# ============================================================
def run_collection(interval_sec: int = 600, max_cycles: int = None):
    """
    데이터 수집 루프
    interval_sec: 수집 주기 (기본 10분 = 600초)
    max_cycles: None이면 무한 루프
    """
    ais_collector     = AISDataCollector()
    weather_collector = WeatherDataCollector()
    loader            = DataLoader(DB_CONFIG)

    cycle = 0
    logger.info(f"수집 시작 | 주기: {interval_sec}초 | DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

    while True:
        cycle += 1
        logger.info(f"--- 수집 사이클 #{cycle} ---")

        try:
            # AIS 수집
            ais_data = ais_collector.fetch()
            n_ais = loader.save_ais(ais_data)
            logger.info(f"AIS 저장 완료: {n_ais}건")

            # 날씨 수집
            wx_data = weather_collector.fetch()
            n_wx = loader.save_weather(wx_data)
            logger.info(f"날씨 저장 완료: {n_wx}건")

            # 간단한 현황 출력
            for r in ais_data:
                logger.info(
                    f"  [{r['vessel_name']:20s}] {r['nav_status']:15s} | "
                    f"({r['latitude']:.3f}, {r['longitude']:.3f}) | "
                    f"{r['speed_kn']}kn | {r['dist_to_dest_nm']}nm 남음 | "
                    f"ETA {r['eta_utc']}"
                )

        except psycopg2.OperationalError as e:
            logger.error(f"DB 연결 실패: {e}")
        except Exception as e:
            logger.error(f"수집 오류: {e}", exc_info=True)

        if max_cycles and cycle >= max_cycles:
            logger.info("지정 사이클 완료, 종료")
            break

        logger.info(f"다음 수집까지 {interval_sec}초 대기...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIS + Weather 데이터 수집기")
    parser.add_argument("--interval", type=int, default=600, help="수집 주기(초), 기본 600")
    parser.add_argument("--cycles",   type=int, default=1,   help="수집 횟수 (0=무한)")
    args = parser.parse_args()

    max_cycles = args.cycles if args.cycles > 0 else None
    run_collection(interval_sec=args.interval, max_cycles=max_cycles)
