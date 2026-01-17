"""
UC11: FDA Surveillance Integration API.
Provides public FDA data for Quality persona.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.fda_service import get_fda_service

router = APIRouter()


class RiskLevel(str, Enum):
    """Surveillance risk level."""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    MINIMAL = "MINIMAL"


class TrendDirection(str, Enum):
    """Adverse event trend direction."""
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class SurveillanceReportResponse(BaseModel):
    """FDA surveillance report response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Type of report")
    generated_at: str = Field(..., description="Report generation timestamp")
    product_codes: List[str] = Field(..., description="FDA product codes queried")
    product_descriptions: Dict[str, str] = Field(default_factory=dict, description="Product code descriptions")
    adverse_events_summary: Dict[str, Any] = Field(default_factory=dict, description="Adverse events summary")
    clearances_summary: Dict[str, Any] = Field(default_factory=dict, description="510(k) clearances summary")
    recalls_summary: Dict[str, Any] = Field(default_factory=dict, description="Recalls summary")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Overall risk assessment")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(1.0, description="Data confidence score")


class TrendAnalysisResponse(BaseModel):
    """Adverse event trend analysis response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Type of report")
    generated_at: str = Field(..., description="Report generation timestamp")
    product_codes: List[str] = Field(..., description="FDA product codes queried")
    trends_by_year: Dict[str, int] = Field(default_factory=dict, description="Event counts by year")
    year_over_year_changes: List[Dict[str, Any]] = Field(default_factory=list, description="YoY changes")
    overall_trend: Optional[TrendDirection] = Field(None, description="Overall trend direction")
    trend_insight: Optional[str] = Field(None, description="Trend insight narrative")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")


class TriageGuidanceResponse(BaseModel):
    """Complaint triage guidance response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Type of report")
    generated_at: str = Field(..., description="Report generation timestamp")
    fda_context: Dict[str, Any] = Field(default_factory=dict, description="FDA context data")
    triage_categories: List[Dict[str, Any]] = Field(default_factory=list, description="Triage categories")
    priority_guidance: Dict[str, Any] = Field(default_factory=dict, description="Priority guidance")
    common_complaint_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Common patterns")
    regulatory_considerations: List[str] = Field(default_factory=list, description="Regulatory notes")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")


class VigilanceReportResponse(BaseModel):
    """Vigilance report response."""
    success: bool = Field(..., description="Request success status")
    report_type: str = Field(..., description="Type of report")
    reporting_period: str = Field(..., description="Reporting period")
    generated_at: str = Field(..., description="Report generation timestamp")
    executive_summary: str = Field(..., description="Executive summary")
    adverse_event_section: Dict[str, Any] = Field(default_factory=dict, description="Adverse event section")
    recall_section: Dict[str, Any] = Field(default_factory=dict, description="Recall section")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk assessment")
    regulatory_actions: List[Dict[str, str]] = Field(default_factory=list, description="Recommended actions")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Data sources")


@router.get("/surveillance", response_model=SurveillanceReportResponse)
async def get_surveillance_report(
    product_codes: Optional[str] = Query(
        None,
        description="Comma-separated FDA product codes (e.g., LPH,KWZ). Defaults to hip prosthesis codes."
    ),
    start_date: Optional[str] = Query(
        None,
        description="Start date in YYYYMMDD format"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date in YYYYMMDD format"
    ),
) -> SurveillanceReportResponse:
    """
    Get comprehensive FDA surveillance report.

    Combines data from:
    - FDA MAUDE (adverse events)
    - FDA 510(k) (clearances)
    - FDA Recall Database

    Returns surveillance summary with risk assessment.
    """
    codes = product_codes.split(",") if product_codes else None
    date_range = {}
    if start_date:
        date_range["start"] = start_date
    if end_date:
        date_range["end"] = end_date

    service = get_fda_service()
    result = await service.get_surveillance_report(
        product_codes=codes,
        date_range=date_range if date_range else None,
    )

    return SurveillanceReportResponse(**result)


@router.get("/trends", response_model=TrendAnalysisResponse)
async def get_adverse_event_trends(
    product_codes: Optional[str] = Query(
        None,
        description="Comma-separated FDA product codes"
    ),
) -> TrendAnalysisResponse:
    """
    Analyze adverse event trends over time.

    Shows year-over-year changes in adverse event reporting
    for the specified product codes.

    Helps answer: "What is the complaint rate trend?"
    """
    codes = product_codes.split(",") if product_codes else None

    service = get_fda_service()
    result = await service.get_adverse_event_trends(product_codes=codes)

    return TrendAnalysisResponse(**result)


