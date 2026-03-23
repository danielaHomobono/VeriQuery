"""
Schema Scanning Service
=======================
Orquestador para escaneo y exportación de schemas de BD
"""

import logging
import json
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from src.backend.database.multi_db_connector import MultiDatabaseConnector

logger = logging.getLogger(__name__)


class SchemaService:
    """
    Servicio que encapsula la lógica de escaneo y gestión de schemas.
    
    Responsabilidades:
    - Escanear schema de BD activa o especificada
    - Cachear schemas escaneados
    - Exportar schemas en diferentes formatos
    """

    def __init__(self, multi_connector: Optional[MultiDatabaseConnector] = None):
        """
        Args:
            multi_connector: Instancia de MultiDatabaseConnector
        """
        self.connector = multi_connector or MultiDatabaseConnector()
        # Cache: {database_name: {"schema": dict, "timestamp": datetime, "tables_count": int}}
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    def scan_schema(self, database_name: Optional[str] = None) -> Tuple[Dict, Optional[str]]:
        """
        Escanea el schema de una base de datos.

        Args:
            database_name: Nombre de la BD (None = usar la activa)

        Returns:
            Tuple[schema: Dict, error: Optional[str]]
        """
        try:
            logger.info(f"Escaneando schema de BD: {database_name or '(active)'}")
            
            # Llamar al conector para escanear
            schema, error = self.connector.scan_schema(database_name)
            
            if error:
                logger.error(f"Error escaneando: {error}")
                return {}, error
            
            # Cachear el resultado
            if database_name:
                self._schema_cache[database_name] = {
                    "schema": schema,
                    "timestamp": datetime.now().isoformat(),
                    "tables_count": len(schema.get("tables", []))
                }
                logger.info(f"✓ Schema cacheado para: {database_name}")
            
            logger.info(f"✓ Scan exitoso: {len(schema.get('tables', []))} tablas encontradas")
            return schema, None

        except Exception as e:
            logger.error(f"Error en scan_schema: {str(e)}", exc_info=True)
            return {}, str(e)

    def get_cached_schema(self, database_name: Optional[str] = None) -> Optional[Dict]:
        """
        Obtiene schema cacheado de una BD.

        Args:
            database_name: Nombre de la BD (si None, retorna todos en cache)

        Returns:
            Dict del schema o None
        """
        try:
            if database_name is None:
                # Retornar información sobre todos los schemas en cache
                logger.info(f"Retornando {len(self._schema_cache)} schemas en cache")
                return {
                    "cached_databases": [
                        {
                            "name": name,
                            "tables_count": info.get("tables_count", 0),
                            "cached_at": info.get("timestamp")
                        }
                        for name, info in self._schema_cache.items()
                    ]
                }
            
            if database_name in self._schema_cache:
                logger.info(f"Retornando schema en cache para: {database_name}")
                return self._schema_cache[database_name]["schema"]
            
            logger.warning(f"Schema no en cache para: {database_name}")
            return None

        except Exception as e:
            logger.error(f"Error obteniendo schema en cache: {str(e)}", exc_info=True)
            return None

    def export_schema(self, database_name: Optional[str] = None, format: str = "json") -> Tuple[str, Optional[str]]:
        """
        Exporta el schema en un formato específico.

        Args:
            database_name: Nombre de la BD (None = usar la activa)
            format: Formato de exportación ("json", "sql", "csv")

        Returns:
            Tuple[exported_data: str, error: Optional[str]]
        """
        try:
            logger.info(f"Exportando schema de {database_name or '(active)'} en formato {format}")
            
            # Escanear si no está en cache
            if database_name not in self._schema_cache:
                schema, error = self.scan_schema(database_name)
                if error:
                    return "", error
            else:
                schema = self._schema_cache[database_name]["schema"]
            
            # Exportar según formato
            if format == "json":
                exported = json.dumps(schema, indent=2, default=str)
            elif format == "sql":
                exported = self._export_as_sql(schema, database_name)
            elif format == "csv":
                exported = self._export_as_csv(schema)
            else:
                return "", f"Formato no soportado: {format}"
            
            logger.info(f"✓ Schema exportado en formato {format} ({len(exported)} chars)")
            return exported, None

        except Exception as e:
            logger.error(f"Error exportando schema: {str(e)}", exc_info=True)
            return "", str(e)

    def _export_as_sql(self, schema: Dict, database_name: Optional[str]) -> str:
        """
        Exporta schema como comentarios SQL.

        Args:
            schema: Dict del schema
            database_name: Nombre de la BD

        Returns:
            String con SQL comentado
        """
        lines = [
            "-- Database Schema Export",
            f"-- Database: {database_name or 'Unknown'}",
            f"-- Exported: {datetime.now().isoformat()}",
            "",
        ]
        
        for table in schema.get("tables", []):
            lines.append(f"-- TABLE: {table.get('name', 'unknown')}")
            lines.append(f"-- Columns:")
            for col in table.get("columns", []):
                lines.append(f"--   - {col.get('name', 'unknown')} ({col.get('type', 'unknown')})")
            lines.append("")
        
        return "\n".join(lines)

    def _export_as_csv(self, schema: Dict) -> str:
        """
        Exporta schema como CSV.

        Args:
            schema: Dict del schema

        Returns:
            String con CSV
        """
        lines = ["TableName,ColumnName,DataType,Nullable"]
        
        for table in schema.get("tables", []):
            table_name = table.get("name", "unknown")
            for col in table.get("columns", []):
                col_name = col.get("name", "unknown")
                col_type = col.get("type", "unknown")
                nullable = col.get("nullable", True)
                lines.append(f"{table_name},{col_name},{col_type},{nullable}")
        
        return "\n".join(lines)

    def clear_schema_cache(self, database_name: Optional[str] = None) -> None:
        """
        Limpia el cache de schemas.

        Args:
            database_name: Si None, limpia TODO el cache
        """
        try:
            if database_name is None:
                self._schema_cache.clear()
                logger.info("Cache de schemas limpiado completamente")
            else:
                if database_name in self._schema_cache:
                    del self._schema_cache[database_name]
                    logger.info(f"Cache de {database_name} limpiado")

        except Exception as e:
            logger.error(f"Error limpiando cache: {str(e)}", exc_info=True)

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Retorna información sobre el cache actual.

        Returns:
            Dict con información del cache
        """
        return {
            "cached_databases": len(self._schema_cache),
            "databases": [
                {
                    "name": name,
                    "tables_count": info.get("tables_count", 0),
                    "cached_at": info.get("timestamp"),
                    "schema_size_kb": len(json.dumps(info.get("schema", {}))) / 1024
                }
                for name, info in self._schema_cache.items()
            ]
        }
