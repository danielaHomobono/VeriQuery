"""
Schema Scanner API Router
Endpoints for scanning and retrieving database schemas
Delegates business logic to SchemaService
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schema", tags=["schema"])


# Request/Response Models
class SchemaScanRequest(BaseModel):
    database_name: Optional[str] = None


class SchemaResponse(BaseModel):
    schema_data: Dict
    database_name: Optional[str] = None
    error: Optional[str] = None


class SchemaExportRequest(BaseModel):
    database_name: Optional[str] = None
    format: str = "json"  # "json", "sql", or "csv"


class SchemaExportResponse(BaseModel):
    content: str
    format: str
    database_name: Optional[str] = None
    error: Optional[str] = None


# Endpoints

@router.post("/scan", response_model=SchemaResponse)
async def scan_schema(request_body: SchemaScanRequest, request: Request):
    """
    Scan database schema
    Business logic delegated to SchemaService
    """
    try:
        schema_service = request.app.state.schema_service
        
        schema_data = schema_service.scan_schema(request_body.database_name)
        
        if not schema_data:
            raise HTTPException(status_code=400, detail="Failed to scan schema")
        
        return SchemaResponse(
            schema_data=schema_data,
            database_name=request_body.database_name,
            error=None,
        )
    except Exception as e:
        logger.error(f"❌ Error scanning schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Schema scan error: {str(e)}")


@router.get("", response_model=SchemaResponse)
async def get_cached_schema(request: Request):
    """
    Get currently cached schema from active database
    """
    try:
        schema_service = request.app.state.schema_service
        session_service = request.app.state.session_service
        
        # Get active database from session
        active_db = session_service.get_selected_database()
        if not active_db:
            raise HTTPException(status_code=400, detail="No active database set")
        
        schema_data = schema_service.get_cached_schema(active_db)
        
        if not schema_data:
            raise HTTPException(status_code=400, detail="No cached schema available")
        
        return SchemaResponse(
            schema_data=schema_data,
            database_name=active_db,
            error=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting cached schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/export", response_model=SchemaExportResponse)
async def export_schema(request_body: SchemaExportRequest, request: Request):
    """
    Export database schema in specified format (json, sql, csv)
    Business logic delegated to SchemaService
    """
    try:
        schema_service = request.app.state.schema_service
        
        # Validate format
        if request_body.format.lower() not in ["json", "sql", "csv"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request_body.format}")
        
        content = schema_service.export_schema(
            database_name=request_body.database_name,
            format=request_body.format.lower()
        )
        
        if not content:
            raise HTTPException(status_code=400, detail="Failed to export schema")
        
        return SchemaExportResponse(
            content=content,
            format=request_body.format.lower(),
            database_name=request_body.database_name,
            error=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error exporting schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
