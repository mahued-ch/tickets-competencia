"""
Migration v3: Deploy fn_replace_ticket_scan_file and fn_confirm_ticket_scan_file.

Run: python scripts/migrate_v3_scan_file_functions.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.session import engine

SQL_REPLACE = """
CREATE OR REPLACE FUNCTION competitor_ticket.fn_replace_ticket_scan_file(
    p_ticket_id           bigint,
    p_file_name           varchar,
    p_file_extension      varchar,
    p_mime_type           varchar,
    p_file_size_bytes     bigint,
    p_file_hash           varchar,
    p_storage_path        varchar,
    p_uploaded_by_user_id bigint,
    p_storage_provider    varchar DEFAULT 'IFS',
    p_notes               text DEFAULT NULL
)
RETURNS TABLE (
    new_ticket_scan_file_id       bigint,
    new_version_number            integer,
    previous_ticket_scan_file_id  bigint
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_ticket_id               bigint;
    v_source_status_code      varchar(10);
    v_source_ticket_key       varchar(120);
    v_previous_file_id        bigint;
    v_previous_is_confirmed   boolean;
    v_next_version            integer;
    v_new_file_id             bigint;
BEGIN
    IF p_ticket_id IS NULL THEN
        RAISE EXCEPTION 'p_ticket_id es obligatorio';
    END IF;
    IF p_file_name IS NULL OR BTRIM(p_file_name) = '' THEN
        RAISE EXCEPTION 'p_file_name es obligatorio';
    END IF;
    IF p_file_extension IS NULL OR BTRIM(p_file_extension) = '' THEN
        RAISE EXCEPTION 'p_file_extension es obligatorio';
    END IF;
    IF p_mime_type IS NULL OR BTRIM(p_mime_type) = '' THEN
        RAISE EXCEPTION 'p_mime_type es obligatorio';
    END IF;
    IF p_file_size_bytes IS NULL OR p_file_size_bytes <= 0 THEN
        RAISE EXCEPTION 'p_file_size_bytes debe ser mayor a 0';
    END IF;
    IF p_file_hash IS NULL OR BTRIM(p_file_hash) = '' THEN
        RAISE EXCEPTION 'p_file_hash es obligatorio';
    END IF;
    IF p_storage_path IS NULL OR BTRIM(p_storage_path) = '' THEN
        RAISE EXCEPTION 'p_storage_path es obligatorio';
    END IF;
    IF p_uploaded_by_user_id IS NULL THEN
        RAISE EXCEPTION 'p_uploaded_by_user_id es obligatorio';
    END IF;

    PERFORM 1 FROM competitor_ticket.app_user u WHERE u.user_id = p_uploaded_by_user_id AND u.is_active = true;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario % no existe o esta inactivo', p_uploaded_by_user_id;
    END IF;

    SELECT t.ticket_id, t.source_status_code, t.source_ticket_key
      INTO v_ticket_id, v_source_status_code, v_source_ticket_key
      FROM competitor_ticket.ticket t WHERE t.ticket_id = p_ticket_id
      FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el ticket_id %', p_ticket_id;
    END IF;
    IF v_source_status_code IS DISTINCT FROM '9' THEN
        RAISE EXCEPTION 'No se permite adjuntar/reemplazar archivo para ticket_id % porque source_status_code = % (se requiere 9)', p_ticket_id, v_source_status_code;
    END IF;

    SELECT tsf.ticket_scan_file_id, tsf.is_confirmed
      INTO v_previous_file_id, v_previous_is_confirmed
      FROM competitor_ticket.ticket_scan_file tsf
      WHERE tsf.ticket_id = p_ticket_id AND tsf.is_active = true
      ORDER BY tsf.version_number DESC, tsf.ticket_scan_file_id DESC
      LIMIT 1
      FOR UPDATE;
    IF v_previous_file_id IS NOT NULL AND v_previous_is_confirmed = true THEN
        RAISE EXCEPTION 'El ticket_id % ya tiene un archivo confirmado (ticket_scan_file_id = %). No se puede reemplazar.', p_ticket_id, v_previous_file_id;
    END IF;

    IF v_previous_file_id IS NOT NULL THEN
        UPDATE competitor_ticket.ticket_scan_file SET is_active = false WHERE ticket_scan_file_id = v_previous_file_id;
    END IF;

    SELECT COALESCE(MAX(tsf.version_number), 0) + 1
      INTO v_next_version
      FROM competitor_ticket.ticket_scan_file tsf WHERE tsf.ticket_id = p_ticket_id;

    INSERT INTO competitor_ticket.ticket_scan_file (ticket_id, file_name, file_extension, mime_type, file_size_bytes, file_hash, storage_path, storage_provider, version_number, is_active, is_confirmed, uploaded_by_user_id, uploaded_at, confirmed_by_user_id, confirmed_at, replaced_by_file_id, notes)
    VALUES (p_ticket_id, p_file_name, p_file_extension, p_mime_type, p_file_size_bytes, p_file_hash, p_storage_path, COALESCE(p_storage_provider, 'IFS'), v_next_version, true, false, p_uploaded_by_user_id, NOW(), NULL, NULL, NULL, p_notes)
    RETURNING ticket_scan_file_id INTO v_new_file_id;

    IF v_previous_file_id IS NOT NULL THEN
        UPDATE competitor_ticket.ticket_scan_file SET replaced_by_file_id = v_new_file_id WHERE ticket_scan_file_id = v_previous_file_id;
    END IF;

    INSERT INTO competitor_ticket.audit_event (event_type, entity_name, entity_id, source_ticket_key, user_id, event_timestamp, old_values_json, new_values_json, event_details_json)
    VALUES (
        CASE WHEN v_previous_file_id IS NULL THEN 'SCAN_FILE_UPLOADED' ELSE 'SCAN_FILE_REPLACED' END,
        'ticket_scan_file', v_new_file_id, v_source_ticket_key, p_uploaded_by_user_id, NOW(),
        CASE WHEN v_previous_file_id IS NULL THEN NULL ELSE jsonb_build_object('previous_ticket_scan_file_id', v_previous_file_id) END,
        jsonb_build_object('new_ticket_scan_file_id', v_new_file_id, 'new_version_number', v_next_version, 'file_name', p_file_name, 'file_extension', p_file_extension, 'mime_type', p_mime_type, 'file_size_bytes', p_file_size_bytes, 'file_hash', p_file_hash, 'storage_path', p_storage_path, 'storage_provider', COALESCE(p_storage_provider, 'IFS')),
        jsonb_build_object('ticket_id', p_ticket_id, 'previous_ticket_scan_file_id', v_previous_file_id, 'replacement_allowed', true)
    );

    new_ticket_scan_file_id := v_new_file_id;
    new_version_number := v_next_version;
    previous_ticket_scan_file_id := v_previous_file_id;
    RETURN NEXT;
    RETURN;
END;
$$;
"""

SQL_CONFIRM = """
CREATE OR REPLACE FUNCTION competitor_ticket.fn_confirm_ticket_scan_file(
    p_ticket_id             bigint,
    p_confirmed_by_user_id  bigint,
    p_notes                 text DEFAULT NULL
)
RETURNS TABLE (
    ticket_scan_file_id     bigint,
    ticket_id               bigint,
    version_number          integer,
    confirmed_at            timestamptz
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_ticket_key     varchar(120);
    v_file_id               bigint;
    v_version_number        integer;
    v_is_confirmed          boolean;
    v_confirmed_at          timestamptz;
BEGIN
    IF p_ticket_id IS NULL THEN
        RAISE EXCEPTION 'p_ticket_id es obligatorio';
    END IF;
    IF p_confirmed_by_user_id IS NULL THEN
        RAISE EXCEPTION 'p_confirmed_by_user_id es obligatorio';
    END IF;

    PERFORM 1 FROM competitor_ticket.app_user u WHERE u.user_id = p_confirmed_by_user_id AND u.is_active = true;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario % no existe o esta inactivo', p_confirmed_by_user_id;
    END IF;

    SELECT t.source_ticket_key INTO v_source_ticket_key
      FROM competitor_ticket.ticket t WHERE t.ticket_id = p_ticket_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el ticket_id %', p_ticket_id;
    END IF;

    SELECT tsf.ticket_scan_file_id, tsf.version_number, tsf.is_confirmed
      INTO v_file_id, v_version_number, v_is_confirmed
      FROM competitor_ticket.ticket_scan_file tsf
      WHERE tsf.ticket_id = p_ticket_id AND tsf.is_active = true
      ORDER BY tsf.version_number DESC, tsf.ticket_scan_file_id DESC
      LIMIT 1
      FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El ticket_id % no tiene archivo activo para confirmar', p_ticket_id;
    END IF;
    IF v_is_confirmed = true THEN
        RAISE EXCEPTION 'El archivo activo del ticket_id % ya esta confirmado (ticket_scan_file_id = %)', p_ticket_id, v_file_id;
    END IF;

    UPDATE competitor_ticket.ticket_scan_file
       SET is_confirmed = true, confirmed_at = NOW(), confirmed_by_user_id = p_confirmed_by_user_id,
           notes = CASE WHEN p_notes IS NULL OR BTRIM(p_notes) = '' THEN notes WHEN notes IS NULL OR BTRIM(notes) = '' THEN p_notes ELSE notes || E'\\n' || p_notes END
     WHERE ticket_scan_file_id = v_file_id
     RETURNING confirmed_at INTO v_confirmed_at;

    INSERT INTO competitor_ticket.audit_event (event_type, entity_name, entity_id, source_ticket_key, user_id, event_timestamp, old_values_json, new_values_json, event_details_json)
    VALUES ('SCAN_FILE_CONFIRMED', 'ticket_scan_file', v_file_id, v_source_ticket_key, p_confirmed_by_user_id, NOW(),
        jsonb_build_object('ticket_scan_file_id', v_file_id, 'ticket_id', p_ticket_id, 'version_number', v_version_number, 'was_confirmed', false),
        jsonb_build_object('ticket_scan_file_id', v_file_id, 'ticket_id', p_ticket_id, 'version_number', v_version_number, 'is_confirmed', true, 'confirmed_by_user_id', p_confirmed_by_user_id, 'confirmed_at', v_confirmed_at),
        jsonb_build_object('notes', p_notes)
    );

    ticket_scan_file_id := v_file_id;
    ticket_id := p_ticket_id;
    version_number := v_version_number;
    confirmed_at := v_confirmed_at;
    RETURN NEXT;
    RETURN;
END;
$$;
"""


def main():
    print("Running migration v3 (scan file PostgreSQL functions)...")
    with engine.begin() as conn:
        conn.exec_driver_sql(SQL_REPLACE)
        conn.exec_driver_sql(SQL_CONFIRM)
    print("Migration v3 completed. Functions deployed:")
    print("  - competitor_ticket.fn_replace_ticket_scan_file")
    print("  - competitor_ticket.fn_confirm_ticket_scan_file")


if __name__ == '__main__':
    main()
