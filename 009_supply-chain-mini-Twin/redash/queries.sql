-- ============================================================
-- Redash 대시보드 쿼리 모음
-- 009 Supply Chain Mini-Twin
-- ============================================================

-- ============================================================
-- [Dashboard 1] Inbound(원자재) 관제
-- ============================================================

-- Q1-1: 선박 입항 현황 (최근 7일)
SELECT
    shipment_id,
    vessel_name,
    vessel_type,
    origin_name,
    dest_name,
    material_name,
    quantity || ' ' || unit as qty,
    eta_planned::timestamp as "ETA(계획)",
    eta_actual::timestamp as "ETA(실제)",
    delay_hours as "지연(시간)",
    status as "상태",
    CASE
        WHEN delay_hours >= 24 THEN '🔴 CRITICAL'
        WHEN delay_hours >= 6 THEN '🟡 WARNING'
        WHEN delay_hours > 0 THEN '🟠 MINOR'
        ELSE '🟢 정상'
    END as "지연등급"
FROM inbound_shipments
WHERE snapshot_date::date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY eta_actual::timestamp DESC;

-- Q1-2: 출발항별 선적 건수 & 평균 지연
SELECT
    origin_name as "출발항",
    origin_country as "국가",
    COUNT(*) as "선적건수",
    ROUND(AVG(delay_hours::numeric), 1) as "평균지연(시간)",
    SUM(CASE WHEN delay_hours::numeric > 0 THEN 1 ELSE 0 END) as "지연건수",
    ROUND(AVG(customs_hours::numeric), 1) as "평균통관(시간)"
FROM inbound_shipments
GROUP BY origin_name, origin_country
ORDER BY "선적건수" DESC;

-- Q1-3: 원자재별 입항 현황
SELECT
    material_name as "원자재",
    material_category as "카테고리",
    COUNT(*) as "선적건수",
    SUM(quantity) as "총수량",
    ROUND(AVG(delay_hours::numeric), 1) as "평균지연",
    SUM(CASE WHEN status = '항해중' THEN 1 ELSE 0 END) as "항해중",
    SUM(CASE WHEN status = '하역중' THEN 1 ELSE 0 END) as "하역중",
    SUM(CASE WHEN status = '통관중' THEN 1 ELSE 0 END) as "통관중"
FROM inbound_shipments
GROUP BY material_name, material_category
ORDER BY "선적건수" DESC;

-- Q1-4: 일별 입항 트렌드
SELECT
    snapshot_date::date as "날짜",
    COUNT(*) as "선적건수",
    ROUND(AVG(delay_hours::numeric), 1) as "평균지연",
    SUM(CASE WHEN delay_hours::numeric >= 6 THEN 1 ELSE 0 END) as "지연건수"
FROM inbound_shipments
GROUP BY snapshot_date::date
ORDER BY "날짜";


-- ============================================================
-- [Dashboard 2] Inventory & Production Risk
-- ============================================================

-- Q2-1: 현재 재고 현황 (최신일 기준)
SELECT
    material_name as "원자재",
    category as "카테고리",
    ROUND(current_stock::numeric, 0) as "현재고",
    unit as "단위",
    ROUND(dos::numeric, 1) as "재고일수(DOS)",
    safety_stock_days as "안전재고일수",
    ROUND(safety_ratio::numeric, 2) as "안전재고비율",
    ROUND(coverage_pct::numeric, 1) as "커버리지(%)",
    risk_level as "리스크",
    ROUND(stock_value_krw::numeric / 1000000, 0) as "재고가치(백만원)"
FROM inventory_daily
WHERE date = (SELECT MAX(date) FROM inventory_daily)
ORDER BY dos::numeric ASC;

-- Q2-2: 리스크 품목 추이 (최근 30일)
SELECT
    date::date as "날짜",
    SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as "CRITICAL",
    SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as "HIGH",
    SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as "MEDIUM",
    SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) as "LOW"
FROM inventory_daily
GROUP BY date::date
ORDER BY "날짜";

-- Q2-3: 생산 계획 대비 실적
SELECT
    date::date as "날짜",
    product_name as "제품",
    planned_qty as "계획",
    actual_qty as "실적",
    ROUND(achievement_rate::numeric, 1) as "달성률(%)",
    CASE WHEN line_stop = 'true' OR line_stop = 'True' THEN '⛔ 중단' ELSE '✅ 정상' END as "라인상태"
FROM production_plan
WHERE is_weekend = 'false' OR is_weekend = 'False'
ORDER BY date::date DESC, product_name
LIMIT 100;

