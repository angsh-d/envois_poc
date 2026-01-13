"""
IE Violation Detector - Detects inclusion/exclusion criteria violations.

Checks patient data against protocol-defined inclusion and exclusion criteria.

CLINICAL RATIONALE:
Per ICH GCP E6(R2) 3.1.1, subjects must meet all inclusion criteria and have
no exclusion criteria to be eligible for enrollment.

H-34 DELTA Study Key IE Criteria:
- INCLUSION: Age >= 21 years at time of surgery
- EXCLUSION: Severe osteoporosis (BMD T-score < -3.5 without treatment)
- EXCLUSION: Uncontrolled metabolic bone disease

DATA LIMITATIONS:
- Osteoporosis field only contains "Yes/No" - detailed T-score not available
- Some criteria cannot be verified from available data fields
"""
import time
from datetime import date
from typing import Dict, List, Optional, Tuple

from data.models.unified_schema import H34StudyData
from data.loaders.yaml_loader import ProtocolRules
from app.detectors.base_detector import (
    BaseDetector,
    Deviation,
    DeviationType,
    DeviationSeverity,
    DetectorResult,
)


class IEViolationDetector(BaseDetector):
    """
    Detector for inclusion/exclusion criteria violations.

    Checks:
    - Age requirement (>= 21 years)
    - Severe osteoporosis status
    - BMI extremes (if relevant to protocol)
    - Other checkable criteria from patient data
    """

    detector_name = "IEViolationDetector"
    deviation_type = DeviationType.IE_VIOLATION

    # Reference year for age calculation (study enrollment period)
    REFERENCE_YEAR = 2024

    def detect(self, study_data: H34StudyData) -> DetectorResult:
        """
        Detect IE criteria violations.

        Args:
            study_data: Complete H34 study data

        Returns:
            DetectorResult with IE violations
        """
        start_time = time.time()
        deviations: List[Deviation] = []
        patients_checked = 0

        # Build preoperative lookup for osteoporosis status
        osteoporosis_status: Dict[str, str] = {}
        for preop in study_data.preoperatives:
            if preop.patient_id and preop.osteoporosis:
                osteoporosis_status[preop.patient_id] = preop.osteoporosis

        # Check each enrolled patient
        for patient in study_data.patients:
            if not patient.patient_id:
                continue

            # Only check enrolled patients (status = "Enrolled")
            status = patient.status or ""
            if status.lower() != "enrolled":
                continue

            patients_checked += 1
            patient_id = patient.patient_id

            # Check 1: Age requirement (>= 21 years)
            if patient.year_of_birth:
                age = self.REFERENCE_YEAR - patient.year_of_birth
                if age < 21:
                    deviations.append(Deviation(
                        patient_id=patient_id,
                        deviation_type=DeviationType.IE_VIOLATION,
                        severity=DeviationSeverity.CRITICAL,
                        description=f"Patient age ({age} years) below minimum requirement of 21 years",
                        violated_criterion="Age >= 21 years",
                        criterion_type="inclusion",
                        actual_value=age,
                        required_value=">= 21 years",
                        action="Review enrollment eligibility - PI notification required",
                        requires_explanation=True,
                        affects_evaluability=True,
                        requires_pi_notification=True,
                        # Provenance
                        data_source="study_patients table",
                        data_fields_used=["year_of_birth"],
                        protocol_reference="Protocol H-34 v2.0 - Inclusion Criteria",
                        protocol_rule_id="ie_age_minimum",
                        regulatory_reference="ICH GCP E6(R2) 3.1.1 - IE verification",
                    ))

            # Check 2: Severe osteoporosis (BMD T-score < -3.5 without treatment)
            # NOTE: Available data only has "Yes/No" - we cannot determine severity
            # Only flag when we have EVIDENCE of severe osteoporosis, not just "Yes"
            osteo_status = osteoporosis_status.get(patient_id, "")
            if osteo_status:
                osteo_lower = osteo_status.lower()

                # Case A: T-score data is explicitly provided (rare but possible)
                if "t-score" in osteo_lower or "t=" in osteo_lower:
                    t_score = self._extract_t_score(osteo_status)
                    if t_score is not None and t_score < -3.5:
                        deviations.append(Deviation(
                            patient_id=patient_id,
                            deviation_type=DeviationType.IE_VIOLATION,
                            severity=DeviationSeverity.CRITICAL,
                            description=f"Patient has severe osteoporosis (T-score: {t_score})",
                            violated_criterion="BMD T-score < -3.5 (severe osteoporosis without treatment)",
                            criterion_type="exclusion",
                            actual_value=t_score,
                            required_value="T-score >= -3.5",
                            action="Review enrollment eligibility - potential exclusion violation per ICH GCP 3.1.1",
                            requires_explanation=True,
                            affects_evaluability=True,
                            requires_pi_notification=True,
                            # Provenance
                            data_source="study_patients table (preoperative data)",
                            data_fields_used=["osteoporosis"],
                            protocol_reference="Protocol H-34 v2.0 - Exclusion Criteria (severe osteoporosis)",
                            protocol_rule_id="ie_osteoporosis_exclusion",
                            regulatory_reference="ICH GCP E6(R2) 3.1.1 - IE verification",
                        ))

                # Case B: Explicit "severe" designation in data
                elif "severe" in osteo_lower:
                    deviations.append(Deviation(
                        patient_id=patient_id,
                        deviation_type=DeviationType.IE_VIOLATION,
                        severity=DeviationSeverity.MAJOR,
                        description=f"Patient has severe osteoporosis: {osteo_status}",
                        violated_criterion="Severe osteoporosis without treatment",
                        criterion_type="exclusion",
                        actual_value=osteo_status,
                        required_value="No severe osteoporosis (T-score >= -3.5)",
                        action="Verify treatment status and surgical fitness",
                        requires_explanation=True,
                        affects_evaluability=True,
                        # Provenance
                        data_source="study_patients table (preoperative data)",
                        data_fields_used=["osteoporosis"],
                        protocol_reference="Protocol H-34 v2.0 - Exclusion Criteria (severe osteoporosis)",
                        protocol_rule_id="ie_osteoporosis_exclusion",
                        regulatory_reference="ICH GCP E6(R2) 3.1.1 - IE verification",
                    ))

                # NOTE: Simple "Yes" osteoporosis is NOT flagged as a deviation
                # because we cannot determine severity from "Yes/No" alone.
                # This is a data limitation, not a protocol violation.

            # Check 3: BMI extremes (protocol may have limits)
            if patient.bmi:
                # Very low BMI might indicate malnutrition/bone issues
                if patient.bmi < 15:
                    deviations.append(Deviation(
                        patient_id=patient_id,
                        deviation_type=DeviationType.IE_VIOLATION,
                        severity=DeviationSeverity.MAJOR,
                        description=f"Patient BMI ({patient.bmi:.1f}) is extremely low",
                        violated_criterion="Patient general health status",
                        criterion_type="inclusion",
                        actual_value=patient.bmi,
                        required_value="BMI within healthy range",
                        action="Review nutritional status and surgical fitness",
                        requires_explanation=True,
                        affects_evaluability=False,
                        # Provenance
                        data_source="study_patients table",
                        data_fields_used=["bmi"],
                        protocol_reference="Protocol H-34 v2.0 - General Health Status",
                        regulatory_reference="Clinical judgment - surgical fitness",
                    ))
                # Very high BMI might affect surgical outcomes
                elif patient.bmi > 50:
                    deviations.append(Deviation(
                        patient_id=patient_id,
                        deviation_type=DeviationType.IE_VIOLATION,
                        severity=DeviationSeverity.MINOR,
                        description=f"Patient BMI ({patient.bmi:.1f}) is extremely high",
                        violated_criterion="Patient surgical fitness",
                        criterion_type="general",
                        actual_value=patient.bmi,
                        required_value="BMI within operative range",
                        action="Document high BMI and surgical plan",
                        requires_explanation=False,
                        affects_evaluability=False,
                        # Provenance
                        data_source="study_patients table",
                        data_fields_used=["bmi"],
                        protocol_reference="Protocol H-34 v2.0 - Surgical Fitness",
                        regulatory_reference="Clinical judgment - surgical fitness",
                    ))

        return DetectorResult(
            detector_name=self.detector_name,
            deviation_type=self.deviation_type,
            deviations=deviations,
            patients_checked=patients_checked,
            visits_checked=0,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    def _extract_t_score(self, text: str) -> Optional[float]:
        """Try to extract T-score from osteoporosis description."""
        import re

        # Look for patterns like "T-score: -3.5" or "T=-3.5"
        patterns = [
            r"[Tt]-?score[:\s]*(-?\d+\.?\d*)",
            r"[Tt]\s*=\s*(-?\d+\.?\d*)",
            r"(-\d+\.?\d*)\s*[Tt]-?score",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None
