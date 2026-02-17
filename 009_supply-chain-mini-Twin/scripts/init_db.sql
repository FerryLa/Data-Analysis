-- 009 Supply Chain Mini-Twin - PostgreSQL 초기화
-- Docker 컨테이너 시작 시 자동 실행

-- ============================================================
-- 뷰: Inbound 관제 대시보드용
-- ============================================================
CREATE OR REPLACE VIEW v_inbound_dashboard AS
SELECT
    shipment_id,
    vessel_name,
    vessel_type,
    origin_name,
    origin_country,
    dest_name,
    material_name,
    material_category,
    quantity,
    unit,
    eta_planned::timestamp,
    eta_actual::timestamp,
    delay_hours,
    CASE
        WHEN delay_hours >= 24 THEN 'CRITICAL'
        WHEN delay_hours >= 6 THEN 'WARNING'
        WHEN delay_hours > 0 THEN 'MINOR'
        ELSE 'ON_TIME'
    END as delay_severity,
    status,
    berth_wait_hours,
    customs_hours,
    snapshot_date::date
FROM inbound_shipments;

-- ============================================================
-- 뷰: Inventory Risk 대시보드용
-- ============================================================
CREATE OR REPLACE VIEW v_inventory_risk AS
SELECT
    date::date,
    material_code,
    material_name,
    category,
    current_stock,
    daily_usage,
    dos,
    safety_stock_days,
    safety_ratio,
    coverage_pct,
    risk_level,
    stock_value_krw,
    lead_time_days,
    CASE
        WHEN dos <= lead_time_days THEN true
        ELSE false
    END as reorder_needed
FROM inventory_daily;

-- ============================================================
-- 뷰: Outbound OTIF 대시보드용
-- ============================================================
CREATE OR REPLACE VIEW v_outbound_otif AS
SELECT
    order_id,
    order_date::date,
    customer_name,
    customer_region,
    product_name,
    order_qty,
    shipped_qty,
    qty_fill_rate,
    due_date::date,
    ship_plan_date::date,
    ship_actual_date::date,
    ship_delay_days,
    on_time::boolean,
    in_full::boolean,
    otif::boolean,
    transport_mode,
    transport_km
FROM outbound_orders;

-- ============================================================
-- 뷰: 알림 이벤트 (n8n 연동)
-- ============================================================
CREATE OR REPLACE VIEW v_active_alerts AS
SELECT
    alert_id,
    alert_type,
    alert_name,
    severity,
    timestamp,
    reference_id,
    message,
    resolved::boolean
FROM alert_events
WHERE resolved = false
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        ELSE 4
    END,
    timestamp DESC;

-- ============================================================
-- 뷰: OTIF 고객별 집계
-- ============================================================
CREATE OR REPLACE VIEW v_otif_by_customer AS
SELECT
    customer_name,
    customer_region,
    COUNT(*) as total_orders,
    SUM(CASE WHEN otif = 'true' OR otif = 'True' THEN 1 ELSE 0 END) as otif_count,
    ROUND(AVG(CASE WHEN otif = 'true' OR otif = 'True' THEN 100.0 ELSE 0.0 END), 1) as otif_rate,
    ROUND(AVG(CASE WHEN on_time = 'true' OR on_time = 'True' THEN 100.0 ELSE 0.0 END), 1) as on_time_rate,
    ROUND(AVG(CASE WHEN in_full = 'true' OR in_full = 'True' THEN 100.0 ELSE 0.0 END), 1) as in_full_rate,
    ROUND(AVG(ship_delay_days::numeric), 2) as avg_delay_days
FROM outbound_orders
GROUP BY customer_name, customer_region;

-- ============================================================
-- 뷰: 알림 유형별 집계
-- ============================================================
CREATE OR REPLACE VIEW v_alert_summary AS
SELECT
    alert_type,
    alert_name,
    COUNT(*) as total_count,
    SUM(CASE WHEN resolved = 'false' OR resolved = 'False' THEN 1 ELSE 0 END) as open_count,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_count
FROM alert_events
GROUP BY alert_type, alert_name
ORDER BY alert_type;
