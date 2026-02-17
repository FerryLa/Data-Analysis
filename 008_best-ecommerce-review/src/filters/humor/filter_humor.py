"""유머 필터링 로직"""
import sqlite3
import sys
sys.path.append('../..')
from config.filter_rules import HUMOR_KEYWORDS, CS_RISK_KEYWORDS, PROFANITY_KEYWORDS

def filter_humor_reviews(db_path='review.db', target_date=None):
    """유머 리뷰 필터링"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 전날 리뷰 중 유머 키워드 포함된 것 추출
    query = """
        SELECT r.id, r.review_content, r.rating
        FROM raw_reviews r
        LEFT JOIN cleaned_reviews c ON r.id = c.raw_review_id
        WHERE c.id IS NULL  -- 아직 처리 안 된 것만
        AND r.created_date = ?
        AND LENGTH(r.review_content) BETWEEN 20 AND 200
    """
    
    cursor.execute(query, (target_date,))
    rows = cursor.fetchall()
    
    filtered = []
    for row in rows:
        content = row[1]
        
        # 유머 키워드 체크
        has_humor = any(kw in content for kw in HUMOR_KEYWORDS)
        # CS 리스크 체크
        has_risk = any(kw in content for kw in CS_RISK_KEYWORDS)
        # 욕설 체크
        has_profanity = any(kw in content for kw in PROFANITY_KEYWORDS)
        
        if has_humor and not has_risk and not has_profanity:
            filtered.append(row)
    
    print(f"✅ Filtered {len(filtered)} humor reviews from {len(rows)} total")
    conn.close()
    return filtered

if __name__ == "__main__":
    from datetime import date, timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    filter_humor_reviews(target_date=yesterday)
