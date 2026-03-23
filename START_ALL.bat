@echo off
REM ========================================
REM VeriQuery - Full Stack Startup
REM ========================================
REM Levanta Backend + Frontend en paralelo

cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════╗
echo ║     🚀 VeriQuery Full Stack Startup    ║
echo ╚════════════════════════════════════════╝
echo.
echo Este script lanzará:
echo   ✅ Backend (FastAPI) → http://localhost:8000
echo   ✅ Frontend (Vite)   → http://localhost:5173
echo.
echo NOTA: Se abrirán DOS ventanas nuevas.
echo Cierra CUALQUIERA de ellas para detener el sistema.
echo.
pause

REM Activar venv
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Abrir Backend en nueva ventana
echo Lanzando Backend...
start "VeriQuery Backend - FastAPI (Port 8000)" cmd /k "python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload"

REM Esperar un segundo para que se estabilice
timeout /t 2 /nobreak

REM Abrir Frontend en nueva ventana
echo Lanzando Frontend...
start "VeriQuery Frontend - Vite (Port 5173)" cmd /k "cd frontend && if not exist node_modules npm install && npm run dev"

echo.
echo ✅ Backend y Frontend lanzados
echo.
echo 📍 URLs:
echo   - Frontend:    http://localhost:5173
echo   - Backend API: http://localhost:8000
echo   - API Docs:    http://localhost:8000/docs
echo   - OpenAPI:     http://localhost:8000/openapi.json
echo.
echo 💡 Tips:
echo   - Las consolas se cerrará cuando termines
echo   - Los cambios se recargan automáticamente (hot reload)
echo   - Revisa los logs en cada consola para errores
echo.
pause
