"""
UC6: Regulatory Narrative Generator API.
Generates regulatory-grade narratives for submission documents.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.regulatory_service import get_regulatory_service

router = APIRouter()


class NarrativeType(str, Enum):
    """Regulatory narrative type."""
    SAFETY_SUMMARY = "safety_summary"
    EFFICACY_SUMMARY = "efficacy_summary"
    RISK_BENEFIT = "risk_benefit"


class RiskBenefitDetermination(str, Enum):
    """Risk-benefit determination."""
    FAVORABLE = "FAVORABLE"
    ACCEPTABLE = "ACCEPTABLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class RegulatoryContext(BaseModel):
    """Regulatory context for narrative."""
    suitable_for: List[str] = Field(default_factory=list, description="Suitable regulatory pathways")
    document_type: str = Field(..., description="Document type")


class SafetyData(BaseModel):
    """Safety data summary."""
    n_patients: int = Field(default=0, description="Number of patients analyzed")
    n_signals: int = Field(default=0, description="Number of safety signals")
    overall_status: Optional[str] = Field(None, description="Overall safety status")
    metrics: List[Dict[str, Any]] = Field(default_factory=list, description="Safety metrics")


class EfficacyData(BaseModel):
    """Efficacy data summary."""
    primary_endpoint: str = Field(..., description="Primary efficacy endpoint")
    survival_rate: float = Field(..., description="Implant survival rate")
    revision_rate: float = Field(..., description="Revision rate")
    hhs_improvement: float = Field(..., description="Harris Hip Score improvement")
    mcid_achievement: float = Field(..., description="MCID achievement rate")


class RegulatoryNarrativeResponse(BaseModel):
    """Regulatory narrative response."""
    success: bool = Field(..., description="Request success status")
    narrative_type: str = Field(..., description="Type of narrative generated")
    generated_at: str = Field(..., description="Generation timestamp")
    executive_summary: Optional[str] = Field(None, description="Executive summary")
    narrative: Optional[str] = Field(None, description="Full regulatory narrative")
    safety_data: Optional[Dict[str, Any]] = Field(None, description="Safety data if applicable")
    efficacy_data: Optional[Dict[str, Any]] = Field(None, description="Efficacy data if applicable")
    benchmarks: Dict[str, Any] = Field(default_factory=dict, description="Benchmark comparisons")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.85, description="Confidence score")
    regulatory_context: Dict[str, Any] = Field(default_factory=dict, description="Regulatory context")


class RiskBenefitResponse(BaseModel):
    """Risk-benefit analysis response."""
    success: bool = Field(..., description="Request success status")
    narrative_type: str = Field(..., description="Type of narrative")
    generated_at: str = Field(..., description="Generation timestamp")
    executive_summary: Optional[str] = Field(None, description="Executive summary")
    narrative: Optional[str] = Field(None, description="Risk-benefit narrative")
    components: Dict[str, Any] = Field(default_factory=dict, description="Component summaries")
    risk_benefit_determination: Dict[str, Any] = Field(default_factory=dict, description="Determination")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.85, description="Confidence score")
    regulatory_context: Dict[str, Any] = Field(default_factory=dict, description="Regulatory context")


@router.post("/regulatory-narrative", response_model=RegulatoryNarrativeResponse)
async def generate_regulatory_narrative(
    narrative_type: NarrativeType = Query(
        NarrativeType.SAFETY_SUMMARY,
        description="Type of regulatory narrative to generate"
    )
) -> RegulatoryNarrativeResponse:
    """
    Generate a regulatory-grade narrative.

    Creates formal narratives suitable for regulatory submission including:
    - **safety_summary**: Safety profile summary for PMA/510(k)/CE submission
    - **efficacy_summary**: Efficacy outcomes summary
    - **risk_benefit**: Combined risk-benefit analysis

    All narratives include:
    - Evidence from study data
    - Comparison to registry benchmarks
    - Comparison to literature benchmarks
    - Full source provenance
    """
    service = get_regulatory_service()
    result = await service.generate_narrative(narrative_type=narrative_type.value)

    return RegulatoryNarrativeResponse(**result)


@router.get("/safety-summary", response_model=RegulatoryNarrativeResponse)
async def get_safety_summary() -> RegulatoryNarrativeResponse:
    """
    Generate safety summary narrative.

    Creates a formal safety summary including:
    - Overall safety profile assessment
    - Adverse event analysis with rates
    - Comparison to protocol thresholds
    - Comparison to registry and literature benchmarks
    - Safety conclusions

    Suitable for: FDA PMA, FDA 510(k), CE Mark Technical File, PMCF Report
    """
    service = get_regulatory_service()
    result = await service.generate_narrative(narrative_type="safety_summary")

    return RegulatoryNarrativeResponse(**result)


@router.get("/efficacy-summary", response_model=RegulatoryNarrativeResponse)
async def get_efficacy_summary() -> RegulatoryNarrativeResponse:
    """
    Generate efficacy summary narrative.

    Creates a formal efficacy summary including:
    - Primary endpoint analysis
    - Secondary endpoint results
    - Functional outcome measures
    - Comparative efficacy assessment
    - Efficacy conclusions

    Suitable for: FDA PMA, FDA 510(k), CE Mark Technical File, PMCF Report
    """
    service = get_regulatory_service()
    result = await service.generate_narrative(narrative_type="efficacy_summary")

    return RegulatoryNarrativeResponse(**result)


@router.get("/risk-benefit", response_model=RiskBenefitResponse)
async def get_risk_benefit_analysis() -> RiskBenefitResponse:
    """
    Generate risk-benefit analysis.

    Creates a comprehensive risk-benefit analysis combining:
    - Safety summary findings
    - Efficacy summary findings
    - Benefit-risk weighing
    - Overall determination

    Suitable for: FDA PMA, CE Mark Clinical Evaluation Report
    """
    service = get_regulatory_service()
    result = await service.generate_narrative(narrative_type="risk_benefit")

    return RiskBenefitResponse(**result)


@router.get("/narrative-types")
async def get_narrative_types() -> Dict[str, Any]:
    """
    Get available regulatory narrative types.

    Returns list of narrative types with descriptions and suitable regulatory pathways.
    """
    return {
        "available_types": [
            {
                "type": "safety_summary",
                "description": "Safety profile summary with adverse event analysis",
                "suitable_for": ["FDA PMA", "FDA 510(k)", "CE Mark Technical File", "PMCF Report"],
            },
            {
                "type": "efficacy_summary",
                "description": "Efficacy outcomes summary with functional measures",
                "suitable_for": ["FDA PMA", "FDA 510(k)", "CE Mark Technical File", "PMCF Report"],
            },
            {
                "type": "risk_benefit",
                "description": "Combined risk-benefit analysis",
                "suitable_for": ["FDA PMA", "CE Mark Clinical Evaluation Report"],
            },
        ],
        "default_type": "safety_summary",
    }
