"""
UC1 Readiness Service for Clinical Intelligence Platform.

Orchestrates agents for regulatory submission readiness assessment.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext, AgentType, get_orchestrator
from app.agents.protocol_agent import ProtocolAgent
from app.agents.data_agent import DataAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.synthesis_agent import SynthesisAgent
from data.loaders.yaml_loader import get_doc_loader

logger = logging.getLogger(__name__)


class ReadinessService:
    """
    Service for UC1: Regulatory Submission Readiness.

    Orchestrates multiple agents to assess:
    - Data completeness
    - Protocol compliance
    - Safety signal status
    - Endpoint achievement
    """

    def __init__(self):
        """Initialize readiness service."""
        self._protocol_agent = ProtocolAgent()
        self._data_agent = DataAgent()
        self._compliance_agent = ComplianceAgent()
        self._safety_agent = SafetyAgent()
        self._literature_agent = LiteratureAgent()
        self._synthesis_agent = SynthesisAgent()
        self._doc_loader = get_doc_loader()

    async def get_readiness_assessment(self) -> Dict[str, Any]:
        """
        Get comprehensive regulatory readiness assessment.

        Returns:
            Dict with readiness status across all dimensions
        """
        request_id = str(uuid.uuid4())

        # Gather data from multiple agents in parallel
        data_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "summary"}
        )
        compliance_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "study"}
        )
        safety_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "study"}
        )

        # Run agents
        data_result = await self._data_agent.run(data_context)
        compliance_result = await self._compliance_agent.run(compliance_context)
        safety_result = await self._safety_agent.run(safety_context)

        # Get protocol requirements
        protocol_rules = self._doc_loader.load_protocol_rules()

        # Calculate readiness scores
        enrollment_status = self._assess_enrollment(
            data_result.data if data_result.success else {},
            protocol_rules
        )
        compliance_status = self._assess_compliance(
            compliance_result.data if compliance_result.success else {}
        )
        safety_status = self._assess_safety(
            safety_result.data if safety_result.success else {}
        )
        data_status = self._assess_data_completeness(
            data_result.data if data_result.success else {},
            protocol_rules
        )

        # Calculate overall readiness
        is_ready, blocking_issues = self._calculate_overall_readiness(
            enrollment_status,
            compliance_status,
            safety_status,
            data_status
        )

        # Generate narrative
        synthesis_context = AgentContext(
            request_id=request_id,
            parameters={"synthesis_type": "uc1_readiness"},
            shared_data={
                "data": data_result.to_dict() if data_result.success else {},
                "compliance": compliance_result.to_dict() if compliance_result.success else {},
                "safety": safety_result.to_dict() if safety_result.success else {},
            }
        )
        synthesis_result = await self._synthesis_agent.run(synthesis_context)

        # Collect all sources
        sources = []
        for result in [data_result, compliance_result, safety_result]:
            if result.success:
                sources.extend([s.to_dict() for s in result.sources])

        return {
            "success": True,
            "assessment_date": datetime.utcnow().isoformat(),
            "protocol_id": protocol_rules.protocol_id,
            "protocol_version": protocol_rules.protocol_version,
            "is_ready": is_ready,
            "blocking_issues": blocking_issues,
            "enrollment": enrollment_status,
            "compliance": compliance_status,
            "safety": safety_status,
            "data_completeness": data_status,
            "narrative": synthesis_result.narrative if synthesis_result.success else None,
            "sources": sources,
            "execution_time_ms": sum([
                data_result.execution_time_ms,
                compliance_result.execution_time_ms,
                safety_result.execution_time_ms,
            ]),
        }

    async def get_patient_readiness(self, patient_id: str) -> Dict[str, Any]:
        """
        Get readiness assessment for a specific patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Dict with patient readiness status
        """
        request_id = str(uuid.uuid4())

        # Get patient compliance
        compliance_context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            parameters={"query_type": "patient"}
        )
        compliance_result = await self._compliance_agent.run(compliance_context)

        if not compliance_result.success:
            return {
                "success": False,
                "patient_id": patient_id,
                "error": compliance_result.error,
            }

        data = compliance_result.data

        # Determine if patient is evaluable
        is_evaluable = True
        blocking_issues = []
        warnings = []

        # Check deviations
        for dev in data.get("deviations", []):
            if dev.get("affects_evaluability"):
                is_evaluable = False
                blocking_issues.append({
                    "type": "critical_deviation",
                    "description": f"Critical deviation at {dev.get('visit_name')}",
                    "visit_id": dev.get("visit_id"),
                })
            elif dev.get("classification") == "major":
                warnings.append({
                    "type": "major_deviation",
                    "description": f"Major deviation at {dev.get('visit_name')}",
                })

        # Check missing assessments
        for missing in data.get("missing_assessments", []):
            if missing.get("is_primary_endpoint"):
                is_evaluable = False
                blocking_issues.append({
                    "type": "missing_primary_endpoint",
                    "description": f"Missing {missing['assessment']} at {missing['visit_id']}",
                })

        # Generate synthesis
        synthesis_context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            parameters={"synthesis_type": "uc1_readiness"},
            shared_data={"compliance": compliance_result.to_dict()}
        )
        synthesis_result = await self._synthesis_agent.run(synthesis_context)

        return {
            "success": True,
            "patient_id": patient_id,
            "assessment_date": datetime.utcnow().isoformat(),
            "is_evaluable": is_evaluable,
            "blocking_issues": blocking_issues,
            "warnings": warnings,
            "compliance_rate": data.get("compliance_rate", 1.0),
            "n_deviations": data.get("n_deviations", 0),
            "deviation_summary": data.get("deviation_summary", {}),
            "narrative": synthesis_result.narrative if synthesis_result.success else None,
            "sources": [s.to_dict() for s in compliance_result.sources],
            "execution_time_ms": compliance_result.execution_time_ms,
        }

    async def get_visit_readiness(
        self,
        patient_id: str,
        visit_id: str
    ) -> Dict[str, Any]:
        """
        Get readiness for a specific patient visit.

        Args:
            patient_id: Patient identifier
            visit_id: Visit identifier

        Returns:
            Dict with visit readiness status
        """
        # Get protocol window
        window = self._protocol_agent.get_visit_window(visit_id)

        if not window:
            return {
                "success": False,
                "error": f"Unknown visit ID: {visit_id}",
            }

        return {
            "success": True,
            "patient_id": patient_id,
            "visit_id": visit_id,
            "visit_name": window.name,
            "target_day": window.target_day,
            "allowed_range": window.get_window_range(),
            "required_assessments": window.required_assessments,
            "is_primary_endpoint": window.is_primary_endpoint,
        }

    def _assess_enrollment(
        self,
        data: Dict[str, Any],
        protocol: Any
    ) -> Dict[str, Any]:
        """Assess enrollment status."""
        enrolled = data.get("enrolled", 0)
        target = protocol.sample_size_target
        interim = protocol.sample_size_interim

        status = "on_track"
        if enrolled >= target:
            status = "complete"
        elif enrolled >= interim:
            status = "interim_reached"
        elif enrolled < interim * 0.5:
            status = "behind"

        return {
            "enrolled": enrolled,
            "target": target,
            "interim_target": interim,
            "percent_complete": round((enrolled / target) * 100, 1) if target > 0 else 0,
            "status": status,
            "is_ready": enrolled >= target,
        }

    def _assess_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess protocol compliance status."""
        deviation_rate = data.get("deviation_rate", 0)
        by_severity = data.get("by_severity", {})

        critical_count = by_severity.get("critical", 0)
        major_count = by_severity.get("major", 0)

        status = "acceptable"
        if critical_count > 0:
            status = "concerning"
        elif major_count > 3:
            status = "monitoring"

        return {
            "deviation_rate": round(deviation_rate * 100, 1),
            "by_severity": by_severity,
            "status": status,
            "is_ready": critical_count == 0,
        }

    def _assess_safety(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess safety status."""
        n_signals = data.get("n_signals", 0)
        overall_status = data.get("overall_status", "unknown")

        is_ready = overall_status in ["acceptable", "monitoring"]

        return {
            "n_signals": n_signals,
            "overall_status": overall_status,
            "is_ready": is_ready,
        }

    def _assess_data_completeness(
        self,
        data: Dict[str, Any],
        protocol: Any
    ) -> Dict[str, Any]:
        """Assess data completeness."""
        enrolled = data.get("enrolled", 0)
        completed = data.get("completed", 0)
        withdrawn = data.get("withdrawn", 0)

        evaluable = enrolled - withdrawn
        completion_rate = (completed / evaluable) * 100 if evaluable > 0 else 0

        return {
            "enrolled": enrolled,
            "completed": completed,
            "withdrawn": withdrawn,
            "evaluable": evaluable,
            "completion_rate": round(completion_rate, 1),
            "is_ready": completion_rate >= 80,
        }

    def _calculate_overall_readiness(
        self,
        enrollment: Dict,
        compliance: Dict,
        safety: Dict,
        data: Dict
    ) -> tuple:
        """Calculate overall readiness and identify blocking issues."""
        blocking_issues = []

        if not enrollment.get("is_ready"):
            blocking_issues.append({
                "category": "enrollment",
                "issue": f"Enrollment at {enrollment['percent_complete']}% (target: 100%)",
            })

        if not compliance.get("is_ready"):
            blocking_issues.append({
                "category": "compliance",
                "issue": f"Critical deviations detected",
            })

        if not safety.get("is_ready"):
            blocking_issues.append({
                "category": "safety",
                "issue": f"Safety status: {safety['overall_status']}",
            })

        if not data.get("is_ready"):
            blocking_issues.append({
                "category": "data_completeness",
                "issue": f"Completion rate: {data['completion_rate']}%",
            })

        is_ready = len(blocking_issues) == 0

        return is_ready, blocking_issues

    def get_protocol_requirements(self) -> Dict[str, Any]:
        """Get protocol requirements summary."""
        protocol = self._doc_loader.load_protocol_rules()

        return {
            "protocol_id": protocol.protocol_id,
            "protocol_version": protocol.protocol_version,
            "title": protocol.title,
            "sample_size": {
                "target": protocol.sample_size_target,
                "interim": protocol.sample_size_interim,
            },
            "primary_endpoint": {
                "id": protocol.primary_endpoint.id,
                "name": protocol.primary_endpoint.name,
                "success_criterion": protocol.primary_endpoint.success_criterion,
            },
            "n_visits": len(protocol.visits),
            "n_secondary_endpoints": len(protocol.secondary_endpoints),
        }


# Singleton instance
_readiness_service: Optional[ReadinessService] = None


def get_readiness_service() -> ReadinessService:
    """Get singleton readiness service instance."""
    global _readiness_service
    if _readiness_service is None:
        _readiness_service = ReadinessService()
    return _readiness_service
