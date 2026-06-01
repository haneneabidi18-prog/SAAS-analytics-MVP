import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import streamlit as st
from utils.auth import login, is_authenticated, get_user, logout, PLANS

st.set_page_config(
    page_title="StreamAnalytics Pro",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #07070f; }
[data-testid="stSidebar"] { display: none; }

.login-card {
    background: linear-gradient(135deg, #0f0f1a, #14143a);
    border: 1px solid #7F77DD44;
    border-radius: 16px;
    padding: 40px 44px;
    max-width: 420px;
    margin: 0 auto;
}
.stTextInput > div > div > input {
    background: #0f0f20 !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
    color: #e0e0f0 !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7F77DD !important;
    box-shadow: 0 0 0 2px #7F77DD22 !important;
}
.stTextInput label { color: #a0a0c0 !important; font-size: 13px !important; }
.stButton > button {
    background: linear-gradient(90deg, #7F77DD, #534AB7) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    padding: 10px !important; font-size: 14px !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
.plan-card {
    border-radius: 12px; padding: 18px;
    border: 1px solid #2a2a4a; margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Si déjà connecté → rediriger ─────────────────────────────────────────────
if is_authenticated():
    st.switch_page("pages/1_Dashboard.py")
    st.stop()

# ── LOGO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 40px 0 20px 0;'>
    <div style='font-size:44px;'>📡</div>
    <div style='font-size:26px; font-weight:700; color:#7F77DD; margin-top:8px;'>
        StreamAnalytics <span style='color:#ffffff;'>Pro</span>
    </div>
    <div style='font-size:13px; color:#6060a0; margin-top:4px;'>
        Plateforme de monitoring streaming avec AI
    </div>
</div>
""", unsafe_allow_html=True)

# ── FORMULAIRE DE LOGIN ───────────────────────────────────────────────────────
st.markdown("<div class='login-card'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#e0e0f0;font-size:18px;margin-bottom:20px;text-align:center;'>Connexion</h3>", unsafe_allow_html=True)

username = st.text_input("Identifiant", placeholder="votre identifiant")
password = st.text_input("Mot de passe", type="password", placeholder="••••••••")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Se connecter", use_container_width=True):
    if not username or not password:
        st.error("Veuillez renseigner tous les champs.")
    else:
        success, error = login(username, password)
        if success:
            st.success("Connexion réussie !")
            st.switch_page("pages/1_Dashboard.py")
        else:
            st.error(error)

st.markdown("</div>", unsafe_allow_html=True)

# ── PLANS ─────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;font-size:12px;color:#404060;margin-bottom:14px;'>Choisissez votre plan</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class='plan-card' style='background:#0f0f20;'>
        <div style='font-size:14px;font-weight:600;color:#a0a0c0;'>Basic</div>
        <div style='font-size:20px;font-weight:700;color:#e0e0f0;margin:6px 0;'>Gratuit</div>
        <div style='font-size:11px;color:#1D9E75;'>✓ Dashboard Live</div>
        <div style='font-size:11px;color:#1D9E75;'>✓ Demo Interactive</div>
        <div style='font-size:11px;color:#404060;'>✗ QoE Score</div>
        <div style='font-size:11px;color:#404060;'>✗ AI Decision Engine</div>
        <div style='font-size:11px;color:#404060;'>✗ AI Copilot</div>
        <div style='font-size:11px;color:#404060;'>✗ Analyse de Logs</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class='plan-card' style='background:#14143a;border-color:#7F77DD55;'>
        <div style='font-size:14px;font-weight:600;color:#7F77DD;'>Premium ⭐</div>
        <div style='font-size:20px;font-weight:700;color:#e0e0f0;margin:6px 0;'>149€<span style='font-size:12px;color:#6060a0;'>/mois</span></div>
        <div style='font-size:11px;color:#1D9E75;'>✓ Dashboard Live</div>
        <div style='font-size:11px;color:#1D9E75;'>✓ Demo Interactive</div>
        <div style='font-size:11px;color:#1D9E75;'>✓ QoE Score</div>
        <div style='font-size:11px;color:#1D9E75;'>✓ AI Decision Engine</div>
        <div style='font-size:11px;color:#1D9E75;'>✓ AI Copilot</div>
        <div style='font-size:11px;color:#1D9E75;'>✓ Analyse de Logs</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;margin-top:20px;font-size:12px;color:#404060;'>
    Pas encore de compte ? <span style='color:#7F77DD;'>contact@streamanalytics.pro</span>
</div>
""", unsafe_allow_html=True)
