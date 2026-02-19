# -*- coding: utf-8 -*-
"""
디지털 트윈 통합 실행기
순서: DB 스키마 적용 → AIS/날씨 수집 → SimPy 시뮬레이션 → 결과 확인

사용법:
  python scripts/run_digital_twin.py --mode once      # 1회 실행 (기본)
  python scripts/run_digital_twin.py --mode loop      # 10분 주기 반복
  python scripts/run_digital_twin.py --mode schema    # DB 스키마만 적용
  python scripts/run_digital_twin.py --mode collect   # 수집만
  python scripts/run_digital_twin.py --mode simulate  # 시뮬레이션만
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime

import psycopg2

# 현재 파일 위치 기준으로 모듈 경로 추가
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TWIN] %(message)s",
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


def apply_schema():
    """디지털 트윈 DB 스키마 적용"""
    sql_path = os.path.join(SCRIPTS_DIR, "init_digital_twin.sql")
    logger.info(f"스키마 적용: {sql_path}")

    with open(sql_path, encoding="utf-8") as f:
        sql = f.read()

    with psycopg2.connect(**DB_CONFIG) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
    logger.info("스키마 적용 완료")


def run_collection(cycles=1):
    """AIS + 날씨 데이터 수집"""
    from collect_ais_weather import run_collection as _collect
    logger.info("=== AIS + 날씨 데이터 수집 시작 ===")
    _collect(interval_sec=1, max_cycles=cycles)  # 테스트: 1초 간격
    logger.info("=== 수집 완료 ===")


def run_simulation():
    """SimPy 시뮬레이션 실행"""
    from simulate_port import run_simulation as _simulate
    logger.info("=== SimPy 항만 시뮬레이션 시작 ===")
    results = _simulate()
    logger.info(f"=== 시뮬레이션 완료: {len(results)}건 저장 ===")
    return results


def print_summary():
    """실행 결과 요약 출력"""
    logger.info("\n" + "="*60)
    logger.info("디지털 트윈 실행 결과 요약")
    logger.info("="*60)

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:

            # AIS 현황
            cur.execute("SELECT COUNT(*) FROM ship_tracking")
            ais_total = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(DISTINCT mmsi) FROM ship_tracking
                WHERE timestamp_utc = (SELECT MAX(timestamp_utc) FROM ship_tracking)
            """)
            ais_latest = cur.fetchone()[0]

            # 날씨 현황
            cur.execute("SELECT COUNT(*) FROM weather_data")
            wx_total = cur.fetchone()[0]
            cur.execute("""
                SELECT nav_safety, COUNT(*) FROM weather_data
                WHERE timestamp_utc = (SELECT MAX(timestamp_utc) FROM weather_data)
                GROUP BY nav_safety
            """)
            wx_status = dict(cur.fetchall())

            # 시뮬레이션 결과
            cur.execute("SELECT COUNT(*) FROM simulation_results")
            sim_total = cur.fetchone()[0]
            cur.execute("""
                SELECT COALESCE(SUM(throughput_teu),0), COALESCE(SUM(throughput_ton),0),
                       ROUND(AVG(berth_wait_min)/60.0, 1),
                       ROUND(AVG(crane_utilization), 1)
                FROM simulation_results
                WHERE sim_run_dt::date = CURRENT_DATE
            """)
            sim_row = cur.fetchone()

    logger.info(f"\n[AIS 선박 위치]")
    logger.info(f"  전체 레코드: {ais_total:,}건")
    logger.info(f"  현재 추적 선박: {ais_latest}척")

    logger.info(f"\n[서해 기상]")
    logger.info(f"  전체 레코드: {wx_total:,}건")
    for status, cnt in wx_status.items():
        icon = "🔴" if status == "DANGER" else "🟡" if status == "CAUTION" else "🟢"
        logger.info(f"  {icon} {status}: {cnt}개 관측포인트")

    logger.info(f"\n[시뮬레이션 결과]")
    logger.info(f"  전체 레코드: {sim_total:,}건")
    if sim_row and sim_row[0] is not None:
        logger.info(f"  금일 TEU 처리: {sim_row[0]:,}")
        logger.info(f"  금일 톤 처리: {sim_row[1]:,}")
        logger.info(f"  평균 선석 대기: {sim_row[2]}시간")
        logger.info(f"  평균 크레인 가동률: {sim_row[3]}%")

    logger.info(f"\n[Redash 대시보드]")
    logger.info(f"  http://localhost:5901")
    logger.info(f"  → Dashboard 4: 선박 실시간 추적 (Q4-1 ~ Q4-4)")
    logger.info(f"  → Dashboard 5: 시뮬레이션 KPI (Q5-1 ~ Q5-4)")
    logger.info("="*60)


def run_once():
    """1회 전체 파이프라인 실행"""
    logger.info(f"\n{'#'*60}")
    logger.info(f"디지털 트윈 파이프라인 시작: {datetime.now()}")
    logger.info(f"{'#'*60}")

    try:
        apply_schema()
    except Exception as e:
        logger.warning(f"스키마 적용 중 일부 오류 (이미 존재할 수 있음): {e}")

    run_collection(cycles=1)
    run_simulation()
    print_summary()


def run_loop(interval_sec=600):
    """반복 실행 (10분 주기)"""
    logger.info(f"루프 모드 시작: {interval_sec}초 간격")
    cycle = 0

    # 최초 스키마 적용
    try:
        apply_schema()
    except Exception as e:
        logger.warning(f"스키마: {e}")

    while True:
        cycle += 1
        logger.info(f"\n--- 사이클 #{cycle} ({datetime.now()}) ---")
        try:
            run_collection(cycles=1)
            run_simulation()
            print_summary()
        except Exception as e:
            logger.error(f"사이클 오류: {e}", exc_info=True)

        logger.info(f"다음 실행까지 {interval_sec}초 대기...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="디지털 트윈 통합 실행기")
    parser.add_argument(
        "--mode",
        choices=["once", "loop", "schema", "collect", "simulate"],
        default="once",
        help="실행 모드"
    )
    parser.add_argument("--interval", type=int, default=600, help="루프 주기(초)")
    args = parser.parse_args()

    if args.mode == "once":
        run_once()
    elif args.mode == "loop":
        run_loop(interval_sec=args.interval)
    elif args.mode == "schema":
        apply_schema()
    elif args.mode == "collect":
        run_collection(cycles=1)
    elif args.mode == "simulate":
        run_simulation()
        print_summary()
