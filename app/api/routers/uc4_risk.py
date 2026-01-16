"""
UC4: Patient Risk Stratification with Actionable Monitoring API.
ML + Literature + Registry producing prioritized surveillance lists.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from app.services.risk_service import get_risk_service
from app.services.cache_service import get_cache_service

router = APIRouter()


class RiskLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class ContributingFactor(BaseModel):
    """A contributing risk factor."""
    factor: str = Field(..., description="Risk factor name")
    hazard_ratio: float = Field(..., description="Hazard ratio from literature")
    contribution: float = Field(..., description="Contribution to risk score")


class Recommendation(BaseModel):
    """Clinical recommendation based on risk."""
    action: str = Field(..., description="Recommended action")
    rationale: str = Field(..., description="Reason for recommendation")
    priority: str = Field(..., description="Priority level")


class PatientRiskResponse(BaseModel):
    """Patient risk assessment response."""
    success: bool = Field(..., description="Request success status")
    patient_id: str = Field(..., description="Patient identifier")
    assessment_date: Optional[str] = Field(None, description="Assessment timestamp")
    risk_score: float = Field(..., description="Risk score (0-1)")
    risk_level: RiskLevel = Field(..., description="Risk classification")
    combined_hazard_ratio: float = Field(..., description="Combined hazard ratio")
    n_risk_factors: int = Field(..., description="Number of risk factors present")
    contributing_factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    narrative: Optional[str] = Field(None, description="AI-generated narrative")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)


class PatientRiskDetail(BaseModel):
    """Detailed risk information for a patient."""
    patient_id: str = Field(..., description="Patient identifier")
    risk_score: float = Field(..., description="Risk score 0-1")
    clinical_risk_score: Optional[float] = Field(None, description="Clinical (HR-based) risk score")
    demographic_risk_score: Optional[float] = Field(None, description="ML demographic risk score")
    n_risk_factors: int = Field(..., description="Number of clinical risk factors")
    n_demographic_factors: Optional[int] = Field(None, description="Number of demographic factors")
    contributing_factors: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Clinical risk factors with hazard ratios")
    demographic_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Demographic factors (age, BMI, gender)")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)


class FactorPrevalence(BaseModel):
    """Risk factor prevalence in population."""
    factor: str = Field(..., description="Factor name")
    count: int = Field(..., description="Number of patients with factor")
    percentage: float = Field(..., description="Percentage of population")
    hazard_ratio: float = Field(..., description="Hazard ratio from literature")


class PopulationRiskResponse(BaseModel):
    """Population risk distribution response."""
    success: bool = Field(..., description="Request success status")
    assessment_date: str = Field(..., description="Assessment timestamp")
    n_patients: int = Field(..., description="Total patients analyzed")
    risk_distribution: Dict[str, int] = Field(..., description="Count by risk level")
    high_risk_patients: List[PatientRiskDetail] = Field(default_factory=list)
    moderate_risk_patients: List[PatientRiskDetail] = Field(default_factory=list)
    low_risk_patients: List[PatientRiskDetail] = Field(default_factory=list)
    high_risk_count: int = Field(default=0, description="Count of high risk patients")
    moderate_risk_count: int = Field(default=0, description="Count of moderate risk patients")
    low_risk_count: int = Field(default=0, description="Count of low risk patients")
    high_risk_pct: float = Field(default=0.0, description="Percentage of high risk patients")
    factor_prevalence: List[FactorPrevalence] = Field(default_factory=list)
    mean_risk_score: float = Field(..., description="Mean risk score")
    median_risk_score: Optional[float] = Field(None, description="Median risk score")
    std_risk_score: Optional[float] = Field(None, description="Standard deviation")
    note: Optional[str] = Field(None)


class RiskFactorsResponse(BaseModel):
    """Risk factors reference response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Generation timestamp")
    model_factors: List[Dict[str, Any]] = Field(..., description="Model hazard ratios")
    literature_factors: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class RiskCalculationRequest(BaseModel):
    """Request for ad-hoc risk calculation."""
    age_over_80: bool = Field(default=False)
    bmi_over_35: bool = Field(default=False)
    diabetes: bool = Field(default=False)
    osteoporosis: bool = Field(default=False)
    rheumatoid_arthritis: bool = Field(default=False)
    chronic_kidney_disease: bool = Field(default=False)
    smoking: bool = Field(default=False)
    prior_revision: bool = Field(default=False)
    severe_bone_loss: bool = Field(default=False)
    paprosky_3b: bool = Field(default=False)


class RiskCalculationResponse(BaseModel):
    """Risk calculation response."""
    success: bool = Field(..., description="Request success status")
    calculated_at: str = Field(..., description="Calculation timestamp")
    input_features: Dict[str, bool] = Field(..., description="Input features")
    risk_score: float = Field(..., description="Calculated risk score")
    risk_level: RiskLevel = Field(..., description="Risk classification")
    combined_hazard_ratio: float = Field(..., description="Combined HR")
    n_risk_factors: int = Field(..., description="Number of risk factors")
    contributing_factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("/risk/patient/{patient_id}", response_model=PatientRiskResponse)
