"""필터링 규칙 중앙 관리"""

# 유머 키워드
HUMOR_KEYWORDS = [
    'ㅋㅋ', 'ㅎㅎ', 'ㅋ', 'ㅎ',
    '웃겨', '웃김', '빵터', '빵 터', '웃음',
    '농담', '반전', '깜짝', '놀랐',
    '재미', '재밌', '꿀잼'
]

# 긍정 키워드
POSITIVE_KEYWORDS = [
    '감사', '고마워', '고맙', '최고',
    '따뜻', '감동', '행복', '좋아',
    '추천', '강추', '만족', '대만족',
    '완벽', '훌륭', '멋져', '좋네'
]

# CS 리스크 키워드 (제외)
CS_RISK_KEYWORDS = [
    '환불', '교환', '파손', '불량',
    '이상', '문제', '고장', '안됨',
    '최악', '화', '실망', '짜증'
]

# 욕설/비속어 (제외)
PROFANITY_KEYWORDS = [
    '시발', '씨발', '병신', '개새',
    '지랄', '좆', '빙신'
]

# 필터링 설정
HUMOR_FILTER_CONFIG = {
    'min_length': 20,
    'max_length': 200,
    'min_score_threshold': 70,
    'sample_size': 5,
}

POSITIVE_FILTER_CONFIG = {
    'min_rating': 4.5,
    'min_score_threshold': 80,
    'top_percent': 20,
}
