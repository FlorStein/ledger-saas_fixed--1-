/**
 * Vercel Serverless Function - WhatsApp Cloud API Webhook
 * GET:  Webhook verification from Meta
 * POST: Webhook events from Meta
 */

export default async function handler(req, res) {
  const { method, query, body } = req;

  // ============================================
  // GET: Webhook Verification
  // ============================================
  if (method === "GET") {
    const hubMode = query["hub.mode"];
    const hubVerifyToken = query["hub.verify_token"];
    const hubChallenge = query["hub.challenge"];

    const expectedToken = process.env.WHATSAPP_VERIFY_TOKEN;

    console.log(
      `[GET] Verification - mode: ${hubMode}, token_match: ${
        hubVerifyToken === expectedToken
      }`
    );

    if (
      hubMode === "subscribe" &&
      hubVerifyToken === expectedToken &&
      hubChallenge
    ) {
      console.log(`[GET] ✅ Verification successful`);
      return res.status(200).send(hubChallenge);
    } else {
      console.warn(`[GET] ❌ Verification failed - invalid token or params`);
      return res.status(403).json({ error: "Verification failed" });
    }
  }

  // ============================================
  // POST: Webhook Events
  // ============================================
  if (method === "POST") {
    try {
      console.log(`[POST] Received webhook event:`);
      console.log(JSON.stringify(body, null, 2));

      // Respond immediately with 200
      return res.status(200).json({ ok: true });
    } catch (error) {
      console.error(`[POST] Error processing webhook:`, error.message);
      return res.status(500).json({ error: "Internal server error" });
    }
  }

  // Method not allowed
  return res.status(405).json({ error: "Method not allowed" });
}
