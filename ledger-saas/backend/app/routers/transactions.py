from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import get_current_user
from ..models import Transaction

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])

@router.get("")
def list_transactions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(Transaction).filter(Transaction.tenant_id == user.tenant_id).order_by(Transaction.id.desc()).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "source_file": r.source_file,
            "source_system": r.source_system,
            "doc_type": r.doc_type,
            "datetime": r.datetime,
            "amount": float(r.amount) if r.amount is not None else None,
            "currency": r.currency,
            "operation_id": r.operation_id,
            "payer_name": r.payer_name,
            "payee_name": r.payee_name,
            "match_status": r.match_status,
            "match_score": r.match_score,
            "match_method": r.match_method,
            "needs_review": r.needs_review,
        })
    return out
