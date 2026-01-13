"""
YAML Loader for Document-as-Code files.
Loads and validates protocol rules, literature benchmarks, and registry norms.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Protocol Rules Models
# ============================================================================

class VisitWindow(BaseModel):
    """Protocol-defined visit window."""
    id: str = Field(..., description="Visit identifier")
    name: str = Field(..., description="Visit display name")
    target_day: int = Field(..., description="Target days from surgery")
    window_minus: int = Field(..., description="Days before target allowed")
    window_plus: int = Field(..., description="Days after target allowed")
    required_assessments: List[str] = Field(default_factory=list, description="Required assessments")
    is_primary_endpoint: bool = Field(default=False, description="Is this the primary endpoint visit")

    def get_window_range(self) -> tuple:
        """Get (min_day, max_day) tuple."""
        return (
            self.target_day - self.window_minus,
            self.target_day + self.window_plus
        )

    def is_within_window(self, actual_day: int) -> bool:
        """Check if actual_day is within the allowed window."""
        min_day, max_day = self.get_window_range()
        return min_day <= actual_day <= max_day

    def get_deviation_days(self, actual_day: int) -> int:
        """Get number of days outside window (0 if within window)."""
        min_day, max_day = self.get_window_range()
        if actual_day < min_day:
            return min_day - actual_day
        elif actual_day > max_day:
            return actual_day - max_day
        return 0


class Endpoint(BaseModel):
    """Study endpoint definition."""
    id: str
    name: str
    calculation: Optional[str] = None
    success_threshold: Optional[float] = None
    mcid_threshold: Optional[float] = None
    success_criterion: Optional[str] = None


class SafetyThreshold(BaseModel):
    """Safety monitoring threshold."""
    metric: str
    threshold: float
    action: str = "monitor"


class ProtocolRules(BaseModel):
    """Complete protocol rules structure."""
    protocol_id: str
    protocol_version: str
    effective_date: str
    title: str
    visits: List[VisitWindow]
    primary_endpoint: Endpoint
    secondary_endpoints: List[Endpoint] = Field(default_factory=list)
    sample_size_target: int
    sample_size_interim: int
    safety_thresholds: Dict[str, float]
    deviation_classification: Dict[str, Dict[str, Any]]
    inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)

    def get_visit(self, visit_id: str) -> Optional[VisitWindow]:
        """Get visit by ID."""
        for visit in self.visits:
            if visit.id == visit_id:
                return visit
        return None

    def get_all_visit_windows(self) -> Dict[str, VisitWindow]:
        """Get all visits as dictionary."""
        return {v.id: v for v in self.visits}


# ============================================================================
# Literature Benchmarks Models
# ============================================================================

class RiskFactor(BaseModel):
    """Literature-derived risk factor."""
    factor: str
    hazard_ratio: float
    confidence_interval: Optional[List[float]] = None
    outcome: str
    source: str


class PublicationBenchmark(BaseModel):
    """Benchmarks from a single publication."""
    id: str
    title: str
    year: int
    n_patients: Optional[int] = None
    follow_up_years: Optional[float] = None
    benchmarks: Dict[str, Any] = Field(default_factory=dict)
    risk_factors: List[RiskFactor] = Field(default_factory=list)


class LiteratureBenchmarks(BaseModel):
    """Complete literature benchmarks structure."""
    publications: List[PublicationBenchmark]
    aggregate_benchmarks: Dict[str, Any]
    all_risk_factors: List[RiskFactor] = Field(default_factory=list)

    def get_benchmark(self, metric: str) -> Optional[Dict[str, Any]]:
        """Get aggregate benchmark for a metric."""
        return self.aggregate_benchmarks.get(metric)

    def get_risk_factors_for_outcome(self, outcome: str) -> List[RiskFactor]:
        """Get all risk factors for a specific outcome."""
        return [rf for rf in self.all_risk_factors if outcome.lower() in rf.outcome.lower()]


# ============================================================================
# Registry Norms Models
# ============================================================================

class RegistryBenchmark(BaseModel):
    """Single registry benchmark with complete data from YAML."""
    id: str = Field(default="", description="Registry identifier (e.g., 'aoanjrr')")
    name: str
    abbreviation: str = Field(default="", description="Short form (e.g., 'AOANJRR')")
    report_year: int
    data_years: Optional[str] = None
    population: Optional[str] = None
    n_procedures: Optional[int] = None
    n_primary: Optional[int] = None
    revision_burden: Optional[float] = None

    # Survival rates at multiple timepoints
    survival_1yr: Optional[float] = None
    survival_2yr: Optional[float] = None
    survival_5yr: Optional[float] = None
    survival_10yr: Optional[float] = None
    survival_15yr: Optional[float] = None

    # Revision rates at multiple timepoints
    revision_rate_1yr: Optional[float] = None
    revision_rate_2yr: Optional[float] = None
    revision_rate_median: Optional[float] = None
    revision_rate_p75: Optional[float] = None
    revision_rate_p95: Optional[float] = None

    # Revision reasons
    revision_reasons: Optional[List[Dict[str, Any]]] = None

    # Outcomes by indication (AOANJRR has this)
    outcomes_by_indication: Optional[Dict[str, Dict[str, float]]] = None


class PooledNorms(BaseModel):
    """Aggregated norms from all registries."""
    total_procedures: int
    total_registries: int
    survival_rates: Dict[str, Dict[str, Any]]
    revision_rates: Dict[str, Dict[str, Any]]
    revision_reasons_pooled: Dict[str, float]


class PerformanceLevel(BaseModel):
    """Performance classification criteria."""
    description: str
    revision_rate_max: Optional[float] = None
    survival_2yr_min: Optional[float] = None


class ComparativeCriteria(BaseModel):
    """Criteria for comparative assessment."""
    performance_levels: Dict[str, PerformanceLevel]
    signal_thresholds: Dict[str, float]


class DeviceBenchmark(BaseModel):
    """Device-specific benchmarks (e.g., porous tantalum cups)."""
    description: str
    source: str
    survival_2yr: Optional[float] = None
    survival_5yr: Optional[float] = None
    revision_rate_2yr: Optional[float] = None
    advantages: List[str] = Field(default_factory=list)
    indications: List[str] = Field(default_factory=list)
    comparison_to_conventional: Dict[str, float] = Field(default_factory=dict)


class RegistryNorms(BaseModel):
    """Complete registry norms structure with multi-registry support."""
    registries: List[RegistryBenchmark]
    pooled_norms: Optional[PooledNorms] = None
    concern_thresholds: Dict[str, float]
    risk_thresholds: Dict[str, float]
    comparative_criteria: Optional[ComparativeCriteria] = None
    device_benchmarks: Dict[str, DeviceBenchmark] = Field(default_factory=dict)

    def get_primary_registry(self) -> Optional[RegistryBenchmark]:
        """Get primary registry (AOANJRR)."""
        for reg in self.registries:
            if "aoanjrr" in reg.name.lower() or reg.id == "aoanjrr":
                return reg
        return self.registries[0] if self.registries else None

    def get_registry_by_id(self, registry_id: str) -> Optional[RegistryBenchmark]:
        """Get registry by its identifier."""
        for reg in self.registries:
            if reg.id.lower() == registry_id.lower() or reg.abbreviation.lower() == registry_id.lower():
                return reg
        return None

    def get_all_registries(self) -> List[RegistryBenchmark]:
        """Get all registries."""
        return self.registries

    def compare_metric_across_registries(
        self,
        metric: str,
        study_value: float
    ) -> Dict[str, Any]:
        """
        Compare a study metric against ALL registries.

        Returns:
            Dictionary with comparison results for each registry
        """
        results = {
            "metric": metric,
            "study_value": study_value,
            "registries_higher": [],
            "registries_lower": [],
            "registries_equal": [],
            "comparisons": [],
        }

        for reg in self.registries:
            registry_value = getattr(reg, metric, None)
            if registry_value is not None:
                diff = round(study_value - registry_value, 4)
                comparison = {
                    "registry_id": reg.id,
                    "registry_name": reg.abbreviation or reg.name,
                    "registry_value": registry_value,
                    "difference": diff,
                    "n_procedures": reg.n_procedures,
                }
                results["comparisons"].append(comparison)

                if study_value > registry_value:
                    results["registries_lower"].append(reg.abbreviation or reg.id)
                elif study_value < registry_value:
                    results["registries_higher"].append(reg.abbreviation or reg.id)
                else:
                    results["registries_equal"].append(reg.abbreviation or reg.id)

        # Sort comparisons by registry value
        results["comparisons"].sort(key=lambda x: x["registry_value"])

        # Add summary statistics
        values = [c["registry_value"] for c in results["comparisons"]]
        if values:
            results["registry_min"] = min(values)
            results["registry_max"] = max(values)
            results["registry_mean"] = round(sum(values) / len(values), 4)
            results["registry_range"] = f"{min(values)*100:.1f}% - {max(values)*100:.1f}%"

        return results

    def get_percentile_across_registries(
        self,
        metric: str,
        study_value: float
    ) -> Dict[str, Any]:
        """
        Determine percentile position across all registries.

        Returns:
            Dictionary with percentile position info
        """
        values = []
        for reg in self.registries:
            registry_value = getattr(reg, metric, None)
            if registry_value is not None:
                values.append(registry_value)

        if not values:
            return {"error": f"No registry data for metric: {metric}"}

        values_sorted = sorted(values)
        n = len(values_sorted)

        # Find position
        below_count = sum(1 for v in values if study_value > v)
        percentile = (below_count / n) * 100

        return {
            "metric": metric,
            "study_value": study_value,
            "n_registries": n,
            "percentile": round(percentile, 1),
            "registry_values": values_sorted,
            "min": min(values),
            "max": max(values),
            "median": values_sorted[n // 2],
            "position_description": self._describe_position(percentile),
        }

    def _describe_position(self, percentile: float) -> str:
        """Describe percentile position in words."""
        if percentile >= 90:
            return "Above all registries (>90th percentile)"
        elif percentile >= 75:
            return "Higher than most registries (75th-90th percentile)"
        elif percentile >= 50:
            return "Above median (50th-75th percentile)"
        elif percentile >= 25:
            return "Below median (25th-50th percentile)"
        else:
            return "Lower than most registries (<25th percentile)"

    def find_closest_registry(
        self,
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Find the registry whose outcomes most closely match study results.

        Args:
            metrics: Dictionary of metric_name -> study_value

        Returns:
            Dictionary with closest registry and match details
        """
        registry_scores = []

        for reg in self.registries:
            total_diff = 0
            matched_metrics = 0

            for metric, study_value in metrics.items():
                registry_value = getattr(reg, metric, None)
                if registry_value is not None:
                    # Normalize difference as percentage of registry value
                    diff = abs(study_value - registry_value) / registry_value
                    total_diff += diff
                    matched_metrics += 1

            if matched_metrics > 0:
                avg_diff = total_diff / matched_metrics
                registry_scores.append({
                    "registry_id": reg.id,
                    "registry_name": reg.abbreviation or reg.name,
                    "n_procedures": reg.n_procedures,
                    "average_difference": round(avg_diff * 100, 2),  # as percentage
                    "metrics_compared": matched_metrics,
                })

        # Sort by average difference (lower is closer)
        registry_scores.sort(key=lambda x: x["average_difference"])

        return {
            "closest_match": registry_scores[0] if registry_scores else None,
            "all_rankings": registry_scores,
        }

    def classify_performance(
        self,
        revision_rate: Optional[float] = None,
        survival_2yr: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Classify study performance based on comparative criteria.

        Returns:
            Performance classification and details
        """
        if not self.comparative_criteria:
            return {"error": "No comparative criteria available"}

        classification = "unknown"
        details = {}

        levels = self.comparative_criteria.performance_levels
        # Check from best to worst
        for level_name in ["excellent", "good", "acceptable", "concerning"]:
            level = levels.get(level_name)
            if not level:
                continue

            meets_criteria = True

            if revision_rate is not None and level.revision_rate_max is not None:
                if revision_rate > level.revision_rate_max:
                    meets_criteria = False
                details["revision_rate_threshold"] = level.revision_rate_max

            if survival_2yr is not None and level.survival_2yr_min is not None:
                if survival_2yr < level.survival_2yr_min:
                    meets_criteria = False
                details["survival_2yr_threshold"] = level.survival_2yr_min

            if meets_criteria:
                classification = level_name
                break

        return {
            "classification": classification,
            "description": levels.get(classification, PerformanceLevel(description="Unknown")).description if classification != "unknown" else "Unable to classify",
            "details": details,
        }


# ============================================================================
# YAML Loader
# ============================================================================

class DocumentAsCodeLoader:
    """
    Loader for Document-as-Code YAML files.

    Loads and validates:
    - protocol_rules.yaml
    - literature_benchmarks.yaml
    - registry_norms.yaml
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            base_path: Path to document_as_code directory
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = settings.project_root / "data" / "processed" / "document_as_code"

        logger.info(f"Document-as-Code loader initialized: {self.base_path}")

    @lru_cache(maxsize=10)
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load and cache YAML file."""
        file_path = self.base_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        logger.info(f"Loaded YAML: {filename}")
        return data

    def load_protocol_rules(self) -> ProtocolRules:
        """Load and parse protocol rules."""
        data = self._load_yaml("protocol_rules.yaml")

        # Parse visits
        visits = [VisitWindow(**v) for v in data.get("schedule_of_assessments", {}).get("visits", [])]

        # Parse endpoints
        primary_ep = Endpoint(**data.get("endpoints", {}).get("primary", {}))
        secondary_eps = [
            Endpoint(**ep) for ep in data.get("endpoints", {}).get("secondary", [])
        ]

        return ProtocolRules(
            protocol_id=data.get("protocol", {}).get("id", ""),
            protocol_version=data.get("protocol", {}).get("version", ""),
            effective_date=data.get("protocol", {}).get("effective_date", ""),
            title=data.get("protocol", {}).get("title", ""),
            visits=visits,
            primary_endpoint=primary_ep,
            secondary_endpoints=secondary_eps,
            sample_size_target=data.get("sample_size", {}).get("target_enrollment", 50),
            sample_size_interim=data.get("sample_size", {}).get("interim_analysis", 25),
            safety_thresholds=data.get("safety_thresholds", {}),
            deviation_classification=data.get("deviation_classification", {}),
            inclusion_criteria=data.get("ie_criteria", {}).get("inclusion", []),
            exclusion_criteria=data.get("ie_criteria", {}).get("exclusion", []),
        )

    def load_literature_benchmarks(self) -> LiteratureBenchmarks:
        """Load and parse literature benchmarks."""
        data = self._load_yaml("literature_benchmarks.yaml")

        publications = []
        all_risk_factors = []

        for pub_id, pub_data in data.get("publications", {}).items():
            risk_factors = [RiskFactor(**rf) for rf in pub_data.get("risk_factors", [])]
            all_risk_factors.extend(risk_factors)

            publications.append(PublicationBenchmark(
                id=pub_id,
                title=pub_data.get("title", ""),
                year=pub_data.get("year", 0),
                n_patients=pub_data.get("n_patients"),
                follow_up_years=pub_data.get("follow_up_years"),
                benchmarks=pub_data.get("benchmarks", {}),
                risk_factors=risk_factors,
            ))

        return LiteratureBenchmarks(
            publications=publications,
            aggregate_benchmarks=data.get("aggregate_benchmarks", {}),
            all_risk_factors=all_risk_factors,
        )

    def load_registry_norms(self) -> RegistryNorms:
        """Load and parse registry norms with full multi-registry support."""
        data = self._load_yaml("registry_norms.yaml")

        # Load all registries with complete data
        registries = []
        for reg_id, reg_data in data.get("registries", {}).items():
            registries.append(RegistryBenchmark(
                id=reg_id,
                name=reg_data.get("name", reg_id),
                abbreviation=reg_data.get("abbreviation", reg_id.upper()),
                report_year=reg_data.get("report_year", 0),
                data_years=reg_data.get("data_years"),
                population=reg_data.get("population"),
                n_procedures=reg_data.get("n_procedures"),
                n_primary=reg_data.get("n_primary"),
                revision_burden=reg_data.get("revision_burden"),
                # Survival rates at all timepoints
                survival_1yr=reg_data.get("survival_1yr"),
                survival_2yr=reg_data.get("survival_2yr"),
                survival_5yr=reg_data.get("survival_5yr"),
                survival_10yr=reg_data.get("survival_10yr"),
                survival_15yr=reg_data.get("survival_15yr"),
                # Revision rates
                revision_rate_1yr=reg_data.get("revision_rate_1yr"),
                revision_rate_2yr=reg_data.get("revision_rate_2yr"),
                revision_rate_median=reg_data.get("revision_rate_median"),
                revision_rate_p75=reg_data.get("revision_rate_p75"),
                revision_rate_p95=reg_data.get("revision_rate_p95"),
                # Revision reasons and outcomes
                revision_reasons=reg_data.get("revision_reasons"),
                outcomes_by_indication=reg_data.get("outcomes_by_indication"),
            ))

        # Load pooled norms
        pooled_data = data.get("pooled_norms", {})
        pooled_norms = None
        if pooled_data:
            pooled_norms = PooledNorms(
                total_procedures=pooled_data.get("total_procedures", 0),
                total_registries=pooled_data.get("total_registries", 0),
                survival_rates=pooled_data.get("survival_rates", {}),
                revision_rates=pooled_data.get("revision_rates", {}),
                revision_reasons_pooled=pooled_data.get("revision_reasons_pooled", {}),
            )

        # Load comparative criteria
        criteria_data = data.get("comparative_criteria", {})
        comparative_criteria = None
        if criteria_data:
            perf_levels = {}
            for level_name, level_data in criteria_data.get("performance_levels", {}).items():
                perf_levels[level_name] = PerformanceLevel(
                    description=level_data.get("description", ""),
                    revision_rate_max=level_data.get("revision_rate_max"),
                    survival_2yr_min=level_data.get("survival_2yr_min"),
                )
            comparative_criteria = ComparativeCriteria(
                performance_levels=perf_levels,
                signal_thresholds=criteria_data.get("signal_thresholds", {}),
            )

        # Load device benchmarks
        device_data = data.get("device_benchmarks", {})
        device_benchmarks = {}
        for device_id, device_info in device_data.items():
            device_benchmarks[device_id] = DeviceBenchmark(
                description=device_info.get("description", ""),
                source=device_info.get("source", ""),
                survival_2yr=device_info.get("survival_2yr"),
                survival_5yr=device_info.get("survival_5yr"),
                revision_rate_2yr=device_info.get("revision_rate_2yr"),
                advantages=device_info.get("advantages", []),
                indications=device_info.get("indications", []),
                comparison_to_conventional=device_info.get("comparison_to_conventional", {}),
            )

        return RegistryNorms(
            registries=registries,
            pooled_norms=pooled_norms,
            concern_thresholds=data.get("concern_thresholds", {}),
            risk_thresholds=data.get("risk_thresholds", {}),
            comparative_criteria=comparative_criteria,
            device_benchmarks=device_benchmarks,
        )

    def clear_cache(self):
        """Clear the YAML cache."""
        self._load_yaml.cache_clear()
        logger.info("YAML cache cleared")


# Singleton instance
_loader: Optional[DocumentAsCodeLoader] = None


def get_doc_loader() -> DocumentAsCodeLoader:
    """Get singleton loader instance."""
    global _loader
    if _loader is None:
        _loader = DocumentAsCodeLoader()
    return _loader


class HybridLoader:
    """
    Hybrid loader that tries database first, then falls back to files.
    Provides seamless transition from file-based to database-backed storage.
    """

    def __init__(self):
        self._file_loader = get_doc_loader()
        self._db_loader = None

    def _get_db_loader(self):
        """Lazy-load database loader to avoid import issues."""
        if self._db_loader is None:
            try:
                from data.loaders.db_loader import get_db_loader
                self._db_loader = get_db_loader()
            except Exception as e:
                logger.warning(f"Database loader not available: {e}")
        return self._db_loader

    def load_protocol_rules(self) -> ProtocolRules:
        """Load protocol rules from DB or files."""
        db_loader = self._get_db_loader()
        if db_loader and db_loader.is_available():
            result = db_loader.load_protocol_rules()
            if result:
                logger.debug("Loaded protocol rules from database")
                return result
        logger.debug("Loading protocol rules from files (fallback)")
        return self._file_loader.load_protocol_rules()

    def load_literature_benchmarks(self) -> LiteratureBenchmarks:
        """Load literature benchmarks from DB or files."""
        db_loader = self._get_db_loader()
        if db_loader and db_loader.is_available():
            result = db_loader.load_literature_benchmarks()
            if result:
                logger.debug("Loaded literature benchmarks from database")
                return result
        logger.debug("Loading literature benchmarks from files (fallback)")
        return self._file_loader.load_literature_benchmarks()

    def load_registry_norms(self) -> RegistryNorms:
        """Load registry norms from DB or files."""
        db_loader = self._get_db_loader()
        if db_loader and db_loader.is_available():
            result = db_loader.load_registry_norms()
            if result:
                logger.debug("Loaded registry norms from database")
                return result
        logger.debug("Loading registry norms from files (fallback)")
        return self._file_loader.load_registry_norms()


_hybrid_loader: Optional[HybridLoader] = None


def get_hybrid_loader() -> HybridLoader:
    """Get singleton hybrid loader instance."""
    global _hybrid_loader
    if _hybrid_loader is None:
        _hybrid_loader = HybridLoader()
    return _hybrid_loader
