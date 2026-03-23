@echo off
REM Backend Startup Script
REM Levanta FastAPI en puerto 8000

cd /d "%~dp0"

echo.
echo ========================================
echo 🚀 Iniciando Backend (FastAPI)
echo ========================================
echo.
echo Puerto: 8000
echo URL: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo.

REM Activar venv si existe
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Iniciar uvicorn con reload
python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload

pause
