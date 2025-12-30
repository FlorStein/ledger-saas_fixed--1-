# 🗺️ ROADMAP - WhatsApp Integration Future Features

Estado actual: **MVP completado** ✅

---

## 📋 Roadmap Overview

```
Phase 1: MVP (COMPLETADO ✅)
├─ GET verification
├─ POST HMAC validation
├─ Multi-tenant routing
├─ Bearer token auth
└─ Contact/message/status processing

Phase 2: Media & OCR Integration (PRÓXIMO 🔄)
├─ Download media from Meta
├─ OCR extraction
├─ Auto-ingest a matching algorithm
└─ Response messages

Phase 3: Advanced Features (FUTURO 📅)
├─ Message templates
├─ Rate limiting & throttling
├─ Webhook retry logic
├─ Media caching
└─ Analytics dashboard

Phase 4: Enterprise (ROADMAP 🎯)
├─ E2E encryption
├─ Audit logging
├─ Compliance reporting
├─ Multi-region deployment
└─ Custom workflows
```

---

## 🔄 Phase 2: Media & OCR Integration

**Objetivo:** Permitir que usuarios envíen recibos/comprobantes por WhatsApp y se procesen automáticamente.

### 2.1 Media Download

**Timeline:** 2-3 semanas  
**Complexity:** Medium  
**Priority:** P0

**Descripción:**
```
User sends document/image via WhatsApp
    ↓
Meta Cloud API webhook con media_id
    ↓
Vercel extracts media_id
    ↓
Backend fetch media URL via Graph API
    ↓
Download PDF/PNG
    ↓
Save to /uploads
```

**Implementación:**

```python
# backend/app/ingest.py (nueva función)

async def download_media_from_meta(
    media_id: str,
    media_type: str,  # image, document, etc
    access_token: str,
    tenant_id: str
) -> str:
    """
    Descarga media de Meta Graph API
    
    Returns:
        Path a archivo local guardado
    """
    # 1. Get media URL from Meta
    url = f"https://graph.instagram.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Get media details (URL, mime type, etc)
    response = await httpx.get(url, headers=headers)
    media_data = response.json()
    
    # 3. Download actual file
    file_url = media_data["url"]
    file_response = await httpx.get(file_url)
    
    # 4. Save locally
    filename = f"{tenant_id}_{media_id}_{datetime.now().timestamp()}"
    file_path = f"uploads/{filename}"
    
    with open(file_path, "wb") as f:
        f.write(file_response.content)
    
    return file_path
```

**Cambios necesarios:**
- Agregar `access_token` a env vars
- Agregar Media Upload permission en Meta Dashboard
- Guardar media en `/uploads`
- Linkear media con transaction en DB

---

### 2.2 OCR Extraction Mejorado

**Timeline:** 1 semana  
**Complexity:** Low  
**Priority:** P0

**Descripción:**
Sistema OCR existente ya funciona, mejorar para WhatsApp documents:

```python
# backend/app/ingest.py (mejorado)

async def extract_receipt_from_whatsapp(
    file_path: str,
    media_type: str,
    tenant_id: str
) -> dict:
    """
    Extract receipt data using OCR
    
    Handles:
    - PDF (pdfplumber)
    - PNG/JPG (pytesseract)
    - GIF, WebP (convert first)
    """
    
    # 1. Validar formato
    if media_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise ValueError(f"Unsupported media type: {media_type}")
    
    # 2. Convertir a formato estándar si es necesario
    if media_type == "image/webp":
        file_path = convert_webp_to_png(file_path)
    
    # 3. Extraer texto
    if media_type == "application/pdf":
        text_data = extract_from_pdf(file_path)
    else:
        text_data = extract_from_image(file_path)
    
    # 4. Parse campos
    receipt_data = {
        "date": parse_date(text_data),
        "amount": parse_amount(text_data),
        "vendor": parse_vendor(text_data),
        "category": parse_category(text_data),
        "items": parse_items(text_data),
        "confidence": calculate_confidence(text_data),
    }
    
    return receipt_data
```

**Cambios necesarios:**
- Manejar formatos adicionales (WebP, GIF)
- Mejorar regex para más tipos de recibos
- Agregar confidence scoring
- Tests para diferentes formatos

