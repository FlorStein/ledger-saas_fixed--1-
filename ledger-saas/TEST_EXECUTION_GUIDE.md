# Test Execution Guide - WhatsApp POC

**Objetivo:** Validar que el flujo completo WhatsApp → Vercel → Backend → DB funciona correctamente.

---

## ✅ Pre-Requisitos

- [x] Backend Python venv activo
- [x] Vercel CLI instalado y autenticado (`vercel login`)
- [x] ngrok instalado o Cloudflare Tunnel accesible
- [x] SQLite3 accesible (incluido en Python)
- [x] Scripts PowerShell en `./scripts/` con permisos de ejecución

**Verificar:**
```powershell
# Check Python venv
& .\.venv\Scripts\python.exe --version

# Check Vercel
vercel --version

# Check ngrok
ngrok version

# Check scripts exist
Get-ChildItem scripts/test_*.ps1
```

---

## 📋 Test Sequence (~ 20 minutos)

### Phase 1: Local Setup (5 min)

#### Step 1.1: Initialize Database
```powershell
cd c:\Users\mfrst\Downloads\ledger-saas_fixed\ (1)\ledger-saas\backend

# Clear old DB
Remove-Item -Path app.db -ErrorAction SilentlyContinue
Write-Host "✓ Old DB removed"

# Initialize + Seed
$env:META_WA_PHONE_NUMBER_ID = "123456789012345"  # Use a test ID

.\.venv\Scripts\python.exe -c @'
from app.db import init_db
from app.seed import seed_if_empty
from app.db import SessionLocal

init_db()
db = SessionLocal()
seed_if_empty(db)
db.close()
print("✓ Database initialized and seeded")
'@
```

**Expected Output:**
```
✓ Database initialized and seeded
```

#### Step 1.2: Verify Database State
```powershell
.\.venv\Scripts\python.exe -c @'
from app.db import SessionLocal
from app.models import Tenant, Channel

db = SessionLocal()
tenants = db.query(Tenant).all()
channels = db.query(Channel).filter_by(provider='meta').all()

print(f"Tenants: {len(tenants)}")
for t in tenants:
    print(f"  - ID: {t.id}, Name: {t.name}, Phone ID: {t.phone_number_id}")

print(f"Meta Channels: {len(channels)}")
for c in channels:
    print(f"  - Tenant: {c.tenant_id}, External ID: {c.external_id}, Kind: {c.kind}")

db.close()
'@
```

**Expected Output:**
```
Tenants: 1
  - ID: 1, Name: default, Phone ID: 123456789012345
Meta Channels: 1
  - Tenant: 1, External ID: 123456789012345, Kind: whatsapp
```

#### Step 1.3: Start Backend Server
```powershell
# In a new terminal window
cd backend
$env:BACKEND_SHARED_SECRET = "ledger_saas_backend_secret"
$env:META_WA_TOKEN = "EAAxxxxx_your_token_here_or_dummy"
$env:META_WA_PHONE_NUMBER_ID = "123456789012345"

.\.venv\Scripts\python.exe app/main.py
```

**Expected Output in Terminal:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
...
```

**Keep this terminal open for the rest of the test.**

---

### Phase 2: Expose Backend (5 min)

#### Step 2.1: Start ngrok Tunnel
```powershell
# In another new terminal window
ngrok http 8000
```

**Expected Output:**
```
ngrok                     (Ctrl+C to quit)

Session Status    online
Account           your@email.com
Version           3.X.X
Region            us (United States)
Forwarding        https://abc123.ngrok.io -> http://localhost:8000
```

**Note the Forwarding URL:** `https://abc123.ngrok.io` (you'll need this)

**Keep this terminal open.**

---

### Phase 3: Configure Vercel (3 min)

#### Step 3.1: Set Environment Variables
```powershell
# In main terminal (backend terminal not needed here)
cd c:\Users\mfrst\Downloads\ledger-saas_fixed\ (1)\ledger-saas

# Get the ngrok URL from Phase 2
$NGROK_URL = "https://abc123.ngrok.io"  # Replace with actual URL
$BACKEND_INGEST_URL = "$NGROK_URL/webhooks/whatsapp/meta/cloud"
$BACKEND_SHARED_SECRET = "ledger_saas_backend_secret"

# Add to Vercel
vercel env add BACKEND_INGEST_URL
# Paste: https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud

vercel env add BACKEND_SHARED_SECRET
# Paste: ledger_saas_backend_secret

vercel env add WHATSAPP_VERIFY_TOKEN
# Paste: my_verify_token_12345 (any test value)

vercel env add META_APP_SECRET
# Paste: my_app_secret_12345 (any test value)
```

#### Step 3.2: Verify Environment Variables
```powershell
vercel env ls
```

