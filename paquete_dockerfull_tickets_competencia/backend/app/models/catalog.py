from sqlalchemy import BigInteger, Boolean, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CompetitorStore(Base):
    __tablename__ = "competitor_store"
    __table_args__ = (
        UniqueConstraint("business_code", "store_code", name="uq_competitor_store_biz_store"),
        {"schema": "competitor_ticket"},
    )

    store_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_code: Mapped[str] = mapped_column(String(10), nullable=False)
    store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    store_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ChedrauiProduct(Base):
    __tablename__ = "chedraui_product"
    __table_args__ = {"schema": "competitor_ticket"}

    product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    upc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    list_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    department_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sub_department_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    class_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    subclass_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CompetitorProductMapping(Base):
    __tablename__ = "competitor_product_mapping"
    __table_args__ = (
        UniqueConstraint("business_code", "competitor_code", name="uq_cp_mapping_biz_code"),
        {"schema": "competitor_ticket"},
    )

    mapping_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_code: Mapped[str] = mapped_column(String(10), nullable=False)
    competitor_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    competitor_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chedraui_product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    match_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NearbyStore(Base):
    __tablename__ = "nearby_store"
    __table_args__ = (
        UniqueConstraint("business_code", "store_code", "nearby_chedraui_store_code", name="uq_nearby_store_triplet"),
        {"schema": "competitor_ticket"},
    )

    nearby_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_code: Mapped[str] = mapped_column(String(10), nullable=False)
    store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    nearby_chedraui_store_code: Mapped[str] = mapped_column(String(30), nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
