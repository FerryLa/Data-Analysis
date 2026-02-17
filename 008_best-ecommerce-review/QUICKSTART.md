# 🚀 008_best-ecomerce-review 퀵스타트 가이드

## 📦 생성 완료!

프로젝트 구조가 성공적으로 생성되었습니다.

- **총 폴더**: 73개
- **총 파일**: 14개 (핵심 파일)
- **구조**: Data_Analysis 표준 준수

---

## 🎯 다음 단계

### 1️⃣ Windows에서 프로젝트 설정

```powershell
# 1. 다운로드한 폴더를 원하는 위치로 이동
# 예: C:\dev\Data_Analysis\008_best-ecomerce-review

# 2. 가상환경 생성
cd C:\dev\Data_Analysis\008_best-ecomerce-review
python -m venv venv

# 3. 가상환경 활성화
venv\Scripts\activate

# 4. 패키지 설치
pip install -r requirements.txt

# 5. DB 초기화 (SQLite)
sqlite3 review.db < sql\ddl\01_create_tables.sql
```

---

### 2️⃣ 데이터 준비 (체크리스트 1단계)

#### 옵션 A: 실제 데이터 사용
```powershell
# 스마트스토어 판매자 센터에서 리뷰 CSV 다운로드
# → data\bronze\smartstore\reviews_YYYYMMDD.csv 로 저장
```

#### 옵션 B: 샘플 데이터 생성 (테스트용)
```powershell
python tests\fixtures\sample_reviews.py > sample_data.csv
```

---

### 3️⃣ ETL 실행

```powershell
# CSV → DB 적재
python src\etl\extractors\csv_loader.py

# 유머 필터링
python src\filters\humor\filter_humor.py

# 결과 확인
sqlite3 review.db "SELECT COUNT(*) FROM raw_reviews;"
```

---

## 📂 프로젝트 구조 살펴보기

### 핵심 파일 위치

```
008_best-ecomerce-review/
│
├── 📄 README.md                    # 프로젝트 개요
├── 📄 requirements.txt              # Python 패키지 목록
├── 📄 .gitignore                    # Git 제외 파일
│
├── data/                            # 데이터 레이어
│   ├── bronze/                      # 원시 데이터
│   │   └── smartstore/              # 스마트스토어 CSV
│   ├── silver/                      # 전처리 데이터
│   └── gold/                        # 최종 데이터
│
├── governance/                      # 거버넌스 문서
│   ├── catalog/                     # 📋 데이터 카탈로그
│   ├── lineage/                     # 🔄 데이터 계보
│   ├── quality/                     # ✅ 품질 규칙
│   └── policy/                      # 🔐 보안 정책
│
├── src/                             # 소스 코드
│   ├── config/
│   │   └── filter_rules.py          # ⚙️ 필터링 규칙 중앙 관리
│   ├── etl/
│   │   └── extractors/
│   │       └── csv_loader.py        # 📥 CSV → DB 적재
│   └── filters/
│       └── humor/
│           └── filter_humor.py      # 😄 유머 필터링
│
├── sql/                             # SQL 스크립트
│   └── ddl/
│       └── 01_create_tables.sql     # 🗄️ DB 스키마
│
├── tests/
│   └── fixtures/
│       └── sample_reviews.py        # 🧪 샘플 데이터 생성
│
└── docs/
    └── private/architecture/
        └── CHECKLIST.md             # ✅ 실행 체크리스트
```

---

## 🎓 학습 가이드

### 1. 데이터 카탈로그 먼저 읽기
```powershell
start governance\catalog\data_catalog.md
```
→ 모든 테이블 스키마와 구조 이해

### 2. 필터링 규칙 커스터마이징
```powershell
notepad src\config\filter_rules.py
```
→ 유머/긍정/제외 키워드 수정

### 3. 체크리스트 따라가기
```powershell
start docs\private\architecture\CHECKLIST.md
```
→ 1단계부터 7단계까지 순차 실행

---

## 🔍 주요 개념

### Bronze → Silver → Gold

- **Bronze**: 원시 데이터 (CSV 그대로)
- **Silver**: 정제/필터링/점수화 완료
- **Gold**: 비즈니스에 바로 사용 가능 (메시지)

### 거버넌스 4대 요소

1. **Catalog**: 무엇이 있는가? (메타데이터)
2. **Lineage**: 어디서 왔는가? (데이터 흐름)
3. **Quality**: 믿을 수 있는가? (검증 규칙)
4. **Policy**: 안전한가? (보안/권한)

---

## 💡 팁

### VS Code에서 열기
```powershell
code C:\dev\Data_Analysis\008_best-ecomerce-review
```

### SQLite DB 확인
```powershell
# 설치: https://sqlitebrowser.org/
DB Browser for SQLite로 review.db 열기
```

### n8n 설치 (나중에)
```powershell
npm install -g n8n
n8n start
```

---

## 📞 문제 해결

### Q1: Python 패키지 설치 실패
```powershell
# 관리자 권한으로 실행
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Q2: SQLite 명령어 인식 안됨
```powershell
# SQLite 다운로드: https://www.sqlite.org/download.html
# sqlite3.exe를 PATH에 추가하거나 직접 경로 지정
```

### Q3: 한글 인코딩 에러
```powershell
# CSV 저장 시 UTF-8 인코딩 사용
# Excel에서는 "UTF-8 BOM" 선택
```

---

## 🎉 성공 기준

✅ DB에 샘플 리뷰 100개 적재  
✅ 유머 필터링으로 10개 선별  
✅ 아침 메시지 1개 생성  
✅ 거버넌스 문서 3개 이상 작성  

---

## 📚 다음 학습 자료

- [x] 프로젝트 구조 생성 ← **지금 여기**
- [ ] DB 스키마 설계 이해
- [ ] ETL 파이프라인 구축
- [ ] n8n 워크플로우 설계
- [ ] 대시보드 연동 (Tableau/Redash)

---

**Ready? Let's Build! 🚀**

체크리스트 1단계부터 시작하세요:  
`docs\private\architecture\CHECKLIST.md`
