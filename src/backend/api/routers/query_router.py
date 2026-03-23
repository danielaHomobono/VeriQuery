"""
Query Router
============
Endpoints REST para ejecutar queries NL→SQL
Delega lógica a QueryService
"""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from src.backend.schemas import QueryRequest, QueryResponse
from src.backend.services import QueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["query"])


def get_query_service(request: Request) -> QueryService:
    """
    Extrae QueryService del contexto de la app
    (se inyecta en main.py via app.state)
    """
    return request.app.state.query_service


@router.post("", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def execute_query(request_body: QueryRequest, request: Request) -> QueryResponse:
    """
    Ejecuta una query NL→SQL end-to-end.

    Flujo:
    1. Validación de seguridad (PromptShield)
    2. Generación de SQL (NL2SQLGenerator)
    3. Ejecución en BD
    4. Formateo de respuesta

    Args:
        request_body: QueryRequest con pregunta
        request: FastAPI Request (para acceso a app.state)

    Returns:
        QueryResponse con resultado o error
    """
    try:
        query_service = get_query_service(request)
        response = query_service.execute_query(request_body)
        return response

    except Exception as e:
        logger.error(f"❌ Error en endpoint /api/query: {e}", exc_info=True)
        return QueryResponse(
            success=False,
            answer=None,
            error=f"Error procesando query: {str(e)[:200]}",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__
            }
        )


@router.get("/examples", tags=["examples"])
async def get_examples():
    """
    Retorna ejemplos de queries para mostrar en el frontend
    """
    examples = [
        "¿Cuántos clientes tenemos?",
        "¿Cuál es el producto más vendido?",
        "¿Cuántas transacciones se realizaron en marzo?",
        "¿Cuál es el total de ventas por región?",
        "¿Cuál es el cliente con mayor compra histórica?",
    ]
    return {
        "examples": examples,
        "count": len(examples)
    }
