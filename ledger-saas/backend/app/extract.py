import re
import pdfplumber
from datetime import datetime

def extract_text_from_pdf(pdf_path: str) -> str:
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
    return "\n".join(parts).strip()

def detect_doc(text: str) -> str:
    t = (text or "").lower()
    if "comprobante de transferencia" in t and "mercado pago" in t:
        return "mp_transfer"
    if "office banking" in t and "detalle de movimiento" in t:
        return "galicia_movement"
    if "comprobante de pago" in t and ("tarjeta de crédito" in t or "tarjeta de credito" in t):
        return "card_payment"
    return "unknown"

def _grab(text: str, pattern: str, flags=re.I):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None

def _money_to_float(s: str | None) -> float | None:
    if not s:
        return None
    s = s.strip()
    # admite: 13.300 / 38.000,00 / 13.176,21
    if "," in s:
        # miles con puntos, decimal con coma
        s = s.replace(".", "").replace(",", ".")
    else:
        # miles con puntos, sin decimales
        s = s.replace(".", "")
    try:
        return float(s)
    except Exception:
        return None

def _parse_dt_es(s: str | None) -> str | None:
    """POC: parsea casos típicos de los 3 comprobantes."""
    if not s:
        return None
    s = s.strip()
    # "Lunes, 29 de diciembre de 2025 a las 10:39 hs"
    m = re.search(r"(\d{1,2})\s+de\s+([a-zñ]+)\s+de\s+(\d{4}).*?(\d{1,2}):(\d{2})", s, re.I)
    if m:
        day, mon, year, hh, mm = m.groups()
        months = {
            "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
            "julio":7,"agosto":8,"septiembre":9,"setiembre":9,"octubre":10,"noviembre":11,"diciembre":12
        }
        month = months.get(mon.lower())
        if month:
            dt = datetime(int(year), month, int(day), int(hh), int(mm), 0)
            return dt.isoformat()
    # "Miércoles, 17 de diciembre 2025, 16:11:36"
    m = re.search(r"(\d{1,2})\s+de\s+([a-zñ]+)\s+(\d{4}).*?(\d{1,2}):(\d{2}):(\d{2})", s, re.I)
    if m:
        day, mon, year, hh, mm, ss = m.groups()
        months = {
            "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
            "julio":7,"agosto":8,"septiembre":9,"setiembre":9,"octubre":10,"noviembre":11,"diciembre":12
        }
        month = months.get(mon.lower())
        if month:
            dt = datetime(int(year), month, int(day), int(hh), int(mm), int(ss))
            return dt.isoformat()
    # "29/12/2025"
    m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", s)
    if m:
        d, mo, y = m.groups()
        return datetime(int(y), int(mo), int(d), 0, 0, 0).isoformat()
    return None

def parse_mp_transfer(text: str) -> dict:
    # monto: primera ocurrencia "$ 13.300"
    amount_raw = _grab(text, r"\$\s*([0-9\.\,]+)")
    amount = _money_to_float(amount_raw)

    dt_line = _grab(text, r"Comprobante de transferencia\s*\n([^\n]+)", flags=re.I)
    dt_iso = _parse_dt_es(dt_line)

    return {
        "source_system": "mercado_pago",
        "doc_type": "transfer",
        "currency": "ARS",
        "amount": amount,
        "datetime": dt_iso,
        "operation_id": _grab(text, r"Número de operación de Mercado Pago\s*\n([0-9]+)") or _grab(text, r"N° de operación\s*([0-9]+)"),
        "operation_id_type": "mp_operation",
        "concept": _grab(text, r"Motivo:\s*([^\n]+)"),
        "payer_name": _grab(text, r"De\s*\n([^\n]+)"),
        "payer_cuit": _grab(text, r"De\s*\n[^\n]+\nCUIT/CUIL:\s*([0-9\-]+)", flags=re.I),
        "payer_bank": "Mercado Pago" if re.search(r"\bMercado Pago\b", text, re.I) else None,
        "payer_account_type": "CVU" if "CVU:" in text else None,
        "payer_account_id": _grab(text, r"CVU:\s*([0-9]+)"),
        "payee_name": _grab(text, r"Para\s*\n([^\n]+)"),
        "payee_cuit": _grab(text, r"Para\s*\n[^\n]+\nCUIT/CUIL:\s*([0-9\-]+)", flags=re.I),
        "payee_bank": _grab(text, r"Para\s*\n[^\n]+\n[^\n]+\n([^\n]+)", flags=re.I),
        "payee_account_type": "CBU" if "CBU:" in text else None,
        "payee_account_id": _grab(text, r"CBU:\s*([0-9]+)"),
        "needs_review": False if amount is not None else True,
        "parse_confidence": 90 if amount is not None else 30,
    }

