"""
UC2: Safety Signal Detection & Contextualization API.
Cross-source signal correlation with literature-grounded risk interpretation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.safety_service import get_safety_service

router = APIRouter()


class SignalStatus(str, Enum):
    """Signal status classification."""
    ELEVATED = "ELEVATED"
    NORMAL = "NORMAL"
    LOW = "LOW"


class SignalLevel(str, Enum):
    """Signal priority level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SafetyMetric(BaseModel):
    """A single safety metric with thresholds."""
    metric: str = Field(..., description="Name of the safety metric")
    rate: float = Field(..., description="Rate observed in study")
    count: int = Field(default=0, description="Event count")
    total: int = Field(default=0, description="Total patients")
    threshold: float = Field(..., description="Protocol threshold")
    signal: bool = Field(default=False, description="Whether threshold is exceeded")
    threshold_exceeded_by: float = Field(default=0.0, description="Amount by which threshold exceeded")


class RiskFactor(BaseModel):
    """Literature-derived risk factor."""
    factor: str = Field(..., description="Risk factor name")
    hazard_ratio: float = Field(..., description="Hazard ratio from literature")
    confidence_interval: Optional[List[float]] = Field(None, description="95% CI")
    source: str = Field(..., description="Literature source")


class SafetySignal(BaseModel):
    """Detected safety signal."""
    metric: str = Field(..., description="Metric with signal")
    rate: float = Field(..., description="Observed rate")
    threshold: float = Field(..., description="Threshold exceeded")
    signal_level: SignalLevel = Field(..., description="Priority level")
    recommended_action: str = Field(..., description="Recommended action")


class SafetySummaryResponse(BaseModel):
    """Comprehensive safety summary response."""
    success: bool = Field(..., description="Request success status")
    assessment_date: str = Field(..., description="Assessment timestamp")
    n_patients: int = Field(default=0, description="Total patients analyzed")
    overall_status: str = Field(..., description="Overall safety status")
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    n_signals: int = Field(default=0, description="Number of signals detected")
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    registry_comparison: Dict[str, Any] = Field(default_factory=dict)
    literature_benchmarks: Dict[str, Any] = Field(default_factory=dict)
    narrative: Optional[str] = Field(None, description="AI-generated narrative")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.9, description="Confidence in assessment")
    execution_time_ms: float = Field(default=0.0)


class PatientSafetyResponse(BaseModel):
    """Patient-specific safety response."""
    success: bool = Field(..., description="Request success status")
    patient_id: str = Field(..., description="Patient identifier")
    assessment_date: Optional[str] = Field(None, description="Assessment timestamp")
    adverse_events: List[Dict[str, Any]] = Field(default_factory=list)
    n_adverse_events: int = Field(default=0)
    has_sae: bool = Field(default=False, description="Has serious adverse event")
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    risk_level: str = Field(default="low", description="Overall risk level")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)


class SignalDetectionResponse(BaseModel):
    """Signal detection response."""
    success: bool = Field(..., description="Request success status")
    detection_date: str = Field(..., description="Detection timestamp")
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    n_signals: int = Field(default=0)
    high_priority: List[Dict[str, Any]] = Field(default_factory=list)
    medium_priority: List[Dict[str, Any]] = Field(default_factory=list)
    requires_dsmb_review: bool = Field(default=False)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)


class BenchmarkComparisonResponse(BaseModel):
    """Benchmark comparison response."""
    success: bool = Field(..., description="Request success status")
    comparison_date: str = Field(..., description="Comparison timestamp")
    input_metrics: Dict[str, float] = Field(..., description="Input metrics")
    comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class ThresholdsResponse(BaseModel):
    """Safety thresholds response."""
    protocol_thresholds: Dict[str, float] = Field(..., description="Protocol-defined thresholds")
    registry_concern_thresholds: Dict[str, float] = Field(..., description="Registry concern thresholds")
    registry_risk_thresholds: Dict[str, float] = Field(..., description="Registry risk thresholds")
    protocol_version: str = Field(..., description="Protocol version")


@router.get("/safety/overview", response_model=SafetySummaryResponse)
async def get_safety_overview() -> SafetySummaryResponse:
    """
    Get comprehensive safety signal overview with contextualization.

    Compares study AE rates against:
    - Protocol-defined thresholds
    - Literature benchmarks
    - Registry population norms

    Returns AI-generated narrative with provenance.
    """
    service = get_safety_service()
    result = await service.get_safety_summary()

    return SafetySummaryResponse(**result)


@router.get("/safety/patient/{patient_id}", response_model=PatientSafetyResponse)
async def get_patient_safety(patient_id: str) -> PatientSafetyResponse:
    """
    Get safety analysis for a specific patient.

    Returns:
    - Adverse events for the patient
    - Identified risk factors with hazard ratios
    - Overall risk level
    """
    service = get_safety_service()
    result = await service.get_patient_safety(patient_id)

    return PatientSafetyResponse(**result)


@router.get("/safety/signals", response_model=SignalDetectionResponse)
async def get_safety_signals() -> SignalDetectionResponse:
    """
    Detect and classify safety signals.

    Returns prioritized list of signals with:
    - Signal level (high/medium/low)
    - Recommended actions
    - DSMB review requirements
    """
    service = get_safety_service()
    result = await service.detect_signals()

    return SignalDetectionResponse(**result)


@router.get("/safety/compare-benchmarks", response_model=BenchmarkComparisonResponse)
async def compare_to_benchmarks(
    revision_rate: Optional[float] = Query(None, description="Revision rate to compare"),
    dislocation_rate: Optional[float] = Query(None, description="Dislocation rate to compare"),
    infection_rate: Optional[float] = Query(None, description="Infection rate to compare"),
    fracture_rate: Optional[float] = Query(None, description="Fracture rate to compare"),
) -> BenchmarkComparisonResponse:
    """
    Compare study metrics to literature and registry benchmarks.

    Provide one or more rates to compare against published benchmarks.
    """
    metrics = {}
    if revision_rate is not None:
        metrics["revision_rate"] = revision_rate
    if dislocation_rate is not None:
        metrics["dislocation_rate"] = dislocation_rate
    if infection_rate is not None:
        metrics["infection_rate"] = infection_rate
    if fracture_rate is not None:
        metrics["fracture_rate"] = fracture_rate

    if not metrics:
        raise HTTPException(status_code=400, detail="At least one rate must be provided")

    service = get_safety_service()
    result = await service.compare_to_benchmarks(metrics)

    return BenchmarkComparisonResponse(**result)


@router.get("/safety/thresholds", response_model=ThresholdsResponse)
async def get_thresholds() -> ThresholdsResponse:
    """
    Get protocol and registry safety thresholds.

    Returns thresholds from:
    - Protocol-defined safety monitoring rules
    - Registry concern and risk thresholds
    """
    service = get_safety_service()
    result = service.get_thresholds()

    return ThresholdsResponse(**result)


@router.get("/safety/adverse-events")
async def get_adverse_events_summary() -> Dict[str, Any]:
    """
    Get summary of all adverse events with classification.

    Returns counts by type, severity, and relationship.
    """
    service = get_safety_service()
    result = await service.get_adverse_event_summary()

    return result


@router.get("/safety/metrics")
async def get_safety_metrics() -> Dict[str, Any]:
    """
    Get current safety metrics with thresholds.

    Returns individual metrics showing rate vs threshold.
    """
    service = get_safety_service()
    summary = await service.get_safety_summary()

    return {
        "success": summary.get("success", False),
        "generated_at": datetime.utcnow().isoformat(),
        "n_patients": summary.get("n_patients", 0),
        "metrics": summary.get("metrics", []),
    }
