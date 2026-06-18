@echo off
echo Deteniendo servicios...
taskkill /f /im python.exe /t 2>nul
taskkill /f /im node.exe /t 2>nul
echo Listo.
pause
