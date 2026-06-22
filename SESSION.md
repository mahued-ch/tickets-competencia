# Resumen de Sesión — Tickets Competencia

## Objetivo
Sistema Web de Gestión de Tickets de Competencia (reemplazo de InvesDoc).

## Estado Actual (22/jun/2026)

### Backend — Python/FastAPI + PostgreSQL/SQLAlchemy 2.0

#### Endpoints (todos bajo `/api/v1`)

| Ruta | Método | Rol | Estado |
|------|--------|-----|--------|
| `/health` | GET | público | ✅ |
| `/auth/login` | POST | público | ✅ |
| `/auth/logout` | POST | autenticado | ✅ |
| `/auth/password` | PUT | autenticado | ✅ |
| `/me` | GET | autenticado | ✅ |
| `/tickets` | GET | según permiso | ✅ |
| `/tickets/{id}` | GET | según permiso | ✅ |
| `/tickets/{id}/items` | GET | según permiso | ✅ |
| `/tickets/{id}/stores` | GET | según permiso | ✅ |
| `/tickets/{id}/scan-file` | GET/POST | según permiso | ✅ |
| `/tickets/{id}/scan-file/confirm` | PUT | según permiso | ✅ |
| `/tickets/{id}/scan-file/content` | GET | según permiso | ✅ |
| `/tickets/coverage` | GET | ADMIN/SUPERVISOR | ✅ |
| `/audit/events` | GET | ADMIN/SUPERVISOR | ✅ |
| `/admin/users` | GET/POST | ADMIN | ✅ |
| `/admin/users/{id}` | PUT/DELETE | ADMIN | ✅ |
| `/admin/users/{id}/password` | PUT | ADMIN | ✅ |
| `/admin/users/{id}/stores` | GET/POST | ADMIN | ✅ |
| `/admin/users/{id}/stores/{code}` | DELETE | ADMIN | ✅ |
| `/integration/batches` | GET | ADMIN | ✅ |
| `/integration/batches/{id}` | GET | ADMIN | ✅ |
| `/integration/batches/{id}/files` | GET | ADMIN | ✅ |
| `/integration/batches/{id}/errors` | GET | ADMIN | ✅ |

#### Modelos
- **user**: `AppRole`, `AppUser`, `AppUserStore`
- **ticket**: `Ticket`, `TicketItem`, `TicketStore`, `TicketScanFile`, `AuditEvent`
- **integration**: `IntegrationBatch`, `IntegrationFile`, `IntegrationError`
- **inbound**: `InboundTicketHeader`, `InboundTicketItem`, `InboundTicketStore`

#### Servicios
- `ticket_service`: search, detail, coverage stats
- `security_service`: role/permission checks
- `scan_file_service`: upload/replace/confirm via PostgreSQL functions
- `importer_service`: staging-first insert + archivo hash + error handling
- `audit_service`: búsqueda de eventos de auditoría

#### Migraciones
- `scripts/migrate_v2_staging.py`: tablas inbound + columnas payload
- `scripts/migrate_v3_scan_file_functions.py`: funciones `fn_replace_ticket_scan_file()` y `fn_confirm_ticket_scan_file()`

### Frontend — React/Vite

#### Páginas
| Ruta | Componente | Estado |
|------|-----------|--------|
| `/login` | LoginPage | ✅ |
| `/dashboard` | DashboardPage | ✅ |
| `/admin/users` | UsersPage | ✅ — CRUD completo, orden por columnas |
| `/coverage` | SupervisorDashboardPage | ✅ |
| `/audit` | AuditPage | ✅ |
| `/integration` | IntegrationPage | ✅ |
| `/tickets` | TicketsPage | ✅ |
| `/tickets/:id` | TicketDetailPage | ✅ |

#### Componentes UI
- `DataTable` — tabla genérica con ordenamiento por columnas (▲/▼), sortable via prop
- `StatusBadge` — badges de estado con colores
- `Breadcrumbs` — migas de pan
- `AppLayout` — layout con sidebar + topbar

#### Funcionalidades recientes
- **Editar usuario**: modal con campos login, nombre, email, rol, activo/inactivo
- **Eliminar usuario**: soft-delete (is_active=false), protege usuario admin
- **Ordenamiento**: columnas Login, Nombre, Rol y Tienda ordenables clicando el header

### Pruebas

#### Backend — Unitarias (51 tests, pytest + SQLite in-memory)
| Archivo | Tests | Estado |
|---------|-------|--------|
| `test_security_service.py` | 9 | ✅ |
| `test_ticket_service.py` | 8 | ✅ |
| `test_api_endpoints.py` | 10 | ✅ |
| `test_scan_file_service.py` | 16 | ✅ — mocks selectivos solo para TextClause |
| `test_importer_service.py` | 8 | ✅ — directorios temporales con tmp_path |

- SQLite in-memory con `StaticPool` + `check_same_thread=False`
- Schemas de PostgreSQL eliminados vía evento `before_create`
- `BigInteger` PKs convertidos a `Integer` automáticamente en `conftest.py`
- Mocks con `patch.object(db_session, 'execute', side_effect=...)` que solo interceptan `TextClause`

#### Backend — E2E contra PostgreSQL real (14 tests)
| Archivo | Tests | Estado |
|---------|-------|--------|
| `test_scan_file_e2e.py` | 7 | ✅ — upload, confirm, replace, auditoría |
| `test_importer_e2e.py` | 7 | ✅ — batch completo, duplicados, errores |

- Conexión directa a `localhost:5432/tickets_db`
- `Base.metadata.create_all()` + funciones PG en fixture session-scoped
- Seeds con `SELECT ... WHERE` antes de INSERT para evitar duplicados
- Cada test usa supropio ticket/archivo (UUID) para evitar interferencias

#### Frontend (10 tests, vitest + testing-library)
| Archivo | Tests | Estado |
|---------|-------|--------|
| `DataTable.test.jsx` | 4 | ✅ |
| `StatusBadge.test.jsx` | 4 | ✅ |
| `AuthContext.test.jsx` | 2 | ✅ |

#### Total: 75 tests (61 backend + 10 frontend + 4 herramientas)

### Bugs corregidos
- **security_service.py**: se restauró filtro `FILE_CONFIRMED` para `STORE_USER` (no veían tickets confirmados)
- **migrate_v3**: columnas ambiguas `ticket_scan_file_id` y `confirmed_at` en `fn_confirm_ticket_scan_file` — chocaban con output parameters del `RETURNS TABLE`. Se antepuso `competitor_ticket.ticket_scan_file.` para desambiguar.
- **audit_event**: faltaba columna `ip_address` (no creada en migraciones iniciales). Se agregó `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` en setup E2E.

### Pendiente / Mejoras futuras
- CI/CD pipeline (GitHub Actions)
- Ejecutar migración v3 corregida contra la BD de producción (script corregido pero no ejecutado)
- Tests del importador E2E con más escenarios de error
- End-to-end general con cypress/playwright
- Dockerizar E2E tests con base de datos aislada
