import streamlit as st

st.set_page_config(
    page_title="StreamAnalytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS global
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
[data-testid="stSidebar"] .stSelectbox label { color: #a0a0c0 !important; }
.metric-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px;
    color: white;
}
.premium-badge {
    background: linear-gradient(90deg, #7F77DD, #534AB7);
    color: white;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}
div[data-testid="metric-container"] {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    padding: 15px;
}
div[data-testid="metric-container"] label { color: #a0a0c0 !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #ffffff !important; }
.stButton > button {
    background: linear-gradient(90deg, #7F77DD, #534AB7);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
}
.stButton > button:hover { opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# Sidebar logo
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <div style='font-size:28px;'>📡</div>
        <div style='font-size:20px; font-weight:700; color:#7F77DD;'>StreamAnalytics</div>
        <div style='font-size:12px; color:#6060a0; margin-top:4px;'>Platform Premium</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### Navigation")

# Home content
st.markdown("""
<div style='text-align:center; padding: 60px 0 30px 0;'>
    <div style='font-size:48px;'>📡</div>
    <h1 style='font-size:40px; font-weight:700; margin:10px 0;'>StreamAnalytics <span style='color:#7F77DD;'>Pro</span></h1>
    <p style='font-size:18px; color:#888; max-width:600px; margin:0 auto;'>
        Plateforme de monitoring streaming temps réel avec Intelligence Artificielle intégrée
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class='metric-card'>
        <div style='font-size:28px;'>📊</div>
        <h3 style='margin:10px 0 5px 0;'>Dashboard Live</h3>
        <p style='color:#a0a0c0; font-size:14px;'>Métriques temps réel — viewers, bitrate, CDN, latence</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='metric-card' style='border-color:#7F77DD;'>
        <div style='font-size:28px;'>🎯</div>
        <h3 style='margin:10px 0 5px 0;'>QoE Score <span class='premium-badge'>PREMIUM</span></h3>
        <p style='color:#a0a0c0; font-size:14px;'>Score qualité pondéré sur 6 dimensions en temps réel</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class='metric-card' style='border-color:#7F77DD;'>
        <div style='font-size:28px;'>🤖</div>
        <h3 style='margin:10px 0 5px 0;'>AI Decision Engine <span class='premium-badge'>PREMIUM</span></h3>
        <p style='color:#a0a0c0; font-size:14px;'>Recommandations intelligentes basées sur vos données live</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
col4, col5, col6 = st.columns([1, 2, 1])
with col5:
    if st.button("🚀  Ouvrir le Dashboard", use_container_width=True):
        st.switch_page("pages/1_📊_Dashboard.py")

st.markdown("""
<div style='text-align:center; margin-top:50px; color:#555; font-size:13px;'>
    StreamAnalytics Pro · Powered by Claude AI · v2.0
</div>
""", unsafe_allow_html=True)
