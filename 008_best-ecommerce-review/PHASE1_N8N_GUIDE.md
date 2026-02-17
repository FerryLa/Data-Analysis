# Phase 1 + n8n 통합 실행 가이드

## 🎯 목표

1. **Phase 1**: Google Play Store에서 한국 이커머스 리뷰 6,000개 수집
2. **n8n 설정**: 자동화 파이프라인 구축
3. **통합**: 데이터 → n8n → 메시지 생성 → Dashboard

---

## 📋 전체 실행 순서

```
1. 프로젝트 설정 (10분)
   ↓
2. Phase 1: 데이터 수집 (20분)
   ↓
3. DB 초기화 및 적재 (10분)
   ↓
4. n8n 설치 및 설정 (30분)
   ↓
5. 워크플로우 Import (10분)
   ↓
6. 테스트 실행 (10분)
   ↓
7. 모니터링 설정 (10분)
```

**총 소요 시간: 약 100분 (1시간 40분)**

---

## 1️⃣ 프로젝트 설정 (10분)

### Windows PowerShell

```powershell
# 1. 프로젝트 디렉토리로 이동
cd C:\dev\Data_Analysis\008_best-ecomerce-review

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화
venv\Scripts\activate

# 4. 패키지 설치
pip install -r requirements.txt

# 5. 폴더 구조 확인
tree /F /A
```

### 필수 폴더 생성

```powershell
# n8n 워크플로우 폴더
mkdir n8n_workflows\morning
mkdir n8n_workflows\evening
mkdir n8n_workflows\loader

# 데이터 폴더
mkdir data\bronze\playstore
mkdir data\silver\cleaned
mkdir data\gold\morning
mkdir data\gold\evening
```

---

## 2️⃣ Phase 1: 데이터 수집 (20분)

### 순차 실행

```powershell
# 1. 쿠팡 리뷰 2,000개 (약 5분)
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 2000

# 2. 11번가 리뷰 2,000개 (약 5분)
python src\etl\extractors\download_playstore_reviews.py --app 11번가 --count 2000

# 3. 네이버쇼핑 리뷰 1,000개 (약 3분)
python src\etl\extractors\download_playstore_reviews.py --app 네이버쇼핑 --count 1000

# 4. 마켓컬리 리뷰 1,000개 (약 3분)
python src\etl\extractors\download_playstore_reviews.py --app 마켓컬리 --count 1000
```

### 수집 결과 확인

```powershell
# CSV 파일 목록
dir data\bronze\playstore\*.csv

# 예상 출력:
# reviews_쿠팡_20250208.csv (약 500KB)
# reviews_11번가_20250208.csv (약 500KB)
# reviews_네이버쇼핑_20250208.csv (약 250KB)
# reviews_마켓컬리_20250208.csv (약 250KB)
```

### 샘플 데이터 확인

```powershell
# 첫 번째 파일 미리보기
python -c "import pandas as pd; df = pd.read_csv('data/bronze/playstore/reviews_쿠팡_20250208.csv', encoding='utf-8-sig'); print(df.head(3))"
```

---

## 3️⃣ DB 초기화 및 적재 (10분)

### SQLite 사용 (간단)

```powershell
# 1. DB 생성 및 스키마 적용
sqlite3 review.db < sql\ddl\01_create_tables.sql

# 2. 테이블 확인
sqlite3 review.db "SELECT name FROM sqlite_master WHERE type='table';"

# 예상 출력:
# raw_reviews
# cleaned_reviews
# filtered_reviews
# scored_reviews
# morning_messages
# evening_messages
# audit_log
```

### CSV → DB 적재

```powershell
# Python 스크립트로 4개 CSV 모두 적재
python src\etl\extractors\csv_loader.py

# 또는 개별 적재
python src\etl\extractors\csv_loader.py --input data\bronze\playstore\reviews_쿠팡_20250208.csv
python src\etl\extractors\csv_loader.py --input data\bronze\playstore\reviews_11번가_20250208.csv
python src\etl\extractors\csv_loader.py --input data\bronze\playstore\reviews_네이버쇼핑_20250208.csv
python src\etl\extractors\csv_loader.py --input data\bronze\playstore\reviews_마켓컬리_20250208.csv
```

### 적재 결과 확인

```powershell
# 총 행 수 확인
sqlite3 review.db "SELECT COUNT(*) as total FROM raw_reviews;"

# 앱별 통계
sqlite3 review.db "SELECT product_category, COUNT(*) as count, AVG(rating) as avg_rating FROM raw_reviews GROUP BY product_category;"

# 예상 출력:
# 쿠팡         | 2000 | 4.3
# 11번가       | 2000 | 4.2
# 네이버쇼핑   | 1000 | 4.4
# 마켓컬리     | 1000 | 4.5
```

