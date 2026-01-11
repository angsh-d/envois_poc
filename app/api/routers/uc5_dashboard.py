"""
UC5: Intelligent Study Health Executive Dashboard API.
Aggregated multi-source intelligence with strategic decision support.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.dashboard_service import get_dashboard_service

router = APIRouter()


class HealthStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class StudyMetric(BaseModel):
    """A single study health metric."""
    name: str = Field(..., description="Metric name")
    value: str = Field(..., description="Current value")
    target: Optional[str] = Field(None, description="Target value")
    status: str = Field(..., description="Status indicator")
    trend: str = Field(default="stable", description="up, down, stable")


class ActionItem(BaseModel):
    """An action item requiring attention."""
    priority: int = Field(..., description="Priority ranking (1=highest)")
    category: str = Field(..., description="Category of action")
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Detailed description")
    owner: Optional[str] = Field(None, description="Responsible party")
    source: str = Field(..., description="Source use case (UC1-UC4)")


class ExecutiveSummaryResponse(BaseModel):
    """Executive summary response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Report generation timestamp")
    overall_status: str = Field(..., description="Overall study health status")
    headline: str = Field(..., description="One-line status summary")
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    top_priorities: List[Dict[str, Any]] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    narrative: Optional[str] = Field(None, description="AI-generated narrative")
    data_sources: List[str] = Field(default_factory=list)


class StudyProgressResponse(BaseModel):
    """Study progress response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Report generation timestamp")
    target_enrollment: int = Field(..., description="Target enrollment")
    current_enrollment: int = Field(..., description="Current enrollment")
    enrollment_pct: float = Field(..., description="Enrollment percentage")
    interim_target: int = Field(..., description="Interim analysis target")
    status: str = Field(..., description="Enrollment status")
    evaluable_patients: int = Field(..., description="Evaluable patients")
    completion_rate: float = Field(..., description="Completion rate")
    protocol_id: Optional[str] = Field(None)
    primary_endpoint: Dict[str, Any] = Field(default_factory=dict)


class ActionItemsResponse(BaseModel):
    """Action items response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Report generation timestamp")
    total_items: int = Field(..., description="Total action items")
    by_category: Dict[str, int] = Field(default_factory=dict)
    items: List[Dict[str, Any]] = Field(default_factory=list)


class MetricsSummaryResponse(BaseModel):
    """Metrics summary response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Report generation timestamp")
    overall_status: str = Field(..., description="Overall status")
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    n_metrics: int = Field(..., description="Number of metrics")


class DataQualityResponse(BaseModel):
    """Data quality response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Report generation timestamp")
    overall_quality_pct: float = Field(..., description="Overall quality percentage")
    by_domain: List[Dict[str, Any]] = Field(default_factory=list)
    n_deviations: int = Field(..., description="Number of deviations")
    compliance_rate: float = Field(..., description="Compliance rate")


