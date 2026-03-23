"""
Database Management Service
===========================
Orquestador para gestión de configuraciones de bases de datos
"""

import logging
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

from src.backend.database.multi_db_connector import MultiDatabaseConnector

logger = logging.getLogger(__name__)


class DatabaseManagementService:
    """
    Servicio que encapsula la lógica de gestión de bases de datos.
    
    Responsabilidades:
    - Probar conexiones a BD
    - Guardar/listar/eliminar configuraciones de BD
    - Validar credenciales
    - Activar BD para sesión
    """

    def __init__(self, multi_connector: Optional[MultiDatabaseConnector] = None):
        """
        Args:
            multi_connector: Instancia de MultiDatabaseConnector
        """
        self.connector = multi_connector or MultiDatabaseConnector()

    def test_database_connection(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Prueba la conexión a una base de datos.

        Args:
            config: Configuración de BD (host, port, user, password, database)

        Returns:
            Tuple[success: bool, message: str]
        """
        try:
            logger.info(f"Probando conexión a: {config.get('host')}:{config.get('port')}")
            success, msg = self.connector.test_connection(config)
            
            if success:
                logger.info(f"✓ Conexión exitosa: {msg}")
            else:
                logger.warning(f"✗ Conexión fallida: {msg}")
            
            return success, msg

        except Exception as e:
            logger.error(f"Error probando conexión: {str(e)}", exc_info=True)
            return False, f"Error: {str(e)}"

    def save_database_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Guarda configuración de base de datos.

        Args:
            config: Configuración con nombre y detalles

        Returns:
            Tuple[success: bool, message: str]
        """
        try:
            logger.info(f"Guardando configuración de BD: {config.get('name')}")
            success, msg = self.connector.save_database_config(
                config.get('name'),
                config.get('db_type'),
                config.get('host'),
                config.get('port'),
                config.get('database'),
                config.get('username'),
                config.get('password')
            )
            
            if success:
                logger.info(f"✓ Configuración guardada: {msg}")
            else:
                logger.warning(f"✗ Error guardando: {msg}")
            
            return success, msg

        except Exception as e:
            logger.error(f"Error guardando configuración: {str(e)}", exc_info=True)
            return False, f"Error: {str(e)}"

    def list_databases(self) -> List[str]:
        """
        Lista todas las bases de datos configuradas.

        Returns:
            List de nombres de BD
        """
        try:
            databases = self.connector.list_databases()
            logger.info(f"Listando {len(databases)} BDs configuradas")
            return databases

        except Exception as e:
            logger.error(f"Error listando BDs: {str(e)}", exc_info=True)
            return []

    def get_database_info(self, database_name: str) -> Optional[Dict]:
        """
        Obtiene información de una base de datos.

        Args:
            database_name: Nombre de la BD

        Returns:
            Dict con configuración o None
        """
        try:
            info = self.connector.get_database_info(database_name)
            if info:
                logger.info(f"Información de BD '{database_name}' recuperada")
            else:
                logger.warning(f"BD '{database_name}' no encontrada")
            return info

        except Exception as e:
            logger.error(f"Error obteniendo info de BD: {str(e)}", exc_info=True)
            return None

    def delete_database_config(self, database_name: str) -> Tuple[bool, str]:
        """
        Elimina configuración de una base de datos.

        Args:
            database_name: Nombre de la BD

        Returns:
            Tuple[success: bool, message: str]
        """
        try:
            logger.info(f"Eliminando configuración de BD: {database_name}")
            success, msg = self.connector.delete_database_config(database_name)
            
            if success:
                logger.info(f"✓ BD eliminada: {msg}")
            else:
                logger.warning(f"✗ Error eliminando: {msg}")
            
            return success, msg

        except Exception as e:
            logger.error(f"Error eliminando BD: {str(e)}", exc_info=True)
            return False, f"Error: {str(e)}"

    def activate_database(self, database_name: str) -> Tuple[bool, str]:
        """
        Activa una base de datos como la actual.

        Args:
            database_name: Nombre de la BD

        Returns:
            Tuple[success: bool, message: str]
        """
        try:
            logger.info(f"Activando BD: {database_name}")
            success, msg = self.connector.set_active_database(database_name)
            
            if success:
                logger.info(f"✓ BD activada: {msg}")
            else:
                logger.warning(f"✗ Error activando: {msg}")
            
            return success, msg

        except Exception as e:
            logger.error(f"Error activando BD: {str(e)}", exc_info=True)
            return False, f"Error: {str(e)}"

    def scan_database_schema(self, database_name: Optional[str] = None) -> Tuple[Dict, Optional[str]]:
        """
        Escanea el schema de una base de datos.

        Args:
            database_name: Nombre de la BD (None = usar la activa)

        Returns:
            Tuple[schema: Dict, error: Optional[str]]
        """
        try:
            logger.info(f"Escaneando schema de BD: {database_name or 'active'}")
            schema, error = self.connector.scan_schema(database_name)
            
            if error:
                logger.error(f"Error escaneando schema: {error}")
            else:
                logger.info(f"✓ Schema escaneado: {len(schema.get('tables', []))} tablas")
            
            return schema, error

        except Exception as e:
            logger.error(f"Error en scan_database_schema: {str(e)}", exc_info=True)
            return {}, str(e)
