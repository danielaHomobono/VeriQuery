"""
FORENSIC DATA GUARDIAN - API REST
==================================
Enterprise-grade API with:
- Security validation (PromptShield)
- NL-to-SQL generation
- Database execution (agnóstic connector)
- Comprehensive error handling
- Audit logging

Architecture:
    Request → PromptShield → NL2SQL → Database → Response
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
tools_path = str(Path(__file__).parent.parent.parent.parent / "tools")
sys.path.insert(0, tools_path)

# Load environment variables
load_dotenv()

# Import components
from security.prompt_shields import PromptShield, ThreatLevel
from nl2sql_generator import NL2SQLGenerator
from config.azure_ai import AzureAIConfig
from schemas import QueryRequest, QueryResponse
from database import (
    get_database_connector,
    validate_database_connection,
    get_connector_info,
    DatabaseConnector,
)

# Import routers
from .database_management_router import router as db_router
from .schema_scanner_router import router as schema_router
from .ambiguity_router import router as ambiguity_router

# ============================================================================
# GLOBAL STATE
# ============================================================================

class AppState:
    """Application state container."""
    
    def __init__(self):
        self.shield: Optional[PromptShield] = None
        self.azure_config: Optional[AzureAIConfig] = None
        self.nl2sql_gen: Optional[NL2SQLGenerator] = None
        self.db_connector: Optional[DatabaseConnector] = None
        self.db_healthy = False
    
    def is_ready(self) -> bool:
        """Check if app is ready to serve requests."""
        return all([
            self.shield,
            self.azure_config,
            self.nl2sql_gen,
            self.db_healthy
        ])


# Initialize state
app_state = AppState()

# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    - Startup: Initialize all components
    - Shutdown: Cleanup and close connections
    """
    
    logger.info("=" * 70)
    logger.info("FORENSIC DATA GUARDIAN - STARTING UP")
    logger.info("=" * 70)
    
    try:
        # ========== STARTUP ==========
        
        # 1. Initialize PromptShield
        app_state.shield = PromptShield()
        logger.info("✅ PromptShield initialized successfully")
        
        # 2. Initialize Azure AI Config
        app_state.azure_config = AzureAIConfig()
        logger.info("✅ AzureAIConfig initialized successfully")
        
        # 3. Initialize NL2SQL Generator
        app_state.nl2sql_gen = NL2SQLGenerator()
        logger.info("✅ NL2SQLGenerator initialized successfully")
        
        # 4. Initialize Database Connector
        app_state.db_connector = get_database_connector()
        logger.info(f"✅ Database connector created: {app_state.db_connector}")
        
        if app_state.db_connector.connect():
            app_state.db_healthy = True
            is_healthy, message = app_state.db_connector.health_check()
            logger.info(f"✅ Database health check: {message}")
        else:
            logger.warning("⚠️  Database connector created but connection failed")
            app_state.db_healthy = False
        
        # 5. Log startup summary
        logger.info("=" * 70)
        logger.info("STARTUP COMPLETE")
        logger.info(f"  PromptShield: {'✅' if app_state.shield else '❌'}")
        logger.info(f"  AzureAIConfig: {'✅' if app_state.azure_config else '❌'}")
        logger.info(f"  NL2SQLGenerator: {'✅' if app_state.nl2sql_gen else '❌'}")
        logger.info(f"  Database: {'✅' if app_state.db_healthy else '⚠️ Degraded'}")
        logger.info("=" * 70)
        
    except Exception as startup_error:
        logger.error(f"❌ STARTUP FAILED: {startup_error}", exc_info=True)
        raise
    
    yield  # Application is running
    
    # ========== SHUTDOWN ==========
    
    logger.info("=" * 70)
    logger.info("FORENSIC DATA GUARDIAN - SHUTTING DOWN")
    logger.info("=" * 70)
    
    try:
        if app_state.db_connector and app_state.db_connector.is_connected:
            app_state.db_connector.disconnect()
            logger.info("✅ Database connection closed")
    except Exception as shutdown_error:
        logger.error(f"Error during shutdown: {shutdown_error}", exc_info=True)
    
    logger.info("✅ Shutdown complete")
    logger.info("=" * 70)


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="Forensic Data Guardian API",
    description="Enterprise API for forensic data queries with NL-to-SQL translation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(db_router)
app.include_router(schema_router)
app.include_router(ambiguity_router)

