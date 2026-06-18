from __future__ import annotations
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime
import json
import shutil
from app.core.config import get_settings
from app.models.integration import IntegrationBatch, IntegrationFile, IntegrationError
from app.models.ticket import Ticket, TicketItem, TicketStore

settings = get_settings()


class ImporterService:
    def __init__(self, db: Session):
        self.db = db
        self.inbound = Path(settings.inbound_path)
        self.archive = Path(settings.archive_path)
        self.error = Path(settings.error_path)
        self.archive.mkdir(parents=True, exist_ok=True)
        self.error.mkdir(parents=True, exist_ok=True)

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

        batch = IntegrationBatch(
            batch_code=batch_code,
            source_system='AS400',
            source_directory=str(self.inbound),
            archive_directory=str(self.archive),
            error_directory=str(self.error),
            status='PROCESSING',
        )
        self.db.add(batch)
        self.db.flush()

        files_data = {}
        for kind, fpath in expected.items():
            raw = json.loads(fpath.read_text(encoding='utf-8'))
            files_data[kind] = raw
            count = len(raw) if isinstance(raw, list) else 1
            frow = IntegrationFile(
                batch_id=batch.batch_id,
                file_type=kind,
                file_name=fpath.name,
                original_path=str(fpath),
                file_size_bytes=fpath.stat().st_size,
                record_count=count,
                status='PROCESSED',
            )
            self.db.add(frow)

        headers = files_data['HEADER']
        items = files_data['ITEM']
        stores = files_data['STORE']
        batch.header_record_count = len(headers)
        batch.item_record_count = len(items)
        batch.store_record_count = len(stores)

        inserted = 0
        skipped = 0
        for h in headers:
            skey = self._build_key(h)
            exists = self.db.query(Ticket).filter(Ticket.source_ticket_key == skey).first()
            if exists:
                skipped += 1
                continue
            ticket = Ticket(
                source_ticket_code=h['source_ticket_code'],
                source_business_code=h['source_business_code'],
                source_store_code=h['source_store_code'],
                source_ticket_date=datetime.fromisoformat(h['source_ticket_date']).date(),
                source_ticket_key=skey,
                source_status_code=h.get('source_status_code'),
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
                ))
            for s in [x for x in stores if self._build_key(x) == skey]:
                self.db.add(TicketStore(ticket_id=ticket.ticket_id, store_code=s['applies_to_store_code']))
            inserted += 1

        batch.inserted_ticket_count = inserted
        batch.skipped_ticket_count = skipped
        batch.status = 'PROCESSED'
        batch.finished_at = datetime.utcnow()
        self.db.commit()

        # move files to archive
        for fpath in expected.values():
            target = self.archive / fpath.name
            if target.exists():
                target.unlink()
            shutil.move(str(fpath), str(target))
        batch.status = 'ARCHIVED'
        self.db.commit()
        return {'batchCode': batch_code, 'status': 'ARCHIVED', 'inserted': inserted, 'skipped': skipped}

    @staticmethod
    def _build_key(obj: dict) -> str:
        d = obj['source_ticket_date'].replace('-', '')
        return f"{obj['source_ticket_code']}|{obj['source_business_code']}|{obj['source_store_code']}|{d}"
