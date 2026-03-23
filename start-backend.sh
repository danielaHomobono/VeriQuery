#!/bin/bash
# Backend startup script para Linux/Mac

cd "$(dirname "$0")"

echo ""
echo "========================================" 
echo "🚀 Iniciando Backend (FastAPI)"
echo "========================================"
echo ""
echo "Puerto: 8000"
echo "URL: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""

# Activar venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Iniciar uvicorn
python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload
