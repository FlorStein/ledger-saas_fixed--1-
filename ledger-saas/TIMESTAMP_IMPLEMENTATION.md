# Implementación de Timestamps - Resumen

## ✅ Completado

### 1. **TimestampMixin Creado**
Se agregó una clase mixin reutilizable en [backend/app/models.py](backend/app/models.py) con:
```python
class TimestampMixin:
    """Mixin para agregar created_at y updated_at a modelos."""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

### 2. **Modelos Actualizado**
Los siguientes modelos ahora heredan de `TimestampMixin`:
- ✅ **Tenant** - timestamps para tracking de tenants
- ✅ **Channel** - timestamps para tracking de canales WhatsApp
- ✅ **Transaction** - timestamps para transacciones recibidas
- ✅ **Counterparty** - timestamps para contrapartes
- ✅ **WhatsAppEvent** - timestamps para eventos de Meta
- ✅ **IncomingMessage** - timestamps para mensajes entrantes

### 3. **Health Endpoint Actualizado**
El endpoint [GET /webhooks/whatsapp/meta/cloud/health](backend/app/routers/whatsapp.py#L315) ahora retorna:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "database": {
    "tenants": [
      {
        "id": 1,
        "name": "default",
        "phone_number_id": "123456789012345",
        "created_at": "2024-01-15T10:00:00.000000",
        "updated_at": "2024-01-15T10:30:45.123456",
        "channels": [
          {
            "external_id": "123456789012345",
            "kind": "whatsapp",
            "created_at": "2024-01-15T10:00:00.000000"
          }
        ]
      }
    ]
  }
}
```

### 4. **Documentación Actualizada**
- ✅ [WHATSAPP_QUICKSTART.md](WHATSAPP_QUICKSTART.md) - secciones renumeradas
- ✅ Sección "0. Preparar la Base de Datos (Dev Only)" - instrucciones de recrear DB
- ✅ Todos los comandos documentados para verificación

---

## 🔧 Pasos de Verificación

### Paso 1: Recrear la Base de Datos
Como no usamos Alembic, el cambio de schema requiere recrear la DB:

```powershell
cd c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas

# Opción 1: Eliminar DB y relanzar backend (automático)
cd backend
if (Test-Path .\app.db) { Remove-Item .\app.db -Force }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Esperar a que termine init_db() y seed_if_empty()
# Deberías ver en los logs: "Database schema created" y "Seeding completed"
```

### Paso 2: Verificar Health Endpoint
```powershell
# En otra terminal
$response = Invoke-RestMethod http://127.0.0.1:8000/webhooks/whatsapp/meta/cloud/health
$response | ConvertTo-Json -Depth 5

# Deberías ver:
# - status: "healthy"
# - tenants[0].created_at: "2024-01-15T10:00:00..."
# - tenants[0].updated_at: "2024-01-15T10:30:45..."
# - channels[0].created_at: "2024-01-15T10:00:00..."
```

### Paso 3: Verificar Persistencia de Timestamps
```powershell
cd backend

# Ver timestamps de tenants
.\.venv\Scripts\python.exe -c "
from app.db import SessionLocal
from app.models import Tenant

db = SessionLocal()
tenant = db.query(Tenant).first()
if tenant:
    print(f'Tenant: {tenant.name}')
    print(f'  created_at: {tenant.created_at.isoformat()}')
    print(f'  updated_at: {tenant.updated_at.isoformat()}')
db.close()
"

# Ver timestamps de channels
.\.venv\Scripts\python.exe -c "
from app.db import SessionLocal
from app.models import Channel

db = SessionLocal()
channels = db.query(Channel).all()
for ch in channels:
    print(f'Channel: {ch.external_id}')
    print(f'  created_at: {ch.created_at.isoformat()}')
    print(f'  updated_at: {ch.updated_at.isoformat()}')
db.close()
"

# Ver timestamps de transacciones
.\.venv\Scripts\python.exe -c "
from app.db import SessionLocal
from app.models import Transaction

db = SessionLocal()
txs = db.query(Transaction).limit(3).all()
for tx in txs:
    print(f'Transaction: {tx.id}')
    print(f'  created_at: {tx.created_at.isoformat()}')
    print(f'  updated_at: {tx.updated_at.isoformat()}')
db.close()
"
```

### Paso 4: Test de Simulación WhatsApp
```powershell
cd c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas

# Configurar túnel (si no está ya activo)
ngrok http 8000
# Copiar URL tipo: https://abc123.ngrok.io

# En otra terminal, configurar Vercel (si no está hecho)
vercel env add BACKEND_INGEST_URL
# Valor: https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud

vercel env add BACKEND_SHARED_SECRET
# Valor: ledger_saas_backend_secret

vercel --prod

# Ejecutar test de simulación
.\scripts\test_simulate_whatsapp.ps1 `
    -VercelUrl "https://tu-vercel-url.vercel.app" `
    -Message "Prueba de timestamps" `
    -PhoneNumberId "123456789012345" `
    -SenderWaId "5491123456789"
```

