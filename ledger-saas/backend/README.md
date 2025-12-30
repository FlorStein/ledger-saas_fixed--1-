# Ledger SaaS (POC)

POC multi-tenant para:
- Recepción de comprobantes (web upload + webhook WhatsApp opcional)
- Extracción básica
- Base de contrapartes por tenant
- Conciliación comprobante ↔ venta
- Frontend mínimo para ver y operar

## Requisitos
- Python 3.11+
- Node 18+

## Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# mac/linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # mac/linux

uvicorn app.main:app --reload
```

Demo login:
- owner@demo.com / demo123

## Frontend
```bash
cd frontend
npm install
npm run dev
```

## WhatsApp (POC)
Este repo incluye endpoints para integrar *oficialmente* con:
- Twilio WhatsApp Sandbox (webhook /webhooks/whatsapp/twilio)
- Meta Cloud API (webhook /webhooks/whatsapp/meta)

Para probar webhooks desde tu máquina necesitás exponer localhost (ngrok / Cloudflare Tunnel).
