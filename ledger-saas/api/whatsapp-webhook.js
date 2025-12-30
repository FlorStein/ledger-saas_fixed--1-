/**
 * Vercel Serverless Function para WhatsApp Cloud API
 * GET:  Verificación de webhook
 * POST: Recepción de eventos con validación de firma
 */

const crypto = require("crypto");

/**
 * Leer el raw body como Buffer (necesario para validar firma HMAC)
 */
async function readRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

/**
 * Validar firma HMAC SHA256
 */
function validateSignature(rawBody, signature, appSecret) {
  if (!signature || typeof signature !== "string") return false;

  const parts = signature.split("=");
  if (parts.length !== 2) return false;

  const [algorithm, hashHex] = parts;
  if (algorithm !== "sha256") return false;

  // must be 64 hex chars for sha256
  if (!/^[a-f0-9]{64}$/i.test(hashHex)) return false;

  const expectedHex = crypto
    .createHmac("sha256", appSecret)
    .update(rawBody)
    .digest("hex");

  const hashBuf = Buffer.from(hashHex, "hex");
  const expectedBuf = Buffer.from(expectedHex, "hex");

  if (hashBuf.length !== expectedBuf.length) return false;

  return crypto.timingSafeEqual(hashBuf, expectedBuf);
}

async function getFetch() {
  if (typeof globalThis.fetch === "function") return globalThis.fetch;
  const { fetch } = await import("undici");
  globalThis.fetch = fetch;
  return fetch;
}

/**
 * Parsear TENANT_ROUTING_JSON y obtener tenant_id
 */
function getTenantIdFromPhoneNumberId(phoneNumberId, routingJson) {
  try {
    const routing = JSON.parse(routingJson);
    return routing[phoneNumberId] || "default";
  } catch (e) {
    console.error("Error parsing TENANT_ROUTING_JSON:", e);
    return "default";
  }
}

/**
 * Forward al backend (sin bloquear el respuesta)
 */
async function forwardToBackend(
  payload,
  tenantId,
  phoneNumberId,
  requestId,
  senderWaId
) {
  const backendUrl = process.env.BACKEND_INGEST_URL;
  const sharedSecret = process.env.BACKEND_SHARED_SECRET;

  if (!backendUrl) {
    console.warn("BACKEND_INGEST_URL no configurada, omitiendo forward");
    return;
  }

  try {
    const fetchFn = await getFetch();
    const response = await fetchFn(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sharedSecret}`,
        "X-Tenant-ID": tenantId,
        "X-Phone-Number-ID": phoneNumberId,
        "X-Request-ID": requestId,
        ...(senderWaId ? { "X-Sender-WA-ID": senderWaId } : {}),
      },
      body: JSON.stringify({
        tenant_id: tenantId,
        phone_number_id: phoneNumberId,
        sender_wa_id: senderWaId,
        payload: payload,
        timestamp: new Date().toISOString(),
        request_id: requestId,
      }),
    });

    if (!response.ok) {
      console.error(
        `Backend returned status ${response.status}: ${await response.text()}`
      );
    }
  } catch (error) {
    console.error("Error forwarding to backend:", error.message);
    // No relanzo el error, el webhook ya respondió 200 a Meta
  }
}

/**
 * Handler principal
 */
export default async function handler(req, res) {
  const method = req.method;
  const requestId =
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  // ============================================
  // GET: Verificación de webhook
  // ============================================
  if (method === "GET") {
    const hubMode = req.query["hub.mode"];
    const hubVerifyToken = req.query["hub.verify_token"];
    const hubChallenge = req.query["hub.challenge"];

    const expectedToken = process.env.WHATSAPP_VERIFY_TOKEN;

    console.log(
      `[GET][${requestId}] Verification request - mode: ${hubMode}, token match: ${
        hubVerifyToken === expectedToken
      }`
    );

    if (hubMode === "subscribe" && hubVerifyToken === expectedToken) {
      console.log(`[GET][${requestId}] ✅ Verification successful`);
      return res.status(200).send(hubChallenge);
    } else {
      console.warn(`[GET][${requestId}] ❌ Verification failed - invalid token`);
      return res.status(403).json({ error: "Verification failed" });
    }
  }

  // ============================================
  // POST: Recepción de eventos
  // ============================================
  if (method === "POST") {
    try {
      // 1. Leer raw body para validar firma
      const rawBody = await readRawBody(req);

      // 2. Validar firma HMAC
      const signature =
        req.headers["x-hub-signature-256"] ||
        req.headers["X-Hub-Signature-256"];
      const appSecret = process.env.META_APP_SECRET;

      if (!signature || !appSecret) {
        console.error(`[POST][${requestId}] ❌ Missing signature or app secret`);
        return res.status(401).json({ error: "Unauthorized" });
      }

      let isValidSignature = false;
      try {
        isValidSignature = validateSignature(rawBody, signature, appSecret);
      } catch (e) {
        console.error(
          `[POST][${requestId}] ❌ Signature validation error: ${e.message}`
        );
        return res.status(401).json({ error: "Signature validation failed" });
      }

      if (!isValidSignature) {
        console.warn(`[POST][${requestId}] ❌ Invalid signature`);
        return res.status(401).json({ error: "Invalid signature" });
      }

      console.log(`[POST][${requestId}] ✅ Signature validated`);

      // 3. Parsear payload
      let payload;
      try {
        payload = JSON.parse(rawBody.toString("utf-8"));
      } catch (e) {
        console.error(`[POST][${requestId}] ❌ Invalid JSON: ${e.message}`);
        return res.status(400).json({ error: "Invalid JSON" });
      }

      // 4. Extraer datos relevantes
      const entry = payload.entry?.[0];
      const change = entry?.changes?.[0];
      const value = change?.value;

      const phoneNumberId = value?.metadata?.phone_number_id;
      const messages = value?.messages || [];
      const statuses = value?.statuses || [];
      const senderWaId = messages?.[0]?.from;

      console.log(
        `[POST][${requestId}] Received event - phone_number_id: ${phoneNumberId}, messages: ${messages.length}, statuses: ${statuses.length}`
      );

      // 5. Determinar tenant
      const tenantRoutingJson = process.env.TENANT_ROUTING_JSON || "{}";
      const tenantId = getTenantIdFromPhoneNumberId(
        phoneNumberId,
        tenantRoutingJson
      );

      console.log(
        `[POST][${requestId}] Routing to tenant: ${tenantId} (phone_number_id: ${phoneNumberId})`
      );

      // 6. **RESPONDER RÁPIDO a Meta (SIN esperar el backend)**
      res.status(200).json({ ok: true });

      // 7. **FORWARD al backend de forma asincrónica (no bloquea la respuesta)**
      // Iniciar el fetch sin await
      forwardToBackend(
        payload,
        tenantId,
        phoneNumberId,
        requestId,
        senderWaId
      ).catch((e) => {
        console.error(
          `[POST][${requestId}] Unexpected error in forwardToBackend:`,
          e
        );
      });
      return;

      // Log de éxito
      console.log(
        `[POST][${requestId}] ✅ Event processed and forwarded to backend (tenant: ${tenantId}, phone_number_id: ${phoneNumberId})`
      );
    } catch (error) {
      console.error(`[POST][${requestId}] ❌ Unexpected error: ${error.message}`);
      return res.status(500).json({ error: "Internal server error" });
    }
  }

  // Método no soportado
  return res.status(405).json({ error: "Method not allowed" });
}
