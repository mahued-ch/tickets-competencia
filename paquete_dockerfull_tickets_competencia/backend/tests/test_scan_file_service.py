from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.sql.elements import TextClause
from app.services.scan_file_service import validate_upload_basics, upload_or_replace_scan_file, confirm_scan_file
from app.models.ticket import TicketStore, TicketScanFile


STORE_FILE = {
    'file_name': 'scan.pdf',
    'extension': 'pdf',
    'mime_type': 'application/pdf',
    'size': 1024,
    'hash': 'abc123def456',
    'path': '/tmp/storage/scan.pdf',
    'provider': 'LOCAL',
}


# ── helpers ───────────────────────────────────────────────

def _mock_pg_execute(db_session, return_row):
    """Return a side_effect that mocks only PostgreSQL function calls via db.execute,
    letting ORM queries pass through to the real execute."""
    original = db_session.execute

    def side_effect(*args, **kwargs):
        stmt = args[0] if args else kwargs.get('statement')
        if isinstance(stmt, TextClause):
            mock_result = MagicMock()
            mock_result.fetchone.return_value = return_row
            return mock_result
        return original(*args, **kwargs)

    return side_effect


def _mock_pg_execute_none(db_session):
    """Like _mock_pg_execute but returns None (simulating no active scan file)."""
    return _mock_pg_execute(db_session, None)


# ── validate_upload_basics ────────────────────────────────

def test_validate_passes_for_store_user_on_own_ticket(store_user_ctx, seed_ticket):
    validate_upload_basics(seed_ticket, store_user_ctx)


def test_validate_raises_permission_error_for_store_user_on_other_ticket(store_user_ctx, seed_ticket, db_session):
    db_session.query(TicketStore).filter(TicketStore.ticket_id == seed_ticket.ticket_id).delete()
    db_session.commit()
    db_session.refresh(seed_ticket)
    with pytest.raises(PermissionError, match="Forbidden"):
        validate_upload_basics(seed_ticket, store_user_ctx)


def test_validate_raises_value_error_when_source_status_not_9(store_user_ctx, seed_ticket):
    seed_ticket.source_status_code = '5'
    with pytest.raises(ValueError, match="SCAN_UPLOAD_NOT_ALLOWED_BY_SOURCE_STATUS"):
        validate_upload_basics(seed_ticket, store_user_ctx)


# ── upload_or_replace_scan_file ──────────────────────────

def test_upload_success_as_supervisor(seed_ticket, supervisor_ctx, db_session):
    mock_row = MagicMock()
    mock_row.new_ticket_scan_file_id = 100
    mock_row.new_version_number = 1
    mock_row.previous_ticket_scan_file_id = None

    side_effect = _mock_pg_execute(db_session, mock_row)
    with patch.object(db_session, 'execute', side_effect=side_effect):
        result = upload_or_replace_scan_file(db_session, supervisor_ctx, seed_ticket.ticket_id, STORE_FILE)

    assert result['ticketScanFileId'] == 100
    assert result['versionNumber'] == 1
    assert result['previousTicketScanFileId'] is None
    assert result['ticketId'] == seed_ticket.ticket_id


def test_upload_success_as_supervisor_with_notes(seed_ticket, supervisor_ctx, db_session):
    mock_row = MagicMock()
    mock_row.new_ticket_scan_file_id = 101
    mock_row.new_version_number = 1
    mock_row.previous_ticket_scan_file_id = None

    side_effect = _mock_pg_execute(db_session, mock_row)
    with patch.object(db_session, 'execute', side_effect=side_effect):
        result = upload_or_replace_scan_file(db_session, supervisor_ctx, seed_ticket.ticket_id, STORE_FILE, notes='Primera carga')

    assert result['ticketScanFileId'] == 101
    assert result['versionNumber'] == 1


def test_upload_success_replaces_previous(seed_ticket_with_scan, supervisor_ctx, db_session):
    mock_row = MagicMock()
    mock_row.new_ticket_scan_file_id = 102
    mock_row.new_version_number = 2
    mock_row.previous_ticket_scan_file_id = 1

    side_effect = _mock_pg_execute(db_session, mock_row)
    with patch.object(db_session, 'execute', side_effect=side_effect):
        result = upload_or_replace_scan_file(db_session, supervisor_ctx, seed_ticket_with_scan.ticket_id, STORE_FILE)

    assert result['ticketScanFileId'] == 102
    assert result['versionNumber'] == 2
    assert result['previousTicketScanFileId'] == 1


