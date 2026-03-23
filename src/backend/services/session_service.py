"""
Session Management Service
==========================
Gestión de sesiones de usuario y selección de bases de datos
Integra la lógica de database_session.py con patrón Service Layer
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SESSION_TIMEOUT_MINUTES = 30


class SessionService:
    """
    Servicio que gestiona las sesiones de usuario.
    
    Responsabilidades:
    - Crear y gestionar sesiones de usuario
    - Almacenar BD activa por sesión
    - Cachear schemas por sesión
    - Limpiar sesiones expiradas
    """

    def __init__(self):
        """
        Inicializa el servicio de sesiones.
        
        In-memory storage: {user_id: {session_data}}
        """
        # Formato: {user_id: {"database_name": str, "schema": dict, "timestamp": datetime, "session_id": str}}
        self._user_sessions: Dict[str, dict] = {}

    def create_session(self, user_id: str, session_id: str, database_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea o actualiza la sesión de un usuario.

        Args:
            user_id: ID del usuario
            session_id: ID de sesión único
            database_name: BD inicial (opcional)

        Returns:
            Dict con información de la sesión
        """
        try:
            logger.info(f"Creando sesión para usuario: {user_id}, session_id: {session_id}")
            
            session = {
                "user_id": user_id,
                "session_id": session_id,
                "database_name": database_name,
                "schema": {},
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "query_count": 0
            }
            
            self._user_sessions[user_id] = session
            logger.info(f"✓ Sesión creada para {user_id}")
            
            return session

        except Exception as e:
            logger.error(f"Error creando sesión: {str(e)}", exc_info=True)
            raise

    def set_selected_database(self, user_id: str, database_name: str, schema: Optional[dict] = None) -> None:
        """
        Establece la BD seleccionada para un usuario.

        Args:
            user_id: ID del usuario
            database_name: Nombre de la BD
            schema: Schema de la BD (opcional)
        """
        try:
            logger.info(f"[{user_id}] Seleccionando BD: {database_name}")
            
            if user_id not in self._user_sessions:
                logger.warning(f"[{user_id}] Sesión no existe, creando nueva")
                self.create_session(user_id, f"session_{user_id}")
            
            session = self._user_sessions[user_id]
            session["database_name"] = database_name
            session["schema"] = schema or {}
            session["last_accessed"] = datetime.now().isoformat()
            
            logger.info(f"✓ [{{user_id}}] BD establecida: {database_name}")

        except Exception as e:
            logger.error(f"[{user_id}] Error estableciendo BD: {str(e)}", exc_info=True)

    def get_selected_database(self, user_id: str) -> Optional[str]:
        """
        Obtiene la BD actualmente seleccionada por un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Nombre de la BD o None
        """
        try:
            if user_id not in self._user_sessions:
                logger.warning(f"[{user_id}] No hay sesión activa")
                return None
            
            session = self._user_sessions[user_id]
            
            # Verificar expiración
            if self._is_session_expired(session):
                logger.info(f"[{user_id}] Sesión expirada, eliminando")
                del self._user_sessions[user_id]
                return None
            
            # Actualizar timestamp
            session["last_accessed"] = datetime.now().isoformat()
            
            db_name = session.get("database_name")
            logger.info(f"✓ [{{user_id}}] BD activa: {db_name}")
            
            return db_name

        except Exception as e:
            logger.error(f"[{user_id}] Error obteniendo BD: {str(e)}", exc_info=True)
            return None

    def get_session_id(self, user_id: str) -> Optional[str]:
        """
        Obtiene el session_id para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Session ID o None
        """
        try:
            if user_id not in self._user_sessions:
                logger.warning(f"[{user_id}] No hay sesión activa")
                return None
            
            session = self._user_sessions[user_id]
            
            # Verificar expiración
            if self._is_session_expired(session):
                logger.info(f"[{user_id}] Sesión expirada, eliminando")
                del self._user_sessions[user_id]
                return None
            
            session_id = session.get("session_id")
            logger.info(f"✓ [{{user_id}}] Session ID: {session_id}")
            
            return session_id

        except Exception as e:
            logger.error(f"[{user_id}] Error obteniendo session_id: {str(e)}", exc_info=True)
            return None

    def get_selected_schema(self, user_id: str) -> Optional[dict]:
        """
        Obtiene el schema de la BD seleccionada.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con schema o None
        """
        try:
            if user_id not in self._user_sessions:
                return None
            
            session = self._user_sessions[user_id]
            
            if self._is_session_expired(session):
                del self._user_sessions[user_id]
                return None
            
            schema = session.get("schema", {})
            logger.info(f"[{user_id}] Schema retornado ({len(schema.get('tables', []))} tablas)")
            
            return schema

        except Exception as e:
            logger.error(f"[{user_id}] Error obteniendo schema: {str(e)}", exc_info=True)
            return None

    def update_schema(self, user_id: str, schema: dict) -> bool:
        """
        Actualiza el schema almacenado en la sesión.

        Args:
            user_id: ID del usuario
            schema: Nuevo schema

        Returns:
            True si se actualizó, False si no
        """
        try:
            if user_id not in self._user_sessions:
                logger.warning(f"[{user_id}] Sesión no existe")
                return False
            
            session = self._user_sessions[user_id]
            if self._is_session_expired(session):
                del self._user_sessions[user_id]
                return False
            
            session["schema"] = schema
            session["last_accessed"] = datetime.now().isoformat()
            
            logger.info(f"✓ [{{user_id}}] Schema actualizado")
            return True

        except Exception as e:
            logger.error(f"[{user_id}] Error actualizando schema: {str(e)}", exc_info=True)
            return False

    def increment_query_count(self, user_id: str) -> int:
        """
        Incrementa el contador de queries ejecutadas.

        Args:
            user_id: ID del usuario

        Returns:
            Nuevo contador
        """
        try:
            if user_id in self._user_sessions:
                session = self._user_sessions[user_id]
                session["query_count"] = session.get("query_count", 0) + 1
                session["last_accessed"] = datetime.now().isoformat()
                return session["query_count"]
            return 0

        except Exception as e:
            logger.error(f"[{user_id}] Error incrementando contador: {str(e)}", exc_info=True)
            return 0

    def get_session_info(self, user_id: str) -> Optional[Dict]:
        """
        Obtiene información completa de la sesión de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con info de sesión o None
        """
        try:
            if user_id not in self._user_sessions:
                return None
            
            session = self._user_sessions[user_id]
            
            if self._is_session_expired(session):
                del self._user_sessions[user_id]
                return None
            
            return {
                "user_id": session.get("user_id"),
                "session_id": session.get("session_id"),
                "database_name": session.get("database_name"),
                "query_count": session.get("query_count", 0),
                "created_at": session.get("created_at"),
                "last_accessed": session.get("last_accessed"),
                "schema_tables": len(session.get("schema", {}).get("tables", []))
            }

        except Exception as e:
            logger.error(f"[{user_id}] Error obteniendo info: {str(e)}", exc_info=True)
            return None

    def clear_session(self, user_id: str) -> None:
        """
        Limpia la sesión de un usuario.

        Args:
            user_id: ID del usuario
        """
        try:
            if user_id in self._user_sessions:
                del self._user_sessions[user_id]
                logger.info(f"✓ Sesión eliminada para: {user_id}")

        except Exception as e:
            logger.error(f"[{user_id}] Error limpiando sesión: {str(e)}", exc_info=True)

    def cleanup_expired_sessions(self) -> int:
        """
        Limpia todas las sesiones expiradas.

        Returns:
            Número de sesiones eliminadas
        """
        try:
            expired_users = [
                user_id for user_id, session in self._user_sessions.items()
                if self._is_session_expired(session)
            ]
            
            for user_id in expired_users:
                del self._user_sessions[user_id]
            
            if expired_users:
                logger.info(f"✓ {len(expired_users)} sesiones expiradas limpiadas")
            
            return len(expired_users)

        except Exception as e:
            logger.error(f"Error limpiando sesiones expiradas: {str(e)}", exc_info=True)
            return 0

    def get_active_sessions_count(self) -> int:
        """
        Retorna el número de sesiones activas (no expiradas).

        Returns:
            Número de sesiones
        """
        active = sum(
            1 for session in self._user_sessions.values()
            if not self._is_session_expired(session)
        )
        return active

    # ── PRIVATE ────────────────────────────────────────────────────────────

    def _is_session_expired(self, session: dict) -> bool:
        """
        Verifica si una sesión ha expirado.

        Args:
            session: Dict de sesión

        Returns:
            True si expiró, False si sigue activa
        """
        try:
            last_accessed = datetime.fromisoformat(session.get("last_accessed", datetime.now().isoformat()))
            return datetime.now() - last_accessed > timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        except Exception:
            return True
