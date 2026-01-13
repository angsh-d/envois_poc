"""
API Router for Protocol Digitization.

Provides endpoints to access digitized protocol content:
- USDM 4.0 structured data
- Schedule of Assessments (SOA)
- Eligibility Criteria with OMOP mappings
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
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
