"""
UC3 Deviations Service for Clinical Intelligence Platform.

Orchestrates modular detectors for comprehensive protocol deviation detection.
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext, AgentType, get_orchestrator
from app.agents.protocol_agent import ProtocolAgent
from app.agents.data_agent import DataAgent, get_study_data
from app.agents.compliance_agent import ComplianceAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.detectors import (
    get_all_detectors,
    DeviationType,
    DeviationSeverity,
    DetectorResult,
)
from app.config import settings
from app.exceptions import StudyDataLoadError, DatabaseUnavailableError
from data.loaders.yaml_loader import get_hybrid_loader
from data.loaders.db_loader import get_db_loader

logger = logging.getLogger(__name__)


class DeviationsService:
    """
    Service for UC3: Protocol Deviation Detection.

    Orchestrates modular detectors to:
    - Load protocol rules (Document-as-Code)
    - Load study data from H-34 Excel
    - Run all deviation detectors
    - Aggregate and classify results
    - Generate narratives with recommendations
    """

    def __init__(self):
        """Initialize deviations service."""
        self._orchestrator = get_orchestrator()
        self._protocol_agent = ProtocolAgent()
        self._data_agent = DataAgent()
        self._compliance_agent = ComplianceAgent()
        self._synthesis_agent = SynthesisAgent()
        self._doc_loader = get_hybrid_loader()
        self._study_data = None

    def _get_study_data(self):
        """
        Load and cache H-34 study data from database.

        Uses the centralized get_study_data() function from data_agent
        which handles database loading and model conversion.

        Raises:
            StudyDataLoadError: If study data cannot be loaded from database
            DatabaseUnavailableError: If database is not available
        """
        if self._study_data is None:
            # Use the centralized study data loader from data_agent
            self._study_data = get_study_data()
            logger.info(f"Loaded H-34 study data: {self._study_data.total_patients} patients")

        return self._study_data

    def run_all_detectors(self) -> Dict[str, Any]:
        """
        Run all deviation detectors and aggregate results.

        Returns:
            Dict with comprehensive deviation analysis across all types
        """
        start_time = time.time()

        # Load protocol rules and study data
        protocol_rules = self._doc_loader.load_protocol_rules()
        study_data = self._get_study_data()

        if not study_data:
            return {
                "success": False,
                "error": "Could not load study data",
            }

        # Get all detectors
        detectors = get_all_detectors(protocol_rules)

        # Run each detector and collect results
        all_deviations = []
        detector_results = []
        by_type = {}
        by_severity = {"minor": 0, "major": 0, "critical": 0}
        total_execution_time = 0

        for detector in detectors:
            try:
                result = detector.detect(study_data)
                detector_results.append(result.to_dict())
                total_execution_time += result.execution_time_ms

                # Aggregate deviations
                for dev in result.deviations:
                    all_deviations.append(dev.to_dict())

                # Count by type
                type_key = result.deviation_type.value
                by_type[type_key] = by_type.get(type_key, 0) + result.n_deviations

                # Count by severity
                for sev, count in result.by_severity.items():
                    by_severity[sev] += count

            except Exception as e:
                logger.error(f"Detector {detector.detector_name} failed: {e}")
                detector_results.append({
                    "detector_name": detector.detector_name,
                    "deviation_type": detector.deviation_type.value,
                    "error": str(e),
                    "n_deviations": 0,
                })

        # Calculate total visits - use maximum visits checked across all visit-level detectors
        # This ensures the denominator captures all visits that were assessed
        total_visits = 0
        for result in detector_results:
            dev_type = result.get("deviation_type", "")
            # Only consider visit-level detectors (not patient-level like IE violations)
            if dev_type in ("visit_timing", "missing_assessment"):
                visits_checked = result.get("visits_checked", 0)
                total_visits = max(total_visits, visits_checked)

        # Calculate visits with ANY deviations (not just timing)
        # This provides a true picture of protocol compliance across all deviation types
        visits_with_deviations = set()
        patients_with_deviations = set()  # For patient-level deviations (IE, consent)

        for dev in all_deviations:
            patient_id = dev.get("patient_id", "unknown")
            dev_type = dev.get("deviation_type", "")

            # Visit-level deviations have a visit field
            visit = dev.get("visit") or dev.get("visit_id")
            if visit and visit != "unknown":
                visits_with_deviations.add((patient_id, visit))

            # Patient-level deviations (IE violations, consent timing) affect the patient overall
            if dev_type in ("ie_violation", "consent_timing"):
                patients_with_deviations.add(patient_id)

        n_visits_with_deviations = len(visits_with_deviations)
        n_patients_with_patient_level_deviations = len(patients_with_deviations)

        # Deviation rate = percentage of visits that have at least one deviation
        # Cap at 1.0 since we cannot have more than 100% deviation rate
        deviation_rate = min(1.0, n_visits_with_deviations / total_visits) if total_visits > 0 else 0

        return {
            "success": True,
            "assessment_date": datetime.utcnow().isoformat(),
            "total_deviations": len(all_deviations),
            "total_visits": total_visits,
            "visits_with_deviations": n_visits_with_deviations,
            "patients_with_patient_level_deviations": n_patients_with_patient_level_deviations,
            "compliant_visits": total_visits - n_visits_with_deviations,
            "deviation_rate": deviation_rate,
            "by_type": by_type,
            "by_severity": by_severity,
            "deviations": all_deviations,
            "detector_results": detector_results,
            "protocol_version": protocol_rules.protocol_version,
            "execution_time_ms": total_execution_time,
        }

    async def get_study_deviations(self) -> Dict[str, Any]:
        """
        Get all protocol deviations across the study.

        Uses modular detectors to comprehensively check:
        - Visit timing windows
        - Missing assessments
        - IE criteria violations
        - AE reporting delays
        - Consent timing issues

        Returns:
            Dict with deviation summary and details
        """
        # Run all detectors
        detector_results = self.run_all_detectors()

        if not detector_results.get("success"):
            return detector_results

        # Get protocol rules for context
        protocol_rules = self._doc_loader.load_protocol_rules()

        # Group deviations by visit for backward compatibility
        by_visit = {}
        for dev in detector_results.get("deviations", []):
            visit = dev.get("visit", "unknown")
            by_visit[visit] = by_visit.get(visit, 0) + 1

        # Build response compatible with existing frontend
        return {
            "success": True,
            "assessment_date": detector_results.get("assessment_date"),
            "total_visits": detector_results.get("total_visits", 0),
            "total_deviations": detector_results.get("total_deviations", 0),
            "visits_with_deviations": detector_results.get("visits_with_deviations", 0),
            "patients_with_patient_level_deviations": detector_results.get("patients_with_patient_level_deviations", 0),
            "compliant_visits": detector_results.get("compliant_visits", 0),
            "deviation_rate": detector_results.get("deviation_rate", 0),
            "by_severity": detector_results.get("by_severity", {}),
            "by_type": detector_results.get("by_type", {}),
            "by_visit": by_visit,
            "deviations": detector_results.get("deviations", []),
            "detector_results": detector_results.get("detector_results", []),
            "protocol_version": protocol_rules.protocol_version,
            "sources": [
                {"type": "protocol", "reference": "protocol_rules.yaml", "confidence": 1.0},
                {"type": "study_data", "reference": "H-34 Study Database", "confidence": 1.0},
            ],
            "execution_time_ms": detector_results.get("execution_time_ms", 0),
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
