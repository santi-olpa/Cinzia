require("dotenv").config();
const { Client, LocalAuth, MessageMedia } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const axios = require("axios");

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// ── WhatsApp client with persistent session ──────────────────────────────────
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: "./.wwebjs_auth" }),
  puppeteer: {
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  },
});

// ── QR code — scan this with WhatsApp on your test phone ────────────────────
client.on("qr", (qr) => {
  console.log("\n📱 Escaneá este QR con WhatsApp en tu teléfono de prueba:\n");
  qrcode.generate(qr, { small: true });
});

client.on("authenticated", () => {
  console.log("✅ Sesión autenticada — guardada localmente");
});

client.on("ready", () => {
  console.log("🟢 Bridge listo. Esperando mensajes...\n");
});

client.on("disconnected", (reason) => {
  console.log("🔴 Desconectado:", reason);
  process.exit(1);
});

// ── Incoming message handler ─────────────────────────────────────────────────
client.on("message", async (msg) => {
  // Ignore group messages and status updates
  if (msg.isGroupMsg || msg.from === "status@broadcast") return;

  const wa_id = msg.from.replace("@c.us", "");
  const contact = await msg.getContact();
  const name = contact.pushname || contact.name || "";

  console.log(`📨 [${wa_id}] ${name}: type=${msg.type}`);

  try {
    let payload = { wa_id, name, type: msg.type };

    if (msg.type === "chat") {
      payload.type = "text";
      payload.text = msg.body;

    } else if (msg.type === "audio" || msg.type === "ptt") {
      // ptt = push-to-talk (voice note)
      payload.type = "audio";
      const media = await msg.downloadMedia();
      if (!media) {
        await msg.reply("No pude procesar tu audio. ¿Podés escribirme?");
        return;
      }
      payload.media_data = media.data;       // base64
      payload.mime_type = media.mimetype;

    } else if (msg.type === "image") {
      payload.type = "image";
      payload.caption = msg.caption || "";
      // Optionally download image for future vision support
    } else {
      // Unsupported type — ignore silently
      return;
    }

    // ── Call Python backend ─────────────────────────────────────────────────
    const response = await axios.post(`${BACKEND_URL}/bridge/message`, payload, {
      timeout: 30000,
    });

    const replyText = response.data?.response;
    if (replyText) {
      await client.sendMessage(msg.from, replyText);
      console.log(`📤 [${wa_id}] Respuesta enviada`);
    }

  } catch (err) {
    console.error(`❌ Error procesando mensaje de ${wa_id}:`, err.message);
    await msg.reply(
      "Tuve un problema técnico. Intento de nuevo en un momento."
    );
  }
});

// ── Start ────────────────────────────────────────────────────────────────────
console.log("🚀 Iniciando Cinzia WhatsApp Bridge...");
client.initialize();
