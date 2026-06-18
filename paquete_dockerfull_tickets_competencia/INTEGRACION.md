# Guía de Integración del Paquete Dockerfull

## 1. Prerrequisitos
Debes partir de los dos starters ya generados:
- backend starter
- frontend starter

## 2. Script de preparación
El script `scripts/prepare_from_starters.sh` hace lo siguiente:
1. valida que existan los 2 ZIP
2. descomprime el starter backend como `backend/`
3. descomprime el starter frontend como `frontend/`
4. agrega / sobreescribe:
   - `backend/Dockerfile`
   - `backend/scripts/entrypoint.sh`
   - `backend/scripts/wait_for_db.py`
   - `backend/.dockerignore`
   - `frontend/Dockerfile`
   - `frontend/nginx/default.conf`
   - `frontend/.dockerignore`
   - `frontend/.env.example`

## 3. Estructura final esperada
```text
paquete_dockerfull_tickets_competencia/
  docker-compose.yml
  .env
  backend/
  frontend/
  scripts/
```

## 4. Si quieres regenerar desde cero
Borra las carpetas `backend/` y `frontend/` y vuelve a ejecutar:
```bash
bash scripts/prepare_from_starters.sh
```
