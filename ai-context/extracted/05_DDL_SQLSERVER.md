
# DDL SQL Server Completo

> **Nota**: este script es el equivalente del esquema para SQL Server.
> Se usa para conservar portabilidad si el proyecto se mueve de PostgreSQL a SQL Server.

```sql
/* =========================================================
   SISTEMA WEB DE GESTION DE TICKETS DE COMPETENCIA
   DDL SQL Server v1
   ========================================================= */

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'competitor_ticket'
)
BEGIN
    EXEC('CREATE SCHEMA competitor_ticket');
END
GO

CREATE OR ALTER FUNCTION competitor_ticket.fn_build_source_ticket_key
(
    @source_ticket_code   varchar(30),
    @source_business_code varchar(30),
    @source_store_code    varchar(30),
    @source_ticket_date   date
)
RETURNS varchar(120)
AS
BEGIN
    RETURN
        ISNULL(@source_ticket_code, '') + '|' +
        ISNULL(@source_business_code, '') + '|' +
        ISNULL(@source_store_code, '') + '|' +
        CONVERT(char(8), @source_ticket_date, 112);
END
GO

CREATE TABLE competitor_ticket.app_role
(
    role_id        bigint IDENTITY(1,1) NOT NULL,
    role_code      varchar(30) NOT NULL,
    role_name      varchar(100) NOT NULL,
    is_active      bit NOT NULL CONSTRAINT DF_app_role_is_active DEFAULT (1),
    created_at     datetimeoffset(0) NOT NULL CONSTRAINT DF_app_role_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_app_role PRIMARY KEY (role_id),
    CONSTRAINT UQ_app_role_role_code UNIQUE (role_code)
);
GO

CREATE TABLE competitor_ticket.app_user
(
    user_id        bigint IDENTITY(1,1) NOT NULL,
    login_name     varchar(100) NOT NULL,
    display_name   varchar(150) NOT NULL,
    email          varchar(200) NULL,
    role_id        bigint NOT NULL,
    is_active      bit NOT NULL CONSTRAINT DF_app_user_is_active DEFAULT (1),
    created_at     datetimeoffset(0) NOT NULL CONSTRAINT DF_app_user_created_at DEFAULT (SYSDATETIMEOFFSET()),
    updated_at     datetimeoffset(0) NOT NULL CONSTRAINT DF_app_user_updated_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_app_user PRIMARY KEY (user_id),
    CONSTRAINT UQ_app_user_login_name UNIQUE (login_name),
    CONSTRAINT FK_app_user_role FOREIGN KEY (role_id) REFERENCES competitor_ticket.app_role(role_id)
);
GO

CREATE TABLE competitor_ticket.app_user_store
(
    app_user_store_id bigint IDENTITY(1,1) NOT NULL,
    user_id           bigint NOT NULL,
    store_code        varchar(30) NOT NULL,
    is_active         bit NOT NULL CONSTRAINT DF_app_user_store_is_active DEFAULT (1),
    created_at        datetimeoffset(0) NOT NULL CONSTRAINT DF_app_user_store_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_app_user_store PRIMARY KEY (app_user_store_id),
    CONSTRAINT UQ_app_user_store UNIQUE (user_id, store_code),
    CONSTRAINT FK_app_user_store_user FOREIGN KEY (user_id) REFERENCES competitor_ticket.app_user(user_id) ON DELETE CASCADE
);
GO

CREATE OR ALTER TRIGGER competitor_ticket.trg_app_user_set_updated_at
ON competitor_ticket.app_user
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE u
       SET updated_at = SYSDATETIMEOFFSET()
    FROM competitor_ticket.app_user u
    INNER JOIN inserted i ON u.user_id = i.user_id;
END
GO

CREATE TABLE competitor_ticket.integration_batch
(
    batch_id               bigint IDENTITY(1,1) NOT NULL,
    batch_code             varchar(15) NOT NULL,
    source_system          varchar(30) NOT NULL CONSTRAINT DF_integration_batch_source_system DEFAULT ('AS400'),
    source_directory       varchar(500) NOT NULL,
    archive_directory      varchar(500) NULL,
    error_directory        varchar(500) NULL,
    started_at             datetimeoffset(0) NOT NULL CONSTRAINT DF_integration_batch_started_at DEFAULT (SYSDATETIMEOFFSET()),
    finished_at            datetimeoffset(0) NULL,
    status                 varchar(30) NOT NULL,
    header_record_count    int NOT NULL CONSTRAINT DF_integration_batch_header_record_count DEFAULT (0),
    item_record_count      int NOT NULL CONSTRAINT DF_integration_batch_item_record_count DEFAULT (0),
    store_record_count     int NOT NULL CONSTRAINT DF_integration_batch_store_record_count DEFAULT (0),
    inserted_ticket_count  int NOT NULL CONSTRAINT DF_integration_batch_inserted_ticket_count DEFAULT (0),
    skipped_ticket_count   int NOT NULL CONSTRAINT DF_integration_batch_skipped_ticket_count DEFAULT (0),
    error_count            int NOT NULL CONSTRAINT DF_integration_batch_error_count DEFAULT (0),
    notes                  varchar(max) NULL,
    created_at             datetimeoffset(0) NOT NULL CONSTRAINT DF_integration_batch_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_integration_batch PRIMARY KEY (batch_id),
    CONSTRAINT UQ_integration_batch_batch_code UNIQUE (batch_code),
    CONSTRAINT CK_integration_batch_status CHECK (status IN ('RECEIVED', 'PROCESSING', 'PROCESSED', 'PROCESSED_WITH_ERRORS', 'FAILED', 'ARCHIVED'))
);
GO

CREATE TABLE competitor_ticket.integration_file
(
    integration_file_id    bigint IDENTITY(1,1) NOT NULL,
    batch_id               bigint NOT NULL,
    file_type              varchar(20) NOT NULL,
    file_name              varchar(255) NOT NULL,
    original_path          varchar(500) NOT NULL,
    archived_path          varchar(500) NULL,
    file_size_bytes        bigint NOT NULL,
    file_hash              varchar(128) NULL,
    record_count           int NOT NULL CONSTRAINT DF_integration_file_record_count DEFAULT (0),
    processed_at           datetimeoffset(0) NULL,
    archived_at            datetimeoffset(0) NULL,
    status                 varchar(20) NOT NULL,
    raw_metadata           nvarchar(max) NULL,
    created_at             datetimeoffset(0) NOT NULL CONSTRAINT DF_integration_file_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_integration_file PRIMARY KEY (integration_file_id),
    CONSTRAINT UQ_integration_file_name UNIQUE (file_name),
    CONSTRAINT FK_integration_file_batch FOREIGN KEY (batch_id) REFERENCES competitor_ticket.integration_batch(batch_id) ON DELETE CASCADE,
    CONSTRAINT CK_integration_file_type CHECK (file_type IN ('HEADER', 'ITEM', 'STORE', 'CONTROL')),
    CONSTRAINT CK_integration_file_status CHECK (status IN ('RECEIVED', 'PROCESSING', 'PROCESSED', 'ARCHIVED', 'ERROR', 'SKIPPED')),
    CONSTRAINT CK_integration_file_size CHECK (file_size_bytes >= 0),
    CONSTRAINT CK_integration_file_raw_metadata_json CHECK (raw_metadata IS NULL OR ISJSON(raw_metadata) = 1)
);
GO

CREATE TABLE competitor_ticket.integration_error
(
    integration_error_id   bigint IDENTITY(1,1) NOT NULL,
    batch_id               bigint NOT NULL,
    integration_file_id    bigint NULL,
    entity_type            varchar(20) NOT NULL,
    source_ticket_key      varchar(120) NULL,
    error_code             varchar(50) NOT NULL,
    error_message          varchar(max) NOT NULL,
    payload_fragment       nvarchar(max) NULL,
    line_number            int NULL,
    created_at             datetimeoffset(0) NOT NULL CONSTRAINT DF_integration_error_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_integration_error PRIMARY KEY (integration_error_id),
    CONSTRAINT FK_integration_error_batch FOREIGN KEY (batch_id) REFERENCES competitor_ticket.integration_batch(batch_id) ON DELETE CASCADE,
    CONSTRAINT FK_integration_error_file FOREIGN KEY (integration_file_id) REFERENCES competitor_ticket.integration_file(integration_file_id) ON DELETE SET NULL,
    CONSTRAINT CK_integration_error_entity_type CHECK (entity_type IN ('BATCH', 'CONTROL', 'HEADER', 'ITEM', 'STORE', 'SCAN_FILE', 'SYSTEM')),
    CONSTRAINT CK_integration_error_payload_json CHECK (payload_fragment IS NULL OR ISJSON(payload_fragment) = 1)
);
GO

CREATE TABLE competitor_ticket.inbound_ticket_header
(
    inbound_header_id       bigint IDENTITY(1,1) NOT NULL,
    batch_id                bigint NOT NULL,
    source_ticket_code      varchar(30) NOT NULL,
    source_business_code    varchar(30) NOT NULL,
    source_store_code       varchar(30) NOT NULL,
    source_ticket_date      date NOT NULL,
    source_ticket_key AS (
        ISNULL(source_ticket_code, '') + '|' +
        ISNULL(source_business_code, '') + '|' +
        ISNULL(source_store_code, '') + '|' +
        CONVERT(char(8), source_ticket_date, 112)
    ) PERSISTED,
    source_status_code      varchar(10) NULL,
    source_created_at       datetimeoffset(0) NULL,
    payload_json            nvarchar(max) NOT NULL,
    is_processed            bit NOT NULL CONSTRAINT DF_inbound_ticket_header_is_processed DEFAULT (0),
    processed_at            datetimeoffset(0) NULL,
    created_at              datetimeoffset(0) NOT NULL CONSTRAINT DF_inbound_ticket_header_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_inbound_ticket_header PRIMARY KEY (inbound_header_id),
    CONSTRAINT FK_inbound_ticket_header_batch FOREIGN KEY (batch_id) REFERENCES competitor_ticket.integration_batch(batch_id) ON DELETE CASCADE,
    CONSTRAINT UQ_inbound_ticket_header_batch_key UNIQUE (batch_id, source_ticket_key),
    CONSTRAINT CK_inbound_ticket_header_payload_json CHECK (ISJSON(payload_json) = 1)
);
GO

CREATE TABLE competitor_ticket.inbound_ticket_item
(
    inbound_item_id         bigint IDENTITY(1,1) NOT NULL,
    batch_id                bigint NOT NULL,
    source_ticket_code      varchar(30) NOT NULL,
    source_business_code    varchar(30) NOT NULL,
    source_store_code       varchar(30) NOT NULL,
    source_ticket_date      date NOT NULL,
    source_ticket_key AS (
        ISNULL(source_ticket_code, '') + '|' +
        ISNULL(source_business_code, '') + '|' +
        ISNULL(source_store_code, '') + '|' +
        CONVERT(char(8), source_ticket_date, 112)
    ) PERSISTED,
    source_item_sequence    int NOT NULL,
    product_code            varchar(50) NULL,
    product_description     varchar(255) NULL,
    quantity                decimal(18,4) NULL,
    unit_price              decimal(18,4) NULL,
    line_amount             decimal(18,4) NULL,
    payload_json            nvarchar(max) NOT NULL,
    is_processed            bit NOT NULL CONSTRAINT DF_inbound_ticket_item_is_processed DEFAULT (0),
    processed_at            datetimeoffset(0) NULL,
    created_at              datetimeoffset(0) NOT NULL CONSTRAINT DF_inbound_ticket_item_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_inbound_ticket_item PRIMARY KEY (inbound_item_id),
    CONSTRAINT FK_inbound_ticket_item_batch FOREIGN KEY (batch_id) REFERENCES competitor_ticket.integration_batch(batch_id) ON DELETE CASCADE,
    CONSTRAINT UQ_inbound_ticket_item_batch_key_seq UNIQUE (batch_id, source_ticket_key, source_item_sequence),
    CONSTRAINT CK_inbound_ticket_item_payload_json CHECK (ISJSON(payload_json) = 1),
    CONSTRAINT CK_inbound_ticket_item_quantity CHECK (quantity IS NULL OR quantity >= 0),
    CONSTRAINT CK_inbound_ticket_item_unit_price CHECK (unit_price IS NULL OR unit_price >= 0),
    CONSTRAINT CK_inbound_ticket_item_line_amount CHECK (line_amount IS NULL OR line_amount >= 0)
);
GO

CREATE TABLE competitor_ticket.inbound_ticket_store
(
    inbound_store_id        bigint IDENTITY(1,1) NOT NULL,
    batch_id                bigint NOT NULL,
    source_ticket_code      varchar(30) NOT NULL,
    source_business_code    varchar(30) NOT NULL,
    source_store_code       varchar(30) NOT NULL,
    source_ticket_date      date NOT NULL,
    source_ticket_key AS (
        ISNULL(source_ticket_code, '') + '|' +
        ISNULL(source_business_code, '') + '|' +
        ISNULL(source_store_code, '') + '|' +
        CONVERT(char(8), source_ticket_date, 112)
    ) PERSISTED,
    applies_to_store_code   varchar(30) NOT NULL,
    payload_json            nvarchar(max) NOT NULL,
    is_processed            bit NOT NULL CONSTRAINT DF_inbound_ticket_store_is_processed DEFAULT (0),
    processed_at            datetimeoffset(0) NULL,
    created_at              datetimeoffset(0) NOT NULL CONSTRAINT DF_inbound_ticket_store_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_inbound_ticket_store PRIMARY KEY (inbound_store_id),
    CONSTRAINT FK_inbound_ticket_store_batch FOREIGN KEY (batch_id) REFERENCES competitor_ticket.integration_batch(batch_id) ON DELETE CASCADE,
    CONSTRAINT UQ_inbound_ticket_store_batch_key_store UNIQUE (batch_id, source_ticket_key, applies_to_store_code),
    CONSTRAINT CK_inbound_ticket_store_payload_json CHECK (ISJSON(payload_json) = 1)
);
GO

CREATE TABLE competitor_ticket.ticket
(
    ticket_id                   bigint IDENTITY(1,1) NOT NULL,
    source_ticket_code          varchar(30) NOT NULL,
    source_business_code        varchar(30) NOT NULL,
    source_store_code           varchar(30) NOT NULL,
    source_ticket_date          date NOT NULL,
    source_ticket_key AS (
        ISNULL(source_ticket_code, '') + '|' +
        ISNULL(source_business_code, '') + '|' +
        ISNULL(source_store_code, '') + '|' +
        CONVERT(char(8), source_ticket_date, 112)
    ) PERSISTED,
    source_status_code          varchar(10) NULL,
    source_header_payload       nvarchar(max) NOT NULL,
    batch_id                    bigint NOT NULL,
    scan_status                 varchar(25) NOT NULL CONSTRAINT DF_ticket_scan_status DEFAULT ('NO_FILE'),
    has_scan_file               bit NOT NULL CONSTRAINT DF_ticket_has_scan_file DEFAULT (0),
    scan_confirmed_at           datetimeoffset(0) NULL,
    scan_confirmed_by_user_id   bigint NULL,
    created_at                  datetimeoffset(0) NOT NULL CONSTRAINT DF_ticket_created_at DEFAULT (SYSDATETIMEOFFSET()),
    updated_at                  datetimeoffset(0) NOT NULL CONSTRAINT DF_ticket_updated_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_ticket PRIMARY KEY (ticket_id),
    CONSTRAINT UQ_ticket_source_key UNIQUE (source_ticket_key),
    CONSTRAINT UQ_ticket_source_tuple UNIQUE (
        source_ticket_code,
        source_business_code,
        source_store_code,
        source_ticket_date
    ),
    CONSTRAINT FK_ticket_batch FOREIGN KEY (batch_id) REFERENCES competitor_ticket.integration_batch(batch_id),
    CONSTRAINT FK_ticket_scan_confirmed_by_user FOREIGN KEY (scan_confirmed_by_user_id) REFERENCES competitor_ticket.app_user(user_id),
    CONSTRAINT CK_ticket_source_header_payload_json CHECK (ISJSON(source_header_payload) = 1),
    CONSTRAINT CK_ticket_scan_status CHECK (scan_status IN ('NO_FILE', 'FILE_UPLOADED', 'FILE_CONFIRMED'))
);
GO

CREATE TABLE competitor_ticket.ticket_item
(
    ticket_item_id              bigint IDENTITY(1,1) NOT NULL,
    ticket_id                   bigint NOT NULL,
    item_sequence               int NOT NULL,
    product_code                varchar(50) NULL,
    product_description         varchar(255) NULL,
    quantity                    decimal(18,4) NULL,
    unit_price                  decimal(18,4) NULL,
    line_amount                 decimal(18,4) NULL,
    source_item_payload         nvarchar(max) NOT NULL,
    created_at                  datetimeoffset(0) NOT NULL CONSTRAINT DF_ticket_item_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_ticket_item PRIMARY KEY (ticket_item_id),
    CONSTRAINT FK_ticket_item_ticket FOREIGN KEY (ticket_id) REFERENCES competitor_ticket.ticket(ticket_id) ON DELETE CASCADE,
    CONSTRAINT UQ_ticket_item_ticket_seq UNIQUE (ticket_id, item_sequence),
    CONSTRAINT CK_ticket_item_source_item_payload_json CHECK (ISJSON(source_item_payload) = 1),
    CONSTRAINT CK_ticket_item_quantity CHECK (quantity IS NULL OR quantity >= 0),
    CONSTRAINT CK_ticket_item_unit_price CHECK (unit_price IS NULL OR unit_price >= 0),
    CONSTRAINT CK_ticket_item_line_amount CHECK (line_amount IS NULL OR line_amount >= 0)
);
GO

CREATE TABLE competitor_ticket.ticket_store
(
    ticket_store_id             bigint IDENTITY(1,1) NOT NULL,
    ticket_id                   bigint NOT NULL,
    store_code                  varchar(30) NOT NULL,
    created_at                  datetimeoffset(0) NOT NULL CONSTRAINT DF_ticket_store_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_ticket_store PRIMARY KEY (ticket_store_id),
    CONSTRAINT FK_ticket_store_ticket FOREIGN KEY (ticket_id) REFERENCES competitor_ticket.ticket(ticket_id) ON DELETE CASCADE,
    CONSTRAINT UQ_ticket_store_ticket_store UNIQUE (ticket_id, store_code)
);
GO

CREATE TABLE competitor_ticket.ticket_scan_file
(
    ticket_scan_file_id         bigint IDENTITY(1,1) NOT NULL,
    ticket_id                   bigint NOT NULL,
    file_name                   varchar(255) NOT NULL,
    file_extension              varchar(20) NOT NULL,
    mime_type                   varchar(100) NOT NULL,
    file_size_bytes             bigint NOT NULL,
    file_hash                   varchar(128) NOT NULL,
    storage_path                varchar(500) NOT NULL,
    storage_provider            varchar(30) NOT NULL CONSTRAINT DF_ticket_scan_file_storage_provider DEFAULT ('IFS'),
    version_number              int NOT NULL CONSTRAINT DF_ticket_scan_file_version_number DEFAULT (1),
    is_active                   bit NOT NULL CONSTRAINT DF_ticket_scan_file_is_active DEFAULT (1),
    is_confirmed                bit NOT NULL CONSTRAINT DF_ticket_scan_file_is_confirmed DEFAULT (0),
    uploaded_by_user_id         bigint NOT NULL,
    uploaded_at                 datetimeoffset(0) NOT NULL CONSTRAINT DF_ticket_scan_file_uploaded_at DEFAULT (SYSDATETIMEOFFSET()),
    confirmed_by_user_id        bigint NULL,
    confirmed_at                datetimeoffset(0) NULL,
    replaced_by_file_id         bigint NULL,
    notes                       varchar(max) NULL,
    created_at                  datetimeoffset(0) NOT NULL CONSTRAINT DF_ticket_scan_file_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_ticket_scan_file PRIMARY KEY (ticket_scan_file_id),
    CONSTRAINT FK_ticket_scan_file_ticket FOREIGN KEY (ticket_id) REFERENCES competitor_ticket.ticket(ticket_id) ON DELETE CASCADE,
    CONSTRAINT FK_ticket_scan_file_uploaded_by_user FOREIGN KEY (uploaded_by_user_id) REFERENCES competitor_ticket.app_user(user_id),
    CONSTRAINT FK_ticket_scan_file_confirmed_by_user FOREIGN KEY (confirmed_by_user_id) REFERENCES competitor_ticket.app_user(user_id),
    CONSTRAINT FK_ticket_scan_file_replaced_by FOREIGN KEY (replaced_by_file_id) REFERENCES competitor_ticket.ticket_scan_file(ticket_scan_file_id),
    CONSTRAINT UQ_ticket_scan_file_ticket_version UNIQUE (ticket_id, version_number),
    CONSTRAINT CK_ticket_scan_file_size CHECK (file_size_bytes > 0),
    CONSTRAINT CK_ticket_scan_file_storage_provider CHECK (storage_provider IN ('IFS', 'LOCAL', 'SHARED', 'OBJECT_STORAGE')),
    CONSTRAINT CK_ticket_scan_file_version CHECK (version_number > 0),
    CONSTRAINT CK_ticket_scan_file_confirmed_fields CHECK (
        (is_confirmed = 0 AND confirmed_at IS NULL AND confirmed_by_user_id IS NULL)
        OR
        (is_confirmed = 1 AND confirmed_at IS NOT NULL AND confirmed_by_user_id IS NOT NULL)
    ),
    CONSTRAINT CK_ticket_scan_file_confirmed_active CHECK (
        is_confirmed = 0 OR is_active = 1
    ),
    CONSTRAINT CK_ticket_scan_file_replaced_by_self CHECK (
        replaced_by_file_id IS NULL OR replaced_by_file_id <> ticket_scan_file_id
    )
);
GO

CREATE OR ALTER TRIGGER competitor_ticket.trg_ticket_set_updated_at
ON competitor_ticket.ticket
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE t
       SET updated_at = SYSDATETIMEOFFSET()
    FROM competitor_ticket.ticket t
    INNER JOIN inserted i ON t.ticket_id = i.ticket_id;
END
GO

CREATE OR ALTER TRIGGER competitor_ticket.trg_ticket_scan_file_assign_version
ON competitor_ticket.ticket_scan_file
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH i AS
    (
        SELECT
            i.ticket_id,
            i.file_name,
            i.file_extension,
            i.mime_type,
            i.file_size_bytes,
            i.file_hash,
            i.storage_path,
            i.storage_provider,
            i.version_number,
            i.is_active,
            i.is_confirmed,
            i.uploaded_by_user_id,
            i.uploaded_at,
            i.confirmed_by_user_id,
            i.confirmed_at,
            i.replaced_by_file_id,
            i.notes,
            i.created_at,
            ROW_NUMBER() OVER (
                PARTITION BY i.ticket_id
                ORDER BY (SELECT 1)
            ) AS rn
        FROM inserted i
    ),
    base AS
    (
        SELECT
            t.ticket_id,
            ISNULL(MAX(tsf.version_number), 0) AS max_version
        FROM (SELECT DISTINCT ticket_id FROM inserted) t
        LEFT JOIN competitor_ticket.ticket_scan_file tsf WITH (UPDLOCK, HOLDLOCK)
            ON tsf.ticket_id = t.ticket_id
        GROUP BY t.ticket_id
    )
    INSERT INTO competitor_ticket.ticket_scan_file
    (
        ticket_id,
        file_name,
        file_extension,
        mime_type,
        file_size_bytes,
        file_hash,
        storage_path,
        storage_provider,
        version_number,
        is_active,
        is_confirmed,
        uploaded_by_user_id,
        uploaded_at,
        confirmed_by_user_id,
        confirmed_at,
        replaced_by_file_id,
        notes,
        created_at
    )
    SELECT
        i.ticket_id,
        i.file_name,
        i.file_extension,
        i.mime_type,
        i.file_size_bytes,
        i.file_hash,
        i.storage_path,
        ISNULL(i.storage_provider, 'IFS'),
        CASE
            WHEN i.version_number IS NULL OR i.version_number <= 0
                THEN b.max_version + i.rn
            ELSE i.version_number
        END AS version_number,
        ISNULL(i.is_active, 1),
        ISNULL(i.is_confirmed, 0),
        i.uploaded_by_user_id,
        ISNULL(i.uploaded_at, SYSDATETIMEOFFSET()),
        i.confirmed_by_user_id,
        i.confirmed_at,
        i.replaced_by_file_id,
        i.notes,
        ISNULL(i.created_at, SYSDATETIMEOFFSET())
    FROM i
    INNER JOIN base b
        ON b.ticket_id = i.ticket_id;
END
GO

CREATE OR ALTER TRIGGER competitor_ticket.trg_ticket_scan_file_validate_and_sync
ON competitor_ticket.ticket_scan_file
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS
    (
        SELECT 1
        FROM deleted d
        INNER JOIN inserted i ON d.ticket_scan_file_id = i.ticket_scan_file_id
        WHERE d.is_confirmed = 1
    )
    BEGIN
        THROW 50001, 'No se puede modificar un archivo escaneado confirmado.', 1;
    END;

    IF EXISTS
    (
        SELECT 1
        FROM deleted d
        LEFT JOIN inserted i ON d.ticket_scan_file_id = i.ticket_scan_file_id
        WHERE i.ticket_scan_file_id IS NULL
          AND d.is_confirmed = 1
    )
    BEGIN
        THROW 50002, 'No se puede eliminar un archivo escaneado confirmado.', 1;
    END;

    IF EXISTS
    (
        SELECT 1
        FROM inserted i
        INNER JOIN competitor_ticket.ticket t ON t.ticket_id = i.ticket_id
        WHERE ISNULL(t.source_status_code, '') <> '9'
    )
    BEGIN
        THROW 50003, 'No se permite adjuntar/reemplazar archivo porque el ticket no tiene source_status_code = 9.', 1;
    END;

    IF EXISTS
    (
        SELECT 1 FROM inserted i
        WHERE i.is_confirmed = 1
          AND (i.confirmed_at IS NULL OR i.confirmed_by_user_id IS NULL)
    )
    BEGIN
        THROW 50004, 'Un archivo confirmado debe tener confirmed_at y confirmed_by_user_id.', 1;
    END;

    IF EXISTS
    (
        SELECT 1 FROM inserted i
        WHERE i.is_confirmed = 1
          AND i.is_active = 0
    )
    BEGIN
        THROW 50005, 'Un archivo confirmado debe permanecer activo.', 1;
    END;

    ;WITH affected_tickets AS
    (
        SELECT ticket_id FROM inserted
        UNION
        SELECT ticket_id FROM deleted
    ),
    active_file AS
    (
        SELECT
            tsf.ticket_id,
            tsf.is_confirmed,
            tsf.confirmed_at,
            tsf.confirmed_by_user_id,
            ROW_NUMBER() OVER (
                PARTITION BY tsf.ticket_id
                ORDER BY tsf.version_number DESC, tsf.ticket_scan_file_id DESC
            ) AS rn
        FROM competitor_ticket.ticket_scan_file tsf
        INNER JOIN affected_tickets a ON a.ticket_id = tsf.ticket_id
        WHERE tsf.is_active = 1
    )
    UPDATE t
       SET
           has_scan_file = CASE WHEN af.ticket_id IS NULL THEN 0 ELSE 1 END,
           scan_status = CASE
               WHEN af.ticket_id IS NULL THEN 'NO_FILE'
               WHEN af.is_confirmed = 1 THEN 'FILE_CONFIRMED'
               ELSE 'FILE_UPLOADED'
           END,
           scan_confirmed_at = CASE WHEN af.is_confirmed = 1 THEN af.confirmed_at ELSE NULL END,
           scan_confirmed_by_user_id = CASE WHEN af.is_confirmed = 1 THEN af.confirmed_by_user_id ELSE NULL END,
           updated_at = SYSDATETIMEOFFSET()
    FROM competitor_ticket.ticket t
    INNER JOIN affected_tickets a ON a.ticket_id = t.ticket_id
    LEFT JOIN active_file af ON af.ticket_id = t.ticket_id AND af.rn = 1;
END
GO

CREATE TABLE competitor_ticket.audit_event
(
    audit_event_id            bigint IDENTITY(1,1) NOT NULL,
    event_type                varchar(50) NOT NULL,
    entity_name               varchar(50) NOT NULL,
    entity_id                 bigint NULL,
    source_ticket_key         varchar(120) NULL,
    user_id                   bigint NULL,
    event_timestamp           datetimeoffset(0) NOT NULL CONSTRAINT DF_audit_event_event_timestamp DEFAULT (SYSDATETIMEOFFSET()),
    old_values_json           nvarchar(max) NULL,
    new_values_json           nvarchar(max) NULL,
    event_details_json        nvarchar(max) NULL,
    ip_address                varchar(64) NULL,
    created_at                datetimeoffset(0) NOT NULL CONSTRAINT DF_audit_event_created_at DEFAULT (SYSDATETIMEOFFSET()),
    CONSTRAINT PK_audit_event PRIMARY KEY (audit_event_id),
    CONSTRAINT FK_audit_event_user FOREIGN KEY (user_id) REFERENCES competitor_ticket.app_user(user_id),
    CONSTRAINT CK_audit_event_old_values_json CHECK (old_values_json IS NULL OR ISJSON(old_values_json) = 1),
    CONSTRAINT CK_audit_event_new_values_json CHECK (new_values_json IS NULL OR ISJSON(new_values_json) = 1),
    CONSTRAINT CK_audit_event_event_details_json CHECK (event_details_json IS NULL OR ISJSON(event_details_json) = 1)
);
GO

CREATE INDEX IX_integration_batch_status ON competitor_ticket.integration_batch(status);
GO
CREATE INDEX IX_integration_batch_started_at ON competitor_ticket.integration_batch(started_at);
GO
CREATE INDEX IX_integration_file_batch ON competitor_ticket.integration_file(batch_id);
GO
CREATE INDEX IX_integration_file_type ON competitor_ticket.integration_file(file_type);
GO
CREATE INDEX IX_integration_file_status ON competitor_ticket.integration_file(status);
GO
CREATE INDEX IX_integration_error_batch ON competitor_ticket.integration_error(batch_id);
GO
CREATE INDEX IX_integration_error_file ON competitor_ticket.integration_error(integration_file_id);
GO
CREATE INDEX IX_integration_error_source_ticket_key ON competitor_ticket.integration_error(source_ticket_key);
GO
CREATE INDEX IX_integration_error_entity_type ON competitor_ticket.integration_error(entity_type);
GO
CREATE INDEX IX_inbound_ticket_header_batch ON competitor_ticket.inbound_ticket_header(batch_id);
GO
CREATE INDEX IX_inbound_ticket_header_source_ticket_key ON competitor_ticket.inbound_ticket_header(source_ticket_key);
GO
CREATE INDEX IX_inbound_ticket_header_is_processed ON competitor_ticket.inbound_ticket_header(is_processed);
GO
CREATE INDEX IX_inbound_ticket_item_batch ON competitor_ticket.inbound_ticket_item(batch_id);
GO
CREATE INDEX IX_inbound_ticket_item_source_ticket_key ON competitor_ticket.inbound_ticket_item(source_ticket_key);
GO
CREATE INDEX IX_inbound_ticket_item_is_processed ON competitor_ticket.inbound_ticket_item(is_processed);
GO
CREATE INDEX IX_inbound_ticket_store_batch ON competitor_ticket.inbound_ticket_store(batch_id);
GO
CREATE INDEX IX_inbound_ticket_store_source_ticket_key ON competitor_ticket.inbound_ticket_store(source_ticket_key);
GO
CREATE INDEX IX_inbound_ticket_store_store_code ON competitor_ticket.inbound_ticket_store(applies_to_store_code);
GO
CREATE INDEX IX_inbound_ticket_store_is_processed ON competitor_ticket.inbound_ticket_store(is_processed);
GO
CREATE INDEX IX_app_user_role_id ON competitor_ticket.app_user(role_id);
GO
CREATE INDEX IX_app_user_is_active ON competitor_ticket.app_user(is_active);
GO
CREATE INDEX IX_app_user_store_store_code ON competitor_ticket.app_user_store(store_code);
GO
CREATE INDEX IX_app_user_store_user_id ON competitor_ticket.app_user_store(user_id);
GO
CREATE INDEX IX_ticket_batch_id ON competitor_ticket.ticket(batch_id);
GO
CREATE INDEX IX_ticket_source_status_code ON competitor_ticket.ticket(source_status_code);
GO
CREATE INDEX IX_ticket_source_ticket_date ON competitor_ticket.ticket(source_ticket_date);
GO
CREATE INDEX IX_ticket_scan_status ON competitor_ticket.ticket(scan_status);
GO
CREATE INDEX IX_ticket_has_scan_file ON competitor_ticket.ticket(has_scan_file);
GO
CREATE INDEX IX_ticket_item_ticket_id ON competitor_ticket.ticket_item(ticket_id);
GO
CREATE INDEX IX_ticket_item_product_code ON competitor_ticket.ticket_item(product_code);
GO
CREATE INDEX IX_ticket_store_ticket_id ON competitor_ticket.ticket_store(ticket_id);
GO
CREATE INDEX IX_ticket_store_store_code ON competitor_ticket.ticket_store(store_code);
GO
CREATE INDEX IX_ticket_scan_file_ticket_id ON competitor_ticket.ticket_scan_file(ticket_id);
GO
CREATE INDEX IX_ticket_scan_file_uploaded_by_user_id ON competitor_ticket.ticket_scan_file(uploaded_by_user_id);
GO
CREATE INDEX IX_ticket_scan_file_confirmed_by_user_id ON competitor_ticket.ticket_scan_file(confirmed_by_user_id);
GO
CREATE INDEX IX_ticket_scan_file_file_hash ON competitor_ticket.ticket_scan_file(file_hash);
GO
CREATE INDEX IX_ticket_scan_file_is_confirmed ON competitor_ticket.ticket_scan_file(is_confirmed);
GO
CREATE UNIQUE INDEX UX_ticket_scan_file_one_active_per_ticket
    ON competitor_ticket.ticket_scan_file(ticket_id)
    WHERE is_active = 1;
GO
CREATE UNIQUE INDEX UX_ticket_scan_file_one_confirmed_per_ticket
    ON competitor_ticket.ticket_scan_file(ticket_id)
    WHERE is_confirmed = 1;
GO
CREATE INDEX IX_audit_event_entity ON competitor_ticket.audit_event(entity_name, entity_id);
GO
CREATE INDEX IX_audit_event_source_ticket_key ON competitor_ticket.audit_event(source_ticket_key);
GO
CREATE INDEX IX_audit_event_user_id ON competitor_ticket.audit_event(user_id);
GO
CREATE INDEX IX_audit_event_event_timestamp ON competitor_ticket.audit_event(event_timestamp);
GO
CREATE INDEX IX_audit_event_event_type ON competitor_ticket.audit_event(event_type);
GO

IF NOT EXISTS (SELECT 1 FROM competitor_ticket.app_role WHERE role_code = 'STORE_USER')
BEGIN
    INSERT INTO competitor_ticket.app_role (role_code, role_name)
    VALUES ('STORE_USER', 'Usuario de tienda');
END
GO
IF NOT EXISTS (SELECT 1 FROM competitor_ticket.app_role WHERE role_code = 'SUPERVISOR')
BEGIN
    INSERT INTO competitor_ticket.app_role (role_code, role_name)
    VALUES ('SUPERVISOR', 'Supervisor');
END
GO
IF NOT EXISTS (SELECT 1 FROM competitor_ticket.app_role WHERE role_code = 'ADMIN')
BEGIN
    INSERT INTO competitor_ticket.app_role (role_code, role_name)
    VALUES ('ADMIN', 'Administrador');
END
GO

CREATE OR ALTER VIEW competitor_ticket.v_ticket_access_store_user
AS
SELECT
    t.ticket_id,
    t.source_ticket_key,
    t.source_status_code,
    t.scan_status,
    ts.store_code
FROM competitor_ticket.ticket t
INNER JOIN competitor_ticket.ticket_store ts
    ON ts.ticket_id = t.ticket_id;
GO

CREATE OR ALTER VIEW competitor_ticket.v_active_ticket_scan_file
AS
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
WHERE tsf.is_active = 1;
GO
```

## Comentarios sobre SQL Server
- La logica del `source_ticket_key` se resuelve con columnas calculadas `PERSISTED`.
- El versionamiento automatico del archivo escaneado se resolvio con `INSTEAD OF INSERT` para suplir la ausencia de `BEFORE INSERT` estilo PostgreSQL.
- El soporte JSON se modela con `NVARCHAR(MAX)` + `ISJSON(...)`.
- La integridad de "un archivo activo" y "un confirmado" se garantiza con `filtered unique indexes`.
