import os
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import require_role
from ..models import Transaction, Counterparty
from ..extract import extract_text_from_pdf, detect_doc, parse_by_type
from ..match import normalize_name, match_sale, match_counterparty

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/v1/receipts", tags=["receipts"])

@router.post("")
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("owner","admin","employee")),
):
    filename = file.filename or "upload.bin"
    path = os.path.join(UPLOAD_DIR, f"t{user.tenant_id}_{filename}")
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    text = ""
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(path)

    doc_key = detect_doc(text) if text else "unknown"
    parsed = parse_by_type(doc_key, text) if text else {"needs_review": True, "parse_confidence": 10}

    tx = Transaction(
        tenant_id=user.tenant_id,
        source_file=filename,
        source_system=parsed.get("source_system","unknown"),
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
        concept=parsed.get("concept"),
        raw_text=(text[:1900] if text else None),
        needs_review=bool(parsed.get("needs_review", False)),
        parse_confidence=parsed.get("parse_confidence"),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    _resolve_and_match(db, tx, user.tenant_id)

    return {
        "id": tx.id,
        "match": {"status": tx.match_status, "score": tx.match_score, "sale_id": tx.matched_sale_id},
        "counterparty": {"status": tx.counterparty_match_status, "score": tx.counterparty_match_score},
        "parsed": {"amount": float(tx.amount) if tx.amount is not None else None, "currency": tx.currency, "operation_id": tx.operation_id},
        "needs_review": tx.needs_review,
    }

def _resolve_and_match(db: Session, tx: Transaction, tenant_id: int):
    # Resolver contrapartes (si no existe, crear provisional)
    for side in ["payer", "payee"]:
        name = getattr(tx, f"{side}_name")
        cuit = getattr(tx, f"{side}_cuit")
        cuit_masked = getattr(tx, f"{side}_cuit_masked")

        if not (name or cuit or cuit_masked):
            continue

        res = match_counterparty(db, tenant_id, name, cuit, cuit_masked)
        tx.counterparty_match_score = res.score
        tx.counterparty_match_status = res.status

        if res.status == "matched" and res.id:
            setattr(tx, f"{side}_counterparty_id", res.id)
        else:
            # crear provisional si no hay match y hay nombre
            if name:
                norm = normalize_name(name)
                prefix, suffix, cuit_full = None, None, None
                if cuit and len(cuit.replace("-","")) >= 11:
                    digits = cuit.replace("-","")
                    prefix, suffix, cuit_full = digits[:2], digits[-5:], cuit

                cp = Counterparty(
                    tenant_id=tenant_id,
                    display_name=name.strip(),
                    normalized_name=norm,
                    cuit=cuit_full,
                    cuit_prefix=prefix,
                    cuit_suffix=suffix,
                    type="unknown",
                )
                db.add(cp)
                db.commit()
                db.refresh(cp)
                setattr(tx, f"{side}_counterparty_id", cp.id)
                tx.needs_review = True

    # Match con ventas
    sale_res = match_sale(db, tx)
    tx.match_score = sale_res.score
    tx.match_status = sale_res.status
    tx.match_method = sale_res.method
    if sale_res.status == "matched" and sale_res.id:
        tx.matched_sale_id = sale_res.id
        tx.needs_review = sale_res.needs_review
    elif sale_res.status == "ambiguous":
        tx.needs_review = True

    db.commit()
    db.refresh(tx)
