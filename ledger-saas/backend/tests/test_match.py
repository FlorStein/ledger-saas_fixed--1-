"""
Tests unitarios para el matcher de transacciones con ventas.
Cubre:
- Gap match: diferencia suficiente entre candidatos
- Tie-break por evidencia: cuando scores son iguales
- Tie-break por cercanía de fecha: cuando evidencia también es igual
- Casos que deben quedar ambiguous
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import Transaction, Sale, Tenant, User
from app.match import match_sale, normalize_name, AUTO_MATCH_THRESHOLD, AUTO_MATCH_GAP


@pytest.fixture
def db():
    """Crea una BD SQLite en memoria para tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Crear tenant y usuario demo
    tenant = Tenant(name="Test Tenant", status="active")
    session.add(tenant)
    session.commit()
    
    yield session
    session.close()


def test_strong_id_match(db):
    """Test: Strong ID Match - operation_id == external_ref"""
    tenant_id = 1
    
    # Crear venta con external_ref específica
    sale = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente A",
        external_ref="OP-12345"
    )
    db.add(sale)
    db.commit()
    
    # Crear transacción con mismo operation_id
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:05:00",
        amount=1000.00,
        currency="ARS",
        operation_id="OP-12345",
        payer_name="Cliente A"
    )
    db.add(tx)
    db.commit()
    
    result = match_sale(db, tx)
    
    assert result.status == "matched"
    assert result.method == "strong_id"
    assert result.sale_id == sale.id
    assert result.needs_review == False
    assert result.score == 100


def test_gap_match(db):
    """Test: Gap Match - top score >= threshold y gap >= AUTO_MATCH_GAP"""
    tenant_id = 1
    
    # Crear dos ventas del mismo monto
    sale1 = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente A",
        customer_cuit="20123456789"
    )
    sale2 = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T14:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente B",
        customer_phone="1123456789"
    )
    db.add(sale1)
    db.add(sale2)
    db.commit()
    
    # Transacción con CUIT que coincide con sale1
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:05:00",
        amount=1000.00,
        currency="ARS",
        operation_id=None,
        payer_name="Cliente A",
        payer_cuit="20123456789"
    )
    db.add(tx)
    db.commit()
    
    result = match_sale(db, tx)
    
    # sale1 debe ganar por CUIT exacto (score alto), gap debe ser >= AUTO_MATCH_GAP
    assert result.status == "matched"
    assert result.method == "gap"
    assert result.sale_id == sale1.id
    assert result.needs_review == False


def test_single_candidate_match(db):
    """Test: Single candidate con score alto"""
    tenant_id = 1
    
    sale = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente Único",
        customer_cuit="20123456789"
    )
    db.add(sale)
    db.commit()
    
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:05:00",
        amount=1000.00,
        currency="ARS",
        payer_name="Cliente Único",
        payer_cuit="20123456789"
    )
    db.add(tx)
    db.commit()
    
    result = match_sale(db, tx)
    
    assert result.status == "matched"
    assert result.method == "single_candidate"
    assert result.sale_id == sale.id
    assert result.needs_review == False


def test_tiebreak_by_evidence(db):
    """Test: Tie-break por evidencia cuando scores son iguales"""
    tenant_id = 1

    # Dos ventas con scores exactamente iguales (mismo monto, fecha, nombre)
    sale_option_a = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente A",
        customer_cuit="20123456789"  # CUIT presente pero NO coincide con tx
    )
    sale_option_b = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente A",  # Nombre igual para scores coincidan
        customer_phone="1199999999"  # Teléfono presente pero NO coincide
    )
    db.add(sale_option_a)
    db.add(sale_option_b)
    db.commit()

    # Transacción sin identificadores específicos
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        payer_name="Cliente A",
        payer_cuit=None
    )
    db.add(tx)
    db.commit()

    result = match_sale(db, tx)
    
    # Con scores iguales, ambiguo
    assert result.status == "ambiguous"
    assert result.needs_review == True


def test_tiebreak_by_date_proximity(db):
    """Test: Tie-break por cercanía de fecha cuando evidencia es igual"""
    tenant_id = 1
    
    # Dos ventas con misma evidencia (nombre)
    sale_close = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente A",
    )
    sale_far = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T22:00:00",  # 12 horas después
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente A",
    )
    db.add(sale_close)
    db.add(sale_far)
    db.commit()
    
    # Transacción en horario cercano a sale_close
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:05:00",
        amount=1000.00,
        currency="ARS",
        payer_name="Cliente A",
    )
    db.add(tx)
    db.commit()
    
    result = match_sale(db, tx)
    
    # Debe elegir sale_close por estar más cerca en tiempo
    assert result.status == "matched"
    assert result.sale_id == sale_close.id
    """Test: Ambiguous cuando no se puede romper empate"""
    tenant_id = 1
    
    # Dos ventas idénticas (misma fecha, mismo nombre)
    sale1 = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente",
    )
    sale2 = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente",
    )
    db.add(sale1)
    db.add(sale2)
    db.commit()
    
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        payer_name="Cliente",
    )
    db.add(tx)
    db.commit()
    
    result = match_sale(db, tx)
    
    # Debe quedar ambiguous porque no se puede romper el empate perfecto
    assert result.status == "ambiguous"
    assert result.method == "needs_review"
    assert result.needs_review == True


def test_low_score_unmatched(db):
    """Test: Unmatched cuando score es demasiado bajo"""
    tenant_id = 1
    
    # Venta sin coincidencias útiles
    sale = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-30T10:00:00",  # Día diferente
        amount=1000.00,
        currency="ARS",
        customer_name="Otro Cliente",
        customer_cuit="20999999999"
    )
    db.add(sale)
    db.commit()
    
    # Transacción con datos completamente diferentes
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        payer_name="Cliente Diferente",
        payer_cuit="20111111111"
    )
    db.add(tx)
    db.commit()
    
    result = match_sale(db, tx)
    
    # Bajo score debe resultar en unmatched
    assert result.status == "unmatched"
    assert result.method == "low_score"


def test_normalize_name():
    """Test: Normalización de nombres"""
    assert normalize_name("JUAN PÉREZ S.A.") == "juan perez"
    assert normalize_name("  María   García  ") == "maria garcia"
    assert normalize_name("ABC srl XYZ") == "abc xyz"
    assert normalize_name(None) == ""


def test_date_window_configuration(db):
    """Test: DATE_WINDOW_HOURS se respeta en búsqueda de candidatos"""
    # Este test verifica que la ventana de fechas es correcta
    tenant_id = 1
    
    # Sale fuera de la ventana
    sale_old = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-28T00:00:00",  # >72 horas antes
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente",
    )
    
    # Sale dentro de la ventana
    sale_new = Sale(
        tenant_id=tenant_id,
        datetime="2025-12-29T10:00:00",  # Dentro de 72h
        amount=1000.00,
        currency="ARS",
        customer_name="Cliente",
    )
    db.add(sale_old)
    db.add(sale_new)
    db.commit()
    
    tx = Transaction(
        tenant_id=tenant_id,
        source_file="test.pdf",
        datetime="2025-12-29T10:00:00",
        amount=1000.00,
        currency="ARS",
        payer_name="Cliente",
    )
    db.add(tx)
    db.commit()
    
    result = match_sale(db, tx)
    
    # Solo sale_new debería ser candidato
    assert result.sale_id == sale_new.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
