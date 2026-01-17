"""
UC8: Sales Enablement Content Generator API.
Generates sales-ready content for surgeon meetings and presentations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.sales_content_service import get_sales_content_service

router = APIRouter()


class ContentType(str, Enum):
    """Sales content type."""
    TALKING_POINTS = "talking_points"
    VALUE_PROPOSITION = "value_proposition"
    SURGEON_PRESENTATION = "surgeon_presentation"


class EvidenceCitation(BaseModel):
    """Evidence citation for claims."""
    claim: str = Field(..., description="Claim being made")
    source: str = Field(..., description="Evidence source")


class ObjectionHandler(BaseModel):
    """Objection and response pair."""
    objection: str = Field(..., description="Customer objection")
    response: str = Field(..., description="Evidence-based response")


class UsageGuidelines(BaseModel):
    """Guidelines for content usage."""
    target_audience: str = Field(..., description="Target audience")
    context: str = Field(..., description="Usage context")
    compliance_note: str = Field(..., description="Compliance notes")


class TalkingPointsResponse(BaseModel):
    """Talking points response."""
    success: bool = Field(..., description="Request success status")
    content_type: str = Field(..., description="Content type")
    generated_at: str = Field(..., description="Generation timestamp")
    product: str = Field(..., description="Product name")
    content: Optional[str] = Field(None, description="Generated content")
    key_messages: List[str] = Field(default_factory=list, description="Key messages")
    evidence_citations: List[Dict[str, str]] = Field(default_factory=list, description="Evidence citations")
    competitive_positioning: Dict[str, Any] = Field(default_factory=dict, description="Competitive positioning")
    objection_handlers: List[Dict[str, str]] = Field(default_factory=list, description="Objection handlers")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.85, description="Confidence score")
    usage_guidelines: Dict[str, Any] = Field(default_factory=dict, description="Usage guidelines")


class ValuePropositionResponse(BaseModel):
    """Value proposition response."""
    success: bool = Field(..., description="Request success status")
    content_type: str = Field(..., description="Content type")
    generated_at: str = Field(..., description="Generation timestamp")
    product: str = Field(..., description="Product name")
    content: Optional[str] = Field(None, description="Generated content")
    target_customer: Dict[str, Any] = Field(default_factory=dict, description="Target customer profile")
    problem_addressed: str = Field(..., description="Problem addressed")
    key_benefits: List[Dict[str, Any]] = Field(default_factory=list, description="Key benefits with evidence")
    differentiation: str = Field(..., description="Differentiation statement")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.83, description="Confidence score")


class PresentationResponse(BaseModel):
    """Surgeon presentation response."""
    success: bool = Field(..., description="Request success status")
    content_type: str = Field(..., description="Content type")
    generated_at: str = Field(..., description="Generation timestamp")
    product: str = Field(..., description="Product name")
    content: Optional[str] = Field(None, description="Generated content")
    presentation_outline: List[Dict[str, Any]] = Field(default_factory=list, description="Presentation outline")
    key_slides_content: Dict[str, Any] = Field(default_factory=dict, description="Key slide content")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.82, description="Confidence score")


@router.post("/sales-content", response_model=TalkingPointsResponse)
async def generate_sales_content(
    content_type: ContentType = Query(
        ContentType.TALKING_POINTS,
        description="Type of sales content to generate"
    )
) -> TalkingPointsResponse:
    """
    Generate sales enablement content.

    Creates evidence-based sales content including:
    - **talking_points**: Key messages for surgeon meetings
    - **value_proposition**: Structured value proposition
    - **surgeon_presentation**: Presentation outline

    All content includes:
    - Evidence citations from clinical study
    - Registry benchmark comparisons
    - Objection handlers with responses
    """
    service = get_sales_content_service()
    result = await service.generate_sales_content(content_type=content_type.value)

    return TalkingPointsResponse(**result)


@router.get("/talking-points", response_model=TalkingPointsResponse)
async def get_talking_points() -> TalkingPointsResponse:
    """
    Generate talking points for surgeon meetings.

    Creates 5-7 evidence-based talking points including:
    - Clinical benefit statements
    - Supporting data points
    - Registry comparisons
    - Objection handlers

    Designed for: 1:1 surgeon meetings, product presentations
    """
    service = get_sales_content_service()
    result = await service.generate_sales_content(content_type="talking_points")

    return TalkingPointsResponse(**result)


@router.get("/value-proposition", response_model=ValuePropositionResponse)
async def get_value_proposition() -> ValuePropositionResponse:
    """
    Generate structured value proposition.

    Creates a comprehensive value proposition including:
    - Target customer profile
    - Problem statement
    - Solution overview
    - Key benefits with evidence
    - Differentiation statement

    Suitable for: Sales training, marketing materials, elevator pitch
    """
    service = get_sales_content_service()
    result = await service.generate_sales_content(content_type="value_proposition")

    return ValuePropositionResponse(**result)


@router.get("/presentation", response_model=PresentationResponse)
async def get_surgeon_presentation() -> PresentationResponse:
    """
    Generate surgeon presentation outline.

    Creates a 10-minute presentation outline including:
    - Section breakdown with timing
    - Key content for each section
    - Clinical evidence summary
    - Registry comparison data

    Designed for: Surgeon education events, product launches
    """
    service = get_sales_content_service()
    result = await service.generate_sales_content(content_type="surgeon_presentation")

    return PresentationResponse(**result)


@router.get("/objection-handlers")
async def get_objection_handlers() -> Dict[str, Any]:
    """
    Get objection handlers with evidence-based responses.

    Returns common objections and data-backed responses suitable for:
    - Sales training
    - Quick reference during meetings
    """
    service = get_sales_content_service()
    result = await service.generate_sales_content(content_type="talking_points")

    return {
        "success": result.get("success", False),
        "generated_at": datetime.utcnow().isoformat(),
        "product": "DELTA Revision Cup",
        "objection_handlers": result.get("objection_handlers", []),
        "sources": result.get("sources", []),
    }


@router.get("/content-types")
async def get_content_types() -> Dict[str, Any]:
    """
    Get available sales content types.

    Returns list of content types with descriptions and usage contexts.
    """
    return {
        "available_types": [
            {
                "type": "talking_points",
                "description": "Evidence-based talking points for surgeon meetings",
                "use_case": "1:1 meetings, product presentations",
            },
            {
                "type": "value_proposition",
                "description": "Structured value proposition with benefits",
                "use_case": "Sales training, marketing materials",
            },
            {
                "type": "surgeon_presentation",
                "description": "10-minute presentation outline",
                "use_case": "Education events, product launches",
            },
        ],
        "default_type": "talking_points",
    }