def parse_galicia_movement(text: str) -> dict:
    # línea típica: "29/12/2025 Débito $ 38.000,00"
    amount_raw = _grab(text, r"\b(?:Débito|Debito|Crédito|Credito)\b\s*\$\s*([0-9\.\,]+)", flags=re.I)
    amount = _money_to_float(amount_raw)

    dt_raw = _grab(text, r"\b(\d{2}/\d{2}/\d{4})\b")
    dt_iso = _parse_dt_es(dt_raw)

    direction = "debit" if re.search(r"\bDébito\b|\bDebito\b", text, re.I) else "credit" if re.search(r"\bCrédito\b|\bCredito\b", text, re.I) else "unknown"

    return {
        "source_system": "galicia",
        "doc_type": "movement",
        "currency": "ARS",
        "amount": amount,
        "datetime": dt_iso,
        "direction": direction,
        "operation_id": _grab(text, r"Número de comprobante\s*\n([0-9]+)", flags=re.I) or _grab(text, r"Nro\.?\s*Comprobante\s*([0-9]+)", flags=re.I),
        "operation_id_type": "receipt_number",
        "concept": "Trf Inmed Proveed" if re.search(r"Trf Inmed Proveed", text, re.I) else _grab(text, r"Tipo de movimiento\s*([^\n]+)"),
        "payer_name": _grab(text, r"Leyendas adicionales\s*\n([^\n]+)", flags=re.I),
        "payer_cuit": _grab(text, r"Leyendas adicionales\s*\n[^\n]+\n([0-9]{11})", flags=re.I),
        "payer_bank": _grab(text, r"(BANCO DE[^\n]+)", flags=re.I),
        "needs_review": False if amount is not None else True,
        "parse_confidence": 85 if amount is not None else 25,
    }

def parse_card_payment(text: str) -> dict:
    # el PDF tiene texto duplicado (TToottaall) pero el monto está como "$ 13.176,21"
    amount_raw = _grab(text, r"\$\s*([0-9\.\,]+)")
    amount = _money_to_float(amount_raw)

    dt_line = _grab(text, r"Comprobante de pago\s*\n([^\n]+)", flags=re.I)
    dt_iso = _parse_dt_es(dt_line)

    # CUIT enmascarado: aparecen 2 sufijos
    masked = re.findall(r"CUIT\*+([0-9]{4,5})\*+\b", text, flags=re.I)
    payer_suffix = masked[0] if len(masked) >= 1 else None
    payee_suffix = masked[1] if len(masked) >= 2 else None

    return {
        "source_system": "card_payment",
        "doc_type": "card_payment",
        "currency": "ARS",
        "amount": amount,
        "datetime": dt_iso,
        "operation_id": _grab(text, r"N[úu]mero de transacci[óo]n::?\s*([0-9]+)", flags=re.I),
        "operation_id_type": "transaction_number",
        "concept": _grab(text, r"TT[íi]ttuulloo::\s*([^\n]+)", flags=re.I) or _grab(text, r"T[íi]tulo:\s*([^\n]+)", flags=re.I),
        "payer_name": _grab(text, r"De\s*\n([^\n]+)", flags=re.I),
        "payer_cuit_masked": payer_suffix,
        "payee_name": _grab(text, r"Para\s*\n([^\n]+)", flags=re.I),
        "payee_cuit_masked": payee_suffix,
        "needs_review": True,  # CUIT enmascarado requiere base de contrapartes
        "parse_confidence": 80 if amount is not None else 20,
    }

def parse_by_type(doc_type: str, text: str) -> dict:
    if doc_type == "mp_transfer":
        return parse_mp_transfer(text)
    if doc_type == "galicia_movement":
        return parse_galicia_movement(text)
    if doc_type == "card_payment":
        return parse_card_payment(text)
    return {"needs_review": True, "parse_confidence": 10}
