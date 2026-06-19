
# Funciones PostgreSQL del Archivo Escaneado

## 1. Objetivo de este documento
Este documento explica la operacion completa del **archivo escaneado del ticket** en PostgreSQL, incluyendo:
- la filosofia del flujo,
- los triggers de respaldo,
- la funcion de reemplazo,
- la funcion de confirmacion,
- como utilizarlas,
- por que deben usarse en lugar de inserts/updates directos.

## 2. Principios de diseno del archivo escaneado

### 2.1 El archivo escaneado se asocia al ticket
La relacion es:

```text
ticket 1 --- N ticket_scan_file
```

### 2.2 Solo una version activa
Aunque puede haber historial de versiones, solo una puede estar activa.

### 2.3 Reemplazo antes de confirmar
Mientras el archivo activo no este confirmado, puede reemplazarse por una nueva version.

### 2.4 Confirmacion bloqueante
Una vez confirmado, ya no puede:
- modificarse,
- eliminarse,
- reemplazarse.

### 2.5 Regla de origen
Solo se puede cargar o reemplazar archivo si el ticket tiene:

```text
source_status_code = '9'
```

## 3. Triggers de respaldo sobre `ticket_scan_file`

### 3.1 `fn_assign_ticket_scan_file_version`
Asigna `version_number` automaticamente si no se proporciona.

### 3.2 `fn_validate_ticket_scan_file`
Valida:
- que el ticket exista;
- que el status de origen sea 9;
- que un archivo confirmado tenga campos de confirmacion completos;
- que un archivo confirmado no quede inactivo.

### 3.3 `fn_prevent_confirmed_scan_file_changes`
Impide:
- update de archivo confirmado;
- delete de archivo confirmado.

### 3.4 `fn_after_ticket_scan_file_change`
Despues de insert/update/delete en `ticket_scan_file`, actualiza la tabla `ticket` para que refleje:
- `has_scan_file`
- `scan_status`
- `scan_confirmed_at`
- `scan_confirmed_by_user_id`

## 4. Recomendacion operativa critica
**La aplicacion no debe hacer `INSERT/UPDATE` directos a `ticket_scan_file`** para el flujo principal.

Debe utilizar:
- `fn_replace_ticket_scan_file`
- `fn_confirm_ticket_scan_file`

Dejar inserts directos aumenta el riesgo de:
- violar reglas de reemplazo,
- chocar con el indice de un solo activo,
- tener versionamiento inconsistente,
- perder auditoria.

---

## 5. Funcion de reemplazo / carga inicial

## 5.1 Proposito
`fn_replace_ticket_scan_file` sirve para:
- subir archivo por primera vez;
- reemplazar el archivo activo antes de confirmar.

## 5.2 Garantias que ofrece
- valida al usuario;
- valida que el ticket exista;
- valida `source_status_code = '9'`;
- bloquea el ticket para evitar reemplazos concurrentes;
- bloquea el archivo activo actual;
- impide reemplazo si ya existe archivo confirmado activo;
- desactiva version previa;
- calcula nueva version;
- inserta nueva version;
- liga version previa con la nueva via `replaced_by_file_id`;
- registra auditoria.

## 5.3 Codigo completo

