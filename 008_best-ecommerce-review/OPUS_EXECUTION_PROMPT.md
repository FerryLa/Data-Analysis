# Claude Opus 4.5용 실행 프롬프트 - Phase 1 + n8n 통합

## 🎯 목표

Google Play Store에서 한국 이커머스 리뷰 6,000개를 수집하고, n8n 자동화 파이프라인을 구축하여 매일 아침/저녁 메시지를 자동 생성하는 시스템을 완성합니다.

---

## 📋 작업 범위

### Part A: Phase 1 - 데이터 수집 (Python)

#### 1. 프로젝트 설정
- 경로: `C:\dev\Data_Analysis\008_best-ecomerce-review`
- 가상환경 생성 및 활성화
- requirements.txt 패키지 설치
- 폴더 구조 확인

#### 2. 리뷰 데이터 수집
다음 4개 앱에서 **순차적으로** 리뷰 수집:

1. **쿠팡** (com.coupang.mobile) - 2,000개
2. **11번가** (com.skplanet.eleven) - 2,000개
3. **네이버쇼핑** (com.nhn.android.search) - 1,000개
4. **마켓컬리** (com.dmp.market.kurly) - 1,000개

각 수집 후 **즉시 확인**:
- 파일 저장 위치: `data/bronze/playstore/`
- 파일 크기 (KB)
- 샘플 데이터 3개 출력

**총 목표: 6,000개 한국어 이커머스 리뷰**

#### 3. 데이터 검증
각 CSV 파일에 대해:
- 총 행 수
- 컬럼 구조 (작성일, 리뷰내용, 평점, 앱명)
- 평균 리뷰 길이
- 평균 평점
- 유머 키워드 포함 리뷰 개수 (ㅋㅋ, 웃겨 등)
- 긍정 키워드 포함 리뷰 개수 (감사, 추천 등)

#### 4. 데이터베이스 구축
- SQLite DB 생성: `review.db`
- 스키마 적용: `sql/ddl/01_create_tables.sql`
- 테이블 7개 생성 확인:
  - raw_reviews
  - cleaned_reviews
  - filtered_reviews
  - scored_reviews
  - morning_messages
  - evening_messages
  - audit_log

#### 5. CSV → DB 적재
- 4개 CSV 파일 모두 `raw_reviews` 테이블에 INSERT
- 적재 건수 확인 (6,000개 목표)
- 중복 제거 (review_id UNIQUE 제약)
- 앱별 통계 출력

---

### Part B: n8n 파이프라인 구축

#### 6. n8n 설치 및 설정

**Docker 방식 (권장)**
```powershell
docker run -d `
  --name n8n `
  -p 5678:5678 `
  -e N8N_BASIC_AUTH_ACTIVE=true `
  -e N8N_BASIC_AUTH_USER=admin `
  -e N8N_BASIC_AUTH_PASSWORD=review_automation_2025 `
  -e GENERIC_TIMEZONE=Asia/Seoul `
  -v C:\dev\Data_Analysis\008_best-ecomerce-review\n8n_data:/home/node/.n8n `
  n8nio/n8n
```

**설정**:
- 브라우저 접속: http://localhost:5678
- 로그인 확인
- Credentials 3개 설정:
  1. SQLite Database
  2. Anthropic API (Claude)
  3. Slack Webhook (선택)

#### 7. 워크플로우 Import

**3개 워크플로우 Import**:
1. `n8n_workflows/morning/001_morning_message.json`
   - Cron: 매일 07:00
   - 어제 유머 리뷰 1개 선택
   
2. `n8n_workflows/evening/002_evening_message.json`
   - Cron: 매일 17:00
   - 오늘 긍정 리뷰 1개 선택
   
3. `n8n_workflows/loader/003_csv_loader.json`
   - Manual/Webhook 트리거
   - CSV → DB 적재

**각 워크플로우**:
- Credentials 연결
- 노드별 설정 확인
- Active 토글 ON

#### 8. 테스트 실행

**아침 메시지 워크플로우**:
1. 수동 실행 (Execute Workflow 버튼)
2. 각 노드별 결과 확인:
   - DB Query: 어제 리뷰 조회
   - Filter: 유머 키워드 필터링
   - Claude API: 점수화 (0-100)
   - Random Select: 상위 5개 중 랜덤 1개
   - Claude API: 메시지 포맷팅
   - DB Insert: morning_messages 테이블
3. 성공/실패 확인

**저녁 메시지 워크플로우**:
- 동일한 방식으로 테스트
- 오늘 긍정 리뷰 대상

**DB 결과 확인**:
```sql
SELECT * FROM morning_messages WHERE message_date = date('now');
SELECT * FROM evening_messages WHERE message_date = date('now');
```

---

## 🔧 실행 원칙

