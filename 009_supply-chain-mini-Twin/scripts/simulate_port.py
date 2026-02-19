# -*- coding: utf-8 -*-
"""
SimPy 선박 입출항 시뮬레이션
서해안 항만 (군산항 / 새만금항) 디지털 트윈 시뮬레이션

시뮬레이션 범위:
  - 입항 → 정박(Berth) 대기 → 하역(Unloading) → 통관(Customs) → 출항
  - 날씨 조건 반영 (풍속, 파고 → 작업 중단/지연)
  - 컨테이너 처리량 (TEU/일) 계산
  - 예상 도착 시간(ETA) 정밀 예측

결과 저장: simulation_results 테이블
"""

import os
import math
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import simpy
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SIM] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5900")),
    "dbname": os.getenv("DB_NAME", "supply_chain_db"),
    "user": os.getenv("DB_USER", "n8n_user"),
    "password": os.getenv("DB_PASS", "n8n_pass"),
}

# ============================================================
# 항만 설정 (실제 군산항/새만금항 스펙 기반)
# ============================================================
PORT_CONFIG = {
    "KRSMG": {
        "name": "새만금항",
        "berths": 4,                  # 동시 접안 선석 수
        "crane_rate_teu_hr": 25,      # 크레인 처리율 (TEU/hr)
        "crane_count": 6,
        "bulk_rate_ton_hr": 1200,     # 벌크 처리율 (톤/hr)
        "customs_staff": 3,           # 통관 담당자
        "tug_boats": 3,               # 예선
        "pilot_boats": 2,             # 도선선
        "wind_limit_kn": 20,          # 작업 중단 풍속 (kn)
        "wave_limit_m": 2.0,          # 작업 중단 파고 (m)
    },
    "KRGUN": {
        "name": "군산항",
        "berths": 6,
        "crane_rate_teu_hr": 22,
        "crane_count": 8,
        "bulk_rate_ton_hr": 1500,
        "customs_staff": 4,
        "tug_boats": 4,
        "pilot_boats": 3,
        "wind_limit_kn": 22,
        "wave_limit_m": 2.5,
    },
}

# 화물 유형별 처리 파라미터
CARGO_PARAMS = {
    "Container":   {"unit": "TEU",  "rate_key": "crane_rate_teu_hr",  "customs_hr_per_unit": 0.004},
    "Bulk":        {"unit": "톤",   "rate_key": "bulk_rate_ton_hr",   "customs_hr_per_unit": 0.001},
    "General":     {"unit": "톤",   "rate_key": "bulk_rate_ton_hr",   "customs_hr_per_unit": 0.002},
    "RoRo":        {"unit": "대",   "rate_key": "crane_rate_teu_hr",  "customs_hr_per_unit": 0.003},
}

# ============================================================
# 시뮬레이션 시간 단위: 분(min)
# 1 sim_time_unit = 1 분
# ============================================================
SIM_DURATION_DAYS = 3      # 시뮬레이션 기간 (일)
SIM_MINUTES = SIM_DURATION_DAYS * 24 * 60


