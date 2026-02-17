# 📥 공개 데이터 확보 가이드

## 🎯 두 가지 추천 방법

---

## 방법 1: Google Play Store 한국어 리뷰 (추천!) 🇰🇷

### 장점
- ✅ **한국어** (프로젝트에 최적)
- ✅ **실시간** 수집
- ✅ **합법적** (공개 API)
- ✅ **즉시 시작** 가능

### 설치

```powershell
pip install google-play-scraper
```

### 사용법

#### Step 1: 인기 앱 목록 확인
```powershell
python src\etl\extractors\download_playstore_reviews.py --list
```

**출력 예시:**
```
🔥 추천 앱 목록:
   1. 쿠팡: com.coupang.mobile
   2. 네이버쇼핑: com.nhn.android.search
   3. 배달의민족: com.sampleapp
   4. 마켓컬리: com.dmp.market.kurly
   5. 11번가: com.skeletonapp.skplanet11st
   ...
```

#### Step 2: 리뷰 다운로드
```powershell
# 쿠팡 리뷰 1000개 수집
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 1000

# 또는 패키지명으로
python src\etl\extractors\download_playstore_reviews.py --app com.coupang.mobile --count 1000
```

#### Step 3: 결과 확인
```
✅ 수집 완료: 1,000개
📄 파일: data\bronze\playstore\reviews_쿠팡_20250208.csv

📊 데이터 통계:
   평균 평점: 4.3
   평균 길이: 45.2자
   날짜 범위: 2024-11-08 ~ 2025-02-08
```

---

## 방법 2: Kaggle 데이터셋 (영어)

### 장점
- ✅ **대용량** (23,000건)
- ✅ **고품질** (정제됨)
- ✅ **즉시 다운로드**

### 준비 (최초 1회만)

#### Step 1: Kaggle 계정 생성
```
https://www.kaggle.com/account/login
→ 무료 계정 생성
```

#### Step 2: API Token 발급
```
1. https://www.kaggle.com/settings/account
2. "Create New API Token" 클릭
3. kaggle.json 다운로드
```

#### Step 3: kaggle.json 설치
```powershell
# Windows
mkdir C:\Users\YourName\.kaggle
copy Downloads\kaggle.json C:\Users\YourName\.kaggle\

# 권한 설정 (PowerShell 관리자 모드)
icacls C:\Users\YourName\.kaggle\kaggle.json /inheritance:r /grant:r "%USERNAME%:R"
```

### 사용법

```powershell
# 패키지 설치
pip install kaggle

# 데이터 다운로드 및 변환
python src\etl\extractors\download_kaggle_data.py
```

**자동으로 수행:**
1. Kaggle에서 데이터셋 다운로드
2. 프로젝트 형식으로 변환
3. CSV 저장

---

## 📊 데이터 비교

| 항목 | Google Play Store | Kaggle |
|------|-------------------|--------|
| 언어 | 🇰🇷 **한국어** | 🇺🇸 영어 |
| 규모 | 1,000~10,000건 | 23,000건 |
| 설정 | 간단 (1분) | 중간 (5분) |
| 카테고리 | 앱 선택 가능 | 의류 고정 |
| 실시간 | ✅ 가능 | ❌ 불가 |
| 추천 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🚀 추천 시작 방법

### 초보자 / 빠른 시작
```powershell
# Google Play Store (한국어, 5분)
pip install google-play-scraper
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 1000
```

### 대용량 데이터 필요
```powershell
# Kaggle (영어, 10분)
pip install kaggle
# kaggle.json 설정 (위 가이드 참조)
python src\etl\extractors\download_kaggle_data.py
```

### 두 개 모두 사용
```powershell
# 둘 다 수집해서 혼합 사용 가능!
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 1000
python src\etl\extractors\download_kaggle_data.py
```

---

## ✅ 다음 단계

데이터 다운로드 후:

```powershell
# 1. 데이터 검증
python src\etl\extractors\validate_smartstore_csv.py
→ 경로 입력: data\bronze\playstore\reviews_쿠팡_20250208.csv

# 2. DB 초기화
sqlite3 review.db < sql\ddl\01_create_tables.sql

# 3. CSV → DB 적재
python src\etl\extractors\csv_loader.py

# 4. 필터링 테스트
python src\filters\humor\filter_humor.py
```

---

## 🆘 문제 해결

### Q1: "google_play_scraper 모듈을 찾을 수 없습니다"
```powershell
# 가상환경 활성화 확인
venv\Scripts\activate

# 재설치
pip uninstall google-play-scraper
pip install google-play-scraper
```

### Q2: Kaggle API 401 Unauthorized
```powershell
# kaggle.json 위치 확인
dir C:\Users\YourName\.kaggle\kaggle.json

# 없으면 다시 다운로드 및 복사
```

### Q3: 수집된 리뷰가 너무 적어요
```powershell
# 개수 증가 (최대 수천~수만 개)
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 5000

# 여러 앱 수집
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 2000
python src\etl\extractors\download_playstore_reviews.py --app 배달의민족 --count 2000
python src\etl\extractors\download_playstore_reviews.py --app 11번가 --count 2000
```

---

## 📝 법적 고지

### ✅ 합법적 사용
- Google Play Store 공개 API 사용 (합법)
- Kaggle 공개 데이터셋 (연구/상업 가능)
- 개인 학습 및 연구 목적

### ⚠️ 주의사항
- 수집 속도 제한 준수 (API Rate Limit)
- 개인정보 마스킹 처리
- 상업적 사용 시 라이선스 확인

---

**Ready? 지금 바로 시작하세요! 🚀**

```powershell
# 한국어 리뷰 1000개 수집 (권장)
pip install google-play-scraper
python src\etl\extractors\download_playstore_reviews.py --app 쿠팡 --count 1000
```
