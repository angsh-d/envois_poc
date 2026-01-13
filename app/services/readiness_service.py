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

        # Calculate overall readiness with full provenance
        is_ready, blocking_issues = self._calculate_overall_readiness(
            enrollment_status,
            compliance_status,
            safety_status,
            data_status,
            protocol_rules,
            safety_result.data if safety_result.success else {}
        )

        # Generate narrative
        synthesis_context = AgentContext(
            request_id=request_id,
            parameters={"synthesis_type": "uc1_readiness"},
            shared_data={
                "data": data_result.to_dict() if data_result.success else {},
                "compliance": compliance_result.to_dict() if compliance_result.success else {},
                "safety": safety_result.to_dict() if safety_result.success else {},
                # Pass calculated readiness for narrative generation
                "readiness_status": {
                    "is_ready": is_ready,
                    "blocking_issues": blocking_issues,
                },
            }
        )
        synthesis_result = await self._synthesis_agent.run(synthesis_context)

        # Collect sources with enhanced provenance
        sources = []

        # Add primary data source with provenance details
        sources.append({
            "type": "study_data",
            "reference": f"H-34 Study Excel Export (n={enrollment_status.get('enrolled', 0)})",
            "confidence": 1.0,
            "details": {
                "data_source": "H-34DELTARevisionstudy_export",
                "data_fields": ["patients", "hhs_scores", "adverse_events", "intraoperatives"],
                "query_types": ["summary", "safety", "deviations"],
            }
        })

        # Add protocol rules source
        sources.append({
            "type": "protocol",
            "reference": f"protocol_rules.yaml v{protocol_rules.protocol_version}",
            "confidence": 1.0,
            "details": {
                "protocol_id": protocol_rules.protocol_id,
                "sample_size_target": protocol_rules.sample_size_target,
                "primary_endpoint": protocol_rules.primary_endpoint.id,
                "regulatory_reference": "FDA 21 CFR 812, ICH GCP E6(R2)",
            }
        })

        # Add compliance calculation provenance
        sources.append({
            "type": "compliance_analysis",
            "reference": "Protocol Deviation Detection",
            "confidence": 1.0,
            "details": {
                "calculation": "Visit timing deviations from protocol windows",
                "protocol_reference": "Schedule of Assessments",
                "regulatory_reference": "ICH GCP E6(R2) - Protocol adherence",
            }
        })

        # Add safety analysis provenance
        sources.append({
            "type": "safety_analysis",
            "reference": "Safety Signal Detection",
            "confidence": 0.95,
            "details": {
                "thresholds_source": "protocol_rules.yaml safety_thresholds",
                "metrics_evaluated": ["revision_rate", "dislocation_rate", "infection_rate", "fracture_rate"],
                "regulatory_reference": "FDA 21 CFR 812.150 - Safety reporting",
            }
        })

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
        """
        Assess protocol compliance status.

        CLINICAL RATIONALE (ICH GCP E6(R2)):
        - Critical deviations affect patient evaluability per protocol
        - Major deviation threshold (>3) triggers monitoring per internal SOP
        - Compliance status determines regulatory defensibility

        Note: deviation_rate is returned as decimal (0.0-1.0) for API consistency
        with UC3 deviations endpoint. Frontend should format as percentage.
        """
        deviation_rate = data.get("deviation_rate", 0)
        by_severity = data.get("by_severity", {})

        critical_count = by_severity.get("critical", 0)
        major_count = by_severity.get("major", 0)

        # Status determination per protocol deviation_classification rules
        status = "acceptable"
        if critical_count > 0:
            # Critical deviations affect evaluability (protocol_rules.yaml)
            status = "concerning"
        elif major_count > 3:
            # Internal SOP: >3 major deviations triggers monitoring
            status = "monitoring"

        return {
            "deviation_rate": round(deviation_rate, 4),  # Decimal format for API consistency
            "by_severity": by_severity,
            "status": status,
            "is_ready": critical_count == 0,  # Per protocol: critical affects evaluability
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
        """
        Assess data completeness for primary endpoint.

        CLINICAL RATIONALE:
        - completed: Patients with 2-year HHS data (primary endpoint)
        - evaluable: enrolled - withdrawn (per protocol definition)
        - 80% threshold: Derived from protocol dropout_allowance (0.20)
          Protocol allows 20% dropout → 80% minimum completion expected
        """
        enrolled = data.get("enrolled", 0)
        completed = data.get("completed", 0)
        withdrawn = data.get("withdrawn", 0)

        evaluable = enrolled - withdrawn
        completion_rate = (completed / evaluable) * 100 if evaluable > 0 else 0

        # Threshold: 100% - dropout_allowance (20%) = 80%
        # From protocol_rules.yaml sample_size.dropout_allowance: 0.20
        # Note: Protocol allows 20% dropout, so 80% completion is minimum
        MIN_COMPLETION_THRESHOLD = 80.0  # (1.0 - 0.20) * 100

        return {
            "enrolled": enrolled,
            "completed": completed,
            "withdrawn": withdrawn,
            "evaluable": evaluable,
            "completion_rate": round(completion_rate, 1),
            "is_ready": completion_rate >= MIN_COMPLETION_THRESHOLD,
        }

    def _calculate_overall_readiness(
        self,
        enrollment: Dict,
        compliance: Dict,
        safety: Dict,
        data: Dict,
        protocol_rules: Any,
        safety_raw_data: Dict = None
    ) -> tuple:
        """
        Calculate overall readiness and identify blocking issues with full provenance.

        Each blocking issue includes:
        - calculation: How the value was derived
        - values: Actual data values used
        - threshold: The target/limit being compared
        - source: Where the data came from
        - regulatory_reference: Applicable regulatory guidance
        """
        blocking_issues = []

        if not enrollment.get("is_ready"):
            blocking_issues.append({
                "category": "enrollment",
                "issue": f"Enrollment at {enrollment['percent_complete']}% (target: 100%)",
                "provenance": {
                    "calculation": f"{enrollment['enrolled']} enrolled ÷ {enrollment['target']} target × 100 = {enrollment['percent_complete']}%",
                    "values": {
                        "enrolled_count": enrollment['enrolled'],
                        "target_enrollment": enrollment['target'],
                        "interim_target": enrollment['interim_target'],
                        "percent_complete": enrollment['percent_complete'],
                    },
                    "threshold": f"100% of target enrollment ({enrollment['target']} patients)",
                    "current_status": enrollment['status'],
                    "source": "H-34 Study Excel Export - Patients sheet",
                    "regulatory_reference": "Protocol Section 6.1 - Sample Size Justification",
                }
            })

        if not compliance.get("is_ready"):
            by_sev = compliance.get("by_severity", {})
            deviation_rate_pct = compliance['deviation_rate'] * 100  # Convert decimal to percentage for display
            blocking_issues.append({
                "category": "compliance",
                "issue": f"Critical deviations detected ({by_sev.get('critical', 0)} critical)",
                "provenance": {
                    "calculation": f"Deviation rate = {deviation_rate_pct:.1f}% of scheduled visits",
                    "values": {
                        "critical_deviations": by_sev.get("critical", 0),
                        "major_deviations": by_sev.get("major", 0),
                        "minor_deviations": by_sev.get("minor", 0),
                        "deviation_rate_percent": deviation_rate_pct,
                    },
                    "threshold": "0 critical deviations allowed (critical deviations affect patient evaluability)",
                    "classification_rules": {
                        "critical": "Missing visit OR missing primary endpoint assessment",
                        "major": "Visit >1.5x window OR missing non-critical assessment",
                        "minor": "Visit within 1.5x allowed window extension",
                    },
                    "source": "Protocol deviation detection comparing visit dates to protocol windows",
                    "regulatory_reference": "ICH GCP E6(R2) Section 4.5 - Protocol Compliance",
                }
            })

        if not safety.get("is_ready"):
            # Extract actual signal details from raw safety data
            signals_list = safety_raw_data.get("signals", []) if safety_raw_data else []
            signals_detail = []
            for sig in signals_list:
                metric = sig.get("metric", "unknown")
                rate = sig.get("rate", 0) * 100
                threshold = sig.get("threshold", 0) * 100
                count = sig.get("count", 0)
                total = sig.get("total", 0)
                signals_detail.append({
                    "metric": metric.replace("_", " ").title(),
                    "observed_rate": f"{rate:.1f}%",
                    "threshold": f"{threshold:.0f}%",
                    "calculation": f"{count} events / {total} patients = {rate:.1f}%",
                    "exceeded_by": f"+{(rate - threshold):.1f}%"
                })

            blocking_issues.append({
                "category": "safety",
                "issue": f"Safety status: {safety['overall_status']} ({safety['n_signals']} active signals)",
                "provenance": {
                    "calculation": "Compare observed rates against protocol-defined safety thresholds",
                    "values": {
                        "active_signals": safety['n_signals'],
                        "overall_status": safety['overall_status'],
                    },
                    "signals_detected": signals_detail,
                    "thresholds": {
                        "revision_rate": f"{protocol_rules.safety_thresholds.get('revision_rate_concern', 0.10)*100:.0f}%",
                        "dislocation_rate": f"{protocol_rules.safety_thresholds.get('dislocation_rate_concern', 0.08)*100:.0f}%",
                        "infection_rate": f"{protocol_rules.safety_thresholds.get('infection_rate_concern', 0.05)*100:.0f}%",
                        "fracture_rate": f"{protocol_rules.safety_thresholds.get('fracture_rate_concern', 0.08)*100:.0f}%",
                    },
                    "determination": "Status = 'concerning' when any rate exceeds protocol threshold",
                    "source": "H-34 Study Excel Export - Adverse Events sheet",
                    "regulatory_reference": "FDA 21 CFR 812.150 - Safety Reporting Requirements",
                }
            })

        if not data.get("is_ready"):
            blocking_issues.append({
                "category": "data_completeness",
                "issue": f"Completion rate: {data['completion_rate']}% (threshold: 80%)",
                "provenance": {
                    "calculation": f"{data['completed']} completed ÷ {data['evaluable']} evaluable × 100 = {data['completion_rate']}%",
                    "values": {
                        "enrolled": data['enrolled'],
                        "completed": data['completed'],
                        "withdrawn": data['withdrawn'],
                        "evaluable": data['evaluable'],
                        "completion_rate_percent": data['completion_rate'],
                    },
                    "definitions": {
                        "completed": "Patients with 2-year HHS primary endpoint data",
                        "evaluable": "Enrolled patients minus withdrawn (can contribute to analysis)",
                        "withdrawn": "Patients who discontinued study participation",
                    },
                    "threshold": "80% completion rate (derived from protocol 20% dropout allowance)",
                    "source": "H-34 Study Excel Export - HHS Scores sheet (FU 2 Years timepoint)",
                    "regulatory_reference": "Protocol Section 6.1 - Evaluable Population Definition",
                }
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
