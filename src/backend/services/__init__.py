""""""

Services PackageQueryService - Capa de servicios que orquesta el procesamiento de queries

================Responsable de: validación → generación SQL → ejecución → formateo

Orquestadores de lógica de negocio (Application Layer)"""

"""

import logging

from .query_service import QueryServicefrom typing import Optional, Dict, Any, List

from datetime import datetime

__all__ = ["QueryService"]import json


from security.prompt_shields import PromptShield, ThreatLevel
from nl2sql_generator import NL2SQLGenerator
from database import DatabaseConnector
from exceptions import (
    SecurityException,
    InvalidSQLException,
    DatabaseException,
    ValidationException
)

logger = logging.getLogger(__name__)


class QueryResult:
    """Domain model for query results"""
    
    def __init__(
        self,
        success: bool,
        answer: Optional[str] = None,
        sql: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None,
        row_count: int = 0,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        execution_time_ms: float = 0
    ):
        self.success = success
        self.answer = answer
        self.sql = sql
        self.data = data or []
        self.row_count = row_count
        self.error = error
        self.error_code = error_code
        self.execution_time_ms = execution_time_ms
        self.timestamp = datetime.utcnow()


class QueryService:
    """
    Orquesta todo el pipeline de procesamiento de queries
    
    Responsabilidades:
    1. Validación de seguridad
    2. Generación de SQL
    3. Ejecución en BD
    4. Formateo de respuesta
    5. Logging y auditoría
    """
    
    def __init__(
        self,
        shield: PromptShield,
        nl2sql_generator: NL2SQLGenerator,
        db_connector: DatabaseConnector
    ):
        """
        Args:
            shield: PromptShield para validación de seguridad
            nl2sql_generator: Generador de SQL desde NL
            db_connector: Conector de base de datos
        """
        self.shield = shield
        self.nl2sql_gen = nl2sql_generator
        self.db = db_connector
        self.logger = logger.getChild(self.__class__.__name__)
    
    def execute_query(
        self,
        question: str,
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
        database_name: Optional[str] = None
    ) -> QueryResult:
        """
        Ejecuta el pipeline completo de procesamiento de query
        
        Args:
            question: Pregunta en lenguaje natural
            user_id: ID del usuario que hace la pregunta
            session_id: ID de sesión (para contexto)
            database_name: Base de datos seleccionada
        
        Returns:
            QueryResult con resultado o error
        
        Raises:
            SecurityException: Si validación de seguridad falla
            InvalidSQLException: Si SQL generado es inválido
            DatabaseException: Si ejecución en BD falla
            ValidationException: Si validación de entrada falla
        """
        query_id = self._generate_query_id()
        start_time = datetime.utcnow()
        
        try:
            # Si no se pasa database_name, intentar obtenerlo de la sesión
            if not database_name:
                import database_session
                database_name = database_session.get_selected_database(user_id)
            
            self.logger.info(f"[{query_id}] ➡️ RECEIVED: {question} (user={user_id}, db={database_name})")
            
            # STEP 1: Validación
            self.logger.info(f"[{query_id}] 🛡️ Security validation...")
            security_result = self._validate_security(question, user_id)
            self.logger.info(f"[{query_id}] 🛡️ Security check: {security_result}")
            
            # STEP 2: Generación de SQL
            self.logger.info(f"[{query_id}] 🤖 Generating SQL...")
            sql = self._generate_sql(question, query_id, database_name)
            self.logger.info(f"[{query_id}] ✅ SQL generated: {sql}")
            
            # STEP 3: Ejecución
            self.logger.info(f"[{query_id}] 💾 Executing query...")
            db_result = self._execute_database_query(sql, query_id, database_name, user_id)
            self.logger.info(f"[{query_id}] ✅ Query executed: {db_result.row_count} rows")
            
            # STEP 4: Formateo de respuesta
            self.logger.info(f"[{query_id}] 📝 Formatting answer...")
            answer = self._format_answer(question, db_result.data)
            self.logger.info(f"[{query_id}] ✅ Answer formatted")
            
            # Calcular tiempo
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Retornar resultado exitoso
            result = QueryResult(
                success=True,
                answer=answer,
                sql=sql,
                data=db_result.data,
                row_count=db_result.row_count,
                execution_time_ms=execution_time
            )
            
            self.logger.info(f"[{query_id}] 🎯 SUCCESS - Returning result")
            return result
            
        except SecurityException as e:
            self.logger.error(f"[{query_id}] 🚫 SECURITY ERROR: {e.message}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResult(
                success=False,
                error=e.message,
                error_code=e.error_code.value,
                execution_time_ms=execution_time
            )
        except InvalidSQLException as e:
            self.logger.error(f"[{query_id}] ❌ INVALID SQL: {e.message}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResult(
                success=False,
                error=e.message,
                error_code=e.error_code.value,
                execution_time_ms=execution_time
            )
        except DatabaseException as e:
            self.logger.error(f"[{query_id}] 💥 DATABASE ERROR: {e.message}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResult(
                success=False,
                error=e.message,
                error_code=e.error_code.value,
                execution_time_ms=execution_time
            )
        except ValidationException as e:
            self.logger.error(f"[{query_id}] ⚠️ VALIDATION ERROR: {e.message}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResult(
                success=False,
                error=e.message,
                error_code=e.error_code.value,
                execution_time_ms=execution_time
            )
        except Exception as e:
            self.logger.error(f"[{query_id}] 💣 UNEXPECTED ERROR: {str(e)}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="INTERNAL_ERROR",
                execution_time_ms=execution_time
            )
    
    # ========================================================================
    # PRIVATE METHODS - LÓGICA DE CADA PASO
    # ========================================================================
    
    def _validate_security(self, question: str, user_id: str) -> bool:
        """
        Valida que la pregunta sea segura
        
        Raises:
            SecurityException: Si la pregunta es considerada una amenaza
        """
        try:
            result = self.shield.validate_user_input(question)
            
            if not result.is_safe:
                raise SecurityException(
                    message=f"Query blocked by security: {result.threat_level.name}",
                    details={
                        "threat_level": result.threat_level.name,
                        "blocked_patterns": result.blocked_patterns if hasattr(result, 'blocked_patterns') else []
                    }
                )
            
            return True
        except Exception as e:
            if isinstance(e, SecurityException):
                raise
            raise SecurityException(f"Security validation failed: {str(e)}")
    
    def _generate_sql(self, question: str, query_id: str, database_name: Optional[str] = None) -> str:
        """
        Genera SQL desde la pregunta en lenguaje natural
        
        Raises:
            InvalidSQLException: Si la generación falla o SQL es inválido
        """
        try:
            # Si hay database_name, activarla en el generador
            if database_name:
                self.logger.info(f"[{query_id}] Activating database: {database_name}")
                self.nl2sql_gen.set_active_database_name(database_name)
            
            result = self.nl2sql_gen.generate_sql(question)
            
            # Validar respuesta
            if not result or not isinstance(result, dict):
                raise InvalidSQLException("SQL generation returned invalid response")
            
            sql = result.get("sql")
            if not sql:
                raise InvalidSQLException("No SQL generated from question")
            
            # Validación básica del SQL
            if not self._is_valid_sql(sql):
                raise InvalidSQLException(f"Generated SQL failed validation: {sql}")
            
            return sql
        except Exception as e:
            if isinstance(e, InvalidSQLException):
                raise
            raise InvalidSQLException(f"SQL generation failed: {str(e)}", sql=str(e))
    
    def _execute_database_query(self, sql: str, query_id: str, database_name: Optional[str] = None, user_id: str = "anonymous"):
        """
        Ejecuta query en la base de datos.
        Si database_name está especificado, obtiene credenciales de Key Vault y crea un connector dinámico.
        Soporta SQL Server y PostgreSQL (Supabase).
        
        Raises:
            DatabaseException: Si la ejecución falla
        """
        try:
            # Si hay database_name, crear connector dinámico desde Key Vault
            db_connector = self.db
            if database_name and database_name != "default":
                self.logger.info(f"[{query_id}] 🔑 Obteniendo credenciales de Key Vault para: {database_name}")
                from core.secure_credential_store import SecureCredentialStore
                store = SecureCredentialStore()
                creds, error = store.get_credentials(database_name)
                
                if creds and not error:
                    self.logger.info(f"[{query_id}] ✅ Credenciales obtenidas de Key Vault")
                    
                    # Determinar tipo de BD y crear connector apropiado
                    db_type = creds.get("db_type", "sqlserver").lower()
                    self.logger.info(f"[{query_id}] 🗄️ Tipo de BD: {db_type}")
                    
                    from database import ConnectionConfig, SQLServerConnector, PostgreSQLConnector
                    
                    config = ConnectionConfig(
                        host=creds.get("host"),
                        port=int(creds.get("port", 1433 if db_type == "sqlserver" else 5432)),
                        username=creds.get("username"),
                        password=creds.get("password"),
                        database=creds.get("database"),
                        driver=creds.get("driver")  # Para SQL Server
                    )
                    
                    # Crear connector específico según tipo de BD
                    if db_type == "postgresql":
                        self.logger.info(f"[{query_id}] 📊 Creando connector PostgreSQL/Supabase")
                        db_connector = PostgreSQLConnector(config)
                    else:  # sqlserver
                        self.logger.info(f"[{query_id}] 📊 Creando connector SQL Server/Azure SQL")
                        db_connector = SQLServerConnector(config)
                    
                    db_connector.connect()
                    self.logger.info(f"[{query_id}] ✅ Connector dinámico conectado exitosamente")
                else:
                    self.logger.warning(f"[{query_id}] ⚠️ No se encontraron credenciales para {database_name}, usando connector por defecto")
            
            if not db_connector:
                raise DatabaseException("Database connector not available")
            
            # Ejecutar query (método sincrónico)
            self.logger.debug(f"[{query_id}] Ejecutando query en BD...")
            result = db_connector.execute_query(sql)
            
            if not result:
                raise DatabaseException("Database returned empty result")
            
            if hasattr(result, 'success') and not result.success:
                raise DatabaseException(
                    f"Query execution failed: {result.error if hasattr(result, 'error') else 'Unknown error'}",
                    query=sql
                )
            
            return result
        except Exception as e:
            if isinstance(e, DatabaseException):
                raise
            raise DatabaseException(f"Database execution failed: {str(e)}", query=sql)
    
    def _format_answer(self, question: str, data: List[Dict[str, Any]]) -> str:
        """
        Formatea los datos en una respuesta legible para el usuario
        """
        if not data:
            return "No data found for this query."
        
        if len(data) == 1 and len(data[0]) == 1:
            # Respuesta simple (un valor)
            value = list(data[0].values())[0]
            key = list(data[0].keys())[0]
            return f"The result is {value} ({key})"
        
        # Respuesta compleja
        return f"Query returned {len(data)} row(s) with data: {json.dumps(data, indent=2)}"
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _is_valid_sql(self, sql: str) -> bool:
        """Validación básica de SQL"""
        if not sql or not isinstance(sql, str):
            return False
        
        sql_upper = sql.strip().upper()
        
        # Debe comenzar con un comando válido
        valid_starts = ("SELECT", "WITH")
        if not any(sql_upper.startswith(start) for start in valid_starts):
            return False
        
        # No debe contener comandos peligrosos
        dangerous_keywords = ("DROP", "DELETE FROM", "TRUNCATE", "ALTER", "UPDATE", "INSERT INTO")
        if any(keyword in sql_upper for keyword in dangerous_keywords):
            return False
        
        return True
    
    def _generate_query_id(self) -> str:
        """Genera un ID único para la query"""
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%H%M%S")
        return timestamp


class DatabaseQueryService:
    """
    Servicio para operaciones de base de datos (selección, listado, etc)
    """
    
    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector
        self.logger = logger.getChild(self.__class__.__name__)
    
    def get_available_databases(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene lista de bases de datos disponibles para un usuario"""
        try:
            # TODO: Implementar consulta a Guardian DB
            # Por ahora retorna lista por defecto
            return [
                {
                    "db_name": "contosoV210k",
                    "db_type": "sqlserver",
                    "display_name": "Contoso (Local)",
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
        except Exception as e:
            self.logger.error(f"Failed to get databases: {str(e)}")
            raise DatabaseException(f"Failed to list databases: {str(e)}")
    
    def select_database(self, db_name: str, user_id: str) -> Dict[str, Any]:
        """Selecciona una base de datos para el usuario"""
        try:
            # TODO: Implementar selección con Guardian DB
            return {
                "success": True,
                "db_name": db_name,
                "message": f"Database '{db_name}' selected successfully"
            }
        except Exception as e:
            self.logger.error(f"Failed to select database: {str(e)}")
            raise DatabaseException(f"Failed to select database: {str(e)}")
