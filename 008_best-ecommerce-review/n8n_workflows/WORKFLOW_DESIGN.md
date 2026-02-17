# n8n 워크플로우 설계 - 리뷰 자동화 시스템

## 🎯 목표

- 아침 7시: 전날 유머 리뷰 1개 자동 선택 및 배포
- 저녁 5시: 당일 긍정 리뷰 1개 자동 선택 및 배포
- Tableau (모니터용) + Redash (모바일용) 동시 업데이트

---

## 📊 전체 아키텍처

```
[Google Play Store] 
        ↓ (Python Script - 수동/일배치)
[CSV Files] → [DB (SQLite/PostgreSQL)]
                      ↓
              [n8n Orchestration]
                   ↙     ↘
        [아침 워크플로우]  [저녁 워크플로우]
              ↓              ↓
        [필터링 로직]   [필터링 로직]
              ↓              ↓
        [LLM 점수화]    [LLM 점수화]
              ↓              ↓
        [메시지 생성]   [메시지 생성]
              ↓              ↓
        [DB 저장: morning_messages / evening_messages]
              ↓              ↓
         [Tableau]      [Redash]
```

---

## 🔄 워크플로우 구조

### 워크플로우 1: 아침 메시지 (7:00 AM)

```
┌─────────────────┐
│ Cron Trigger    │ → 매일 07:00
└────────┬────────┘
         ↓
┌─────────────────┐
│ DB Query        │ → 어제 날짜 리뷰 조회
│ (raw_reviews)   │    + 기본 필터링
└────────┬────────┘
         ↓
┌─────────────────┐
│ Function Node   │ → 유머 키워드 필터링
│ (Humor Filter)  │    - ㅋㅋ, 웃겨, 빵터짐
│                 │    - 욕설 제외
│                 │    - 길이 20-200자
└────────┬────────┘
         ↓
┌─────────────────┐
│ Claude API      │ → LLM 유머 점수 (0-100)
│ (Scoring)       │    배치로 상위 10개 점수화
└────────┬────────┘
         ↓
┌─────────────────┐
│ Function Node   │ → 상위 5개 중 랜덤 1개 선택
│ (Random Pick)   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Claude API      │ → 메시지 포맷팅
│ (Message Gen)   │    "오늘의 리뷰: ... + 해설"
└────────┬────────┘
         ↓
┌─────────────────┐
│ DB Insert       │ → morning_messages 테이블
│ (morning_msgs)  │    message_date = TODAY
└────────┬────────┘
         ↓
┌─────────────────┐
│ HTTP Request    │ → Tableau Refresh API (선택)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Slack/Email     │ → 성공/실패 알림
│ (Notification)  │
└─────────────────┘
```

### 워크플로우 2: 저녁 메시지 (5:00 PM)

```
┌─────────────────┐
│ Cron Trigger    │ → 매일 17:00
└────────┬────────┘
         ↓
┌─────────────────┐
│ DB Query        │ → 오늘 날짜 리뷰 조회
│ (raw_reviews)   │    + 평점 ≥ 4.5
└────────┬────────┘
         ↓
┌─────────────────┐
│ Function Node   │ → 긍정 키워드 필터링
│ (Positive)      │    - 감사, 따뜻, 추천
│                 │    - CS 이슈 제외
└────────┬────────┘
         ↓
┌─────────────────┐
│ Claude API      │ → LLM 긍정 점수 (0-100)
│ (Scoring)       │    배치로 전체 점수화
└────────┬────────┘
         ↓
┌─────────────────┐
│ Function Node   │ → 상위 20% 중 랜덤 1개
│ (Top 20% Pick)  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Claude API      │ → 메시지 포맷팅
│ (Message Gen)   │    "...리뷰가 도착했습니다 + 해설"
└────────┬────────┘
         ↓
┌─────────────────┐
│ DB Insert       │ → evening_messages 테이블
│ (evening_msgs)  │    message_date = TODAY
└────────┬────────┘
         ↓
┌─────────────────┐
│ HTTP Request    │ → Redash Refresh (선택)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Slack/Email     │ → 성공/실패 알림
└─────────────────┘
```

