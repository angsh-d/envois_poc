"""
UC10 Claim Validation Service for Clinical Intelligence Platform.

Validates marketing claims against clinical evidence.
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext
from app.agents.literature_agent import LiteratureAgent
from app.agents.registry_agent import RegistryAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.data_agent import get_study_data
from app.services.llm_service import get_llm_service
from app.services.prompt_service import get_prompt_service
from data.loaders.yaml_loader import get_hybrid_loader

logger = logging.getLogger(__name__)


class ClaimValidationService:
    """
    Service for UC10: Claim Validation Engine.

    Validates marketing claims against:
    - Clinical study data
    - Registry benchmarks
    - Literature evidence
    """

    def __init__(self):
        """Initialize claim validation service."""
        self._literature_agent = LiteratureAgent()
        self._registry_agent = RegistryAgent()
        self._safety_agent = SafetyAgent()
        self._llm = get_llm_service()
        self._prompts = get_prompt_service()
        self._doc_loader = get_hybrid_loader()

    async def validate_claim(self, claim: str) -> Dict[str, Any]:
        """
        Validate a marketing claim against available evidence.

        Args:
            claim: Marketing claim to validate

        Returns:
            Dict with validation result and analysis
        """
        request_id = str(uuid.uuid4())

        # Get study metrics
        study_metrics = self._get_study_metrics()

        # Get safety data for additional metrics
        safety_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "study"}
        )
        safety_result = await self._safety_agent.run(safety_context)

        # Get registry data
        reg_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "all"}
        )
        registry_result = await self._registry_agent.run(reg_context)
        reg_data = registry_result.data if registry_result.success else {}

        # Get literature data
        lit_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "all"}
        )
        literature_result = await self._literature_agent.run(lit_context)
        lit_data = literature_result.data if literature_result.success else {}

        # Perform rule-based validation first
        rule_based_result = self._rule_based_validation(claim, study_metrics, reg_data, lit_data)

        # Generate LLM-based analysis
        llm_analysis = await self._llm_validation(
            claim, study_metrics, reg_data, lit_data
        )

        # Combine results
        validation_result = self._combine_validations(
            claim, rule_based_result, llm_analysis
        )

        # Build response
        return {
            "success": True,
            "claim": claim,
            "validated_at": datetime.utcnow().isoformat(),
            "claim_validated": validation_result["validated"],
            "validation_status": validation_result["status"],
            "supporting_evidence": validation_result["supporting_evidence"],
            "contradicting_evidence": validation_result["contradicting_evidence"],
            "evidence_gaps": validation_result["evidence_gaps"],
            "confidence_level": validation_result["confidence_level"],
            "recommended_language": validation_result["recommended_language"],
            "analysis": llm_analysis,
            "compliance_notes": self._get_compliance_notes(claim, validation_result),
            "sources": self._collect_sources(safety_result, registry_result, literature_result),
            "study_data_used": study_metrics,
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
                "follow_up_months": 24,
                "data_source": "H-34 Study Database",
            }
        except Exception as e:
            logger.error(f"Failed to load study metrics from database: {e}")
            raise ValueError(f"Cannot load study metrics: {e}")

    def _rule_based_validation(
        self,
        claim: str,
        study_metrics: Dict,
        reg_data: Dict,
        lit_data: Dict
    ) -> Dict[str, Any]:
        """Perform rule-based claim validation."""
        claim_lower = claim.lower()

        supporting = []
        contradicting = []
        gaps = []

        # Check for survival claims
        if "survival" in claim_lower:
            survival = study_metrics.get("survival_rate", 0)
            # Extract percentage from claim if present
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', claim)
            if pct_match:
                claimed_pct = float(pct_match.group(1)) / 100
                if abs(claimed_pct - survival) < 0.02:  # Within 2%
                    supporting.append({
                        "type": "study_data",
                        "evidence": f"Study shows {survival*100:.1f}% 2-year survival",
                        "claim_value": f"{claimed_pct*100:.1f}%",
                    })
                else:
                    contradicting.append({
                        "type": "study_data",
                        "evidence": f"Study shows {survival*100:.1f}% (claim states {claimed_pct*100:.1f}%)",
                    })
            else:
                supporting.append({
                    "type": "study_data",
                    "evidence": f"Study shows {survival*100:.1f}% 2-year survival",
                })

        # Check for revision rate claims
        if "revision" in claim_lower:
            revision = study_metrics.get("revision_rate", 0)
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', claim)
            if pct_match:
                claimed_pct = float(pct_match.group(1)) / 100
                if abs(claimed_pct - revision) < 0.02:
                    supporting.append({
                        "type": "study_data",
                        "evidence": f"Study shows {revision*100:.1f}% revision rate",
                    })
                else:
                    contradicting.append({
                        "type": "study_data",
                        "evidence": f"Study shows {revision*100:.1f}% (claim states {claimed_pct*100:.1f}%)",
                    })

        # Check for comparative claims ("superior", "better", "best")
        comparative_words = ["superior", "better", "best", "outperforms", "exceeds"]
        if any(word in claim_lower for word in comparative_words):
            # Need registry comparison to support
            comparisons = reg_data.get("comparisons", {})
            if comparisons:
                rev_comp = comparisons.get("revision_rate_2yr", {})
                n_better = rev_comp.get("n_better_than", 0)
                n_total = reg_data.get("n_registries", 5)

                if n_better >= n_total / 2:
                    supporting.append({
                        "type": "registry_comparison",
                        "evidence": f"Favorable vs {n_better} of {n_total} registries",
                    })
                else:
                    contradicting.append({
                        "type": "registry_comparison",
                        "evidence": f"Only favorable vs {n_better} of {n_total} registries - comparative claim may be overstated",
                    })
            else:
                gaps.append("Registry comparison data needed for comparative claims")

        # Check for superlative claims ("best", "leading", "first")
        superlative_words = ["best", "leading", "first", "only", "unique"]
        if any(word in claim_lower for word in superlative_words):
            gaps.append("Superlative claims typically require comprehensive competitive data")
            contradicting.append({
                "type": "regulatory_concern",
                "evidence": "Superlative language may not be substantiable",
            })

        # Check for MCID claims
        if "mcid" in claim_lower or "clinically meaningful" in claim_lower:
            mcid = study_metrics.get("mcid_achievement", 0)
            supporting.append({
                "type": "study_data",
                "evidence": f"{mcid*100:.0f}% of patients achieved MCID",
            })

        # Check for HHS improvement claims
        if "harris hip" in claim_lower or "hhs" in claim_lower:
            hhs = study_metrics.get("hhs_improvement", 0)
            supporting.append({
                "type": "study_data",
                "evidence": f"Mean HHS improvement of {hhs:.1f} points",
            })

        return {
            "supporting": supporting,
            "contradicting": contradicting,
            "gaps": gaps,
        }

    async def _llm_validation(
        self,
        claim: str,
        study_metrics: Dict,
        reg_data: Dict,
        lit_data: Dict
    ) -> str:
        """Generate LLM-based claim validation analysis."""
        # Format data for prompt
        registry_text = self._format_registry_data(reg_data)
        literature_text = self._format_literature_data(lit_data)

        prompt = self._prompts.load("claim_validation", {
            "claim": claim,
            "n_patients": study_metrics.get("n_patients", 0),
            "survival_rate": f"{study_metrics.get('survival_rate', 0)*100:.1f}%",
            "revision_rate": f"{study_metrics.get('revision_rate', 0)*100:.1f}%",
            "hhs_improvement": study_metrics.get("hhs_improvement", 0),
            "mcid_achievement": f"{study_metrics.get('mcid_achievement', 0)*100:.0f}%",
            "registry_data": registry_text,
            "literature_data": literature_text,
        })

        analysis = await self._llm.generate(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.1,
            max_tokens=1500
        )

        return analysis.strip()

    def _format_registry_data(self, reg_data: Dict) -> str:
        """Format registry data for validation prompt."""
        if not reg_data:
            return "Registry data not available."

        lines = ["Registry Benchmarks:"]
        registries = reg_data.get("registries", [])

        for reg in registries[:5]:
            abbr = reg.get("abbreviation", "Unknown")
            revision = reg.get("revision_rates", {}).get("2yr")
            survival = reg.get("survival_rates", {}).get("2yr")

            if revision is not None:
                line = f"- {abbr}: Revision {revision*100:.1f}%"
                if survival:
                    line += f", Survival {survival*100:.1f}%"
                lines.append(line)

        return "\n".join(lines)

    def _format_literature_data(self, lit_data: Dict) -> str:
        """Format literature data for validation prompt."""
        if not lit_data:
            return "Literature benchmarks not available."

        benchmarks = lit_data.get("aggregate_benchmarks", {})
        n_pubs = lit_data.get("n_publications", 0)

        lines = [f"Literature Benchmarks ({n_pubs} publications):"]

        for metric, data in benchmarks.items():
            if isinstance(data, dict):
                mean = data.get("mean")
                if mean is not None:
                    if mean < 1:
                        lines.append(f"- {metric}: {mean*100:.1f}%")
                    else:
                        lines.append(f"- {metric}: {mean:.1f}")

        return "\n".join(lines)

    def _combine_validations(
        self,
        claim: str,
        rule_based: Dict,
        llm_analysis: str
    ) -> Dict[str, Any]:
        """Combine rule-based and LLM validation results."""
        supporting = rule_based.get("supporting", [])
        contradicting = rule_based.get("contradicting", [])
        gaps = rule_based.get("gaps", [])

        # Determine validation status
        if len(contradicting) > 0:
            if len(supporting) > len(contradicting):
                status = "partial"
                validated = "partial"
            else:
                status = "not_validated"
                validated = False
        elif len(supporting) > 0:
            if len(gaps) > 0:
                status = "partial"
                validated = "partial"
            else:
                status = "validated"
                validated = True
        else:
            status = "insufficient_evidence"
            validated = False

        # Determine confidence level
        if status == "validated" and len(supporting) >= 2:
            confidence = "high"
        elif status == "partial":
            confidence = "medium"
        else:
            confidence = "low"

        # Generate recommended language
        recommended = self._generate_recommended_language(
            claim, status, supporting, contradicting
        )

        return {
            "validated": validated,
            "status": status,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "evidence_gaps": gaps,
            "confidence_level": confidence,
            "recommended_language": recommended,
        }

    def _generate_recommended_language(
        self,
        claim: str,
        status: str,
        supporting: List,
        contradicting: List
    ) -> Optional[str]:
        """Generate recommended alternative language for claim."""
        if status == "validated":
            return None  # Original claim is acceptable

        # Build recommended language based on supporting evidence
        if not supporting:
            return "Insufficient evidence to support this claim. Consider removing or reformulating."

        # Extract key evidence points
        evidence_points = []
        for ev in supporting:
            evidence_points.append(ev.get("evidence", ""))

        # Generate recommended language
        claim_lower = claim.lower()

        if "superior" in claim_lower or "better" in claim_lower:
            # Soften comparative language
            return (
                "Consider: 'DELTA Revision Cup demonstrates competitive performance"
                "compared to international registry benchmarks' instead of using comparative language."
            )

        if "best" in claim_lower or "leading" in claim_lower:
            # Remove superlatives
            return (
                "Remove superlative language. Consider: 'DELTA Revision Cup demonstrates"
                "favorable clinical outcomes' with specific data points."
            )

        # Default recommendation
        return (
            "Consider qualifying the claim with specific data points from the study. "
            f"Available evidence: {'; '.join(evidence_points[:2])}"
        )

    def _get_compliance_notes(
        self,
        claim: str,
        validation_result: Dict
    ) -> List[str]:
        """Get compliance notes for the claim."""
        notes = []
        claim_lower = claim.lower()

        # Check for promotional red flags
        if any(word in claim_lower for word in ["best", "leading", "first", "only"]):
            notes.append(
                "FDA/EU MDR: Superlative claims require comprehensive evidence. "
                "Consider removing or qualifying."
            )

        if any(word in claim_lower for word in ["superior", "better", "outperforms"]):
            notes.append(
                "Comparative claims must be substantiated by head-to-head data or "
                "validated benchmark comparisons."
            )

        if "safe" in claim_lower or "safety" in claim_lower:
            notes.append(
                "Safety claims are closely scrutinized. Ensure all safety data "
                "is accurately represented."
            )

        if validation_result["status"] != "validated":
            notes.append(
                "Claim may require modification for regulatory compliance. "
                "Review recommended language."
            )

        if not notes:
            notes.append("No significant compliance concerns identified.")

        return notes

    def _collect_sources(self, safety_result, registry_result, literature_result) -> List[Dict]:
        """Collect all sources from agent results."""
        sources = []

        if safety_result.success:
            for source in safety_result.sources:
                sources.append(source.to_dict())

        if registry_result.success:
            for source in registry_result.sources:
                sources.append(source.to_dict())

        if literature_result.success:
            for source in literature_result.sources:
                sources.append(source.to_dict())

        return sources


# Singleton instance
_claim_validation_service: Optional[ClaimValidationService] = None


def get_claim_validation_service() -> ClaimValidationService:
    """Get singleton claim validation service instance."""
    global _claim_validation_service
    if _claim_validation_service is None:
        _claim_validation_service = ClaimValidationService()
    return _claim_validation_service
