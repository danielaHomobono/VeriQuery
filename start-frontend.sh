#!/bin/bash
# Frontend startup script para Linux/Mac

cd "$(dirname "$0")"

echo ""
echo "========================================"
echo "🎨 Iniciando Frontend (Vite + React)"
echo "========================================"
echo ""
echo "Puerto: 5173"
echo "URL: http://localhost:5173"
echo ""

cd frontend

# Instalar si no existe
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias npm..."
    npm install
fi

# Iniciar Vite
npm run dev
