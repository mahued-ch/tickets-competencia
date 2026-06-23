from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class TicketEnrichment(Base):
    __tablename__ = "ticket_enrichment"
    __table_args__ = {"schema": "competitor_ticket"}

    enrichment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.ticket.ticket_id"), nullable=False)
    ocr_result_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.ocr_result.ocr_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("competitor_ticket.app_user.user_id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ticket = relationship("Ticket")
    ocr_result = relationship("OcrResult")
