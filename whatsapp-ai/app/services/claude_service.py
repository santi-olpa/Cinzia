import anthropic
import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# Use Sonnet for complex cases, Haiku for simple queries
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_HAIKU = "claude-haiku-4-5-20251001"

# Max tokens to keep in conversation history (avoid exceeding context window)
MAX_HISTORY_MESSAGES = 20


async def get_response(
    system_prompt: str,
    conversation_history: list[dict],
    use_haiku: bool = False,
) -> Optional[str]:
    """
    Send conversation to Claude and get a response.
    conversation_history: list of {"role": "user"|"assistant", "content": "..."}
    """
    model = MODEL_HAIKU if use_haiku else MODEL_SONNET

    # Keep only last N messages to control cost
    trimmed_history = conversation_history[-MAX_HISTORY_MESSAGES:]

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=trimmed_history,
        )
        return response.content[0].text
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return None


async def classify_intent(message: str, language: str = "es") -> str:
    """
    Quick Haiku call to classify message intent before the main response.
    Returns one of: consulta_informativa, troubleshooting, emergencia,
                    dejar_registro, devolucion, ventas, reclamo, unknown
    """
    prompt = f"""Classify the intent of this WhatsApp message from a motorhome rental customer.
Reply with ONLY one of these labels, nothing else:
- consulta_informativa
- troubleshooting
- emergencia
- dejar_registro
- devolucion
- ventas
- reclamo
- unknown

Message: {message}"""

    try:
        response = client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        intent = response.content[0].text.strip().lower()
        valid = {
            "consulta_informativa", "troubleshooting", "emergencia",
            "dejar_registro", "devolucion", "ventas", "reclamo", "unknown"
        }
        return intent if intent in valid else "unknown"
    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return "unknown"


async def detect_language(message: str) -> str:
    """Quick detection of message language. Returns 'es' or 'en'."""
    prompt = f"What language is this message written in? Reply with ONLY 'es' or 'en'.\n\nMessage: {message}"
    try:
        response = client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}],
        )
        lang = response.content[0].text.strip().lower()
        return lang if lang in ("es", "en") else "es"
    except Exception:
        return "es"
