"""
Registry Agent for Clinical Intelligence Platform.

Responsible for loading and comparing against population-level registry norms.
"""
import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from data.loaders.yaml_loader import (
    get_doc_loader, RegistryNorms, RegistryBenchmark
)

logger = logging.getLogger(__name__)


class RegistryAgent(BaseAgent):
    """
    Agent for registry norm extraction and comparison.

    Capabilities:
    - Load registry norms from Document-as-Code YAML
    - Compare study results to population benchmarks
    - Identify performance relative to registry percentiles
    - Flag results exceeding concern thresholds
    """

    agent_type = AgentType.REGISTRY

    def __init__(self, **kwargs):
        """Initialize registry agent."""
        super().__init__(**kwargs)
        self._loader = get_doc_loader()
        self._norms: Optional[RegistryNorms] = None

    def _load_norms(self) -> RegistryNorms:
        """Load registry norms with caching."""
        if self._norms is None:
            self._norms = self._loader.load_registry_norms()
        return self._norms

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute registry norm extraction.

        Args:
            context: Execution context with query parameters

        Returns:
            AgentResult with registry benchmark data
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        norms = self._load_norms()
        query_type = context.parameters.get("query_type", "all")

        if query_type == "all":
            result.data = self._get_all_norms(norms)
        elif query_type == "primary":
            result.data = self._get_primary_registry(norms)
        elif query_type == "thresholds":
            result.data = self._get_thresholds(norms)
        elif query_type == "compare":
            result.data = self._compare_to_registry(context, norms)
        elif query_type == "percentile":
            result.data = self._get_percentile_position(context, norms)
        else:
            result.success = False
            result.error = f"Unknown query_type: {query_type}"
            return result

        # Add source
        primary = norms.get_primary_registry()
        source_name = primary.name if primary else "Registry norms"
        result.add_source(
            SourceType.REGISTRY,
            f"{source_name} ({len(norms.registries)} registries)",
            confidence=0.95,
            details={"n_registries": len(norms.registries)}
        )

        return result

    def _get_all_norms(self, norms: RegistryNorms) -> Dict[str, Any]:
        """Get all registry norms."""
        return {
            "n_registries": len(norms.registries),
            "registries": [
                {
                    "name": reg.name,
                    "report_year": reg.report_year,
                    "n_procedures": reg.n_procedures,
                    "survival_2yr": reg.survival_2yr,
                    "survival_5yr": reg.survival_5yr,
                    "revision_rate_median": reg.revision_rate_median,
                }
                for reg in norms.registries
            ],
            "concern_thresholds": norms.concern_thresholds,
            "risk_thresholds": norms.risk_thresholds,
        }

    def _get_primary_registry(self, norms: RegistryNorms) -> Dict[str, Any]:
        """Get primary registry data (AOANJRR)."""
        primary = norms.get_primary_registry()
        if not primary:
            return {"error": "No primary registry found"}

        return {
            "name": primary.name,
            "report_year": primary.report_year,
            "population": primary.population,
            "n_procedures": primary.n_procedures,
            "survival_2yr": primary.survival_2yr,
            "survival_5yr": primary.survival_5yr,
            "revision_rate_median": primary.revision_rate_median,
            "revision_rate_p75": primary.revision_rate_p75,
            "revision_rate_p95": primary.revision_rate_p95,
            "revision_reasons": primary.revision_reasons,
        }

    def _get_thresholds(self, norms: RegistryNorms) -> Dict[str, Any]:
        """Get concern and risk thresholds."""
        return {
            "concern_thresholds": norms.concern_thresholds,
            "risk_thresholds": norms.risk_thresholds,
        }

    def _compare_to_registry(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """Compare study results to registry benchmarks."""
        study_data = context.parameters.get("study_data", {})
        primary = norms.get_primary_registry()

        if not primary:
            return {"error": "No primary registry found"}

        comparisons = []
        signals = []

        # Compare revision rate
        if "revision_rate" in study_data:
            study_rate = study_data["revision_rate"]
            comparison = self._compare_metric(
                "revision_rate",
                study_rate,
                primary.revision_rate_median,
                primary.revision_rate_p75,
                primary.revision_rate_p95,
                norms.concern_thresholds.get("revision_rate_2yr"),
                norms.risk_thresholds.get("revision_rate_2yr"),
                lower_is_better=True
            )
            comparisons.append(comparison)
            if comparison.get("signal"):
                signals.append(comparison)

        # Compare survival rate
        if "survival_2yr" in study_data:
            study_rate = study_data["survival_2yr"]
            median_survival = primary.survival_2yr or 0.94
            comparison = {
                "metric": "survival_2yr",
                "study_value": study_rate,
                "registry_median": median_survival,
                "difference": round(study_rate - median_survival, 4),
                "favorable": study_rate >= median_survival,
                "signal": study_rate < 0.90,
                "signal_level": "risk" if study_rate < 0.90 else None,
            }
            comparisons.append(comparison)
            if comparison["signal"]:
                signals.append(comparison)

        return {
            "comparisons": comparisons,
            "signals": signals,
            "n_signals": len(signals),
            "registry_source": primary.name,
            "registry_year": primary.report_year,
        }

    def _compare_metric(
        self,
        metric: str,
        study_value: float,
        median: Optional[float],
        p75: Optional[float],
        p95: Optional[float],
        concern_threshold: Optional[float],
        risk_threshold: Optional[float],
        lower_is_better: bool = True
    ) -> Dict[str, Any]:
        """Compare a single metric to registry benchmarks."""
        comparison = {
            "metric": metric,
            "study_value": study_value,
            "registry_median": median,
            "registry_p75": p75,
            "registry_p95": p95,
            "signal": False,
            "signal_level": None,
        }

        if median:
            comparison["difference"] = round(study_value - median, 4)
            if lower_is_better:
                comparison["favorable"] = study_value <= median
            else:
                comparison["favorable"] = study_value >= median

        # Determine percentile position
        if p95 and study_value > p95:
            comparison["percentile_position"] = ">95th"
        elif p75 and study_value > p75:
            comparison["percentile_position"] = "75th-95th"
        elif median and study_value > median:
            comparison["percentile_position"] = "50th-75th"
        else:
            comparison["percentile_position"] = "<50th"

        # Check thresholds
        if risk_threshold and study_value >= risk_threshold:
            comparison["signal"] = True
            comparison["signal_level"] = "risk"
        elif concern_threshold and study_value >= concern_threshold:
            comparison["signal"] = True
            comparison["signal_level"] = "concern"

        return comparison

    def _get_percentile_position(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """Determine where study falls in registry distribution."""
        metric = context.parameters.get("metric")
        value = context.parameters.get("value")

        if not metric or value is None:
            return {"error": "metric and value parameters required"}

        primary = norms.get_primary_registry()
        if not primary:
            return {"error": "No primary registry found"}

        # Map metrics to registry attributes
        metric_map = {
            "revision_rate": ("revision_rate_median", "revision_rate_p75", "revision_rate_p95"),
            "survival_2yr": ("survival_2yr", None, None),
        }

        if metric not in metric_map:
            return {"error": f"Unknown metric: {metric}"}

        median_attr, p75_attr, p95_attr = metric_map[metric]

        result = {
            "metric": metric,
            "value": value,
            "registry_median": getattr(primary, median_attr, None),
        }

        if p75_attr:
            result["registry_p75"] = getattr(primary, p75_attr, None)
        if p95_attr:
            result["registry_p95"] = getattr(primary, p95_attr, None)

        # Determine position
        median = result.get("registry_median")
        p75 = result.get("registry_p75")
        p95 = result.get("registry_p95")

        if p95 and value > p95:
            result["position"] = "above_95th"
            result["description"] = "Above 95th percentile - exceptional outcome"
        elif p75 and value > p75:
            result["position"] = "75th_to_95th"
            result["description"] = "Between 75th and 95th percentile"
        elif median and value > median:
            result["position"] = "50th_to_75th"
            result["description"] = "Between median and 75th percentile"
        elif median:
            result["position"] = "below_50th"
            result["description"] = "Below median"
        else:
            result["position"] = "unknown"

        return result

    def get_concern_threshold(self, metric: str) -> Optional[float]:
        """Get concern threshold for a metric."""
        norms = self._load_norms()
        return norms.concern_thresholds.get(metric)

    def get_risk_threshold(self, metric: str) -> Optional[float]:
        """Get risk threshold for a metric."""
        norms = self._load_norms()
        return norms.risk_thresholds.get(metric)

    def check_signal(
        self,
        metric: str,
        value: float
    ) -> Dict[str, Any]:
        """Check if a value triggers a signal against registry thresholds."""
        norms = self._load_norms()

        concern = norms.concern_thresholds.get(metric)
        risk = norms.risk_thresholds.get(metric)

        result = {
            "metric": metric,
            "value": value,
            "concern_threshold": concern,
            "risk_threshold": risk,
            "signal": False,
            "level": None,
        }

        if risk and value >= risk:
            result["signal"] = True
            result["level"] = "risk"
        elif concern and value >= concern:
            result["signal"] = True
            result["level"] = "concern"

        return result
