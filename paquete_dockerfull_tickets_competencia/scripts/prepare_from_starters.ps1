$ErrorActionPreference = "Stop"

$BackendZip = "starter_tecnico_tickets_competencia.zip"
$FrontendZip = "starter_frontend_tickets_competencia.zip"

if (-not (Test-Path $BackendZip)) {
    Write-Host "No se encontro $BackendZip"
    exit 1
}

if (-not (Test-Path $FrontendZip)) {
    Write-Host "No se encontro $FrontendZip"
    exit 1
}

if (Test-Path "backend") { Remove-Item -Recurse -Force "backend" }
if (Test-Path "frontend") { Remove-Item -Recurse -Force "frontend" }
if (Test-Path "__tmp_backend") { Remove-Item -Recurse -Force "__tmp_backend" }
if (Test-Path "__tmp_frontend") { Remove-Item -Recurse -Force "__tmp_frontend" }

New-Item -ItemType Directory -Path "__tmp_backend" -Force | Out-Null
New-Item -ItemType Directory -Path "__tmp_frontend" -Force | Out-Null

Expand-Archive -Path $BackendZip -DestinationPath "__tmp_backend" -Force
Expand-Archive -Path $FrontendZip -DestinationPath "__tmp_frontend" -Force

Copy-Item -Recurse "__tmp_backend/starter_tecnico_tickets_competencia/backend" -Destination "./backend"
Copy-Item -Recurse "__tmp_frontend/starter_frontend_tickets_competencia" -Destination "./frontend"

# Sobrescribir archivos dockerfull
Copy-Item "docker/backend.Dockerfile" -Destination "backend/Dockerfile"
New-Item -ItemType Directory -Path "backend/scripts" -Force | Out-Null
Copy-Item "scripts/backend_entrypoint.sh" -Destination "backend/scripts/entrypoint.sh"
Copy-Item "scripts/wait_for_db.py" -Destination "backend/scripts/wait_for_db.py"
Copy-Item "docker/backend.dockerignore" -Destination "backend/.dockerignore"

Copy-Item "docker/frontend.Dockerfile" -Destination "frontend/Dockerfile"
New-Item -ItemType Directory -Path "frontend/nginx" -Force | Out-Null
Copy-Item "docker/frontend.default.conf" -Destination "frontend/nginx/default.conf"
Copy-Item "docker/frontend.dockerignore" -Destination "frontend/.dockerignore"
Copy-Item "docker/frontend.env.example" -Destination "frontend/.env.example"

Write-Host "Estructura preparada correctamente."
Write-Host "Siguiente paso: Copy-Item .env.example .env && docker compose up --build"

Remove-Item -Recurse -Force "__tmp_backend"
Remove-Item -Recurse -Force "__tmp_frontend"
