"""
Migration v5: Add all missing columns from AS400 export schema.

Fields added:
  - inbound_ticket_header: source_ticket_time, zone_code, terminal_code, subsidiary_code, user_code
  - inbound_ticket_item:   source_ticket_time, department_code, sub_department_code, class_code,
                           subclass_code, provider_code
  - inbound_ticket_store:  source_ticket_time
  - ticket:                source_ticket_time, zone_code, terminal_code, subsidiary_code, user_code
  - ticket_item:           department_code, sub_department_code, class_code, subclass_code,
                           provider_code
  - Also widened source_ticket_code to VARCHAR(35) and source_business_code to VARCHAR(10)
    to match actual AS400 column widths.

Run: python scripts/migrate_v5_add_as400_columns.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy import text
from app.db.session import engine


SQL_STATEMENTS = [
    # ── inbound_ticket_header ──
    "ALTER TABLE competitor_ticket.inbound_ticket_header ALTER COLUMN source_ticket_code TYPE VARCHAR(35)",
    "ALTER TABLE competitor_ticket.inbound_ticket_header ALTER COLUMN source_business_code TYPE VARCHAR(10)",
    "ALTER TABLE competitor_ticket.inbound_ticket_header ADD COLUMN IF NOT EXISTS source_ticket_time VARCHAR(8)",
    "ALTER TABLE competitor_ticket.inbound_ticket_header ADD COLUMN IF NOT EXISTS zone_code SMALLINT",
    "ALTER TABLE competitor_ticket.inbound_ticket_header ADD COLUMN IF NOT EXISTS terminal_code INTEGER",
    "ALTER TABLE competitor_ticket.inbound_ticket_header ADD COLUMN IF NOT EXISTS subsidiary_code INTEGER",
    "ALTER TABLE competitor_ticket.inbound_ticket_header ADD COLUMN IF NOT EXISTS user_code VARCHAR(10)",

    # ── inbound_ticket_item ──
    "ALTER TABLE competitor_ticket.inbound_ticket_item ALTER COLUMN source_ticket_code TYPE VARCHAR(35)",
    "ALTER TABLE competitor_ticket.inbound_ticket_item ALTER COLUMN source_business_code TYPE VARCHAR(10)",
    "ALTER TABLE competitor_ticket.inbound_ticket_item ADD COLUMN IF NOT EXISTS source_ticket_time VARCHAR(8)",
    "ALTER TABLE competitor_ticket.inbound_ticket_item ADD COLUMN IF NOT EXISTS department_code SMALLINT",
    "ALTER TABLE competitor_ticket.inbound_ticket_item ADD COLUMN IF NOT EXISTS sub_department_code SMALLINT",
    "ALTER TABLE competitor_ticket.inbound_ticket_item ADD COLUMN IF NOT EXISTS class_code SMALLINT",
    "ALTER TABLE competitor_ticket.inbound_ticket_item ADD COLUMN IF NOT EXISTS subclass_code SMALLINT",
    "ALTER TABLE competitor_ticket.inbound_ticket_item ADD COLUMN IF NOT EXISTS provider_code INTEGER",

    # ── inbound_ticket_store ──
    "ALTER TABLE competitor_ticket.inbound_ticket_store ALTER COLUMN source_ticket_code TYPE VARCHAR(35)",
    "ALTER TABLE competitor_ticket.inbound_ticket_store ALTER COLUMN source_business_code TYPE VARCHAR(10)",
    "ALTER TABLE competitor_ticket.inbound_ticket_store ADD COLUMN IF NOT EXISTS source_ticket_time VARCHAR(8)",

    # ── ticket ──
    "ALTER TABLE competitor_ticket.ticket ALTER COLUMN source_ticket_code TYPE VARCHAR(35)",
    "ALTER TABLE competitor_ticket.ticket ALTER COLUMN source_business_code TYPE VARCHAR(10)",
    "ALTER TABLE competitor_ticket.ticket ADD COLUMN IF NOT EXISTS source_ticket_time VARCHAR(8)",
    "ALTER TABLE competitor_ticket.ticket ADD COLUMN IF NOT EXISTS zone_code SMALLINT",
    "ALTER TABLE competitor_ticket.ticket ADD COLUMN IF NOT EXISTS terminal_code INTEGER",
    "ALTER TABLE competitor_ticket.ticket ADD COLUMN IF NOT EXISTS subsidiary_code INTEGER",
    "ALTER TABLE competitor_ticket.ticket ADD COLUMN IF NOT EXISTS user_code VARCHAR(10)",

    # ── ticket_item ──
    "ALTER TABLE competitor_ticket.ticket_item ADD COLUMN IF NOT EXISTS department_code SMALLINT",
    "ALTER TABLE competitor_ticket.ticket_item ADD COLUMN IF NOT EXISTS sub_department_code SMALLINT",
    "ALTER TABLE competitor_ticket.ticket_item ADD COLUMN IF NOT EXISTS class_code SMALLINT",
    "ALTER TABLE competitor_ticket.ticket_item ADD COLUMN IF NOT EXISTS subclass_code SMALLINT",
    "ALTER TABLE competitor_ticket.ticket_item ADD COLUMN IF NOT EXISTS provider_code INTEGER",
]


def main():
    print("Running migration v5 (add AS400 columns)...")
    with engine.begin() as conn:
        for sql in SQL_STATEMENTS:
            print(f"  EXEC: {sql[:80]}...")
            conn.execute(text(sql))
    print("Migration v5 completed.")


if __name__ == '__main__':
    main()
