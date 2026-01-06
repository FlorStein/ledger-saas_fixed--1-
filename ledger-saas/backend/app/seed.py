from sqlalchemy.orm import Session
from .models import Tenant, User, Sale, Channel
from .auth import hash_password
import os

SEED_SALES = os.getenv("SEED_SALES", "false").lower() in ("1", "true", "yes", "y")

def seed_if_empty(db: Session):
    if db.query(Tenant).count() > 0:
        return

    t = Tenant(name="Cliente Demo")
    db.add(t)
    db.commit()
    db.refresh(t)

    owner = User(
        tenant_id=t.id,
        email="owner@demo.com",
        password_hash=hash_password("demo123"),
        role="owner",
    )
    admin = User(
        tenant_id=t.id,
        email="admin@demo.com",
        password_hash=hash_password("demo123"),
        role="admin",
    )
    db.add_all([owner, admin])

    # Canal demo (para enrutar webhooks por tenant)
    ch = Channel(tenant_id=t.id, kind="whatsapp", provider="twilio", external_id="sandbox", label="WhatsApp Sandbox")
    db.add(ch)

    # Canal Meta si está configurado
    meta_phone_number_id = os.getenv("META_WA_PHONE_NUMBER_ID", "")
    if meta_phone_number_id:
        ch_meta = Channel(tenant_id=t.id, kind="whatsapp", provider="meta", external_id=meta_phone_number_id, label="Meta Cloud API")
        db.add(ch_meta)
        t.phone_number_id = meta_phone_number_id
        db.add(t)

    # Ventas inventadas (solo si SEED_SALES=true)
    if SEED_SALES:
        sales = [
            Sale(tenant_id=t.id, datetime="2025-12-29T10:35:00", amount=13300, currency="ARS",
                 description="Art. librería", customer_name="Maria Florencia Rojas Steinfeld",
                 customer_cuit="27999999999", customer_phone="+5491234567890", external_ref="VENTA001"),
            Sale(tenant_id=t.id, datetime="2025-12-29T09:00:00", amount=38000, currency="ARS",
                 description="Servicio", customer_name="Maria de la Paz Vespignani",
                 customer_cuit="28888888888", customer_phone="+5491122334455", external_ref="VENTA002"),
        ]
        db.add_all(sales)
    
    db.commit()
