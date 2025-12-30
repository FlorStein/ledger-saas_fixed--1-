import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook

from ..db import get_db
from ..deps import get_current_user
from ..models import Transaction

router = APIRouter(prefix="/v1/export", tags=["export"])

@router.get("/transactions.xlsx")
def export_transactions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(Transaction).filter(Transaction.tenant_id == user.tenant_id).order_by(Transaction.id.asc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "transactions"
    ws.append([
        "id","datetime","amount","currency","source_system","doc_type","operation_id",
        "payer_name","payer_cuit","payee_name","payee_cuit",
        "match_status","match_score","needs_review",
    ])
    for r in rows:
        ws.append([
            r.id, r.datetime, float(r.amount) if r.amount is not None else None, r.currency, r.source_system, r.doc_type, r.operation_id,
            r.payer_name, r.payer_cuit or r.payer_cuit_masked, r.payee_name, r.payee_cuit or r.payee_cuit_masked,
            r.match_status, r.match_score, r.needs_review
        ])

    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)

    filename = "transactions.xlsx"
    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