---

### 2.3 Auto-Ingest to Matching

**Timeline:** 1 semana  
**Complexity:** Low  
**Priority:** P1

**Descripción:**
```python
# backend/app/routers/whatsapp.py (modificado)

async def process_whatsapp_message(message_data):
    """
    Process WhatsApp message:
    1. Extract text/document
    2. If document → download media
    3. Extract data via OCR
    4. Auto-match against transactions
    5. Create counterparty if needed
    """
    
    if message_data.type == "document":
        # 1. Download document
        file_path = await download_media_from_meta(...)
        
        # 2. OCR
        receipt_data = await extract_receipt_from_whatsapp(...)
        
        # 3. Auto-match
        matches = await match_receipt_to_transaction(
            receipt_data,
            tenant_id
        )
        
        # 4. Create sale/transaction
        if matches:
            await create_linked_transaction(matches[0])
        else:
            # Mark for manual review
            await flag_for_review(receipt_data)
```

---

### 2.4 Response Messages

**Timeline:** 1 semana  
**Complexity:** Medium  
**Priority:** P1

**Descripción:**
```python
# backend/app/whatsapp_responder.py (nuevo)

async def send_whatsapp_message(
    to_number: str,
    message_type: str,  # "text", "template", "document"
    content: dict,
    access_token: str,
    phone_number_id: str
):
    """
    Enviar respuesta via WhatsApp
    
    Ejemplos:
    - Confirmación de recepción
    - Categoría detectada
    - Requerimiento de más info
    - Error si OCR falló
    """
    
    url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": message_type,
    }
    
    if message_type == "text":
        payload["text"] = {"body": content["body"]}
    
    elif message_type == "template":
        # Usar message templates de Meta
        payload["template"] = {
            "name": content["template_name"],
            "language": {"code": "es_AR"},
            "parameters": {"body": {"parameters": content["params"]}}
        }
    
    elif message_type == "document":
        payload["document"] = {
            "link": content["url"],
            "filename": content["filename"]
        }
    
    response = await httpx.post(url, json=payload, headers=headers)
    return response.json()
```

**Cambios necesarios:**
- Crear message templates en Meta Dashboard
- Implementar response logic
- Agregar access_token para sending
- Tests de respuestas

---

## 📊 Phase 3: Advanced Features

**Timeline:** 1-2 meses  
**Complexity:** High  
**Priority:** P2

### 3.1 Message Templates

Meta requiere pre-registrar templates para respuestas.

**Templates sugeridos:**
```
receipt_received:
  Hola {{name}}, recibimos tu comprobante. 
  Categoría: {{category}}
  Monto: {{amount}}

receipt_matched:
  Tu comprobante fue vinculado a:
  {{transaction_date}} - {{amount}} - {{vendor}}

receipt_needs_review:
  Hemos tenido dificultad leyendo tu comprobante.
  Por favor, envía una foto más clara.

daily_summary:
  Resumen de hoy:
  {{transaction_count}} comprobantes procesados
  Total: {{total_amount}}
```

---

### 3.2 Rate Limiting

Proteger contra abuse:

```python
# backend/app/middleware/rate_limit.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 10 requests / minuto por IP
@limiter.limit("10/minute")
@router.post("/webhooks/whatsapp/meta/cloud")
async def receive_meta_cloud_events(...):
    ...
```

**Configuración:**
- 10 requests/minuto por phone number
- 100 requests/minuto por tenant
- 1000 requests/minuto global

---

### 3.3 Webhook Retry Logic

Meta reintentar si backend offline. Mejorar con:

```python
# backend/app/models.py

class WebhookEvent(Base):
    """Track incoming webhooks"""
    __tablename__ = "webhook_events"
    
    id: int = Column(Integer, primary_key=True)
    provider: str = Column(String)  # "whatsapp"
    event_id: str = Column(String, unique=True)
    payload: JSON = Column(JSON)
    status: str = Column(String)  # "received", "processing", "failed"
    retries: int = Column(Integer, default=0)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    processed_at: datetime = Column(DateTime, nullable=True)
```

