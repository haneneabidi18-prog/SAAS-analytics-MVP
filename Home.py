import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import streamlit as st
from utils.auth import is_authenticated, logout, PLANS
from utils.db   import authenticate_user, create_user, upgrade_to_premium, get_user_by_username
from utils.payments import get_payment_link, verify_payment_session

st.set_page_config(
    page_title="StreamAnalytics Pro",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #07070f; }
[data-testid="stSidebar"] { display: none; }

.card {
    background: linear-gradient(135deg, #0f0f1a, #14143a);
    border: 1px solid #7F77DD44;
    border-radius: 16px;
    padding: 36px 40px;
    max-width: 440px;
    margin: 0 auto;
}
.stTextInput > div > div > input {
    background: #0f0f20 !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
    color: #e0e0f0 !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7F77DD !important;
    box-shadow: 0 0 0 2px #7F77DD22 !important;
}
.stTextInput label { color: #a0a0c0 !important; font-size: 13px !important; }
.stButton > button {
    background: linear-gradient(90deg, #7F77DD, #534AB7) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
.plan-card { border-radius: 12px; padding: 18px; border: 1px solid #2a2a4a; }
.stTabs [data-baseweb="tab"] {
    color: #6060a0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stTabs [aria-selected="true"] { color: #7F77DD !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ── Vérifier retour Stripe ────────────────────────────────────────────────────
params = st.query_params
payment_status = params.get("payment", "")
session_id     = params.get("session_id", "")

if payment_status == "success":
    st.query_params.clear()
    if is_authenticated():
        upgrade_to_premium(st.session_state.get("username", ""), session_id)
        st.session_state["plan"] = "premium"
        st.success("🎉 Paiement confirmé ! Votre compte est maintenant Premium.")
    else:
        st.success("🎉 Paiement confirmé ! Connectez-vous pour accéder à Premium.")

elif payment_status == "cancelled":
    st.query_params.clear()
    st.warning("Paiement annulé. Vous pouvez réessayer à tout moment.")

# ── Si déjà connecté → dashboard ─────────────────────────────────────────────
if is_authenticated():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Aller au Dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Dashboard.py")
    with col2:
        if st.button("Déconnexion", use_container_width=True):
            logout()
            st.rerun()
    st.stop()

# ── LOGO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 35px 0 18px 0;'>
    <div style='font-size:42px;'>📡</div>
    <div style='font-size:24px; font-weight:700; color:#7F77DD; margin-top:8px;'>
        StreamAnalytics <span style='color:#ffffff;'>Pro</span>
    </div>
    <div style='font-size:13px; color:#6060a0; margin-top:4px;'>
        Plateforme de monitoring streaming avec AI
    </div>
</div>
""", unsafe_allow_html=True)

# ── TABS LOGIN / INSCRIPTION ──────────────────────────────────────────────────
tab_login, tab_register = st.tabs(["Connexion", "Créer un compte"])

# ════════════════════════════════════════════════
# TAB 1 — LOGIN
# ════════════════════════════════════════════════
with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    username = st.text_input("Identifiant", placeholder="votre identifiant", key="login_user")
    password = st.text_input("Mot de passe", type="password", placeholder="••••••••", key="login_pwd")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Se connecter", use_container_width=True, key="btn_login"):
        if not username or not password:
            st.error("Veuillez renseigner tous les champs.")
        else:
            success, user, error = authenticate_user(username, password)
            if success and user:
                st.session_state["authenticated"] = True
                st.session_state["username"]      = user["username"]
                st.session_state["display_name"]  = user.get("display_name", username.title())
                st.session_state["plan"]          = user.get("plan", "basic")
                st.session_state["email"]         = user.get("email", "")
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.error(error)

    st.markdown("""
    <div style='text-align:center;margin-top:16px;font-size:12px;color:#404060;'>
        Mot de passe oublié ? <span style='color:#7F77DD;'>contact@streamanalytics.pro</span>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 2 — INSCRIPTION
# ════════════════════════════════════════════════
with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)

    # Choix du plan
    st.markdown("<div style='font-size:13px;color:#a0a0c0;margin-bottom:10px;font-weight:600;'>Choisissez votre plan</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class='plan-card' style='background:#0f0f20;cursor:pointer;'>
            <div style='font-size:14px;font-weight:600;color:#a0a0c0;'>Basic</div>
            <div style='font-size:22px;font-weight:700;color:#e0e0f0;margin:4px 0 8px 0;'>Gratuit</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ Dashboard Live</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ Demo Interactive</div>
            <div style='font-size:11px;color:#404060;margin-top:4px;'>✗ QoE Score</div>
            <div style='font-size:11px;color:#404060;'>✗ AI Decision Engine</div>
            <div style='font-size:11px;color:#404060;'>✗ AI Copilot</div>
            <div style='font-size:11px;color:#404060;'>✗ Analyse de Logs</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='plan-card' style='background:#14143a;border-color:#7F77DD66;cursor:pointer;'>
            <div style='font-size:14px;font-weight:600;color:#7F77DD;'>Premium ⭐</div>
            <div style='font-size:22px;font-weight:700;color:#e0e0f0;margin:4px 0 8px 0;'>
                149€<span style='font-size:12px;color:#6060a0;'>/mois</span>
            </div>
            <div style='font-size:11px;color:#1D9E75;'>✓ Dashboard Live</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ Demo Interactive</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ QoE Score</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ AI Decision Engine</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ AI Copilot</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ Analyse de Logs</div>
        </div>
        """, unsafe_allow_html=True)

    selected_plan = st.radio(
        "Plan sélectionné",
        options=["basic", "premium"],
        format_func=lambda x: "Basic — Gratuit" if x == "basic" else "Premium — 149€/mois",
        horizontal=True,
        label_visibility="collapsed",
        key="reg_plan",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    r_name     = st.text_input("Nom complet",    placeholder="Jean Dupont",         key="r_name")
    r_email    = st.text_input("Email",           placeholder="jean@exemple.com",    key="r_email")
    r_username = st.text_input("Identifiant",     placeholder="jean_dupont",         key="r_user")
    r_pwd      = st.text_input("Mot de passe",    type="password", placeholder="Minimum 6 caractères", key="r_pwd")
    r_pwd2     = st.text_input("Confirmer le mot de passe", type="password", placeholder="••••••••", key="r_pwd2")

    st.markdown("<br>", unsafe_allow_html=True)
    btn_label = "Créer mon compte" if selected_plan == "basic" else "Créer mon compte et payer →"

    if st.button(btn_label, use_container_width=True, key="btn_register", type="primary"):
        # Validations
        errors = []
        if not all([r_name, r_email, r_username, r_pwd, r_pwd2]):
            errors.append("Tous les champs sont obligatoires.")
        if r_pwd != r_pwd2:
            errors.append("Les mots de passe ne correspondent pas.")
        if len(r_pwd) < 6:
            errors.append("Le mot de passe doit contenir au moins 6 caractères.")
        if "@" not in r_email:
            errors.append("Email invalide.")
        if len(r_username) < 3:
            errors.append("L'identifiant doit contenir au moins 3 caractères.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # Créer le compte (basic d'abord, upgrade après paiement)
            ok, err = create_user(
                username     = r_username,
                email        = r_email,
                password     = r_pwd,
                display_name = r_name,
                plan         = "basic",   # Toujours basic à la création
            )
            if not ok:
                st.error(err)
            else:
                # Connecter l'utilisateur
                st.session_state["authenticated"] = True
                st.session_state["username"]      = r_username.lower()
                st.session_state["display_name"]  = r_name
                st.session_state["plan"]          = "basic"
                st.session_state["email"]         = r_email.lower()

                if selected_plan == "premium":
                    # Rediriger vers Stripe
                    app_url = st.secrets.get("APP_URL", "https://votre-app.streamlit.app")
                    payment_link = get_payment_link()

                    st.success("✅ Compte créé ! Redirection vers le paiement...")
                    st.markdown(f"""
                    <div style='background:#14143a;border:1px solid #7F77DD55;border-radius:12px;
                         padding:24px;text-align:center;margin-top:12px;'>
                        <div style='font-size:20px;margin-bottom:8px;'>💳</div>
                        <div style='font-size:16px;font-weight:600;color:#e0e0f0;margin-bottom:8px;'>
                            Finaliser votre abonnement Premium
                        </div>
                        <div style='font-size:13px;color:#a0a0c0;margin-bottom:16px;'>
                            149€/mois · Sans engagement · Annulable à tout moment
                        </div>
                        <a href='{payment_link}?prefilled_email={r_email}&client_reference_id={r_username.lower()}'
                           target='_blank'
                           style='background:linear-gradient(90deg,#7F77DD,#534AB7);
                                  color:white;padding:12px 32px;border-radius:8px;
                                  text-decoration:none;font-weight:600;font-size:14px;'>
                            Payer maintenant →
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    st.info("Après le paiement, revenez sur l'app et reconnectez-vous.")
                else:
                    st.success("✅ Compte Basic créé ! Bienvenue.")
                    st.switch_page("pages/1_Dashboard.py")

# ── Plans résumé ──────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;margin-top:24px;font-size:12px;color:#303050;'>
    Déjà client ? Connectez-vous via l'onglet Connexion · contact@streamanalytics.pro
</div>
""", unsafe_allow_html=True)
