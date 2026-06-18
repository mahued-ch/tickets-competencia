from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class IntegrationBatch(Base):
    __tablename__ = "integration_batch"
    __table_args__ = {"schema": "competitor_ticket"}

    batch_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_code: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(30), default="AS400", nullable=False)
    source_directory: Mapped[str] = mapped_column(String(500), nullable=False)
    archive_directory: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_directory: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    header_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    item_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    store_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inserted_ticket_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_ticket_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    files = relationship("IntegrationFile", back_populates="batch", cascade="all, delete-orphan")
    errors = relationship("IntegrationError", back_populates="batch", cascade="all, delete-orphan")


class IntegrationFile(Base):
    __tablename__ = "integration_file"
    __table_args__ = {"schema": "competitor_ticket"}

    integration_file_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.integration_batch.batch_id"), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    archived_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    batch = relationship("IntegrationBatch", back_populates="files")


class IntegrationError(Base):
    __tablename__ = "integration_error"
    __table_args__ = {"schema": "competitor_ticket"}

    integration_error_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.integration_batch.batch_id"), nullable=False)
    integration_file_id: Mapped[int | None] = mapped_column(ForeignKey("competitor_ticket.integration_file.integration_file_id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ticket_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)

    batch = relationship("IntegrationBatch", back_populates="errors")
