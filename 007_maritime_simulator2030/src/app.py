g"""
Maritime Communication Simulation Platform - Streamlit App
===========================================================

2030 혼합 선박 함대의 실시간 AIS + 위성 통신 추적 시뮬레이터

기능:
- 실시간 선박 위치 지도 시각화
- Dead Reckoning 오차 반경 표시
- 통신 신뢰성 대시보드
- 시나리오 제어 인터페이스
- 지오펜스 모니터링
"""

import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import threading
import os
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드 (프로젝트 루트의 .env 파일)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 로컬 모듈 임포트
from ais_client import AISStreamClient, VesselState
from simulation_ammonia import create_ammonia_fleet, AmmoniaVesselSimulator
from simulation_smr import (
    SMRVesselSimulator,
    SMRVesselConfig,
    create_sample_corridor,
    create_sample_geofences
)
from simulation_oceanic import get_oceanic_ships_predicted_positions
from prediction_engine import DeadReckoningEngine
from scenario_controller import (
    ScenarioController,
    ScenarioConfig,
    CommunicationType,
    create_scenario_normal_conditions,
    create_scenario_heavy_weather,
    create_scenario_satellite_handover
)
from eta_calculator import ETACalculator, format_timedelta


# ============================================================================
# 페이지 설정
# ============================================================================

