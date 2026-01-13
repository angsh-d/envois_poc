"""
AE Reporting Detector - Detects adverse event reporting delays.

Checks SAE reporting timeline against protocol-required 24-hour window.

REGULATORY REQUIREMENTS:
- FDA 21 CFR 312.32: SAEs must be reported within 24 hours of awareness
- ICH E2A: Initial reports within 24 hours for fatal/life-threatening SAEs
- ICH GCP 4.11: Investigators must report all SAEs immediately to sponsor

DEVIATION CLASSIFICATION:
- MINOR: SAE reported 1-2 days late (minor administrative delay)
- MAJOR: SAE reported 3-7 days late (significant compliance concern)
- CRITICAL: SAE reported >7 days late (potential regulatory violation)
"""
import time
from datetime import date, timedelta
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


class AEReportingDetector(BaseDetector):
    """
    Detector for adverse event reporting timeline violations.

    Protocol requires SAEs to be reported within 24 hours (1 day) of onset.
    Also checks for general AE reporting delays.
    """

    detector_name = "AEReportingDetector"
    deviation_type = DeviationType.AE_REPORTING

    # Default SAE reporting window (can be overridden by protocol)
    DEFAULT_SAE_WINDOW_DAYS = 1  # 24 hours

    def detect(self, study_data: H34StudyData) -> DetectorResult:
        """
        Detect AE reporting timeline violations.

        Args:
            study_data: Complete H34 study data

        Returns:
            DetectorResult with reporting violations
        """
        start_time = time.time()
        deviations: List[Deviation] = []
        patients_checked = set()
        aes_checked = 0

        # Get SAE reporting window from protocol
        ae_rules = getattr(self.protocol_rules, 'adverse_events', None)
        if ae_rules and isinstance(ae_rules, dict):
            sae_window_days = ae_rules.get('sae_reporting_window_days', self.DEFAULT_SAE_WINDOW_DAYS)
        else:
            sae_window_days = self.DEFAULT_SAE_WINDOW_DAYS

        for ae in study_data.adverse_events:
            if not ae.patient_id or not ae.onset_date:
                continue

            patients_checked.add(ae.patient_id)
            aes_checked += 1

            # Determine if this is an SAE
            is_sae = ae.is_sae and ae.is_sae.lower() in ("yes", "true", "1")

            # Get report date (use initial_report_date or report_date)
            report_date = ae.initial_report_date or ae.report_date
            if not report_date:
                # Missing report date is itself a deviation for SAEs
                if is_sae:
                    deviations.append(Deviation(
                        patient_id=ae.patient_id,
                        deviation_type=DeviationType.AE_REPORTING,
                        severity=DeviationSeverity.CRITICAL,
                        description=f"SAE '{ae.ae_title or ae.ae_id}' missing report date",
                        ae_id=ae.ae_id,
                        is_sae=is_sae,
                        onset_date=ae.onset_date,
                        action="Complete SAE reporting documentation immediately",
                        requires_explanation=True,
                        affects_evaluability=False,
                        requires_pi_notification=True,
                        # Provenance
                        data_source="H-34 Excel: Adverse Events sheet",
                        data_fields_used=["ae_id", "is_sae", "onset_date", "report_date"],
                        protocol_reference="Section 8.3 - SAE Reporting Requirements",
                        regulatory_reference="FDA 21 CFR 312.32; ICH E2A - SAE within 24 hours",
                    ))
                continue

            # Calculate reporting delay
            days_to_report = (report_date - ae.onset_date).days

            # Check SAE reporting window
            if is_sae:
                if days_to_report > sae_window_days:
                    days_delayed = days_to_report - sae_window_days

                    # Classify severity based on delay
                    if days_delayed <= 2:
                        severity = DeviationSeverity.MINOR
                    elif days_delayed <= 7:
                        severity = DeviationSeverity.MAJOR
                    else:
                        severity = DeviationSeverity.CRITICAL

                    deviations.append(Deviation(
                        patient_id=ae.patient_id,
                        deviation_type=DeviationType.AE_REPORTING,
                        severity=severity,
                        description=f"SAE '{ae.ae_title or ae.ae_id}' reported {days_delayed} days late",
                        ae_id=ae.ae_id,
                        is_sae=True,
                        onset_date=ae.onset_date,
                        report_date=report_date,
                        days_delayed=days_delayed,
                        action=self._get_sae_action(days_delayed),
                        requires_explanation=days_delayed > 2,
                        affects_evaluability=False,
                        requires_pi_notification=days_delayed > 7,
                        # Provenance
                        data_source="H-34 Excel: Adverse Events sheet",
                        data_fields_used=["ae_id", "is_sae", "onset_date", "initial_report_date"],
                        protocol_reference="Section 8.3 - SAE Reporting Window (24 hours)",
                        protocol_rule_id="sae_reporting_window_days",
                        regulatory_reference="FDA 21 CFR 312.32; ICH E2A; ICH GCP 4.11",
                    ))

            # Check for very late non-SAE reporting (> 30 days is concerning)
            elif days_to_report > 30:
                deviations.append(Deviation(
                    patient_id=ae.patient_id,
                    deviation_type=DeviationType.AE_REPORTING,
                    severity=DeviationSeverity.MINOR,
                    description=f"AE '{ae.ae_title or ae.ae_id}' reported {days_to_report} days after onset",
                    ae_id=ae.ae_id,
                    is_sae=False,
                    onset_date=ae.onset_date,
                    report_date=report_date,
                    days_delayed=days_to_report,
                    action="Document reason for delayed reporting",
                    requires_explanation=False,
                    affects_evaluability=False,
                    # Provenance
                    data_source="H-34 Excel: Adverse Events sheet",
                    data_fields_used=["ae_id", "is_sae", "onset_date", "report_date"],
                    protocol_reference="Section 8.2 - AE Documentation Requirements",
                    regulatory_reference="ICH GCP 4.11 - Timely AE recording",
                ))

        return DetectorResult(
            detector_name=self.detector_name,
            deviation_type=self.deviation_type,
            deviations=deviations,
            patients_checked=len(patients_checked),
            visits_checked=aes_checked,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    def _get_sae_action(self, days_delayed: int) -> str:
        """Get required action based on SAE reporting delay."""
        if days_delayed <= 2:
            return "Document reason for minor delay"
        elif days_delayed <= 7:
            return "Complete deviation report and PI notification"
        else:
            return "Escalate to sponsor - potential regulatory reporting required"
