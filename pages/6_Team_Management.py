import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.auth import require_org_admin, show_sidebar_user, get_org, get_user
require_org_admin()

import streamlit as st
from utils.org import list_org_members, add_team_member, remove_team_member, \
                       reset_member_password, PLAN_TIERS, estimate_monthly_price

st.set_page_config(page_title="Gestion d'equipe · StreamAnalytics", page_icon="👥", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #07070f; }
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
.member-row {
    background: #0f0f20; border: 1px solid #2a2a4a;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 8px;
    display: flex; align-items: center; justify-content: space-between;
}
.role-badge {
    display: inline-block; padding: 2px 10px; border-radius: 12px;
    font-size: 11px; font-weight: 600;
}
.cred-box {
    background: #14143a; border: 1px solid #7F77DD55; border-radius: 10px;
    padding: 16px; margin-top: 10px;
    font-family: 'JetBrains Mono', monospace;
}
div[data-testid="metric-container"] {
    background: #0f0f20; border: 1px solid #2a2a4a;
    border-radius: 10px; padding: 14px;
}
div[data-testid="metric-container"] label { color: #6060a0 !important; font-size: 11px !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e0e0f0 !important; font-family: 'JetBrains Mono', monospace !important;
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
    show_sidebar_user()
    st.divider()
    if st.button("Dashboard",           use_container_width=True): st.switch_page("pages/1_Dashboard.py")
    if st.button("QoE Score",           use_container_width=True): st.switch_page("pages/2_QoE_Score.py")
    if st.button("AI Decision Engine",  use_container_width=True): st.switch_page("pages/3_AI_Decision_Engine.py")
    if st.button("AI Copilot",          use_container_width=True): st.switch_page("pages/4_AI_Copilot.py")
    if st.button("Analyse de Logs",     use_container_width=True): st.switch_page("pages/5_Analyse_Logs.py")
    if st.button("Demo Interactive",    use_container_width=True): st.switch_page("pages/0_Demo.py")
    if st.button("Gestion d'equipe",    use_container_width=True): pass

# ── Data ──────────────────────────────────────────────────────────────────────
org  = get_org()
user = get_user()

if not org:
    st.error("Aucune organisation associee a votre compte. Contactez contact@streamanalytics.pro")
    st.stop()

tier    = PLAN_TIERS.get(org["plan_tier"], PLAN_TIERS["starter"])
members = list_org_members(org["id"])
used    = len(members)
max_u   = org["max_users"]
monthly = estimate_monthly_price(org["plan_tier"], max_u)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"## 👥 Gestion d'equipe — {org['name']}")
st.markdown(f"""
<span style='background:#7F77DD;color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;'>
    Plan {tier['name']}
</span>
<span style='font-size:13px;color:#6060a0;margin-left:10px;'>
    {tier['label']} · {tier['price_per_user']}€/utilisateur/mois
</span>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Licences utilisees", f"{used} / {max_u}")
c2.metric("Plan", tier["name"])
c3.metric("Tarif mensuel estime", f"{monthly:,} €")
c4.metric("Statut", "Actif" if org["status"] == "active" else "Suspendu")

st.progress(min(used / max_u, 1.0) if max_u else 0)

if used >= max_u:
    st.warning(
        f"⚠️ Limite de licences atteinte ({max_u} utilisateurs). "
        f"Pour ajouter des membres, contactez contact@streamanalytics.pro pour upgrader votre plan."
    )

# ── Ajouter un membre ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Ajouter un collaborateur")

with st.form("add_member", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        new_email = st.text_input("Email professionnel", placeholder="prenom.nom@isp.com")
    with col2:
        new_name = st.text_input("Nom complet", placeholder="Prenom Nom")

    submitted = st.form_submit_button(
        "Ajouter a l'equipe",
        type="primary",
        disabled=(used >= max_u or org["status"] != "active"),
    )

    if submitted:
        if not new_email or "@" not in new_email:
            st.error("Email invalide.")
        elif not new_name:
            st.error("Le nom complet est requis.")
        else:
            ok, err, username, pwd = add_team_member(org["id"], new_email, new_name)
            if ok:
                st.success(f"✅ {new_name} a ete ajoute(e) a l'equipe !")
                st.markdown(f"""
                <div class='cred-box'>
                    <div style='font-size:11px;color:#6060a0;margin-bottom:8px;'>
                        ⚠️ Identifiants a transmettre — affiches une seule fois
                    </div>
                    <div style='font-size:14px;color:#e0e0f0;'>
                        URL : <strong>{st.secrets.get("APP_URL", "")}</strong><br>
                        Identifiant : <strong>{username}</strong><br>
                        Mot de passe : <strong>{pwd}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(err)

# ── Liste des membres ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Membres de l'equipe ({used}/{max_u})")

role_labels = {
    "org_admin":   ("Administrateur", "7F77DD"),
    "member":      ("Membre", "1D9E75"),
    "super_admin": ("Super Admin", "EF9F27"),
}

for m in members:
    label, color = role_labels.get(m["role"], ("Membre", "6060A0"))
    col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 1.2, 1.2])
    with col1:
        st.markdown(f"**{m['display_name']}**")
    with col2:
        st.markdown(f"<span style='color:#a0a0c0;font-size:13px;'>{m['email']}</span>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<span class='role-badge' style='background:#{color}22;color:#{color};border:1px solid #{color}55;'>{label}</span>", unsafe_allow_html=True)
    with col4:
        if m["username"] != user["username"]:
            if st.button("Reset mdp", key=f"reset_{m['id']}", use_container_width=True):
                ok, pwd = reset_member_password(m["id"])
                if ok:
                    st.info(f"Nouveau mot de passe pour {m['display_name']} : **{pwd}**")
                else:
                    st.error(pwd)
    with col5:
        if m["role"] != "org_admin" and m["username"] != user["username"]:
            if st.button("Retirer", key=f"del_{m['id']}", use_container_width=True):
                remove_team_member(m["id"])
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;font-size:12px;color:#404060;'>
    Besoin de plus de licences ? contact@streamanalytics.pro
</div>
""", unsafe_allow_html=True)
