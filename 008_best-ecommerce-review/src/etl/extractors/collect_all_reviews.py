"""
4개 한국 이커머스 앱에서 Google Play Store 리뷰를 순차적으로 수집
총 목표: 6,000개
"""
import pandas as pd
from google_play_scraper import reviews, Sort
from datetime import datetime
from pathlib import Path
import time
import sys

APPS = [
    {"name": "coupang", "id": "com.coupang.mobile", "target": 2000, "label": "쿠팡"},
    {"name": "11st", "id": "com.elevenst.deals", "target": 2000, "label": "11번가"},
    {"name": "navershopping", "id": "com.nhn.android.search", "target": 1000, "label": "네이버쇼핑"},
    {"name": "kurly", "id": "com.dmp.market.kurly", "target": 1000, "label": "마켓컬리"},
]

OUTPUT_DIR = Path("data/bronze/playstore")


def collect_reviews_batch(app_id, target_count, label):
    """배치 방식으로 리뷰를 수집 (reviews_all 대신 pagination 사용)"""
    all_reviews = []
    token = None
    batch_size = 200

    print(f"\n{'='*60}")
    print(f"  {label} ({app_id}) - 목표: {target_count:,}개")
    print(f"{'='*60}")

    while len(all_reviews) < target_count:
        try:
            result, token = reviews(
                app_id,
                lang='ko',
                country='kr',
                sort=Sort.NEWEST,
                count=batch_size,
                continuation_token=token,
            )
            if not result:
                print(f"  더 이상 리뷰 없음. 총 {len(all_reviews)}개 수집.")
                break

            all_reviews.extend(result)
            print(f"  수집 진행: {len(all_reviews):,}/{target_count:,}", end='\r')

            if token is None:
                break
            time.sleep(0.5)

        except Exception as e:
            print(f"\n  오류 발생: {e}")
            if len(all_reviews) > 0:
                print(f"  현재까지 {len(all_reviews)}개 수집됨. 이어서 진행.")
                break
            else:
                raise

    all_reviews = all_reviews[:target_count]
    print(f"\n  수집 완료: {len(all_reviews):,}개")
    return all_reviews


def save_to_csv(reviews_list, app_name, label):
    """리뷰를 CSV로 저장"""
    if not reviews_list:
        print(f"  {label}: 저장할 리뷰가 없습니다.")
        return None

    df = pd.DataFrame(reviews_list)

    df_out = pd.DataFrame({
        'review_id': [f"PLAY_{app_name}_{i:06d}" for i in range(len(df))],
        'source': 'google_play',
        'created_date': pd.to_datetime(df['at']).dt.strftime('%Y-%m-%d'),
        'review_content': df['content'],
        'rating': df['score'],
        'author_masked': df['userName'].apply(
            lambda x: x[0] + '*' * (len(str(x)) - 1) if x and len(str(x)) > 0 else '익명'
        ),
        'product_category': label,
    })

    # 필터링: NULL 제거, 10자 미만 제거
    before = len(df_out)
    df_out = df_out.dropna(subset=['review_content'])
    df_out = df_out[df_out['review_content'].str.len() >= 10]
    after = len(df_out)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime('%Y%m%d')
    filepath = OUTPUT_DIR / f"reviews_{app_name}_{today}.csv"
    df_out.to_csv(filepath, index=False, encoding='utf-8-sig')

    file_size = filepath.stat().st_size / 1024
    print(f"  파일 저장: {filepath}")
    print(f"  파일 크기: {file_size:.1f} KB")
    print(f"  원본: {before}개 -> 필터 후: {after}개")

    # 샘플 3개 출력
    print(f"\n  샘플 데이터 (3개):")
    for idx, row in df_out.head(3).iterrows():
        content_preview = row['review_content'][:50] + '...' if len(str(row['review_content'])) > 50 else row['review_content']
        print(f"    [{row['rating']}점] {row['created_date']} | {content_preview}")

    return filepath, df_out


def main():
    print("=" * 60)
    print("  Google Play Store 한국 이커머스 리뷰 수집")
    print(f"  실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}
    total_collected = 0

    for app_info in APPS:
        try:
            reviews_list = collect_reviews_batch(
                app_info['id'], app_info['target'], app_info['label']
            )
            result = save_to_csv(reviews_list, app_info['name'], app_info['label'])
            if result:
                filepath, df = result
                results[app_info['label']] = {
                    'file': str(filepath),
                    'count': len(df),
                    'avg_rating': df['rating'].mean(),
                    'avg_length': df['review_content'].str.len().mean(),
                }
                total_collected += len(df)
        except Exception as e:
            print(f"\n  {app_info['label']} 수집 실패: {e}")
            results[app_info['label']] = {'error': str(e)}

    # 최종 요약
    print(f"\n{'='*60}")
    print(f"  수집 완료 요약")
    print(f"{'='*60}")
    print(f"  총 수집 리뷰: {total_collected:,}개")
    for label, info in results.items():
        if 'error' in info:
            print(f"  {label}: 실패 - {info['error']}")
        else:
            print(f"  {label}: {info['count']:,}개 | 평균평점: {info['avg_rating']:.2f} | 평균길이: {info['avg_length']:.0f}자")


if __name__ == "__main__":
    main()
