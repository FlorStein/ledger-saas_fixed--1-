import hmac
import hashlib
import json

# Payload de prueba
payload = {
    "object": "whatsapp_business_account",
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
                                "text": {"body": "Hola, prueba de mensaje"}
                            }
                        ]
                    }
                }
            ]
        }
    ]
}

# Usar el mismo secreto que configuraste en Vercel (META_APP_SECRET)
app_secret = input("Ingresa tu META_APP_SECRET: ")

body_str = json.dumps(payload, separators=(',', ':'))
signature = hmac.new(
    app_secret.encode('utf-8'),
    body_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print("\n✅ Payload generado:")
print(body_str)

print("\n✅ Firma HMAC SHA256:")
print(f"sha256={signature}")

print("\n✅ Comando cURL para probar:")
print(f"curl -X POST https://ledger-saas-fixed-1.vercel.app/api/whatsapp-webhook -H \"Content-Type: application/json\" -H \"x-hub-signature-256: sha256={signature}\" -d '{body_str}'")

# Guardar para usar fácilmente
with open("test_webhook_command.txt", "w") as f:
    f.write(f'curl -X POST https://ledger-saas-fixed-1.vercel.app/api/whatsapp-webhook -H "Content-Type: application/json" -H "x-hub-signature-256: sha256={signature}" -d \'{body_str}\'')

print("\n✅ Comando guardado en: test_webhook_command.txt")
