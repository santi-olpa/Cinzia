import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import Customer, Conversation, EscalationCase, Fleet, CustomerStage
from app.services import whatsapp, claude_service, transcription, knowledge_base
from app.config import get_settings
from prompts.system_prompt import build_system_prompt, build_escalation_summary

logger = logging.getLogger(__name__)
settings = get_settings()

# Hard-stop keywords that trigger immediate escalation (no troubleshooting attempts)
EMERGENCY_KEYWORDS = {
    "es": ["accidente", "choque", "incendio", "fuego", "gas", "varado", "varada",
           "atascado", "atascada", "emergencia", "herido", "herida", "médico", "ambulancia"],
    "en": ["accident", "crash", "fire", "gas leak", "stuck", "stranded",
           "emergency", "injured", "medical", "ambulance"],
}

MAX_TROUBLESHOOTING_ATTEMPTS = 2


async def handle_incoming_message(parsed: dict, db: Session) -> None:
    wa_id = parsed["wa_id"]
    name = parsed.get("name", "")
    msg_type = parsed["type"]

    # Get or create customer
    customer = db.query(Customer).filter(Customer.wa_id == wa_id).first()
    if not customer:
        customer = Customer(wa_id=wa_id, name=name)
        db.add(customer)
        db.commit()

    # Update name if we now have it
    if name and not customer.name:
        customer.name = name
        db.commit()

    # --- Extract text content from message ---
    user_text = ""

    if msg_type == "text":
        user_text = parsed.get("text", "")

    elif msg_type == "audio":
        media_bytes = await whatsapp.download_media(parsed["media_id"])
        if media_bytes:
            transcribed = await transcription.transcribe_audio(
                media_bytes, parsed.get("mime_type", "audio/ogg")
            )
            if transcribed:
                user_text = f"[Audio transcripto]: {transcribed}"
            else:
                await whatsapp.send_text_message(
                    wa_id,
                    "No pude procesar tu audio. ¿Podés escribirme lo que necesitás?"
                    if customer.language == "es"
                    else "I couldn't process your audio. Could you write your message instead?",
                )
                return
        else:
            return

    elif msg_type == "image":
        caption = parsed.get("caption", "")
        user_text = f"[El cliente envió una foto{': ' + caption if caption else ''}]"

    if not user_text:
        return

    # --- Detect language on first message ---
    if customer.language == "es" and len(db.query(Conversation).filter(
        Conversation.wa_id == wa_id
    ).all()) == 0:
        detected_lang = await claude_service.detect_language(user_text)
        customer.language = detected_lang
        db.commit()

    # --- Check for emergency keywords ---
    lang = customer.language
    emergency_words = EMERGENCY_KEYWORDS.get(lang, EMERGENCY_KEYWORDS["es"])
    is_emergency = any(kw in user_text.lower() for kw in emergency_words)

    # --- Save user message ---
    db.add(Conversation(
        wa_id=wa_id,
        role="user",
        content=user_text,
        message_type=msg_type,
    ))
    db.commit()

    # --- Count troubleshooting attempts ---
    troubleshooting_count = db.query(EscalationCase).filter(
        EscalationCase.wa_id == wa_id,
        EscalationCase.resolved == False,
    ).count()

    # --- Classify intent ---
    intent = await claude_service.classify_intent(user_text, lang)
    logger.info(f"[{wa_id}] intent={intent}, emergency={is_emergency}")

    # --- Escalation decision ---
    should_escalate_jorge = (
        is_emergency
        or intent == "emergencia"
        or troubleshooting_count >= MAX_TROUBLESHOOTING_ATTEMPTS
    )
    should_escalate_paulo = intent in ("reclamo",) and "seguro" in user_text.lower()

    if should_escalate_paulo:
        await _escalate(wa_id, customer, db, user_text, level="paulo")
        return

    if should_escalate_jorge:
        await _escalate(wa_id, customer, db, user_text, level="jorge")
        return

    # --- Build conversation history ---
    history_rows = (
        db.query(Conversation)
        .filter(Conversation.wa_id == wa_id)
        .order_by(Conversation.created_at)
        .all()
    )
    history = [{"role": row.role, "content": row.content} for row in history_rows]

    # --- Load knowledge base ---
    kb_section = knowledge_base.get_knowledge_section(customer.fleet or "argentina")

    # --- Build system prompt ---
    system = build_system_prompt(
        fleet=customer.fleet or "argentina",
        customer_name=customer.name or "",
        vehicle=customer.vehicle or "",
        stage=customer.stage or CustomerStage.UNKNOWN,
        language=lang,
        knowledge_section=kb_section,
        troubleshooting_attempts=troubleshooting_count,
    )

    # Use Haiku for simple informational queries to save cost
    use_haiku = intent == "consulta_informativa"

    # --- Get Claude response ---
    response_text = await claude_service.get_response(system, history, use_haiku=use_haiku)

    if not response_text:
        fallback = (
            "Perdón, tuve un problema técnico. Intento de nuevo en un momento."
            if lang == "es"
            else "Sorry, I had a technical issue. Please try again in a moment."
        )
        await whatsapp.send_text_message(wa_id, fallback)
        return

    # --- Save assistant response ---
    db.add(Conversation(
        wa_id=wa_id,
        role="assistant",
        content=response_text,
        message_type="text",
    ))
    db.commit()

    # --- Send response ---
    await whatsapp.send_text_message(wa_id, response_text)


async def _escalate(wa_id: str, customer: Customer, db: Session, problem_text: str, level: str):
    lang = customer.language or "es"
    attempts = db.query(Conversation).filter(
        Conversation.wa_id == wa_id, Conversation.role == "assistant"
    ).count()

    # Save escalation case
    case = EscalationCase(
        wa_id=wa_id,
        customer_name=customer.name,
        vehicle=customer.vehicle,
        problem_summary=problem_text[:500],
        attempts=attempts,
        level=level,
    )
    db.add(case)
    db.commit()

    # Notify the right person
    target_number = (
        settings.escalation_jorge_number
        if level == "jorge"
        else settings.escalation_paulo_number
    )

    if target_number:
        summary = build_escalation_summary(
            customer_name=customer.name or wa_id,
            vehicle=customer.vehicle or "N/A",
            problem_summary=problem_text[:300],
            attempts=attempts,
            level=level,
            language="es",
        )
        await whatsapp.send_text_message(target_number, summary)
        case.notified = True
        db.commit()

    # Inform the customer
    if level == "jorge":
        msg_es = "Estoy comunicando tu caso a Jorge ahora mismo. Te va a contactar en breve."
        msg_en = "I'm escalating your case to Jorge right now. He will contact you shortly."
    else:
        msg_es = "Estoy comunicando tu situación a Paulo ahora mismo. Te contactará a la brevedad."
        msg_en = "I'm escalating your situation to Paulo right now. He will be in touch shortly."

    await whatsapp.send_text_message(wa_id, msg_es if lang == "es" else msg_en)

    # Log in conversation
    db.add(Conversation(
        wa_id=wa_id,
        role="assistant",
        content=f"[ESCALADO A {level.upper()}]",
        message_type="text",
    ))
    db.commit()
