
# Modelo de Datos Detallado

## 1. Filosofia del modelo
El modelo se divide en dos capas:

1. **Capa de integracion / staging persistente**
2. **Capa operativa del sistema web**

Adicionalmente, hay una capa transversal de:
- seguridad,
- auditoria,
- control de lotes.

## 2. Objetivos del modelo
- preservar trazabilidad de origen;
- desacoplar el formato de entrada del esquema operativo;
- soportar reproceso;
- soportar seguridad por tienda;
- soportar archivo escaneado con versionamiento;
- mantener portabilidad razonable entre PostgreSQL y SQL Server.

## 3. Entidades principales

## 3.1 Control e integracion
- `integration_batch`
- `integration_file`
- `integration_error`

## 3.2 Staging persistente
- `inbound_ticket_header`
- `inbound_ticket_item`
- `inbound_ticket_store`

## 3.3 Modelo operativo
- `ticket`
- `ticket_item`
- `ticket_store`
- `ticket_scan_file`

## 3.4 Seguridad
- `app_role`
- `app_user`
- `app_user_store`

## 3.5 Auditoria
- `audit_event`

---

## 4. Detalle por tabla

## 4.1 integration_batch
Representa un lote logico de integracion identificado por `batch_code`.

### Responsabilidad
- registrar inicio/fin de proceso,
- directorios,
- conteos,
- estatus global del lote.

### Llave primaria
- `batch_id`

### Llave natural importante
- `batch_code` (timestamp del lote, p.ej. `20260618_090000`)

### Campos mas importantes
- `source_system`
- `source_directory`
- `archive_directory`
- `error_directory`
- `status`
- `header_record_count`
- `item_record_count`
- `store_record_count`
- `inserted_ticket_count`
- `skipped_ticket_count`
- `error_count`

### Estatus sugeridos
- `RECEIVED`
- `PROCESSING`
- `PROCESSED`
- `PROCESSED_WITH_ERRORS`
- `FAILED`
- `ARCHIVED`

---

## 4.2 integration_file
Representa cada archivo fisico procesado dentro de un lote.

### Responsabilidad
- registrar existencia de `header/items/stores/control`;
- conservar paths origen/archivo;
- guardar metadata tecnica del archivo.

### Relacion
- muchos `integration_file` pertenecen a un `integration_batch`.

### Campos mas importantes
- `file_type`
- `file_name`
- `original_path`
- `archived_path`
- `file_size_bytes`
- `file_hash`
- `record_count`
- `status`
- `raw_metadata`

### Tipos validos
- `HEADER`
- `ITEM`
- `STORE`
- `CONTROL`

---

## 4.3 integration_error
Representa errores tecnicos o funcionales detectados en el proceso.

### Responsabilidad
- conservar trazabilidad de lotes fallidos;
- registrar errores por entidad o por archivo;
- apoyar depuracion y reproceso.

### Relacion
- pertenece a `integration_batch`;
- opcionalmente vincula a `integration_file`.

### Campos mas importantes
- `entity_type`
- `source_ticket_key`
- `error_code`
- `error_message`
- `payload_fragment`
- `line_number`

---

## 4.4 inbound_ticket_header
Representa cabeceras parseadas desde el archivo fuente.

### Responsabilidad
- staging persistente de la cabecera;
- conservar payload crudo original;
- permitir reproceso y auditoria.

### Relacion
- pertenece a `integration_batch`.

### Llave tecnica de negocio
- `source_ticket_key`

### Campos mas importantes
- `source_ticket_code`
- `source_business_code`
- `source_store_code`
- `source_ticket_date`
- `source_status_code`
- `payload_json`
- `is_processed`
- `processed_at`

### Regla de unicidad
- `unique(batch_id, source_ticket_key)`

---

## 4.5 inbound_ticket_item
Representa el detalle parseado desde el archivo fuente.

### Responsabilidad
- staging persistente de lineas del ticket.

### Relacion
- pertenece a `integration_batch`.

