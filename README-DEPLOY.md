# Despliegue de Cinzia Rental + Asistente Cinzi en Netlify

Esta guía te lleva paso a paso desde el repo vacío hasta el sitio funcionando con el asistente Cinzi (IA real con Claude).

---

## 📁 Estructura del proyecto

```
cinzia-website/
├── *.html                       (las páginas del sitio)
├── cinzia-assets/               (imágenes — banners, productos)
├── docs/
│   ├── manual-motorhome.pdf
│   └── contrato-rental.pdf
├── netlify/
│   └── functions/
│       └── cinzi.js             (endpoint serverless de IA)
├── netlify.toml                 (config de Netlify)
├── package.json                 (dependencias: @anthropic-ai/sdk)
├── .gitignore
├── .env.example                 (plantilla — NO subir .env real)
└── README-DEPLOY.md             (este archivo)
```

---

## 🚀 Despliegue desde cero (10 minutos)

### Paso 1 — Subir el código a GitHub (1ª vez)

Abrí Terminal y ubicate en la carpeta del proyecto:

```bash
cd "/Users/santivillalba/Documents/Claude/Projects/Cinzia chat ia/cinzia-website"

# Inicializar git
git init
git branch -M main

# Conectar con el repo de GitHub
git remote add origin https://github.com/santi-olpa/Cinzia.git

# Stage + commit + push
git add .
git commit -m "Initial commit: sitio Cinzia Rental + asistente Cinzi"
git push -u origin main
```

