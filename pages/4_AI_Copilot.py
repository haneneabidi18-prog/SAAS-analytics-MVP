import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.auth import require_premium, show_sidebar_user, is_org_admin, is_super_admin
require_premium("AI Copilot")

import streamlit as st
import anthropic

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
    show_sidebar_user()
    st.divider()
    if st.button("Dashboard",          use_container_width=True): st.switch_page("pages/1_Dashboard.py")
    if st.button("QoE Score",          use_container_width=True): st.switch_page("pages/2_QoE_Score.py")
    if st.button("AI Decision Engine", use_container_width=True): st.switch_page("pages/3_AI_Decision_Engine.py")
    if st.button("AI Copilot",         use_container_width=True): pass
    if st.button("Analyse de Logs",    use_container_width=True): st.switch_page("pages/5_Analyse_Logs.py")
    if st.button("Demo Interactive",   use_container_width=True): st.switch_page("pages/0_Demo.py")
    if is_org_admin():
        if st.button("Gestion d'equipe", use_container_width=True): st.switch_page("pages/6_Team_Management.py")
    if is_super_admin():
        if st.button("Admin ABIDSON", use_container_width=True): st.switch_page("pages/9_Admin_ABIDSON.py")

    st.divider()
    st.markdown("**Parametres**")
    MODEL_OPTIONS = {
        "Standard (recommande)": "claude-sonnet-4-6",
        "Rapide":                "claude-haiku-4-5-20251001",
    }
    model_label  = st.selectbox("Modele IA", list(MODEL_OPTIONS.keys()))
    model_choice = MODEL_OPTIONS[model_label]
    max_tokens   = st.slider("Longueur reponse", 200, 2000, 800, 100)
    inject_live  = st.toggle("Injecter metriques live", value=True)
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

    return f"""Tu es le Copilot IA de StreamAnalytics Pro, une plateforme de monitoring streaming temps reel.
Tu es un expert en streaming video (HLS/DASH), CDN, encodage, QoE (Quality of Experience) et infrastructure.
Tu assistes l'operateur avec des reponses concises, precises et actionnables.

## Contexte live actuel ({metrics['timestamp'].strftime('%H:%M:%S')})
- Viewers actifs : {metrics['viewers']:,}
- Bitrate moyen : {metrics['bitrate_avg']} Mbps
- Taux rebuffering : {metrics['rebuffer_rate']}%
- Latence P95 : {metrics['latency_p95']} s
- Delai demarrage : {metrics['startup_time']} s
- Taux d'erreur : {metrics['error_rate']}%
- CDN Health : {cdn_str}
- CDN degrades : {degraded}

## Score QoE
- Score global : {qoe['global']}/100 ({qoe['label']})
- Dimensions faibles : {weak_str}

## Regles de reponse
- Reponds TOUJOURS en francais
- Sois direct et actionnable (bullet points si liste > 3 items)
- Cite les metriques live quand c'est pertinent
- Pour les recommandations CDN, propose des alternatives concretes
- Termine par une question de suivi si c'est utile
- N'invente pas de metriques absentes du contexte
"""

# ── Init session ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🤖 AI Copilot")
st.markdown("""<span style='background:#7F77DD;color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;'>PREMIUM</span>""", unsafe_allow_html=True)

# Live snapshot
col1, col2, col3, col4 = st.columns(4)
col1.metric("QoE", f"{qoe['global']}/100",  qoe["label"].split()[0])
col2.metric("Viewers", f"{metrics['viewers']:,}", "+12%")
col3.metric("Rebuffering", f"{metrics['rebuffer_rate']}%", delta_color="inverse")
col4.metric("CDN degrades", f"{len(degraded_cdns)}", delta_color="inverse")

st.markdown("---")

# ── Questions rapides ─────────────────────────────────────────────────────────
st.markdown("**Questions rapides :**")
quick_cols = st.columns(4)
quick_questions = [
    "Pourquoi mon rebuffering monte ce soir ?",
    "Quel CDN est le plus performant en ce moment ?",
    "Comment ameliorer mon QoE de 10 points ?",
    "Predis le trafic pour les 4 prochaines heures",
]
for i, (col, q) in enumerate(zip(quick_cols, quick_questions)):
    with col:
        if st.button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state["messages"].append({"role": "user", "content": q})
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Prefill depuis Decision Engine ────────────────────────────────────────────
if st.session_state.get("copilot_prefill"):
    prefill = st.session_state.pop("copilot_prefill")
    if not any(m["content"] == prefill for m in st.session_state["messages"]):
        st.session_state["messages"].append({"role": "user", "content": prefill})
        st.rerun()

# ── Message d'accueil si vide ─────────────────────────────────────────────────
if not st.session_state["messages"]:
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(f"""
Bonjour ! Je suis votre **Copilot IA StreamAnalytics**.

Je surveille vos streams en temps reel. Voici ce que je vois maintenant :
- **QoE Global : {qoe['global']}/100** — {qoe['label']}
- **{metrics['viewers']:,} viewers actifs** · Rebuffering a {metrics['rebuffer_rate']}%
{f"- ⚠️ CDN degrades : **{', '.join(degraded_cdns)}**" if degraded_cdns else "- ✅ Tous les CDN sont operationnels"}

Comment puis-je vous aider ?
        """)

# ── Affichage historique ──────────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Posez votre question a l'AI Copilot...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.rerun()

# ── Generation de la reponse si le dernier message est de l'utilisateur ────────
# Ce bloc gere TOUTES les sources de message utilisateur :
# chat_input, questions rapides, prefill depuis Decision Engine.
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analyse en cours..."):
            try:
                api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
                if not api_key:
                    st.error("⚠️ Cle API manquante. Contactez l'administrateur de la plateforme.")
                    st.stop()

                client = anthropic.Anthropic(api_key=api_key)

                system = build_system_prompt(metrics, qoe) if inject_live else (
                    "Tu es un expert streaming video. Reponds en francais, de maniere concise et technique."
                )

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
                st.error("❌ Cle API invalide. Verifiez ANTHROPIC_API_KEY dans les secrets Streamlit Cloud — elle doit commencer par sk-ant-api03-...")
            except anthropic.NotFoundError:
                st.error("❌ Modele introuvable. Verifiez le nom du modele configure.")
            except anthropic.RateLimitError:
                st.error("⏳ Limite de debit atteinte. Reessayez dans quelques secondes.")
            except Exception as e:
                st.error(f"Erreur : {str(e)}")