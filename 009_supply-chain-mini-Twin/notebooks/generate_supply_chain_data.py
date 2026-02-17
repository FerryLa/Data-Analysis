"""
009 Supply Chain Mini-Twin - 시뮬레이션 데이터 생성
서해안 항만(군산/새만금) ↔ 새만금 산업단지 물류센터
중국/동아시아 교역 기반 Supply Chain Control Tower MVP

대시보드 3개:
  1. Inbound(원자재) 관제 - 선박 ETA, 입항/하역/통관
  2. Inventory & Production Risk - 재고일수, 안전재고, 커버리지
  3. Outbound(출하) & OTIF - 출하 지연, OTIF 추적

알림 5개 (n8n):
  A1: ETA 지연  A2: 재고 커버리지 부족  A3: 생산 라인 스톱 위험
  A4: 항만 체류 과다  A5: 출하 OTIF 리스크
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
import os

np.random.seed(42)

# ============================================================
# 기본 설정
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver")

TODAY = datetime(2025, 2, 17)
SIMULATION_DAYS = 90  # 3개월 시뮬레이션

# ============================================================
# 항만/항구 마스터 데이터
# ============================================================
PORTS = {
    # 중국 주요 항만
    "CNSHA": {"name": "상하이항 (Shanghai)", "lat": 31.2304, "lon": 121.4737, "country": "CN", "type": "origin"},
    "CNQDG": {"name": "칭다오항 (Qingdao)", "lat": 36.0671, "lon": 120.3826, "country": "CN", "type": "origin"},
    "CNNBO": {"name": "닝보항 (Ningbo)", "lat": 29.8683, "lon": 121.5440, "country": "CN", "type": "origin"},
    "CNTSN": {"name": "톈진항 (Tianjin)", "lat": 39.0842, "lon": 117.2010, "country": "CN", "type": "origin"},
    "CNDLC": {"name": "다롄항 (Dalian)", "lat": 38.9140, "lon": 121.6147, "country": "CN", "type": "origin"},
    # 동아시아
    "JPTYO": {"name": "도쿄항 (Tokyo)", "lat": 35.6532, "lon": 139.7965, "country": "JP", "type": "origin"},
    "VNHPH": {"name": "하이퐁항 (Hai Phong)", "lat": 20.8449, "lon": 106.6881, "country": "VN", "type": "origin"},
    # 서해안 도착 항만
    "KRGUN": {"name": "군산항 (Gunsan)", "lat": 35.9900, "lon": 126.7130, "country": "KR", "type": "destination"},
    "KRSMG": {"name": "새만금항 (Saemangeum)", "lat": 35.8200, "lon": 126.6700, "country": "KR", "type": "destination"},
}

# 해상 거리 (해리, nautical miles) - 서해 루트
SEA_DISTANCES_NM = {
    ("CNSHA", "KRGUN"): 520,
    ("CNSHA", "KRSMG"): 530,
    ("CNQDG", "KRGUN"): 380,
    ("CNQDG", "KRSMG"): 390,
    ("CNNBO", "KRGUN"): 560,
    ("CNNBO", "KRSMG"): 570,
    ("CNTSN", "KRGUN"): 480,
    ("CNTSN", "KRSMG"): 490,
    ("CNDLC", "KRGUN"): 420,
    ("CNDLC", "KRSMG"): 430,
    ("JPTYO", "KRGUN"): 680,
    ("JPTYO", "KRSMG"): 690,
    ("VNHPH", "KRGUN"): 1350,
    ("VNHPH", "KRSMG"): 1360,
}

# ============================================================
# 원자재/품목 마스터
# ============================================================
MATERIALS = [
    {"code": "RM-STL-01", "name": "열연강판 (Hot-Rolled Steel)", "unit": "톤", "category": "철강",
     "safety_stock_days": 14, "daily_usage": 50, "unit_cost": 850_000, "lead_time_days": 5},
    {"code": "RM-ALM-01", "name": "알루미늄 잉곳 (Aluminum Ingot)", "unit": "톤", "category": "비철금속",
     "safety_stock_days": 10, "daily_usage": 20, "unit_cost": 3_200_000, "lead_time_days": 4},
    {"code": "RM-CPR-01", "name": "전해동판 (Copper Cathode)", "unit": "톤", "category": "비철금속",
     "safety_stock_days": 10, "daily_usage": 8, "unit_cost": 9_500_000, "lead_time_days": 4},
    {"code": "RM-CHM-01", "name": "리튬 (Lithium Carbonate)", "unit": "톤", "category": "화학",
     "safety_stock_days": 21, "daily_usage": 5, "unit_cost": 45_000_000, "lead_time_days": 7},
    {"code": "RM-PLS-01", "name": "PE 수지 (Polyethylene)", "unit": "톤", "category": "화학",
     "safety_stock_days": 7, "daily_usage": 30, "unit_cost": 1_500_000, "lead_time_days": 3},
    {"code": "RM-RBR-01", "name": "합성고무 (Synthetic Rubber)", "unit": "톤", "category": "화학",
     "safety_stock_days": 10, "daily_usage": 15, "unit_cost": 2_800_000, "lead_time_days": 5},
    {"code": "CP-BMS-01", "name": "BMS 모듈 (Battery Management)", "unit": "개", "category": "전자부품",
     "safety_stock_days": 7, "daily_usage": 200, "unit_cost": 85_000, "lead_time_days": 3},
    {"code": "CP-PCB-01", "name": "PCB 기판 (Printed Circuit Board)", "unit": "매", "category": "전자부품",
     "safety_stock_days": 7, "daily_usage": 500, "unit_cost": 12_000, "lead_time_days": 3},
]

# 완제품 (Outbound)
FINISHED_GOODS = [
    {"code": "FG-BAT-01", "name": "배터리 팩 (Battery Pack)", "unit": "개", "daily_production": 150},
    {"code": "FG-MTR-01", "name": "전기모터 (Electric Motor)", "unit": "개", "daily_production": 80},
    {"code": "FG-INV-01", "name": "인버터 (Inverter)", "unit": "개", "daily_production": 120},
    {"code": "FG-CHG-01", "name": "충전기 (EV Charger)", "unit": "개", "daily_production": 200},
]

# 고객/지역
CUSTOMERS = [
    {"code": "CUS-HMC", "name": "현대자동차", "region": "울산"},
    {"code": "CUS-KIA", "name": "기아자동차", "region": "광주"},
    {"code": "CUS-SSE", "name": "삼성SDI", "region": "천안"},
    {"code": "CUS-LGE", "name": "LG에너지솔루션", "region": "오창"},
    {"code": "CUS-SKI", "name": "SK이노베이션", "region": "서산"},
    {"code": "CUS-EXP", "name": "수출(유럽)", "region": "부산항"},
    {"code": "CUS-EXA", "name": "수출(북미)", "region": "부산항"},
]

# 선박 마스터
VESSELS = [
    {"imo": "IMO9800001", "name": "HANJIN SAEMANGEUM", "type": "벌크선", "capacity_ton": 35000, "speed_knots": 14},
    {"imo": "IMO9800002", "name": "KORYO DRAGON", "type": "컨테이너선", "capacity_teu": 4500, "speed_knots": 18},
    {"imo": "IMO9800003", "name": "YELLOW SEA STAR", "type": "벌크선", "capacity_ton": 50000, "speed_knots": 13},
    {"imo": "IMO9800004", "name": "GUNSAN GLORY", "type": "컨테이너선", "capacity_teu": 2800, "speed_knots": 16},
    {"imo": "IMO9800005", "name": "SUNRISE JEONBUK", "type": "벌크선", "capacity_ton": 28000, "speed_knots": 14.5},
    {"imo": "IMO9800006", "name": "DONGBANG EXPRESS", "type": "컨테이너선", "capacity_teu": 3200, "speed_knots": 17},
    {"imo": "IMO9800007", "name": "WEST SEA PRIDE", "type": "벌크선", "capacity_ton": 42000, "speed_knots": 13.5},
    {"imo": "IMO9800008", "name": "SAEMANGEUM BRIDGE", "type": "컨테이너선", "capacity_teu": 5000, "speed_knots": 19},
]


def haversine(lat1, lon1, lat2, lon2):
    """두 좌표 간 대원거리(km) 계산"""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ============================================================
# 1. Inbound(원자재) 관제 데이터
# ============================================================
def generate_inbound_shipments():
    """선박 입항/하역/통관 시뮬레이션 데이터 생성"""
    records = []
    shipment_id = 1000

    for day_offset in range(SIMULATION_DAYS):
        current_date = TODAY + timedelta(days=day_offset)

        # 하루 평균 2-4건의 선적
        n_shipments = np.random.choice([1, 2, 3, 4], p=[0.15, 0.40, 0.30, 0.15])

        for _ in range(n_shipments):
            shipment_id += 1
            vessel = np.random.choice(VESSELS)
            material = np.random.choice(MATERIALS)

            # 출발항/도착항 선택
            origin_ports = [k for k, v in PORTS.items() if v["type"] == "origin"]
            # 중국이 80%, 일본/베트남 20%
            weights = []
            for p in origin_ports:
                if PORTS[p]["country"] == "CN":
                    weights.append(0.16)
                else:
                    weights.append(0.1)
            weights = np.array(weights) / sum(weights)
            origin = np.random.choice(origin_ports, p=weights)

            dest = np.random.choice(["KRGUN", "KRSMG"], p=[0.55, 0.45])

            # 해상 거리 → 항해 시간
            distance_nm = SEA_DISTANCES_NM.get((origin, dest), 500)
            speed = vessel["speed_knots"]
            voyage_hours = distance_nm / speed
            voyage_days = voyage_hours / 24

            # 출발 시각 (현재일 기준 과거)
            departure_dt = current_date - timedelta(days=voyage_days + np.random.uniform(0, 1))

            # ETA (계획)
            eta_planned = departure_dt + timedelta(hours=voyage_hours)

            # ETA 지연 시뮬레이션 (20% 확률로 지연)
            delay_hours = 0
            if np.random.random() < 0.20:
                delay_hours = int(np.random.choice([2, 4, 6, 8, 12, 24, 36, 48],
                                                   p=[0.25, 0.20, 0.15, 0.15, 0.10, 0.08, 0.05, 0.02]))
            eta_actual = eta_planned + timedelta(hours=delay_hours)

            # 입항 후 프로세스
            berth_wait_hours = int(np.random.choice([0, 1, 2, 4, 8], p=[0.4, 0.25, 0.2, 0.1, 0.05]))
            berth_start = eta_actual + timedelta(hours=berth_wait_hours)

            quantity = int(np.random.randint(100, 2000) if material["unit"] == "톤" else np.random.randint(500, 10000))
            unloading_hours = max(4, quantity / 200)  # 시간당 200톤 하역
            unloading_end = berth_start + timedelta(hours=unloading_hours)

            # 통관 (0.5~3일)
            customs_hours = np.random.uniform(12, 72)
            # 10% 확률로 통관 지연
            if np.random.random() < 0.10:
                customs_hours += np.random.uniform(24, 96)
            customs_clear = unloading_end + timedelta(hours=customs_hours)

            # 내륙 운송 (군산항→새만금 물류센터: 30분~1시간)
            inland_hours = np.random.uniform(0.5, 2.0)
            factory_arrival = customs_clear + timedelta(hours=inland_hours)

            # 상태 결정
            if current_date < departure_dt:
                status = "예약"
            elif current_date < eta_actual:
                status = "항해중"
            elif current_date < berth_start:
                status = "입항대기"
            elif current_date < unloading_end:
                status = "하역중"
            elif current_date < customs_clear:
                status = "통관중"
            elif current_date < factory_arrival:
                status = "내륙운송"
            else:
                status = "입고완료"

            records.append({
                "shipment_id": f"SH-{shipment_id}",
                "vessel_imo": vessel["imo"],
                "vessel_name": vessel["name"],
                "vessel_type": vessel["type"],
                "origin_port": origin,
                "origin_name": PORTS[origin]["name"],
                "origin_country": PORTS[origin]["country"],
                "dest_port": dest,
                "dest_name": PORTS[dest]["name"],
                "material_code": material["code"],
                "material_name": material["name"],
                "material_category": material["category"],
                "quantity": quantity,
                "unit": material["unit"],
                "departure_dt": departure_dt.strftime("%Y-%m-%d %H:%M"),
                "eta_planned": eta_planned.strftime("%Y-%m-%d %H:%M"),
                "eta_actual": eta_actual.strftime("%Y-%m-%d %H:%M"),
                "delay_hours": round(delay_hours, 1),
                "berth_start": berth_start.strftime("%Y-%m-%d %H:%M"),
                "unloading_end": unloading_end.strftime("%Y-%m-%d %H:%M"),
                "customs_clear": customs_clear.strftime("%Y-%m-%d %H:%M"),
                "factory_arrival": factory_arrival.strftime("%Y-%m-%d %H:%M"),
                "status": status,
                "distance_nm": distance_nm,
                "voyage_hours": round(voyage_hours, 1),
                "berth_wait_hours": berth_wait_hours,
                "customs_hours": round(customs_hours, 1),
                "inland_hours": round(inland_hours, 1),
                "snapshot_date": current_date.strftime("%Y-%m-%d"),
            })

    return pd.DataFrame(records)


# ============================================================
# 2. Inventory & Production Risk 데이터
# ============================================================
def generate_inventory_data():
    """일별 재고 & 생산 리스크 데이터 생성"""
    records = []

    for mat in MATERIALS:
        # 초기 재고 = 안전재고의 1.0~2.5배
        current_stock = mat["daily_usage"] * mat["safety_stock_days"] * np.random.uniform(1.0, 2.5)

        for day_offset in range(SIMULATION_DAYS):
            current_date = TODAY + timedelta(days=day_offset)

            # 일일 소비 (변동 ±20%)
            daily_consume = mat["daily_usage"] * np.random.uniform(0.8, 1.2)

            # 입고 (평균 3~7일 간격)
            incoming = 0
            if np.random.random() < (1.0 / np.random.uniform(3, 7)):
                incoming = mat["daily_usage"] * np.random.uniform(3, 10)

            current_stock = max(0, current_stock - daily_consume + incoming)

            # 재고일수(DOS)
            dos = current_stock / mat["daily_usage"] if mat["daily_usage"] > 0 else 999

            # 안전재고 비율
            safety_stock_qty = mat["safety_stock_days"] * mat["daily_usage"]
            safety_ratio = current_stock / safety_stock_qty if safety_stock_qty > 0 else 999

            # 부족 예상일 (현재 재고 / 일일 소비)
            shortage_days = dos

            # 생산 계획 대비 커버리지
            production_plan_days = 14  # 향후 14일 생산 계획
            required_stock = mat["daily_usage"] * production_plan_days
            cover_days = min(dos, production_plan_days)
            coverage_pct = min(100.0, (current_stock / required_stock) * 100) if required_stock > 0 else 100.0

            # 리스크 레벨
            if dos <= 3:
                risk_level = "CRITICAL"
            elif dos <= mat["safety_stock_days"] * 0.5:
                risk_level = "HIGH"
            elif dos <= mat["safety_stock_days"]:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            # 재고 금액
            stock_value = current_stock * mat["unit_cost"]

            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "material_code": mat["code"],
                "material_name": mat["name"],
                "category": mat["category"],
                "unit": mat["unit"],
                "current_stock": round(current_stock, 1),
                "daily_usage": round(daily_consume, 1),
                "incoming": round(incoming, 1),
                "dos": round(dos, 1),
                "safety_stock_days": mat["safety_stock_days"],
                "safety_stock_qty": round(safety_stock_qty, 1),
                "safety_ratio": round(safety_ratio, 2),
                "shortage_forecast_days": round(shortage_days, 1),
                "cover_days": round(cover_days, 1),
                "coverage_pct": round(coverage_pct, 1),
                "risk_level": risk_level,
                "stock_value_krw": round(stock_value),
                "unit_cost": mat["unit_cost"],
                "lead_time_days": mat["lead_time_days"],
            })

    return pd.DataFrame(records)


# ============================================================
# 3. 생산 계획 데이터
# ============================================================
def generate_production_plan():
    """생산 계획 vs 실적 데이터"""
    records = []

    for day_offset in range(SIMULATION_DAYS):
        current_date = TODAY + timedelta(days=day_offset)
        # 주말 생산 감소
        is_weekend = current_date.weekday() >= 5
        weekend_factor = 0.3 if is_weekend else 1.0

        for fg in FINISHED_GOODS:
            planned = round(fg["daily_production"] * weekend_factor)
            # 실적: 계획의 85~105% (자재 부족 시 하락)
            achievement_rate = np.random.uniform(0.85, 1.05)
            # 10% 확률로 자재 부족에 의한 라인 스톱
            line_stop = False
            if np.random.random() < 0.10 and not is_weekend:
                achievement_rate = np.random.uniform(0.3, 0.7)
                line_stop = True

            actual = round(planned * achievement_rate)

            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "product_code": fg["code"],
                "product_name": fg["name"],
                "planned_qty": planned,
                "actual_qty": actual,
                "achievement_rate": round(achievement_rate * 100, 1),
                "line_stop": line_stop,
                "is_weekend": is_weekend,
            })

    return pd.DataFrame(records)


# ============================================================
# 4. Outbound(출하) & OTIF 데이터
# ============================================================
def generate_outbound_orders():
    """출하 주문 & OTIF 추적 데이터"""
    records = []
    order_id = 5000

    for day_offset in range(SIMULATION_DAYS):
        current_date = TODAY + timedelta(days=day_offset)

        # 하루 3~8건 주문
        n_orders = np.random.randint(3, 9)

        for _ in range(n_orders):
            order_id += 1
            customer = np.random.choice(CUSTOMERS)
            fg = np.random.choice(FINISHED_GOODS)

            order_qty = np.random.randint(10, 500)
            # 납기: 주문일 +2~10일
            due_days = np.random.randint(2, 11)
            due_date = current_date + timedelta(days=due_days)

            # 출하 계획일: 납기 -1~2일
            ship_plan_date = due_date - timedelta(days=np.random.randint(1, 3))

            # 실제 출하: 계획 대비 지연 가능
            ship_delay_days = 0
            if np.random.random() < 0.15:  # 15% 지연
                ship_delay_days = int(np.random.choice([1, 2, 3, 5], p=[0.5, 0.3, 0.15, 0.05]))
            ship_actual_date = ship_plan_date + timedelta(days=ship_delay_days)

            # 수량 충족률
            qty_fill_rate = 1.0
            if np.random.random() < 0.08:  # 8% 수량 미달
                qty_fill_rate = np.random.uniform(0.7, 0.95)
            shipped_qty = round(order_qty * qty_fill_rate)

            # OTIF 판정
            on_time = ship_actual_date <= due_date
            in_full = shipped_qty >= order_qty
            otif = on_time and in_full

            # 운송 구간
            if customer["region"] in ["부산항"]:
                transport_mode = "컨테이너 트럭"
                transport_km = np.random.randint(250, 350)
            else:
                transport_mode = "트럭"
                transport_km = np.random.randint(80, 400)

            records.append({
                "order_id": f"ORD-{order_id}",
                "order_date": current_date.strftime("%Y-%m-%d"),
                "customer_code": customer["code"],
                "customer_name": customer["name"],
                "customer_region": customer["region"],
                "product_code": fg["code"],
                "product_name": fg["name"],
                "order_qty": order_qty,
                "shipped_qty": shipped_qty,
                "qty_fill_rate": round(qty_fill_rate * 100, 1),
                "due_date": due_date.strftime("%Y-%m-%d"),
                "ship_plan_date": ship_plan_date.strftime("%Y-%m-%d"),
                "ship_actual_date": ship_actual_date.strftime("%Y-%m-%d"),
                "ship_delay_days": ship_delay_days,
                "on_time": on_time,
                "in_full": in_full,
                "otif": otif,
                "transport_mode": transport_mode,
                "transport_km": transport_km,
            })

    return pd.DataFrame(records)


# ============================================================
# 5. 항만 마커 & 해상 루트 좌표 (지도용)
# ============================================================
def generate_port_markers():
    """Power BI ArcGIS Maps용 항만 마커"""
    records = []
    for code, info in PORTS.items():
        records.append({
            "port_code": code,
            "port_name": info["name"],
            "country": info["country"],
            "latitude": info["lat"],
            "longitude": info["lon"],
            "port_type": info["type"],
            "marker_size": 30 if info["type"] == "destination" else 20,
        })
    return pd.DataFrame(records)


def generate_sea_routes():
    """서해 해상 루트 좌표 (대원 경로 보간)"""
    records = []

    for (origin, dest), distance in SEA_DISTANCES_NM.items():
        o = PORTS[origin]
        d = PORTS[dest]

        # 서해 루트: 중간 웨이포인트 추가 (직선이 아닌 해상 경로)
        n_points = 15
        for i in range(n_points + 1):
            t = i / n_points

            # 선형 보간 + 서해 해상 커브
            lat = o["lat"] + (d["lat"] - o["lat"]) * t
            lon = o["lon"] + (d["lon"] - o["lon"]) * t

            # 서해 중간 해역 보정 (육지 회피)
            if 0.2 < t < 0.8:
                # 서해 중앙부에서 약간 서쪽으로 커브
                curve_offset = math.sin(t * math.pi) * (-0.5)
                lon += curve_offset

            records.append({
                "route_id": f"{origin}-{dest}",
                "origin_port": origin,
                "dest_port": dest,
                "origin_name": o["name"],
                "dest_name": d["name"],
                "sequence": i,
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "distance_nm": distance,
                "point_type": "waypoint" if i in [0, n_points] else "intermediate",
            })

    return pd.DataFrame(records)


# ============================================================
# 6. 새만금 물류 센터 좌표
# ============================================================
def generate_logistics_zones():
    """새만금 산업단지 / 물류 구역 좌표"""
    zones = [
        {"zone_code": "SMG-IND-01", "zone_name": "새만금 산업단지 1구역", "zone_type": "산업단지",
         "lat": 35.8100, "lon": 126.7200, "area_sqm": 500000},
        {"zone_code": "SMG-LOG-01", "zone_name": "새만금 물류센터", "zone_type": "물류센터",
         "lat": 35.8150, "lon": 126.7300, "area_sqm": 200000},
        {"zone_code": "SMG-FTZ-01", "zone_name": "새만금 자유무역지대", "zone_type": "자유무역",
         "lat": 35.8050, "lon": 126.7100, "area_sqm": 300000},
        {"zone_code": "GUN-PRT-01", "zone_name": "군산항 컨테이너 터미널", "zone_type": "항만터미널",
         "lat": 35.9900, "lon": 126.7130, "area_sqm": 150000},
        {"zone_code": "GUN-PRT-02", "zone_name": "군산항 벌크 터미널", "zone_type": "항만터미널",
         "lat": 35.9850, "lon": 126.7080, "area_sqm": 100000},
        {"zone_code": "SMG-PRT-01", "zone_name": "새만금 신항만", "zone_type": "항만터미널",
         "lat": 35.8200, "lon": 126.6700, "area_sqm": 250000},
    ]
    return pd.DataFrame(zones)


# ============================================================
# 7. 알림 이벤트 데이터 (n8n 연동용)
# ============================================================
def generate_alert_events(inbound_df, inventory_df, outbound_df):
    """5대 알림 이벤트 생성"""
    alerts = []
    alert_id = 100

    # A1: ETA 지연 (입항 예정 대비 6시간 초과)
    eta_delays = inbound_df[inbound_df["delay_hours"] >= 6]
    for _, row in eta_delays.iterrows():
        alert_id += 1
        alerts.append({
            "alert_id": f"ALT-{alert_id}",
            "alert_type": "A1",
            "alert_name": "ETA 지연",
            "severity": "HIGH" if row["delay_hours"] >= 24 else "MEDIUM",
            "timestamp": row["eta_actual"],
            "reference_id": row["shipment_id"],
            "message": f"선박 {row['vessel_name']} ETA {row['delay_hours']}시간 지연. "
                       f"원자재: {row['material_name']}, 출발항: {row['origin_name']}",
            "resolved": np.random.random() < 0.7,
        })

    # A2: 재고 커버리지 부족 (5일 이하)
    low_inventory = inventory_df[inventory_df["dos"] <= 5]
    for _, row in low_inventory.iterrows():
        alert_id += 1
        alerts.append({
            "alert_id": f"ALT-{alert_id}",
            "alert_type": "A2",
            "alert_name": "재고 커버리지 부족",
            "severity": "CRITICAL" if row["dos"] <= 2 else "HIGH",
            "timestamp": row["date"],
            "reference_id": row["material_code"],
            "message": f"{row['material_name']} 재고일수 {row['dos']}일. "
                       f"현재고: {row['current_stock']}{row['unit']}",
            "resolved": np.random.random() < 0.5,
        })

    # A3: 생산 라인 스톱 위험 (재고 부족 + 생산 임박)
    critical_inv = inventory_df[inventory_df["risk_level"] == "CRITICAL"]
    for _, row in critical_inv.sample(min(50, len(critical_inv))).iterrows():
        alert_id += 1
        alerts.append({
            "alert_id": f"ALT-{alert_id}",
            "alert_type": "A3",
            "alert_name": "생산 라인 스톱 위험",
            "severity": "CRITICAL",
            "timestamp": row["date"],
            "reference_id": row["material_code"],
            "message": f"{row['material_name']} 재고 부족으로 생산 중단 위험. "
                       f"커버리지: {row['coverage_pct']}%",
            "resolved": np.random.random() < 0.4,
        })

    # A4: 항만 체류 과다 (하역 후 반출 지연 - 통관 48시간 초과)
    port_delays = inbound_df[inbound_df["customs_hours"] >= 48]
    for _, row in port_delays.iterrows():
        alert_id += 1
        alerts.append({
            "alert_id": f"ALT-{alert_id}",
            "alert_type": "A4",
            "alert_name": "항만 체류 과다",
            "severity": "MEDIUM",
            "timestamp": row["customs_clear"],
            "reference_id": row["shipment_id"],
            "message": f"선적 {row['shipment_id']} 통관 {row['customs_hours']}시간 소요. "
                       f"원자재: {row['material_name']}",
            "resolved": np.random.random() < 0.6,
        })

    # A5: 출하 OTIF 리스크 (납기 임박 + 미출고)
    otif_risk = outbound_df[outbound_df["ship_delay_days"] >= 2]
    for _, row in otif_risk.iterrows():
        alert_id += 1
        alerts.append({
            "alert_id": f"ALT-{alert_id}",
            "alert_type": "A5",
            "alert_name": "출하 OTIF 리스크",
            "severity": "HIGH" if row["ship_delay_days"] >= 3 else "MEDIUM",
            "timestamp": row["ship_actual_date"],
            "reference_id": row["order_id"],
            "message": f"주문 {row['order_id']} 출하 {row['ship_delay_days']}일 지연. "
                       f"고객: {row['customer_name']}, 제품: {row['product_name']}",
            "resolved": np.random.random() < 0.5,
        })

    return pd.DataFrame(alerts)


# ============================================================
# 8. KPI 서머리
# ============================================================
def generate_kpi_summary(inbound_df, inventory_df, outbound_df):
    """대시보드 상단 KPI 카드 데이터"""
    return pd.DataFrame([{
        "total_shipments": len(inbound_df["shipment_id"].unique()),
        "avg_delay_hours": round(inbound_df["delay_hours"].mean(), 1),
        "delayed_shipments_pct": round((inbound_df["delay_hours"] > 0).mean() * 100, 1),
        "avg_dos": round(inventory_df["dos"].mean(), 1),
        "critical_items": len(inventory_df[inventory_df["risk_level"] == "CRITICAL"]["material_code"].unique()),
        "total_orders": len(outbound_df),
        "otif_rate": round(outbound_df["otif"].mean() * 100, 1),
        "on_time_rate": round(outbound_df["on_time"].mean() * 100, 1),
        "in_full_rate": round(outbound_df["in_full"].mean() * 100, 1),
        "avg_ship_delay_days": round(outbound_df["ship_delay_days"].mean(), 2),
        "total_inventory_value_krw": round(inventory_df.groupby("date")["stock_value_krw"].sum().mean()),
        "simulation_start": TODAY.strftime("%Y-%m-%d"),
        "simulation_end": (TODAY + timedelta(days=SIMULATION_DAYS)).strftime("%Y-%m-%d"),
    }])


# ============================================================
# MAIN: 데이터 생성 & CSV 저장
# ============================================================
def main():
    print("=" * 60)
    print("009 Supply Chain Mini-Twin - 데이터 생성 시작")
    print("=" * 60)

    os.makedirs(BRONZE_DIR, exist_ok=True)
    os.makedirs(SILVER_DIR, exist_ok=True)

    # 1. Inbound 데이터
    print("\n[1/8] Inbound(원자재) 관제 데이터 생성...")
    inbound_df = generate_inbound_shipments()
    inbound_df.to_csv(os.path.join(BRONZE_DIR, "inbound_shipments.csv"),
                      index=False, encoding="utf-8-sig")
    print(f"  → {len(inbound_df):,}건 생성")

    # 2. Inventory 데이터
    print("[2/8] Inventory & Production Risk 데이터 생성...")
    inventory_df = generate_inventory_data()
    inventory_df.to_csv(os.path.join(BRONZE_DIR, "inventory_daily.csv"),
                        index=False, encoding="utf-8-sig")
    print(f"  → {len(inventory_df):,}건 생성")

    # 3. 생산 계획 데이터
    print("[3/8] 생산 계획/실적 데이터 생성...")
    production_df = generate_production_plan()
    production_df.to_csv(os.path.join(BRONZE_DIR, "production_plan.csv"),
                         index=False, encoding="utf-8-sig")
    print(f"  → {len(production_df):,}건 생성")

    # 4. Outbound 데이터
    print("[4/8] Outbound(출하) & OTIF 데이터 생성...")
    outbound_df = generate_outbound_orders()
    outbound_df.to_csv(os.path.join(BRONZE_DIR, "outbound_orders.csv"),
                       index=False, encoding="utf-8-sig")
    print(f"  → {len(outbound_df):,}건 생성")

    # 5. 항만 마커
    print("[5/8] 항만 마커 데이터 생성...")
    ports_df = generate_port_markers()
    ports_df.to_csv(os.path.join(BRONZE_DIR, "port_markers.csv"),
                    index=False, encoding="utf-8-sig")
    print(f"  → {len(ports_df)}건 생성")

    # 6. 해상 루트
    print("[6/8] 해상 루트 좌표 생성...")
    routes_df = generate_sea_routes()
    routes_df.to_csv(os.path.join(BRONZE_DIR, "sea_routes.csv"),
                     index=False, encoding="utf-8-sig")
    print(f"  → {len(routes_df):,}건 생성")

    # 7. 물류 구역
    print("[7/8] 새만금 물류 구역 데이터 생성...")
    zones_df = generate_logistics_zones()
    zones_df.to_csv(os.path.join(BRONZE_DIR, "logistics_zones.csv"),
                    index=False, encoding="utf-8-sig")
    print(f"  → {len(zones_df)}건 생성")

    # 8. 알림 이벤트
    print("[8/8] 알림 이벤트 데이터 생성...")
    alerts_df = generate_alert_events(inbound_df, inventory_df, outbound_df)
    alerts_df.to_csv(os.path.join(BRONZE_DIR, "alert_events.csv"),
                     index=False, encoding="utf-8-sig")
    print(f"  → {len(alerts_df):,}건 생성")

    # KPI 서머리
    kpi_df = generate_kpi_summary(inbound_df, inventory_df, outbound_df)
    kpi_df.to_csv(os.path.join(SILVER_DIR, "kpi_summary.csv"),
                  index=False, encoding="utf-8-sig")
    print(f"\n  KPI 서머리 → silver/kpi_summary.csv")

    print("\n" + "=" * 60)
    print("데이터 생성 완료!")
    print(f"  Bronze: {BRONZE_DIR}")
    print(f"  Silver: {SILVER_DIR}")
    print("=" * 60)

    # 요약 통계
    print("\n[요약 통계]")
    print(f"  Inbound 선적 건수: {len(inbound_df['shipment_id'].unique()):,}")
    print(f"  평균 ETA 지연: {inbound_df['delay_hours'].mean():.1f}시간")
    print(f"  재고 CRITICAL 일수: {len(inventory_df[inventory_df['risk_level'] == 'CRITICAL']):,}")
    print(f"  OTIF 달성률: {outbound_df['otif'].mean() * 100:.1f}%")
    print(f"  총 알림 이벤트: {len(alerts_df):,}")
    print(f"  알림 유형별:")
    for atype in ["A1", "A2", "A3", "A4", "A5"]:
        count = len(alerts_df[alerts_df["alert_type"] == atype])
        print(f"    {atype}: {count:,}건")


if __name__ == "__main__":
    main()