-- Q2-4: 품목별 재고일수(DOS) 추이
SELECT
    date::date as "날짜",
    material_name as "원자재",
    ROUND(dos::numeric, 1) as "재고일수",
    safety_stock_days as "안전재고일수"
FROM inventory_daily
ORDER BY date::date, material_name;


-- ============================================================
-- [Dashboard 3] Outbound(출하) & OTIF
-- ============================================================

-- Q3-1: 고객별 OTIF 현황
SELECT
    customer_name as "고객",
    customer_region as "지역",
    COUNT(*) as "주문건수",
    SUM(CASE WHEN otif = 'true' OR otif = 'True' THEN 1 ELSE 0 END) as "OTIF달성",
    ROUND(AVG(CASE WHEN otif = 'true' OR otif = 'True' THEN 100.0 ELSE 0.0 END), 1) as "OTIF률(%)",
    ROUND(AVG(CASE WHEN on_time = 'true' OR on_time = 'True' THEN 100.0 ELSE 0.0 END), 1) as "정시율(%)",
    ROUND(AVG(CASE WHEN in_full = 'true' OR in_full = 'True' THEN 100.0 ELSE 0.0 END), 1) as "정량율(%)",
    ROUND(AVG(ship_delay_days::numeric), 2) as "평균지연(일)"
FROM outbound_orders
GROUP BY customer_name, customer_region
ORDER BY "OTIF률(%)" ASC;

-- Q3-2: 일별 OTIF 추이
SELECT
    order_date::date as "날짜",
    COUNT(*) as "주문건수",
    ROUND(AVG(CASE WHEN otif = 'true' OR otif = 'True' THEN 100.0 ELSE 0.0 END), 1) as "OTIF(%)",
    ROUND(AVG(CASE WHEN on_time = 'true' OR on_time = 'True' THEN 100.0 ELSE 0.0 END), 1) as "정시율(%)",
    SUM(CASE WHEN ship_delay_days::numeric > 0 THEN 1 ELSE 0 END) as "지연건수"
FROM outbound_orders
GROUP BY order_date::date
ORDER BY "날짜";

-- Q3-3: 제품별 출하 현황
SELECT
    product_name as "제품",
    COUNT(*) as "주문건수",
    SUM(order_qty) as "주문수량",
    SUM(shipped_qty) as "출하수량",
    ROUND(AVG(qty_fill_rate::numeric), 1) as "충족률(%)",
    ROUND(AVG(CASE WHEN otif = 'true' OR otif = 'True' THEN 100.0 ELSE 0.0 END), 1) as "OTIF(%)"
FROM outbound_orders
GROUP BY product_name
ORDER BY "OTIF(%)" ASC;

-- Q3-4: 출하 지연 상세
SELECT
    order_id as "주문번호",
    customer_name as "고객",
    product_name as "제품",
    order_qty as "주문수량",
    shipped_qty as "출하수량",
    due_date::date as "납기일",
    ship_actual_date::date as "실제출하일",
    ship_delay_days as "지연(일)",
    CASE
        WHEN otif = 'true' OR otif = 'True' THEN '✅ OTIF'
        WHEN on_time = 'false' AND (in_full = 'false' OR in_full = 'False') THEN '🔴 지연+미달'
        WHEN on_time = 'false' OR on_time = 'False' THEN '🟡 지연'
        ELSE '🟠 수량미달'
    END as "상태"
FROM outbound_orders
WHERE otif = 'false' OR otif = 'False'
ORDER BY ship_delay_days::numeric DESC
LIMIT 50;


-- ============================================================
-- [공통] 알림 모니터링
-- ============================================================

-- Q-ALERT: 활성 알림 현황
SELECT
    alert_type as "유형",
    alert_name as "알림명",
    severity as "등급",
    timestamp as "발생시각",
    reference_id as "참조ID",
    message as "메시지"
FROM alert_events
WHERE resolved = 'false' OR resolved = 'False'
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
    END,
    timestamp DESC
LIMIT 30;

-- Q-ALERT-SUMMARY: 알림 유형별 집계
SELECT
    alert_type as "유형코드",
    alert_name as "알림명",
    COUNT(*) as "총건수",
    SUM(CASE WHEN resolved = 'false' OR resolved = 'False' THEN 1 ELSE 0 END) as "미해결",
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as "CRITICAL",
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as "HIGH"
FROM alert_events
GROUP BY alert_type, alert_name
ORDER BY alert_type;
