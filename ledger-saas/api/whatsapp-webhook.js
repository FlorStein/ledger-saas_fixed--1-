/**
 * Vercel Serverless Function - WhatsApp Webhook (Meta Cloud API)
 * - GET: verifica hub.challenge
 * - POST: opcionalmente valida firma HMAC, resuelve tenant y reenvía al backend
 */

const crypto = require("crypto");

function generateRequestId() {
  return `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function getTenantIdFromPhoneNumberId(phoneNumberId) {
  try {
    const routing = JSON.parse(process.env.TENANT_ROUTING_JSON || "{}") || {};
    return routing[phoneNumberId] || "default";
  } catch (e) {
    console.warn("⚠️ TENANT_ROUTING_JSON inválido, usando 'default'", e);
    return "default";
  }
}

async function readRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function validateSignature(rawBody, signature, appSecret) {
  if (!signature || !appSecret) return true; // si no hay firma, no bloqueamos
  if (typeof signature !== "string") return false;
  const parts = signature.split("=");
  if (parts.length !== 2) return false;
  const [algo, hashHex] = parts;
  if (algo !== "sha256") return false;
  const expected = crypto.createHmac("sha256", appSecret).update(rawBody).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(hashHex, "hex"), Buffer.from(expected, "hex"));
  } catch {
    return false;
  }
}

module.exports = async function handler(req, res) {
  const requestId = generateRequestId();
  console.log(`[${requestId}] 🔔 WEBHOOK ${req.method}`);
  
  const { method } = req;

  // ============================================
  // GET - Verificación del Webhook
  // ============================================
  if (method === "GET") {
    const mode = req.query["hub.mode"];
    const token = req.query["hub.verify_token"];
    const challenge = req.query["hub.challenge"];

    // Verificar que los parámetros existan
    if (!mode || !token || !challenge) {
      console.log("❌ GET: Parámetros faltantes");
      return res.status(400).send("Missing parameters");
    }

    // Verificar el token
    const verifyToken = process.env.WHATSAPP_VERIFY_TOKEN;
    
    if (mode === "subscribe" && token === verifyToken) {
      console.log("✅ GET: Webhook verificado correctamente");
      return res.status(200).send(challenge);
    } else {
      console.log("❌ GET: Token de verificación incorrecto");
      return res.status(403).send("Verification token mismatch");
    }
  }

  // ============================================
  // POST - Recepción de Eventos
  // ============================================
  if (method === "POST") {
    console.log("📨 POST RECIBIDO!");
    let rawBody;
    try {
      rawBody = await readRawBody(req);
    } catch (e) {
      console.error("❌ No se pudo leer raw body", e);
      return res.status(400).send("Bad Request");
    }

    const signature = req.headers["x-hub-signature-256"];
    const appSecret = process.env.META_APP_SECRET;
    if (appSecret && signature) {
      const ok = validateSignature(rawBody, signature, appSecret);
      if (!ok) {
        console.warn("❌ Firma inválida");
        return res.status(401).send("Invalid signature");
      }
    }

    let body = {};
    try {
      body = JSON.parse(rawBody.toString("utf8") || "{}");
    } catch (err) {
      console.error("❌ JSON inválido", err);
      return res.status(200).json({ ok: true });
    }

    try {
      let phoneNumberId = null;
      let senderWaId = null;
      const extractedMessages = [];

      if (body.entry && body.entry.length > 0) {
        const entry = body.entry[0];
        if (entry.changes && entry.changes.length > 0) {
          const change = entry.changes[0];
          phoneNumberId = change?.value?.metadata?.phone_number_id || change?.value?.metadata?.display_phone_number || entry.id || null;
          if (change.value && change.value.messages && change.value.messages.length > 0) {
            senderWaId = change.value.messages[0].from;
            change.value.messages.forEach((msg) => {
              extractedMessages.push({
                from: msg.from,
                type: msg.type,
                text: msg.text?.body || msg.type,
                timestamp: msg.timestamp,
                id: msg.id,
              });
            });
          }
        }
      }

      const tenantId = getTenantIdFromPhoneNumberId(phoneNumberId);
      console.log(`[${requestId}] 📱 phone_number_id=${phoneNumberId}, sender=${senderWaId}, tenant=${tenantId}, messages=${extractedMessages.length}`);

      const backendUrl = process.env.BACKEND_INGEST_URL;
      const sharedSecret = process.env.BACKEND_SHARED_SECRET;

      if (!backendUrl) {
        console.error(`[${requestId}] ❌ BACKEND_INGEST_URL not configured`);
        return res.status(500).json({ ok: false, error: "BACKEND_INGEST_URL not configured", request_id: requestId });
      }
      if (!sharedSecret) {
        console.error(`[${requestId}] ❌ BACKEND_SHARED_SECRET not configured`);
        return res.status(500).json({ ok: false, error: "BACKEND_SHARED_SECRET not configured", request_id: requestId });
      }

      try {
        const forwardPayload = {
          tenant_id: tenantId,
          phone_number_id: phoneNumberId,
          payload: body,
          timestamp: new Date().toISOString(),
          request_id: requestId,
        };

        const resp = await fetch(backendUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sharedSecret}`,
            "X-Tenant-ID": tenantId,
            "X-Phone-Number-ID": phoneNumberId || "",
            "X-Request-ID": requestId,
          },
          body: JSON.stringify(forwardPayload),
        });

        const txt = await resp.text();
        console.log(`[${requestId}] ➡️ backend status=${resp.status}, body=${txt.slice(0, 200)}`);
        if (!resp.ok) console.error(`[${requestId}] ⚠️ backend error: ${txt}`);

        return res.status(200).json({ ok: true, received: true, tenant: tenantId, phone_number_id: phoneNumberId, request_id: requestId });
      } catch (err) {
        console.error(`[${requestId}] ❌ Error forwarding:`, err.message);
        return res.status(500).json({ ok: false, error: "Forward failed", request_id: requestId });
      }

    } catch (error) {
      console.error(`[${requestId}] ❌ POST Error:`, error);
      return res.status(200).json({ ok: true, request_id: requestId });
    }
  }

  // Método no permitido
  console.log("❌ Método no soportado:", method);
  return res.status(405).send("Method Not Allowed");
};

// Configuración para Vercel
module.exports.config = {
  api: {
    bodyParser: false
  }
};