### Campos mas importantes
- `source_ticket_key`
- `source_item_sequence`
- `product_code`
- `product_description`
- `quantity`
- `unit_price`
- `line_amount`
- `payload_json`

### Regla de unicidad
- `unique(batch_id, source_ticket_key, source_item_sequence)`

---

## 4.6 inbound_ticket_store
Representa las tiendas a las que aplica el ticket.

### Responsabilidad
- staging persistente de la distribucion.

### Relacion
- pertenece a `integration_batch`.

### Campos mas importantes
- `source_ticket_key`
- `applies_to_store_code`
- `payload_json`

### Regla de unicidad
- `unique(batch_id, source_ticket_key, applies_to_store_code)`

---

## 4.7 ticket
Es la tabla principal operativa del sistema.

### Responsabilidad
- representar la cabecera consolidada del ticket;
- mantener estatus de origen y estatus documental del escaneo;
- ser la entidad padre del resto del modelo operativo.

### Llave primaria
- `ticket_id`

### Llaves de negocio
- combinacion: `source_ticket_code + source_business_code + source_store_code + source_ticket_date`
- adicional: `source_ticket_key`

### Campos mas importantes
- `source_status_code`
- `source_header_payload`
- `batch_id`
- `scan_status`
- `has_scan_file`
- `scan_confirmed_at`
- `scan_confirmed_by_user_id`

### Estatus documental (`scan_status`)
- `NO_FILE`
- `FILE_UPLOADED`
- `FILE_CONFIRMED`

### Reglas de unicidad
- `unique(source_ticket_key)`
- `unique(source_ticket_code, source_business_code, source_store_code, source_ticket_date)`

### Relacion
- 1 `ticket` -> N `ticket_item`
- 1 `ticket` -> N `ticket_store`
- 1 `ticket` -> N `ticket_scan_file` (historial de versiones)

---

## 4.8 ticket_item
Lineas operativas del ticket.

### Responsabilidad
- representar el detalle de productos consolidado.

### Relacion
- muchos `ticket_item` pertenecen a un `ticket`.

### Campos mas importantes
- `item_sequence`
- `product_code`
- `product_description`
- `quantity`
- `unit_price`
- `line_amount`
- `source_item_payload`

### Regla de unicidad
- `unique(ticket_id, item_sequence)`

---

## 4.9 ticket_store
Tiendas a las que aplica el ticket.

### Responsabilidad
- soportar seguridad y consulta por tienda;
- representar la distribucion consolidada.

### Relacion
- muchos `ticket_store` pertenecen a un `ticket`.

### Campos mas importantes
- `ticket_id`
- `store_code`

### Regla de unicidad
- `unique(ticket_id, store_code)`

---

## 4.10 ticket_scan_file
Representa las versiones del archivo escaneado de un ticket.

### Responsabilidad
- almacenar metadata de los archivos escaneados;
- permitir historial de reemplazos;
- asegurar un solo activo por ticket;
- marcar confirmacion.

### Relacion
- muchos `ticket_scan_file` pertenecen a un `ticket`.

### Campos mas importantes
- `file_name`
- `file_extension`
- `mime_type`
- `file_size_bytes`
- `file_hash`
- `storage_path`
- `storage_provider`
- `version_number`
- `is_active`
- `is_confirmed`
- `uploaded_by_user_id`
- `uploaded_at`
- `confirmed_by_user_id`
- `confirmed_at`
- `replaced_by_file_id`
- `notes`

### Reglas de negocio modeladas
- solo un archivo activo por ticket;
- un archivo confirmado debe estar activo;
- un archivo confirmado no puede modificarse ni borrarse;
- se conserva historial via `version_number` y `replaced_by_file_id`.

---

## 4.11 app_role
Catalogo de roles.

### Valores iniciales
- `STORE_USER`
- `SUPERVISOR`
- `ADMIN`

---

## 4.12 app_user
Usuarios del sistema.

### Relacion
- cada usuario pertenece a un `app_role`.

### Campos mas importantes
- `login_name`
- `display_name`
- `email`
- `role_id`
- `is_active`

