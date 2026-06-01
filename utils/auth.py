"""
Système d'authentification StreamAnalytics Pro
- Deux plans : basic / premium
- Passwords hashés en SHA-256
- Sessions via st.session_state
"""

import hashlib
import streamlit as st
from datetime import datetime

# ── Plans ─────────────────────────────────────────────────────────────────────
PLANS = {
    "basic": {
        "name":     "Basic",
        "color":    "6060A0",
        "features": ["Dashboard Live", "Demo Interactive"],
        "locked":   ["QoE Score", "AI Decision Engine", "AI Copilot", "Analyse de Logs"],
        "price":    "Gratuit",
    },
    "premium": {
        "name":     "Premium",
        "color":    "7F77DD",
        "features": ["Dashboard Live", "QoE Score", "AI Decision Engine",
                     "AI Copilot", "Analyse de Logs", "Demo Interactive"],
        "locked":   [],
        "price":    "149€/mois",
    },
}

# Pages premium — à vérifier dans chaque page
PREMIUM_PAGES = {"QoE Score", "AI Decision Engine", "AI Copilot", "Analyse de Logs"}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load_users() -> dict:
    """
    Charge les utilisateurs depuis st.secrets.
    Format secrets.toml :
        [users.alice]
        password_hash = "abc123..."
        plan = "premium"
        email = "alice@example.com"
    """
    try:
        return dict(st.secrets.get("users", {}))
    except Exception:
        return {}


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Tente un login. Retourne (success, error_message).
    """
    users = _load_users()
    uname = username.strip().lower()

    if uname not in users:
        return False, "Identifiant ou mot de passe incorrect."

    user = users[uname]
    stored_hash = user.get("password_hash", "")

    if stored_hash != _hash(password):
        return False, "Identifiant ou mot de passe incorrect."

    # Stocker la session
    st.session_state["authenticated"] = True
    st.session_state["username"]      = uname
    st.session_state["display_name"]  = user.get("display_name", username.title())
    st.session_state["plan"]          = user.get("plan", "basic")
    st.session_state["email"]         = user.get("email", "")
    st.session_state["login_time"]    = datetime.now().strftime("%H:%M")
    return True, ""


def logout():
    for key in ["authenticated", "username", "display_name", "plan", "email", "login_time"]:
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_plan() -> str:
    return st.session_state.get("plan", "basic")


def get_user() -> dict:
    return {
        "username":     st.session_state.get("username", ""),
        "display_name": st.session_state.get("display_name", ""),
        "plan":         st.session_state.get("plan", "basic"),
        "email":        st.session_state.get("email", ""),
        "login_time":   st.session_state.get("login_time", ""),
    }


def is_premium() -> bool:
    return get_plan() == "premium"


def require_auth():
    """
    A appeler en haut de chaque page.
    Redirige vers le login si non authentifié.
    """
    if not is_authenticated():
        st.switch_page("Home.py")
        st.stop()


def require_premium(page_name: str):
    """
    A appeler sur les pages premium.
    Affiche un écran d'upgrade si plan basic.
    """
    require_auth()
    if not is_premium():
        _show_upgrade_wall(page_name)
        st.stop()


def _show_upgrade_wall(page_name: str):
    """Affiche le mur d'upgrade pour les utilisateurs basic."""
    st.markdown("""
    <style>
    .upgrade-wall {
        background: linear-gradient(135deg, #0f0f1a, #14143a);
        border: 1px solid #7F77DD55;
        border-radius: 16px;
        padding: 50px;
        text-align: center;
        max-width: 600px;
        margin: 60px auto;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="upgrade-wall">
        <div style='font-size:48px;margin-bottom:16px;'>🔒</div>
        <h2 style='color:#7F77DD;font-size:26px;margin-bottom:8px;'>{page_name}</h2>
        <p style='color:#a0a0c0;font-size:15px;margin-bottom:24px;'>
            Cette fonctionnalité est réservée au plan <strong style='color:#7F77DD;'>Premium</strong>.
        </p>
        <div style='background:#1a1a2e;border-radius:10px;padding:16px;margin-bottom:24px;'>
            <div style='font-size:13px;color:#6060a0;margin-bottom:10px;'>Inclus dans Premium :</div>
            {''.join([f"<div style='color:#1D9E75;font-size:13px;margin:4px 0;'>✓ {f}</div>" for f in PLANS['premium']['features']])}
        </div>
        <div style='font-size:28px;font-weight:700;color:#7F77DD;margin-bottom:6px;'>149€ / mois</div>
        <div style='font-size:12px;color:#6060a0;'>Sans engagement · Déploiement en 24h</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Passer au plan Premium", use_container_width=True, type="primary"):
            st.info("Contactez-nous : contact@streamanalytics.pro")
        if st.button("← Retour au Dashboard", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")


def show_sidebar_user():
    """
    Affiche le bloc utilisateur + plan dans la sidebar.
    A appeler dans le with st.sidebar: de chaque page.
    """
    user = get_user()
    plan = user["plan"]
    plan_info = PLANS[plan]
    color = plan_info["color"]

    st.markdown(f"""
    <div style='background:#0f0f20;border:1px solid #{color}44;border-radius:10px;
         padding:12px;margin-bottom:12px;'>
        <div style='font-size:13px;font-weight:600;color:#e0e0f0;'>{user['display_name']}</div>
        <div style='font-size:11px;color:#6060a0;margin-top:2px;'>{user['email']}</div>
        <div style='margin-top:8px;'>
            <span style='background:#{color}22;color:#{color};border:1px solid #{color}55;
                  padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;'>
                {plan_info["name"].upper()}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Déconnexion", use_container_width=True):
        logout()
        st.switch_page("Home.py")
