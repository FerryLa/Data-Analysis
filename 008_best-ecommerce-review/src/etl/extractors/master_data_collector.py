"""
데이터 수집 마스터 도구
모든 공개 데이터 소스 통합 관리

지원 데이터 소스:
1. AI Hub (한국어 쇼핑 리뷰) - 최우선
2. Amazon Reviews (영어, 대용량)
3. Kaggle (영어, 의류)
4. Google Play Store (한국어, 실시간)

사용법:
python src/etl/extractors/master_data_collector.py
"""

import sys
from pathlib import Path


MENU = """
╔══════════════════════════════════════════════════════════════════╗
║          📊 008_best-ecomerce-review 데이터 수집 도구           ║
╚══════════════════════════════════════════════════════════════════╝

우선순위별 데이터 소스:

  1️⃣  AI Hub (한국어) ⭐⭐⭐⭐⭐
       ├─ 규모: 10만~100만 건
       ├─ 품질: 최고 (감성 라벨 포함)
       └─ 설정: 회원가입 필요 (무료)

  2️⃣  Amazon Reviews (영어) ⭐⭐⭐⭐
       ├─ 규모: 수백만 건
       ├─ 품질: 높음
       └─ 설정: 즉시 다운로드

  3️⃣  Kaggle (영어) ⭐⭐⭐⭐
       ├─ 규모: 23,000건
       ├─ 품질: 높음 (정제됨)
       └─ 설정: API Token 필요

  4️⃣  Google Play Store (한국어) ⭐⭐⭐⭐⭐
       ├─ 규모: 1,000~10,000건
       ├─ 품질: 중상
       └─ 설정: 즉시 사용

  5️⃣  모든 소스 통합 수집
       └─ 한국어 + 영어 혼합 데이터

  0️⃣  종료

╔══════════════════════════════════════════════════════════════════╗
"""


def run_aihub():
    """AI Hub 데이터 수집"""
    print("\n" + "="*70)
    print("🇰🇷 AI Hub 한국어 쇼핑 리뷰 데이터")
    print("="*70)
    
    try:
        import download_aihub_data
        download_aihub_data.main()
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        print("\n수동 실행:")
        print("  python src/etl/extractors/download_aihub_data.py")


def run_amazon():
    """Amazon 리뷰 수집"""
    print("\n" + "="*70)
    print("🌎 Amazon Review 데이터셋")
    print("="*70)
    print("\n선택 가능한 카테고리:")
    print("  1. electronics (전자제품)")
    print("  2. clothing (의류)")
    print("  3. home (가정용품)")
    print("  4. beauty (뷰티)")
    
    category = input("\n카테고리 번호 또는 이름 입력 (엔터: 전자제품): ").strip()
    
    category_map = {
        '1': 'electronics',
        '2': 'clothing',
        '3': 'home',
        '4': 'beauty',
    }
    
    category = category_map.get(category, category) or 'electronics'
    
    sample = input("샘플 데이터셋으로 시작하시겠습니까? (y/n, 기본: y): ").strip().lower()
    sample_flag = "--sample" if sample != 'n' else ""
    
    max_rows = input("최대 행 수 제한 (엔터: 제한 없음): ").strip()
    max_rows_flag = f"--max-rows {max_rows}" if max_rows else ""
    
    cmd = f"python src/etl/extractors/download_amazon_reviews.py --category {category} {sample_flag} {max_rows_flag}"
    
    print(f"\n실행 명령: {cmd}")
    
    import subprocess
    try:
        subprocess.run(cmd, shell=True, check=True)
    except:
        print(f"\n수동 실행:")
        print(f"  {cmd}")


def run_kaggle():
    """Kaggle 데이터 수집"""
    print("\n" + "="*70)
    print("📊 Kaggle 데이터셋")
    print("="*70)
    
    try:
        import download_kaggle_data
        download_kaggle_data.main()
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        print("\n수동 실행:")
        print("  python src/etl/extractors/download_kaggle_data.py")


