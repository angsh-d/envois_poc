"""
Consent Timing Detector - Detects informed consent timing issues.

Checks that informed consent was obtained properly before surgery.

CLINICAL RATIONALE:
Per ICH GCP E6(R2) 4.8.10, informed consent must be obtained BEFORE any
study-specific procedures are performed. For surgical studies, this means
consent must be documented BEFORE the index surgery date.

DEVIATION CLASSIFICATION:
- CRITICAL: Consent documented AFTER surgery (potential regulatory issue)
- MAJOR: Consent on same day as surgery (may indicate inadequate time)
- MINOR: Consent >90 days before screening (may need re-consent)

NOTE: This detector ONLY flags deviations when consent_date data EXISTS.
Missing consent_date is a DATA QUALITY issue, not a protocol deviation.
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


class ConsentTimingDetector(BaseDetector):
    """
    Detector for informed consent timing violations.

    Checks:
    - Consent obtained before surgery
    - Consent obtained after screening (if applicable)

    IMPORTANT: Only flags deviations when consent_date is PRESENT in data.
    Missing consent_date indicates data unavailability, not a deviation.
    """

    detector_name = "ConsentTimingDetector"
    deviation_type = DeviationType.CONSENT_TIMING

    def detect(self, study_data: H34StudyData) -> DetectorResult:
        """
        Detect consent timing violations.

        Args:
            study_data: Complete H34 study data

        Returns:
            DetectorResult with consent violations
        """
        start_time = time.time()
        deviations: List[Deviation] = []
        patients_checked = 0
        patients_with_consent_data = 0

        # Build surgery date lookup
        surgery_dates: Dict[str, date] = {}
        for intraop in study_data.intraoperatives:
            if intraop.patient_id and intraop.surgery_date:
                surgery_dates[intraop.patient_id] = intraop.surgery_date

        # Check each patient
        for patient in study_data.patients:
            if not patient.patient_id:
                continue

            # Only check enrolled patients (status = "Enrolled")
            status = patient.status or ""
            if status.lower() != "enrolled":
                continue

            patients_checked += 1
            patient_id = patient.patient_id
            surgery_date = surgery_dates.get(patient_id)

            # CRITICAL: Only check consent timing if consent_date EXISTS
            # Missing consent_date is a data quality issue, not a deviation
            if not patient.consent_date:
                # Skip - no consent data to evaluate
                continue

            patients_with_consent_data += 1

            # Check 1: Consent after surgery (critical violation)
            if surgery_date and patient.consent_date > surgery_date:
                days_after = (patient.consent_date - surgery_date).days
                deviations.append(Deviation(
                    patient_id=patient_id,
                    deviation_type=DeviationType.CONSENT_TIMING,
                    severity=DeviationSeverity.CRITICAL,
                    description=f"Informed consent obtained {days_after} days after surgery",
                    consent_date=patient.consent_date,
                    surgery_date=surgery_date,
                    action="Critical protocol violation - patient may not be evaluable. ICH GCP 4.8.10 requires consent before study procedures.",
                    requires_explanation=True,
                    affects_evaluability=True,
                    requires_pi_notification=True,
                    # Provenance
                    data_source="H-34 Excel: Patients sheet + Intraoperatives sheet",
                    data_fields_used=["consent_date", "surgery_date"],
                    protocol_reference="Section 4.1 - Informed Consent Procedures",
                    regulatory_reference="ICH GCP E6(R2) 4.8.10 - Consent before study procedures",
                ))

            # Check 2: Consent on same day as surgery (may be rushed)
            elif surgery_date and patient.consent_date == surgery_date:
                deviations.append(Deviation(
                    patient_id=patient_id,
                    deviation_type=DeviationType.CONSENT_TIMING,
                    severity=DeviationSeverity.MAJOR,
                    description="Informed consent obtained on surgery day - verify adequate time for consideration",
                    consent_date=patient.consent_date,
                    surgery_date=surgery_date,
                    action="Document that patient had adequate time to consider participation per ICH GCP 4.8.10",
                    requires_explanation=True,
                    affects_evaluability=False,
                    # Provenance
                    data_source="H-34 Excel: Patients sheet + Intraoperatives sheet",
                    data_fields_used=["consent_date", "surgery_date"],
                    protocol_reference="Section 4.1 - Informed Consent Procedures",
                    regulatory_reference="ICH GCP E6(R2) 4.8.10 - Adequate consideration time",
                ))

            # Check 3: Consent very long before screening (may need re-consent)
            if patient.screening_date and patient.consent_date:
                if patient.consent_date < patient.screening_date:
                    days_before = (patient.screening_date - patient.consent_date).days
                    # More than 90 days before screening may require re-consent
                    if days_before > 90:
                        deviations.append(Deviation(
                            patient_id=patient_id,
                            deviation_type=DeviationType.CONSENT_TIMING,
                            severity=DeviationSeverity.MINOR,
                            description=f"Consent obtained {days_before} days before screening (>90 days)",
                            consent_date=patient.consent_date,
                            action="Verify re-consent was obtained if protocol amendments occurred",
                            requires_explanation=False,
                            affects_evaluability=False,
                            # Provenance
                            data_source="H-34 Excel: Patients sheet",
                            data_fields_used=["consent_date", "screening_date"],
                            protocol_reference="Section 4.1.2 - Re-consent Requirements",
                            regulatory_reference="ICH GCP E6(R2) 4.8.2 - Consent revisions",
                        ))

        return DetectorResult(
            detector_name=self.detector_name,
            deviation_type=self.deviation_type,
            deviations=deviations,
            patients_checked=patients_checked,
            visits_checked=patients_with_consent_data,  # Use this to show how many had consent data
            execution_time_ms=(time.time() - start_time) * 1000,
        )