class WeatherState:
    """현재 기상 상태 관리 (weather_data 테이블 최신값 사용)"""

    def __init__(self, db_config):
        self.db_config = db_config
        self.wind_kn    = 10.0
        self.wave_m     = 0.8
        self.nav_safety = "SAFE"
        self._load_latest()

    def _load_latest(self):
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT AVG(wind_speed_kn), AVG(wave_height_m),
                               (CASE WHEN MAX(CASE nav_safety
                                   WHEN 'DANGER'  THEN 3
                                   WHEN 'CAUTION' THEN 2
                                   ELSE 1 END) = 3 THEN 'DANGER'
                                WHEN MAX(CASE nav_safety
                                   WHEN 'DANGER'  THEN 3
                                   WHEN 'CAUTION' THEN 2
                                   ELSE 1 END) = 2 THEN 'CAUTION'
                                ELSE 'SAFE' END)
                        FROM weather_data
                        WHERE timestamp_utc = (SELECT MAX(timestamp_utc) FROM weather_data)
                    """)
                    row = cur.fetchone()
                    if row and row[0]:
                        self.wind_kn    = float(row[0])
                        self.wave_m     = float(row[1])
                        self.nav_safety = row[2]
                        logger.info(f"기상 로드: 풍속={self.wind_kn:.1f}kn, 파고={self.wave_m:.2f}m, 등급={self.nav_safety}")
        except Exception as e:
            logger.warning(f"기상 DB 조회 실패, 기본값 사용: {e}")


class PortSimulation:
    """SimPy 기반 항만 시뮬레이션"""

    def __init__(self, port_id: str, run_dt: datetime, weather: WeatherState, db_config: dict):
        self.port_id  = port_id
        self.port_cfg = PORT_CONFIG[port_id]
        self.run_dt   = run_dt
        self.weather  = weather
        self.db_cfg   = db_config
        self.results: List[Dict] = []

        self.env = simpy.Environment()

        # 자원 정의
        self.berths        = simpy.Resource(self.env, capacity=self.port_cfg["berths"])
        self.cranes        = simpy.Resource(self.env, capacity=self.port_cfg["crane_count"])
        self.customs_desks = simpy.Resource(self.env, capacity=self.port_cfg["customs_staff"])
        self.tug_boats     = simpy.Resource(self.env, capacity=self.port_cfg["tug_boats"])

    def _weather_delay_factor(self) -> float:
        """날씨에 따른 작업 지연 배율 (1.0 = 정상, >1.0 = 지연)"""
        factor = 1.0
        if self.weather.wind_kn > self.port_cfg["wind_limit_kn"]:
            factor *= 1.8  # 풍속 초과: 작업 80% 지연
        elif self.weather.wind_kn > self.port_cfg["wind_limit_kn"] * 0.7:
            factor *= 1.25
        if self.weather.wave_m > self.port_cfg["wave_limit_m"]:
            factor *= 1.6
        elif self.weather.wave_m > self.port_cfg["wave_limit_m"] * 0.8:
            factor *= 1.2
        return factor

    def _vessel_process(self, vessel_id: str, vessel_info: dict):
        """선박 한 척의 전체 프로세스 시뮬레이션"""
        arrive_min  = vessel_info["arrive_min"]    # 입항 예정 시각 (sim 분)
        cargo_type  = vessel_info["cargo_type"]
        cargo_qty   = vessel_info["cargo_qty"]
        cargo_unit  = vessel_info["cargo_unit"]

        port_name   = self.port_cfg["name"]
        params      = CARGO_PARAMS.get(cargo_type, CARGO_PARAMS["General"])
        delay_f     = self._weather_delay_factor()

        result = {
            "run_id":        f"{self.port_id}-{self.run_dt.strftime('%Y%m%d%H%M')}-{vessel_id}",
            "port_id":       self.port_id,
            "port_name":     port_name,
            "vessel_id":     vessel_id,
            "vessel_name":   vessel_info["vessel_name"],
            "vessel_type":   vessel_info["vessel_type"],
            "cargo_type":    cargo_type,
            "cargo_qty":     cargo_qty,
            "cargo_unit":    cargo_unit,
            "eta_planned":   (self.run_dt + timedelta(minutes=arrive_min)).strftime("%Y-%m-%d %H:%M:%S"),
            "sim_run_dt":    self.run_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "weather_wind_kn":   round(self.weather.wind_kn, 1),
            "weather_wave_m":    round(self.weather.wave_m, 2),
            "weather_nav_safety": self.weather.nav_safety,
            "delay_factor":  round(delay_f, 2),
            # 시뮬레이션 결과 (이후 채워짐)
            "berth_wait_min":    0,
            "unload_min":        0,
            "customs_min":       0,
            "total_port_min":    0,
            "eta_actual":        "",
            "throughput_teu":    0,
            "throughput_ton":    0,
            "crane_utilization": 0.0,
            "status":            "simulated",
        }

        # ── 1. 입항 대기 ──────────────────────────────────────
        yield self.env.timeout(arrive_min)
        berth_request_time = self.env.now

        with self.tug_boats.request() as tug_req:
            yield tug_req
            # 예선 이동 시간 (15~40분)
            tug_time = random.randint(15, 40)
            yield self.env.timeout(tug_time)

        # ── 2. 선석 대기 ─────────────────────────────────────
        with self.berths.request() as berth_req:
            yield berth_req
            berth_wait = self.env.now - berth_request_time
            result["berth_wait_min"] = int(berth_wait)

            # ── 3. 하역 ──────────────────────────────────────
            unload_start = self.env.now

            # 투입 크레인 수 계산
            cranes_needed = min(
                max(1, math.ceil(cargo_qty / 500)),
                self.port_cfg["crane_count"]
            )

            with self.cranes.request() as crane_req:
                yield crane_req

                if cargo_type in ("Container", "RoRo"):
                    rate = self.port_cfg["crane_rate_teu_hr"]
                    base_hr = cargo_qty / rate
                else:
                    rate = self.port_cfg["bulk_rate_ton_hr"]
                    base_hr = cargo_qty / rate

                # 날씨 지연 + 장비 효율 변동 (±10%)
                actual_hr = base_hr * delay_f * random.uniform(0.90, 1.10)
                unload_min = max(30, int(actual_hr * 60))
                yield self.env.timeout(unload_min)

                result["unload_min"] = unload_min
                if cargo_type in ("Container", "RoRo"):
                    result["throughput_teu"] = cargo_qty
                else:
                    result["throughput_ton"] = cargo_qty

                crane_util = min(100, (base_hr / actual_hr) * 100)
                result["crane_utilization"] = round(crane_util, 1)

            # ── 4. 통관 ──────────────────────────────────────
            customs_start = self.env.now
            with self.customs_desks.request() as cust_req:
                yield cust_req
                customs_hr  = cargo_qty * params["customs_hr_per_unit"] * delay_f
                customs_min = max(60, int(customs_hr * 60))
                yield self.env.timeout(customs_min)
                result["customs_min"] = customs_min

        # ── 5. 결과 계산 ─────────────────────────────────────
        total_min = self.env.now - arrive_min
        result["total_port_min"] = int(total_min)
        eta_actual = self.run_dt + timedelta(minutes=self.env.now)
        result["eta_actual"] = eta_actual.strftime("%Y-%m-%d %H:%M:%S")

        self.results.append(result)
        logger.info(
            f"  [{vessel_id}] {result['vessel_name'][:20]:20s} | "
            f"선석대기:{berth_wait:4.0f}분 | 하역:{unload_min:4d}분 | "
            f"통관:{customs_min:4d}분 | ETA: {result['eta_actual']}"
        )

    def _arrival_schedule(self) -> List[Dict]:
        """
        입항 예정 선박 스케줄 생성.
        실제 운영 시: ship_tracking 테이블의 ETA 데이터를 사용.
        """
        try:
            with psycopg2.connect(**self.db_cfg) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT st.ship_id, st.vessel_name, st.vessel_type,
                               st.eta_utc, st.dist_to_dest_nm, st.speed_kn,
                               st.destination
                        FROM ship_tracking st
                        INNER JOIN (
                            SELECT mmsi, MAX(timestamp_utc) as max_ts
                            FROM ship_tracking GROUP BY mmsi
                        ) latest ON st.mmsi = latest.mmsi AND st.timestamp_utc = latest.max_ts
                        WHERE st.destination = %s
                          AND st.nav_status != 'moored'
                        ORDER BY st.eta_utc
                    """, (self.port_id,))
                    rows = cur.fetchall()

                    if rows:
                        schedule = []
                        for row in rows:
                            ship_id, vname, vtype, eta_utc, dist_nm, speed, dest = row
                            eta_dt = datetime.strptime(str(eta_utc), "%Y-%m-%d %H:%M:%S") \
                                     if isinstance(eta_utc, str) else eta_utc
                            arrive_min = max(0, int((eta_dt - self.run_dt).total_seconds() / 60))

                            # 선박 유형으로 화물 유추
                            if "Container" in str(vtype):
                                cargo_type = "Container"; qty = random.randint(500, 2000); unit = "TEU"
                            elif "Bulk" in str(vtype):
                                cargo_type = "Bulk";      qty = random.randint(500, 5000); unit = "톤"
                            elif "RoRo" in str(vtype):
                                cargo_type = "RoRo";      qty = random.randint(100, 500);  unit = "대"
                            else:
                                cargo_type = "General";   qty = random.randint(300, 2000); unit = "톤"

                            schedule.append({
                                "vessel_id":   ship_id or f"SIM-{len(schedule)+1:03d}",
                                "vessel_name": vname,
                                "vessel_type": vtype,
                                "arrive_min":  arrive_min,
                                "cargo_type":  cargo_type,
                                "cargo_qty":   qty,
                                "cargo_unit":  unit,
                            })
                        logger.info(f"{self.port_cfg['name']}: DB에서 {len(schedule)}척 스케줄 로드")
                        return schedule

        except Exception as e:
            logger.warning(f"ship_tracking 조회 실패, 랜덤 스케줄 사용: {e}")

        # Fallback: 랜덤 스케줄 생성
        return self._random_schedule()

    def _random_schedule(self) -> List[Dict]:
        """DB 데이터 없을 때 사용하는 랜덤 입항 스케줄"""
        vessel_templates = [
            ("SIM-001", "SUNRISE JEONBUK",   "Bulk Carrier",   "Bulk",      2000, "톤"),
            ("SIM-002", "DONGBANG EXPRESS",  "Container Ship", "Container", 800,  "TEU"),
            ("SIM-003", "WEST SEA PRIDE",    "Bulk Carrier",   "Bulk",      3000, "톤"),
            ("SIM-004", "SAEMANGEUM STAR",   "General Cargo",  "General",   1500, "톤"),
            ("SIM-005", "CHINA PROSPERITY",  "Container Ship", "Container", 1200, "TEU"),
            ("SIM-006", "YELLOW SEA GIANT",  "Bulk Carrier",   "Bulk",      4000, "톤"),
            ("SIM-007", "GUNSAN GLORY",      "Container Ship", "Container", 600,  "TEU"),
            ("SIM-008", "NEW JEONBUK",       "RoRo Cargo",     "RoRo",      250,  "대"),
        ]

        schedule = []
        for i, (vid, vname, vtype, ctype, cqty, cunit) in enumerate(vessel_templates):
            # 3일 동안 랜덤 도착 (포아송 과정)
            arrive_min = random.randint(i * 120, min(i * 120 + 480, SIM_MINUTES - 60))
            schedule.append({
                "vessel_id":   vid,
                "vessel_name": vname,
                "vessel_type": vtype,
                "arrive_min":  arrive_min,
                "cargo_type":  ctype,
                "cargo_qty":   cqty + random.randint(-200, 200),
                "cargo_unit":  cunit,
            })
        schedule.sort(key=lambda x: x["arrive_min"])
        return schedule

    def run(self) -> List[Dict]:
        """시뮬레이션 실행"""
        logger.info(f"\n{'='*60}")
        logger.info(f"시뮬레이션 시작: {self.port_cfg['name']} ({self.port_id})")
        logger.info(f"기간: {self.run_dt} ~ {self.run_dt + timedelta(days=SIM_DURATION_DAYS)}")
        logger.info(f"날씨: 풍속={self.weather.wind_kn:.1f}kn, 파고={self.weather.wave_m:.2f}m ({self.weather.nav_safety})")
        logger.info(f"{'='*60}")

        schedule = self._arrival_schedule()
        for vessel_info in schedule:
            self.env.process(self._vessel_process(vessel_info["vessel_id"], vessel_info))

        self.env.run(until=SIM_MINUTES)

        logger.info(f"\n처리 완료: {len(self.results)}척")
        return self.results


