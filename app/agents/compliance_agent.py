"""
Compliance Agent for Clinical Intelligence Platform.

Responsible for detecting and classifying protocol deviations.
"""
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from app.agents.protocol_agent import ProtocolAgent
from app.agents.data_agent import DataAgent

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseAgent):
    """
    Agent for protocol compliance checking and deviation detection.

    Capabilities:
    - Detect visit window deviations
    - Classify deviations by severity (minor/major/critical)
    - Identify missing assessments
    - Generate deviation narratives with recommendations
    """

    agent_type = AgentType.COMPLIANCE

    def __init__(self, **kwargs):
        """Initialize compliance agent."""
        super().__init__(**kwargs)
        self._protocol_agent = ProtocolAgent()
        self._data_agent = DataAgent()

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute compliance checking.

        Args:
            context: Execution context with patient/visit info

        Returns:
            AgentResult with deviation analysis
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        query_type = context.parameters.get("query_type", "patient")

        if query_type == "patient":
            patient_id = context.patient_id
            if not patient_id:
                result.success = False
                result.error = "patient_id required for patient compliance check"
                return result
            result.data = await self._check_patient_compliance(patient_id, context)

        elif query_type == "visit":
            result.data = await self._check_visit_compliance(context)

        elif query_type == "study":
            result.data = await self._check_study_compliance(context)

        else:
            result.success = False
            result.error = f"Unknown query_type: {query_type}"
            return result

        # Add sources
        result.add_source(
            SourceType.PROTOCOL,
            "protocol_rules.yaml",
            confidence=1.0
        )
        result.add_source(
            SourceType.STUDY_DATA,
            "H-34 Study Database",
            confidence=1.0
        )

        # Generate narrative if deviations found
        if result.data.get("deviations"):
            result.narrative = await self._generate_deviation_narrative(result.data)

        return result

    async def _check_patient_compliance(
        self,
        patient_id: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Check compliance for a specific patient."""
        # Get patient data
        data_context = AgentContext(
            request_id=context.request_id,
            patient_id=patient_id,
            parameters={"query_type": "patient"}
        )
        data_result = await self._data_agent.run(data_context)

        if not data_result.success:
            return {"error": data_result.error}

        patient_data = data_result.data
        visits = patient_data.get("visits", [])

        deviations = []
        visit_status = []

        for visit in visits:
            visit_id = visit.get("visit_id")
            actual_day = visit.get("actual_day")

            if visit_id and actual_day is not None:
                # Validate timing
                timing = self._protocol_agent.validate_visit_timing(visit_id, actual_day)

                if not timing.get("is_within_window"):
                    # Classify deviation
                    classification = self._protocol_agent.classify_deviation(
                        visit_id,
                        timing.get("deviation_days", 0)
                    )

                    deviation = {
                        "patient_id": patient_id,
                        "visit_id": visit_id,
                        "visit_name": timing.get("visit_name"),
                        "actual_day": actual_day,
                        "target_day": timing.get("target_day"),
                        "allowed_range": timing.get("allowed_range"),
                        "deviation_days": timing.get("deviation_days"),
                        "classification": classification.get("classification"),
                        "action": classification.get("action"),
                        "requires_explanation": classification.get("requires_explanation"),
                        "affects_evaluability": classification.get("affects_evaluability"),
                    }
                    deviations.append(deviation)

                visit_status.append({
                    "visit_id": visit_id,
                    "status": "deviation" if not timing.get("is_within_window") else "compliant",
                    "actual_day": actual_day,
                    "target_day": timing.get("target_day"),
                })

        # Check for missing assessments
        missing_assessments = self._check_missing_assessments(visits)

        return {
            "patient_id": patient_id,
            "n_visits": len(visits),
            "n_deviations": len(deviations),
            "deviations": deviations,
            "visit_status": visit_status,
            "missing_assessments": missing_assessments,
            "compliance_rate": self._calculate_compliance_rate(visits, deviations),
            "deviation_summary": self._summarize_deviations(deviations),
        }

    async def _check_visit_compliance(
        self,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Check compliance for a specific visit."""
        visit_id = context.visit_id
        actual_day = context.parameters.get("actual_day")
        patient_id = context.patient_id

        if not visit_id:
            return {"error": "visit_id required"}
        if actual_day is None:
            return {"error": "actual_day parameter required"}

        # Validate timing
        timing = self._protocol_agent.validate_visit_timing(visit_id, actual_day)

        result = {
            "patient_id": patient_id,
            "visit_id": visit_id,
            "visit_name": timing.get("visit_name"),
            "actual_day": actual_day,
            "target_day": timing.get("target_day"),
            "allowed_range": timing.get("allowed_range"),
            "is_compliant": timing.get("is_within_window"),
        }

        if not timing.get("is_within_window"):
            classification = self._protocol_agent.classify_deviation(
                visit_id,
                timing.get("deviation_days", 0)
            )
            result["deviation"] = {
                "deviation_days": timing.get("deviation_days"),
                "classification": classification.get("classification"),
                "action": classification.get("action"),
                "requires_explanation": classification.get("requires_explanation"),
                "affects_evaluability": classification.get("affects_evaluability"),
            }

        return result

    async def _check_study_compliance(
        self,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Check compliance across entire study."""
        # Get deviation data
        data_context = AgentContext(
            request_id=context.request_id,
            parameters={"query_type": "deviations"}
        )
        data_result = await self._data_agent.run(data_context)

        if not data_result.success:
            return {"error": data_result.error}

        deviation_data = data_result.data

        return {
            "total_visits": deviation_data.get("total_visits", 0),
            "n_deviations": len(deviation_data.get("deviations", [])),
            "by_severity": deviation_data.get("by_severity", {}),
            "deviation_rate": self._calc_rate(
                len(deviation_data.get("deviations", [])),
                deviation_data.get("total_visits", 0)
            ),
            "deviations_by_visit": self._group_by_visit(deviation_data.get("deviations", [])),
        }

    def _check_missing_assessments(self, visits: List[Dict]) -> List[Dict]:
        """Check for missing required assessments."""
        missing = []
        visit_ids = self._protocol_agent.get_all_visit_ids()

        for visit_id in visit_ids:
            window = self._protocol_agent.get_visit_window(visit_id)
            if not window:
                continue

            # Find this visit in patient data
            visit_data = next(
                (v for v in visits if v.get("visit_id") == visit_id),
                None
            )

            if not visit_data:
                # Visit not yet completed - check if it's due
                continue

            # Check for missing assessments
            completed = visit_data.get("completed_assessments", [])
            required = window.required_assessments

            for assessment in required:
                if assessment not in completed:
                    missing.append({
                        "visit_id": visit_id,
                        "assessment": assessment,
                        "is_primary_endpoint": window.is_primary_endpoint,
                    })

        return missing

    def _calculate_compliance_rate(
        self,
        visits: List[Dict],
        deviations: List[Dict]
    ) -> float:
        """Calculate compliance rate."""
        if not visits:
            return 1.0
        compliant = len(visits) - len(deviations)
        return round(compliant / len(visits), 3)

    def _summarize_deviations(self, deviations: List[Dict]) -> Dict[str, Any]:
        """Summarize deviations by classification."""
        summary = {
            "minor": 0,
            "major": 0,
            "critical": 0,
            "affects_evaluability": 0,
        }

        for dev in deviations:
            classification = dev.get("classification", "minor")
            if classification in summary:
                summary[classification] += 1
            if dev.get("affects_evaluability"):
                summary["affects_evaluability"] += 1

        return summary

    def _calc_rate(self, numerator: int, denominator: int) -> float:
        """Calculate rate with zero handling."""
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)

    def _group_by_visit(self, deviations: List[Dict]) -> Dict[str, int]:
        """Group deviations by visit type."""
        by_visit = {}
        for dev in deviations:
            visit_id = dev.get("visit_id", "unknown")
            by_visit[visit_id] = by_visit.get(visit_id, 0) + 1
        return by_visit

    async def _generate_deviation_narrative(
        self,
        compliance_data: Dict[str, Any]
    ) -> str:
        """Generate narrative for deviation findings."""
        deviations = compliance_data.get("deviations", [])
        summary = compliance_data.get("deviation_summary", {})

        if not deviations:
            return "No protocol deviations detected."

        prompt = self.load_prompt("deviation_narrative", {
            "n_deviations": len(deviations),
            "minor_count": summary.get("minor", 0),
            "major_count": summary.get("major", 0),
            "critical_count": summary.get("critical", 0),
            "deviations": str(deviations[:5]),  # Limit for context
        })

        narrative = await self.call_llm(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
        )
        return narrative.strip()
