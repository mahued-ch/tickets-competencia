from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, Text, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class OcrResult(Base):
    __tablename__ = "ocr_result"
    __table_args__ = {"schema": "competitor_ticket"}

    ocr_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_scan_file_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.ticket_scan_file.ticket_scan_file_id"), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scan_file = relationship("TicketScanFile")
