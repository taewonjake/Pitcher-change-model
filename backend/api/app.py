from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# 모델 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"
RF_MODEL_PATH = MODEL_DIR / "rf_pitch_model.pkl"
LSTM_MODEL_PATH = MODEL_DIR / "lstm_pitch_model.h5"

app = Flask(__name__)
CORS(app)

# 모델 로드
rf_model = None
lstm_model = None

def load_models():
    global rf_model, lstm_model
    try:
        # RandomForest 모델 로드
        if RF_MODEL_PATH.exists():
            with open(RF_MODEL_PATH, "rb") as f:
                rf_model = pickle.load(f)
        else:
            print(f"Warning: {RF_MODEL_PATH} not found. Using dummy model.")
            rf_model = None
        
        # LSTM 모델 로드
        try:
            from tensorflow.keras.models import load_model
            if LSTM_MODEL_PATH.exists():
                lstm_model = load_model(LSTM_MODEL_PATH)
            else:
                print(f"Warning: {LSTM_MODEL_PATH} not found. Using dummy model.")
                lstm_model = None
        except ImportError:
            print("Warning: TensorFlow not available. LSTM model will use dummy predictions.")
            lstm_model = None
    except Exception as e:
        print(f"Error loading models: {e}")
        rf_model = None
        lstm_model = None

# 서버 시작 시 모델 로드
load_models()

def prepare_features(data):
    """입력 데이터를 모델이 요구하는 형식으로 변환"""
    df = pd.DataFrame([data])
    
    # matchup_type 생성
    df["matchup_type"] = df["pitcher_hand"] + "_" + df["batter_side"]
    
    # 투수 유형 처리 (선발투수: 1, 불펜투수: 0)
    if "pitcher_type" in df.columns:
        df["is_starter"] = (df["pitcher_type"] == "선발투수").astype(int)
    else:
        df["is_starter"] = 1  # 기본값: 선발투수
    
    # 범주형 변수 인코딩
    cat_cols = ["pitcher_hand", "batter_side", "next_batter_side", "matchup_type"]
    
    # 모든 가능한 범주 값 정의 (실제 모델 학습 시 사용된 값들)
    all_categories = {
        "pitcher_hand": ["R", "L"],
        "batter_side": ["R", "L", "S"],
        "next_batter_side": ["R", "L", "S"],
        "matchup_type": ["R_R", "R_L", "R_S", "L_R", "L_L", "L_S"]
    }
    
    # 현재 타자 OPS와 다음 타자 OPS 처리
    # 원-핫 인코딩 전에 처리해야 함
    if "current_batter_ops" not in df.columns:
        df["current_batter_ops"] = 0.8  # 기본값
    
    if "next_batter_ops" not in df.columns:
        if "batter_ops" in df.columns:
            df["next_batter_ops"] = df["batter_ops"]
        elif "batter_slugging" in df.columns:
            # SLG를 OPS로 대략 변환 (SLG * 1.5 정도)
            df["next_batter_ops"] = df["batter_slugging"] * 1.5
        else:
            df["next_batter_ops"] = 0.8  # 기본값
    
    # 두 OPS 값의 가중 평균 사용 (현재 타자 60%, 다음 타자 40%)
    df["batter_ops"] = (df["current_batter_ops"] * 0.6 + df["next_batter_ops"] * 0.4)
    
    # 원-핫 인코딩
    df_encoded = pd.get_dummies(df, columns=cat_cols, prefix=cat_cols)
    
    # 누락된 컬럼 추가 (0으로 채움)
    expected_cols = [
        "inning", "pitch_count", "velocity_drop", "earned_runs", "batter_ops", "is_starter",
        "pitcher_hand_L", "pitcher_hand_R",
        "batter_side_L", "batter_side_R", "batter_side_S",
        "next_batter_side_L", "next_batter_side_R", "next_batter_side_S",
        "matchup_type_L_L", "matchup_type_L_R", "matchup_type_L_S",
        "matchup_type_R_L", "matchup_type_R_R", "matchup_type_R_S"
    ]
    
    # batter_ops와 is_starter 컬럼 추가
    if "batter_ops" not in df_encoded.columns:
        df_encoded["batter_ops"] = df["batter_ops"].values
    if "is_starter" not in df_encoded.columns:
        df_encoded["is_starter"] = df["is_starter"].values
    
    for col in expected_cols:
        if col not in df_encoded.columns:
            df_encoded[col] = 0
    
    # 컬럼 순서 정렬
    df_encoded = df_encoded.reindex(columns=expected_cols, fill_value=0)
    
    return df_encoded.values

