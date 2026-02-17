# 009 Supply Chain Mini-Twin

## 프로젝트 개요
서해안 항만(군산항/새만금항) ↔ 새만금 산업단지 물류센터 기반
중국/동아시아 교역 Supply Chain Control Tower + Digital Twin 시뮬레이션

## Phase 로드맵

| Phase | 내용 | 기술 스택 | 상태 |
|-------|------|-----------|------|
| **Phase 1** | 물류 대시보드 MVP (3화면 + 5알림) | Python + PostgreSQL + Power BI + Redash + n8n | 🔨 진행중 |
| **Phase 2** | 중국-항만-새만금 인터랙티브 지도 | Power BI + ArcGIS Maps | ⏳ 대기 |
| **Phase 3** | 대시보드 + 지도 통합 (Control Tower) | Power BI 통합 | ⏳ 대기 |
| **Phase 4** | Mini Twin 디지털트윈 시뮬레이션 | Python + 시뮬레이터 | ⏳ 대기 |

## 핵심 물류 축
```
중국(상하이/칭다오/닝보/톈진)
    ↓ 서해 해상 루트
서해안 항만(군산항/새만금항)
    ↓ 내륙 운송
새만금 산업단지 물류센터
    ↓ 생산/출하
고객(내수/수출)
```

## 버전 이력
| 버전 | 날짜 | 내용 |
|------|------|------|
| 0.1.0 | 2025-02-17 | 프로젝트 초기 구조 생성, MVP 설계 |

## 기술 스택
- **데이터 처리**: Python 3 + Pandas + NumPy
- **데이터베이스**: PostgreSQL (Docker)
- **BI 도구**: Power BI Desktop + Redash
- **자동화**: n8n (Docker)
- **지도**: ArcGIS Maps for Power BI
- **인프라**: Docker Compose
