# Estado Actual del WhatsApp POC - Resumido

## ✅ Completado

### Frontend
- [x] Tab "Clientes" con agregación de clientes desde ventas
- [x] Tab "Configuración" con seguridad de cuenta (2FA email/WhatsApp)
- [x] Sidebar con 6 iconos de features navegables
- [x] Logout funcional

### Vercel API
- [x] `api/whatsapp-webhook.js` - Recibe webhooks de Meta, valida HMAC, genera requestId, logs estructurados, forwarda al backend
- [x] `api/simulate-whatsapp.js` - Endpoint de test sin HMAC, valida payload structure, matching logs, forwarda exacto

### Backend FastAPI
- [x] `GET /webhooks/whatsapp/meta/cloud/health` - Diagnóstico completo con tenant/channel details, timestamps
- [x] `POST /webhooks/whatsapp/meta/cloud` - Recibe eventos, tenant resolution, DB persistence (WhatsAppEvent + IncomingMessage idempotency)
- [x] `seed.py` - Auto-crea Meta channel si META_WA_PHONE_NUMBER_ID seteado

### Environment Variables
- [x] `.env.example` actualizado con BACKEND_SHARED_SECRET, META_WA_TOKEN (renamed from ACCESS_TOKEN), META_APP_SECRET
- [x] Vercel env properly documented in WHATSAPP_QUICKSTART.md

### Scripts PowerShell
- [x] `scripts/test_health.ps1` - Test health endpoint con output formateado
- [x] `scripts/test_simulate_whatsapp.ps1` - Test simulate endpoint con parameters personalizables

### Documentación
- [x] WHATSAPP_QUICKSTART.md actualizado con:
  - [x] "Qué deberías ver" en cada paso
  - [x] Errores comunes detallados con soluciones específicas
  - [x] Comandos útiles para debugging y verificación

---

## 🔄 Pronto a Testear (Secuencia Recomendada)

### 1. Setup Local
```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -c "from app.db import init_db; from app.seed import seed_if_empty; from app.db import SessionLocal; init_db(); db = SessionLocal(); seed_if_empty(db); db.close()"

# Start backend
.\.venv\Scripts\python.exe app/main.py
```

### 2. Exponer Backend
```powershell
# Opción A: ngrok
ngrok http 8000
# Nota la URL: https://abc123.ngrok.io

# Opción B: Cloudflare
cloudflared tunnel --url http://localhost:8000
```

### 3. Configurar Vercel
```powershell
vercel env add BACKEND_INGEST_URL
# Value: https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud

vercel env add BACKEND_SHARED_SECRET
# Value: (debe coincidir con backend .env)

vercel --prod
```

### 4. Test Health
```powershell
.\scripts\test_health.ps1
# Debe mostrar: tenants, channels, ✅ Configured, etc
```

### 5. Test Simulate
```powershell
.\scripts\test_simulate_whatsapp.ps1 -Message "Test" -PhoneNumberId "META_WA_PHONE_NUMBER_ID"
# Debe mostrar: request_id, status: "received", messages_processed: 1
```

### 6. Verificar Backend Persistence
```powershell
# Ver últimas transacciones
cd backend
.\.venv\Scripts\python.exe -c "from app.db import SessionLocal; from app.models import Transaction; db = SessionLocal(); txs = db.query(Transaction).filter_by(source_system='whatsapp').order_by(Transaction.id.desc()).limit(3).all(); [print(f'{t.id}: {t.source_file}') for t in txs]; db.close()"
```

### 7. Test Meta Real (opcional)
- Ve a Meta Developers > WhatsApp > Configuration
- Webhook URL: `https://tu-vercel-url.vercel.app/api/whatsapp-webhook`
- Verify Token: `WHATSAPP_VERIFY_TOKEN` de Vercel
- Suscribite a: `messages`
- Enviá un mensaje desde tu celular al número de prueba

---

## 📋 Cómo Funciona el Flujo Actual

### Simulación (test_simulate_whatsapp.ps1)
```
PowerShell
  ↓
POST /api/simulate-whatsapp (Vercel)
  • Valida: entry[0].changes[0].value obligatorio
  • Genera requestId
  • Extrae: sender_wa_id, phone_number_id
  • Logs: [requestId] prefix
  ↓
POST /webhooks/whatsapp/meta/cloud (Backend con Bearer auth)
  • Header: Authorization: Bearer BACKEND_SHARED_SECRET
  • _resolve_tenant(): X-Tenant-ID header → Channel lookup → Tenant.phone_number_id
  • Persist: WhatsAppEvent (raw payload)
  • Check idempotency: IncomingMessage (tenant_id, message_id)
  • Process message: type=text (log), type=document (download + parse + create Transaction), type=image (TODO)
  ↓
Database (SQLite ./app.db)
  • WhatsAppEvent: raw event for traceability
  • IncomingMessage: idempotency marker
  • Transaction: parsed data (si es document)
```

