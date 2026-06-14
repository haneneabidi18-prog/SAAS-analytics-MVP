import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import streamlit as st
from utils.auth     import is_authenticated, logout
from utils.payments import get_payment_link
from utils.org import get_organization

# ── Helpers Supabase directs ──────────────────────────────────────────────────
def get_sb():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def auth_user(username: str, password: str):
    import hashlib
    h = hashlib.sha256(password.encode()).hexdigest()
    try:
        sb  = get_sb()
        res = sb.table("users").select("*").eq("username", username.lower().strip()).execute()
        if not res.data:
            return None, "Identifiant ou mot de passe incorrect."
        user = res.data[0]
        if user["password_hash"] != h:
            return None, "Identifiant ou mot de passe incorrect."
        return user, ""
    except Exception as e:
        return None, f"Erreur connexion : {e}"

def register_user(username, email, password, display_name):
    import hashlib
    h = hashlib.sha256(password.encode()).hexdigest()
    try:
        sb = get_sb()
        # Vérif unicité
        if sb.table("users").select("id").eq("username", username.lower()).execute().data:
            return False, "Cet identifiant est déjà utilisé."
        if sb.table("users").select("id").eq("email", email.lower()).execute().data:
            return False, "Cet email est déjà enregistré."
        sb.table("users").insert({
            "username":      username.lower().strip(),
            "email":         email.lower().strip(),
            "password_hash": h,
            "display_name":  display_name.strip() or username.title(),
            "plan":          "basic",
        }).execute()
        return True, ""
    except Exception as e:
        return False, f"Erreur création : {e}"

def save_pending(username: str):
    try:
        get_sb().table("pending_upgrades").insert({"username": username.lower()}).execute()
    except Exception:
        pass

def pop_pending() -> str:
    try:
        sb  = get_sb()
        res = sb.table("pending_upgrades").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data:
            row = res.data[0]
            sb.table("pending_upgrades").delete().eq("id", row["id"]).execute()
            return row["username"]
    except Exception:
        pass
    return ""

def do_upgrade(username: str):
    try:
        get_sb().table("users").update({"plan": "premium"}).eq("username", username.lower()).execute()
        return True
    except Exception:
        return False