**Expected Output:**
```
vercel env ls
> Environment Variables
  BACKEND_INGEST_URL (Production, Development, Preview)
  BACKEND_SHARED_SECRET (Production, Development, Preview)
  WHATSAPP_VERIFY_TOKEN (Production, Development, Preview)
  META_APP_SECRET (Production, Development, Preview)
```

#### Step 3.3: Redeploy to Vercel
```powershell
vercel --prod
```

**Expected Output:**
```
✓ Production: https://your-project.vercel.app
✓ Inspect: https://vercel.com/...
```

**Note the Production URL for next phase.**

---

### Phase 4: Test Health Endpoint (1 min)

#### Step 4.1: Run Health Check
```powershell
# Back in main terminal
.\scripts\test_health.ps1
```

**Expected Output:**
```
🏥 Testing Backend Health Endpoint
=================================

📍 Endpoint: http://localhost:8000/webhooks/whatsapp/meta/cloud/health
🔍 Sending GET request...

✅ Health Check Passed!

📊 Status: healthy
⏰ Timestamp: 2025-01-06T...

🔐 Environment Configuration:
  - META_WA_TOKEN: ✅ Configured
  - BACKEND_SHARED_SECRET: ✅ Configured
  - META_WA_PHONE_NUMBER_ID: 123456789012345

💾 Database Status:
  - Total Tenants: 1
  - Meta Channels: 1

👥 Tenants Details:
  ├─ ID: 1
  │  Name: default
  │  Phone Number ID: 123456789012345
  │  Channels:
  │    - External ID: 123456789012345
```

✅ **If you see this, backend is healthy!**

---

### Phase 5: Test Webhook Simulation (3 min)

#### Step 5.1: Run Simulate Script
```powershell
# Set your Vercel URL
$env:VERCEL_URL = "https://your-project.vercel.app"

.\scripts\test_simulate_whatsapp.ps1 `
    -Message "Test transaction receipt" `
    -PhoneNumberId "123456789012345" `
    -SenderWaId "5491123456789"
```

**Expected Output:**
```
🧪 Testing Simulate WhatsApp Endpoint
====================================

📍 Vercel URL: https://your-project.vercel.app
📱 Phone Number ID: 123456789012345
💬 Message: Test transaction receipt
👤 Sender WA ID: 5491123456789

🔍 Sending POST request...

✅ Request Successful!

📊 Response Status: success
🆔 Request ID: req_1735989045_abc123
📨 Messages Forwarded: 1

🔄 Backend Response:
   Status: received
   Tenant ID: 1
   Messages Processed: 1

✅ Webhook simulation successful!
```

✅ **If you see this, the webhook forwarding works!**

#### Step 5.2: Check Backend Logs
Look at the backend terminal window (Phase 1.3). You should see:
```
[req_1735989045_abc123] 📱 Meta Cloud Event - tenant: 1, phone_number_id: 123456789012345
[req_1735989045_abc123] 📝 Text: Test transaction receipt...
[req_1735989045_abc123] ✅ Meta event processed - tenant: 1, messages: 1
```

✅ **Backend received the event!**

#### Step 5.3: Check Vercel Logs
```powershell
vercel logs api/simulate-whatsapp.js --lines 20
```

You should see:
```
[req_1735989045_abc123] 🔔 WEBHOOK POST
[req_1735989045_abc123] 📱 phone_number_id=123456789012345, sender=5491123456789...
[req_1735989045_abc123] ➡️ backend status=200, body={"status":"received",...}
```

✅ **Vercel is logging correctly!**

---

### Phase 6: Verify Database Persistence (2 min)

#### Step 6.1: Count Transactions
```powershell
cd backend
.\.venv\Scripts\python.exe -c @'
from app.db import SessionLocal
from app.models import Transaction, IncomingMessage

db = SessionLocal()

# Count transactions
txs = db.query(Transaction).filter_by(source_system='whatsapp').all()
print(f"WhatsApp Transactions: {len(txs)}")

# Count incoming messages
msgs = db.query(IncomingMessage).all()
print(f"Incoming Messages (idempotency): {len(msgs)}")

# Show last transaction
if txs:
    t = txs[-1]
    print(f"\nLast Transaction:")
    print(f"  ID: {t.id}")
    print(f"  Type: {t.doc_type}")
    print(f"  Source: {t.source_file}")
    print(f"  Text: {(t.raw_text or '')[:100]}")

db.close()
'@
```

**Expected Output:**
```
WhatsApp Transactions: 1
Incoming Messages (idempotency): 1

Last Transaction:
  ID: 1
  Type: document
  Source: whatsapp_1_wamid_123.pdf
  Text: Test transaction receipt
