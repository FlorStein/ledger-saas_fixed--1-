# 🧪 MANUAL TESTING - cURL Examples

Ejemplos para testear los endpoints manualmente sin Python.

## Setup Previo

```bash
# 1. Estar en raíz del proyecto
cd ledger-saas

# 2. Backend debe estar corriendo
cd backend
python -m uvicorn app.main:app --reload
# → Debe responder en http://localhost:8000

# 3. Vercel dev (opcional, pero recomendado)
cd ledger-saas
vercel dev
# → Debe correr en http://localhost:3000
```

---

## Test 1: GET Verification (Vercel)

Simula que Meta intenta verificar el webhook.

```bash
# Con token CORRECTO
curl -X GET "http://localhost:3000/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=TEST_CHALLENGE_STRING"

# Respuesta esperada:
# TEST_CHALLENGE_STRING

# Con token INCORRECTO
curl -X GET "http://localhost:3000/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=WRONG_TOKEN&hub.challenge=TEST_CHALLENGE_STRING"

# Respuesta esperada:
# Verification token mismatch
```

---

## Test 2: POST con Firma HMAC válida (Vercel)

Necesitas generar una firma HMAC válida. Usa Python para generarla:

```python
# generate_hmac_signature.py
import hmac
import hashlib
import json

# Data to send
payload = {
    "entry": [
        {
            "id": "123456",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "1234567890"
                        },
                        "contacts": [
                            {
                                "profile": {"name": "Test User"},
                                "wa_id": "5511987654321"
                            }
                        ],
                        "messages": [
                            {
                                "from": "5511987654321",
                                "id": "msg_123",
                                "timestamp": "1234567890",
                                "type": "text",
                                "text": {"body": "Hello"}
                            }
                        ]
                    }
                }
            ]
        }
    ]
}

# Secret (must match META_APP_SECRET in Vercel)
app_secret = "your_meta_app_secret_here"

# Generate signature
body_str = json.dumps(payload, separators=(',', ':'))
signature = hmac.new(
    app_secret.encode('utf-8'),
    body_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print("Body:")
print(body_str)
print("\nSignature (header X-Hub-Signature):")
print(f"sha256={signature}")
```

**Ejecutar:**

```bash
python generate_hmac_signature.py
```

**Copiar output y usar en cURL:**

```bash
BODY='{"entry":[{"id":"123456","changes":[{"field":"messages","value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"1234567890","phone_number_id":"1234567890"},"contacts":[{"profile":{"name":"Test User"},"wa_id":"5511987654321"}],"messages":[{"from":"5511987654321","id":"msg_123","timestamp":"1234567890","type":"text","text":{"body":"Hello"}}]}}]}]}'

SIGNATURE="sha256=abc123def456..."

curl -X POST "http://localhost:3000/api/whatsapp-webhook" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature: $SIGNATURE" \
  -d "$BODY"

# Respuesta esperada:
# {"ok":true}
```

---

## Test 3: POST con Firma HMAC inválida (Vercel)

```bash
# Mismo body pero firma incorrecta
BODY='{"entry":...}'
WRONG_SIGNATURE="sha256=wrong_signature_here"

curl -X POST "http://localhost:3000/api/whatsapp-webhook" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature: $WRONG_SIGNATURE" \
  -d "$BODY"

# Respuesta esperada:
# {"detail":"Signature validation failed"}
# HTTP Status: 401
```

---

## Test 4: Backend Health Check

```bash
# Sin autenticación (debe funcionar)
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"ok"}
```

---

## Test 5: Backend Webhook Endpoint (con Bearer Token)

Endpoint: `POST http://localhost:8000/webhooks/whatsapp/meta/cloud`

### Con token CORRECTO

```bash
TOKEN="Bearer ledger_saas_backend_secret"

curl -X POST "http://localhost:8000/webhooks/whatsapp/meta/cloud" \
  -H "Content-Type: application/json" \
  -H "Authorization: $TOKEN" \
  -d '{
    "entry": [{
      "id": "123456",
      "changes": [{
        "field": "messages",
        "value": {
          "messaging_product": "whatsapp",
          "metadata": {
            "display_phone_number": "1234567890",
            "phone_number_id": "1234567890"
          },
          "contacts": [{
            "profile": {"name": "Test User"},
            "wa_id": "5511987654321"
          }],
          "messages": [{
            "from": "5511987654321",
            "id": "msg_123",
            "timestamp": "1234567890",
            "type": "text",
            "text": {"body": "Comprobante adjunto"}
          }]
        }
      }]
    }]
  }'

# Respuesta esperada:
# {"messages_processed":1,"statuses_processed":0,"contacts_processed":1}
```

### Con token INCORRECTO

