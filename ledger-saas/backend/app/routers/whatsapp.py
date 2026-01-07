import os
import tempfile
import requests
import logging
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from datetime import datetime

from ..db import get_db
from ..models import (
    Channel,
    Transaction,
    Counterparty,
    User,
    WhatsAppInboundMessage,
    WhatsAppEvent,
    IncomingMessage,
    Tenant,
)
from ..extract import extract_text_from_pdf, detect_doc, parse_by_type
from .receipts import _resolve_and_match

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)

# Auth para eventos reenviados por Vercel
BACKEND_SHARED_SECRET = os.getenv("BACKEND_SHARED_SECRET", "ledger_saas_backend_secret")

# Meta Cloud API
META_WA_TOKEN = os.getenv("META_WA_TOKEN", "")
META_API_VERSION = os.getenv("META_API_VERSION", "v20.0")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _route_tenant_by_provider(db: Session, provider: str, external_id: str) -> int | None:
    ch = db.query(Channel).filter(Channel.kind == "whatsapp", Channel.provider == provider, Channel.external_id == external_id).first()
    return ch.tenant_id if ch else None


def _resolve_tenant(db: Session, phone_number_id: str | None, fallback_tenant_id: str | None) -> int | None:
    # 1) Header-provided tenant id (from Vercel) wins
    if fallback_tenant_id:
        try:
            return int(fallback_tenant_id)
        except Exception:
            logger.warning(f"⚠️  Invalid tenant id header: {fallback_tenant_id}")

    # 2) Channel lookup (preferred)
    if phone_number_id:
        ch = db.query(Channel).filter(
            Channel.kind == "whatsapp",
            Channel.provider == "meta",
            Channel.external_id == phone_number_id,
        ).first()
        if ch:
            return ch.tenant_id

    # 3) Tenant direct mapping
    if phone_number_id:
        tenant = db.query(Tenant).filter(Tenant.phone_number_id == phone_number_id).first()
        if tenant:
            return tenant.id

    return None

def _message_already_processed(db: Session, tenant_id: int | None, message_id: str) -> bool:
    """Verificar si un mensaje ya fue procesado (idempotencia por message_id)."""
    existing = db.query(IncomingMessage).filter(
        IncomingMessage.message_id == message_id,
        IncomingMessage.tenant_id == tenant_id,
    ).first()
    return existing is not None

def _record_inbound_message(
    db: Session,
    message_id: str,
    sender_wa_id: str | None,
    phone_number_id: str | None,
    tenant_id: int | None,
    msg_type: str | None,
    content: str | None,
    status: str = "received",
) -> IncomingMessage | None:
    """Registrar mensaje entrante en tabla de idempotencia."""
    try:
        inbound = IncomingMessage(
            tenant_id=tenant_id,
            message_id=message_id,
            sender_wa_id=sender_wa_id,
            phone_number_id=phone_number_id,
            msg_type=msg_type,
            content=content,
            created_at=datetime.utcnow().isoformat(),
            status=status,
        )
        db.add(inbound)
        db.commit()
        return inbound
    except Exception as e:
        logger.warning(f"⚠️  Could not record inbound message {message_id}: {str(e)}")
        db.rollback()
        return None

