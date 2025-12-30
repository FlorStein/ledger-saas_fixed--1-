import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Transaction, Sale, Counterparty

# Configuración desde .env
AUTO_MATCH_THRESHOLD = int(os.getenv("AUTO_MATCH_THRESHOLD", "85"))
AUTO_MATCH_GAP = int(os.getenv("AUTO_MATCH_GAP", "10"))
DATE_WINDOW_HOURS = int(os.getenv("DATE_WINDOW_HOURS", "72"))

def normalize_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for w in [" sa", " srl", " s a", " s r l"]:
        s = s.replace(w, "")
    return s.strip()

def extract_visible_suffix(masked: str | None) -> str | None:
    if not masked:
        return None
    digits = re.findall(r"\d+", masked)
    joined = "".join(digits)
    return joined if len(joined) in (4, 5) else None

def _parse_iso(dt: str | None) -> datetime | None:
    if not dt:
        return None
    try:
        if "T" in dt:
            return datetime.fromisoformat(dt)
        return datetime.fromisoformat(dt + "T00:00:00")
    except Exception:
        return None

@dataclass
class MatchResult:
    id: int | None
    sale_id: int | None  # alias para ID
    score: int
    status: str  # matched/ambiguous/unmatched
    method: str | None = None  # strong_id/gap/single_candidate/tiebreak/needs_review
    needs_review: bool = True
    candidates: list = None  # lista de candidatos con reasons
    
    def __post_init__(self):
        if self.candidates is None:
            self.candidates = []
        if self.sale_id is None:
            self.sale_id = self.id