### Paso 5: Verificar Logs
```powershell
# Backend logs deberían mostrar:
# ✅ "Database schema created" (con created_at, updated_at columns)
# ✅ "📱 Meta Cloud Event - tenant: 1"
# ✅ "✅ WhatsAppEvent persisted" (incluye created_at)

# Vercel logs:
vercel logs api/whatsapp-webhook.js --follow
# Deberías ver: "✅ [requestId] Event forwarded to backend"
```

---

## 📋 Cambios en Detalle

### [backend/app/models.py](backend/app/models.py)
**Imports:**
```python
from datetime import datetime
from sqlalchemy import String, Numeric, Boolean, Integer, ForeignKey, UniqueConstraint, DateTime, func
```

**TimestampMixin:**
```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**Modelos actualizados:**
```python
class Tenant(Base, TimestampMixin):  # ← Agregado TimestampMixin
class Channel(Base, TimestampMixin):  # ← Agregado TimestampMixin
class Transaction(Base, TimestampMixin):  # ← Agregado TimestampMixin
class Counterparty(Base, TimestampMixin):  # ← Agregado TimestampMixin
class WhatsAppEvent(Base, TimestampMixin):  # ← Agregado TimestampMixin
class IncomingMessage(Base, TimestampMixin):  # ← Agregado TimestampMixin
```

### [backend/app/routers/whatsapp.py](backend/app/routers/whatsapp.py#L315-L350)
**Health endpoint ahora retorna timestamps:**
```python
tenants_list = [
    {
        "id": t.id,
        "name": t.name or t.id,
        "phone_number_id": t.phone_number_id or "not_set",
        "created_at": t.created_at.isoformat() if t.created_at else None,  # ← Nuevo
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,  # ← Nuevo
        "channels": [
            {
                "external_id": c.external_id,
                "kind": c.kind or "whatsapp",
                "created_at": c.created_at.isoformat() if c.created_at else None,  # ← Nuevo
            }
            for c in meta_channels if c.tenant_id == t.id
        ]
    }
    for t in tenants
]
```

### [WHATSAPP_QUICKSTART.md](WHATSAPP_QUICKSTART.md)
**Sección 0 (nueva):**
- Instrucciones de cómo recrear DB
- Documentación que crear_at/updated_at se agregaron
- Nota sobre errores de "no such column"

**Secciones renumeradas:**
- Sección 2 → 1: Configurá las variables en Vercel
- Sección 3 → 2: Probá el endpoint de simulación
- Sección 4 → 3: Verificá el health check
- Sección 5 → 4: Probá con Meta real
- Sección 6 → 5: Variables de entorno completas
- Sección 7 → 6: Errores Comunes y Soluciones
- Sección 8 → 7: Comandos útiles

---

## ⚡ Casos de Uso

### Tracking de Cuándo se Recibió una Transacción
```sql
SELECT 
  id, 
  doc_type, 
  amount, 
  created_at,
  DATE(created_at) as dia_recepcion
FROM transactions 
WHERE source_system = 'whatsapp'
ORDER BY created_at DESC
```

### Monitoreo de Cambios en Tenants
```sql
SELECT 
  id, 
  name, 
  created_at,
  updated_at,
  CAST((julianday(updated_at) - julianday(created_at)) * 24 * 60 as INTEGER) as minutos_desde_creacion
FROM tenants
ORDER BY updated_at DESC
```

### Auditoría de Canales
```sql
SELECT 
  c.id,
  t.name as tenant,
  c.external_id,
  c.created_at,
  (SELECT COUNT(*) FROM transactions WHERE source_system = 'whatsapp' AND tenant_id = t.id) as msg_count
FROM channels c
JOIN tenants t ON c.tenant_id = t.id
WHERE c.provider = 'meta'
```

---

## 🚀 Próximos Pasos (Opcional)

Si querés ir más allá:

1. **Migración a Alembic** - Para manejar cambios de schema sin borrar DB
2. **Agregar updated_at a User, Sale, WhatsAppInboundMessage** - Para auditoría completa
3. **Índices en Timestamps** - Para queries más rápidas (`created_at DESC`)
4. **Soft Deletes** - Agregar `deleted_at` para mantener historial

---

## ❓ Troubleshooting

### "SQLAlchemy: no such column: tenants.created_at"
**Causa:** DB vieja sin el schema nuevo
**Solución:**
```powershell
cd backend
Remove-Item app.db -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### "Field 'created_at' has no default"
**Causa:** Cambio de código sin recrear DB
**Solución:** Mismo pasos que arriba (recrear DB)

### Health endpoint retorna None en timestamps
**Causa:** Transacciones antiguas antes del cambio
**Solución:** Borrar DB y usar seed nuevo, o hacer UPDATE SQL manual

---

**Estado:** ✅ Implementación completa y documentada
**Última actualización:** [fecha actual]
**Responsable:** GitHub Copilot
