"""
스마트스토어 CSV 파일 검증 및 전처리
실행: python src/etl/extractors/validate_smartstore_csv.py
"""

import pandas as pd
import os
from datetime import datetime

def validate_smartstore_csv(csv_path):
    """
    스마트스토어 CSV 파일 검증
    """
    print(f"📂 파일 경로: {csv_path}")
    print(f"📊 파일 존재 여부: {os.path.exists(csv_path)}\n")
    
    if not os.path.exists(csv_path):
        print("❌ 파일을 찾을 수 없습니다!")
        print(f"경로를 확인하세요: {csv_path}")
        return False
    
    # CSV 읽기 (여러 인코딩 시도)
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
    df = None
    
    for enc in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            print(f"✅ 파일 읽기 성공 (인코딩: {enc})\n")
            break
        except Exception as e:
            continue
    
    if df is None:
        print("❌ 파일을 읽을 수 없습니다. 인코딩 문제일 수 있습니다.")
        return False
    
    # 기본 정보
    print("=" * 60)
    print("📊 데이터 기본 정보")
    print("=" * 60)
    print(f"총 행 수: {len(df):,}개")
    print(f"총 컬럼 수: {len(df.columns)}개\n")
    
    # 컬럼명 출력
    print("컬럼 목록:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    print()
    
    # 필수 컬럼 매핑 시도
    print("=" * 60)
    print("🔍 필수 컬럼 매핑")
    print("=" * 60)
    
    column_mapping = {
        '작성일': None,
        '리뷰내용': None,
        '평점': None,
        '작성자': None,
        '상품명': None,
    }
    
    # 자동 매핑 시도
    for required_col in column_mapping.keys():
        for actual_col in df.columns:
            if required_col in actual_col or \
               ('작성일' in required_col and any(x in actual_col for x in ['일자', '날짜', '등록', 'date'])) or \
               ('리뷰' in required_col and any(x in actual_col for x in ['내용', '평', '리뷰', 'review', 'content'])) or \
               ('평점' in required_col and any(x in actual_col for x in ['별점', '만족', 'rating', 'score'])) or \
               ('작성자' in required_col and any(x in actual_col for x in ['구매자', '닉네임', '회원', 'author', 'user'])) or \
               ('상품' in required_col and any(x in actual_col for x in ['상품', 'product', '제품'])):
                column_mapping[required_col] = actual_col
                break
    
    # 매핑 결과 출력
    for req, actual in column_mapping.items():
        status = "✅" if actual else "❌"
        print(f"{status} {req}: {actual if actual else '찾을 수 없음'}")
    
    print()
    
    # 샘플 데이터 출력
    print("=" * 60)
    print("📄 샘플 데이터 (상위 5개)")
    print("=" * 60)
    print(df.head(5).to_string())
    print()
    
    # 데이터 품질 체크
    print("=" * 60)
    print("✅ 데이터 품질 체크")
    print("=" * 60)
    
    if column_mapping['리뷰내용']:
        review_col = column_mapping['리뷰내용']
        null_count = df[review_col].isnull().sum()
        empty_count = (df[review_col] == '').sum()
        print(f"리뷰 NULL 개수: {null_count}")
        print(f"리뷰 빈 값 개수: {empty_count}")
        print(f"평균 리뷰 길이: {df[review_col].fillna('').str.len().mean():.1f}자")
        print(f"최소 리뷰 길이: {df[review_col].fillna('').str.len().min()}자")
        print(f"최대 리뷰 길이: {df[review_col].fillna('').str.len().max()}자")
    
    print()
    
    if column_mapping['평점']:
        rating_col = column_mapping['평점']
        print(f"평균 평점: {df[rating_col].mean():.2f}")
        print(f"평점 분포:")
        print(df[rating_col].value_counts().sort_index())
    
    print()
    
    # 권장 사항
    print("=" * 60)
    print("💡 권장 사항")
    print("=" * 60)
    
    if len(df) < 100:
        print("⚠️  리뷰 개수가 100개 미만입니다. 더 많은 데이터를 수집하는 것이 좋습니다.")
    elif len(df) < 1000:
        print("✅ 리뷰 개수가 적절합니다. (테스트 가능)")
    else:
        print("✅ 리뷰 개수가 충분합니다. (프로덕션 가능)")
    
    print()
    
    if not all(column_mapping.values()):
        print("⚠️  일부 필수 컬럼이 없습니다.")
        print("   → src/config/column_mapping.py 파일을 생성하여 수동 매핑이 필요합니다.")
    else:
        print("✅ 모든 필수 컬럼이 확인되었습니다.")
    
    print()
    
    # 컬럼 매핑 파일 생성 제안
    if all(column_mapping.values()):
        mapping_code = f"""
# src/config/column_mapping.py
# 자동 생성된 컬럼 매핑

SMARTSTORE_COLUMN_MAPPING = {{
    'review_id': None,  # 수동 생성
    'source': 'smartstore',
    'created_date': '{column_mapping['작성일']}',
    'review_content': '{column_mapping['리뷰내용']}',
    'rating': '{column_mapping['평점']}',
    'author_masked': '{column_mapping['작성자']}',
    'product_category': '{column_mapping['상품명']}',
}}
"""
        print("=" * 60)
        print("📝 자동 생성된 컬럼 매핑 코드")
        print("=" * 60)
        print(mapping_code)
        
        # 파일로 저장
        mapping_file = "src/config/column_mapping.py"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            f.write(mapping_code)
        print(f"✅ 매핑 파일 저장: {mapping_file}")
    
    return True


def main():
    """메인 실행"""
    print("=" * 60)
    print("🔍 스마트스토어 CSV 검증 도구")
    print("=" * 60)
    print()
    
    # CSV 파일 경로 입력
    csv_path = input("CSV 파일 경로를 입력하세요 (예: data/bronze/smartstore/reviews.csv): ").strip()
    
    if not csv_path:
        csv_path = "data/bronze/smartstore/reviews_20250208.csv"
        print(f"기본 경로 사용: {csv_path}")
    
    print()
    validate_smartstore_csv(csv_path)
    
    print()
    print("=" * 60)
    print("✅ 검증 완료!")
    print("=" * 60)
    print()
    print("다음 단계:")
    print("1. 컬럼 매핑이 정확한지 확인")
    print("2. python src/etl/extractors/csv_loader.py 실행")
    print("3. DB에 데이터 적재 확인")


if __name__ == "__main__":
    main()