### 워크플로우 3: 데이터 적재 (CSV → DB)

```
┌─────────────────┐
│ Webhook/Manual  │ → Python 스크립트 완료 후 트리거
└────────┬────────┘
         ↓
┌─────────────────┐
│ Read CSV        │ → data/bronze/playstore/*.csv
└────────┬────────┘
         ↓
┌─────────────────┐
│ Function Node   │ → 데이터 검증
│ (Validation)    │    - 필수 컬럼 확인
│                 │    - NULL 체크
│                 │    - 중복 제거
└────────┬────────┘
         ↓
┌─────────────────┐
│ DB Insert       │ → raw_reviews 테이블
│ (Batch)         │    ON CONFLICT DO NOTHING
└────────┬────────┘
         ↓
┌─────────────────┐
│ Slack           │ → 적재 완료 알림
│                 │    "6,000개 리뷰 적재 완료"
└─────────────────┘
```

---

## 🔧 n8n 노드 상세 설정

### 1. Cron Trigger 노드

**아침 워크플로우**
```json
{
  "mode": "everyDay",
  "hour": 7,
  "minute": 0,
  "timezone": "Asia/Seoul"
}
```

**저녁 워크플로우**
```json
{
  "mode": "everyDay",
  "hour": 17,
  "minute": 0,
  "timezone": "Asia/Seoul"
}
```

### 2. PostgreSQL/SQLite 노드

**아침 쿼리 (어제 리뷰)**
```sql
SELECT 
    id,
    review_id,
    review_content,
    rating,
    created_date,
    product_category
FROM raw_reviews
WHERE created_date = CURRENT_DATE - INTERVAL '1 day'
  AND LENGTH(review_content) BETWEEN 20 AND 200
  AND review_content NOT LIKE '%환불%'
  AND review_content NOT LIKE '%파손%'
  AND review_content NOT LIKE '%최악%'
ORDER BY created_date DESC
LIMIT 100;
```

**저녁 쿼리 (오늘 리뷰)**
```sql
SELECT 
    id,
    review_id,
    review_content,
    rating,
    created_date,
    product_category
FROM raw_reviews
WHERE created_date = CURRENT_DATE
  AND rating >= 4.5
  AND (
    review_content LIKE '%감사%' OR
    review_content LIKE '%따뜻%' OR
    review_content LIKE '%감동%' OR
    review_content LIKE '%추천%' OR
    review_content LIKE '%행복%'
  )
  AND review_content NOT LIKE '%환불%'
  AND review_content NOT LIKE '%교환%'
ORDER BY rating DESC, created_date DESC
LIMIT 50;
```

### 3. Function 노드 (유머 필터링)

```javascript
// 유머 키워드 필터링
const items = $input.all();

const HUMOR_KEYWORDS = ['ㅋㅋ', 'ㅎㅎ', '웃겨', '빵터', '농담', '반전', '재미', '꿀잼'];
const PROFANITY = ['시발', '씨발', '병신', '개새'];

const filtered = items.filter(item => {
  const content = item.json.review_content || '';
  
  // 유머 키워드 포함 확인
  const hasHumor = HUMOR_KEYWORDS.some(keyword => content.includes(keyword));
  
  // 욕설 제외
  const hasProfanity = PROFANITY.some(word => content.includes(word));
  
  return hasHumor && !hasProfanity;
});

return filtered;
```

### 4. Function 노드 (긍정 필터링)

