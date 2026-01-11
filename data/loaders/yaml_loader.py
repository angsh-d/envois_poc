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
    deviation_classification: Dict[str, Dict[str, str]]
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
    """Single registry benchmark."""
    name: str
    report_year: int
    population: Optional[str] = None
    n_procedures: Optional[int] = None
    survival_2yr: Optional[float] = None
    survival_5yr: Optional[float] = None
    revision_rate_median: Optional[float] = None
    revision_rate_p75: Optional[float] = None
    revision_rate_p95: Optional[float] = None
    revision_reasons: Optional[List[Dict[str, Any]]] = None


class RegistryNorms(BaseModel):
    """Complete registry norms structure."""
    registries: List[RegistryBenchmark]
    concern_thresholds: Dict[str, float]
    risk_thresholds: Dict[str, float]

    def get_primary_registry(self) -> Optional[RegistryBenchmark]:
        """Get primary registry (AOANJRR)."""
        for reg in self.registries:
            if "aoanjrr" in reg.name.lower():
                return reg
        return self.registries[0] if self.registries else None


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
        """Load and parse registry norms."""
        data = self._load_yaml("registry_norms.yaml")

        registries = []
        for reg_id, reg_data in data.get("registries", {}).items():
            registries.append(RegistryBenchmark(
                name=reg_data.get("name", reg_id),
                report_year=reg_data.get("report_year", 0),
                population=reg_data.get("population"),
                n_procedures=reg_data.get("n_procedures"),
                survival_2yr=reg_data.get("survival_2yr"),
                survival_5yr=reg_data.get("survival_5yr"),
                revision_rate_median=reg_data.get("revision_rate_median"),
                revision_rate_p75=reg_data.get("revision_rate_p75"),
                revision_rate_p95=reg_data.get("revision_rate_p95"),
                revision_reasons=reg_data.get("revision_reasons"),
            ))

        return RegistryNorms(
            registries=registries,
            concern_thresholds=data.get("concern_thresholds", {}),
            risk_thresholds=data.get("risk_thresholds", {}),
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
