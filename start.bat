@echo off
echo ========================================
echo  Tickets Competencia - Inicio rapido
echo ========================================

echo [1/2] Iniciando backend (puerto 8000)...
start "Backend" cmd /c "cd /d paquete_dockerfull_tickets_competencia\backend && .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

echo [2/2] Iniciando frontend (puerto 5173)...
start "Frontend" cmd /c "cd /d paquete_dockerfull_tickets_competencia\frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo  Frontend: http://localhost:5173/login
echo  Backend:  http://localhost:8000/docs
echo ========================================
echo.
pause
