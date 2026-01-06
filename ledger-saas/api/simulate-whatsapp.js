/**
 * Simulation endpoint to push WhatsApp-like events into the backend pipeline without HMAC.
 * Usage (POST): payload should mimic Meta Cloud body; optional tenant_id and phone_number_id.
 */

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
  if (req.method !== "POST") {
    return res.status(405).send("Method Not Allowed");
  }

  const body = req.body || {};
  const phoneNumberId = body.phone_number_id || body?.entry?.[0]?.changes?.[0]?.value?.metadata?.phone_number_id || null;
  const tenantId = body.tenant_id || getTenantIdFromPhoneNumberId(phoneNumberId);

  const backendUrl = process.env.BACKEND_INGEST_URL;
  const sharedSecret = process.env.BACKEND_SHARED_SECRET;

  if (!backendUrl || !sharedSecret) {
    console.warn("⚠️ BACKEND_INGEST_URL o BACKEND_SHARED_SECRET no configurados, no se reenvía");
    return res.status(500).json({ ok: false, error: "Backend not configured" });
  }

  try {
    const forwardPayload = {
      tenant_id: tenantId,
      phone_number_id: phoneNumberId,
      payload: body.payload || body,
      timestamp: new Date().toISOString(),
    };

    const resp = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sharedSecret}`,
        "X-Tenant-ID": tenantId,
        "X-Phone-Number-ID": phoneNumberId || "",
      },
      body: JSON.stringify(forwardPayload),
    });

    const txt = await resp.text();
    console.log(`➡️ Forwarded simulated event (${resp.status}):`, txt.slice(0, 300));
    return res.status(200).json({ ok: true, forwarded: true, tenant: tenantId, phone_number_id: phoneNumberId });
  } catch (error) {
    console.error("❌ Error reenviando evento simulado:", error);
    return res.status(500).json({ ok: false, error: "Forward failed" });
  }
};
