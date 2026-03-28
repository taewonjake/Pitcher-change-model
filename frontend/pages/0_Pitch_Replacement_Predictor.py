import os

import requests
import streamlit as st


st.set_page_config(page_title="투수 교체 예측", page_icon="⚾", layout="centered")
st.title("투수 교체 예측")
st.caption("경기 상황을 입력하면 교체 권장 확률을 계산합니다.")

default_api_url = os.getenv("API_URL", "https://basegram.p-e.kr/api")

with st.sidebar:
    st.header("연결 설정")
    api_url = st.text_input("API URL", value=default_api_url)

st.markdown("### 경기 입력")
col1, col2 = st.columns(2)

with col1:
    inning = st.number_input("현재 이닝", min_value=1, max_value=12, value=6)
    pitch_count = st.number_input("투구 수", min_value=1, max_value=200, value=90)
    velocity_drop = st.number_input("구속 감소(km/h)", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
    earned_runs = st.number_input("자책점", min_value=0, max_value=15, value=2)
    pitcher_type = st.selectbox("투수 유형", ["선발투수", "불펜투수"])
    pitcher_hand = st.selectbox("투수 손", ["R", "L"])

with col2:
    batter_side = st.selectbox("현재 타자 유형", ["R", "L", "S"])
    current_batter_ops = st.slider("현재 타자 OPS", 0.0, 2.0, 0.8, 0.01)
    next_batter_side = st.selectbox("다음 타자 유형", ["R", "L", "S"])
    next_batter_ops = st.slider("다음 타자 OPS", 0.0, 2.0, 0.8, 0.01)

if st.button("예측 실행", type="primary", use_container_width=True):
    payload = {
        "inning": int(inning),
        "pitch_count": int(pitch_count),
        "velocity_drop": float(velocity_drop),
        "earned_runs": int(earned_runs),
        "pitcher_type": pitcher_type,
        "pitcher_hand": pitcher_hand,
        "batter_side": batter_side,
        "current_batter_ops": float(current_batter_ops),
        "next_batter_side": next_batter_side,
        "next_batter_ops": float(next_batter_ops),
    }

    try:
        response = requests.post(f"{api_url}/predict", json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        st.error(f"예측 요청 실패: {exc}")
        st.stop()

    if data.get("status") != "success":
        st.error(f"예측 실패: {data.get('error', 'unknown error')}")
        st.stop()

    st.markdown("### 예측 결과")
    st.metric("최종 교체 확률", f"{float(data.get('final_prob', 0)) * 100:.1f}%")
    st.write(f"권장: **{data.get('recommendation', '-') }**")
    st.write(
        f"RF: {data.get('rf_prob', 0)} / "
        f"LSTM: {data.get('lstm_prob', 0)} / "
        f"Final: {data.get('final_prob', 0)}"
    )
