
# Arquitectura e Integracion JSON

## 1. Arquitectura logica objetivo

```text
SAP
  ↓
AS400 (tablas SAPRCTGH / SAPRCTGD / SAPRCTGDI)
  ↓
Programa RPG Free
  ↓
IFS (archivos JSON)
  ↓
Importador del sistema web
  ↓
Base de datos del sistema (staging + operativa)
  ↓
API / Backend
  ↓
Frontend web
  ↓
Usuarios (STORE_USER / SUPERVISOR / ADMIN)
```

## 2. Razon del diseno desacoplado
Se adopta una integracion desacoplada por varias razones:
- aislar AS400 del nuevo sistema web;
- separar tiempos de extraccion y tiempos de carga;
- facilitar reprocesos y trazabilidad;
- permitir auditoria por lote;
- simplificar debugging de errores;
- evitar dependencia directa del nuevo sistema hacia tablas AS400 en linea.

## 3. Flujo oficial de archivos

### 3.1 Generacion
Un programa en RPG Free debe generar periodicamente archivos JSON a partir de las tablas:
- `SAPRCTGH`
- `SAPRCTGD`
- `SAPRCTGDI`

### 3.2 Deposito en IFS
Los archivos se depositan en una sola carpeta `inbound`.

### 3.3 Lectura por el importador
El importador escanea la carpeta, identifica lotes por timestamp en el nombre y procesa el lote solo cuando existe `control_YYYYMMDD_HHMMSS.json`.

### 3.4 Postproceso
- si el lote se integra correctamente: mover archivos a `ARCHIVE`
- si el lote falla por estructura o integridad: mover a `ERROR` (recomendado) o dejarlos para revision manual segun estrategia operativa.

## 4. Estructura de carpetas IFS

```text
/ifs/tickets/inbound/
/ifs/tickets/inbound/ARCHIVE/
/ifs/tickets/inbound/ERROR/   (opcional pero recomendado)
```

### Regla
No se deben crear carpetas por lote. La identificacion del lote la da el timestamp compartido del nombre de archivo.

## 5. Convencion de nombres de archivos

### Patron oficial
```text
header_YYYYMMDD_HHMMSS.json
items_YYYYMMDD_HHMMSS.json
stores_YYYYMMDD_HHMMSS.json
control_YYYYMMDD_HHMMSS.json
```

### Ejemplo real
```text
header_20260618_090000.json
items_20260618_090000.json
stores_20260618_090000.json
control_20260618_090000.json
```

### Regla del lote logico
Todos los archivos del mismo lote deben compartir exactamente el mismo timestamp.

## 6. Regla del control.json
El archivo `control_*.json` es la senal de "lote completo".

### Regla de proceso
El importador **no debe procesar** un lote si no existe su `control_*.json`.

## 7. Layouts JSON recomendados

## 7.1 header.json
Representa cabeceras.

### Estructura sugerida
```json
[
  {
    "source_ticket_code": "...",
    "source_business_code": "...",
    "source_store_code": "...",
    "source_ticket_date": "2026-06-18",
    "source_status_code": "9",
    "payload": {
      "raw_fields": {
        "DGHTCK": "...",
        "DGHCOD": "...",
        "DGHSTR": "...",
        "DGHDAT": "..."
      }
    }
  }
]
```

## 7.2 items.json
Representa detalle de productos.

### Estructura sugerida
```json
[
  {
    "source_ticket_code": "...",
    "source_business_code": "...",
    "source_store_code": "...",
    "source_ticket_date": "2026-06-18",
    "source_item_sequence": 1,
    "product_code": "12345",
    "product_description": "PRODUCTO X",
    "quantity": 2,
    "unit_price": 45.50,
    "line_amount": 91.00,
    "payload": {}
  }
]
```

## 7.3 stores.json
Representa distribucion a tiendas.

### Estructura sugerida
```json
[
  {
    "source_ticket_code": "...",
    "source_business_code": "...",
    "source_store_code": "...",
    "source_ticket_date": "2026-06-18",
    "applies_to_store_code": "0123",
    "payload": {}
  }
]
```