---

### 3.4 Analytics Dashboard

Dashboard en React para visualizar:
- Mensajes recibidos por día
- Tasa de éxito de OCR
- Categorías más comunes
- Tiempo promedio de procesamiento
- Errores más frecuentes

---

## 🏢 Phase 4: Enterprise

**Timeline:** 3-6 meses  
**Complexity:** Very High  
**Priority:** P3

### 4.1 E2E Encryption

Signal Protocol para mensajes encriptados de extremo a extremo.

---

### 4.2 Audit Logging

Compliance logging para SOC 2, ISO 27001:

```python
class AuditLog(Base):
    """Track all actions for compliance"""
    __tablename__ = "audit_logs"
    
    id: int
    tenant_id: str
    action: str  # "receipt_received", "receipt_matched"
    user_id: str  # si aplica
    resource: str
    timestamp: datetime
    details: JSON
```

---

### 4.3 Multi-region Deployment

Deploy en múltiples regiones para:
- Latencia baja
- Disponibilidad alta
- Data residency compliance

**Regiones sugeridas:**
- Vercel us-east-1 (América del Norte)
- Vercel eu-west-1 (Europa)
- Vercel ap-south-1 (Asia)

---

## 📈 Success Metrics

Antes de avanzar cada fase, validar:

**Phase 1 (MVP):** ✅ COMPLETADO
- [ ] 6/6 tests pasando
- [ ] 0 signature validation errors
- [ ] < 1s response time
- [ ] 100% uptime

**Phase 2 (Media & OCR):**
- [ ] Media download success rate > 95%
- [ ] OCR accuracy > 90%
- [ ] Auto-match rate > 80%
- [ ] User satisfaction > 4/5 estrellas

**Phase 3 (Advanced):**
- [ ] API rate limits working
- [ ] Webhook retry < 1% fail rate
- [ ] Dashboard load time < 2s
- [ ] 50%+ engagement via messages

**Phase 4 (Enterprise):**
- [ ] SOC 2 Type II certified
- [ ] 99.99% uptime
- [ ] Multi-region sync < 100ms
- [ ] Enterprise customer count > 10

---

## 💰 Estimation & Resources

| Phase | Timeline | Dev Hours | Complexity |
|-------|----------|-----------|------------|
| 1 MVP | ✅ Done | ~120 | Medium |
| 2 Media | 4 weeks | ~80 | Medium |
| 3 Advanced | 8 weeks | ~120 | High |
| 4 Enterprise | 16 weeks | ~200 | Very High |
| **TOTAL** | **28 weeks** | **~520** | - |

---

## 🔗 Dependencies & Integrations

**Phase 2 requiere:**
- [ ] Meta Graph API access_token
- [ ] Media upload permission
- [ ] pytesseract + Tesseract OCR binary
- [ ] pdfplumber para PDFs

**Phase 3 requiere:**
- [ ] slowapi package (rate limiting)
- [ ] Message templates registrados en Meta
- [ ] Redis para cache (opcional)

**Phase 4 requiere:**
- [ ] Signal Protocol library
- [ ] Kubernetes para multi-region
- [ ] Data replication setup

---

## 🎯 Decision Points

**Antes de Phase 2:**
- [ ] ¿Usuarios realmente quieren enviar por WhatsApp?
- [ ] ¿OCR accuracy es suficiente para auto-match?
- [ ] ¿Meta Graph API access aprobado?
- [ ] ¿Budget para desarrollo?

**Antes de Phase 3:**
- [ ] ¿Abuse/spam es problema real?
- [ ] ¿Necesitan templates de respuesta?
- [ ] ¿Analytics insights valuable?

**Antes de Phase 4:**
- [ ] ¿Clientes enterprise lo piden?
- [ ] ¿Compliance certifications necesarias?
- [ ] ¿Multi-region worth the cost?

---

## 📞 Communication

Updates:
- [ ] Share roadmap con stakeholders
- [ ] Monthly progress updates
- [ ] Request feedback per phase
- [ ] Adjust based on customer input

---

**Última actualización:** 15 Enero 2025  
**Próxima revisión:** Marzo 2025

