"""
Gestion des organisations (clients ISP) et licences par equipe.
Modele de tarification par paliers (type Microsoft 365) :
  - Starter    : 1-5 utilisateurs   -> 149 EUR / utilisateur / mois
  - Business   : 6-20 utilisateurs  -> 119 EUR / utilisateur / mois
  - Enterprise : 21-50 utilisateurs -> 89  EUR / utilisateur / mois
"""

import secrets
import string
import hashlib
import streamlit as st


# ── Paliers de tarification ──────────────────────────────────────────────────
PLAN_TIERS = {
    "starter": {
        "name":           "Starter",
        "label":          "1 a 5 utilisateurs",
        "min_users":      1,
        "max_users":      5,
        "price_per_user": 149,
        "custom_pricing": False,
    },
    "business": {
        "name":           "Business",
        "label":          "6 a 20 utilisateurs",
        "min_users":      6,
        "max_users":      20,
        "price_per_user": 119,
        "custom_pricing": False,
    },
    "enterprise": {
        "name":           "Enterprise",
        "label":          "21 a 50 utilisateurs",
        "min_users":      21,
        "max_users":      50,
        "price_per_user": 89,
        "custom_pricing": False,
    },
    "enterprise_plus": {
        "name":           "Enterprise+",
        "label":          "50+ utilisateurs (sur devis)",
        "min_users":      51,
        "max_users":      1000,
        "price_per_user": 75,   # tarif de reference indicatif, prix final negocie
        "custom_pricing": True,
    },
}


def estimate_monthly_price(plan_tier: str, n_users: int, custom_price: float | None = None) -> float:
    """
    Calcule le tarif mensuel.
    Pour 'enterprise_plus', si custom_price est fourni (tarif negocie avec le client),
    il prevaut sur le calcul automatique par utilisateur.
    """
    tier = PLAN_TIERS.get(plan_tier, PLAN_TIERS["starter"])
    if tier.get("custom_pricing") and custom_price is not None:
        return custom_price
    return tier["price_per_user"] * n_users


