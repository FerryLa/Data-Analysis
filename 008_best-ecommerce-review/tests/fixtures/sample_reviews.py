"""샘플 리뷰 데이터 생성"""
import random
from datetime import datetime, timedelta

def generate_sample_reviews(count=100):
    """샘플 리뷰 데이터 생성"""
    sources = ['smartstore', 'coupang', '11st']
    humor_templates = [
        "배송이 로켓보다 빠르네요 ㅋㅋㅋ",
        "포장이 너무 꼼꼼해서 열기 힘들었어요 ㅎㅎ 좋은 의미로!",
        "상품 설명이 시처럼 아름답네요 ㅋㅋ",
        "이 가격에 이 품질이면 반칙 아닌가요? ㅋㅋ",
    ]
    positive_templates = [
        "덕분에 하루가 따뜻했어요. 감사합니다.",
        "기대 이상이었습니다. 강력 추천합니다!",
        "정말 만족스러운 구매였습니다. 행복해요.",
        "완벽한 제품입니다. 주변에도 추천했어요.",
    ]
    
    reviews = []
    for i in range(count):
        is_humor = random.random() < 0.3
        template = random.choice(humor_templates if is_humor else positive_templates)
        
        review = {
            'review_id': f"SMT{datetime.now().strftime('%Y%m%d')}{i:04d}",
            'source': random.choice(sources),
            'created_date': (datetime.now() - timedelta(days=random.randint(0, 30))).date(),
            'review_content': template,
            'rating': round(random.uniform(4.0, 5.0), 1),
            'author_masked': f"고객{i}",
            'product_category': random.choice(['패션', '가전', '식품', '생활']),
        }
        reviews.append(review)
    
    return reviews

if __name__ == "__main__":
    reviews = generate_sample_reviews(100)
    for r in reviews[:5]:
        print(r)
