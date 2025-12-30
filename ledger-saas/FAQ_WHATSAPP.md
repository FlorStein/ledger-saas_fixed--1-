# ❓ FAQ - WhatsApp Cloud API Integration

## General

### ¿Por qué usar Vercel como intermediario?

**Respuesta:** Meta Cloud API envía webhooks vía HTTP POST a una URL pública. Vercel proporciona:
- ✅ URL pública con HTTPS
- ✅ Serverless (sin servidor que mantener)
- ✅ Auto-escaling
- ✅ Logs integrados
- ✅ Enviroment variables encriptadas
- ✅ Deployment automático desde GitHub

Tu backend FastAPI está en una máquina privada (localhost/VPN), así que Vercel actúa como proxy público seguro.

---

### ¿Es seguro pasar datos por Vercel?

**Respuesta:** Sí, completamente:

1. **Validación de firma:** El Vercel Function valida que los datos vienen de Meta (HMAC SHA256)
2. **Bearer Token:** El forward al backend requiere token secreto
3. **HTTPS:** Toda comunicación es encriptada en tránsito
4. **Env vars encriptadas:** Meta App Secret nunca está en código
5. **Logs sanitizados:** Los datos sensibles no se loguean

**Flujo seguro:**
```
Meta (HTTPS)
  ↓ + Firma HMAC
Vercel (Valida firma con secret)
  ↓ + Bearer Token
Backend (Valida token)
  ↓
Database
```

---

### ¿Qué pasa si Vercel está caído?

**Respuesta:** Meta reintentará:
- Reintento 1: 5 minutos después
- Reintento 2: 30 minutos después
- Reintento 3: 2 horas después
- Reintento 4: 24 horas después

**Solución:** Mantén monitoreado `vercel logs --prod --follow`

---

## Setup & Configuration

### ¿Dónde obtengo el App Secret?

**Respuesta:** 
```
https://developers.facebook.com/apps
→ Selecciona tu app
→ Settings → Basic
→ App Secret (cópialo, está debajo de App ID)
```

**Nota:** Si es requerido, meta pedirá contraseña de Facebook.

---

### ¿Qué es TENANT_ROUTING_JSON?

**Respuesta:** Mapeo de números de teléfono de Meta a tenants de tu app.

```json
{
  "1234567890": "tenant_demo",
  "9876543210": "tenant_production",
  "5555555555": "tenant_testing"
}
```

**Cómo obtener `phone_number_id`:**
```
Meta Developer Dashboard
→ App → WhatsApp → API Setup
→ Test Message → "From" (ese es el phone_number_id)
```

---

### ¿Debo usar venv?

**Respuesta:** Sí, es recomendado:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt
```

El script `setup_whatsapp.sh` lo hace automáticamente.

---

## Deployment

### ¿Cómo hago deploy a Vercel?

**Respuesta: Opción A - Desde terminal**

```bash
# Instalar CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

**Opción B - Automático desde GitHub**

1. Conectar repo a Vercel
   ```
   https://vercel.com/new
   → Import Git Repository
   → Selecciona tu repo
   → Deploy
   ```

2. Cada push a `main` hace deploy automático

---

### ¿Cómo agregó variables de entorno en Vercel?

**Opción A - CLI:**

```bash
vercel env add WHATSAPP_VERIFY_TOKEN
vercel env add META_APP_SECRET
vercel env add BACKEND_INGEST_URL
vercel env add BACKEND_SHARED_SECRET
vercel env add TENANT_ROUTING_JSON
```

**Opción B - Web UI:**

```
Vercel Dashboard
→ Tu proyecto
→ Settings → Environment Variables
→ Add New Variable
```

---

### ¿Cómo hago rollback si algo va mal?

**Respuesta:**

```bash
# Ver deployments previos
vercel list

# Rollback a deployment anterior
vercel rollback

# O especifica timestamp
vercel rollback 2025-01-15T12:00:00Z
```

---

## Testing

### ¿Cómo testeo localmente?

**Respuesta:**

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Vercel Function
cd ledger-saas
vercel dev

# Terminal 3: Tests
python test_whatsapp_integration.py
```

---

### ¿Cómo testeo en producción?

**Respuesta:**

```bash
# Ver logs en vivo
vercel logs --prod --follow

# Desde tu app Meta, envía test message
# O simula POST con curl (necesita firma válida)
```

---

### Las pruebas dicen "Connection refused"

**Respuesta:** El backend no está corriendo:

```bash
# Verificar que backend está levantado
curl http://localhost:8000/docs

# Si no funciona, levanta el backend
cd backend
python -m uvicorn app.main:app --reload

# Luego vuelve a correr tests
python test_whatsapp_integration.py
```

---

## Troubleshooting

### "Signature validation failed" en Vercel logs

**Causas:**
1. ❌ `META_APP_SECRET` incorrecto en Vercel
2. ❌ Alguien modificó el body del webhook
3. ❌ Vercel está usando el env var incorrecto

**Soluciones:**
```bash
# Verificar env var
vercel env list

# Re-agregar variable (la anterior estaba mal)
vercel env rm META_APP_SECRET
vercel env add META_APP_SECRET

# Redeploy
vercel --prod
```

---

### "Unauthorized" error en backend (401)

**Causas:**
1. ❌ `BACKEND_SHARED_SECRET` no coincide
2. ❌ Bearer token malformado

**Verificar:**
```bash
# Backend .env
cat backend/.env | grep BACKEND_SHARED_SECRET

# Vercel env
vercel env list | grep BACKEND_SHARED_SECRET

