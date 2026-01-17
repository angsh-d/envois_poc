"""
UC8 Sales Enablement Content Service for Clinical Intelligence Platform.

Generates sales-ready content including talking points, value propositions, and presentations.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext
from app.agents.literature_agent import LiteratureAgent
from app.agents.registry_agent import RegistryAgent
from app.agents.data_agent import get_study_data
from app.services.llm_service import get_llm_service
from app.services.prompt_service import get_prompt_service
from data.loaders.yaml_loader import get_hybrid_loader

logger = logging.getLogger(__name__)


class SalesContentService:
    """
    Service for UC8: Sales Enablement Content Generation.

    Generates sales-ready content:
    - Talking points for surgeon meetings
    - Value propositions
    - Surgeon presentation outlines
    - Objection handlers
    """

    def __init__(self):
        """Initialize sales content service."""
        self._literature_agent = LiteratureAgent()
        self._registry_agent = RegistryAgent()
        self._llm = get_llm_service()
        self._prompts = get_prompt_service()
        self._doc_loader = get_hybrid_loader()

    async def generate_sales_content(
        self,
        content_type: str = "talking_points"
    ) -> Dict[str, Any]:
        """
        Generate sales enablement content.

        Args:
            content_type: Type of content - "talking_points", "value_proposition", or "surgeon_presentation"

        Returns:
            Dict with generated sales content
        """
        request_id = str(uuid.uuid4())

        # Get study metrics
        study_metrics = self._get_study_metrics()

        # Get registry context
        reg_context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "compare_all",
                "study_data": {
                    "revision_rate": study_metrics.get("revision_rate", 0.071),
                    "survival_2yr": study_metrics.get("survival_rate", 0.929),
                }
            }
        )
        registry_result = await self._registry_agent.run(reg_context)
        reg_data = registry_result.data if registry_result.success else {}

        # Get literature context
        lit_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "all"}
        )
        literature_result = await self._literature_agent.run(lit_context)
        lit_data = literature_result.data if literature_result.success else {}

        # Format context for prompt
        registry_context = self._format_registry_context(reg_data)
        literature_context = self._format_literature_context(lit_data)

        # Generate content based on type
        prompt = self._prompts.load("sales_talking_points", {
            "n_patients": study_metrics.get("n_patients", 56),
            "survival_rate": f"{study_metrics.get('survival_rate', 0.929)*100:.1f}%",
            "revision_rate": f"{study_metrics.get('revision_rate', 0.071)*100:.1f}%",
            "hhs_improvement": study_metrics.get("hhs_improvement", 35.2),
            "mcid_achievement": f"{study_metrics.get('mcid_achievement', 0.85)*100:.0f}%",
            "registry_context": registry_context,
            "literature_context": literature_context,
            "content_type": content_type,
        })

        content = await self._llm.generate(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.3,
            max_tokens=2000
        )

        # Build response based on content type
        if content_type == "talking_points":
            return self._build_talking_points_response(
                content, study_metrics, reg_data, lit_data,
                registry_result, literature_result
            )
        elif content_type == "value_proposition":
            return self._build_value_proposition_response(
                content, study_metrics, reg_data, lit_data,
                registry_result, literature_result
            )
        elif content_type == "surgeon_presentation":
            return self._build_presentation_response(
                content, study_metrics, reg_data, lit_data,
                registry_result, literature_result
            )
        else:
            return {
                "success": False,
                "error": f"Unknown content type: {content_type}",
            }

    def _get_study_metrics(self) -> Dict[str, Any]:
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

            return {
                "n_patients": n_patients,
                "survival_rate": round(survival_rate, 3),
                "revision_rate": round(revision_rate, 3),
                "hhs_improvement": round(hhs_improvement, 1),
                "mcid_achievement": round(mcid_rate, 2),
                "dislocation_rate": round(n_dislocations / n_patients, 3) if n_patients > 0 else 0,
                "infection_rate": round(n_infections / n_patients, 3) if n_patients > 0 else 0,
                "data_source": "H-34 Study Database",
            }
        except Exception as e:
            logger.error(f"Failed to load study metrics from database: {e}")
            raise ValueError(f"Cannot load study metrics: {e}")

    def _format_registry_context(self, reg_data: Dict) -> str:
        """Format registry data for sales context."""
        if not reg_data:
            return "Registry comparison data not available."

        comparisons = reg_data.get("comparisons", {})
        lines = ["Registry Performance Context:"]

        # Revision rate comparison
        rev_comp = comparisons.get("revision_rate_2yr", {})
        n_better = rev_comp.get("n_better_than", 0)
        n_total = reg_data.get("n_registries_compared", 5)

        if n_better > 0:
            lines.append(f"- DELTA Revision Cup revision rate is favorable vs {n_better} of {n_total} major registries")

        # Get specific registry values
        by_registry = rev_comp.get("by_registry", {})
        for reg_name, data in by_registry.items():
            value = data.get("value")
            if value is not None:
                lines.append(f"- {reg_name}: {value*100:.1f}% revision rate")

        return "\n".join(lines)

    def _format_literature_context(self, lit_data: Dict) -> str:
        """Format literature data for sales context."""
        if not lit_data:
            return "Literature benchmark data not available."

        benchmarks = lit_data.get("aggregate_benchmarks", {})
        n_pubs = lit_data.get("n_publications", 0)

        lines = [f"Literature Context ({n_pubs} publications):"]

        for metric, data in benchmarks.items():
            if isinstance(data, dict):
                mean = data.get("mean")
                if mean is not None:
                    if mean < 1:
                        lines.append(f"- Literature {metric}: {mean*100:.1f}% (mean)")
                    else:
                        lines.append(f"- Literature {metric}: {mean:.1f} (mean)")

        return "\n".join(lines)

    def _build_talking_points_response(
        self,
        content: str,
        study_metrics: Dict,
        reg_data: Dict,
        lit_data: Dict,
        registry_result,
        literature_result
    ) -> Dict[str, Any]:
        """Build talking points response."""
        # Extract key messages for structured response
        key_messages = [
            f"92.9% 2-year implant survival in revision hip surgery",
            f"85% of patients achieve clinically meaningful improvement",
            f"7.1% revision rate compares favorably to registry benchmarks",
            f"35.2-point Harris Hip Score improvement demonstrates functional benefit",
            f"Porous tantalum technology for enhanced osseointegration",
        ]

        return {
            "success": True,
            "content_type": "talking_points",
            "generated_at": datetime.utcnow().isoformat(),
            "product": "DELTA Revision Cup",
            "content": content.strip(),
            "key_messages": key_messages,
            "evidence_citations": self._build_evidence_citations(study_metrics, reg_data),
            "competitive_positioning": self._build_competitive_positioning(reg_data),
            "objection_handlers": self._build_objection_handlers(study_metrics, reg_data),
            "sources": self._collect_sources(registry_result, literature_result),
            "confidence": 0.85,
            "usage_guidelines": {
                "target_audience": "Orthopedic surgeons performing revision THA",
                "context": "Product presentation or 1:1 meeting",
                "compliance_note": "All claims must be supported by referenced evidence",
            }
        }

    def _build_value_proposition_response(
        self,
        content: str,
        study_metrics: Dict,
        reg_data: Dict,
        lit_data: Dict,
        registry_result,
        literature_result
    ) -> Dict[str, Any]:
        """Build value proposition response."""
        return {
            "success": True,
            "content_type": "value_proposition",
            "generated_at": datetime.utcnow().isoformat(),
            "product": "DELTA Revision Cup",
            "content": content.strip(),
            "target_customer": {
                "specialty": "Orthopedic surgery",
                "subspecialty": "Adult reconstruction / joint arthroplasty",
                "practice_type": "Academic medical center or high-volume joint replacement center",
            },
            "problem_addressed": "Bone loss management in revision total hip arthroplasty",
            "key_benefits": [
                {
                    "benefit": "High implant survival",
                    "evidence": f"{study_metrics.get('survival_rate', 0.929)*100:.1f}% 2-year survival",
                },
                {
                    "benefit": "Functional improvement",
                    "evidence": f"{study_metrics.get('mcid_achievement', 0.85)*100:.0f}% MCID achievement",
                },
                {
                    "benefit": "Enhanced osseointegration",
                    "evidence": "Porous tantalum technology for bone ingrowth",
                },
            ],
            "differentiation": "Designed specifically for compromised bone stock in revision surgery",
            "sources": self._collect_sources(registry_result, literature_result),
            "confidence": 0.83,
        }

    def _build_presentation_response(
        self,
        content: str,
        study_metrics: Dict,
        reg_data: Dict,
        lit_data: Dict,
        registry_result,
        literature_result
    ) -> Dict[str, Any]:
        """Build surgeon presentation response."""
        return {
            "success": True,
            "content_type": "surgeon_presentation",
            "generated_at": datetime.utcnow().isoformat(),
            "product": "DELTA Revision Cup",
            "content": content.strip(),
            "presentation_outline": [
                {
                    "section": "Opening",
                    "duration": "1-2 min",
                    "content": "Clinical challenge scenario in revision THA",
                },
                {
                    "section": "Clinical Challenge",
                    "duration": "2 min",
                    "content": "Bone loss and fixation challenges in revision surgery",
                },
                {
                    "section": "Solution Overview",
                    "duration": "2 min",
                    "content": "DELTA Revision Cup technology and mechanism",
                },
                {
                    "section": "Clinical Evidence",
                    "duration": "3 min",
                    "content": f"Study results: {study_metrics.get('survival_rate', 0.929)*100:.1f}% survival, {study_metrics.get('mcid_achievement', 0.85)*100:.0f}% MCID",
                },
                {
                    "section": "Summary",
                    "duration": "2 min",
                    "content": "Key takeaways and next steps",
                },
            ],
            "key_slides_content": {
                "clinical_evidence": study_metrics,
                "registry_comparison": self._build_competitive_positioning(reg_data),
            },
            "sources": self._collect_sources(registry_result, literature_result),
            "confidence": 0.82,
        }

    def _build_evidence_citations(
        self,
        study_metrics: Dict,
        reg_data: Dict
    ) -> List[Dict[str, str]]:
        """Build evidence citations list."""
        return [
            {
                "claim": "92.9% 2-year implant survival",
                "source": "DELTA Revision Cup Post-Market Study (n=56)",
            },
            {
                "claim": "85% MCID achievement rate",
                "source": "DELTA Revision Cup Post-Market Study",
            },
            {
                "claim": "Favorable vs registry benchmarks",
                "source": "AOANJRR, NJR, SHAR, AJRR, CJRR 2023 Reports",
            },
        ]

    def _build_competitive_positioning(self, reg_data: Dict) -> Dict[str, Any]:
        """Build competitive positioning summary."""
        comparisons = reg_data.get("comparisons", {})
        rev_comp = comparisons.get("revision_rate_2yr", {})
        n_better = rev_comp.get("n_better_than", 0)
        n_total = reg_data.get("n_registries_compared", 5)

        return {
            "position": "COMPETITIVE" if n_better >= 2 else "DEVELOPING",
            "vs_registries": f"Favorable vs {n_better} of {n_total} major registries",
            "key_advantage": "Designed for revision surgery with compromised bone",
        }

    def _build_objection_handlers(
        self,
        study_metrics: Dict,
        reg_data: Dict
    ) -> List[Dict[str, str]]:
        """Build objection handlers."""
        return [
            {
                "objection": "What about long-term data?",
                "response": f"Current 2-year data shows {study_metrics.get('survival_rate', 0.929)*100:.1f}% survival with ongoing follow-up. Registry data supports favorable long-term outcomes for porous tantalum technology.",
            },
            {
                "objection": "How does this compare to my current implant?",
                "response": f"At {study_metrics.get('revision_rate', 0.071)*100:.1f}% revision rate, DELTA Revision Cup performs competitively against published registry benchmarks from 5 major international registries.",
            },
            {
                "objection": "Is the cost justified?",
                "response": f"With {study_metrics.get('mcid_achievement', 0.85)*100:.0f}% of patients achieving meaningful functional improvement, the clinical outcomes demonstrate value in complex revision cases.",
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
_sales_content_service: Optional[SalesContentService] = None


def get_sales_content_service() -> SalesContentService:
    """Get singleton sales content service instance."""
    global _sales_content_service
    if _sales_content_service is None:
        _sales_content_service = SalesContentService()
    return _sales_content_service
