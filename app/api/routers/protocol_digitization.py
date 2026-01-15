"""
API Router for Protocol Digitization.

Provides endpoints to access digitized protocol content:
- USDM 4.0 structured data
- Schedule of Assessments (SOA)
- Eligibility Criteria with OMOP mappings
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.protocol_digitization_service import get_protocol_digitization_service

router = APIRouter()


# === Response Models ===

class SourceDocumentResponse(BaseModel):
    filename: str
    page_count: int


class ExtractionMetadataResponse(BaseModel):
    timestamp: Optional[str]
    pipeline_version: Optional[str]
    quality_score: Optional[float]
    agents_used: int


class SOASummaryResponse(BaseModel):
    total_visits: int
    total_activities: int
    scheduled_instances: int
    footnotes: int


class EligibilitySummaryResponse(BaseModel):
    total_criteria: int
    inclusion_count: int
    exclusion_count: int
    atomic_count: int


class OverviewResponse(BaseModel):
    protocol_id: Optional[str]
    protocol_name: Optional[str]
    official_title: Optional[str]
    version: Optional[str]
    study_type: Optional[str]
    study_phase: Optional[str]
    source_document: SourceDocumentResponse
    extraction_metadata: ExtractionMetadataResponse
    soa_summary: SOASummaryResponse
    eligibility_summary: EligibilitySummaryResponse


class AgentDetailResponse(BaseModel):
    name: str
    score: Optional[float]
    from_cache: bool = False


class QualitySummaryResponse(BaseModel):
    average_score: Optional[float]
    pipeline_version: Optional[str]
    primary_model: Optional[str]
    successful_agents: List[str]
    failed_agents: List[str]
    agent_details: List[AgentDetailResponse]


class VisitResponse(BaseModel):
    id: str
    name: str
    original_name: Optional[str]
    visit_type: Optional[str]
    timing: Optional[Dict[str, Any]]
    window: Optional[Dict[str, Any]]
    type_code: Optional[str]
    provenance: Optional[Dict[str, Any]]


class ActivityResponse(BaseModel):
    id: str
    name: str
    category: Optional[str]
    cdash_domain: Optional[str]
    provenance: Optional[Dict[str, Any]]


class VisitInfoResponse(BaseModel):
    id: str
    name: str


class ActivityMatrixResponse(BaseModel):
    activity: str
    category: Optional[str]
    cdash_domain: Optional[str]
    visits: Dict[str, Any]


class SOAMatrixResponse(BaseModel):
    visits: List[VisitInfoResponse]
    activities: List[ActivityMatrixResponse]
    quality_metrics: Optional[Dict[str, Any]]


class FootnoteResponse(BaseModel):
    marker: str
    text: str
    rule_type: Optional[str]
    category: Optional[Any]
    subcategory: Optional[Any]
    edc_impact: Optional[Dict[str, Any]]
    structured_rule: Optional[Dict[str, Any]]
    applies_to: Optional[List[str]]
    provenance: Optional[Dict[str, Any]]


class AtomicCriterionResponse(BaseModel):
    atomicId: Optional[str]
    atomicText: Optional[str]
    omopTable: Optional[str]
    strategy: Optional[str]


class CriterionResponse(BaseModel):
    id: str
    original_id: Optional[str]
    original_text: str
    type: str
    logic_operator: Optional[str]
    decomposition_strategy: Optional[str]
    expression: Optional[Dict[str, Any]]
    atomic_criteria: List[Dict[str, Any]]
    sql_template: Optional[str]
    provenance: Optional[Dict[str, Any]]


class EligibilityCriteriaSummaryResponse(BaseModel):
    totalCriteria: int
    inclusionCount: int
    exclusionCount: int
    atomicCount: int


class EligibilityCriteriaResponse(BaseModel):
    protocol_id: Optional[str]
    summary: Optional[EligibilityCriteriaSummaryResponse]
    inclusion_criteria: List[CriterionResponse]
    exclusion_criteria: List[CriterionResponse]


# === Endpoints ===

@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Get Protocol Digitization Overview",
    description="Returns high-level summary of all digitized protocol data"
)
async def get_overview() -> OverviewResponse:
    """Get overview of all digitized protocol data."""
    service = get_protocol_digitization_service()
    return service.get_overview()


@router.get(
    "/usdm/study-metadata",
    summary="Get USDM Study Metadata",
    description="Returns study metadata from USDM 4.0 extraction"
)
async def get_usdm_study_metadata() -> Dict[str, Any]:
    """Get study metadata from USDM data."""
    service = get_protocol_digitization_service()
    return service.get_usdm_study_metadata()


@router.get(
    "/usdm/quality",
    response_model=QualitySummaryResponse,
    summary="Get USDM Quality Metrics",
    description="Returns quality metrics from USDM extraction"
)
async def get_usdm_quality() -> QualitySummaryResponse:
    """Get quality metrics from USDM extraction."""
    service = get_protocol_digitization_service()
    return service.get_usdm_quality_summary()


@router.get(
    "/usdm/full",
    summary="Get Full USDM Data",
    description="Returns complete USDM 4.0 extraction data (large response)"
)
async def get_usdm_full() -> Dict[str, Any]:
    """Get full USDM data."""
    service = get_protocol_digitization_service()
    return service.get_usdm_data()


@router.get(
    "/soa/visits",
    response_model=List[VisitResponse],
    summary="Get SOA Visits",
    description="Returns visit schedule from Schedule of Assessments"
)
async def get_soa_visits() -> List[VisitResponse]:
    """Get visit schedule from SOA."""
    service = get_protocol_digitization_service()
    return service.get_soa_visits()


@router.get(
    "/soa/activities",
    response_model=List[ActivityResponse],
    summary="Get SOA Activities",
    description="Returns activities from Schedule of Assessments"
)
async def get_soa_activities() -> List[ActivityResponse]:
    """Get activities from SOA."""
    service = get_protocol_digitization_service()
    return service.get_soa_activities()


@router.get(
    "/soa/matrix",
    response_model=SOAMatrixResponse,
    summary="Get SOA Matrix",
    description="Returns full SOA matrix (activities x visits)"
)
async def get_soa_matrix() -> SOAMatrixResponse:
    """Get full SOA matrix."""
    service = get_protocol_digitization_service()
    return service.get_soa_matrix()


@router.get(
    "/soa/footnotes",
    response_model=List[FootnoteResponse],
    summary="Get SOA Footnotes",
    description="Returns classified footnotes from Schedule of Assessments"
)
async def get_soa_footnotes() -> List[FootnoteResponse]:
    """Get footnotes from SOA."""
    service = get_protocol_digitization_service()
    return service.get_soa_footnotes()


@router.get(
    "/soa/full",
    summary="Get Full SOA Data",
    description="Returns complete Schedule of Assessments data"
)
async def get_soa_full() -> Dict[str, Any]:
    """Get full SOA data."""
    service = get_protocol_digitization_service()
    return service.get_soa_data()


@router.get(
    "/eligibility",
    response_model=EligibilityCriteriaResponse,
    summary="Get Eligibility Criteria",
    description="Returns eligibility criteria with OMOP CDM mappings"
)
async def get_eligibility_criteria() -> EligibilityCriteriaResponse:
    """Get eligibility criteria with OMOP mappings."""
    service = get_protocol_digitization_service()
    return service.get_eligibility_criteria()


@router.get(
    "/eligibility/full",
    summary="Get Full Eligibility Data",
    description="Returns complete eligibility criteria data"
)
async def get_eligibility_full() -> Dict[str, Any]:
    """Get full eligibility data."""
    service = get_protocol_digitization_service()
    return service.get_eligibility_data()


@router.get(
    "/usdm/agents",
    summary="Get All USDM Agent Outputs",
    description="Returns all extraction agent outputs with their data and quality scores"
)
async def get_usdm_agents() -> List[Dict[str, Any]]:
    """Get all USDM agent outputs."""
    service = get_protocol_digitization_service()
    return service.get_usdm_agents()


@router.get(
    "/domains",
    summary="Get Protocol Domain Sections",
    description="Returns all domain sections with structured data for display"
)
async def get_domain_sections() -> List[Dict[str, Any]]:
    """Get all domain sections with structured data."""
    service = get_protocol_digitization_service()
    return service.get_domain_sections()


@router.get(
    "/rules",
    summary="Get Protocol Rules",
    description="Returns protocol rules from Document-as-Code YAML (visit windows, endpoints, thresholds)"
)
async def get_protocol_rules() -> Dict[str, Any]:
    """Get protocol rules from Document-as-Code YAML."""
    service = get_protocol_digitization_service()
    return service.get_protocol_rules()


class ProtocolRuleUpdateRequest(BaseModel):
    field_path: str = Field(..., description="Dot-separated path to the field (e.g., 'protocol.version')")
    value: Any = Field(..., description="The new value to set")


class ProtocolRuleBatchUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]] = Field(..., description="List of updates with 'field_path' and 'value' keys")


@router.put(
    "/rules",
    summary="Update Protocol Rule",
    description="Update a specific field in the protocol rules YAML"
)
async def update_protocol_rule(request: ProtocolRuleUpdateRequest) -> Dict[str, Any]:
    """Update a specific protocol rule field."""
    service = get_protocol_digitization_service()
    try:
        return service.update_protocol_rule(request.field_path, request.value)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Field path not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update protocol rule: {e}")


@router.put(
    "/rules/batch",
    summary="Batch Update Protocol Rules",
    description="Update multiple fields in the protocol rules YAML at once"
)
async def update_protocol_rules_batch(request: ProtocolRuleBatchUpdateRequest) -> Dict[str, Any]:
    """Batch update multiple protocol rule fields."""
    service = get_protocol_digitization_service()
    try:
        return service.update_protocol_rules_batch(request.updates)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Field path not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update protocol rules: {e}")


PROTOCOL_DATA_DIR = Path("data/raw/protocol")

@router.get(
    "/download/soa-usdm",
    summary="Download SOA USDM JSON",
    description="Download the Schedule of Assessments USDM JSON file"
)
async def download_soa_usdm():
    """Download SOA USDM JSON file."""
    file_path = PROTOCOL_DATA_DIR / "CIP_H-34_v.2.0_05Nov2024_fully signed_soa_usdm_draft.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="SOA USDM file not found")
    return FileResponse(
        path=str(file_path),
        filename="H-34_SOA_USDM.json",
        media_type="application/json"
    )


@router.get(
    "/download/eligibility",
    summary="Download Eligibility Criteria JSON",
    description="Download the Eligibility Criteria JSON file"
)
async def download_eligibility():
    """Download Eligibility Criteria JSON file."""
    file_path = PROTOCOL_DATA_DIR / "CIP_H-34_v.2.0_05Nov2024_fully signed_eligibility_criteria.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Eligibility criteria file not found")
    return FileResponse(
        path=str(file_path),
        filename="H-34_Eligibility_Criteria.json",
        media_type="application/json"
    )


@router.get(
    "/download/usdm",
    summary="Download USDM 4.0 JSON",
    description="Download the complete USDM 4.0 protocol JSON file"
)
async def download_usdm():
    """Download complete USDM 4.0 JSON file."""
    file_path = PROTOCOL_DATA_DIR / "CIP_H-34_v.2.0_05Nov2024_fully signed_usdm_4.0.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="USDM file not found")
    return FileResponse(
        path=str(file_path),
        filename="H-34_USDM_4.0.json",
        media_type="application/json"
    )
