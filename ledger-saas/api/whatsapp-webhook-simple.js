/**
 * Vercel Serverless Function - WhatsApp Webhook Simple
 * GET:  Verificación de webhook
 * POST: Recepción de eventos
 */

module.exports = async function handler(req, res) {
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
    try {
      const body = req.body;
      
      // Loguear todo el body recibido
      console.log("📨 POST: Webhook recibido");
      console.log(JSON.stringify(body, null, 2));

      // Extraer información útil si existe
      if (body.entry && body.entry.length > 0) {
        const entry = body.entry[0];
        if (entry.changes && entry.changes.length > 0) {
          const change = entry.changes[0];
          console.log("📋 Tipo de cambio:", change.field);
          
          if (change.value && change.value.messages) {
            const messages = change.value.messages;
            console.log(`📩 ${messages.length} mensaje(s) recibido(s)`);
            messages.forEach((msg, index) => {
              console.log(`  Mensaje ${index + 1}:`, {
                from: msg.from,
                type: msg.type,
                text: msg.text?.body || msg.type,
                timestamp: msg.timestamp
              });
            });
          }
        }
      }

      // Responder siempre 200 OK
      return res.status(200).json({ ok: true });

    } catch (error) {
      console.error("❌ POST: Error procesando webhook:", error);
      // Aún así responder 200 para que Meta no reintente
      return res.status(200).json({ ok: true });
    }
  }

  // ============================================
  // Método no permitido
  // ============================================
  console.log(`❌ Método ${method} no permitido`);
  return res.status(405).send("Method Not Allowed");
};