> Si GitHub te pide credenciales, vas a tener que generar un **Personal Access Token**
> (https://github.com/settings/tokens) y usarlo como contraseña.
> O más fácil: instalar **GitHub Desktop** (https://desktop.github.com) y pushear con un click.

### Paso 2 — Conectar el repo a Netlify

1. Ir a https://app.netlify.com/start
2. Click en **"Import an existing project"**
3. Click en **"Deploy with GitHub"** (te pide autorizar Netlify a leer tus repos — solo la primera vez)
4. Buscar y seleccionar `santi-olpa/Cinzia`
5. En la pantalla de configuración, dejá los defaults:
   - **Base directory**: (vacío)
   - **Build command**: (vacío)
   - **Publish directory**: `.`
   - **Functions directory**: `netlify/functions` (lo lee del `netlify.toml`)
6. Click en **"Deploy site"**

Netlify va a:
- Instalar las dependencias del `package.json`
- Compilar la function `cinzi.js`
- Servir los HTML estáticos
- Darte una URL provisoria tipo `https://cuddly-platypus-abc123.netlify.app`

### Paso 3 — Configurar la API key de Anthropic

1. En el dashboard de Netlify, abrí tu nuevo sitio
2. Ir a **Site settings** → **Environment variables**
3. Click en **Add a variable**
4. Crear:
   | Key | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | `sk-ant-api03-tu_key_real_aqui` |
   | `ALLOWED_ORIGIN` | `https://cuddly-platypus-abc123.netlify.app` (la URL de tu sitio — opcional, recomendado en producción) |
5. (Opcional) Cambiar el modelo:
   | Key | Value |
   |---|---|
   | `CINZI_MODEL` | `claude-haiku-4-5-20251001` (default · barato) |

   o usar `claude-sonnet-4-6` si querés más capacidad (5× más caro).

6. **IMPORTANTE**: después de agregar variables, ir a **Deploys** → click en el último deploy → **"Trigger deploy"** → **"Clear cache and deploy site"**. Esto fuerza a rebuildear con las nuevas vars.

### Paso 4 — Probar que Cinzi funciona

1. Abrí la URL del sitio
2. Andá a `/soporte-viajero.html`
3. Click en el botón flotante naranja (Cinzi, esquina inferior derecha)
4. Escribí: _"Mi heladera no enfría, ¿qué hago?"_
5. Cinzi debería responder con instrucciones específicas del manual, en streaming (palabra por palabra)

Si en lugar de eso ves una respuesta genérica del motor local, hay algo mal con la API key. Revisar:
- Que `ANTHROPIC_API_KEY` esté bien copiada (sin espacios al final)
- Que tu cuenta de Anthropic tenga créditos
- Logs de la function en Netlify: **Functions** → `cinzi` → **Function log**

### Paso 5 — Dominio personalizado (opcional)

1. En Netlify: **Domain management** → **Add custom domain**
2. Apuntar `cinziarental.com.ar` (o el dominio que tengan) con un CNAME al subdominio `.netlify.app`
3. Netlify provisiona SSL automáticamente

---

## 🔄 Actualizar el sitio después del deploy inicial

Cada vez que querés hacer un cambio:

```bash
cd "cinzia-website"
# Hacés tus cambios en los archivos
git add .
git commit -m "ajuste: descripción del cambio"
git push
```

Netlify detecta el push y redeploya automáticamente en ~30 segundos. No hay que hacer nada en su dashboard.

---

## 🛠️ Desarrollo local (opcional · para testear antes de subir)

### Pre-requisitos

- **Node.js 18+** instalado (https://nodejs.org)
- **Netlify CLI**:
  ```bash
  npm install -g netlify-cli
  ```

### Setup

```bash
cd "cinzia-website"
npm install                       # instala @anthropic-ai/sdk
cp .env.example .env              # crear tu .env local
# Editar .env y poner tu ANTHROPIC_API_KEY real
```

### Correr local

```bash
netlify dev
```

Abre `http://localhost:8888` con el sitio funcionando + la function disponible en `/api/cinzi`. Recarga en vivo cuando guardás archivos.

---

## 💰 Costos en producción

### Anthropic (Claude Haiku 4.5)
- Input: $0.25 / millón tokens
- Output: $1.25 / millón tokens
- Un chat típico (3 turnos) ≈ 3.000 tokens input + 600 tokens output ≈ **$0.001 USD por conversación**

| Tráfico mensual | Costo Anthropic |
|---|---|
| 100 conversaciones | ~$0.10 |
| 1.000 conversaciones | ~$1 |
| 10.000 conversaciones | ~$10 |

### Netlify
- Free tier: 125.000 invocaciones de functions/mes + 100 GB de bandwidth
- Free hasta volúmenes muy altos. Plan Pro ($19/mes) solo si superan ese tráfico.

---

## 🆘 Troubleshooting

### "El asistente no está disponible temporalmente"
- Falta `ANTHROPIC_API_KEY` en env vars. Agregala y trigger redeploy.

### "Credencial de Anthropic inválida"
- La key está mal copiada o fue revocada. Crear una nueva en https://console.anthropic.com/settings/keys.

### "Demasiados pedidos al asistente"
- Rate limit de Anthropic (raro). Esperar unos segundos o subir al plan pro de Anthropic.

### El streaming no funciona, pero el bot responde de una sola vez
- Algún proxy o el plan de Netlify free no soporta SSE. Soluciones:
  - En `soporte-viajero.html`, buscar `stream: true` en la línea del fetch y cambiar a `stream: false`
  - El bot va a responder todo de una sola vez, sin el efecto "escribiendo en vivo". Sigue funcionando perfectamente.

### Cinzi responde con info incorrecta
- El system prompt vive en `netlify/functions/cinzi.js`. Editalo, commit + push, y Netlify redeploya.

---

## 🔐 Seguridad

- **Nunca** commitear `.env` al repo (ya está en `.gitignore`).
- **Nunca** poner la API key en el JavaScript del frontend (ya lo evitamos: vive solo en env vars de Netlify).
- Configurar `ALLOWED_ORIGIN` con tu dominio real en producción para que nadie use tu endpoint desde otros sitios.
- Rotar la API key cada 6 meses por buena práctica.

---

## 📞 Contactos del proyecto

- Línea Cinzia: +54 9 3515 29-3858
- MB Assistance: 0800 666 2369
- Email rental: rental@cinziavehiculos.com
