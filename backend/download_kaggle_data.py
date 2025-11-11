"""
Kaggle MLB 데이터 다운로드 및 전처리 스크립트

사용법:
1. pip install kagglehub[pandas-datasets]
2. python download_kaggle_data.py

참고: kagglehub는 API 토큰 설정이 필요 없습니다 (자동 인증)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import os
warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def download_kaggle_dataset_kagglehub():
    """
    kagglehub를 사용하여 Kaggle에서 MLB 데이터 다운로드 (최신 방법)
    
    장점: API 토큰 설정 불필요, 더 간단한 사용법
    """
    try:
        import kagglehub
        from kagglehub import KaggleDatasetAdapter
        
        dataset = "pschale/mlb-pitch-data-20152018"
        print(f"🔄 kagglehub를 사용하여 데이터셋 다운로드 중: {dataset}")
        print("   (이 방법은 API 토큰 설정이 필요 없습니다)")
        
        # 데이터셋의 모든 파일 목록 확인을 위해 먼저 다운로드
        # kagglehub는 데이터를 캐시에 저장하고 pandas로 직접 로드 가능
        # 파일명을 지정하지 않으면 첫 번째 파일을 로드하거나 에러 발생 가능
        
        # 방법 1: 특정 파일명을 알고 있는 경우
        # 방법 2: 데이터셋의 모든 파일 다운로드
        
        # 먼저 데이터셋 경로 가져오기
        dataset_path = kagglehub.dataset_download(dataset)
        print(f"✅ 데이터셋 다운로드 완료: {dataset_path}")
        
        # 다운로드된 파일들을 data 폴더로 복사
        dataset_path = Path(dataset_path)
        
        # CSV 파일 찾기
        csv_files = list(dataset_path.rglob("*.csv"))
        zip_files = list(dataset_path.rglob("*.zip"))
        
        if csv_files or zip_files:
            print(f"📁 발견된 파일: {len(csv_files)} CSV, {len(zip_files)} ZIP")
            
            # CSV 파일들을 data 폴더로 복사
            for csv_file in csv_files:
                dest_file = DATA_DIR / csv_file.name
                import shutil
                shutil.copy2(csv_file, dest_file)
                print(f"   복사됨: {dest_file.name}")
            
            # ZIP 파일들도 복사
            for zip_file in zip_files:
                dest_file = DATA_DIR / zip_file.name
                import shutil
                shutil.copy2(zip_file, dest_file)
                print(f"   복사됨: {dest_file.name}")
                # ZIP 파일 압축 해제
                import zipfile
                with zipfile.ZipFile(dest_file, 'r') as zip_ref:
                    zip_ref.extractall(DATA_DIR)
                print(f"   압축 해제됨: {dest_file.name}")
        
        return True
    
    except ImportError:
        print("❌ kagglehub가 설치되지 않았습니다.")
        print("   설치 방법: pip install kagglehub[pandas-datasets]")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def download_kaggle_dataset_legacy():
    """
    기존 kaggle API를 사용하는 방법 (백업)
    """
    try:
        import kaggle
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        api = KaggleApi()
        api.authenticate()
        
        dataset = "pschale/mlb-pitch-data-20152018"
        print(f"Downloading dataset: {dataset}")
        api.dataset_download_files(dataset, path=str(DATA_DIR), unzip=True)
        
        print("Download completed!")
        return True
    
    except ImportError:
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def download_kaggle_dataset():
    """
    kagglehub를 먼저 시도하고, 실패하면 기존 방법 시도
    """
    # 먼저 kagglehub 시도 (더 간단하고 최신 방법)
    if download_kaggle_dataset_kagglehub():
        return True
    
    # kagglehub 실패 시 기존 방법 시도
    print("\n🔄 kagglehub 실패, 기존 kaggle API 방법 시도...")
    if download_kaggle_dataset_legacy():
        return True
    
    return False

def process_kaggle_data():
    """
    Kaggle MLB 데이터를 투수 교체 예측용 데이터로 변환
    
    실제 데이터 구조에 맞게 수정이 필요할 수 있습니다.
    """
    print("Processing Kaggle data...")
    
    # 데이터 파일 찾기
    csv_files = list(DATA_DIR.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in data directory")
        return None
    
    # 가장 큰 파일 선택 (보통 메인 데이터 파일)
    main_file = max(csv_files, key=lambda x: x.stat().st_size)
    print(f"Processing file: {main_file}")
    
    try:
        # 데이터 로드 (큰 파일이므로 청크로 읽을 수 있음)
        df = pd.read_csv(main_file, nrows=100000)  # 샘플링 (전체 데이터가 너무 클 수 있음)
        
        print(f"Loaded {len(df)} rows")
        print(f"Columns: {df.columns.tolist()}")
        
        # 필요한 컬럼 매핑 (실제 데이터 구조에 맞게 수정 필요)
        # 예시 매핑 (실제 컬럼명은 다를 수 있음)
        column_mapping = {
            # 실제 컬럼명으로 매핑 필요
            # "inning": "inning",
            # "pitch_count": "pitch_count",
            # 등등...
        }
        
        # 데이터 전처리 및 특징 생성
        # 실제 Kaggle 데이터 구조에 맞게 구현 필요
        
        print("Data processing completed!")
        return df
    
    except Exception as e:
        print(f"Error processing data: {e}")
        return None

def check_existing_data():
    """이미 다운로드된 데이터 파일 확인"""
    csv_files = list(DATA_DIR.glob("*.csv"))
    zip_files = list(DATA_DIR.glob("*.zip"))
    
    if csv_files or zip_files:
        print(f"\n✅ 발견된 데이터 파일:")
        for f in csv_files + zip_files:
            print(f"   - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")
        return True
    return False

def main():
    print("=" * 60)
    print("Kaggle MLB 데이터 다운로드 및 전처리")
    print("=" * 60)
    
    DATA_DIR.mkdir(exist_ok=True)
    
    # 이미 데이터가 있는지 확인
    has_data = check_existing_data()
    
    if has_data:
        print("\n📁 기존 데이터 파일을 발견했습니다.")
        use_existing = input("기존 데이터를 사용하시겠습니까? (y/n): ").lower().strip()
        if use_existing == 'y':
            df = process_kaggle_data()
            if df is not None:
                output_path = DATA_DIR / "train_pitch_replacement.csv"
                df.to_csv(output_path, index=False)
                print(f"\n✅ 전처리된 데이터 저장 완료: {output_path}")
                return
    
    # Kaggle 데이터 자동 다운로드 시도
    print("\n🔄 Kaggle API를 통한 자동 다운로드 시도...")
    downloaded = download_kaggle_dataset()
    
    if downloaded:
        # 데이터 전처리
        df = process_kaggle_data()
        
        if df is not None:
            # 전처리된 데이터 저장
            output_path = DATA_DIR / "train_pitch_replacement.csv"
            df.to_csv(output_path, index=False)
            print(f"\n✅ 전처리된 데이터 저장 완료: {output_path}")
    else:
        print("\n" + "=" * 60)
        print("📥 수동 다운로드 방법")
        print("=" * 60)
        print("\n1. 다음 링크에서 데이터 다운로드:")
        print("   https://www.kaggle.com/datasets/pschale/mlb-pitch-data-20152018")
        print("\n2. 다운로드한 파일을 다음 폴더에 넣으세요:")
        print(f"   {DATA_DIR}")
        print("\n3. 이 스크립트를 다시 실행하세요.")
        print("\n또는")
        print("\n🔑 자동 다운로드를 원하시면:")
        print("   방법 1 (권장 - 가장 간단):")
        print("   1. pip install kagglehub[pandas-datasets]")
        print("   2. 이 스크립트를 다시 실행")
        print("   → API 토큰 설정 불필요!")
        print("\n   방법 2 (기존 방법):")
        print("   1. pip install kaggle")
        print("   2. https://www.kaggle.com/account 에서 API 토큰 다운로드")
        print("   3. Windows: C:\\Users\\[사용자명]\\.kaggle\\kaggle.json 에 토큰 저장")
        print("   4. 이 스크립트를 다시 실행")
        print("\n💡 참고: 모델 학습은 합성 데이터로도 가능합니다 (train_models.py)")

if __name__ == "__main__":
    main()