class SafetyDashboardResponse(BaseModel):
    """Safety dashboard response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Report generation timestamp")
    overall_status: str = Field(..., description="Overall safety status")
    n_signals: int = Field(..., description="Number of signals")
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    high_priority: List[Dict[str, Any]] = Field(default_factory=list)
    requires_dsmb_review: bool = Field(..., description="DSMB review needed")
    metrics: List[Dict[str, Any]] = Field(default_factory=list)


class BenchmarkComparisonResponse(BaseModel):
    """Benchmark comparison response."""
    success: bool = Field(..., description="Request success status")
    generated_at: str = Field(..., description="Report generation timestamp")
    comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    literature_sources: List[str] = Field(default_factory=list)
    registry_sources: List[str] = Field(default_factory=list)


@router.get("/dashboard/executive-summary", response_model=ExecutiveSummaryResponse)
async def get_executive_summary() -> ExecutiveSummaryResponse:
    """
    Get executive dashboard summary aggregating insights from UC1-UC4.

    Provides:
    - Overall study health status
    - Key metrics with status indicators
    - Top priority action items
    - Key findings across all data sources
    - AI-generated narrative synthesis
    """
    service = get_dashboard_service()
    result = await service.get_executive_summary()

    return ExecutiveSummaryResponse(**result)


@router.get("/dashboard/study-progress", response_model=StudyProgressResponse)
async def get_study_progress() -> StudyProgressResponse:
    """
    Get detailed study progress metrics.

    Returns enrollment, follow-up, and completion status.
    """
    service = get_dashboard_service()
    result = await service.get_study_progress()

    return StudyProgressResponse(**result)


@router.get("/dashboard/action-items", response_model=ActionItemsResponse)
async def get_action_items() -> ActionItemsResponse:
    """
    Get all action items aggregated from UC1-UC4.

    Returns prioritized list with category breakdown.
    """
    service = get_dashboard_service()
    result = await service.get_action_items()

    return ActionItemsResponse(**result)


@router.get("/dashboard/metrics", response_model=MetricsSummaryResponse)
async def get_metrics_summary() -> MetricsSummaryResponse:
    """
    Get current metrics summary.

    Returns all key metrics with status indicators.
    """
    service = get_dashboard_service()
    result = await service.get_metrics_summary()

    return MetricsSummaryResponse(**result)


@router.get("/dashboard/data-quality", response_model=DataQualityResponse)
async def get_data_quality_summary() -> DataQualityResponse:
    """
    Get data quality metrics across all study data.

    Returns quality assessment by domain.
    """
    service = get_dashboard_service()
    result = await service.get_data_quality_summary()

    return DataQualityResponse(**result)


@router.get("/dashboard/safety", response_model=SafetyDashboardResponse)
async def get_safety_dashboard() -> SafetyDashboardResponse:
    """
    Get safety-focused dashboard view.

    Returns safety signals, metrics, and DSMB status.
    """
    service = get_dashboard_service()
    result = await service.get_safety_dashboard()

    return SafetyDashboardResponse(**result)


@router.get("/dashboard/benchmarks", response_model=BenchmarkComparisonResponse)
async def get_benchmark_comparison() -> BenchmarkComparisonResponse:
    """
    Get study vs benchmark comparison.

    Compares study metrics against:
    - Literature benchmarks
    - Registry population norms
    """
    service = get_dashboard_service()
    result = await service.get_benchmark_comparison()

    return BenchmarkComparisonResponse(**result)


@router.get("/dashboard/metrics-trend")
async def get_metrics_trend() -> Dict[str, Any]:
    """
    Get historical trend of key metrics.

    Returns trend data for visualization.
    """
    service = get_dashboard_service()
    summary = await service.get_metrics_summary()

    # Build trend data from current metrics
    trends = []
    for metric in summary.get("metrics", []):
        trends.append({
            "metric": metric.get("name"),
            "current": metric.get("value"),
            "trend": metric.get("trend", "stable"),
            "status": metric.get("status"),
        })

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "period": "Current snapshot",
        "trends": trends,
    }


@router.get("/dashboard/upcoming-milestones")
async def get_upcoming_milestones() -> Dict[str, Any]:
    """
    Get upcoming study milestones and deadlines.

    Returns milestones with status and blockers.
    """
    service = get_dashboard_service()
    progress = await service.get_study_progress()
    action_items = await service.get_action_items()

    # Build milestones from progress data
    enrolled = progress.get("current_enrollment", 0)
    interim = progress.get("interim_target", 25)

    milestones = []

    # Interim analysis milestone
    if enrolled < interim:
        milestones.append({
            "milestone": f"Interim Analysis (n={interim} at 2yr)",
            "status": "AT_RISK" if enrolled < interim * 0.8 else "ON_TRACK",
            "blockers": [f"Need {interim - enrolled} more patients to reach interim"],
        })

    # Safety review based on action items
    safety_items = [i for i in action_items.get("items", []) if i.get("category") == "Safety"]
    if safety_items:
        milestones.append({
            "milestone": "DSMB Safety Review",
            "status": "REQUIRES_ATTENTION",
            "blockers": [item.get("title") for item in safety_items[:2]],
        })

    # Regulatory submission
    milestones.append({
        "milestone": "Regulatory Submission",
        "status": "ON_TRACK" if progress.get("enrollment_pct", 0) >= 70 else "AT_RISK",
        "blockers": [] if progress.get("enrollment_pct", 0) >= 70 else ["Enrollment behind target"],
    })

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "milestones": milestones,
    }


@router.get("/dashboard/health-check")
async def dashboard_health_check() -> Dict[str, Any]:
    """
    Quick health check for dashboard status.

    Returns lightweight status indicators.
    """
    service = get_dashboard_service()
    summary = await service.get_executive_summary()

    return {
        "status": "healthy",
        "generated_at": datetime.utcnow().isoformat(),
        "overall_status": summary.get("overall_status"),
        "n_priorities": len(summary.get("top_priorities", [])),
        "n_metrics": len(summary.get("metrics", [])),
    }