---

## 4️⃣ n8n 설치 및 설정 (30분)

### Docker로 n8n 설치 (권장)

```powershell
# 1. Docker Desktop 설치 확인
docker --version

# 2. n8n 컨테이너 실행
docker run -d `
  --name n8n `
  -p 5678:5678 `
  -e N8N_BASIC_AUTH_ACTIVE=true `
  -e N8N_BASIC_AUTH_USER=admin `
  -e N8N_BASIC_AUTH_PASSWORD=your_auth_password `
  -e GENERIC_TIMEZONE=Asia/Seoul `
  -v C:\dev\Data_Analysis\008_best-ecommerce-review\n8n_data:/home/node/.n8n `
  n8nio/n8n

# 3. 브라우저에서 접속
# http://localhost:5678
# 로그인: admin / your_secure_password
```

### npm으로 설치 (대안)

```powershell
# 1. Node.js 설치 확인
node --version

# 2. n8n 전역 설치
npm install -g n8n

# 3. n8n 실행
n8n start

# 4. 브라우저에서 접속
# http://localhost:5678
```

### n8n 초기 설정

1. **계정 생성**
   - Email: your@email.com
   - Password: 강력한 비밀번호

2. **Credentials 설정**
   
   **PostgreSQL/SQLite**
   ```
   Settings → Credentials → Add Credential
   Type: PostgreSQL (또는 SQLite)
   
   SQLite:
   - Database Path: C:\dev\Data_Analysis\008_best-ecomerce-review\review.db
   
   PostgreSQL:
   - Host: localhost
   - Database: review_db
   - User: n8n_worker
   - Password: your_db_password
   ```

   **Anthropic API**
   ```
   Settings → Credentials → Add Credential
   Type: HTTP Header Auth
   
   Name: x-api-key
   Value: sk-ant-api03-YOUR_API_KEY
   ```

   **Slack Webhook (선택)**
   ```
   Settings → Credentials → Add Credential
   Type: Slack Incoming Webhook
   
   Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

---

## 5️⃣ 워크플로우 Import (10분)

### 워크플로우 Import

1. **n8n 대시보드 접속**
   - http://localhost:5678

2. **워크플로우 Import**
   ```
   Workflows → Add workflow → Import from File
   
   파일 선택:
   1. n8n_workflows/morning/001_morning_message.json
   2. n8n_workflows/evening/002_evening_message.json
   3. n8n_workflows/loader/003_csv_loader.json
   ```

3. **Credentials 연결**
   - 각 워크플로우 열기
   - 빨간색 노드 클릭 (Credentials 필요)
   - 앞서 생성한 Credentials 선택

4. **저장**
   - 각 워크플로우 저장 (Ctrl+S)
   - Active 토글 ON

---

## 6️⃣ 테스트 실행 (10분)

### 수동 테스트

#### 아침 메시지 워크플로우

```
1. n8n → Workflows → 001_Morning_Message_Generator 열기
2. [Execute Workflow] 버튼 클릭
3. 각 노드별 결과 확인:
   - Query_Yesterday_Reviews: 어제 리뷰 조회
   - Filter_Humor_Keywords: 유머 키워드 필터링
   - Claude_Score_Humor: LLM 점수화
   - Random_Select_Top5: 랜덤 선택
   - Claude_Format_Message: 메시지 포맷팅
   - Insert_Morning_Message: DB 저장
4. 성공 여부 확인
```

#### DB 결과 확인

```powershell
# 아침 메시지 확인
sqlite3 review.db "SELECT * FROM morning_messages WHERE message_date = date('now');"

# 출력 예시:
# id | scored_review_id | message_date | original_review | formatted_message | commentary | created_at
# 1  | PLAY_쿠팡_001234 | 2025-02-08   | 배송이...       | 오늘의 리뷰...    | 빠름은...  | 2025-02-08 07:02:15
```

#### 저녁 메시지 워크플로우

```
1. n8n → Workflows → 002_Evening_Message_Generator 열기
2. [Execute Workflow] 버튼 클릭
3. 결과 확인
```

### 시간 트리거 테스트

```
1. 워크플로우 열기
2. Cron Trigger 노드 클릭
3. 설정 변경:
   - Hour: 현재 시각 + 5분
   - Minute: 0
