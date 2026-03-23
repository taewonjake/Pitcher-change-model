from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_sources.thesportsdb_client import TheSportsDBClient
from data_sources.kbodata_client import KBODataClient
from services.bullpen import build_bullpen_snapshot, recommend_pitchers

MODEL_DIR = BASE_DIR / "model"
RF_MODEL_PATH = MODEL_DIR / "rf_pitch_model.pkl"
LSTM_MODEL_PATH = MODEL_DIR / "lstm_pitch_model.h5"

app = Flask(__name__)
CORS(app)

rf_model = None
lstm_model = None
sports_client = TheSportsDBClient()
kbo_data_client = KBODataClient()


def load_models():
    global rf_model, lstm_model
    try:
        if RF_MODEL_PATH.exists():
            with open(RF_MODEL_PATH, "rb") as f:
                rf_model = pickle.load(f)
        else:
            rf_model = None

        try:
            from tensorflow.keras.models import load_model
            if LSTM_MODEL_PATH.exists():
                lstm_model = load_model(LSTM_MODEL_PATH)
            else:
                lstm_model = None
        except ImportError:
            lstm_model = None
    except Exception:
        rf_model = None
        lstm_model = None


load_models()


def _resolve_team_name_and_id(team_query):
    teams_payload = sports_client.get_kbo_teams()
    teams = teams_payload.get("teams", [])
    source = teams_payload.get("source", "unknown")
    if not teams:
        return None, None, source

    if not team_query:
        return teams[0].get("name"), teams[0].get("id"), source

    q = str(team_query).strip().lower()
    for t in teams:
        if q in (
            str(t.get("name", "")).lower(),
            str(t.get("short_name", "")).lower(),
            str(t.get("id", "")).lower(),
        ):
            return t.get("name"), t.get("id"), source

    return teams[0].get("name"), teams[0].get("id"), source


def prepare_features(data):
    df = pd.DataFrame([data])
    df["matchup_type"] = df["pitcher_hand"] + "_" + df["batter_side"]

    if "pitcher_type" in df.columns:
        df["is_starter"] = (df["pitcher_type"] == "선발투수").astype(int)
    else:
        df["is_starter"] = 1

    cat_cols = ["pitcher_hand", "batter_side", "next_batter_side", "matchup_type"]

    if "current_batter_ops" not in df.columns:
        df["current_batter_ops"] = 0.8
    if "next_batter_ops" not in df.columns:
        if "batter_ops" in df.columns:
            df["next_batter_ops"] = df["batter_ops"]
        elif "batter_slugging" in df.columns:
            df["next_batter_ops"] = df["batter_slugging"] * 1.5
        else:
            df["next_batter_ops"] = 0.8

    df["batter_ops"] = (df["current_batter_ops"] * 0.6 + df["next_batter_ops"] * 0.4)
    df_encoded = pd.get_dummies(df, columns=cat_cols, prefix=cat_cols)

    expected_cols = [
        "inning", "pitch_count", "velocity_drop", "earned_runs", "batter_ops", "is_starter",
        "pitcher_hand_L", "pitcher_hand_R",
        "batter_side_L", "batter_side_R", "batter_side_S",
        "next_batter_side_L", "next_batter_side_R", "next_batter_side_S",
        "matchup_type_L_L", "matchup_type_L_R", "matchup_type_L_S",
        "matchup_type_R_L", "matchup_type_R_R", "matchup_type_R_S",
    ]

    if "batter_ops" not in df_encoded.columns:
        df_encoded["batter_ops"] = df["batter_ops"].values
    if "is_starter" not in df_encoded.columns:
        df_encoded["is_starter"] = df["is_starter"].values

    for col in expected_cols:
        if col not in df_encoded.columns:
            df_encoded[col] = 0

    df_encoded = df_encoded.reindex(columns=expected_cols, fill_value=0)
    return df_encoded.values


def dummy_rf_predict(X):
    inning = X[0][0]
    pitch_count = X[0][1]
    velocity_drop = X[0][2]
    earned_runs = X[0][3]
    batter_ops = X[0][4] if len(X[0]) > 4 else 0.8
    is_starter = int(X[0][5]) if len(X[0]) > 5 else 1

    prob = 0.3
    if is_starter:
        if pitch_count > 100:
            prob += 0.2
        elif pitch_count > 80:
            prob += 0.1
        if inning > 6:
            prob += 0.15
        elif inning > 5:
            prob += 0.08
    else:
        if pitch_count > 20:
            prob += 0.25
        elif pitch_count > 15:
            prob += 0.15
        if inning > 1:
            prob += 0.2
        elif inning >= 1:
            prob += 0.1

    if velocity_drop >= 0.8:
        prob += 0.15 + (velocity_drop - 0.8) / 5 * 0.1
    elif velocity_drop >= 0.5:
        prob += 0.08

    if is_starter:
        if earned_runs > 3:
            prob += 0.15
        elif earned_runs > 2:
            prob += 0.1
    else:
        if earned_runs >= 1:
            prob += 0.1 + (earned_runs - 1) * 0.08
            if earned_runs >= 3:
                prob += 0.1

    if batter_ops > 0.9:
        prob += 0.1

    return np.array([[1 - prob, prob]])


