"""Vacía tablas de tickets y archivos JSON para re-importar."""

import os
from pathlib import Path
import psycopg2
from urllib.parse import urlparse

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://tickets_user:tickets_pass@localhost:5432/tickets_db",
)
conn_str = DB_URL.replace("+psycopg2", "").replace("+psycopg", "")

parsed = urlparse(conn_str)
conn = psycopg2.connect(
    host=parsed.hostname or "localhost",
    port=parsed.port or 5432,
    dbname=parsed.path.lstrip("/"),
    user=parsed.username,
    password=parsed.password,
)
conn.autocommit = True
cur = conn.cursor()

TABLES = [
    "competitor_ticket.ticket_scan_file",
    "competitor_ticket.ticket_item",
    "competitor_ticket.ticket_store",
    "competitor_ticket.ticket",
    "competitor_ticket.inbound_ticket_store",
    "competitor_ticket.inbound_ticket_item",
    "competitor_ticket.inbound_ticket_header",
    "competitor_ticket.integration_error",
    "competitor_ticket.integration_file",
    "competitor_ticket.integration_batch",
]

for table in TABLES:
    cur.execute(f"DELETE FROM {table}")
    print(f"  {table}: vaciada")

cur.close()
conn.close()

JSON_DIRS = ["data/inbound/ARCHIVE", "data/inbound/ERROR"]
base = Path(__file__).resolve().parent.parent
for rel in JSON_DIRS:
    d = base / rel
    for f in d.glob("*.json"):
        f.unlink()
        print(f"  eliminado: {f.relative_to(base)}")

print("Limpieza completa.")
