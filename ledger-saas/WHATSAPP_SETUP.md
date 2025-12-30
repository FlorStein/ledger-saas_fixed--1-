# 🔗 Integración WhatsApp Cloud API + Vercel

## Descripción General

Esta integración conecta **Meta Cloud API (WhatsApp)** con **Vercel Serverless Functions** para recibir webhooks de mensajes y eventos, procesarlos con validación de firma, y reenviarlos al backend de Ledger SaaS para su procesamiento (OCR, matching, etc.).

**Flujo:**
```
WhatsApp Cloud API
    ↓ (Webhook POST)
Vercel Function (/api/whatsapp-webhook.js)
    ↓ (Valida firma + responde 200)
Backend FastAPI (/webhooks/whatsapp/meta/cloud)
    ↓ (Procesa evento)
Database + Ingest
```

---

## 📋 Prerequisitos

1. **Cuenta de Meta Business** con acceso a Cloud API
2. **Vercel** con proyecto conectado a GitHub
3. **Backend FastAPI** corriendo (puede ser local o remoto)
4. **Node.js 20+** para Vercel Functions

---

## 🛠️ Setup Paso a Paso

### Paso 1: Variables de Entorno en Vercel

En **Project Settings → Environment Variables**, agregar:

| Variable | Valor | Descripción |
|----------|-------|-----------|
| `WHATSAPP_VERIFY_TOKEN` | `ledger_saas_verify_123` (cualquier string) | Token para verificar webhook |
| `META_APP_SECRET` | `abc123...` (de Meta App) | App Secret de tu aplicación Meta |
| `BACKEND_INGEST_URL` | `https://backend.example.com/webhooks/whatsapp/meta/cloud` | Endpoint del backend |
| `BACKEND_SHARED_SECRET` | `ledger_saas_backend_secret` | Bearer token para autenticar al backend |
| `TENANT_ROUTING_JSON` | `{"1234567890":"tenant_demo"}` | Mapeo phone_number_id → tenant_id |

**Nota:** Estas variables están en `vercel.json` con referencias a secrets. Para agregar:
```bash
vercel env add WHATSAPP_VERIFY_TOKEN
vercel env add META_APP_SECRET
# ... etc
```

Luego en Vercel Dashboard:
1. Settings → Environment Variables
2. Add new
3. Copiar el valor
4. Seleccionar Production/Preview/Development

### Paso 2: Obtener META_APP_SECRET

1. Ir a https://developers.facebook.com
2. Tu aplicación → Settings → Basic
3. Copiar **App Secret**
4. Guardar en Vercel como `META_APP_SECRET`

### Paso 3: Configurar Backend

**Backend `.env`:**
```dotenv
BACKEND_SHARED_SECRET=ledger_saas_backend_secret
TENANT_ROUTING_JSON={"1234567890":"tenant_demo"}
```

**Backend debe tener:**
```bash
pip install requests  # Si no está ya
```

### Paso 4: Configurar Webhook en Meta

1. Ir a https://developers.facebook.com
2. Tu app → Whatsapp → Configuration
3. **Callback URL:** `https://tu-vercel-app.vercel.app/api/whatsapp-webhook`
4. **Verify Token:** `ledger_saas_verify_123` (mismo que en env)
5. Click "Verify and Save"

Meta hará un GET a tu endpoint:
```
GET /api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=CHALLENGE_VALUE
```

Tu Vercel Function debe responder con el challenge.

### Paso 5: Subscribe to Webhook Fields

En Meta Developer Dashboard:
1. Whatsapp → Webhooks
2. Subscribe to: `messages`, `message_status`, `message_template_status_update`

---

## 🔐 Seguridad

### Validación de Firma (HMAC SHA256)

**Meta envía header:** `x-hub-signature-256: sha256=<hex>`

**Vercel valida:**
1. Leer raw body (buffer)
2. Calcular HMAC SHA256 usando `META_APP_SECRET`
3. Comparar con timing-safe compare
4. Si no coincide: rechazar con 401

