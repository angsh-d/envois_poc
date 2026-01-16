"""
Protocol Deviation Detectors.

Modular detector pattern for comprehensive deviation detection.
Each detector focuses on a specific category of protocol deviations.
"""
from app.detectors.base_detector import (
    BaseDetector,
    Deviation,
    DeviationType,
    DeviationSeverity,
    DetectorResult,
)
from app.detectors.visit_timing_detector import VisitTimingDetector
from app.detectors.missing_assessment_detector import MissingAssessmentDetector
from app.detectors.missed_visit_detector import MissedVisitDetector
from app.detectors.ie_violation_detector import IEViolationDetector
from app.detectors.ae_reporting_detector import AEReportingDetector
from app.detectors.consent_timing_detector import ConsentTimingDetector

__all__ = [
    # Base types
    "BaseDetector",
    "Deviation",
    "DeviationType",
    "DeviationSeverity",
    "DetectorResult",
    # Detectors
    "VisitTimingDetector",
    "MissingAssessmentDetector",
    "MissedVisitDetector",
    "IEViolationDetector",
    "AEReportingDetector",
    "ConsentTimingDetector",
    # Registry
    "get_all_detectors",
]


def get_all_detectors(protocol_rules) -> list:
    """
    Get all registered deviation detectors.

    Args:
        protocol_rules: ProtocolRules instance

    Returns:
        List of initialized detector instances
    """
    return [
        VisitTimingDetector(protocol_rules),
        MissingAssessmentDetector(protocol_rules),
        MissedVisitDetector(protocol_rules),
        IEViolationDetector(protocol_rules),
        AEReportingDetector(protocol_rules),
        ConsentTimingDetector(protocol_rules),
    ]
