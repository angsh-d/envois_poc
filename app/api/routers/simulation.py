"""
Monte Carlo Simulation API.

Multi-factor simulation for risk-adjusted cohort outcome projection.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.monte_carlo_service import get_monte_carlo_service

router = APIRouter()


class RiskDistribution(BaseModel):
    """Risk factor prevalence distribution for cohort."""
    age_over_80: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of age ≥80")
    bmi_over_35: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of BMI ≥35")
    diabetes: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of diabetes")
    osteoporosis: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of osteoporosis")
    rheumatoid_arthritis: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of RA")
    chronic_kidney_disease: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of CKD")
    smoking: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of smoking")
    prior_revision: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of prior revision")
    severe_bone_loss: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of severe bone loss")
    paprosky_3b: Optional[float] = Field(None, ge=0, le=1, description="Prevalence of Paprosky 3B")

    def to_dict(self) -> Dict[str, float]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class SimulationRequest(BaseModel):
    """Request for Monte Carlo simulation."""
    n_patients: int = Field(default=549, ge=10, le=10000, description="Cohort size")
    threshold: str = Field(default="fda_510k", description="Regulatory threshold key")
    n_iterations: int = Field(default=10000, ge=100, le=100000, description="Number of iterations")
    risk_distribution: Optional[RiskDistribution] = Field(None, description="Custom risk prevalence")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")


class ScenarioSpec(BaseModel):
    """Specification for a scenario to compare."""
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    risk_distribution: Optional[RiskDistribution] = Field(None, description="Modified risk prevalence")
    exclusions: Optional[List[str]] = Field(None, description="Risk factors to exclude (set to 0%)")


class ScenarioComparisonRequest(BaseModel):
    """Request for scenario comparison."""
    n_patients: int = Field(default=549, ge=10, le=10000, description="Cohort size")
    threshold: str = Field(default="fda_510k", description="Regulatory threshold key")
    n_iterations: int = Field(default=10000, ge=100, le=100000, description="Iterations per scenario")
    scenarios: List[ScenarioSpec] = Field(..., min_length=1, max_length=10, description="Scenarios to compare")
    seed: Optional[int] = Field(default=42, description="Random seed")


class HazardRatioResponse(BaseModel):
    """Hazard ratio specification."""
    factor: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    source: str


class SimulationResponse(BaseModel):
    """Response from Monte Carlo simulation."""
    success: bool = True
    n_iterations: int
    n_patients: int
    threshold: float
    threshold_name: str
    mean_revision_rate: float
    median_revision_rate: float
    p5_revision_rate: float
    p95_revision_rate: float
    std_revision_rate: float
    probability_pass: float
    probability_pass_pct: float = Field(description="Probability as percentage")
    verdict: str
    verdict_label: str = Field(description="Human-readable verdict")
    variance_contributions: Dict[str, float]
    execution_time_ms: float
    generated_at: str


class ScenarioComparisonResponse(BaseModel):
    """Response for scenario comparison."""
    success: bool = True
    n_scenarios: int
    threshold: str
    threshold_name: str
    scenarios: List[Dict[str, Any]]
    generated_at: str


class HazardRatiosResponse(BaseModel):
    """Response with all hazard ratio specifications."""
    success: bool = True
    n_factors: int
    factors: List[HazardRatioResponse]
    sources: List[str]


@router.post("/monte-carlo/run", response_model=SimulationResponse)
async def run_monte_carlo_simulation(request: SimulationRequest) -> SimulationResponse:
    """
    Run multi-factor Monte Carlo simulation.

    This simulation:
    1. Generates a synthetic cohort with specified risk factor prevalence
    2. Samples hazard ratios from their uncertainty distributions
    3. Calculates patient-level revision risk using multiplicative HRs
    4. Simulates binary outcomes for each patient
    5. Aggregates to cohort-level revision rate
    6. Repeats for n_iterations to build outcome distribution

    Returns probability of meeting regulatory benchmark and outcome distribution.
    """
    service = get_monte_carlo_service()

    # Get risk distribution
    risk_dist = None
    if request.risk_distribution:
        risk_dist = request.risk_distribution.to_dict()
        if not risk_dist:
            risk_dist = None

    # Generate cohort
    cohort = service.generate_synthetic_cohort(
        n_patients=request.n_patients,
        risk_distribution=risk_dist
    )

    # Run simulation
    summary = service.run_simulation(
        cohort=cohort,
        threshold_key=request.threshold,
        n_iterations=request.n_iterations,
        seed=request.seed
    )

    # Map verdict to label
    verdict_labels = {
        "high_confidence": "High Confidence",
        "uncertain": "Uncertain",
        "at_risk": "At Risk"
    }

    return SimulationResponse(
        success=True,
        n_iterations=summary.n_iterations,
        n_patients=summary.n_patients,
        threshold=summary.threshold,
        threshold_name=summary.threshold_name,
        mean_revision_rate=round(summary.mean_revision_rate, 4),
        median_revision_rate=round(summary.median_revision_rate, 4),
        p5_revision_rate=round(summary.p5_revision_rate, 4),
        p95_revision_rate=round(summary.p95_revision_rate, 4),
        std_revision_rate=round(summary.std_revision_rate, 4),
        probability_pass=round(summary.probability_pass, 4),
        probability_pass_pct=round(summary.probability_pass * 100, 1),
        verdict=summary.verdict,
        verdict_label=verdict_labels.get(summary.verdict, summary.verdict),
        variance_contributions=summary.variance_contributions,
        execution_time_ms=round(summary.execution_time_ms, 1),
        generated_at=summary.generated_at,
    )


@router.post("/monte-carlo/compare", response_model=ScenarioComparisonResponse)
async def compare_scenarios(request: ScenarioComparisonRequest) -> ScenarioComparisonResponse:
    """
    Compare multiple enrollment/exclusion scenarios.

    Useful for answering questions like:
    - "What if we exclude patients over 80?"
    - "What if we tighten BMI criteria?"
    - "How does Paprosky 3B exclusion affect outcomes?"

    Each scenario gets its own Monte Carlo run with modified risk distribution.
    """
    service = get_monte_carlo_service()

    # Build scenarios list
    scenarios = []
    for spec in request.scenarios:
        risk_dist = None
        if spec.risk_distribution:
            risk_dist = spec.risk_distribution.to_dict()

        # Handle exclusions (set prevalence to 0)
        if spec.exclusions and risk_dist:
            for factor in spec.exclusions:
                risk_dist[factor] = 0.0
        elif spec.exclusions:
            # Start from default and zero out exclusions
            risk_dist = {factor: 0.0 for factor in spec.exclusions}

        scenarios.append({
            "name": spec.name,
            "description": spec.description or "",
            "risk_distribution": risk_dist,
        })

    # Run comparison
    results = service.compare_scenarios(
        scenarios=scenarios,
        n_patients=request.n_patients,
        threshold_key=request.threshold,
        n_iterations=request.n_iterations,
        seed=request.seed,
    )

    # Format response
    threshold_info = service.THRESHOLDS.get(request.threshold, service.THRESHOLDS["fda_510k"])

    scenario_results = []
    for result in results:
        scenario_results.append({
            "name": result.scenario_name,
            "description": result.description,
            "probability_pass": round(result.summary.probability_pass, 4),
            "probability_pass_pct": round(result.summary.probability_pass * 100, 1),
            "mean_revision_rate": round(result.summary.mean_revision_rate, 4),
            "mean_revision_rate_pct": round(result.summary.mean_revision_rate * 100, 2),
            "p5_revision_rate": round(result.summary.p5_revision_rate, 4),
            "p95_revision_rate": round(result.summary.p95_revision_rate, 4),
            "ci_90": f"{result.summary.p5_revision_rate*100:.1f}% - {result.summary.p95_revision_rate*100:.1f}%",
            "verdict": result.summary.verdict,
            "delta_probability": round(result.delta_probability, 4) if result.delta_probability else None,
            "delta_probability_pct": round(result.delta_probability * 100, 1) if result.delta_probability else None,
            "delta_mean_rate": round(result.delta_mean_rate, 4) if result.delta_mean_rate else None,
        })

    return ScenarioComparisonResponse(
        success=True,
        n_scenarios=len(results),
        threshold=request.threshold,
        threshold_name=threshold_info["label"],
        scenarios=scenario_results,
        generated_at=datetime.utcnow().isoformat(),
    )


@router.get("/monte-carlo/hazard-ratios", response_model=HazardRatiosResponse)
async def get_hazard_ratios() -> HazardRatiosResponse:
    """
    Get all literature-derived hazard ratios used in simulation.

    Returns hazard ratio point estimates and confidence intervals
    from registry and literature sources.
    """
    service = get_monte_carlo_service()
    specs = service.get_hazard_ratio_specs()

    factors = [HazardRatioResponse(**spec) for spec in specs]
    sources = list(set(spec["source"] for spec in specs))

    return HazardRatiosResponse(
        success=True,
        n_factors=len(factors),
        factors=factors,
        sources=sorted(sources),
    )


@router.get("/monte-carlo/thresholds")
async def get_regulatory_thresholds() -> Dict[str, Any]:
    """
    Get available regulatory thresholds.

    Returns threshold definitions that can be used in simulation.
    """
    service = get_monte_carlo_service()
    return {
        "success": True,
        "thresholds": [
            {"key": key, **value}
            for key, value in service.THRESHOLDS.items()
        ],
        "default": "fda_510k",
    }


@router.get("/monte-carlo/quick")
async def quick_simulation(
    n_patients: int = Query(default=549, ge=10, le=10000, description="Cohort size"),
    threshold: str = Query(default="fda_510k", description="Threshold key"),
) -> Dict[str, Any]:
    """
    Quick simulation with default settings.

    Runs a fast 5,000 iteration simulation with default risk distribution.
    Use the POST endpoint for custom configurations.
    """
    service = get_monte_carlo_service()

    cohort = service.generate_synthetic_cohort(n_patients)
    summary = service.run_simulation(
        cohort=cohort,
        threshold_key=threshold,
        n_iterations=5000,
        seed=42,
    )

    return {
        "success": True,
        "n_patients": n_patients,
        "threshold": threshold,
        "probability_pass_pct": round(summary.probability_pass * 100, 1),
        "mean_revision_rate_pct": round(summary.mean_revision_rate * 100, 2),
        "ci_90": f"{summary.p5_revision_rate*100:.1f}% - {summary.p95_revision_rate*100:.1f}%",
        "verdict": summary.verdict,
        "top_variance_contributors": dict(list(summary.variance_contributions.items())[:5]),
        "execution_time_ms": round(summary.execution_time_ms, 1),
    }
