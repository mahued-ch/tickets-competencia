from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, Time, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class InboundTicketHeader(Base):
    __tablename__ = "inbound_ticket_header"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_ticket_key", name="uq_inbound_ticket_header_batch_key"),
        {"schema": "competitor_ticket"},
    )

    inbound_header_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.integration_batch.batch_id"), nullable=False)
    source_ticket_code: Mapped[str] = mapped_column(String(35), nullable=False)
    source_business_code: Mapped[str] = mapped_column(String(10), nullable=False)
    source_store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    source_ticket_date: Mapped = mapped_column(Date, nullable=False)
    source_ticket_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source_ticket_key: Mapped[str] = mapped_column(String(120), nullable=False)
    source_status_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    zone_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    terminal_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subsidiary_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())


class InboundTicketItem(Base):
    __tablename__ = "inbound_ticket_item"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_ticket_key", "source_item_sequence", name="uq_inbound_ticket_item_batch_key_seq"),
        {"schema": "competitor_ticket"},
    )

    inbound_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.integration_batch.batch_id"), nullable=False)
    source_ticket_code: Mapped[str] = mapped_column(String(35), nullable=False)
    source_business_code: Mapped[str] = mapped_column(String(10), nullable=False)
    source_store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    source_ticket_date: Mapped = mapped_column(Date, nullable=False)
    source_ticket_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source_ticket_key: Mapped[str] = mapped_column(String(120), nullable=False)
    source_item_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    department_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sub_department_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    class_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    subclass_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    provider_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    line_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())


class InboundTicketStore(Base):
    __tablename__ = "inbound_ticket_store"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_ticket_key", "applies_to_store_code", name="uq_inbound_ticket_store_batch_key_store"),
        {"schema": "competitor_ticket"},
    )

    inbound_store_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.integration_batch.batch_id"), nullable=False)
    source_ticket_code: Mapped[str] = mapped_column(String(35), nullable=False)
    source_business_code: Mapped[str] = mapped_column(String(10), nullable=False)
    source_store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    source_ticket_date: Mapped = mapped_column(Date, nullable=False)
    source_ticket_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source_ticket_key: Mapped[str] = mapped_column(String(120), nullable=False)
    applies_to_store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
