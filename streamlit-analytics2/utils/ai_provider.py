"""
Abstraction fournisseur IA pour l'AI Copilot et l'Analyse de Logs.

Priorite :
  1. Gemini (gratuit, sans carte bancaire — via GEMINI_API_KEY)
  2. Anthropic Claude (si ANTHROPIC_API_KEY est configuree)

Aucune des deux configuree -> RuntimeError("NO_PROVIDER"), gere par l'appelant
(generalement avec un mode demo / reponses pre-ecrites).
"""

import streamlit as st


def get_provider() -> str | None:
    if st.secrets.get("GEMINI_API_KEY"):
        return "gemini"
    if st.secrets.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def stream_response(messages: list[dict], system: str, model_label: str = "standard"):
    """
    Genere une reponse en streaming, chunk de texte par chunk de texte.

    messages    : liste de {"role": "user"|"assistant", "content": str}
    system      : instructions systeme
    model_label : "standard" (qualite) ou "rapide" (vitesse)
    """
    provider = get_provider()

    if provider == "gemini":
        from google import genai
        from google.genai import types

        api_key = st.secrets["GEMINI_API_KEY"]
        client  = genai.Client(api_key=api_key)

        model = "gemini-2.5-flash" if model_label == "standard" else "gemini-2.5-flash-lite"

        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

        config = types.GenerateContentConfig(system_instruction=system)

        stream = client.models.generate_content_stream(
            model=model, contents=contents, config=config,
        )
        for chunk in stream:
            if getattr(chunk, "text", None):
                yield chunk.text

    elif provider == "anthropic":
        import anthropic

        api_key = st.secrets["ANTHROPIC_API_KEY"]
        client  = anthropic.Anthropic(api_key=api_key)

        model = "claude-sonnet-4-6" if model_label == "standard" else "claude-haiku-4-5-20251001"

        with client.messages.stream(
            model=model, max_tokens=1000, system=system,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
        ) as stream:
            for text in stream.text_stream:
                yield text

    else:
        raise RuntimeError("NO_PROVIDER")


def friendly_error(e: Exception) -> str:
    """Transforme une erreur technique en message comprehensible pour l'utilisateur."""
    msg = str(e)
    low = msg.lower()
    if "api key" in low or "api_key" in low or "401" in msg or "403" in msg or "permission" in low:
        return "❌ Cle IA invalide ou manquante. Contactez l'administrateur de la plateforme."
    if "429" in msg or "resource_exhausted" in low or "rate" in low or "quota" in low:
        return "⏳ Limite de requetes atteinte (quota gratuit). Reessayez dans quelques instants."
    if "not_found" in low or "404" in msg or "not found" in low:
        return "❌ Modele introuvable. Verifiez la configuration."
    return f"Erreur : {msg}"
