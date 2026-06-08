"""
Intégration Stripe — Paiement plan Premium
Utilise Stripe Checkout (redirect).
"""

import streamlit as st


PREMIUM_PRICE = "149€/mois"


def get_stripe_client():
    try:
        import stripe
        stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
        return stripe
    except Exception:
        return None


def create_checkout_session(username: str, email: str, success_url: str, cancel_url: str) -> str | None:
    """
    Crée une session Stripe Checkout.
    Retourne l'URL de paiement ou None si erreur.
    """
    stripe = get_stripe_client()
    if not stripe:
        return None

    try:
        price_id = st.secrets.get("STRIPE_PRICE_ID", "")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url + "?payment=success&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url + "?payment=cancelled",
            metadata={"username": username},
        )
        return session.url
    except Exception as e:
        st.error(f"Erreur Stripe : {e}")
        return None


def verify_payment_session(session_id: str) -> tuple[bool, str]:
    """
    Vérifie qu'une session Stripe a bien été payée.
    Retourne (success, username).
    """
    stripe = get_stripe_client()
    if not stripe:
        return False, ""

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status in ("paid", "no_payment_required"):
            username = session.metadata.get("username", "")
            return True, username
        return False, ""
    except Exception:
        return False, ""


def get_payment_link() -> str:
    """
    Retourne le Payment Link Stripe statique (alternative simple).
    Configuré dans secrets : STRIPE_PAYMENT_LINK
    """
    return st.secrets.get("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/votre-lien")
