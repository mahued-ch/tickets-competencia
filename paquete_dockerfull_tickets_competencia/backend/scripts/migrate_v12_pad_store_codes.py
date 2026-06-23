"""Migrate v12: zero-pad Chedraui store codes (< 1000) to 4 digits.

Only applies_to_store_code (tienda Chedraui) receives padding.
source_store_code (tienda competencia) is left unchanged.
"""

from sqlalchemy import text
from app.db.session import engine


def run():
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE competitor_ticket.ticket_store
            SET store_code = LPAD(store_code, 4, '0')
            WHERE store_code ~ '^\d{1,3}$'
        """))
        print(f"  ticket_store: {conn.rowcount} rows updated")

        conn.execute(text("""
            UPDATE competitor_ticket.inbound_ticket_store
            SET applies_to_store_code = LPAD(applies_to_store_code, 4, '0')
            WHERE applies_to_store_code ~ '^\d{1,3}$'
        """))
        print(f"  inbound_ticket_store.applies_to_store_code: {conn.rowcount} rows updated")

    print("Migration v12 complete: Chedraui store codes padded to 4 digits.")


if __name__ == "__main__":
    run()
