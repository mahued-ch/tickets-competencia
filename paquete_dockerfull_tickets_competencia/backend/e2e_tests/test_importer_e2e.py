import json
from pathlib import Path
from uuid import uuid4
import pytest
from app.services.importer_service import ImporterService
from app.models.integration import IntegrationBatch, IntegrationError
from app.models.ticket import Ticket, TicketItem, TicketStore
from app.models.inbound import InboundTicketHeader, InboundTicketItem, InboundTicketStore


def _write_json(dir_path: Path, file_name: str, data) -> Path:
    fpath = dir_path / file_name
    fpath.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return fpath


def _make_service(db, tmp_path: Path) -> ImporterService:
    inbound = tmp_path / 'inbound'
    archive = tmp_path / 'archive'
    error_dir = tmp_path / 'error'
    for d in (inbound, archive, error_dir):
        d.mkdir(parents=True, exist_ok=True)
    svc = ImporterService(db)
    svc.inbound = inbound
    svc.archive = archive
    svc.error_dir = error_dir
    return svc


def _headers(suffix: str, count: int = 2):
    return [
        {"source_ticket_code": f"E2E_IMP_{suffix}_T1", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_status_code": "9"},
        {"source_ticket_code": f"E2E_IMP_{suffix}_T2", "source_business_code": "BUS001", "source_store_code": "0456", "source_ticket_date": "2026-06-22", "source_status_code": "9"},
    ][:count]


def _items(suffix: str, count: int = 2):
    return [
        {"source_ticket_code": f"E2E_IMP_{suffix}_T1", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_item_sequence": 1, "product_code": "P001", "product_description": "Producto A", "quantity": 2, "unit_price": 10.50, "line_amount": 21.00},
        {"source_ticket_code": f"E2E_IMP_{suffix}_T2", "source_business_code": "BUS001", "source_store_code": "0456", "source_ticket_date": "2026-06-22", "source_item_sequence": 1, "product_code": "P002", "quantity": 5, "unit_price": 3.00, "line_amount": 15.00},
    ][:count]


def _stores(suffix: str, count: int = 2):
    return [
        {"source_ticket_code": f"E2E_IMP_{suffix}_T1", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0123"},
        {"source_ticket_code": f"E2E_IMP_{suffix}_T1", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0789"},
        {"source_ticket_code": f"E2E_IMP_{suffix}_T2", "source_business_code": "BUS001", "source_store_code": "0456", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0456"},
    ][:count + 1]


class TestE2eImporter:

    def test_process_batch_happy_path(self, db, tmp_path):
        uid = uuid4().hex[:6]
        svc = _make_service(db, tmp_path)
        _write_json(svc.inbound, f'control_{uid}.json', {"batchCode": uid})
        _write_json(svc.inbound, f'header_{uid}.json', _headers(uid))
        _write_json(svc.inbound, f'items_{uid}.json', _items(uid))
        _write_json(svc.inbound, f'stores_{uid}.json', _stores(uid, 3))

        result = svc.process_batch(uid)

        assert result['status'] == 'ARCHIVED'
        assert result['inserted'] == 2

        t1 = db.query(Ticket).filter(Ticket.source_ticket_key == f'E2E_IMP_{uid}_T1|BUS001|0123|20260622').first()
        assert t1 is not None
        assert t1.scan_status == 'NO_FILE'
        assert len(t1.items) == 1
        assert len(t1.stores) == 2

    def test_skips_duplicate_tickets(self, db, tmp_path):
        uid = uuid4().hex[:6]
        svc = _make_service(db, tmp_path)
        _write_json(svc.inbound, f'control_{uid}.json', {"batchCode": uid})
        _write_json(svc.inbound, f'header_{uid}.json', _headers(uid))
        _write_json(svc.inbound, f'items_{uid}.json', _items(uid))
        _write_json(svc.inbound, f'stores_{uid}.json', _stores(uid, 3))

        r1 = svc.process_batch(uid)
        assert r1['inserted'] == 2

        uid2 = uuid4().hex[:6]
        for f in list(svc.inbound.glob('*')):
            f.unlink()
        _write_json(svc.inbound, f'control_{uid2}.json', {"batchCode": uid2})
        _write_json(svc.inbound, f'header_{uid2}.json', _headers(uid))
        _write_json(svc.inbound, f'items_{uid2}.json', _items(uid))
        _write_json(svc.inbound, f'stores_{uid2}.json', _stores(uid, 3))

        r2 = svc.process_batch(uid2)
        assert r2['inserted'] == 0
        assert r2['skipped'] == 2

        assert db.query(Ticket).filter(
            Ticket.source_ticket_key.like(f'E2E_IMP_{uid}_T%')
        ).count() == 2

    def test_missing_files(self, db, tmp_path):
        uid = uuid4().hex[:6]
        svc = _make_service(db, tmp_path)
        _write_json(svc.inbound, f'control_{uid}.json', {"batchCode": uid})

        result = svc.process_batch(uid)
        assert result['status'] == 'FAILED'
        assert 'HEADER' in result['missing']

    def test_parse_error(self, db, tmp_path):
        uid = uuid4().hex[:6]
        svc = _make_service(db, tmp_path)
        _write_json(svc.inbound, f'control_{uid}.json', {"batchCode": uid})
        _write_json(svc.inbound, f'header_{uid}.json', _headers(uid))
        (svc.inbound / f'items_{uid}.json').write_text('not valid json', encoding='utf-8')
        _write_json(svc.inbound, f'stores_{uid}.json', _stores(uid, 3))

        result = svc.process_batch(uid)
        assert result['status'] == 'FAILED'
        assert 'parseErrors' in result

    def test_batch_fails_when_all_records_fail(self, db, tmp_path):
        uid = uuid4().hex[:6]
        svc = _make_service(db, tmp_path)
        _write_json(svc.inbound, f'control_{uid}.json', {"batchCode": uid})
        bad_headers = [
            {"source_ticket_code": f"E2E_IMP_{uid}_BAD", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "source_status_code": "9"},
        ]
        _write_json(svc.inbound, f'header_{uid}.json', bad_headers)
        _write_json(svc.inbound, f'items_{uid}.json', _items(uid))
        _write_json(svc.inbound, f'stores_{uid}.json', _stores(uid, 3))

        result = svc.process_batch(uid)
        assert result['status'] == 'FAILED'
        assert result['inserted'] == 0
        assert result['errors'] > 0

        batch = db.query(IntegrationBatch).filter_by(batch_code=uid).first()
        assert batch is not None
        assert batch.status == 'FAILED'
        assert len(list(svc.error_dir.glob('*'))) == 4

    def test_partial_success_with_errors(self, db, tmp_path):
        uid = uuid4().hex[:6]
        svc = _make_service(db, tmp_path)
        _write_json(svc.inbound, f'control_{uid}.json', {"batchCode": uid})

        mixed_headers = [
            {"source_ticket_code": f"E2E_IMP_{uid}_OK", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_status_code": "9"},
            {"source_ticket_code": f"E2E_IMP_{uid}_BAD", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "source_status_code": "9"},
        ]
        _write_json(svc.inbound, f'header_{uid}.json', mixed_headers)

        items_both = [
            {"source_ticket_code": f"E2E_IMP_{uid}_OK", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "source_item_sequence": 1, "product_code": "P001", "quantity": 1, "unit_price": 10, "line_amount": 10},
            {"source_ticket_code": f"E2E_IMP_{uid}_BAD", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "source_item_sequence": 1, "product_code": "P999", "quantity": 1, "unit_price": 10, "line_amount": 10},
        ]
        _write_json(svc.inbound, f'items_{uid}.json', items_both)

        stores_both = [
            {"source_ticket_code": f"E2E_IMP_{uid}_OK", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "2026-06-22", "applies_to_store_code": "0123"},
            {"source_ticket_code": f"E2E_IMP_{uid}_BAD", "source_business_code": "BUS001", "source_store_code": "0123", "source_ticket_date": "not-a-date", "applies_to_store_code": "0123"},
        ]
        _write_json(svc.inbound, f'stores_{uid}.json', stores_both)

        result = svc.process_batch(uid)
        assert result['status'] == 'ARCHIVED'
        assert result['inserted'] == 1
        assert result['errors'] > 0

        assert db.query(Ticket).filter(Ticket.source_ticket_code == f'E2E_IMP_{uid}_OK').first() is not None
        assert db.query(Ticket).filter(Ticket.source_ticket_code == f'E2E_IMP_{uid}_BAD').first() is None

    def test_run_pending_batches(self, db, tmp_path):
        uid = uuid4().hex[:6]
        svc = _make_service(db, tmp_path)
        _write_json(svc.inbound, f'control_{uid}.json', {"batchCode": uid})
        _write_json(svc.inbound, f'header_{uid}.json', _headers(uid))
        _write_json(svc.inbound, f'items_{uid}.json', _items(uid))
        _write_json(svc.inbound, f'stores_{uid}.json', _stores(uid, 3))

        uid2 = uuid4().hex[:6]
        h2 = [{"source_ticket_code": f"E2E_IMP_{uid2}_T1", "source_business_code": "BUS001", "source_store_code": "0999", "source_ticket_date": "2026-06-23", "source_status_code": "9"}]
        i2 = [{"source_ticket_code": f"E2E_IMP_{uid2}_T1", "source_business_code": "BUS001", "source_store_code": "0999", "source_ticket_date": "2026-06-23", "source_item_sequence": 1, "product_code": "P003", "quantity": 1, "unit_price": 100, "line_amount": 100}]
        s2 = [{"source_ticket_code": f"E2E_IMP_{uid2}_T1", "source_business_code": "BUS001", "source_store_code": "0999", "source_ticket_date": "2026-06-23", "applies_to_store_code": "0999"}]

        _write_json(svc.inbound, f'control_{uid2}.json', {"batchCode": uid2})
        _write_json(svc.inbound, f'header_{uid2}.json', h2)
        _write_json(svc.inbound, f'items_{uid2}.json', i2)
        _write_json(svc.inbound, f'stores_{uid2}.json', s2)

        results = svc.run_pending_batches()

        assert len(results) == 2
        by_code = {r['batchCode']: r for r in results}
        assert by_code[uid]['status'] == 'ARCHIVED'
        assert by_code[uid]['inserted'] == 2
        assert by_code[uid2]['status'] == 'ARCHIVED'
        assert by_code[uid2]['inserted'] == 1

        assert db.query(Ticket).filter(
            Ticket.source_ticket_key.like(f'E2E_IMP_{uid}_T%')
        ).count() == 2
        assert db.query(Ticket).filter(Ticket.source_ticket_code == f'E2E_IMP_{uid2}_T1').first() is not None
