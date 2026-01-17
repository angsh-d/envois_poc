"""
UC9: State-of-the-Art (SOTA) Report Generator API.
Generates comprehensive SOTA reports for regulatory submission and marketing.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.sota_service import get_sota_service

router = APIRouter()


class SectionInfo(BaseModel):
    """SOTA section information."""
    section_id: str = Field(..., description="Section identifier")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    word_count: int = Field(default=0, description="Word count")


class ReferenceInfo(BaseModel):
    """Reference entry."""
    id: str = Field(..., description="Reference ID")
    type: str = Field(..., description="Reference type (literature/registry)")
    reference: str = Field(..., description="Formatted reference")
    n_patients: Optional[int] = Field(None, description="Patient count if literature")
    n_procedures: Optional[int] = Field(None, description="Procedure count if registry")


class SummaryTable(BaseModel):
    """Summary statistics table."""
    registry_summary: List[Dict[str, Any]] = Field(default_factory=list)
    outcome_benchmarks: List[Dict[str, Any]] = Field(default_factory=list)


class SOTAReportResponse(BaseModel):
    """Full SOTA report response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Report type")
    generated_at: str = Field(..., description="Generation timestamp")
    title: str = Field(..., description="Report title")
    topic: str = Field(..., description="Report topic")
    executive_summary: Optional[str] = Field(None, description="Executive summary")
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="Report sections")
    references: List[Dict[str, Any]] = Field(default_factory=list, description="References")
    summary_table: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.85, description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Report metadata")


class AvailableSectionsResponse(BaseModel):
    """Available sections response."""
    available_sections: List[Dict[str, str]] = Field(default_factory=list)
    default_sections: List[str] = Field(default_factory=list)


@router.post("/sota-report", response_model=SOTAReportResponse)
async def generate_sota_report(
    topic: str = Query(
        "hip_revision",
        description="Report topic (e.g., hip_revision, acetabular_reconstruction)"
    ),
    sections: Optional[List[str]] = Query(
        None,
        description="Specific sections to include (default: all sections)"
    )
) -> SOTAReportResponse:
    """
    Generate a comprehensive State-of-the-Art report.

    Creates a regulatory-grade SOTA report with:
    - Executive summary
    - Multiple evidence-based sections
    - Registry benchmark data
    - Literature citations
    - Summary statistics table

    Available topics:
    - **hip_revision**: Revision total hip arthroplasty
    - **acetabular_reconstruction**: Acetabular reconstruction techniques
    - **porous_tantalum**: Porous tantalum technology

    Available sections:
    - epidemiology
    - current_treatment_options
    - clinical_outcomes
    - emerging_technologies
    - unmet_needs
    """
    service = get_sota_service()
    result = await service.generate_sota_report(topic=topic, sections=sections)

    return SOTAReportResponse(**result)


@router.get("/sota-report", response_model=SOTAReportResponse)
async def get_sota_report(
    topic: str = Query(
        "hip_revision",
        description="Report topic"
    )
) -> SOTAReportResponse:
    """
    Get a SOTA report with all default sections.

    Shorthand for generating a complete SOTA report on the specified topic.
    """
    service = get_sota_service()
    result = await service.generate_sota_report(topic=topic)

    return SOTAReportResponse(**result)


@router.get("/sections", response_model=AvailableSectionsResponse)
async def get_available_sections() -> AvailableSectionsResponse:
    """
    Get list of available SOTA sections.

    Returns available section IDs and their titles for customizing reports.
    """
    service = get_sota_service()
    result = await service.get_available_sections()

    return AvailableSectionsResponse(**result)


@router.get("/executive-summary")
async def get_executive_summary(
    topic: str = Query("hip_revision", description="Report topic")
) -> Dict[str, Any]:
    """
    Get just the executive summary for a SOTA topic.

    Useful for quick overviews without generating the full report.
    """
    service = get_sota_service()
    result = await service.generate_sota_report(topic=topic, sections=["clinical_outcomes"])

    return {
        "success": result.get("success", False),
        "generated_at": datetime.utcnow().isoformat(),
        "topic": topic,
        "title": result.get("title", ""),
        "executive_summary": result.get("executive_summary", ""),
        "metadata": result.get("metadata", {}),
    }


@router.get("/benchmarks")
async def get_sota_benchmarks(
    topic: str = Query("hip_revision", description="Report topic")
) -> Dict[str, Any]:
    """
    Get benchmark data that would be included in a SOTA report.

    Returns summary statistics from literature and registries
    without generating the full narrative content.
    """
    service = get_sota_service()
    result = await service.generate_sota_report(
        topic=topic,
        sections=["clinical_outcomes"]  # Minimal generation
    )

    return {
        "success": result.get("success", False),
        "generated_at": datetime.utcnow().isoformat(),
        "topic": topic,
        "summary_table": result.get("summary_table", {}),
        "references": result.get("references", []),
        "sources": result.get("sources", []),
    }
