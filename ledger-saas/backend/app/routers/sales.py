import os
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Sale
from ..deps import get_current_user, require_role
from ..ingest import (
    extract_text_from_image,
    extract_text_from_pdf_ingest,
    parse_sale_from_text,
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/v1/sales", tags=["sales"])

class SaleIn(BaseModel):
    datetime: str
    amount: float
    currency: str = "ARS"
    customer_name: str | None = None
    customer_cuit: str | None = None
    customer_phone: str | None = None
    description: str | None = None
    external_ref: str | None = None

@router.post("")
def create_sale(payload: SaleIn, db: Session = Depends(get_db), user=Depends(require_role("owner","admin","employee"))):
    s = Sale(tenant_id=user.tenant_id, **payload.model_dump(), status="open")
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id}

@router.get("")
def list_sales(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(Sale).filter(Sale.tenant_id == user.tenant_id).order_by(Sale.id.desc()).all()
    return [{"id": r.id, "datetime": r.datetime, "amount": float(r.amount), "currency": r.currency, "customer_name": r.customer_name, "customer_cuit": r.customer_cuit, "customer_phone": r.customer_phone, "description": r.description, "external_ref": r.external_ref, "status": r.status} for r in rows]

@router.post("/ingest")
async def ingest_sale(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("owner", "admin", "employee")),
):
    """
    Endpoint para subir una imagen o PDF de venta.
    Extrae información automáticamente y retorna un draft para revisión.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
        
        filename = file.filename.lower()
        
        # Verificar tipo de archivo
        is_pdf = filename.endswith(".pdf")
        is_image = any(filename.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"])
        
        if not (is_pdf or is_image):
            raise HTTPException(
                status_code=400,
                detail="Formato no soportado. Use PDF o imagen (JPG, PNG, etc.)"
            )
        
        # Guardar archivo temporalmente
        temp_path = os.path.join(UPLOAD_DIR, f"ingest_t{user.tenant_id}_{file.filename}")
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Extraer texto
        if is_pdf:
            raw_text = extract_text_from_pdf_ingest(temp_path)
        else:
            raw_text = extract_text_from_image(temp_path)
        
        # Parsear información
        parsed = parse_sale_from_text(raw_text)
        
        # Si no se detectó fecha, usar la actual
        if not parsed.get("datetime"):
            parsed["datetime"] = datetime.now().isoformat()
        
        # Retornar draft (sin guardar en BD)
        result = {
            "draft": True,
            "amount": parsed.get("amount"),
            "datetime": parsed.get("datetime"),
            "customer_name": parsed.get("customer_name"),
            "customer_phone": parsed.get("customer_phone"),
            "customer_cuit": parsed.get("customer_cuit"),
            "external_ref": parsed.get("external_ref"),
            "raw_text": parsed.get("raw_text"),
            "currency": "ARS",
        }
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar archivo: {str(e)}")
    finally:
        # Opcionalmente eliminar archivo temporal
        try:
            temp_path = os.path.join(UPLOAD_DIR, f"ingest_t{user.tenant_id}_{file.filename}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass


