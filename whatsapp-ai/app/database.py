from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Fleet(str, enum.Enum):
    ARGENTINA = "argentina"
    MIAMI = "miami"
    UNKNOWN = "unknown"


class CustomerStage(str, enum.Enum):
    PROSPECT = "prospecto"
    UPCOMING = "proximo"
    ON_TRIP = "en_viaje"
    POST_TRIP = "post_viaje"
    UNKNOWN = "unknown"


class Intent(str, enum.Enum):
    INFO = "consulta_informativa"
    TROUBLESHOOTING = "troubleshooting"
    EMERGENCY = "emergencia"
    REGISTER = "dejar_registro"
    RETURN = "devolucion"
    SALES = "ventas"
    CLAIM = "reclamo"
    UNKNOWN = "unknown"


class EscalationLevel(str, enum.Enum):
    NONE = "none"
    JORGE = "jorge"
    PAULO = "paulo"


class Customer(Base):
    __tablename__ = "customers"

    wa_id = Column(String, primary_key=True)  # WhatsApp phone number
    name = Column(String, nullable=True)
    fleet = Column(String, default=Fleet.UNKNOWN)
    stage = Column(String, default=CustomerStage.UNKNOWN)
    vehicle = Column(String, nullable=True)
    reservation_end_date = Column(String, nullable=True)
    language = Column(String, default="es")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wa_id = Column(String, index=True)
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    message_type = Column(String, default="text")  # text, audio, image
    created_at = Column(DateTime, default=datetime.utcnow)


class EscalationCase(Base):
    __tablename__ = "escalation_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wa_id = Column(String, index=True)
    customer_name = Column(String, nullable=True)
    vehicle = Column(String, nullable=True)
    problem_summary = Column(Text)
    attempts = Column(Integer, default=0)
    level = Column(String)  # jorge or paulo
    notified = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
