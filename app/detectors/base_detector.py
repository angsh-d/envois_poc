"""
Base Detector class for protocol deviation detection.

Provides common interface, types, and utilities for all deviation detectors.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from data.models.unified_schema import H34StudyData
from data.loaders.yaml_loader import ProtocolRules


class DeviationType(str, Enum):
    """Types of protocol deviations detected by the system."""
    VISIT_TIMING = "visit_timing"
    MISSING_ASSESSMENT = "missing_assessment"
    MISSED_VISIT = "missed_visit"
    IE_VIOLATION = "ie_violation"
    CONSENT_TIMING = "consent_timing"
    AE_REPORTING = "ae_reporting"
    OUTCOME_INCOMPLETE = "outcome_incomplete"
    RADIOGRAPHIC_GAP = "radiographic_gap"
    BATCH_EXPIRY = "batch_expiry"
    WITHDRAWAL_DOCUMENTATION = "withdrawal_documentation"


class DeviationSeverity(str, Enum):
    """Severity classification per protocol rules."""
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


@dataclass
class Deviation:
    """
    A single detected protocol deviation with full provenance tracking.

    Provenance fields enable traceability from detection back to:
    - Source data (which Excel sheet/table the data came from)
    - Protocol reference (which section of protocol defines the rule)
    - Regulatory reference (ICH GCP, FDA CFR citations)
    """
    patient_id: str
    deviation_type: DeviationType
    severity: DeviationSeverity
    description: str

    # === PROVENANCE FIELDS ===
    # Data source provenance
    data_source: Optional[str] = None  # e.g., "H-34 Excel: Patients sheet"
    data_fields_used: Optional[List[str]] = None  # Fields used for detection

    # Protocol provenance
    protocol_reference: Optional[str] = None  # e.g., "Schedule of Assessments, Section 7.1"
    protocol_rule_id: Optional[str] = None  # e.g., "fu_2yr_window"

    # Regulatory provenance
    regulatory_reference: Optional[str] = None  # e.g., "ICH GCP E6(R2) 4.8.10"

    # Detection metadata
    detected_at: Optional[str] = None  # ISO timestamp of detection

    # Visit/context info
    visit: Optional[str] = None
    visit_id: Optional[str] = None

    # Timing details (for visit timing deviations)
    expected_day: Optional[int] = None
    actual_day: Optional[int] = None
    deviation_days: Optional[int] = None
    window: Optional[str] = None

    # Assessment details (for missing assessment deviations)
    missing_assessment: Optional[str] = None
    required_assessments: Optional[List[str]] = None
    completed_assessments: Optional[List[str]] = None

    # IE criteria details
    violated_criterion: Optional[str] = None
    criterion_type: Optional[str] = None  # inclusion or exclusion
    actual_value: Optional[Any] = None
    required_value: Optional[str] = None

    # AE reporting details
    ae_id: Optional[str] = None
    onset_date: Optional[date] = None
    report_date: Optional[date] = None
    days_delayed: Optional[int] = None
    is_sae: Optional[bool] = None

    # Consent/timing details
    consent_date: Optional[date] = None
    surgery_date: Optional[date] = None

    # Batch/device details
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None

    # Classification metadata
    action: str = "Document deviation"
    requires_explanation: bool = False
    affects_evaluability: bool = False
    requires_pi_notification: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "patient_id": self.patient_id,
            "deviation_type": self.deviation_type.value,
            "classification": self.severity.value,
            "severity": self.severity.value,
            "description": self.description,
            "action": self.action,
            "requires_explanation": self.requires_explanation,
            "affects_evaluability": self.affects_evaluability,
        }

        # === PROVENANCE FIELDS ===
        provenance = {}
        if self.data_source:
            provenance["data_source"] = self.data_source
        if self.data_fields_used:
            provenance["data_fields_used"] = self.data_fields_used
        if self.protocol_reference:
            provenance["protocol_reference"] = self.protocol_reference
        if self.protocol_rule_id:
            provenance["protocol_rule_id"] = self.protocol_rule_id
        if self.regulatory_reference:
            provenance["regulatory_reference"] = self.regulatory_reference
        if self.detected_at:
            provenance["detected_at"] = self.detected_at
        if provenance:
            result["provenance"] = provenance

        # Add optional fields if present
        if self.visit:
            result["visit"] = self.visit
        if self.visit_id:
            result["visit_id"] = self.visit_id
        if self.expected_day is not None:
            result["expected_day"] = self.expected_day
        if self.actual_day is not None:
            result["actual_day"] = self.actual_day
        if self.deviation_days is not None:
            result["deviation_days"] = self.deviation_days
        if self.window:
            result["window"] = self.window
        if self.missing_assessment:
            result["missing_assessment"] = self.missing_assessment
        if self.violated_criterion:
            result["violated_criterion"] = self.violated_criterion
            result["criterion_type"] = self.criterion_type
        if self.actual_value is not None:
            result["actual_value"] = self.actual_value
        if self.required_value:
            result["required_value"] = self.required_value
        if self.ae_id:
            result["ae_id"] = self.ae_id
        if self.onset_date:
            result["onset_date"] = self.onset_date.isoformat()
        if self.report_date:
            result["report_date"] = self.report_date.isoformat()
        if self.days_delayed is not None:
            result["days_delayed"] = self.days_delayed
        if self.is_sae is not None:
            result["is_sae"] = self.is_sae
        if self.consent_date:
            result["consent_date"] = self.consent_date.isoformat()
        if self.surgery_date:
            result["surgery_date"] = self.surgery_date.isoformat()

        return result


@dataclass
class DetectorResult:
    """Result from a deviation detector."""
    detector_name: str
    deviation_type: DeviationType
    deviations: List[Deviation] = field(default_factory=list)
    patients_checked: int = 0
    visits_checked: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None

    @property
    def n_deviations(self) -> int:
        return len(self.deviations)

    @property
    def by_severity(self) -> Dict[str, int]:
        counts = {"minor": 0, "major": 0, "critical": 0}
        for dev in self.deviations:
            counts[dev.severity.value] += 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detector_name": self.detector_name,
            "deviation_type": self.deviation_type.value,
            "n_deviations": self.n_deviations,
            "by_severity": self.by_severity,
            "patients_checked": self.patients_checked,
            "visits_checked": self.visits_checked,
            "execution_time_ms": self.execution_time_ms,
            "deviations": [d.to_dict() for d in self.deviations],
        }


class BaseDetector(ABC):
    """
    Base class for all protocol deviation detectors.

    Each detector focuses on a specific type of deviation:
    - VisitTimingDetector: Visit window compliance
    - MissingAssessmentDetector: Required assessment completion
    - IEViolationDetector: Inclusion/exclusion criteria
    - ConsentTimingDetector: Consent-to-surgery timing
    - AEReportingDetector: SAE reporting timeline
    - OutcomeCompletenessDetector: HHS/OHS score completeness
    - RadiographicDetector: X-ray completion at visits
    - BatchExpiryDetector: Device batch expiry checks
    """

    detector_name: str = "BaseDetector"
    deviation_type: DeviationType = DeviationType.VISIT_TIMING

    def __init__(self, protocol_rules: ProtocolRules):
        """Initialize detector with protocol rules."""
        self.protocol_rules = protocol_rules

    @abstractmethod
    def detect(self, study_data: H34StudyData) -> DetectorResult:
        """
        Run deviation detection on study data.

        Args:
            study_data: Complete H34 study data

        Returns:
            DetectorResult with all detected deviations
        """
        pass

    def classify_severity(
        self,
        deviation_days: int = 0,
        is_primary_endpoint: bool = False,
        is_missing: bool = False,
    ) -> DeviationSeverity:
        """
        Classify deviation severity based on protocol rules.

        Args:
            deviation_days: Days outside allowed window
            is_primary_endpoint: Whether deviation affects primary endpoint
            is_missing: Whether something is completely missing

        Returns:
            DeviationSeverity classification
        """
        rules = self.protocol_rules.deviation_classification

        # Critical: Missing primary endpoint data or completely missing visit
        if is_missing and is_primary_endpoint:
            return DeviationSeverity.CRITICAL

        # Get window extensions from protocol
        minor_factor = rules.get("minor", {}).get("max_extension_factor", 1.5)
        major_factor = rules.get("major", {}).get("max_extension_factor", 2.0)

        # For timing deviations, check against extension factors
        if deviation_days > 0:
            # Need to know the original window to calculate extension
            # For now, use simple day thresholds as approximation
            if deviation_days <= 14:  # ~1.5x a 2-week window
                return DeviationSeverity.MINOR
            elif deviation_days <= 30:  # ~2x a 2-week window
                return DeviationSeverity.MAJOR
            else:
                return DeviationSeverity.CRITICAL

        # Missing non-primary assessment
        if is_missing:
            return DeviationSeverity.MAJOR

        return DeviationSeverity.MINOR

    def get_action(self, severity: DeviationSeverity) -> str:
        """Get required action for deviation severity."""
        rules = self.protocol_rules.deviation_classification
        return rules.get(severity.value, {}).get("action", "Document deviation")

    def requires_explanation(self, severity: DeviationSeverity) -> bool:
        """Check if deviation requires explanation."""
        rules = self.protocol_rules.deviation_classification
        return rules.get(severity.value, {}).get("requires_explanation", False)

    def affects_evaluability(self, severity: DeviationSeverity) -> bool:
        """Check if deviation affects patient evaluability."""
        rules = self.protocol_rules.deviation_classification
        return rules.get(severity.value, {}).get("affects_evaluability", False)
