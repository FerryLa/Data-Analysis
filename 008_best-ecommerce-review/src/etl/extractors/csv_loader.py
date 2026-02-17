"""CSV 데이터 추출 및 PostgreSQL 적재"""
import os
import psycopg
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import sys
sys.path.append('../..')
from config.filter_rules import CS_RISK_KEYWORDS, PROFANITY_KEYWORDS

load_dotenv(encoding='utf-8')

PG_CONFIG = {
    'host': os.getenv('PG_HOST', 'localhost'),
    'port': int(os.getenv('PG_PORT', 5432)),
    'dbname': os.getenv('PG_DATABASE', 'review_db'),
    'user': os.getenv('PG_USER', 'n8n_user'),
    'password': os.getenv('PG_PASSWORD', ''),
}


def load_csv_to_db(csv_path, source='smartstore', pg_config=None):
    """CSV 파일을 PostgreSQL에 적재"""
    if pg_config is None:
        pg_config = PG_CONFIG

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    conn = psycopg.connect(**pg_config, autocommit=False)
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for idx, row in df.iterrows():
        author_masked = mask_author(row.get('작성자', '익명'))
        review_id = f"{source.upper()}_{datetime.now().strftime('%Y%m%d')}_{idx}"

        try:
            cur.execute("""
                INSERT INTO raw_reviews
                (review_id, source, created_date, review_content, rating, author_masked, product_category)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (review_id) DO NOTHING
            """, (
                review_id,
                source,
                row['작성일'],
                row['리뷰내용'],
                row.get('평점', None),
                author_masked,
                row.get('카테고리', None)
            ))
            inserted += 1
        except Exception as e:
            print(f"  오류: {e} (review_id={review_id})")
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Loaded {inserted} reviews from {csv_path} ({skipped} skipped)")


def mask_author(name):
    """작성자명 마스킹"""
    if not name or len(name) < 2:
        return "익명"
    return name[0] + "*" * (len(name) - 1)


if __name__ == "__main__":
    load_csv_to_db('data/bronze/smartstore/reviews_20250208.csv', 'smartstore')
