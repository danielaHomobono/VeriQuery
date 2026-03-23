"""
Database Management API Router
Endpoints for managing database connections, configurations, and credentials
Delegates business logic to DatabaseManagementService
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/databases", tags=["databases"])


# Request/Response Models
class DatabaseTestRequest(BaseModel):
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    filepath: Optional[str] = None


class DatabaseTestResponse(BaseModel):
    success: bool
    message: str


class DatabaseSaveRequest(BaseModel):
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    filepath: Optional[str] = None


class DatabaseCredentialsResponse(BaseModel):
    success: bool
    message: str
    stored_in_keyvault: bool
    is_readonly: Optional[bool] = None
    readonly_message: Optional[str] = None


class SelectDatabaseRequest(BaseModel):
    user_id: str
    permission_details: Optional[Dict] = None
    warnings: Optional[List[str]] = None


class DatabaseConfig(BaseModel):
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    filepath: Optional[str] = None
    active: bool = False


class DatabaseListResponse(BaseModel):
    databases: List[DatabaseConfig]  # Return full database objects, not just names
    active: Optional[str] = None


class DatabaseDetailsResponse(BaseModel):
    database: DatabaseConfig


class DatabaseActivateResponse(BaseModel):
    success: bool
    message: str


class SelectDatabaseResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


class CredentialSecurityCheckResponse(BaseModel):
    success: bool
    message: str
    is_readonly: bool
    readonly_message: str
    permission_details: Dict
    can_save_securely: bool


class CredentialListResponse(BaseModel):
    credentials: List[str]
    stored_in_keyvault: bool


class CredentialMetadataResponse(BaseModel):
    db_name: str
    db_type: str
    host: Optional[str]
    database: str
    saved_at: Optional[str]
    product: str
    stored_in_keyvault: bool


# Endpoints

@router.post("/test", response_model=DatabaseTestResponse)
async def test_database_connection(request_body: DatabaseTestRequest, request: Request):
    """
    Test connection to a database
    Business logic delegated to DatabaseManagementService
    """
    try:
        db_service = request.app.state.database_management_service
        
        success, message = db_service.test_database_connection(request_body)
        
        return DatabaseTestResponse(success=success, message=message)
    except Exception as e:
        logger.error(f"❌ Error testing database connection: {e}", exc_info=True)
        return DatabaseTestResponse(success=False, message=f"Test failed: {str(e)}")


@router.post("/save", response_model=DatabaseCredentialsResponse)
async def save_database_config(request_body: DatabaseSaveRequest, request: Request):
    """
    Save a database configuration with security validation
    Business logic delegated to DatabaseManagementService
    """
    try:
        logger.info(f"📝 Saving database config: {request_body.dict()}")
        
        db_service = request.app.state.database_management_service
        
        # Service now returns complete dict matching DatabaseCredentialsResponse
        result = db_service.save_database_config(request_body.dict())
        logger.info(f"✅ Database saved successfully: {result}")
        
        return DatabaseCredentialsResponse(**result)
    except Exception as e:
        logger.error(f"❌ Error saving database config: {e}", exc_info=True)
        return DatabaseCredentialsResponse(
            success=False,
            message=f"Save failed: {str(e)}",
            stored_in_keyvault=False
        )


@router.get("", response_model=DatabaseListResponse)
async def list_databases(request: Request):
    """List all saved database configurations"""
    try:
        db_service = request.app.state.database_management_service
        
        databases = db_service.list_databases()
        active = db_service.get_active_database()
        
        return DatabaseListResponse(databases=databases, active=active)
    except Exception as e:
        logger.error(f"❌ Error listing databases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{database_name}", response_model=DatabaseDetailsResponse)
async def get_database_info(database_name: str, request: Request):
    """Get information about a specific database"""
    try:
        db_service = request.app.state.database_management_service
        
        info = db_service.get_database_info(database_name)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        return DatabaseDetailsResponse(database=DatabaseConfig(**info))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting database info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/{database_name}", response_model=Dict)
async def delete_database(database_name: str, request: Request):
    """Delete a database configuration"""
    try:
        db_service = request.app.state.database_management_service
        
        success = db_service.delete_database_config(database_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        return {"success": True, "message": f"Database '{database_name}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{database_name}/activate", response_model=DatabaseActivateResponse)
async def activate_database(database_name: str, request: Request):
    """Set a database as active"""
    try:
        db_service = request.app.state.database_management_service
        session_service = request.app.state.session_service
        
        success = db_service.activate_database(database_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        # Sync with SessionService
        session_service.set_selected_database(database_name)
        
        return DatabaseActivateResponse(
            success=True,
            message=f"Database '{database_name}' is now active"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error activating database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/select/{db_name}", response_model=SelectDatabaseResponse)
async def select_database(db_name: str, request_body: SelectDatabaseRequest, request: Request):
    """Select a database for the user's session"""
    try:
        db_service = request.app.state.database_management_service
        session_service = request.app.state.session_service
        user_id = request_body.user_id
        
        success = db_service.activate_database(db_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")
        
        # Sync with SessionService
        session_service.set_selected_database(user_id, db_name)
        
        # Get the session_id from the session data
        session_id = session_service.get_session_id(user_id)
        
        return SelectDatabaseResponse(
            success=True,
            message=f"Database '{db_name}' selected",
            session_id=session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error selecting database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ==================== KEY VAULT CREDENTIAL ENDPOINTS ====================

@router.post("/credentials/validate", response_model=CredentialSecurityCheckResponse)
async def validate_credentials_security(request_body: DatabaseTestRequest, request: Request):
    """
    Validate credentials and check read-only permissions
    Business logic delegated to DatabaseManagementService
    """
    try:
        db_service = request.app.state.database_management_service
        
        result = db_service.test_database_connection(request_body)
        
        if not result["success"]:
            return CredentialSecurityCheckResponse(
                success=False,
                message=result["message"],
                is_readonly=False,
                readonly_message="Could not test",
                permission_details={},
                can_save_securely=False
            )
        
        # Get permission details
        perm_result = db_service.validate_permissions(request_body)
        
        return CredentialSecurityCheckResponse(
            success=True,
            message="✓ Credentials validated successfully",
            is_readonly=perm_result.get("is_readonly", False),
            readonly_message=perm_result.get("message", "Unknown"),
            permission_details=perm_result.get("details", {}),
            can_save_securely=perm_result.get("can_save_securely", False)
        )
    except Exception as e:
        logger.error(f"❌ Error validating credentials: {e}", exc_info=True)
        return CredentialSecurityCheckResponse(
            success=False,
            message=f"Validation failed: {str(e)}",
            is_readonly=False,
            readonly_message=str(e),
            permission_details={},
            can_save_securely=False
        )


@router.get("/credentials/list", response_model=CredentialListResponse)
async def list_stored_credentials(request: Request):
    """List all stored credentials in Key Vault"""
    try:
        db_service = request.app.state.database_management_service
        
        credentials = db_service.list_stored_credentials()
        
        return CredentialListResponse(
            credentials=credentials,
            stored_in_keyvault=len(credentials) > 0
        )
    except Exception as e:
        logger.error(f"❌ Error listing credentials: {e}", exc_info=True)
        return CredentialListResponse(credentials=[], stored_in_keyvault=False)


@router.get("/credentials/{database_name}/metadata", response_model=CredentialMetadataResponse)
async def get_credential_metadata(database_name: str, request: Request):
    """Get metadata about stored credentials (without retrieving password)"""
    try:
        db_service = request.app.state.database_management_service
        
        metadata = db_service.get_credential_metadata(database_name)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"No credentials found for '{database_name}'")
        
        return CredentialMetadataResponse(**metadata)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting credential metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/credentials/{database_name}", response_model=Dict)
async def delete_stored_credentials(database_name: str, request: Request):
    """Delete credentials from Key Vault"""
    try:
        db_service = request.app.state.database_management_service
        
        success = db_service.delete_stored_credentials(database_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Credentials not found for '{database_name}'")
        
        return {"success": True, "message": f"Credentials for '{database_name}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/credentials/{database_name}/verify", response_model=Dict)
async def verify_stored_credentials(database_name: str, request: Request):
    """
    Verify that stored credentials still work
    Business logic delegated to DatabaseManagementService
    """
    try:
        db_service = request.app.state.database_management_service
        
        success, message = db_service.verify_credentials(database_name)
        
        return {
            "success": success,
            "message": message,
            "database_name": database_name
        }
    except Exception as e:
        logger.error(f"❌ Error verifying credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keyvault/status", response_model=Dict)
async def get_keyvault_status(request: Request):
    """Get Azure Key Vault integration status"""
    try:
        db_service = request.app.state.database_management_service
        
        status = db_service.get_keyvault_status()
        
        return status
    except Exception as e:
        return {
            "enabled": False,
            "status": "✗ Error",
            "error": str(e)
        }