**Code:**
```javascript
const signature = req.headers["x-hub-signature-256"];
const [algorithm, hash] = signature.split("=");
const expectedHash = crypto
  .createHmac("sha256", appSecret)
  .update(rawBody)
  .digest("hex");
const isValid = crypto.timingSafeEqual(
  Buffer.from(hash),
  Buffer.from(expectedHash)
);
```

### Bearer Token para Backend

**Vercel envía header:** `Authorization: Bearer ${BACKEND_SHARED_SECRET}`

**Backend valida:**
```python
auth_header = request.headers.get("Authorization", "")
token = auth_header.replace("Bearer ", "")
if token != BACKEND_SHARED_SECRET:
    raise HTTPException(status_code=401)
```

---

## 📨 Flujo de Eventos

### GET Verification (Setup)

```http
GET /api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=CHALLENGE_VALUE
```

**Response:**
```
200 OK
CHALLENGE_VALUE
```

### POST Message Event

```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "metadata": {
              "phone_number_id": "1234567890"
            },
            "messages": [
              {
                "id": "wamid.123",
                "type": "document",
                "document": {
                  "id": "doc_id_123",
                  "filename": "comprobante.pdf",
                  "mime_type": "application/pdf"
                },
                "from": "5491123456789",
                "timestamp": "1234567890"
              }
            ],
            "contacts": [
              {
                "profile": {
                  "name": "Juan Pérez"
                },
                "wa_id": "5491123456789"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Vercel responde:**
```json
200 OK
{
  "ok": true
}
```

**Vercel luego hace (async):**
```http
POST https://backend.example.com/webhooks/whatsapp/meta/cloud
Authorization: Bearer ledger_saas_backend_secret
X-Tenant-ID: tenant_demo
X-Phone-Number-ID: 1234567890
Content-Type: application/json

