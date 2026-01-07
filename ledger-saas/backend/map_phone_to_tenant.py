"""Map phone_number_id to tenant via Channel"""
import os
from app.db import SessionLocal
from app.models import Tenant, Channel

db = SessionLocal()
phone_id = os.environ.get('META_WA_PHONE_NUMBER_ID')

if not phone_id:
    print("❌ META_WA_PHONE_NUMBER_ID no está configurado")
    exit(1)

# Get first tenant
tenant = db.query(Tenant).first()
if not tenant:
    print("❌ No hay tenant en la base de datos")
    exit(1)

# Update tenant phone_number_id
tenant.phone_number_id = phone_id

# Check if Channel already exists
existing_channel = db.query(Channel).filter_by(
    provider='meta',
    kind='whatsapp',
    external_id=phone_id,
    tenant_id=tenant.id
).first()

if not existing_channel:
    # Create new channel
    channel = Channel(
        tenant_id=tenant.id,
        provider='meta',
        kind='whatsapp',
        external_id=phone_id
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    print(f"✅ Created Channel id={channel.id}")
else:
    print(f"✅ Channel already exists id={existing_channel.id}")

db.commit()
print(f"✅ Mapped phone_number_id {phone_id} -> tenant {tenant.id} ({tenant.name})")
db.close()
