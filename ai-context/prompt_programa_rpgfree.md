# Prompt: Programa RPG Free para exportar tickets desde AS400 a JSON en IFS

## Contexto del proyecto

Somos parte de un proyecto que sustituye la funcionalidad documental de InvesDoc para **tickets de competencia**. La informacion base del ticket ya existe en AS400 y necesitamos un programa en **RPG Free** (ILE RPG) que lea las tablas origen y genere archivos JSON en el IFS para que un importador externo (sistema web Python) los consuma.

El flujo completo es:

```
SAP → AS400 (tablas SAPRCTGH / SAPRCTGD / SAPRCTGDI) → Programa RPG Free → IFS (archivos JSON) → Importador web → Base de datos → API → Frontend
```

## Tablas origen en AS400

### SAPRCTGH — Cabecera del ticket

Campos clave:

| Campo    | Tipo          | Descripcion                         |
|----------|---------------|--------------------------------------|
| DGHTCK   | varchar/?     | Codigo del ticket (source_ticket_code) |
| DGHCOD   | varchar/?     | Codigo de negocio (source_business_code) |
| DGHSTR   | varchar/?     | Codigo de tienda origen (source_store_code) |
| DGHDAT   | date          | Fecha del ticket (source_ticket_date) |
| DGHEST   | varchar(10)   | Estatus del ticket en origen (source_status_code) |
| DGHFEAL  | timestamptz   | Fecha/hora de alta en origen (opcional) |

**Llave natural:** `DGHTCK + DGHCOD + DGHSTR + DGHDAT`

### SAPRCTGD — Detalle / productos del ticket

Campos clave:

| Campo     | Tipo        | Descripcion                         |
|-----------|-------------|--------------------------------------|
| DGHTCK    | varchar     | Codigo del ticket (relaciona con SAPRCTGH) |
| DGHCOD    | varchar     | Codigo de negocio                    |
| DGHSTR    | varchar     | Codigo de tienda origen              |
| DGHDAT    | date        | Fecha del ticket                     |
| DGDPRO    | integer     | Secuencia del item (source_item_sequence) |
| DGDART    | varchar(50) | Codigo de producto (product_code)    |
| DGDDSC    | varchar     | Descripcion del producto (product_description) |
| DGDCAN    | numeric(18,4) | Cantidad (quantity)                |
| DGDPRE    | numeric(18,4) | Precio unitario (unit_price)       |
| DGDIMP    | numeric(18,4) | Importe linea (line_amount)        |

**Llave:** `DGHTCK + DGHCOD + DGHSTR + DGHDAT + DGDPRO`

### SAPRCTGDI — Distribucion (tiendas a las que aplica)

Campos clave:

| Campo     | Tipo        | Descripcion                               |
|-----------|-------------|--------------------------------------------|
| DGHTCK    | varchar     | Codigo del ticket                          |
| DGHCOD    | varchar     | Codigo de negocio                          |
| DGHSTR    | varchar     | Codigo de tienda origen                    |
| DGHDAT    | date        | Fecha del ticket                           |
| DGDITIE   | varchar(30) | Codigo de tienda destino (applies_to_store_code) |

**Llave:** `DGHTCK + DGHCOD + DGHSTR + DGHDAT + DGDITIE`

## Archivos JSON a generar

Por cada ejecucion del programa se genera un **lote** de 4 archivos con la siguiente convencion de nombres:

```
header_YYYYMMDD_HHMMSS.json
items_YYYYMMDD_HHMMSS.json
stores_YYYYMMDD_HHMMSS.json
control_YYYYMMDD_HHMMSS.json
```

Los 4 archivos deben usar **el mismo timestamp** (momento de inicio de la extraccion).

### 1. header_YYYYMMDD_HHMMSS.json

Array JSON de objetos con los campos mapeados a nombres neutrales (no los nombres AS400):

```json
[
  {
    "source_ticket_code": "DGHTCK",
    "source_business_code": "DGHCOD",
    "source_store_code": "DGHSTR",
    "source_ticket_date": "YYYY-MM-DD",
    "source_status_code": "DGHEST",
    "payload": {
      "raw_fields": {
        "DGHTCK": "...",
        "DGHCOD": "...",
        "DGHSTR": "...",
        "DGHDAT": "...",
        "DGHEST": "...",
        "DGHFEAL": "..."
      }
    }
  }
]
```

El campo `payload.raw_fields` debe contener los valores originales de AS400 para trazabilidad.

### 2. items_YYYYMMDD_HHMMSS.json

Array JSON de objetos:

```json
[
  {
    "source_ticket_code": "DGHTCK",
    "source_business_code": "DGHCOD",
    "source_store_code": "DGHSTR",
    "source_ticket_date": "YYYY-MM-DD",
    "source_item_sequence": 1,
    "product_code": "DGDART",
    "product_description": "DGDDSC",
    "quantity": 2.0000,
    "unit_price": 45.5000,
    "line_amount": 91.0000,
    "payload": {
      "raw_fields": {
        "DGDPRO": 1,
        "DGDART": "...",
        "DGDDSC": "...",
        "DGDCAN": 2.0000,
        "DGDPRE": 45.5000,
        "DGDIMP": 91.0000
      }
    }
  }
]
```

### 3. stores_YYYYMMDD_HHMMSS.json

Array JSON de objetos:

```json
[
  {
    "source_ticket_code": "DGHTCK",
    "source_business_code": "DGHCOD",
    "source_store_code": "DGHSTR",
    "source_ticket_date": "YYYY-MM-DD",
    "applies_to_store_code": "DGDITIE",
    "payload": {
      "raw_fields": {
        "DGDITIE": "..."
      }
    }
  }
]
```

