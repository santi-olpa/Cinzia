# Cinzia Rental — Plataforma Digital

Repositorio central del ecosistema digital de Cinzia Rental: sitio web institucional + asistente de IA para soporte al viajero por WhatsApp.

---

## Estructura del repositorio

```
/
├── index.html                   Sitio web — home
├── rental.html                  Página de alquiler
├── rental-detail.html           Detalle de vehículo
├── soporte-viajero.html         Soporte en viaje (con asistente Cinzi web)
├── productos.html               Catálogo de motorhomes
├── nosotros.html                Sobre Cinzia
├── contacto.html                Contacto
├── preguntas-frecuentes.html    FAQ
├── cinzia-assets/               Imágenes y recursos del sitio
├── docs/                        PDFs públicos (manuales, contratos)
├── netlify/
│   └── functions/
│       └── cinzi.js             Función serverless — asistente Cinzi (web)
├── netlify.toml                 Configuración de Netlify
├── package.json                 Dependencias web (Anthropic SDK)
├── README-DEPLOY.md             Guía de deploy del sitio web
│
└── whatsapp-ai/                 Asistente de IA para WhatsApp Business
    ├── app/
    │   ├── main.py              FastAPI + webhook WhatsApp
    │   ├── config.py            Variables de entorno
    │   ├── database.py          Base de datos (clientes, conversaciones, escalados)
    │   ├── services/
    │   │   ├── whatsapp.py      Cliente WhatsApp Cloud API
    │   │   ├── claude_service.py Claude API + clasificación de intent
    │   │   ├── transcription.py Whisper (transcripción de audios)
    │   │   └── knowledge_base.py Carga de manuales técnicos
    │   └── handlers/
    │       └── message_handler.py Orquestación principal
    ├── prompts/
    │   └── system_prompt.py     Prompt del asistente
    ├── knowledge_base/
    │   ├── argentina/           Manuales flota AR (Cinzia Sprinter)
    │   └── miami/               Manuales flota Miami (Entegra Odyssey SE)
    ├── .env.example             Variables requeridas
    ├── requirements.txt         Dependencias Python
    ├── Dockerfile               Imagen para deploy
    └── README.md                Guía de setup del backend WhatsApp
```

---

## Componentes

### Sitio web — Netlify

Sitio estático HTML/CSS deployado en Netlify con una función serverless que alimenta al asistente **Cinzi** en la página de soporte.

- Deploy: automático en cada push a `main`
- Guía completa: [README-DEPLOY.md](README-DEPLOY.md)
- Función de IA: `netlify/functions/cinzi.js` (Claude via Anthropic API)

### Asistente WhatsApp — Backend Python

Servicio independiente que recibe mensajes de WhatsApp Business API, los procesa con Claude, y responde 24/7 con:

- Soporte técnico basado en los manuales de cada flota
- Transcripción de audios (Whisper)
- Detección de idioma (ES / EN)
- Clasificación de intent y escalado automático a Jorge y Paulo
- Historial persistente de conversaciones por cliente

- Stack: Python + FastAPI + Claude + OpenAI Whisper
- Deploy: Railway / Fly.io / Docker
- Guía completa: [whatsapp-ai/README.md](whatsapp-ai/README.md)

---

## Flotas

| Flota | Vehículo | Base |
|-------|----------|------|
| Argentina | Mercedes-Benz Sprinter (Cinzia) | Argentina |
| Miami | Entegra Odyssey SE | Miami, USA |

---

## Contacto del proyecto

- Desarrollo: Olpa Group
- Cliente: Cinzia Rental
- Email: rental@cinziavehiculos.com