```javascript
// 긍정 키워드 필터링
const items = $input.all();

const POSITIVE_KEYWORDS = ['감사', '고마워', '최고', '따뜻', '감동', '행복', '추천', '만족', '완벽'];
const CS_RISK = ['환불', '교환', '파손', '불량', '문제', '고장', '최악'];

const filtered = items.filter(item => {
  const content = item.json.review_content || '';
  
  // 긍정 키워드 포함
  const hasPositive = POSITIVE_KEYWORDS.some(keyword => content.includes(keyword));
  
  // CS 리스크 제외
  const hasRisk = CS_RISK.some(word => content.includes(word));
  
  return hasPositive && !hasRisk;
});

return filtered;
```

### 5. HTTP Request 노드 (Claude API)

**점수화 요청**
```json
{
  "method": "POST",
  "url": "https://api.anthropic.com/v1/messages",
  "authentication": "headerAuth",
  "headerParameters": {
    "parameters": [
      {
        "name": "x-api-key",
        "value": "={{$credentials.anthropicApi.apiKey}}"
      },
      {
        "name": "anthropic-version",
        "value": "2023-06-01"
      }
    ]
  },
  "bodyParameters": {
    "parameters": [
      {
        "name": "model",
        "value": "claude-sonnet-4-20250514"
      },
      {
        "name": "max_tokens",
        "value": 1024
      },
      {
        "name": "messages",
        "value": [
          {
            "role": "user",
            "content": "다음 리뷰의 유머 점수를 0-100으로 평가해주세요. 숫자만 출력하세요.\n\n리뷰: {{$json.review_content}}"
          }
        ]
      }
    ]
  }
}
```

### 6. Function 노드 (랜덤 선택)

```javascript
// 상위 점수 중 랜덤 선택
const items = $input.all();

// 점수순 정렬
const sorted = items.sort((a, b) => {
  const scoreA = parseInt(a.json.humor_score || 0);
  const scoreB = parseInt(b.json.humor_score || 0);
  return scoreB - scoreA;
});

// 아침: 상위 5개 중 랜덤
// 저녁: 상위 20% 중 랜덤
const topCount = Math.ceil(sorted.length * 0.2); // 상위 20%
const candidates = sorted.slice(0, Math.max(topCount, 5));

// 랜덤 선택
const selected = candidates[Math.floor(Math.random() * candidates.length)];

return [selected];
```

### 7. PostgreSQL 노드 (메시지 저장)

**아침 메시지 INSERT**
```sql
INSERT INTO morning_messages (
    scored_review_id,
    message_date,
    original_review,
    formatted_message,
    commentary,
    is_displayed,
    created_at
) VALUES (
    {{$json.review_id}},
    CURRENT_DATE,
    {{$json.review_content}},
    {{$json.formatted_message}},
    {{$json.commentary}},
    TRUE,
    NOW()
)
ON CONFLICT (message_date) DO UPDATE SET
    scored_review_id = EXCLUDED.scored_review_id,
    original_review = EXCLUDED.original_review,
    formatted_message = EXCLUDED.formatted_message,
    commentary = EXCLUDED.commentary,
    created_at = NOW();
```

---

## 🔐 보안 & 거버넌스

### Credentials 관리 (n8n)

```
1. PostgreSQL/SQLite
   - Host: localhost / Cloud RDS
   - Database: review_db
   - User: n8n_worker (READ/WRITE 권한만)
   
2. Claude API
   - API Key: Anthropic API Key
   - 환경변수로 관리
   
3. Tableau API (선택)
   - Personal Access Token
   - Refresh Workbook API
   
4. Slack Webhook
   - Incoming Webhook URL
```

### 에러 핸들링

```javascript
// Function 노드에서 에러 처리
try {
  // 메인 로직
  const result = processData($input.all());
  return result;
} catch (error) {
  // 에러 로깅
  console.error('Error:', error);
  
  // Slack 알림
  $node["Slack"].send({
    text: `❌ 워크플로우 실패: ${error.message}`,
    channel: '#alerts'
  });
  
  // 빈 결과 반환 (워크플로우 중단 방지)
  return [];
}
```

### 감사 로그

