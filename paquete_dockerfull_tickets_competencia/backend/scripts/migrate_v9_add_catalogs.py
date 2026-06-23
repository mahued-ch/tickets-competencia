"""
Migration v9: Add catalog tables for Phase 2 enrichment.

Run: python scripts/migrate_v9_add_catalogs.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy import text
from app.db.session import engine

SQL = """
CREATE TABLE IF NOT EXISTS competitor_ticket.competitor_store (
    store_id BIGSERIAL PRIMARY KEY,
    business_code VARCHAR(10) NOT NULL,
    store_code VARCHAR(30) NOT NULL,
    store_name VARCHAR(200),
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT uq_competitor_store_biz_store UNIQUE (business_code, store_code)
);

CREATE TABLE IF NOT EXISTS competitor_ticket.chedraui_product (
    product_id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    upc VARCHAR(20),
    description VARCHAR(255),
    list_price DECIMAL(18, 4),
    department_code SMALLINT,
    sub_department_code SMALLINT,
    class_code SMALLINT,
    subclass_code SMALLINT,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS competitor_ticket.competitor_product_mapping (
    mapping_id BIGSERIAL PRIMARY KEY,
    business_code VARCHAR(10) NOT NULL,
    competitor_code VARCHAR(50),
    competitor_description VARCHAR(255),
    chedraui_product_id BIGINT,
    match_type VARCHAR(20),
    confidence DECIMAL(5, 4),
    is_active BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT uq_cp_mapping_biz_code UNIQUE (business_code, competitor_code)
);

CREATE TABLE IF NOT EXISTS competitor_ticket.nearby_store (
    nearby_id BIGSERIAL PRIMARY KEY,
    business_code VARCHAR(10) NOT NULL,
    store_code VARCHAR(30) NOT NULL,
    nearby_chedraui_store_code VARCHAR(30) NOT NULL,
    distance_km DECIMAL(8, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT uq_nearby_store_triplet UNIQUE (business_code, store_code, nearby_chedraui_store_code)
);
"""


def main():
    print("Running migration v9 (add catalog tables)...")
    with engine.begin() as conn:
        for stmt in SQL.split(";"):
            stripped = stmt.strip()
            if stripped:
                conn.execute(text(stripped + ";"))
    print("Migration v9 completed. Tables created:")
    print("  - competitor_ticket.competitor_store")
    print("  - competitor_ticket.chedraui_product")
    print("  - competitor_ticket.competitor_product_mapping")
    print("  - competitor_ticket.nearby_store")


if __name__ == '__main__':
    main()
