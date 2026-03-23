"""
Routers Package
===============
Endpoints REST organizados por dominio
"""

from .query_router import router as query_router

__all__ = ["query_router"]
