# 데이터 품질 규칙

## 검증 항목

### 1. Null 체크
- NOT NULL 컬럼에 NULL 값 없음

### 2. 중복 체크
- review_id UNIQUE 제약조건 준수
- message_date UNIQUE (하루 1개)

### 3. 범위 체크
- rating: 1.0 ~ 5.0
- humor_score: 0 ~ 100
- positive_score: 0 ~ 100

### 4. 길이 체크
- char_length: 20 ~ 200 (유머)
- char_length: 10 ~ 500 (긍정)

### 5. 키워드 검증
- 욕설/비속어 제외
- CS 리스크 키워드 제외
