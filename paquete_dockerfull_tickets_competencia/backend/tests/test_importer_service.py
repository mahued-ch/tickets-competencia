import json
from pathlib import Path
import pytest
from app.services.importer_service import ImporterService
from app.models.integration import IntegrationBatch, IntegrationFile, IntegrationError
from app.models.ticket import Ticket, TicketItem, TicketStore
from app.models.inbound import InboundTicketHeader, InboundTicketItem, InboundTicketStore


# ── helpers ───────────────────────────────────────────────

def _build_dir(tmp_path: Path, name: str) -> Path:
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_json(dir_path: Path, file_name: str, data) -> Path:
    fpath = dir_path / file_name
    fpath.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return fpath


def _make_service(db_session, tmp_path) -> ImporterService:
    inbound = _build_dir(tmp_path, 'inbound')
    archive = _build_dir(tmp_path, 'archive')
    error_dir = _build_dir(tmp_path, 'error')
    svc = ImporterService(db_session)
    svc.inbound = inbound
    svc.archive = archive
    svc.error_dir = error_dir
    return svc


CONTROL = {"batchCode": "BATCH001", "createdAt": "2026-06-22T10:00:00Z"}

HEADERS = [
    {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_status_code": "9"},
    {"source_ticket_code": "TKT002", "source_business_code": "BUS001", "source_store_code": "0456", "source_ticket_date": "2026-06-22", "source_status_code": "9"},
]

ITEMS = [
    {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_item_sequence": 1, "product_code": "P001", "product_description": "Producto A", "quantity": 2, "unit_price": 10.50, "line_amount": 21.00},
    {"source_ticket_code": "TKT002", "source_business_code": "BUS001", "source_store_code": "0456", "source_ticket_date": "2026-06-22", "source_item_sequence": 1, "product_code": "P002", "quantity": 5, "unit_price": 3.00, "line_amount": 15.00},
]

STORES = [
    {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0123"},
    {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0789"},
    {"source_ticket_code": "TKT002", "source_business_code": "BUS001", "source_store_code": "0456", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0456"},
]


# ── Happy path ────────────────────────────────────────────

class TestProcessBatchSuccess:

    def test_inserts_tickets_and_moves_to_archive(self, db_session, tmp_path):
        svc = _make_service(db_session, tmp_path)
        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)
        _write_json(svc.inbound, 'header_BATCH001.json', HEADERS)
        _write_json(svc.inbound, 'items_BATCH001.json', ITEMS)
        _write_json(svc.inbound, 'stores_BATCH001.json', STORES)

        result = svc.process_batch('BATCH001')

        assert result['status'] == 'ARCHIVED'
        assert result['inserted'] == 2
        assert result['skipped'] == 0
        assert result['errors'] == 0

        batch = db_session.query(IntegrationBatch).filter_by(batch_code='BATCH001').first()
        assert batch is not None
        assert batch.status == 'ARCHIVED'
        assert batch.header_record_count == 2
        assert batch.item_record_count == 2
        assert batch.store_record_count == 3

        assert db_session.query(Ticket).count() == 2
        assert db_session.query(TicketItem).count() == 2
        assert db_session.query(TicketStore).count() == 3

        t1 = db_session.query(Ticket).filter(Ticket.source_ticket_key == 'TKT001|BUS001|0123|20260622').first()
        assert t1 is not None
        assert t1.source_ticket_code == 'TKT001'
        assert t1.scan_status == 'NO_FILE'
        assert t1.has_scan_file is False
        assert len(t1.items) == 1
        assert len(t1.stores) == 2

        assert db_session.query(InboundTicketHeader).filter_by(is_processed=True).count() == 2

        assert not list(svc.inbound.glob('*'))
        archived = list(svc.archive.glob('*'))
        assert len(archived) == 4

    def test_skips_tickets_already_in_database(self, db_session, tmp_path):
        svc = _make_service(db_session, tmp_path)
        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)
        _write_json(svc.inbound, 'header_BATCH001.json', HEADERS)
        _write_json(svc.inbound, 'items_BATCH001.json', ITEMS)
        _write_json(svc.inbound, 'stores_BATCH001.json', STORES)

        r1 = svc.process_batch('BATCH001')
        assert r1['inserted'] == 2
        assert r1['skipped'] == 0

        # second run with different batch_code but same ticket data
        _write_json(svc.inbound, 'control_BATCH002.json', {"batchCode": "BATCH002", "createdAt": "2026-06-22T11:00:00Z"})
        _write_json(svc.inbound, 'header_BATCH002.json', HEADERS)
        _write_json(svc.inbound, 'items_BATCH002.json', ITEMS)
        _write_json(svc.inbound, 'stores_BATCH002.json', STORES)

        r2 = svc.process_batch('BATCH002')
        assert r2['inserted'] == 0
        assert r2['skipped'] == 2
        assert r2['errors'] == 0

        assert db_session.query(Ticket).count() == 2

    def test_run_pending_batches(self, db_session, tmp_path):
        svc = _make_service(db_session, tmp_path)

        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)
        _write_json(svc.inbound, 'header_BATCH001.json', HEADERS)
        _write_json(svc.inbound, 'items_BATCH001.json', ITEMS)
        _write_json(svc.inbound, 'stores_BATCH001.json', STORES)

        h2 = [{"source_ticket_code": "TKT003", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-23", "source_status_code": "9"}]
        i2 = [{"source_ticket_code": "TKT003", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-23", "source_item_sequence": 1, "product_code": "P003", "quantity": 1, "unit_price": 100, "line_amount": 100}]
        s2 = [{"source_ticket_code": "TKT003", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-23", "applies_to_store_code": "0123"}]

        _write_json(svc.inbound, 'control_BATCH002.json', {"batchCode": "BATCH002", "createdAt": "2026-06-23T10:00:00Z"})
        _write_json(svc.inbound, 'header_BATCH002.json', h2)
        _write_json(svc.inbound, 'items_BATCH002.json', i2)
        _write_json(svc.inbound, 'stores_BATCH002.json', s2)

        results = svc.run_pending_batches()

        assert len(results) == 2
        assert results[0]['status'] == 'ARCHIVED'
        assert results[0]['batchCode'] == 'BATCH001'
        assert results[0]['inserted'] == 2
        assert results[1]['status'] == 'ARCHIVED'
        assert results[1]['batchCode'] == 'BATCH002'
        assert results[1]['inserted'] == 1

        assert db_session.query(Ticket).count() == 3
        assert db_session.query(IntegrationBatch).count() == 2


# ── Error scenarios ───────────────────────────────────────

class TestProcessBatchErrors:

    def test_missing_files(self, db_session, tmp_path):
        svc = _make_service(db_session, tmp_path)
        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)

        result = svc.process_batch('BATCH001')

        assert result['status'] == 'FAILED'
        assert 'missing' in result
        assert 'HEADER' in result['missing']
        assert 'ITEM' in result['missing']
        assert 'STORE' in result['missing']

    def test_parse_error_in_header(self, db_session, tmp_path):
        svc = _make_service(db_session, tmp_path)
        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)
        (svc.inbound / 'header_BATCH001.json').write_text('not valid json', encoding='utf-8')
        _write_json(svc.inbound, 'items_BATCH001.json', ITEMS)
        _write_json(svc.inbound, 'stores_BATCH001.json', STORES)

        result = svc.process_batch('BATCH001')

        assert result['status'] == 'FAILED'
        assert 'parseErrors' in result
        assert any(e['file'] == 'header_BATCH001.json' for e in result['parseErrors'])

    def test_parse_error_in_items(self, db_session, tmp_path):
        svc = _make_service(db_session, tmp_path)
        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)
        _write_json(svc.inbound, 'header_BATCH001.json', HEADERS)
        (svc.inbound / 'items_BATCH001.json').write_text('{bad json', encoding='utf-8')
        _write_json(svc.inbound, 'stores_BATCH001.json', STORES)

        result = svc.process_batch('BATCH001')

        assert result['status'] == 'FAILED'
        assert 'parseErrors' in result

    def test_all_errors_batch_fails(self, db_session, tmp_path):
        """When all headers fail during insert and no tickets are inserted, batch should FAIL."""
        svc = _make_service(db_session, tmp_path)
        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)
        _write_json(svc.inbound, 'header_BATCH001.json', HEADERS)
        _write_json(svc.inbound, 'items_BATCH001.json', ITEMS)
        _write_json(svc.inbound, 'stores_BATCH001.json', STORES)

        for fpath in svc.inbound.glob('*.json'):
            fpath.unlink()

        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)
        bad_headers = [
            {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "source_status_code": "9"},
        ]
        _write_json(svc.inbound, 'header_BATCH001.json', bad_headers)
        _write_json(svc.inbound, 'items_BATCH001.json', ITEMS)
        _write_json(svc.inbound, 'stores_BATCH001.json', STORES)

        result = svc.process_batch('BATCH001')

        assert result['status'] == 'FAILED'
        assert result['inserted'] == 0
        assert result['errors'] > 0

        batch = db_session.query(IntegrationBatch).filter_by(batch_code='BATCH001').first()
        assert batch is not None
        assert batch.status == 'FAILED'
        assert db_session.query(IntegrationError).filter_by(batch_id=batch.batch_id).count() > 0

        error_files = list(svc.error_dir.glob('*'))
        assert len(error_files) == 4

    def test_partial_success_with_some_consolidation_errors(self, db_session, tmp_path):
        """When one header has invalid date and fails consolidation, the batch still processes the valid ones."""
        svc = _make_service(db_session, tmp_path)
        _write_json(svc.inbound, 'control_BATCH001.json', CONTROL)

        mixed_headers = [
            {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_status_code": "9"},
            {"source_ticket_code": "TKT999", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "source_status_code": "9"},
        ]
        _write_json(svc.inbound, 'header_BATCH001.json', mixed_headers)

        items_both = [
            {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_item_sequence": 1, "product_code": "P001", "quantity": 1, "unit_price": 10, "line_amount": 10},
            {"source_ticket_code": "TKT999", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "source_item_sequence": 1, "product_code": "P999", "quantity": 1, "unit_price": 10, "line_amount": 10},
        ]
        _write_json(svc.inbound, 'items_BATCH001.json', items_both)

        stores_both = [
            {"source_ticket_code": "TKT001", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0123"},
            {"source_ticket_code": "TKT999", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "applies_to_store_code": "0123"},
        ]
        _write_json(svc.inbound, 'stores_BATCH001.json', stores_both)

        result = svc.process_batch('BATCH001')

        assert result['status'] == 'ARCHIVED'
        assert result['inserted'] == 1
        assert result['errors'] > 0

        batch = db_session.query(IntegrationBatch).filter_by(batch_code='BATCH001').first()
        assert batch is not None
        assert db_session.query(IntegrationError).filter_by(batch_id=batch.batch_id).count() == result['errors']

        assert db_session.query(Ticket).count() == 1
        assert db_session.query(Ticket).filter(Ticket.source_ticket_code == 'TKT001').first() is not None
        assert db_session.query(Ticket).filter(Ticket.source_ticket_code == 'TKT999').first() is None
