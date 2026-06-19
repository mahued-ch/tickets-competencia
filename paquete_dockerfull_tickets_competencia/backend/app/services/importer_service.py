from __future__ import annotations
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime
import json
import hashlib
import shutil
from app.core.config import get_settings
from app.models.integration import IntegrationBatch, IntegrationFile, IntegrationError
from app.models.ticket import Ticket, TicketItem, TicketStore
from app.models.inbound import InboundTicketHeader, InboundTicketItem, InboundTicketStore

settings = get_settings()


class ImporterService:
    def __init__(self, db: Session):
        self.db = db
        self.inbound = Path(settings.inbound_path)
        self.archive = Path(settings.archive_path)
        self.error_dir = Path(settings.error_path)
        self.inbound.mkdir(parents=True, exist_ok=True)
        self.archive.mkdir(parents=True, exist_ok=True)
        self.error_dir.mkdir(parents=True, exist_ok=True)

    # ── public ──────────────────────────────────────────────

    def run_pending_batches(self) -> list[dict]:
        results = []
        for control_file in sorted(self.inbound.glob('control_*.json')):
            batch_code = control_file.stem.split('_', 1)[1]
            results.append(self.process_batch(batch_code))
        return results

    def process_batch(self, batch_code: str) -> dict:
        expected = {
            'HEADER': self.inbound / f'header_{batch_code}.json',
            'ITEM': self.inbound / f'items_{batch_code}.json',
            'STORE': self.inbound / f'stores_{batch_code}.json',
            'CONTROL': self.inbound / f'control_{batch_code}.json',
        }

        missing = [k for k, p in expected.items() if not p.exists()]
        if missing:
            return {'batchCode': batch_code, 'status': 'FAILED', 'missing': missing}

        # ── parse files ─────────────────────────────────────
        files_data = {}
        file_hashes = {}
        parse_errors = []
        for kind, fpath in expected.items():
            try:
                raw = fpath.read_bytes()
                file_hashes[kind] = hashlib.sha256(raw).hexdigest()
                parsed = json.loads(raw.decode('utf-8'))
                files_data[kind] = parsed
            except Exception as e:
                parse_errors.append({'file': fpath.name, 'error': str(e)})

        if parse_errors:
            return {'batchCode': batch_code, 'status': 'FAILED', 'parseErrors': parse_errors}

        # ── create batch ────────────────────────────────────
        batch = IntegrationBatch(
            batch_code=batch_code,
            source_system='AS400',
            source_directory=str(self.inbound),
            archive_directory=str(self.archive),
            error_directory=str(self.error_dir),
            status='PROCESSING',
        )
        self.db.add(batch)
        self.db.flush()

        # ── register files ──────────────────────────────────
        for kind, fpath in expected.items():
            raw_data = files_data[kind]
            count = len(raw_data) if isinstance(raw_data, list) else 1
            frow = IntegrationFile(
                batch_id=batch.batch_id,
                file_type=kind,
                file_name=fpath.name,
                original_path=str(fpath),
                file_size_bytes=fpath.stat().st_size,
                file_hash=file_hashes[kind],
                record_count=count,
                status='PROCESSING',
            )
            self.db.add(frow)
        self.db.flush()

        headers = files_data['HEADER']
        items = files_data['ITEM']
        stores = files_data['STORE']

        batch.header_record_count = len(headers)
        batch.item_record_count = len(items)
        batch.store_record_count = len(stores)

        # ── staging: insert into inbound tables ─────────────
        error_count = 0
        for h in headers:
            skey = self._build_key(h)
            try:
                self.db.add(InboundTicketHeader(
                    batch_id=batch.batch_id,
                    source_ticket_code=h['source_ticket_code'],
                    source_business_code=h['source_business_code'],
                    source_store_code=h['source_store_code'],
                    source_ticket_date=datetime.fromisoformat(h['source_ticket_date']).date(),
                    source_ticket_key=skey,
                    source_status_code=h.get('source_status_code'),
                    payload_json=json.dumps(h, ensure_ascii=False),
                ))
            except Exception as e:
                self._add_error(batch, 'HEADER', skey, 'STAGING_INSERT_ERROR', str(e))
                error_count += 1

        for i in items:
            skey = self._build_key(i)
            try:
                self.db.add(InboundTicketItem(
                    batch_id=batch.batch_id,
                    source_ticket_code=i['source_ticket_code'],
                    source_business_code=i['source_business_code'],
                    source_store_code=i['source_store_code'],
                    source_ticket_date=datetime.fromisoformat(i['source_ticket_date']).date(),
                    source_ticket_key=skey,
                    source_item_sequence=i['source_item_sequence'],
                    product_code=i.get('product_code'),
                    product_description=i.get('product_description'),
                    quantity=i.get('quantity'),
                    unit_price=i.get('unit_price'),
                    line_amount=i.get('line_amount'),
                    payload_json=json.dumps(i, ensure_ascii=False),
                ))
            except Exception as e:
                self._add_error(batch, 'ITEM', skey, 'STAGING_INSERT_ERROR', str(e))
                error_count += 1

        for s in stores:
            skey = self._build_key(s)
            try:
                self.db.add(InboundTicketStore(
                    batch_id=batch.batch_id,
                    source_ticket_code=s['source_ticket_code'],
                    source_business_code=s['source_business_code'],
                    source_store_code=s['source_store_code'],
                    source_ticket_date=datetime.fromisoformat(s['source_ticket_date']).date(),
                    source_ticket_key=skey,
                    applies_to_store_code=s['applies_to_store_code'],
                    payload_json=json.dumps(s, ensure_ascii=False),
                ))
            except Exception as e:
                self._add_error(batch, 'STORE', skey, 'STAGING_INSERT_ERROR', str(e))
                error_count += 1

        self.db.flush()

        # ── consolidate: staging → operational ─────────────
        inserted = 0
        skipped = 0
        for h in headers:
            skey = self._build_key(h)
            exists = self.db.query(Ticket).filter(Ticket.source_ticket_key == skey).first()
            if exists:
                skipped += 1
                continue
            try:
                ticket = Ticket(
                    source_ticket_code=h['source_ticket_code'],
                    source_business_code=h['source_business_code'],
                    source_store_code=h['source_store_code'],
                    source_ticket_date=datetime.fromisoformat(h['source_ticket_date']).date(),
                    source_ticket_key=skey,
                    source_status_code=h.get('source_status_code'),
                    source_header_payload=json.dumps(h, ensure_ascii=False),
                    batch_id=batch.batch_id,
                    scan_status='NO_FILE',
                    has_scan_file=False,
                )
                self.db.add(ticket)
                self.db.flush()

                for i in [x for x in items if self._build_key(x) == skey]:
                    self.db.add(TicketItem(
                        ticket_id=ticket.ticket_id,
                        item_sequence=i['source_item_sequence'],
                        product_code=i.get('product_code'),
                        product_description=i.get('product_description'),
                        quantity=i.get('quantity'),
                        unit_price=i.get('unit_price'),
                        line_amount=i.get('line_amount'),
                        source_item_payload=json.dumps(i, ensure_ascii=False),
                    ))
                for s in [x for x in stores if self._build_key(x) == skey]:
                    self.db.add(TicketStore(
                        ticket_id=ticket.ticket_id,
                        store_code=s['applies_to_store_code'],
                    ))

                # mark staging rows as processed
                self.db.query(InboundTicketHeader).filter(
                    InboundTicketHeader.batch_id == batch.batch_id,
                    InboundTicketHeader.source_ticket_key == skey,
                ).update({'is_processed': True, 'processed_at': datetime.utcnow()})
                self.db.query(InboundTicketItem).filter(
                    InboundTicketItem.batch_id == batch.batch_id,
                    InboundTicketItem.source_ticket_key == skey,
                ).update({'is_processed': True, 'processed_at': datetime.utcnow()})
                self.db.query(InboundTicketStore).filter(
                    InboundTicketStore.batch_id == batch.batch_id,
                    InboundTicketStore.source_ticket_key == skey,
                ).update({'is_processed': True, 'processed_at': datetime.utcnow()})

                inserted += 1
                self.db.flush()
            except Exception as e:
                self._add_error(batch, 'HEADER', skey, 'CONSOLIDATE_ERROR', str(e))
                error_count += 1

        # ── finalize batch ──────────────────────────────────
        batch.inserted_ticket_count = inserted
        batch.skipped_ticket_count = skipped
        batch.error_count = error_count
        batch.finished_at = datetime.utcnow()

        if error_count > 0 and inserted == 0:
            batch.status = 'FAILED'
            self.db.commit()
            self._move_files(expected, self.error_dir)
            return {'batchCode': batch_code, 'status': 'FAILED', 'inserted': inserted, 'skipped': skipped, 'errors': error_count}

        batch.status = 'PROCESSED'
        self.db.commit()

        # move files to archive
        self._move_files(expected, self.archive)
        batch.status = 'ARCHIVED'
        self.db.commit()

        return {'batchCode': batch_code, 'status': 'ARCHIVED', 'inserted': inserted, 'skipped': skipped, 'errors': error_count}

    # ── helpers ─────────────────────────────────────────────

    @staticmethod
    def _build_key(obj: dict) -> str:
        d = obj['source_ticket_date'].replace('-', '')
        return f"{obj['source_ticket_code']}|{obj['source_business_code']}|{obj['source_store_code']}|{d}"

    def _add_error(self, batch, entity_type, source_ticket_key, error_code, error_message):
        self.db.add(IntegrationError(
            batch_id=batch.batch_id,
            entity_type=entity_type,
            source_ticket_key=source_ticket_key,
            error_code=error_code,
            error_message=error_message,
        ))

    def _move_files(self, expected: dict, target_dir: Path):
        target_dir.mkdir(parents=True, exist_ok=True)
        for fpath in expected.values():
            target = target_dir / fpath.name
            if target.exists():
                target.unlink()
            shutil.move(str(fpath), str(target))