def run_playstore():
    """Google Play Store 리뷰 수집"""
    print("\n" + "="*70)
    print("📱 Google Play Store 리뷰")
    print("="*70)
    print("\n추천 앱:")
    print("  1. 쿠팡")
    print("  2. 네이버쇼핑")
    print("  3. 배달의민족")
    print("  4. 11번가")
    print("  5. 직접 입력")
    
    choice = input("\n번호 선택 (기본: 1): ").strip()
    
    app_map = {
        '1': '쿠팡',
        '2': '네이버쇼핑',
        '3': '배달의민족',
        '4': '11번가',
    }
    
    if choice == '5':
        app = input("앱 이름 또는 패키지명 입력: ").strip()
    else:
        app = app_map.get(choice, '쿠팡')
    
    count = input("수집할 리뷰 개수 (기본: 1000): ").strip() or "1000"
    
    cmd = f"python src/etl/extractors/download_playstore_reviews.py --app {app} --count {count}"
    
    print(f"\n실행 명령: {cmd}")
    
    import subprocess
    try:
        subprocess.run(cmd, shell=True, check=True)
    except:
        print(f"\n수동 실행:")
        print(f"  {cmd}")


def run_all():
    """모든 소스에서 데이터 수집"""
    print("\n" + "="*70)
    print("🌍 전체 데이터 소스 수집")
    print("="*70)
    print("\n다음 순서로 진행합니다:")
    print("  1. Google Play Store (쿠팡, 1000개)")
    print("  2. Kaggle (의류 리뷰)")
    print("  3. Amazon (전자제품 샘플)")
    print()
    
    confirm = input("계속하시겠습니까? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("취소되었습니다.")
        return
    
    # 1. Google Play Store
    print("\n[1/3] Google Play Store 수집 중...")
    import subprocess
    subprocess.run("python src/etl/extractors/download_playstore_reviews.py --app 쿠팡 --count 1000", shell=True)
    
    # 2. Kaggle
    print("\n[2/3] Kaggle 수집 중...")
    try:
        import download_kaggle_data
        download_kaggle_data.download_kaggle_dataset()
    except:
        print("⚠️  Kaggle 설정이 필요합니다. 건너뜁니다.")
    
    # 3. Amazon
    print("\n[3/3] Amazon 수집 중...")
    subprocess.run("python src/etl/extractors/download_amazon_reviews.py --category electronics --sample --max-rows 5000", shell=True)
    
    print("\n" + "="*70)
    print("✅ 전체 수집 완료!")
    print("="*70)
    print("\n수집된 데이터:")
    print("  - Google Play Store: data/bronze/playstore/")
    print("  - Kaggle: data/bronze/kaggle/")
    print("  - Amazon: data/bronze/amazon/")


def check_requirements():
    """필수 패키지 확인"""
    required = {
        'Google Play Store': 'google_play_scraper',
        'Kaggle': 'kaggle',
        'Amazon': 'requests',
    }
    
    missing = []
    
    for name, package in required.items():
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append((name, package))
    
    if missing:
        print("\n⚠️  누락된 패키지:")
        for name, package in missing:
            print(f"   - {package} (for {name})")
        print("\n설치 명령:")
        print(f"   pip install {' '.join([p for _, p in missing])}")
        print()


def main():
    """메인 메뉴"""
    
    # 필수 패키지 확인
    check_requirements()
    
    while True:
        print(MENU)
        choice = input("선택 (0-5): ").strip()
        
        if choice == '0':
            print("\n종료합니다.")
            break
        
        elif choice == '1':
            run_aihub()
        
        elif choice == '2':
            run_amazon()
        
        elif choice == '3':
            run_kaggle()
        
        elif choice == '4':
            run_playstore()
        
        elif choice == '5':
            run_all()
        
        else:
            print("\n❌ 잘못된 선택입니다.")
        
        input("\n[엔터] 계속...")


if __name__ == "__main__":
    # 경로 설정
    sys.path.append(str(Path(__file__).parent))
    
    main()
