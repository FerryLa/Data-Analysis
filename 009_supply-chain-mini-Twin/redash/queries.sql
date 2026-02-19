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


-- ============================================================
-- [Dashboard 4] 디지털 트윈 - 선박 실시간 추적
-- (ship_tracking + weather_data 기반)
-- ============================================================

-- Q4-1: 현재 운항 중인 선박 위치 + 기상 등급
SELECT
    vessel_name                         AS "선박명",
    vessel_type                         AS "선종",
    flag                                AS "국적",
    ROUND(latitude::numeric, 4)         AS "위도",
    ROUND(longitude::numeric, 4)        AS "경도",
    speed_kn                            AS "속력(kn)",
    course_deg                          AS "방위각",
    nav_status                          AS "항행상태",
    origin_port                         AS "출발항",
    destination_name                    AS "목적항",
    to_char(eta_utc, 'MM/DD HH24:MI')   AS "AIS_ETA",
    dist_to_dest_nm                     AS "잔여거리(nm)",
    voyage_progress_pct                 AS "진행률(%)",
    nearest_nav_safety                  AS "인근기상",
    to_char(timestamp_utc AT TIME ZONE 'Asia/Seoul', 'HH24:MI') AS "최종수신"
FROM v_ship_positions
ORDER BY voyage_progress_pct DESC;

-- Q4-2: AIS ETA vs 시뮬레이션 ETA 비교 (디지털 트윈 핵심 뷰)
SELECT
    vessel_name                         AS "선박명",
    port_name                           AS "입항항",
    voyage_progress_pct                 AS "진행률(%)",
    dist_to_dest_nm                     AS "잔여거리(nm)",
    to_char(ais_eta, 'MM/DD HH24:MI')   AS "AIS_ETA(신고)",
    to_char(sim_eta, 'MM/DD HH24:MI')   AS "SimPy_ETA(예측)",
    ROUND(EXTRACT(EPOCH FROM (sim_eta - ais_eta)) / 3600, 1)
                                        AS "오차(시간)",
    ROUND(berth_wait_min / 60.0, 1)     AS "선석대기(hr)",
    ROUND(unload_min / 60.0, 1)         AS "하역(hr)",
    ROUND(customs_min / 60.0, 1)        AS "통관(hr)",
    throughput_teu                      AS "처리량(TEU)",
    throughput_ton                      AS "처리량(톤)",
    ROUND(crane_utilization, 1)         AS "크레인가동률(%)",
    weather_nav_safety                  AS "기상등급",
    ROUND(delay_factor, 2)              AS "날씨지연배율",
    eta_status                          AS "ETA상태"
FROM v_port_eta
ORDER BY voyage_progress_pct DESC;

-- Q4-3: 서해 기상 현황 (관측 포인트별)
SELECT
    point_name                          AS "관측지점",
    wind_speed_kn                       AS "풍속(kn)",
    wind_speed_ms                       AS "풍속(m/s)",
    CASE
        WHEN wind_direction_deg BETWEEN 292.5 AND 360   THEN 'NW (북서)'
        WHEN wind_direction_deg BETWEEN 0     AND  67.5 THEN 'N (북)'
        WHEN wind_direction_deg BETWEEN 67.5  AND 157.5 THEN 'E (동)'
        WHEN wind_direction_deg BETWEEN 157.5 AND 247.5 THEN 'S (남)'
        ELSE 'W (서)'
    END                                 AS "풍향",
    wave_height_m                       AS "파고(m)",
    wave_period_s                       AS "파주기(s)",
    tidal_current_kn                    AS "조류유속(kn)",
    water_temp_c                        AS "해수온(°C)",
    visibility_km                       AS "가시거리(km)",
    CASE nav_safety
        WHEN 'DANGER'  THEN '🔴 위험'
        WHEN 'CAUTION' THEN '🟡 주의'
        ELSE '🟢 안전'
    END                                 AS "항행안전"
FROM weather_data
WHERE timestamp_utc = (SELECT MAX(timestamp_utc) FROM weather_data)
ORDER BY point_name;

-- Q4-4: 기상 시계열 (최근 24시간 풍속/파고 추이)
SELECT
    date_trunc('hour', timestamp_utc AT TIME ZONE 'Asia/Seoul')
                                        AS "시각(KST)",
    ROUND(AVG(wind_speed_kn), 1)        AS "평균풍속(kn)",
    ROUND(MAX(wind_speed_kn), 1)        AS "최대풍속(kn)",
    ROUND(AVG(wave_height_m), 2)        AS "평균파고(m)",
    ROUND(MAX(wave_height_m), 2)        AS "최대파고(m)",
    ROUND(AVG(tidal_current_kn), 2)     AS "평균조류(kn)",
    COUNT(DISTINCT point_id)            AS "관측포인트수"