def get_org_monthly_price(org: dict) -> float:
    """
    Calcule le tarif mensuel d'une organisation en tenant compte
    d'un eventuel tarif negocie (custom_monthly_price) stocke en base.
    """
    return estimate_monthly_price(
        org.get("plan_tier", "starter"),
        org.get("max_users", 0),
        custom_price=org.get("custom_monthly_price"),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _gen_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_sb():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# ── Organisations (Super Admin — ABIDSON) ──────────────────────────────────────
def create_organization(name: str, plan_tier: str, max_users: int,
                        contact_email: str = "", notes: str = "",
                        custom_monthly_price: float | None = None) -> tuple[bool, str]:
    """Cree une organisation cliente. Retourne (success, org_id_ou_erreur)."""
    try:
        sb = get_sb()
        payload = {
            "name":          name.strip(),
            "plan_tier":     plan_tier,
            "max_users":     max_users,
            "contact_email": contact_email.strip().lower(),
            "notes":         notes,
            "status":        "active",
        }
        if custom_monthly_price is not None:
            payload["custom_monthly_price"] = custom_monthly_price
        result = sb.table("organizations").insert(payload).execute()
        if result.data:
            return True, result.data[0]["id"]
        return False, "Erreur lors de la creation de l'organisation."
    except Exception as e:
        return False, str(e)


def list_organizations() -> list[dict]:
    try:
        sb = get_sb()
        result = sb.table("organizations").select("*").order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def get_organization(org_id: str) -> dict | None:
    try:
        sb = get_sb()
        result = sb.table("organizations").select("*").eq("id", org_id).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def update_organization_status(org_id: str, status: str) -> bool:
    try:
        sb = get_sb()
        sb.table("organizations").update({"status": status}).eq("id", org_id).execute()
        return True
    except Exception:
        return False


def update_organization_plan(org_id: str, plan_tier: str, max_users: int,
                             custom_monthly_price: float | None = None) -> bool:
    try:
        sb = get_sb()
        payload = {
            "plan_tier": plan_tier,
            "max_users": max_users,
            "custom_monthly_price": custom_monthly_price,
        }
        sb.table("organizations").update(payload).eq("id", org_id).execute()
        return True
    except Exception:
        return False


# ── Compte admin initial (cree par ABIDSON apres virement) ─────────────────────
def create_org_admin(org_id: str, username: str, email: str,
                     display_name: str, password: str = None) -> tuple[bool, str, str]:
    """
    Cree le premier compte administrateur d'une organisation.
    Retourne (success, error, password_genere)
    """
    pwd = password or _gen_password()
    try:
        sb = get_sb()
        if sb.table("users").select("id").eq("username", username.lower()).execute().data:
            return False, "Cet identifiant existe deja.", ""
        if sb.table("users").select("id").eq("email", email.lower()).execute().data:
            return False, "Cet email est deja enregistre.", ""

        sb.table("users").insert({
            "username":      username.lower().strip(),
            "email":         email.lower().strip(),
            "password_hash": _hash(pwd),
            "display_name":  display_name.strip(),
            "plan":          "premium",
            "role":          "org_admin",
            "org_id":        org_id,
        }).execute()
        return True, "", pwd
    except Exception as e:
        return False, str(e), ""


# ── Membres de l'equipe (gere par org_admin) ────────────────────────────────────
def count_org_members(org_id: str) -> int:
    try:
        sb = get_sb()
        result = sb.table("users").select("id").eq("org_id", org_id).execute()
        return len(result.data or [])
    except Exception:
        return 0


def list_org_members(org_id: str) -> list[dict]:
    try:
        sb = get_sb()
        result = sb.table("users")\
            .select("id, username, email, display_name, role, created_at")\
            .eq("org_id", org_id)\
            .order("created_at")\
            .execute()
        return result.data or []
    except Exception:
        return []


def add_team_member(org_id: str, email: str, display_name: str) -> tuple[bool, str, str, str]:
    """
    Ajoute un membre a l'organisation (limite par le nombre de licences).
    Retourne (success, error, username_genere, password_genere)
    """
    org = get_organization(org_id)
    if not org:
        return False, "Organisation introuvable.", "", ""
    if org.get("status") != "active":
        return False, "Cette organisation est suspendue.", "", ""

    current = count_org_members(org_id)
    if current >= org["max_users"]:
        return False, f"Limite de licences atteinte ({org['max_users']} utilisateurs). Contactez ABIDSON pour upgrader votre plan.", "", ""

    sb = get_sb()

    if sb.table("users").select("id").eq("email", email.lower().strip()).execute().data:
        return False, "Cet email est deja enregistre.", "", ""

    # Generer un username unique depuis l'email
    base_username = email.split("@")[0].lower().strip()
    username = base_username
    suffix = 1
    while sb.table("users").select("id").eq("username", username).execute().data:
        suffix += 1
        username = f"{base_username}{suffix}"

    pwd = _gen_password()
    try:
        sb.table("users").insert({
            "username":      username,
            "email":         email.lower().strip(),
            "password_hash": _hash(pwd),
            "display_name":  display_name.strip() or username.title(),
            "plan":          "premium",
            "role":          "member",
            "org_id":        org_id,
        }).execute()
        return True, "", username, pwd
    except Exception as e:
        return False, str(e), "", ""


def remove_team_member(user_id: str) -> bool:
    try:
        sb = get_sb()
        sb.table("users").delete().eq("id", user_id).execute()
        return True
    except Exception:
        return False


def reset_member_password(user_id: str) -> tuple[bool, str]:
    """Genere un nouveau mot de passe pour un membre."""
    pwd = _gen_password()
    try:
        sb = get_sb()
        sb.table("users").update({"password_hash": _hash(pwd)}).eq("id", user_id).execute()
        return True, pwd
    except Exception as e:
        return False, str(e)