# Deben ser IDÉNTICOS
```

---

### "Invalid tenant" en logs

**Causa:** El `phone_number_id` no está en `TENANT_ROUTING_JSON`

**Solución:**
```bash
# 1. Obtén el phone_number_id de Meta
# 2. Actualiza TENANT_ROUTING_JSON
"phone_number_id_aqui": "tenant_name"

# 3. Actualiza variable en Vercel
vercel env add TENANT_ROUTING_JSON

# 4. Redeploy
vercel --prod
```

---

### Los mensajes no llegan al backend

**Debug:**
```bash
# 1. Ver logs de Vercel
vercel logs --prod --follow

# 2. Ver logs del backend
tail -f backend/app.log

# 3. Verificar Bearer token
grep BACKEND_SHARED_SECRET backend/.env
grep BACKEND_SHARED_SECRET <(vercel env list)

# 4. Hacer test manual
python test_whatsapp_integration.py
```

---

## Architecture

### ¿Por qué HMAC SHA256?

**Respuesta:** Meta Cloud API requiere validar que los webhooks vienen realmente de Meta.

```
Meta crea firma: HMAC-SHA256(body, APP_SECRET)
                = "a1b2c3d4e5f6..."

Meta envía: body + header "X-Hub-Signature" = "sha256=a1b2c3d4e5f6..."

Vercel calcula: HMAC-SHA256(body, META_APP_SECRET)
                = "a1b2c3d4e5f6..."

Vercel compara con crypto.timingSafeEqual()
```

Si coincide → Request legítimo de Meta ✅  
Si no coincide → Request falsificado o body modificado ❌

---

### ¿Por qué timing-safe compare?

**Respuesta:** Previene timing attacks.

```
❌ Comparación normal: "abc123" == "abc123"
   Toma ~6 bytes de tiempo si ambas coinciden

✅ Timing-safe: Toma MISMO tiempo sin importar cuántos bytes coincidan
   Previene que atacantes adivinen byte por byte
```

---

### ¿Qué es multi-tenant routing?

**Respuesta:** Soporte para múltiples números de WhatsApp + clientes.

```
Escenario: Tu SaaS sirve a 3 clientes

Cliente A:
  phone_number_id: 1234567890
  tenant_id: "empresa_a"

Cliente B:
  phone_number_id: 9876543210
  tenant_id: "empresa_b"

Cliente C:
  phone_number_id: 5555555555
  tenant_id: "empresa_c"

Vercel ve incoming webhook con phone_number_id 9876543210
→ Busca en TENANT_ROUTING_JSON
→ Encuentra tenant_id "empresa_b"
→ Forward al backend con tenant_id
→ Backend crea Counterparty en DB de empresa_b
```

---

## Future Features

### ¿Puedo descargar media (imágenes) de Meta?

**Respuesta:** Sí, es Phase 2. Necesitas:

```python
# 1. Meta Media ID (viene en webhook)
# 2. Access Token (de Meta)
# 3. Download URL de Graph API

# Implementar en whatsapp.py
async def download_media(media_id: str, access_token: str):
    url = f"https://graph.instagram.com/{media_id}?fields=media_product_type&access_token={access_token}"
    # ...descargar
    # ...guardar en /uploads
    # ...procesar con OCR
```

---

### ¿Cómo envío respuestas desde WhatsApp?

**Respuesta:** Meta Cloud API Graph API:

```python
async def send_message(phone_number_id: str, to: str, message: str):
    url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = await httpx.post(url, json=payload)
    return response.json()
```

---

## Security

### ¿Qué pasa si alguien obtiene mi Meta App Secret?

**Respuesta:**

1. Van a poder falsificar webhooks
2. Solución:
   - Ir a Meta Developer Dashboard
   - Settings → Rotate app secret
   - Actualizar Vercel env var
   - Redeploy

---

### ¿Necesito logs en producción?

**Respuesta:** Sí, pero sin datos sensibles:

```javascript
// ✅ BIEN
console.log(`Webhook from phone: ${phone_number_id}`);

// ❌ MAL
console.log(`Webhook payload: ${JSON.stringify(body)}`);  // Loguea números de teléfono

// ✅ MEJOR
console.log(`Processing message for tenant: ${tenant_id}`);
console.error(`Signature validation failed for IP: ${req.ip}`);
```

---

### ¿Cómo roto credenciales?

```bash
# 1. Meta App Secret
# Panel Meta → Settings → Rotate App Secret

# 2. BACKEND_SHARED_SECRET
# backend/.env → generar nuevo token
# vercel env rm BACKEND_SHARED_SECRET
# vercel env add BACKEND_SHARED_SECRET

# 3. WHATSAPP_VERIFY_TOKEN
# vercel env rm WHATSAPP_VERIFY_TOKEN
# vercel env add WHATSAPP_VERIFY_TOKEN
# Actualizar en Meta Dashboard → Webhooks
```

---

## Support

### ¿Dónde reporto bugs?

1. Verificar `vercel logs --prod --follow`
2. Ejecutar `test_whatsapp_integration.py` localmente
3. Revisar `TROUBLESHOOTING` en WHATSAPP_SETUP.md
4. Verificar documentación de Meta Cloud API

### ¿Dónde consigo ayuda?

- **Meta Cloud API:** https://developers.facebook.com/docs/whatsapp/cloud-api
- **Vercel:** https://vercel.com/docs
- **FastAPI:** https://fastapi.tiangolo.com/
- **Este proyecto:** WHATSAPP_SETUP.md

---

**¿Tu pregunta no está aquí?** → Revisa la documentación específica en:
- `WHATSAPP_SETUP.md` - Setup detallado
- `DEPLOYMENT_GUIDE.md` - Deploy
- `WHATSAPP_INTEGRATION_SUMMARY.md` - Overview

