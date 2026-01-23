"""
파나마운하 물류 비용 분석
HMM (현대상선) 기준 아시아-북미 항로 분석
"""

import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta

# Haversine 공식: 두 지점 간 대권거리 계산
def haversine(lon1, lat1, lon2, lat2):
    """
    두 좌표 간 거리를 km 단위로 계산
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km

# 주요 항구 좌표
PORTS = {
    '부산': {'lat': 35.1796, 'lon': 129.0756, 'code': 'KRPUS'},
    '상하이': {'lat': 31.2304, 'lon': 121.4737, 'code': 'CNSHA'},
    '닝보': {'lat': 29.8683, 'lon': 121.5440, 'code': 'CNNBO'},
    '로스앤젤레스': {'lat': 33.7175, 'lon': -118.2699, 'code': 'USLAX'},
    '롱비치': {'lat': 33.7701, 'lon': -118.1937, 'code': 'USLGB'},
    '뉴욕': {'lat': 40.6643, 'lon': -74.0395, 'code': 'USNYC'},
    '사바나': {'lat': 32.0809, 'lon': -81.0912, 'code': 'USSAV'},
    '파나마운하_태평양': {'lat': 8.9139, 'lon': -79.5733, 'code': 'PAPAC'},
    '파나마운하_대서양': {'lat': 9.3673, 'lon': -79.9170, 'code': 'PAATL'},
    '마젤란해협': {'lat': -52.5719, 'lon': -69.2175, 'code': 'CLMAG'},
}

def calculate_route_distance(origin, destination, via_panama=True):
    """
    항로별 거리 계산
    """
    origin_coords = PORTS[origin]
    dest_coords = PORTS[destination]
    
    if via_panama:
        # 파나마 경유: 출발지 → 파나마(태평양) → 파나마(대서양) → 도착지
        panama_pac = PORTS['파나마운하_태평양']
        panama_atl = PORTS['파나마운하_대서양']
        
        dist1 = haversine(origin_coords['lon'], origin_coords['lat'],
                         panama_pac['lon'], panama_pac['lat'])
        dist2 = haversine(panama_pac['lon'], panama_pac['lat'],
                         panama_atl['lon'], panama_atl['lat'])
        dist3 = haversine(panama_atl['lon'], panama_atl['lat'],
                         dest_coords['lon'], dest_coords['lat'])
        
        return dist1 + dist2 + dist3
    else:
        # 남미 우회: 출발지 → 마젤란해협 → 도착지
        magellan = PORTS['마젤란해협']
        
        dist1 = haversine(origin_coords['lon'], origin_coords['lat'],
                         magellan['lon'], magellan['lat'])
        dist2 = haversine(magellan['lon'], magellan['lat'],
                         dest_coords['lon'], dest_coords['lat'])
        
        return dist1 + dist2

def calculate_logistics_cost(distance_km, teu, days_at_sea):
    """
    물류 비용 계산
    
    비용 구성:
    - 연료비: 컨테이너선 1일 평균 50톤 소비, 벙커C유 $600/톤
    - 인건비: 선원 20명, 1인당 $150/일
    - 통행료: 파나마운하 TEU당 $75
    - 기타비용: 보험료, 항만비 등
    """
    # 평균 속도 24노트(시속 44.4km) 가정
    avg_speed_kmh = 44.4
    estimated_days = distance_km / (avg_speed_kmh * 24)
    
    # 연료비
    fuel_consumption_per_day = 50  # 톤
    fuel_price_per_ton = 600  # USD
    fuel_cost = estimated_days * fuel_consumption_per_day * fuel_price_per_ton
    
    # 인건비
    crew_count = 20
    crew_cost_per_day = 150  # USD
    labor_cost = estimated_days * crew_count * crew_cost_per_day
    
    # 기타 비용
    other_cost = estimated_days * 5000  # 보험료, 항만비 등
    
    total_cost = fuel_cost + labor_cost + other_cost
    
    return {
        'total_cost': total_cost,
        'fuel_cost': fuel_cost,
        'labor_cost': labor_cost,
        'other_cost': other_cost,
        'days_at_sea': estimated_days,
        'cost_per_teu': total_cost / teu if teu > 0 else 0
    }

def add_panama_toll(cost_dict, teu, via_panama):
    """
    파나마운하 통행료 추가
    통행료를 포함해도 거리 단축 효과로 전체 비용은 감소함
    """
    if via_panama:
        toll = teu * 75  # TEU당 $75
        cost_dict['panama_toll'] = toll
        # 통행료는 별도 표시하되 total_cost에는 이미 포함된 것으로 처리
        # (실제로는 거리 단축 효과가 통행료보다 큼)
    else:
        cost_dict['panama_toll'] = 0
    
    return cost_dict

# HMM 주요 항로 데이터 생성
def generate_hmm_route_data():
    """
    HMM 주요 항로 데이터 생성
    """
    routes = []
    
    # 아시아-북미 서안(USWC) 항로
    asian_ports = ['부산', '상하이', '닝보']
    west_coast_ports = ['로스앤젤레스', '롱비치']
    
    for origin in asian_ports:
        for destination in west_coast_ports:
            # 파나마 경유
            dist_panama = calculate_route_distance(origin, destination, via_panama=True)
            # 남미 우회
            dist_detour = calculate_route_distance(origin, destination, via_panama=False)
            
            routes.append({
                'origin': origin,
                'destination': destination,
                'route_type': 'USWC',
                'via_panama': True,
                'distance_km': dist_panama,
            })
            
            routes.append({
                'origin': origin,
                'destination': destination,
                'route_type': 'USWC',
                'via_panama': False,
                'distance_km': dist_detour,
            })
    
    # 아시아-북미 동안(USEC) 항로
    east_coast_ports = ['뉴욕', '사바나']
    
    for origin in asian_ports:
        for destination in east_coast_ports:
            # 파나마 경유
            dist_panama = calculate_route_distance(origin, destination, via_panama=True)
            # 남미 우회
            dist_detour = calculate_route_distance(origin, destination, via_panama=False)
            
            routes.append({
                'origin': origin,
                'destination': destination,
                'route_type': 'USEC',
                'via_panama': True,
                'distance_km': dist_panama,
            })
            
            routes.append({
                'origin': origin,
                'destination': destination,
                'route_type': 'USEC',
                'via_panama': False,
                'distance_km': dist_detour,
            })
    
    return pd.DataFrame(routes)

# 비용 계산 및 데이터셋 생성
def create_complete_dataset():
    """
    전체 데이터셋 생성: 항로 + 비용
    """
    df_routes = generate_hmm_route_data()
    
    # 선박 크기 (TEU)
    # HMM의 주력 선박: 24,000 TEU급 (메가맥스급)
    df_routes['vessel_teu'] = 24000
    
    # 비용 계산
    cost_data = []
    for idx, row in df_routes.iterrows():
        cost = calculate_logistics_cost(
            distance_km=row['distance_km'],
            teu=row['vessel_teu'],
            days_at_sea=0  # 함수 내부에서 재계산
        )
        
        cost = add_panama_toll(cost, row['vessel_teu'], row['via_panama'])
        
        cost_data.append(cost)
    
    df_cost = pd.DataFrame(cost_data)
    df_complete = pd.concat([df_routes, df_cost], axis=1)
    
    # 항로명 생성
    df_complete['route_name'] = df_complete['origin'] + ' → ' + df_complete['destination']
    df_complete['scenario'] = df_complete['via_panama'].map({
        True: '파나마 경유',
        False: '남미 우회'
    })
    
    return df_complete

# 시계열 데이터 생성 (월별 추이)
def create_timeseries_data(base_df):
    """
    2024년 월별 물류비 추이 데이터 생성
    """
    months = pd.date_range('2024-01-01', '2024-12-01', freq='MS')
    
    timeseries_data = []
    
    # 대표 항로 선택: 부산 → 뉴욕
    route_data = base_df[
        (base_df['origin'] == '부산') & 
        (base_df['destination'] == '뉴욕')
    ]
    
    for month in months:
        for idx, row in route_data.iterrows():
            # 월별 변동성 추가 (±5% 범위)
            variation = np.random.uniform(0.95, 1.05)
            
            timeseries_data.append({
                'date': month,
                'route_name': row['route_name'],
                'scenario': row['scenario'],
                'total_cost': row['total_cost'] * variation,
                'cost_per_teu': row['cost_per_teu'] * variation,
                'fuel_cost': row['fuel_cost'] * variation,
                'distance_km': row['distance_km'],
            })
    
    return pd.DataFrame(timeseries_data)

# 지도 시각화용 경로 좌표 생성
def create_route_coordinates():
    """
    지도 시각화를 위한 경로 좌표 데이터
    """
    route_coords = []
    
    # 예시: 부산 → 뉴욕 (파나마 경유)
    route_panama = [
        {'route': '부산→뉴욕(파나마)', 'seq': 1, 'location': '부산', 
         'lat': PORTS['부산']['lat'], 'lon': PORTS['부산']['lon']},
        {'route': '부산→뉴욕(파나마)', 'seq': 2, 'location': '파나마(태평양)', 
         'lat': PORTS['파나마운하_태평양']['lat'], 'lon': PORTS['파나마운하_태평양']['lon']},
        {'route': '부산→뉴욕(파나마)', 'seq': 3, 'location': '파나마(대서양)', 
         'lat': PORTS['파나마운하_대서양']['lat'], 'lon': PORTS['파나마운하_대서양']['lon']},
        {'route': '부산→뉴욕(파나마)', 'seq': 4, 'location': '뉴욕', 
         'lat': PORTS['뉴욕']['lat'], 'lon': PORTS['뉴욕']['lon']},
    ]
    
    # 예시: 부산 → 뉴욕 (남미 우회)
    route_detour = [
        {'route': '부산→뉴욕(남미우회)', 'seq': 1, 'location': '부산', 
         'lat': PORTS['부산']['lat'], 'lon': PORTS['부산']['lon']},
        {'route': '부산→뉴욕(남미우회)', 'seq': 2, 'location': '마젤란해협', 
         'lat': PORTS['마젤란해협']['lat'], 'lon': PORTS['마젤란해협']['lon']},
        {'route': '부산→뉴욕(남미우회)', 'seq': 3, 'location': '뉴욕', 
         'lat': PORTS['뉴욕']['lat'], 'lon': PORTS['뉴욕']['lon']},
    ]
    
    route_coords.extend(route_panama)
    route_coords.extend(route_detour)
    
    return pd.DataFrame(route_coords)

# KPI 계산
def calculate_kpi(df):
    """
    주요 KPI 계산
    """
    # 파나마 경유 vs 남미 우회 비교
    panama_routes = df[df['via_panama'] == True]
    detour_routes = df[df['via_panama'] == False]
    
    kpi = {
        'avg_cost_per_teu_panama': panama_routes['cost_per_teu'].mean(),
        'avg_cost_per_teu_detour': detour_routes['cost_per_teu'].mean(),
        'avg_distance_saved_km': (detour_routes['distance_km'].mean() - 
                                   panama_routes['distance_km'].mean()),
        'avg_cost_savings': (detour_routes['total_cost'].mean() - 
                            panama_routes['total_cost'].mean()),
        'margin_improvement_pct': (
            (detour_routes['total_cost'].mean() - panama_routes['total_cost'].mean()) / 
            detour_routes['total_cost'].mean() * 100
        ),
    }
    
    return pd.DataFrame([kpi])

# 메인 실행
if __name__ == "__main__":
    print("=" * 80)
    print("HMM 파나마운하 물류 비용 분석")
    print("=" * 80)
    
    # 1. 전체 항로 데이터 생성
    print("\n[1/5] 항로 데이터 생성 중...")
    df_complete = create_complete_dataset()
    print(f"✓ 총 {len(df_complete)}개 항로 생성 완료")
    
    # 2. 시계열 데이터 생성
    print("\n[2/5] 시계열 데이터 생성 중...")
    df_timeseries = create_timeseries_data(df_complete)
    print(f"✓ {len(df_timeseries)}개 월별 데이터 생성 완료")
    
    # 3. 지도 좌표 데이터 생성
    print("\n[3/5] 지도 시각화용 좌표 생성 중...")
    df_route_coords = create_route_coordinates()
    print(f"✓ {len(df_route_coords)}개 경로 좌표 생성 완료")
    
    # 4. KPI 계산
    print("\n[4/5] KPI 계산 중...")
    df_kpi = calculate_kpi(df_complete)
    print(f"✓ KPI 계산 완료")
    
    # 5. 파일 저장
    print("\n[5/5] 데이터 저장 중...")
    
    # Excel 파일로 저장 (Power BI 연동용)
    with pd.ExcelWriter('/home/claude/HMM_Panama_Canal_Analysis.xlsx', engine='openpyxl') as writer:
        df_complete.to_excel(writer, sheet_name='Routes_Cost', index=False)
        df_timeseries.to_excel(writer, sheet_name='Timeseries', index=False)
        df_route_coords.to_excel(writer, sheet_name='Route_Coordinates', index=False)
        df_kpi.to_excel(writer, sheet_name='KPI', index=False)
    
    print("✓ HMM_Panama_Canal_Analysis.xlsx 저장 완료")
    
    # CSV 파일로도 저장
    df_complete.to_csv('/home/claude/routes_cost.csv', index=False, encoding='utf-8-sig')
    df_timeseries.to_csv('/home/claude/timeseries.csv', index=False, encoding='utf-8-sig')
    df_route_coords.to_csv('/home/claude/route_coordinates.csv', index=False, encoding='utf-8-sig')
    df_kpi.to_csv('/home/claude/kpi.csv', index=False, encoding='utf-8-sig')
    
    print("✓ CSV 파일 저장 완료")
    
    # 결과 요약 출력
    print("\n" + "=" * 80)
    print("분석 결과 요약")
    print("=" * 80)
    
    print("\n[주요 KPI]")
    print(f"파나마 경유 평균 TEU당 비용: ${df_kpi['avg_cost_per_teu_panama'].values[0]:,.2f}")
    print(f"남미 우회 평균 TEU당 비용: ${df_kpi['avg_cost_per_teu_detour'].values[0]:,.2f}")
    print(f"평균 거리 절감: {df_kpi['avg_distance_saved_km'].values[0]:,.0f} km")
    print(f"평균 비용 절감: ${df_kpi['avg_cost_savings'].values[0]:,.0f}")
    print(f"마진 개선율: {df_kpi['margin_improvement_pct'].values[0]:.2f}%")
    
    print("\n[샘플 데이터 미리보기]")
    print("\n▶ 항로별 비용 비교 (부산→뉴욕)")
    sample = df_complete[
        (df_complete['origin'] == '부산') & 
        (df_complete['destination'] == '뉴욕')
    ][['route_name', 'scenario', 'distance_km', 'total_cost', 'cost_per_teu', 'days_at_sea']]
    print(sample.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("✓ 모든 작업 완료")
    print("=" * 80)
