# Paquete Dockerfull - Sistema Web de Gestion de Tickets de Competencia

Este paquete entrega la **orquestacion Dockerfull** para levantar el sistema completo usando los dos starters ya generados previamente:

- `starter_tecnico_tickets_competencia.zip`  -> backend ejecutable
- `starter_frontend_tickets_competencia.zip` -> frontend ejecutable

## Objetivo
Permitir que levantes todo el stack con Docker Compose:
- PostgreSQL
- Backend FastAPI
- Frontend React servido con Nginx
- Proxy `/api` -> backend

## Importante
Este paquete **no duplica** el codigo completo de backend/frontend para evitar redundancia de artefactos. En lugar de eso, incluye:
- `docker-compose.yml`
- Dockerfiles de backend y frontend
- Nginx config
- scripts de preparacion y arranque
- entrypoint del backend
- wait_for_db
- guia de integracion

## Requisitos
- Tener descargados estos 2 archivos en la misma carpeta del paquete:
  - `starter_tecnico_tickets_competencia.zip`
  - `starter_frontend_tickets_competencia.zip`
- Docker Engine + Docker Compose plugin

## Flujo recomendado
### 1) Colocar zips en esta carpeta
```text
paquete_dockerfull_tickets_competencia/
  starter_tecnico_tickets_competencia.zip
  starter_frontend_tickets_competencia.zip
```

### 2) Preparar estructura
```bash
bash scripts/prepare_from_starters.sh
```

### 3) Copiar variables
```bash
cp .env.example .env
```

### 4) Levantar todo
```bash
docker compose up --build
```

## URLs esperadas
- Frontend: `http://localhost:8080`
- Backend docs: `http://localhost:8000/docs`
- Health backend: `http://localhost:8000/api/v1/health`

## Usuarios demo
En el frontend selecciona uno de estos usuarios:
- `admin`
- `supervisor`
- `store_a`
- `store_b`

## Qué hace el backend al arrancar
1. espera disponibilidad de la BD
2. ejecuta `bootstrap_demo.py`
3. intenta ejecutar `run_importer_demo.py`
4. levanta `uvicorn`

## Qué hace el frontend
1. compila con Vite
2. sirve el build con Nginx
3. hace proxy de `/api` hacia `backend:8000`

## Siguientes pasos recomendados
- sustituir demo auth por auth real
- endurecer backend con funciones SQL finales
- agregar migraciones
- agregar TLS corporativo / reverse proxy externo
