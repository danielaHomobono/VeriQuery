"""
Schemas Package
===============
Modelos Pydantic centralizados para toda la API
"""

from .query import QueryRequest, QueryResponse

__all__ = [
    "QueryRequest",
    "QueryResponse",
]
