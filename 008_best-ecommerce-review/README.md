# 008_best-ecomerce-review

리뷰 데이터 기반 일일 메시지 자동화 프로젝트

## 🎯 목적
- 아침 7시: 유머러스한 리뷰 (긴장 완화)
- 저녁 5시: 긍정적인 리뷰 (하루 마무리)

## 🏗️ 아키텍처
[CSV/API] → [ETL] → [DB] → [n8n] → [Tableau/Redash]

## 📂 구조
- data/: Bronze → Silver → Gold
- governance/: 거버넌스 문서
- src/: 소스 코드
- sql/: DDL/DML/쿼리
- n8n_workflows/: 워크플로우

## 🚀 시작하기
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
sqlite3 review.db < sql/ddl/01_create_tables.sql
```