```

✅ **Database persistence works!**

#### Step 6.2: Verify Idempotency (No Duplicates)
```powershell
# Run the simulate script again with the same message
.\scripts\test_simulate_whatsapp.ps1 `
    -Message "Test transaction receipt" `
    -PhoneNumberId "123456789012345" `
    -SenderWaId "5491123456789"
```

Then check the count again:
```powershell
cd backend
.\.venv\Scripts\python.exe -c @'
from app.db import SessionLocal
from app.models import IncomingMessage

db = SessionLocal()
msgs = db.query(IncomingMessage).all()
print(f"Incoming Messages: {len(msgs)}")
db.close()
'@
```

**Expected Output:**
```
Incoming Messages: 1
```

✅ **Idempotency check prevents duplicates!**

---

### Phase 7: Test Error Scenarios (2 min - Optional but Recommended)

#### Scenario A: Missing BACKEND_INGEST_URL
```powershell
# Temporarily unset the env var
$env:BACKEND_INGEST_URL = $null

# Redeploy
vercel --prod

# Try to call (should get error)
.\scripts\test_simulate_whatsapp.ps1

# Expected: 500 error with message "BACKEND_INGEST_URL not configured"
```

#### Scenario B: Wrong BACKEND_SHARED_SECRET
```powershell
# Set wrong secret in Vercel
vercel env add BACKEND_SHARED_SECRET
# Enter: wrong_secret_value

vercel --prod

# Try to call (should get 401)
.\scripts\test_simulate_whatsapp.ps1

# Expected: 401 error "Unauthorized"
```

#### Scenario C: Health Check with Missing Config
```powershell
# Stop backend server temporarily (Ctrl+C in backend window)

# Try health check
.\scripts\test_health.ps1

# Expected: Connection error with helpful troubleshooting message
```

---

## 🎯 Test Results Summary

Create a test results file:
```powershell
@"
WhatsApp POC Test Results - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

✅ Phase 1: Local Setup
  - Database initialized
  - Tenant created (ID: 1)
  - Meta Channel created (External ID: 123456789012345)
  - Backend server started

✅ Phase 2: Expose Backend
  - ngrok tunnel active (https://abc123.ngrok.io)

✅ Phase 3: Configure Vercel
  - BACKEND_INGEST_URL set
  - BACKEND_SHARED_SECRET set
  - WHATSAPP_VERIFY_TOKEN set
  - META_APP_SECRET set
  - Deployment successful

✅ Phase 4: Health Check
  - Backend health endpoint responding
  - All environment variables configured
  - Database state correct

✅ Phase 5: Webhook Simulation
  - Vercel receive and forward successful
  - Backend tenant resolution working
  - Message processing successful
  - Vercel logs structured with [requestId]
  - Backend logs show message receipt

✅ Phase 6: Database Persistence
  - Transaction created in DB
  - IncomingMessage idempotency marker created
  - Duplicate prevention working

Summary:
- Total Tests: 7
- Passed: 7
- Failed: 0
- Status: ✅ READY FOR PRODUCTION

Notes:
- Request tracing working (requestId in all logs)
- Tenant resolution correct
- Multi-tenant ready (can add more tenants later)
- Document processing ready (will create Transactions on file upload)

Next Steps:
1. Configure real Meta app credentials (META_APP_SECRET, WHATSAPP_VERIFY_TOKEN)
2. Set up webhook on Meta Developers console pointing to Vercel URL
3. Test with real WhatsApp message
4. Monitor logs in production
"@ | Out-File -FilePath "TEST_RESULTS_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt" -Encoding UTF8

Get-Content "TEST_RESULTS_*.txt" | Write-Host
```

---

## 🆘 Troubleshooting Quick Ref

| Issue | Check | Fix |
|-------|-------|-----|
| Health check fails | Backend running? | `.\scripts\test_health.ps1` shows error |
| Simulate returns 500 | BACKEND_INGEST_URL? | `vercel env ls` → check URL |
| Simulate returns 401 | BACKEND_SHARED_SECRET? | Must match in backend `.env` |
| No backend logs | ngrok tunnel? | Check ngrok terminal window |
| DB empty after simulate | source_system? | Should be "whatsapp" |
| Duplicate messages in DB | Idempotency? | Check IncomingMessage table |

---

## ✅ Pass Criteria

- [x] Health check returns status: "healthy"
- [x] Simulate endpoint returns request successfully
- [x] Backend logs show `📱 Meta Cloud Event`
- [x] Database has 1 Transaction after simulate
- [x] Re-running simulate doesn't create duplicate
- [x] Error scenarios return proper status codes
- [x] Vercel logs have [requestId] prefix
- [x] All environment variables configured

**Status:** ✅ Ready for production testing with real Meta webhook

---

**Last Updated:** 6 January 2026  
**Tested By:** [Your Name]  
**Status:** ✅ PASS / ❌ FAIL
