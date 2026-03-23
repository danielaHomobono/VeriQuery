"""
Ambiguity Detection Service
===========================
Orquestador para detección y resolución de ambigüedades en queries
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

from src.backend.agents.ambiguity_detector import AmbiguityDetector, MetricType, Clarification

logger = logging.getLogger(__name__)


class AmbiguityService:
    """
    Servicio que encapsula la lógica de detección de ambigüedades.
    
    Responsabilidades:
    - Detectar ambigüedades en queries de usuario
    - Almacenar aclaraciones pendientes por sesión
    - Procesar selección de clarificación
    """

    def __init__(self, ambiguity_detector: Optional[AmbiguityDetector] = None):
        """
        Args:
            ambiguity_detector: Instancia de AmbiguityDetector (lazy init si None)
        """
        self.detector = ambiguity_detector or AmbiguityDetector()
        # Store pending clarifications: {session_id: [Clarification, ...]}
        self._pending_clarifications: Dict[str, List[Clarification]] = {}

    def detect_ambiguity(self, query: str, session_id: str = "default") -> Dict:
        """
        Detecta ambigüedades en una query.

        Args:
            query: Pregunta del usuario
            session_id: ID de sesión para almacenar clarificaciones

        Returns:
            Dict con:
            - is_ambiguous: bool
            - ambiguities: List de ambigüedades encontradas
            - clarifications: List de opciones para resolver
        """
        try:
            logger.info(f"[{session_id}] Detectando ambigüedades en: {query[:80]}")
            
            result = self.detector.detect(query)
            
            # Almacenar clarificaciones para esta sesión
            if "clarifications" in result and result["clarifications"]:
                self._pending_clarifications[session_id] = result["clarifications"]
                logger.info(f"[{session_id}] Almacenadas {len(result['clarifications'])} clarificaciones")
            
            return result

        except Exception as e:
            logger.error(f"[{session_id}] Error detectando ambigüedades: {str(e)}", exc_info=True)
            return {
                "is_ambiguous": False,
                "ambiguities": [],
                "clarifications": [],
                "error": str(e)
            }

    def select_clarification(self, session_id: str, clarification_index: int) -> Dict:
        """
        Usuario selecciona una de las clarificaciones propuestas.

        Args:
            session_id: ID de sesión con clarificaciones pendientes
            clarification_index: Índice de la clarificación seleccionada (0-based)

        Returns:
            Dict con:
            - success: bool
            - selected_clarification: Clarification elegida
            - message: Confirmación del usuario
            - query_with_clarification: Query original + aclaración
        """
        try:
            logger.info(f"[{session_id}] Seleccionando clarificación #{clarification_index}")
            
            # Verificar que tenemos clarificaciones para esta sesión
            if session_id not in self._pending_clarifications:
                logger.warning(f"[{session_id}] No hay clarificaciones pendientes")
                return {
                    "success": False,
                    "error": "No hay clarificaciones pendientes para esta sesión"
                }
            
            clarifications = self._pending_clarifications[session_id]
            
            # Verificar índice válido
            if clarification_index < 0 or clarification_index >= len(clarifications):
                logger.warning(f"[{session_id}] Índice inválido: {clarification_index}")
                return {
                    "success": False,
                    "error": f"Índice inválido (0-{len(clarifications)-1})"
                }
            
            selected = clarifications[clarification_index]
            
            # Limpiar clarificaciones de esta sesión
            del self._pending_clarifications[session_id]
            
            logger.info(f"[{session_id}] ✓ Clarificación seleccionada: {selected.option_text}")
            
            return {
                "success": True,
                "selected_clarification": {
                    "index": clarification_index,
                    "option": selected.option_text,
                    "metric_type": selected.metric_type.value if selected.metric_type else None
                },
                "message": f"Entendido, buscarás por {selected.option_text}"
            }

        except Exception as e:
            logger.error(f"[{session_id}] Error seleccionando clarificación: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def get_pending_clarifications(self, session_id: str) -> List[Dict]:
        """
        Obtiene las clarificaciones pendientes para una sesión.

        Args:
            session_id: ID de sesión

        Returns:
            List de clarificaciones en formato dict
        """
        if session_id not in self._pending_clarifications:
            return []
        
        clarifications = self._pending_clarifications[session_id]
        return [
            {
                "index": i,
                "option": c.option_text,
                "metric_type": c.metric_type.value if c.metric_type else None,
                "explanation": c.explanation
            }
            for i, c in enumerate(clarifications)
        ]

    def clear_session(self, session_id: str) -> None:
        """Limpiar clarificaciones de una sesión."""
        if session_id in self._pending_clarifications:
            del self._pending_clarifications[session_id]
            logger.info(f"[{session_id}] Clarificaciones eliminadas")
