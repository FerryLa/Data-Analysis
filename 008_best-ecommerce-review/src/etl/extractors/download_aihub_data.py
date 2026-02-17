"""
AI Hub 한국어 쇼핑 리뷰 데이터 다운로드
최고 품질의 한국어 이커머스 리뷰 데이터

데이터셋 정보:
- 출처: AI Hub (한국지능정보사회진흥원)
- 규모: 10만~100만 건
- 언어: 한국어
- 품질: 높음 (검증됨)
- 라이선스: 공공누리 (연구/상업 가능)

주요 데이터셋:
1. 쇼핑 리뷰 감성 분석 데이터
2. 온라인 쇼핑 상품평 데이터
3. 소비자 리뷰 데이터
"""

import os
import requests
import zipfile
from pathlib import Path
import pandas as pd
import json

# AI Hub 주요 쇼핑 리뷰 데이터셋
AIHUB_DATASETS = {
    '쇼핑_리뷰_감성분석': {
        'id': '71',
        'name': '쇼핑 리뷰 감성 분석 데이터',
        'size': '약 100만 건',
        'url': 'https://aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&aihubDataSe=realm&dataSetSn=71',
        'description': '온라인 쇼핑몰 상품 리뷰 + 감성 라벨',
    },
    '쇼핑몰_상품평': {
        'id': '96',
        'name': '온라인 쇼핑 상품평 데이터',
        'size': '약 50만 건',
        'url': 'https://aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&aihubDataSe=realm&dataSetSn=96',
        'description': '카테고리별 상품평 + 평점',
    }
}


def print_aihub_guide():
    """AI Hub 다운로드 가이드 출력"""
    
    print("=" * 70)
    print("📚 AI Hub 한국어 쇼핑 리뷰 데이터 다운로드 가이드")
    print("=" * 70)
    print()
    
    print("🎯 추천 데이터셋:\n")
    for key, info in AIHUB_DATASETS.items():
        print(f"📦 {info['name']}")
        print(f"   - ID: {info['id']}")
        print(f"   - 규모: {info['size']}")
        print(f"   - 설명: {info['description']}")
        print(f"   - URL: {info['url']}")
        print()
    
    print("=" * 70)
    print("📥 다운로드 방법 (수동)")
    print("=" * 70)
    print()
    print("1️⃣ AI Hub 회원가입")
    print("   https://aihub.or.kr/join/join.do")
    print("   → 무료 회원가입 (1분)")
    print()
    print("2️⃣ 로그인 후 데이터셋 페이지 접속")
    print("   위의 URL 중 하나 선택")
    print()
    print("3️⃣ 데이터 신청")
    print("   [데이터 신청] 버튼 클릭")
    print("   → 사용 목적 입력 (예: 개인 연구 프로젝트)")
    print("   → 신청 완료 (즉시 승인)")
    print()
    print("4️⃣ 다운로드")
    print("   [다운로드] 탭 클릭")
    print("   → Training/Validation 데이터 다운로드")
    print("   → ZIP 파일 저장")
    print()
    print("5️⃣ 압축 해제")
    print("   → data\\bronze\\aihub\\ 폴더에 압축 해제")
    print()
    print("=" * 70)
    print("⚡ 빠른 대안: 공공데이터포털")
    print("=" * 70)
    print()
    print("AI Hub 승인 대기 시간이 길 경우:")
    print("https://www.data.go.kr")
    print("→ '쇼핑 리뷰' 또는 '상품평' 검색")
    print("→ CSV/JSON 형식 데이터 즉시 다운로드 가능")
    print()


def extract_aihub_zip(zip_path, output_dir='data/bronze/aihub'):
    """AI Hub ZIP 파일 압축 해제"""
    
    print(f"\n📦 압축 해제 중: {zip_path}")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        print(f"✅ 압축 해제 완료: {output_dir}")
        
        # 압축 해제된 파일 목록
        files = list(Path(output_dir).rglob('*.json')) + list(Path(output_dir).rglob('*.csv'))
        
        print(f"\n📄 발견된 파일 ({len(files)}개):")
        for f in files[:10]:  # 처음 10개만
            print(f"   - {f.name}")
        
        if len(files) > 10:
            print(f"   ... 외 {len(files) - 10}개")
        
        return files
        
    except Exception as e:
        print(f"❌ 압축 해제 실패: {e}")
        return []


