import tempfile
from pathlib import Path
import pytest
from sqlalchemy import text
from app.services.scan_file_service import upload_or_replace_scan_file, confirm_scan_file
from app.schemas.security import SecurityContext
from app.models.ticket import Ticket, TicketScanFile, AuditEvent

STORAGE_ROOT = Path(tempfile.mkdtemp(prefix='e2e_storage_'))
STORE_FILE = {
    'file_name': 'e2e_test.pdf',
    'extension': 'pdf',
    'mime_type': 'application/pdf',
    'size': 2048,
    'hash': 'e2e_test_hash_001',
    'path': str(STORAGE_ROOT / 'e2e_test.pdf'),
    'provider': 'LOCAL',
}

V2_FILE = {
    'file_name': 'e2e_v2.pdf',
    'extension': 'pdf',
    'mime_type': 'application/pdf',
    'size': 4096,
    'hash': 'e2e_hash_v2',
    'path': str(STORAGE_ROOT / 'e2e_v2.pdf'),
    'provider': 'LOCAL',
}


def ctx(user_id):
    return SecurityContext(
        user_id=user_id, login_name='e2e_sup',
        display_name='Sup E2E', role_code='SUPERVISOR', store_codes=[],
    )


def _check_function_exists(db, function_name):
    result = db.execute(
        text("SELECT COUNT(*) FROM pg_proc WHERE proname = :name AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'competitor_ticket')"),
        {'name': function_name}
    )
    return result.scalar() > 0


class TestE2eScanFile:

    def test_functions_exist(self, db):
        assert _check_function_exists(db, 'fn_replace_ticket_scan_file')
        assert _check_function_exists(db, 'fn_confirm_ticket_scan_file')

    def test_upload_creates_scan_file_record(self, db, seed_ticket, seed_supervisor):
        c = ctx(seed_supervisor)
        result = upload_or_replace_scan_file(db, c, seed_ticket, STORE_FILE)

        assert result['ticketId'] == seed_ticket
        assert result['versionNumber'] == 1

        sf = db.query(TicketScanFile).filter(
            TicketScanFile.ticket_scan_file_id == result['ticketScanFileId']
        ).first()
        assert sf is not None
        assert sf.file_name == 'e2e_test.pdf'
        assert sf.is_active is True
        assert sf.is_confirmed is False
        assert sf.version_number == 1

    def test_upload_creates_audit_event(self, db, seed_ticket, seed_supervisor):
        c = ctx(seed_supervisor)
        before = db.query(AuditEvent).count()
        result = upload_or_replace_scan_file(db, c, seed_ticket, STORE_FILE)
        assert db.query(AuditEvent).count() == before + 1

        event = db.query(AuditEvent).order_by(AuditEvent.audit_event_id.desc()).first()
        assert event.event_type == 'SCAN_FILE_UPLOADED'
        assert event.entity_name == 'ticket_scan_file'
        assert event.entity_id == result['ticketScanFileId']

    def test_confirm_updates_scan_file(self, db, seed_ticket, seed_supervisor):
        c = ctx(seed_supervisor)
        upload_or_replace_scan_file(db, c, seed_ticket, STORE_FILE)
        r = confirm_scan_file(db, c, seed_ticket)

        assert r['ticketId'] == seed_ticket
        sf = db.query(TicketScanFile).filter(
            TicketScanFile.ticket_scan_file_id == r['ticketScanFileId']
        ).first()
        assert sf.is_confirmed is True
        assert sf.confirmed_at is not None

    def test_confirm_creates_audit_event(self, db, seed_ticket, seed_supervisor):
        c = ctx(seed_supervisor)
        upload_or_replace_scan_file(db, c, seed_ticket, STORE_FILE)
        before = db.query(AuditEvent).count()
        confirm_scan_file(db, c, seed_ticket)
        assert db.query(AuditEvent).count() == before + 1

        event = db.query(AuditEvent).order_by(AuditEvent.audit_event_id.desc()).first()
        assert event.event_type == 'SCAN_FILE_CONFIRMED'

    def test_replace_creates_new_version(self, db, seed_ticket, seed_supervisor):
        c = ctx(seed_supervisor)
        r1 = upload_or_replace_scan_file(db, c, seed_ticket, STORE_FILE)
        assert r1['versionNumber'] == 1

        r2 = upload_or_replace_scan_file(db, c, seed_ticket, V2_FILE)
        assert r2['versionNumber'] == 2
        assert r2['previousTicketScanFileId'] == r1['ticketScanFileId']

        old = db.query(TicketScanFile).filter(
            TicketScanFile.ticket_scan_file_id == r1['ticketScanFileId']
        ).first()
        assert old.is_active is False
        assert old.replaced_by_file_id == r2['ticketScanFileId']

        new = db.query(TicketScanFile).filter(
            TicketScanFile.ticket_scan_file_id == r2['ticketScanFileId']
        ).first()
        assert new.is_active is True
        assert new.file_name == 'e2e_v2.pdf'

    def test_cannot_replace_confirmed_file(self, db, seed_ticket, seed_supervisor):
        c = ctx(seed_supervisor)
        upload_or_replace_scan_file(db, c, seed_ticket, STORE_FILE)
        confirm_scan_file(db, c, seed_ticket)

        with pytest.raises(ValueError, match="SCAN_FILE_ALREADY_CONFIRMED"):
            upload_or_replace_scan_file(db, c, seed_ticket, STORE_FILE)
