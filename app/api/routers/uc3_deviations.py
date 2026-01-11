"""
UC3: Automated Protocol Deviation Detection API.
Document-as-Code execution detecting and classifying deviations in real-time.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.deviations_service import get_deviations_service

router = APIRouter()


class DeviationSeverity(str, Enum):
    """Deviation severity classification."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class DeviationType(str, Enum):
    """Type of protocol deviation."""
    VISIT_TIMING = "visit_timing"
    MISSING_ASSESSMENT = "missing_assessment"
    ELIGIBILITY = "eligibility"
    PROCEDURE = "procedure"


class ProtocolDeviation(BaseModel):
    """A detected protocol deviation."""
    patient_id: str = Field(..., description="Affected patient ID")
    visit_id: str = Field(..., description="Visit where deviation occurred")
    visit_name: Optional[str] = Field(None, description="Visit display name")
    deviation_type: str = Field(default="visit_timing", description="Type of deviation")
    classification: DeviationSeverity = Field(..., description="Severity classification")
    actual_day: Optional[int] = Field(None, description="Actual day from surgery")
    target_day: Optional[int] = Field(None, description="Target day per protocol")
    deviation_days: Optional[int] = Field(None, description="Days outside window")
    allowed_range: Optional[List[int]] = Field(None, description="Allowed day range")
    action: str = Field(..., description="Required action")
    requires_explanation: bool = Field(default=False, description="Requires PI explanation")
    affects_evaluability: bool = Field(default=False, description="Affects patient evaluability")


class DeviationSummaryResponse(BaseModel):
    """Summary of protocol deviations."""
    success: bool = Field(..., description="Request success status")
    assessment_date: str = Field(..., description="Assessment timestamp")
    total_visits: int = Field(default=0, description="Total visits assessed")
    total_deviations: int = Field(default=0, description="Total deviations detected")
    deviation_rate: float = Field(default=0.0, description="Deviation rate")
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_visit: Dict[str, int] = Field(default_factory=dict)
    protocol_version: Optional[str] = Field(None, description="Protocol version")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0, description="Execution time")


class PatientDeviationsResponse(BaseModel):
    """Patient-specific deviation response."""
    success: bool = Field(..., description="Request success status")
    patient_id: str = Field(..., description="Patient identifier")
    assessment_date: Optional[str] = Field(None, description="Assessment timestamp")
    n_visits: int = Field(default=0, description="Number of visits")
    n_deviations: int = Field(default=0, description="Number of deviations")
    compliance_rate: float = Field(default=1.0, description="Compliance rate")
    deviations: List[Dict[str, Any]] = Field(default_factory=list)
    deviation_summary: Dict[str, Any] = Field(default_factory=dict)
    missing_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    narrative: Optional[str] = Field(None, description="AI-generated narrative")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)


class VisitComplianceResponse(BaseModel):
    """Visit compliance check response."""
    success: bool = Field(..., description="Request success status")
    patient_id: str = Field(..., description="Patient identifier")
    visit_id: str = Field(..., description="Visit identifier")
    visit_name: Optional[str] = Field(None, description="Visit display name")
    actual_day: int = Field(..., description="Actual day of visit")
    target_day: Optional[int] = Field(None, description="Target day per protocol")
    allowed_range: Optional[List[int]] = Field(None, description="Allowed day range")
    is_compliant: bool = Field(..., description="Whether visit is compliant")
    deviation: Optional[Dict[str, Any]] = Field(None, description="Deviation details if non-compliant")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)


class VisitWindowsResponse(BaseModel):
    """Protocol visit windows response."""
    protocol_id: str = Field(..., description="Protocol identifier")
    protocol_version: str = Field(..., description="Protocol version")
    reference_point: str = Field(default="surgery_date", description="Day 0 reference")
    windows: List[Dict[str, Any]] = Field(..., description="Visit window definitions")
    deviation_classification: Dict[str, Any] = Field(..., description="Classification rules")


class ComplianceRateResponse(BaseModel):
    """Compliance rate response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Generation timestamp")
    overall_compliance_pct: float = Field(..., description="Overall compliance percentage")
    by_visit: List[Dict[str, Any]] = Field(..., description="Compliance by visit type")
    by_severity: Dict[str, int] = Field(default_factory=dict)
    total_visits: int = Field(default=0)
    total_deviations: int = Field(default=0)


@router.get("/deviations/summary", response_model=DeviationSummaryResponse)
async def get_deviation_summary() -> DeviationSummaryResponse:
    """
    Get summary of all detected protocol deviations.

    Uses Document-as-Code protocol rules to validate:
    - Visit timing windows
    - Required assessments
    - Protocol compliance
    """
    service = get_deviations_service()
    result = await service.get_study_deviations()

    return DeviationSummaryResponse(**result)


@router.get("/deviations/patient/{patient_id}", response_model=PatientDeviationsResponse)
async def get_patient_deviations(patient_id: str) -> PatientDeviationsResponse:
    """
    Get all protocol deviations for a specific patient.

    Returns:
    - List of deviations with classification
    - Missing assessments
    - AI-generated narrative with recommendations
    """
    service = get_deviations_service()
    result = await service.get_patient_deviations(patient_id)

    return PatientDeviationsResponse(**result)


@router.get("/deviations/check-visit", response_model=VisitComplianceResponse)
async def check_visit_compliance(
    patient_id: str = Query(..., description="Patient identifier"),
    visit_id: str = Query(..., description="Visit identifier (e.g., fu_6mo)"),
    actual_day: int = Query(..., description="Actual day of visit from surgery"),
) -> VisitComplianceResponse:
    """
    Check if a specific visit is compliant with protocol windows.

    Args:
        patient_id: Patient identifier
        visit_id: Visit identifier (screening, preoperative, surgery, discharge, fu_2mo, fu_6mo, fu_1yr, fu_2yr)
        actual_day: Actual day of visit (relative to surgery = day 0)

    Returns:
        Compliance status with deviation details if non-compliant
    """
    service = get_deviations_service()
    result = await service.check_visit_compliance(patient_id, visit_id, actual_day)

    return VisitComplianceResponse(**result)


@router.get("/deviations/visit-windows", response_model=VisitWindowsResponse)
async def get_visit_windows() -> VisitWindowsResponse:
    """
    Get protocol-defined visit windows (Document-as-Code).

    Returns the complete schedule of assessments with allowed windows
    and deviation classification rules.
    """
    service = get_deviations_service()
    result = service.get_visit_windows()

    return VisitWindowsResponse(**result)


@router.get("/deviations/compliance-rate", response_model=ComplianceRateResponse)
async def get_compliance_rate() -> ComplianceRateResponse:
    """
    Get overall protocol compliance rate by visit type.

    Returns compliance percentages for each visit in the protocol
    and overall study compliance.
    """
    service = get_deviations_service()
    result = await service.get_compliance_rate()

    return ComplianceRateResponse(**result)


@router.get("/deviations/classification-rules")
async def get_classification_rules() -> Dict[str, Any]:
    """
    Get protocol-defined deviation classification rules.

    Returns the Document-as-Code rules for classifying deviations
    as minor, major, or critical.
    """
    service = get_deviations_service()
    return service.get_deviation_classification_rules()