def test_upload_success_as_store_user(seed_ticket, store_user_ctx, db_session):
    mock_row = MagicMock()
    mock_row.new_ticket_scan_file_id = 103
    mock_row.new_version_number = 1
    mock_row.previous_ticket_scan_file_id = None

    side_effect = _mock_pg_execute(db_session, mock_row)
    with patch.object(db_session, 'execute', side_effect=side_effect):
        result = upload_or_replace_scan_file(db_session, store_user_ctx, seed_ticket.ticket_id, STORE_FILE)

    assert result['ticketScanFileId'] == 103


def test_upload_raises_lookup_error_for_missing_ticket(supervisor_ctx, db_session):
    with pytest.raises(LookupError, match="Ticket not found"):
        upload_or_replace_scan_file(db_session, supervisor_ctx, 99999, STORE_FILE)


def test_upload_raises_permission_error(store_user_ctx, seed_ticket, db_session):
    db_session.query(TicketStore).filter(TicketStore.ticket_id == seed_ticket.ticket_id).delete()
    db_session.commit()
    with pytest.raises(PermissionError, match="Forbidden"):
        upload_or_replace_scan_file(db_session, store_user_ctx, seed_ticket.ticket_id, STORE_FILE)


def test_upload_raises_value_error_on_bad_source_status(supervisor_ctx, seed_ticket, db_session):
    seed_ticket.source_status_code = '5'
    db_session.commit()
    with pytest.raises(ValueError, match="SCAN_UPLOAD_NOT_ALLOWED_BY_SOURCE_STATUS"):
        upload_or_replace_scan_file(db_session, supervisor_ctx, seed_ticket.ticket_id, STORE_FILE)


def test_upload_raises_value_error_when_already_confirmed(seed_ticket_with_scan, supervisor_ctx, db_session):
    sf = db_session.query(TicketScanFile).filter(TicketScanFile.ticket_id == seed_ticket_with_scan.ticket_id).first()
    sf.is_confirmed = True
    seed_ticket_with_scan.scan_status = 'FILE_CONFIRMED'
    db_session.commit()

    with pytest.raises(ValueError, match="SCAN_FILE_ALREADY_CONFIRMED"):
        upload_or_replace_scan_file(db_session, supervisor_ctx, seed_ticket_with_scan.ticket_id, STORE_FILE)


# ── confirm_scan_file ─────────────────────────────────────

def test_confirm_success_as_supervisor(seed_ticket_with_scan, supervisor_ctx, db_session):
    mock_row = MagicMock()
    mock_row.ticket_scan_file_id = 1
    mock_row.ticket_id = seed_ticket_with_scan.ticket_id
    mock_row.version_number = 1
    mock_row.confirmed_at = '2026-06-22T12:00:00Z'

    side_effect = _mock_pg_execute(db_session, mock_row)
    with patch.object(db_session, 'execute', side_effect=side_effect):
        result = confirm_scan_file(db_session, supervisor_ctx, seed_ticket_with_scan.ticket_id)

    assert result['ticketScanFileId'] == 1
    assert result['ticketId'] == seed_ticket_with_scan.ticket_id
    assert result['versionNumber'] == 1


def test_confirm_with_notes(seed_ticket_with_scan, supervisor_ctx, db_session):
    mock_row = MagicMock()
    mock_row.ticket_scan_file_id = 1
    mock_row.ticket_id = seed_ticket_with_scan.ticket_id
    mock_row.version_number = 1
    mock_row.confirmed_at = '2026-06-22T12:00:00Z'

    side_effect = _mock_pg_execute(db_session, mock_row)
    with patch.object(db_session, 'execute', side_effect=side_effect):
        result = confirm_scan_file(db_session, supervisor_ctx, seed_ticket_with_scan.ticket_id, notes='Confirmado')

    assert result['ticketScanFileId'] == 1


def test_confirm_raises_lookup_error_for_missing_ticket(supervisor_ctx, db_session):
    with pytest.raises(LookupError, match="Ticket not found"):
        confirm_scan_file(db_session, supervisor_ctx, 99999)


def test_confirm_raises_permission_error(store_user_ctx, seed_ticket_with_scan, db_session):
    db_session.query(TicketStore).filter(TicketStore.ticket_id == seed_ticket_with_scan.ticket_id).delete()
    db_session.commit()
    with pytest.raises(PermissionError, match="Forbidden"):
        confirm_scan_file(db_session, store_user_ctx, seed_ticket_with_scan.ticket_id)


def test_confirm_raises_lookup_error_when_no_active_file(seed_ticket_with_scan, supervisor_ctx, db_session):
    side_effect = _mock_pg_execute_none(db_session)
    with patch.object(db_session, 'execute', side_effect=side_effect):
        with pytest.raises(LookupError, match="ACTIVE_SCAN_FILE_NOT_FOUND"):
            confirm_scan_file(db_session, supervisor_ctx, seed_ticket_with_scan.ticket_id)
