"""
Migration v11: Add ticket_enrichment table for Phase 2 enrichment review.

Run: python scripts/migrate_v11_add_enrichment.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy import text
from app.db.session import engine

SQL = """
CREATE TABLE IF NOT EXISTS competitor_ticket.ticket_enrichment (
    enrichment_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES competitor_ticket.ticket(ticket_id),
    ocr_result_id BIGINT NOT NULL REFERENCES competitor_ticket.ocr_result(ocr_id),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    reviewed_by_user_id BIGINT REFERENCES competitor_ticket.app_user(user_id),
    reviewed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def main():
    print("Running migration v11 (add ticket_enrichment table)...")
    with engine.begin() as conn:
        conn.execute(text(SQL))
    print("Migration v11 completed. Table created:")
    print("  - competitor_ticket.ticket_enrichment")


if __name__ == '__main__':
    main()