def convert_aihub_to_standard(input_file, output_csv='data/bronze/aihub/reviews_aihub.csv'):
    """
    AI Hub JSON/CSV를 프로젝트 표준 형식으로 변환
    
    AI Hub 일반적인 구조:
    {
        "id": "...",
        "review": "배송이 빨라요",
        "rating": 5,
        "category": "패션",
        "sentiment": "positive",
        ...
    }
    """
    
    print(f"\n🔄 데이터 변환 중: {input_file}")
    
    file_ext = Path(input_file).suffix.lower()
    
    try:
        # 파일 형식에 따라 읽기
        if file_ext == '.json':
            # JSON Lines 또는 일반 JSON
            try:
                # JSON Lines 시도
                df = pd.read_json(input_file, lines=True)
            except:
                # 일반 JSON 시도
                with open(input_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # {"data": [...]} 구조
                        df = pd.DataFrame(data.get('data', []))
                    else:
                        df = pd.DataFrame(data)
        
        elif file_ext == '.csv':
            df = pd.read_csv(input_file, encoding='utf-8-sig')
        
        else:
            print(f"⚠️  지원하지 않는 파일 형식: {file_ext}")
            return None
        
        print(f"✅ 파일 읽기 완료: {len(df):,}개")
        
        # 컬럼 자동 매핑 (유연하게)
        column_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower()
            
            # 리뷰 내용
            if any(x in col_lower for x in ['review', '리뷰', '내용', 'content', 'text', 'comment']):
                column_mapping['review_content'] = col
            
            # 평점
            elif any(x in col_lower for x in ['rating', '평점', 'score', 'star', '별점']):
                column_mapping['rating'] = col
            
            # 카테고리
            elif any(x in col_lower for x in ['category', '카테고리', 'type', '분류']):
                column_mapping['product_category'] = col
            
            # 날짜
            elif any(x in col_lower for x in ['date', '날짜', '일자', 'time', 'created']):
                column_mapping['created_date'] = col
        
        # 프로젝트 표준 형식으로 변환
        df_converted = pd.DataFrame({
            'review_id': [f"AIHUB_{i:08d}" for i in range(len(df))],
            'source': 'aihub',
            'created_date': df[column_mapping.get('created_date', df.columns[0])].iloc[:len(df)] if 'created_date' in column_mapping else pd.Timestamp.now().date(),
            'review_content': df[column_mapping.get('review_content', df.columns[0])],
            'rating': df[column_mapping.get('rating')] if 'rating' in column_mapping else 5.0,
            'author_masked': '익명',
            'product_category': df[column_mapping.get('product_category')] if 'product_category' in column_mapping else '기타',
        })
        
        # 데이터 정제
        df_converted = df_converted.dropna(subset=['review_content'])
        df_converted = df_converted[df_converted['review_content'].str.len() >= 5]
        
        # 저장
        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
        df_converted.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
        print(f"✅ 변환 완료!")
        print(f"   - 원본: {len(df):,}개")
        print(f"   - 변환 후: {len(df_converted):,}개")
        print(f"   - 저장: {output_csv}")
        
        # 샘플 출력
        print(f"\n📋 샘플 데이터:")
        print(df_converted.head(3)[['review_content', 'rating', 'product_category']])
        
        # 통계
        print(f"\n📊 통계:")
        print(f"   평균 평점: {df_converted['rating'].mean():.2f}")
        print(f"   평균 길이: {df_converted['review_content'].str.len().mean():.1f}자")
        
        return output_csv
        
    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """메인 실행"""
    
    print_aihub_guide()
    
    print("=" * 70)
    print("🔧 변환 도구")
    print("=" * 70)
    print()
    print("다운로드한 파일이 있으면 변환할 수 있습니다:")
    print()
    
    while True:
        file_path = input("파일 경로 입력 (종료: q): ").strip()
        
        if file_path.lower() == 'q':
            break
        
        if not file_path:
            continue
        
        if not Path(file_path).exists():
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}\n")
            continue
        
        # ZIP 파일인 경우 압축 해제
        if file_path.endswith('.zip'):
            extracted_files = extract_aihub_zip(file_path)
            if extracted_files:
                print("\n변환할 파일을 선택하세요:")
                for i, f in enumerate(extracted_files[:10], 1):
                    print(f"  {i}. {f.name}")
                
                try:
                    choice = int(input("\n번호 선택: "))
                    file_path = extracted_files[choice - 1]
                except:
                    print("❌ 잘못된 선택")
                    continue
        
        # 변환
        output = convert_aihub_to_standard(file_path)
        
        if output:
            print(f"\n✅ 변환 완료! 다음 단계:")
            print(f"   python src/etl/extractors/validate_smartstore_csv.py")
            print(f"   → 경로: {output}")
        
        print()


if __name__ == "__main__":
    main()
