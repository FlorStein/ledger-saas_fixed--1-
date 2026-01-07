/**
 * Simulation endpoint: POST with Meta-like payload -> forward to backend.
 * Accepts payloads with entry structure; validates before accepting.
 */

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

module.exports = async function handler(req, res) {
  const requestId = generateRequestId();
  
  if (req.method !== "POST") {
    return res.status(405).send("Method Not Allowed");
  }

  const body = req.body || {};
  console.log(`[${requestId}] 🎭 Simulate POST`);

  // Validar estructura: entry[0].changes[0].value requerido
  let phoneNumberId = null;
  let senderWaId = null;
  let msgCount = 0;

  if (!body.entry || !Array.isArray(body.entry) || !body.entry[0]) {
    console.error(`[${requestId}] ❌ Missing entry[0]`);
    return res.status(400).json({ ok: false, error: "Missing entry[0]", request_id: requestId });
  }

  const entry = body.entry[0];
  if (!entry.changes || !Array.isArray(entry.changes) || !entry.changes[0]) {
    console.error(`[${requestId}] ❌ Missing entry[0].changes[0]`);
    return res.status(400).json({ ok: false, error: "Missing entry[0].changes[0]", request_id: requestId });
  }

  const value = entry.changes[0].value;
  if (!value) {
    console.error(`[${requestId}] ❌ Missing entry[0].changes[0].value`);
    return res.status(400).json({ ok: false, error: "Missing entry[0].changes[0].value", request_id: requestId });
  }

  // Extraer phone_number_id y sender
  phoneNumberId = value.metadata?.phone_number_id || value.metadata?.display_phone_number || entry.id || null;
  if (value.messages && value.messages.length > 0) {
    senderWaId = value.messages[0].from;
    msgCount = value.messages.length;
  }

  const tenantId = getTenantIdFromPhoneNumberId(phoneNumberId);
  console.log(`[${requestId}] 📱 phone_number_id=${phoneNumberId}, sender=${senderWaId}, tenant=${tenantId}, messages=${msgCount}`);

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
    // Forward EXACTLY como whatsapp-webhook.js
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

    return res.status(200).json({ ok: true, forwarded: true, tenant: tenantId, phone_number_id: phoneNumberId, request_id: requestId });
  } catch (error) {
    console.error(`[${requestId}] ❌ Error forwarding:`, error.message);
    return res.status(500).json({ ok: false, error: "Forward failed", request_id: requestId });
  }
};
