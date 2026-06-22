import pytest
from datetime import date, datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.db.base import Base
from uuid import uuid4
from app.security.password import hash_password
from scripts.migrate_v3_scan_file_functions import SQL_REPLACE, SQL_CONFIRM
from scripts.migrate_v4_add_upc import SQL_ALTER_INBOUND, SQL_ALTER_TICKET
from scripts.migrate_v5_add_as400_columns import SQL_STATEMENTS as SQL_V5

DATABASE_URL = "postgresql+psycopg2://tickets_user:tickets_pass@localhost:5432/tickets_db"
ENGINE = create_engine(DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
def _pg_schema():
    Base.metadata.create_all(bind=ENGINE)
    with ENGINE.begin() as conn:
        conn.execute(text(SQL_REPLACE))
        conn.execute(text(SQL_CONFIRM))
        conn.execute(
            text("ALTER TABLE competitor_ticket.audit_event "
                 "ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)")
        )
        conn.execute(text(SQL_ALTER_INBOUND))
        conn.execute(text(SQL_ALTER_TICKET))
        for sql in SQL_V5:
            conn.execute(text(sql))
    yield


@pytest.fixture
def db(_pg_schema):
    conn = ENGINE.connect()
    session = Session(bind=conn)
    try:
        yield session
    finally:
        conn.close()


def _upsert(db, table, pk_col, data):
    existing = db.execute(
        text(f"SELECT 1 FROM competitor_ticket.{table} WHERE {pk_col}=:pk"),
        {"pk": data[pk_col]}
    ).first()
    if existing:
        return existing
    cols = ", ".join(data.keys())
    vals = ", ".join(f":{k}" for k in data)
    db.execute(
        text(f"INSERT INTO competitor_ticket.{table} ({cols}) VALUES ({vals})"),
        data
    )
    db.flush()


@pytest.fixture
def seed_roles(db):
    roles = {}
    for code, name in [('ADMIN', 'Admin'), ('SUPERVISOR', 'Supervisor'), ('STORE_USER', 'Tienda')]:
        r = db.execute(
            text("SELECT role_id FROM competitor_ticket.app_role WHERE role_code=:c"),
            {"c": code}
        ).first()
        if r:
            roles[code] = r[0]
        else:
            r2 = db.execute(
                text("INSERT INTO competitor_ticket.app_role (role_code, role_name, is_active) "
                     "VALUES (:c, :n, true) RETURNING role_id"),
                {"c": code, "n": name}
            ).first()
            roles[code] = r2[0]
    return roles


@pytest.fixture
def seed_supervisor(seed_roles, db):
    u = db.execute(
        text("SELECT user_id FROM competitor_ticket.app_user WHERE login_name=:l"),
        {"l": "e2e_sup"}
    ).first()
    if u:
        return u[0]
    r = db.execute(
        text("INSERT INTO competitor_ticket.app_user "
             "(login_name, display_name, role_id, password_hash, is_active) "
             "VALUES (:l, :dn, :rid, :ph, true) RETURNING user_id"),
        {"l": "e2e_sup", "dn": "Sup E2E", "rid": seed_roles['SUPERVISOR'],
         "ph": hash_password('demo123')}
    ).first()
    return r[0]


@pytest.fixture
def seed_ticket(seed_supervisor, db):
    uid = uuid4().hex[:8]
    key = f'E2E{uid}|01|0999|20260622'
    batch_id = db.execute(
        text("SELECT batch_id FROM competitor_ticket.integration_batch WHERE batch_code=:bc"),
        {"bc": "E2E_BATCH"}
    ).scalar()
    if not batch_id:
        batch_id = db.execute(
            text("INSERT INTO competitor_ticket.integration_batch "
                 "(batch_code, source_system, source_directory, status, started_at, "
                 "header_record_count, item_record_count, store_record_count, "
                 "inserted_ticket_count, skipped_ticket_count, error_count) "
                 "VALUES (:bc, :ss, :sd, :st, :sa, 0, 0, 0, 0, 0, 0) RETURNING batch_id"),
            {"bc": "E2E_BATCH", "ss": "E2E", "sd": "/tmp/e2e",
             "st": "PROCESSED", "sa": datetime.now()}
        ).scalar()

    ticket_id = db.execute(
        text("SELECT ticket_id FROM competitor_ticket.ticket WHERE source_ticket_key=:k"),
        {"k": key}
    ).scalar()
    if not ticket_id:
        ticket_id = db.execute(
            text("INSERT INTO competitor_ticket.ticket "
                 "(source_ticket_code, source_business_code, source_store_code, "
                 "source_ticket_key, source_ticket_date, source_status_code, "
                 "batch_id, scan_status, has_scan_file) "
                 "VALUES (:stc, :sbc, :ssc, :k, :d, :ss2, :bid, :ss3, false) "
                 "RETURNING ticket_id"),
            {"stc": f"E2E{uid}", "sbc": "01", "ssc": "0999", "k": key,
             "d": date(2026, 6, 22), "ss2": "9", "bid": batch_id, "ss3": "NO_FILE"}
        ).scalar()
        store_exists = db.execute(
            text("SELECT 1 FROM competitor_ticket.ticket_store WHERE "
                 "ticket_id=:tid AND store_code=:sc"),
            {"tid": ticket_id, "sc": "0999"}
        ).first()
        if not store_exists:
            db.execute(
                text("INSERT INTO competitor_ticket.ticket_store (ticket_id, store_code) "
                     "VALUES (:tid, :sc)"),
                {"tid": ticket_id, "sc": "0999"}
            )
    return ticket_id
