"""
Monte Carlo Simulation Service for Clinical Intelligence Platform.

Multi-factor simulation engine for risk-adjusted cohort outcome projection.
Uses literature-derived hazard ratios with uncertainty to simulate revision rates.
"""
import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from data.loaders.yaml_loader import get_hybrid_loader

logger = logging.getLogger(__name__)


@dataclass
class HazardRatioSpec:
    """Specification for a hazard ratio with uncertainty."""
    factor: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    source: str

    @property
    def log_mean(self) -> float:
        """Mean of log-HR for lognormal sampling."""
        return math.log(self.point_estimate)

    @property
    def log_std(self) -> float:
        """Standard deviation of log-HR (derived from CI)."""
        # 95% CI spans approximately 3.92 standard deviations
        log_ci_range = math.log(self.ci_upper) - math.log(self.ci_lower)
        return log_ci_range / 3.92

    def sample(self) -> float:
        """Sample a hazard ratio from lognormal distribution."""
        return np.random.lognormal(self.log_mean, self.log_std)


@dataclass
class PatientRiskProfile:
    """Risk profile for a simulated patient."""
    patient_id: str
    risk_factors: Dict[str, bool] = field(default_factory=dict)
    base_revision_probability: float = 0.052  # Registry baseline ~5.2%

    def calculate_risk(self, sampled_hrs: Dict[str, float], max_risk: float = 0.50) -> float:
        """
        Calculate revision probability using multiplicative hazard ratios.

        Args:
            sampled_hrs: Dict of factor -> sampled HR value
            max_risk: Cap on individual risk to prevent extremes

        Returns:
            Revision probability for this patient
        """
        combined_hr = 1.0
        for factor, present in self.risk_factors.items():
            if present and factor in sampled_hrs:
                combined_hr *= sampled_hrs[factor]

        # Convert hazard ratio to probability (approximate for 2-year risk)
        # Using: P(event) ≈ 1 - exp(-HR * baseline_hazard)
        # For small probabilities: P ≈ HR * baseline_probability
        risk = min(max_risk, combined_hr * self.base_revision_probability)
        return risk

    def has_revision(self, risk: float) -> bool:
        """Simulate whether patient has revision given their risk."""
        return random.random() < risk


@dataclass
class SimulationResult:
    """Result from a single Monte Carlo iteration."""
    iteration: int
    cohort_revision_rate: float
    n_revisions: int
    n_patients: int
    sampled_hrs: Dict[str, float]
    passes_threshold: bool


@dataclass
class MonteCarloSummary:
    """Summary statistics from Monte Carlo simulation."""
    n_iterations: int
    n_patients: int
    threshold: float
    threshold_name: str

    # Cohort outcome distribution
    mean_revision_rate: float
    median_revision_rate: float
    p5_revision_rate: float
    p95_revision_rate: float
    std_revision_rate: float

    # Pass probability
    probability_pass: float
    verdict: str  # "high_confidence", "uncertain", "at_risk"

    # Variance decomposition (sensitivity analysis)
    variance_contributions: Dict[str, float]

    # Raw data for visualization
    revision_rates: List[float]

    # Execution metadata
    execution_time_ms: float
    generated_at: str


@dataclass
class ScenarioComparison:
    """Comparison between simulation scenarios."""
    scenario_name: str
    description: str
    summary: MonteCarloSummary
    delta_probability: Optional[float] = None  # vs baseline
    delta_mean_rate: Optional[float] = None