### 4. control_YYYYMMDD_HHMMSS.json

Objeto JSON unico (NO array). Este archivo **debe ser el ultimo en escribirse** y funciona como senal de "lote completo":

```json
{
  "batch_code": "YYYYMMDD_HHMMSS",
  "generated_at": "YYYY-MM-DDTHH:MM:SS-06:00",
  "source_system": "AS400",
  "files": [
    {
      "file_type": "HEADER",
      "file_name": "header_YYYYMMDD_HHMMSS.json",
      "record_count": 1200
    },
    {
      "file_type": "ITEM",
      "file_name": "items_YYYYMMDD_HHMMSS.json",
      "record_count": 8450
    },
    {
      "file_type": "STORE",
      "file_name": "stores_YYYYMMDD_HHMMSS.json",
      "record_count": 2400
    }
  ],
  "layout_version": "1.0"
}
```

- `batch_code` es el timestamp compartido.
- `generated_at` es la fecha/hora ISO 8601 con offset horario.
- `record_count` debe reflejar la cantidad real de registros escritos en cada archivo.
- `layout_version` es fijo `"1.0"`.

## Estructura de carpetas IFS

```
/ifs/tickets/inbound/
/ifs/tickets/inbound/ARCHIVE/
/ifs/tickets/inbound/ERROR/        (opcional pero recomendado)
```

Los archivos se escriben directamente en `/ifs/tickets/inbound/`. No se usan subcarpetas por lote.

El programa NO debe mover archivos a ARCHIVE/ERROR, eso lo hace el importador del lado del sistema web.

## Reglas obligatorias del programa

1. **Timestamp comun**: los 4 archivos deben compartir exactamente el mismo timestamp `YYYYMMDD_HHMMSS`.
2. **Orden de escritura**: escribir primero `header_*`, luego `items_*`, luego `stores_*`, y **por ultimo** `control_*`. El `control_*` es la senal de "lote completo".
3. **Seleccion de datos**: extraer SOLO tickets que aun no han sido procesados. Definir un criterio de seleccion (ej. basado en `DGHFEAL` o un flag, o extraer todo el universo actual como carga inicial, y luego solo nuevos desde la ultima extraccion). Recomendacion: usar una tabla de control con la fecha/hora de la ultima extraccion exitosa.
4. **Integridad**: si falla la escritura de cualquier archivo antes del `control_*`, no debe quedar un lote huerfano. Idealmente el programa deberia limpiar archivos parciales si algo falla.
5. **Manejo de caracteres especiales**: escapar correctamente caracteres JSON (comillas dobles, backslashes, saltos de linea, etc.) en los valores de texto (descripcion de producto, etc.).
6. **Formato numerico**: usar punto como separador decimal, sin separadores de miles.
7. **Formato fecha**: ISO 8601 (`YYYY-MM-DD`) para fechas, ISO 8601 con offset para timestamps.
8. **Idempotencia**: si se ejecuta dos veces con el mismo criterio, no debe producir registros duplicados en los archivos (el importador web ya maneja deduplicacion, pero el programa debe ser limpio).
9. **Logging**: el programa debe dejar un log (en un archivo de salida o en un spool) indicando:
   - timestamp de inicio y fin
   - cuantos tickets (cabeceras) se extrajeron
   - cuantos items
   - cuantas tiendas
   - cuantos archivos se escribieron
   - errores si los hubo
10. **Control de calidad**: verificar que todos los tickets en `header_*` tengan sus correspondientes items en `items_*` y stores en `stores_*` antes de escribir `control_*`.

## Requisitos tecnicos del programa RPG Free

- Lenguaje: **ILE RPG Free** (miembros en fuente fisica, compilables con CRTBNDRPG o CRTRPGMOD + CRTPGM).
- Usar **APIs de IFS** nativas:
  - `open()` / `write()` / `close()` para archivos, o
  - `Qy2UsOpenFile()` / `Qy2UsWriteFile()` / `Qy2UsCloseFile()` si se prefiere.
  - O usar `Qp0lWrit()`, `Qp0lCreat()`, etc.
- Generar el JSON manualmente como cadenas (no usar librerias externas). Construir la salida concatenando segmentos con las APIs de IFS.
- Declarar la estructura para las tablas AS400 mediante definiciones `DCL-DS` con `EXTNAME` o mediante `DCL-F` con `DISK`.
- El programa debe recibir un parametro opcional: fecha/hora de ultima extraccion. Si no se pasa, extraer todo el universo.
- Los archivos JSON deben escribirse en **UTF-8** (CCSID 1208).
- Usar `RENAME` en las estructuras de datos para mapear los nombres AS400 a nombres legibles (opcional).
- Comentar el codigo en espanol.

## Entregable esperado

1. Codigo fuente RPG Free completo (.rpgle o .sqlrpgle segun corresponda).
2. Instrucciones de compilacion (comandos CRTBNDRPG o CRTRPGMOD + CRTPGM).
3. Ejemplo de ejecucion (llamada CALL desde CL o desde linea de comandos).
4. Ejemplo de los 4 archivos JSON de salida basado en datos dummy.

## Notas adicionales

- El importador web espera **un solo lote por ejecucion**. No generar lotes huecos (sin datos). Si no hay datos nuevos, se puede generar igual un lote con arrays vacios y un control con `record_count: 0` — pero es preferible no generar archivos si no hay datos. Decidir e indicar la estrategia.
- Los archivos deben ser texto plano, formato JSON valido, sin BOM.
- El programa debe ser autocontenido, sin dependencias externas mas alla de las APIs de IFS de IBM i.
