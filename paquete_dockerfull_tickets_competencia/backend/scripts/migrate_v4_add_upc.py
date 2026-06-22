"""
Migration v4: Add upc column to inbound_ticket_item and ticket_item.

Run: python scripts/migrate_v4_add_upc.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy import text
from app.db.session import engine


SQL_ALTER_INBOUND = """
ALTER TABLE competitor_ticket.inbound_ticket_item
ADD COLUMN IF NOT EXISTS upc VARCHAR(20);
"""

SQL_ALTER_TICKET = """
ALTER TABLE competitor_ticket.ticket_item
ADD COLUMN IF NOT EXISTS upc VARCHAR(20);
"""


def main():
    print("Running migration v4 (add upc column)...")
    with engine.begin() as conn:
        conn.execute(text(SQL_ALTER_INBOUND))
        conn.execute(text(SQL_ALTER_TICKET))
    print("Migration v4 completed. Columns added:")
    print("  - competitor_ticket.inbound_ticket_item.upc")
    print("  - competitor_ticket.ticket_item.upc")


if __name__ == '__main__':
    main()