```bash
WRONG_TOKEN="Bearer wrong_token"

curl -X POST "http://localhost:8000/webhooks/whatsapp/meta/cloud" \
  -H "Content-Type: application/json" \
  -H "Authorization: $WRONG_TOKEN" \
  -d '{"entry":...}'

# Respuesta esperada:
# {"detail":"Unauthorized"}
# HTTP Status: 401
```

### Sin Bearer token

```bash
curl -X POST "http://localhost:8000/webhooks/whatsapp/meta/cloud" \
  -H "Content-Type: application/json" \
  -d '{"entry":...}'

# Respuesta esperada:
# {"detail":"Unauthorized"}
# HTTP Status: 401
```

---

## Test 6: Webhook Completo (Vercel → Backend)

Simula flujo completo:

**Paso 1: Generar firma válida**

```bash
python generate_hmac_signature.py
```

**Paso 2: Enviar POST a Vercel**

```bash
BODY='...'
SIGNATURE="sha256=..."

curl -X POST "http://localhost:3000/api/whatsapp-webhook" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature: $SIGNATURE" \
  -d "$BODY"

# Respuesta esperada (inmediata):
# {"ok":true}
```

**Paso 3: Ver logs de backend**

```bash
# En terminal del backend, deberías ver:
# INFO:     POST /webhooks/whatsapp/meta/cloud HTTP/1.1" 200
# INFO:     Processed message for tenant: ...
```

---

## Advanced Testing

### Test con archivo JSON

**save_test_payload.json:**

```json
{
  "entry": [
    {
      "id": "123456",
      "changes": [
        {
          "field": "messages",
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "1234567890",
              "phone_number_id": "1234567890"
            },
            "contacts": [
              {
                "profile": {"name": "John Doe"},
                "wa_id": "5511987654321"
              }
            ],
            "messages": [
              {
                "from": "5511987654321",
                "id": "msg_1234567890",
                "timestamp": "1234567890",
                "type": "text",
                "text": {"body": "Hola, necesito ayuda con mi recibo"}
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Enviar:**

```bash
curl -X POST "http://localhost:8000/webhooks/whatsapp/meta/cloud" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ledger_saas_backend_secret" \
  -d @save_test_payload.json
```

---

## Batch Testing (Script Bash)

**run_all_tests.sh:**

```bash
#!/bin/bash

echo "🧪 Running manual tests..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_count=0
pass_count=0

run_test() {
    test_count=$((test_count + 1))
    echo -n "[$test_count] $1... "
    
    response=$(eval "$2" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "200" ]] || [[ "$response" == *"ok"* ]]; then
        echo -e "${GREEN}PASS${NC}"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}FAIL${NC}"
        echo "    Response: $response"
    fi
}

# Test 1: Health check
run_test "Health Check" "curl -s http://localhost:8000/health -w '%{http_code}'"

# Test 2: GET verification
run_test "GET Verification" "curl -s http://localhost:3000/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=ledger_saas_verify_123&hub.challenge=TEST -w '%{http_code}'"

# Test 3: Backend endpoint with auth
run_test "Backend Endpoint (with auth)" "curl -s -X POST http://localhost:8000/webhooks/whatsapp/meta/cloud \
  -H 'Authorization: Bearer ledger_saas_backend_secret' \
  -H 'Content-Type: application/json' \
  -d '{}' -w '%{http_code}'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: $pass_count/$test_count tests passed"

if [ $pass_count -eq $test_count ]; then
    echo -e "${GREEN}All tests passed! ✅${NC}"
else
    echo -e "${RED}Some tests failed ❌${NC}"
fi
```

**Ejecutar:**

```bash
bash run_all_tests.sh
```

---

## Debugging con verbose cURL

Ver todo lo que pasa:

```bash
# Ver headers, response, timing
curl -v -X POST "http://localhost:3000/api/whatsapp-webhook" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature: sha256=abc123" \
  -d '{"entry":[...]}'

# Ver solo headers de respuesta
curl -i -X GET "http://localhost:3000/api/whatsapp-webhook?..."

# Ver timing
curl -w "@curl-format.txt" "http://localhost:3000/api/whatsapp-webhook?..."
```

---

## Limpieza

Después de testing manual:

```bash
# Ver qué se creó en la DB
sqlite3 backend/app/ledger.db "SELECT COUNT(*) FROM counterparties;"

# Vaciar DB (⚠️ CUIDADO en producción)
rm backend/app/ledger.db

# O desde SQLite
sqlite3 backend/app/ledger.db "DELETE FROM counterparties; DELETE FROM transactions;"
```

---

**💡 Tip:** Combina estos tests con `vercel logs --prod --follow` para ver qué pasa en producción.

