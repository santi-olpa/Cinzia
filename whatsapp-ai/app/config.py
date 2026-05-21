from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # WhatsApp Cloud API
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_verify_token: str = "cinzia_webhook_verify"

    # Anthropic
    anthropic_api_key: str = ""

    # Groq (Whisper transcription — free tier)
    groq_api_key: str = ""

    # Escalation numbers (WhatsApp international format, e.g. 5491155551234)
    escalation_jorge_number: str = ""
    escalation_paulo_number: str = ""

    # App
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./cinzia.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
