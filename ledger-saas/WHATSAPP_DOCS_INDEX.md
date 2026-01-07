# WhatsApp Integration - Documentación Completa

## 📚 Documentos por Propósito

### 🚀 Para Empezar Ahora

**1. [WHATSAPP_QUICKSTART.md](WHATSAPP_QUICKSTART.md)** ⭐ EMPIEZA AQUÍ
- Setup en 5 pasos simples
- Exponé backend con ngrok/tunnel
- Configura Vercel env vars
- Test rápido con simulate endpoint
- Troubleshooting de errores comunes

**Tiempo:** 15 minutos  
**Resultado:** Backend + Vercel conectados

---

### 🧪 Para Testear Completo

**2. [TEST_EXECUTION_GUIDE.md](TEST_EXECUTION_GUIDE.md)** ⭐ TESTING PASO A PASO
- 7 fases de testing (20 minutos totales)
- Pre-requisitos y verificación
- Cada fase con expected outputs
- Error scenarios (opcional)
- Test results template

**Tiempo:** 20 minutos  
**Resultado:** Validar flujo completo funciona

**Utiliza estos scripts:**
- `.\scripts\test_health.ps1` - Verifica backend health
- `.\scripts\test_simulate_whatsapp.ps1` - Simula webhook de Meta

---

### 📊 Para Entender Estado Actual

**3. [WHATSAPP_POC_STATUS.md](WHATSAPP_POC_STATUS.md)** - Estado Ejecutivo
- ✅ Qué está completado
- 🔄 Qué está listo para testear
- 📋 Cómo funciona el flujo
- 🔍 Debugging quick reference
- 📦 Arquitectura simplificada

**Tiempo:** 5 minutos (lectura rápida)  
**Resultado:** Entender architecture & state

---

### 📝 Para Revisar Cambios

**4. [WHATSAPP_CHANGES_SUMMARY.md](WHATSAPP_CHANGES_SUMMARY.md)** - Resumen de Cambios
- Qué se cambió en cada archivo
- Antes/después comparación
- Ejemplos de salida esperada
- Checklist pre-deploy

**Tiempo:** 10 minutos  
**Resultado:** Saber exactamente qué cambió

---

## 🔧 Archivos de Código Modificados

### Backend (Python/FastAPI)

**[backend/app/routers/whatsapp.py](backend/app/routers/whatsapp.py)**
- `GET /webhooks/whatsapp/meta/cloud/health` - Endpoint de diagnóstico mejorado
- `POST /webhooks/whatsapp/meta/cloud` - Recepción de eventos (ya implementado)
- `_resolve_tenant()` - Helper para multi-tenant routing

**[backend/app/seed.py](backend/app/seed.py)**
- Auto-crea Channel de Meta si `META_WA_PHONE_NUMBER_ID` está seteada
- Evita setup manual en DB

**[backend/.env.example](backend/.env.example)**
- `BACKEND_SHARED_SECRET` - Secret compartido con Vercel (nuevo)
- `META_WA_TOKEN` - Token Meta (renombrado de ACCESS_TOKEN)
- `META_APP_SECRET` - App secret de Meta (nuevo)
- Documentación mejorada

---

### Vercel (Node.js Serverless)

**[api/whatsapp-webhook.js](api/whatsapp-webhook.js)**
- Recibe webhooks reales de Meta Cloud API
- HMAC-SHA256 validation (X-Hub-Signature-256)
- GenerateRequestId() para tracing distribuido
- Forwarda a backend con Bearer auth
- Logs estructurados con [requestId] prefix
- Error handling (500 si falta config)

**[api/simulate-whatsapp.js](api/simulate-whatsapp.js)**
- Endpoint de test SIN HMAC validation
- Payload structure validation (entry[0].changes[0].value)
- GenerateRequestId() matching webhook.js
- Mismo logging + forwarding que webhook
- Ideal para desarrollo sin Meta real

---

### Scripts PowerShell (Testing)

**[scripts/test_health.ps1](scripts/test_health.ps1)** ✨ NUEVO
```powershell
.\scripts\test_health.ps1
```
- Verifica health endpoint del backend
- Muestra estado de env vars (META_WA_TOKEN, BACKEND_SHARED_SECRET, etc)
- Lista tenants + channels con detalles
- Error handling + troubleshooting

**[scripts/test_simulate_whatsapp.ps1](scripts/test_simulate_whatsapp.ps1)** ✨ NUEVO
```powershell
.\scripts\test_simulate_whatsapp.ps1 -Message "Tu mensaje" -PhoneNumberId "123456789012345"
```
- Construye payload Meta-compatible
- POST a /api/simulate-whatsapp
- Muestra respuesta + backend response
- Parámetros: Message, PhoneNumberId, SenderWaId, VercelUrl

---

## 🌐 Endpoints Reference

### Backend Local (http://localhost:8000)

| Método | Endpoint | Auth | Propósito |
|--------|----------|------|----------|
| GET | `/webhooks/whatsapp/meta/cloud/health` | None | Diagnóstico estado |
| POST | `/webhooks/whatsapp/meta/cloud` | Bearer | Recibir eventos |

### Vercel (https://tu-proyecto.vercel.app)

| Método | Endpoint | Auth | Propósito |
|--------|----------|------|----------|
| GET | `/api/whatsapp-webhook` | Token query | Verificación inicial |
| POST | `/api/whatsapp-webhook` | HMAC Header | Recibir webhooks reales |
| POST | `/api/simulate-whatsapp` | None | Test sin Meta |

---

## 🔐 Environment Variables Reference

### Backend (`.env` o sistema)

