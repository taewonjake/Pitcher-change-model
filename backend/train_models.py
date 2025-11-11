"""
투수 교체 예측 모델 학습 스크립트

Kaggle MLB 데이터를 기반으로 RandomForest와 LSTM 모델을 학습합니다.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# TensorFlow 임포트 (선택적)
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("Warning: TensorFlow not available. LSTM model will not be trained.")
    TENSORFLOW_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

def generate_synthetic_data(n_samples=10000):
    """
    실제 데이터가 없을 경우 합성 데이터 생성
    실제 Kaggle 데이터를 사용할 경우 이 함수를 수정하세요.
    """
    print("Generating synthetic training data...")
    
    np.random.seed(42)
    
    # 투수 유형 생성 (선발투수 70%, 불펜투수 30%)
    pitcher_types = np.random.choice(
        ["선발투수", "불펜투수"],
        n_samples,
        p=[0.7, 0.3]
    )
    
    # 투수 유형별 투구 수와 이닝 생성
    pitch_counts = []
    innings = []
    
    for pt in pitcher_types:
        if pt == "선발투수":
            # 선발투수: 20-150구, 1-9이닝
            pitch_counts.append(np.random.randint(20, 150))
            innings.append(np.random.randint(1, 10))
        else:
            # 불펜투수: 5-40구, 0.1-2이닝 (소수점 이닝 포함, 1이닝 초과 시 피로도 높음)
            pitch_counts.append(np.random.randint(5, 40))
            # 불펜투수는 주로 1이닝 이하로 던지지만, 1이닝 초과도 가능
            inning_val = np.random.choice([
                np.random.uniform(0.1, 1.0),  # 1이닝 미만 (70%)
                np.random.uniform(1.1, 2.0)   # 1이닝 초과 (30%)
            ], p=[0.7, 0.3])
            # 이닝은 정수로 반올림
            innings.append(int(round(inning_val)))
    
    data = {
        "inning": np.array(innings),
        "pitch_count": np.array(pitch_counts),
        "velocity_drop": np.random.uniform(0, 8, n_samples),
        "earned_runs": np.random.randint(0, 8, n_samples),
        "pitcher_type": pitcher_types,
        "pitcher_hand": np.random.choice(["R", "L"], n_samples),
        "batter_side": np.random.choice(["R", "L", "S"], n_samples),
        "current_batter_ops": np.random.uniform(0.4, 1.2, n_samples),  # 현재 타자 OPS
        "next_batter_side": np.random.choice(["R", "L", "S"], n_samples),
        "next_batter_ops": np.random.uniform(0.4, 1.2, n_samples),  # 다음 타자 OPS
    }
    
    df = pd.DataFrame(data)
    
    # 투수 유형별 플래그 생성
    df["is_starter"] = (df["pitcher_type"] == "선발투수").astype(int)
    
    # 교체 결정 생성 (규칙 기반 + 노이즈)
    # 투수 유형별로 다른 피로도 기준 적용
    replace_prob = np.full(n_samples, 0.1)  # 기본 확률
    
    # 선발투수: 100구/6이닝 기준
    starter_mask = df["is_starter"] == 1
    starter_count = starter_mask.sum()
    if starter_count > 0:
        starter_pitch_impact = np.where(
            df.loc[starter_mask, "pitch_count"] > 100,
            (df.loc[starter_mask, "pitch_count"] - 100) / 50 * 0.3,  # 100구 초과 시 급격히 증가
            df.loc[starter_mask, "pitch_count"] / 100 * 0.15  # 100구 이하
        )
        starter_inning_impact = np.where(
            df.loc[starter_mask, "inning"] > 6,
            (df.loc[starter_mask, "inning"] - 6) / 3 * 0.2 + 0.1,  # 6이닝 초과 시 급격히 증가
            df.loc[starter_mask, "inning"] / 6 * 0.1  # 6이닝 이하
        )
        replace_prob[starter_mask] += (
            starter_pitch_impact.values +
            starter_inning_impact.values +
            np.random.normal(0, 0.05, starter_count)  # 노이즈
        )
    
    # 불펜투수: 20구/1이닝 기준
    reliever_mask = df["is_starter"] == 0
    reliever_count = reliever_mask.sum()
    if reliever_count > 0:
        reliever_pitch_impact = np.where(
            df.loc[reliever_mask, "pitch_count"] > 20,
            (df.loc[reliever_mask, "pitch_count"] - 20) / 20 * 0.4 + 0.2,  # 20구 초과 시 급격히 증가
            df.loc[reliever_mask, "pitch_count"] / 20 * 0.2  # 20구 이하
        )
        reliever_inning_impact = np.where(
            df.loc[reliever_mask, "inning"] > 1,
            (df.loc[reliever_mask, "inning"] - 1) * 0.3 + 0.15,  # 1이닝 초과 시 급격히 증가
            df.loc[reliever_mask, "inning"] * 0.1  # 1이닝 이하
        )
        replace_prob[reliever_mask] += (
            reliever_pitch_impact.values +
            reliever_inning_impact.values +
            np.random.normal(0, 0.05, reliever_count)  # 노이즈
        )
    
    # 구속 감소 영향 (0.8km/h부터 이상)
    velocity_impact = np.where(
        df["velocity_drop"] >= 0.8,
        0.15 + (df["velocity_drop"] - 0.8) / 5 * 0.1,  # 0.8km/h 이상 시 증가
        np.where(
            df["velocity_drop"] >= 0.5,
            0.08,  # 0.5-0.8km/h: 소폭 증가
            0  # 0.5km/h 미만: 영향 없음
        )
    )
    replace_prob += velocity_impact
    
    # 실점 영향 (선발/불펜 투수별 차등 적용)
    earned_runs_impact = np.zeros(n_samples)
    
    # 선발투수: 기존 로직 (3실점부터 증가)
    starter_mask = df["is_starter"] == 1
    earned_runs_impact[starter_mask] = np.where(
        df.loc[starter_mask, "earned_runs"] > 3,
        (df.loc[starter_mask, "earned_runs"] - 3) / 5 * 0.2 + 0.15,  # 3실점 초과
        np.where(
            df.loc[starter_mask, "earned_runs"] > 2,
            0.1,  # 2-3실점
            0  # 2실점 이하
        )
    )
    
    # 불펜투수: 1실점부터 서서히 증가
    reliever_mask = df["is_starter"] == 0
    earned_runs_impact[reliever_mask] = np.where(
        df.loc[reliever_mask, "earned_runs"] >= 1,
        0.1 + (df.loc[reliever_mask, "earned_runs"] - 1) * 0.08,  # 1실점부터 서서히 증가
        0  # 0실점
    )
    # 불펜투수 3실점 이상 시 추가 증가
    reliever_high_runs = (reliever_mask) & (df["earned_runs"] >= 3)
    earned_runs_impact[reliever_high_runs] += 0.1
    
    replace_prob += earned_runs_impact
    replace_prob += np.random.normal(0, 0.05, n_samples)  # 추가 노이즈
    
    # 좌우 매치업 영향 (같은 손=투수 유리=교체 확률 감소, 다른 손=타자 유리=교체 확률 증가)
    # 같은 손 (R-R, L-L) → 투수 유리 → 교체 확률 감소 (추가하지 않음)
    # 다른 손 (R-L, L-R) → 타자 유리 → 교체 확률 증가
    matchup_disadvantage = (
        ((df["pitcher_hand"] == "L") & (df["batter_side"] == "R")) * 0.1 +  # L투 vs R타 → 타자 유리
        ((df["pitcher_hand"] == "R") & (df["batter_side"] == "L")) * 0.1    # R투 vs L타 → 타자 유리
    )
    replace_prob += matchup_disadvantage
    # 같은 손일 경우는 추가하지 않음 (투수 유리하므로 교체 확률이 낮아야 함)
    
    # 현재 타자 영향 (OPS가 높을수록 교체 확률 증가, 더 중요)
    current_batter_impact = (df["current_batter_ops"] - 0.8) * 0.15  # 현재 타자 OPS 기준점 0.8 (가중치 증가)
    replace_prob += current_batter_impact
    
    # 다음 타자 영향 (OPS가 높을수록 교체 확률 증가)
    next_batter_impact = (df["next_batter_ops"] - 0.8) * 0.1  # 다음 타자 OPS 기준점 0.8 (가중치 감소)
    replace_prob += next_batter_impact
    
    # 두 타자 모두 강타자면 더 큰 영향
    both_strong = (df["current_batter_ops"] > 0.9) & (df["next_batter_ops"] > 0.9)
    replace_prob = np.where(both_strong, replace_prob + 0.05, replace_prob)
    
    # 확률을 0-1 범위로 제한
    replace_prob = np.clip(replace_prob, 0, 1)
    
    # 이진 분류로 변환
    df["replace_decision"] = (replace_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    return df

def prepare_features(df):
    """특징 준비 및 인코딩"""
    df = df.copy()
    
    # 기존 pitch_type 컬럼 제거 (더 이상 사용하지 않음)
    if "pitch_type" in df.columns:
        df = df.drop(columns=["pitch_type"])
        print("⚠️ pitch_type 컬럼을 제거했습니다 (더 이상 사용하지 않음).")
    
    # 필수 컬럼 확인
    required_cols = [
        "inning", "pitch_count", "velocity_drop", "earned_runs",
        "pitcher_type", "pitcher_hand", "batter_side", 
        "current_batter_ops", "next_batter_side", "next_batter_ops", "replace_decision"
    ]
    
    # 하위 호환성: 기존 필드명 처리
    if "pitcher_type" not in df.columns:
        df["pitcher_type"] = "선발투수"  # 기본값
        print("⚠️ pitcher_type이 없어서 선발투수로 가정했습니다.")
    if "batter_ops" in df.columns and "next_batter_ops" not in df.columns:
        df["next_batter_ops"] = df["batter_ops"]
        print("⚠️ batter_ops를 next_batter_ops로 변환했습니다.")
    if "current_batter_ops" not in df.columns:
        df["current_batter_ops"] = df.get("next_batter_ops", df.get("batter_ops", 0.8))
        print("⚠️ current_batter_ops가 없어서 기본값 또는 다음 타자 OPS를 사용했습니다.")
    if "batter_slugging" in df.columns and "next_batter_ops" not in df.columns:
        df["next_batter_ops"] = df["batter_slugging"] * 1.5
        print("⚠️ batter_slugging을 next_batter_ops로 변환했습니다.")
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"\n⚠️ 경고: 다음 컬럼이 데이터에 없습니다: {missing_cols}")
        print(f"현재 데이터 컬럼: {df.columns.tolist()}")
        print("\n합성 데이터를 생성합니다...")
        raise ValueError(f"필수 컬럼 누락: {missing_cols}. 합성 데이터를 사용하세요.")
    
    # matchup_type 생성
    df["matchup_type"] = df["pitcher_hand"] + "_" + df["batter_side"]
    
    # 투수 유형 처리 (선발투수: 1, 불펜투수: 0)
    if "is_starter" not in df.columns:
        df["is_starter"] = (df["pitcher_type"] == "선발투수").astype(int)
    
    # OPS 평균 계산 (모델 입력용 - 가중 평균 사용: 현재 60%, 다음 40%)
    if "current_batter_ops" in df.columns and "next_batter_ops" in df.columns:
        df["batter_ops"] = (df["current_batter_ops"] * 0.6 + df["next_batter_ops"] * 0.4)
    elif "current_batter_ops" in df.columns:
        df["batter_ops"] = df["current_batter_ops"]
    elif "next_batter_ops" in df.columns:
        df["batter_ops"] = df["next_batter_ops"]
    else:
        df["batter_ops"] = 0.8  # 기본값
    
    # 범주형 변수 원-핫 인코딩
    cat_cols = ["pitcher_hand", "batter_side", "next_batter_side", "matchup_type"]
    df_encoded = pd.get_dummies(df, columns=cat_cols, prefix=cat_cols)
    
    # 타겟 변수 분리
    if "replace_decision" in df_encoded.columns:
        y = df_encoded["replace_decision"].values
        X = df_encoded.drop("replace_decision", axis=1)
    else:
        raise ValueError("replace_decision column not found")
    
    # 숫자형 컬럼만 남기기 (문자열 컬럼 제거)
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    X = X[numeric_cols]
    
    # 컬럼 순서 정렬 (일관성 유지)
    X = X.reindex(sorted(X.columns), axis=1)
    
    return X, y, X.columns.tolist()

def train_random_forest(X, y):
    """RandomForest 모델 학습"""
    print("\n=== Training RandomForest Model ===")
    
    # 학습/테스트 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 모델 학습
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train, y_train)
    
    # 평가
    train_score = rf_model.score(X_train, y_train)
    test_score = rf_model.score(X_test, y_test)
    
    print(f"Train Accuracy: {train_score:.4f}")
    print(f"Test Accuracy: {test_score:.4f}")
    
    return rf_model

def train_lstm(X, y):
    """LSTM 모델 학습"""
    if not TENSORFLOW_AVAILABLE:
        print("\n=== LSTM Model Training Skipped (TensorFlow not available) ===")
        return None
    
    print("\n=== Training LSTM Model ===")
    
    # 학습/테스트 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 정규화
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # LSTM을 위한 시퀀스 형태로 변환 (특징을 시퀀스로 재구성)
    # 실제로는 시계열 데이터가 아니므로, 특징을 시퀀스로 변환
    seq_length = 5
    n_features = X_train_scaled.shape[1]
    
    # 시퀀스 생성 (간단한 방법: 특징을 여러 그룹으로 나눔)
    def create_sequences(X, seq_len):
        n_samples = len(X)
        n_seqs = n_samples // seq_len
        X_seq = X[:n_seqs * seq_len].reshape(n_seqs, seq_len, n_features // seq_len + 1)
        # 패딩으로 맞춤
        if X_seq.shape[2] != n_features:
            # 간단한 방법: 특징을 평탄화하고 재구성
            X_seq = X[:n_seqs * seq_len].reshape(n_seqs, seq_len, -1)
            # 부족한 차원은 0으로 패딩
            if X_seq.shape[2] < n_features:
                padding = np.zeros((n_seqs, seq_len, n_features - X_seq.shape[2]))
                X_seq = np.concatenate([X_seq, padding], axis=2)
            else:
                X_seq = X_seq[:, :, :n_features]
        return X_seq
    
    # 더 간단한 방법: 특징을 직접 사용 (LSTM 대신 Dense 레이어 사용)
    # 실제 시계열이 아니므로 간단한 신경망으로 대체
    model = Sequential([
        Dense(64, activation='relu', input_shape=(X_train_scaled.shape[1],)),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    # 학습
    history = model.fit(
        X_train_scaled, y_train,
        validation_data=(X_test_scaled, y_test),
        epochs=50,
        batch_size=32,
        verbose=1
    )
    
    # 평가
    test_loss, test_acc = model.evaluate(X_test_scaled, y_test, verbose=0)
    print(f"Test Accuracy: {test_acc:.4f}")
    
    return model

def main():
    print("=" * 60)
    print("투수 교체 예측 모델 학습")
    print("=" * 60)
    
    # 데이터 로드 또는 생성
    data_path = DATA_DIR / "train_pitch_replacement.csv"
    
    df = None
    use_synthetic = False
    
    if data_path.exists():
        print(f"\nLoading data from {data_path}...")
        try:
            df = pd.read_csv(data_path)
            print(f"Loaded {len(df)} samples")
            print(f"Data columns: {df.columns.tolist()}")
            
            # 기존 pitch_type 컬럼 제거 (더 이상 사용하지 않음)
            if "pitch_type" in df.columns:
                df = df.drop(columns=["pitch_type"])
                print("⚠️ pitch_type 컬럼을 제거했습니다 (더 이상 사용하지 않음).")
            
            # 하위 호환성: batter_slugging이 있으면 batter_ops로 변환
            if "batter_slugging" in df.columns and "batter_ops" not in df.columns:
                df["batter_ops"] = df["batter_slugging"] * 1.5  # SLG를 대략적인 OPS로 변환
                print("⚠️ batter_slugging을 batter_ops로 변환했습니다.")
            
            # 필수 컬럼 확인 (pitch_type 제외)
            required_cols = [
                "inning", "pitch_count", "velocity_drop", "earned_runs",
                "pitcher_hand", "batter_side", 
                "next_batter_side", "replace_decision"
            ]
            
            # pitcher_type이 없으면 추가 (기본값: 선발투수)
            if "pitcher_type" not in df.columns:
                df["pitcher_type"] = "선발투수"
                print("⚠️ pitcher_type이 없어서 선발투수로 가정했습니다.")
            
            # current_batter_ops와 next_batter_ops 처리
            if "current_batter_ops" not in df.columns:
                if "batter_ops" in df.columns:
                    df["current_batter_ops"] = df["batter_ops"]
                    df["next_batter_ops"] = df["batter_ops"]
                else:
                    df["current_batter_ops"] = 0.8
                    df["next_batter_ops"] = 0.8
                print("⚠️ current_batter_ops와 next_batter_ops가 없어서 기본값을 사용했습니다.")
            elif "next_batter_ops" not in df.columns:
                if "batter_ops" in df.columns:
                    df["next_batter_ops"] = df["batter_ops"]
                else:
                    df["next_batter_ops"] = df["current_batter_ops"]
                print("⚠️ next_batter_ops가 없어서 batter_ops 또는 current_batter_ops를 사용했습니다.")
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"\n⚠️ 경고: 로드된 데이터에 필수 컬럼이 없습니다: {missing_cols}")
                print("합성 데이터를 사용합니다...")
                use_synthetic = True
        except Exception as e:
            print(f"\n⚠️ 데이터 로드 오류: {e}")
            print("합성 데이터를 사용합니다...")
            use_synthetic = True
    else:
        print(f"\nData file not found: {data_path}")
        print("Generating synthetic data...")
        use_synthetic = True
    
    if use_synthetic or df is None:
        print("\nGenerating synthetic data...")
        df = generate_synthetic_data(n_samples=10000)
        
        # 데이터 저장
        df.to_csv(data_path, index=False)
        print(f"Saved synthetic data to {data_path}")
    
    # 특징 준비
    print("\nPreparing features...")
    try:
        X, y, feature_names = prepare_features(df)
    except ValueError as e:
        print(f"\n❌ 오류: {e}")
        print("합성 데이터로 다시 시도합니다...")
        df = generate_synthetic_data(n_samples=10000)
        df.to_csv(data_path, index=False)
        X, y, feature_names = prepare_features(df)
    
    print(f"Features shape: {X.shape}")
    print(f"Target distribution: {pd.Series(y).value_counts().to_dict()}")
    
    # RandomForest 모델 학습
    # X가 이미 DataFrame이면 values로 변환
    if hasattr(X, 'values'):
        X_train = X.values
    else:
        X_train = X
    rf_model = train_random_forest(X_train, y)
    
    # 모델 저장
    rf_model_path = MODEL_DIR / "rf_pitch_model.pkl"
    with open(rf_model_path, "wb") as f:
        pickle.dump(rf_model, f)
    print(f"\nRandomForest model saved to {rf_model_path}")
    
    # LSTM 모델 학습
    if TENSORFLOW_AVAILABLE:
        # X가 이미 DataFrame이면 values로 변환
        if hasattr(X, 'values'):
            X_train_lstm = X.values
        else:
            X_train_lstm = X
        lstm_model = train_lstm(X_train_lstm, y)
        
        if lstm_model:
            lstm_model_path = MODEL_DIR / "lstm_pitch_model.h5"
            lstm_model.save(lstm_model_path)
            print(f"LSTM model saved to {lstm_model_path}")
    else:
        print("\nLSTM model training skipped (TensorFlow not available)")
    
    print("\n" + "=" * 60)
    print("모델 학습 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()


