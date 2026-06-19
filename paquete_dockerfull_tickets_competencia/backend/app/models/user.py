from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AppRole(Base):
    __tablename__ = "app_role"
    __table_args__ = {"schema": "competitor_ticket"}

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AppUser(Base):
    __tablename__ = "app_user"
    __table_args__ = {"schema": "competitor_ticket"}

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    login_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.app_role.role_id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role = relationship("AppRole")
    stores = relationship("AppUserStore", back_populates="user", cascade="all, delete-orphan")


class AppUserStore(Base):
    __tablename__ = "app_user_store"
    __table_args__ = (
        UniqueConstraint("user_id", "store_code", name="uq_app_user_store"),
        {"schema": "competitor_ticket"},
    )

    app_user_store_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("competitor_ticket.app_user.user_id"), nullable=False)
    store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("AppUser", back_populates="stores")
