"""
Systeme d'authentification StreamAnalytics Pro
- Acces premium herite de l'organisation (licence ISP) ou du plan individuel
- Roles : super_admin (ABIDSON) | org_admin (client ISP) | member
"""

import hashlib
import streamlit as st


PREMIUM_PAGES = {"QoE Score", "AI Decision Engine", "AI Copilot", "Analyse de Logs"}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Etat de session ───────────────────────────────────────────────────────────
def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_plan() -> str:
    return st.session_state.get("plan", "basic")


def get_role() -> str:
    return st.session_state.get("role", "member")


def get_org() -> dict | None:
    return st.session_state.get("org")


def get_user() -> dict:
    return {
        "username":     st.session_state.get("username", ""),
        "display_name": st.session_state.get("display_name", ""),
        "plan":         st.session_state.get("plan", "basic"),
        "email":        st.session_state.get("email", ""),
        "role":         st.session_state.get("role", "member"),
        "org":          st.session_state.get("org"),
    }


# ── Niveaux d'acces ────────────────────────────────────────────────────────────
def is_premium() -> bool:
    """
    Premium si :
    - plan individuel = premium (legacy self-serve), OU
    - l'utilisateur appartient a une organisation au statut 'active'
    """
    if get_plan() == "premium":
        return True
    org = get_org()
    if org and org.get("status") == "active":
        return True
    return False


def is_org_admin() -> bool:
    return get_role() in ("org_admin", "super_admin")


def is_super_admin() -> bool:
    return get_role() == "super_admin"


# ── Logout ──────────────────────────────────────────────────────────────────────
def logout():
    for key in ["authenticated", "username", "display_name", "plan",
                "email", "role", "org", "login_time"]:
        st.session_state.pop(key, None)


# ── Garde-fous de page ────────────────────────────────────────────────────────
def require_auth():
    if not is_authenticated():
        st.switch_page("Home.py")
        st.stop()


def require_premium(page_name: str):
    require_auth()
    if not is_premium():
        _show_upgrade_wall(page_name)
        st.stop()


def require_org_admin():
    require_auth()
    if not is_org_admin():
        st.error("🔒 Cette page est reservee aux administrateurs.")
        st.stop()


def require_super_admin():
    require_auth()
    if not is_super_admin():
        st.error("🔒 Acces reserve.")
        st.stop()


# ── UI : mur d'upgrade ────────────────────────────────────────────────────────
def _show_upgrade_wall(page_name: str):
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
            Cette fonctionnalite est reservee aux comptes <strong style='color:#7F77DD;'>Premium</strong>.
        </p>
        <div style='background:#1a1a2e;border-radius:10px;padding:16px;margin-bottom:24px;'>
            <div style='font-size:13px;color:#6060a0;margin-bottom:10px;'>Inclus dans Premium :</div>
            <div style='color:#1D9E75;font-size:13px;margin:4px 0;'>✓ QoE Score</div>
            <div style='color:#1D9E75;font-size:13px;margin:4px 0;'>✓ AI Decision Engine</div>
            <div style='color:#1D9E75;font-size:13px;margin:4px 0;'>✓ AI Copilot</div>
            <div style='color:#1D9E75;font-size:13px;margin:4px 0;'>✓ Analyse de Logs</div>
        </div>
        <div style='font-size:13px;color:#6060a0;'>
            Contactez votre administrateur ou
            <span style='color:#7F77DD;'>contact@streamanalytics.pro</span>
            pour activer l'acces Premium.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Retour au Dashboard", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")


# ── UI : bloc utilisateur sidebar ──────────────────────────────────────────────
def show_sidebar_user():
    user = get_user()
    org  = user["org"]

    if org:
        plan_label = f"{org['name']} · Premium ⭐"
        color = "7F77DD"
    elif user["plan"] == "premium":
        plan_label = "Premium ⭐"
        color = "7F77DD"
    else:
        plan_label = "Basic"
        color = "6060A0"

    role_label = ""
    if user["role"] == "org_admin":
        role_label = "Administrateur d'equipe"
    elif user["role"] == "super_admin":
        role_label = "Super Admin · ABIDSON"

    st.markdown(f"""
    <div style='background:#0f0f20;border:1px solid #{color}44;border-radius:10px;
         padding:12px;margin-bottom:12px;'>
        <div style='font-size:13px;font-weight:600;color:#e0e0f0;'>{user['display_name']}</div>
        <div style='font-size:11px;color:#6060a0;margin-top:2px;'>{user['email']}</div>
        <div style='margin-top:8px;'>
            <span style='background:#{color}22;color:#{color};border:1px solid #{color}55;
                  padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;'>
                {plan_label}
            </span>
        </div>
        {f"<div style='font-size:10px;color:#6060a0;margin-top:6px;'>{role_label}</div>" if role_label else ""}
    </div>
    """, unsafe_allow_html=True)

    if st.button("Deconnexion", use_container_width=True, key="logout_sidebar"):
        logout()
        st.switch_page("Home.py")
