# Guía de Setup Rápido - WhatsApp Webhook

## Para probar HOY sin más vueltas

### 1. Exponé tu backend con un túnel

**Opción A: ngrok**
```powershell
ngrok http 8000
```
Te dará una URL tipo: `https://abc123.ngrok.io`

**Opción B: Cloudflare Tunnel**
```powershell
cloudflared tunnel --url http://localhost:8000
```

### 2. Configurá las variables en Vercel

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

### 3. Probá el endpoint de simulación

```powershell
# Simulación simple
$body = @{
    entry = @(
        @{
            changes = @(
                @{
                    value = @{
                        metadata = @{
                            phone_number_id = "123456789"
                        }
                        messages = @(
                            @{
                                from = "5491234567890"
                                type = "text"
                                text = @{ body = "Hola desde simulación" }
                                timestamp = "1735689600"
                                id = "wamid.test123"
                            }
                        )
                    }
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-WebRequest -Uri "https://tu-vercel-url.vercel.app/api/simulate-whatsapp" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### 4. Verificá el health check

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/webhooks/whatsapp/meta/cloud/health"
```

Debe mostrar:
- ✅ META_WA_TOKEN: Set
- ✅ BACKEND_SHARED_SECRET: Set
- ✅ META_WA_PHONE_NUMBER_ID: (tu número)
- meta_channels: 1 o más

### 5. Probá con Meta real

Una vez que funcione la simulación y el backend reciba el evento:

1. Ve a Meta Developers > WhatsApp > Configuration
2. Webhook URL: `https://tu-vercel-url.vercel.app/api/whatsapp-webhook`
3. Verify token: (el que pusiste en `WHATSAPP_VERIFY_TOKEN`)
4. Suscribite a: `messages`
5. Enviá un mensaje de prueba al número de WhatsApp Business

### 6. Variables de entorno completas

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

### 7. Troubleshooting

**El backend no recibe nada:**
- Verificá que el túnel esté activo (`ngrok` o `cloudflared`)
- Verificá `BACKEND_INGEST_URL` en Vercel
- Verificá que `BACKEND_SHARED_SECRET` coincida en ambos lados

**Error 401 Unauthorized:**
- `BACKEND_SHARED_SECRET` no coincide entre Vercel y backend

**Meta no verifica el webhook:**
- `WHATSAPP_VERIFY_TOKEN` incorrecto en Vercel
- La URL de Vercel debe ser HTTPS

**Signature inválida:**
- `META_APP_SECRET` incorrecto o faltante
- El payload fue modificado (man-in-the-middle)

**Tenant no se resuelve:**
- Falta el Channel en DB con `external_id = phone_number_id`
- O falta `tenant.phone_number_id` seteado
- Ejecutá seed nuevamente con `META_WA_PHONE_NUMBER_ID` en env

### 8. Comandos útiles

```powershell
# Ver logs de Vercel en tiempo real
vercel logs --follow

# Recrear DB con tenant/channel correcto
cd backend
Remove-Item app.db
& .\.venv\Scripts\python.exe -c "from app.db import init_db; from app.seed import seed_if_empty; from app.db import SessionLocal; init_db(); db = SessionLocal(); seed_if_empty(db); db.close()"

# Ver health check
Invoke-RestMethod http://localhost:8000/webhooks/whatsapp/meta/cloud/health | ConvertTo-Json -Depth 5
```
