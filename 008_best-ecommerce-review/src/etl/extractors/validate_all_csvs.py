"""수집된 CSV 파일 전체 검증"""
import pandas as pd
from pathlib import Path
import re

CSV_DIR = Path("data/bronze/playstore")
HUMOR_KEYWORDS = ['ㅋㅋ', 'ㅎㅎ', '웃겨', '웃긴', 'ㅋㅋㅋ', '빵터', '웃기', 'ㅋㅋㅋㅋ', '웃음', '재밌', '재미']
POSITIVE_KEYWORDS = ['감사', '추천', '좋아요', '최고', '만족', '편리', '굿', '짱', '대박', '사랑', '훌륭', '완벽']


def validate_csv(filepath):
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    name = filepath.stem

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  총 행 수: {len(df):,}")
    print(f"  컬럼: {list(df.columns)}")
    print(f"  평균 리뷰 길이: {df['review_content'].str.len().mean():.1f}자")
    print(f"  평균 평점: {df['rating'].mean():.2f}")
    print(f"  평점 분포:")
    for rating in sorted(df['rating'].unique()):
        count = len(df[df['rating'] == rating])
        print(f"    {rating}점: {count}개 ({count/len(df)*100:.1f}%)")

    # 유머 키워드
    humor_mask = df['review_content'].apply(
        lambda x: any(kw in str(x) for kw in HUMOR_KEYWORDS)
    )
    humor_count = humor_mask.sum()
    print(f"  유머 키워드 포함: {humor_count}개 ({humor_count/len(df)*100:.1f}%)")

    # 긍정 키워드
    positive_mask = df['review_content'].apply(
        lambda x: any(kw in str(x) for kw in POSITIVE_KEYWORDS)
    )
    positive_count = positive_mask.sum()
    print(f"  긍정 키워드 포함: {positive_count}개 ({positive_count/len(df)*100:.1f}%)")

    # NULL 검사
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        print(f"  NULL 값:")
        for col, cnt in null_counts.items():
            if cnt > 0:
                print(f"    {col}: {cnt}개")
    else:
        print(f"  NULL 값: 없음")

    return {
        'file': name,
        'rows': len(df),
        'avg_length': df['review_content'].str.len().mean(),
        'avg_rating': df['rating'].mean(),
        'humor_count': humor_count,
        'positive_count': positive_count,
    }


def main():
    print("=" * 60)
    print("  CSV 데이터 검증 리포트")
    print("=" * 60)

    csv_files = sorted(CSV_DIR.glob("*.csv"))
    results = []
    total_rows = 0
    total_humor = 0
    total_positive = 0

    for f in csv_files:
        r = validate_csv(f)
        results.append(r)
        total_rows += r['rows']
        total_humor += r['humor_count']
        total_positive += r['positive_count']

    print(f"\n{'='*60}")
    print(f"  전체 요약")
    print(f"{'='*60}")
    print(f"  파일 수: {len(csv_files)}")
    print(f"  총 리뷰: {total_rows:,}개")
    print(f"  유머 리뷰 후보: {total_humor:,}개")
    print(f"  긍정 리뷰 후보: {total_positive:,}개")


if __name__ == "__main__":
    main()