def dummy_rf_predict(X):
    """더미 RandomForest 예측 (모델이 없을 때 사용)"""
    # 간단한 규칙 기반 예측
    inning = X[0][0]
    pitch_count = X[0][1]
    velocity_drop = X[0][2]
    earned_runs = X[0][3]
    batter_ops = X[0][4] if len(X[0]) > 4 else 0.8  # 평균 OPS (기본값 0.8)
    is_starter = int(X[0][5]) if len(X[0]) > 5 else 1  # 선발투수 여부 (기본값: 선발)
    
    prob = 0.3  # 기본 확률
    
    # 투수 유형별 피로도 기준 적용
    if is_starter:
        # 선발투수: 100구/6이닝 기준
        if pitch_count > 100:
            prob += 0.2
        elif pitch_count > 80:
            prob += 0.1
        if inning > 6:
            prob += 0.15
        elif inning > 5:
            prob += 0.08
    else:
        # 불펜투수: 20구/1이닝 기준
        if pitch_count > 20:
            prob += 0.25
        elif pitch_count > 15:
            prob += 0.15
        if inning > 1:
            prob += 0.2
        elif inning >= 1:
            prob += 0.1
    
    # 구속 감소 분석 (0.8km/h부터 이상)
    if velocity_drop >= 0.8:
        prob += 0.15 + (velocity_drop - 0.8) / 5 * 0.1  # 0.8km/h 이상 시 증가, 더 많이 감소할수록 더 증가
    elif velocity_drop >= 0.5:
        prob += 0.08
    
    # 실점 분석 (불펜투수는 1실점부터 교체 확률 증가)
    if is_starter:
        # 선발투수 기준
        if earned_runs > 3:
            prob += 0.15
        elif earned_runs > 2:
            prob += 0.1
    else:
        # 불펜투수 기준 (1실점부터 교체 확률 증가)
        if earned_runs >= 1:
            prob += 0.1 + (earned_runs - 1) * 0.08  # 1실점부터 서서히 증가
            if earned_runs >= 3:
                prob += 0.1  # 3실점 이상 시 추가 증가
    
    if batter_ops > 0.9:  # OPS가 높을수록 교체 확률 증가
        prob += 0.1
    
    return np.array([[1 - prob, prob]])