---

## 4.13 app_user_store
Relacion entre usuarios y tiendas.

### Responsabilidad
- soportar autorizacion por tienda.

### Relacion
- un usuario puede tener muchas tiendas.

### Regla de acceso resultante
Un usuario de tienda puede consultar un ticket si existe coincidencia entre:
- `ticket_store.store_code`
- `app_user_store.store_code`

---

## 4.14 audit_event
Bitacora de eventos funcionales y tecnicos.

### Responsabilidad
- registrar eventos de integracion,
- registrar eventos del archivo escaneado,
- registrar eventos administrativos.

### Campos mas importantes
- `event_type`
- `entity_name`
- `entity_id`
- `source_ticket_key`
- `user_id`
- `event_timestamp`
- `old_values_json`
- `new_values_json`
- `event_details_json`
- `ip_address`

---

## 5. Relaciones principales del modelo

## 5.1 Relaciones de integracion
```text
integration_batch 1 --- N integration_file
integration_batch 1 --- N integration_error
integration_batch 1 --- N inbound_ticket_header
integration_batch 1 --- N inbound_ticket_item
integration_batch 1 --- N inbound_ticket_store
```

## 5.2 Relaciones operativas del ticket
```text
ticket 1 --- N ticket_item
ticket 1 --- N ticket_store
ticket 1 --- N ticket_scan_file
```

## 5.3 Relaciones de seguridad
```text
app_role 1 --- N app_user
app_user 1 --- N app_user_store
```

## 5.4 Relaciones de auditoria
```text
app_user 1 --- N audit_event (opcional)
```

## 6. Diagrama logico simplificado

```text
integration_batch
  ├── integration_file
  ├── integration_error
  ├── inbound_ticket_header
  ├── inbound_ticket_item
  └── inbound_ticket_store

app_role
  └── app_user
        └── app_user_store

integration_batch
  └── ticket
        ├── ticket_item
        ├── ticket_store
        └── ticket_scan_file

app_user
  ├── ticket.scan_confirmed_by_user_id
  ├── ticket_scan_file.uploaded_by_user_id
  ├── ticket_scan_file.confirmed_by_user_id
  └── audit_event.user_id
```

## 7. Reglas de integridad mas importantes

### 7.1 Ticket unico
No puede existir mas de un ticket con la misma llave de negocio.

### 7.2 Integracion insert-only
La informacion del ticket origen no se sustituye.

### 7.3 Un solo archivo activo por ticket
Garantizado por restriccion/indice unico parcial en PostgreSQL o filtered unique index en SQL Server.

### 7.4 Confirmacion bloqueante
Una vez confirmado un archivo:
- no se modifica,
- no se elimina,
- no se reemplaza.

### 7.5 Seguridad por tienda
La visibilidad del ticket depende de `ticket_store` combinado con `app_user_store`.

## 8. Estrategia de payload JSON
La operacion del sistema vive en columnas relacionales. Los payloads JSON se almacenan para:
- trazabilidad,
- soporte a diagnostico,
- comparacion con origen,
- posible evolucion futura.

### Principio de diseno
No depender del JSON para la operacion critica del sistema. El JSON sirve como respaldo y auditoria, no como unica fuente operativa.

## 9. Consideraciones de portabilidad
El modelo fue diseniado para ser portable entre PostgreSQL y SQL Server.

### Estrategias de portabilidad usadas
- nombres de tablas y columnas neutrales;
- columnas relacionales para la operacion primaria;
- guardar JSON crudo sin depender de consultas complejas sobre JSON para el flujo principal;
- usar surrogate keys enteras;
- separar staging de operacion;
- no depender de enums nativos.

## 10. Que debe implementar otra IA/ID a partir del modelo
1. Importador JSON -> staging -> operativa.
2. API de consulta del ticket.
3. API de consulta del detalle y distribucion.
4. API/servicios para archivo escaneado.
5. Seguridad por rol y tienda.
6. Auditoria funcional.
7. Monitoreo de lotes.
