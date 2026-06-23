"""
Migration v13: Deploy trigger to sync ticket.scan_status from ticket_scan_file.

Deploys:
  - fn_sync_ticket_scan_status     — updates ticket.scan_status based on active scan file
  - fn_after_ticket_scan_file_change — AFTER INSERT/UPDATE/DELETE trigger function
  - trg_ticket_scan_file_sync_ticket — the trigger on ticket_scan_file

Run: python scripts/migrate_v13_scan_status_trigger.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy import text
from app.db.session import engine

SQL_SYNC_FN = """
CREATE OR REPLACE FUNCTION competitor_ticket.fn_sync_ticket_scan_status(p_ticket_id bigint)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_file_id               bigint;
    v_is_confirmed          boolean;
    v_confirmed_at          timestamptz;
    v_confirmed_by_user_id  bigint;
BEGIN
    SELECT tsf.ticket_scan_file_id,
           tsf.is_confirmed,
           tsf.confirmed_at,
           tsf.confirmed_by_user_id
      INTO v_file_id, v_is_confirmed, v_confirmed_at, v_confirmed_by_user_id
      FROM competitor_ticket.ticket_scan_file tsf
     WHERE tsf.ticket_id = p_ticket_id
       AND tsf.is_active = true
     ORDER BY tsf.version_number DESC, tsf.ticket_scan_file_id DESC
     LIMIT 1;

    IF v_file_id IS NULL THEN
        UPDATE competitor_ticket.ticket
           SET has_scan_file = false,
               scan_status = 'NO_FILE',
               scan_confirmed_at = NULL,
               scan_confirmed_by_user_id = NULL
         WHERE ticket_id = p_ticket_id;
    ELSE
        IF v_is_confirmed THEN
            UPDATE competitor_ticket.ticket
               SET has_scan_file = true,
                   scan_status = 'FILE_CONFIRMED',
                   scan_confirmed_at = v_confirmed_at,
                   scan_confirmed_by_user_id = v_confirmed_by_user_id
             WHERE ticket_id = p_ticket_id;
        ELSE
            UPDATE competitor_ticket.ticket
               SET has_scan_file = true,
                   scan_status = 'FILE_UPLOADED',
                   scan_confirmed_at = NULL,
                   scan_confirmed_by_user_id = NULL
             WHERE ticket_id = p_ticket_id;
        END IF;
    END IF;
END;
$$;
"""

SQL_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION competitor_ticket.fn_after_ticket_scan_file_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM competitor_ticket.fn_sync_ticket_scan_status(OLD.ticket_id);
        RETURN OLD;
    ELSE
        PERFORM competitor_ticket.fn_sync_ticket_scan_status(NEW.ticket_id);
        RETURN NEW;
    END IF;
END;
$$;
"""

SQL_TRIGGER = """
DROP TRIGGER IF EXISTS trg_ticket_scan_file_sync_ticket ON competitor_ticket.ticket_scan_file;
CREATE TRIGGER trg_ticket_scan_file_sync_ticket
AFTER INSERT OR UPDATE OR DELETE ON competitor_ticket.ticket_scan_file
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_after_ticket_scan_file_change();
"""


def main():
    print("Running migration v13 (scan status sync trigger)...")
    with engine.begin() as conn:
        conn.execute(text(SQL_SYNC_FN))
        print("  - competitor_ticket.fn_sync_ticket_scan_status")
        conn.execute(text(SQL_TRIGGER_FN))
        print("  - competitor_ticket.fn_after_ticket_scan_file_change")
        conn.execute(text(SQL_TRIGGER))
        print("  - trg_ticket_scan_file_sync_ticket")
    print("Migration v13 completed.")


if __name__ == '__main__':
    main()
