import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="⚾ 투수 교체 예측 시스템",
    page_icon="⚾",
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        padding: 1rem 0;
        font-weight: bold;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .recommendation-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<h1 class="main-header">⚾ 투수 교체 예측 시스템 (AI Coach)</h1>', unsafe_allow_html=True)
st.markdown("---")

# 사이드바 - API 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_url = st.text_input(
        "API URL",
        value="http://localhost:5000",
        help="Flask 백엔드 API 주소"
    )
    
    if st.button("🔍 API 연결 확인"):
        try:
            response = requests.get(f"{api_url}/health", timeout=2)
            if response.status_code == 200:
                health_data = response.json()
                st.success("✅ API 연결 성공")
                st.json(health_data)
            else:
                st.error("❌ API 응답 오류")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ API 연결 실패: {str(e)}")
            st.info("백엔드 서버가 실행 중인지 확인하세요.")

# 메인 입력 폼
st.header("📝 경기 상황 입력")

col1, col2 = st.columns(2)

with col1:
    st.subheader("투수 상태")
    inning = st.number_input(
        "이닝",
        min_value=1,
        max_value=9,
        value=6,
        help="현재 이닝"
    )
    
    pitch_count = st.number_input(
        "투구 수",
        min_value=1,
        max_value=200,
        value=90,
        help="현재까지의 누적 투구 수"
    )
    
    velocity_drop = st.number_input(
        "구속 감소량 (km/h)",
        min_value=0.0,
        max_value=10.0,
        value=2.5,
        step=0.1,
        help="초반 대비 구속 감소량"
    )
    
    earned_runs = st.number_input(
        "누적 실점",
        min_value=0,
        max_value=10,
        value=2,
        help="현재까지의 누적 실점"
    )
    
    pitcher_type = st.selectbox(
        "투수 유형",
        ["선발투수", "불펜투수"],
        help="선발투수: 100구/6이닝 기준, 불펜투수: 20구/1이닝 기준"
    )
    
    pitcher_hand = st.selectbox(
        "투수 손 방향",
        ["R", "L"],
        help="R: 우투, L: 좌투"
    )

with col2:
    st.subheader("타자 정보")
    batter_side = st.selectbox(
        "현재 타자 타석 방향",
        ["R", "L", "S"],
        help="R: 우타, L: 좌타, S: 스위치"
    )
    
    current_batter_ops = st.slider(
        "현재 타자 OPS",
        0.0,
        2.0,
        0.8,
        0.01,
        help="현재 타자의 OPS (On-base Plus Slugging, 0.0 ~ 2.0)"
    )
    
    st.markdown("---")
    
    next_batter_side = st.selectbox(
        "다음 타자 타석 방향",
        ["R", "L", "S"],
        help="다음 타자의 타석 방향"
    )
    
    next_batter_ops = st.slider(
        "다음 타자 OPS",
        0.0,
        2.0,
        0.8,
        0.01,
        help="다음 타자의 OPS (On-base Plus Slugging, 0.0 ~ 2.0)"
    )

st.markdown("---")

