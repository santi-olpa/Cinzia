import io
import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> Optional[str]:
    """
    Transcribe audio using Groq Whisper API (free tier).
    Returns the transcribed text or None on failure.
    """
    ext_map = {
        "audio/ogg": "ogg",
        "audio/ogg; codecs=opus": "ogg",
        "audio/mpeg": "mp3",
        "audio/mp4": "mp4",
        "audio/wav": "wav",
        "audio/webm": "webm",
    }
    ext = ext_map.get(mime_type.split(";")[0].strip(), "ogg")
    filename = f"audio.{ext}"

    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GROQ_WHISPER_URL,
                headers=headers,
                files={"file": (filename, io.BytesIO(audio_bytes), mime_type)},
                data={"model": "whisper-large-v3-turbo", "language": "es"},
                timeout=30,
            )
            response.raise_for_status()
            text = response.json().get("text", "").strip()
            logger.info(f"Audio transcribed: {text[:80]}...")
            return text
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq Whisper error: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
