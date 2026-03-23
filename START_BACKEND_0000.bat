@echo off
REM Backend Startup Script - Escucha en todas las interfaces
REM Para que el frontend pueda conectar desde localhost y 127.0.0.1

cd /d "%~dp0"

echo.
echo ========================================
echo 🚀 Iniciando Backend (FastAPI)
echo ========================================
echo.
echo Puerto: 8000
echo URL: http://localhost:8000
echo URL: http://127.0.0.1:8000
echo Docs: http://localhost:8000/docs
echo Health: http://localhost:8000/api/health
echo.

REM Activar venv si existe
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Iniciar uvicorn escuchando en TODAS las interfaces (0.0.0.0)
REM Esto permite que el frontend en localhost se conecte
echo Escuchando en 0.0.0.0:8000 (todas las interfaces)
echo.
python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload

pause