{
  "tenant_id": "tenant_demo",
  "phone_number_id": "1234567890",
  "payload": { ... },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Backend procesa:**
1. Valida Bearer token
2. Extrae contactos y crea/actualiza Counterparty
3. Procesa mensajes (documento/imagen → OCR)
4. Retorna status

---

## 🧪 Testing

### Test 1: Verificación de Webhook

```bash
curl -X GET "http://localhost:3000/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=test_challenge"
```

**Esperado:**
```
200 OK
test_challenge
```

### Test 2: POST con Firma Válida

**Script de prueba:**

```bash
#!/bin/bash

APP_SECRET="tu_app_secret_aqui"
VERIFY_TOKEN="ledger_saas_verify_123"
ENDPOINT="http://localhost:3000/api/whatsapp-webhook"

PAYLOAD='{"entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"1234567890"},"messages":[{"id":"msg123","type":"text","text":{"body":"Hola"},"from":"5491123456789"}]}}]}]}'

# Calcular firma
SIGNATURE="sha256=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$APP_SECRET" -hex | sed 's/^.* //')"

echo "Payload: $PAYLOAD"
echo "Signature: $SIGNATURE"

curl -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "x-hub-signature-256: $SIGNATURE" \
  -d "$PAYLOAD"
```

**Esperado:**
```json
200 OK
{
  "ok": true
}
```

### Test 3: POST con Firma Inválida

```bash
curl -X POST "http://localhost:3000/api/whatsapp-webhook" \
  -H "Content-Type: application/json" \
  -H "x-hub-signature-256: sha256=invalid_signature_here" \
  -d '{"entry":[...]}'
```

**Esperado:**
```
401 Unauthorized
{"error": "Invalid signature"}
```

---

## 🏗️ Estructura de Archivos

```
ledger-saas/
├── api/
│   └── whatsapp-webhook.js          ← Vercel Function (Node.js)
├── vercel.json                        ← Configuración Vercel
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── whatsapp.py           ← Endpoint FastAPI
│   │   └── .env                       ← Variables backend
│   └── requirements.txt
└── frontend/
    └── ...
```

---

## 🔄 Multi-Tenant Routing

**TENANT_ROUTING_JSON** mapea `phone_number_id` a `tenant_id`:

```json
{
  "1234567890": "tenant_demo",
  "9876543210": "tenant_ariel",
  "5555555555": "tenant_otro"
}
```

**Flujo:**
1. Vercel recibe evento con `phone_number_id: 1234567890`
2. Parsea `TENANT_ROUTING_JSON`
3. Obtiene `tenant_id = tenant_demo`
4. Envía al backend con `X-Tenant-ID: tenant_demo`
5. Backend procesa dentro del tenant

Si `phone_number_id` no está en el mapping → se usa `tenant_id: "default"`

---

## 📝 Endpoint FastAPI

**POST `/webhooks/whatsapp/meta/cloud`**

```python
@router.post("/meta/cloud")
async def receive_meta_cloud_events(
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(verify_webhook_auth),
):
    """
    Recibir eventos de Meta Cloud API reenviados por Vercel.
    """
```

**Request:**
```json
{
  "tenant_id": "tenant_demo",
  "phone_number_id": "1234567890",
  "payload": { ... },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response:**
```json
200 OK
{
  "status": "received",
  "tenant_id": "tenant_demo",
  "phone_number_id": "1234567890",
  "messages_processed": 1,
  "statuses_processed": 0,
  "contacts_processed": 1
}
```

**Validación:**
- ✅ Bearer token en `Authorization`
- ✅ Crea/actualiza `Counterparty` si es necesario
- ✅ Procesa mensajes (text, document, image, location)
- ✅ Maneja cambios de estado

---

## 🚀 Despliegue

### Vercel

```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel

# Deploy a producción
vercel --prod
```

### Cambiar Webhook URL en Meta

1. Ir a Meta Developer Dashboard
2. Whatsapp → Configuration
3. Actualizar **Callback URL** a tu Vercel production URL
4. Cambiar **Verify Token** si es necesario
5. Click "Verify and Save"

---

## ⚠️ Troubleshooting

### "Signature validation failed"

**Causas:**
- `META_APP_SECRET` incorrecto
- Body no se leyó como raw buffer
- Header `x-hub-signature-256` corrupto

**Solución:**
- Verificar `META_APP_SECRET` en Vercel
- Revisar que se lee raw body antes de parsing
- Usar `crypto.timingSafeEqual` para comparar

### "Verification failed - invalid token"

**Causas:**
- `WHATSAPP_VERIFY_TOKEN` no coincide con el configurado en Meta
- Typo en el verify token

**Solución:**
- Copiar exactamente el token de Vercel
- Configurar el mismo en Meta Developer Dashboard

### "Backend returned status 500"

**Causas:**
- Backend caído
- `BACKEND_INGEST_URL` incorrecto
- `BACKEND_SHARED_SECRET` no coincide

**Solución:**
- Verificar que backend está corriendo: `curl http://backend:8000/health`
- Revisar logs del backend
- Verificar variables en `.env`

### "CORS error" (Frontend)

Este endpoint no requiere CORS (es server-to-server), pero si necesitas:
```javascript
// CORS headers ya están en vercel.json
```

---

## 📊 Monitoreo

### Vercel Logs

```bash
vercel logs --prod
```

### Backend Logs

```bash
# Ver logs en tiempo real
tail -f logs/whatsapp.log

# O consultar DB
SELECT * FROM transactions WHERE source_system = 'whatsapp'
```

---

## 🔮 Futuro

### Media Download (Descarga de documentos/imágenes)

Implementar endpoint `GET /webhooks/whatsapp/media/{media_id}` que:
1. Descarga media via Graph API
2. Procesa con `ingest.py` (OCR, extracción)
3. Crea Transaction automáticamente

**Requerimientos:**
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_BUSINESS_ACCOUNT_ID`

### Respuestas Automáticas

Enviar mensajes de WhatsApp directamente desde Ledger:
```python
# Enviar comprobante de recepción
send_whatsapp_message(
    to=wa_id,
    message="Recibimos tu comprobante ✅",
    media_url="https://..."
)
```

### Webhooks Bidireccionales

Actualizar estado de transacciones en WhatsApp:
```python
# Cuando se resuelve un matching
update_whatsapp_status(
    to=wa_id,
    message="Tu comprobante fue procesado ✅ Monto: $1000"
)
```

---

## 📞 Referencias

- [Meta Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Webhook Signature Verification](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/verify-requests)
- [Vercel Functions](https://vercel.com/docs/functions/overview)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Última actualización:** 2025-01-15  
**Estado:** ✅ Production Ready