# ============================================================================
# REQUEST/RESPONSE MODELS (Otros modelos no incluídos en schemas)
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall status: ok, degraded, or error")
    timestamp: str = Field(...)
    database: Dict[str, Any] = Field(...)
    security: str = Field(...)
    ai: str = Field(...)
    message: Optional[str] = Field(default=None)



class ExamplesResponse(BaseModel):
    """Example queries response."""
    examples: List[str] = Field(...)
    count: int = Field(...)


# ============================================================================
# ERROR HANDLING MIDDLEWARE
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions gracefully."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path
            }
        }
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Get API information."""
    return {
        "name": "Forensic Data Guardian API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /api/query": "Process natural language query",
            "GET /api/health": "Health check all services",
            "GET /api/examples": "Get example queries",
            "GET /docs": "Interactive documentation (Swagger)",
            "GET /redoc": "Alternative documentation (ReDoc)",
        },
        "database_config": get_connector_info()
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns status of all critical components:
    - Database connectivity
    - Azure OpenAI availability
    - Security module status
    """
    
    # Check Database
    db_info = {
        "connected": False,
        "healthy": False,
        "message": "Not initialized"
    }
    
    if app_state.db_connector:
        try:
            is_healthy, health_msg = app_state.db_connector.health_check()
            db_info = {
                "connected": app_state.db_connector.is_connected,
                "healthy": is_healthy,
                "message": health_msg
            }
        except Exception as e:
            db_info["message"] = f"Health check failed: {str(e)[:100]}"
    
    # Check Azure OpenAI
    ai_status = "✅ Ready" if app_state.azure_config else "❌ Not initialized"
    
    # Check Security
    security_status = "✅ Ready" if app_state.shield else "❌ Not initialized"
    
    # Determine overall status
    all_healthy = (
        db_info["healthy"] and
        app_state.azure_config is not None and
        app_state.shield is not None
    )
    
    status_label = "ok" if all_healthy else ("degraded" if db_info["connected"] else "error")
    
    return HealthResponse(
        status=status_label,
        timestamp=datetime.now().isoformat(),
        database=db_info,
        security=security_status,
        ai=ai_status,
        message="All systems operational" if all_healthy else "Some systems degraded or unavailable"
    )


@app.get("/api/schema", tags=["Schema"])
async def get_database_schema():
    """Get the actual database schema - all tables and columns."""
    try:
        if not app_state.db_connector:
            return {"error": "Database not connected"}
        
        # Query for all tables
        tables_query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        
        result = app_state.db_connector.execute_query(tables_query)
        if not result.success:
            return {"error": f"Failed to query tables: {result.error}"}
        
        schema = {}
        if result.rows:
            for (table_name,) in result.rows:
                # Get columns for each table
                cols_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                cols_result = app_state.db_connector.execute_query(cols_query)
                columns = []
                if cols_result.success and cols_result.rows:
                    columns = [{"name": col_name, "type": col_type} for col_name, col_type in cols_result.rows]
                
                schema[table_name] = {"columns": columns}
        
        return {"tables": schema, "table_count": len(schema)}
    
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return {"error": str(e)}


