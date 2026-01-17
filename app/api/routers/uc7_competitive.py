"""
UC7: Competitive Intelligence API.
Literature and registry-based competitive landscape analysis for Sales, Marketing, and Strategy.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.competitive_service import get_competitive_service

router = APIRouter()


class FocusType(str, Enum):
    """Competitive intelligence focus type."""
    LANDSCAPE = "landscape"
    BENCHMARKING = "benchmarking"
    BATTLE_CARD = "battle_card"


class CompetitivePosition(str, Enum):
    """Overall competitive position."""
    STRONG = "STRONG"
    COMPETITIVE = "COMPETITIVE"
    DEVELOPING = "DEVELOPING"


class QuickStat(BaseModel):
    """Quick stat for battle card."""
    stat: str = Field(..., description="Statistic name")
    value: str = Field(..., description="Formatted value")
    context: str = Field(..., description="Context or comparison")


class Differentiator(BaseModel):
    """Competitive differentiator."""
    category: str = Field(..., description="Category of differentiator")
    differentiator: str = Field(..., description="Key differentiator statement")
    evidence: str = Field(..., description="Supporting evidence")


class Rebuttal(BaseModel):
    """Objection and rebuttal pair."""
    objection: str = Field(..., description="Customer objection")
    rebuttal: str = Field(..., description="Evidence-based rebuttal")


class RegistryComparison(BaseModel):
    """Registry comparison entry."""
    registry: str = Field(..., description="Registry abbreviation")
    metric: str = Field(..., description="Metric name")
    registry_value: Optional[float] = Field(None, description="Registry benchmark value")
    comparison: Optional[str] = Field(None, description="Comparison result")


class OverallPosition(BaseModel):
    """Overall competitive position summary."""
    position: CompetitivePosition = Field(..., description="Position classification")
    description: str = Field(..., description="Position description")
    favorable_metrics: int = Field(default=0, description="Number of favorable metrics")
    total_metrics: int = Field(default=0, description="Total metrics compared")


class CompetitiveLandscapeResponse(BaseModel):
    """Competitive landscape report response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Type of report generated")
    generated_at: str = Field(..., description="Generation timestamp")
    study_metrics: Dict[str, Any] = Field(default_factory=dict, description="Study performance metrics")
    competitive_landscape: Optional[str] = Field(None, description="AI-generated landscape narrative")
    registry_comparison: List[Dict[str, Any]] = Field(default_factory=list, description="Registry comparisons")
    literature_benchmarks: Dict[str, Any] = Field(default_factory=dict, description="Literature benchmark summary")
    key_differentiators: List[Dict[str, Any]] = Field(default_factory=list, description="Key competitive differentiators")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.85, description="Confidence score")


class BenchmarkingResponse(BaseModel):
    """Competitive benchmarking response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Type of report generated")
    generated_at: str = Field(..., description="Generation timestamp")
    study_metrics: Dict[str, Any] = Field(default_factory=dict, description="Study performance metrics")
    registry_benchmarks: Dict[str, Any] = Field(default_factory=dict, description="Registry benchmark comparisons")
    literature_comparison: List[Dict[str, Any]] = Field(default_factory=list, description="Literature comparisons")
    overall_position: Dict[str, Any] = Field(default_factory=dict, description="Overall competitive position")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.88, description="Confidence score")


class BattleCardResponse(BaseModel):
    """Battle card response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Type of report generated")
    generated_at: str = Field(..., description="Generation timestamp")
    product: str = Field(..., description="Product name")
    battle_card_content: Optional[str] = Field(None, description="AI-generated battle card content")
    quick_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Quick statistics")
    talking_points: List[str] = Field(default_factory=list, description="Key talking points")
    rebuttals: List[Dict[str, Any]] = Field(default_factory=list, description="Objection/rebuttal pairs")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.82, description="Confidence score")


@router.get("/competitive-intelligence", response_model=CompetitiveLandscapeResponse)
async def get_competitive_intelligence(
    focus: FocusType = Query(
        FocusType.LANDSCAPE,
        description="Report focus: landscape, benchmarking, or battle_card"
    )
) -> CompetitiveLandscapeResponse:
    """
    Get comprehensive competitive intelligence report.

    Analyzes DELTA Revision Cup performance against:
    - International registry benchmarks (AOANJRR, NJR, SHAR, AJRR, CJRR)
    - Published literature benchmarks
    - Industry performance standards

    Focus types:
    - **landscape**: Full competitive landscape analysis
    - **benchmarking**: Focused metric-by-metric comparison
    - **battle_card**: Sales-ready battle card with talking points
    """
    service = get_competitive_service()
    result = await service.get_competitive_intelligence(focus=focus.value)

    return CompetitiveLandscapeResponse(**result)


@router.get("/landscape", response_model=CompetitiveLandscapeResponse)
async def get_landscape() -> CompetitiveLandscapeResponse:
    """
    Get competitive landscape analysis.

    Provides comprehensive market positioning analysis including:
    - Market position summary
    - Registry-by-registry comparison
    - Key differentiators
    - Competitive vulnerabilities
    """
    service = get_competitive_service()
    result = await service.get_competitive_intelligence(focus="landscape")

    return CompetitiveLandscapeResponse(**result)


@router.get("/benchmarking", response_model=BenchmarkingResponse)
async def get_benchmarking() -> BenchmarkingResponse:
    """
    Get competitive benchmarking report.

    Provides metric-by-metric comparison against:
    - 5 international orthopedic registries
    - Published literature benchmarks

    Shows favorable/unfavorable comparisons for each metric.
    """
    service = get_competitive_service()
    result = await service.get_competitive_intelligence(focus="benchmarking")

    return BenchmarkingResponse(**result)


@router.get("/battle-card", response_model=BattleCardResponse)
async def get_battle_card() -> BattleCardResponse:
    """
    Generate sales battle card.

    Creates a sales-ready battle card including:
    - Quick facts and statistics
    - Key talking points with evidence
    - Competitive positioning statements
    - Objection handlers with data-backed rebuttals
    - Value proposition statement
    """
    service = get_competitive_service()
    result = await service.get_competitive_intelligence(focus="battle_card")

    return BattleCardResponse(**result)


@router.get("/differentiators")
async def get_differentiators() -> Dict[str, Any]:
    """
    Get key competitive differentiators.

    Returns evidence-based differentiators derived from:
    - Registry benchmark comparisons
    - Literature performance data
    - Product technology advantages
    """
    service = get_competitive_service()
    result = await service.get_competitive_intelligence(focus="landscape")

    return {
        "success": result.get("success", False),
        "generated_at": datetime.utcnow().isoformat(),
        "product": "DELTA Revision Cup",
        "differentiators": result.get("key_differentiators", []),
        "sources": result.get("sources", []),
    }


@router.get("/talking-points")
async def get_talking_points() -> Dict[str, Any]:
    """
    Get sales talking points.

    Returns evidence-based talking points suitable for:
    - Surgeon meetings
    - Conference presentations
    - Marketing materials
    """
    service = get_competitive_service()
    result = await service.get_competitive_intelligence(focus="battle_card")

    return {
        "success": result.get("success", False),
        "generated_at": datetime.utcnow().isoformat(),
        "product": "DELTA Revision Cup",
        "talking_points": result.get("talking_points", []),
        "quick_stats": result.get("quick_stats", []),
        "sources": result.get("sources", []),
    }
