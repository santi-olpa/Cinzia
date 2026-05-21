import base64
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import create_tables, get_db
from app.services import whatsapp, knowledge_base
from app.handlers.message_handler import handle_incoming_message, handle_bridge_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    logger.info("Database tables ready")
    # Pre-load knowledge base into cache
    knowledge_base.load_fleet_knowledge("argentina")
    knowledge_base.load_fleet_knowledge("miami")
    logger.info("Knowledge base loaded")
    yield


app = FastAPI(title="Cinzia WhatsApp AI", lifespan=lifespan)


# ── Webhook verification (Meta sends a GET to verify the endpoint) ──────────
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("Webhook verified by Meta")
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


# ── Incoming messages (Meta sends POST with each message) ───────────────────
@app.post("/webhook")
async def receive_message(request: Request, db: Session = Depends(get_db)):
    body = await request.json()

    # Ignore non-message events (status updates, etc.)
    if body.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}

    parsed = whatsapp.parse_incoming_message(body)
    if not parsed:
        return {"status": "no_message"}

    logger.info(f"Incoming message from {parsed['wa_id']} type={parsed['type']}")

    try:
        await handle_incoming_message(parsed, db)
    except Exception as e:
        logger.error(f"Error handling message from {parsed['wa_id']}: {e}", exc_info=True)

    # Always return 200 to Meta — otherwise it retries
    return {"status": "ok"}


# ── QR Bridge endpoint (used by whatsapp-bridge Node.js) ────────────────────
class BridgeMessage(BaseModel):
    wa_id: str
    name: Optional[str] = ""
    type: str                        # text | audio | image
    text: Optional[str] = None
    media_data: Optional[str] = None  # base64 encoded
    mime_type: Optional[str] = "audio/ogg"
    caption: Optional[str] = ""


@app.post("/bridge/message")
async def bridge_message(msg: BridgeMessage, db: Session = Depends(get_db)):
    parsed = {
        "wa_id": msg.wa_id,
        "name": msg.name or "",
        "type": msg.type,
    }

    if msg.type == "text":
        parsed["text"] = msg.text or ""
    elif msg.type == "audio":
        parsed["media_bytes"] = base64.b64decode(msg.media_data) if msg.media_data else None
        parsed["mime_type"] = msg.mime_type or "audio/ogg"
    elif msg.type == "image":
        parsed["caption"] = msg.caption or ""

    logger.info(f"Bridge message from {msg.wa_id} type={msg.type}")

    try:
        response_text = await handle_bridge_message(parsed, db)
        return {"response": response_text}
    except Exception as e:
        logger.error(f"Bridge error for {msg.wa_id}: {e}", exc_info=True)
        return {"response": "Tuve un problema técnico. Intento de nuevo en un momento."}


# ── Admin endpoints ──────────────────────────────────────────────────────────
@app.post("/admin/reload-kb")
async def reload_knowledge_base():
    knowledge_base.reload_cache()
    knowledge_base.load_fleet_knowledge("argentina")
    knowledge_base.load_fleet_knowledge("miami")
    return {"status": "reloaded"}


@app.get("/health")
async def health():
    return {"status": "ok"}
