# 🚀 VeriQuery - Guía de Startup (Sin Docker)

## ✅ Pre-requisitos

### Backend (Python)
- [x] Python 3.10+ instalado
- [x] `.venv/` virtualenv creado (NO duplicados - solo `.venv/`)
- [x] Dependencias instaladas: `pip install -r requirements.txt`

### Frontend (Node.js)
- [x] Node.js 18+ instalado
- [x] npm (incluido con Node)
- [x] `frontend/node_modules/` (se instala automáticamente al iniciar)

### Variables de Entorno
- [x] `.env` en raíz del proyecto con:
  ```
  AZURE_OPENAI_API_KEY=tu_key
  AZURE_OPENAI_ENDPOINT=tu_endpoint
  AZURE_OPENAI_MODEL=gpt-4-deployment-name
  ```

---

## 🎯 Opción 1: MODO FÁCIL - Script Todo en Uno

### Windows (cmd.exe o PowerShell)
```bash
# Abre una sola ventana que lanza todo
START_ALL.bat
```

**Qué hace:**
1. ✅ Activa `.venv/`
2. ✅ Lanza Backend en ventana nueva (puerto 8000)
3. ✅ Lanza Frontend en ventana nueva (puerto 5173)
4. ✅ Ambas se recargan al editar código (hot reload)

---

## 🎯 Opción 2: MODO MANUAL - Dos Ventanas Separadas

### Ventana 1: Backend
```bash
# En PowerShell / cmd.exe desde raíz del proyecto
.venv\Scripts\activate
python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Ventana 2: Frontend
```bash
# En PowerShell / cmd.exe desde raíz del proyecto
cd frontend
npm install  # (primera vez solo)
npm run dev
```

**Esperado:**
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

## 📍 URLs Después del Startup

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:5173 | App React con Vite |
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **Swagger UI** | http://localhost:8000/docs | Documentación interactiva |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | Schema OpenAPI |
| **Health Check** | http://localhost:8000/api/health | Verificar backend activo |

---

## 🔗 Flujo de Comunicación

```
Frontend (localhost:5173)
    ↓ HTTP requests
    ↓ CORS enabled (CORSMiddleware)
Backend API (localhost:8000)
    ↓ Delega a Services
Services Layer (QueryService, AmbiguityService, etc.)
    ↓ Accede a DB
Database (SQL Server / SQLite)
```

---

## 🛠️ Troubleshooting

### Backend no inicia
```bash
# Verificar Python
python --version  # Debe ser 3.10+

# Verificar venv activado
.venv\Scripts\activate

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall

# Verificar puerto 8000 libre
netstat -ano | findstr :8000
```

### Frontend no inicia
```bash
# Verificar Node.js
node --version  # Debe ser 18+
npm --version

# Limpiar e reinstalar
rm -r frontend\node_modules
rm frontend\package-lock.json
npm install

# Verificar puerto 5173 libre
netstat -ano | findstr :5173
```

### CORS Error (Frontend no puede conectar a Backend)
**✅ Está resuelto** - main.py tiene CORSMiddleware configurado
```python
allow_origins=["*"]  # Permite cualquier origen
```

### Error: "Address already in use"
```bash
# Encontrar proceso en puerto 8000
netstat -ano | findstr :8000

# Matar proceso
taskkill /PID <PID> /F
```

---

## 🧪 Test Rápido

### Verificar Backend activo
```bash
curl http://localhost:8000/api/health

# Respuesta esperada:
# {"status":"healthy","timestamp":"2025-03-22T..."}
```

### Ver documentación de API
Abre: http://localhost:8000/docs
- Verás todos los endpoints
- Puedes probarlos directamente desde Swagger UI

---

## ⚡ Hot Reload

### Backend
Cambios en `src/backend/**/*.py` se recargan automáticamente
- No necesita reiniciar
- Uvicorn monitorea cambios

### Frontend
Cambios en `frontend/src/**/*.{jsx,js,css}` se recargan automáticamente
- No necesita reiniciar
- Vite HMR (Hot Module Replacement)

---

## 🚫 Notas Importantes

❌ **NO necesitas Docker** - Esto es desarrollo local
✅ Frontend se conecta a Backend vía `http://localhost:8000`
✅ Base de datos local o remota (configurada en .env)
✅ Azure Key Vault (opcional, si está configurado)

---

## 📊 Arquitectura Actual (Post-Refactorización)

```
📦 Frontend (React + Vite)
   └─ Puerto 5173
      └─ fetch → Backend

📦 Backend (FastAPI)
   └─ Puerto 8000
      ├─ routers/ (thin HTTP layer, 520 líneas)
      ├─ services/ (business logic, 1000+ líneas)
      └─ database/ (data access)

✅ SIN Docker necesario para desarrollo
✅ SIN dependencias complejas
✅ SIN duplicación de venv
```

---

## 🎯 Próximos Pasos

1. ✅ **Inicia Backend + Frontend** → Usa START_ALL.bat
2. ✅ **Abre Frontend** → http://localhost:5173
3. ✅ **Prueba endpoints** → http://localhost:8000/docs
4. ✅ **Revisa logs** en ambas consolas
5. ✅ **Edita código** → Hot reload automático

---

**¡Listo para desarrollar!** 🚀
