# 🚀 Deployment Guide - WhatsApp Integration

## Checklist Pre-Deployment

### Local Testing ✅

```bash
# Backend
cd backend
pip install requests
python -m uvicorn app.main:app --reload

# Vercel Functions (local)
npm install -g vercel
vercel dev

# Tests
python test_whatsapp_integration.py

# Curl manual
curl "http://localhost:3000/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=test"
```

### Variables de Entorno ✅

**Backend `.env`:**
```dotenv
BACKEND_SHARED_SECRET=ledger_saas_backend_secret
TENANT_ROUTING_JSON={"1234567890":"tenant_demo"}
```

**Vercel Settings:**
- `WHATSAPP_VERIFY_TOKEN=ledger_saas_verify_123`
- `META_APP_SECRET=<from Meta Dashboard>`
- `BACKEND_INGEST_URL=<backend URL>`
- `BACKEND_SHARED_SECRET=ledger_saas_backend_secret`
- `TENANT_ROUTING_JSON={"1234567890":"tenant_demo"}`

---

## Step-by-Step Deployment

### 1. Backend Deployment

**Opción A: Render.com (recomendado)**

```bash
# Crear cuenta en render.com
# Conectar GitHub repo
# Nuevo servicio → Web Service
# Build: pip install -r requirements.txt
# Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
# Variables de entorno: copiar del .env
```

**Opción B: AWS EC2**

```bash
# Crear instancia EC2
# SSH into instance
git clone <tu-repo>
cd ledger-saas/backend
pip install -r requirements.txt
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

**Opción C: Railway.app**

```bash
# Conectar GitHub
# Crear proyecto
# Variables de entorno
# Deploy automático
```

### 2. Vercel Frontend + Functions

```bash
# Conectar GitHub repo a Vercel
# Project Settings → Environment Variables
# Agregar todas las variables (ver arriba)

# O via CLI:
vercel login
vercel link
vercel env add WHATSAPP_VERIFY_TOKEN
vercel env add META_APP_SECRET
vercel env add BACKEND_INGEST_URL
vercel env add BACKEND_SHARED_SECRET
vercel env add TENANT_ROUTING_JSON
vercel --prod
```

### 3. Meta Dashboard - Configuración

1. **Ir a** https://developers.facebook.com
2. **App Settings → Basic**
   - Copiar **App ID**
   - Copiar **App Secret** → guardar en Vercel como `META_APP_SECRET`

3. **WhatsApp → Configuration**
   - Callback URL: `https://<tu-vercel-app>.vercel.app/api/whatsapp-webhook`
   - Verify Token: `ledger_saas_verify_123` (mismo que env)
   - Click "Verify and Save"
   - Meta hará GET a tu endpoint

4. **WhatsApp → Webhooks**
   - Subscribe to: `messages`, `message_status`, `message_template_status_update`

5. **WhatsApp → API Setup**
   - Display Phone Number ID
   - Access Token (para futura descarga de media)

---

## 🔗 URLs Finales

| Componente | URL |
|-----------|-----|
| Frontend | `https://<tu-vercel-app>.vercel.app` |
| Vercel Webhook | `https://<tu-vercel-app>.vercel.app/api/whatsapp-webhook` |
| Backend | `https://<tu-backend>.com` |
| Backend Webhook | `https://<tu-backend>.com/webhooks/whatsapp/meta/cloud` |

---

## ✅ Post-Deployment Testing

### Test 1: Verificación en Vivo

```bash
curl -X GET "https://<tu-vercel-app>.vercel.app/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=test_123"
```

**Esperado:** `200 OK` con respuesta `test_123`

### Test 2: Monitoreo

**Vercel Logs:**
```bash
vercel logs --prod
```

**Backend Logs:**
```bash
# SSH to server
tail -f /var/log/uvicorn.log
```

### Test 3: Enviar Mensaje de Prueba

1. Ir a Meta Test Phone Number
2. Enviar mensaje de prueba a tu número de negocio
3. Verificar logs en Vercel + Backend
4. Confirmar que se guardó en DB

---

## 🔐 Checklist de Seguridad

- ✅ `META_APP_SECRET` es único y seguro
- ✅ `BACKEND_SHARED_SECRET` es único y seguro
- ✅ No guardar secrets en git (usar .env.local, .gitignore)
- ✅ HTTPS en todo (Vercel y Backend)
- ✅ Validación de firma HMAC activa
- ✅ Bearer token en Backend activo
- ✅ CORS configurado (solo si necesario)

---

## 🆘 Troubleshooting Deployment

### "Verification failed" en Meta

**Causas posibles:**
- URL de Vercel incorrecta
- Verify Token no coincide
- Timeout (timeout > 10s)

**Soluciones:**
```bash
# Verificar URL directamente
curl https://<tu-vercel-app>.vercel.app/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=test

# Ver logs
vercel logs --prod

# Reintentar en Meta Dashboard (botón Retry)
```

### "Backend returned status 500"

**En Vercel logs:**
```bash
vercel logs --prod
# Buscar POST a BACKEND_INGEST_URL
```

**En Backend logs:**
```bash
# SSH to backend
tail -f /var/log/uvicorn.log
```

**Causas comunes:**
- Database no inicializada
- Tables no existen
- Variables de entorno faltantes

**Solución:**
```bash
# SSH to backend
cd backend
python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
systemctl restart uvicorn  # o reiniciar tu servicio
```

### "Unauthorized" en Backend (401)

**Causa:** `BACKEND_SHARED_SECRET` no coincide

**Verificar:**
```bash
# Vercel env
vercel env list

# Backend .env
cat backend/.env | grep BACKEND_SHARED_SECRET

# Deben ser idénticos
```

---

## 📊 Monitoreo en Producción

### Vercel Analytics

```bash
vercel analytics
```

### Backend Metrics

Agregar a FastAPI:

```python
from prometheus_client import Counter, Histogram

webhook_received = Counter('whatsapp_webhooks_received', 'Webhooks received')
webhook_duration = Histogram('whatsapp_webhook_duration_seconds', 'Webhook processing time')

@app.post("/webhooks/whatsapp/meta/cloud")
async def receive_whatsapp_event(...):
    with webhook_duration.time():
        webhook_received.inc()
        # ... processing
```

### Log Aggregation (Opcional)

Usar servicio como:
- [Papertrail](https://www.papertrail.com/)
- [LogRocket](https://logrocket.com/)
- [ELK Stack](https://www.elastic.co/)

---

## 🔄 CI/CD Pipeline

### GitHub Actions

**`.github/workflows/deploy.yml`:**

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r backend/requirements.txt
      - run: python -m pytest backend/tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: vercel/action@master
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-args: '--prod'
```

---

## 🎯 Roadmap Post-Deployment

### Week 1-2: Stabilización
- [ ] Monitorear logs
- [ ] Ajustar rate limits
- [ ] Optimizar queries DB

### Week 3-4: Funcionalidades
- [ ] Implementar media download
- [ ] Agregar respuestas automáticas
- [ ] Dashboard de mensajes

### Month 2: Scale
- [ ] Load testing
- [ ] Multi-region deployment
- [ ] Backup automation

---

## 📞 Support Contacts

- **Meta Support:** https://developers.facebook.com/support
- **Vercel Support:** https://vercel.com/help
- **Backend Issues:** Ver logs + check `TROUBLESHOOTING_JSON_ERROR.md`

---

**Última actualización:** 2025-01-15