async def get_patient_risk(patient_id: str) -> PatientRiskResponse:
    """
    Get comprehensive risk assessment for a patient.

    Combines:
    - ML model predictions using literature hazard ratios
    - Patient-specific risk factors
    - Literature context for risk interpretation

    Returns risk score with explainability and recommendations.
    """
    service = get_risk_service()
    result = await service.get_patient_risk(patient_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", f"Could not assess risk for patient {patient_id}")
        )

    return PatientRiskResponse(**result)


@router.get("/risk/population", response_model=PopulationRiskResponse)
async def get_population_risk() -> PopulationRiskResponse:
    """
    Get risk distribution across the study population.

    Returns aggregate statistics on risk stratification
    across all enrolled patients.
    """
    # Check cache first
    cache = get_cache_service()
    cached = await cache.get("risk-population")
    if cached and not cached.get("is_stale"):
        return PopulationRiskResponse(**cached["data"])

    # Cache miss - compute and cache result
    service = get_risk_service()
    result = await service.get_population_risk()
    await cache.set("risk-population", result)

    return PopulationRiskResponse(**result)


@router.get("/risk/factors", response_model=RiskFactorsResponse)
async def get_risk_factors() -> RiskFactorsResponse:
    """
    Get all risk factors used in the stratification model.

    Returns literature-derived hazard ratios and sources
    for each risk factor in the model.
    """
    # Check cache first (risk factors are static)
    cache = get_cache_service()
    cached = await cache.get("risk-factors")
    if cached and not cached.get("is_stale"):
        return RiskFactorsResponse(**cached["data"])

    service = get_risk_service()
    result = await service.get_risk_factors()
    await cache.set("risk-factors", result)

    return RiskFactorsResponse(**result)


@router.post("/risk/calculate", response_model=RiskCalculationResponse)
async def calculate_risk(
    features: RiskCalculationRequest = Body(...)
) -> RiskCalculationResponse:
    """
    Calculate risk score for a set of features.

    Provide risk factor presence to get instant risk calculation
    without patient lookup. Useful for hypothetical scenarios.
    """
    service = get_risk_service()
    result = await service.calculate_risk(features.model_dump())

    return RiskCalculationResponse(**result)


@router.get("/risk/high-priority")
async def get_high_priority_patients() -> Dict[str, Any]:
    """
    Get prioritized list of high-risk patients requiring attention.

    Returns patients ranked by risk score with recommended actions.
    """
    service = get_risk_service()

    # Get model hazard ratios for reference
    model = service._risk_model

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "model_version": "v1.0",
        "hazard_ratio_threshold": 2.0,
        "priority_factors": [
            {
                "factor": factor,
                "hazard_ratio": hr,
                "priority": "high" if hr >= 2.0 else "medium"
            }
            for factor, hr in sorted(
                model.HAZARD_RATIOS.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ],
        "note": "Patient-level priority requires population data analysis"
    }


@router.get("/risk/summary")
async def get_risk_summary() -> Dict[str, Any]:
    """
    Get summary of risk model and stratification.

    Returns model configuration and key thresholds.
    """
    service = get_risk_service()
    model = service._risk_model

    # Get risk factors with full provenance
    risk_factors_result = await service.get_risk_factors()

    # Extract unique literature sources from model factors
    literature_sources = list(set(
        f.get("source", "literature_aggregate")
        for f in risk_factors_result.get("model_factors", [])
    ))

    return {
        "success": True,
        "generated_at": datetime.utcnow().isoformat(),
        "model_version": "v1.0",
        "n_risk_factors": len(model.HAZARD_RATIOS),
        "risk_thresholds": {
            "high": "score >= 0.6",
            "moderate": "0.3 <= score < 0.6",
            "low": "score < 0.3"
        },
        "hazard_ratios": model.HAZARD_RATIOS,
        "literature_sources": literature_sources,
        "sources": risk_factors_result.get("sources", []),
    }


@router.get("/risk/hazard-ratio/{factor}")
async def get_hazard_ratio(factor: str) -> Dict[str, Any]:
    """
    Get hazard ratio for a specific risk factor.

    Args:
        factor: Risk factor name (e.g., osteoporosis, diabetes)
    """
    service = get_risk_service()
    hr = service.get_hazard_ratio(factor)

    if hr is None:
        raise HTTPException(
            status_code=404,
            detail=f"Risk factor '{factor}' not found in model"
        )

    return {
        "factor": factor,
        "hazard_ratio": hr,
        "interpretation": f"{hr}x increased risk compared to baseline",
        "source": "literature_aggregate"
    }
