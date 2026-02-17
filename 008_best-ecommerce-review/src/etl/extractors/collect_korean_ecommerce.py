"""
한국 이커머스 앱 리뷰 일괄 수집
배치 실행으로 여러 쇼핑 앱의 리뷰를 한 번에 수집

실행:
python src/etl/extractors/collect_korean_ecommerce.py
"""

import subprocess
import time
from datetime import datetime


# 한국 이커머스 앱 목록
KOREAN_ECOMMERCE_APPS = [
    {'name': '쿠팡', 'package': 'com.coupang.mobile', 'count': 2000},
    {'name': '11번가', 'package': 'com.skeletonapp.skplanet11st', 'count': 2000},
    {'name': '네이버쇼핑', 'package': 'com.nhn.android.search', 'count': 1000},
    {'name': '마켓컬리', 'package': 'com.dmp.market.kurly', 'count': 1000},
    {'name': '지마켓', 'package': 'kr.co.gmarket.mobile', 'count': 1000},
    {'name': '무신사', 'package': 'com.musinsa.store', 'count': 1000},
]


def collect_all_ecommerce_reviews():
    """모든 이커머스 앱 리뷰 수집"""
    
    print("=" * 70)
    print("🇰🇷 한국 이커머스 앱 리뷰 일괄 수집")
    print("=" * 70)
    print()
    
    print("📱 수집 대상 앱:")
    total_count = 0
    for i, app in enumerate(KOREAN_ECOMMERCE_APPS, 1):
        print(f"   {i}. {app['name']}: {app['count']:,}개")
        total_count += app['count']
    
    print(f"\n총 예상 리뷰 수: {total_count:,}개")
    print(f"예상 소요 시간: 약 {len(KOREAN_ECOMMERCE_APPS) * 5}분")
    print()
    
    confirm = input("시작하시겠습니까? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("취소되었습니다.")
        return
    
    print("\n" + "=" * 70)
    print("🚀 수집 시작")
    print("=" * 70)
    
    results = []
    start_time = time.time()
    
    for i, app in enumerate(KOREAN_ECOMMERCE_APPS, 1):
        print(f"\n[{i}/{len(KOREAN_ECOMMERCE_APPS)}] {app['name']} 수집 중...")
        
        cmd = f"python src/etl/extractors/download_playstore_reviews.py --app {app['name']} --count {app['count']}"
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                results.append({
                    'app': app['name'],
                    'count': app['count'],
                    'status': 'success'
                })
                print(f"   ✅ {app['name']}: 성공")
            else:
                results.append({
                    'app': app['name'],
                    'count': app['count'],
                    'status': 'failed'
                })
                print(f"   ❌ {app['name']}: 실패")
                print(f"   오류: {result.stderr[:200]}")
        
        except Exception as e:
            results.append({
                'app': app['name'],
                'count': app['count'],
                'status': 'error'
            })
            print(f"   ❌ {app['name']}: 오류 - {e}")
        
        # 다음 앱 수집 전 짧은 대기
        if i < len(KOREAN_ECOMMERCE_APPS):
            time.sleep(2)
    
    elapsed_time = time.time() - start_time
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 수집 결과 요약")
    print("=" * 70)
    print()
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    total_reviews = sum(r['count'] for r in results if r['status'] == 'success')
    
    print(f"✅ 성공: {success_count}/{len(results)}개 앱")
    print(f"📄 총 리뷰 수: 약 {total_reviews:,}개")
    print(f"⏱️  소요 시간: {elapsed_time / 60:.1f}분")
    print()
    
    print("세부 결과:")
    for r in results:
        status_icon = "✅" if r['status'] == 'success' else "❌"
        print(f"   {status_icon} {r['app']}: {r['count']:,}개 ({r['status']})")
    
    print()
    print("=" * 70)
    print("✅ 수집 완료!")
    print("=" * 70)
    print()
    print("📂 저장 위치: data\\bronze\\playstore\\")
    print()
    print("다음 단계:")
    print("1. 데이터 검증:")
    print("   python src\\etl\\extractors\\validate_smartstore_csv.py")
    print()
    print("2. DB 초기화:")
    print("   sqlite3 review.db < sql\\ddl\\01_create_tables.sql")
    print()
    print("3. CSV → DB 적재:")
    print("   python src\\etl\\extractors\\csv_loader.py")


def collect_custom():
    """사용자 지정 앱 리뷰 수집"""
    
    print("\n" + "=" * 70)
    print("🛠️  커스텀 수집")
    print("=" * 70)
    print()
    
    apps = []
    
    while True:
        print(f"\n현재 선택된 앱: {len(apps)}개")
        
        app_name = input("앱 이름 입력 (완료: 엔터): ").strip()
        
        if not app_name:
            break
        
        count = input(f"{app_name} 리뷰 개수 (기본: 1000): ").strip() or "1000"
        
        apps.append({'name': app_name, 'count': int(count)})
        print(f"   ✅ {app_name} 추가됨 ({count}개)")
    
    if not apps:
        print("취소되었습니다.")
        return
    
    print(f"\n총 {len(apps)}개 앱, {sum(a['count'] for a in apps):,}개 리뷰 수집")
    confirm = input("시작하시겠습니까? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("취소되었습니다.")
        return
    
    for app in apps:
        cmd = f"python src/etl/extractors/download_playstore_reviews.py --app {app['name']} --count {app['count']}"
        subprocess.run(cmd, shell=True)


def main():
    """메인 메뉴"""
    
    print("=" * 70)
    print("🇰🇷 한국 이커머스 리뷰 수집 도구")
    print("=" * 70)
    print()
    print("1. 전체 수집 (추천 이커머스 앱 6개)")
    print("2. 커스텀 수집 (직접 선택)")
    print("0. 종료")
    print()
    
    choice = input("선택 (0-2): ").strip()
    
    if choice == '1':
        collect_all_ecommerce_reviews()
    elif choice == '2':
        collect_custom()
    elif choice == '0':
        print("종료합니다.")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    # 필수 패키지 확인
    try:
        from google_play_scraper import app
    except ImportError:
        print("❌ google-play-scraper 패키지가 필요합니다.")
        print("설치: pip install google-play-scraper")
        exit(1)
    
    main()
