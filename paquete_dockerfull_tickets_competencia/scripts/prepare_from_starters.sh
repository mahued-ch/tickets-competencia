#!/usr/bin/env bash
set -euo pipefail

BACKEND_ZIP="starter_tecnico_tickets_competencia.zip"
FRONTEND_ZIP="starter_frontend_tickets_competencia.zip"

if [ ! -f "$BACKEND_ZIP" ]; then
  echo "No se encontro $BACKEND_ZIP"
  exit 1
fi

if [ ! -f "$FRONTEND_ZIP" ]; then
  echo "No se encontro $FRONTEND_ZIP"
  exit 1
fi

rm -rf backend frontend __tmp_backend __tmp_frontend
mkdir -p __tmp_backend __tmp_frontend

unzip -q "$BACKEND_ZIP" -d __tmp_backend
unzip -q "$FRONTEND_ZIP" -d __tmp_frontend

# El backend starter se descomprime como starter_tecnico_tickets_competencia/
# y adentro contiene backend/
cp -R __tmp_backend/starter_tecnico_tickets_competencia/backend ./backend

# El frontend starter se descomprime como starter_frontend_tickets_competencia/
cp -R __tmp_frontend/starter_frontend_tickets_competencia ./frontend

# Sobrescribir archivos dockerfull
cp docker/backend.Dockerfile backend/Dockerfile
mkdir -p backend/scripts
cp scripts/backend_entrypoint.sh backend/scripts/entrypoint.sh
cp scripts/wait_for_db.py backend/scripts/wait_for_db.py
cp docker/backend.dockerignore backend/.dockerignore

cp docker/frontend.Dockerfile frontend/Dockerfile
mkdir -p frontend/nginx
cp docker/frontend.default.conf frontend/nginx/default.conf
cp docker/frontend.dockerignore frontend/.dockerignore
cp docker/frontend.env.example frontend/.env.example

chmod +x backend/scripts/entrypoint.sh || true

echo "Estructura preparada correctamente."
echo "Siguiente paso: cp .env.example .env && docker compose up --build"

rm -rf __tmp_backend __tmp_frontend
