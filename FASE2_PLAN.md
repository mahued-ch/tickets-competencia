# Fase 2 — Importación por escaneo + enriquecimiento con catálogos

## Visión general

Actualmente el sistema importa tickets desde AS400 y luego se les asocia un archivo escaneado.
En la Fase 2 se invierte el flujo: se importa la **imagen del ticket escaneado** (de la competencia),
se extrae su información mediante OCR + IA, se enriquece con catálogos de referencia,
y un supervisor revisa y confirma antes de grabar definitivamente en las tablas de tickets.

---

## Flujo completo

```
Imagen escaneada → OCR (Tesseract + LLM) → items extraídos
    → Enriquecimiento (catálogos) → Preview + revisión editable → Confirmación → Ticket final
```

---

## 1. Catálogos necesarios (nuevos modelos + migraciones)

### competitor_store
```sql
Catálogo de tiendas de la competencia.
Permite mapear (business_code, store_code) a nombre, dirección, etc.

store_id           PK
business_code      VARCHAR(10)      -- cadena (WMT, BRS, SOR, etc.)
store_code         VARCHAR(30)      -- tienda en esa cadena
store_name         VARCHAR(200)
address            TEXT
is_active          BOOLEAN          DEFAULT true
```

### chedraui_product
```sql
Catálogo maestro de productos Chedraui.

product_id         PK
sku                VARCHAR(50)      UNIQUE, SKU Chedraui
upc                VARCHAR(20)      -- código de barras
description        VARCHAR(255)     -- descripción oficial
list_price         DECIMAL(18,4)    -- precio de referencia
department_code    SMALLINT
sub_department_code SMALLINT
class_code         SMALLINT
subclass_code      SMALLINT
is_active          BOOLEAN          DEFAULT true
```

### competitor_product_mapping
```sql
Relaciona productos de la competencia con productos Chedraui.
Un producto competidor puede tener OPCIÓN A: código, OPCIÓN B: solo descripción.

mapping_id             PK
business_code          VARCHAR(10)      -- cadena origen
competitor_code        VARCHAR(50)      -- código en el ticket (nullable)
competitor_description VARCHAR(255)     -- descripción en el ticket
chedraui_product_id    FK → chedraui_product
match_type             VARCHAR(20)      -- 'UPC' | 'CODE' | 'MANUAL' | 'FUZZY'
confidence             DECIMAL(5,4)     -- 0.0000 - 1.0000
is_active              BOOLEAN          DEFAULT true

UNIQUE(business_code, competitor_code)
```

### nearby_store
```sql
Relaciona tienda de competencia con tiendas Chedraui cercanas.
Se usan para poblar TicketStore al importar.

nearby_id                   PK
business_code               VARCHAR(10)      -- cadena competencia
store_code                  VARCHAR(30)      -- tienda competencia
nearby_chedraui_store_code  VARCHAR(30)      -- tienda Chedraui cercana
distance_km                 DECIMAL(8,2)
is_active                   BOOLEAN          DEFAULT true

UNIQUE(business_code, store_code, nearby_chedraui_store_code)
```

---

## 2. OCR + Extracción con IA

### ocr_result
```sql
Resultado del OCR aplicado a un ticket escaneado.

ocr_id               PK
ticket_scan_file_id  FK → ticket_scan_file
raw_text             TEXT             -- texto completo extraído por Tesseract
extracted_items      JSONB            -- items parseados por LLM
llm_model            VARCHAR(100)     -- modelo usado
confidence           DECIMAL(5,4)     -- confianza general
created_at           TIMESTAMP
```

### Proceso
1. Tesseract extrae texto plano de la imagen
2. Se envía a LLM (OpenAI/Claude) con prompt estructurado por cadena para extraer:
   `[{code, description, quantity, unit_price, line_amount}]`
3. El prompt se adapta según `source_business_code` (varía por cadena si usan código, UPC, o nada)
4. Se guarda el resultado en `ocr_result`

### Dependencias
- `pytesseract` + `Pillow`
- `openai` o `anthropic`
- Tesseract OCR engine instalado en el servidor

---

## 3. Enriquecimiento (enrichment_service.py)

Flujo por cada item extraído del OCR:

1. **Match por UPC** → busca en `chedraqui_product.upc`
2. **Match por código competencia** → busca en `competitor_product_mapping` con `(business_code, competitor_code)`
3. **Match fuzzy por descripción** → busca en `competitor_product_mapping.competitor_description` con similitud (pg_trgm o difflib)
   - Si confidence > 0.85 → match automático
   - Si no → queda pendiente de revisión
