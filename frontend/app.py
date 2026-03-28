import os

import requests
import streamlit as st


st.set_page_config(
    page_title="불펜 대시보드 홈",
    page_icon="⚾",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("불펜 대시보드 홈")
st.caption("왼쪽 사이드바에서 `Bullpen Dashboard` 페이지를 선택해 주세요.")

default_api_url = os.getenv("API_URL", "https://basegram.p-e.kr/api")

with st.sidebar:
    st.header("연결 설정")
    api_url = st.text_input("API URL", value=default_api_url)
    run_check = st.button("API 헬스 체크")

if run_check:
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        response.raise_for_status()
        st.success("API 연결 성공")
        st.json(response.json())
    except Exception as exc:
        st.error(f"API 연결 실패: {exc}")

st.info("서비스 점검: `/api/infra/status` 응답이 정상인지 함께 확인해 주세요.")