## 7.4 control.json
Representa el control del lote.

### Estructura sugerida
```json
{
  "batch_code": "20260618_090000",
  "generated_at": "2026-06-18T09:00:00-06:00",
  "source_system": "AS400",
  "files": [
    {
      "file_type": "HEADER",
      "file_name": "header_20260618_090000.json",
      "record_count": 1200
    },
    {
      "file_type": "ITEM",
      "file_name": "items_20260618_090000.json",
      "record_count": 8450
    },
    {
      "file_type": "STORE",
      "file_name": "stores_20260618_090000.json",
      "record_count": 2400
    }
  ],
  "layout_version": "1.0"
}
```

## 8. Proceso recomendado del importador

### 8.1 Descubrimiento
1. escanear `/ifs/tickets/inbound/`;
2. identificar archivos `control_*.json`;
3. derivar el timestamp/lote desde el nombre.

### 8.2 Validacion de consistencia del lote
Por cada `control_*.json` debe validarse:
- existencia de `header_*.json`;
- existencia de `items_*.json`;
- existencia de `stores_*.json`;
- consistencia del timestamp compartido;
- consistencia minima del JSON;
- conteos informados versus conteos reales (si se decide implementar).

### 8.3 Registro del lote
Crear un registro en `integration_batch` con:
- `batch_code`;
- directorios origen/destino;
- estatus inicial (`RECEIVED` o `PROCESSING`);
- conteos.

### 8.4 Registro de archivos
Crear registros en `integration_file` por cada archivo del lote.

### 8.5 Carga staging
Insertar:
- cabeceras en `inbound_ticket_header`;
- items en `inbound_ticket_item`;
- tiendas en `inbound_ticket_store`.

### 8.6 Consolidacion operativa
Procesar cada cabecera nueva:
1. revisar si el ticket ya existe en `ticket`;
2. si existe, omitirlo y registrarlo como repetido;
3. si no existe, crear cabecera en `ticket`;
4. crear sus items en `ticket_item`;
5. crear sus tiendas en `ticket_store`.

### 8.7 Postproceso
- si todo sale bien: mover archivos a `ARCHIVE`;
- si falla el lote: registrar `integration_error` y mover a `ERROR` o mantener para revision operativa.

## 9. Reglas de robustez del importador

### 9.1 Idempotencia
El importador no debe duplicar tickets ya existentes.

### 9.2 Integridad relacional
No consolidar detalle ni distribucion sin cabecera.

### 9.3 Logging
Cada lote debe dejar:
- cuantas cabeceras venian,
- cuantas se insertaron,
- cuantas se omitieron,
- cuantos errores hubo.

### 9.4 Reproceso
La arquitectura con staging permite reprocesar lotes o depurar errores sin perder el payload original.

## 10. Recomendacion sobre el programa RPG Free
El programa RPG Free debe enfocarse en:
- leer tablas AS400 origen;
- construir archivos JSON bien formados;
- escribir primero `header/items/stores`;
- generar `control.json` al final.

### Regla recomendada
El `control.json` debe ser el ultimo archivo del lote en escribirse.

## 11. Responsabilidades por componente

### RPG Free
- extraer informacion;
- formatear JSON;
- escribir archivos en IFS;
- respetar naming convention.

### Importador
- validar archivos y lote;
- registrar batch/files/errors;
- cargar staging;
- consolidar operativa;
- mover a `ARCHIVE/ERROR`.

### Base de datos
- asegurar integridad,
- evitar duplicados,
- controlar archivo escaneado,
- auditar.

### Backend/API
- exponer consultas,
- exponer operaciones del archivo escaneado,
- aplicar seguridad funcional.

### Frontend
- consultar tickets;
- filtrar por rol/tienda;
- mostrar cabecera, detalle, distribucion;
- cargar/reemplazar/confirmar archivo escaneado.
