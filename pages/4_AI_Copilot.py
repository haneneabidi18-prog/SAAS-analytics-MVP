import streamlit as st
import anthropic
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.data import get_live_metrics
from utils.qoe  import compute_qoe

st.set_page_config(page_title="AI Copilot · StreamAnalytics", page_icon="🤖", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
[data-testid="stChatMessage"] { background: #1a1a2e !important; border: 1px solid #2a2a4a; border-radius: 10px; }
.copilot-header {
    background: linear-gradient(135deg, #1a1a2e, #0f0f2a);
    border: 1px solid #7F77DD55; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 16px;
    display: flex; align-items: center; gap: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:15px 0 5px;font-size:22px;'>📡</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:18px;font-weight:700;color:#7F77DD;'>StreamAnalytics</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("📊 Dashboard",          use_container_width=True): st.switch_page("pages/1_📊_Dashboard.py")
    if st.button("🎯 QoE Score",          use_container_width=True): st.switch_page("pages/2_🎯_QoE_Score.py")
    if st.button("🧠 AI Decision Engine", use_container_width=True): st.switch_page("pages/3_🧠_AI_Decision_Engine.py")
    if st.button("🤖 AI Copilot",         use_container_width=True): pass
    st.divider()
    st.markdown("**Paramètres Copilot**")
    model_choice = st.selectbox("Modèle", ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"])
    max_tokens   = st.slider("Longueur réponse", 200, 2000, 800, 100)
    inject_live  = st.toggle("Injecter métriques live", value=True)
    if st.button("🗑 Effacer la conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

# ── Live data ─────────────────────────────────────────────────────────────────
metrics = get_live_metrics()
qoe     = compute_qoe(metrics)
cdn     = metrics.get("cdn_health", {})
degraded_cdns = [c for c, h in cdn.items() if h < 97]

# ── System prompt ──────────────────────────────────────────────────────────────
def build_system_prompt(metrics: dict, qoe: dict) -> str:
    dims = qoe.get("dimensions", {})
    weak_dims = sorted(dims.items(), key=lambda x: x[1])[:2]
    weak_str  = ", ".join([f"{k} ({v:.0f}/100)" for k, v in weak_dims])
    cdn_str   = ", ".join([f"{k}: {v}%" for k, v in metrics.get("cdn_health", {}).items()])
    degraded  = ", ".join(degraded_cdns) if degraded_cdns else "aucun"

    return f"""Tu es le Copilot IA de StreamAnalytics Pro, une plateforme de monitoring streaming temps réel.
Tu es un expert en streaming vidéo (HLS/DASH), CDN, encodage, QoE (Quality of Experience) et infrastructure.
Tu assistes l'opérateur avec des réponses concises, précises et actionnables.

## Contexte live actuel ({metrics['timestamp'].strftime('%H:%M:%S')})
- Viewers actifs : {metrics['viewers']:,}
- Bitrate moyen : {metrics['bitrate_avg']} Mbps
- Taux rebuffering : {metrics['rebuffer_rate']}%
- Latence P95 : {metrics['latency_p95']} s
- Délai démarrage : {metrics['startup_time']} s
- Taux d'erreur : {metrics['error_rate']}%
- CDN Health : {cdn_str}
- CDN dégradés : {degraded}

## Score QoE
- Score global : {qoe['global']}/100 ({qoe['label']})
- Dimensions faibles : {weak_str}

## Règles de réponse
- Réponds TOUJOURS en français
- Sois direct et actionnable (bullet points si liste > 3 items)
- Cite les métriques live quand c'est pertinent
- Pour les recommandations CDN, propose des alternatives concrètes
- Termine par une question de suivi si c'est utile
- N'invente pas de métriques absentes du contexte
"""

# ── Init session ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🤖 AI Copilot")
st.markdown("""<span style='background:#7F77DD;color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;'>PREMIUM · Powered by Claude</span>""", unsafe_allow_html=True)

# Live snapshot
col1, col2, col3, col4 = st.columns(4)
col1.metric("QoE", f"{qoe['global']}/100",  qoe["label"].split()[0])
col2.metric("Viewers", f"{metrics['viewers']:,}", "+12%")
col3.metric("Rebuffering", f"{metrics['rebuffer_rate']}%", delta_color="inverse")
col4.metric("CDN dégradés", f"{len(degraded_cdns)}", delta_color="inverse")

st.markdown("---")

# ── Questions rapides ─────────────────────────────────────────────────────────
st.markdown("**Questions rapides :**")
quick_cols = st.columns(4)
quick_questions = [
    "Pourquoi mon rebuffering monte ce soir ?",
    "Quel CDN est le plus performant en ce moment ?",
    "Comment améliorer mon QoE de 10 points ?",
    "Préds le trafic pour les 4 prochaines heures",
]
for i, (col, q) in enumerate(zip(quick_cols, quick_questions)):
    with col:
        if st.button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state["messages"].append({"role": "user", "content": q})
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Prefill depuis Decision Engine ────────────────────────────────────────────
if "copilot_prefill" in st.session_state and st.session_state["copilot_prefill"]:
    prefill = st.session_state.pop("copilot_prefill")
    if not any(m["content"] == prefill for m in st.session_state["messages"]):
        st.session_state["messages"].append({"role": "user", "content": prefill})
        st.rerun()

# ── Affichage historique ──────────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# ── Message d'accueil si vide ─────────────────────────────────────────────────
if not st.session_state["messages"]:
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(f"""
Bonjour ! Je suis votre **Copilot IA StreamAnalytics**.

Je surveille vos streams en temps réel. Voici ce que je vois maintenant :
- **QoE Global : {qoe['global']}/100** — {qoe['label']}
- **{metrics['viewers']:,} viewers actifs** · Rebuffering à {metrics['rebuffer_rate']}%
{f"- ⚠️ CDN dégradés : **{', '.join(degraded_cdns)}**" if degraded_cdns else "- ✅ Tous les CDN sont opérationnels"}

Comment puis-je vous aider ?
        """)

# ── Chat input + appel API ────────────────────────────────────────────────────
user_input = st.chat_input("Posez votre question à l'AI Copilot...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analyse en cours..."):
            try:
                # Récupérer la clé API depuis les secrets Streamlit
                api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
                if not api_key:
                    st.error("⚠️ Clé API Anthropic manquante. Ajoutez ANTHROPIC_API_KEY dans vos secrets Streamlit.")
                    st.stop()

                client = anthropic.Anthropic(api_key=api_key)

                system = build_system_prompt(metrics, qoe) if inject_live else (
                    "Tu es un expert streaming vidéo. Réponds en français, de manière concise et technique."
                )

                # Streaming de la réponse
                response_placeholder = st.empty()
                full_response = ""

                with client.messages.stream(
                    model      = model_choice,
                    max_tokens = max_tokens,
                    system     = system,
                    messages   = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["messages"]
                    ],
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        response_placeholder.markdown(full_response + "▌")

                response_placeholder.markdown(full_response)
                st.session_state["messages"].append({"role": "assistant", "content": full_response})

            except anthropic.AuthenticationError:
                st.error("❌ Clé API invalide. Vérifiez votre ANTHROPIC_API_KEY dans les secrets.")
            except anthropic.RateLimitError:
                st.error("⏳ Limite de débit atteinte. Réessayez dans quelques secondes.")
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
