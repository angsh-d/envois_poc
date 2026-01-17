"""
UC10: Claim Validation Engine API.
Validates marketing claims against clinical evidence.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.services.claim_validation_service import get_claim_validation_service

router = APIRouter()


class ValidationStatus(str, Enum):
    """Claim validation status."""
    VALIDATED = "validated"
    PARTIAL = "partial"
    NOT_VALIDATED = "not_validated"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ConfidenceLevel(str, Enum):
    """Confidence level for validation."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    """Evidence entry."""
    type: str = Field(..., description="Evidence type (study_data, registry, literature)")
    evidence: str = Field(..., description="Evidence description")
    claim_value: Optional[str] = Field(None, description="Claimed value if applicable")


class ClaimValidationRequest(BaseModel):
    """Claim validation request."""
    claim: str = Field(..., description="Marketing claim to validate", min_length=10)


class ClaimValidationResponse(BaseModel):
    """Claim validation response."""
    success: bool = Field(..., description="Request success status")
    claim: str = Field(..., description="Claim that was validated")
    validated_at: str = Field(..., description="Validation timestamp")
    claim_validated: Any = Field(..., description="Validation result (true/false/partial)")
    validation_status: ValidationStatus = Field(..., description="Validation status")
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting evidence")
    contradicting_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Contradicting evidence")
    evidence_gaps: List[str] = Field(default_factory=list, description="Evidence gaps")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level")
    recommended_language: Optional[str] = Field(None, description="Recommended alternative language")
    analysis: Optional[str] = Field(None, description="Detailed AI analysis")
    compliance_notes: List[str] = Field(default_factory=list, description="Compliance notes")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    study_data_used: Dict[str, Any] = Field(default_factory=dict, description="Study data used for validation")


@router.post("/validate-claim", response_model=ClaimValidationResponse)
async def validate_claim(
    request: ClaimValidationRequest
) -> ClaimValidationResponse:
    """
    Validate a marketing claim against clinical evidence.

    Analyzes the claim against:
    - Clinical study data (n=56 patients, 24-month follow-up)
    - International registry benchmarks (5 registries)
    - Published literature benchmarks

    Returns:
    - Validation status (validated/partial/not_validated)
    - Supporting and contradicting evidence
    - Evidence gaps
    - Recommended alternative language if needed
    - Compliance notes for regulatory review
    """
    service = get_claim_validation_service()
    result = await service.validate_claim(claim=request.claim)

    return ClaimValidationResponse(**result)


@router.get("/validate")
async def validate_claim_get(
    claim: str = Query(..., description="Marketing claim to validate", min_length=10)
) -> ClaimValidationResponse:
    """
    Validate a marketing claim (GET method).

    Alternative to POST endpoint for simple claim validation.
    """
    service = get_claim_validation_service()
    result = await service.validate_claim(claim=claim)

    return ClaimValidationResponse(**result)


@router.post("/validate-batch")
async def validate_claims_batch(
    claims: List[str] = Body(..., description="List of claims to validate")
) -> Dict[str, Any]:
    """
    Validate multiple marketing claims in batch.

    Validates up to 10 claims in a single request.
    Returns validation results for each claim.
    """
    if len(claims) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 claims per batch request"
        )

    service = get_claim_validation_service()
    results = []

    for claim in claims:
        try:
            result = await service.validate_claim(claim=claim)
            results.append({
                "claim": claim,
                "validated": result.get("claim_validated"),
                "status": result.get("validation_status"),
                "confidence": result.get("confidence_level"),
                "recommended_language": result.get("recommended_language"),
            })
        except Exception as e:
            results.append({
                "claim": claim,
                "error": str(e),
            })

    # Summary statistics
    validated_count = sum(1 for r in results if r.get("validated") == True)
    partial_count = sum(1 for r in results if r.get("validated") == "partial")
    not_validated_count = sum(1 for r in results if r.get("validated") == False)

    return {
        "success": True,
        "validated_at": datetime.utcnow().isoformat(),
        "n_claims": len(claims),
        "summary": {
            "validated": validated_count,
            "partial": partial_count,
            "not_validated": not_validated_count,
        },
        "results": results,
    }


@router.get("/example-claims")
async def get_example_claims() -> Dict[str, Any]:
    """
    Get example claims for testing validation.

    Returns sample claims in different categories to demonstrate validation.
    """
    return {
        "example_claims": [
            {
                "category": "efficacy",
                "claim": "DELTA Revision Cup shows 92.9% 2-year implant survival in revision hip surgery",
                "expected": "validated",
            },
            {
                "category": "comparative",
                "claim": "DELTA Revision Cup shows superior revision rates vs. competitors",
                "expected": "partial - comparative claims need qualification",
            },
            {
                "category": "functional",
                "claim": "85% of patients achieve clinically meaningful improvement with DELTA Revision Cup",
                "expected": "validated",
            },
            {
                "category": "superlative",
                "claim": "DELTA Revision Cup is the best revision cup on the market",
                "expected": "not_validated - superlatives not substantiable",
            },
            {
                "category": "mechanism",
                "claim": "Porous tantalum technology provides enhanced osseointegration in compromised bone",
                "expected": "partial - mechanism claims supported by design",
            },
        ],
        "validation_statuses": [
            {"status": "validated", "description": "Claim fully supported by evidence"},
            {"status": "partial", "description": "Some aspects supported, needs modification"},
            {"status": "not_validated", "description": "Insufficient or contradicting evidence"},
            {"status": "insufficient_evidence", "description": "No relevant evidence available"},
        ],
    }


@router.get("/compliance-guidelines")
async def get_compliance_guidelines() -> Dict[str, Any]:
    """
    Get marketing compliance guidelines.

    Returns guidelines for medical device marketing claims.
    """
    return {
        "guidelines": [
            {
                "category": "Comparative Claims",
                "guidance": "Comparative claims (better, superior) require head-to-head data or validated benchmark comparison",
                "example_issue": "'Superior to competitors' without specific comparative data",
            },
            {
                "category": "Superlative Claims",
                "guidance": "Superlatives (best, first, only) require comprehensive evidence and are often non-compliant",
                "example_issue": "'Best revision cup available' is not substantiable",
            },
            {
                "category": "Safety Claims",
                "guidance": "Safety claims must accurately represent all available safety data",
                "example_issue": "Claiming 'safe' without mentioning known risks",
            },
            {
                "category": "Efficacy Claims",
                "guidance": "Efficacy claims should cite specific study data with patient population and follow-up",
                "example_issue": "Stating outcomes without referencing the supporting study",
            },
            {
                "category": "Off-Label Claims",
                "guidance": "Claims must be within approved indications for use",
                "example_issue": "Claiming efficacy for primary THA when indicated for revision only",
            },
        ],
        "regulatory_references": [
            "FDA 21 CFR 801 - Labeling",
            "FDA 21 CFR 803 - Medical Device Reporting",
            "EU MDR 2017/745 - Promotional Materials",
            "AdvaMed Code of Ethics",
        ],
    }
