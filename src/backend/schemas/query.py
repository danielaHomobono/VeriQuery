"""
Query Request/Response Schemas
==============================
Modelos Pydantic para requests y responses del endpoint /api/query
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QueryRequest(BaseModel):
    """Request body para POST /api/query"""
    question: str = Field(..., description="Pregunta en lenguaje natural", min_length=1)
    user_id: str = Field(default="anonymous", description="ID del usuario")
    session_id: Optional[str] = Field(default=None, description="ID de sesión")
    database_name: Optional[str] = Field(default=None, description="BD a usar (si no, usa default)")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Historial de conversación"
    )


class QueryResponse(BaseModel):
    """Response para POST /api/query"""
    success: bool = Field(..., description="¿Query exitosa?")
    answer: Optional[str] = Field(default=None, description="Respuesta en lenguaje natural")
    sql: Optional[str] = Field(default=None, description="SQL generada")
    explanation: Optional[str] = Field(default=None, description="Explicación de la query")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Resultados")
    row_count: int = Field(default=0, description="Cantidad de filas")
    confidence: Optional[float] = Field(default=None, ge=0, le=100, description="Confianza 0-100")
    error: Optional[str] = Field(default=None, description="Mensaje de error si falló")
    trace_steps: Optional[Dict[str, Any]] = Field(default=None, description="Pasos del tracer")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "answer": "Tenemos 1,663 clientes registrados",
                "sql": "SELECT COUNT(*) as total FROM Customer",
                "explanation": "Conté todos los clientes activos",
                "data": [{"total": 1663}],
                "row_count": 1,
                "confidence": 95.0,
                "trace_steps": {
                    "query_id": "1234567890_5678",
                    "question": "¿Cuántos clientes tenemos?",
                    "total_ms": 450.5,
                    "step_count": 8,
                    "error_count": 0,
                    "level": "full",
                    "steps": []
                },
                "metadata": {
                    "execution_time_ms": 125.5,
                    "threat_level": "safe",
                    "query_id": "abc123",
                    "timestamp": "2026-03-22T10:30:00"
                }
            }
        }
    }
