from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Ticket(Base):
    __tablename__ = "ticket"
    __table_args__ = (
        UniqueConstraint("source_ticket_key", name="uq_ticket_source_key"),
        {"schema": "competitor_ticket"},
    )

    ticket_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_ticket_code: Mapped[str] = mapped_column(String(30), nullable=False)
    source_business_code: Mapped[str] = mapped_column(String(30), nullable=False)
    source_store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    source_ticket_date: Mapped = mapped_column(Date, nullable=False)
    source_ticket_key: Mapped[str] = mapped_column(String(120), nullable=False)
    source_status_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    source_header_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("competitor_ticket.integration_batch.batch_id"), nullable=True)
    scan_status: Mapped[str] = mapped_column(String(25), default="NO_FILE", nullable=False)
    has_scan_file: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scan_confirmed_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    scan_confirmed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("competitor_ticket.app_user.user_id"), nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship("TicketItem", back_populates="ticket", cascade="all, delete-orphan")
    stores = relationship("TicketStore", back_populates="ticket", cascade="all, delete-orphan")
    scan_files = relationship("TicketScanFile", back_populates="ticket", cascade="all, delete-orphan")


class TicketItem(Base):
    __tablename__ = "ticket_item"
    __table_args__ = (UniqueConstraint("ticket_id", "item_sequence", name="uq_ticket_item_ticket_seq"), {"schema": "competitor_ticket"})

    ticket_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.ticket.ticket_id"), nullable=False)
    item_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_item_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    line_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)

    ticket = relationship("Ticket", back_populates="items")


class TicketStore(Base):
    __tablename__ = "ticket_store"
    __table_args__ = (UniqueConstraint("ticket_id", "store_code", name="uq_ticket_store_ticket_store"), {"schema": "competitor_ticket"})

    ticket_store_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.ticket.ticket_id"), nullable=False)
    store_code: Mapped[str] = mapped_column(String(30), nullable=False)

    ticket = relationship("Ticket", back_populates="stores")


class TicketScanFile(Base):
    __tablename__ = "ticket_scan_file"
    __table_args__ = (UniqueConstraint("ticket_id", "version_number", name="uq_ticket_scan_file_ticket_version"), {"schema": "competitor_ticket"})

    ticket_scan_file_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.ticket.ticket_id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(30), default="LOCAL", nullable=False)
    version_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.app_user.user_id"), nullable=False)
    uploaded_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("competitor_ticket.app_user.user_id"), nullable=True)
    confirmed_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_file_id: Mapped[int | None] = mapped_column(ForeignKey("competitor_ticket.ticket_scan_file.ticket_scan_file_id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    ticket = relationship("Ticket", back_populates="scan_files")


class AuditEvent(Base):
    __tablename__ = "audit_event"
    __table_args__ = {"schema": "competitor_ticket"}

    audit_event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_ticket_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("competitor_ticket.app_user.user_id"), nullable=True)
    event_timestamp: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    old_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_details_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("AppUser")