def dummy_lstm_predict(X):
    inning = X[0][0]
    pitch_count = X[0][1]
    velocity_drop = X[0][2]
    earned_runs = X[0][3]
    batter_ops = X[0][4] if len(X[0]) > 4 else 0.8
    is_starter = int(X[0][5]) if len(X[0]) > 5 else 1

    prob = 0.25
    if is_starter:
        if pitch_count > 100:
            prob += 0.25
        elif pitch_count > 80:
            prob += 0.12
        if inning > 6:
            prob += 0.18
        elif inning > 5:
            prob += 0.1
    else:
        if pitch_count > 20:
            prob += 0.28
        elif pitch_count > 15:
            prob += 0.18
        if inning > 1:
            prob += 0.22
        elif inning >= 1:
            prob += 0.12

    if velocity_drop >= 0.8:
        prob += 0.2 + (velocity_drop - 0.8) / 5 * 0.1
    elif velocity_drop >= 0.5:
        prob += 0.1

    if is_starter:
        if earned_runs > 2:
            prob += 0.2
        elif earned_runs > 1:
            prob += 0.1
    else:
        if earned_runs >= 1:
            prob += 0.12 + (earned_runs - 1) * 0.1
            if earned_runs >= 2:
                prob += 0.1

    if batter_ops > 0.9:
        prob += 0.08

    return np.array([[min(prob, 0.95)]])


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json() or {}
        required_fields = [
            "inning", "pitch_count", "velocity_drop", "earned_runs",
            "pitcher_type", "pitcher_hand", "batter_side",
            "current_batter_ops", "next_batter_side", "next_batter_ops",
        ]

        if "pitcher_type" not in data:
            data["pitcher_type"] = "선발투수"
        if "batter_ops" in data and "next_batter_ops" not in data:
            data["next_batter_ops"] = data["batter_ops"]
        if "current_batter_ops" not in data:
            data["current_batter_ops"] = data.get("batter_ops", 0.8)
        if "batter_slugging" in data and "next_batter_ops" not in data:
            data["next_batter_ops"] = data["batter_slugging"] * 1.5

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        X = prepare_features(data)

        if rf_model is not None:
            try:
                rf_proba = rf_model.predict_proba(X)
                rf_prob = float(rf_proba[0][1] if rf_proba.shape[1] > 1 else rf_proba[0][0])
            except Exception:
                rf_prob = float(dummy_rf_predict(X)[0][1])
        else:
            rf_prob = float(dummy_rf_predict(X)[0][1])

        if lstm_model is not None:
            try:
                lstm_pred = lstm_model.predict(np.expand_dims(X, axis=0), verbose=0)
                lstm_prob = float(lstm_pred[0][0])
            except Exception:
                lstm_prob = float(dummy_lstm_predict(X)[0][0])
        else:
            lstm_prob = float(dummy_lstm_predict(X)[0][0])

        ensemble_prob = (rf_prob * 0.6) + (lstm_prob * 0.4)

        if ensemble_prob >= 0.5:
            label = "교체 권장"
        elif ensemble_prob >= 0.3:
            label = "주의 필요"
        else:
            label = "유지 가능"

        return jsonify(
            {
                "rf_prob": round(float(rf_prob), 4),
                "lstm_prob": round(float(lstm_prob), 4),
                "final_prob": round(float(ensemble_prob), 4),
                "recommendation": label,
                "status": "success",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "rf_model_loaded": rf_model is not None,
            "lstm_model_loaded": lstm_model is not None,
        }
    )


@app.route("/teams", methods=["GET"])
def list_teams():
    payload = sports_client.get_kbo_teams()
    return jsonify(
        {
            "status": "success",
            "source": payload.get("source", "unknown"),
            "teams": payload.get("teams", []),
        }
    )


@app.route("/bullpen/status", methods=["GET"])
def bullpen_status():
    team_query = request.args.get("team")
    team_name, team_id, source = _resolve_team_name_and_id(team_query)
    if not team_name:
        return jsonify({"status": "error", "error": "No team data available"}), 503

    events = sports_client.get_recent_events(team_id) if source == "thesportsdb" else []
    roster_payload = kbo_data_client.get_team_pitcher_names(team_name)
    roster_names = roster_payload.get("pitcher_names", [])
    if roster_payload.get("source") != "kbodata":
        roster_names = []
    snapshot = build_bullpen_snapshot(team_name, events, pitcher_names=roster_names)

    return jsonify(
        {
            "status": "success",
            "source": source,
            "team_id": team_id,
            "team": team_name,
                "bullpen": {
                    "energy_index": snapshot["energy_index"],
                    "risk_level": snapshot["risk_level"],
                    "usable_pitchers": snapshot["usable_pitchers"],
                    "metrics": snapshot["metrics"],
                    "as_of": snapshot["as_of"],
                    "latest_event_date": snapshot["metrics"]["latest_event_date"],
                    "oldest_event_date": snapshot["metrics"]["oldest_event_date"],
                    "event_count": snapshot["metrics"]["event_count"],
                    "data_as_of": snapshot["metrics"]["data_as_of"],
                    "roster_source": roster_payload.get("source", "error"),
                    "roster_count": len(roster_names),
                    "roster_reason": roster_payload.get("reason", "unknown"),
                },
            }
        )