```sql
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

    PERFORM 1
      FROM competitor_ticket.app_user u
     WHERE u.user_id = p_uploaded_by_user_id
       AND u.is_active = true;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario % no existe o esta inactivo', p_uploaded_by_user_id;
    END IF;

    SELECT t.ticket_id,
           t.source_status_code,
           t.source_ticket_key
      INTO v_ticket_id,
           v_source_status_code,
           v_source_ticket_key
      FROM competitor_ticket.ticket t
     WHERE t.ticket_id = p_ticket_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el ticket_id %', p_ticket_id;
    END IF;

    IF v_source_status_code IS DISTINCT FROM '9' THEN
        RAISE EXCEPTION
            'No se permite adjuntar/reemplazar archivo para ticket_id % porque source_status_code = % (se requiere 9)',
            p_ticket_id, v_source_status_code;
    END IF;

    SELECT tsf.ticket_scan_file_id,
           tsf.is_confirmed
      INTO v_previous_file_id,
           v_previous_is_confirmed
      FROM competitor_ticket.ticket_scan_file tsf
     WHERE tsf.ticket_id = p_ticket_id
       AND tsf.is_active = true
     ORDER BY tsf.version_number DESC, tsf.ticket_scan_file_id DESC
     LIMIT 1
     FOR UPDATE;

    IF v_previous_file_id IS NOT NULL AND v_previous_is_confirmed = true THEN
        RAISE EXCEPTION
            'El ticket_id % ya tiene un archivo confirmado (ticket_scan_file_id = %). No se puede reemplazar.',
            p_ticket_id, v_previous_file_id;
    END IF;

    IF v_previous_file_id IS NOT NULL THEN
        UPDATE competitor_ticket.ticket_scan_file
           SET is_active = false
         WHERE ticket_scan_file_id = v_previous_file_id;
    END IF;

    SELECT COALESCE(MAX(tsf.version_number), 0) + 1
      INTO v_next_version
      FROM competitor_ticket.ticket_scan_file tsf
     WHERE tsf.ticket_id = p_ticket_id;

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
        notes
    )
    VALUES
    (
        p_ticket_id,
        p_file_name,
        p_file_extension,
        p_mime_type,
        p_file_size_bytes,
        p_file_hash,
        p_storage_path,
        COALESCE(p_storage_provider, 'IFS'),
        v_next_version,
        true,
        false,
        p_uploaded_by_user_id,
        NOW(),
        NULL,
        NULL,
        NULL,
        p_notes
    )
    RETURNING ticket_scan_file_id
      INTO v_new_file_id;

    IF v_previous_file_id IS NOT NULL THEN
        UPDATE competitor_ticket.ticket_scan_file
           SET replaced_by_file_id = v_new_file_id
         WHERE ticket_scan_file_id = v_previous_file_id;
    END IF;

    INSERT INTO competitor_ticket.audit_event
    (
        event_type,
        entity_name,
        entity_id,
        source_ticket_key,
        user_id,
        event_timestamp,
        old_values_json,
        new_values_json,
        event_details_json
    )
    VALUES
    (
        CASE
            WHEN v_previous_file_id IS NULL THEN 'SCAN_FILE_UPLOADED'
            ELSE 'SCAN_FILE_REPLACED'
        END,
        'ticket_scan_file',
        v_new_file_id,
        v_source_ticket_key,
        p_uploaded_by_user_id,
        NOW(),
        CASE
            WHEN v_previous_file_id IS NULL THEN NULL
            ELSE jsonb_build_object(
                'previous_ticket_scan_file_id', v_previous_file_id
            )
        END,
        jsonb_build_object(
            'new_ticket_scan_file_id', v_new_file_id,
            'new_version_number', v_next_version,
            'file_name', p_file_name,
            'file_extension', p_file_extension,
            'mime_type', p_mime_type,
            'file_size_bytes', p_file_size_bytes,
            'file_hash', p_file_hash,
            'storage_path', p_storage_path,
            'storage_provider', COALESCE(p_storage_provider, 'IFS')
        ),
        jsonb_build_object(
            'ticket_id', p_ticket_id,
            'previous_ticket_scan_file_id', v_previous_file_id,
            'replacement_allowed', true
        )
    );

    new_ticket_scan_file_id      := v_new_file_id;
    new_version_number           := v_next_version;
    previous_ticket_scan_file_id := v_previous_file_id;

    RETURN NEXT;
    RETURN;
END;
$$;
```

## 5.4 Ejemplo de uso - carga inicial
```sql
SELECT *
FROM competitor_ticket.fn_replace_ticket_scan_file(
    p_ticket_id           => 1001,
    p_file_name           => 'ticket_1001_scan_v1.pdf',
    p_file_extension      => 'pdf',
    p_mime_type           => 'application/pdf',
    p_file_size_bytes     => 245678,
    p_file_hash           => 'HASH_ABC_001',
    p_storage_path        => '/ifs/scans/ticket_1001_scan_v1.pdf',
    p_uploaded_by_user_id => 25,
    p_storage_provider    => 'IFS',
    p_notes               => 'Carga inicial del ticket escaneado'
);
```

## 5.5 Ejemplo de uso - reemplazo
```sql
SELECT *
FROM competitor_ticket.fn_replace_ticket_scan_file(
    p_ticket_id           => 1001,
    p_file_name           => 'ticket_1001_scan_v2.pdf',
    p_file_extension      => 'pdf',
    p_mime_type           => 'application/pdf',
    p_file_size_bytes     => 251111,
    p_file_hash           => 'HASH_ABC_002',
    p_storage_path        => '/ifs/scans/ticket_1001_scan_v2.pdf',
    p_uploaded_by_user_id => 25,
    p_storage_provider    => 'IFS',
    p_notes               => 'Se reemplaza por imagen mas legible'
);
```

## 5.6 Resultado esperado
Devuelve:
- `new_ticket_scan_file_id`
- `new_version_number`
- `previous_ticket_scan_file_id`

---

## 6. Funcion de confirmacion

## 6.1 Proposito
`fn_confirm_ticket_scan_file` sirve para confirmar la version activa actual del archivo escaneado.

## 6.2 Garantias que ofrece
- valida usuario;
- valida existencia del ticket;
- bloquea ticket;
- bloquea archivo activo;
- valida que exista archivo activo;
- valida que no este ya confirmado;
- confirma el archivo;
- registra auditoria.

## 6.3 Codigo completo

