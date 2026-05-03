import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from utils.data import get_live_metrics, get_timeseries, get_cdn_performance, get_region_breakdown, get_device_breakdown
from utils.qoe  import compute_qoe

st.set_page_config(page_title="Dashboard · StreamAnalytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
div[data-testid="metric-container"] {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 10px; padding: 15px;
}
div[data-testid="metric-container"] label { color: #a0a0c0 !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #ffffff !important; }
.qoe-banner {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #7F77DD; border-radius: 12px;
    padding: 16px 24px; margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:15px 0 5px;font-size:22px;'>📡</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:18px;font-weight:700;color:#7F77DD;'>StreamAnalytics</div>", unsafe_allow_html=True)
    st.divider()
    auto_refresh = st.toggle("Refresh auto (30s)", value=False)
    st.markdown("---")
    st.markdown("**Navigation**")
    if st.button("Dashboard",          use_container_width=True): pass
    if st.button("QoE Score",          use_container_width=True): st.switch_page("pages/2_QoE_Score.py")
    if st.button("AI Decision Engine", use_container_width=True): st.switch_page("pages/3_AI_Decision_Engine.py")
    if st.button("AI Copilot",         use_container_width=True): st.switch_page("pages/4_AI_Copilot.py")
    st.divider()
    st.selectbox("Periode", ["Dernieres 24h", "7 jours", "30 jours"])

# ── Data ──────────────────────────────────────────────────────────────────────
metrics = get_live_metrics()
qoe     = compute_qoe(metrics)

# ── Header ────────────────────────────────────────────────────────────────────
col_t, col_live = st.columns([4, 1])
with col_t:
    st.markdown("## Dashboard Live")
    st.caption(f"Derniere mise a jour : {metrics['timestamp'].strftime('%H:%M:%S')}")
with col_live:
    st.markdown("<div style='background:#0a2e1a;border:1px solid #1D9E75;border-radius:8px;padding:8px 14px;text-align:center;margin-top:20px;color:#1D9E75;font-weight:600;'>LIVE</div>", unsafe_allow_html=True)

# ── QoE Banner ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='qoe-banner'>
    <div style='font-size:12px;color:#a0a0c0;'>QoE Score Global - Temps reel</div>
    <div style='font-size:28px;font-weight:700;color:{qoe["color"]};'>{qoe["global"]}/100 — {qoe["label"]}</div>
    <div style='font-size:11px;color:#6060a0;margin-top:4px;'>Pondere sur 6 dimensions</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Viewers actifs",  f"{metrics['viewers']:,}",        "+12%")
c2.metric("Bitrate moyen",   f"{metrics['bitrate_avg']} Mbps", "+0.1")
c3.metric("Rebuffering",     f"{metrics['rebuffer_rate']}%",   "+0.2%", delta_color="inverse")
c4.metric("Latence P95",     f"{metrics['latency_p95']} s",   "-0.2s")
c5.metric("Taux d erreur",   f"{metrics['error_rate']}%",     "-0.1%", delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)

# ── Mapping fillcolor hex -> rgba valide pour Plotly ─────────────────────────
FILL_COLORS = {
    "#7F77DD": "rgba(127,119,221,0.10)",
    "#1D9E75": "rgba(29,158,117,0.10)",
    "#378ADD": "rgba(55,138,221,0.10)",
    "#D85A30": "rgba(216,90,48,0.10)",
}

# ── Charts ────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("#### Evolution 24h")
    tab1, tab2, tab3, tab4 = st.tabs(["QoE Score", "Viewers", "Bitrate", "Rebuffering"])

    for tab, metric, color in [
        (tab1, "qoe",      "#7F77DD"),
        (tab2, "viewers",  "#1D9E75"),
        (tab3, "bitrate",  "#378ADD"),
        (tab4, "rebuffer", "#D85A30"),
    ]:
        with tab:
            df  = get_timeseries(24, metric)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x         = df["time"],
                y         = df["value"],
                mode      = "lines",
                fill      = "tozeroy",
                line      = dict(color=color, width=2),
                fillcolor = FILL_COLORS[color],
                name      = metric,
            ))
            fig.update_layout(
                paper_bgcolor = "rgba(0,0,0,0)",
                plot_bgcolor  = "rgba(26,26,46,0.5)",
                font          = dict(color="#a0a0c0"),
                height        = 220,
                margin        = dict(l=0, r=0, t=10, b=0),
                showlegend    = False,
                xaxis         = dict(gridcolor="#2a2a4a", zeroline=False),
                yaxis         = dict(gridcolor="#2a2a4a", zeroline=False),
            )
            st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("#### Par region")
    df_reg  = get_region_breakdown()
    fig_reg = px.bar(df_reg, x="Viewers", y="Region", orientation="h",
                     color="Viewers", color_continuous_scale="Purples")
    fig_reg.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,26,46,0.5)",
        font=dict(color="#a0a0c0"), height=250,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown("#### Devices")
    df_dev  = get_device_breakdown()
    fig_dev = px.pie(df_dev, values="Part %", names="Device",
                     color_discrete_sequence=["#7F77DD","#1D9E75","#378ADD","#D85A30"],
                     hole=0.45)
    fig_dev.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0a0c0"),
        height=200, margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_dev, use_container_width=True)

# ── CDN ───────────────────────────────────────────────────────────────────────
st.markdown("#### Performance CDN")
df_cdn   = get_cdn_performance()
cdn_cols = st.columns(len(df_cdn))
for i, (_, row) in enumerate(df_cdn.iterrows()):
    health = row["Uptime %"]
    c = "#1D9E75" if health >= 98 else "#EF9F27" if health >= 95 else "#E24B4A"
    with cdn_cols[i]:
        st.markdown(f"""
        <div style='background:#1a1a2e;border:1px solid {c};border-radius:10px;padding:14px;text-align:center;'>
            <div style='font-size:11px;color:#6060a0;'>{row['CDN']}</div>
            <div style='font-size:22px;font-weight:700;color:{c};margin:6px 0;'>{health}%</div>
            <div style='font-size:11px;color:#808080;'>Latence : {row['Latence ms']}ms</div>
            <div style='font-size:11px;color:#808080;'>{row['Viewers']:,} viewers</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Voir les recommandations AI Decision Engine", use_container_width=True):
    st.switch_page("pages/3_AI_Decision_Engine.py")

if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()
