# Power BI 대시보드 구현 가이드
## 009 Supply Chain Mini-Twin

---

## 데이터 소스 연결

### PostgreSQL 직접 연결
```
서버: localhost:5433
데이터베이스: supply_chain_db
사용자: n8n_user
비밀번호: n8n_pass
```

### CSV 직접 로드 (대안)
`data/bronze/` 및 `data/silver/` 폴더의 CSV 파일 Import

---

## Dashboard 1: Inbound(원자재) 관제

### 페이지 레이아웃
```
┌─────────────────────────────────────────────────────┐
│  [KPI] 총선적  [KPI] 항해중  [KPI] 평균지연  [KPI] 지연률 │
├──────────────────────┬──────────────────────────────┤
│                      │  출발항별 선적 건수            │
│  선박 입항 테이블     │  (Clustered Bar Chart)        │
│  (상태별 색상)        │                              │
│                      ├──────────────────────────────┤
│                      │  일별 입항 트렌드              │
│                      │  (Line Chart - 지연 포함)      │
├──────────────────────┴──────────────────────────────┤
│  원자재별 입항 현황 (Stacked Bar / Treemap)           │
└─────────────────────────────────────────────────────┘
```

### KPI 카드 DAX
```dax
총선적건수 = DISTINCTCOUNT(inbound_shipments[shipment_id])

항해중건수 = CALCULATE(
    DISTINCTCOUNT(inbound_shipments[shipment_id]),
    inbound_shipments[status] = "항해중"
)

평균지연시간 = AVERAGE(inbound_shipments[delay_hours])

지연률 = DIVIDE(
    CALCULATE(COUNT(inbound_shipments[shipment_id]), inbound_shipments[delay_hours] > 0),
    COUNT(inbound_shipments[shipment_id])
) * 100
```

### 조건부 서식
- delay_hours >= 24 → 빨간색 배경
- delay_hours >= 6 → 주황색 배경
- delay_hours > 0 → 노란색 배경
- delay_hours = 0 → 초록색 배경

### 슬라이서
- 출발항 (origin_name)
- 원자재 카테고리 (material_category)
- 상태 (status)
- 날짜 범위 (snapshot_date)

---

## Dashboard 2: Inventory & Production Risk

### 페이지 레이아웃
```
┌─────────────────────────────────────────────────────┐
│ [KPI] 평균DOS [KPI] CRITICAL품목 [KPI] 재고가치  [KPI] 커버리지│
├──────────────────────┬──────────────────────────────┤
│                      │  품목별 재고일수 게이지          │
│  재고 현황 테이블     │  (Gauge Chart per item)       │
│  (리스크 색상)        │                              │
│                      ├──────────────────────────────┤
│                      │  리스크 추이 (Stacked Area)     │
│                      │  CRITICAL/HIGH/MEDIUM/LOW     │
├──────────────────────┴──────────────────────────────┤
│  생산 계획 vs 실적 (Clustered Column + Line)          │
└─────────────────────────────────────────────────────┘
```

### 핵심 DAX
```dax
평균재고일수 = AVERAGE(inventory_daily[dos])

CRITICAL품목수 = CALCULATE(
    DISTINCTCOUNT(inventory_daily[material_code]),
    inventory_daily[risk_level] = "CRITICAL"
)

총재고가치 = SUM(inventory_daily[stock_value_krw]) / 1000000  -- 백만원

생산달성률 = DIVIDE(
    SUM(production_plan[actual_qty]),
    SUM(production_plan[planned_qty])
) * 100

라인스톱건수 = CALCULATE(
    COUNT(production_plan[line_stop]),
    production_plan[line_stop] = TRUE()
)
```

### 조건부 서식
- risk_level = "CRITICAL" → 빨간색
- risk_level = "HIGH" → 주황색
- risk_level = "MEDIUM" → 노란색
- risk_level = "LOW" → 초록색

---

## Dashboard 3: Outbound(출하) & OTIF

### 페이지 레이아웃
```
┌─────────────────────────────────────────────────────┐
│ [KPI] OTIF률  [KPI] 정시율  [KPI] 정량율  [KPI] 평균지연 │
├──────────────────────┬──────────────────────────────┤
│  고객별 OTIF          │  일별 OTIF 추이               │
│  (Bar Chart)          │  (Line Chart)               │
│                      │                              │
├──────────────────────┼──────────────────────────────┤
│  제품별 충족률         │  출하 지연 상세 테이블          │
│  (Donut/Pie)         │  (조건부 서식)                │
└──────────────────────┴──────────────────────────────┘
```

### 핵심 DAX
```dax
OTIF률 = DIVIDE(
    CALCULATE(COUNT(outbound_orders[otif]), outbound_orders[otif] = TRUE()),
    COUNT(outbound_orders[otif])
) * 100

정시율 = DIVIDE(
    CALCULATE(COUNT(outbound_orders[on_time]), outbound_orders[on_time] = TRUE()),
    COUNT(outbound_orders[on_time])
) * 100

정량율 = DIVIDE(
    CALCULATE(COUNT(outbound_orders[in_full]), outbound_orders[in_full] = TRUE()),
    COUNT(outbound_orders[in_full])
) * 100

주문완료건수 = CALCULATE(
    COUNT(outbound_orders[order_id]),
    outbound_orders[otif] = TRUE()
)
```

### OTIF 게이지 설정
- 목표: 95%
- 빨강: < 85%
- 노랑: 85% ~ 95%
- 초록: >= 95%

---

## 알림 페이지 (공통)

### 레이아웃
```
┌─────────────────────────────────────────────────────┐
│ [KPI] 총알림 [KPI] CRITICAL [KPI] 미해결  [KPI] 해결률 │
├──────────────────────┬──────────────────────────────┤
│  알림 유형별 집계      │  알림 타임라인               │
│  (Bar Chart)          │  (시간축 Line)              │
├──────────────────────┴──────────────────────────────┤
│  활성 알림 상세 테이블                                │
│  (severity 색상 + 필터)                              │
└─────────────────────────────────────────────────────┘
```

---

## 색상 테마
```json
{
    "dataColors": [
        "#0078D4", "#D13438", "#107C10", "#FFB900",
        "#5C2D91", "#008575", "#E3008C", "#00188F"
    ],
    "background": "#F3F2F1",
    "foreground": "#323130",
    "tableAccent": "#0078D4"
}
```

---

## 데이터 모델 관계도
```
inbound_shipments
    ├── material_code → inventory_daily.material_code
    └── dest_port → port_markers.port_code

inventory_daily
    └── material_code → production_plan (간접 연결)

outbound_orders
    └── product_code → production_plan.product_code

alert_events
    ├── reference_id → inbound_shipments.shipment_id (A1, A4)
    ├── reference_id → inventory_daily.material_code (A2, A3)
    └── reference_id → outbound_orders.order_id (A5)

port_markers → sea_routes (지도용)
logistics_zones (독립)
```
