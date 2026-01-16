"""
Missed Visit Detector - Detects completely missed protocol visits.

Checks if patients have missed their scheduled follow-up visits entirely
based on time elapsed since surgery.

CLINICAL RATIONALE:
Per the protocol Schedule of Assessments, patients must complete follow-up
visits at specified intervals post-surgery. Missing an entire visit:
- Results in gaps in longitudinal outcome data
- May indicate patient dropout or loss to follow-up
- Affects completeness of safety monitoring
- Critical at primary endpoint (2-year) as it affects per-protocol analysis

DETECTION APPROACH:
For each patient with surgery, calculate expected visit dates based on
protocol windows. If current date exceeds the window end date and NO
assessment data exists for that visit, flag as missed visit.

This complements MissingAssessmentDetector which only catches partial visits
(where some but not all required assessments were completed).
"""
import time
from datetime import date
from typing import Dict, List, Set

from data.models.unified_schema import H34StudyData
from data.loaders.yaml_loader import ProtocolRules
from app.detectors.base_detector import (
    BaseDetector,
    Deviation,
    DeviationType,
    DeviationSeverity,
    DetectorResult,
)


class MissedVisitDetector(BaseDetector):
    """
    Detector for completely missed protocol visits.

    Identifies patients who should have completed a visit based on
    their surgery date but have no assessment data for that visit.
    """

    detector_name = "MissedVisitDetector"
    deviation_type = DeviationType.MISSED_VISIT

    # Map protocol visit IDs to follow-up names used in data
    VISIT_ID_TO_FOLLOWUP = {
        "fu_2mo": ["FU 2 Months", "2 Months"],
        "fu_6mo": ["FU 6 Months", "6 Months"],
        "fu_1yr": ["FU 1 Year", "1 Year"],
        "fu_2yr": ["FU 2 Years", "2 Years"],
    }

    def detect(self, study_data: H34StudyData) -> DetectorResult:
        """
        Detect completely missed visits across all patients.

        Args:
            study_data: Complete H34 study data

        Returns:
            DetectorResult with missed visit deviations
        """
        start_time = time.time()
        deviations: List[Deviation] = []
        patients_checked = 0
        visits_checked = 0

        # Use today's date for calculating expected visits
        today = date.today()

        # Build patient surgery date lookup
        surgery_dates: Dict[str, date] = {}
        for intraop in study_data.intraoperatives:
            if intraop.patient_id and intraop.surgery_date:
                surgery_dates[intraop.patient_id] = intraop.surgery_date

        # Build lookup of completed visits by patient (from HHS scores)
        completed_visits: Dict[str, Set[str]] = {}
        for hhs in study_data.hhs_scores:
            if not hhs.patient_id or not hhs.follow_up:
                continue
            if hhs.patient_id not in completed_visits:
                completed_visits[hhs.patient_id] = set()
            completed_visits[hhs.patient_id].add(hhs.follow_up)

        # Also check OHS scores
        for ohs in study_data.ohs_scores:
            if not ohs.patient_id or not ohs.follow_up:
                continue
            if ohs.patient_id not in completed_visits:
                completed_visits[ohs.patient_id] = set()
            completed_visits[ohs.patient_id].add(ohs.follow_up)

        # Get follow-up visit windows from protocol
        follow_up_visits = []
        for visit in self.protocol_rules.visits:
            if visit.id in self.VISIT_ID_TO_FOLLOWUP:
                follow_up_visits.append(visit)

        # Check each patient for missed visits
        for patient_id, surgery_date in surgery_dates.items():
            patients_checked += 1
            patient_completed = completed_visits.get(patient_id, set())

            for visit in follow_up_visits:
                visits_checked += 1

                # Calculate the window end date for this visit
                _, max_day = visit.get_window_range()
                window_end_date = date.fromordinal(
                    surgery_date.toordinal() + max_day
                )

                # If we're past the window end and no data exists, it's missed
                if today > window_end_date:
                    # Check if patient has ANY data for this visit
                    expected_followups = self.VISIT_ID_TO_FOLLOWUP.get(visit.id, [])
                    has_visit_data = any(
                        fu in patient_completed for fu in expected_followups
                    )

                    if not has_visit_data:
                        # Calculate how overdue the visit is
                        days_overdue = (today - window_end_date).days

                        # Classify severity
                        severity = self._classify_missed_severity(
                            visit.is_primary_endpoint,
                            days_overdue
                        )

                        deviations.append(Deviation(
                            patient_id=patient_id,
                            deviation_type=DeviationType.MISSED_VISIT,
                            severity=severity,
                            description=f"Missed {visit.name} visit - {days_overdue} days past window",
                            visit=visit.name,
                            visit_id=visit.id,
                            expected_day=visit.target_day,
                            window=f"Day {visit.target_day - visit.window_minus} to Day {max_day}",
                            deviation_days=days_overdue,
                            surgery_date=surgery_date,
                            action=self.get_action(severity),
                            requires_explanation=True,
                            affects_evaluability=visit.is_primary_endpoint,
                            # Provenance
                            data_source="study_scores + study_surgeries tables",
                            data_fields_used=["surgery_date", "follow_up", "patient_id"],
                            protocol_reference=f"Protocol H-34 v2.0 - Schedule of Assessments ({visit.name})",
                            protocol_rule_id=f"{visit.id}_required",
                            regulatory_reference="ICH GCP E6(R2) 6.4.9 - Visit completion; FDA 21 CFR 312.62",
                        ))

        return DetectorResult(
            detector_name=self.detector_name,
            deviation_type=self.deviation_type,
            deviations=deviations,
            patients_checked=patients_checked,
            visits_checked=visits_checked,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    def _classify_missed_severity(
        self, is_primary_endpoint: bool, days_overdue: int
    ) -> DeviationSeverity:
        """
        Classify severity of missed visit.

        Args:
            is_primary_endpoint: Whether this is the primary endpoint visit
            days_overdue: Days past the visit window

        Returns:
            DeviationSeverity classification
        """
        # Primary endpoint missed = always critical (affects per-protocol analysis)
        if is_primary_endpoint:
            return DeviationSeverity.CRITICAL

        # Other visits: severity based on how overdue
        if days_overdue > 180:  # > 6 months overdue
            return DeviationSeverity.CRITICAL
        elif days_overdue > 90:  # > 3 months overdue
            return DeviationSeverity.MAJOR
        else:
            return DeviationSeverity.MAJOR  # Any missed visit is at least major
