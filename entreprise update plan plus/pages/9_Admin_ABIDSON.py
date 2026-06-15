import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.auth import require_super_admin, show_sidebar_user
require_super_admin()

import streamlit as st
from utils.org import (
    create_organization, create_org_admin, list_organizations,
    update_organization_status, update_organization_plan,
    count_org_members, PLAN_TIERS, estimate_monthly_price, get_org_monthly_price,
)

st.set_page_config(page_title="Admin ABIDSON · StreamAnalytics", page_icon="🛠", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #07070f; }
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
.org-row {
    background: #0f0f20; border: 1px solid #2a2a4a;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 8px;
}
.status-active    { color: #1D9E75; background: #1D9E7522; border: 1px solid #1D9E7555; }
.status-suspended { color: #E24B4A; background: #E24B4A22; border: 1px solid #E24B4A55; }
.status-pill {
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
.stTabs [data-baseweb="tab"] { color: #6060a0 !important; }
.stTabs [aria-selected="true"] { color: #7F77DD !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:15px 0 5px;font-size:22px;'>📡</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:18px;font-weight:700;color:#7F77DD;'>StreamAnalytics</div>", unsafe_allow_html=True)
    show_sidebar_user()
    st.divider()
    if st.button("Dashboard",          use_container_width=True): st.switch_page("pages/1_Dashboard.py")
    if st.button("Demo Interactive",   use_container_width=True): st.switch_page("pages/0_Demo.py")
    if st.button("Admin ABIDSON",      use_container_width=True): pass

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🛠 Administration ABIDSON")
st.caption("Gestion des organisations clientes (ISP) — creation apres reception du virement")

# ── KPIs globaux ──────────────────────────────────────────────────────────────
orgs = list_organizations()
active_orgs = [o for o in orgs if o["status"] == "active"]
total_mrr = sum(get_org_monthly_price(o) for o in active_orgs)
total_licenses = sum(o["max_users"] for o in active_orgs)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Organisations actives", len(active_orgs))
c2.metric("Organisations totales", len(orgs))
c3.metric("Licences vendues",      total_licenses)
c4.metric("MRR estime",            f"{total_mrr:,} €")

st.markdown("<br>", unsafe_allow_html=True)

tab_new, tab_list = st.tabs(["➕ Nouveau client", "📋 Clients existants"])

# ════════════════════════════════════════════════
# TAB — NOUVEAU CLIENT
# ════════════════════════════════════════════════
with tab_new:
    st.markdown("### 1. Informations de l'organisation")

    org_name      = st.text_input("Nom de l'ISP / organisation", placeholder="Orange Telecom SA")
    contact_email = st.text_input("Email de contact (facturation)", placeholder="contact@isp.com")

    col1, col2 = st.columns(2)
    with col1:
        plan_tier = st.selectbox(
            "Palier de licence",
            options=list(PLAN_TIERS.keys()),
            format_func=lambda k: (
                f"{PLAN_TIERS[k]['name']} — {PLAN_TIERS[k]['label']} — sur devis"
                if PLAN_TIERS[k]['custom_pricing']
                else f"{PLAN_TIERS[k]['name']} — {PLAN_TIERS[k]['label']} — {PLAN_TIERS[k]['price_per_user']}€/user/mois"
            ),
        )
    with col2:
        tier_info = PLAN_TIERS[plan_tier]
        max_users = st.number_input(
            "Nombre de licences achetees",
            min_value=tier_info["min_users"],
            max_value=tier_info["max_users"],
            value=tier_info["min_users"],
        )

    custom_monthly_price = None

    if tier_info["custom_pricing"]:
        st.markdown(f"""
        <div style='background:#14143a;border:1px solid #EF9F2755;border-radius:10px;padding:14px;margin:8px 0 4px;'>
            <span style='font-size:12px;color:#EF9F27;font-weight:600;'>⚡ Palier sur devis</span><br>
            <span style='font-size:12px;color:#6060a0;'>
                Tarif indicatif de reference : {tier_info['price_per_user']}€/user/mois
                ({max_users} x {tier_info['price_per_user']}€ = {max_users * tier_info['price_per_user']:,}€/mois).
                Saisissez ci-dessous le tarif mensuel reellement negocie avec le client.
            </span>
        </div>
        """, unsafe_allow_html=True)
        custom_monthly_price = st.number_input(
            "Tarif mensuel negocie (€)",
            min_value=0,
            value=max_users * tier_info["price_per_user"],
            step=100,
        )
        monthly_price = custom_monthly_price
    else:
        monthly_price = estimate_monthly_price(plan_tier, max_users)
        st.markdown(f"""
        <div style='background:#14143a;border:1px solid #7F77DD55;border-radius:10px;padding:14px;margin:8px 0;'>
            <span style='font-size:13px;color:#a0a0c0;'>Tarif mensuel : </span>
            <span style='font-size:20px;font-weight:700;color:#7F77DD;font-family:JetBrains Mono;'>{monthly_price:,} €</span>
            <span style='font-size:12px;color:#6060a0;'> ({max_users} x {tier_info['price_per_user']}€)</span>
        </div>
        """, unsafe_allow_html=True)

    notes = st.text_area("Notes internes (reference virement, date, contrat...)",
                         placeholder="Virement recu le 14/06/2026 - ref FACT-2026-001")

    st.markdown("---")
    st.markdown("### 2. Compte administrateur de l'organisation")
    st.caption("Ce compte pourra ensuite ajouter ses propres collaborateurs (jusqu'a la limite de licences)")

    col1, col2 = st.columns(2)
    with col1:
        admin_username = st.text_input("Identifiant admin", placeholder="orange_admin")
        admin_email    = st.text_input("Email admin", placeholder="admin@orange.com")
    with col2:
        admin_name = st.text_input("Nom complet admin", placeholder="Jean Dupont")
        custom_pwd = st.text_input("Mot de passe (laisser vide pour generation auto)", placeholder="Auto-genere si vide")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Creer l'organisation et le compte admin", type="primary", use_container_width=True):
        errors = []
        if not org_name: errors.append("Le nom de l'organisation est requis.")
        if not admin_username or len(admin_username) < 3: errors.append("Identifiant admin invalide (min 3 caracteres).")
        if not admin_email or "@" not in admin_email: errors.append("Email admin invalide.")
        if not admin_name: errors.append("Nom complet admin requis.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            ok, org_id_or_err = create_organization(
                org_name, plan_tier, max_users, contact_email, notes,
                custom_monthly_price=custom_monthly_price,
            )
            if not ok:
                st.error(f"Erreur creation organisation : {org_id_or_err}")
            else:
                ok2, err, pwd = create_org_admin(
                    org_id_or_err, admin_username, admin_email, admin_name,
                    password=custom_pwd.strip() if custom_pwd.strip() else None,
                )
                if not ok2:
                    st.error(err)
                else:
                    st.success(f"✅ Organisation **{org_name}** creee avec succes !")
                    app_url = st.secrets.get("APP_URL", "https://votre-app.streamlit.app")
                    st.markdown(f"""
                    <div class='cred-box'>
                        <div style='font-size:11px;color:#6060a0;margin-bottom:8px;'>
                            ⚠️ Identifiants a transmettre au client — affiches une seule fois
                        </div>
                        <div style='font-size:14px;color:#e0e0f0;line-height:1.8;'>
                            URL d'acces : <strong>{app_url}</strong><br>
                            Identifiant : <strong>{admin_username}</strong><br>
                            Mot de passe : <strong>{pwd}</strong><br><br>
                            Plan : <strong>{tier_info['name']}</strong> ({max_users} licences)<br>
                            Tarif : <strong>{monthly_price:,} €/mois</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()

# ════════════════════════════════════════════════
# TAB — CLIENTS EXISTANTS
# ════════════════════════════════════════════════
with tab_list:
    if not orgs:
        st.info("Aucune organisation creee pour le moment.")
    else:
        for org in orgs:
            tier   = PLAN_TIERS.get(org["plan_tier"], {})
            used   = count_org_members(org["id"])
            price  = get_org_monthly_price(org)
            price_label = f"{price:,.0f}€/mois" + (" (negocie)" if tier.get("custom_pricing") else "")
            status_class = "status-active" if org["status"] == "active" else "status-suspended"
            status_label = "Actif" if org["status"] == "active" else "Suspendu"

            st.markdown(f"""
            <div class='org-row'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <div style='font-size:15px;font-weight:600;color:#e0e0f0;'>{org['name']}</div>
                        <div style='font-size:12px;color:#6060a0;margin-top:2px;'>{org.get('contact_email','—')}</div>
                    </div>
                    <span class='status-pill {status_class}'>{status_label}</span>
                </div>
                <div style='margin-top:10px;font-size:13px;color:#a0a0c0;'>
                    Plan <strong style='color:#7F77DD;'>{tier.get('name','—')}</strong>
                    · {used}/{org['max_users']} licences
                    · <strong style='color:#1D9E75;'>{price_label}</strong>
                </div>
                {f"<div style='margin-top:6px;font-size:11px;color:#404060;'>{org['notes']}</div>" if org.get('notes') else ""}
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if org["status"] == "active":
                    if st.button("Suspendre", key=f"susp_{org['id']}"):
                        update_organization_status(org["id"], "suspended")
                        st.rerun()
                else:
                    if st.button("Reactiver", key=f"react_{org['id']}"):
                        update_organization_status(org["id"], "active")
                        st.rerun()
            with col2:
                with st.popover("Modifier plan"):
                    new_tier = st.selectbox(
                        "Nouveau palier", options=list(PLAN_TIERS.keys()),
                        format_func=lambda k: PLAN_TIERS[k]["name"],
                        index=list(PLAN_TIERS.keys()).index(org["plan_tier"]),
                        key=f"tier_{org['id']}",
                    )
                    new_tier_info = PLAN_TIERS[new_tier]
                    new_max = st.number_input(
                        "Licences", min_value=new_tier_info["min_users"],
                        max_value=new_tier_info["max_users"],
                        value=min(max(org["max_users"], new_tier_info["min_users"]), new_tier_info["max_users"]),
                        key=f"max_{org['id']}",
                    )

                    new_custom_price = None
                    if new_tier_info["custom_pricing"]:
                        default_price = org.get("custom_monthly_price") or (new_max * new_tier_info["price_per_user"])
                        new_custom_price = st.number_input(
                            "Tarif mensuel negocie (€)", min_value=0,
                            value=int(default_price), step=100,
                            key=f"custom_price_{org['id']}",
                        )

                    if st.button("Mettre a jour", key=f"upd_{org['id']}"):
                        update_organization_plan(org["id"], new_tier, new_max, custom_monthly_price=new_custom_price)
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
