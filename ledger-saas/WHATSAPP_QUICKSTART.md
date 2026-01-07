# Guía de Setup Rápido - WhatsApp Webhook

## Para probar HOY sin más vueltas

### 0. Preparar la Base de Datos (Dev Only)

Como usamos SQLite sin Alembic, cualquier cambio en modelos requiere recrear la BD.
**IMPORTANTE:** Primero navegá al directorio del proyecto:

```powershell
cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas"
```
#### Con PowerShell (recomendado):
```powershell
cd backend
Remove-Item .\app.db -ErrorAction SilentlyContinue
& .\.venv\Scripts\python.exe -c "from app.db import Base, engine, SessionLocal; from app.seed import seed_if_empty; Base.metadata.create_all(bind=engine); db=SessionLocal(); seed_if_empty(db); db.close()"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Con CMD (Windows):
```cmd
cd backend
if exist app.db del app.db
.venv\Scripts\python.exe -c "from app.db import Base, engine, SessionLocal; from app.seed import seed_if_empty; Base.metadata.create_all(bind=engine); db=SessionLocal(); seed_if_empty(db); db.close()"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Con bash (mac/linux):
```bash
cd backend
rm -f app.db
source .venv/bin/activate
python -c "from app.db import Base, engine, SessionLocal; from app.seed import seed_if_empty; Base.metadata.create_all(bind=engine); db=SessionLocal(); seed_if_empty(db); db.close()"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Nota:** Usamos `created_at` y `updated_at` con `server_default=func.now()` (BD maneja timestamps, no Python). Si ves errores de "no such column", ejecutá el reset arriba.

Ahora exponé el backend con un túnel:

**Opción A: ngrok**
```powershell
ngrok http 8000
```
Te dará una URL tipo: `https://abc123.ngrok.io`

**Opción B: Cloudflare Tunnel**
```powershell
cloudflared tunnel --url http://localhost:8000
```

### 1. Configurá las variables en Vercel

```powershell
cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas"

# URL del túnel + endpoint de ingestión
vercel env add BACKEND_INGEST_URL
# Valor: https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud

# Secret compartido (debe coincidir con backend)
vercel env add BACKEND_SHARED_SECRET
# Valor: ledger_saas_backend_secret

# Redeploy
vercel --prod
```

### 2. Probá el endpoint de simulación

Para no depender de Meta al inicio, usá el script de simulación:

```powershell
# Script automatizado (recomendado)
.\scripts\test_simulate_whatsapp.ps1 `
    -Message "Recibo de transferencia" `
    -PhoneNumberId "123456789012345" `
    -SenderWaId "5491123456789"

