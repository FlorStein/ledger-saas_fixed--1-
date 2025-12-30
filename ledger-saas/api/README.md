# `/api` - Vercel Serverless Functions

Este directorio contiene las **Vercel Serverless Functions** (Node.js) que actúan como webhooks para **Meta Cloud API (WhatsApp)**.

## 📋 Estructura

```
api/
└── whatsapp-webhook.js    ← Webhook de WhatsApp (GET verification + POST events)
```

## 🔧 whatsapp-webhook.js

Endpoint único que maneja:

1. **GET Verification** (solo lectura)
   - Valida el token
   - Retorna challenge
   - Meta solo llama una vez durante setup

2. **POST Events** (recepción de eventos)
   - Valida firma HMAC SHA256
   - Parsea eventos de WhatsApp
   - Hace multi-tenant routing
   - Responde rápido (200 OK)
   - Forward al backend de forma asincrónica

## 🚀 Deployment

### Vercel CLI (Local)

```bash
# Test local
vercel dev

# Ver función
vercel functions list

# Deploy preview
vercel

# Deploy production
vercel --prod
```

### GitHub → Vercel (Automático)

1. Conectar repo a Vercel
2. Cada push a main:
   - Build automático
   - Deploy a preview (si no es main)
   - Deploy a production (si es main)

## 📝 Variables de Entorno

En **Vercel Settings → Environment Variables:**

```
WHATSAPP_VERIFY_TOKEN=ledger_saas_verify_123
META_APP_SECRET=<from Meta>
BACKEND_INGEST_URL=<backend URL>
BACKEND_SHARED_SECRET=ledger_saas_backend_secret
TENANT_ROUTING_JSON={"1234567890":"tenant_demo"}
```

## 🧪 Testing

### Local

```bash
# Verificación
curl "http://localhost:3000/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=test_challenge"

# POST (requiere firma válida)
python3 ../test_whatsapp_integration.py
```

### Production

```bash
# Verificar via Vercel Logs
vercel logs --prod

# Test manual (ver WHATSAPP_SETUP.md)
```

## 🔐 Seguridad

- ✅ Validación de firma HMAC SHA256
- ✅ Timing-safe compare
- ✅ Lectura de raw body (no parsed JSON)
- ✅ Bearer token para forward al backend
- ✅ HTTPS en todo

## 📚 Documentación

- [WHATSAPP_SETUP.md](../WHATSAPP_SETUP.md) - Setup completo
- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - Deploy a producción
- [test_whatsapp_integration.py](../test_whatsapp_integration.py) - Tests

## 🆘 Troubleshooting

**"Signature validation failed"**
- Verificar `META_APP_SECRET` en Vercel
- Usar raw body (no JSON parsed)

**"Verification failed"**
- `hub.verify_token` debe coincidir con `WHATSAPP_VERIFY_TOKEN`
- Verificar en Meta Dashboard

**"Backend returned 500"**
- Ver logs del backend
- Verificar `BACKEND_INGEST_URL`
- Revisar `BACKEND_SHARED_SECRET`

## 🔄 Flujo

```
Meta WhatsApp Cloud API
    ↓ (POST /api/whatsapp-webhook)
Vercel Function
    ↓ (Valida firma + Multi-tenant routing)
Response 200 OK (inmediato)
    ↓ (Async forward)
Backend FastAPI
    ↓ (/webhooks/whatsapp/meta/cloud)
Database
```

## 📞 Referencias

- [Vercel Functions Docs](https://vercel.com/docs/functions/overview)
- [Meta Cloud API Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [Node.js crypto HMAC](https://nodejs.org/api/crypto.html#crypto_hmac)

---

**Última actualización:** 2025-01-15
