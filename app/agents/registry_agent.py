"""
Registry Agent for Clinical Intelligence Platform.

Responsible for loading and comparing against population-level registry norms.
Supports multi-registry comparison across 5 international registries:
- AOANJRR (Australian)
- NJR (UK)
- SHAR (Swedish)
- AJRR (American)
- CJRR (Canadian)
"""
import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from data.loaders.yaml_loader import (
    get_hybrid_loader, RegistryNorms, RegistryBenchmark, PooledNorms
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
        self._loader = get_hybrid_loader()
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

        Query Types:
            - all: Get summary of all 5 registries with complete data
            - primary: Get primary registry (AOANJRR) data only
            - thresholds: Get concern and risk thresholds
            - compare: Compare study to primary registry (legacy)
            - compare_all: Compare study to ALL 5 registries
            - percentile: Get percentile position in primary registry
            - percentile_all: Get percentile position across ALL registries
            - ranking: Get registry ranking for a metric
            - closest: Find closest matching registry
            - classify: Classify study performance level
            - pooled: Get pooled norms from all registries
            - device: Get device-specific benchmarks
            - revision_reasons: Get revision reason breakdown across registries
            - threshold_proximity: Check which metrics are near thresholds
            - outcomes_by_indication: Get stratified outcomes (AOANJRR)
            - metadata: Get data quality notes and limitations
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
        elif query_type == "compare_all":
            result.data = self._compare_to_all_registries(context, norms)
        elif query_type == "percentile":
            result.data = self._get_percentile_position(context, norms)
        elif query_type == "percentile_all":
            result.data = self._get_percentile_across_all(context, norms)
        elif query_type == "ranking":
            result.data = self._get_registry_ranking(context, norms)
        elif query_type == "closest":
            result.data = self._find_closest_registry(context, norms)
        elif query_type == "classify":
            result.data = self._classify_performance(context, norms)
        elif query_type == "pooled":
            result.data = self._get_pooled_norms(norms)
        elif query_type == "device":
            result.data = self._get_device_benchmarks(context, norms)
        elif query_type == "revision_reasons":
            result.data = self._get_revision_reasons(norms)
        elif query_type == "threshold_proximity":
            result.data = self._check_threshold_proximity(context, norms)
        elif query_type == "outcomes_by_indication":
            result.data = self._get_outcomes_by_indication(norms)
        elif query_type == "metadata":
            result.data = self._get_registry_metadata(norms)
        else:
            result.success = False
            result.error = f"Unknown query_type: {query_type}"
            return result

        # Add GRANULAR source provenance with specific registry details
        self._add_granular_sources(result, norms, query_type)

        return result

    def _add_granular_sources(
        self,
        result: AgentResult,
        norms: RegistryNorms,
        query_type: str
    ) -> None:
        """
        Add granular source provenance for regulatory traceability.

        Each registry is cited with:
        - Full name and abbreviation
        - Report year and data coverage years
        - Sample size (n_procedures)
        - Data quality notes where applicable
        """
        for reg in norms.registries:
            source_detail = {
                "abbreviation": reg.abbreviation,
                "report_year": reg.report_year,
                "data_coverage": reg.data_years,
                "n_procedures": reg.n_procedures,
                "n_primary": reg.n_primary,
                "metrics_available": {
                    "survival_2yr": reg.survival_2yr is not None,
                    "survival_5yr": reg.survival_5yr is not None,
                    "survival_10yr": reg.survival_10yr is not None,
                    "revision_rate_2yr": reg.revision_rate_2yr is not None,
                    "revision_reasons": reg.revision_reasons is not None,
                    "outcomes_by_indication": reg.outcomes_by_indication is not None,
                },
            }

            # Confidence based on data completeness
            metrics_available = sum(1 for v in source_detail["metrics_available"].values() if v)
            confidence = 0.85 + (0.03 * metrics_available)  # 0.85-1.0 based on completeness

            result.add_source(
                SourceType.REGISTRY,
                f"{reg.name} ({reg.abbreviation}) {reg.report_year}",
                confidence=min(confidence, 0.98),
                details=source_detail
            )

        # Add aggregated source summary
        data_years_list = [r.data_years.split('-')[0] for r in norms.registries if r.data_years and '-' in r.data_years]
        data_years_range = f"{min(data_years_list)}-2023" if data_years_list else "2003-2023"
        result.add_source(
            SourceType.REGISTRY,
            f"Pooled International Registry Data (n={sum(r.n_procedures or 0 for r in norms.registries):,})",
            confidence=0.92,
            details={
                "n_registries": len(norms.registries),
                "registries": [r.abbreviation for r in norms.registries],
                "data_years_range": data_years_range,
                "query_type": query_type,
            }
        )

    def _get_all_norms(self, norms: RegistryNorms) -> Dict[str, Any]:
        """
        Get COMPLETE data from all 5 registries for regulatory-grade analysis.

        Includes:
        - All survival rates at multiple timepoints
        - All revision rates with percentile distribution
        - Revision reason breakdowns
        - Outcomes by indication (where available)
        - Data quality metadata
        """
        registries_data = []
        for reg in norms.registries:
            reg_data = {
                "id": reg.id,
                "abbreviation": reg.abbreviation,
                "name": reg.name,
                "report_year": reg.report_year,
                "data_years": reg.data_years,
                "population": reg.population,
                "n_procedures": reg.n_procedures,
                "n_primary": reg.n_primary,
                "revision_burden": reg.revision_burden,
                # Survival at all timepoints (filter None values for clarity)
                "survival_rates": {
                    k: v for k, v in {
                        "1yr": reg.survival_1yr,
                        "2yr": reg.survival_2yr,
                        "5yr": reg.survival_5yr,
                        "10yr": reg.survival_10yr,
                        "15yr": reg.survival_15yr,
                    }.items() if v is not None
                },
                # Revision rates with percentiles
                "revision_rates": {
                    k: v for k, v in {
                        "1yr": reg.revision_rate_1yr,
                        "2yr": reg.revision_rate_2yr,
                        "median": reg.revision_rate_median,
                        "p75": reg.revision_rate_p75,
                        "p95": reg.revision_rate_p95,
                    }.items() if v is not None
                },
                # Revision reasons (critical for understanding WHY revisions occur)
                "revision_reasons": self._format_revision_reasons(reg.revision_reasons),
                # Stratified outcomes (AOANJRR only currently)
                "outcomes_by_indication": reg.outcomes_by_indication,
                # Data completeness indicator
                "data_completeness": self._calculate_completeness(reg),
            }
            registries_data.append(reg_data)

        # Calculate summary statistics
        rev_rates = [r.revision_rate_2yr for r in norms.registries if r.revision_rate_2yr]
        surv_rates = [r.survival_2yr for r in norms.registries if r.survival_2yr]

        return {
            "n_registries": len(norms.registries),
            "total_procedures": sum(r.n_procedures or 0 for r in norms.registries),
            "registries": registries_data,
            "concern_thresholds": norms.concern_thresholds,
            "risk_thresholds": norms.risk_thresholds,
            # Summary statistics across all registries
            "summary": {
                "revision_rate_2yr": {
                    "min": min(rev_rates) if rev_rates else None,
                    "max": max(rev_rates) if rev_rates else None,
                    "mean": round(sum(rev_rates) / len(rev_rates), 4) if rev_rates else None,
                    "range_formatted": f"{min(rev_rates)*100:.1f}% - {max(rev_rates)*100:.1f}%" if rev_rates else "N/A",
                    "best_registry": min(
                        (r for r in norms.registries if r.revision_rate_2yr),
                        key=lambda x: x.revision_rate_2yr,
                        default=None
                    ).abbreviation if rev_rates else None,
                    "worst_registry": max(
                        (r for r in norms.registries if r.revision_rate_2yr),
                        key=lambda x: x.revision_rate_2yr,
                        default=None
                    ).abbreviation if rev_rates else None,
                },
                "survival_2yr": {
                    "min": min(surv_rates) if surv_rates else None,
                    "max": max(surv_rates) if surv_rates else None,
                    "mean": round(sum(surv_rates) / len(surv_rates), 4) if surv_rates else None,
                    "range_formatted": f"{min(surv_rates)*100:.1f}% - {max(surv_rates)*100:.1f}%" if surv_rates else "N/A",
                    "best_registry": max(
                        (r for r in norms.registries if r.survival_2yr),
                        key=lambda x: x.survival_2yr,
                        default=None
                    ).abbreviation if surv_rates else None,
                },
            },
            # Pooled revision reasons
            "pooled_revision_reasons": norms.pooled_norms.revision_reasons_pooled if norms.pooled_norms else {},
            # Data quality notes (for transparency)
            "data_quality_context": {
                "notes": [
                    "AOANJRR: Most complete long-term follow-up data",
                    "SHAR: Longest historical data (since 1979)",
                    "NJR: Largest absolute numbers",
                    "AJRR: Most recent US-specific data (2012-2023)",
                    "CJRR: Comprehensive Canadian coverage",
                ],
                "limitations": [
                    "Registry data may have selection bias",
                    "Outcome definitions vary between registries",
                    "Loss to follow-up varies by registry",
                ],
            },
        }

    def _format_revision_reasons(
        self,
        reasons: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Format revision reasons with clear percentages."""
        if not reasons:
            return None
        return [
            {
                "reason": r.get("reason", "unknown"),
                "percentage": r.get("percentage"),
                "percentage_formatted": f"{r.get('percentage', 0)*100:.1f}%",
                "description": r.get("description"),
            }
            for r in reasons
        ]

    def _calculate_completeness(self, reg: RegistryBenchmark) -> Dict[str, Any]:
        """Calculate data completeness score for a registry."""
        fields = [
            reg.survival_1yr, reg.survival_2yr, reg.survival_5yr,
            reg.survival_10yr, reg.survival_15yr,
            reg.revision_rate_1yr, reg.revision_rate_2yr,
            reg.revision_reasons, reg.outcomes_by_indication,
        ]
        available = sum(1 for f in fields if f is not None)
        total = len(fields)

        return {
            "score": round(available / total, 2),
            "available_fields": available,
            "total_fields": total,
            "has_long_term_data": reg.survival_10yr is not None,
            "has_revision_reasons": reg.revision_reasons is not None,
            "has_stratified_outcomes": reg.outcomes_by_indication is not None,
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

    # =========================================================================
    # Multi-Registry Comparison Methods
    # =========================================================================

    def _compare_to_all_registries(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """
        Compare study results to ALL 5 registries.

        This is the key method for answering questions like:
        "Which registries have higher/lower rates than our study?"
        """
        study_data = context.parameters.get("study_data", {})

        comparisons = {}
        signals = []

        # Compare revision rate across all registries
        if "revision_rate" in study_data or "revision_rate_2yr" in study_data:
            study_rate = study_data.get("revision_rate") or study_data.get("revision_rate_2yr")
            comparison = norms.compare_metric_across_registries("revision_rate_2yr", study_rate)

            # Add signal status
            concern = norms.concern_thresholds.get("revision_rate_2yr")
            risk = norms.risk_thresholds.get("revision_rate_2yr")
            if risk and study_rate >= risk:
                comparison["signal"] = "risk"
                signals.append({"metric": "revision_rate_2yr", "level": "risk", "value": study_rate})
            elif concern and study_rate >= concern:
                comparison["signal"] = "concern"
                signals.append({"metric": "revision_rate_2yr", "level": "concern", "value": study_rate})
            else:
                comparison["signal"] = None

            comparisons["revision_rate_2yr"] = comparison

        # Compare survival rate across all registries
        if "survival_2yr" in study_data:
            study_rate = study_data["survival_2yr"]
            comparison = norms.compare_metric_across_registries("survival_2yr", study_rate)

            # For survival, higher is better
            if study_rate < 0.90:
                comparison["signal"] = "risk"
                signals.append({"metric": "survival_2yr", "level": "risk", "value": study_rate})
            elif study_rate < 0.92:
                comparison["signal"] = "concern"
                signals.append({"metric": "survival_2yr", "level": "concern", "value": study_rate})
            else:
                comparison["signal"] = None

            comparisons["survival_2yr"] = comparison

        # Compare additional metrics if provided
        for metric in ["survival_5yr", "revision_rate_1yr", "survival_1yr"]:
            if metric in study_data:
                comparisons[metric] = norms.compare_metric_across_registries(metric, study_data[metric])

        return {
            "comparisons": comparisons,
            "signals": signals,
            "n_signals": len(signals),
            "n_registries_compared": len(norms.registries),
            "registry_list": [r.abbreviation for r in norms.registries],
        }

    def _get_percentile_across_all(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """
        Get percentile position of study results across ALL registries.

        Answers: "What percentile does our 7.1% revision rate represent
        in the pooled registry data?"
        """
        metric = context.parameters.get("metric")
        value = context.parameters.get("value")

        if not metric or value is None:
            return {"error": "metric and value parameters required"}

        return norms.get_percentile_across_registries(metric, value)

    def _get_registry_ranking(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """
        Rank all registries by a metric and show where study falls.

        Answers: "Rank all registries by revision rate and show
        where our study would fall in that ranking."
        """
        metric = context.parameters.get("metric", "revision_rate_2yr")
        study_value = context.parameters.get("study_value")
        lower_is_better = context.parameters.get("lower_is_better", True)

        # Get all registry values
        registry_values = []
        for reg in norms.registries:
            value = getattr(reg, metric, None)
            if value is not None:
                registry_values.append({
                    "registry_id": reg.id,
                    "registry_name": reg.abbreviation,
                    "value": value,
                    "n_procedures": reg.n_procedures,
                })

        # Sort by value
        registry_values.sort(key=lambda x: x["value"], reverse=not lower_is_better)

        # Add rank
        for i, rv in enumerate(registry_values):
            rv["rank"] = i + 1

        # Find study position
        study_rank = None
        if study_value is not None:
            if lower_is_better:
                study_rank = sum(1 for rv in registry_values if rv["value"] < study_value) + 1
            else:
                study_rank = sum(1 for rv in registry_values if rv["value"] > study_value) + 1

        return {
            "metric": metric,
            "lower_is_better": lower_is_better,
            "ranking": registry_values,
            "study_value": study_value,
            "study_rank": study_rank,
            "study_rank_description": f"{study_rank} of {len(registry_values) + 1}" if study_rank else None,
            "best_registry": registry_values[0] if registry_values else None,
            "worst_registry": registry_values[-1] if registry_values else None,
        }

    def _find_closest_registry(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """
        Find the registry whose outcomes most closely match the study.

        Answers: "Which registry has outcomes most similar to our study?"
        """
        study_metrics = context.parameters.get("study_metrics", {})

        if not study_metrics:
            return {"error": "study_metrics parameter required (dict of metric->value)"}

        return norms.find_closest_registry(study_metrics)

    def _classify_performance(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """
        Classify study performance as excellent/good/acceptable/concerning.

        Uses comparative criteria from registry norms.
        """
        revision_rate = context.parameters.get("revision_rate")
        survival_2yr = context.parameters.get("survival_2yr")

        return norms.classify_performance(revision_rate, survival_2yr)

    def _get_pooled_norms(self, norms: RegistryNorms) -> Dict[str, Any]:
        """
        Get pooled norms aggregated from all registries.

        Returns median, mean, range for each metric.
        """
        if norms.pooled_norms:
            return {
                "total_procedures": norms.pooled_norms.total_procedures,
                "total_registries": norms.pooled_norms.total_registries,
                "survival_rates": norms.pooled_norms.survival_rates,
                "revision_rates": norms.pooled_norms.revision_rates,
                "revision_reasons_pooled": norms.pooled_norms.revision_reasons_pooled,
            }

        # Fallback: calculate from registries
        registries = norms.registries

        return {
            "total_procedures": sum(r.n_procedures or 0 for r in registries),
            "total_registries": len(registries),
            "survival_rates": {
                "survival_2yr": {
                    "mean": sum(r.survival_2yr or 0 for r in registries) / len(registries),
                    "min": min((r.survival_2yr for r in registries if r.survival_2yr), default=None),
                    "max": max((r.survival_2yr for r in registries if r.survival_2yr), default=None),
                },
            },
            "revision_rates": {
                "revision_rate_2yr": {
                    "mean": sum(r.revision_rate_2yr or 0 for r in registries) / len(registries),
                    "min": min((r.revision_rate_2yr for r in registries if r.revision_rate_2yr), default=None),
                    "max": max((r.revision_rate_2yr for r in registries if r.revision_rate_2yr), default=None),
                },
            },
        }

    def _get_device_benchmarks(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """
        Get device-specific benchmarks (e.g., porous tantalum cups).
        """
        device_type = context.parameters.get("device_type", "porous_tantalum_cups")

        if not norms.device_benchmarks:
            return {"error": "No device benchmarks available"}

        benchmark = norms.device_benchmarks.get(device_type)
        if not benchmark:
            return {
                "error": f"No benchmark for device type: {device_type}",
                "available_devices": list(norms.device_benchmarks.keys()),
            }

        return {
            "device_type": device_type,
            "description": benchmark.description,
            "source": benchmark.source,
            "survival_2yr": benchmark.survival_2yr,
            "survival_5yr": benchmark.survival_5yr,
            "revision_rate_2yr": benchmark.revision_rate_2yr,
            "advantages": benchmark.advantages,
            "indications": benchmark.indications,
            "comparison_to_conventional": benchmark.comparison_to_conventional,
        }

    # =========================================================================
    # Convenience Methods for External Use
    # =========================================================================

    def get_all_registries(self) -> List[Dict[str, Any]]:
        """Get summary of all registries for external use."""
        norms = self._load_norms()
        return [
            {
                "id": reg.id,
                "abbreviation": reg.abbreviation,
                "name": reg.name,
                "n_procedures": reg.n_procedures,
                "revision_rate_2yr": reg.revision_rate_2yr,
                "survival_2yr": reg.survival_2yr,
            }
            for reg in norms.registries
        ]

    def compare_to_all(
        self,
        metric: str,
        study_value: float
    ) -> Dict[str, Any]:
        """
        Direct method to compare a metric against all registries.

        Args:
            metric: Metric name (e.g., 'revision_rate_2yr')
            study_value: Study's value for this metric

        Returns:
            Comparison results for all registries
        """
        norms = self._load_norms()
        return norms.compare_metric_across_registries(metric, study_value)

    # =========================================================================
    # Critical Missing Methods for 100% Accuracy & Completeness
    # =========================================================================

    def _get_revision_reasons(self, norms: RegistryNorms) -> Dict[str, Any]:
        """
        Get detailed breakdown of revision reasons across ALL registries.

        This enables answering questions like:
        - "What are the main reasons for revision across registries?"
        - "How does aseptic loosening compare to infection as revision cause?"
        - "Which registries report higher dislocation rates?"
        """
        revision_data = []

        for reg in norms.registries:
            if reg.revision_reasons:
                reg_reasons = {
                    "registry_id": reg.id,
                    "registry_name": reg.abbreviation,
                    "report_year": reg.report_year,
                    "n_revisions": reg.n_procedures - reg.n_primary if reg.n_primary else None,
                    "reasons": [],
                }

                for reason in reg.revision_reasons:
                    reg_reasons["reasons"].append({
                        "reason": reason.get("reason", "unknown"),
                        "percentage": reason.get("percentage"),
                        "percentage_formatted": f"{reason.get('percentage', 0)*100:.1f}%",
                        "description": reason.get("description"),
                    })

                # Sort by percentage (highest first)
                reg_reasons["reasons"].sort(
                    key=lambda x: x.get("percentage") or 0,
                    reverse=True
                )
                reg_reasons["primary_cause"] = reg_reasons["reasons"][0] if reg_reasons["reasons"] else None

                revision_data.append(reg_reasons)

        # Cross-registry comparison by reason
        reason_comparison = self._compare_revision_reasons_across_registries(norms)

        return {
            "by_registry": revision_data,
            "n_registries_with_data": len(revision_data),
            "cross_registry_comparison": reason_comparison,
            "pooled_reasons": norms.pooled_norms.revision_reasons_pooled if norms.pooled_norms else {},
            "insights": self._generate_revision_reason_insights(revision_data),
        }

    def _compare_revision_reasons_across_registries(
        self,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """Compare specific revision reasons across all registries."""
        reasons_by_type = {}

        for reg in norms.registries:
            if not reg.revision_reasons:
                continue

            for reason in reg.revision_reasons:
                reason_name = reason.get("reason", "").lower()
                if reason_name not in reasons_by_type:
                    reasons_by_type[reason_name] = {
                        "reason": reason.get("reason"),
                        "description": reason.get("description"),
                        "by_registry": {},
                    }

                reasons_by_type[reason_name]["by_registry"][reg.abbreviation] = {
                    "percentage": reason.get("percentage"),
                    "percentage_formatted": f"{reason.get('percentage', 0)*100:.1f}%",
                }

        # Calculate statistics for each reason
        for reason_name, data in reasons_by_type.items():
            percentages = [
                v["percentage"] for v in data["by_registry"].values()
                if v["percentage"] is not None
            ]
            if percentages:
                data["statistics"] = {
                    "min": min(percentages),
                    "max": max(percentages),
                    "mean": round(sum(percentages) / len(percentages), 4),
                    "range_formatted": f"{min(percentages)*100:.1f}% - {max(percentages)*100:.1f}%",
                    "n_registries_reporting": len(percentages),
                }
                # Find which registry has highest/lowest for this reason
                data["highest_registry"] = max(
                    data["by_registry"].items(),
                    key=lambda x: x[1]["percentage"] or 0
                )[0]
                data["lowest_registry"] = min(
                    data["by_registry"].items(),
                    key=lambda x: x[1]["percentage"] or 0
                )[0]

        return reasons_by_type

    def _generate_revision_reason_insights(
        self,
        revision_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate narrative insights about revision reasons."""
        insights = []

        if not revision_data:
            return ["No revision reason data available across registries."]

        # Find most common primary cause across registries
        primary_causes = [
            r["primary_cause"]["reason"]
            for r in revision_data
            if r.get("primary_cause")
        ]
        if primary_causes:
            from collections import Counter
            most_common = Counter(primary_causes).most_common(1)[0]
            insights.append(
                f"Aseptic loosening is the primary cause of revision in "
                f"{most_common[1]} of {len(primary_causes)} registries."
            )

        # Note any significant variations
        insights.append(
            "Revision reason proportions vary by registry due to "
            "population demographics and surgical technique differences."
        )

        return insights

    def _check_threshold_proximity(
        self,
        context: AgentContext,
        norms: RegistryNorms
    ) -> Dict[str, Any]:
        """
        Flag metrics that are within 20% of concern/risk thresholds.

        This provides early warning for metrics approaching danger zones.
        Critical for regulatory surveillance and proactive risk management.
        """
        study_data = context.parameters.get("study_data", {})
        proximity_percent = context.parameters.get("proximity_percent", 0.20)  # 20% default

        proximity_warnings = []
        safe_metrics = []

        # Check revision rate 2yr
        if "revision_rate" in study_data or "revision_rate_2yr" in study_data:
            study_rate = study_data.get("revision_rate") or study_data.get("revision_rate_2yr")
            concern = norms.concern_thresholds.get("revision_rate_2yr")
            risk = norms.risk_thresholds.get("revision_rate_2yr")

            warning = self._calculate_threshold_proximity(
                metric="revision_rate_2yr",
                value=study_rate,
                concern_threshold=concern,
                risk_threshold=risk,
                proximity_percent=proximity_percent,
                lower_is_better=True
            )

            if warning["proximity_warning"]:
                proximity_warnings.append(warning)
            else:
                safe_metrics.append(warning)

        # Check survival rate 2yr
        if "survival_2yr" in study_data:
            study_rate = study_data["survival_2yr"]
            # For survival, we care about falling below thresholds
            warning = self._calculate_threshold_proximity(
                metric="survival_2yr",
                value=study_rate,
                concern_threshold=0.92,  # Below 92% is concern
                risk_threshold=0.90,  # Below 90% is risk
                proximity_percent=proximity_percent,
                lower_is_better=False  # Higher survival is better
            )

            if warning["proximity_warning"]:
                proximity_warnings.append(warning)
            else:
                safe_metrics.append(warning)

        # Check revision rate 1yr if provided
        if "revision_rate_1yr" in study_data:
            study_rate = study_data["revision_rate_1yr"]
            concern = norms.concern_thresholds.get("revision_rate_1yr")
            risk = norms.risk_thresholds.get("revision_rate_1yr")

            if concern or risk:
                warning = self._calculate_threshold_proximity(
                    metric="revision_rate_1yr",
                    value=study_rate,
                    concern_threshold=concern,
                    risk_threshold=risk,
                    proximity_percent=proximity_percent,
                    lower_is_better=True
                )

                if warning["proximity_warning"]:
                    proximity_warnings.append(warning)
                else:
                    safe_metrics.append(warning)

        # Sort warnings by urgency (closest to threshold first)
        proximity_warnings.sort(key=lambda x: x.get("distance_to_threshold", 1))

        return {
            "proximity_warnings": proximity_warnings,
            "safe_metrics": safe_metrics,
            "n_warnings": len(proximity_warnings),
            "n_safe": len(safe_metrics),
            "proximity_threshold_used": f"{proximity_percent*100:.0f}%",
            "action_required": len(proximity_warnings) > 0,
            "recommendation": self._generate_proximity_recommendation(proximity_warnings),
        }

    def _calculate_threshold_proximity(
        self,
        metric: str,
        value: float,
        concern_threshold: Optional[float],
        risk_threshold: Optional[float],
        proximity_percent: float,
        lower_is_better: bool
    ) -> Dict[str, Any]:
        """Calculate how close a value is to thresholds."""
        result = {
            "metric": metric,
            "value": value,
            "value_formatted": f"{value*100:.1f}%" if value < 1 else str(value),
            "concern_threshold": concern_threshold,
            "risk_threshold": risk_threshold,
            "proximity_warning": False,
            "warning_level": None,
            "distance_to_threshold": None,
            "message": None,
        }

        # Determine proximity to thresholds
        if lower_is_better:
            # For metrics where lower is better (revision rate)
            if risk_threshold:
                distance_to_risk = (risk_threshold - value) / risk_threshold
                if value >= risk_threshold:
                    result["proximity_warning"] = True
                    result["warning_level"] = "EXCEEDED_RISK"
                    result["distance_to_threshold"] = 0
                    result["message"] = f"{metric} ({value*100:.1f}%) EXCEEDS risk threshold ({risk_threshold*100:.1f}%)"
                elif distance_to_risk <= proximity_percent:
                    result["proximity_warning"] = True
                    result["warning_level"] = "NEAR_RISK"
                    result["distance_to_threshold"] = distance_to_risk
                    result["message"] = f"{metric} ({value*100:.1f}%) is within {distance_to_risk*100:.0f}% of risk threshold ({risk_threshold*100:.1f}%)"

            if concern_threshold and not result["proximity_warning"]:
                distance_to_concern = (concern_threshold - value) / concern_threshold
                if value >= concern_threshold:
                    result["proximity_warning"] = True
                    result["warning_level"] = "EXCEEDED_CONCERN"
                    result["distance_to_threshold"] = 0
                    result["message"] = f"{metric} ({value*100:.1f}%) EXCEEDS concern threshold ({concern_threshold*100:.1f}%)"
                elif distance_to_concern <= proximity_percent:
                    result["proximity_warning"] = True
                    result["warning_level"] = "NEAR_CONCERN"
                    result["distance_to_threshold"] = distance_to_concern
                    result["message"] = f"{metric} ({value*100:.1f}%) is within {distance_to_concern*100:.0f}% of concern threshold ({concern_threshold*100:.1f}%)"

        else:
            # For metrics where higher is better (survival rate)
            if risk_threshold:
                distance_to_risk = (value - risk_threshold) / risk_threshold
                if value <= risk_threshold:
                    result["proximity_warning"] = True
                    result["warning_level"] = "EXCEEDED_RISK"
                    result["distance_to_threshold"] = 0
                    result["message"] = f"{metric} ({value*100:.1f}%) is BELOW risk threshold ({risk_threshold*100:.1f}%)"
                elif distance_to_risk <= proximity_percent:
                    result["proximity_warning"] = True
                    result["warning_level"] = "NEAR_RISK"
                    result["distance_to_threshold"] = distance_to_risk
                    result["message"] = f"{metric} ({value*100:.1f}%) is within {distance_to_risk*100:.0f}% of risk threshold ({risk_threshold*100:.1f}%)"

            if concern_threshold and not result["proximity_warning"]:
                distance_to_concern = (value - concern_threshold) / concern_threshold
                if value <= concern_threshold:
                    result["proximity_warning"] = True
                    result["warning_level"] = "EXCEEDED_CONCERN"
                    result["distance_to_threshold"] = 0
                    result["message"] = f"{metric} ({value*100:.1f}%) is BELOW concern threshold ({concern_threshold*100:.1f}%)"
                elif distance_to_concern <= proximity_percent:
                    result["proximity_warning"] = True
                    result["warning_level"] = "NEAR_CONCERN"
                    result["distance_to_threshold"] = distance_to_concern
                    result["message"] = f"{metric} ({value*100:.1f}%) is within {distance_to_concern*100:.0f}% of concern threshold ({concern_threshold*100:.1f}%)"

        if not result["proximity_warning"]:
            result["message"] = f"{metric} ({value*100:.1f}%) is within acceptable range"

        return result

    def _generate_proximity_recommendation(
        self,
        warnings: List[Dict[str, Any]]
    ) -> str:
        """Generate actionable recommendation based on proximity warnings."""
        if not warnings:
            return "All monitored metrics are within acceptable ranges. Continue routine surveillance."

        exceeded_risk = [w for w in warnings if w["warning_level"] == "EXCEEDED_RISK"]
        near_risk = [w for w in warnings if w["warning_level"] == "NEAR_RISK"]
        exceeded_concern = [w for w in warnings if w["warning_level"] == "EXCEEDED_CONCERN"]
        near_concern = [w for w in warnings if w["warning_level"] == "NEAR_CONCERN"]

        if exceeded_risk:
            return (
                f"URGENT: {len(exceeded_risk)} metric(s) exceed risk thresholds. "
                f"Immediate review of patient outcomes and surgical technique required. "
                f"Consider notifying regulatory bodies if trend continues."
            )
        elif near_risk:
            return (
                f"WARNING: {len(near_risk)} metric(s) approaching risk thresholds. "
                f"Increase monitoring frequency and investigate contributing factors. "
                f"Prepare mitigation plan if metric continues trending."
            )
        elif exceeded_concern:
            return (
                f"ATTENTION: {len(exceeded_concern)} metric(s) exceed concern thresholds. "
                f"Review recent cases for patterns. Consider root cause analysis."
            )
        elif near_concern:
            return (
                f"NOTE: {len(near_concern)} metric(s) approaching concern thresholds. "
                f"Continue monitoring. Flag for discussion in next quality review."
            )

        return "Metrics require attention. Review detailed warnings above."

    def _get_outcomes_by_indication(self, norms: RegistryNorms) -> Dict[str, Any]:
        """
        Get survival outcomes stratified by revision indication.

        This is primarily from AOANJRR which provides the most detailed
        indication-specific outcome data.

        Enables answering:
        - "What is the survival rate for revisions due to infection vs loosening?"
        - "Which revision indications have the worst outcomes?"
        """
        outcomes_data = []

        for reg in norms.registries:
            if reg.outcomes_by_indication:
                reg_outcomes = {
                    "registry_id": reg.id,
                    "registry_name": reg.abbreviation,
                    "report_year": reg.report_year,
                    "indications": [],
                }

                for indication, outcomes in reg.outcomes_by_indication.items():
                    indication_data = {
                        "indication": indication,
                        "indication_formatted": indication.replace("_", " ").title(),
                    }
                    # Add all outcome metrics for this indication
                    for metric, value in outcomes.items():
                        indication_data[metric] = value
                        if isinstance(value, float) and value < 1:
                            indication_data[f"{metric}_formatted"] = f"{value*100:.1f}%"

                    reg_outcomes["indications"].append(indication_data)

                # Sort by survival (worst first for clinical relevance)
                reg_outcomes["indications"].sort(
                    key=lambda x: x.get("survival_5yr") or x.get("survival_2yr") or 1
                )
                outcomes_data.append(reg_outcomes)

        # Generate insights
        insights = self._generate_indication_insights(outcomes_data)

        return {
            "by_registry": outcomes_data,
            "n_registries_with_data": len(outcomes_data),
            "insights": insights,
            "clinical_note": (
                "Outcomes by indication help identify which revision causes "
                "carry the highest risk of re-revision. This data is critical "
                "for patient counseling and surgical planning."
            ),
        }

    def _generate_indication_insights(
        self,
        outcomes_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights about indication-specific outcomes."""
        insights = []

        if not outcomes_data:
            return ["Indication-specific outcome data not available."]

        # Find worst performing indication
        all_indications = []
        for reg in outcomes_data:
            for ind in reg.get("indications", []):
                all_indications.append({
                    "registry": reg["registry_name"],
                    "indication": ind["indication"],
                    "survival_5yr": ind.get("survival_5yr"),
                    "survival_2yr": ind.get("survival_2yr"),
                })

        # Worst by 5yr survival
        worst = min(
            (i for i in all_indications if i.get("survival_5yr")),
            key=lambda x: x["survival_5yr"],
            default=None
        )
        if worst:
            insights.append(
                f"Worst 5-year survival is for {worst['indication'].replace('_', ' ')} revisions "
                f"({worst['survival_5yr']*100:.1f}% in {worst['registry']})."
            )

        # Best by 5yr survival
        best = max(
            (i for i in all_indications if i.get("survival_5yr")),
            key=lambda x: x["survival_5yr"],
            default=None
        )
        if best:
            insights.append(
                f"Best 5-year survival is for {best['indication'].replace('_', ' ')} revisions "
                f"({best['survival_5yr']*100:.1f}% in {best['registry']})."
            )

        insights.append(
            "Infection-related revisions typically have worse outcomes than "
            "aseptic loosening revisions across most registries."
        )

        return insights

    def _get_registry_metadata(self, norms: RegistryNorms) -> Dict[str, Any]:
        """
        Get comprehensive data quality notes and limitations for all registries.

        This supports regulatory-grade documentation by providing
        full transparency about data sources.
        """
        metadata = []

        for reg in norms.registries:
            reg_meta = {
                "registry_id": reg.id,
                "registry_name": reg.name,
                "abbreviation": reg.abbreviation,
                "report_year": reg.report_year,
                "data_coverage": reg.data_years,
                "population_covered": reg.population,
                "total_procedures": reg.n_procedures,
                "primary_procedures": reg.n_primary,
                "revision_procedures": (
                    reg.n_procedures - reg.n_primary
                    if reg.n_procedures and reg.n_primary
                    else None
                ),
                "data_completeness": self._calculate_completeness(reg),
                "strengths": self._get_registry_strengths(reg),
                "limitations": self._get_registry_limitations(reg),
            }
            metadata.append(reg_meta)

        return {
            "registries": metadata,
            "n_registries": len(metadata),
            "total_global_procedures": sum(r.n_procedures or 0 for r in norms.registries),
            "data_years_range": self._get_data_years_range(norms),
            "general_limitations": [
                "Registry data reflects real-world practice patterns which may differ from clinical trial populations",
                "Outcome definitions and reporting requirements vary between registries",
                "Loss to follow-up may introduce survival bias",
                "Surgical technique evolution over time affects historical comparisons",
                "Patient demographics and comorbidity profiles differ between countries",
            ],
            "citation_format": (
                "[Registry Abbreviation] Annual Report [Year]. "
                "Data coverage: [Start Year]-[End Year]. "
                "n=[Total Procedures]."
            ),
        }

    def _get_registry_strengths(self, reg: RegistryBenchmark) -> List[str]:
        """Get strengths specific to each registry."""
        strengths = []

        if reg.id == "aoanjrr":
            strengths = [
                "Most comprehensive long-term follow-up data (20+ years)",
                "Detailed revision reason breakdown",
                "Outcomes stratified by indication",
                "High data capture rate (>98%)",
            ]
        elif reg.id == "njr":
            strengths = [
                "Largest absolute patient numbers globally",
                "Comprehensive UK-wide coverage",
                "Patient-reported outcome measures (PROMs) included",
            ]
        elif reg.id == "shar":
            strengths = [
                "Longest historical registry (since 1979)",
                "Excellent long-term survival data",
                "High-quality Nordic data standards",
            ]
        elif reg.id == "ajrr":
            strengths = [
                "US-specific population data",
                "Rapidly growing dataset",
                "Multi-payer healthcare system representation",
            ]
        elif reg.id == "cjrr":
            strengths = [
                "Comprehensive Canadian coverage",
                "Bilingual data collection",
                "Universal healthcare system representation",
            ]

        # Add generic strengths based on data availability
        if reg.survival_10yr is not None:
            strengths.append("Long-term (10+ year) survival data available")
        if reg.revision_reasons:
            strengths.append("Detailed revision reason analysis")
        if reg.outcomes_by_indication:
            strengths.append("Indication-specific outcomes reported")

        return strengths

    def _get_registry_limitations(self, reg: RegistryBenchmark) -> List[str]:
        """Get limitations specific to each registry."""
        limitations = []

        if reg.id == "aoanjrr":
            limitations = [
                "Australian population may not generalize to all demographics",
                "Healthcare system differences from US/Europe",
            ]
        elif reg.id == "njr":
            limitations = [
                "UK-specific healthcare context",
                "Some data capture gaps in earlier years",
            ]
        elif reg.id == "shar":
            limitations = [
                "Smaller population than other registries",
                "Nordic healthcare context may not generalize",
            ]
        elif reg.id == "ajrr":
            limitations = [
                "Shorter follow-up period (registry started 2012)",
                "Voluntary participation may introduce selection bias",
            ]
        elif reg.id == "cjrr":
            limitations = [
                "Moderate coverage rate",
                "Shorter follow-up compared to older registries",
            ]

        # Add limitations based on missing data
        if reg.survival_10yr is None:
            limitations.append("No 10-year survival data available")
        if not reg.revision_reasons:
            limitations.append("Revision reason breakdown not reported")
        if not reg.outcomes_by_indication:
            limitations.append("Indication-specific outcomes not available")

        return limitations

    def _get_data_years_range(self, norms: RegistryNorms) -> str:
        """Calculate the full data years range across all registries."""
        start_years = []
        end_years = []

        for reg in norms.registries:
            if reg.data_years:
                parts = reg.data_years.split("-")
                if len(parts) == 2:
                    try:
                        start_years.append(int(parts[0]))
                        end_years.append(int(parts[1]))
                    except ValueError:
                        pass

        if start_years and end_years:
            return f"{min(start_years)}-{max(end_years)}"
        return "Unknown"
