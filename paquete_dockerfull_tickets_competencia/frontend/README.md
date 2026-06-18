# Starter Frontend Ejecutable - Sistema Web de Gestion de Tickets de Competencia

Este starter entrega una **base ejecutable de frontend** para arrancar la capa web del proyecto.

> **Importante:** este starter esta pensado para trabajar junto con el **starter backend ejecutable** ya generado. Usa autenticacion demo por encabezado `X-Demo-User` y consume la API del backend base.

## Que incluye
- **React + Vite**
- **React Router**
- **Axios** para consumo de API
- Auth demo con seleccion de usuario
- Layout base con menu lateral
- Modulo de tickets:
  - lista
  - filtros
  - detalle
  - items
  - stores
  - resumen del archivo escaneado
  - upload/reemplazo/confirmacion del archivo
- Modulo de lotes (admin/supervisor)
- Modulo de usuarios (admin)
- Componentes UI base
- CSS simple para arranque rapido

## Requisitos
- Node.js 20+
- npm 10+
- Backend starter ejecutandose

## Variables de entorno
Copiar:
```bash
cp .env.example .env
```

Por defecto:
```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Arranque rapido
```bash
npm install
npm run dev
```

Luego abrir:
```text
http://localhost:5173
```

## Flujo demo
1. Levantar el **starter backend**.
2. Abrir la app.
3. Elegir usuario demo en login:
   - `admin`
   - `supervisor`
   - `store_a`
   - `store_b`
4. Navegar entre Tickets, Lotes y Usuarios segun rol.

## Notas tecnicas
- El frontend guarda el usuario demo en `localStorage`.
- Cada request agrega el header `X-Demo-User`.
- La visualizacion del archivo escaneado se hace via `fetch`/blob para poder enviar encabezado demo.
- Este starter no incluye autenticacion productiva real.

## Endpoints que consume
- `GET /api/v1/health`
- `GET /api/v1/me`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticketId}`
- `GET /api/v1/tickets/{ticketId}/items`
- `GET /api/v1/tickets/{ticketId}/stores`
- `GET /api/v1/tickets/{ticketId}/scan-file`
- `POST /api/v1/tickets/{ticketId}/scan-file`
- `PUT /api/v1/tickets/{ticketId}/scan-file/confirm`
- `GET /api/v1/tickets/{ticketId}/scan-file/content`
- `GET /api/v1/integration/batches`
- `GET /api/v1/integration/batches/{batchId}`
- `GET /api/v1/integration/batches/{batchId}/files`
- `GET /api/v1/integration/batches/{batchId}/errors`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{userId}/stores`
- `POST /api/v1/admin/users/{userId}/stores`

## Siguiente paso recomendado
Una vez validado el flujo base:
1. conectar autenticacion real;
2. endurecer manejo de errores y permisos;
3. mejorar UX/UI corporativa;
4. conectar con backend final endurecido.
