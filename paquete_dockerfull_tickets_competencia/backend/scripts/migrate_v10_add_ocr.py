"""
Migration v10: Add ocr_result table for Phase 2 OCR processing.

Run: python scripts/migrate_v10_add_ocr.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy import text
from app.db.session import engine

SQL = """
CREATE TABLE IF NOT EXISTS competitor_ticket.ocr_result (
    ocr_id BIGSERIAL PRIMARY KEY,
    ticket_scan_file_id BIGINT NOT NULL REFERENCES competitor_ticket.ticket_scan_file(ticket_scan_file_id),
    raw_text TEXT,
    extracted_items JSONB,
    llm_model VARCHAR(100),
    confidence DECIMAL(5, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def main():
    print("Running migration v10 (add ocr_result table)...")
    with engine.begin() as conn:
        conn.execute(text(SQL))
    print("Migration v10 completed. Table created:")
    print("  - competitor_ticket.ocr_result")


if __name__ == '__main__':
    main()