# O manual con Invoke-WebRequest
$body = @{
    entry = @(
        @{
            changes = @(
                @{
                    value = @{
                        metadata = @{
                            phone_number_id = "123456789012345"
                        }
                        messages = @(
                            @{
                                from = "5491123456789"
                                type = "text"
                                text = @{ body = "Hola desde simulación" }
                                timestamp = [int]([DateTime]::UtcNow.Subtract([DateTime]::UnixEpoch).TotalSeconds)
                                id = "wamid.test_$(Get-Random)"
                            }
                        )
                    }
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-WebRequest `
    -Uri "https://tu-vercel-url.vercel.app/api/simulate-whatsapp" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

**Qué deberías ver:**
- Vercel logs: `[requestId: xxxxxx] POST /api/simulate-whatsapp`
- Backend logs: `📱 Meta Cloud Event - tenant: 1, phone_number_id: 123456789012345`
- Backend logs: `📝 Text: Hola desde simulación...`
- Database: Nuevo registro en `transactions` table

### 3. Verificá el health check

```powershell
# Script automatizado (recomendado)
.\scripts\test_health.ps1

# O manual
Invoke-RestMethod http://localhost:8000/webhooks/whatsapp/meta/cloud/health | ConvertTo-Json -Depth 5
```

**Qué deberías ver:**
```json
{
  "status": "healthy",
  "environment": {
    "META_WA_TOKEN": "✅ Configured",
    "BACKEND_SHARED_SECRET": "✅ Configured",
    "META_WA_PHONE_NUMBER_ID": "123456789012345"
  },
  "database": {
    "total_tenants": 1,
    "meta_channels": 1,
    "tenants": [
      {
        "id": 1,
        "name": "default",
        "phone_number_id": "123456789012345",
        "channels": [
          {
            "external_id": "123456789012345",
            "kind": "whatsapp"
          }
        ]
      }
    ]
  }
}
```

- ✅ META_WA_TOKEN: Configured (o ✅ Set)
- ✅ BACKEND_SHARED_SECRET: Configured
- ✅ META_WA_PHONE_NUMBER_ID: (tu número)
- database.total_tenants: 1 o más
- database.meta_channels: 1 o más

### 4. Probá con Meta real

Una vez que funcione la simulación y el backend reciba el evento:

1. Ve a Meta Developers > WhatsApp > Configuration
2. Webhook URL: `https://tu-vercel-url.vercel.app/api/whatsapp-webhook`
3. Verify token: (el que pusiste en `WHATSAPP_VERIFY_TOKEN`)
4. Suscribite a: `messages`
5. Enviá un mensaje de prueba al número de WhatsApp Business

### 5. Variables de entorno completas

**Backend (.env)**
```env
BACKEND_SHARED_SECRET=ledger_saas_backend_secret
META_WA_TOKEN=EAAxxxxx (tu token de Meta)
META_WA_PHONE_NUMBER_ID=123456789
META_WA_VERIFY_TOKEN=mi_token_secreto
META_APP_SECRET=abc123def456
```

**Vercel**
```env
BACKEND_INGEST_URL=https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud
BACKEND_SHARED_SECRET=ledger_saas_backend_secret
WHATSAPP_VERIFY_TOKEN=mi_token_secreto
META_APP_SECRET=abc123def456
TENANT_ROUTING_JSON={"123456789": "1"}
```

### 6. Errores Comunes y Soluciones

#### Vercel endpoint returns 500

**Error en logs:**
```
Error: BACKEND_INGEST_URL not configured
Error: BACKEND_SHARED_SECRET not configured
```

**Solución:**
```powershell
# Verificar que ambas variables estén en Vercel
vercel env ls

# Si no están, agregarlas
vercel env add BACKEND_INGEST_URL
vercel env add BACKEND_SHARED_SECRET

# Redeploy
vercel --prod
```

#### Backend returns 401 Unauthorized

**Error en logs:**
```
❌ Authorization header missing or invalid
```

**Solución:**
1. Verificá que Vercel tenga `BACKEND_SHARED_SECRET` seteado
2. Verificá que coincida con `BACKEND_SHARED_SECRET` en backend `.env`
3. El secret debe ser el mismo en ambos lados (sin "Bearer " prefix)

```bash
# Backend
cat backend/.env | grep BACKEND_SHARED_SECRET

# Vercel
vercel env ls | grep BACKEND_SHARED_SECRET
```

#### Meta webhook verification fails

**Error en Meta Developers console:**
```
The URL couldn't be validated. Callback URL and verify token do not match.
```

**Solución:**
1. Verificá que `WHATSAPP_VERIFY_TOKEN` en Vercel sea idéntico al que pusiste en Meta
2. Verificá que la URL de Vercel sea HTTPS (no HTTP)
3. Verificá que `META_APP_SECRET` esté seteado en Vercel

```powershell
# Ver el token que Meta está esperando
vercel env ls | grep WHATSAPP_VERIFY_TOKEN

# Copiar exactamente ese valor a Meta Developers > Configuration
```

#### X-Hub-Signature-256 validation failed

**Error en logs Vercel:**
```
❌ Invalid signature: signature mismatch
```

**Solución:**
1. Verificá que `META_APP_SECRET` coincida con el App Secret en Meta Developers
2. Verificá que el raw body esté siendo leído correctamente (esto está automatizado en whatsapp-webhook.js)
3. Desactiva momentáneamente la validación para debuggear (busca `validateSignature` en api/whatsapp-webhook.js)

#### Tenant not resolved (falls back to tenant_id 1)

**Advertencia en logs:**
```
⚠️  Could not resolve tenant, using default tenant_id 1
```

**Solución:**
1. Ejecuta el seed del backend con la variable correcta:
```bash
# Windows
cd backend
$env:META_WA_PHONE_NUMBER_ID = "123456789012345"
.\.venv\Scripts\python.exe app/seed.py

# O manualmente agregar el Channel:
# INSERT INTO channels (tenant_id, provider, kind, external_id) 
#   VALUES (1, 'meta', 'whatsapp', '123456789012345');
```

2. Verificá que el phone_number_id en el payload Meta coincida con `META_WA_PHONE_NUMBER_ID`

#### Backend recibe evento pero no persiste a la base de datos

**Solución:**
1. Verificá que SQLite esté funcionando:
```powershell
cd backend
# Ver todos los transactions
.\.venv\Scripts\python.exe -c "from app.db import SessionLocal; from app.models import Transaction; db = SessionLocal(); print(db.query(Transaction).count()); db.close()"
```

2. Verificá que el backend pueda escribir en `./app.db`:
```powershell
# Verificar permisos
Get-Acl "backend/app.db" | Format-List
```

3. Revisá los logs del backend para `Error persisting WhatsAppEvent` o `Error saving file`

### 7. Comandos útiles

```powershell
# ========== BACKEND CHECKS ==========

# Ver health endpoint
.\scripts\test_health.ps1

# O manualmente
Invoke-RestMethod http://localhost:8000/webhooks/whatsapp/meta/cloud/health | ConvertTo-Json -Depth 5

# Contar transacciones recibidas
cd backend
.\.venv\Scripts\python.exe -c "from app.db import SessionLocal; from app.models import Transaction; db = SessionLocal(); count = db.query(Transaction).filter_by(source_system='whatsapp').count(); print(f'WhatsApp Transactions: {count}'); db.close()"

# Ver últimas transacciones
.\.venv\Scripts\python.exe -c "from app.db import SessionLocal; from app.models import Transaction; db = SessionLocal(); txs = db.query(Transaction).filter_by(source_system='whatsapp').order_by(Transaction.id.desc()).limit(5).all(); [print(f'{t.id}: {t.doc_type} - {t.amount} {t.currency}') for t in txs]; db.close()"

# Recrear DB desde cero
Remove-Item app.db -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -c "from app.db import init_db; from app.seed import seed_if_empty; from app.db import SessionLocal; init_db(); db = SessionLocal(); seed_if_empty(db); db.close()"

# ========== VERCEL CHECKS ==========

# Ver logs en tiempo real
vercel logs --follow

# Ver todas las variables de entorno
vercel env ls

# Redeploy después de cambiar env vars
vercel --prod

# Ver logs de una función específica
vercel logs api/whatsapp-webhook.js

# ========== TESTING ==========

# Test simulate endpoint
.\scripts\test_simulate_whatsapp.ps1 -Message "Test from script" -PhoneNumberId "123456789012345"

# Test con diferentes tipos de mensaje
.\scripts\test_simulate_whatsapp.ps1 -Message "Recibo de transferencia adjunto" -PhoneNumberId "123456789012345" -SenderWaId "5491234567890"

# ========== TUNNEL ==========

# ngrok (si no está instalado: choco install ngrok)
ngrok http 8000
# Copiá la URL https://xxx.ngrok.io y usala como BACKEND_INGEST_URL

# Cloudflare tunnel
cloudflared tunnel --url http://localhost:8000
---

## Deployment en Vercel (Monorepo)

Este proyecto usa una estructura de monorepo:
- `frontend/` - Aplicación Vite/React (se sirve en `/`)
- `api/` - Funciones serverless Node.js (se sirven en `/api/*`)
- `backend/` - FastAPI local (NO se deploya; se expone con ngrok/cloudflare)

**Configuración clave:**

1. **NO cambiar Root Directory** en Vercel settings - dejar en `.` (raíz)
2. El archivo `vercel.json` en la raíz controla todo:
   - Build del frontend usando `@vercel/static-build`
   - Build de funciones API usando `@vercel/node`
   - Rutas: `/api/*` → funciones, `/*` → frontend estático

3. **Para deployar:**
   ```powershell
   cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas"
   vercel --prod
   ```

4. **Resultado esperado:**
   - `https://tu-app.vercel.app/` → muestra el frontend React
   - `https://tu-app.vercel.app/api/simulate-whatsapp` → función serverless
   - `https://tu-app.vercel.app/api/whatsapp-webhook` → recibe webhooks de Meta

**Nota:** Si el frontend no se ve después del deploy, verificá:
- Que `frontend/package.json` tenga `"build": "vite build"`
- Que `vercel.json` esté en la raíz (no en subdirectorios)
- Los logs de build en Vercel dashboard