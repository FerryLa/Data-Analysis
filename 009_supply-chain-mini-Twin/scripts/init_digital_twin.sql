-- ============================================================
-- 009 Supply Chain Mini-Twin
-- Digital Twin 확장 스키마 (Phase 4)
-- 테이블: ship_tracking, weather_data, simulation_results
-- 뷰: v_ship_positions, v_port_eta, v_sim_kpi, v_twin_dashboard
-- ============================================================

-- ============================================================
-- 1. AIS 선박 위치 추적 테이블
--    (collect_ais_weather.py → ship_tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS ship_tracking (
    id                  BIGSERIAL PRIMARY KEY,
    mmsi                VARCHAR(12)  NOT NULL,          -- AIS 선박 식별번호 (9자리)
    imo                 VARCHAR(10),                    -- IMO 번호
    vessel_name         VARCHAR(100) NOT NULL,
    vessel_type         VARCHAR(50),
    flag                CHAR(2),                        -- 선박 국적 코드 (KR, CN ...)
    length_m            SMALLINT,
    beam_m              SMALLINT,
    latitude            DECIMAL(9,6) NOT NULL,
    longitude           DECIMAL(9,6) NOT NULL,
    speed_kn            DECIMAL(5,1),                  -- 속력 (knot)
    course_deg          DECIMAL(5,1),                  -- 진행 방위각
    heading_deg         DECIMAL(5,1),                  -- 선수 방향
    nav_status          VARCHAR(30),                   -- underway_engine / moored / at_anchor ...
    destination         VARCHAR(10),                   -- 목적항 UN/LOCODE
    destination_name    VARCHAR(100),
    eta_utc             TIMESTAMP,                     -- 자체 신고 ETA (UTC)
    origin_port         VARCHAR(10),                   -- 출항지 UN/LOCODE
    ship_id             VARCHAR(20),                   -- 내부 화물 연계 ID (SH-XXXX)
    dist_to_dest_nm     DECIMAL(8,1),                  -- 목적항까지 거리 (nm)
    voyage_progress_pct DECIMAL(5,1),                  -- 항해 진행률 (%)
    timestamp_utc       TIMESTAMP    NOT NULL,          -- AIS 수신 시각 (UTC)
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (mmsi, timestamp_utc)
);

CREATE INDEX IF NOT EXISTS idx_ship_tracking_mmsi        ON ship_tracking(mmsi);
CREATE INDEX IF NOT EXISTS idx_ship_tracking_ts          ON ship_tracking(timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_ship_tracking_destination ON ship_tracking(destination);
CREATE INDEX IF NOT EXISTS idx_ship_tracking_ship_id     ON ship_tracking(ship_id);

COMMENT ON TABLE ship_tracking IS 'AIS 선박 실시간 위치 추적 (10분 주기)';


-- ============================================================
-- 2. 해상 기상 데이터 테이블
--    (collect_ais_weather.py → weather_data)
-- ============================================================
CREATE TABLE IF NOT EXISTS weather_data (
    id                    BIGSERIAL PRIMARY KEY,
    point_id              VARCHAR(10)  NOT NULL,         -- 관측 포인트 ID (WP-01 ...)
    point_name            VARCHAR(100),
    latitude              DECIMAL(7,4) NOT NULL,
    longitude             DECIMAL(7,4) NOT NULL,
    wind_speed_ms         DECIMAL(5,1),                 -- 풍속 (m/s)
    wind_speed_kn         DECIMAL(5,1),                 -- 풍속 (knot)
    wind_direction_deg    DECIMAL(5,1),                 -- 풍향 (도)
    wave_height_m         DECIMAL(4,2),                 -- 유의파고 (m)
    wave_period_s         DECIMAL(4,1),                 -- 파주기 (초)
    tidal_current_kn      DECIMAL(4,2),                 -- 조류 유속 (knot)
    current_direction_deg DECIMAL(5,1),                 -- 조류 방향
    water_temp_c          DECIMAL(4,1),                 -- 해수면 온도 (°C)
    air_temp_c            DECIMAL(4,1),                 -- 기온 (°C)
    visibility_km         SMALLINT,                     -- 가시거리 (km)
    pressure_hpa          DECIMAL(6,1),                 -- 기압 (hPa)
    nav_safety            VARCHAR(10),                  -- SAFE / CAUTION / DANGER
    source                VARCHAR(50),                  -- 데이터 출처 (OpenMeteo / KMA / ...)
    timestamp_utc         TIMESTAMP    NOT NULL,
    created_at            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (point_id, timestamp_utc)
);

CREATE INDEX IF NOT EXISTS idx_weather_point_ts ON weather_data(point_id, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_weather_ts       ON weather_data(timestamp_utc DESC);

COMMENT ON TABLE weather_data IS '서해 해상 기상 관측 데이터 (10분 주기)';


-- ============================================================
-- 3. SimPy 시뮬레이션 결과 테이블
--    (simulate_port.py → simulation_results)
-- ============================================================
CREATE TABLE IF NOT EXISTS simulation_results (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              VARCHAR(100) NOT NULL UNIQUE,   -- 시뮬레이션 실행 고유 ID
    port_id             VARCHAR(10)  NOT NULL,          -- 항만 코드
    port_name           VARCHAR(100),
    vessel_id           VARCHAR(30),
    vessel_name         VARCHAR(100),
    vessel_type         VARCHAR(50),
    cargo_type          VARCHAR(30),                   -- Container / Bulk / General / RoRo
    cargo_qty           INT,
    cargo_unit          VARCHAR(10),
    -- ETA 예측
    eta_planned         TIMESTAMP,                     -- 입항 예정 (AIS 기반)
    eta_actual          TIMESTAMP,                     -- 시뮬레이션 예측 ETA
    sim_run_dt          TIMESTAMP    NOT NULL,          -- 시뮬레이션 실행 시각
    -- 처리 시간 분석 (분)
    berth_wait_min      INT          DEFAULT 0,         -- 선석 대기 시간
    unload_min          INT          DEFAULT 0,         -- 하역 시간
    customs_min         INT          DEFAULT 0,         -- 통관 시간
    total_port_min      INT          DEFAULT 0,         -- 총 항만 체류 시간
    -- 처리량
    throughput_teu      INT          DEFAULT 0,         -- 컨테이너 (TEU)
    throughput_ton      INT          DEFAULT 0,         -- 벌크/일반 (톤)
    crane_utilization   DECIMAL(5,1) DEFAULT 0,         -- 크레인 가동률 (%)
    -- 기상 조건
    weather_wind_kn     DECIMAL(5,1),
    weather_wave_m      DECIMAL(4,2),
    weather_nav_safety  VARCHAR(10),
    delay_factor        DECIMAL(4,2) DEFAULT 1.0,       -- 날씨 지연 배율
    status              VARCHAR(20)  DEFAULT 'simulated',
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_simres_port_dt    ON simulation_results(port_id, sim_run_dt DESC);
CREATE INDEX IF NOT EXISTS idx_simres_vessel     ON simulation_results(vessel_id);
CREATE INDEX IF NOT EXISTS idx_simres_run_dt     ON simulation_results(sim_run_dt DESC);

COMMENT ON TABLE simulation_results IS 'SimPy 선박 입출항 시뮬레이션 결과';


-- ============================================================
-- 4. 뷰: 현재 선박 위치 (최신 AIS 핀)
-- ============================================================
CREATE OR REPLACE VIEW v_ship_positions AS
SELECT
    st.mmsi,
    st.imo,
    st.vessel_name,
    st.vessel_type,
    st.flag,
    st.latitude,
    st.longitude,
    st.speed_kn,
    st.course_deg,
    st.nav_status,
    st.destination,
    st.destination_name,
    st.eta_utc,
    st.origin_port,
    st.ship_id,
    st.dist_to_dest_nm,
    st.voyage_progress_pct,
    st.timestamp_utc,
    -- 현재 기상 (가장 가까운 관측 포인트)
    (SELECT nav_safety FROM weather_data
     WHERE timestamp_utc = (SELECT MAX(timestamp_utc) FROM weather_data)
     ORDER BY SQRT(POWER(latitude - st.latitude, 2) + POWER(longitude - st.longitude, 2))
     LIMIT 1) AS nearest_nav_safety
FROM ship_tracking st
INNER JOIN (
    SELECT mmsi, MAX(timestamp_utc) AS max_ts
    FROM ship_tracking GROUP BY mmsi
) latest ON st.mmsi = latest.mmsi AND st.timestamp_utc = latest.max_ts;

COMMENT ON VIEW v_ship_positions IS '현재 AIS 선박 위치 (최신 스냅샷)';


-- ============================================================
-- 5. 뷰: 항만별 입항 예정 + 시뮬레이션 ETA 비교 (디지털 트윈 핵심)
-- ============================================================
CREATE OR REPLACE VIEW v_port_eta AS
SELECT
    sp.ship_id,
    sp.vessel_name,
    sp.vessel_type,
    sp.destination        AS port_id,
    sp.destination_name   AS port_name,
    sp.origin_port,
    sp.dist_to_dest_nm,
    sp.voyage_progress_pct,
    sp.speed_kn,
    sp.eta_utc            AS ais_eta,               -- AIS 자체 신고 ETA
    sr.eta_actual         AS sim_eta,               -- SimPy 시뮬레이션 ETA (더 정밀)
    sr.berth_wait_min,
    sr.unload_min,
    sr.customs_min,
    sr.total_port_min,
    sr.throughput_teu,
    sr.throughput_ton,
    sr.crane_utilization,
    sr.weather_nav_safety,
    sr.delay_factor,
    CASE
        WHEN sr.sim_eta IS NULL THEN '시뮬레이션 미완료'
        WHEN sr.sim_eta > sp.eta_utc + INTERVAL '6 hours' THEN '지연 예상'
        WHEN sr.sim_eta > sp.eta_utc + INTERVAL '2 hours' THEN '소폭 지연'
        ELSE '정상'
    END AS eta_status,
    sp.timestamp_utc AS last_ais_update
FROM v_ship_positions sp
LEFT JOIN simulation_results sr
    ON sp.ship_id = sr.vessel_id
    AND sr.sim_run_dt = (
        SELECT MAX(sim_run_dt) FROM simulation_results
        WHERE vessel_id = sp.ship_id
    )
WHERE sp.nav_status != 'moored';

COMMENT ON VIEW v_port_eta IS '실시간 AIS ETA + 시뮬레이션 ETA 비교 (디지털 트윈)';


-- ============================================================
-- 6. 뷰: 시뮬레이션 KPI 집계
-- ============================================================
CREATE OR REPLACE VIEW v_sim_kpi AS
SELECT
    port_id,
    port_name,
    sim_run_dt::date                                  AS sim_date,
    COUNT(*)                                          AS vessel_count,
    SUM(throughput_teu)                               AS total_teu,
    SUM(throughput_ton)                               AS total_ton,
    ROUND(AVG(berth_wait_min) / 60.0, 2)              AS avg_berth_wait_hr,
    ROUND(AVG(unload_min) / 60.0, 2)                  AS avg_unload_hr,
    ROUND(AVG(customs_min) / 60.0, 2)                 AS avg_customs_hr,
    ROUND(AVG(total_port_min) / 60.0, 2)              AS avg_total_port_hr,
    ROUND(AVG(crane_utilization), 1)                  AS avg_crane_util_pct,
    ROUND(AVG(delay_factor), 2)                       AS avg_delay_factor,
    SUM(CASE WHEN weather_nav_safety = 'DANGER'  THEN 1 ELSE 0 END) AS weather_danger_cnt,
    SUM(CASE WHEN weather_nav_safety = 'CAUTION' THEN 1 ELSE 0 END) AS weather_caution_cnt
FROM simulation_results
GROUP BY port_id, port_name, sim_run_dt::date
ORDER BY sim_date DESC, port_id;

COMMENT ON VIEW v_sim_kpi IS '일별 항만 시뮬레이션 KPI';


-- ============================================================
-- 7. 뷰: 디지털 트윈 통합 대시보드 (현재 상태 + 예측)
-- ============================================================
CREATE OR REPLACE VIEW v_twin_dashboard AS
SELECT
    'AIS_실시간'                            AS data_type,
    NOW()                                   AS snapshot_time,
    -- 현재 운항 선박
    (SELECT COUNT(*) FROM v_ship_positions WHERE nav_status = 'underway_engine') AS underway_count,
    -- 항만 접안 중
    (SELECT COUNT(*) FROM v_ship_positions WHERE nav_status = 'moored')          AS moored_count,
    -- 금일 총 처리 TEU (시뮬레이션 기준)
    (SELECT COALESCE(SUM(throughput_teu), 0) FROM simulation_results
     WHERE sim_run_dt::date = CURRENT_DATE)                                       AS today_teu,
    -- 금일 총 처리 톤 (시뮬레이션 기준)
    (SELECT COALESCE(SUM(throughput_ton), 0) FROM simulation_results
     WHERE sim_run_dt::date = CURRENT_DATE)                                       AS today_ton,
    -- 평균 선석 대기 (시간)
    (SELECT ROUND(AVG(berth_wait_min)/60.0, 1) FROM simulation_results
     WHERE sim_run_dt::date = CURRENT_DATE)                                       AS avg_berth_wait_hr,
    -- 현재 기상 등급
    (SELECT nav_safety FROM weather_data
     ORDER BY timestamp_utc DESC LIMIT 1)                                         AS current_weather,
    -- 현재 평균 풍속 (kn)
    (SELECT ROUND(AVG(wind_speed_kn), 1) FROM weather_data
     WHERE timestamp_utc = (SELECT MAX(timestamp_utc) FROM weather_data))         AS avg_wind_kn,
    -- 현재 평균 파고 (m)
    (SELECT ROUND(AVG(wave_height_m), 2) FROM weather_data
     WHERE timestamp_utc = (SELECT MAX(timestamp_utc) FROM weather_data))         AS avg_wave_m,
    -- ETA 지연 예상 선박 수
    (SELECT COUNT(*) FROM v_port_eta WHERE eta_status = '지연 예상')              AS delayed_vessel_count,
    -- 평균 크레인 가동률
    (SELECT ROUND(AVG(crane_utilization), 1) FROM simulation_results
     WHERE sim_run_dt::date = CURRENT_DATE)                                       AS avg_crane_util_pct;

COMMENT ON VIEW v_twin_dashboard IS '디지털 트윈 통합 현황판 (현재 상태 + 예측 KPI)';
