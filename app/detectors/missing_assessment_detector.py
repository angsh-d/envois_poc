"""
Missing Assessment Detector - Detects missing required assessments.

Checks if required assessments (HHS, OHS, X-rays) were completed at each visit.

CLINICAL RATIONALE:
Per the Schedule of Assessments (SoA) in the protocol, specific assessments
must be completed at each visit. Missing assessments can:
- Affect primary endpoint analysis (missing HHS at 2-year visit)
- Compromise safety monitoring (missing radiology may miss complications)
- Create incomplete patient records for regulatory submission

DETECTION APPROACH:
For each patient visit where we have SOME data, check if ALL required
assessments per protocol were completed. This detects partial visits.

NOTE: Completely missed visits (no data at all) are detected by examining
expected vs actual visit schedule - not covered by this detector.
"""
import time
from datetime import date
from typing import Dict, List, Optional, Set

from data.models.unified_schema import H34StudyData
from data.loaders.yaml_loader import ProtocolRules
from app.detectors.base_detector import (
    BaseDetector,
    Deviation,
    DeviationType,
    DeviationSeverity,
    DetectorResult,
)


class MissingAssessmentDetector(BaseDetector):
    """
    Detector for missing required assessments.

    For each visit a patient has completed, checks if all
    protocol-required assessments were performed.
    """

    detector_name = "MissingAssessmentDetector"
    deviation_type = DeviationType.MISSING_ASSESSMENT

    # Map follow-up names in data to protocol visit IDs
    FOLLOWUP_TO_VISIT_ID = {
        "Preoperative": "preoperative",
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
        Detect missing required assessments.

        Args:
            study_data: Complete H34 study data

        Returns:
            DetectorResult with missing assessment deviations
        """
        start_time = time.time()
        deviations: List[Deviation] = []
        patients_checked = 0
        visits_checked = 0

        # IMPORTANT: Determine which data types are actually available in dataset
        # Only check for assessments that exist - missing data types are NOT deviations
        has_hhs_data = len(study_data.hhs_scores) > 0
        has_ohs_data = len(study_data.ohs_scores) > 0
        has_radio_data = len(study_data.radiographic_evaluations) > 0

        # Build patient surgery date lookup
        surgery_dates: Dict[str, date] = {}
        for intraop in study_data.intraoperatives:
            if intraop.patient_id and intraop.surgery_date:
                surgery_dates[intraop.patient_id] = intraop.surgery_date

        # Build lookup of completed assessments by patient and visit
        # HHS scores
        hhs_by_patient_visit: Dict[str, Set[str]] = {}
        for hhs in study_data.hhs_scores:
            if not hhs.patient_id or not hhs.follow_up:
                continue
            key = hhs.patient_id
            if key not in hhs_by_patient_visit:
                hhs_by_patient_visit[key] = set()
            hhs_by_patient_visit[key].add(hhs.follow_up)

        # OHS scores
        ohs_by_patient_visit: Dict[str, Set[str]] = {}
        for ohs in study_data.ohs_scores:
            if not ohs.patient_id or not ohs.follow_up:
                continue
            key = ohs.patient_id
            if key not in ohs_by_patient_visit:
                ohs_by_patient_visit[key] = set()
            ohs_by_patient_visit[key].add(ohs.follow_up)

        # Radiographic evaluations
        radio_by_patient_visit: Dict[str, Set[str]] = {}
        for radio in study_data.radiographic_evaluations:
            if not radio.patient_id or not radio.follow_up:
                continue
            key = radio.patient_id
            if key not in radio_by_patient_visit:
                radio_by_patient_visit[key] = set()
            radio_by_patient_visit[key].add(radio.follow_up)

        # For each patient with surgery, check required assessments at each visit
        for patient_id, surgery_date in surgery_dates.items():
            patients_checked += 1

            # Get all follow-up visits this patient should have by now
            # (based on HHS score visits as proxy for scheduled visits)
            patient_hhs_visits = hhs_by_patient_visit.get(patient_id, set())
            patient_ohs_visits = ohs_by_patient_visit.get(patient_id, set())
            patient_radio_visits = radio_by_patient_visit.get(patient_id, set())

            # All visits the patient has data for
            all_visits = patient_hhs_visits | patient_ohs_visits | patient_radio_visits

            for visit_name in all_visits:
                visits_checked += 1
                visit_id = self.FOLLOWUP_TO_VISIT_ID.get(visit_name)
                if not visit_id:
                    continue

                # Get required assessments for this visit from protocol
                visit_window = self.protocol_rules.get_visit(visit_id)
                if not visit_window:
                    continue

                required = set(visit_window.required_assessments)
                completed = []
                missing = []

                # Check HHS - ONLY if HHS data exists in dataset
                if "hhs" in required and has_hhs_data:
                    if visit_name in patient_hhs_visits:
                        completed.append("hhs")
                    else:
                        missing.append("hhs")

                # Check OHS - ONLY if OHS data exists in dataset
                if "ohs" in required and has_ohs_data:
                    if visit_name in patient_ohs_visits:
                        completed.append("ohs")
                    else:
                        missing.append("ohs")

                # Check radiology - ONLY if radiology data exists in dataset
                # NOTE: If no radiology data in entire dataset, this is a data
                # availability issue, NOT a protocol deviation
                if ("radiology" in required or "radiology_baseline" in required) and has_radio_data:
                    radio_label = self._get_radio_label(visit_name)
                    if radio_label and radio_label in patient_radio_visits:
                        completed.append("radiology")
                    else:
                        missing.append("radiology")

                # Create deviation for each missing assessment
                for assessment in missing:
                    severity = self._classify_missing_severity(
                        assessment, visit_window.is_primary_endpoint
                    )

                    # Determine data source based on assessment type
                    data_source_map = {
                        "hhs": "H-34 Excel: HHS Scores sheet",
                        "ohs": "H-34 Excel: OHS Scores sheet",
                        "radiology": "H-34 Excel: Radiographic Evaluations sheet",
                    }

                    deviations.append(Deviation(
                        patient_id=patient_id,
                        deviation_type=DeviationType.MISSING_ASSESSMENT,
                        severity=severity,
                        description=f"Missing {assessment.upper()} assessment at {visit_name}",
                        visit=visit_name,
                        visit_id=visit_id,
                        missing_assessment=assessment,
                        required_assessments=list(required),
                        completed_assessments=completed,
                        action=self.get_action(severity),
                        requires_explanation=self.requires_explanation(severity),
                        affects_evaluability=self.affects_evaluability(severity),
                        # Provenance
                        data_source=data_source_map.get(assessment, "H-34 Excel"),
                        data_fields_used=["patient_id", "follow_up", f"{assessment}_score"],
                        protocol_reference=f"Schedule of Assessments - {visit_name}",
                        protocol_rule_id=f"{visit_id}_required_assessments",
                        regulatory_reference="ICH GCP E6(R2) 6.4 - Case Report Form completion",
                    ))

        return DetectorResult(
            detector_name=self.detector_name,
            deviation_type=self.deviation_type,
            deviations=deviations,
            patients_checked=patients_checked,
            visits_checked=visits_checked,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    def _get_radio_label(self, visit_name: str) -> Optional[str]:
        """Map visit name to radiographic evaluation follow-up label."""
        mapping = {
            "Preoperative": "Preoperative",
            "Discharge": "Discharge",
            "FU 2 Months": "2 Months",
            "2 Months": "2 Months",
            "FU 6 Months": "6 Months",
            "6 Months": "6 Months",
            "FU 1 Year": "1 Year",
            "1 Year": "1 Year",
            "FU 2 Years": "2 Years",
            "2 Years": "2 Years",
        }
        return mapping.get(visit_name)

    def _classify_missing_severity(
        self, assessment: str, is_primary_endpoint: bool
    ) -> DeviationSeverity:
        """Classify severity of missing assessment."""
        # Primary endpoint assessments at primary endpoint visit are critical
        if is_primary_endpoint and assessment in ("hhs", "ohs"):
            return DeviationSeverity.CRITICAL

        # Missing HHS/OHS at any visit is major
        if assessment in ("hhs", "ohs"):
            return DeviationSeverity.MAJOR

        # Missing radiology is minor unless at primary endpoint
        if assessment == "radiology":
            if is_primary_endpoint:
                return DeviationSeverity.MAJOR
            return DeviationSeverity.MINOR

        return DeviationSeverity.MINOR
