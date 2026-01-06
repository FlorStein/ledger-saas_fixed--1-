from datetime import datetime
from sqlalchemy import String, Numeric, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="active")
    phone_number_id: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "whatsapp_wa_id", name="uq_user_whatsapp_wa_id"),
        UniqueConstraint("tenant_id", "whatsapp_number", name="uq_user_whatsapp_number"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(30), default="owner")  # owner/admin/employee/viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String(30), nullable=True)  # E.164 +54911...
    whatsapp_wa_id: Mapped[str | None] = mapped_column(String(40), nullable=True)  # digits only 54911...

    tenant = relationship("Tenant")

class Counterparty(Base):
    __tablename__ = "counterparties"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"))

    type: Mapped[str] = mapped_column(String(20), default="unknown")  # person/company/unknown
    display_name: Mapped[str] = mapped_column(String(180))
    normalized_name: Mapped[str] = mapped_column(String(220))

    cuit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cuit_prefix: Mapped[str | None] = mapped_column(String(2), nullable=True)
    cuit_suffix: Mapped[str | None] = mapped_column(String(5), nullable=True)

    tenant = relationship("Tenant")

class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"))

    datetime: Mapped[str] = mapped_column(String(25))  # ISO
    currency: Mapped[str] = mapped_column(String(10), default="ARS")
    amount: Mapped[float] = mapped_column(Numeric(14, 2))

    customer_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    customer_cuit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="open")  # open/matched

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"))

    source_file: Mapped[str] = mapped_column(String(300))
    source_system: Mapped[str] = mapped_column(String(40), default="unknown")  # mp/galicia/andreani/whatsapp
    doc_type: Mapped[str] = mapped_column(String(40), default="unknown")       # transfer/card_payment/movement

    datetime: Mapped[str | None] = mapped_column(String(25), nullable=True)    # ISO (ideal) o None en POC
    currency: Mapped[str] = mapped_column(String(10), default="ARS")
    amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    direction: Mapped[str] = mapped_column(String(10), default="unknown")      # debit/credit/unknown

    operation_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    operation_id_type: Mapped[str] = mapped_column(String(40), default="unknown")

    payer_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    payer_cuit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payer_cuit_masked: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payer_bank: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payer_account_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # CBU/CVU
    payer_account_id: Mapped[str | None] = mapped_column(String(40), nullable=True)

    payee_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    payee_cuit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payee_cuit_masked: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payee_bank: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payee_account_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payee_account_id: Mapped[str | None] = mapped_column(String(40), nullable=True)

    concept: Mapped[str | None] = mapped_column(String(300), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    parse_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)

    matched_sale_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sales.id"), nullable=True)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_status: Mapped[str] = mapped_column(String(20), default="unmatched")  # matched/ambiguous/unmatched
    match_method: Mapped[str | None] = mapped_column(String(30), nullable=True)  # strong_id/gap/single_candidate/tiebreak/needs_review

    payer_counterparty_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("counterparties.id"), nullable=True)
    payee_counterparty_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("counterparties.id"), nullable=True)
    counterparty_match_status: Mapped[str] = mapped_column(String(20), default="unmatched")
    counterparty_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    matched_sale = relationship("Sale", foreign_keys=[matched_sale_id])
    payer_counterparty = relationship("Counterparty", foreign_keys=[payer_counterparty_id])
    payee_counterparty = relationship("Counterparty", foreign_keys=[payee_counterparty_id])

class Channel(Base):
    """Canal de ingreso por tenant (por ahora WhatsApp)."""
    __tablename__ = "channels"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"))
    kind: Mapped[str] = mapped_column(String(20), default="whatsapp")  # whatsapp
    provider: Mapped[str] = mapped_column(String(20), default="twilio")  # twilio/meta
    # Identificador del canal: en Twilio puede ser el "to" (número sandbox), en Meta el phone_number_id
    external_id: Mapped[str] = mapped_column(String(120))
    label: Mapped[str] = mapped_column(String(120), default="WhatsApp")

class WhatsAppInboundMessage(Base):
    __tablename__ = "whatsapp_inbound_messages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "message_id", name="uq_whatsapp_inbound_message"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), default="meta")
    message_id: Mapped[str] = mapped_column(String(120))
    sender_wa_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    phone_number_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())
    status: Mapped[str] = mapped_column(String(20), default="received")  # received/processed/skipped

    tenant = relationship("Tenant")

    __mapper_args__ = {
        "eager_defaults": True,
    }


class WhatsAppEvent(Base):
    __tablename__ = "whatsapp_events"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=True)
    phone_number_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    wa_from: Mapped[str | None] = mapped_column(String(40), nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())

    tenant = relationship("Tenant")


class IncomingMessage(Base):
    __tablename__ = "incoming_messages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "message_id", name="uq_incoming_message"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sender_wa_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    phone_number_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    msg_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # text/document/image
    content: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued/processing/done
    timestamp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[str] = mapped_column(String(30), default=lambda: datetime.utcnow().isoformat())

    tenant = relationship("Tenant")