# ── Config page ───────────────────────────────────────────────────────────────
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
.stTextInput > div > div > input {
    background: #0f0f20 !important; border: 1px solid #2a2a4a !important;
    border-radius: 8px !important; color: #e0e0f0 !important; padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7F77DD !important; box-shadow: 0 0 0 2px #7F77DD22 !important;
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
.stTabs [data-baseweb="tab"] { color: #6060a0 !important; }
.stTabs [aria-selected="true"] { color: #7F77DD !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ── Retour Stripe ─────────────────────────────────────────────────────────────
payment_status = st.query_params.get("payment", "")

if payment_status == "success":
    st.query_params.clear()

    # Chercher qui upgrader : session ou pending_upgrades Supabase
    username_to_upgrade = (
        st.session_state.get("username") or
        pop_pending()
    )

    if username_to_upgrade:
        ok = do_upgrade(username_to_upgrade)
        if ok:
            st.session_state["plan"] = "premium"
            st.balloons()
            st.success(f"🎉 Paiement confirmé ! Compte **{username_to_upgrade}** passé en Premium.")
        else:
            st.error("Erreur lors de l'upgrade. Contactez contact@streamanalytics.pro")
    else:
        st.warning("Paiement reçu mais compte introuvable. Contactez contact@streamanalytics.pro")

elif payment_status == "cancelled":
    st.query_params.clear()
    st.warning("Paiement annulé. Vous pouvez réessayer à tout moment.")

# ── Déjà connecté ─────────────────────────────────────────────────────────────
if is_authenticated():
    plan       = st.session_state.get("plan", "basic")
    plan_color = "#7F77DD" if plan == "premium" else "#6060A0"
    plan_label = "Premium ⭐" if plan == "premium" else "Basic"

    st.markdown(f"""
    <div style='text-align:center;padding:40px 0 20px;'>
        <div style='font-size:40px;'>📡</div>
        <div style='font-size:22px;font-weight:700;color:#7F77DD;margin-top:8px;'>
            Bonjour, {st.session_state.get('display_name', '')} !
        </div>
        <div style='margin-top:8px;'>
            <span style='background:{plan_color}22;color:{plan_color};
                  border:1px solid {plan_color}55;padding:3px 12px;
                  border-radius:12px;font-size:12px;font-weight:600;'>
                {plan_label}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Aller au Dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Dashboard.py")
    with col2:
        if st.button("Deconnexion", use_container_width=True):
            logout()
            st.rerun()

    # Upgrade si basic
    if plan == "basic":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background:#14143a;border:1px solid #7F77DD44;border-radius:12px;
             padding:20px;text-align:center;'>
            <div style='font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:6px;'>
                Passez au plan Premium
            </div>
            <div style='font-size:12px;color:#6060a0;margin-bottom:4px;'>
                QoE Score · AI Decision Engine · AI Copilot · Analyse de Logs
            </div>
            <div style='font-size:18px;font-weight:700;color:#7F77DD;margin:10px 0 4px;'>
                149€ / mois
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Passer au Premium", use_container_width=True):
            uname = st.session_state.get("username", "")
            email = st.session_state.get("email", "")
            save_pending(uname)
            url = f"{get_payment_link()}?prefilled_email={email}&client_reference_id={uname}"
            st.markdown(f"<meta http-equiv='refresh' content='0; url={url}'>", unsafe_allow_html=True)
            st.markdown(f"[Cliquer ici si pas de redirection automatique]({url})")
    st.stop()

# ── Logo ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:35px 0 18px;'>
    <div style='font-size:42px;'>📡</div>
    <div style='font-size:24px;font-weight:700;color:#7F77DD;margin-top:8px;'>
        StreamAnalytics <span style='color:#ffffff;'>Pro</span>
    </div>
    <div style='font-size:13px;color:#6060a0;margin-top:4px;'>
        Plateforme de monitoring streaming avec AI
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_login, tab_register = st.tabs(["Connexion", "Creer un compte"])

# ─── LOGIN ────────────────────────────────────────────────────────────────────
with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    l_user = st.text_input("Identifiant", placeholder="votre identifiant", key="l_user")
    l_pwd  = st.text_input("Mot de passe", type="password", placeholder="••••••••", key="l_pwd")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Se connecter", use_container_width=True, key="btn_login"):
    if not l_user or not l_pwd:
        st.error("Veuillez renseigner tous les champs.")
    else:
        user, error = auth_user(l_user, l_pwd)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["username"]      = user["username"]
            st.session_state["display_name"]  = user.get("display_name", l_user.title())
            st.session_state["plan"]          = user.get("plan", "basic")
            st.session_state["email"]         = user.get("email", "")
            st.session_state["role"]          = user.get("role", "member")

            # Charger l'organisation si l'utilisateur en fait partie
            org_id = user.get("org_id")
            if org_id:
                st.session_state["org"] = get_organization(org_id)
            else:
                st.session_state["org"] = None

            st.switch_page("pages/1_Dashboard.py")
        else:
            st.error(error)

    st.markdown("""
    <div style='text-align:center;margin-top:14px;font-size:12px;color:#404060;'>
        Mot de passe oublie ? contact@streamanalytics.pro
    </div>
    """, unsafe_allow_html=True)

# ─── INSCRIPTION ──────────────────────────────────────────────────────────────
with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:13px;color:#a0a0c0;margin-bottom:10px;font-weight:600;'>Choisissez votre plan</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='plan-card' style='background:#0f0f20;'>
            <div style='font-size:14px;font-weight:600;color:#a0a0c0;'>Basic</div>
            <div style='font-size:22px;font-weight:700;color:#e0e0f0;margin:4px 0 8px;'>Gratuit</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ Dashboard Live</div>
            <div style='font-size:11px;color:#1D9E75;'>✓ Demo Interactive</div>
            <div style='font-size:11px;color:#404060;margin-top:4px;'>✗ QoE Score</div>
            <div style='font-size:11px;color:#404060;'>✗ AI Decision Engine</div>
            <div style='font-size:11px;color:#404060;'>✗ AI Copilot</div>
            <div style='font-size:11px;color:#404060;'>✗ Analyse de Logs</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='plan-card' style='background:#14143a;border-color:#7F77DD66;'>
            <div style='font-size:14px;font-weight:600;color:#7F77DD;'>Premium ⭐</div>
            <div style='font-size:22px;font-weight:700;color:#e0e0f0;margin:4px 0 8px;'>
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
        "Plan", options=["basic", "premium"],
        format_func=lambda x: "Basic — Gratuit" if x == "basic" else "Premium — 149€/mois",
        horizontal=True, label_visibility="collapsed", key="reg_plan",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    r_name  = st.text_input("Nom complet",              placeholder="Jean Dupont",         key="r_name")
    r_email = st.text_input("Email",                    placeholder="jean@exemple.com",    key="r_email")
    r_user  = st.text_input("Identifiant",              placeholder="jean_dupont",          key="r_user")
    r_pwd   = st.text_input("Mot de passe",             type="password",
                            placeholder="Minimum 6 caracteres",                             key="r_pwd")
    r_pwd2  = st.text_input("Confirmer le mot de passe",type="password",
                            placeholder="••••••••",                                          key="r_pwd2")
    st.markdown("<br>", unsafe_allow_html=True)

    btn_label = "Creer mon compte" if selected_plan == "basic" else "Creer mon compte et payer →"
    if st.button(btn_label, use_container_width=True, key="btn_register", type="primary"):
        errors = []
        if not all([r_name, r_email, r_user, r_pwd, r_pwd2]):
            errors.append("Tous les champs sont obligatoires.")
        if r_pwd != r_pwd2:
            errors.append("Les mots de passe ne correspondent pas.")
        if len(r_pwd) < 6:
            errors.append("Le mot de passe doit contenir au moins 6 caracteres.")
        if "@" not in r_email:
            errors.append("Email invalide.")
        if len(r_user) < 3:
            errors.append("L'identifiant doit contenir au moins 3 caracteres.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            ok, err = register_user(r_user, r_email, r_pwd, r_name)
            if not ok:
                st.error(err)
            else:
                # Connecter
                st.session_state["authenticated"] = True
                st.session_state["username"]      = r_user.lower()
                st.session_state["display_name"]  = r_name
                st.session_state["plan"]          = "basic"
                st.session_state["email"]         = r_email.lower()

                if selected_plan == "premium":
                    uname = r_user.lower()
                    # Sauvegarder dans Supabase avant redirection
                    save_pending(uname)
                    pay_link = get_payment_link()
                    url = f"{pay_link}?prefilled_email={r_email}&client_reference_id={uname}"
                    st.success("Compte cree ! Cliquez ci-dessous pour finaliser.")
                    st.markdown(f"""
                    <div style='background:#14143a;border:1px solid #7F77DD55;border-radius:12px;
                         padding:24px;text-align:center;margin-top:8px;'>
                        <div style='font-size:20px;margin-bottom:8px;'>💳</div>
                        <div style='font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:6px;'>
                            Finaliser votre abonnement Premium
                        </div>
                        <div style='font-size:12px;color:#a0a0c0;margin-bottom:16px;'>
                            149€/mois · Sans engagement · Annulable a tout moment
                        </div>
                        <a href='{url}' target='_blank'
                           style='background:linear-gradient(90deg,#7F77DD,#534AB7);
                                  color:white;padding:12px 32px;border-radius:8px;
                                  text-decoration:none;font-weight:600;font-size:14px;'>
                            Payer maintenant →
                        </a>
                        <div style='font-size:11px;color:#404060;margin-top:12px;'>
                            Apres le paiement vous serez redirige automatiquement
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success("Compte Basic cree ! Bienvenue.")
                    st.switch_page("pages/1_Dashboard.py")

st.markdown("""
<div style='text-align:center;margin-top:24px;font-size:12px;color:#303050;'>
    contact@streamanalytics.pro
</div>
""", unsafe_allow_html=True)
