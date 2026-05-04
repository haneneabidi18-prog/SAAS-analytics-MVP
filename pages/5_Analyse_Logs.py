import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import anthropic

from utils.log_parser import (
    parse_uploaded_file, get_summary_stats,
    compute_qoe_from_logs, build_ai_context, ALL_METRICS
)

st.set_page_config(
    page_title="Analyse de Logs · StreamAnalytics",
    page_icon="📂",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #07070f; }
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
div[data-testid="metric-container"] {
    background: #0f0f20; border: 1px solid #2a2a4a;
    border-radius: 10px; padding: 14px;
}
div[data-testid="metric-container"] label {
    color: #6060a0 !important; font-size: 11px !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e0e0f0 !important; font-family: 'JetBrains Mono', monospace !important;
}
.upload-zone {
    background: #0f0f20;
    border: 2px dashed #2a2a4a;
    border-radius: 16px; padding: 40px;
    text-align: center; transition: border-color .2s;
}
.upload-zone:hover { border-color: #7F77DD; }
.format-pill {
    display: inline-block; background: #1a1a2e;
    border: 1px solid #2a2a4a; border-radius: 20px;
    padding: 4px 12px; font-size: 12px; color: #a0a0c0;
    margin: 3px; font-family: 'JetBrains Mono', monospace;
}
.stat-card {
    background: #0f0f20; border: 1px solid #2a2a4a;
    border-radius: 12px; padding: 16px; margin-bottom: 8px;
}
.section-title {
    font-size: 12px; font-weight: 600; color: #6060a0;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 12px;
}
.anomaly-badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600;
    background: #2e1a1a; color: #E24B4A;
}
.ok-badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600;
    background: #0a1f0a; color: #1D9E75;
}
.stButton > button {
    font-family: 'Space Grotesk', sans-serif; font-weight: 500; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:15px 0 5px;font-size:22px;'>📡</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:18px;font-weight:700;color:#7F77DD;'>StreamAnalytics</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("Dashboard",           use_container_width=True): st.switch_page("pages/1_Dashboard.py")
    if st.button("QoE Score",           use_container_width=True): st.switch_page("pages/2_QoE_Score.py")
    if st.button("AI Decision Engine",  use_container_width=True): st.switch_page("pages/3_AI_Decision_Engine.py")
    if st.button("AI Copilot",          use_container_width=True): st.switch_page("pages/4_AI_Copilot.py")
    if st.button("Demo Interactive",    use_container_width=True): st.switch_page("pages/0_Demo.py")
    if st.button("Analyse de Logs",     use_container_width=True): pass
    st.divider()
    st.markdown("**Options d'analyse**")
    show_raw     = st.toggle("Afficher les données brutes", value=False)
    max_rows_chart = st.slider("Points sur les graphiques", 50, 500, 200)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📂 Analyse de vos logs streaming")
st.markdown("""<span style='background:#7F77DD;color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;'>PREMIUM</span>
<span style='font-size:13px;color:#6060a0;margin-left:10px;'>Uploadez vos vrais logs — obtenez un dashboard et une analyse IA instantanés</span>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Upload zone ────────────────────────────────────────────────────────────────
col_upload, col_sample = st.columns([2, 1])

with col_upload:
    st.markdown('<div class="section-title">Uploadez votre fichier de logs</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        label="Glissez votre fichier ici",
        type=["csv", "json", "jsonl", "log", "txt", "tsv", "ndjson"],
        help="Formats supportés : CSV, JSON, JSONL, fichiers .log texte",
        label_visibility="collapsed",
    )
    st.markdown("""
    <div style='margin-top:8px;'>
        <span style='font-size:12px;color:#6060a0;'>Formats supportés : </span>
        <span class='format-pill'>.csv</span>
        <span class='format-pill'>.json</span>
        <span class='format-pill'>.jsonl</span>
        <span class='format-pill'>.log</span>
        <span class='format-pill'>.tsv</span>
        <span style='font-size:11px;color:#404060;margin-left:6px;'>Max 50 000 lignes</span>
    </div>
    """, unsafe_allow_html=True)

with col_sample:
    st.markdown('<div class="section-title">Pas de logs sous la main ?</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size:13px;color:#a0a0c0;margin-bottom:10px;'>Testez avec nos données d'exemple réalistes</div>", unsafe_allow_html=True)

    sample_type = st.selectbox("Choisir un jeu de données",
        ["Incident CDN — Broadcaster", "Pic de trafic — OTT", "Dégradation qualité — Telco"])

    if st.button("Charger les données exemple", use_container_width=True):
        import numpy as np
        np.random.seed(42)
        n = 200
        if "CDN" in sample_type:
            qoe_vals    = [85]*60 + [45+i*0.5 for i in range(40)] + [42]*50 + [55+i*1.2 for i in range(50)]
            rebuf_vals  = [0.3]*60 + [0.3+i*0.12 for i in range(40)] + [5.2]*50 + [5.2-i*0.1 for i in range(50)]
        elif "Pic" in sample_type:
            qoe_vals    = [83]*80 + [60+abs(40-i) for i in range(80)] + [81]*40
            rebuf_vals  = [0.4]*80 + [0.4+abs(i-40)*0.05 for i in range(80)] + [0.5]*40
        else:
            qoe_vals    = [82 - i*0.3 for i in range(100)] + [52]*60 + [52+i*0.5 for i in range(40)]
            rebuf_vals  = [0.3 + i*0.02 for i in range(100)] + [2.4]*60 + [2.4-i*0.04 for i in range(40)]

        from datetime import datetime, timedelta
        times   = [datetime(2024, 3, 15, 18, 0) + timedelta(minutes=i*3) for i in range(n)]
        viewers = [int(24000 + 3000*np.sin(i*np.pi/50) + np.random.randint(-500,500)) for i in range(n)]
        bitrate = [round(5.2 - (max(0, 82-q)/82)*3.5 + np.random.uniform(-0.2,0.2), 2) for q in qoe_vals]
        latency = [round(2.0 + (5.5 - b)*0.8 + np.random.uniform(-0.2,0.3), 2) for b in bitrate]
        cdns    = ["CDN-EU1"]*80 + ["CDN-FR2"]*80 + ["CDN-US1"]*40
        regions = ["France", "Allemagne", "Espagne", "UK", "Italie"]

        sample_df = pd.DataFrame({
            "timestamp":    times,
            "viewers":      viewers,
            "bitrate":      bitrate[:n],
            "rebuffer_rate":[min(8.0, max(0, v + np.random.uniform(-0.1,0.1))) for v in rebuf_vals[:n]],
            "latency":      latency,
            "startup_time": [round(1.8 + l*0.3 + np.random.uniform(-0.1,0.2), 2) for l in latency],
            "error_rate":   [round(max(0, r*0.08 + np.random.uniform(-0.05, 0.1)), 2) for r in rebuf_vals[:n]],
            "qoe":          [min(100, max(0, round(q + np.random.uniform(-2,2), 1))) for q in qoe_vals[:n]],
            "cdn":          [cdns[i % len(cdns)] for i in range(n)],
            "region":       [regions[i % len(regions)] for i in range(n)],
        })
        st.session_state["sample_df"]   = sample_df
        st.session_state["sample_name"] = sample_type.replace(" — ", "_").replace(" ", "_") + ".csv"
        st.rerun()

# ── Récupération des données ───────────────────────────────────────────────────
df       = None
fmt      = None
filename = None
warnings_list = []

if uploaded:
    df, fmt, warnings_list = parse_uploaded_file(uploaded)
    filename = uploaded.name
    if "sample_df" in st.session_state:
        del st.session_state["sample_df"]

elif "sample_df" in st.session_state:
    df       = st.session_state["sample_df"]
    fmt      = "csv"
    filename = st.session_state.get("sample_name", "sample.csv")

# ── Warnings ───────────────────────────────────────────────────────────────────
for w in warnings_list:
    st.warning(w)

if df is None:
    st.markdown("""
    <div style='background:#0f0f20;border:1px solid #2a2a4a;border-radius:14px;
         padding:50px;text-align:center;color:#6060a0;margin-top:20px;'>
        <div style='font-size:40px;margin-bottom:12px;'>📂</div>
        <div style='font-size:16px;font-weight:500;color:#a0a0c0;'>
            Uploadez un fichier ou chargez des données exemple pour commencer
        </div>
        <div style='font-size:13px;margin-top:8px;'>
            Colonnes détectées automatiquement : viewers, bitrate, rebuffer_rate, latency, startup_time, error_rate, cdn, region...
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Données chargées ───────────────────────────────────────────────────────────
stats = get_summary_stats(df)
qoe   = compute_qoe_from_logs(stats)

# Colonnes métriques disponibles
available_metrics = [m for m in ALL_METRICS if m in df.columns]

st.markdown("<br>", unsafe_allow_html=True)
st.success(f"✅ **{filename}** chargé — {stats['rows']:,} lignes · Format : {fmt.upper()} · {len(available_metrics)} métriques détectées : {', '.join(available_metrics)}")

# ── KPI Banner ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">Vue d\'ensemble</div>', unsafe_allow_html=True)

kpi_cols = st.columns(6)
kpi_defs = [
    ("viewers",       "Viewers moy.",    "",      False),
    ("bitrate",       "Bitrate moy.",    " Mbps", False),
    ("rebuffer_rate", "Rebuffering",     "%",     True),
    ("latency",       "Latence P95",     " s",    True),
    ("startup_time",  "Startup time",    " s",    True),
    ("error_rate",    "Taux d'erreur",   "%",     True),
]
for i, (metric, label, unit, inv) in enumerate(kpi_defs):
    with kpi_cols[i]:
        if metric in stats:
            val = stats[metric]["mean"]
            fmt_val = f"{int(val):,}" if metric == "viewers" else f"{val}{unit}"
            st.metric(label, fmt_val)
        else:
            st.metric(label, "N/A")

# ── QoE Score ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">Score QoE calculé depuis vos logs</div>', unsafe_allow_html=True)

col_g, col_dims = st.columns([1, 2])
with col_g:
    fig_gauge = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = qoe["global"],
        number = {"font": {"size": 48, "color": qoe["color"], "family": "JetBrains Mono"},
                  "suffix": "/100"},
        title  = {"text": "QoE Global", "font": {"size": 12, "color": "#6060a0"}},
        gauge  = {
            "axis": {"range": [0, 100], "tickcolor": "#6060a0"},
            "bar":  {"color": qoe["color"], "thickness": 0.2},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 55],   "color": "rgba(226,75,74,0.12)"},
                {"range": [55, 70],  "color": "rgba(239,159,39,0.12)"},
                {"range": [70, 100], "color": "rgba(29,158,117,0.12)"},
            ],
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0a0c0"),
        height=230, margin=dict(l=20, r=20, t=30, b=0),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.markdown(f"<div style='text-align:center;font-size:16px;font-weight:600;color:{qoe['color']};'>{qoe['label']}</div>", unsafe_allow_html=True)

with col_dims:
    from utils.qoe import LABELS, WEIGHTS
    for key, label in LABELS.items():
        score = qoe["dimensions"][key]
        c     = "#1D9E75" if score >= 70 else "#EF9F27" if score >= 55 else "#E24B4A"
        anomaly = score < 55
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>
            <div style='width:160px;font-size:12px;color:#a0a0c0;'>{label}</div>
            <div style='flex:1;background:#1a1a2e;border-radius:4px;height:8px;overflow:hidden;'>
                <div style='background:{c};width:{int(score)}%;height:8px;border-radius:4px;'></div>
            </div>
            <div style='font-size:16px;font-weight:600;color:{c};font-family:JetBrains Mono;width:45px;text-align:right;'>{score:.0f}</div>
            {"<span class='anomaly-badge'>Anomalie</span>" if anomaly else "<span class='ok-badge'>OK</span>"}
        </div>
        """, unsafe_allow_html=True)

# ── Graphiques temporels ──────────────────────────────────────────────────────
if "timestamp" in df.columns or df.index.dtype == "datetime64[ns]":
    st.markdown("---")
    st.markdown('<div class="section-title">Evolution temporelle</div>', unsafe_allow_html=True)

    try:
        df_plot = df.copy()
        if "timestamp" in df_plot.columns:
            df_plot["timestamp"] = pd.to_datetime(df_plot["timestamp"], errors="coerce")
            df_plot = df_plot.dropna(subset=["timestamp"]).sort_values("timestamp")

        # Sous-échantillonnage
        step = max(1, len(df_plot) // max_rows_chart)
        df_plot = df_plot.iloc[::step]

        FILL_COLORS = {
            "qoe":          ("rgba(127,119,221,0.10)", "#7F77DD"),
            "viewers":      ("rgba(29,158,117,0.10)",  "#1D9E75"),
            "bitrate":      ("rgba(55,138,221,0.10)",  "#378ADD"),
            "rebuffer_rate":("rgba(216,90,48,0.10)",   "#D85A30"),
            "latency":      ("rgba(239,159,39,0.10)",  "#EF9F27"),
            "startup_time": ("rgba(226,75,74,0.10)",   "#E24B4A"),
        }

        chart_metrics = [m for m in ["qoe", "viewers", "bitrate", "rebuffer_rate", "latency"]
                         if m in df_plot.columns]
        if chart_metrics:
            tabs = st.tabs([m.replace("_", " ").title() for m in chart_metrics])
            x_col = "timestamp" if "timestamp" in df_plot.columns else df_plot.index

            for tab, metric in zip(tabs, chart_metrics):
                with tab:
                    fill_c, line_c = FILL_COLORS.get(metric, ("rgba(127,119,221,0.10)", "#7F77DD"))
                    y = pd.to_numeric(df_plot[metric], errors="coerce")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_plot[x_col] if "timestamp" in df_plot.columns else list(range(len(y))),
                        y=y, mode="lines", fill="tozeroy",
                        line=dict(color=line_c, width=2),
                        fillcolor=fill_c, name=metric,
                    ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(15,15,32,0.8)",
                        font=dict(color="#a0a0c0"), height=230,
                        margin=dict(l=0, r=0, t=10, b=0),
                        showlegend=False,
                        xaxis=dict(gridcolor="#1a1a2e", zeroline=False),
                        yaxis=dict(gridcolor="#1a1a2e", zeroline=False),
                    )
                    st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.info(f"Graphiques temporels non disponibles : {e}")

# ── Breakdowns CDN / Region ────────────────────────────────────────────────────
breakdown_cols = [c for c in ["cdn", "region", "device"] if c in df.columns]
if breakdown_cols:
    st.markdown("---")
    st.markdown('<div class="section-title">Repartition</div>', unsafe_allow_html=True)
    b_cols = st.columns(len(breakdown_cols))
    for i, cat in enumerate(breakdown_cols):
        with b_cols[i]:
            counts = df[cat].value_counts().head(8)
            fig_b = px.bar(
                x=counts.values, y=counts.index, orientation="h",
                color=counts.values, color_continuous_scale="Purples",
                labels={"x": "Occurrences", "y": cat.title()},
            )
            fig_b.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,15,32,0.8)",
                font=dict(color="#a0a0c0"), height=200,
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False,
                title=dict(text=cat.title(), font=dict(size=12, color="#6060a0")),
            )
            st.plotly_chart(fig_b, use_container_width=True)

# ── Données brutes ─────────────────────────────────────────────────────────────
if show_raw:
    st.markdown("---")
    st.markdown('<div class="section-title">Donnees brutes (50 premieres lignes)</div>', unsafe_allow_html=True)
    st.dataframe(df.head(50), use_container_width=True, height=300)

# ── AI Copilot — Analyse des logs ──────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">AI Copilot — Analyse de vos logs</div>', unsafe_allow_html=True)

ai_context = build_ai_context(df, stats, qoe, filename)

# Init chat
if "log_messages" not in st.session_state:
    st.session_state["log_messages"] = []

# Analyse automatique au premier chargement
if not st.session_state["log_messages"]:
    col_auto1, col_auto2, col_auto3 = st.columns(3)
    with col_auto1:
        if st.button("🔍 Analyse complète automatique", use_container_width=True, type="primary"):
            st.session_state["log_messages"].append({
                "role": "user",
                "content": "Analyse ces logs streaming en détail. Identifie les anomalies, les tendances, les problèmes critiques et donne-moi 3 recommandations prioritaires avec leur impact estimé sur le QoE."
            })
            st.rerun()
    with col_auto2:
        if st.button("⚠️ Détecter les anomalies", use_container_width=True):
            st.session_state["log_messages"].append({
                "role": "user",
                "content": "Quelles sont les anomalies et incidents détectés dans ces logs ? Donne-moi les timestamps approximatifs et la durée estimée de chaque incident."
            })
            st.rerun()
    with col_auto3:
        if st.button("📈 Analyse de tendances", use_container_width=True):
            st.session_state["log_messages"].append({
                "role": "user",
                "content": "Analyse les tendances dans ces logs : y a-t-il une dégradation progressive ? Des patterns récurrents ? Quels créneaux horaires sont les plus problématiques ?"
            })
            st.rerun()

# Historique
for msg in st.session_state["log_messages"]:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# Input
user_q = st.chat_input("Posez une question sur vos logs...")
if user_q:
    st.session_state["log_messages"].append({"role": "user", "content": user_q})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_q)

if st.session_state["log_messages"] and st.session_state["log_messages"][-1]["role"] == "user":
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analyse des logs en cours..."):
            try:
                api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
                if not api_key:
                    # Mode démo sans clé API
                    last_q = st.session_state["log_messages"][-1]["content"].lower()
                    if "anomalie" in last_q or "incident" in last_q:
                        resp = (
                            f"**Anomalies détectées dans {filename} :**\n\n"
                            f"1. **Pic de rebuffering** — Le taux moyen est à {stats.get('rebuffer_rate', {}).get('mean', 'N/A')}% "
                            f"avec un P95 à {stats.get('rebuffer_rate', {}).get('p95', 'N/A')}%. "
                            f"Dépasse le seuil critique de 2% sur certaines plages.\n\n"
                            f"2. **Dégradation bitrate** — Bitrate moyen à {stats.get('bitrate', {}).get('mean', 'N/A')} Mbps, "
                            f"en dessous de l'optimal (5+ Mbps).\n\n"
                            f"3. **Latence élevée** — P95 à {stats.get('latency', {}).get('p95', 'N/A')}s. "
                            f"Impacte la sync audio/vidéo.\n\n"
                            f"**Action recommandée :** Connectez votre clé API Anthropic pour une analyse IA complète et précise."
                        )
                    else:
                        resp = (
                            f"**Résumé de l'analyse de {filename} :**\n\n"
                            f"- **{stats['rows']:,} événements** analysés\n"
                            f"- **QoE Global : {qoe['global']}/100** — {qoe['label']}\n"
                            f"- Métriques disponibles : {', '.join(available_metrics)}\n\n"
                            f"La dimension la plus dégradée est **{min(qoe['dimensions'], key=qoe['dimensions'].get)}** "
                            f"à {min(qoe['dimensions'].values()):.0f}/100.\n\n"
                            f"💡 *Ajoutez votre clé API Anthropic dans les secrets Streamlit pour une analyse IA complète.*"
                        )
                    st.markdown(resp)
                    st.session_state["log_messages"].append({"role": "assistant", "content": resp})
                else:
                    client = anthropic.Anthropic(api_key=api_key)
                    system = f"""Tu es le Copilot IA de StreamAnalytics Pro, expert en analyse de logs streaming vidéo.
Tu analyses des logs uploadés par un client et fournis des insights actionnables.

=== DONNÉES DU FICHIER ANALYSÉ ===
{ai_context}

=== INSTRUCTIONS ===
- Réponds en français, de manière structurée et professionnelle
- Cite les métriques concrètes de ce fichier dans tes réponses
- Identifie les anomalies, tendances et recommandations prioritaires
- Quantifie l'impact sur le QoE quand c'est possible
- Sois précis sur les timestamps si la donnée est disponible
"""
                    placeholder   = st.empty()
                    full_response = ""
                    with client.messages.stream(
                        model="claude-sonnet-4-20250514", max_tokens=1200,
                        system=system,
                        messages=[{"role": m["role"], "content": m["content"]}
                                  for m in st.session_state["log_messages"]],
                    ) as stream:
                        for text in stream.text_stream:
                            full_response += text
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                    st.session_state["log_messages"].append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Erreur API : {e}")

# Bouton reset chat
if st.session_state["log_messages"]:
    if st.button("🗑 Effacer la conversation", use_container_width=False):
        st.session_state["log_messages"] = []
        st.rerun()