class MonteCarloService:
    """
    Service for multi-factor Monte Carlo simulation.

    Simulates cohort outcomes by:
    1. Sampling hazard ratios from their uncertainty distributions
    2. Calculating patient-level risks using multiplicative HRs
    3. Simulating binary outcomes for each patient
    4. Aggregating to cohort-level revision rate
    5. Repeating 10,000 times to build outcome distribution
    """

    # Regulatory thresholds
    THRESHOLDS = {
        "fda_510k": {"rate": 0.10, "label": "FDA 510(k)", "description": "≤10% revision rate"},
        "mdr_pmcf": {"rate": 0.12, "label": "MDR PMCF", "description": "≤12% revision rate"},
        "registry_parity": {"rate": 0.09, "label": "Registry Parity", "description": "≤9% (NJR match)"},
    }

    # Default baseline revision rate from registry data
    DEFAULT_BASELINE_RATE = 0.052  # 5.2% from NJR/AOANJRR
    BASELINE_RATE_CI = (0.048, 0.056)  # Confidence interval

    def __init__(self):
        """Initialize Monte Carlo service with hazard ratios from literature."""
        self._doc_loader = get_hybrid_loader()
        self._hazard_ratio_specs = self._load_hazard_ratios()

    def _load_hazard_ratios(self) -> Dict[str, HazardRatioSpec]:
        """Load hazard ratio specifications from literature_benchmarks.yaml."""
        specs = {}
        try:
            lit_benchmarks = self._doc_loader.load_literature_benchmarks()
            # Filter for patient demographic risk factors (not HHS scores)
            demographic_factors = [
                "age_over_80", "bmi_over_35", "diabetes", "osteoporosis",
                "rheumatoid_arthritis", "chronic_kidney_disease", "smoking",
                "prior_revision", "severe_bone_loss", "paprosky_3b"
            ]
            for rf in lit_benchmarks.all_risk_factors:
                if rf.factor in demographic_factors:
                    ci = rf.confidence_interval
                    specs[rf.factor] = HazardRatioSpec(
                        factor=rf.factor,
                        point_estimate=rf.hazard_ratio,
                        ci_lower=ci[0] if ci else rf.hazard_ratio * 0.8,
                        ci_upper=ci[1] if len(ci) > 1 else rf.hazard_ratio * 1.2,
                        source=rf.source,
                    )
            logger.info(f"Loaded {len(specs)} hazard ratio specifications")
        except Exception as e:
            logger.error(f"Failed to load hazard ratios: {e}")
            # Use defaults if YAML loading fails
            specs = self._default_hazard_ratios()
        return specs

    def _default_hazard_ratios(self) -> Dict[str, HazardRatioSpec]:
        """Default hazard ratios if YAML loading fails."""
        defaults = [
            ("age_over_80", 1.85, 1.42, 2.41, "NJR UK 2024"),
            ("bmi_over_35", 1.52, 1.28, 1.81, "AOANJRR 2024"),
            ("diabetes", 1.38, 1.15, 1.66, "Jamsen 2012"),
            ("osteoporosis", 1.62, 1.31, 2.00, "NJR UK 2024"),
            ("rheumatoid_arthritis", 1.71, 1.38, 2.12, "Ravi 2012"),
            ("chronic_kidney_disease", 1.45, 1.18, 1.78, "AOANJRR 2024"),
            ("smoking", 1.32, 1.12, 1.56, "Teng 2015"),
            ("prior_revision", 2.45, 2.02, 2.97, "NJR/AOANJRR 2024"),
            ("severe_bone_loss", 1.89, 1.52, 2.35, "Paprosky literature"),
            ("paprosky_3b", 2.21, 1.75, 2.79, "Paprosky et al."),
        ]
        return {
            name: HazardRatioSpec(name, hr, ci_l, ci_u, src)
            for name, hr, ci_l, ci_u, src in defaults
        }

    def _sample_baseline_rate(self) -> float:
        """Sample baseline revision rate from Beta distribution."""
        # Use Beta distribution with parameters derived from registry data
        # For 5.2% rate with CI (4.8%, 5.6%), approximate with Beta(52, 948)
        alpha = 52
        beta = 948
        return np.random.beta(alpha, beta)

    def _sample_all_hazard_ratios(self) -> Dict[str, float]:
        """Sample all hazard ratios for one iteration."""
        return {
            factor: spec.sample()
            for factor, spec in self._hazard_ratio_specs.items()
        }

    def generate_synthetic_cohort(
        self,
        n_patients: int,
        risk_distribution: Optional[Dict[str, float]] = None
    ) -> List[PatientRiskProfile]:
        """
        Generate a synthetic patient cohort with risk factor distribution.

        Args:
            n_patients: Number of patients in cohort
            risk_distribution: Optional dict of factor -> prevalence (0-1)
                             If None, uses realistic population prevalence

        Returns:
            List of PatientRiskProfile objects
        """
        # Default risk factor prevalence based on registry data for revision THA
        # Calibrated to produce mean revision rates consistent with NJR/AOANJRR (~5-8%)
        default_prevalence = {
            "age_over_80": 0.08,      # ~8% of revision THA patients are ≥80 (NJR 2024)
            "bmi_over_35": 0.12,      # ~12% have BMI ≥35 (AOANJRR)
            "diabetes": 0.15,         # ~15% have diabetes
            "osteoporosis": 0.12,     # ~12% have osteoporosis
            "rheumatoid_arthritis": 0.04,  # ~4% have RA
            "chronic_kidney_disease": 0.06,  # ~6% have CKD
            "smoking": 0.08,          # ~8% current smokers
            "prior_revision": 0.10,   # ~10% have had prior revision (re-revision)
            "severe_bone_loss": 0.15, # ~15% have severe bone loss (Paprosky 3)
            "paprosky_3b": 0.06,      # ~6% have Paprosky 3B specifically
        }

        prevalence = risk_distribution or default_prevalence

        patients = []
        for i in range(n_patients):
            risk_factors = {
                factor: random.random() < prev
                for factor, prev in prevalence.items()
            }
            patients.append(PatientRiskProfile(
                patient_id=f"SIM-{i+1:04d}",
                risk_factors=risk_factors,
            ))

        return patients

    def run_simulation(
        self,
        cohort: List[PatientRiskProfile],
        threshold_key: str = "fda_510k",
        n_iterations: int = 10000,
        seed: Optional[int] = None
    ) -> MonteCarloSummary:
        """
        Run Monte Carlo simulation for cohort outcome projection.

        Args:
            cohort: List of patient risk profiles
            threshold_key: Regulatory threshold to evaluate against
            n_iterations: Number of Monte Carlo iterations
            seed: Optional random seed for reproducibility

        Returns:
            MonteCarloSummary with results
        """
        import time
        start_time = time.time()

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        threshold_info = self.THRESHOLDS.get(threshold_key, self.THRESHOLDS["fda_510k"])
        threshold_rate = threshold_info["rate"]

        n_patients = len(cohort)
        revision_rates = []
        pass_count = 0

        # For variance decomposition
        hr_samples_by_factor: Dict[str, List[float]] = {
            factor: [] for factor in self._hazard_ratio_specs.keys()
        }
        baseline_samples: List[float] = []

        for iteration in range(n_iterations):
            # Sample baseline rate
            baseline_rate = self._sample_baseline_rate()
            baseline_samples.append(baseline_rate)

            # Sample all hazard ratios
            sampled_hrs = self._sample_all_hazard_ratios()
            for factor, hr in sampled_hrs.items():
                hr_samples_by_factor[factor].append(hr)

            # Calculate cohort outcome
            n_revisions = 0
            for patient in cohort:
                patient.base_revision_probability = baseline_rate
                risk = patient.calculate_risk(sampled_hrs)
                if patient.has_revision(risk):
                    n_revisions += 1

            cohort_rate = n_revisions / n_patients if n_patients > 0 else 0
            revision_rates.append(cohort_rate)

            if cohort_rate <= threshold_rate:
                pass_count += 1

        # Calculate summary statistics
        rates_array = np.array(revision_rates)
        probability_pass = pass_count / n_iterations

        # Determine verdict
        if probability_pass >= 0.80:
            verdict = "high_confidence"
        elif probability_pass >= 0.50:
            verdict = "uncertain"
        else:
            verdict = "at_risk"

        # Variance decomposition using correlation with cohort rate
        variance_contributions = self._calculate_variance_contributions(
            revision_rates, hr_samples_by_factor, baseline_samples
        )

        execution_time_ms = (time.time() - start_time) * 1000

        return MonteCarloSummary(
            n_iterations=n_iterations,
            n_patients=n_patients,
            threshold=threshold_rate,
            threshold_name=threshold_info["label"],
            mean_revision_rate=float(np.mean(rates_array)),
            median_revision_rate=float(np.median(rates_array)),
            p5_revision_rate=float(np.percentile(rates_array, 5)),
            p95_revision_rate=float(np.percentile(rates_array, 95)),
            std_revision_rate=float(np.std(rates_array)),
            probability_pass=probability_pass,
            verdict=verdict,
            variance_contributions=variance_contributions,
            revision_rates=revision_rates,
            execution_time_ms=execution_time_ms,
            generated_at=datetime.utcnow().isoformat(),
        )

    def _calculate_variance_contributions(
        self,
        revision_rates: List[float],
        hr_samples: Dict[str, List[float]],
        baseline_samples: List[float]
    ) -> Dict[str, float]:
        """
        Calculate variance contribution of each factor using Spearman correlation.

        This shows which uncertain inputs contribute most to outcome uncertainty.
        """
        contributions = {}
        rates_array = np.array(revision_rates)
        total_variance = np.var(rates_array)

        if total_variance == 0:
            return {factor: 0.0 for factor in hr_samples.keys()}

        # Correlation with baseline rate
        baseline_array = np.array(baseline_samples)
        corr = np.corrcoef(baseline_array, rates_array)[0, 1]
        contributions["baseline_rate"] = abs(corr) ** 2  # R-squared approximation

        # Correlation with each HR
        for factor, samples in hr_samples.items():
            samples_array = np.array(samples)
            corr = np.corrcoef(samples_array, rates_array)[0, 1]
            contributions[factor] = abs(corr) ** 2

        # Normalize to percentages
        total_contribution = sum(contributions.values())
        if total_contribution > 0:
            contributions = {
                k: round(v / total_contribution * 100, 1)
                for k, v in contributions.items()
            }

        # Sort by contribution descending
        contributions = dict(sorted(
            contributions.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        return contributions

    def compare_scenarios(
        self,
        scenarios: List[Dict[str, Any]],
        n_patients: int = 549,
        threshold_key: str = "fda_510k",
        n_iterations: int = 10000,
        seed: Optional[int] = 42
    ) -> List[ScenarioComparison]:
        """
        Compare multiple enrollment/exclusion scenarios.

        Args:
            scenarios: List of scenario dicts with 'name', 'description',
                      'risk_distribution' modifications
            n_patients: Cohort size
            threshold_key: Regulatory threshold
            n_iterations: Iterations per scenario
            seed: Random seed for reproducibility

        Returns:
            List of ScenarioComparison results
        """
        results = []
        baseline_summary = None

        for i, scenario in enumerate(scenarios):
            # Generate cohort with scenario's risk distribution
            cohort = self.generate_synthetic_cohort(
                n_patients,
                scenario.get("risk_distribution")
            )

            # Run simulation
            summary = self.run_simulation(
                cohort,
                threshold_key,
                n_iterations,
                seed=seed + i if seed else None
            )

            # Calculate delta from baseline
            delta_prob = None
            delta_rate = None
            if baseline_summary is not None:
                delta_prob = summary.probability_pass - baseline_summary.probability_pass
                delta_rate = summary.mean_revision_rate - baseline_summary.mean_revision_rate
            else:
                baseline_summary = summary

            results.append(ScenarioComparison(
                scenario_name=scenario.get("name", f"Scenario {i+1}"),
                description=scenario.get("description", ""),
                summary=summary,
                delta_probability=delta_prob,
                delta_mean_rate=delta_rate,
            ))

        return results

    def get_hazard_ratio_specs(self) -> List[Dict[str, Any]]:
        """Get all hazard ratio specifications for display."""
        return [
            {
                "factor": spec.factor,
                "point_estimate": spec.point_estimate,
                "ci_lower": spec.ci_lower,
                "ci_upper": spec.ci_upper,
                "source": spec.source,
            }
            for spec in self._hazard_ratio_specs.values()
        ]

    def summary_to_dict(self, summary: MonteCarloSummary) -> Dict[str, Any]:
        """Convert MonteCarloSummary to API-friendly dict."""
        return {
            "n_iterations": summary.n_iterations,
            "n_patients": summary.n_patients,
            "threshold": summary.threshold,
            "threshold_name": summary.threshold_name,
            "mean_revision_rate": round(summary.mean_revision_rate, 4),
            "median_revision_rate": round(summary.median_revision_rate, 4),
            "p5_revision_rate": round(summary.p5_revision_rate, 4),
            "p95_revision_rate": round(summary.p95_revision_rate, 4),
            "std_revision_rate": round(summary.std_revision_rate, 4),
            "probability_pass": round(summary.probability_pass, 4),
            "verdict": summary.verdict,
            "variance_contributions": summary.variance_contributions,
            "execution_time_ms": round(summary.execution_time_ms, 1),
            "generated_at": summary.generated_at,
        }


# Singleton instance
_monte_carlo_service: Optional[MonteCarloService] = None


def get_monte_carlo_service() -> MonteCarloService:
    """Get singleton Monte Carlo service instance."""
    global _monte_carlo_service
    if _monte_carlo_service is None:
        _monte_carlo_service = MonteCarloService()
    return _monte_carlo_service
