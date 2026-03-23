"""
Query Service
=============
Orquestador de lógica de negocio para ejecutar queries NL→SQL
Separa la lógica de BD y LLM de los endpoints
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import json

from src.backend.schemas import QueryRequest, QueryResponse
from src.backend.security.prompt_shields import PromptShield, ThreatLevel
from src.backend.nl2sql_generator import NL2SQLGenerator
from src.backend.core.tracer import QueryTracer

logger = logging.getLogger(__name__)


class QueryService:
    """
    Orquesta el flujo completo: Validación → NL2SQL → Ejecución → Formato
    
    Responsabilidades:
    - Validar input con PromptShield
    - Generar SQL con NL2SQLGenerator
    - Ejecutar en base de datos
    - Formatear respuesta
    - Manejar errores
    """

    @staticmethod
    def _format_schema_dict_to_string(schema_dict: Dict) -> str:
        """
        Convierte el schema dict de SchemaService a un string formateado
        compatible con nl2sql_generator.
        
        Args:
            schema_dict: Dict con estructura {"tables": [...]}
            
        Returns:
            String formateado del schema
        """
        if isinstance(schema_dict, str):
            return schema_dict  # Ya es string
        
        if not isinstance(schema_dict, dict):
            return str(schema_dict)
        
        schema_text = "=== SCHEMA ===\n"
        
        tables = schema_dict.get("tables", [])
        schema_text += f"Total tablas: {len(tables)}\n\n"
        
        for table in tables:
            table_name = table.get("name", "unnamed")
            schema_text += f"TABLA: {table_name}\n" + "-" * 40 + "\n"
            
            columns = table.get("columns", [])
            for col in columns:
                col_name = col.get("name", "unnamed")
                col_type = col.get("type", "unknown")
                col_nullable = "nullable" if col.get("nullable") else "not null"
                schema_text += f"  {col_name}: {col_type} ({col_nullable})\n"
            
            schema_text += "\n"
        
        return schema_text if schema_text.strip() else "⚠️ Schema vacío"

    def __init__(
        self,
        prompt_shield: PromptShield,
        nl2sql_generator: NL2SQLGenerator,
        multi_db_connector,
        schema_service=None
    ):
        """
        Args:
            prompt_shield: Instancia de validación de seguridad
            nl2sql_generator: Generador NL2SQL con QueryTracer
            multi_db_connector: MultiDatabaseConnector para ejecutar queries en diferentes BDs
            schema_service: (Opcional) Servicio de schemas para sincronizar caché
        """
        self.shield = prompt_shield
        self.nl2sql = nl2sql_generator
        self.multi_db = multi_db_connector
        self.schema_service = schema_service

    def execute_query(self, request: QueryRequest) -> QueryResponse:
        """
        Ejecuta una query end-to-end.

        Args:
            request: QueryRequest con pregunta y metadata

        Returns:
            QueryResponse con resultado o error
        """
        start_time = datetime.now()
        query_id = f"{int(start_time.timestamp() * 1000)}"

        try:
            logger.info(f"[{query_id}] Iniciando query: {request.question[:80]}")

            # ── PASO 1: Validación de seguridad ────────────────────────────
            validation = self.shield.validate_user_input(request.question)
            if not validation.is_safe:
                logger.warning(
                    f"[{query_id}] ❌ BLOQUEADO: {validation.threat_level.value} - {validation.message}"
                )
                return QueryResponse(
                    success=False,
                    answer=None,
                    error=f"Solicitud bloqueada: {validation.message}",
                    metadata={
                        "query_id": query_id,
                        "threat_level": validation.threat_level.value,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # ── PASO 2: Cambiar BD activa si es necesario ──────────────────
            if request.database_name:
                # Si tenemos SchemaService, pre-cargar schema desde caché sincronizado
                if self.schema_service:
                    cached_schema_dict = self.schema_service.get_cached_schema(request.database_name)
                    if cached_schema_dict:
                        # Convertir dict a string formateado
                        schema_str = self._format_schema_dict_to_string(cached_schema_dict)
                        # Sincronizar schema entre servicios
                        self.nl2sql._schema_cache[request.database_name] = schema_str
                        logger.info(f"✓ Schema sincronizado a nl2sql para: {request.database_name} ({len(schema_str)} chars)")
                
                # Ahora cambiar BD activa (encontrará schema en caché)
                self.nl2sql.set_active_database_name(request.database_name)
                logger.info(f"✓ BD activa cambiada a: {request.database_name}")

            # ── PASO 3: Generar SQL ───────────────────────────────────────
            sql_result = self.nl2sql.generate_sql(
                natural_language_query=request.question,
                conversation_history=request.conversation_history or []
            )

            if sql_result.get("type") == "error":
                logger.error(f"[{query_id}] Error generando SQL: {sql_result.get('message')}")
                return QueryResponse(
                    success=False,
                    answer=None,
                    error=sql_result.get("message"),
                    trace_steps=sql_result.get("trace_steps"),
                    metadata={
                        "query_id": query_id,
                        "threat_level": validation.threat_level.value,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            if sql_result.get("type") == "clarification":
                # Usuario necesita aclarar ambigüedad
                logger.info(f"[{query_id}] Ambigüedad detectada, pidiendo clarificación")
                return QueryResponse(
                    success=True,
                    answer=None,
                    error=None,
                    metadata={
                        "type": "clarification",
                        "keywords": sql_result.get("keywords_found"),
                        "options": sql_result.get("clarifications"),
                        "query_id": query_id,
                        "timestamp": datetime.now().isoformat()
                    },
                    trace_steps=sql_result.get("trace_steps")
                )

            # ── PASO 4: Validación de SQL ──────────────────────────────────
            sql = sql_result.get("sql")
            if not sql or not sql_result.get("valid"):
                logger.error(f"[{query_id}] SQL inválida o vacía")
                return QueryResponse(
                    success=False,
                    answer=None,
                    sql=sql,
                    error="SQL inválida o vacía",
                    metadata={
                        "query_id": query_id,
                        "threat_level": validation.threat_level.value,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # ── PASO 5: Validación de salida (segundo PromptShield) ────────
            output_validation = self.shield.validate_generated_sql(sql)
            if not output_validation.is_safe:
                logger.error(
                    f"[{query_id}] SQL bloqueada: {output_validation.threat_level.value}"
                )
                return QueryResponse(
                    success=False,
                    answer=None,
                    sql=sql,
                    error=f"SQL bloqueada por validación de seguridad",
                    metadata={
                        "query_id": query_id,
                        "threat_level": output_validation.threat_level.value,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # ── PASO 6: Ejecución en base de datos ────────────────────────
            db_exec_start = datetime.now()
            
            # Usar MultiDatabaseConnector con el database_name especificado
            db_results, db_error = self.multi_db.execute_query(
                sql,
                database_name=request.database_name or self.multi_db.active_database.name if self.multi_db.active_database else None
            )
            db_exec_time = (datetime.now() - db_exec_start).total_seconds() * 1000

            if db_error:
                logger.error(f"[{query_id}] Error BD: {db_error}")
                return QueryResponse(
                    success=False,
                    answer=None,
                    sql=sql,
                    explanation=sql_result.get("explanation"),
                    error=db_error,
                    data=[],
                    row_count=0,
                    confidence=0.0,
                    metadata={
                        "query_id": query_id,
                        "threat_level": validation.threat_level.value,
                        "db_execution_time_ms": round(db_exec_time, 2),
                        "total_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2),
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # ── PASO 7: Retornar resultado exitoso ─────────────────────────
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"[{query_id}] ✅ Query exitosa: {len(db_results)} rows en {db_exec_time:.0f}ms"
            )

            return QueryResponse(
                success=True,
                answer=sql_result.get("explanation", "Query ejecutada correctamente"),
                sql=sql,
                explanation=sql_result.get("explanation"),
                data=db_results or [],
                row_count=len(db_results),
                confidence=sql_result.get("confidence", 95.0),
                error=None,
                trace_steps=sql_result.get("trace_steps"),
                metadata={
                    "query_id": query_id,
                    "threat_level": validation.threat_level.value,
                    "db_execution_time_ms": round(db_exec_time, 2),
                    "total_time_ms": round(total_time, 2),
                    "user_id": request.user_id,
                    "database": self.nl2sql._active_db_name,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"[{query_id}] Excepción: {e}", exc_info=True)
            return QueryResponse(
                success=False,
                answer=None,
                error=f"Error inesperado: {str(e)[:200]}",
                metadata={
                    "query_id": query_id,
                    "total_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2),
                    "timestamp": datetime.now().isoformat()
                }
            )
