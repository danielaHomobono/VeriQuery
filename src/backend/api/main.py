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
        db_connector.connect()
        logger.info("✅ Database connector initialized")
        
        # 5. Initialize MultiDatabaseConnector
        multi_db_connector = MultiDatabaseConnector()
        logger.info("✅ MultiDatabaseConnector initialized")
        
        # 6. Initialize AmbiguityDetector
        ambiguity_detector = AmbiguityDetector()
        logger.info("✅ AmbiguityDetector initialized")
        
        # 7. Create QueryService (inyectar dependencias)
        app.state.query_service = QueryService(
            prompt_shield=shield,
            nl2sql_generator=nl2sql_gen,
            db_connector=db_connector
        )
        logger.info("✅ QueryService initialized")
        
        # 8. Create AmbiguityService
        app.state.ambiguity_service = AmbiguityService(
            ambiguity_detector=ambiguity_detector
        )
        logger.info("✅ AmbiguityService initialized")
        
        # 9. Create DatabaseManagementService
        app.state.database_management_service = DatabaseManagementService(
            multi_db_connector=multi_db_connector
        )
        logger.info("✅ DatabaseManagementService initialized")
        
        # 10. Create SchemaService
        app.state.schema_service = SchemaService(
            multi_db_connector=multi_db_connector
        )
        logger.info("✅ SchemaService initialized")
        
        # 11. Create SessionService
        app.state.session_service = SessionService()
        logger.info("✅ SessionService initialized")
        
        logger.info("=" * 70)
        logger.info("🚀 VeriQuery API ready - All services initialized")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # ── SHUTDOWN ───────────────────────────────────────────────────────────
    logger.info("Shutting down VeriQuery API...")
    try:
        db_connector.disconnect()
        logger.info("✅ Database disconnected")
    except Exception as e:
        logger.warning(f"⚠️ Error during shutdown: {e}")


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
    allow_origins=["*"],  # ⚠️ En producción: restringir
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

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "success": False,
        "error": "Internal server error",
        "detail": str(exc)[:200]
    }


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