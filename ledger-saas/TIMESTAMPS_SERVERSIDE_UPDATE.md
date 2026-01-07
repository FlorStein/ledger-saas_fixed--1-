# Actualización: Timestamps Server-Side con func.now()

## ✅ Cambios Completados

### TimestampMixin Mejorado
```python
class TimestampMixin:
    """Mixin para agregar created_at y updated_at a modelos.
    
    Usa server_default=func.now() para consistencia en entornos multi-worker.
    La BD es responsable de los timestamps, no la aplicación.
    """
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

### Modelos con TimestampMixin (8 en total)
✅ **Tenant**  
✅ **User** (agregado)  
✅ **Counterparty**  
✅ **Sale** (agregado)  
✅ **Transaction**  
✅ **Channel**  
✅ **WhatsAppEvent**  
✅ **IncomingMessage**  

---

## 🔑 Por Qué esto es Mejor para Producción

| Aspecto | Antes | Ahora |
|--------|-------|-------|
| **Default** | `default=datetime.utcnow` (Python) | `server_default=func.now()` (BD) |
| **Tipo** | `DateTime` (sin zona) | `DateTime(timezone=True)` (UTC) |
| **Update** | `onupdate=datetime.utcnow` | `onupdate=func.now()` |
| **Multi-worker** | ❌ Inconsistente (cada worker su hora) | ✅ Consistente (BD es fuente única) |
| **Timezone** | ❌ Naive (sin zona) | ✅ UTC explícito |

### Ventajas de `func.now()`
1. **BD es la fuente única de verdad** - todos los workers usan el mismo reloj
2. **Timezone-aware** - `DateTime(timezone=True)` almacena `TIMESTAMP WITH TIME ZONE`
3. **Sincronización automática** - no depende del reloj de la app
4. **Exactitud** - SQLite usa `CURRENT_TIMESTAMP` (UTC)

---

## 🧪 Verificación Rápida

### 1. Borrar DB vieja y reiniciar backend
```powershell
cd backend
Remove-Item app.db -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Esperar a que se cree el schema
Deberías ver en los logs:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
✅ Database initialized (TimestampMixin columns created)
```

### 3. Verificar que los campos tengan defaults
```powershell
# En otra terminal
$health = Invoke-RestMethod http://127.0.0.1:8000/webhooks/whatsapp/meta/cloud/health
$health.database.tenants[0] | Select-Object created_at, updated_at | ConvertTo-Json
```

**Output esperado:**
```json
{
  "created_at": "2026-01-06T10:30:45.123456+00:00",
  "updated_at": "2026-01-06T10:30:45.123456+00:00"
}
```

### 4. Verificar que `updated_at` cambia en updates
```powershell
# Crear una transacción
$body = @{
    tenant_id = 1
    phone_number_id = "123456789012345"
    payload = @{
        entry = @(@{
            changes = @(@{
                value = @{
                    messages = @(@{
                        id = "wamid.test_$(Get-Random)"
                        from = "5491123456789"
                        type = "text"
                        text = @{ body = "Test" }
                        timestamp = [int]([DateTime]::UtcNow.Subtract([DateTime]::UnixEpoch).TotalSeconds)
                    })
                    metadata = @{
                        phone_number_id = "123456789012345"
                    }
                }
            })
        })
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/webhooks/whatsapp/meta/cloud" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -Headers @{"Authorization" = "Bearer ledger_saas_backend_secret"}

# Leer transaction
python -c "
from app.db import SessionLocal
from app.models import Transaction
db = SessionLocal()
tx = db.query(Transaction).order_by(Transaction.id.desc()).first()
if tx:
    print(f'created_at: {tx.created_at}')
    print(f'updated_at: {tx.updated_at}')
db.close()
"
```

---

## 📊 Schema en SQLite

Después de `func.now()`, el schema lucirá así:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    ...
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);

-- Nota: SQLite usa CURRENT_TIMESTAMP (UTC)
-- Para PostgreSQL/MySQL en prod, sería TIMESTAMP WITH TIME ZONE
```

---

## 🔗 Aplicaciones Importantes

### Auditoría: Quién hizo qué y cuándo
```sql
SELECT 
  id,
  email,
  role,
  is_active,
  created_at,
  updated_at,
  (julianday(updated_at) - julianday(created_at)) * 24 * 60 as minutos_activos
FROM users
ORDER BY created_at DESC
```

### Detección de Cambios
```sql
SELECT 
  id,
  display_name,
  created_at,
  updated_at,
  CASE 
    WHEN created_at = updated_at THEN 'Sin cambios'
    ELSE 'Modificado ' || 
          CAST(ROUND((julianday('now') - julianday(updated_at)) * 24 * 60) as INTEGER) || ' minutos atrás'
  END as estado
FROM counterparties
```

### Historial de Ventas
```sql
SELECT 
  s.id,
  s.amount,
  s.status,
  s.created_at,
  s.updated_at,
  ROUND((julianday(s.updated_at) - julianday(s.created_at)) * 24, 2) as horas_hasta_cierre
FROM sales s
WHERE s.status = 'matched'
ORDER BY s.updated_at DESC
```

---

## 🚀 Configuración para Otros Dialectos SQL

Si en futuro migrás de SQLite a PostgreSQL/MySQL:

### PostgreSQL (con timezone)
```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    server_default=func.now(),  # usa CURRENT_TIMESTAMP
    nullable=False
)
```

### MySQL
```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    server_default=func.utc_timestamp(),  # MySQL
    nullable=False
)
```

SQLAlchemy maneja la traducción automáticamente. ✅

---

## ⚠️ Importante: DB Reset Requerido

Porque `func.now()` es un `server_default`, SQLite necesita recrear las tablas:

```powershell
cd backend

# Opción A: Borrar y dejar que init_db() recree
Remove-Item app.db -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Opción B: Script manual
.\.venv\Scripts\python.exe -c "
from app.db import init_db, SessionLocal, Base, engine
from app.seed import seed_if_empty
import os

if os.path.exists('app.db'):
    os.remove('app.db')

Base.metadata.create_all(engine)
db = SessionLocal()
seed_if_empty(db)
db.close()
print('✅ DB reiniciada con func.now() defaults')
"
```

---

## 📋 Próximos Pasos Opcionales

1. **Soft Deletes** - Agregar `deleted_at` para auditoría completa
2. **Eventos de Auditoría** - Crear tabla `audit_log` con `user_id`, `table_name`, `action`, `timestamp`
3. **Migrations con Alembic** - Para prod con múltiples BD
4. **Índices en Timestamps** - Para queries rápidas:
   ```sql
   CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
   CREATE INDEX idx_users_updated_at ON users(updated_at DESC);
   ```

---

**Status:** ✅ TimestampMixin ahora es robusto para multi-worker en producción  
**Cambios:** 8 modelos con `server_default=func.now()` + `DateTime(timezone=True)`  
**BD Reset:** Requerido (ejecutar pasos arriba)
