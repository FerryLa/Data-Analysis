"""
마켓컬리 수집 실패 대체 및 추가 수집
대체 앱: 무신사, 지마켓, 배달의민족, 당근마켓
"""
import pandas as pd
from google_play_scraper import reviews, Sort
from datetime import datetime
from pathlib import Path
import time

SUPPLEMENT_APPS = [
    {"name": "musinsa", "id": "com.musinsa.store", "target": 1500, "label": "무신사"},
    {"name": "gmarket", "id": "com.ebay.kr.gmarket", "target": 1500, "label": "지마켓"},
    {"name": "baemin", "id": "com.sampleapp.baemin", "target": 1000, "label": "배달의민족"},
    {"name": "daangn", "id": "com.towneers.www", "target": 1000, "label": "당근마켓"},
]

OUTPUT_DIR = Path("data/bronze/playstore")


def collect_reviews_batch(app_id, target_count, label):
    all_reviews = []
    token = None

    print(f"\n{'='*60}")
    print(f"  {label} ({app_id}) - 목표: {target_count:,}개")
    print(f"{'='*60}")

    while len(all_reviews) < target_count:
        try:
            result, token = reviews(
                app_id, lang='ko', country='kr',
                sort=Sort.NEWEST, count=200,
                continuation_token=token,
            )
            if not result:
                print(f"  더 이상 리뷰 없음. 총 {len(all_reviews)}개.")
                break
            all_reviews.extend(result)
            print(f"  수집: {len(all_reviews):,}/{target_count:,}", end='\r')
            if token is None:
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"\n  오류: {e}")
            break

    all_reviews = all_reviews[:target_count]
    print(f"\n  수집 완료: {len(all_reviews):,}개")
    return all_reviews


def save_to_csv(reviews_list, app_name, label):
    if not reviews_list:
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

    before = len(df_out)
    df_out = df_out.dropna(subset=['review_content'])
    df_out = df_out[df_out['review_content'].str.len() >= 10]
    after = len(df_out)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime('%Y%m%d')
    filepath = OUTPUT_DIR / f"reviews_{app_name}_{today}.csv"
    df_out.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"  파일: {filepath} ({filepath.stat().st_size/1024:.1f} KB)")
    print(f"  원본: {before}개 -> 필터 후: {after}개")

    for idx, row in df_out.head(3).iterrows():
        preview = str(row['review_content'])[:50]
        print(f"    [{row['rating']}점] {row['created_date']} | {preview}")

    return str(filepath), after


def main():
    print("추가 앱 리뷰 수집 시작")

    # 현재까지 수집된 개수
    existing = 3637  # coupang 1513 + 11st 1247 + naver 877
    needed = 6000 - existing
    print(f"현재: {existing}개 수집됨, 추가 {needed}개 필요")

    total_added = 0
    for app in SUPPLEMENT_APPS:
        if total_added >= needed:
            break
        try:
            rvs = collect_reviews_batch(app['id'], app['target'], app['label'])
            result = save_to_csv(rvs, app['name'], app['label'])
            if result:
                total_added += result[1]
                print(f"  누적 추가: {total_added}개")
                if total_added >= needed:
                    print(f"\n  목표 달성! 총 {existing + total_added}개")
                    break
        except Exception as e:
            print(f"  {app['label']} 실패: {e}")
            continue

    print(f"\n최종 총 수집: {existing + total_added}개")


if __name__ == "__main__":
    main()
