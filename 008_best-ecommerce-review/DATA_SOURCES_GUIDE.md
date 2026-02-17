# 📥 공개 데이터 확보 종합 가이드

## 🎯 우선순위별 데이터 소스

당신이 선택한 우선순위:
1. **한국어 리뷰** (AI Hub, 공공데이터) ⭐⭐⭐⭐⭐
2. **Amazon 리뷰** (공개 데이터셋) ⭐⭐⭐⭐
3. **학술 데이터셋** (UCI, Kaggle) ⭐⭐⭐⭐
4. **App Store/Google Play** (공개 API) ⭐⭐⭐⭐⭐

---

## 🚀 빠른 시작

### 가장 쉬운 방법 (5분)

```powershell
# 마스터 도구 실행
python src\etl\extractors\master_data_collector.py

# 메뉴에서 선택:
# 1. AI Hub (한국어, 최우선)
# 4. Google Play Store (한국어, 즉시 가능)
```

---

## 1️⃣ AI Hub (한국어) - 최우선 🇰🇷

### 데이터셋 정보
```
📊 규모: 10만~100만 건
🇰🇷 언어: 한국어
✅ 품질: 최고 (감성 라벨 포함)
📝 컬럼: 리뷰, 평점, 카테고리, 감성
💰 비용: 무료
📄 라이선스: 공공누리 (연구/상업 가능)
```

### 다운로드 방법

#### 준비 (최초 1회)
1. **회원가입**
   ```
   https://aihub.or.kr/join/join.do
   → 무료 회원가입 (1분)
   ```

2. **데이터 신청**
   ```
   https://aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&aihubDataSe=realm&dataSetSn=71
   
   [데이터 신청] 버튼 클릭
   → 사용 목적: "개인 연구 프로젝트"
   → 즉시 승인 (또는 1~2일 대기)
   ```

3. **다운로드**
   ```
   [다운로드] 탭
   → Training 데이터 선택
   → ZIP 다운로드
   ```

#### 데이터 처리
```powershell
# 1. ZIP 파일을 프로젝트에 복사
copy Downloads\쇼핑리뷰_*.zip data\bronze\aihub\

# 2. 변환 스크립트 실행
python src\etl\extractors\download_aihub_data.py

# → 자동으로 압축 해제 및 CSV 변환
```

### 추천 데이터셋

| 이름 | 규모 | 특징 |
|------|------|------|
| 쇼핑 리뷰 감성 분석 | 100만 건 | 감성 라벨 포함 ✨ |
| 온라인 쇼핑 상품평 | 50만 건 | 카테고리별 분류 |

---

## 2️⃣ Amazon Reviews (영어) 🌎

### 데이터셋 정보
```
📊 규모: 수백만 건 (카테고리별)
🌍 언어: 영어
✅ 품질: 높음
📝 기간: 1996-2018
💰 비용: 무료
📄 라이선스: 학술/연구용
```

### 즉시 다운로드

```powershell
# 샘플 데이터 (빠른 테스트)
python src\etl\extractors\download_amazon_reviews.py --category electronics --sample

# 전체 데이터 (시간 소요)
python src\etl\extractors\download_amazon_reviews.py --category electronics

# 행 수 제한 (메모리 절약)
python src\etl\extractors\download_amazon_reviews.py --category electronics --max-rows 50000
```

### 카테고리 선택

| 카테고리 | 키워드 | 규모 |
|----------|--------|------|
| 전자제품 | electronics | 700만 |
| 의류 | clothing | 1,000만 |
| 가정용품 | home | 500만 |
| 뷰티 | beauty | 700만 |

---

## 3️⃣ Kaggle (영어) 📊

### 데이터셋 정보
```
📊 규모: 23,000건
🌍 언어: 영어
✅ 품질: 높음 (정제됨)
📝 카테고리: 여성 의류
💰 비용: 무료
```

### 준비 (최초 1회)

1. **Kaggle 계정**
   ```
   https://www.kaggle.com/account/login
   ```

2. **API Token 발급**
   ```
   https://www.kaggle.com/settings/account
   → "Create New API Token" 클릭
   → kaggle.json 다운로드
   ```

3. **Token 설치**
   ```powershell
   # Windows
   mkdir C:\Users\YourName\.kaggle
   copy Downloads\kaggle.json C:\Users\YourName\.kaggle\
   ```

