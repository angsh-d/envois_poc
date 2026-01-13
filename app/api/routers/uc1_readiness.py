"""
UC1: Regulatory Submission Readiness Assessment API.
Multi-source gap analysis producing actionable remediation checklist.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.readiness_service import get_readiness_service

router = APIRouter()


class EnrollmentStatus(BaseModel):
    """Enrollment status."""
    enrolled: int = Field(..., description="Current enrolled count")
    target: int = Field(..., description="Target enrollment")
    interim_target: int = Field(..., description="Interim analysis target")
    percent_complete: float = Field(..., description="Percent of target enrolled")
    status: str = Field(..., description="Enrollment status")
    is_ready: bool = Field(..., description="Meets enrollment requirement")


class ComplianceStatus(BaseModel):
    """Compliance status."""
    deviation_rate: float = Field(..., description="Deviation rate percentage")
    by_severity: Dict[str, int] = Field(default_factory=dict)
    status: str = Field(..., description="Compliance status")
    is_ready: bool = Field(..., description="Meets compliance requirement")


class SafetyStatus(BaseModel):
    """Safety status."""
    n_signals: int = Field(default=0, description="Number of safety signals")
    overall_status: str = Field(..., description="Overall safety status")
    is_ready: bool = Field(..., description="Meets safety requirement")


class DataCompletenessStatus(BaseModel):
    """Data completeness status."""
    enrolled: int = Field(..., description="Total enrolled")
    completed: int = Field(..., description="Completed study")
    withdrawn: int = Field(..., description="Withdrawn")
    evaluable: int = Field(..., description="Evaluable patients")
    completion_rate: float = Field(..., description="Completion rate percentage")
    is_ready: bool = Field(..., description="Meets completeness requirement")


class SafetySignalDetail(BaseModel):
    """Detail of a detected safety signal."""
    metric: str = Field(..., description="Signal metric name")
    observed_rate: str = Field(..., description="Observed rate as percentage string")
    threshold: str = Field(..., description="Threshold as percentage string")
    calculation: str = Field(..., description="Calculation formula")
    exceeded_by: str = Field(..., description="Amount exceeded threshold")


class BlockingIssueProvenance(BaseModel):
    """Full provenance for a blocking issue - supports regulatory defensibility."""
    calculation: Optional[str] = Field(None, description="How the value was calculated")
    values: Optional[Dict[str, Any]] = Field(None, description="Raw data values used")
    threshold: Optional[str] = Field(None, description="Single threshold description")
    thresholds: Optional[Dict[str, str]] = Field(None, description="Multiple thresholds by category")
    signals_detected: Optional[List[SafetySignalDetail]] = Field(None, description="Safety signals detail")
    current_status: Optional[str] = Field(None, description="Current status value")
    source: Optional[str] = Field(None, description="Data source reference")
    regulatory_reference: Optional[str] = Field(None, description="Regulatory citation")
    classification_rules: Optional[Dict[str, str]] = Field(None, description="Classification criteria")
    definitions: Optional[Dict[str, str]] = Field(None, description="Term definitions")
    determination: Optional[str] = Field(None, description="How status was determined")


class BlockingIssue(BaseModel):
    """A blocking issue for submission with full provenance."""
    category: str = Field(..., description="Issue category")
    issue: str = Field(..., description="Issue description")
    provenance: Optional[BlockingIssueProvenance] = Field(None, description="Full provenance for regulatory defensibility")


class ReadinessAssessmentResponse(BaseModel):
    """Complete regulatory readiness assessment response."""
    success: bool = Field(..., description="Request success status")
    assessment_date: str = Field(..., description="Assessment timestamp")
    protocol_id: str = Field(..., description="Protocol identifier")
    protocol_version: str = Field(..., description="Protocol version")
    is_ready: bool = Field(..., description="Overall readiness status")
    blocking_issues: List[BlockingIssue] = Field(default_factory=list)
    enrollment: Dict[str, Any] = Field(..., description="Enrollment status")
    compliance: Dict[str, Any] = Field(..., description="Compliance status")
    safety: Dict[str, Any] = Field(..., description="Safety status")
    data_completeness: Dict[str, Any] = Field(..., description="Data completeness status")
    narrative: Optional[str] = Field(None, description="AI-generated narrative")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)


class PatientReadinessResponse(BaseModel):
    """Patient-specific readiness response."""
    success: bool = Field(..., description="Request success status")
    patient_id: str = Field(..., description="Patient identifier")
    assessment_date: Optional[str] = Field(None, description="Assessment timestamp")
    is_evaluable: bool = Field(..., description="Patient is evaluable")
    blocking_issues: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_rate: float = Field(default=1.0)
    n_deviations: int = Field(default=0)
    deviation_summary: Dict[str, Any] = Field(default_factory=dict)
    narrative: Optional[str] = Field(None)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)


class ProtocolRequirementsResponse(BaseModel):
    """Protocol requirements response."""
    protocol_id: str = Field(..., description="Protocol identifier")
    protocol_version: str = Field(..., description="Protocol version")
    title: str = Field(..., description="Protocol title")
    sample_size: Dict[str, int] = Field(..., description="Sample size requirements")
    primary_endpoint: Dict[str, Any] = Field(..., description="Primary endpoint")
    n_visits: int = Field(..., description="Number of scheduled visits")
    n_secondary_endpoints: int = Field(..., description="Number of secondary endpoints")


@router.get("/readiness", response_model=ReadinessAssessmentResponse)
async def get_regulatory_readiness() -> ReadinessAssessmentResponse:
    """
    Get current regulatory submission readiness assessment.

    Analyzes:
    - Protocol requirements (Document-as-Code)
    - Study enrollment and data status
    - Protocol compliance
    - Safety signal status

    Returns actionable gap analysis with blocking issues.
    """
    service = get_readiness_service()
    result = await service.get_readiness_assessment()

    return ReadinessAssessmentResponse(**result)


@router.get("/readiness/patient/{patient_id}", response_model=PatientReadinessResponse)
async def get_patient_readiness(patient_id: str) -> PatientReadinessResponse:
    """
    Get readiness assessment for a specific patient.

    Returns:
    - Whether patient is evaluable
    - Blocking issues affecting evaluability
    - Warnings requiring attention
    """
    service = get_readiness_service()
    result = await service.get_patient_readiness(patient_id)

    return PatientReadinessResponse(**result)


@router.get("/readiness/visit/{patient_id}/{visit_id}")
async def get_visit_readiness(
    patient_id: str,
    visit_id: str
) -> Dict[str, Any]:
    """
    Get readiness status for a specific patient visit.

    Args:
        patient_id: Patient identifier
        visit_id: Visit identifier (e.g., fu_2yr)

    Returns:
        Visit requirements and status
    """
    service = get_readiness_service()
    result = await service.get_visit_readiness(patient_id, visit_id)

    return result


@router.get("/readiness/protocol-requirements", response_model=ProtocolRequirementsResponse)
async def get_protocol_requirements() -> ProtocolRequirementsResponse:
    """
    Get protocol requirements summary.

    Returns key protocol parameters from Document-as-Code.
    """
    service = get_readiness_service()
    result = service.get_protocol_requirements()

    return ProtocolRequirementsResponse(**result)


@router.get("/readiness/chase-list")
async def get_chase_list() -> Dict[str, Any]:
    """
    Get prioritized patient chase list for follow-up completion.

    Returns list of patients requiring follow-up attention,
    prioritized by urgency and missing assessments.
    """
    service = get_readiness_service()
    assessment = await service.get_readiness_assessment()

    # Extract patients needing attention from blocking issues
    chase_list = []
    for issue in assessment.get("blocking_issues", []):
        if issue.get("category") == "compliance":
            chase_list.append({
                "priority": "HIGH",
                "category": "compliance",
                "description": issue.get("issue"),
            })

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_issues": len(assessment.get("blocking_issues", [])),
        "chase_list": chase_list,
        "overall_readiness": assessment.get("is_ready", False),
    }


@router.get("/readiness/summary")
async def get_readiness_summary() -> Dict[str, Any]:
    """
    Get concise readiness summary.

    Returns high-level readiness status without full details.
    """
    service = get_readiness_service()
    assessment = await service.get_readiness_assessment()

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "is_ready": assessment.get("is_ready", False),
        "n_blocking_issues": len(assessment.get("blocking_issues", [])),
        "enrollment_ready": assessment.get("enrollment", {}).get("is_ready", False),
        "compliance_ready": assessment.get("compliance", {}).get("is_ready", False),
        "safety_ready": assessment.get("safety", {}).get("is_ready", False),
        "data_ready": assessment.get("data_completeness", {}).get("is_ready", False),
        "protocol_version": assessment.get("protocol_version"),
    }
