import os
import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ?˜ì´ì§€ ?¤ì •
st.set_page_config(
    page_title="???¬ìˆ˜ êµì²´ ?ˆì¸¡ ?œìŠ¤??,
    page_icon="??,
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS ?¤í??¼ë§
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

# ?œëª©
st.markdown('<h1 class="main-header">???¬ìˆ˜ êµì²´ ?ˆì¸¡ ?œìŠ¤??(AI Coach)</h1>', unsafe_allow_html=True)
st.markdown("---")

# ?¬ì´?œë°” - API ?¤ì •
with st.sidebar:
    st.header("?™ï¸ ?¤ì •")
    api_url = st.text_input(
        "API URL",
        value=os.getenv("API_URL", "https://basegram.p-e.kr/api"),
        help="Flask ë°±ì—”??API ì£¼ì†Œ"
    )
    
    if st.button("?” API ?°ê²° ?•ì¸"):
        try:
            response = requests.get(f"{api_url}/health", timeout=2)
            if response.status_code == 200:
                health_data = response.json()
                st.success("??API ?°ê²° ?±ê³µ")
                st.json(health_data)
            else:
                st.error("??API ?‘ë‹µ ?¤ë¥˜")
        except requests.exceptions.RequestException as e:
            st.error(f"??API ?°ê²° ?¤íŒ¨: {str(e)}")
            st.info("ë°±ì—”???œë²„ê°€ ?¤í–‰ ì¤‘ì¸ì§€ ?•ì¸?˜ì„¸??")

# ë©”ì¸ ?…ë ¥ ??st.header("?“ ê²½ê¸° ?í™© ?…ë ¥")

col1, col2 = st.columns(2)

with col1:
    st.subheader("?¬ìˆ˜ ?íƒœ")
    inning = st.number_input(
        "?´ë‹",
        min_value=1,
        max_value=9,
        value=6,
        help="?„ì¬ ?´ë‹"
    )
    
    pitch_count = st.number_input(
        "?¬êµ¬ ??,
        min_value=1,
        max_value=200,
        value=90,
        help="?„ì¬ê¹Œì????„ì  ?¬êµ¬ ??
    )
    
    velocity_drop = st.number_input(
        "êµ¬ì† ê°ì†Œ??(km/h)",
        min_value=0.0,
        max_value=10.0,
        value=2.5,
        step=0.1,
        help="ì´ˆë°˜ ?€ë¹?êµ¬ì† ê°ì†Œ??
    )
    
    earned_runs = st.number_input(
        "?„ì  ?¤ì ",
        min_value=0,
        max_value=10,
        value=2,
        help="?„ì¬ê¹Œì????„ì  ?¤ì "
    )
    
    pitcher_type = st.selectbox(
        "?¬ìˆ˜ ? í˜•",
        ["? ë°œ?¬ìˆ˜", "ë¶ˆíœ?¬ìˆ˜"],
        help="? ë°œ?¬ìˆ˜: 100êµ?6?´ë‹ ê¸°ì?, ë¶ˆíœ?¬ìˆ˜: 20êµ?1?´ë‹ ê¸°ì?"
    )
    
    pitcher_hand = st.selectbox(
        "?¬ìˆ˜ ??ë°©í–¥",
        ["R", "L"],
        help="R: ?°íˆ¬, L: ì¢Œíˆ¬"
    )

with col2:
    st.subheader("?€???•ë³´")
    batter_side = st.selectbox(
        "?„ì¬ ?€???€??ë°©í–¥",
        ["R", "L", "S"],
        help="R: ?°í?, L: ì¢Œí?, S: ?¤ìœ„ì¹?
    )
    
    current_batter_ops = st.slider(
        "?„ì¬ ?€??OPS",
        0.0,
        2.0,
        0.8,
        0.01,
        help="?„ì¬ ?€?ì˜ OPS (On-base Plus Slugging, 0.0 ~ 2.0)"
    )
    
    st.markdown("---")
    
    next_batter_side = st.selectbox(
        "?¤ìŒ ?€???€??ë°©í–¥",
        ["R", "L", "S"],
        help="?¤ìŒ ?€?ì˜ ?€??ë°©í–¥"
    )
    
    next_batter_ops = st.slider(
        "?¤ìŒ ?€??OPS",
        0.0,
        2.0,
        0.8,
        0.01,
        help="?¤ìŒ ?€?ì˜ OPS (On-base Plus Slugging, 0.0 ~ 2.0)"
    )

st.markdown("---")

# ?ˆì¸¡ ë²„íŠ¼
if st.button("?¯ ?ˆì¸¡?˜ê¸°", type="primary", use_container_width=True):
    # ?…ë ¥ ?°ì´??ê²€ì¦?    if api_url == "":
        st.error("??API URL???…ë ¥?´ì£¼?¸ìš”.")
    else:
        with st.spinner("?¤– AI ì½”ì¹˜ê°€ ?ë‹¨ ì¤?.."):
            try:
                # API ?¸ì¶œ
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
                        st.error(f"???¤ë¥˜: {res.get('error', 'Unknown error')}")
                    else:
                        # ê²°ê³¼ ?œì‹œ
                        st.markdown("---")
                        st.header("?“Š ?ˆì¸¡ ê²°ê³¼")
                        
                        # ë©”ì¸ ë©”íŠ¸ë¦?                        final_prob = res["final_prob"]
                        recommendation = res["recommendation"]
                        
                        # ìµœì¢… ?•ë¥ ????ì¹´ë“œë¡??œì‹œ
                        st.markdown("### ?¯ ìµœì¢… ?ˆì¸¡ ê²°ê³¼")
                        
                        # ?•ë¥ ???°ë¥¸ ?‰ìƒ ê²°ì • (50% ?´ìƒ?´ë©´ êµì²´ ê¶Œì¥)
                        if final_prob >= 0.5:
                            color = "#ef4444"  # ë¹¨ê°•
                            bg_color = "#fee2e2"
                        elif final_prob >= 0.3:
                            color = "#f59e0b"  # ì£¼í™©
                            bg_color = "#fef3c7"
                        else:
                            color = "#10b981"  # ?¹ìƒ‰
                            bg_color = "#d1fae5"
                        
                        # ??ë©”íŠ¸ë¦?ì¹´ë“œ
                        st.markdown(
                            f"""
                            <div style='background-color: {bg_color}; padding: 2rem; border-radius: 15px; 
                                        border-left: 5px solid {color}; margin: 1rem 0;'>
                                <h2 style='color: {color}; margin: 0; text-align: center; font-size: 3rem;'>
                                    {final_prob*100:.1f}%
                                </h2>
                                <p style='text-align: center; font-size: 1.2rem; color: #666; margin-top: 0.5rem;'>
                                    êµì²´ ê¶Œì¥ ?•ë¥ 
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # ê¶Œì¥ ?¬í•­ ë°•ìŠ¤
                        if recommendation == "êµì²´ ê¶Œì¥":
                            st.markdown(
                                f"""
                                <div class='recommendation-box' style='background-color: #fee2e2; color: #991b1b; 
                                    border: 2px solid #ef4444;'>
                                    ? ï¸ {recommendation}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class='recommendation-box' style='background-color: #d1fae5; color: #065f46; 
                                    border: 2px solid #10b981;'>
                                    ??{recommendation}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        # ê²°ê³¼ ?¤ëª… ?ì„±
                        st.markdown("### ?’¡ ?ë‹¨ ê·¼ê±°")
                        explanation_parts = []
                        
                        # ?¬ìˆ˜ ? í˜•ë³??¼ë¡œ??ê¸°ì?
                        is_starter = pitcher_type == "? ë°œ?¬ìˆ˜"
                        pitch_threshold = 100 if is_starter else 20
                        inning_threshold = 6 if is_starter else 1
                        pitcher_type_kr = "? ë°œ?¬ìˆ˜" if is_starter else "ë¶ˆíœ?¬ìˆ˜"
                        
                        # ?¬êµ¬ ??ë¶„ì„ (?¬ìˆ˜ ? í˜•ë³?
                        if pitch_count >= pitch_threshold:
                            explanation_parts.append(f"??{pitcher_type_kr} ê¸°ì??¼ë¡œ ?¬êµ¬ ?˜ê? {pitch_count}ê°?{pitch_threshold}ê°?ê¸°ì?)ë¡?ë§ì•„ ?¼ë¡œ?„ê? ?’ì„ ê°€?¥ì„±???ˆìŠµ?ˆë‹¤.")
                        elif pitch_count >= pitch_threshold * 0.8:
                            explanation_parts.append(f"??{pitcher_type_kr} ê¸°ì??¼ë¡œ ?¬êµ¬ ?˜ê? {pitch_count}ê°œë¡œ ?ë‹¹?˜ì?ë§?ì£¼ì˜ê°€ ?„ìš”?©ë‹ˆ??")
                        else:
                            explanation_parts.append(f"??{pitcher_type_kr} ê¸°ì??¼ë¡œ ?¬êµ¬ ?˜ê? {pitch_count}ê°œë¡œ ?„ì§ ?¬ìœ ê°€ ?ˆìŠµ?ˆë‹¤.")
                        
                        # ?´ë‹ ë¶„ì„ (?¬ìˆ˜ ? í˜•ë³?
                        if inning > inning_threshold:
                            explanation_parts.append(f"??{pitcher_type_kr} ê¸°ì??¼ë¡œ {inning}?´ë‹({inning_threshold}?´ë‹ ì´ˆê³¼)?¼ë¡œ ?¼ë¡œ?„ê? ?’ì„ ???ˆì–´ êµì²´ ?€?´ë°??ê³ ë ¤?´ì•¼ ?©ë‹ˆ??")
                        elif inning == inning_threshold:
                            explanation_parts.append(f"??{pitcher_type_kr} ê¸°ì??¼ë¡œ {inning}?´ë‹?¼ë¡œ ì£¼ì˜ê°€ ?„ìš”?©ë‹ˆ??")
                        else:
                            explanation_parts.append(f"??{pitcher_type_kr} ê¸°ì??¼ë¡œ {inning}?´ë‹?¼ë¡œ ?„ì§ ?¬ìœ ê°€ ?ˆìŠµ?ˆë‹¤.")
                        
                        # êµ¬ì† ê°ì†Œ ë¶„ì„ (0.8km/hë¶€???´ìƒ)
                        if velocity_drop >= 0.8:
                            explanation_parts.append(f"??êµ¬ì†??{velocity_drop}km/h ê°ì†Œ?˜ì—¬ ?¬êµ¬???€?˜ê? ?°ë ¤?©ë‹ˆ??")
                        elif velocity_drop >= 0.5:
                            explanation_parts.append(f"??êµ¬ì†??{velocity_drop}km/h ê°ì†Œ?˜ì—¬ ì£¼ì˜ê°€ ?„ìš”?©ë‹ˆ??")
                        else:
                            explanation_parts.append(f"??êµ¬ì† ê°ì†Œê°€ {velocity_drop}km/hë¡??¬ì? ?ŠìŠµ?ˆë‹¤.")
                        
                        # ?¤ì  ë¶„ì„ (ë¶ˆíœ?¬ìˆ˜??1?¤ì ë¶€??êµì²´ ?•ë¥  ì¦ê?)
                        if is_starter:
                            # ? ë°œ?¬ìˆ˜ ê¸°ì?
                            if earned_runs > 4:
                                explanation_parts.append(f"???„ì  ?¤ì ??{earned_runs}?ìœ¼ë¡?ë§ì•„ êµì²´ë¥?ê³ ë ¤?´ì•¼ ?©ë‹ˆ??")
                            elif earned_runs > 2:
                                explanation_parts.append(f"???„ì  ?¤ì ??{earned_runs}?ìœ¼ë¡?ì£¼ì˜ê°€ ?„ìš”?©ë‹ˆ??")
                            else:
                                explanation_parts.append(f"???„ì  ?¤ì ??{earned_runs}?ìœ¼ë¡??‘í˜¸?©ë‹ˆ??")
                        else:
                            # ë¶ˆíœ?¬ìˆ˜ ê¸°ì? (1?¤ì ë¶€??êµì²´ ?•ë¥  ì¦ê?)
                            if earned_runs >= 1:
                                explanation_parts.append(f"??ë¶ˆíœ?¬ìˆ˜ ê¸°ì??¼ë¡œ ?„ì  ?¤ì ??{earned_runs}?ìœ¼ë¡?êµì²´ë¥?ê³ ë ¤?´ì•¼ ?©ë‹ˆ??")
                            else:
                                explanation_parts.append(f"???„ì  ?¤ì ??{earned_runs}?ìœ¼ë¡??‘í˜¸?©ë‹ˆ??")
                        
                        # ?„ì¬ ?€??ë¶„ì„
                        if current_batter_ops > 0.9:
                            explanation_parts.append(f"???„ì¬ ?€?ì˜ OPSê°€ {current_batter_ops:.2f}ë¡??’ì•„ ì£¼ì˜ê°€ ?„ìš”?©ë‹ˆ??")
                        else:
                            explanation_parts.append(f"???„ì¬ ?€?ì˜ OPSê°€ {current_batter_ops:.2f}ë¡??ë??˜ê¸° ?˜ì›”?©ë‹ˆ??")
                        
                        # ?¤ìŒ ?€??ë¶„ì„
                        if next_batter_ops > 0.9:
                            explanation_parts.append(f"???¤ìŒ ?€?ì˜ OPSê°€ {next_batter_ops:.2f}ë¡??’ì•„ ë¯¸ë¦¬ êµì²´ë¥?ê³ ë ¤?????ˆìŠµ?ˆë‹¤.")
                        else:
                            explanation_parts.append(f"???¤ìŒ ?€?ì˜ OPSê°€ {next_batter_ops:.2f}ë¡??ë??˜ê¸° ?˜ì›”?©ë‹ˆ??")
                        
                        # ì¢Œìš° ë§¤ì¹˜??ë¶„ì„ (ê°™ì? ???¬ìˆ˜ ? ë¦¬, ?¤ë¥¸ ???€??? ë¦¬)
                        matchup_info = f"{pitcher_hand}??vs {batter_side}?€"
                        # ê°™ì? ??(R-R, L-L) ???¬ìˆ˜ ? ë¦¬
                        # ?¤ë¥¸ ??(R-L, L-R) ???€??? ë¦¬
                        if (pitcher_hand == "L" and batter_side == "L") or (pitcher_hand == "R" and batter_side == "R"):
                            explanation_parts.append(f"???„ì¬ ë§¤ì¹˜??{matchup_info})?€ ?¬ìˆ˜?ê²Œ ? ë¦¬?©ë‹ˆ??")
                        else:
                            explanation_parts.append(f"???„ì¬ ë§¤ì¹˜??{matchup_info})?€ ?€?ì—ê²?? ë¦¬?©ë‹ˆ??")
                        
                        # ?¤ëª… ?œì‹œ (ê°???ª©??ë³„ë„ ì¤„ë¡œ ?œì‹œ)
                        explanation_html = "<div style='background-color: #e8f4f8; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4; color: #1e293b;'>"
                        for part in explanation_parts:
                            explanation_html += f"<p style='margin: 0.5rem 0; color: #1e293b;'>{part}</p>"
                        explanation_html += "</div>"
                        st.markdown(explanation_html, unsafe_allow_html=True)
                        
                        # ê²Œì´ì§€ ì°¨íŠ¸
                        st.subheader("?“ˆ êµì²´ ?•ë¥  ?œê°??)
                        
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number+delta",
                            value=final_prob * 100,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={
                                'text': "êµì²´ ê¶Œì¥ ?•ë¥  (%)",
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
                        
                        # ëª¨ë¸ë³??•ë¥  ë¹„êµ ë°?ì°¨íŠ¸
                        st.subheader("?“Š ëª¨ë¸ë³??ˆì¸¡ ë¹„êµ")
                        
                        model_data = pd.DataFrame({
                            "ëª¨ë¸": ["RandomForest", "LSTM", "?™ìƒë¸?(ìµœì¢…)"],
                            "êµì²´ ?•ë¥  (%)": [
                                res["rf_prob"] * 100,
                                res["lstm_prob"] * 100,
                                res["final_prob"] * 100
                            ]
                        })
                        
                        fig_bar = px.bar(
                            model_data,
                            x="ëª¨ë¸",
                            y="êµì²´ ?•ë¥  (%)",
                            color="êµì²´ ?•ë¥  (%)",
                            color_continuous_scale=["green", "yellow", "red"],
                            text="êµì²´ ?•ë¥  (%)",
                            title="ëª¨ë¸ë³?êµì²´ ?•ë¥  ë¹„êµ"
                        )
                        fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig_bar.update_layout(
                            height=400,
                            showlegend=False,
                            yaxis_range=[0, 100]
                        )
                        
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                        # ?…ë ¥ ?”ì•½
                        with st.expander("?“‹ ?…ë ¥ ?”ì•½ ë³´ê¸°"):
                            st.json(payload)
                
                else:
                    st.error(f"??API ?¤ë¥˜ (?íƒœ ì½”ë“œ: {response.status_code})")
                    try:
                        error_data = response.json()
                        st.json(error_data)
                    except:
                        st.text(response.text)
            
            except requests.exceptions.RequestException as e:
                st.error(f"??API ?°ê²° ?¤íŒ¨: {str(e)}")
                st.info("ë°±ì—”???œë²„ê°€ ?¤í–‰ ì¤‘ì¸ì§€ ?•ì¸?˜ì„¸??")
                st.code("cd backend\npython api/app.py", language="bash")

# ?¸í„°
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 1rem;'>"
    "???¬ìˆ˜ êµì²´ ?ˆì¸¡ ?œìŠ¤??| AI Coach | Powered by RandomForest & LSTM"
    "</div>",
    unsafe_allow_html=True
)



