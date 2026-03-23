"""
VeriQuery - FastAPI Main Application
====================================
Punto de entrada de la API REST
Responsabilidades SOLO:
- Startup/Shutdown
- Router registration
- CORS configuration
- Health checks
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Configure paths
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import components
from security.prompt_shields import PromptShield, ThreatLevel
from nl2sql_generator import NL2SQLGenerator
from config.azure_ai import AzureAIConfig
from database import get_database_connector
from schemas import QueryResponse
from services import (
    QueryService,
    AmbiguityService,
    DatabaseManagementService,
    SchemaService,
    SessionService
)
from agents.ambiguity_detector import AmbiguityDetector
from database.multi_db_connector import MultiDatabaseConnector
from api.routers import query_router
from api.database_management_router import router as db_router
from api.schema_scanner_router import router as schema_router
from api.ambiguity_router import router as ambiguity_router


# ============================================================================
# APPLICATION STATE
# ============================================================================

class AppState:
    """Container for shared application components."""
    query_service: QueryService = None


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    
    db_connector = None
    
    # ── STARTUP ────────────────────────────────────────────────────────────
    try:
        logger.info("Starting VeriQuery API...")
        
        # 1. Initialize PromptShield
        shield = PromptShield()
        logger.info("✅ PromptShield initialized")
        
        # 2. Initialize Azure OpenAI Config
        azure_config = AzureAIConfig()
        logger.info("✅ Azure OpenAI configured")
        
        # 3. Initialize NL2SQLGenerator
        nl2sql_gen = NL2SQLGenerator()
        logger.info("✅ NL2SQLGenerator initialized")
        
        # 4. Initialize Database connector
        db_connector = get_database_connector()
        try:
            db_connector.connect()
            logger.info("✅ Database connector initialized")
        except Exception as e:
            logger.warning(f"⚠️  Database connection failed (non-fatal): {e}")
            logger.info("ℹ️  API will run but database operations will fail until connection is restored")
        
        # 5. Initialize MultiDatabaseConnector
        multi_db_connector = MultiDatabaseConnector()
        logger.info("✅ MultiDatabaseConnector initialized")
        
        # 6. Initialize AmbiguityDetector
        ambiguity_detector = AmbiguityDetector()
        logger.info("✅ AmbiguityDetector initialized")
        
        # 7. Create SchemaService FIRST (needed for QueryService)
        app.state.schema_service = SchemaService(
            multi_connector=multi_db_connector
        )
        logger.info("✅ SchemaService initialized")
        
        # 8. Create QueryService (inyectar MultiDatabaseConnector para soportar múltiples BDs)
        app.state.query_service = QueryService(
            prompt_shield=shield,
            nl2sql_generator=nl2sql_gen,
            multi_db_connector=multi_db_connector,
            schema_service=app.state.schema_service
        )
        logger.info("✅ QueryService initialized")
        
        # 9. Create AmbiguityService
        app.state.ambiguity_service = AmbiguityService(
            ambiguity_detector=ambiguity_detector
        )
        logger.info("✅ AmbiguityService initialized")
        
        # 10. Create DatabaseManagementService
        app.state.database_management_service = DatabaseManagementService(
            multi_connector=multi_db_connector
        )
        logger.info("✅ DatabaseManagementService initialized")
        
        # 11. Create SessionService
        app.state.session_service = SessionService()
        logger.info("✅ SessionService initialized")
        
        logger.info("=" * 70)
        logger.info("🚀 VeriQuery API ready - All services initialized")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise
    
    # Yield control - application is now running
    logger.info("📢 Yielding control to application...")
    yield
    logger.info("📢 Received shutdown signal")
    
    # ── SHUTDOWN ───────────────────────────────────────────────────────────
    logger.info("Shutting down VeriQuery API...")
    if db_connector:
        try:
            db_connector.disconnect()
            logger.info("✅ Database disconnected")
        except Exception as e:
            logger.warning(f"⚠️ Error during shutdown: {e}")
    logger.info("📢 Shutdown complete")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="VeriQuery",
    description="NL → SQL con Multi-BD y Security",
    version="2.0.0",
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "*"  # Fallback para desarrollo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROUTERS
# ============================================================================

app.include_router(query_router, prefix="/api")
app.include_router(db_router, prefix="/api")
app.include_router(schema_router, prefix="/api")
app.include_router(ambiguity_router, prefix="/api")

# ============================================================================
# BASIC ENDPOINTS
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint - API info."""
    return {
        "name": "VeriQuery",
        "version": "2.0.0",
        "status": "ready",
        "docs": "/docs"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors."""
    logger.error(f"❌ Validation Error on {request.url}: {exc.errors()}", exc_info=True)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "detail": f"Invalid request body: {exc.errors()}"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)[:200]
        }
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )