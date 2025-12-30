import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .db import Base, engine, SessionLocal
from .seed import seed_if_empty
from .routers import auth, receipts, sales, transactions, chat, whatsapp, export, users

load_dotenv()

app = FastAPI(title="Ledger SaaS (POC)")

Base.metadata.create_all(bind=engine)

SEED_DEMO = os.getenv("SEED_DEMO", "true").lower() in ("1", "true", "yes", "y")

if SEED_DEMO:
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()

# Default includes both localhost and 127.0.0.1 to avoid CORS issues when
# running Vite preview/dev with explicit host.
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(receipts.router)
app.include_router(sales.router)
app.include_router(transactions.router)
app.include_router(chat.router)
app.include_router(whatsapp.router)
app.include_router(export.router)
