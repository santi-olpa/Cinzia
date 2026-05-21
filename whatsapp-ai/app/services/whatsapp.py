import httpx
import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BASE_URL = "https://graph.facebook.com/v20.0"


async def send_text_message(to: str, text: str) -> bool:
    url = f"{BASE_URL}/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Message sent to {to}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending message to {to}: {e.response.text}")
            return False


async def download_media(media_id: str) -> Optional[bytes]:
    """Download audio/image from WhatsApp media ID."""
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}

    async with httpx.AsyncClient() as client:
        # Step 1: get media URL
        try:
            meta_response = await client.get(
                f"{BASE_URL}/{media_id}", headers=headers, timeout=10
            )
            meta_response.raise_for_status()
            media_url = meta_response.json().get("url")
        except Exception as e:
            logger.error(f"Error getting media URL for {media_id}: {e}")
            return None

        # Step 2: download the actual file
        try:
            file_response = await client.get(media_url, headers=headers, timeout=30)
            file_response.raise_for_status()
            return file_response.content
        except Exception as e:
            logger.error(f"Error downloading media {media_id}: {e}")
            return None


def parse_incoming_message(body: dict) -> Optional[dict]:
    """Extract relevant fields from the Meta webhook payload."""
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]["value"]

        if "messages" not in changes:
            return None

        message = changes["messages"][0]
        contact = changes["contacts"][0]

        result = {
            "wa_id": message["from"],
            "name": contact["profile"].get("name", ""),
            "message_id": message["id"],
            "timestamp": message["timestamp"],
            "type": message["type"],
        }

        if message["type"] == "text":
            result["text"] = message["text"]["body"]

        elif message["type"] == "audio":
            result["media_id"] = message["audio"]["id"]
            result["mime_type"] = message["audio"].get("mime_type", "audio/ogg")

        elif message["type"] == "image":
            result["media_id"] = message["image"]["id"]
            result["caption"] = message["image"].get("caption", "")

        return result

    except (KeyError, IndexError) as e:
        logger.warning(f"Could not parse webhook payload: {e}")
        return None
