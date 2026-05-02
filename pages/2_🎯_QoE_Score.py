import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.data import get_live_metrics, get_timeseries
from utils.qoe  import compute_qoe, LABELS, WEIGHTS

st.set_page_config(page_title="QoE Score · StreamAnalytics", page_icon="🎯", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
.dim-card {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 10px; padding: 16px; margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='text-align:center;padding:15px 0 5px;font-size:22px;'>📡</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:18px;font-weight:700;color:#7F77DD;'>StreamAnalytics</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("📊 Dashboard",          use_container_width=True): st.switch_page("pages/1_📊_Dashboard.py")
    if st.button("🎯 QoE Score",          use_container_width=True): pass
    if st.button("🧠 AI Decision Engine", use_container_width=True): st.switch_page("pages/3_🧠_AI_Decision_Engine.py")
    if st.button("🤖 AI Copilot",         use_container_width=True): st.switch_page("pages/4_🤖_AI_Copilot.py")

# ── Data ──────────────────────────────────────────────────────────────────────
metrics = get_live_metrics()
qoe     = compute_qoe(metrics)
dims    = qoe["dimensions"]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🎯 QoE Score — Quality of Experience")
st.caption("Score qualité pondéré calculé en temps réel sur 6 dimensions clés")
st.markdown("""
<span style='background:#7F77DD;color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;'>PREMIUM</span>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gauge principale ──────────────────────────────────────────────────────────
col_gauge, col_detail = st.columns([1, 2])

with col_gauge:
    score = qoe["global"]
    color = qoe["color"]

    fig_gauge = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = score,
        title = {"text": "Score QoE Global", "font": {"size": 14, "color": "#a0a0c0"}},
        number= {"font": {"size": 48, "color": color}, "suffix": "/100"},
        gauge = {
            "axis":       {"range": [0, 100], "tickcolor": "#a0a0c0"},
            "bar":        {"color": color, "thickness": 0.25},
            "bgcolor":    "rgba(0,0,0,0)",
            "bordercolor":"#2a2a4a",
            "steps": [
                {"range": [0, 55],   "color": "rgba(226,75,74,0.15)"},
                {"range": [55, 70],  "color": "rgba(239,159,39,0.15)"},
                {"range": [70, 85],  "color": "rgba(29,158,117,0.15)"},
                {"range": [85, 100], "color": "rgba(29,158,117,0.25)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": score},
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0a0c0"),
        height=280,
        margin=dict(l=20, r=20, t=40, b=0),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown(f"""
    <div style='text-align:center;background:#1a1a2e;border:1px solid {color}55;border-radius:10px;padding:12px;'>
        <div style='font-size:22px;font-weight:700;color:{color};'>{qoe['label']}</div>
        <div style='font-size:12px;color:#6060a0;margin-top:4px;'>Calculé à {metrics['timestamp'].strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

with col_detail:
    st.markdown("#### Détail par dimension")

    dim_colors = {
        (85, 100): "#1D9E75",
        (70, 85):  "#1D9E75",
        (55, 70):  "#EF9F27",
        (0, 55):   "#E24B4A",
    }

    def get_color(score):
        if score >= 85: return "#1D9E75"
        if score >= 70: return "#EF9F27"
        if score >= 55: return "#D85A30"
        return "#E24B4A"

    for key, label in LABELS.items():
        dim_score  = dims[key]
        dim_color  = get_color(dim_score)
        dim_weight = int(WEIGHTS[key] * 100)
        pct        = int(dim_score)

        st.markdown(f"""
        <div class='dim-card'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                <span style='color:#e0e0f0;font-size:14px;font-weight:500;'>{label}</span>
                <div style='display:flex;align-items:center;gap:10px;'>
                    <span style='font-size:11px;color:#6060a0;'>Poids : {dim_weight}%</span>
                    <span style='font-size:18px;font-weight:700;color:{dim_color};'>{dim_score:.0f}</span>
                </div>
            </div>
            <div style='background:#2a2a4a;border-radius:4px;height:8px;overflow:hidden;'>
                <div style='background:{dim_color};width:{pct}%;height:8px;border-radius:4px;transition:width .4s;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Évolution QoE 24h ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 📈 Évolution du QoE Score — dernières 24 heures")

df_qoe = get_timeseries(24, "qoe")
fig_line = go.Figure()

# Zone critique
fig_line.add_hrect(y0=0, y1=55, fillcolor="rgba(226,75,74,0.05)", line_width=0, annotation_text="Critique", annotation_position="right")
fig_line.add_hrect(y0=55, y1=70, fillcolor="rgba(239,159,39,0.05)", line_width=0, annotation_text="Acceptable", annotation_position="right")
fig_line.add_hrect(y0=70, y1=100, fillcolor="rgba(29,158,117,0.05)", line_width=0, annotation_text="Bon", annotation_position="right")

fig_line.add_trace(go.Scatter(
    x=df_qoe["time"], y=df_qoe["value"],
    mode="lines+markers",
    line=dict(color="#7F77DD", width=2.5),
    marker=dict(size=4, color="#7F77DD"),
    fill="tozeroy",
    fillcolor="rgba(127,119,221,0.08)",
    name="QoE Score",
))
fig_line.add_hline(y=70, line_dash="dash", line_color="#EF9F27", line_width=1,
                   annotation_text="Seuil Min 70", annotation_position="left")

fig_line.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(26,26,46,0.5)",
    font=dict(color="#a0a0c0"),
    height=250,
    margin=dict(l=0, r=60, t=20, b=0),
    showlegend=False,
    xaxis=dict(gridcolor="#2a2a4a", zeroline=False),
    yaxis=dict(gridcolor="#2a2a4a", zeroline=False, range=[50, 100]),
)
st.plotly_chart(fig_line, use_container_width=True)

# ── Radar chart ───────────────────────────────────────────────────────────────
st.markdown("#### 🕸 Radar des dimensions QoE")
categories = list(LABELS.values())
values_    = [dims[k] for k in LABELS.keys()]

fig_radar = go.Figure(go.Scatterpolar(
    r     = values_ + [values_[0]],
    theta = categories + [categories[0]],
    fill  = "toself",
    fillcolor="rgba(127,119,221,0.15)",
    line  = dict(color="#7F77DD", width=2),
    name  = "QoE"
))
fig_radar.update_layout(
    polar=dict(
        bgcolor="rgba(26,26,46,0.5)",
        radialaxis=dict(range=[0, 100], gridcolor="#2a2a4a", tickcolor="#a0a0c0"),
        angularaxis=dict(gridcolor="#2a2a4a", tickcolor="#a0a0c0"),
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a0a0c0"),
    height=350,
    showlegend=False,
    margin=dict(l=40, r=40, t=20, b=20),
)
st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🤖 Analyser avec le Copilot AI →", use_container_width=True):
    st.session_state["copilot_prefill"] = (
        f"Mon QoE est à {qoe['global']}/100 ({qoe['label']}). "
        f"La dimension la plus faible est '{min(dims, key=dims.get)}' à {min(dims.values()):.0f}/100. "
        f"Que recommandes-tu pour l'améliorer en priorité ?"
    )
    st.switch_page("pages/4_🤖_AI_Copilot.py")