### Meta Real
```
Meta Webhook (X-Hub-Signature-256 HMAC validation)
  ↓
POST /api/whatsapp-webhook (Vercel)
  • Valida signature con META_APP_SECRET
  • Genera requestId
  • Logs de entrada/salida
  ↓
POST /webhooks/whatsapp/meta/cloud (Backend)
  [mismo flujo que simulación]
```

---

## 🔍 Debugging Quick Reference

### "No veo el request en Vercel"
```powershell
vercel logs --follow
# Debe mostrar: POST /api/simulate-whatsapp [requestId]
```

### "Backend no recibe nada"
```powershell
# 1. Verificar túnel está activo
ngrok ngrok_status  # o revisar ventana de ngrok

# 2. Verificar BACKEND_INGEST_URL
vercel env ls | grep BACKEND_INGEST_URL

# 3. Revisar logs del backend
# Debe mostrar: "📱 Meta Cloud Event"
```

### "Request llega pero sin tenant"
```powershell
# Backend logs: "⚠️  Could not resolve tenant, using default"
# Solución: Verificar META_WA_PHONE_NUMBER_ID matches el payload
# O ejecutar seed de nuevo
```

### "Error 401 Unauthorized"
```powershell
# Backend logs: "❌ Authorization header missing"
# Solución: Verificar BACKEND_SHARED_SECRET coincide en ambos lados
```

---

## 📦 Arquitectura Simplificada

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEDGER-SAAS WHATSAPP FLOW                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Test Layer (PowerShell Scripts)                               │
│  ├─ test_simulate_whatsapp.ps1   → /api/simulate-whatsapp     │
│  └─ test_health.ps1              → /webhooks/whatsapp/.../h.. │
│                                                                  │
│  Vercel Edge (Node.js Serverless)                              │
│  ├─ /api/whatsapp-webhook                                      │
│  │   • HMAC validation (X-Hub-Signature-256)                   │
│  │   • RequestId generation                                     │
│  │   • Structured logging [requestId] prefix                   │
│  │   └─→ POST /webhooks/whatsapp/meta/cloud (Bearer auth)     │
│  │                                                               │
│  └─ /api/simulate-whatsapp                                      │
│      • Payload structure validation (no HMAC)                   │
│      • RequestId generation                                     │
│      • Same logging + forwarding as webhook.js                  │
│      └─→ POST /webhooks/whatsapp/meta/cloud (Bearer auth)     │
│                                                                  │
│  Backend API (FastAPI on localhost:8000 / ngrok tunnel)        │
│  ├─ GET /webhooks/whatsapp/meta/cloud/health                   │
│  │   └─ Returns: env status, tenant/channel details, timestamp  │
│  │                                                               │
│  ├─ POST /webhooks/whatsapp/meta/cloud                         │
│  │   ├─ Verify Bearer auth                                      │
│  │   ├─ Resolve tenant (header → Channel → Tenant.phone_id)    │
│  │   ├─ Persist WhatsAppEvent (raw)                            │
│  │   ├─ Check IncomingMessage idempotency                      │
│  │   └─ Process messages:                                       │
│  │       ├─ text: Log body                                      │
│  │       ├─ document: Download → Parse → Create Transaction     │
│  │       └─ image: TODO (download + OCR)                        │
│  │                                                               │
│  └─ GET /webhooks/whatsapp/meta/cloud/seed (auto-run on start)  │
│      └─ Creates Channel if META_WA_PHONE_NUMBER_ID set         │
│                                                                  │
│  Database (SQLite ./app.db)                                     │
│  ├─ Tenant (id, name, phone_number_id)                         │
│  ├─ Channel (tenant_id, provider, external_id)                 │
│  ├─ WhatsAppEvent (tenant_id, phone_number_id, raw_payload)    │
│  ├─ IncomingMessage (tenant_id, message_id, status) [idempotent]│
│  ├─ Transaction (tenant_id, source_system, doc_type, amounts) │
│  └─ Counterparty, User, Sale, etc. (existing)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Próximos Pasos (Post-POC)

1. **Env Vars Validation**: Agregar checks en startup de backend para META_WA_TOKEN, BACKEND_SHARED_SECRET
2. **Tenant Routing**: Soportar multi-tenant scenarios con X-Tenant-ID fallback
3. **Document Processing**: Completar OCR para imágenes, mejorar parsing de PDFs
4. **Message Replies**: Implementar endpoint para enviar mensajes de vuelta al usuario
5. **Analytics**: Dashboard con stats de mensajes recibidos, documentos procesados, transactions creados
6. **Error Recovery**: Retry logic para downloads fallidos, queue para procesamiento async
7. **Webhooks Monitoring**: Logs persistentes, alertas en fallos de validación

---

**Última actualización:** 2025-01-15  
**Estado:** Listo para testing (POC v1 completo)