@router.get("/triage", response_model=TriageGuidanceResponse)
async def get_triage_guidance(
    product_codes: Optional[str] = Query(
        None,
        description="Comma-separated FDA product codes"
    ),
) -> TriageGuidanceResponse:
    """
    Get complaint triage guidance based on FDA data.

    Provides prioritization guidance for complaint handling
    based on historical FDA adverse event patterns.

    Helps answer: "How should I triage today's complaints?"
    """
    codes = product_codes.split(",") if product_codes else None

    service = get_fda_service()
    result = await service.triage_complaints(product_codes=codes)

    return TriageGuidanceResponse(**result)


@router.get("/vigilance-report", response_model=VigilanceReportResponse)
async def get_vigilance_report(
    product_codes: Optional[str] = Query(
        None,
        description="Comma-separated FDA product codes"
    ),
    reporting_period: Optional[str] = Query(
        None,
        description="Reporting period description (e.g., 'Q4 2024')"
    ),
) -> VigilanceReportResponse:
    """
    Generate vigilance report for regulatory submission.

    Combines FDA surveillance data into a formatted vigilance report
    suitable for regulatory review.

    Helps answer: "Generate a vigilance report for the current period"
    """
    codes = product_codes.split(",") if product_codes else None

    service = get_fda_service()
    result = await service.generate_vigilance_report(
        product_codes=codes,
        reporting_period=reporting_period,
    )

    return VigilanceReportResponse(**result)


@router.get("/product-codes")
async def get_product_codes() -> Dict[str, Any]:
    """
    Get available FDA product codes for hip prostheses.

    Returns product codes and their descriptions.
    """
    from app.agents.fda_agent import HIP_PRODUCT_CODES

    product_code_list = list(HIP_PRODUCT_CODES.keys())
    return {
        "product_codes": HIP_PRODUCT_CODES,
        "default_codes": product_code_list[:3],
        "usage": "Use comma-separated codes in query parameters, e.g., ?product_codes=LPH,KWZ",
    }


@router.get("/data-sources")
async def get_data_sources() -> Dict[str, Any]:
    """
    Get information about FDA data sources.

    Returns details about the public FDA APIs used.
    """
    return {
        "data_sources": [
            {
                "name": "FDA MAUDE Database",
                "description": "Manufacturer and User Facility Device Experience",
                "api_endpoint": "https://api.fda.gov/device/event.json",
                "coverage": "1992-present",
                "update_frequency": "Weekly",
                "content": "Device adverse event reports including injuries, deaths, and malfunctions",
            },
            {
                "name": "FDA 510(k) Database",
                "description": "Premarket Notification Database",
                "api_endpoint": "https://api.fda.gov/device/510k.json",
                "coverage": "1976-present",
                "update_frequency": "Weekly",
                "content": "510(k) premarket clearance records",
            },
            {
                "name": "FDA Device Recall Database",
                "description": "Medical Device Recall Database",
                "api_endpoint": "https://api.fda.gov/device/recall.json",
                "coverage": "All active and recent recalls",
                "update_frequency": "Daily",
                "content": "Device recall information including reason and status",
            },
        ],
        "disclaimer": (
            "Data is retrieved from public FDA APIs. This data should be used "
            "for informational purposes as part of post-market surveillance "
            "activities. Always verify critical findings through official FDA channels."
        ),
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Check FDA API connectivity.

    Tests connection to FDA APIs.
    """
    import httpx

    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "apis": {},
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        for api_name, endpoint in [
            ("maude", "https://api.fda.gov/device/event.json?limit=1"),
            ("510k", "https://api.fda.gov/device/510k.json?limit=1"),
            ("recall", "https://api.fda.gov/device/recall.json?limit=1"),
        ]:
            try:
                response = await client.get(endpoint)
                status["apis"][api_name] = {
                    "status": "available" if response.status_code == 200 else "error",
                    "status_code": response.status_code,
                }
            except Exception as e:
                status["apis"][api_name] = {
                    "status": "unavailable",
                    "error": str(e),
                }

    status["overall"] = (
        "healthy"
        if all(api.get("status") == "available" for api in status["apis"].values())
        else "degraded"
    )

    return status