@app.route("/bullpen/pitchers", methods=["GET"])
def bullpen_pitchers():
    team_query = request.args.get("team")
    team_name, team_id, source = _resolve_team_name_and_id(team_query)
    if not team_name:
        return jsonify({"status": "error", "error": "No team data available"}), 503

    events = sports_client.get_recent_events(team_id) if source == "thesportsdb" else []
    roster_payload = kbo_data_client.get_team_pitcher_names(team_name)
    roster_names = roster_payload.get("pitcher_names", [])
    if roster_payload.get("source") != "kbodata" or not roster_names:
        return jsonify(
            {
                "status": "error",
                "error_code": "ROSTER_UNAVAILABLE",
                "error": "Roster data is unavailable for this team right now.",
                "team": team_name,
                "team_id": team_id,
                "source": source,
                "roster_source": roster_payload.get("source", "error"),
                "roster_count": len(roster_names),
                "roster_reason": roster_payload.get("reason", "unknown"),
            }
        ), 503

    snapshot = build_bullpen_snapshot(
        team_name,
        events,
        pitcher_names=roster_names,
    )

    return jsonify(
        {
            "status": "success",
            "source": source,
            "team_id": team_id,
            "team": team_name,
            "pitchers": snapshot["pitchers"],
            "as_of": snapshot["as_of"],
            "latest_event_date": snapshot["metrics"]["latest_event_date"],
            "oldest_event_date": snapshot["metrics"]["oldest_event_date"],
            "event_count": snapshot["metrics"]["event_count"],
            "data_as_of": snapshot["metrics"]["data_as_of"],
            "roster_source": roster_payload.get("source", "fallback"),
            "roster_count": len(roster_payload.get("pitcher_names", [])),
            "roster_reason": roster_payload.get("reason", "unknown"),
        }
    )


@app.route("/bullpen/recommend", methods=["POST"])
def bullpen_recommend():
    try:
        payload = request.get_json() or {}
        team_query = payload.get("team")
        inning = int(payload.get("inning", 8))
        score_diff = int(payload.get("score_diff", 0))
        batter_side = str(payload.get("batter_side", "R")).upper()
        count = int(payload.get("count", 2))

        team_name, team_id, source = _resolve_team_name_and_id(team_query)
        if not team_name:
            return jsonify({"status": "error", "error": "No team data available"}), 503

        events = sports_client.get_recent_events(team_id) if source == "thesportsdb" else []
        roster_payload = kbo_data_client.get_team_pitcher_names(team_name)
        roster_names = roster_payload.get("pitcher_names", [])
        if roster_payload.get("source") != "kbodata" or not roster_names:
            return jsonify(
                {
                    "status": "error",
                    "error_code": "ROSTER_UNAVAILABLE",
                    "error": "Roster data is unavailable for recommendation.",
                    "team": team_name,
                    "team_id": team_id,
                    "source": source,
                    "roster_source": roster_payload.get("source", "error"),
                    "roster_count": len(roster_names),
                    "roster_reason": roster_payload.get("reason", "unknown"),
                }
            ), 503

        snapshot = build_bullpen_snapshot(
            team_name,
            events,
            pitcher_names=roster_names,
        )
        picks, reasons = recommend_pitchers(
            snapshot=snapshot,
            inning=inning,
            score_diff=score_diff,
            batter_side=batter_side if batter_side in {"R", "L", "S"} else "R",
            count=max(1, min(3, count)),
        )

        return jsonify(
            {
                "status": "success",
                "source": source,
                "team_id": team_id,
                "team": team_name,
                "context": {
                    "inning": inning,
                    "score_diff": score_diff,
                    "batter_side": batter_side,
                },
                "bullpen": {
                    "energy_index": snapshot["energy_index"],
                    "risk_level": snapshot["risk_level"],
                    "usable_pitchers": snapshot["usable_pitchers"],
                    "latest_event_date": snapshot["metrics"]["latest_event_date"],
                    "oldest_event_date": snapshot["metrics"]["oldest_event_date"],
                    "event_count": snapshot["metrics"]["event_count"],
                    "data_as_of": snapshot["metrics"]["data_as_of"],
                    "roster_source": roster_payload.get("source", "fallback"),
                    "roster_count": len(roster_payload.get("pitcher_names", [])),
                    "roster_reason": roster_payload.get("reason", "unknown"),
                },
                "recommendations": picks,
                "reasons": reasons,
                "as_of": snapshot["as_of"],
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    print("Starting Flask server...")
    print(f"RF Model: {'Loaded' if rf_model else 'Using dummy'}")
    print(f"LSTM Model: {'Loaded' if lstm_model else 'Using dummy'}")
    app.run(host="0.0.0.0", port=5000, debug=True)

