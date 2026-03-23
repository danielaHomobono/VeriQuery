"""
Ambiguity Detection API Router
Endpoints for analyzing query ambiguity and suggesting clarifications
Delegates business logic to AmbiguityService
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["query-analysis"])


# Request/Response Models
class AnalyzeAmbiguityRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class Clarification(BaseModel):
    label: str
    metric: str
    description: str
    icon: str


class AnalyzeAmbiguityResponse(BaseModel):
    question: str
    is_ambiguous: bool
    keywords_found: List[str]
    clarifications: List[Clarification]
    confidence: float


class SelectClarificationRequest(BaseModel):
    question: str
    chosen_metric: str
    session_id: Optional[str] = None


class SelectClarificationResponse(BaseModel):
    question: str
    chosen_metric: str
    metric_label: str
    message: str
    next_step: str


# Endpoints

@router.post("/analyze-ambiguity", response_model=AnalyzeAmbiguityResponse)
async def analyze_ambiguity(request_body: AnalyzeAmbiguityRequest, request: Request):
    """
    Analyze a question for ambiguity and suggest clarifications
    Business logic delegated to AmbiguityService
    """
    try:
        ambiguity_service = request.app.state.ambiguity_service
        
        result = ambiguity_service.detect_ambiguity(
            question=request_body.question,
            session_id=request_body.session_id
        )
        
        return AnalyzeAmbiguityResponse(
            question=request_body.question,
            is_ambiguous=result["is_ambiguous"],
            keywords_found=result["keywords_found"],
            clarifications=[
                Clarification(
                    label=c["label"],
                    metric=c["metric"],
                    description=c["description"],
                    icon=c["icon"],
                )
                for c in result["clarifications"]
            ],
            confidence=result["confidence"],
        )
    except Exception as e:
        logger.error(f"❌ Error analyzing ambiguity: {e}", exc_info=True)
        raise


@router.post("/select-clarification", response_model=SelectClarificationResponse)
async def select_clarification(request_body: SelectClarificationRequest, request: Request):
    """
    User selects a clarification option
    Business logic delegated to AmbiguityService
    """
    try:
        ambiguity_service = request.app.state.ambiguity_service
        
        result = ambiguity_service.select_clarification(
            question=request_body.question,
            chosen_metric=request_body.chosen_metric,
            session_id=request_body.session_id
        )
        
        return SelectClarificationResponse(
            question=request_body.question,
            chosen_metric=request_body.chosen_metric,
            metric_label=result["metric_label"],
            message=result["message"],
            next_step="generating_queries",
        )
    except Exception as e:
        logger.error(f"❌ Error selecting clarification: {e}", exc_info=True)
        raise
