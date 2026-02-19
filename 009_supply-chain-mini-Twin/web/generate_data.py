# -*- coding: utf-8 -*-
"""
서해안 벌크선 AIS + 날씨 데이터 생성기
→ web/data.js 출력 (deck.gl 대시보드용)

006_Panama_ArcGIS 패턴 참고:
  - Bronze: 원시 계산 데이터
  - Silver: 시각화용 정제 데이터 (data.js)
"""

import math, random, json
from datetime import datetime, timedelta

random.seed(42)

# ── 항구 좌표 (실제 기반) ────────────────────────────────────
PORTS = {
    "KRSMG": {"lon": 126.610, "lat": 35.830, "name": "새만금항",  "country": "KR"},
    "KRGUN": {"lon": 126.716, "lat": 35.982, "name": "군산항",    "country": "KR"},
    "CNSHA": {"lon": 121.474, "lat": 31.230, "name": "상하이항",  "country": "CN"},
    "CNDLC": {"lon": 121.615, "lat": 38.914, "name": "다롄항",    "country": "CN"},
    "CNQDG": {"lon": 120.383, "lat": 36.067, "name": "칭다오항",  "country": "CN"},
    "CNNBO": {"lon": 121.544, "lat": 29.868, "name": "닝보항",    "country": "CN"},
    "CNTXG": {"lon": 117.715, "lat": 39.004, "name": "톈진항",    "country": "CN"},
}

# ── 벌크선 항로 (실제 서해 대권 항로 웨이포인트) ─────────────
ROUTES = [
    {
        "id": "R01", "origin": "CNSHA", "dest": "KRSMG",
        "waypoints": [
            (121.47, 31.23), (122.50, 31.80), (123.50, 32.50),
            (124.20, 33.50), (124.80, 34.50), (125.50, 35.20),
            (126.00, 35.60), (126.61, 35.83),
        ],
        "color": [0, 140, 255],
    },
    {
        "id": "R02", "origin": "CNDLC", "dest": "KRSMG",
        "waypoints": [
            (121.62, 38.91), (122.50, 38.20), (123.00, 37.50),
            (123.50, 36.80), (124.00, 36.20), (124.80, 35.80),
            (125.50, 35.60), (126.61, 35.83),
        ],
        "color": [0, 200, 180],
    },
    {
        "id": "R03", "origin": "CNQDG", "dest": "KRGUN",
        "waypoints": [
            (120.38, 36.07), (121.50, 36.20), (122.50, 36.10),
            (123.50, 36.00), (124.50, 36.00), (125.50, 36.00),
            (126.20, 35.98), (126.72, 35.98),
        ],
        "color": [80, 220, 120],
    },
    {
        "id": "R04", "origin": "CNNBO", "dest": "KRSMG",
        "waypoints": [
            (121.54, 29.87), (122.50, 30.50), (123.20, 31.50),
            (123.80, 32.80), (124.30, 33.80), (124.80, 34.60),
            (125.50, 35.20), (126.61, 35.83),
        ],
        "color": [255, 180, 0],
    },
    {
        "id": "R05", "origin": "CNTXG", "dest": "KRSMG",
        "waypoints": [
            (117.72, 39.00), (119.00, 38.50), (120.50, 38.00),
            (122.00, 37.50), (123.00, 37.00), (124.00, 36.50),
            (124.80, 36.00), (125.50, 35.60), (126.61, 35.83),
        ],
        "color": [255, 80, 80],
    },
]

# ── 벌크선 함대 ─────────────────────────────────────────────
FLEET = [
    {"id": "SH-001", "name": "SUNRISE JEONBUK",  "imo": "9800005", "route": "R01", "dwt": 75000, "max_kn": 14.5, "cargo": "석탄",    "qty_ton": 68000, "progress": 0.72},
    {"id": "SH-002", "name": "WEST SEA PRIDE",   "imo": "9800007", "route": "R02", "dwt": 82000, "max_kn": 13.8, "cargo": "철광석",  "qty_ton": 79000, "progress": 0.45},
    {"id": "SH-003", "name": "YELLOW SEA GIANT", "imo": "9800010", "route": "R03", "dwt": 95000, "max_kn": 13.0, "cargo": "곡물",    "qty_ton": 88000, "progress": 0.88},
    {"id": "SH-004", "name": "SAEMANGEUM STAR",  "imo": "9800008", "route": "R04", "dwt": 58000, "max_kn": 12.5, "cargo": "알루미나", "qty_ton": 54000, "progress": 0.30},
    {"id": "SH-005", "name": "NEW JEONBUK",      "imo": "9800012", "route": "R05", "dwt": 65000, "max_kn": 13.5, "cargo": "유연탄",  "qty_ton": 61000, "progress": 0.15},
]

