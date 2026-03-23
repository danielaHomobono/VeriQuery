"""
Services Package - Capa de servicios de VeriQuery
================================================
Expone servicios centralizados:
- QueryService: Orquesta pipeline NL→SQL→Execute→Format
- AmbiguityService: Detecta y resuelve ambigüedades en queries
- DatabaseManagementService: Gestiona configuraciones de BD
- SchemaService: Escanea y exporta schemas
- SessionService: Gestiona sesiones de usuario
"""

# Importar desde módulos individuales
from .query_service import QueryService
from .ambiguity_service import AmbiguityService
from .database_management_service import DatabaseManagementService
from .schema_service import SchemaService
from .session_service import SessionService

# Exportar públicamente
__all__ = [
    "QueryService",
    "AmbiguityService",
    "DatabaseManagementService",
    "SchemaService",
    "SessionService",
]