### 다운로드

```powershell
pip install kaggle
python src\etl\extractors\download_kaggle_data.py
```

---

## 4️⃣ Google Play Store (한국어) 📱

### 데이터셋 정보
```
📊 규모: 1,000~10,000건 (앱별)
🇰🇷 언어: 한국어 ✨
✅ 품질: 중상
📝 실시간: 최신 리뷰
💰 비용: 무료
```

### 즉시 다운로드

```powershell
pip install google-play-scraper

# 쿠팡 앱 리뷰 1000개
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 1000

# 여러 앱 수집
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 2000
python src\etl\extractors\download_playstore_reviews.py --app 배달의민족 --count 2000
```

---

## 🎯 추천 시작 방법

### 시나리오 1: 한국어 중심 (추천!)

```powershell
# Step 1: Google Play Store (즉시)
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 2000

# Step 2: AI Hub (회원가입 후)
# → 웹사이트에서 수동 다운로드
python src\etl\extractors\download_aihub_data.py

# 결과: 한국어 리뷰 10만+ 건
```

### 시나리오 2: 대용량 필요

```powershell
# Step 1: Amazon (샘플로 시작)
python src\etl\extractors\download_amazon_reviews.py --category electronics --sample

# Step 2: 전체 다운로드 (선택)
python src\etl\extractors\download_amazon_reviews.py --category electronics

# 결과: 영어 리뷰 수백만 건
```

### 시나리오 3: 혼합 (한국어 + 영어)

```powershell
# 마스터 도구로 전체 수집
python src\etl\extractors\master_data_collector.py
→ 메뉴에서 "5. 모든 소스 통합 수집" 선택

# 결과: 다국어 리뷰 10만+ 건
```

---

## 📊 데이터 소스 비교표

| 소스 | 언어 | 규모 | 품질 | 설정 | 추천도 |
|------|------|------|------|------|--------|
| **AI Hub** | 🇰🇷 한국어 | 10만~100만 | ⭐⭐⭐⭐⭐ | 중간 | ⭐⭐⭐⭐⭐ |
| **Amazon** | 🇺🇸 영어 | 수백만 | ⭐⭐⭐⭐ | 쉬움 | ⭐⭐⭐⭐ |
| **Kaggle** | 🇺🇸 영어 | 23,000 | ⭐⭐⭐⭐ | 중간 | ⭐⭐⭐⭐ |
| **Play Store** | 🇰🇷 한국어 | 1,000~10,000 | ⭐⭐⭐ | 즉시 | ⭐⭐⭐⭐⭐ |

---

## ✅ 다음 단계

데이터를 다운로드한 후:

### 1. 데이터 검증
```powershell
python src\etl\extractors\validate_smartstore_csv.py
```

### 2. DB 초기화
```powershell
sqlite3 review.db < sql\ddl\01_create_tables.sql
```

### 3. CSV → DB 적재
```powershell
python src\etl\extractors\csv_loader.py
```

### 4. 필터링 테스트
```powershell
python src\filters\humor\filter_humor.py
python src\filters\positive\filter_positive.py
```

---

## 🆘 문제 해결

### Q1: AI Hub 승인이 오래 걸려요
**A**: Google Play Store로 먼저 시작하세요 (즉시 가능)
```powershell
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 2000
```

### Q2: 영어 리뷰를 한국어로 번역하고 싶어요
**A**: 나중에 번역 모듈을 추가할 수 있습니다. 지금은 한국어 데이터 우선!

### Q3: 메모리가 부족해요
**A**: `--max-rows` 옵션 사용
```powershell
python src\etl\extractors\download_amazon_reviews.py --category electronics --max-rows 10000
```

---

## 🎉 권장 첫 실행

```powershell
# 1. 프로젝트 설정
cd C:\dev\Data_Analysis\008_best-ecomerce-review
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. 한국어 리뷰 수집 (5분)
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 2000

# 3. 데이터 검증
python src\etl\extractors\validate_smartstore_csv.py
→ 경로: data\bronze\playstore\reviews_쿠팡_20250208.csv

# 4. DB 적재
sqlite3 review.db < sql\ddl\01_create_tables.sql
python src\etl\extractors\csv_loader.py

# 완료! 🎊
```

---

**Ready? 지금 바로 시작하세요! 🚀**

```powershell
python src\etl\extractors\master_data_collector.py
```