@app.post("/api/query", response_model=QueryResponse, tags=["Query"])
async def process_query(request: QueryRequest) -> QueryResponse:
    """
    Process natural language query.
    
    Orchestrates the complete flow:
    1. Security validation (PromptShield)
    2. SQL generation (NL2SQLGenerator)
    3. Query execution (Database)
    4. Result formatting
    
    Returns:
        QueryResponse: Result with data or error details
    """
    
    start_time = datetime.now()
    query_id = f"{start_time.timestamp()}_{hash(request.question) % 10000}"
    
    logger.info(f"[{query_id}] Query received: {request.question}")
    
    try:
        # =====================================================================
        # STEP 1: VALIDATE INPUT WITH PROMPT SHIELD
        # =====================================================================
        
        if not app_state.shield:
            logger.error("PromptShield not available")
            return QueryResponse(
                success=False,
                answer="Security module not available",
                error="PromptShield not initialized",
                metadata={"execution_time_ms": _get_elapsed_ms(start_time)}
            )
        
        logger.debug(f"[{query_id}] Validating input with PromptShield")
        validation_result = app_state.shield.validate_user_input(
            request.question
        )
        
        if not validation_result.is_safe:
            logger.warning(
                f"[{query_id}] Query blocked by security: {validation_result.threat_level.value}"
            )
            return QueryResponse(
                success=False,
                answer=f"Query blocked for security reasons ({validation_result.threat_level.value})",
                error=f"Threat type: {validation_result.threat_type.value if validation_result.threat_type else 'Unknown'}",
                metadata={
                    "threat_level": validation_result.threat_level.value,
                    "threat_type": validation_result.threat_type.value if validation_result.threat_type else None,
                    "message": validation_result.message,
                    "execution_time_ms": _get_elapsed_ms(start_time),
                    "query_id": query_id
                }
            )
        
        logger.info(f"[{query_id}] Input validated: threat_level={validation_result.threat_level.value}")
        
        # =====================================================================
        # STEP 2: GENERATE SQL WITH NL2SQL GENERATOR
        # =====================================================================
        
        if not app_state.nl2sql_gen:
            logger.error("NL2SQLGenerator not available")
            return QueryResponse(
                success=False,
                answer="SQL generation module not available",
                error="NL2SQLGenerator not initialized",
                metadata={"execution_time_ms": _get_elapsed_ms(start_time)}
            )
        
        logger.debug(f"[{query_id}] Generating SQL from natural language")
        sql_result = app_state.nl2sql_gen.generate_sql(request.question)
        
        if "error" in sql_result or not sql_result.get("sql"):
            logger.error(f"[{query_id}] SQL generation failed: {sql_result.get('error')}")
            return QueryResponse(
                success=False,
                answer="Could not generate valid SQL query",
                error=sql_result.get("error", "Unknown error"),
                metadata={
                    "execution_time_ms": _get_elapsed_ms(start_time),
                    "query_id": query_id
                }
            )
        
        generated_sql = sql_result.get("sql")
        logger.info(f"[{query_id}] SQL generated successfully")
        logger.debug(f"[{query_id}] SQL:\n{generated_sql}")
        
        # Clean SQL (remove comments, etc.)
        generated_sql = _clean_sql(generated_sql)
        logger.debug(f"[{query_id}] Cleaned SQL:\n{generated_sql}")
        
        # Convert to SQL Server syntax if needed
        generated_sql = _convert_sql_to_sqlserver(generated_sql)
        logger.debug(f"[{query_id}] SQL Server compatible SQL:\n{generated_sql}")
        
        # =====================================================================
        # STEP 3: VALIDATE GENERATED SQL FOR SECURITY
        # =====================================================================
        
        logger.debug(f"[{query_id}] Validating generated SQL")
        logger.info(f"[{query_id}] Generated SQL:\n{generated_sql}")  # Log full SQL for debugging
        sql_validation = app_state.shield.validate_generated_sql(generated_sql)
        
        if not sql_validation.is_safe:
            logger.error(f"[{query_id}] Generated SQL failed security check")
            return QueryResponse(
                success=False,
                answer="Generated SQL did not pass security validation",
                sql=generated_sql,
                error=f"SQL validation failed: {sql_validation.message}",
                metadata={
                    "sql_threat_type": sql_validation.threat_type.value if sql_validation.threat_type else None,
                    "sql_threat_level": sql_validation.threat_level.value,
                    "execution_time_ms": _get_elapsed_ms(start_time),
                    "query_id": query_id
                }
            )
        
        logger.info(f"[{query_id}] SQL validated: safe to execute")
        
        # =====================================================================
        # STEP 4: EXECUTE SQL AGAINST DATABASE
        # =====================================================================
        
        if not app_state.db_healthy or not app_state.db_connector:
            logger.warning(f"[{query_id}] Database not available")
            return QueryResponse(
                success=False,
                answer="Database is not available",
                sql=generated_sql,
                error="Database connection lost",
                metadata={
                    "execution_time_ms": _get_elapsed_ms(start_time),
                    "query_id": query_id
                }
            )
        
        logger.debug(f"[{query_id}] Executing SQL against database")
        query_exec_time = datetime.now()
        
        db_result = app_state.db_connector.execute_query(generated_sql)
        
        if not db_result.success:
            # DEPRECATED: Fallback logic removed in v2.0
            # Reason: New multi-BD architecture loads real schema, no TABLE_ALIASES needed
            # If query fails, it's a real database error that needs to be reported
            logger.error(f"[{query_id}] Database query execution failed: {db_result.error}")
            exec_time_ms = (datetime.now() - query_exec_time).total_seconds() * 1000
            total_time_ms = _get_elapsed_ms(start_time)
            
            return QueryResponse(
                success=False,
                answer=None,
                sql=generated_sql,
                explanation=f"Query execution failed: {db_result.error}",
                data=[],
                row_count=0,
                confidence=0.0,
                metadata={
                    "execution_time_ms": round(total_time_ms, 2),
                    "db_execution_time_ms": round(exec_time_ms, 2),
                    "error": db_result.error,
                    "threat_level": validation_result.threat_level.value,
                    "user_id": request.user_id,
                    "organization_id": request.organization_id,
                    "timestamp": datetime.now().isoformat(),
                    "query_id": query_id
                }
            )
            
            logger.error(f"[{query_id}] Query execution failed: {db_result.error}")
            logger.error(f"[{query_id}] Error type: {db_result.error_type}")
            logger.error(f"[{query_id}] SQL executed: {generated_sql}")
            return QueryResponse(
                success=False,
                answer="Error executing query",
                sql=generated_sql,
                error=db_result.error,
                metadata={
                    "db_error_type": db_result.error_type,
                    "execution_time_ms": _get_elapsed_ms(start_time),
                    "query_id": query_id
                }
            )
        
        exec_time_ms = (datetime.now() - query_exec_time).total_seconds() * 1000
        logger.info(
            f"[{query_id}] Query executed: "
            f"{db_result.row_count} rows in {exec_time_ms:.2f}ms"
        )
        
        # =====================================================================
        # STEP 5: FORMAT RESPONSE
        # =====================================================================
        
        # Generate natural language answer from data
        answer = _format_natural_language_answer(request.question, db_result.data)
        
        total_time_ms = _get_elapsed_ms(start_time)
        logger.info(
            f"[{query_id}] Query complete: "
            f"{db_result.row_count} rows, {total_time_ms:.2f}ms total"
        )
        
        return QueryResponse(
            success=True,
            answer=answer,
            sql=generated_sql,
            explanation=sql_result.get("explanation", "Query executed successfully"),
            data=db_result.data,
            row_count=db_result.row_count,
            confidence=95.0,  # TODO: Calculate based on result certainty
            metadata={
                "execution_time_ms": round(total_time_ms, 2),
                "db_execution_time_ms": round(exec_time_ms, 2),
                "threat_level": validation_result.threat_level.value,
                "user_id": request.user_id,
                "organization_id": request.organization_id,
                "timestamp": datetime.now().isoformat(),
                "query_id": query_id
            }
        )
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    
    except Exception as e:
        logger.error(f"[{query_id}] Unexpected error: {e}", exc_info=True)
        return QueryResponse(
            success=False,
            answer="Unexpected error processing query",
            error=str(e)[:200],
            metadata={
                "execution_time_ms": _get_elapsed_ms(start_time),
                "query_id": query_id
            }
        )