```sql
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

    PERFORM 1
      FROM competitor_ticket.app_user u
     WHERE u.user_id = p_confirmed_by_user_id
       AND u.is_active = true;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario % no existe o esta inactivo', p_confirmed_by_user_id;
    END IF;

    SELECT t.source_ticket_key
      INTO v_source_ticket_key
      FROM competitor_ticket.ticket t
     WHERE t.ticket_id = p_ticket_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el ticket_id %', p_ticket_id;
    END IF;

    SELECT tsf.ticket_scan_file_id,
           tsf.version_number,
           tsf.is_confirmed
      INTO v_file_id,
           v_version_number,
           v_is_confirmed
      FROM competitor_ticket.ticket_scan_file tsf
     WHERE tsf.ticket_id = p_ticket_id
       AND tsf.is_active = true
     ORDER BY tsf.version_number DESC, tsf.ticket_scan_file_id DESC
     LIMIT 1
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'El ticket_id % no tiene archivo activo para confirmar',
            p_ticket_id;
    END IF;

    IF v_is_confirmed = true THEN
        RAISE EXCEPTION
            'El archivo activo del ticket_id % ya esta confirmado (ticket_scan_file_id = %)',
            p_ticket_id, v_file_id;
    END IF;

    UPDATE competitor_ticket.ticket_scan_file
       SET is_confirmed = true,
           confirmed_at = NOW(),
           confirmed_by_user_id = p_confirmed_by_user_id,
           notes = CASE
                     WHEN p_notes IS NULL OR BTRIM(p_notes) = '' THEN notes
                     WHEN notes IS NULL OR BTRIM(notes) = '' THEN p_notes
                     ELSE notes || E'
' || p_notes
                   END
     WHERE ticket_scan_file_id = v_file_id
     RETURNING confirmed_at
      INTO v_confirmed_at;

    INSERT INTO competitor_ticket.audit_event
    (
        event_type,
        entity_name,
        entity_id,
        source_ticket_key,
        user_id,
        event_timestamp,
        old_values_json,
        new_values_json,
        event_details_json
    )
    VALUES
    (
        'SCAN_FILE_CONFIRMED',
        'ticket_scan_file',
        v_file_id,
        v_source_ticket_key,
        p_confirmed_by_user_id,
        NOW(),
        jsonb_build_object(
            'ticket_scan_file_id', v_file_id,
            'ticket_id', p_ticket_id,
            'version_number', v_version_number,
            'was_confirmed', false
        ),
        jsonb_build_object(
            'ticket_scan_file_id', v_file_id,
            'ticket_id', p_ticket_id,
            'version_number', v_version_number,
            'is_confirmed', true,
            'confirmed_by_user_id', p_confirmed_by_user_id,
            'confirmed_at', v_confirmed_at
        ),
        jsonb_build_object(
            'notes', p_notes
        )
    );

    ticket_scan_file_id := v_file_id;
    ticket_id           := p_ticket_id;
    version_number      := v_version_number;
    confirmed_at        := v_confirmed_at;

    RETURN NEXT;
    RETURN;
END;
$$;
```

## 6.4 Ejemplo de uso
```sql
SELECT *
FROM competitor_ticket.fn_confirm_ticket_scan_file(
    p_ticket_id            => 1001,
    p_confirmed_by_user_id => 25,
    p_notes                => 'Archivo validado y confirmado por operacion'
);
```

## 6.5 Resultado esperado
Devuelve:
- `ticket_scan_file_id`
- `ticket_id`
- `version_number`
- `confirmed_at`

---

## 7. Flujo operativo recomendado del archivo escaneado

### 7.1 Carga inicial
1. backend valida permiso del usuario;
2. backend guarda archivo fisico (IFS/share/object storage segun estrategia);
3. backend llama `fn_replace_ticket_scan_file`;
4. se registra auditoria;
5. `ticket.scan_status` queda `FILE_UPLOADED`.

### 7.2 Reemplazo antes de confirmar
1. backend valida permiso del usuario;
2. backend guarda nueva copia fisica;
3. backend llama `fn_replace_ticket_scan_file`;
4. la funcion desactiva la version previa;
5. inserta la nueva version;
6. registra auditoria;
7. `ticket.scan_status` permanece `FILE_UPLOADED`.

### 7.3 Confirmacion
1. backend valida permiso del usuario;
2. backend llama `fn_confirm_ticket_scan_file`;
3. la funcion confirma el archivo activo;
4. auditoria;
5. `ticket.scan_status` queda `FILE_CONFIRMED`.

### 7.4 Consulta/visualizacion
La UI debe consultar la vista actividad o la tabla `ticket_scan_file` filtrando `is_active = true`.

## 8. Consideraciones de seguridad
Este documento solo valida existencia de usuario. Si se quiere endurecer seguridad desde BD, se puede ampliar para validar:
- que `STORE_USER` solo opere tickets de sus tiendas;
- que `SUPERVISOR` y `ADMIN` tengan acceso global.

### Recomendacion
Esa validacion puede vivir tanto en backend como en funciones de BD. Idealmente, en ambos niveles para mayor blindaje.

## 9. Recomendacion de permisos de BD
- Revocar `INSERT/UPDATE/DELETE` directos sobre `ticket_scan_file` para el usuario tecnico de aplicacion.
- Conceder `EXECUTE` solo sobre las funciones de negocio.

## 10. Posibles extensiones futuras
- funcion para cancelacion/eliminacion logica de archivo no confirmado;
- procedimiento de mantenimiento para purga de archivos huerfanos;
- validacion de hash duplicado por ticket.
