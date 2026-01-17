"""
UC7 Competitive Intelligence Service for Clinical Intelligence Platform.

Orchestrates agents for competitive landscape analysis and battle card generation.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext
from app.agents.literature_agent import LiteratureAgent
from app.agents.registry_agent import RegistryAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.data_agent import get_study_data
from app.services.llm_service import get_llm_service
from app.services.prompt_service import get_prompt_service
from data.loaders.yaml_loader import get_hybrid_loader

logger = logging.getLogger(__name__)


class CompetitiveService:
    """
    Service for UC7: Competitive Intelligence.

    Orchestrates multiple agents to:
    - Analyze competitive landscape using registry benchmarks
    - Generate literature-supported comparisons
    - Create sales battle cards
    - Identify key differentiators and competitive positioning
    """

    def __init__(self):
        """Initialize competitive service."""
        self._literature_agent = LiteratureAgent()
        self._registry_agent = RegistryAgent()
        self._synthesis_agent = SynthesisAgent()
        self._llm = get_llm_service()
        self._prompts = get_prompt_service()
        self._doc_loader = get_hybrid_loader()

    async def get_competitive_intelligence(
        self,
        focus: str = "landscape"
    ) -> Dict[str, Any]:
        """
        Get comprehensive competitive intelligence report.

        Args:
            focus: Report focus - "landscape", "benchmarking", or "battle_card"

        Returns:
            Dict with competitive analysis
        """
        request_id = str(uuid.uuid4())

        # Get study data from safety metrics
        study_data = await self._get_study_metrics()

        # Get registry comparison data
        registry_context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "compare_all",
                "study_data": {
                    "revision_rate": study_data.get("revision_rate_2yr", 0.071),
                    "survival_2yr": study_data.get("survival_2yr", 0.929),
                }
            }
        )
        registry_result = await self._registry_agent.run(registry_context)

        # Get literature benchmarks
        lit_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "all"}
        )
        literature_result = await self._literature_agent.run(lit_context)

        # Build competitive landscape
        if focus == "landscape":
            return await self._build_landscape_report(
                study_data, registry_result, literature_result
            )
        elif focus == "benchmarking":
            return await self._build_benchmarking_report(
                study_data, registry_result, literature_result
            )
        elif focus == "battle_card":
            return await self._build_battle_card(
                study_data, registry_result, literature_result
            )
        else:
            return {
                "success": False,
                "error": f"Unknown focus type: {focus}",
            }

    async def _get_study_metrics(self) -> Dict[str, Any]:
        """Get current study performance metrics from centralized database."""
        try:
            study_data = get_study_data()
            n_patients = study_data.total_patients

            # Calculate revision rate from adverse events
            n_revisions = sum(
                1 for ae in study_data.adverse_events
                if ae.device_removed and ae.device_removed.lower() == "yes"
            )
            revision_rate = n_revisions / n_patients if n_patients > 0 else 0
            survival_rate = 1 - revision_rate

            # Calculate AE-specific rates
            ae_titles = [ae.ae_title.lower() if ae.ae_title else "" for ae in study_data.adverse_events]
            n_dislocations = sum(1 for t in ae_titles if "dislocation" in t)
            n_infections = sum(1 for t in ae_titles if "infection" in t)

            # Calculate HHS improvement and MCID from actual scores
            hhs_improvements = []
            for patient in study_data.patients:
                scores = study_data.get_patient_hhs_scores(patient.patient_id)
                baseline = None
                two_year = None
                for s in scores:
                    fu = (s.follow_up or "").lower()
                    if "preop" in fu or "baseline" in fu or "screening" in fu:
                        baseline = s.total_score
                    elif "2 year" in fu or "24 month" in fu:
                        two_year = s.total_score
                if baseline is not None and two_year is not None:
                    hhs_improvements.append(two_year - baseline)

            hhs_improvement = sum(hhs_improvements) / len(hhs_improvements) if hhs_improvements else 0
            mcid_achieved = sum(1 for imp in hhs_improvements if imp >= 20)
            mcid_rate = mcid_achieved / len(hhs_improvements) if hhs_improvements else 0

            # Get protocol version from YAML
            protocol_version = "1.0"
            try:
                protocol_rules = self._doc_loader.load_protocol_rules()
                protocol_version = protocol_rules.protocol_version
            except Exception:
                pass

            return {
                "n_patients": n_patients,
                "revision_rate_2yr": round(revision_rate, 3),
                "survival_2yr": round(survival_rate, 3),
                "hhs_improvement": round(hhs_improvement, 1),
                "mcid_achievement": round(mcid_rate, 2),
                "dislocation_rate": round(n_dislocations / n_patients, 3) if n_patients > 0 else 0,
                "infection_rate": round(n_infections / n_patients, 3) if n_patients > 0 else 0,
                "protocol_version": protocol_version,
                "data_source": "H-34 Study Database",
            }
        except Exception as e:
            logger.error(f"Failed to load study metrics from database: {e}")
            raise ValueError(f"Cannot load study metrics: {e}")

    async def _build_landscape_report(
        self,
        study_data: Dict[str, Any],
        registry_result,
        literature_result
    ) -> Dict[str, Any]:
        """Build comprehensive competitive landscape report."""
        registry_data = registry_result.data if registry_result.success else {}
        lit_data = literature_result.data if literature_result.success else {}

        # Format registry data for prompt
        registry_text = self._format_registry_for_prompt(registry_data)
        literature_text = self._format_literature_for_prompt(lit_data)

        # Generate narrative using LLM
        prompt = self._prompts.load("competitive_landscape", {
            "revision_rate_2yr": f"{study_data.get('revision_rate_2yr', 0)*100:.1f}%",
            "survival_rate_2yr": f"{study_data.get('survival_2yr', 0)*100:.1f}%",
            "hhs_improvement": study_data.get('hhs_improvement', 'N/A'),
            "mcid_achievement": f"{study_data.get('mcid_achievement', 0)*100:.1f}%",
            "registry_data": registry_text,
            "literature_data": literature_text,
        })

        narrative = await self._llm.generate(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
            max_tokens=2000
        )

        # Build structured response
        return {
            "success": True,
            "report_type": "competitive_landscape",
            "generated_at": datetime.utcnow().isoformat(),
            "study_metrics": study_data,
            "competitive_landscape": narrative.strip(),
            "registry_comparison": self._build_registry_comparison(registry_data),
            "literature_benchmarks": self._build_literature_summary(lit_data),
            "key_differentiators": self._extract_differentiators(study_data, registry_data),
            "sources": self._collect_sources(registry_result, literature_result),
            "confidence": 0.85,
        }

    async def _build_benchmarking_report(
        self,
        study_data: Dict[str, Any],
        registry_result,
        literature_result
    ) -> Dict[str, Any]:
        """Build focused benchmarking comparison report."""
        registry_data = registry_result.data if registry_result.success else {}
        lit_data = literature_result.data if literature_result.success else {}

        comparisons = registry_data.get("comparisons", {})

        # Build metric-by-metric comparison
        benchmarking = {
            "revision_rate_2yr": self._build_metric_benchmark(
                "Revision Rate (2yr)",
                study_data.get("revision_rate_2yr", 0.071),
                comparisons.get("revision_rate_2yr", {}),
                lower_is_better=True
            ),
            "survival_2yr": self._build_metric_benchmark(
                "Survival Rate (2yr)",
                study_data.get("survival_2yr", 0.929),
                comparisons.get("survival_2yr", {}),
                lower_is_better=False
            ),
        }

        # Add literature comparison
        agg_benchmarks = lit_data.get("aggregate_benchmarks", {})
        lit_comparison = []

        if "revision_rate_2yr" in agg_benchmarks:
            lit_bench = agg_benchmarks["revision_rate_2yr"]
            study_rate = study_data.get("revision_rate_2yr", 0.071)
            lit_mean = lit_bench.get("mean", 0.08)
            lit_comparison.append({
                "metric": "Revision Rate (2yr)",
                "study_value": study_rate,
                "literature_mean": lit_mean,
                "favorable": study_rate <= lit_mean,
                "difference": round((study_rate - lit_mean) * 100, 2),
            })

        return {
            "success": True,
            "report_type": "competitive_benchmarking",
            "generated_at": datetime.utcnow().isoformat(),
            "study_metrics": study_data,
            "registry_benchmarks": benchmarking,
            "literature_comparison": lit_comparison,
            "overall_position": self._determine_overall_position(
                study_data, registry_data, lit_data
            ),
            "sources": self._collect_sources(registry_result, literature_result),
            "confidence": 0.88,
        }

    async def _build_battle_card(
        self,
        study_data: Dict[str, Any],
        registry_result,
        literature_result
    ) -> Dict[str, Any]:
        """Build sales battle card."""
        registry_data = registry_result.data if registry_result.success else {}
        lit_data = literature_result.data if literature_result.success else {}

        # Format data for battle card prompt
        registry_text = self._format_registry_for_prompt(registry_data)
        lit_text = self._format_literature_for_prompt(lit_data)

        # Generate battle card content
        prompt = self._prompts.load("battle_card_generation", {
            "revision_rate_2yr": f"{study_data.get('revision_rate_2yr', 0)*100:.1f}%",
            "survival_rate_2yr": f"{study_data.get('survival_2yr', 0)*100:.1f}%",
            "hhs_improvement": study_data.get('hhs_improvement', 'N/A'),
            "mcid_achievement": f"{study_data.get('mcid_achievement', 0)*100:.1f}%",
            "registry_comparison": registry_text,
            "literature_benchmarks": lit_text,
        })

        battle_card_content = await self._llm.generate(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
            max_tokens=2500
        )

        # Build structured battle card
        return {
            "success": True,
            "report_type": "battle_card",
            "generated_at": datetime.utcnow().isoformat(),
            "product": "DELTA Revision Cup",
            "battle_card_content": battle_card_content.strip(),
            "quick_stats": self._build_quick_stats(study_data, registry_data),
            "talking_points": self._build_talking_points(study_data, registry_data),
            "rebuttals": self._build_rebuttals(study_data, registry_data),
            "sources": self._collect_sources(registry_result, literature_result),
            "confidence": 0.82,
        }

    def _format_registry_for_prompt(self, registry_data: Dict) -> str:
        """Format registry data for prompt inclusion."""
        if not registry_data:
            return "Registry data not available."

        comparisons = registry_data.get("comparisons", {})
        lines = ["Registry Comparison:"]

        for metric, data in comparisons.items():
            if isinstance(data, dict):
                by_registry = data.get("by_registry", {})
                for reg_name, values in by_registry.items():
                    value = values.get("value")
                    if value is not None:
                        lines.append(f"- {reg_name} {metric}: {value*100:.1f}%")

        return "\n".join(lines) if len(lines) > 1 else "Registry comparison data available."

    def _format_literature_for_prompt(self, lit_data: Dict) -> str:
        """Format literature data for prompt inclusion."""
        if not lit_data:
            return "Literature benchmarks not available."

        benchmarks = lit_data.get("aggregate_benchmarks", {})
        lines = ["Literature Benchmarks:"]

        for metric, data in benchmarks.items():
            if isinstance(data, dict):
                mean = data.get("mean")
                if mean is not None:
                    lines.append(f"- {metric} mean: {mean*100:.1f}%")

        return "\n".join(lines) if len(lines) > 1 else "Literature benchmark data available."

    def _build_registry_comparison(self, registry_data: Dict) -> List[Dict]:
        """Build structured registry comparison."""
        comparisons = registry_data.get("comparisons", {})
        result = []

        for metric, data in comparisons.items():
            if isinstance(data, dict):
                by_registry = data.get("by_registry", {})
                for reg_name, values in by_registry.items():
                    result.append({
                        "registry": reg_name,
                        "metric": metric,
                        "registry_value": values.get("value"),
                        "comparison": values.get("comparison"),
                    })

        return result

    def _build_literature_summary(self, lit_data: Dict) -> Dict:
        """Build literature benchmark summary."""
        return {
            "n_publications": lit_data.get("n_publications", 0),
            "aggregate_benchmarks": lit_data.get("aggregate_benchmarks", {}),
        }

    def _extract_differentiators(
        self,
        study_data: Dict,
        registry_data: Dict
    ) -> List[Dict]:
        """Extract key competitive differentiators."""
        differentiators = []

        study_revision = study_data.get("revision_rate_2yr", 0.071)
        study_survival = study_data.get("survival_2yr", 0.929)

        # Check against registry data
        comparisons = registry_data.get("comparisons", {})

        rev_comparison = comparisons.get("revision_rate_2yr", {})
        n_better = rev_comparison.get("n_better_than", 0)
        n_total = rev_comparison.get("n_registries", 5)

        if n_better >= 3:
            differentiators.append({
                "category": "Revision Rate",
                "differentiator": f"Lower revision rate than {n_better} of {n_total} major registries",
                "evidence": f"{study_revision*100:.1f}% vs registry range",
            })

        surv_comparison = comparisons.get("survival_2yr", {})
        n_better_surv = surv_comparison.get("n_better_than", 0)

        if n_better_surv >= 3:
            differentiators.append({
                "category": "Survival",
                "differentiator": f"Superior 2-year survival vs {n_better_surv} registries",
                "evidence": f"{study_survival*100:.1f}% survival rate",
            })

        # Add product-specific differentiators
        differentiators.append({
            "category": "Technology",
            "differentiator": "Porous tantalum construction for enhanced osseointegration",
            "evidence": "Designed for compromised bone stock in revision surgery",
        })

        return differentiators

    def _build_metric_benchmark(
        self,
        metric_name: str,
        study_value: float,
        comparison_data: Dict,
        lower_is_better: bool
    ) -> Dict:
        """Build detailed metric benchmark comparison."""
        by_registry = comparison_data.get("by_registry", {})

        registry_values = []
        for reg_name, data in by_registry.items():
            value = data.get("value")
            if value is not None:
                registry_values.append({
                    "registry": reg_name,
                    "value": value,
                    "favorable": (study_value <= value) if lower_is_better else (study_value >= value),
                })

        return {
            "metric": metric_name,
            "study_value": study_value,
            "study_value_formatted": f"{study_value*100:.1f}%",
            "by_registry": registry_values,
            "n_favorable": sum(1 for r in registry_values if r["favorable"]),
            "n_total": len(registry_values),
        }

    def _determine_overall_position(
        self,
        study_data: Dict,
        registry_data: Dict,
        lit_data: Dict
    ) -> Dict:
        """Determine overall competitive position."""
        comparisons = registry_data.get("comparisons", {})

        # Calculate favorable metrics count
        n_favorable = 0
        n_total = 0

        for metric, data in comparisons.items():
            n_better = data.get("n_better_than", 0)
            n_regs = data.get("n_registries", 5)
            if n_better >= n_regs / 2:
                n_favorable += 1
            n_total += 1

        if n_favorable == n_total:
            position = "STRONG"
            description = "Outperforms majority of registry benchmarks across all metrics"
        elif n_favorable > 0:
            position = "COMPETITIVE"
            description = "Competitive performance with some metrics exceeding benchmarks"
        else:
            position = "DEVELOPING"
            description = "Performance within registry ranges with room for differentiation"

        return {
            "position": position,
            "description": description,
            "favorable_metrics": n_favorable,
            "total_metrics": n_total,
        }

    def _build_quick_stats(
        self,
        study_data: Dict,
        registry_data: Dict
    ) -> List[Dict]:
        """Build quick stats for battle card."""
        return [
            {
                "stat": "2-Year Survival",
                "value": f"{study_data.get('survival_2yr', 0.929)*100:.1f}%",
                "context": "Registry range: 92-97%",
            },
            {
                "stat": "Revision Rate",
                "value": f"{study_data.get('revision_rate_2yr', 0.071)*100:.1f}%",
                "context": "Competitive vs benchmarks",
            },
            {
                "stat": "MCID Achievement",
                "value": f"{study_data.get('mcid_achievement', 0.85)*100:.0f}%",
                "context": "Clinically meaningful improvement",
            },
            {
                "stat": "HHS Improvement",
                "value": f"{study_data.get('hhs_improvement', 35.2):.1f} points",
                "context": "Functional outcome measure",
            },
        ]

    def _build_talking_points(
        self,
        study_data: Dict,
        registry_data: Dict
    ) -> List[str]:
        """Build key talking points."""
        survival = study_data.get('survival_2yr', 0.929)
        revision = study_data.get('revision_rate_2yr', 0.071)
        mcid = study_data.get('mcid_achievement', 0.85)

        return [
            f"DELTA Revision Cup demonstrates {survival*100:.1f}% 2-year implant survival in revision hip surgery",
            f"{mcid*100:.0f}% of patients achieve clinically meaningful functional improvement",
            f"Revision rate of {revision*100:.1f}% compares favorably to international registry benchmarks",
            "Porous tantalum technology provides enhanced fixation in compromised bone",
        ]

    def _build_rebuttals(
        self,
        study_data: Dict,
        registry_data: Dict
    ) -> List[Dict]:
        """Build objection/rebuttal pairs."""
        return [
            {
                "objection": "What's the long-term data?",
                "rebuttal": f"Current 2-year data shows {study_data.get('survival_2yr', 0.929)*100:.1f}% survival with ongoing follow-up. Registry data supports favorable long-term outcomes for porous tantalum in revision surgery.",
            },
            {
                "objection": "How does this compare to other options?",
                "rebuttal": f"At {study_data.get('revision_rate_2yr', 0.071)*100:.1f}% revision rate, DELTA Revision Cup performs competitively against international registry benchmarks (AOANJRR, NJR, etc.).",
            },
            {
                "objection": "Is the cost justified?",
                "rebuttal": f"With {study_data.get('mcid_achievement', 0.85)*100:.0f}% of patients achieving meaningful functional improvement, the outcomes demonstrate clinical value in complex revision cases.",
            },
        ]

    def _collect_sources(self, registry_result, literature_result) -> List[Dict]:
        """Collect all sources from agent results."""
        sources = []

        if registry_result.success:
            for source in registry_result.sources:
                sources.append(source.to_dict())

        if literature_result.success:
            for source in literature_result.sources:
                sources.append(source.to_dict())

        return sources


# Singleton instance
_competitive_service: Optional[CompetitiveService] = None


def get_competitive_service() -> CompetitiveService:
    """Get singleton competitive service instance."""
    global _competitive_service
    if _competitive_service is None:
        _competitive_service = CompetitiveService()
    return _competitive_service