@app.get("/api/examples", response_model=ExamplesResponse, tags=["Examples"])
async def get_examples():
    """
    Get example queries to display in frontend.
    
    Returns:
        ExamplesResponse: List of example queries
    """
    examples = [
        "¿Cuántos clientes tenemos en total?",
        "¿Cuál es el producto más vendido?",
        "¿Cuántas transacciones se realizaron en marzo?",
        "¿Cuál es el total de ventas por región?",
        "¿Cuál es el cliente con mayor compra histórica?",
    ]
    
    return ExamplesResponse(
        examples=examples,
        count=len(examples)
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_elapsed_ms(start_time: datetime) -> float:
    """Calculate elapsed time in milliseconds."""
    return (datetime.now() - start_time).total_seconds() * 1000


def _clean_sql(sql: str) -> str:
    """
    Remove SQL comments and extra whitespace.
    
    Args:
        sql: Raw SQL with potential comments
        
    Returns:
        Clean SQL starting with SELECT
    """
    import re
    
    # Remove line comments (-- ...)
    sql = re.sub(r'--[^\n]*', '', sql)
    # Remove block comments (/* ... */)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    # Remove leading/trailing whitespace
    sql = sql.strip()
    # Remove extra whitespace
    sql = re.sub(r'\s+', ' ', sql)
    
    return sql


def _fix_column_names_with_spaces(sql: str) -> str:
    """
    Fix column references with spaces - wrap them in brackets.
    
    Examples:
    - SUM(s.Net Price) → SUM(s.[Net Price])
    - s.Order Date → s.[Order Date]
    - Already bracketed columns are left alone
    
    Args:
        sql: SQL query
        
    Returns:
        SQL with properly bracketed column names
    """
    import re
    
    # Pattern: table_alias.ColumnName where ColumnName has spaces (not already bracketed)
    # Look ahead to ensure we're at a word boundary
    pattern = r'(\w+\.)([A-Z][A-Za-z\s]+)(?=[\s,);\n]|ORDER|GROUP|WHERE|JOIN|FROM)'
    
    def fix_match(match):
        prefix = match.group(1)  # e.g., "s."
        col_name = match.group(2).rstrip()  # e.g., "Net Price"
        
        # Check if has spaces (multi-word) and isn't already bracketed
        if ' ' in col_name and '[' not in col_name:
            return f"{prefix}[{col_name}]"
        return match.group(0)
    
    sql = re.sub(pattern, fix_match, sql, flags=re.IGNORECASE)
    
    return sql


def _convert_sql_to_sqlserver(sql: str) -> str:
    """
    Convert SQL from PostgreSQL/generic syntax to SQL Server syntax.
    
    Conversions:
    - LIMIT n OFFSET m → OFFSET m ROWS FETCH NEXT n ROWS ONLY
    - LIMIT n → TOP n
    - Remove RETURNING clause
    
    Args:
        sql: SQL query to convert
        
    Returns:
        SQL Server compatible query
    """
    import re
    
    # Note: NOT calling _fix_column_names_with_spaces() as it can damage the SQL
    # Instead, rely on Azure OpenAI to generate correct SQL with brackets
    
    # Convert LIMIT n OFFSET m → OFFSET m ROWS FETCH NEXT n ROWS ONLY
    # Pattern: LIMIT \d+ OFFSET \d+
    sql = re.sub(
        r'LIMIT\s+(\d+)\s+OFFSET\s+(\d+)',
        r'OFFSET \2 ROWS FETCH NEXT \1 ROWS ONLY',
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert LIMIT n (without OFFSET) → TOP n
    # But only if it's at the end of the SELECT clause
    if re.search(r'LIMIT\s+\d+\s*$', sql, re.IGNORECASE):
        # Extract the LIMIT value
        limit_match = re.search(r'LIMIT\s+(\d+)\s*$', sql, re.IGNORECASE)
        if limit_match:
            limit_val = limit_match.group(1)
            # Remove LIMIT clause
            sql = re.sub(r'\s*LIMIT\s+\d+\s*$', '', sql, flags=re.IGNORECASE)
            # Add TOP clause after SELECT
            sql = re.sub(
                r'SELECT\s+',
                f'SELECT TOP {limit_val} ',
                sql,
                count=1,
                flags=re.IGNORECASE
            )
    
    # Remove RETURNING clause (SQL Server doesn't support it in SELECT)
    sql = re.sub(r'\s+RETURNING\s+.*$', '', sql, flags=re.IGNORECASE)
    
    return sql


def _format_natural_language_answer(question: str, data: List[Dict[str, Any]]) -> str:
    """
    Generate natural language answer from query results.
    
    Args:
        question: Original user question
        data: Query result rows
    
    Returns:
        str: Natural language answer
    """
    if not data:
        return "No data found matching your query."
    
    if len(data) == 1:
        row = data[0]
        # Try to find a numeric column for the answer
        for key, value in row.items():
            if isinstance(value, (int, float)):
                return f"The result is {value}"
        
        # If no numeric column, return first value
        first_value = list(row.values())[0]
        return f"The answer is: {first_value}"
    
    # Multiple rows
    return f"Found {len(data)} results matching your query."


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Información de la API"""
    return {
        "name": "Forensic Data Guardian",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/query": "Procesar consulta en lenguaje natural",
            "GET /api/health": "Estado de salud",
            "GET /api/docs": "Documentación interactiva (Swagger)",
        }
    }

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Verificar estado de todos los servicios"""
    
    # Check Database
    db_status = "❌ No disponible"
    try:
        # Aquí irías a conectar a SQL Server y hacer ping
        db_status = "✅ Conectado"
    except:
        db_status = "❌ Error de conexión"
    
    # Check Azure OpenAI
    openai_status = "❌ No disponible"
    try:
        if app_state.azure_config:
            openai_status = "✅ Conectado"
        else:
            openai_status = "❌ No inicializado"
    except:
        openai_status = "❌ Error"
    
    return HealthResponse(
        status="ok" if db_status.startswith("✅") and openai_status.startswith("✅") else "degraded",
        timestamp=datetime.now().isoformat(),
        database=db_status,
        azure_openai=openai_status
    )

@app.get("/api/examples", tags=["Examples"])
async def get_examples():
    """Retorna ejemplos de consultas para mostrar en frontend"""
    return {
        "examples": [
            "¿Cuántos beneficiarios tenemos en total?",
            "¿Qué asistencias se entregaron en marzo?",
            "¿Cuál es el producto más distribuido?",
        ]
    }



