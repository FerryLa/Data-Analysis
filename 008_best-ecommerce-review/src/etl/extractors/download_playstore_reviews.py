"""
Google Play Store 앱 리뷰 실시간 수집
한국어 리뷰 자동 다운로드

실행 전 설치:
pip install google-play-scraper

사용법:
python src/etl/extractors/download_playstore_reviews.py --app "com.naver.shopping" --count 1000
"""

import pandas as pd
from google_play_scraper import app, reviews_all, Sort
from datetime import datetime
from pathlib import Path
import argparse


# 인기 한국 앱 목록 (추천)
POPULAR_KOREAN_APPS = {
    '쿠팡': 'com.coupang.mobile',
    '네이버쇼핑': 'com.nhn.android.search',
    '배달의민족': 'com.sampleapp',
    '마켓컬리': 'com.dmp.market.kurly',
    '11번가': 'com.skeletonapp.skplanet11st',
    '지마켓': 'kr.co.gmarket.mobile',
    '무신사': 'com.musinsa.store',
    '카카오톡': 'com.kakao.talk',
}


def get_app_info(app_id):
    """앱 정보 조회"""
    try:
        info = app(app_id, lang='ko', country='kr')
        print(f"\n📱 앱 정보:")
        print(f"   이름: {info.get('title', 'N/A')}")
        print(f"   카테고리: {info.get('genre', 'N/A')}")
        print(f"   평점: {info.get('score', 'N/A'):.2f}")
        print(f"   리뷰 수: {info.get('reviews', 'N/A'):,}개")
        return info
    except Exception as e:
        print(f"❌ 앱 정보 조회 실패: {e}")
        return None


def collect_reviews(app_id, count=1000, lang='ko', country='kr'):
    """
    Google Play Store 리뷰 수집
    
    Args:
        app_id: 앱 패키지명 (예: com.coupang.mobile)
        count: 수집할 리뷰 개수
        lang: 언어 (ko: 한국어)
        country: 국가 (kr: 한국)
    """
    print(f"\n📥 리뷰 수집 시작...")
    print(f"   앱 ID: {app_id}")
    print(f"   목표 개수: {count:,}개")
    print(f"   언어: {lang}, 국가: {country}\n")
    
    try:
        # 리뷰 수집
        result = reviews_all(
            app_id,
            sleep_milliseconds=0,  # 요청 간 대기 시간
            lang=lang,
            country=country,
            sort=Sort.NEWEST,  # 최신순
        )
        
        if count and len(result) > count:
            result = result[:count]
        
        print(f"✅ 수집 완료: {len(result):,}개\n")
        
        return result
        
    except Exception as e:
        print(f"❌ 리뷰 수집 실패: {e}")
        return []


def convert_to_csv(reviews, app_name, output_dir='data/bronze/playstore'):
    """리뷰를 CSV 형식으로 변환"""
    
    if not reviews:
        print("❌ 변환할 리뷰가 없습니다.")
        return None
    
    print(f"🔄 CSV 변환 중...")
    
    # 데이터프레임 생성
    df = pd.DataFrame(reviews)
    
    # 프로젝트 형식으로 변환
    df_converted = pd.DataFrame({
        'review_id': [f"PLAY_{app_name}_{i:06d}" for i in range(len(df))],
        'source': 'google_play',
        'created_date': pd.to_datetime(df['at']).dt.date,
        'review_content': df['content'],
        'rating': df['score'],
        'author_masked': df['userName'].apply(lambda x: x[0] + '*' * (len(x)-1) if x else '익명'),
        'product_category': app_name,
    })
    
    # 필터링
    df_converted = df_converted.dropna(subset=['review_content'])
    df_converted = df_converted[df_converted['review_content'].str.len() >= 10]
    
    # 저장
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_file = f"{output_dir}/reviews_{app_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    df_converted.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ CSV 저장 완료!")
    print(f"   - 원본: {len(reviews):,}개")
    print(f"   - 필터링 후: {len(df_converted):,}개")
    print(f"   - 파일: {output_file}")
    
    # 샘플 출력
    print(f"\n📋 샘플 데이터 (상위 3개):")
    print(df_converted.head(3)[['created_date', 'rating', 'review_content']])
    
    # 통계
    print(f"\n📊 데이터 통계:")
    print(f"   평균 평점: {df_converted['rating'].mean():.2f}")
    print(f"   평균 길이: {df_converted['review_content'].str.len().mean():.1f}자")
    print(f"   날짜 범위: {df_converted['created_date'].min()} ~ {df_converted['created_date'].max()}")
    
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Google Play Store 리뷰 수집')
    parser.add_argument('--app', type=str, help='앱 패키지명 또는 한글명')
    parser.add_argument('--count', type=int, default=1000, help='수집할 리뷰 개수 (기본: 1000)')
    parser.add_argument('--list', action='store_true', help='인기 앱 목록 출력')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📱 Google Play Store 리뷰 수집 도구")
    print("=" * 60)
    
    # 인기 앱 목록 출력
    if args.list or not args.app:
        print("\n🔥 추천 앱 목록:")
        for i, (name, package) in enumerate(POPULAR_KOREAN_APPS.items(), 1):
            print(f"   {i}. {name}: {package}")
        
        if not args.app:
            print("\n사용 예시:")
            print(f"python {__file__} --app com.coupang.mobile --count 1000")
            print(f"또는")
            print(f"python {__file__} --app 쿠팡 --count 1000")
            return
    
    # 앱 ID 변환 (한글명 → 패키지명)
    app_id = args.app
    app_name = args.app
    
    if args.app in POPULAR_KOREAN_APPS:
        app_id = POPULAR_KOREAN_APPS[args.app]
        app_name = args.app
    elif args.app in POPULAR_KOREAN_APPS.values():
        # 패키지명에서 앱 이름 찾기
        for name, package in POPULAR_KOREAN_APPS.items():
            if package == args.app:
                app_name = name
                break
    
    # 앱 정보 조회
    app_info = get_app_info(app_id)
    
    if not app_info:
        print("\n❌ 유효하지 않은 앱 ID입니다.")
        print("--list 옵션으로 추천 앱 목록을 확인하세요.")
        return
    
    # 리뷰 수집
    reviews = collect_reviews(app_id, count=args.count)
    
    if reviews:
        # CSV 변환
        output_file = convert_to_csv(reviews, app_name)
        
        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. 데이터 검증:")
        print(f"   python src/etl/extractors/validate_smartstore_csv.py")
        print(f"   → 경로 입력: {output_file}")
        print("\n2. DB 적재:")
        print(f"   python src/etl/extractors/csv_loader.py")


if __name__ == "__main__":
    # 필수 패키지 확인
    try:
        from google_play_scraper import app, reviews_all, Sort
    except ImportError:
        print("❌ google-play-scraper 패키지가 설치되지 않았습니다.")
        print("설치 명령: pip install google-play-scraper")
        exit(1)
    
    main()
