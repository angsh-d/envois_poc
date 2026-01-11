"""
UC3 Deviations Service for Clinical Intelligence Platform.

Orchestrates agents for protocol deviation detection and classification.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext, AgentType, get_orchestrator
from app.agents.protocol_agent import ProtocolAgent
from app.agents.data_agent import DataAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.synthesis_agent import SynthesisAgent
from data.loaders.yaml_loader import get_doc_loader

logger = logging.getLogger(__name__)


class DeviationsService:
    """
    Service for UC3: Protocol Deviation Detection.

    Orchestrates multiple agents to:
    - Load protocol rules (Document-as-Code)
    - Query patient visit data
    - Detect and classify deviations
    - Generate narratives with recommendations
    """

    def __init__(self):
        """Initialize deviations service."""
        self._orchestrator = get_orchestrator()
        self._protocol_agent = ProtocolAgent()
        self._data_agent = DataAgent()
        self._compliance_agent = ComplianceAgent()
        self._synthesis_agent = SynthesisAgent()
        self._doc_loader = get_doc_loader()

    async def get_study_deviations(self) -> Dict[str, Any]:
        """
        Get all protocol deviations across the study.

        Returns:
            Dict with deviation summary and details
        """
        request_id = str(uuid.uuid4())

        # Create context for study-wide deviation check
        context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "study"}
        )

        # Run compliance agent
        compliance_result = await self._compliance_agent.run(context)

        if not compliance_result.success:
            return {
                "success": False,
                "error": compliance_result.error,
                "assessment_date": datetime.utcnow().isoformat(),
            }

        data = compliance_result.data
        deviations = data.get("deviations_by_visit", {})

        # Get protocol rules for context
        protocol_rules = self._doc_loader.load_protocol_rules()

        # Build response
        return {
            "success": True,
            "assessment_date": datetime.utcnow().isoformat(),
            "total_visits": data.get("total_visits", 0),
            "total_deviations": data.get("n_deviations", 0),
            "deviation_rate": data.get("deviation_rate", 0),
            "by_severity": data.get("by_severity", {}),
            "by_visit": deviations,
            "protocol_version": protocol_rules.protocol_version,
            "sources": [s.to_dict() for s in compliance_result.sources],
            "execution_time_ms": compliance_result.execution_time_ms,
        }

    async def get_patient_deviations(self, patient_id: str) -> Dict[str, Any]:
        """
        Get all protocol deviations for a specific patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Dict with patient deviation details and narrative
        """
        request_id = str(uuid.uuid4())

        # Create context for patient deviation check
        context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            parameters={"query_type": "patient"}
        )

        # Run compliance agent
        compliance_result = await self._compliance_agent.run(context)

        if not compliance_result.success:
            return {
                "success": False,
                "patient_id": patient_id,
                "error": compliance_result.error,
            }

        data = compliance_result.data

        # Add synthesis for narrative
        synthesis_context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            parameters={"synthesis_type": "uc3_deviations"},
            shared_data={"compliance": compliance_result.to_dict()}
        )
        synthesis_result = await self._synthesis_agent.run(synthesis_context)

        return {
            "success": True,
            "patient_id": patient_id,
            "assessment_date": datetime.utcnow().isoformat(),
            "n_visits": data.get("n_visits", 0),
            "n_deviations": data.get("n_deviations", 0),
            "compliance_rate": data.get("compliance_rate", 1.0),
            "deviations": data.get("deviations", []),
            "deviation_summary": data.get("deviation_summary", {}),
            "missing_assessments": data.get("missing_assessments", []),
            "narrative": synthesis_result.narrative if synthesis_result.success else compliance_result.narrative,
            "sources": [s.to_dict() for s in compliance_result.sources],
            "execution_time_ms": compliance_result.execution_time_ms,
        }

    async def check_visit_compliance(
        self,
        patient_id: str,
        visit_id: str,
        actual_day: int
    ) -> Dict[str, Any]:
        """
        Check if a specific visit is compliant with protocol windows.

        Args:
            patient_id: Patient identifier
            visit_id: Visit identifier (e.g., "fu_6mo")
            actual_day: Actual day of visit from surgery

        Returns:
            Dict with compliance status and deviation details if any
        """
        request_id = str(uuid.uuid4())

        # Create context for visit check
        context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            visit_id=visit_id,
            parameters={
                "query_type": "visit",
                "actual_day": actual_day
            }
        )

        # Run compliance agent
        compliance_result = await self._compliance_agent.run(context)

        if not compliance_result.success:
            return {
                "success": False,
                "error": compliance_result.error,
            }

        data = compliance_result.data

        # Build response
        response = {
            "success": True,
            "patient_id": patient_id,
            "visit_id": visit_id,
            "visit_name": data.get("visit_name"),
            "actual_day": actual_day,
            "target_day": data.get("target_day"),
            "allowed_range": data.get("allowed_range"),
            "is_compliant": data.get("is_compliant", True),
        }

        if not data.get("is_compliant"):
            deviation = data.get("deviation", {})
            response["deviation"] = {
                "days_out_of_window": deviation.get("deviation_days", 0),
                "classification": deviation.get("classification", "minor"),
                "action": deviation.get("action", "Document deviation"),
                "requires_explanation": deviation.get("requires_explanation", False),
                "affects_evaluability": deviation.get("affects_evaluability", False),
            }

        response["sources"] = [s.to_dict() for s in compliance_result.sources]
        response["execution_time_ms"] = compliance_result.execution_time_ms

        return response

    def get_visit_windows(self) -> Dict[str, Any]:
        """
        Get all protocol-defined visit windows.

        Returns:
            Dict with visit window definitions
        """
        protocol_rules = self._doc_loader.load_protocol_rules()

        windows = []
        for visit in protocol_rules.visits:
            min_day, max_day = visit.get_window_range()
            windows.append({
                "visit_id": visit.id,
                "visit_name": visit.name,
                "target_day": visit.target_day,
                "window_minus": visit.window_minus,
                "window_plus": visit.window_plus,
                "min_day": min_day,
                "max_day": max_day,
                "required_assessments": visit.required_assessments,
                "is_primary_endpoint": visit.is_primary_endpoint,
            })

        return {
            "protocol_id": protocol_rules.protocol_id,
            "protocol_version": protocol_rules.protocol_version,
            "reference_point": "surgery_date",
            "windows": windows,
            "deviation_classification": protocol_rules.deviation_classification,
        }

    def get_deviation_classification_rules(self) -> Dict[str, Any]:
        """
        Get protocol-defined deviation classification rules.

        Returns:
            Dict with classification rules and thresholds
        """
        protocol_rules = self._doc_loader.load_protocol_rules()

        return {
            "protocol_id": protocol_rules.protocol_id,
            "protocol_version": protocol_rules.protocol_version,
            "classification_rules": protocol_rules.deviation_classification,
        }

    async def get_compliance_rate(self) -> Dict[str, Any]:
        """
        Get overall protocol compliance rate by visit type.

        Returns:
            Dict with compliance rates per visit
        """
        # Get study-wide deviation data
        study_data = await self.get_study_deviations()

        if not study_data.get("success"):
            return study_data

        # Get visit windows for reference
        windows = self.get_visit_windows()

        # Calculate compliance per visit
        by_visit = []
        total_visits = study_data.get("total_visits", 0)
        total_deviations = study_data.get("total_deviations", 0)

        for window in windows.get("windows", []):
            visit_id = window["visit_id"]
            deviations_at_visit = study_data.get("by_visit", {}).get(visit_id, 0)
            # Estimate visits per type (would come from data in production)
            est_visits = max(1, total_visits // len(windows.get("windows", [1])))
            compliant = est_visits - deviations_at_visit
            compliance_pct = (compliant / est_visits) * 100 if est_visits > 0 else 100

            by_visit.append({
                "visit_id": visit_id,
                "visit_name": window["visit_name"],
                "compliance_pct": round(compliance_pct, 1),
                "deviations": deviations_at_visit,
                "is_primary_endpoint": window["is_primary_endpoint"],
            })

        overall_compliance = (1 - study_data.get("deviation_rate", 0)) * 100

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "overall_compliance_pct": round(overall_compliance, 1),
            "by_visit": by_visit,
            "by_severity": study_data.get("by_severity", {}),
            "total_visits": total_visits,
            "total_deviations": total_deviations,
        }


# Singleton instance
_deviations_service: Optional[DeviationsService] = None


def get_deviations_service() -> DeviationsService:
    """Get singleton deviations service instance."""
    global _deviations_service
    if _deviations_service is None:
        _deviations_service = DeviationsService()
    return _deviations_service
