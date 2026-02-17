"""
Amazon Review Dataset 다운로드
Julian McAuley 교수의 공개 데이터셋

데이터셋 정보:
- 출처: UCSD (University of California, San Diego)
- 규모: 수백만 건 (카테고리별)
- 언어: 영어
- 기간: 1996-2018
- 라이선스: 학술/연구용 공개

카테고리:
- Electronics (전자제품)
- Clothing (의류)
- Books (도서)
- Home & Kitchen (가정용품)
- 등 30개 이상
"""

import requests
import gzip
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import argparse


# Amazon Review 데이터셋 URL
AMAZON_DATASETS = {
    'electronics': {
        'name': 'Electronics',
        'url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Electronics.jsonl.gz',
        'size': '약 700만 건',
        'sample_url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Electronics_sample.jsonl.gz',
    },
    'clothing': {
        'name': 'Clothing, Shoes and Jewelry',
        'url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Clothing_Shoes_and_Jewelry.jsonl.gz',
        'size': '약 1,000만 건',
        'sample_url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Clothing_sample.jsonl.gz',
    },
    'home': {
        'name': 'Home and Kitchen',
        'url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Home_and_Kitchen.jsonl.gz',
        'size': '약 500만 건',
        'sample_url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Home_sample.jsonl.gz',
    },
    'beauty': {
        'name': 'Beauty and Personal Care',
        'url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Beauty_and_Personal_Care.jsonl.gz',
        'size': '약 700만 건',
        'sample_url': 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Beauty_sample.jsonl.gz',
    },
}


def print_amazon_datasets():
    """사용 가능한 Amazon 데이터셋 출력"""
    print("\n📦 Amazon Review 데이터셋 목록:\n")
    
    for key, info in AMAZON_DATASETS.items():
        print(f"🔹 {info['name']}")
        print(f"   키: {key}")
        print(f"   규모: {info['size']}")
        print()
    
    print("💡 샘플 데이터셋으로 먼저 테스트하는 것을 권장합니다!")


def download_file(url, output_path, chunk_size=8192):
    """파일 다운로드 (진행률 표시)"""
    
    print(f"\n📥 다운로드 중: {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f, tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=Path(output_path).name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        print(f"✅ 다운로드 완료: {output_path}")
        return output_path
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ 다운로드 실패 (HTTP 오류): {e}")
        print("⚠️  URL이 변경되었을 수 있습니다. 공식 사이트를 확인하세요:")
        print("   https://cseweb.ucsd.edu/~jmcauley/datasets.html")
        return None
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        return None


def extract_gz(gz_path, output_jsonl=None):
    """GZIP 압축 해제"""
    
    if not output_jsonl:
        output_jsonl = str(gz_path).replace('.gz', '')
    
    print(f"\n📦 압축 해제 중: {gz_path}")
    
    try:
        with gzip.open(gz_path, 'rb') as f_in:
            with open(output_jsonl, 'wb') as f_out:
                f_out.write(f_in.read())
        
        print(f"✅ 압축 해제 완료: {output_jsonl}")
        return output_jsonl
        
    except Exception as e:
        print(f"❌ 압축 해제 실패: {e}")
        return None


def convert_amazon_to_standard(jsonl_path, output_csv, max_rows=None):
    """
    Amazon JSONL을 프로젝트 표준 형식으로 변환
    
    Amazon 데이터 구조:
    {
        "rating": 5.0,
        "text": "Great product!",
        "timestamp": 1234567890,
        "asin": "B001...",
        ...
    }
    """
    
    print(f"\n🔄 데이터 변환 중: {jsonl_path}")
    
    reviews = []
    
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if max_rows and i >= max_rows:
                    break
                
                try:
                    data = json.loads(line)
                    reviews.append({
                        'review_id': f"AMZN_{data.get('asin', 'unknown')}_{i:08d}",
                        'source': 'amazon',
                        'created_date': pd.to_datetime(data.get('timestamp', 0), unit='s').date(),
                        'review_content': data.get('text', ''),
                        'rating': data.get('rating', 0),
                        'author_masked': '익명',
                        'product_category': 'Amazon',
                    })
                except:
                    continue
                
                if i % 100000 == 0 and i > 0:
                    print(f"   처리 중: {i:,}개...")
        
        print(f"✅ 읽기 완료: {len(reviews):,}개")
        
        # DataFrame 변환
        df = pd.DataFrame(reviews)
        
        # 데이터 정제
        df = df.dropna(subset=['review_content'])
        df = df[df['review_content'].str.len() >= 10]
        df = df[df['rating'] > 0]
        
        # 저장
        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
        print(f"✅ 변환 완료!")
        print(f"   - 원본: {len(reviews):,}개")
        print(f"   - 정제 후: {len(df):,}개")
        print(f"   - 저장: {output_csv}")
        
        # 샘플 출력
        print(f"\n📋 샘플 데이터:")
        print(df.head(3)[['created_date', 'rating', 'review_content']])
        
        # 통계
        print(f"\n📊 통계:")
        print(f"   평균 평점: {df['rating'].mean():.2f}")
        print(f"   평균 길이: {df['review_content'].str.len().mean():.1f}자")
        print(f"   날짜 범위: {df['created_date'].min()} ~ {df['created_date'].max()}")
        
        return output_csv
        
    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='Amazon Review 데이터셋 다운로드')
    parser.add_argument('--category', type=str, choices=list(AMAZON_DATASETS.keys()) + ['list'],
                       help='카테고리 선택 (list: 목록 출력)')
    parser.add_argument('--sample', action='store_true', help='샘플 데이터셋 다운로드 (빠름)')
    parser.add_argument('--max-rows', type=int, help='최대 변환 행 수 (메모리 절약)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🌎 Amazon Review 데이터셋 다운로드")
    print("=" * 70)
    
    if not args.category or args.category == 'list':
        print_amazon_datasets()
        print("\n사용 예시:")
        print("  python download_amazon_reviews.py --category electronics --sample")
        print("  python download_amazon_reviews.py --category clothing --max-rows 50000")
        return
    
    dataset = AMAZON_DATASETS[args.category]
    
    print(f"\n📦 선택된 데이터셋: {dataset['name']}")
    print(f"규모: {dataset['size']}")
    
    # URL 선택 (샘플 또는 전체)
    url = dataset['sample_url'] if args.sample else dataset['url']
    filename = f"{args.category}_{'sample' if args.sample else 'full'}.jsonl.gz"
    
    # 다운로드
    output_dir = 'data/bronze/amazon'
    gz_path = Path(output_dir) / filename
    
    if not gz_path.exists():
        downloaded = download_file(url, gz_path)
        if not downloaded:
            return
    else:
        print(f"\n✅ 파일이 이미 존재합니다: {gz_path}")
    
    # 압축 해제
    jsonl_path = str(gz_path).replace('.gz', '')
    
    if not Path(jsonl_path).exists():
        extracted = extract_gz(gz_path, jsonl_path)
        if not extracted:
            return
    else:
        print(f"\n✅ 압축 해제된 파일이 이미 존재합니다: {jsonl_path}")
    
    # CSV 변환
    output_csv = f"{output_dir}/reviews_{args.category}_{'sample' if args.sample else 'full'}.csv"
    
    convert_amazon_to_standard(jsonl_path, output_csv, max_rows=args.max_rows)
    
    print("\n" + "=" * 70)
    print("✅ 모든 작업 완료!")
    print("=" * 70)
    print("\n다음 단계:")
    print(f"  python src/etl/extractors/validate_smartstore_csv.py")
    print(f"  → 경로: {output_csv}")


if __name__ == "__main__":
    main()