FROM weather_data
WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', timestamp_utc AT TIME ZONE 'Asia/Seoul')
ORDER BY "시각(KST)";


-- ============================================================
-- [Dashboard 5] 디지털 트윈 - 시뮬레이션 KPI
-- (simulation_results 기반)
-- ============================================================

-- Q5-1: 항만별 일별 처리량 KPI
SELECT
    sim_date                            AS "날짜",
    port_name                           AS "항만",
    vessel_count                        AS "처리선박수",
    total_teu                           AS "TEU처리량",
    total_ton                           AS "톤처리량",
    avg_berth_wait_hr                   AS "평균선석대기(hr)",
    avg_unload_hr                       AS "평균하역(hr)",
    avg_customs_hr                      AS "평균통관(hr)",
    avg_total_port_hr                   AS "평균항만체류(hr)",
    avg_crane_util_pct                  AS "크레인가동률(%)",
    avg_delay_factor                    AS "날씨지연배율",
    weather_danger_cnt                  AS "기상위험건수",
    weather_caution_cnt                 AS "기상주의건수"
FROM v_sim_kpi
ORDER BY sim_date DESC, port_name;

-- Q5-2: 선박별 상세 시뮬레이션 결과
SELECT
    sr.sim_run_dt::date                 AS "시뮬일",
    sr.port_name                        AS "항만",
    sr.vessel_name                      AS "선박명",
    sr.vessel_type                      AS "선종",
    sr.cargo_type                       AS "화물유형",
    sr.cargo_qty                        AS "화물량",
    sr.cargo_unit                       AS "단위",
    to_char(sr.eta_planned, 'MM/DD HH24:MI')  AS "ETA계획",
    to_char(sr.eta_actual,  'MM/DD HH24:MI')  AS "ETA예측",
    ROUND(sr.berth_wait_min / 60.0, 1) AS "선석대기(hr)",
    ROUND(sr.unload_min / 60.0, 1)     AS "하역(hr)",
    ROUND(sr.customs_min / 60.0, 1)    AS "통관(hr)",
    ROUND(sr.total_port_min / 60.0, 1) AS "총체류(hr)",
    NULLIF(sr.throughput_teu, 0)        AS "TEU",
    NULLIF(sr.throughput_ton, 0)        AS "처리톤",
    sr.crane_utilization                AS "크레인가동률(%)",
    sr.weather_nav_safety               AS "기상등급",
    sr.delay_factor                     AS "지연배율"
FROM simulation_results sr
ORDER BY sr.sim_run_dt DESC, sr.port_id, sr.berth_wait_min DESC
LIMIT 200;

-- Q5-3: 통합 디지털 트윈 현황판 (단일 행 KPI)
SELECT
    underway_count                      AS "운항중선박",
    moored_count                        AS "접안중선박",
    today_teu                           AS "금일TEU처리",
    today_ton                           AS "금일톤처리",
    COALESCE(avg_berth_wait_hr, 0)      AS "평균선석대기(hr)",
    CASE current_weather
        WHEN 'DANGER'  THEN '🔴 위험'
        WHEN 'CAUTION' THEN '🟡 주의'
        ELSE '🟢 안전'
    END                                 AS "현재기상",
    COALESCE(avg_wind_kn, 0)            AS "평균풍속(kn)",
    COALESCE(avg_wave_m, 0)             AS "평균파고(m)",
    COALESCE(delayed_vessel_count, 0)   AS "지연예상선박",
    COALESCE(avg_crane_util_pct, 0)     AS "크레인가동률(%)"
FROM v_twin_dashboard;

-- Q5-4: 선박 유형별 처리 효율 비교
SELECT
    vessel_type                         AS "선종",
    cargo_type                          AS "화물유형",
    COUNT(*)                            AS "처리선박수",
    ROUND(AVG(berth_wait_min) / 60.0, 1) AS "평균선석대기(hr)",
    ROUND(AVG(unload_min) / 60.0, 1)    AS "평균하역(hr)",
    ROUND(AVG(customs_min) / 60.0, 1)   AS "평균통관(hr)",
    ROUND(AVG(total_port_min) / 60.0, 1) AS "평균체류(hr)",
    ROUND(AVG(crane_utilization), 1)    AS "평균크레인가동률(%)",
    SUM(throughput_teu)                 AS "TEU합계",
    SUM(throughput_ton)                 AS "톤합계"
FROM simulation_results
GROUP BY vessel_type, cargo_type
ORDER BY "평균체류(hr)" DESC;