st.set_page_config(
    page_title="Maritime Communication Simulator 2030",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# 세션 상태 초기화
# ============================================================================

if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.ais_client = None
    st.session_state.ammonia_fleet = []
    st.session_state.smr_vessel = None
    st.session_state.scenario_controller = None
    st.session_state.simulation_running = False
    st.session_state.vessel_states = {}
    st.session_state.prediction_errors = []
    st.session_state.routes = {}  # 항로 정보
    st.session_state.eta_calculator = ETACalculator()


# ============================================================================
# 헬퍼 함수
# ============================================================================

def export_powerbi_data():
    """PowerBI용 데이터를 CSV로 내보내기 (ETA 정보 포함)"""
    try:
        export_data = []
        current_time = datetime.utcnow()

        # 항로 정보 로드 (처음 한 번만)
        if not st.session_state.routes:
            st.session_state.routes = ETACalculator.load_routes()

        # 실시간 AIS 선박 데이터
        for vessel in st.session_state.vessel_states.values():
            # 통신 타입 결정
            if 'AMMONIA' in vessel.vessel_type or 'Ammonia' in vessel.vessel_name:
                comm_type = 'AMMONIA_SIM'
                comm_status = 'Normal'
                color_code = 'Green'
            elif 'SMR' in vessel.vessel_type or 'SMR' in vessel.vessel_name:
                comm_type = 'SMR_SIM'
                comm_status = 'Normal'
                color_code = 'Red'
            else:
                comm_type = 'AIS'
                comm_status = 'Connected'
                color_code = 'Black'

            # ETA 계산 (항로 정보가 있으면)
            eta_info = {}
            if vessel.mmsi in st.session_state.routes:
                route_info = st.session_state.routes[vessel.mmsi]
                eta_result = ETACalculator.calculate_full_eta(
                    vessel.vessel_name,
                    vessel.mmsi,
                    vessel.latitude,
                    vessel.longitude,
                    vessel.speed,
                    route_info,
                    current_time
                )

                eta_info = {
                    'departure_port': eta_result.departure_port,
                    'arrival_port': eta_result.arrival_port,
                    'distance_remaining_nm': round(eta_result.distance_remaining_nm, 2),
                    'eta': eta_result.eta.strftime('%Y-%m-%d %H:%M:%S'),
                    'eta_formatted': eta_result.eta_formatted,
                    'voyage_progress_pct': round(eta_result.voyage_progress_pct, 2),
                    'time_elapsed': format_timedelta(eta_result.time_elapsed),
                    'time_remaining': format_timedelta(eta_result.time_remaining)
                }
            else:
                eta_info = {
                    'departure_port': 'N/A',
                    'arrival_port': 'N/A',
                    'distance_remaining_nm': 0,
                    'eta': 'N/A',
                    'eta_formatted': 'N/A',
                    'voyage_progress_pct': 0,
                    'time_elapsed': 'N/A',
                    'time_remaining': 'N/A'
                }

            export_data.append({
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'vessel_id': vessel.mmsi,
                'vessel_name': vessel.vessel_name,
                'mmsi': vessel.mmsi,
                'vessel_type': vessel.vessel_type,
                'latitude': vessel.latitude,
                'longitude': vessel.longitude,
                'speed_knots': vessel.speed,
                'course_deg': vessel.course,
                'comm_type': comm_type,
                'comm_status': comm_status,
                'data_source': vessel.data_source,
                'color_code': color_code,
                'last_update': vessel.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                **eta_info
            })

        # 예상 위치 선박 데이터 (실시간 데이터가 없는 경우만)
        oceanic_predicted = get_oceanic_ships_predicted_positions()
        for pred in oceanic_predicted:
            has_realtime = pred['mmsi'] in st.session_state.vessel_states

            if not has_realtime:
                # ETA 계산
                eta_info = {}
                if pred['mmsi'] in st.session_state.routes:
                    route_info = st.session_state.routes[pred['mmsi']]
                    eta_result = ETACalculator.calculate_full_eta(
                        pred['vessel_name'],
                        pred['mmsi'],
                        pred['latitude'],
                        pred['longitude'],
                        pred['speed'],
                        route_info,
                        current_time
                    )

                    eta_info = {
                        'departure_port': eta_result.departure_port,
                        'arrival_port': eta_result.arrival_port,
                        'distance_remaining_nm': round(eta_result.distance_remaining_nm, 2),
                        'eta': eta_result.eta.strftime('%Y-%m-%d %H:%M:%S'),
                        'eta_formatted': eta_result.eta_formatted,
                        'voyage_progress_pct': round(eta_result.voyage_progress_pct, 2),
                        'time_elapsed': format_timedelta(eta_result.time_elapsed),
                        'time_remaining': format_timedelta(eta_result.time_remaining)
                    }
                else:
                    eta_info = {
                        'departure_port': 'N/A',
                        'arrival_port': 'N/A',
                        'distance_remaining_nm': 0,
                        'eta': 'N/A',
                        'eta_formatted': 'N/A',
                        'voyage_progress_pct': 0,
                        'time_elapsed': 'N/A',
                        'time_remaining': 'N/A'
                    }

                export_data.append({
                    'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'vessel_id': pred['mmsi'],
                    'vessel_name': pred['vessel_name'],
                    'mmsi': pred['mmsi'],
                    'vessel_type': pred['vessel_type'],
                    'latitude': pred['latitude'],
                    'longitude': pred['longitude'],
                    'speed_knots': pred['speed'],
                    'course_deg': pred['course'],
                    'comm_type': 'SATELLITE_PRED',
                    'comm_status': 'Predicted',
                    'data_source': 'PREDICTED',
                    'color_code': 'LightBlue',
                    'last_update': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    **eta_info
                })

        # DataFrame 생성 및 저장
        df = pd.DataFrame(export_data)

        # powerbi/datasets 폴더에 저장
        export_path = Path(__file__).parent.parent / 'powerbi' / 'datasets'
        export_path.mkdir(parents=True, exist_ok=True)

        # 타임스탬프 파일명
        filename = f"maritime_data_{current_time.strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = export_path / filename

        df.to_csv(filepath, index=False, encoding='utf-8-sig')

        # 최신 데이터로 덮어쓰기 (PowerBI 연동용)
        latest_filepath = export_path / "maritime_data_latest.csv"
        df.to_csv(latest_filepath, index=False, encoding='utf-8-sig')

        st.success(f"✅ 데이터 내보내기 완료!\n파일: {filename}\n경로: {export_path}")

    except Exception as e:
        st.error(f"❌ 데이터 내보내기 실패: {str(e)}")


def create_vessel_marker(vessel: VesselState, map_obj: folium.Map, is_predicted: bool = False):
    """선박 마커를 지도에 추가

    Args:
        vessel: 선박 상태 객체
        map_obj: Folium 지도 객체
        is_predicted: True이면 하늘색 예상 위치 마커, False이면 선박 타입별 색상 마커
    """

    if is_predicted:
        # 예상 위치: 하늘색 마커
        color = 'lightblue'
        icon_name = 'map-marker'
        marker_prefix = 'fa'
        arrow_color = 'lightblue'
    else:
        # 실시간 선박: 타입별 색상
        icon_name = 'ship'
        marker_prefix = 'fa'

        if 'AMMONIA' in vessel.vessel_type or 'Ammonia' in vessel.vessel_name:
            color = 'green'
            arrow_color = 'green'
        elif 'SMR' in vessel.vessel_type or 'SMR' in vessel.vessel_name:
            color = 'red'
            arrow_color = 'red'
        else:
            # AIS 실시간 (자율선박, LNG 등)
            color = 'black'
            arrow_color = 'black'

    # 아이콘 생성
    icon = folium.Icon(
        color=color,
        icon=icon_name,
        prefix=marker_prefix
    )

    # 팝업 내용
    if is_predicted:
        source_label = "🔵 예상 위치 (시뮬레이션)"
    else:
        if color == 'green':
            source_label = "🟢 암모니아 선박 (시뮬레이션)"
        elif color == 'red':
            source_label = "🔴 SMR 선박 (시뮬레이션)"
        else:
            source_label = "⚫ 실시간 AIS"

    popup_html = f"""
    <div style="font-family: Arial; font-size: 12px;">
        <b>{vessel.vessel_name}</b><br>
        Type: {vessel.vessel_type}<br>
        MMSI: {vessel.mmsi}<br>
        Speed: {vessel.speed:.1f} knots<br>
        Course: {vessel.course:.1f}°<br>
        Position: {vessel.latitude:.4f}°N, {vessel.longitude:.4f}°E<br>
        Time: {vessel.timestamp.strftime('%H:%M:%S UTC')}<br>
        Source: {source_label}
    </div>
    """

    # 마커 추가
    folium.Marker(
        location=[vessel.latitude, vessel.longitude],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=vessel.vessel_name,
        icon=icon
    ).add_to(map_obj)

    # 침로 방향 표시 (화살표) - 예상 위치는 표시 안 함
    if not is_predicted:
        folium.RegularPolygonMarker(
            location=[vessel.latitude, vessel.longitude],
            fill_color=arrow_color,
            number_of_sides=3,
            radius=8,
            rotation=vessel.course,
            opacity=0.7
        ).add_to(map_obj)


def create_error_radius_circle(
    lat: float,
    lon: float,
    radius_m: float,
    map_obj: folium.Map,
    color: str = 'orange'
):
    """오차 반경 원 추가"""

    folium.Circle(
        location=[lat, lon],
        radius=radius_m,
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.2,
        opacity=0.5,
        weight=2
    ).add_to(map_obj)


def initialize_simulation():
    """시뮬레이션 초기화"""

    # AIS 클라이언트 (환경 변수에서 API 키 로드)
    api_key = os.getenv("AISSTREAM_API_KEY")

    if api_key and api_key != "your_api_key_here":
        try:
            st.info(f"🔌 AIS 클라이언트 연결 중... (API 키: {api_key[:10]}...)")
            st.session_state.ais_client = AISStreamClient(api_key=api_key)
            st.session_state.ais_client.start()
            st.success("✅ AIS 클라이언트 시작됨!")
        except Exception as e:
            st.error(f"❌ AIS 클라이언트 초기화 실패: {e}")
            st.session_state.ais_client = None
    else:
        st.warning("⚠️ AIS API 키가 없습니다. 시뮬레이션 데이터만 사용합니다.")
        st.session_state.ais_client = None

    # 암모니아 선박 함대
    st.session_state.ammonia_fleet = create_ammonia_fleet()

    # SMR 선박
    smr_config = SMRVesselConfig(vessel_name="SMR-PACIFIC-PIONEER")
    corridor = create_sample_corridor()
    geofences = create_sample_geofences()

    st.session_state.smr_vessel = SMRVesselSimulator(
        config=smr_config,
        corridor=corridor,
        geofence_zones=geofences
    )

    # 시나리오 컨트롤러
    scenario_config = create_scenario_normal_conditions()
    st.session_state.scenario_controller = ScenarioController(scenario_config)

    st.session_state.initialized = True


def simulation_step():
    """시뮬레이션 1 스텝 실행"""

    # 암모니아 선박 업데이트
    for vessel_sim in st.session_state.ammonia_fleet:
        state = vessel_sim.step(delta_time_sec=10)
        st.session_state.vessel_states[state.mmsi] = state

    # SMR 선박 업데이트
    smr_state = st.session_state.smr_vessel.step(delta_time_sec=10)
    st.session_state.vessel_states[smr_state.mmsi] = smr_state

    # AIS 선박 상태 가져오기 (실시간)
    if st.session_state.ais_client:
        ais_vessels = st.session_state.ais_client.get_latest_vessels()
        for mmsi, vessel in ais_vessels.items():
            st.session_state.vessel_states[mmsi] = vessel


# ============================================================================
# 메인 UI
# ============================================================================

def main():
    """메인 애플리케이션"""

    # 타이틀
    st.title("🚢 Maritime Communication Simulator 2030")
    st.markdown("**AIS + 위성 통신 기반 혼합 선박 함대 추적 시뮬레이터**")

    # 사이드바
    with st.sidebar:
        st.header("⚙️ 제어 패널")

        # 초기화 버튼
        if not st.session_state.initialized:
            if st.button("🚀 시뮬레이션 초기화", type="primary"):
                with st.spinner("초기화 중..."):
                    initialize_simulation()
                st.success("초기화 완료!")
                st.rerun()

        else:
            # 시뮬레이션 제어
            col1, col2 = st.columns(2)

            with col1:
                if st.button("▶️ 시작"):
                    st.session_state.simulation_running = True

            with col2:
                if st.button("⏸️ 정지"):
                    st.session_state.simulation_running = False

            # 업데이트 간격 조절
            if st.session_state.simulation_running:
                st.info("▶️ 시뮬레이션 실행 중 - 🔄 수동 새로고침 버튼을 클릭하여 지도를 업데이트하세요")
                if st.button("🔄 지도 새로고침"):
                    st.rerun()

            st.divider()

            # 시나리오 선택
            st.subheader("📡 통신 시나리오")

            scenario_choice = st.selectbox(
                "시나리오 선택",
                ["정상 조건", "악천후", "LEO 위성 핸드오버"]
            )

            if scenario_choice == "정상 조건":
                scenario_config = create_scenario_normal_conditions()
            elif scenario_choice == "악천후":
                scenario_config = create_scenario_heavy_weather()
            else:
                scenario_config = create_scenario_satellite_handover()

            st.session_state.scenario_controller = ScenarioController(scenario_config)

            # 저하 수준 슬라이더
            degradation = st.slider(
                "통신 저하 수준",
                min_value=0.0,
                max_value=1.0,
                value=scenario_config.degradation_level,
                step=0.1
            )

            st.session_state.scenario_controller.config.degradation_level = degradation

            st.divider()

            # 통계
            st.subheader("📊 시뮬레이션 통계")

            total_vessels = len(st.session_state.vessel_states)
            st.metric("총 선박 수", total_vessels)

            # AIS 연결 상태
            if st.session_state.ais_client:
                ais_stats = st.session_state.ais_client.get_statistics()
                if ais_stats['is_connected']:
                    st.success(f"✅ AIS 연결됨 (추적 중: {ais_stats['vessels_tracked']}척)")
                else:
                    st.warning(f"⚠️ AIS 연결 중... (재시도: {ais_stats['reconnect_attempts']})")
                st.caption(f"수신: {ais_stats['messages_received']} | 필터링: {ais_stats['messages_filtered']}")
            else:
                st.error("❌ AIS 클라이언트 없음")

            if st.session_state.scenario_controller:
                stats = st.session_state.scenario_controller.get_statistics()
                st.metric(
                    "통신 신뢰성 지수",
                    f"{stats['reliability_index']:.1f}%"
                )
                st.metric(
                    "평균 지연",
                    f"{stats['average_latency_ms']:.0f} ms"
                )

    # 메인 콘텐츠
    if not st.session_state.initialized:
        st.info("👈 왼쪽 사이드바에서 시뮬레이션을 초기화하세요.")
        return

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ 실시간 지도",
        "⏱️ ETA 현황",
        "📈 성능 분석",
        "⚠️ 이벤트 로그",
        "ℹ️ 시스템 정보"
    ])

    # 탭 1: 실시간 지도
    with tab1:
        st.subheader("실시간 선박 위치 추적")

        # 시뮬레이션 스텝 실행
        if st.session_state.simulation_running:
            simulation_step()

        # 지도 생성
        if st.session_state.vessel_states:
            # 대양 선박 예상 위치 가져오기
            oceanic_predicted = get_oceanic_ships_predicted_positions()

            # 중심 좌표 계산 (모든 선박의 평균)
            lats = [v.latitude for v in st.session_state.vessel_states.values()]
            lons = [v.longitude for v in st.session_state.vessel_states.values()]

            # 예상 위치도 중심 계산에 포함
            for pred in oceanic_predicted:
                lats.append(pred['latitude'])
                lons.append(pred['longitude'])

            center_lat = sum(lats) / len(lats) if lats else 0
            center_lon = sum(lons) / len(lons) if lons else 0

            # Folium 지도 생성
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=3,
                tiles='OpenStreetMap'
            )

            # 실시간 AIS 선박 마커 추가 (검은색)
            oceanic_mmsi_set = {pred['mmsi'] for pred in oceanic_predicted}

            for vessel in st.session_state.vessel_states.values():
                # 실시간 데이터가 있는 선박은 검은색 마커로 표시
                create_vessel_marker(vessel, m, is_predicted=False)

                # Dead Reckoning 오차 반경 (예시)
                if vessel.data_source != "AIS":
                    dr_engine = DeadReckoningEngine()
                    # 10분 경과 가정
                    prediction = dr_engine.predict_position(
                        last_latitude=vessel.latitude,
                        last_longitude=vessel.longitude,
                        course_deg=vessel.course,
                        speed_knots=vessel.speed,
                        time_elapsed_seconds=600
                    )

                    create_error_radius_circle(
                        vessel.latitude,
                        vessel.longitude,
                        prediction.error_radius_95,
                        m,
                        color='orange'
                    )

            # 대양 선박 예상 위치 추가 (빨간색) - 실시간 데이터가 없는 경우만
            for pred in oceanic_predicted:
                # 실시간 AIS 데이터가 있는지 확인
                has_realtime = pred['mmsi'] in st.session_state.vessel_states

                if not has_realtime:
                    # 실시간 데이터가 없으면 예상 위치를 빨간색 마커로 표시
                    predicted_vessel = VesselState(
                        vessel_name=pred['vessel_name'],
                        mmsi=pred['mmsi'],
                        latitude=pred['latitude'],
                        longitude=pred['longitude'],
                        speed=pred['speed'],
                        course=pred['course'],
                        vessel_type=pred['vessel_type'],
                        timestamp=datetime.utcnow(),
                        data_source='PREDICTED'
                    )

                    create_vessel_marker(predicted_vessel, m, is_predicted=True)

            # 지도 렌더링
            folium_static(m, width=1200, height=600)

        else:
            st.warning("선박 데이터가 없습니다. 시뮬레이션을 시작하세요.")

        # 선박 목록
        st.subheader("선박 목록")

        if st.session_state.vessel_states:
            vessel_data = []

            # 실시간 AIS 선박
            for vessel in st.session_state.vessel_states.values():
                # 선박 타입별 이모지
                if 'AMMONIA' in vessel.vessel_type or 'Ammonia' in vessel.vessel_name:
                    emoji = "🟢"
                elif 'SMR' in vessel.vessel_type or 'SMR' in vessel.vessel_name:
                    emoji = "🔴"
                else:
                    emoji = "⚫"

                vessel_data.append({
                    '이름': vessel.vessel_name,
                    '타입': vessel.vessel_type,
                    'MMSI': vessel.mmsi,
                    '위도': f"{vessel.latitude:.4f}",
                    '경도': f"{vessel.longitude:.4f}",
                    '속도 (knots)': f"{vessel.speed:.1f}",
                    '침로 (°)': f"{vessel.course:.1f}",
                    '소스': emoji + " " + vessel.data_source
                })

            # 예상 위치 선박 (실시간 데이터가 없는 경우만)
            oceanic_predicted = get_oceanic_ships_predicted_positions()

            for pred in oceanic_predicted:
                has_realtime = pred['mmsi'] in st.session_state.vessel_states

                if not has_realtime:
                    vessel_data.append({
                        '이름': pred['vessel_name'],
                        '타입': pred['vessel_type'],
                        'MMSI': pred['mmsi'],
                        '위도': f"{pred['latitude']:.4f}",
                        '경도': f"{pred['longitude']:.4f}",
                        '속도 (knots)': f"{pred['speed']:.1f}",
                        '침로 (°)': f"{pred['course']:.1f}",
                        '소스': "🔵 PREDICTED (" + pred['current_leg'] + ")"
                    })

            df = pd.DataFrame(vessel_data)
            st.dataframe(df, use_container_width=True)

            # PowerBI용 CSV Export 버튼
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("📊 PowerBI용 데이터 내보내기"):
                    export_powerbi_data()

    # 탭 2: ETA 현황
    with tab2:
        st.subheader("⏱️ 선박 ETA (예상 도착 시간) 현황")

        # 항로 정보 로드
        if not st.session_state.routes:
            st.session_state.routes = ETACalculator.load_routes()

        current_time = datetime.utcnow()
        eta_data = []

        # 실시간 선박 ETA 계산
        for vessel in st.session_state.vessel_states.values():
            if vessel.mmsi in st.session_state.routes:
                route_info = st.session_state.routes[vessel.mmsi]
                eta_result = ETACalculator.calculate_full_eta(
                    vessel.vessel_name,
                    vessel.mmsi,
                    vessel.latitude,
                    vessel.longitude,
                    vessel.speed,
                    route_info,
                    current_time
                )

                eta_data.append({
                    '선박명': eta_result.vessel_name,
                    'MMSI': eta_result.mmsi,
                    '출발지': eta_result.departure_port,
                    '도착지': eta_result.arrival_port,
                    '현재 위치': f"{eta_result.current_latitude:.4f}°N, {eta_result.current_longitude:.4f}°E",
                    '속도': f"{eta_result.speed_knots:.1f} kn",
                    '남은 거리': f"{eta_result.distance_remaining_nm:.1f} nm",
                    '진행률': f"{eta_result.voyage_progress_pct:.1f}%",
                    '경과 시간': eta_result.time_elapsed,
                    '남은 시간': eta_result.time_remaining,
                    'ETA': eta_result.eta_formatted
                })

        # 예상 위치 선박 ETA 계산
        oceanic_predicted = get_oceanic_ships_predicted_positions()
        for pred in oceanic_predicted:
            if pred['mmsi'] not in st.session_state.vessel_states:
                if pred['mmsi'] in st.session_state.routes:
                    route_info = st.session_state.routes[pred['mmsi']]
                    eta_result = ETACalculator.calculate_full_eta(
                        pred['vessel_name'],
                        pred['mmsi'],
                        pred['latitude'],
                        pred['longitude'],
                        pred['speed'],
                        route_info,
                        current_time
                    )

                    eta_data.append({
                        '선박명': eta_result.vessel_name,
                        'MMSI': eta_result.mmsi,
                        '출발지': eta_result.departure_port,
                        '도착지': eta_result.arrival_port,
                        '현재 위치': f"{eta_result.current_latitude:.4f}°N, {eta_result.current_longitude:.4f}°E",
                        '속도': f"{eta_result.speed_knots:.1f} kn",
                        '남은 거리': f"{eta_result.distance_remaining_nm:.1f} nm",
                        '진행률': f"{eta_result.voyage_progress_pct:.1f}%",
                        '경과 시간': format_timedelta(eta_result.time_elapsed),
                        '남은 시간': format_timedelta(eta_result.time_remaining),
                        'ETA': eta_result.eta_formatted
                    })

        if eta_data:
            df_eta = pd.DataFrame(eta_data)
            st.dataframe(df_eta, use_container_width=True)

            # ETA 시각화 (진행률 바 차트)
            st.subheader("항해 진행률")
            progress_data = []
            for item in eta_data:
                progress_data.append({
                    '선박명': item['선박명'],
                    '진행률': float(item['진행률'].replace('%', ''))
                })

            df_progress = pd.DataFrame(progress_data)
            fig = px.bar(
                df_progress,
                x='진행률',
                y='선박명',
                orientation='h',
                title='선박별 항해 진행률 (%)',
                labels={'진행률': '진행률 (%)', '선박명': '선박'},
                color='진행률',
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("항로 정보가 있는 선박이 없습니다.")

    # 탭 3: 성능 분석
    with tab3:
        st.subheader("통신 성능 분석")

        if st.session_state.scenario_controller:
            stats = st.session_state.scenario_controller.get_statistics()

            # 메트릭 카드
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("총 패킷", stats['total_packets'])

            with col2:
                st.metric("손실 패킷", stats['lost_packets'])

            with col3:
                st.metric(
                    "신뢰성 지수",
                    f"{stats['reliability_index']:.2f}%"
                )

            with col4:
                st.metric(
                    "패킷 손실률",
                    f"{stats['packet_loss_rate']:.2%}"
                )

            # 시계열 그래프 (예시)
            st.subheader("예측 오차 시계열")

            if st.session_state.prediction_errors:
                fig = px.line(
                    st.session_state.prediction_errors,
                    x='time',
                    y='error_m',
                    title='Dead Reckoning 예측 오차 (미터)'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("아직 오차 데이터가 없습니다.")

        else:
            st.warning("시나리오 컨트롤러가 초기화되지 않았습니다.")

    # 탭 4: 이벤트 로그
    with tab4:
        st.subheader("항로 이탈 및 위반 이벤트")

        if st.session_state.smr_vessel:
            violations = st.session_state.smr_vessel.get_violation_log()

            if violations:
                event_data = []

                for event in violations[-20:]:  # 최근 20건
                    event_data.append({
                        '시간': event.timestamp.strftime('%H:%M:%S'),
                        '이벤트': event.event_type,
                        '심각도': event.severity,
                        '위도': f"{event.latitude:.4f}",
                        '경도': f"{event.longitude:.4f}",
                        '상세': str(event.details)
                    })

                df = pd.DataFrame(event_data)
                st.dataframe(df, use_container_width=True)

            else:
                st.success("위반 이벤트가 없습니다.")

    # 탭 5: 시스템 정보
    with tab5:
        st.subheader("시스템 정보")

        st.markdown("""
        ### 📡 통신 프로파일

        **AIS 지상국**:
        - 지연: 2000±500ms
        - 정상 업데이트: 10초

        **VSAT 위성**:
        - 지연: 500±100ms
        - 정상 업데이트: 5초

        **LEO 위성** (Starlink, OneWeb):
        - 지연: 30±10ms
        - 정상 업데이트: 2초

        ---

        ### 🚢 선박 구성

        - **Q-Max LNG 운반선**: 14척 (실시간 AIS)
        - **암모니아 연료선**: 5척 (시뮬레이션)
        - **SMR 추진 선박**: 1척 (시뮬레이션)

        ---

        ### 🧮 수학적 모델

        **Dead Reckoning**:
        ```
        φ₂ = asin(sin(φ₁)·cos(δ) + cos(φ₁)·sin(δ)·cos(θ))
        λ₂ = λ₁ + atan2(sin(θ)·sin(δ)·cos(φ₁), cos(δ) - sin(φ₁)·sin(φ₂))
        ```

        **오차 반경 (95% 신뢰)**:
        ```
        r₉₅(t) = 2.45 · √(σ_sensor² + σ_course²·t² + σ_speed²·t²)
        ```
        """)

    # 자동 갱신 (지도 탭이 아닐 때만)
    # 지도 깜빡임 방지: 수동 새로고침 버튼 사용
    if st.session_state.simulation_running:
        with st.sidebar:
            if st.button("🔄 수동 새로고침"):
                st.rerun()


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    main()
