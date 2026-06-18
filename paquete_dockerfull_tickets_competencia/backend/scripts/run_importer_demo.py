from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.session import SessionLocal
from app.services.importer_service import ImporterService


def main():
    db = SessionLocal()
    try:
        svc = ImporterService(db)
        results = svc.run_pending_batches()
        for r in results:
            print(r)
    finally:
        db.close()


if __name__ == '__main__':
    main()
