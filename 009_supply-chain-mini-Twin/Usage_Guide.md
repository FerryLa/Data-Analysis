# Usage Guide - 009 Supply Chain Mini-Twin

## 빠른 시작

### Step 1: 데이터 생성
```bash
cd 009_supply-chain-mini-Twin
python notebooks/generate_supply_chain_data.py
```

### Step 2: 인프라 기동 (Docker)
```bash
cd docker
docker-compose up -d
```
- PostgreSQL: `localhost:5433`
- n8n: `http://localhost:5679` (admin / scm2025!)
- Redash: `http://localhost:5001`

### Step 3: DB 적재
```bash
python scripts/load_csvs_to_db.py
```

### Step 4: Power BI 연결
1. Power BI Desktop → 데이터 가져오기 → PostgreSQL
2. 서버: `localhost:5433`, DB: `supply_chain_db`
3. 또는 `data/bronze/*.csv` 직접 Import

### Step 5: n8n 알림 설정
1. `http://localhost:5679` 접속
2. Import: `n8n/workflows/scm_alerts_workflow.json`
3. PostgreSQL 자격증명 설정 (Host: `postgres`, Port: 5432)
4. Webhook URL 설정 (Slack/Teams)

### Step 6: Redash 대시보드
1. `http://localhost:5001` 접속
2. Data Source 추가: PostgreSQL (Host: `postgres`, Port: 5432)
3. `redash/queries.sql`의 쿼리를 등록

---

## 파일 구조
```
009_supply-chain-mini-Twin/
├── data/
│   ├── bronze/          ← 원시 시뮬레이션 데이터 (8개 CSV)
│   ├── silver/          ← 가공 데이터 (KPI 서머리)
│   └── gold/            ← 최종 큐레이션 (향후)
├── docs/
│   └── private/         ← Power BI / ArcGIS 구현 가이드
├── docker/
│   └── docker-compose.yml
├── n8n/
│   └── workflows/       ← n8n 알림 워크플로우 JSON
├── notebooks/
│   └── generate_supply_chain_data.py  ← 데이터 생성 스크립트
├── powerbi/
│   └── dashboards/      ← .pbix 파일 (수동 생성)
├── redash/
│   └── queries.sql      ← Redash 대시보드 쿼리
├── scripts/
│   ├── load_csvs_to_db.py  ← CSV → PostgreSQL 로더
│   └── init_db.sql         ← DB 초기화 (뷰 생성)
├── Release.md
└── Usage_Guide.md
```

## 데이터셋 요약
| 파일 | 건수 | 내용 |
|------|------|------|
| inbound_shipments.csv | ~234 | 선박 입항/하역/통관 |
| inventory_daily.csv | ~720 | 8품목 × 90일 재고 |
| production_plan.csv | ~360 | 4제품 × 90일 생산 |
| outbound_orders.csv | ~492 | 출하 주문/OTIF |
| port_markers.csv | 9 | 항만 좌표 |
| sea_routes.csv | ~224 | 해상 루트 웨이포인트 |
| logistics_zones.csv | 6 | 새만금 물류 구역 |
| alert_events.csv | ~314 | 5대 알림 이벤트 |
