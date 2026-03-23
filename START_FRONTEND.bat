@echo off
REM Frontend Startup Script
REM Levanta Vite en puerto 5173

cd /d "%~dp0"

echo.
echo ========================================
echo 🎨 Iniciando Frontend (Vite + React)
echo ========================================
echo.
echo Puerto: 5173
echo URL: http://localhost:5173
echo.

cd frontend

REM Instalar dependencias si no existen
if not exist node_modules (
    echo Instalando dependencias npm...
    call npm install
)

REM Iniciar Vite dev server
call npm run dev

pause
