import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, Integer, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.schemas.security import SecurityContext
from app.security.auth import get_current_context
from app.models.user import AppRole, AppUser, AppUserStore
from app.models.integration import IntegrationBatch
from app.models.ticket import Ticket, TicketItem, TicketStore, TicketScanFile, AuditEvent
from app.security.password import hash_password

# ── in-memory SQLite for tests ──────────────────────────

TEST_ENGINE = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE)

# SQLite doesn't support PostgreSQL schemas; strip them for tests
@event.listens_for(Base.metadata, "before_create")
def _prepare_sqlite(target, connection, **kw):
    if connection.engine.name == "sqlite":
        for table in target.tables.values():
            table.schema = None
            for column in table.columns:
                for fk in list(column.foreign_keys):
                    fk._colspec = fk._colspec.replace("competitor_ticket.", "")
                # SQLite autoincrement only works with INTEGER type, not BIGINT
                if isinstance(column.type, BigInteger) and column.autoincrement and column.primary_key:
                    column.type = Integer()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── seed data ───────────────────────────────────────────

@pytest.fixture
def seed_roles(db_session):
    roles = {}
    for i, (code, name) in enumerate([('ADMIN', 'Admin'), ('SUPERVISOR', 'Supervisor'), ('STORE_USER', 'Usuario Tienda')], 1):
        r = AppRole(role_id=i, role_code=code, role_name=name, is_active=True)
        db_session.add(r)
        db_session.flush()
        roles[code] = r
    db_session.commit()
    return roles


@pytest.fixture
def seed_admin(seed_roles, db_session):
    u = AppUser(user_id=1, login_name='admin', display_name='Admin', role_id=seed_roles['ADMIN'].role_id, is_active=True, password_hash=hash_password('demo123'))
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def seed_supervisor(seed_roles, db_session):
    u = AppUser(user_id=2, login_name='supervisor', display_name='Supervisor', role_id=seed_roles['SUPERVISOR'].role_id, is_active=True, password_hash=hash_password('demo123'))
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def seed_store_user(seed_roles, db_session):
    u = AppUser(user_id=3, login_name='store_a', display_name='Tienda A', role_id=seed_roles['STORE_USER'].role_id, is_active=True, password_hash=hash_password('demo123'))
    db_session.add(u)
    db_session.flush()
    db_session.add(AppUserStore(app_user_store_id=1, user_id=u.user_id, store_code='0123'))
    db_session.add(AppUserStore(app_user_store_id=2, user_id=u.user_id, store_code='0789'))
    db_session.commit()
    return u


@pytest.fixture
def seed_ticket(seed_roles, db_session):
    batch = IntegrationBatch(batch_id=1, batch_code='20260619_000000', source_system='TEST', source_directory='/tmp', status='PROCESSED')
    db_session.add(batch)
    db_session.flush()
    t = Ticket(
        ticket_id=1,
        source_ticket_code='TKT001', source_business_code='01', source_store_code='0123',
        source_ticket_key='TKT001|01|0123|20260619', source_ticket_date=date(2026, 6, 19),
        source_status_code='9', batch_id=batch.batch_id,
        scan_status='NO_FILE', has_scan_file=False,
    )
    db_session.add(t)
    db_session.flush()
    db_session.add(TicketItem(ticket_item_id=1, ticket_id=t.ticket_id, item_sequence=1, product_code='P001', quantity=2, unit_price=10, line_amount=20))
    db_session.add(TicketStore(ticket_store_id=1, ticket_id=t.ticket_id, store_code='0123'))
    db_session.add(TicketStore(ticket_store_id=2, ticket_id=t.ticket_id, store_code='0789'))
    db_session.commit()
    return t


@pytest.fixture
def seed_ticket_with_scan(seed_ticket, db_session):
    t = seed_ticket
    sf = TicketScanFile(
        ticket_scan_file_id=1,
        ticket_id=t.ticket_id, file_name='scan.pdf', file_extension='pdf', mime_type='application/pdf',
        file_size_bytes=100, file_hash='abc123', storage_path='/tmp/scan.pdf', storage_provider='LOCAL',
        version_number=1, is_active=True, is_confirmed=False, uploaded_by_user_id=1,
    )
    db_session.add(sf)
    t.has_scan_file = True
    t.scan_status = 'FILE_UPLOADED'
    db_session.commit()
    return t


# ── helper to build SecurityContext ─────────────────────

def _build_ctx(db_session, login_name):
    user = db_session.query(AppUser).filter(AppUser.login_name == login_name).first()
    if not user:
        return SecurityContext(user_id=0, login_name=login_name, display_name=login_name, role_code='STORE_USER', store_codes=[])
    store_codes = [s.store_code for s in db_session.query(AppUserStore).filter(AppUserStore.user_id == user.user_id).all()]
    return SecurityContext(
        user_id=user.user_id,
        login_name=user.login_name,
        display_name=user.display_name,
        role_code=user.role.role_code,
        store_codes=store_codes,
    )


@pytest.fixture
def supervisor_ctx(db_session, seed_roles, seed_supervisor):
    return _build_ctx(db_session, 'supervisor')


@pytest.fixture
def admin_ctx(db_session, seed_roles, seed_admin):
    return _build_ctx(db_session, 'admin')


@pytest.fixture
def store_user_ctx(db_session, seed_roles, seed_store_user):
    return _build_ctx(db_session, 'store_a')


# ── FastAPI test client with overridden deps ────────────

@pytest.fixture
def client(db_session):
    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client_with_supervisor(db_session, seed_roles, seed_supervisor):
    ctx = _build_ctx(db_session, 'supervisor')

    def _get_db():
        yield db_session

    def _get_ctx():
        yield ctx

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_context] = _get_ctx
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_context, None)


@pytest.fixture
def client_with_store_user(db_session, seed_roles, seed_store_user):
    ctx = _build_ctx(db_session, 'store_a')

    def _get_db():
        yield db_session

    def _get_ctx():
        yield ctx

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_context] = _get_ctx
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_context, None)
