"""
CSV → PostgreSQL 로더
Bronze/Silver CSV 파일을 PostgreSQL에 적재
"""

import os
import csv
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    "host": "localhost",
    "port": 5900,
    "dbname": "supply_chain_db",
    "user": "n8n_user",
    "password": "n8n_pass",
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver")

# CSV 파일 → 테이블 매핑
FILE_TABLE_MAP = {
    os.path.join(BRONZE_DIR, "inbound_shipments.csv"): "inbound_shipments",
    os.path.join(BRONZE_DIR, "inventory_daily.csv"): "inventory_daily",
    os.path.join(BRONZE_DIR, "production_plan.csv"): "production_plan",
    os.path.join(BRONZE_DIR, "outbound_orders.csv"): "outbound_orders",
    os.path.join(BRONZE_DIR, "port_markers.csv"): "port_markers",
    os.path.join(BRONZE_DIR, "sea_routes.csv"): "sea_routes",
    os.path.join(BRONZE_DIR, "logistics_zones.csv"): "logistics_zones",
    os.path.join(BRONZE_DIR, "alert_events.csv"): "alert_events",
    os.path.join(SILVER_DIR, "kpi_summary.csv"): "kpi_summary",
}


def detect_column_type(values):
    """값 샘플로 컬럼 타입 추정"""
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return "TEXT"

    # Boolean 체크
    bool_vals = {"true", "false", "True", "False", "TRUE", "FALSE"}
    if all(v in bool_vals for v in non_empty):
        return "BOOLEAN"

    # Integer 체크
    try:
        [int(v) for v in non_empty]
        max_val = max(abs(int(v)) for v in non_empty)
        return "BIGINT"
    except ValueError:
        pass

    # Float 체크
    try:
        [float(v) for v in non_empty]
        return "NUMERIC"
    except ValueError:
        pass

    # 날짜 체크
    if all(len(v) == 10 and v[4] == "-" and v[7] == "-" for v in non_empty[:10]):
        return "DATE"

    # DateTime 체크
    if all(len(v) >= 16 and v[4] == "-" and v[7] == "-" for v in non_empty[:10]):
        return "TIMESTAMP"

    return "TEXT"


def load_csv_to_table(conn, filepath, table_name):
    """단일 CSV를 테이블에 적재"""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    if not rows:
        print(f"  ⚠ {table_name}: 빈 파일, 건너뜀")
        return 0

    # 컬럼 타입 추정 (처음 100행 샘플)
    sample_rows = rows[:100]
    col_types = []
    for i, col in enumerate(headers):
        values = [row[i] for row in sample_rows if i < len(row)]
        col_types.append(detect_column_type(values))

    cur = conn.cursor()

    # 테이블 DROP & CREATE
    cur.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name)))

    create_cols = ", ".join(
        f'"{h}" {t}' for h, t in zip(headers, col_types)
    )
    cur.execute(f'CREATE TABLE "{table_name}" ({create_cols})')

    # INSERT
    placeholders = ", ".join(["%s"] * len(headers))
    insert_sql = f'INSERT INTO "{table_name}" ({", ".join(f"{h!r}" for h in headers)}) VALUES ({placeholders})'
    # 더 깔끔한 방식
    col_names = ", ".join(f'"{h}"' for h in headers)
    insert_sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'

    for row in rows:
        # 타입 변환
        converted = []
        for val, ctype in zip(row, col_types):
            if val.strip() == "":
                converted.append(None)
            elif ctype == "BOOLEAN":
                converted.append(val.lower() == "true")
            elif ctype == "INTEGER":
                converted.append(int(val))
            elif ctype == "BIGINT":
                converted.append(int(val))
            elif ctype == "NUMERIC":
                converted.append(float(val))
            else:
                converted.append(val)
        cur.execute(insert_sql, converted)

    conn.commit()
    cur.close()
    return len(rows)


def main():
    print("=" * 60)
    print("CSV → PostgreSQL 로딩 시작")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    total = 0

    for filepath, table_name in FILE_TABLE_MAP.items():
        if os.path.exists(filepath):
            count = load_csv_to_table(conn, filepath, table_name)
            print(f"  [OK] {table_name}: {count:,}건 적재")
            total += count
        else:
            print(f"  [SKIP] {filepath} 파일 없음")

    conn.close()
    print(f"\n총 {total:,}건 적재 완료")


if __name__ == "__main__":
    main()
