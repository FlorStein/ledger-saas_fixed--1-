# 🚀 QUICK REFERENCE - WhatsApp POC v1

**Copiar-pegar listo. Modificar solo [VALORES]**

---

## QUICK START (5 min)

```powershell
# Terminal 1: Backend
cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas\backend"
Remove-Item app.db -ErrorAction SilentlyContinue
$env:META_WA_PHONE_NUMBER_ID = "123456789012345"
$env:BACKEND_SHARED_SECRET = "ledger_saas_backend_secret"
$env:META_WA_TOKEN = "dummy_token"

.\.venv\Scripts\python.exe -c @'
from app.db import init_db
from app.seed import seed_if_empty
from app.db import SessionLocal
init_db()
db = SessionLocal()
seed_if_empty(db)
db.close()
'@

.\.venv\Scripts\python.exe app/main.py
```

```powershell
# Terminal 2: Tunnel
ngrok http 8000
# COPY THIS URL: https://abc123.ngrok.io
```

```powershell
# Terminal 3: Vercel Config
cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas"

vercel env add BACKEND_INGEST_URL
# PASTE: https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud

vercel env add BACKEND_SHARED_SECRET
# PASTE: ledger_saas_backend_secret

vercel env add WHATSAPP_VERIFY_TOKEN
# PASTE: test_verify_token_123

vercel env add META_APP_SECRET
# PASTE: test_app_secret_123

vercel --prod
```

```powershell
# Terminal 3: Test
cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas"
.\scripts\test_health.ps1
.\scripts\test_simulate_whatsapp.ps1
```

---

## COMMANDS CHEATSHEET

### Health Check
```powershell
.\scripts\test_health.ps1
```

### Simulate Webhook
```powershell
.\scripts\test_simulate_whatsapp.ps1 -Message "Test" -PhoneNumberId "123456789012345"
```

### Count DB Transactions
```powershell
cd backend
.\.venv\Scripts\python.exe -c @'
from app.db import SessionLocal
from app.models import Transaction
db = SessionLocal()
count = db.query(Transaction).filter_by(source_system="whatsapp").count()
print(f"WhatsApp Transactions: {count}")
db.close()
'@
```

### View Latest Transaction
```powershell
cd backend
.\.venv\Scripts\python.exe -c @'
from app.db import SessionLocal
from app.models import Transaction
db = SessionLocal()
tx = db.query(Transaction).filter_by(source_system="whatsapp").order_by(Transaction.id.desc()).first()
if tx:
    print(f"ID: {tx.id}")
    print(f"Type: {tx.doc_type}")
    print(f"Amount: {tx.amount} {tx.currency}")
    print(f"File: {tx.source_file}")
db.close()
'@
```

### View Vercel Logs
```powershell
vercel logs api/whatsapp-webhook.js --lines 50
vercel logs api/simulate-whatsapp.js --lines 50
```

### Check Env Vars
```powershell
vercel env ls
```

### Redeploy
```powershell
vercel --prod
```

---

## ERROR QUICK FIX

### "BACKEND_INGEST_URL not configured"
```powershell
vercel env add BACKEND_INGEST_URL
# PASTE: https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud
vercel --prod
```

### "401 Unauthorized"
```powershell
# Verify secret matches
cat backend\.env | grep BACKEND_SHARED_SECRET
vercel env ls | grep BACKEND_SHARED_SECRET
# If different, update in Vercel
vercel env add BACKEND_SHARED_SECRET
# PASTE: ledger_saas_backend_secret
vercel --prod
```

### "Health check fails"
```powershell
# Check backend running
# Terminal should show "Uvicorn running on http://127.0.0.1:8000"

# If not, start backend
cd backend
.\.venv\Scripts\python.exe app/main.py
```

### "No backend logs appear"
```powershell
# Check ngrok tunnel active
# Should show "Forwarding ... -> http://localhost:8000"

# Check BACKEND_INGEST_URL points to ngrok URL
vercel env ls | grep BACKEND_INGEST_URL
```

### "Simulate retorna vacío"
```powershell
# Check VERCEL_URL is set
$env:VERCEL_URL = "https://tu-proyecto.vercel.app"

# Or provide manually
.\scripts\test_simulate_whatsapp.ps1 -VercelUrl "https://tu-proyecto.vercel.app"
```

---

## EXPECTED OUTPUTS

### test_health.ps1 ✅
```
🏥 Testing Backend Health Endpoint
✅ Health Check Passed!
📊 Status: healthy
🔐 META_WA_TOKEN: ✅ Configured
💾 Total Tenants: 1
   Meta Channels: 1
```

### test_simulate_whatsapp.ps1 ✅
```
🧪 Testing Simulate WhatsApp Endpoint
✅ Request Successful!
📊 Response Status: success
📨 Messages Forwarded: 1
✅ Webhook simulation successful!
```

### Backend Logs ✅
```
📱 Meta Cloud Event - tenant: 1, phone_number_id: 123456789012345
📝 Text: [mensaje]...
✅ Meta event processed - tenant: 1, messages: 1
```

---

## FILES TO KNOW

| Purpose | File |
|---------|------|
| Setup | [WHATSAPP_START_HERE.md](WHATSAPP_START_HERE.md) |
| Quick start | [WHATSAPP_QUICKSTART.md](WHATSAPP_QUICKSTART.md) |
| Testing | [TEST_EXECUTION_GUIDE.md](TEST_EXECUTION_GUIDE.md) |
| State | [WHATSAPP_POC_STATUS.md](WHATSAPP_POC_STATUS.md) |
| Changes | [WHATSAPP_CHANGES_SUMMARY.md](WHATSAPP_CHANGES_SUMMARY.md) |
| Index | [WHATSAPP_DOCS_INDEX.md](WHATSAPP_DOCS_INDEX.md) |

---

## ARCHITECTURE

```
You (PowerShell)
  ↓
Vercel Edge (Node.js)
  • api/whatsapp-webhook.js (Meta real)
  • api/simulate-whatsapp.js (test)
  ↓
Backend (FastAPI on localhost:8000 via ngrok tunnel)
  • POST /webhooks/whatsapp/meta/cloud
  • GET /webhooks/whatsapp/meta/cloud/health
  ↓
Database (SQLite ./app.db)
  • Transactions
  • IncomingMessages
  • WhatsAppEvents
```

---

## ENV VARS NEEDED

```
Backend (.env):
  BACKEND_SHARED_SECRET=ledger_saas_backend_secret
  META_WA_TOKEN=[token from Meta]
  META_WA_PHONE_NUMBER_ID=123456789012345
  META_APP_SECRET=[from Meta]
  WHATSAPP_VERIFY_TOKEN=[your choice]

Vercel (env):
  BACKEND_INGEST_URL=https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud
  BACKEND_SHARED_SECRET=ledger_saas_backend_secret
  WHATSAPP_VERIFY_TOKEN=[same as backend]
  META_APP_SECRET=[same as backend]
```

---

**Save this file, run QUICK START, done! 🎉**