# ============================================================
# KPI 집계
# ============================================================
def calc_kpis(results: List[Dict]) -> Dict:
    if not results:
        return {}

    total_teu = sum(r["throughput_teu"] for r in results)
    total_ton = sum(r["throughput_ton"] for r in results)
    avg_berth_wait = sum(r["berth_wait_min"] for r in results) / len(results)
    avg_unload     = sum(r["unload_min"] for r in results) / len(results)
    avg_customs    = sum(r["customs_min"] for r in results) / len(results)
    avg_total      = sum(r["total_port_min"] for r in results) / len(results)
    avg_crane_util = sum(r["crane_utilization"] for r in results) / len(results)

    weather_danger_cnt = sum(1 for r in results if r["weather_nav_safety"] == "DANGER")
    delay_factor_avg   = sum(r["delay_factor"] for r in results) / len(results)

    return {
        "vessel_count":       len(results),
        "total_teu":          total_teu,
        "total_ton":          total_ton,
        "teu_per_day":        round(total_teu / SIM_DURATION_DAYS, 1),
        "ton_per_day":        round(total_ton / SIM_DURATION_DAYS, 1),
        "avg_berth_wait_hr":  round(avg_berth_wait / 60, 2),
        "avg_unload_hr":      round(avg_unload / 60, 2),
        "avg_customs_hr":     round(avg_customs / 60, 2),
        "avg_total_port_hr":  round(avg_total / 60, 2),
        "avg_crane_util_pct": round(avg_crane_util, 1),
        "weather_impact_cnt": weather_danger_cnt,
        "delay_factor_avg":   round(delay_factor_avg, 2),
    }