```sql
-- 모든 메시지 생성 시 audit_log 기록
INSERT INTO audit_log (
    table_name,
    action_type,
    record_id,
    user_name,
    action_timestamp,
    description
) VALUES (
    'morning_messages',
    'INSERT',
    {{$json.id}},
    'n8n_worker',
    NOW(),
    '아침 메시지 자동 생성 완료'
);
```

---

## 📊 Tableau/Redash 연동

### Tableau (모니터용)

**방법 1: DB 직접 연결 (권장)**
```
Tableau Desktop/Server
→ Data Source 추가
→ PostgreSQL/SQLite 선택
→ 테이블: morning_messages, evening_messages
→ WHERE message_date = TODAY()
```

**방법 2: Tableau API Refresh**
```javascript
// n8n HTTP Request 노드
POST https://tableau-server.com/api/3.x/sites/{site-id}/workbooks/{workbook-id}/refresh

Headers:
- X-Tableau-Auth: {token}

Body:
{
  "workbook": {
    "id": "workbook-id"
  }
}
```

### Redash (모바일용)

**방법 1: DB 직접 연결 (권장)**
```sql
-- Redash Query
SELECT 
    formatted_message,
    commentary,
    created_at
FROM morning_messages
WHERE message_date = CURRENT_DATE
UNION ALL
SELECT 
    formatted_message,
    commentary,
    created_at
FROM evening_messages
WHERE message_date = CURRENT_DATE;
```

**방법 2: Redash API**
```javascript
// n8n HTTP Request 노드
POST https://redash.example.com/api/queries/{query-id}/refresh

Headers:
- Authorization: Key {api-key}
```

---

## 🧪 테스트 시나리오

### 1. 수동 트리거 테스트
```
n8n UI → 워크플로우 선택 → [Execute Workflow] 버튼
→ 각 노드별 출력 확인
→ DB에 데이터 적재 확인
```

### 2. 시간 테스트
```
Cron 노드 설정 변경:
- 아침: 현재 시각 + 5분
- 저녁: 현재 시각 + 10분
→ 자동 실행 확인
```

### 3. 에러 핸들링 테스트
```
- DB 연결 끊기 → 에러 알림 확인
- Claude API 키 제거 → Fallback 로직 확인
- 빈 데이터 → 기본 메시지 생성 확인
```

---

## 📈 모니터링

### n8n 실행 로그
```
Settings → Executions
→ 성공/실패 확인
→ 실행 시간 체크
→ 에러 메시지 분석
```

### DB 확인
```sql
-- 오늘 생성된 메시지 확인
SELECT * FROM morning_messages WHERE message_date = CURRENT_DATE;
SELECT * FROM evening_messages WHERE message_date = CURRENT_DATE;

-- 최근 7일 통계
SELECT 
    message_date,
    COUNT(*) as message_count
FROM morning_messages
WHERE message_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY message_date
ORDER BY message_date DESC;
```

### Slack 알림 예시
```
✅ 아침 메시지 생성 완료 (07:02)
📊 리뷰: "배송이 너무 빨라서 놀랐어요 ㅋㅋ"
📈 유머 점수: 85/100

✅ 저녁 메시지 생성 완료 (17:03)
📊 리뷰: "덕분에 하루가 따뜻했어요"
📈 긍정 점수: 92/100
```

---

## 🚀 배포 체크리스트

- [ ] n8n 설치 및 설정
- [ ] DB 연결 테스트
- [ ] Claude API 키 등록
- [ ] 워크플로우 3개 Import
- [ ] Cron 스케줄 설정
- [ ] 에러 알림 채널 설정 (Slack/Email)
- [ ] 수동 테스트 1회 실행
- [ ] 시간 테스트 (아침/저녁)
- [ ] Tableau/Redash 연결 확인
- [ ] 1주일 모니터링

---

**다음**: n8n 워크플로우 JSON 파일 생성