def dummy_lstm_predict(X):
    """더미 LSTM 예측 (모델이 없을 때 사용)"""
    # RF와 유사하지만 약간 다른 로직
    inning = X[0][0]
    pitch_count = X[0][1]
    velocity_drop = X[0][2]
    earned_runs = X[0][3]
    batter_ops = X[0][4] if len(X[0]) > 4 else 0.8  # 평균 OPS (기본값 0.8)
    is_starter = int(X[0][5]) if len(X[0]) > 5 else 1  # 선발투수 여부 (기본값: 선발)
    
    prob = 0.25
    
    # 투수 유형별 피로도 기준 적용
    if is_starter:
        # 선발투수: 100구/6이닝 기준
        if pitch_count > 100:
            prob += 0.25
        elif pitch_count > 80:
            prob += 0.12
        if inning > 6:
            prob += 0.18
        elif inning > 5:
            prob += 0.1
    else:
        # 불펜투수: 20구/1이닝 기준
        if pitch_count > 20:
            prob += 0.28
        elif pitch_count > 15:
            prob += 0.18
        if inning > 1:
            prob += 0.22
        elif inning >= 1:
            prob += 0.12
    
    # 구속 감소 분석 (0.8km/h부터 이상)
    if velocity_drop >= 0.8:
        prob += 0.2 + (velocity_drop - 0.8) / 5 * 0.1  # 0.8km/h 이상 시 증가
    elif velocity_drop >= 0.5:
        prob += 0.1
    
    # 실점 분석 (불펜투수는 1실점부터 교체 확률 증가)
    if is_starter:
        # 선발투수 기준
        if earned_runs > 2:
            prob += 0.2
        elif earned_runs > 1:
            prob += 0.1
    else:
        # 불펜투수 기준 (1실점부터 교체 확률 증가)
        if earned_runs >= 1:
            prob += 0.12 + (earned_runs - 1) * 0.1  # 1실점부터 서서히 증가
            if earned_runs >= 2:
                prob += 0.1  # 2실점 이상 시 추가 증가
    
    if batter_ops > 0.9:  # OPS가 높을수록 교체 확률 증가
        prob += 0.08
    
    return np.array([[min(prob, 0.95)]])

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = [
            "inning", "pitch_count", "velocity_drop", "earned_runs",
            "pitcher_type", "pitcher_hand", "batter_side", 
            "current_batter_ops", "next_batter_side", "next_batter_ops"
        ]
        
        # 하위 호환성을 위해 기존 필드명도 허용
        if "pitcher_type" not in data:
            # 기본값: 선발투수로 가정
            data["pitcher_type"] = "선발투수"
        if "batter_ops" in data and "next_batter_ops" not in data:
            data["next_batter_ops"] = data["batter_ops"]
        if "current_batter_ops" not in data:
            data["current_batter_ops"] = data.get("batter_ops", 0.8)  # 기본값
        if "batter_slugging" in data and "next_batter_ops" not in data:
            data["next_batter_ops"] = data["batter_slugging"] * 1.5  # SLG를 대략적인 OPS로 변환
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # 특징 준비
        X = prepare_features(data)
        
        # RandomForest 예측
        if rf_model is not None:
            try:
                rf_proba = rf_model.predict_proba(X)
                rf_prob = float(rf_proba[0][1] if rf_proba.shape[1] > 1 else rf_proba[0][0])
            except:
                rf_proba = dummy_rf_predict(X)
                rf_prob = float(rf_proba[0][1])
        else:
            rf_proba = dummy_rf_predict(X)
            rf_prob = float(rf_proba[0][1])
        
        # LSTM 예측
        if lstm_model is not None:
            try:
                lstm_pred = lstm_model.predict(np.expand_dims(X, axis=0), verbose=0)
                lstm_prob = float(lstm_pred[0][0])
            except:
                lstm_prob = float(dummy_lstm_predict(X)[0][0])
        else:
            lstm_prob = float(dummy_lstm_predict(X)[0][0])
        
        # 앙상블 예측 (RF 0.6 + LSTM 0.4)
        ensemble_prob = (rf_prob * 0.6) + (lstm_prob * 0.4)
        
        # 권장 여부 결정 (50% 이상이면 교체 권장)
        if ensemble_prob >= 0.5:
            label = "교체 권장"
        elif ensemble_prob >= 0.3:
            label = "주의 필요"
        else:
            label = "유지 가능"
        
        return jsonify({
            "rf_prob": round(float(rf_prob), 4),
            "lstm_prob": round(float(lstm_prob), 4),
            "final_prob": round(float(ensemble_prob), 4),
            "recommendation": label,
            "status": "success"
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "rf_model_loaded": rf_model is not None,
        "lstm_model_loaded": lstm_model is not None
    })

if __name__ == "__main__":
    print("Starting Flask server...")
    print(f"RF Model: {'Loaded' if rf_model else 'Using dummy'}")
    print(f"LSTM Model: {'Loaded' if lstm_model else 'Using dummy'}")
    app.run(host="0.0.0.0", port=5000, debug=True)



