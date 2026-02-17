"""6개 CSV 파일을 PostgreSQL raw_reviews 테이블에 일괄 적재"""
import os
import psycopg
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

PG_CONFIG = {
    'host': os.getenv('PG_HOST', 'localhost'),
    'port': int(os.getenv('PG_PORT', 5432)),
    'dbname': os.getenv('PG_DATABASE', 'review_db'),
    'user': os.getenv('PG_USER', 'n8n_user'),
    'password': os.getenv('PG_PASSWORD', ''),
}

CSV_DIR = Path("data/bronze/playstore")


def load_all_csvs():
    conn = psycopg.connect(**PG_CONFIG, autocommit=False)
    cur = conn.cursor()
    csv_files = sorted(CSV_DIR.glob("*.csv"))

    print(f"DB: {PG_CONFIG['dbname']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}")
    print(f"CSV 파일: {len(csv_files)}개\n")

    total_inserted = 0
    total_skipped = 0

    for csv_file in csv_files:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO raw_reviews
                    (review_id, source, created_date, review_content, rating, author_masked, product_category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (review_id) DO NOTHING
                """, (
                    row['review_id'],
                    row['source'],
                    row['created_date'],
                    row['review_content'],
                    float(row['rating']),
                    row['author_masked'],
                    row['product_category'],
                ))
                if cur.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  오류: {e} (review_id={row.get('review_id', 'N/A')})")
                conn.rollback()
                skipped += 1

        conn.commit()
        total_inserted += inserted
        total_skipped += skipped
        print(f"  {csv_file.name}: {inserted}개 INSERT, {skipped}개 중복/스킵")

    # audit_log에 기록
    cur.execute("""
        INSERT INTO audit_log (action, table_name, details)
        VALUES (%s, %s, %s)
    """, (
        'BULK_INSERT',
        'raw_reviews',
        f'총 {total_inserted}건 적재, {total_skipped}건 스킵 ({datetime.now()})'
    ))
    conn.commit()

    # 통계 출력
    print(f"\n{'='*50}")
    print(f"적재 결과")
    print(f"{'='*50}")

    cur.execute("SELECT COUNT(*) FROM raw_reviews")
    total = cur.fetchone()[0]
    print(f"총 적재: {total:,}건")

    cur.execute("""
        SELECT product_category, COUNT(*) as cnt,
               AVG(rating) as avg_rating,
               AVG(LENGTH(review_content)) as avg_len
        FROM raw_reviews
        GROUP BY product_category
        ORDER BY cnt DESC
    """)
    stats = cur.fetchall()

    print(f"\n앱별 통계:")
    for cat, cnt, avg_r, avg_l in stats:
        print(f"  {cat}: {cnt:,}건 | 평균평점: {avg_r:.2f} | 평균길이: {avg_l:.0f}자")

    cur.close()
    conn.close()


if __name__ == "__main__":
    load_all_csvs()
