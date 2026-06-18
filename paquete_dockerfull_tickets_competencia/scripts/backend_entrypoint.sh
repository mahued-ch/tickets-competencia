#!/usr/bin/env bash
set -euo pipefail

python scripts/wait_for_db.py
python scripts/bootstrap_demo.py
python scripts/run_importer_demo.py || true

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
