"""
Couche base de données — Supabase
Gère les utilisateurs, plans et paiements Stripe.
"""

import hashlib
import streamlit as st
from datetime import datetime

# ── SQL de création de table (à exécuter 1 fois dans Supabase) ───────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        TEXT UNIQUE NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    display_name    TEXT,
    plan            TEXT DEFAULT 'basic',
    stripe_customer_id TEXT,
    stripe_session_id  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
"""


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@st.cache_resource
def get_supabase():
    """Retourne le client Supabase (singleton)."""
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        return None


def create_user(username: str, email: str, password: str,
                display_name: str, plan: str = "basic") -> tuple[bool, str]:
    """
    Crée un nouvel utilisateur.
    Retourne (success, error_message).
    """
    sb = get_supabase()
    if not sb:
        return False, "Base de données non configurée."

    try:
        # Vérifier unicité username
        existing = sb.table("users").select("id").eq("username", username.lower()).execute()
        if existing.data:
            return False, "Cet identifiant est déjà utilisé."

        # Vérifier unicité email
        existing_email = sb.table("users").select("id").eq("email", email.lower()).execute()
        if existing_email.data:
            return False, "Cet email est déjà enregistré."

        sb.table("users").insert({
            "username":     username.lower().strip(),
            "email":        email.lower().strip(),
            "password_hash": _hash(password),
            "display_name": display_name.strip() or username.title(),
            "plan":         plan,
        }).execute()

        return True, ""
    except Exception as e:
        return False, f"Erreur lors de la création du compte : {e}"


def authenticate_user(username: str, password: str) -> tuple[bool, dict | None, str]:
    """
    Authentifie un utilisateur.
    Retourne (success, user_dict, error_message).
    """
    sb = get_supabase()
    if not sb:
        # Fallback sur secrets.toml si Supabase pas configuré
        return _auth_from_secrets(username, password)

    try:
        result = sb.table("users")\
            .select("*")\
            .eq("username", username.lower().strip())\
            .execute()

        if not result.data:
            return False, None, "Identifiant ou mot de passe incorrect."

        user = result.data[0]
        if user["password_hash"] != _hash(password):
            return False, None, "Identifiant ou mot de passe incorrect."

        return True, user, ""
    except Exception as e:
        return False, None, f"Erreur de connexion : {e}"


# ── def upgrade_to_premium(username: str, stripe_session_id: str = "") -> bool:
  # ──   """Passe l'utilisateur en plan premium après paiement."""
 # ──    sb = get_supabase()
 # ──    if not sb:
  # ──       return False
  # ──   try:
  # ──       sb.table("users").update({
   # ──          "plan":              "premium",
   # ──          "stripe_session_id": stripe_session_id,
    # ──         "updated_at":        datetime.now().isoformat(),
    # ──     }).eq("username", username.lower()).execute()
     # ──    return True
    # ── except Exception:
     # ──    return False

def upgrade_to_premium(username: str, stripe_session_id: str = "") -> bool:
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        sb  = create_client(url, key)

        result = sb.table("users").update({
            "plan": "premium",
            "stripe_session_id": stripe_session_id,
        }).eq("username", username.lower().strip()).execute()

        return len(result.data) > 0
    except Exception as e:
        st.error(f"Erreur upgrade: {e}")
        return False
    
def get_user_by_username(username: str) -> dict | None:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("users").select("*").eq("username", username.lower()).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


# ── Fallback secrets.toml (si Supabase pas encore configuré) ─────────────────
def _auth_from_secrets(username: str, password: str) -> tuple[bool, dict | None, str]:
    """Auth de secours via secrets.toml."""
    try:
        users = dict(st.secrets.get("users", {}))
        uname = username.strip().lower()
        if uname not in users:
            return False, None, "Identifiant ou mot de passe incorrect."
        user = users[uname]
        if user.get("password_hash", "") != _hash(password):
            return False, None, "Identifiant ou mot de passe incorrect."
        return True, {
            "username":     uname,
            "email":        user.get("email", ""),
            "display_name": user.get("display_name", username.title()),
            "plan":         user.get("plan", "basic"),
        }, ""
    except Exception as e:
        return False, None, f"Erreur : {e}"
