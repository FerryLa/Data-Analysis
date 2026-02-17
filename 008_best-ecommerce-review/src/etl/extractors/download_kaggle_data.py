"""
Kaggle Women's E-Commerce Clothing Reviews 다운로드
즉시 사용 가능한 공개 데이터셋

실행 전 준비:
1. Kaggle 계정 생성: https://www.kaggle.com/account/login
2. API Token 발급: https://www.kaggle.com/settings/account
   → "Create New API Token" 클릭 → kaggle.json 다운로드
3. kaggle.json을 ~/.kaggle/ 폴더에 복사
"""

import os
import subprocess
import pandas as pd
from pathlib import Path

def setup_kaggle():
    """Kaggle API 설정 확인"""
    kaggle_dir = Path.home() / '.kaggle'
    kaggle_json = kaggle_dir / 'kaggle.json'
    
    print("🔍 Kaggle API 설정 확인...")
    
    if not kaggle_json.exists():
        print("\n❌ Kaggle API 설정이 필요합니다!")
        print("\n📝 설정 방법:")
        print("1. https://www.kaggle.com/settings/account 접속")
        print("2. 'Create New API Token' 클릭")
        print("3. 다운로드된 kaggle.json을 다음 위치에 저장:")
        print(f"   {kaggle_dir}")
        print("\nWindows 예시:")
        print(f"   C:\\Users\\YourName\\.kaggle\\kaggle.json")
        return False
    
    print("✅ Kaggle API 설정 완료\n")
    return True


def download_kaggle_dataset():
    """Kaggle 데이터셋 다운로드"""
    
    if not setup_kaggle():
        return None
    
    # 데이터셋 정보
    dataset_name = "nicapotato/womens-ecommerce-clothing-reviews"
    output_dir = "data/bronze/kaggle"
    
    print(f"📥 데이터셋 다운로드 중: {dataset_name}\n")
    
    # 폴더 생성
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Kaggle CLI로 다운로드
        cmd = f"kaggle datasets download -d {dataset_name} -p {output_dir} --unzip"
        subprocess.run(cmd, shell=True, check=True)
        
        print("\n✅ 다운로드 완료!")
        
        # CSV 파일 찾기
        csv_files = list(Path(output_dir).glob("*.csv"))
        
        if csv_files:
            csv_path = csv_files[0]
            print(f"📄 파일 위치: {csv_path}")
            
            # 파일 정보 출력
            df = pd.read_csv(csv_path)
            print(f"\n📊 데이터 정보:")
            print(f"   - 총 행 수: {len(df):,}개")
            print(f"   - 총 컬럼 수: {len(df.columns)}개")
            print(f"\n컬럼 목록:")
            for i, col in enumerate(df.columns, 1):
                print(f"   {i}. {col}")
            
            print(f"\n📋 샘플 데이터 (상위 3개):")
            print(df.head(3))
            
            return csv_path
        else:
            print("❌ CSV 파일을 찾을 수 없습니다.")
            return None
            
    except subprocess.CalledProcessError:
        print("\n❌ 다운로드 실패!")
        print("\n해결 방법:")
        print("1. Kaggle API가 설치되어 있는지 확인: pip install kaggle")
        print("2. 인터넷 연결 확인")
        print("3. Kaggle 계정이 활성화되어 있는지 확인")
        return None
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return None


def convert_to_korean_format(input_csv, output_csv):
    """
    Kaggle 데이터를 프로젝트 형식으로 변환
    """
    print(f"\n🔄 데이터 형식 변환 중...")
    
    df = pd.read_csv(input_csv)
    
    # 컬럼 매핑
    df_converted = pd.DataFrame({
        'review_id': [f"KAGGLE_{i:06d}" for i in range(len(df))],
        'source': 'kaggle_clothing',
        'created_date': pd.to_datetime(df.get('Review Date', pd.Timestamp.now())).dt.date,
        'review_content': df.get('Review Text', ''),
        'rating': df.get('Rating', 0),
        'author_masked': '익명',
        'product_category': df.get('Department Name', '의류'),
    })
    
    # NULL 제거
    df_converted = df_converted.dropna(subset=['review_content'])
    df_converted = df_converted[df_converted['review_content'].str.len() > 10]
    
    # 저장
    df_converted.to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"✅ 변환 완료!")
    print(f"   - 입력: {len(df):,}개")
    print(f"   - 출력: {len(df_converted):,}개 (필터링 후)")
    print(f"   - 저장 위치: {output_csv}")
    
    return output_csv


def main():
    """메인 실행"""
    print("=" * 60)
    print("📦 Kaggle 리뷰 데이터 다운로드 도구")
    print("=" * 60)
    print()
    
    # 다운로드
    csv_path = download_kaggle_dataset()
    
    if csv_path:
        # 형식 변환
        output_csv = "data/bronze/kaggle/reviews_kaggle_converted.csv"
        convert_to_korean_format(csv_path, output_csv)
        
        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. 데이터 검증:")
        print(f"   python src/etl/extractors/validate_smartstore_csv.py")
        print(f"   → 경로 입력: {output_csv}")
        print("\n2. DB 적재:")
        print(f"   python src/etl/extractors/csv_loader.py")


if __name__ == "__main__":
    # 필수 패키지 확인
    try:
        import kaggle
    except ImportError:
        print("❌ Kaggle 패키지가 설치되지 않았습니다.")
        print("설치 명령: pip install kaggle")
        exit(1)
    
    main()