### 거버넌스 & 컴플라이언스
- **모든 단계에서 로그 기록** (Python, n8n)
- **개인정보 마스킹 확인** (작성자명)
- **에러 발생 시 즉시 중단** 및 원인 분석
- **데이터 품질 기준 준수**:
  - 리뷰 길이: 10자 이상
  - 평점: 1.0~5.0 범위
  - NULL 값 제외

### 오류 처리
- 각 단계 실패 시 **다음 단계 진행 안 함**
- 실패 원인 **상세 분석** (스택 트레이스 포함)
- **복구 방법 제시** (재시도, 수동 개입 등)

### 출력 형식
- 각 단계마다 **명확한 구분선** (`====`)
- **진행률 표시** (1/8, 2/8, ...)
- **성공/실패 아이콘** (✅/❌)
- 중요 정보 **강조 표시** (***볼드***)

---

## 📊 산출물

### 1. Phase 1 산출물
- CSV 파일 4개 (`data/bronze/playstore/`)
- SQLite DB (`review.db`)
- 검증 리포트 (`PHASE1_VALIDATION_REPORT.md`)

### 2. n8n 산출물
- 워크플로우 3개 (Import 완료, Active)
- 테스트 실행 로그 (성공/실패)
- DB에 메시지 2개 (morning + evening)

### 3. 통합 리포트
다음 내용으로 `PHASE1_N8N_REPORT.md` 생성:
- 수집된 총 리뷰 개수
- 앱별 통계 (개수, 평균 평점, 평균 길이)
- 유머 리뷰 후보 개수
- 긍정 리뷰 후보 개수
- n8n 워크플로우 테스트 결과
- 생성된 메시지 샘플 (아침 + 저녁)
- 발견된 이슈 및 해결 방법
- 다음 단계 권장사항 (Tableau/Redash 연동)

---

## 🎯 제약사항

- **네트워크 오류 시 최대 3회 재시도**
- **각 앱당 수집 시간 제한: 10분**
- **메모리 사용량 모니터링** (pandas DataFrame 크기)
- **Windows 환경 기준** 명령어 사용
- **Claude API 호출 제한**: 배치당 최대 10개

---

## ✅ 최종 체크리스트

### Phase 1 완료
- [ ] 쿠팡 리뷰 2,000개
- [ ] 11번가 리뷰 2,000개
- [ ] 네이버쇼핑 리뷰 1,000개
- [ ] 마켓컬리 리뷰 1,000개
- [ ] CSV 파일 4개 확인
- [ ] DB 생성 및 스키마
- [ ] CSV → DB 적재 (6,000개)
- [ ] 검증 리포트 작성

### n8n 완료
- [ ] n8n 설치 및 실행
- [ ] Credentials 3개 설정
- [ ] 워크플로우 3개 Import
- [ ] 아침 메시지 테스트 성공
- [ ] 저녁 메시지 테스트 성공
- [ ] DB에 메시지 2개 저장
- [ ] Cron 스케줄 설정 (7:00, 17:00)

### 통합 확인
- [ ] Python → DB → n8n 연동 확인
- [ ] 메시지 자동 생성 테스트
- [ ] 에러 핸들링 확인
- [ ] 통합 리포트 작성

---

## 🚀 실행 시작

위 지침에 따라 **Phase 1 + n8n 통합**을 **순차적으로** 실행하고, 각 단계의 결과를 **명확하게 보고**해주세요.

**실행 가이드 참조**:
- `PHASE1_N8N_GUIDE.md` - 상세 실행 가이드
- `n8n_workflows/WORKFLOW_DESIGN.md` - 워크플로우 설계 문서

문제가 발생하면 **즉시 중단**하고 원인을 분석한 후 해결 방법을 제시해주세요.

---

## 💡 중요 참고사항

### n8n 워크플로우 구조
```
아침 메시지:
Cron(7AM) → DB Query(어제) → Filter(유머) → Claude(점수) 
→ Random(Top5) → Claude(포맷) → DB Insert → Slack

저녁 메시지:
Cron(5PM) → DB Query(오늘) → Filter(긍정) → Claude(점수) 
→ Random(Top20%) → Claude(포맷) → DB Insert → Slack
```

### 예상 실행 시간
```
Phase 1 데이터 수집:     20분
DB 구축 및 적재:         10분
n8n 설치:                15분
워크플로우 설정:         15분
테스트 실행:             10분
리포트 작성:             10분
-----------------------------------
총 소요 시간:            약 80분
```

### 성공 기준
```
✅ 6,000개 리뷰 수집 완료
✅ DB에 6,000개 행 확인
✅ n8n 워크플로우 3개 Active
✅ 테스트 메시지 2개 생성 (morning + evening)
✅ 에러 없이 전체 파이프라인 동작
```

---

**준비되셨나요? 시작합니다! 🚀**
