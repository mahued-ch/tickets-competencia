
# DDL PostgreSQL Completo

> **Nota**: este script es la base fisica del sistema en PostgreSQL.
> Incluye:
> - esquema,
> - funciones utilitarias,
> - tablas,
> - constraints,
> - indices,
> - triggers,
> - datos semilla,
> - vistas utiles.

```sql
-- =========================================================
-- SISTEMA WEB DE GESTION DE TICKETS DE COMPETENCIA
-- DDL PostgreSQL v1
-- =========================================================
-- Autor: M365 Copilot
-- Fecha: 2026-06-18
-- Motor objetivo: PostgreSQL
-- =========================================================

CREATE SCHEMA IF NOT EXISTS competitor_ticket;

SET search_path TO competitor_ticket, public;

CREATE OR REPLACE FUNCTION competitor_ticket.fn_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION competitor_ticket.fn_build_source_ticket_key(
    p_source_ticket_code   varchar,
    p_source_business_code varchar,
    p_source_store_code    varchar,
    p_source_ticket_date   date
)
RETURNS varchar
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN COALESCE(p_source_ticket_code, '') || '|' ||
           COALESCE(p_source_business_code, '') || '|' ||
           COALESCE(p_source_store_code, '') || '|' ||
           TO_CHAR(p_source_ticket_date, 'YYYYMMDD');
END;
$$;

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

CREATE OR REPLACE FUNCTION competitor_ticket.fn_validate_ticket_scan_file()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_status_code varchar(10);
BEGIN
    SELECT t.source_status_code
      INTO v_source_status_code
      FROM competitor_ticket.ticket t
     WHERE t.ticket_id = NEW.ticket_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe ticket_id = %', NEW.ticket_id;
    END IF;

    IF v_source_status_code IS DISTINCT FROM '9' THEN
        RAISE EXCEPTION 'No se permite adjuntar archivo a ticket_id = % porque source_status_code = % (se requiere 9)',
            NEW.ticket_id, v_source_status_code;
    END IF;

    IF NEW.is_confirmed = true AND (NEW.confirmed_at IS NULL OR NEW.confirmed_by_user_id IS NULL) THEN
        RAISE EXCEPTION 'Un archivo confirmado debe tener confirmed_at y confirmed_by_user_id';
    END IF;

    IF NEW.is_confirmed = true AND NEW.is_active = false THEN
        RAISE EXCEPTION 'Un archivo confirmado no puede estar inactivo';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION competitor_ticket.fn_prevent_confirmed_scan_file_changes()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.is_confirmed = true THEN
            RAISE EXCEPTION 'No se puede modificar un archivo escaneado confirmado. ticket_scan_file_id=%', OLD.ticket_scan_file_id;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.is_confirmed = true THEN
            RAISE EXCEPTION 'No se puede eliminar un archivo escaneado confirmado. ticket_scan_file_id=%', OLD.ticket_scan_file_id;
        END IF;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION competitor_ticket.fn_assign_ticket_scan_file_version()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_next_version integer;
BEGIN
    IF NEW.version_number IS NULL OR NEW.version_number <= 0 THEN
        SELECT COALESCE(MAX(version_number), 0) + 1
          INTO v_next_version
          FROM competitor_ticket.ticket_scan_file
         WHERE ticket_id = NEW.ticket_id;

        NEW.version_number := v_next_version;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION competitor_ticket.fn_fill_source_ticket_key()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.source_ticket_key := competitor_ticket.fn_build_source_ticket_key(
        NEW.source_ticket_code,
        NEW.source_business_code,
        NEW.source_store_code,
        NEW.source_ticket_date
    );
    RETURN NEW;
END;
$$;

CREATE TABLE competitor_ticket.app_role (
    role_id          bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    role_code        varchar(30) NOT NULL,
    role_name        varchar(100) NOT NULL,
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_app_role_role_code UNIQUE (role_code)
);

CREATE TABLE competitor_ticket.app_user (
    user_id          bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    login_name       varchar(100) NOT NULL,
    display_name     varchar(150) NOT NULL,
    email            varchar(200),
    role_id          bigint NOT NULL,
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT NOW(),
    updated_at       timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_app_user_login_name UNIQUE (login_name),
    CONSTRAINT fk_app_user_role
        FOREIGN KEY (role_id)
        REFERENCES competitor_ticket.app_role(role_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

CREATE TABLE competitor_ticket.app_user_store (
    app_user_store_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id           bigint NOT NULL,
    store_code        varchar(30) NOT NULL,
    is_active         boolean NOT NULL DEFAULT true,
    created_at        timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_app_user_store UNIQUE (user_id, store_code),
    CONSTRAINT fk_app_user_store_user
        FOREIGN KEY (user_id)
        REFERENCES competitor_ticket.app_user(user_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE TRIGGER trg_app_user_set_updated_at
BEFORE UPDATE ON competitor_ticket.app_user
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_set_updated_at();

CREATE TABLE competitor_ticket.integration_batch (
    batch_id                 bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    batch_code               varchar(15) NOT NULL,
    source_system            varchar(30) NOT NULL DEFAULT 'AS400',
    source_directory         varchar(500) NOT NULL,
    archive_directory        varchar(500),
    error_directory          varchar(500),
    started_at               timestamptz NOT NULL DEFAULT NOW(),
    finished_at              timestamptz,
    status                   varchar(30) NOT NULL,
    header_record_count      integer NOT NULL DEFAULT 0,
    item_record_count        integer NOT NULL DEFAULT 0,
    store_record_count       integer NOT NULL DEFAULT 0,
    inserted_ticket_count    integer NOT NULL DEFAULT 0,
    skipped_ticket_count     integer NOT NULL DEFAULT 0,
    error_count              integer NOT NULL DEFAULT 0,
    notes                    text,
    created_at               timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_integration_batch_batch_code UNIQUE (batch_code),
    CONSTRAINT ck_integration_batch_status
        CHECK (status IN (
            'RECEIVED',
            'PROCESSING',
            'PROCESSED',
            'PROCESSED_WITH_ERRORS',
            'FAILED',
            'ARCHIVED'
        ))
);

CREATE TABLE competitor_ticket.integration_file (
    integration_file_id      bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    batch_id                 bigint NOT NULL,
    file_type                varchar(20) NOT NULL,
    file_name                varchar(255) NOT NULL,
    original_path            varchar(500) NOT NULL,
    archived_path            varchar(500),
    file_size_bytes          bigint NOT NULL,
    file_hash                varchar(128),
    record_count             integer NOT NULL DEFAULT 0,
    processed_at             timestamptz,
    archived_at              timestamptz,
    status                   varchar(20) NOT NULL,
    raw_metadata             jsonb,
    created_at               timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_integration_file_name UNIQUE (file_name),
    CONSTRAINT fk_integration_file_batch
        FOREIGN KEY (batch_id)
        REFERENCES competitor_ticket.integration_batch(batch_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT ck_integration_file_type
        CHECK (file_type IN ('HEADER', 'ITEM', 'STORE', 'CONTROL')),
    CONSTRAINT ck_integration_file_status
        CHECK (status IN ('RECEIVED', 'PROCESSING', 'PROCESSED', 'ARCHIVED', 'ERROR', 'SKIPPED')),
    CONSTRAINT ck_integration_file_size
        CHECK (file_size_bytes >= 0)
);

CREATE TABLE competitor_ticket.integration_error (
    integration_error_id     bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    batch_id                 bigint NOT NULL,
    integration_file_id      bigint,
    entity_type              varchar(20) NOT NULL,
    source_ticket_key        varchar(120),
    error_code               varchar(50) NOT NULL,
    error_message            text NOT NULL,
    payload_fragment         jsonb,
    line_number              integer,
    created_at               timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_integration_error_batch
        FOREIGN KEY (batch_id)
        REFERENCES competitor_ticket.integration_batch(batch_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT fk_integration_error_file
        FOREIGN KEY (integration_file_id)
        REFERENCES competitor_ticket.integration_file(integration_file_id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,
    CONSTRAINT ck_integration_error_entity_type
        CHECK (entity_type IN ('BATCH', 'CONTROL', 'HEADER', 'ITEM', 'STORE', 'SCAN_FILE', 'SYSTEM'))
);

CREATE TABLE competitor_ticket.inbound_ticket_header (
    inbound_header_id         bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    batch_id                  bigint NOT NULL,
    source_ticket_code        varchar(30) NOT NULL,
    source_business_code      varchar(30) NOT NULL,
    source_store_code         varchar(30) NOT NULL,
    source_ticket_date        date NOT NULL,
    source_ticket_key         varchar(120) NOT NULL,
    source_status_code        varchar(10),
    source_created_at         timestamptz,
    payload_json              jsonb NOT NULL,
    is_processed              boolean NOT NULL DEFAULT false,
    processed_at              timestamptz,
    created_at                timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_inbound_ticket_header_batch
        FOREIGN KEY (batch_id)
        REFERENCES competitor_ticket.integration_batch(batch_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT uq_inbound_ticket_header_batch_key
        UNIQUE (batch_id, source_ticket_key)
);

CREATE TABLE competitor_ticket.inbound_ticket_item (
    inbound_item_id           bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    batch_id                  bigint NOT NULL,
    source_ticket_code        varchar(30) NOT NULL,
    source_business_code      varchar(30) NOT NULL,
    source_store_code         varchar(30) NOT NULL,
    source_ticket_date        date NOT NULL,
    source_ticket_key         varchar(120) NOT NULL,
    source_item_sequence      integer NOT NULL,
    product_code              varchar(50),
    product_description       varchar(255),
    quantity                  numeric(18,4),
    unit_price                numeric(18,4),
    line_amount               numeric(18,4),
    payload_json              jsonb NOT NULL,
    is_processed              boolean NOT NULL DEFAULT false,
    processed_at              timestamptz,
    created_at                timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_inbound_ticket_item_batch
        FOREIGN KEY (batch_id)
        REFERENCES competitor_ticket.integration_batch(batch_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT uq_inbound_ticket_item_batch_key_seq
        UNIQUE (batch_id, source_ticket_key, source_item_sequence),
    CONSTRAINT ck_inbound_ticket_item_quantity
        CHECK (quantity IS NULL OR quantity >= 0),
    CONSTRAINT ck_inbound_ticket_item_unit_price
        CHECK (unit_price IS NULL OR unit_price >= 0),
    CONSTRAINT ck_inbound_ticket_item_line_amount
        CHECK (line_amount IS NULL OR line_amount >= 0)
);

CREATE TABLE competitor_ticket.inbound_ticket_store (
    inbound_store_id          bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    batch_id                  bigint NOT NULL,
    source_ticket_code        varchar(30) NOT NULL,
    source_business_code      varchar(30) NOT NULL,
    source_store_code         varchar(30) NOT NULL,
    source_ticket_date        date NOT NULL,
    source_ticket_key         varchar(120) NOT NULL,
    applies_to_store_code     varchar(30) NOT NULL,
    payload_json              jsonb NOT NULL,
    is_processed              boolean NOT NULL DEFAULT false,
    processed_at              timestamptz,
    created_at                timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_inbound_ticket_store_batch
        FOREIGN KEY (batch_id)
        REFERENCES competitor_ticket.integration_batch(batch_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT uq_inbound_ticket_store_batch_key_store
        UNIQUE (batch_id, source_ticket_key, applies_to_store_code)
);

CREATE TRIGGER trg_inbound_ticket_header_fill_source_ticket_key
BEFORE INSERT OR UPDATE OF source_ticket_code, source_business_code, source_store_code, source_ticket_date
ON competitor_ticket.inbound_ticket_header
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_fill_source_ticket_key();

CREATE TRIGGER trg_inbound_ticket_item_fill_source_ticket_key
BEFORE INSERT OR UPDATE OF source_ticket_code, source_business_code, source_store_code, source_ticket_date
ON competitor_ticket.inbound_ticket_item
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_fill_source_ticket_key();

CREATE TRIGGER trg_inbound_ticket_store_fill_source_ticket_key
BEFORE INSERT OR UPDATE OF source_ticket_code, source_business_code, source_store_code, source_ticket_date
ON competitor_ticket.inbound_ticket_store
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_fill_source_ticket_key();

CREATE TABLE competitor_ticket.ticket (
    ticket_id                     bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    source_ticket_code            varchar(30) NOT NULL,
    source_business_code          varchar(30) NOT NULL,
    source_store_code             varchar(30) NOT NULL,
    source_ticket_date            date NOT NULL,
    source_ticket_key             varchar(120) NOT NULL,
    source_status_code            varchar(10),
    source_header_payload         jsonb NOT NULL,
    batch_id                      bigint NOT NULL,
    scan_status                   varchar(25) NOT NULL DEFAULT 'NO_FILE',
    has_scan_file                 boolean NOT NULL DEFAULT false,
    scan_confirmed_at             timestamptz,
    scan_confirmed_by_user_id     bigint,
    created_at                    timestamptz NOT NULL DEFAULT NOW(),
    updated_at                    timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ticket_source_key UNIQUE (source_ticket_key),
    CONSTRAINT uq_ticket_source_tuple UNIQUE (
        source_ticket_code,
        source_business_code,
        source_store_code,
        source_ticket_date
    ),
    CONSTRAINT fk_ticket_batch
        FOREIGN KEY (batch_id)
        REFERENCES competitor_ticket.integration_batch(batch_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_scan_confirmed_by_user
        FOREIGN KEY (scan_confirmed_by_user_id)
        REFERENCES competitor_ticket.app_user(user_id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,
    CONSTRAINT ck_ticket_scan_status
        CHECK (scan_status IN ('NO_FILE', 'FILE_UPLOADED', 'FILE_CONFIRMED'))
);

CREATE TABLE competitor_ticket.ticket_item (
    ticket_item_id                bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    ticket_id                     bigint NOT NULL,
    item_sequence                 integer NOT NULL,
    product_code                  varchar(50),
    product_description           varchar(255),
    quantity                      numeric(18,4),
    unit_price                    numeric(18,4),
    line_amount                   numeric(18,4),
    source_item_payload           jsonb NOT NULL,
    created_at                    timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ticket_item_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES competitor_ticket.ticket(ticket_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT uq_ticket_item_ticket_seq
        UNIQUE (ticket_id, item_sequence),
    CONSTRAINT ck_ticket_item_quantity
        CHECK (quantity IS NULL OR quantity >= 0),
    CONSTRAINT ck_ticket_item_unit_price
        CHECK (unit_price IS NULL OR unit_price >= 0),
    CONSTRAINT ck_ticket_item_line_amount
        CHECK (line_amount IS NULL OR line_amount >= 0)
);

CREATE TABLE competitor_ticket.ticket_store (
    ticket_store_id               bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    ticket_id                     bigint NOT NULL,
    store_code                    varchar(30) NOT NULL,
    created_at                    timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ticket_store_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES competitor_ticket.ticket(ticket_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT uq_ticket_store_ticket_store
        UNIQUE (ticket_id, store_code)
);

CREATE TABLE competitor_ticket.ticket_scan_file (
    ticket_scan_file_id           bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    ticket_id                     bigint NOT NULL,
    file_name                     varchar(255) NOT NULL,
    file_extension                varchar(20) NOT NULL,
    mime_type                     varchar(100) NOT NULL,
    file_size_bytes               bigint NOT NULL,
    file_hash                     varchar(128) NOT NULL,
    storage_path                  varchar(500) NOT NULL,
    storage_provider              varchar(30) NOT NULL DEFAULT 'IFS',
    version_number                integer NOT NULL DEFAULT 1,
    is_active                     boolean NOT NULL DEFAULT true,
    is_confirmed                  boolean NOT NULL DEFAULT false,
    uploaded_by_user_id           bigint NOT NULL,
    uploaded_at                   timestamptz NOT NULL DEFAULT NOW(),
    confirmed_by_user_id          bigint,
    confirmed_at                  timestamptz,
    replaced_by_file_id           bigint,
    notes                         text,
    created_at                    timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ticket_scan_file_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES competitor_ticket.ticket(ticket_id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,
    CONSTRAINT fk_ticket_scan_file_uploaded_by_user
        FOREIGN KEY (uploaded_by_user_id)
        REFERENCES competitor_ticket.app_user(user_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_scan_file_confirmed_by_user
        FOREIGN KEY (confirmed_by_user_id)
        REFERENCES competitor_ticket.app_user(user_id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,
    CONSTRAINT fk_ticket_scan_file_replaced_by
        FOREIGN KEY (replaced_by_file_id)
        REFERENCES competitor_ticket.ticket_scan_file(ticket_scan_file_id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,
    CONSTRAINT uq_ticket_scan_file_ticket_version
        UNIQUE (ticket_id, version_number),
    CONSTRAINT ck_ticket_scan_file_size
        CHECK (file_size_bytes > 0),
    CONSTRAINT ck_ticket_scan_file_storage_provider
        CHECK (storage_provider IN ('IFS', 'LOCAL', 'SHARED', 'OBJECT_STORAGE')),
    CONSTRAINT ck_ticket_scan_file_version
        CHECK (version_number > 0),
    CONSTRAINT ck_ticket_scan_file_confirmed_fields
        CHECK (
            (is_confirmed = false AND confirmed_at IS NULL AND confirmed_by_user_id IS NULL)
            OR
            (is_confirmed = true AND confirmed_at IS NOT NULL AND confirmed_by_user_id IS NOT NULL)
        ),
    CONSTRAINT ck_ticket_scan_file_confirmed_active
        CHECK (NOT is_confirmed OR is_active = true),
    CONSTRAINT ck_ticket_scan_file_replaced_by_self
        CHECK (replaced_by_file_id IS NULL OR replaced_by_file_id <> ticket_scan_file_id)
);

CREATE TRIGGER trg_ticket_fill_source_ticket_key
BEFORE INSERT OR UPDATE OF source_ticket_code, source_business_code, source_store_code, source_ticket_date
ON competitor_ticket.ticket
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_fill_source_ticket_key();

CREATE TRIGGER trg_ticket_set_updated_at
BEFORE UPDATE ON competitor_ticket.ticket
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_set_updated_at();

CREATE TRIGGER trg_ticket_scan_file_assign_version
BEFORE INSERT ON competitor_ticket.ticket_scan_file
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_assign_ticket_scan_file_version();

CREATE TRIGGER trg_ticket_scan_file_validate
BEFORE INSERT OR UPDATE ON competitor_ticket.ticket_scan_file
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_validate_ticket_scan_file();

CREATE TRIGGER trg_ticket_scan_file_prevent_confirmed_update
BEFORE UPDATE OR DELETE ON competitor_ticket.ticket_scan_file
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_prevent_confirmed_scan_file_changes();

CREATE TRIGGER trg_ticket_scan_file_sync_ticket
AFTER INSERT OR UPDATE OR DELETE ON competitor_ticket.ticket_scan_file
FOR EACH ROW
EXECUTE FUNCTION competitor_ticket.fn_after_ticket_scan_file_change();

CREATE TABLE competitor_ticket.audit_event (
    audit_event_id                bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    event_type                    varchar(50) NOT NULL,
    entity_name                   varchar(50) NOT NULL,
    entity_id                     bigint,
    source_ticket_key             varchar(120),
    user_id                       bigint,
    event_timestamp               timestamptz NOT NULL DEFAULT NOW(),
    old_values_json               jsonb,
    new_values_json               jsonb,
    event_details_json            jsonb,
    ip_address                    varchar(64),
    created_at                    timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_audit_event_user
        FOREIGN KEY (user_id)
        REFERENCES competitor_ticket.app_user(user_id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL
);

CREATE INDEX idx_integration_batch_status
    ON competitor_ticket.integration_batch(status);
CREATE INDEX idx_integration_batch_started_at
    ON competitor_ticket.integration_batch(started_at);
CREATE INDEX idx_integration_file_batch
    ON competitor_ticket.integration_file(batch_id);
CREATE INDEX idx_integration_file_type
    ON competitor_ticket.integration_file(file_type);
CREATE INDEX idx_integration_file_status
    ON competitor_ticket.integration_file(status);
CREATE INDEX idx_integration_error_batch
    ON competitor_ticket.integration_error(batch_id);
CREATE INDEX idx_integration_error_file
    ON competitor_ticket.integration_error(integration_file_id);
CREATE INDEX idx_integration_error_source_ticket_key
    ON competitor_ticket.integration_error(source_ticket_key);
CREATE INDEX idx_integration_error_entity_type
    ON competitor_ticket.integration_error(entity_type);
CREATE INDEX idx_inbound_ticket_header_batch
    ON competitor_ticket.inbound_ticket_header(batch_id);
CREATE INDEX idx_inbound_ticket_header_source_ticket_key
    ON competitor_ticket.inbound_ticket_header(source_ticket_key);
CREATE INDEX idx_inbound_ticket_header_is_processed
    ON competitor_ticket.inbound_ticket_header(is_processed);
CREATE INDEX idx_inbound_ticket_item_batch
    ON competitor_ticket.inbound_ticket_item(batch_id);
CREATE INDEX idx_inbound_ticket_item_source_ticket_key
    ON competitor_ticket.inbound_ticket_item(source_ticket_key);
CREATE INDEX idx_inbound_ticket_item_is_processed
    ON competitor_ticket.inbound_ticket_item(is_processed);
CREATE INDEX idx_inbound_ticket_store_batch
    ON competitor_ticket.inbound_ticket_store(batch_id);
CREATE INDEX idx_inbound_ticket_store_source_ticket_key
    ON competitor_ticket.inbound_ticket_store(source_ticket_key);
CREATE INDEX idx_inbound_ticket_store_store_code
    ON competitor_ticket.inbound_ticket_store(applies_to_store_code);
CREATE INDEX idx_inbound_ticket_store_is_processed
    ON competitor_ticket.inbound_ticket_store(is_processed);
CREATE INDEX idx_app_user_role_id
    ON competitor_ticket.app_user(role_id);
CREATE INDEX idx_app_user_is_active
    ON competitor_ticket.app_user(is_active);
CREATE INDEX idx_app_user_store_store_code
    ON competitor_ticket.app_user_store(store_code);
CREATE INDEX idx_app_user_store_user_id
    ON competitor_ticket.app_user_store(user_id);
CREATE INDEX idx_ticket_batch_id
    ON competitor_ticket.ticket(batch_id);
CREATE INDEX idx_ticket_source_status_code
    ON competitor_ticket.ticket(source_status_code);
CREATE INDEX idx_ticket_source_ticket_date
    ON competitor_ticket.ticket(source_ticket_date);
CREATE INDEX idx_ticket_scan_status
    ON competitor_ticket.ticket(scan_status);
CREATE INDEX idx_ticket_has_scan_file
    ON competitor_ticket.ticket(has_scan_file);
CREATE INDEX idx_ticket_item_ticket_id
    ON competitor_ticket.ticket_item(ticket_id);
CREATE INDEX idx_ticket_item_product_code
    ON competitor_ticket.ticket_item(product_code);
CREATE INDEX idx_ticket_store_ticket_id
    ON competitor_ticket.ticket_store(ticket_id);
CREATE INDEX idx_ticket_store_store_code
    ON competitor_ticket.ticket_store(store_code);
CREATE INDEX idx_ticket_scan_file_ticket_id
    ON competitor_ticket.ticket_scan_file(ticket_id);
CREATE INDEX idx_ticket_scan_file_uploaded_by_user_id
    ON competitor_ticket.ticket_scan_file(uploaded_by_user_id);
CREATE INDEX idx_ticket_scan_file_confirmed_by_user_id
    ON competitor_ticket.ticket_scan_file(confirmed_by_user_id);
CREATE INDEX idx_ticket_scan_file_file_hash
    ON competitor_ticket.ticket_scan_file(file_hash);
CREATE INDEX idx_ticket_scan_file_is_confirmed
    ON competitor_ticket.ticket_scan_file(is_confirmed);
CREATE UNIQUE INDEX uq_ticket_scan_file_one_active_per_ticket
    ON competitor_ticket.ticket_scan_file(ticket_id)
    WHERE is_active = true;
CREATE UNIQUE INDEX uq_ticket_scan_file_one_confirmed_per_ticket
    ON competitor_ticket.ticket_scan_file(ticket_id)
    WHERE is_confirmed = true;
CREATE INDEX idx_audit_event_entity
    ON competitor_ticket.audit_event(entity_name, entity_id);
CREATE INDEX idx_audit_event_source_ticket_key
    ON competitor_ticket.audit_event(source_ticket_key);
CREATE INDEX idx_audit_event_user_id
    ON competitor_ticket.audit_event(user_id);
CREATE INDEX idx_audit_event_event_timestamp
    ON competitor_ticket.audit_event(event_timestamp);
CREATE INDEX idx_audit_event_event_type
    ON competitor_ticket.audit_event(event_type);

INSERT INTO competitor_ticket.app_role (role_code, role_name)
VALUES
    ('STORE_USER', 'Usuario de tienda'),
    ('SUPERVISOR', 'Supervisor'),
    ('ADMIN', 'Administrador')
ON CONFLICT (role_code) DO NOTHING;

CREATE OR REPLACE VIEW competitor_ticket.v_ticket_access_store_user AS
SELECT
    t.ticket_id,
    t.source_ticket_key,
    t.source_status_code,
    t.scan_status,
    ts.store_code
FROM competitor_ticket.ticket t
JOIN competitor_ticket.ticket_store ts
  ON ts.ticket_id = t.ticket_id;

CREATE OR REPLACE VIEW competitor_ticket.v_active_ticket_scan_file AS
SELECT
    tsf.ticket_scan_file_id,
    tsf.ticket_id,
    tsf.file_name,
    tsf.file_extension,
    tsf.mime_type,
    tsf.file_size_bytes,
    tsf.file_hash,
    tsf.storage_path,
    tsf.storage_provider,
    tsf.version_number,
    tsf.is_confirmed,
    tsf.uploaded_by_user_id,
    tsf.uploaded_at,
    tsf.confirmed_by_user_id,
    tsf.confirmed_at
FROM competitor_ticket.ticket_scan_file tsf
WHERE tsf.is_active = true;
```

## Comentarios sobre el DDL PostgreSQL

### Notas operativas
- El trigger `fn_assign_ticket_scan_file_version` es util como **respaldo** de versionamiento automatico, pero para el flujo real de reemplazo se recomienda usar la funcion `fn_replace_ticket_scan_file` documentada aparte.
- El trigger `fn_validate_ticket_scan_file` garantiza la regla `source_status_code = '9'`.
- El trigger `fn_prevent_confirmed_scan_file_changes` protege contra cambios a archivos confirmados.
- El trigger `fn_after_ticket_scan_file_change` sincroniza `ticket.scan_status` y los campos de confirmacion.

### Recomendacion
Para operacion real del archivo escaneado, usar:
- `fn_replace_ticket_scan_file`
- `fn_confirm_ticket_scan_file`

Y evitar `INSERT/UPDATE` directos desde la aplicacion.