def download_meta_media(media_id: str, token: str = None, version: str = None) -> tuple[bytes, str, str] | None:
    """
    Descargar media desde Meta Cloud API.
    
    Args:
        media_id: ID del media en Meta
        token: META_WA_TOKEN (si es None, usa env)
        version: META_API_VERSION (si es None, usa env o default)
    
    Returns:
        (bytes, filename, content_type) o None si falla
    """
    if not token:
        token = META_WA_TOKEN
    if not version:
        version = META_API_VERSION
    
    if not token:
        logger.error("❌ META_WA_TOKEN not set, cannot download media")
        return None
    
    try:
        # Step 1: Get media URL from Graph API
        url = f"https://graph.facebook.com/{version}/{media_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        logger.info(f"📥 Fetching media URL from {url}")
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        media_url = data.get("url")
        
        if not media_url:
            logger.error(f"❌ No URL in media response: {data}")
            return None
        
        logger.info(f"📥 Got media URL: {media_url[:80]}...")
        
        # Step 2: Download file from URL
        resp = requests.get(media_url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        media_bytes = resp.content
        content_type = resp.headers.get("Content-Type", "application/octet-stream").lower()
        
        # Infer filename from content-type
        filename = f"media_{media_id}"
        if "pdf" in content_type:
            filename += ".pdf"
        elif "jpeg" in content_type or "jpg" in content_type:
            filename += ".jpg"
        elif "png" in content_type:
            filename += ".png"
        else:
            filename += ".bin"
        
        logger.info(f"✅ Downloaded media: {filename} ({len(media_bytes)} bytes, type: {content_type})")
        return media_bytes, filename, content_type
        
    except Exception as e:
        logger.error(f"❌ Error downloading media {media_id}: {str(e)}")
        return None

@router.post("/twilio", response_class=PlainTextResponse)
async def twilio_inbound(request: Request, db: Session = Depends(get_db)):
    """Twilio envía application/x-www-form-urlencoded."""
    form = await request.form()
    from_phone = str(form.get("From") or "")
    to_phone = str(form.get("To") or "sandbox")
    body = str(form.get("Body") or "")
    num_media = int(form.get("NumMedia") or 0)
    media_url = str(form.get("MediaUrl0") or "")

    tenant_id = _route_tenant_by_provider(db, "twilio", "sandbox")
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Channel not configured")

    # POC: si hay media, intentamos descargarlo (requiere SID/Auth Token)
    filename = "whatsapp_message.txt"
    parsed = {"needs_review": True, "parse_confidence": 10}
    text = ""

    if num_media > 0 and media_url:
        sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        token = os.getenv("TWILIO_AUTH_TOKEN", "")
        if not sid or not token:
            # sin credenciales: guardamos la URL como referencia
            filename = "whatsapp_media_url.txt"
            text = f"TWILIO_MEDIA_URL={media_url}"
        else:
            r = requests.get(media_url, auth=(sid, token), timeout=30)
            r.raise_for_status()
            # Twilio media puede ser pdf/jpg. Inferimos por content-type.
            ctype = (r.headers.get("Content-Type") or "").lower()
            ext = "bin"
            if "pdf" in ctype:
                ext = "pdf"
            elif "jpeg" in ctype or "jpg" in ctype:
                ext = "jpg"
            elif "png" in ctype:
                ext = "png"
            filename = f"whatsapp_{tenant_id}_{abs(hash(media_url))}.{ext}"
            path = os.path.join(UPLOAD_DIR, filename)
            with open(path, "wb") as f:
                f.write(r.content)

            if ext == "pdf":
                text = extract_text_from_pdf(path)
                doc_key = detect_doc(text) if text else "unknown"
                parsed = parse_by_type(doc_key, text) if text else parsed
            else:
                # imágenes: OCR/visión pendiente
                parsed = {"source_system":"whatsapp","doc_type":"image","needs_review": True, "parse_confidence": 20}

    tx = Transaction(
        tenant_id=tenant_id,
        source_file=filename,
        source_system="whatsapp",
        doc_type=parsed.get("doc_type","unknown"),
        datetime=parsed.get("datetime"),
        currency=parsed.get("currency","ARS"),
        amount=parsed.get("amount"),
        direction=parsed.get("direction","unknown"),
        operation_id=parsed.get("operation_id"),
        operation_id_type=parsed.get("operation_id_type","unknown"),
        payer_name=parsed.get("payer_name"),
        payer_cuit=parsed.get("payer_cuit"),
        payer_cuit_masked=parsed.get("payer_cuit_masked"),
        payer_bank=parsed.get("payer_bank"),
        payer_account_type=parsed.get("payer_account_type"),
        payer_account_id=parsed.get("payer_account_id"),
        payee_name=parsed.get("payee_name"),
        payee_cuit=parsed.get("payee_cuit"),
        payee_cuit_masked=parsed.get("payee_cuit_masked"),
        payee_bank=parsed.get("payee_bank"),
        payee_account_type=parsed.get("payee_account_type"),
        payee_account_id=parsed.get("payee_account_id"),
        concept=parsed.get("concept") or body[:300] if body else None,
        raw_text=(text[:1900] if text else None),
        needs_review=bool(parsed.get("needs_review", True)),
        parse_confidence=parsed.get("parse_confidence", 10),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    _resolve_and_match(db, tx, tenant_id)

    # Respuesta TwiML simplificada (texto plano; Twilio acepta)
    return "OK"

@router.get("/meta", response_class=PlainTextResponse)
def meta_verify(request: Request):
    """Verificación del webhook (Meta Cloud API)."""
    verify_token = os.getenv("META_WA_VERIFY_TOKEN", "change_me")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == verify_token and challenge:
        return challenge
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/meta", response_class=PlainTextResponse)
async def meta_inbound(request: Request, db: Session = Depends(get_db)):
    """Stub: en producción, parseás el payload Cloud API y descargás media con access token."""
    payload = await request.json()
    # POC: guardar payload en texto para inspección
    tenant_id = _route_tenant_by_provider(db, "meta", os.getenv("META_WA_PHONE_NUMBER_ID","") or "sandbox") or 1
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="meta_webhook.json",
        source_system="whatsapp",
        doc_type="meta_webhook",
        currency="ARS",
        needs_review=True,
        parse_confidence=5,
        raw_text=str(payload)[:1900],
    )
    db.add(tx)
    db.commit()
    return "OK"


# ============================================
# NUEVO: Eventos reenviados por Vercel (Meta Cloud API)
# ============================================


async def verify_webhook_auth(request: Request) -> dict:
    """Validar bearer token del webhook"""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        logger.warning("❌ Webhook auth: Missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.replace("Bearer ", "")

    if token != BACKEND_SHARED_SECRET:
        logger.warning("❌ Webhook auth: Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")

    logger.info("✅ Webhook auth: Token verified")
    return {"verified": True}


@router.get("/meta/cloud/health")
async def meta_cloud_health(db: Session = Depends(get_db)):
    """Endpoint de diagnóstico para verificar configuración del webhook Meta Cloud."""
    from datetime import datetime
    
    meta_token = META_WA_TOKEN
    backend_secret = BACKEND_SHARED_SECRET
    meta_phone_id = os.getenv("META_WA_PHONE_NUMBER_ID", "")
    
    # Get all tenants with their Meta channels
    tenants = db.query(Tenant).all()
    meta_channels = db.query(Channel).filter(Channel.provider == "meta").all()
    
    tenants_list = [
        {
            "id": t.id,
            "name": t.name or t.id,
            "phone_number_id": t.phone_number_id or "not_set",
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            "channels": [
                {
                    "external_id": c.external_id,
                    "kind": c.kind or "whatsapp",
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in meta_channels if c.tenant_id == t.id
            ]
        }
        for t in tenants
    ]
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": {
            "META_WA_TOKEN": "✅ Configured" if meta_token else "❌ Missing",
            "BACKEND_SHARED_SECRET": "✅ Configured" if backend_secret else "❌ Missing",
            "META_WA_PHONE_NUMBER_ID": meta_phone_id if meta_phone_id else "❌ Not configured",
        },
        "database": {
            "total_tenants": len(tenants),
            "meta_channels": len(meta_channels),
            "tenants": tenants_list,
        },
        "notes": [
            "BACKEND_SHARED_SECRET must match Vercel secret",
            "META_WA_TOKEN is used for downloading media from Meta Graph API",
            "META_WA_PHONE_NUMBER_ID must have a Channel entry in DB (created by seed.py)",
            "Each tenant can have multiple Meta channels (for multi-phone scenarios)",
        ]
    }


@router.post("/meta/cloud")
async def receive_meta_cloud_events(
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(verify_webhook_auth),
):
    """
    Recibir eventos de Meta Cloud API reenviados por Vercel.

    Headers esperados:
    - Authorization: Bearer ${BACKEND_SHARED_SECRET}
    - X-Tenant-ID: tenant_id
    - X-Phone-Number-ID: phone_number_id

    Body:
    {
        "tenant_id": "tenant_demo",
        "phone_number_id": "1234567890",
        "payload": {...},  # Payload original de Meta
        "timestamp": "2025-01-15T10:30:00Z"
    }
    """

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"❌ Invalid JSON: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Extraer datos
    tenant_header = body.get("tenant_id") or request.headers.get("x-tenant-id")
    phone_number_id = body.get("phone_number_id") or request.headers.get("x-phone-number-id")
    payload = body.get("payload", {})
    timestamp_str = body.get("timestamp", datetime.utcnow().isoformat())

    tenant_id = _resolve_tenant(db, phone_number_id, tenant_header)

    logger.info(
        f"📱 Meta Cloud Event - tenant: {tenant_id}, phone_number_id: {phone_number_id}"
    )

    # Extraer datos del payload
    try:
        entry = payload.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0]
        value = change.get("value", {})

        messages = value.get("messages", [])
        statuses = value.get("statuses", [])
        contacts = value.get("contacts", [])

        # Persist raw event for debugging/traceability
        try:
            evt = WhatsAppEvent(
                tenant_id=tenant_id,
                phone_number_id=phone_number_id,
                wa_from=messages[0].get("from") if messages else None,
                message_id=messages[0].get("id") if messages else None,
                timestamp=timestamp_str,
                raw_payload=json.dumps(payload)[:3800],
            )
            db.add(evt)
            db.commit()
        except Exception as e:
            logger.warning(f"⚠️  Could not persist WhatsAppEvent: {str(e)}")
            db.rollback()

        # Procesar contactos (solo log, el modelo de Counterparty no incluye campos WA)
        for contact in contacts:
            contact_name = contact.get("profile", {}).get("name", "Unknown")
            contact_wa_id = contact.get("wa_id")
            logger.info(f"👤 Contact: {contact_name} ({contact_wa_id})")

        # Procesar mensajes
        for message in messages:
            msg_id = message.get("id")
            msg_type = message.get("type")
            from_wa_id = message.get("from")

            logger.info(f"📨 Message - id: {msg_id}, type: {msg_type}, from: {from_wa_id}")

            # Verificar idempotencia por message_id
            if _message_already_processed(db, tenant_id, msg_id):
                logger.info(f"  ↩️  Message {msg_id} already processed, skipping")
                continue

            # Registrar mensaje en tabla de idempotencia
            _record_inbound_message(
                db,
                message_id=msg_id,
                sender_wa_id=from_wa_id,
                phone_number_id=phone_number_id,
                tenant_id=tenant_id,
                msg_type=msg_type,
                content=json.dumps(message).replace("\\n", " ")[:500],
                status="received",
            )

            # Procesar según tipo
            if msg_type == "text":
                msg_content = message.get("text", {})
                text_body = msg_content.get("body", "")
                logger.info(f"  📝 Text: {text_body[:100]}...")

            elif msg_type == "document":
                msg_content = message.get("document", {})
                doc_id = msg_content.get("id")
                doc_filename = msg_content.get("filename", "document")
                logger.info(f"  📄 Document: {doc_filename} (ID: {doc_id})")
                
                # Descargar media
                result = download_meta_media(doc_id)
                if not result:
                    logger.warning(f"  ❌ Could not download document {doc_filename}")
                    continue
                
                media_bytes, local_filename, content_type = result
                
                # Guardar archivo
                safe_filename = f"whatsapp_{tenant_id}_{msg_id.replace('/', '_')}.pdf"
                file_path = os.path.join(UPLOAD_DIR, safe_filename)
                try:
                    with open(file_path, "wb") as f:
                        f.write(media_bytes)
                    logger.info(f"  💾 Saved to {safe_filename}")
                except Exception as e:
                    logger.error(f"  ❌ Error saving file: {str(e)}")
                    continue
                
                # Extraer y parsear PDF
                text = ""
                parsed = {"needs_review": True, "parse_confidence": 10, "source_system": "whatsapp", "doc_type": "document"}
                
                if "pdf" in content_type:
                    try:
                        text = extract_text_from_pdf(file_path)
                        if text:
                            doc_key = detect_doc(text)
                            parsed = parse_by_type(doc_key, text)
                            logger.info(f"  ✅ Parsed as {parsed.get('doc_type')}: {parsed.get('concept', '')[:80]}")
                    except Exception as e:
                        logger.error(f"  ❌ Error extracting PDF: {str(e)}")
                
                # Crear Transaction
                tx = Transaction(
                    tenant_id=tenant_id or 1,
                    source_file=safe_filename,
                    source_system="whatsapp",
                    doc_type=parsed.get("doc_type", "document"),
                    datetime=parsed.get("datetime"),
                    currency=parsed.get("currency", "ARS"),
                    amount=parsed.get("amount"),
                    direction=parsed.get("direction", "unknown"),
                    operation_id=parsed.get("operation_id"),
                    operation_id_type=parsed.get("operation_id_type", "unknown"),
                    payer_name=parsed.get("payer_name"),
                    payer_cuit=parsed.get("payer_cuit"),
                    payer_cuit_masked=parsed.get("payer_cuit_masked"),
                    payer_bank=parsed.get("payer_bank"),
                    payer_account_type=parsed.get("payer_account_type"),
                    payer_account_id=parsed.get("payer_account_id"),
                    payee_name=parsed.get("payee_name"),
                    payee_cuit=parsed.get("payee_cuit"),
                    payee_cuit_masked=parsed.get("payee_cuit_masked"),
                    payee_bank=parsed.get("payee_bank"),
                    payee_account_type=parsed.get("payee_account_type"),
                    payee_account_id=parsed.get("payee_account_id"),
                    concept=parsed.get("concept") or doc_filename[:300],
                    raw_text=(text[:1900] if text else None),
                    needs_review=bool(parsed.get("needs_review", True)),
                    parse_confidence=parsed.get("parse_confidence", 10),
                )
                db.add(tx)
                db.commit()
                db.refresh(tx)
                logger.info(f"  📦 Created Transaction {tx.id}")
                
                # Resolver y matchear
                _resolve_and_match(db, tx, tenant_id)

            elif msg_type == "image":
                msg_content = message.get("image", {})
                image_id = msg_content.get("id")
                logger.info(f"  🖼️  Image ID: {image_id}")
                # TODO: Descargar via Graph API y procesar con OCR

        # Procesar cambios de estado
        for status in statuses:
            status_id = status.get("id")
            status_value = status.get("status")  # sent, delivered, read, failed
            recipient_id = status.get("recipient_id")
            logger.info(
                f"✓ Status - id: {status_id}, status: {status_value}, recipient: {recipient_id}"
            )

        logger.info(
            f"✅ Meta event processed - tenant: {tenant_id}, messages: {len(messages)}"
        )

        return {
            "status": "received",
            "tenant_id": tenant_id,
            "phone_number_id": phone_number_id,
            "messages_processed": len(messages),
            "statuses_processed": len(statuses),
            "contacts_processed": len(contacts),
        }

    except Exception as e:
        logger.error(f"❌ Error processing Meta event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
