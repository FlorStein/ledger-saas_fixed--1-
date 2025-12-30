import re
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import get_current_user
from ..models import Sale, Transaction

router = APIRouter(prefix="/v1/chat", tags=["chat"])

class ChatIn(BaseModel):
    message: str

@router.post("")
def chat(payload: ChatIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = payload.message.strip().lower()

    if re.search(r"(pendiente|revisar|needs_review|sin matchear)", m):
        rows = db.query(Transaction).filter(Transaction.tenant_id == user.tenant_id, Transaction.needs_review == True).order_by(Transaction.id.desc()).limit(20).all()
        return {"reply": f"Encontré {len(rows)} transacciones para revisar.", "data": [{"id": r.id, "amount": float(r.amount) if r.amount else None, "source_file": r.source_file} for r in rows]}

    mm = re.search(r"venta\s+([0-9]+)\s*(.*)", m)
    if mm:
        amount = float(mm.group(1))
        desc = (mm.group(2) or "").strip() or "Venta"
        s = Sale(tenant_id=user.tenant_id, datetime="2025-12-29T00:00:00", amount=amount, currency="ARS", description=desc, status="open")
        db.add(s)
        db.commit()
        db.refresh(s)
        return {"reply": f"Creé una venta #{s.id} por ARS {amount:.2f} ({desc}).", "data": {"sale_id": s.id}}

    if "ultimas" in m or "últimas" in m or "transacciones" in m:
        rows = db.query(Transaction).filter(Transaction.tenant_id == user.tenant_id).order_by(Transaction.id.desc()).limit(10).all()
        return {"reply": "Últimas 10 transacciones:", "data": [{"id": r.id, "amount": float(r.amount) if r.amount else None, "match": r.match_status} for r in rows]}

    return {"reply": "Puedo: (1) listar pendientes, (2) crear venta: 'venta 13300 libreria', (3) mostrar últimas transacciones. ¿Qué querés hacer?"}
