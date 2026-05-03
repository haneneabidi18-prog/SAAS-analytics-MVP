import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import time
import anthropic

from utils.demo_scenarios import INDUSTRIES, SCENARIOS, get_roi_data

st.set_page_config(
    page_title="StreamAnalytics Pro — Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS Demo ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

.stApp { background: #07070f; }
[data-testid="stSidebar"] { display: none; }

/* Header demo */
.demo-header {
    background: linear-gradient(135deg, #0d0d20 0%, #12122a 50%, #0d0d20 100%);
    border-bottom: 1px solid #7F77DD33;
    padding: 16px 32px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
}
.demo-logo { font-size: 20px; font-weight: 700; color: #7F77DD; letter-spacing: -0.5px; }
.demo-badge {
    background: linear-gradient(90deg, #7F77DD22, #534AB722);
    border: 1px solid #7F77DD55;
    color: #7F77DD; padding: 4px 14px; border-radius: 20px;
    font-size: 12px; font-weight: 600; letter-spacing: 1px;
}
.live-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #1D9E75; border-radius: 50%;
    animation: blink 1.2s ease-in-out infinite;
    margin-right: 6px;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* Industry cards */
.industry-card {
    background: #0f0f20;
    border: 1px solid #2a2a4a;
    border-radius: 14px; padding: 20px; cursor: pointer;
    transition: all .2s; text-align: center;
}
.industry-card:hover { border-color: #7F77DD; transform: translateY(-2px); }
.industry-card.selected { border-color: #7F77DD; background: #14143a; box-shadow: 0 0 20px #7F77DD22; }

/* Scenario buttons */
.scenario-btn {
    background: #0f0f20; border-radius: 12px;
    padding: 16px; margin-bottom: 8px;
    border: 1px solid #2a2a4a; cursor: pointer;
    transition: all .2s;
}

/* KPI Cards */
.kpi-card {
    background: #0f0f20;
    border: 1px solid #2a2a4a;
    border-radius: 12px; padding: 18px; text-align: center;
}
.kpi-value { font-size: 32px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.kpi-label { font-size: 11px; color: #6060a0; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; }

/* QoE gauge color zones */
.alert-box {
    background: #0f0f20;
    border-radius: 12px; padding: 16px 20px;
    border-left: 3px solid #7F77DD;
    font-size: 13px; line-height: 1.7; color: #c0c0e0;
    font-family: 'Space Grotesk', sans-serif;
}

/* ROI Section */
.roi-card {
    background: linear-gradient(135deg, #0f0f20, #141428);
    border: 1px solid #7F77DD44;
    border-radius: 14px; padding: 24px; text-align: center;
}
.roi-value { font-size: 36px; font-weight: 700; color: #1D9E75; font-family: 'JetBrains Mono', monospace; }
.roi-label { font-size: 12px; color: #6060a0; margin-top: 6px; }

/* Section title */
.section-title {
    font-size: 13px; font-weight: 600; color: #6060a0;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 14px; display: flex; align-items: center; gap: 8px;
}

/* Severity badge */
.sev-critical { color: #E24B4A; }
.sev-warning  { color: #EF9F27; }
.sev-ok       { color: #1D9E75; }
.sev-info     { color: #7F77DD; }

div[data-testid="metric-container"] {
    background: #0f0f20; border: 1px solid #2a2a4a;
    border-radius: 10px; padding: 14px;
}
div[data-testid="metric-container"] label { color: #6060a0 !important; font-size: 11px !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e0e0f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stTabs [data-baseweb="tab"] { color: #6060a0; }
.stTabs [aria-selected="true"] { color: #7F77DD !important; }
.stButton > button {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="demo-header">
    <div class="demo-logo">📡 StreamAnalytics Pro</div>
    <div class="demo-badge">DEMO INTERACTIVE</div>
    <div style="font-size:13px;color:#6060a0;">
        <span class="live-dot"></span>Données simulées en temps réel
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Init session state ────────────────────────────────────────────────────────
if "demo_industry"  not in st.session_state: st.session_state["demo_industry"]  = "media"
if "demo_scenario"  not in st.session_state: st.session_state["demo_scenario"]  = "normal"
if "demo_messages"  not in st.session_state: st.session_state["demo_messages"]  = []
if "scenario_triggered" not in st.session_state: st.session_state["scenario_triggered"] = False

industry_id = st.session_state["demo_industry"]
scenario_id = st.session_state["demo_scenario"]
industry    = INDUSTRIES[industry_id]
scenario    = SCENARIOS[scenario_id]
roi         = get_roi_data(industry_id, scenario_id)

# ── STEP 1 — Choix industrie ──────────────────────────────────────────────────
st.markdown('<div class="section-title">① Choisissez votre secteur</div>', unsafe_allow_html=True)

ind_cols = st.columns(4)
for i, (ind_id, ind) in enumerate(INDUSTRIES.items()):
    with ind_cols[i]:
        selected = ind_id == industry_id
        border   = ind["color"] if selected else "#2a2a4a"
        bg       = "#14143a" if selected else "#0f0f20"
        if st.button(
            f"{ind['icon']} {ind['name']}\n{ind['description']}",
            key=f"ind_{ind_id}",
            use_container_width=True,
        ):
            st.session_state["demo_industry"]  = ind_id
            st.session_state["demo_scenario"]  = "normal"
            st.session_state["demo_messages"]  = []
            st.session_state["scenario_triggered"] = False
            st.rerun()
        # Indicateur sélection
        if selected:
            st.markdown(f"<div style='height:3px;background:{ind['color']};border-radius:2px;margin-top:-8px;'></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── STEP 2 — Simulateur de scénarios ─────────────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown('<div class="section-title">② Simulez un incident</div>', unsafe_allow_html=True)

    for sc_id, sc in SCENARIOS.items():
        sev_colors = {"critical": "#2e1a1a", "warning": "#2a2a1a", "ok": "#0f201a", "info": "#1a1a2e"}
        border_col = sc["color"] if sc_id == scenario_id else "#2a2a4a"
        is_sel     = sc_id == scenario_id

        st.markdown(f"""
        <div style='background:{"#16162a" if is_sel else "#0f0f20"};
             border:1px solid {border_col};border-radius:10px;
             padding:12px 14px;margin-bottom:6px;'>
            <div style='font-size:14px;font-weight:600;color:#e0e0f0;'>{sc["icon"]} {sc["name"]}</div>
            <div style='font-size:11px;color:#6060a0;margin-top:3px;'>{sc["description"][:60]}...</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "▶ Simuler" if not is_sel else "✓ Actif",
            key=f"sc_{sc_id}",
            use_container_width=True,
        ):
            st.session_state["demo_scenario"]       = sc_id
            st.session_state["demo_messages"]       = []
            st.session_state["scenario_triggered"]  = False
            st.rerun()

with col_right:
    st.markdown('<div class="section-title">③ Métriques live</div>', unsafe_allow_html=True)

    m = scenario["metrics"]
    sev = scenario["severity"]
    sev_col = {"critical": "#E24B4A", "warning": "#EF9F27", "ok": "#1D9E75", "info": "#7F77DD"}[sev]

    # QoE Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = m["qoe"],
        number = {"font": {"size": 52, "color": sev_col, "family": "JetBrains Mono"}, "suffix": "/100"},
        title  = {"text": "QoE Score Global", "font": {"size": 13, "color": "#6060a0"}},
        gauge  = {
            "axis": {"range": [0, 100], "tickcolor": "#6060a0", "tickfont": {"size": 10}},
            "bar":  {"color": sev_col, "thickness": 0.2},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 55],   "color": "rgba(226,75,74,0.12)"},
                {"range": [55, 70],  "color": "rgba(239,159,39,0.12)"},
                {"range": [70, 100], "color": "rgba(29,158,117,0.12)"},
            ],
            "threshold": {"line": {"color": sev_col, "width": 3}, "thickness": 0.8, "value": m["qoe"]},
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0a0c0"),
        height=200, margin=dict(l=20, r=20, t=30, b=0),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Rebuffering",    f"{m['rebuffer']}%",    delta_color="inverse")
    k2.metric("Bitrate",        f"{m['bitrate']} Mbps")
    k3.metric("Latence P95",    f"{m['latency']} s",    delta_color="inverse")
    k4.metric("Taux d'erreur",  f"{m['error_rate']}%",  delta_color="inverse")

    # CDN status
    st.markdown("<div style='display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;'>", unsafe_allow_html=True)
    for cdn_key, cdn_name in [("cdn_eu1", "CDN-EU1"), ("cdn_fr2", "CDN-FR2")]:
        val = m[cdn_key]
        c   = "#1D9E75" if val >= 98 else "#EF9F27" if val >= 94 else "#E24B4A"
        st.markdown(f"""
        <div style='background:#0f0f20;border:1px solid {c}44;border-radius:8px;
             padding:8px 14px;text-align:center;min-width:100px;'>
            <div style='font-size:10px;color:#6060a0;'>{cdn_name}</div>
            <div style='font-size:18px;font-weight:700;color:{c};font-family:JetBrains Mono;'>{val}%</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── STEP 3 — AI Copilot Demo ───────────────────────────────────────────────────
st.markdown('<div class="section-title">④ AI Copilot en action</div>', unsafe_allow_html=True)

col_chat, col_roi = st.columns([3, 2])

with col_chat:
    # Bouton de déclenchement IA
    if scenario_id != "normal":
        if not st.session_state.get("scenario_triggered"):
            btn_label = f"🤖 Analyser l'incident avec le Copilot AI"
            if st.button(btn_label, use_container_width=True, type="primary"):
                st.session_state["scenario_triggered"] = True
                # Ajoute le message d'alerte auto
                alert_template = scenario.get("ai_alert", "")
                if alert_template:
                    alert_msg = alert_template.format(
                        impact_viewers=roi["impact_viewers"],
                        revenue_loss=roi["revenue_loss"],
                    )
                    st.session_state["demo_messages"].append({
                        "role": "assistant", "content": alert_msg
                    })
                st.rerun()
    else:
        st.button("✅ Système nominal — posez une question au Copilot", use_container_width=True, disabled=False)

    # Historique chat
    for msg in st.session_state["demo_messages"]:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # Input
    user_q = st.chat_input("Posez une question au Copilot AI...")
    if user_q:
        st.session_state["demo_messages"].append({"role": "user", "content": user_q})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_q)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyse en cours..."):
                try:
                    api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
                    if not api_key:
                        # Mode démo sans clé API
                        demo_responses = {
                            "cdn": f"Sur le scénario '{scenario['name']}', CDN-EU1 est à {m['cdn_eu1']}%. Je recommande le basculement immédiat vers CDN-FR2 qui est à {m['cdn_fr2']}%.",
                            "qoe": f"Le QoE est actuellement à {m['qoe']}/100. La dimension la plus dégradée est le rebuffering ({m['rebuffer']}%). Action prioritaire : activer l'ABR adaptatif.",
                            "roi": f"L'impact financier estimé est de {roi['revenue_loss']:,}€/heure. Avec StreamAnalytics Pro, le MTTR passe de {roi['mttr_before']}min à {roi['mttr_after']}min, soit {roi['revenue_saved']:,}€ économisés.",
                        }
                        resp = next((v for k, v in demo_responses.items() if k in user_q.lower()), 
                                    f"Basé sur les métriques actuelles (QoE: {m['qoe']}/100, Rebuffering: {m['rebuffer']}%), voici mon analyse pour le scénario '{scenario['name']}' dans le secteur {industry['name']} : l'action prioritaire est d'adresser le rebuffering qui impacte {roi['impact_viewers']:,} viewers.")
                        st.markdown(resp)
                        st.session_state["demo_messages"].append({"role": "assistant", "content": resp})
                    else:
                        client  = anthropic.Anthropic(api_key=api_key)
                        system  = f"""Tu es le Copilot IA de StreamAnalytics Pro, expert streaming vidéo.
Contexte démo : secteur {industry['name']}, scénario '{scenario['name']}'.
Métriques live : QoE={m['qoe']}/100, rebuffering={m['rebuffer']}%, bitrate={m['bitrate']}Mbps, latence={m['latency']}s.
CDN-EU1={m['cdn_eu1']}%, CDN-FR2={m['cdn_fr2']}%.
Viewers impactés : {roi['impact_viewers']:,}. Perte estimée : {roi['revenue_loss']:,}€/h.
Réponds en français, de manière concise et professionnelle. Tu es en mode démo commerciale."""

                        placeholder  = st.empty()
                        full_response = ""
                        with client.messages.stream(
                            model="claude-sonnet-4-20250514", max_tokens=600,
                            system=system,
                            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state["demo_messages"]],
                        ) as stream:
                            for text in stream.text_stream:
                                full_response += text
                                placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                        st.session_state["demo_messages"].append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"Erreur: {e}")

with col_roi:
    st.markdown('<div class="section-title">Impact & ROI</div>', unsafe_allow_html=True)

    if scenario_id == "normal":
        st.markdown(f"""
        <div class="roi-card">
            <div style='font-size:32px;'>✅</div>
            <div style='font-size:18px;font-weight:600;color:#1D9E75;margin:10px 0;'>Tout est nominal</div>
            <div style='font-size:13px;color:#6060a0;'>
                {industry['icon']} {industry['name']}<br>
                {roi['viewers_total']:,} viewers monitorés<br>
                SLA cible : {industry['sla']}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif scenario_id == "live_event":
        st.markdown(f"""
        <div class="roi-card">
            <div style='font-size:32px;'>⚡</div>
            <div class="roi-value">{roi['viewers_total']:,}</div>
            <div class="roi-label">viewers simultanés gérés</div>
            <hr style='border-color:#2a2a4a;margin:14px 0;'>
            <div style='font-size:13px;color:#1D9E75;font-weight:600;'>
                Pertes évitées grâce au scaling préventif IA
            </div>
            <div style='font-size:28px;font-weight:700;color:#1D9E75;font-family:JetBrains Mono;'>
                {roi['revenue_saved']:,}€
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="roi-card">
            <div style='font-size:11px;color:#6060a0;text-transform:uppercase;letter-spacing:1px;'>Viewers impactés</div>
            <div class="roi-value" style='color:#E24B4A;'>{roi['impact_viewers']:,}</div>
            <hr style='border-color:#2a2a4a;margin:14px 0;'>
            <div style='font-size:11px;color:#6060a0;text-transform:uppercase;letter-spacing:1px;'>Perte sans outil</div>
            <div style='font-size:28px;font-weight:700;color:#E24B4A;font-family:JetBrains Mono;'>
                {roi['revenue_loss']:,}€<span style='font-size:14px;'>/heure</span>
            </div>
            <hr style='border-color:#2a2a4a;margin:14px 0;'>
            <div style='font-size:11px;color:#6060a0;text-transform:uppercase;letter-spacing:1px;'>Economies avec StreamAnalytics</div>
            <div class="roi-value">{roi['revenue_saved']:,}€</div>
            <hr style='border-color:#2a2a4a;margin:14px 0;'>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;text-align:center;'>
                <div>
                    <div style='font-size:22px;font-weight:700;color:#E24B4A;font-family:JetBrains Mono;'>{roi['mttr_before']}min</div>
                    <div style='font-size:10px;color:#6060a0;'>MTTR sans outil</div>
                </div>
                <div>
                    <div style='font-size:22px;font-weight:700;color:#1D9E75;font-family:JetBrains Mono;'>{roi['mttr_after']}min</div>
                    <div style='font-size:10px;color:#6060a0;'>MTTR avec IA</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Calculateur ROI annuel
    st.markdown('<div class="section-title">Calculateur ROI</div>', unsafe_allow_html=True)
    incidents_month = st.slider("Incidents/mois", 1, 30, 8)
    avg_duration    = st.slider("Duree moyenne (min)", 5, 120, 35)
    rev_hour_custom = st.number_input("Revenue/heure (€)", value=industry["revenue_per_hour"], step=1000)

    saving_pct   = 0.82
    annual_saving = int((incidents_month * 12) * (avg_duration / 60) * rev_hour_custom * saving_pct)

    st.markdown(f"""
    <div style='background:#0a1f0a;border:1px solid #1D9E7555;border-radius:10px;padding:16px;text-align:center;margin-top:8px;'>
        <div style='font-size:11px;color:#6060a0;text-transform:uppercase;letter-spacing:1px;'>ROI annuel estime</div>
        <div style='font-size:36px;font-weight:700;color:#1D9E75;font-family:JetBrains Mono;'>
            {annual_saving:,}€
        </div>
        <div style='font-size:11px;color:#6060a0;margin-top:4px;'>
            Economises grace a la detection et resolution acceleree
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer démo ────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;border-top:1px solid #2a2a4a;padding-top:24px;color:#404060;font-size:12px;'>
    StreamAnalytics Pro · Demo Commerciale · Powered by Claude AI · contact@streamanalytics.pro
</div>
""", unsafe_allow_html=True)
