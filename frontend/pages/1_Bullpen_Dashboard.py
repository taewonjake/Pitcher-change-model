import os
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="우리 팀 불펜 체력 대시보드", page_icon="⚾", layout="wide")

st.title("우리 팀 불펜 체력 대시보드")
st.caption("TheSportsDB 기반 MVP + 로컬 계산 로직")

with st.sidebar:
    default_api_url = os.getenv("API_URL", "https://basegram.p-e.kr/api")
    api_url = st.text_input("API URL", value=default_api_url)
    st.markdown("---")
    inning = st.slider("현재 이닝", 1, 12, 8)
    score_diff = st.slider("점수차(우리팀-상대)", -10, 10, 0)
    batter_side = st.selectbox("다음 타자 유형", ["R", "L", "S"])


def call_api(method: str, url: str, timeout: int = 25, **kwargs):
    try:
        request_timeout = None if timeout <= 0 else timeout
        response = requests.request(method, url, timeout=request_timeout, **kwargs)
        try:
            payload = response.json()
        except Exception:
            payload = {}

        if response.status_code >= 400:
            detail = payload.get("error", response.text)
            reason = payload.get("roster_reason")
            code = payload.get("error_code")
            if reason:
                detail = f"{detail} (reason: {reason})"
            if code:
                detail = f"[{code}] {detail}"
            return None, detail

        return payload, None
    except Exception as e:
        return None, str(e)


def call_api_with_loading(method: str, url: str, loading_prefix: str, **kwargs):
    placeholder = st.empty()
    dots = [".", "..", "..."]
    timeout = int(kwargs.pop("timeout", 25))
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(call_api, method, url, timeout=timeout, **kwargs)
        idx = 0
        while not future.done():
            placeholder.info(f"{loading_prefix} 로딩 중{dots[idx % 3]} (초기 1회는 최대 1분 정도 걸릴 수 있어요)")
            idx += 1
            time.sleep(0.35)

    placeholder.empty()
    return future.result()


teams_res, err = call_api_with_loading("GET", f"{api_url}/teams", "팀 목록", timeout=20)
if err:
    st.error(f"팀 목록을 불러오지 못했습니다: {err}")
    st.stop()

teams = teams_res.get("teams", [])
if not teams:
    st.warning("표시할 팀 데이터가 없습니다.")
    st.stop()

team_names = [t.get("name", "") for t in teams]
selected_team = st.selectbox("팀 선택", team_names)

api_timeout = int(os.getenv("FRONTEND_API_TIMEOUT_SEC", "120"))

status_res, err = call_api_with_loading(
    "GET",
    f"{api_url}/bullpen/status",
    "불펜 상태",
    params={"team": selected_team},
    timeout=api_timeout,
)
if err:
    st.error(f"불펜 상태를 불러오지 못했습니다: {err}")
    st.stop()

pitchers_res, err = call_api_with_loading(
    "GET",
    f"{api_url}/bullpen/pitchers",
    "투수 정보",
    params={"team": selected_team},
    timeout=api_timeout,
)
if err:
    st.error(f"투수 상태를 불러오지 못했습니다: {err}")
    st.stop()

rec_res, err = call_api_with_loading(
    "POST",
    f"{api_url}/bullpen/recommend",
    "추천 계산",
    json={
        "team": selected_team,
        "inning": inning,
        "score_diff": score_diff,
        "batter_side": batter_side,
        "count": 2,
    },
    timeout=api_timeout,
)
if err:
    st.error(f"추천 결과를 불러오지 못했습니다: {err}")
    st.stop()

bullpen = status_res.get("bullpen", {})
metrics = bullpen.get("metrics", {})

c1, c2, c3 = st.columns(3)
c1.metric("불펜 에너지 지수", bullpen.get("energy_index", "-"))
c2.metric("팀 위험도", bullpen.get("risk_level", "-"))
c3.metric("상위 3명 평균 체력", metrics.get("top3_avg_energy", "-"))

st.markdown("### 투수별 상태 카드")
pitchers = pitchers_res.get("pitchers", [])
if pitchers:
    df = pd.DataFrame(pitchers)
    fig = px.bar(
        df.sort_values("energy_score", ascending=False),
        x="name",
        y="energy_score",
        color="fatigue_grade",
        hover_data=["handed", "availability", "availability_label"],
        title="투수별 체력 점수(0-100)",
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

    show_df = df[["name", "handed", "energy_score", "fatigue_grade", "availability", "availability_label"]].copy()
    show_df.columns = ["이름", "투구손", "체력점수", "피로등급", "등판가능성", "가능성등급"]
    st.dataframe(show_df, use_container_width=True)

st.markdown("### 상황별 추천")
recs = rec_res.get("recommendations", [])
reasons = rec_res.get("reasons", [])

for idx, rec in enumerate(recs, start=1):
    st.markdown(
        f"{idx}. **{rec.get('name')}** ({rec.get('handed')}투) | "
        f"체력 {rec.get('energy_score')} | 등판가능성 {rec.get('availability')} | 추천점수 {rec.get('recommendation_score')}"
    )

st.markdown("### 추천 이유 3줄")
for line in reasons:
    st.write(f"- {line}")

with st.expander("원본 API 응답 보기"):
    st.json({"teams": teams_res, "status": status_res, "pitchers": pitchers_res, "recommend": rec_res})
