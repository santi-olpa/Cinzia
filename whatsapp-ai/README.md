# Cinzia WhatsApp AI — Backend

Asistente de soporte 24/7 para clientes de Cinzia Rental vía WhatsApp Business.

## Setup local

### 1. Clonar e instalar dependencias

```bash
cd cinzia-whatsapp-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Completar los valores en .env
```

### 3. Agregar los manuales a la knowledge base

```
knowledge_base/argentina/manual_cinzia_argentina.txt
knowledge_base/miami/manual_entegra_odyssey.txt
```

### 4. Levantar el servidor

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Exponer localmente con ngrok (para conectar el webhook de Meta)

```bash
ngrok http 8000
# Copiar la URL https://xxxx.ngrok.io y configurarla en Meta como:
# https://xxxx.ngrok.io/webhook
```

## Estructura

```
app/
├── main.py                  # FastAPI + endpoints webhook
├── config.py                # Variables de entorno
├── database.py              # Modelos SQLite/Postgres
├── services/
│   ├── whatsapp.py          # Cliente WhatsApp Cloud API
│   ├── claude_service.py    # Claude + clasificación de intent
│   ├── transcription.py     # Whisper para audios
│   └── knowledge_base.py    # Carga de manuales
└── handlers/
    └── message_handler.py   # Orquestación principal
prompts/
└── system_prompt.py         # Prompt del asistente
knowledge_base/
├── argentina/               # Manuales flota AR
└── miami/                   # Manuales flota Miami
```

## Variables requeridas

| Variable | Dónde conseguirla |
|----------|-------------------|
| `WHATSAPP_TOKEN` | Meta Developers > tu app > WhatsApp > Inicio |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta Developers > tu app > WhatsApp > Inicio |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Meta Developers > tu app > WhatsApp > Inicio |
| `ANTHROPIC_API_KEY` | console.anthropic.com > API Keys |
| `OPENAI_API_KEY` | platform.openai.com > API Keys |
| `ESCALATION_JORGE_NUMBER` | Número WhatsApp de Jorge (ej: 5491155551234) |
| `ESCALATION_PAULO_NUMBER` | Número WhatsApp de Paulo |
