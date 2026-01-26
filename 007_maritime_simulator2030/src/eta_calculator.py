"""
ETA (Estimated Time of Arrival) Calculator
==========================================

선박의 현재 위치와 목적지 항구를 기반으로 예상 도착 시간을 계산합니다.
Great Circle 거리 계산과 현재 속도를 사용하여 ETA를 추정합니다.
"""

import math
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from pathlib import Path


@dataclass
class Port:
    """항구 정보"""
    name: str
    latitude: float
    longitude: float


@dataclass
class RouteInfo:
    """항로 정보"""
    vessel_name: str
    mmsi: str
    departure_port: Port
    arrival_port: Port
    departure_time: datetime
    status: str


@dataclass
class ETAResult:
    """ETA 계산 결과"""
    vessel_name: str
    mmsi: str
    current_latitude: float
    current_longitude: float
    departure_port: str
    arrival_port: str
    distance_remaining_nm: float
    speed_knots: float
    eta: datetime
    eta_formatted: str
    voyage_progress_pct: float
    time_elapsed: timedelta
    time_remaining: timedelta


class ETACalculator:
    """ETA 계산 엔진"""

    EARTH_RADIUS_KM = 6371.0
    NAUTICAL_MILES_PER_KM = 0.539957

    @staticmethod
    def calculate_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        두 좌표 간의 Great Circle 거리 계산 (해리)

        Args:
            lat1: 출발 위도
            lon1: 출발 경도
            lat2: 도착 위도
            lon2: 도착 경도

        Returns:
            거리 (해리)
        """
        # Haversine 공식
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        distance_km = ETACalculator.EARTH_RADIUS_KM * c
        distance_nm = distance_km * ETACalculator.NAUTICAL_MILES_PER_KM

        return distance_nm

    @staticmethod
    def calculate_eta(
        current_lat: float,
        current_lon: float,
        destination_lat: float,
        destination_lon: float,
        speed_knots: float,
        current_time: Optional[datetime] = None
    ) -> datetime:
        """
        ETA 계산

        Args:
            current_lat: 현재 위도
            current_lon: 현재 경도
            destination_lat: 목적지 위도
            destination_lon: 목적지 경도
            speed_knots: 현재 속도 (노트)
            current_time: 현재 시각 (None이면 UTC 현재 시각)

        Returns:
            예상 도착 시간
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # 남은 거리 계산 (해리)
        distance_nm = ETACalculator.calculate_distance_nm(
            current_lat, current_lon,
            destination_lat, destination_lon
        )

        # 속도가 0이면 계산 불가
        if speed_knots <= 0:
            # 평균 속도 가정 (10노트)
            speed_knots = 10.0

        # 남은 시간 계산 (시간)
        time_remaining_hours = distance_nm / speed_knots

        # ETA 계산
        eta = current_time + timedelta(hours=time_remaining_hours)

        return eta

    @staticmethod
    def calculate_voyage_progress(
        departure_lat: float,
        departure_lon: float,
        current_lat: float,
        current_lon: float,
        arrival_lat: float,
        arrival_lon: float
    ) -> float:
        """
        항해 진행률 계산 (%)

        Args:
            departure_lat: 출발지 위도
            departure_lon: 출발지 경도
            current_lat: 현재 위도
            current_lon: 현재 경도
            arrival_lat: 도착지 위도
            arrival_lon: 도착지 경도

        Returns:
            진행률 (0-100%)
        """
        # 총 거리
        total_distance = ETACalculator.calculate_distance_nm(
            departure_lat, departure_lon,
            arrival_lat, arrival_lon
        )

        # 이동한 거리
        traveled_distance = ETACalculator.calculate_distance_nm(
            departure_lat, departure_lon,
            current_lat, current_lon
        )

        if total_distance <= 0:
            return 0.0

        progress = (traveled_distance / total_distance) * 100.0

        # 100% 초과 방지
        return min(progress, 100.0)

    @staticmethod
    def load_routes(csv_path: str = None) -> dict:
        """
        항로 데이터 로드

        Args:
            csv_path: CSV 파일 경로 (None이면 기본 경로)

        Returns:
            MMSI를 키로 하는 RouteInfo 딕셔너리
        """
        if csv_path is None:
            csv_path = Path(__file__).parent.parent / 'data' / 'bronze' / 'Ship_Routes.csv'

        df = pd.read_csv(csv_path)

        routes = {}
        for _, row in df.iterrows():
            departure_port = Port(
                name=row['departure_port'],
                latitude=row['departure_lat'],
                longitude=row['departure_lon']
            )

            arrival_port = Port(
                name=row['arrival_port'],
                latitude=row['arrival_lat'],
                longitude=row['arrival_lon']
            )

            route_info = RouteInfo(
                vessel_name=row['vessel_name'],
                mmsi=str(row['mmsi']),
                departure_port=departure_port,
                arrival_port=arrival_port,
                departure_time=pd.to_datetime(row['departure_time']),
                status=row['status']
            )

            routes[str(row['mmsi'])] = route_info

        return routes

    @staticmethod
    def calculate_full_eta(
        vessel_name: str,
        mmsi: str,
        current_lat: float,
        current_lon: float,
        speed_knots: float,
        route_info: RouteInfo,
        current_time: Optional[datetime] = None
    ) -> ETAResult:
        """
        전체 ETA 정보 계산

        Args:
            vessel_name: 선박명
            mmsi: MMSI 번호
            current_lat: 현재 위도
            current_lon: 현재 경도
            speed_knots: 현재 속도
            route_info: 항로 정보
            current_time: 현재 시각

        Returns:
            ETAResult 객체
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # ETA 계산
        eta = ETACalculator.calculate_eta(
            current_lat, current_lon,
            route_info.arrival_port.latitude,
            route_info.arrival_port.longitude,
            speed_knots,
            current_time
        )

        # 남은 거리
        distance_remaining = ETACalculator.calculate_distance_nm(
            current_lat, current_lon,
            route_info.arrival_port.latitude,
            route_info.arrival_port.longitude
        )

        # 항해 진행률
        progress = ETACalculator.calculate_voyage_progress(
            route_info.departure_port.latitude,
            route_info.departure_port.longitude,
            current_lat, current_lon,
            route_info.arrival_port.latitude,
            route_info.arrival_port.longitude
        )

        # 경과 시간
        time_elapsed = current_time - route_info.departure_time

        # 남은 시간
        time_remaining = eta - current_time

        # ETA 포맷 (년-월-일-시)
        eta_formatted = eta.strftime('%Y-%m-%d %H시')

        return ETAResult(
            vessel_name=vessel_name,
            mmsi=mmsi,
            current_latitude=current_lat,
            current_longitude=current_lon,
            departure_port=route_info.departure_port.name,
            arrival_port=route_info.arrival_port.name,
            distance_remaining_nm=distance_remaining,
            speed_knots=speed_knots,
            eta=eta,
            eta_formatted=eta_formatted,
            voyage_progress_pct=progress,
            time_elapsed=time_elapsed,
            time_remaining=time_remaining
        )


def format_timedelta(td: timedelta) -> str:
    """
    timedelta를 읽기 쉬운 형식으로 변환

    Args:
        td: timedelta 객체

    Returns:
        "X일 Y시간 Z분" 형식 문자열
    """
    total_seconds = int(td.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days}일")
    if hours > 0:
        parts.append(f"{hours}시간")
    if minutes > 0 or not parts:
        parts.append(f"{minutes}분")

    return " ".join(parts)


if __name__ == "__main__":
    # 테스트
    calculator = ETACalculator()

    # 예시: Yara Birkeland (노르웨이 연안)
    current_lat = 59.1
    current_lon = 9.65
    destination_lat = 59.1333
    destination_lon = 9.65
    speed = 12.5

    distance = calculator.calculate_distance_nm(
        current_lat, current_lon,
        destination_lat, destination_lon
    )

    eta = calculator.calculate_eta(
        current_lat, current_lon,
        destination_lat, destination_lon,
        speed
    )

    print(f"현재 위치: {current_lat}°N, {current_lon}°E")
    print(f"목적지: {destination_lat}°N, {destination_lon}°E")
    print(f"남은 거리: {distance:.2f} 해리")
    print(f"현재 속도: {speed} 노트")
    print(f"예상 도착 시간: {eta.strftime('%Y-%m-%d %H:%M:%S')}")