# 예측 버튼
if st.button("🎯 예측하기", type="primary", use_container_width=True):
    # 입력 데이터 검증
    if api_url == "":
        st.error("❌ API URL을 입력해주세요.")
    else:
        with st.spinner("🤖 AI 코치가 판단 중..."):
            try:
                # API 호출
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
                    "next_batter_ops": float(next_batter_ops)
                }
                
                response = requests.post(
                    f"{api_url}/predict",
                    json=payload,
                    timeout=5
                )
                
                if response.status_code == 200:
                    res = response.json()
                    
                    if res.get("status") == "error":
                        st.error(f"❌ 오류: {res.get('error', 'Unknown error')}")
                    else:
                        # 결과 표시
                        st.markdown("---")
                        st.header("📊 예측 결과")
                        
                        # 메인 메트릭
                        final_prob = res["final_prob"]
                        recommendation = res["recommendation"]
                        
                        # 최종 확률을 큰 카드로 표시
                        st.markdown("### 🎯 최종 예측 결과")
                        
                        # 확률에 따른 색상 결정 (50% 이상이면 교체 권장)
                        if final_prob >= 0.5:
                            color = "#ef4444"  # 빨강
                            bg_color = "#fee2e2"
                        elif final_prob >= 0.3:
                            color = "#f59e0b"  # 주황
                            bg_color = "#fef3c7"
                        else:
                            color = "#10b981"  # 녹색
                            bg_color = "#d1fae5"
                        
                        # 큰 메트릭 카드
                        st.markdown(
                            f"""
                            <div style='background-color: {bg_color}; padding: 2rem; border-radius: 15px; 
                                        border-left: 5px solid {color}; margin: 1rem 0;'>
                                <h2 style='color: {color}; margin: 0; text-align: center; font-size: 3rem;'>
                                    {final_prob*100:.1f}%
                                </h2>
                                <p style='text-align: center; font-size: 1.2rem; color: #666; margin-top: 0.5rem;'>
                                    교체 권장 확률
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # 권장 사항 박스
                        if recommendation == "교체 권장":
                            st.markdown(
                                f"""
                                <div class='recommendation-box' style='background-color: #fee2e2; color: #991b1b; 
                                    border: 2px solid #ef4444;'>
                                    ⚠️ {recommendation}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class='recommendation-box' style='background-color: #d1fae5; color: #065f46; 
                                    border: 2px solid #10b981;'>
                                    ✅ {recommendation}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        # 결과 설명 생성
                        st.markdown("### 💡 판단 근거")
                        explanation_parts = []
                        
                        # 투수 유형별 피로도 기준
                        is_starter = pitcher_type == "선발투수"
                        pitch_threshold = 100 if is_starter else 20
                        inning_threshold = 6 if is_starter else 1
                        pitcher_type_kr = "선발투수" if is_starter else "불펜투수"
                        
                        # 투구 수 분석 (투수 유형별)
                        if pitch_count >= pitch_threshold:
                            explanation_parts.append(f"• {pitcher_type_kr} 기준으로 투구 수가 {pitch_count}개({pitch_threshold}개 기준)로 많아 피로도가 높을 가능성이 있습니다.")
                        elif pitch_count >= pitch_threshold * 0.8:
                            explanation_parts.append(f"• {pitcher_type_kr} 기준으로 투구 수가 {pitch_count}개로 적당하지만 주의가 필요합니다.")
                        else:
                            explanation_parts.append(f"• {pitcher_type_kr} 기준으로 투구 수가 {pitch_count}개로 아직 여유가 있습니다.")
                        
                        # 이닝 분석 (투수 유형별)
                        if inning > inning_threshold:
                            explanation_parts.append(f"• {pitcher_type_kr} 기준으로 {inning}이닝({inning_threshold}이닝 초과)으로 피로도가 높을 수 있어 교체 타이밍을 고려해야 합니다.")
                        elif inning == inning_threshold:
                            explanation_parts.append(f"• {pitcher_type_kr} 기준으로 {inning}이닝으로 주의가 필요합니다.")
                        else:
                            explanation_parts.append(f"• {pitcher_type_kr} 기준으로 {inning}이닝으로 아직 여유가 있습니다.")
                        
                        # 구속 감소 분석 (0.8km/h부터 이상)
                        if velocity_drop >= 0.8:
                            explanation_parts.append(f"• 구속이 {velocity_drop}km/h 감소하여 투구력 저하가 우려됩니다.")
                        elif velocity_drop >= 0.5:
                            explanation_parts.append(f"• 구속이 {velocity_drop}km/h 감소하여 주의가 필요합니다.")
                        else:
                            explanation_parts.append(f"• 구속 감소가 {velocity_drop}km/h로 크지 않습니다.")
                        
                        # 실점 분석 (불펜투수는 1실점부터 교체 확률 증가)
                        if is_starter:
                            # 선발투수 기준
                            if earned_runs > 4:
                                explanation_parts.append(f"• 누적 실점이 {earned_runs}점으로 많아 교체를 고려해야 합니다.")
                            elif earned_runs > 2:
                                explanation_parts.append(f"• 누적 실점이 {earned_runs}점으로 주의가 필요합니다.")
                            else:
                                explanation_parts.append(f"• 누적 실점이 {earned_runs}점으로 양호합니다.")
                        else:
                            # 불펜투수 기준 (1실점부터 교체 확률 증가)
                            if earned_runs >= 1:
                                explanation_parts.append(f"• 불펜투수 기준으로 누적 실점이 {earned_runs}점으로 교체를 고려해야 합니다.")
                            else:
                                explanation_parts.append(f"• 누적 실점이 {earned_runs}점으로 양호합니다.")
                        
                        # 현재 타자 분석
                        if current_batter_ops > 0.9:
                            explanation_parts.append(f"• 현재 타자의 OPS가 {current_batter_ops:.2f}로 높아 주의가 필요합니다.")
                        else:
                            explanation_parts.append(f"• 현재 타자의 OPS가 {current_batter_ops:.2f}로 상대하기 수월합니다.")
                        
                        # 다음 타자 분석
                        if next_batter_ops > 0.9:
                            explanation_parts.append(f"• 다음 타자의 OPS가 {next_batter_ops:.2f}로 높아 미리 교체를 고려할 수 있습니다.")
                        else:
                            explanation_parts.append(f"• 다음 타자의 OPS가 {next_batter_ops:.2f}로 상대하기 수월합니다.")
                        
                        # 좌우 매치업 분석 (같은 손=투수 유리, 다른 손=타자 유리)
                        matchup_info = f"{pitcher_hand}투 vs {batter_side}타"
                        # 같은 손 (R-R, L-L) → 투수 유리
                        # 다른 손 (R-L, L-R) → 타자 유리
                        if (pitcher_hand == "L" and batter_side == "L") or (pitcher_hand == "R" and batter_side == "R"):
                            explanation_parts.append(f"• 현재 매치업({matchup_info})은 투수에게 유리합니다.")
                        else:
                            explanation_parts.append(f"• 현재 매치업({matchup_info})은 타자에게 유리합니다.")
                        
                        # 설명 표시 (각 항목을 별도 줄로 표시)
                        explanation_html = "<div style='background-color: #e8f4f8; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4; color: #1e293b;'>"
                        for part in explanation_parts:
                            explanation_html += f"<p style='margin: 0.5rem 0; color: #1e293b;'>{part}</p>"
                        explanation_html += "</div>"
                        st.markdown(explanation_html, unsafe_allow_html=True)
                        
                        # 게이지 차트
                        st.subheader("📈 교체 확률 시각화")
                        
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number+delta",
                            value=final_prob * 100,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={
                                'text': "교체 권장 확률 (%)",
                                'font': {'size': 24}
                            },
                            delta={'reference': 50},
                            gauge={
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "#f87171" if final_prob >= 0.5 else "#34d399"},
                                'steps': [
                                    {'range': [0, 30], 'color': "lightgray"},
                                    {'range': [30, 50], 'color': "gray"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 50
                                }
                            }
                        ))
                        
                        fig_gauge.update_layout(
                            height=300,
                            margin=dict(l=20, r=20, t=40, b=20)
                        )
                        
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                        # 모델별 확률 비교 바 차트
                        st.subheader("📊 모델별 예측 비교")
                        
                        model_data = pd.DataFrame({
                            "모델": ["RandomForest", "LSTM", "앙상블 (최종)"],
                            "교체 확률 (%)": [
                                res["rf_prob"] * 100,
                                res["lstm_prob"] * 100,
                                res["final_prob"] * 100
                            ]
                        })
                        
                        fig_bar = px.bar(
                            model_data,
                            x="모델",
                            y="교체 확률 (%)",
                            color="교체 확률 (%)",
                            color_continuous_scale=["green", "yellow", "red"],
                            text="교체 확률 (%)",
                            title="모델별 교체 확률 비교"
                        )
                        fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig_bar.update_layout(
                            height=400,
                            showlegend=False,
                            yaxis_range=[0, 100]
                        )
                        
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                        # 입력 요약
                        with st.expander("📋 입력 요약 보기"):
                            st.json(payload)
                
                else:
                    st.error(f"❌ API 오류 (상태 코드: {response.status_code})")
                    try:
                        error_data = response.json()
                        st.json(error_data)
                    except:
                        st.text(response.text)
            
            except requests.exceptions.RequestException as e:
                st.error(f"❌ API 연결 실패: {str(e)}")
                st.info("백엔드 서버가 실행 중인지 확인하세요.")
                st.code("cd backend\npython api/app.py", language="bash")

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 1rem;'>"
    "⚾ 투수 교체 예측 시스템 | AI Coach | Powered by RandomForest & LSTM"
    "</div>",
    unsafe_allow_html=True
)