# ── 서해 기상 관측 포인트 ─────────────────────────────────────
WEATHER_POINTS = [
    {"id": "WP-01", "name": "군산 서방",   "lon": 125.50, "lat": 35.80},
    {"id": "WP-02", "name": "새만금 인근", "lon": 126.00, "lat": 35.83},
    {"id": "WP-03", "name": "서해 중부",   "lon": 124.00, "lat": 34.50},
    {"id": "WP-04", "name": "서해 북부",   "lon": 123.50, "lat": 37.00},
    {"id": "WP-05", "name": "군산항 입구", "lon": 126.50, "lat": 35.95},
]

# ────────────────────────────────────────────────────────────

def haversine(lon1, lat1, lon2, lat2):
    R = 3440.065
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def interpolate(wp_list, progress):
    """웨이포인트 목록에서 progress(0~1) 위치 반환"""
    segs = []
    for i in range(len(wp_list) - 1):
        d = haversine(wp_list[i][0], wp_list[i][1], wp_list[i+1][0], wp_list[i+1][1])
        segs.append(d)
    total = sum(segs)
    target = total * progress
    cum = 0
    for i, d in enumerate(segs):
        if cum + d >= target:
            frac = (target - cum) / d
            lon = wp_list[i][0] + (wp_list[i+1][0] - wp_list[i][0]) * frac
            lat = wp_list[i][1] + (wp_list[i+1][1] - wp_list[i][1]) * frac
            return lon, lat
        cum += d
    return wp_list[-1]

def bearing(lon1, lat1, lon2, lat2):
    dl = math.radians(lon2 - lon1)
    la1, la2 = math.radians(lat1), math.radians(lat2)
    x = math.sin(dl) * math.cos(la2)
    y = math.cos(la1)*math.sin(la2) - math.sin(la1)*math.cos(la2)*math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def gen_vessels():
    now = datetime.utcnow()
    vessels = []
    for v in FLEET:
        route = next(r for r in ROUTES if r["id"] == v["route"])
        wp = route["waypoints"]
        lon, lat = interpolate(wp, v["progress"])
        # GPS 노이즈
        lon += random.gauss(0, 0.003)
        lat += random.gauss(0, 0.003)

        dest_p = PORTS[route["dest"]]
        dist_nm = haversine(lon, lat, dest_p["lon"], dest_p["lat"])
        speed = v["max_kn"] * random.uniform(0.85, 0.96)
        eta_hr = dist_nm / speed
        eta_dt = now + timedelta(hours=eta_hr)

        # 이전 위치 (항적: 6시간 전)
        trail = []
        for step in [6, 4, 2, 1, 0.5]:
            back_prog = max(0, v["progress"] - (step * speed) / haversine(
                wp[0][0], wp[0][1], wp[-1][0], wp[-1][1]) * 100 * 0.01)
            tlon, tlat = interpolate(wp, back_prog)
            trail.append([round(tlon, 5), round(tlat, 5)])
        trail.append([round(lon, 5), round(lat, 5)])

        o_port = PORTS[route["origin"]]
        brg = bearing(lon, lat, dest_p["lon"], dest_p["lat"])

        vessels.append({
            "id":          v["id"],
            "name":        v["name"],
            "imo":         v["imo"],
            "lon":         round(lon, 5),
            "lat":         round(lat, 5),
            "speed_kn":    round(speed, 1),
            "course_deg":  round(brg, 1),
            "progress":    round(v["progress"] * 100, 1),
            "dist_nm":     round(dist_nm, 1),
            "eta":         eta_dt.strftime("%m/%d %H:%M"),
            "cargo":       v["cargo"],
            "qty_ton":     v["qty_ton"],
            "dwt":         v["dwt"],
            "origin":      o_port["name"],
            "dest":        dest_p["name"],
            "origin_code": route["origin"],
            "dest_code":   route["dest"],
            "status":      "접안중" if v["progress"] >= 0.98 else "항해중",
            "trail":       trail,
            "route_color": route["color"],
        })
    return vessels