def match_sale(db: Session, tx: Transaction, days_window: int = 2, amount_tol: float = 0.01) -> MatchResult:
    """
    Matching inteligente con auto-resolución de casos ambiguos.
    Reglas de prioridad:
    1. Strong ID: operation_id == external_ref
    2. Gap suficiente entre top y second candidato
    3. Un solo candidato con score alto
    4. Tie-break determinístico por evidencia
    """
    if tx.amount is None:
        return MatchResult(None, None, 0, "unmatched", method="no_amount", needs_review=False)
    
    tx_dt = _parse_iso(tx.datetime)
    if not tx_dt:
        return MatchResult(None, None, 0, "unmatched", method="no_date", needs_review=False)

    # Calcular ventana de fechas usando DATE_WINDOW_HOURS
    hours_window = DATE_WINDOW_HOURS / 24.0
    start = tx_dt - timedelta(days=hours_window)
    end = tx_dt + timedelta(days=hours_window)
    
    # Buscar candidatos por monto
    candidates = db.query(Sale).filter(
        Sale.tenant_id == tx.tenant_id,
        Sale.currency == tx.currency,
        Sale.amount >= float(tx.amount) - amount_tol,
        Sale.amount <= float(tx.amount) + amount_tol,
    ).all()

    # REGLA 1: Strong ID Match
    if tx.operation_id:
        for s in candidates:
            if s.external_ref and tx.operation_id == s.external_ref:
                return MatchResult(
                    s.id, s.id, 100, "matched",
                    method="strong_id",
                    needs_review=False,
                    candidates=[{"sale_id": s.id, "score": 100, "reasons": ["ID de operación coincide exactamente"]}]
                )

    # Calcular scores para todos los candidatos
    scored = []
    for s in candidates:
        s_dt = _parse_iso(s.datetime)
        if not s_dt or not (start <= s_dt <= end):
            continue
        
        score = 60
        reasons = []
        evidence_types = []  # Para tie-break
        
        # Puntuación por fecha
        delta_days = abs((s_dt.date() - tx_dt.date()).days)
        if delta_days == 0:
            score += 25
            reasons.append("Mismo día")
        elif delta_days == 1:
            score += 15
            reasons.append(f"Diferencia de {delta_days} día")
        elif delta_days <= 2:
            score += 5
            reasons.append(f"Diferencia de {delta_days} días")
        
        # Puntuación por CUIT (evidencia fuerte)
        if tx.payer_cuit and s.customer_cuit and tx.payer_cuit == s.customer_cuit:
            score += 20
            reasons.append("CUIT cliente coincide")
            evidence_types.append(("cuit_exact", 100))
        elif tx.payer_cuit_masked and s.customer_cuit:
            suffix = extract_visible_suffix(tx.payer_cuit_masked)
            if suffix and s.customer_cuit.endswith(suffix):
                score += 10
                reasons.append("Últimos dígitos del CUIT coinciden")
                evidence_types.append(("cuit_suffix", 50))
        
        # Puntuación por referencia externa
        if s.external_ref and tx.concept:
            if s.external_ref.lower() in tx.concept.lower():
                score += 15
                reasons.append("Referencia en concepto")
                evidence_types.append(("ref_match", 90))
        
        # Puntuación por teléfono (evidencia fuerte)
        if s.customer_phone:
            s_phone = re.sub(r"\D", "", s.customer_phone)
            # Buscar en distintos campos
            tx_phone_concept = re.sub(r"\D", "", tx.concept or "")
            tx_phone_payer = re.sub(r"\D", "", tx.payer_cuit or "")
            
            if s_phone and (
                (tx_phone_concept and s_phone in tx_phone_concept) or
                (tx_phone_payer and s_phone == tx_phone_payer)
            ):
                score += 15
                reasons.append("Teléfono cliente coincide")
                evidence_types.append(("phone_match", 80))
        
        # Puntuación por nombre
        norm_tx = normalize_name(tx.payer_name)
        norm_sale = normalize_name(s.customer_name)
        if norm_tx and norm_sale:
            tokens_tx = set(t for t in norm_tx.split() if len(t) > 2)
            tokens_sale = set(t for t in norm_sale.split() if len(t) > 2)
            intersection = tokens_tx.intersection(tokens_sale)
            if intersection:
                name_match_score = min(10, len(intersection) * 2)
                score += name_match_score
                reasons.append("Nombre coincide parcialmente")
                evidence_types.append(("name_match", 70))
        
        # Monto exacto (ya filtrado, pero es evidencia)
        if abs(float(s.amount) - float(tx.amount)) < 0.01:
            evidence_types.append(("amount_exact", 60))
        
        # Calcular evidence_rank para tie-break
        evidence_rank = max([e[1] for e in evidence_types], default=0)
        time_delta = abs((s_dt - tx_dt).total_seconds())
        
        scored.append((s, score, reasons, evidence_rank, time_delta))

    if not scored:
        return MatchResult(None, None, 0, "unmatched", method="no_candidates", needs_review=False)

    # Ordenar por score desc, luego por evidence_rank desc, luego por time_delta asc, luego por sale_id asc
    scored.sort(key=lambda x: (-x[1], -x[3], x[4], x[0].id))
    
    best_sale, best_score, best_reasons, best_evidence, best_time_delta = scored[0]
    
    # Preparar candidatos para respuesta (top 3)
    candidates_out = [
        {"sale_id": s.id, "score": score, "reasons": reasons}
        for s, score, reasons, _, _ in scored[:3]
    ]
    
    # REGLA 2: Single candidate con score alto
    if len(scored) == 1:
        if best_score >= AUTO_MATCH_THRESHOLD:
            return MatchResult(
                best_sale.id, best_sale.id, best_score, "matched",
                method="single_candidate",
                needs_review=False,
                candidates=candidates_out
            )
        else:
            return MatchResult(
                None, None, best_score, "unmatched",
                method="low_score",
                needs_review=False,
                candidates=candidates_out
            )
    
    # Hay múltiples candidatos
    second_sale, second_score, second_reasons, second_evidence, second_time_delta = scored[1]
    gap = best_score - second_score
    
    # REGLA 3: Gap suficiente entre top y second
    if best_score >= AUTO_MATCH_THRESHOLD and gap >= AUTO_MATCH_GAP:
        return MatchResult(
            best_sale.id, best_sale.id, best_score, "matched",
            method="gap",
            needs_review=False,
            candidates=candidates_out
        )
    
    # REGLA 4: Tie-break determinístico
    # Si los scores son iguales o el gap es pequeño, usar evidencia y otros criterios
    if gap < AUTO_MATCH_GAP:
        # El sort ya colocó el mejor por evidence_rank, time_delta, y sale_id
        # Si best tiene mejor evidencia o está más cerca en tiempo, es el ganador
        if best_score >= AUTO_MATCH_THRESHOLD:
            # Verificar que realmente hay diferencia en evidencia o tiempo
            if best_evidence > second_evidence or (best_evidence == second_evidence and best_time_delta < second_time_delta):
                return MatchResult(
                    best_sale.id, best_sale.id, best_score, "matched",
                    method="tiebreak",
                    needs_review=False,
                    candidates=candidates_out
                )
        
        # No se pudo romper el empate o score bajo: ambiguous
        return MatchResult(
            None, None, best_score, "ambiguous",
            method="needs_review",
            needs_review=True,
            candidates=candidates_out
        )
    
    # Score del mejor candidato no alcanza el threshold
    if best_score < AUTO_MATCH_THRESHOLD:
        return MatchResult(
            None, None, best_score, "unmatched",
            method="low_score",
            needs_review=False,
            candidates=candidates_out
        )
    
    # Fallback: matched con el mejor
    return MatchResult(
        best_sale.id, best_sale.id, best_score, "matched",
        method="default",
        needs_review=False,
        candidates=candidates_out
    )

def match_counterparty(db: Session, tenant_id: int, name: str | None, cuit: str | None, cuit_masked: str | None) -> MatchResult:
    if cuit:
        cand = db.query(Counterparty).filter(Counterparty.tenant_id == tenant_id, Counterparty.cuit == cuit).first()
        if cand:
            return MatchResult(cand.id, cand.id, 100, "matched", [{"counterparty_id": cand.id, "score": 100, "reasons": ["CUIT exacto"]}])

    norm = normalize_name(name or "")
    suffix = extract_visible_suffix(cuit_masked)

    q = db.query(Counterparty).filter(Counterparty.tenant_id == tenant_id)
    if suffix:
        q = q.filter(Counterparty.cuit_suffix == suffix)

    candidates = q.all()
    if not candidates and norm:
        candidates = db.query(Counterparty).filter(Counterparty.tenant_id == tenant_id).all()

    if not candidates:
        return MatchResult(None, None, 0, "unmatched", [])

    def name_score(a: str, b: str) -> int:
        ta = set([t for t in a.split() if len(t) > 2])
        tb = set([t for t in b.split() if len(t) > 2])
        inter = len(ta.intersection(tb))
        return min(55, inter * 11)

    scored = []
    for c in candidates:
        score = 0
        reasons = []
        if suffix and c.cuit_suffix == suffix:
            score += 40
            reasons.append("Últimos dígitos del CUIT coinciden")
        if norm and c.normalized_name:
            name_s = name_score(norm, c.normalized_name)
            if name_s > 0:
                score += name_s
                reasons.append("Nombre coincide parcialmente")
        scored.append((c, score, reasons))

    scored.sort(key=lambda x: x[1], reverse=True)
    best, best_score, best_reasons = scored[0]
    
    candidates_out = [
        {"counterparty_id": c.id, "score": score, "reasons": reasons}
        for c, score, reasons in scored[:3]
    ]
    
    if len(scored) > 1 and (scored[0][1] - scored[1][1]) < 10:
        return MatchResult(None, None, best_score, "ambiguous", candidates_out)
    
    if best_score >= 85:
        return MatchResult(best.id, best.id, best_score, "matched", candidates_out)
    else:
        return MatchResult(None, None, best_score, "unmatched", candidates_out)