# ============================================================
# DB 저장
# ============================================================
def save_results(results: List[Dict], db_config: dict) -> int:
    if not results:
        return 0

    sql = """
    INSERT INTO simulation_results (
        run_id, port_id, port_name, vessel_id, vessel_name, vessel_type,
        cargo_type, cargo_qty, cargo_unit,
        eta_planned, eta_actual, sim_run_dt,
        berth_wait_min, unload_min, customs_min, total_port_min,
        throughput_teu, throughput_ton, crane_utilization,
        weather_wind_kn, weather_wave_m, weather_nav_safety,
        delay_factor, status
    ) VALUES %s
    ON CONFLICT (run_id) DO UPDATE SET
        eta_actual          = EXCLUDED.eta_actual,
        berth_wait_min      = EXCLUDED.berth_wait_min,
        unload_min          = EXCLUDED.unload_min,
        customs_min         = EXCLUDED.customs_min,
        total_port_min      = EXCLUDED.total_port_min,
        throughput_teu      = EXCLUDED.throughput_teu,
        throughput_ton      = EXCLUDED.throughput_ton,
        crane_utilization   = EXCLUDED.crane_utilization,
        delay_factor        = EXCLUDED.delay_factor
    """

    rows = [
        (
            r["run_id"], r["port_id"], r["port_name"],
            r["vessel_id"], r["vessel_name"], r["vessel_type"],
            r["cargo_type"], r["cargo_qty"], r["cargo_unit"],
            r["eta_planned"], r["eta_actual"], r["sim_run_dt"],
            r["berth_wait_min"], r["unload_min"], r["customs_min"], r["total_port_min"],
            r["throughput_teu"], r["throughput_ton"], r["crane_utilization"],
            r["weather_wind_kn"], r["weather_wave_m"], r["weather_nav_safety"],
            r["delay_factor"], r["status"],
        )
        for r in results
    ]

    with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)
    return len(rows)


# ============================================================
# 메인
# ============================================================
def run_simulation():
    run_dt  = datetime.now()
    weather = WeatherState(DB_CONFIG)

    all_results = []
    for port_id in ["KRSMG", "KRGUN"]:
        sim = PortSimulation(port_id, run_dt, weather, DB_CONFIG)
        results = sim.run()
        kpis    = calc_kpis(results)

        logger.info(f"\n[KPI - {PORT_CONFIG[port_id]['name']}]")
        for k, v in kpis.items():
            logger.info(f"  {k:25s}: {v}")

        all_results.extend(results)

    # DB 저장
    try:
        n = save_results(all_results, DB_CONFIG)
        logger.info(f"\n시뮬레이션 결과 저장: {n}건 → simulation_results 테이블")
    except Exception as e:
        logger.error(f"DB 저장 실패: {e}")

    return all_results


if __name__ == "__main__":
    run_simulation()
