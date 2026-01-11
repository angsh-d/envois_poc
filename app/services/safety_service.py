"""
UC2 Safety Service for Clinical Intelligence Platform.

Orchestrates agents for safety signal detection and analysis.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext, AgentType, get_orchestrator
from app.agents.safety_agent import SafetyAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.registry_agent import RegistryAgent
from app.agents.synthesis_agent import SynthesisAgent
from data.loaders.yaml_loader import get_doc_loader

logger = logging.getLogger(__name__)


class SafetyService:
    """
    Service for UC2: Safety Signal Detection.

    Orchestrates multiple agents to:
    - Analyze study safety data
    - Compare against protocol thresholds
    - Compare against registry benchmarks
    - Compare against literature benchmarks
    - Generate narratives with recommendations
    """

    def __init__(self):
        """Initialize safety service."""
        self._safety_agent = SafetyAgent()
        self._literature_agent = LiteratureAgent()
        self._registry_agent = RegistryAgent()
        self._synthesis_agent = SynthesisAgent()
        self._doc_loader = get_doc_loader()

    async def get_safety_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive safety analysis for the study.

        Returns:
            Dict with safety signals, metrics, and comparisons
        """
        request_id = str(uuid.uuid4())

        # Create context for study-wide safety analysis
        context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "study"}
        )

        # Run safety agent
        safety_result = await self._safety_agent.run(context)

        if not safety_result.success:
            return {
                "success": False,
                "error": safety_result.error,
                "assessment_date": datetime.utcnow().isoformat(),
            }

        data = safety_result.data

        # Run synthesis for comprehensive narrative
        synthesis_context = AgentContext(
            request_id=request_id,
            parameters={"synthesis_type": "uc2_safety"},
            shared_data={
                "safety": safety_result.to_dict(),
            }
        )

        # Get literature benchmarks
        lit_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "all"}
        )
        literature_result = await self._literature_agent.run(lit_context)
        if literature_result.success:
            synthesis_context.shared_data["literature"] = literature_result.to_dict()

        # Get registry comparison
        registry_context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "compare",
                "study_data": {
                    "revision_rate": data.get("metrics", [{}])[0].get("rate", 0) if data.get("metrics") else 0,
                    "survival_2yr": 1 - (data.get("metrics", [{}])[0].get("rate", 0) if data.get("metrics") else 0),
                }
            }
        )
        registry_result = await self._registry_agent.run(registry_context)
        if registry_result.success:
            synthesis_context.shared_data["registry"] = registry_result.to_dict()

        synthesis_result = await self._synthesis_agent.run(synthesis_context)

        # Build response
        return {
            "success": True,
            "assessment_date": datetime.utcnow().isoformat(),
            "n_patients": data.get("n_patients", 0),
            "overall_status": data.get("overall_status", "unknown"),
            "signals": data.get("signals", []),
            "n_signals": data.get("n_signals", 0),
            "metrics": data.get("metrics", []),
            "registry_comparison": data.get("registry_comparison", {}),
            "literature_benchmarks": literature_result.data.get("aggregate_benchmarks", {}) if literature_result.success else {},
            "narrative": synthesis_result.narrative if synthesis_result.success else safety_result.narrative,
            "sources": [s.to_dict() for s in safety_result.sources],
            "confidence": safety_result.confidence,
            "execution_time_ms": safety_result.execution_time_ms,
        }

    async def get_patient_safety(self, patient_id: str) -> Dict[str, Any]:
        """
        Get safety analysis for a specific patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Dict with patient safety data and risk factors
        """
        request_id = str(uuid.uuid4())

        context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            parameters={"query_type": "patient"}
        )

        safety_result = await self._safety_agent.run(context)

        if not safety_result.success:
            return {
                "success": False,
                "patient_id": patient_id,
                "error": safety_result.error,
            }

        data = safety_result.data

        return {
            "success": True,
            "patient_id": patient_id,
            "assessment_date": datetime.utcnow().isoformat(),
            "adverse_events": data.get("adverse_events", []),
            "n_adverse_events": data.get("n_adverse_events", 0),
            "has_sae": data.get("has_sae", False),
            "risk_factors": data.get("risk_factors", []),
            "risk_level": data.get("risk_level", "low"),
            "sources": [s.to_dict() for s in safety_result.sources],
            "execution_time_ms": safety_result.execution_time_ms,
        }

    async def detect_signals(self) -> Dict[str, Any]:
        """
        Detect and classify safety signals.

        Returns:
            Dict with prioritized safety signals
        """
        request_id = str(uuid.uuid4())

        context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "signals"}
        )

        safety_result = await self._safety_agent.run(context)

        if not safety_result.success:
            return {
                "success": False,
                "error": safety_result.error,
            }

        data = safety_result.data

        return {
            "success": True,
            "detection_date": datetime.utcnow().isoformat(),
            "signals": data.get("signals", []),
            "n_signals": data.get("n_signals", 0),
            "high_priority": data.get("high_priority", []),
            "medium_priority": data.get("medium_priority", []),
            "requires_dsmb_review": data.get("requires_dsmb_review", False),
            "sources": [s.to_dict() for s in safety_result.sources],
            "execution_time_ms": safety_result.execution_time_ms,
        }

    async def compare_to_benchmarks(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare study metrics to literature and registry benchmarks.

        Args:
            metrics: Dict of metric names to values

        Returns:
            Dict with benchmark comparisons
        """
        request_id = str(uuid.uuid4())

        # Compare to literature
        lit_context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "compare",
                "study_data": metrics
            }
        )
        literature_result = await self._literature_agent.run(lit_context)

        # Compare to registry
        reg_context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "compare",
                "study_data": metrics
            }
        )
        registry_result = await self._registry_agent.run(reg_context)

        comparisons = []
        sources = []

        if literature_result.success:
            lit_data = literature_result.data
            comparisons.append({
                "source": "literature",
                "comparisons": lit_data.get("comparisons", []),
                "overall_assessment": lit_data.get("overall_assessment"),
            })
            sources.extend(literature_result.sources)

        if registry_result.success:
            reg_data = registry_result.data
            comparisons.append({
                "source": "registry",
                "comparisons": reg_data.get("comparisons", []),
                "signals": reg_data.get("signals", []),
            })
            sources.extend(registry_result.sources)

        return {
            "success": True,
            "comparison_date": datetime.utcnow().isoformat(),
            "input_metrics": metrics,
            "comparisons": comparisons,
            "sources": [s.to_dict() for s in sources],
        }

    def get_thresholds(self) -> Dict[str, Any]:
        """
        Get protocol and registry safety thresholds.

        Returns:
            Dict with threshold definitions
        """
        protocol_rules = self._doc_loader.load_protocol_rules()
        registry_norms = self._doc_loader.load_registry_norms()

        return {
            "protocol_thresholds": protocol_rules.safety_thresholds,
            "registry_concern_thresholds": registry_norms.concern_thresholds,
            "registry_risk_thresholds": registry_norms.risk_thresholds,
            "protocol_version": protocol_rules.protocol_version,
        }

    async def get_adverse_event_summary(self) -> Dict[str, Any]:
        """
        Get summary of adverse events.

        Returns:
            Dict with adverse event statistics
        """
        # Get safety summary
        safety_summary = await self.get_safety_summary()

        if not safety_summary.get("success"):
            return safety_summary

        metrics = safety_summary.get("metrics", [])

        # Extract adverse event metrics
        ae_metrics = {}
        for metric in metrics:
            metric_name = metric.get("metric", "")
            if "rate" in metric_name:
                ae_metrics[metric_name] = {
                    "rate": metric.get("rate", 0),
                    "count": metric.get("count", 0),
                    "threshold": metric.get("threshold", 0),
                    "signal": metric.get("signal", False),
                }

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "n_patients": safety_summary.get("n_patients", 0),
            "adverse_event_metrics": ae_metrics,
            "signals": safety_summary.get("signals", []),
            "overall_status": safety_summary.get("overall_status", "unknown"),
        }


# Singleton instance
_safety_service: Optional[SafetyService] = None


def get_safety_service() -> SafetyService:
    """Get singleton safety service instance."""
    global _safety_service
    if _safety_service is None:
        _safety_service = SafetyService()
    return _safety_service
