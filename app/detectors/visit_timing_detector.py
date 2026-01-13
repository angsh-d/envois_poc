"""
Visit Timing Detector - Detects visit window deviations.

Checks if patient visits occurred within protocol-defined windows.

CLINICAL RATIONALE:
Per ICH GCP E6(R2), visits must occur within protocol-defined windows to ensure
data comparability and endpoint validity. Deviation from windows may affect:
- Data integrity (measurements not comparable across patients)
- Endpoint validity (primary endpoint measured at wrong timepoint)
- Regulatory compliance (visit schedule is part of approved protocol)

DEVIATION CLASSIFICATION:
- MINOR: Visit <14 days outside window, not at primary endpoint
- MAJOR: Visit >=14 days outside window OR at non-primary endpoint visit
- CRITICAL: Primary endpoint visit outside window (affects evaluability)
"""
import time
from datetime import date
from typing import Dict, List, Optional

from data.models.unified_schema import H34StudyData
from data.loaders.yaml_loader import ProtocolRules
from app.detectors.base_detector import (
    BaseDetector,
    Deviation,
    DeviationType,
    DeviationSeverity,
    DetectorResult,
)


class VisitTimingDetector(BaseDetector):
    """
    Detector for visit timing deviations.

    Compares actual visit dates against protocol-defined windows
    to identify early or late visits.
    """

    detector_name = "VisitTimingDetector"
    deviation_type = DeviationType.VISIT_TIMING

    # Map follow-up names in data to protocol visit IDs
    FOLLOWUP_TO_VISIT_ID = {
        "Discharge": "discharge",
        "FU 2 Months": "fu_2mo",
        "2 Months": "fu_2mo",
        "FU 6 Months": "fu_6mo",
        "6 Months": "fu_6mo",
        "FU 1 Year": "fu_1yr",
        "1 Year": "fu_1yr",
        "FU 2 Years": "fu_2yr",
        "2 Years": "fu_2yr",
    }

    def detect(self, study_data: H34StudyData) -> DetectorResult:
        """
        Detect visit timing deviations across all patients.

        Args:
            study_data: Complete H34 study data

        Returns:
            DetectorResult with timing deviations
        """
        start_time = time.time()
        deviations: List[Deviation] = []
        patients_checked = 0
        visits_checked = 0

        # Build patient surgery date lookup
        surgery_dates: Dict[str, date] = {}
        for intraop in study_data.intraoperatives:
            if intraop.patient_id and intraop.surgery_date:
                surgery_dates[intraop.patient_id] = intraop.surgery_date

        # Check HHS scores for visit timing
        for hhs in study_data.hhs_scores:
            if not hhs.patient_id or not hhs.follow_up or not hhs.follow_up_date:
                continue

            surgery_date = surgery_dates.get(hhs.patient_id)
            if not surgery_date:
                continue

            visit_id = self.FOLLOWUP_TO_VISIT_ID.get(hhs.follow_up)
            if not visit_id:
                continue

            visits_checked += 1
            actual_day = (hhs.follow_up_date - surgery_date).days

            # Get protocol window for this visit
            visit_window = self.protocol_rules.get_visit(visit_id)
            if not visit_window:
                continue

            # Check if within window
            min_day, max_day = visit_window.get_window_range()
            if not (min_day <= actual_day <= max_day):
                # Calculate deviation
                if actual_day < min_day:
                    deviation_days = min_day - actual_day
                else:
                    deviation_days = actual_day - max_day

                # Classify severity
                severity = self.classify_severity(
                    deviation_days=deviation_days,
                    is_primary_endpoint=visit_window.is_primary_endpoint,
                )

                deviations.append(Deviation(
                    patient_id=hhs.patient_id,
                    deviation_type=DeviationType.VISIT_TIMING,
                    severity=severity,
                    description=f"Visit {hhs.follow_up} occurred {deviation_days} days outside window",
                    visit=hhs.follow_up,
                    visit_id=visit_id,
                    expected_day=visit_window.target_day,
                    actual_day=actual_day,
                    deviation_days=deviation_days,
                    window=f"Day {min_day} to Day {max_day}",
                    action=self.get_action(severity),
                    requires_explanation=self.requires_explanation(severity),
                    affects_evaluability=self.affects_evaluability(severity),
                    # Provenance
                    data_source="H-34 Excel: HHS Scores sheet + Intraoperatives sheet",
                    data_fields_used=["follow_up_date", "surgery_date"],
                    protocol_reference=f"Schedule of Assessments - {hhs.follow_up} window",
                    protocol_rule_id=f"{visit_id}_window",
                    regulatory_reference="ICH GCP E6(R2) - Protocol adherence",
                ))

        # Track unique patients
        unique_patients = set(surgery_dates.keys())
        patients_checked = len(unique_patients)

        return DetectorResult(
            detector_name=self.detector_name,
            deviation_type=self.deviation_type,
            deviations=deviations,
            patients_checked=patients_checked,
            visits_checked=visits_checked,
            execution_time_ms=(time.time() - start_time) * 1000,
        )