4. 저장 및 Active ON
5. 5분 후 자동 실행 확인
```

---

## 7️⃣ 모니터링 설정 (10분)

### n8n 실행 로그

```
Settings → Executions
- 최근 실행 내역 확인
- 성공/실패 상태
- 실행 시간
- 에러 메시지
```

### DB 모니터링 쿼리

```sql
-- 오늘 생성된 메시지
SELECT 
    'morning' as type,
    message_date,
    formatted_message,
    created_at
FROM morning_messages
WHERE message_date = date('now')
UNION ALL
SELECT 
    'evening' as type,
    message_date,
    formatted_message,
    created_at
FROM evening_messages
WHERE message_date = date('now');

-- 최근 7일 통계
SELECT 
    message_date,
    COUNT(*) as message_count
FROM morning_messages
WHERE message_date >= date('now', '-7 days')
GROUP BY message_date
ORDER BY message_date DESC;
```

### Slack 알림 설정

```
각 워크플로우에 Slack 노드 추가됨:
- 성공 알림: ✅ 메시지 생성 완료
- 실패 알림: ❌ 워크플로우 실패

Slack 채널: #review-automation
```

---

## ✅ 완료 체크리스트

### Phase 1 완료

- [ ] 쿠팡 리뷰 2,000개 수집
- [ ] 11번가 리뷰 2,000개 수집
- [ ] 네이버쇼핑 리뷰 1,000개 수집
- [ ] 마켓컬리 리뷰 1,000개 수집
- [ ] CSV 파일 4개 확인
- [ ] DB 생성 및 스키마 적용
- [ ] CSV → DB 적재 완료
- [ ] 총 6,000개 리뷰 확인

### n8n 설정 완료

- [ ] n8n 설치 및 실행
- [ ] Credentials 설정 (DB, Claude API)
- [ ] 워크플로우 3개 Import
- [ ] 아침 메시지 테스트 실행
- [ ] 저녁 메시지 테스트 실행
- [ ] Cron 스케줄 설정 (7:00, 17:00)
- [ ] Slack 알림 테스트

### 통합 확인

- [ ] 아침 메시지 DB 저장 확인
- [ ] 저녁 메시지 DB 저장 확인
- [ ] Tableau/Redash 연결 (다음 단계)
- [ ] 1주일 모니터링 계획

---

## 🔧 문제 해결

### Q1: n8n에서 DB 연결 실패

**문제**: `Database connection failed`

**해결**:
```powershell
# SQLite 경로 확인
sqlite3 review.db ".databases"

# n8n Credentials에서 절대 경로 사용
# 예: C:\dev\Data_Analysis\008_best-ecomerce-review\review.db
```

### Q2: Claude API 호출 실패

**문제**: `401 Unauthorized`

**해결**:
```
1. API Key 확인: https://console.anthropic.com
2. n8n Credentials 재설정
3. HTTP Header Auth:
   - Name: x-api-key
   - Value: sk-ant-api03-YOUR_KEY
```

### Q3: 메시지 생성 안 됨

**문제**: `No humor reviews found`

**해결**:
```sql
-- 어제 리뷰 존재 확인
SELECT COUNT(*) FROM raw_reviews WHERE created_date = date('now', '-1 day');

-- 없으면 테스트 데이터 생성
UPDATE raw_reviews 
SET created_date = date('now', '-1 day') 
WHERE id <= 100;
```

### Q4: Cron이 실행 안 됨

**문제**: 스케줄 시간에 실행 안 됨

**해결**:
```
1. 워크플로우 Active 상태 확인
2. n8n 시간대 확인: Asia/Seoul
3. 서버 시간 확인
4. 테스트: 현재 시각 + 5분으로 설정
```

---

## 📊 다음 단계

### Phase 2: Tableau/Redash 연동

1. **Tableau Desktop 설치**
   - SQLite 데이터 소스 연결
   - morning_messages 테이블 추가
   - 시각화 디자인

2. **Redash 설정**
   - Docker로 Redash 설치
   - PostgreSQL로 마이그레이션 (선택)
   - Query 작성 및 대시보드 구성

3. **모바일 최적화**
   - Redash 모바일 뷰 테스트
   - 알림 설정

---

## 🎯 현재 상태

```
✅ Phase 1 완료 (데이터 수집)
✅ DB 구축 완료
✅ n8n 파이프라인 구축 완료
⏳ Tableau/Redash 연동 대기
⏳ 프로덕션 모니터링 대기
```

**축하합니다! 자동화 파이프라인의 핵심이 완성되었습니다! 🎉**

---

## 📞 지원

문제 발생 시:
1. n8n 로그 확인: Executions → 실패한 실행 클릭
2. DB 쿼리 확인: SQLite 브라우저로 직접 확인
3. Python 로그 확인: `logs/` 디렉토리