4. Si hay match → copia `sku`, `upc`, `description`, `list_price`, jerarquía al `TicketItem`
5. **Tiendas:** busca en `nearby_store` por `(business_code, store_code)` y agrega a `TicketStore`

### ticket_enrichment
```sql
Controla el estado de enriquecimiento de un ticket.

enrichment_id        PK
ticket_id            FK → ticket
ocr_result_id        FK → ocr_result
status               VARCHAR(20)      -- 'PENDING' | 'REVIEW' | 'COMPLETED' | 'REJECTED'
reviewed_by_user_id  FK → app_user    (nullable)
reviewed_at          TIMESTAMP        (nullable)
notes                TEXT             (nullable)
```

---

## 4. Preview + Revisión editable

### Endpoints backend

| Método | Ruta | Propósito |
|--------|------|-----------|
| `GET` | `/api/v1/tickets/{ticket_id}/scan-file/download` | Servir archivo de imagen para el preview |
| `GET` | `/api/v1/tickets/{ticket_id}/enrichment-preview` | Preview: imagen + items extraídos + items enriquecidos + sugerencias |
| `PUT` | `/api/v1/tickets/{ticket_id}/enrichment-items` | Actualizar items editados por el revisor |
| `POST` | `/api/v1/tickets/{ticket_id}/enrichment-confirm` | Confirmar enriquecimiento y grabar |
| `POST` | `/api/v1/tickets/{ticket_id}/enrichment-reject` | Rechazar enriquecimiento |

### Frontend: EnrichmentReviewPage

- Split view:
  - **Izquierda:** imagen del ticket escaneado (`<img src="/api/v1/tickets/{id}/scan-file/download">`)
  - **Derecha:** tabla de items editable inline (descripción, precio, cantidad, UPC, jerarquía)
- Items sin match se marcan visualmente (ej. fondo amarillo)
- Botón "Buscar producto" por item → modal de búsqueda en `chedraui_product` (SKU, UPC, descripción)
- Botones: "Confirmar enriquecimiento" / "Rechazar"
- El revisor puede modificar **cualquier campo** antes de confirmar

### Endpoint servir imagen

`GET /api/v1/tickets/{ticket_id}/scan-file/download`

- Busca el `TicketScanFile` activo del ticket
- Devuelve `FileResponse` con el contenido desde `storage_path`
- Headers: `Content-Type: image/*`, `Content-Disposition: inline`

---

## 5. Autorización para revisión

- **Sin restricción de rol específico por ahora**
- Se aplica el filtro existente `can_view_ticket()` de `security_service.py`
- Para `STORE_USER` ya está limitado a sus tiendas asignadas
- En la práctica solo ADMIN/SUPERVISOR tendrán acceso real
- Si se requiere un rol específico después, se agrega sin cambios estructurales

---

## 6. Importación CSV de catálogos

- Endpoint `POST /api/v1/catalogs/{catalog}/import` que recibe CSV con header row
- Mapea columnas por nombre (case-insensitive)
- Templates descargables: `GET /api/v1/catalogs/{catalog}/template` → CSV con headers
- Los catálogos también se pueden alimentar desde UI de administración (CRUD estándar)

---

## 7. Orden de implementación

| # | Componente | Prioridad |
|---|-----------|-----------|
| 1 | Modelos + migraciones de catálogos | Alta |
| 2 | CRUD backend + frontend para catálogos | Alta |
| 3 | Endpoint servir imagen escaneada | Alta |
| 4 | Servicio OCR (Tesseract + LLM) + ocr_result | Alta |
| 5 | Servicio de enriquecimiento | Alta |
| 6 | Modelo ticket_enrichment + flujo de revisión | Alta |
| 7 | Frontend: preview split + tabla editable + confirmar/rechazar | Alta |
| 8 | Importación CSV de catálogos | Media |
| 9 | Tests (unit, frontend, E2E) | Media |

---

## Acuerdos tomados

1. **OCR:** Tesseract para extracción base + LLM para parseo estructurado
2. **Precio en catálogo:** Se agrega `list_price` a `chedraui_product`
3. **Revisor:** Sin restricción de rol, aplica `can_view_ticket()` existente
4. **Edición:** El revisor puede modificar cualquier campo del item antes de confirmar
5. **Catálogos iniciales:** Se cargarán vía CSV (templates disponibles) y/o UI
6. **Importación CSV:** Formato con header row, mapeo por nombre de columna
7. **Preview de imagen:** Endpoint nuevo para servir archivo desde `storage_path`
