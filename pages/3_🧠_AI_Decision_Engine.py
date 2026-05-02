import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.data            import get_live_metrics
from utils.qoe             import compute_qoe
from utils.decision_engine import analyze

st.set_page_config(page_title="AI Decision Engine · StreamAnalytics", page_icon="🧠", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
.dec-critical {
    background: linear-gradient(135deg, #2e1a1a, #1a1a2e);
    border: 1px solid #E24B4A55; border-radius: 12px; padding: 18px; margin-bottom: 12px;
}
.dec-warning {
    background: linear-gradient(135deg, #2e2a1a, #1a1a2e);
    border: 1px solid #EF9F2755; border-radius: 12px; padding: 18px; margin-bottom: 12px;
}
.dec-info {
    background: linear-gradient(135deg, #1a1e2e, #1a1a2e);
    border: 1px solid #378ADD55; border-radius: 12px; padding: 18px; margin-bottom: 12px;
}
.conf-pill {
    display: inline-block; padding: 3px 10px;
    border-radius: 20px; font-size: 11px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='text-align:center;padding:15px 0 5px;font-size:22px;'>📡</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:18px;font-weight:700;color:#7F77DD;'>StreamAnalytics</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("📊 Dashboard",          use_container_width=True): st.switch_page("pages/1_📊_Dashboard.py")
    if st.button("🎯 QoE Score",          use_container_width=True): st.switch_page("pages/2_🎯_QoE_Score.py")
    if st.button("🧠 AI Decision Engine", use_container_width=True): pass
    if st.button("🤖 AI Copilot",         use_container_width=True): st.switch_page("pages/4_🤖_AI_Copilot.py")
    st.divider()
    st.markdown("**Seuils d'alerte**")
    thresh_rebuffer = st.slider("Rebuffering max (%)", 0.5, 3.0, 1.0, 0.1)
    thresh_qoe      = st.slider("QoE minimum",         40,  90,  70)
    thresh_cdn      = st.slider("Uptime CDN min (%)",  90,  99,  97)

# ── Data ──────────────────────────────────────────────────────────────────────
metrics   = get_live_metrics()
qoe       = compute_qoe(metrics)
decisions = analyze(metrics, qoe)

# Filtre custom selon les seuils sidebar
# (En production, passer les seuils à analyze())

# ── Header ────────────────────────────────────────────────────────────────────
col_h, col_badge = st.columns([3, 1])
with col_h:
    st.markdown("## 🧠 AI Decision Engine")
    st.caption("Recommandations intelligentes générées automatiquement depuis vos métriques live")
with col_badge:
    st.markdown("""
    <div style='background:#1a1a2e;border:1px solid #7F77DD55;border-radius:8px;padding:10px;text-align:center;margin-top:20px;'>
        <div style='font-size:11px;color:#6060a0;'>Décisions actives</div>
        <div style='font-size:28px;font-weight:700;color:#7F77DD;'>""" + str(len(decisions)) + """</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("""<span style='background:#7F77DD;color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;'>PREMIUM</span>""", unsafe_allow_html=True)

# ── Résumé priorités ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
n_crit = sum(1 for d in decisions if d.priority == "critical")
n_warn = sum(1 for d in decisions if d.priority == "warning")
n_info = sum(1 for d in decisions if d.priority == "info")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div style='background:#2e1a1a;border:1px solid #E24B4A55;border-radius:10px;padding:14px;text-align:center;'>
        <div style='font-size:11px;color:#E24B4A;'>CRITIQUES</div>
        <div style='font-size:32px;font-weight:700;color:#E24B4A;'>{n_crit}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div style='background:#2e2a1a;border:1px solid #EF9F2755;border-radius:10px;padding:14px;text-align:center;'>
        <div style='font-size:11px;color:#EF9F27;'>AVERTISSEMENTS</div>
        <div style='font-size:32px;font-weight:700;color:#EF9F27;'>{n_warn}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div style='background:#1a1e2e;border:1px solid #378ADD55;border-radius:10px;padding:14px;text-align:center;'>
        <div style='font-size:11px;color:#378ADD;'>INFORMATIFS</div>
        <div style='font-size:32px;font-weight:700;color:#378ADD;'>{n_info}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div style='background:#1a2e1a;border:1px solid #1D9E7555;border-radius:10px;padding:14px;text-align:center;'>
        <div style='font-size:11px;color:#1D9E75;'>QOE ACTUEL</div>
        <div style='font-size:32px;font-weight:700;color:{qoe["color"]};'>{qoe["global"]}/100</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Recommandations")

# ── Décisions ─────────────────────────────────────────────────────────────────
priority_class = {"critical": "dec-critical", "warning": "dec-warning", "info": "dec-info"}
priority_color = {"critical": "#E24B4A", "warning": "#EF9F27", "info": "#378ADD"}
conf_bg        = lambda c: "#2e1a1a" if c >= 90 else "#2e2a1a" if c >= 75 else "#1a1e2e"
conf_col       = lambda c: "#E24B4A" if c >= 90 else "#EF9F27" if c >= 75 else "#378ADD"

for i, dec in enumerate(decisions):
    cls   = priority_class.get(dec.priority, "dec-info")
    pcolor= priority_color.get(dec.priority, "#378ADD")

    st.markdown(f"""
    <div class='{cls}'>
        <div style='display:flex;align-items:flex-start;gap:14px;'>
            <div style='font-size:24px;margin-top:2px;'>{dec.icon}</div>
            <div style='flex:1;'>
                <div style='font-size:16px;font-weight:600;color:#e0e0f0;margin-bottom:4px;'>{dec.title}</div>
                <div style='font-size:13px;color:#a0a0c0;line-height:1.6;margin-bottom:8px;'>{dec.description}</div>
                <div style='font-size:12px;color:{pcolor};margin-bottom:10px;'>📈 {dec.impact}</div>
                <div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;'>
                    <span class='conf-pill' style='background:{conf_bg(dec.confidence)};color:{conf_col(dec.confidence)};'>
                        Confiance {dec.confidence}%
                    </span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([2, 2, 3])
    with col_a:
        if st.button(f"✅ {dec.action_label}", key=f"apply_{i}", use_container_width=True):
            st.toast(f"Action '{dec.action_label}' déclenchée !", icon="✅")
    with col_b:
        if st.button(f"🤖 Demander au Copilot", key=f"copilot_{i}", use_container_width=True):
            st.session_state["copilot_prefill"] = dec.copilot_prompt
            st.switch_page("pages/4_🤖_AI_Copilot.py")
    with col_c:
        if st.button(f"✕ Ignorer", key=f"dismiss_{i}", use_container_width=True):
            st.toast("Recommandation ignorée", icon="✕")

    st.markdown("<br>", unsafe_allow_html=True)

# ── Refresh ───────────────────────────────────────────────────────────────────
st.divider()
col_r1, col_r2 = st.columns(2)
with col_r1:
    if st.button("🔄 Rafraîchir l'analyse", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_r2:
    if st.button("🤖 Ouvrir le Copilot AI complet →", use_container_width=True):
        st.switch_page("pages/4_🤖_AI_Copilot.py")