def gen_routes():
    """ArcLayer용 출발-도착 쌍"""
    arcs = []
    for r in ROUTES:
        o = PORTS[r["origin"]]
        d = PORTS[r["dest"]]
        arcs.append({
            "id":         r["id"],
            "src_lon":    o["lon"], "src_lat": o["lat"],
            "dst_lon":    d["lon"], "dst_lat": d["lat"],
            "origin":     o["name"],
            "dest":       d["name"],
            "color":      r["color"],
        })
    return arcs

def gen_ports():
    pts = []
    for code, p in PORTS.items():
        pts.append({
            "code":    code,
            "name":    p["name"],
            "lon":     p["lon"],
            "lat":     p["lat"],
            "country": p["country"],
            "is_dest": code in ("KRSMG", "KRGUN"),
        })
    return pts

def gen_weather():
    now = datetime.utcnow()
    hour = now.hour
    base_wind = 8 + 5 * math.sin(math.pi * hour / 12)
    tide_phase = (now.minute / 60) * 2 * math.pi

    points = []
    for wp in WEATHER_POINTS:
        wind_kn   = round(max(2, base_wind + random.gauss(0, 2.0)), 1)
        wave_m    = round(max(0.2, 0.4 + wind_kn * 0.07 + random.gauss(0, 0.1)), 2)
        current   = round(max(0.3, 1.2 + 0.8 * math.sin(tide_phase) + random.gauss(0, 0.2)), 2)
        wind_dir  = round((315 + random.uniform(-25, 25)) % 360, 1)

        if wind_kn > 20 or wave_m > 2.5:
            safety = "DANGER"
        elif wind_kn > 14 or wave_m > 1.5:
            safety = "CAUTION"
        else:
            safety = "SAFE"

        points.append({
            "id":        wp["id"],
            "name":      wp["name"],
            "lon":       wp["lon"],
            "lat":       wp["lat"],
            "wind_kn":   wind_kn,
            "wind_dir":  wind_dir,
            "wave_m":    wave_m,
            "current_kn": current,
            "water_temp": round(random.uniform(5, 10), 1),
            "visibility": random.choice([5, 10, 15, 20]),
            "safety":    safety,
        })

    # 서해 평균 (헤더 KPI용)
    avg_wind = round(sum(p["wind_kn"] for p in points) / len(points), 1)
    avg_wave = round(sum(p["wave_m"] for p in points) / len(points), 2)
    avg_curr = round(sum(p["current_kn"] for p in points) / len(points), 2)
    worst    = max(points, key=lambda x: {"SAFE":0,"CAUTION":1,"DANGER":2}[x["safety"]])

    return {
        "points":   points,
        "summary":  {
            "avg_wind_kn":   avg_wind,
            "avg_wave_m":    avg_wave,
            "avg_current_kn": avg_curr,
            "overall_safety": worst["safety"],
        },
    }

def gen_kpi(vessels, weather):
    underway  = sum(1 for v in vessels if v["status"] == "항해중")
    moored    = sum(1 for v in vessels if v["status"] == "접안중")
    total_ton = sum(v["qty_ton"] for v in vessels)
    avg_speed = round(sum(v["speed_kn"] for v in vessels) / len(vessels), 1)
    return {
        "underway":    underway,
        "moored":      moored,
        "total_ton":   f"{total_ton:,}",
        "avg_speed_kn": avg_speed,
        "wind_kn":     weather["summary"]["avg_wind_kn"],
        "wave_m":      weather["summary"]["avg_wave_m"],
        "safety":      weather["summary"]["overall_safety"],
        "updated":     datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

def main():
    vessels = gen_vessels()
    routes  = gen_routes()
    ports   = gen_ports()
    weather = gen_weather()
    kpi     = gen_kpi(vessels, weather)

    data = {
        "kpi":      kpi,
        "vessels":  vessels,
        "routes":   routes,
        "ports":    ports,
        "weather":  weather,
    }

    out_path = "web/data.js"
    js = "// Auto-generated by generate_data.py — DO NOT EDIT\n"
    js += f"const DASHBOARD_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"생성 완료: {out_path}")
    print(f"  선박: {len(vessels)}척  |  항로: {len(routes)}개  |  기상관측: {len(weather['points'])}개")
    print(f"  운항중: {kpi['underway']}척  |  풍속: {kpi['wind_kn']}kn  |  파고: {kpi['wave_m']}m  |  기상: {kpi['safety']}")

if __name__ == "__main__":
    main()