```env
# Seguridad webhook
BACKEND_SHARED_SECRET=ledger_saas_backend_secret  # Debe coincidir con Vercel

# Meta Graph API
META_WA_TOKEN=EAAxxxxx_tu_token_de_meta_aqui     # Para descargar media
META_WA_PHONE_NUMBER_ID=123456789012345          # Identificador de tu número
META_APP_SECRET=abc123def456                     # Para validación HMAC

# Webhook verification
WHATSAPP_VERIFY_TOKEN=mi_token_secreto           # Para Meta verify GET request
```

### Vercel (`.env` o Vercel Dashboard)

```env
# Backend communication
BACKEND_INGEST_URL=https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud
BACKEND_SHARED_SECRET=ledger_saas_backend_secret

# Meta validation
WHATSAPP_VERIFY_TOKEN=mi_token_secreto
META_APP_SECRET=abc123def456
```

---

## 📋 Checklist de Setup

### 1️⃣ Preparación (Haz una sola vez)

- [ ] Instalar/actualizar Python 3.9+
- [ ] Instalar/actualizar Node.js 16+
- [ ] Instalar ngrok o Cloudflare Tunnel
- [ ] Instalar/configurar Vercel CLI
- [ ] Crear venv Python en backend

### 2️⃣ Cada Sesión de Testing

- [ ] Backend: `.venv\Scripts\python.exe app/main.py`
- [ ] Tunnel: `ngrok http 8000` (o Cloudflare)
- [ ] Vercel: `vercel --prod` (después cambios env)
- [ ] Test: `.\scripts\test_health.ps1` ✅
- [ ] Test: `.\scripts\test_simulate_whatsapp.ps1` ✅

### 3️⃣ Antes de Meta Real

- [ ] Health check pasa ✅
- [ ] Simulate endpoint funciona ✅
- [ ] Transactions se crean en DB ✅
- [ ] Idempotency previene duplicados ✅
- [ ] Vercel logs muestran [requestId] ✅
- [ ] Backend logs muestran `📱 Meta Cloud Event` ✅

---

## 🚨 Errores Frecuentes

**Error:** Backend returns `500 BACKEND_INGEST_URL not configured`  
**Solución:** `vercel env add BACKEND_INGEST_URL` y `vercel --prod`

**Error:** Health check shows `❌ Missing` para vars  
**Solución:** Setear en backend `.env` o variables de sistema

**Error:** Simulate returns `401 Unauthorized`  
**Solución:** BACKEND_SHARED_SECRET debe coincidir entre Vercel y backend

**Error:** No se ve el request en backend logs  
**Solución:** Verificar ngrok tunnel esté activo + BACKEND_INGEST_URL correcto

**Error:** DB vacía después de simulate  
**Solución:** Revisar backend logs buscar `Error persisting` + verificar permisos app.db

---

## 📞 Flujo Completo en Acción

```
PowerShell test_simulate_whatsapp.ps1
  ↓
[requestId generado]
  ↓
POST https://tu-vercel.vercel.app/api/simulate-whatsapp
  • Sin HMAC validation (es simulación)
  • Valida estructura Meta
  • Genera requestId
  • Logs: [requestId] 🔔 WEBHOOK POST
  ↓
POST https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud
  • Header: Authorization: Bearer BACKEND_SHARED_SECRET
  • Header: X-Request-ID: [requestId]
  • Body: payload Meta + request_id
  ↓
Backend FastAPI:
  1. Verifica Bearer auth
  2. _resolve_tenant(phone_number_id)
  3. Persiste WhatsAppEvent (raw)
  4. Verifica idempotencia (IncomingMessage)
  5. Procesa según tipo (text/document/image)
  6. Crea Transaction si es document
  7. Logs: 📱 Meta Cloud Event
  ↓
Database SQLite:
  • WhatsAppEvent (para auditoría)
  • IncomingMessage (para idempotencia)
  • Transaction (si hay documento)
  ↓
Response 200:
  status: "received"
  tenant_id: 1
  messages_processed: 1
```

---

## 🎓 Learning Resources

- [Meta Cloud API Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [SQLAlchemy Sessions](https://docs.sqlalchemy.org/en/14/orm/session.html)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)

---

## 📅 Cronograma Recomendado

**Hoy (Session 1):**
1. Leer WHATSAPP_QUICKSTART.md
2. Ejecutar test_health.ps1
3. Ejecutar test_simulate_whatsapp.ps1
4. Verificar logs ✅

**Próximo día (Session 2):**
1. Ejecutar TEST_EXECUTION_GUIDE.md completo
2. Registrar resultados en template
3. Revisar WHATSAPP_POC_STATUS.md

**Cuando esté listo Meta:**
1. Configurar webhook en Meta Developers
2. Setear WHATSAPP_VERIFY_TOKEN correcto
3. Test con mensaje real desde celular
4. Monitor logs en production

---

## 📞 Support Docs

- Error: `❌ Authorization header missing` → Ver sección "Backend returns 401" en WHATSAPP_QUICKSTART.md
- Error: `Invalid signature` → Ver sección "X-Hub-Signature-256 validation failed" en WHATSAPP_QUICKSTART.md
- Error: `Tenant not resolved` → Ver sección "Tenant not resolved" en WHATSAPP_QUICKSTART.md
- Pregunta: "¿Cómo agregó el requestId a los logs?" → Ver WHATSAPP_CHANGES_SUMMARY.md, sección "Backend FastAPI"

---

**Última actualización:** 6 Enero 2026  
**Versión:** 1.0  
**Estado:** ✅ Listo para Testing
