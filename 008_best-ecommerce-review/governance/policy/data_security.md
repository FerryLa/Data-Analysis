# 데이터 보안 정책

## 개인정보 보호

### 마스킹 규칙
- 작성자명: 첫 글자만 표시 (홍*동)
- 연락처: 수집 금지
- 이메일: 수집 금지

### 데이터 보유기간
- Bronze (raw): 90일
- Silver (processed): 180일
- Gold (message): 365일
- audit_log: 730일

## 접근 권한
- READ: 전체 팀원
- WRITE: ETL Team, Data Team
- DELETE: Admin Only

## 감사 로그
- 모든 CUD 작업 기록
- 누가, 언제, 무엇을 수정했는지 추적
