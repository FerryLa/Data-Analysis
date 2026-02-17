"""
n8n 알림 로직 검증 스크립트
5대 알림(A1~A5)이 DB에서 정상 조회되는지 테스트
"""
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5900,
    "dbname": "supply_chain_db",
    "user": "n8n_user",
    "password": "n8n_pass",
}

ALERT_QUERIES = {
    "A1: ETA Delay (>6h)": """
        SELECT shipment_id, vessel_name, delay_hours, origin_name, material_name, status
        FROM inbound_shipments
        WHERE delay_hours >= 6
        ORDER BY delay_hours DESC LIMIT 5
    """,
    "A2: Inventory Coverage (<5 days)": """
        SELECT date, material_name, ROUND(dos::numeric,1) as dos,
               risk_level, ROUND(coverage_pct::numeric,1) as coverage_pct
        FROM inventory_daily
        WHERE dos <= 5
        ORDER BY dos ASC LIMIT 5
    """,
    "A3: Production Line Stop Risk": """
        SELECT date, material_name, risk_level,
               ROUND(current_stock::numeric,0) as stock, daily_usage
        FROM inventory_daily
        WHERE risk_level = 'CRITICAL'
        ORDER BY date DESC LIMIT 5
    """,
    "A4: Port Dwell Excess (customs>48h)": """
        SELECT shipment_id, vessel_name, customs_hours, material_name, status
        FROM inbound_shipments
        WHERE customs_hours >= 48
        ORDER BY customs_hours DESC LIMIT 5
    """,
    "A5: OTIF Risk (delay>=2 days)": """
        SELECT order_id, customer_name, product_name,
               ship_delay_days, due_date, otif
        FROM outbound_orders
        WHERE ship_delay_days >= 2
        ORDER BY ship_delay_days DESC LIMIT 5
    """,
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("=" * 65)
    print("  SCM Alert System Test - 5 Alerts Verification")
    print("=" * 65)

    # Summary
    cur.execute("""
        SELECT alert_type, alert_name,
               COUNT(*) as total,
               SUM(CASE WHEN resolved='false' THEN 1 ELSE 0 END) as open_cnt,
               SUM(CASE WHEN severity='CRITICAL' THEN 1 ELSE 0 END) as critical
        FROM alert_events
        GROUP BY alert_type, alert_name
        ORDER BY alert_type
    """)
    rows = cur.fetchall()
    print("\n[Alert Summary]")
    print(f"  {'Type':<6} {'Name':<25} {'Total':>6} {'Open':>6} {'CRIT':>6}")
    print("  " + "-" * 55)
    for r in rows:
        print(f"  {r[0]:<6} {r[1]:<25} {r[2]:>6} {r[3]:>6} {r[4]:>6}")

    # Each alert query test
    for name, query in ALERT_QUERIES.items():
        print(f"\n--- {name} ---")
        cur.execute(query)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        if rows:
            print(f"  {' | '.join(cols)}")
            for r in rows:
                print(f"  {' | '.join(str(v) for v in r)}")
            print(f"  >> {len(rows)} rows (showing top 5)")
        else:
            print("  >> No data")

    # KPI
    cur.execute("SELECT * FROM kpi_summary")
    kpi = cur.fetchone()
    cols = [d[0] for d in cur.description]
    print("\n" + "=" * 65)
    print("[KPI Dashboard]")
    for c, v in zip(cols, kpi):
        print(f"  {c}: {v}")

    cur.close()
    conn.close()
    print("\n[OK] All 5 alert queries verified successfully!")


if __name__ == "__main__":
    main()
