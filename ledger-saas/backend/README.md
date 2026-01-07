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

### Reset DB (dev)

Cuando cambies modelos SQLAlchemy (añadas columnas, nuevas tablas, etc), necesitás recrear la BD.

**IMPORTANTE:** Estos comandos asumen que estás en el directorio raíz del proyecto (donde está la carpeta `backend/`). Si estás en otra ubicación, primero navegá al proyecto:

```powershell
cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas"
```

#### Con PowerShell (recomendado):
```powershell
cd backend
Remove-Item .\app.db -ErrorAction SilentlyContinue
& .\venv\Scripts\python.exe -c "from app.db import Base, engine, SessionLocal; from app.seed import seed_if_empty; Base.metadata.create_all(bind=engine); db=SessionLocal(); seed_if_empty(db); db.close()"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

#### Con CMD (Windows):
```cmd
cd backend
if exist app.db del app.db
.venv\Scripts\python.exe -c "from app.db import Base, engine, SessionLocal; from app.seed import seed_if_empty; Base.metadata.create_all(bind=engine); db=SessionLocal(); seed_if_empty(db); db.close()"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

#### Con bash (mac/linux):
```bash
cd backend
rm -f app.db
source .venv/bin/activate
python -c "from app.db import Base, engine, SessionLocal; from app.seed import seed_if_empty; Base.metadata.create_all(bind=engine); db=SessionLocal(); seed_if_empty(db); db.close()"
python -m uvicorn app.main:app --reload
```

Este comando:
1. Borra `app.db` vieja
2. Recrea todas las tablas desde los modelos (con `created_at`, `updated_at`, etc)
3. Ejecuta el seed con datos de demo
4. Inicia el backend

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
