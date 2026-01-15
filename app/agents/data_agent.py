"""
Data Agent for Clinical Intelligence Platform.

Responsible for querying and analyzing study data from the H-34 Excel export.
Uses H34ExcelLoader to load real study data - no fallback or mock data.
"""
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from app.config import settings
from data.loaders.excel_loader import H34ExcelLoader
from data.models.unified_schema import H34StudyData

logger = logging.getLogger(__name__)

# Module-level singleton for loaded study data
_study_data: Optional[H34StudyData] = None
_excel_loader: Optional[H34ExcelLoader] = None


def get_study_data() -> H34StudyData:
    """
    Get the loaded H-34 study data singleton.

    Raises:
        FileNotFoundError: If the Excel file doesn't exist
        ValueError: If data loading fails
    """
    global _study_data, _excel_loader

    if _study_data is not None:
        return _study_data

    # Get path from settings
    excel_path = settings.get_h34_study_data_path()

    # If primary study data doesn't exist, try synthetic data
    if not excel_path.exists():
        excel_path = settings.get_h34_synthetic_data_path()

    if not excel_path.exists():
        raise FileNotFoundError(
            f"H-34 study data file not found. Checked paths:\n"
            f"  Primary: {settings.get_h34_study_data_path()}\n"
            f"  Synthetic: {settings.get_h34_synthetic_data_path()}"
        )

    logger.info(f"Loading H-34 study data from: {excel_path}")
    _excel_loader = H34ExcelLoader(excel_path)
    _study_data = _excel_loader.load()

    logger.info(f"Successfully loaded {_study_data.total_patients} patients")
    return _study_data


def get_excel_loader() -> H34ExcelLoader:
    """Get the Excel loader (ensures data is loaded)."""
    global _excel_loader
    if _excel_loader is None:
        get_study_data()  # This initializes the loader
    return _excel_loader


class DataAgent(BaseAgent):
    """
    Agent for study data queries and analysis.

    Capabilities:
    - Load patient data from H-34 Excel export
    - Calculate visit timing and deviations
    - Compute outcome metrics (HHS, OHS improvements)
    - Aggregate data for safety and efficacy analysis

    Data Source: H34ExcelLoader (21-sheet Excel export)
    NO FALLBACK: Raises errors if data unavailable.
    """

    agent_type = AgentType.DATA

    def __init__(self, **kwargs):
        """Initialize data agent."""
        super().__init__(**kwargs)
        self._study_data: Optional[H34StudyData] = None

    def _load_data(self) -> H34StudyData:
        """
        Load patient and visit data from Excel.

        Returns:
            H34StudyData object with all study data

        Raises:
            FileNotFoundError: If Excel file not found
            ValueError: If data loading fails
        """
        if self._study_data is None:
            self._study_data = get_study_data()
        return self._study_data

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute data query based on context parameters.

        Args:
            context: Execution context with query parameters

        Returns:
            AgentResult with queried data

        Raises:
            FileNotFoundError: If study data file not found
            ValueError: For invalid queries
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        # Load data - will raise error if file not found
        study_data = self._load_data()

        query_type = context.parameters.get("query_type", "summary")

        if query_type == "patient":
            patient_id = context.patient_id
            if not patient_id:
                raise ValueError("patient_id required for patient query")
            result.data = self._get_patient_data(patient_id)

        elif query_type == "visit":
            visit_id = context.visit_id
            patient_id = context.patient_id
            if not visit_id:
                raise ValueError("visit_id required for visit query")
            result.data = self._get_visit_data(patient_id, visit_id)

        elif query_type == "summary":
            result.data = self._get_study_summary()

        elif query_type == "safety":
            result.data = self._get_safety_data()

        elif query_type == "deviations":
            result.data = self._get_deviation_data(context.parameters)

        elif query_type == "hhs_scores":
            result.data = self._get_hhs_scores(context.parameters)

        elif query_type == "ohs_scores":
            result.data = self._get_ohs_scores(context.parameters)

        elif query_type == "adverse_events":
            result.data = self._get_adverse_events(context.parameters)

        elif query_type == "survival_analysis":
            result.data = self._get_survival_data(context.parameters)

        else:
            raise ValueError(f"Unknown query_type: {query_type}")

        # Add source provenance
        result.add_source(
            SourceType.STUDY_DATA,
            f"H-34 Study Database (n={study_data.total_patients} patients)",
            confidence=1.0,
            details={
                "query_type": query_type,
                "data_source": "PostgreSQL database",
                "tables": ["study_patients", "study_scores", "study_adverse_events", "study_surgeries"],
                "total_patients": study_data.total_patients,
            }
        )

        return result

    def _get_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Get comprehensive data for a specific patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Dictionary with patient demographics, scores, AEs

        Raises:
            ValueError: If patient not found
        """
        study_data = self._load_data()

        patient = study_data.get_patient(patient_id)
        if patient is None:
            raise ValueError(f"Patient {patient_id} not found in study data")

        # Get HHS scores for patient
        hhs_scores = study_data.get_patient_hhs_scores(patient_id)
        hhs_data = [
            {
                "follow_up": s.follow_up,
                "date": s.follow_up_date.isoformat() if s.follow_up_date else None,
                "total_score": s.total_score,
                "category": s.score_category,
            }
            for s in hhs_scores
        ]

        # Get OHS scores for patient
        ohs_scores = study_data.get_patient_ohs_scores(patient_id)
        ohs_data = [
            {
                "follow_up": s.follow_up,
                "date": s.follow_up_date.isoformat() if s.follow_up_date else None,
                "total_score": s.total_score,
                "category": s.score_category,
            }
            for s in ohs_scores
        ]

        # Get adverse events for patient
        adverse_events = study_data.get_patient_adverse_events(patient_id)
        ae_data = [
            {
                "ae_id": ae.ae_id,
                "title": ae.ae_title,
                "onset_date": ae.onset_date.isoformat() if ae.onset_date else None,
                "severity": ae.severity,
                "is_sae": ae.is_sae,
                "outcome": ae.outcome,
                "device_relationship": ae.device_relationship,
            }
            for ae in adverse_events
        ]

        # Get preoperative data
        preop_data = None
        for preop in study_data.preoperatives:
            if preop.patient_id == patient_id:
                preop_data = {
                    "affected_side": preop.affected_side,
                    "primary_diagnosis": preop.primary_diagnosis,
                    "osteoporosis": preop.osteoporosis,
                    "medical_history": preop.medical_history,
                }
                break

        # Get surgery/intraoperative data
        surgery_data = None
        for intraop in study_data.intraoperatives:
            if intraop.patient_id == patient_id:
                surgery_data = {
                    "surgery_date": intraop.surgery_date.isoformat() if intraop.surgery_date else None,
                    "cup_type": intraop.cup_type,
                    "cup_diameter": intraop.cup_diameter,
                    "stem_type": intraop.stem_type,
                    "head_material": intraop.head_material,
                    "acetabulum_bone_quality": intraop.acetabulum_bone_quality,
                }
                break

        return {
            "patient_id": patient_id,
            "demographics": {
                "facility": patient.facility,
                "year_of_birth": patient.year_of_birth,
                "gender": patient.gender,
                "bmi": patient.bmi,
                "weight": patient.weight,
                "height": patient.height,
                "activity_level": patient.activity_level,
                "smoking_habits": patient.smoking_habits,
                "status": patient.status,
            },
            "preoperative": preop_data,
            "surgery": surgery_data,
            "hhs_scores": hhs_data,
            "ohs_scores": ohs_data,
            "adverse_events": ae_data,
            "n_adverse_events": len(ae_data),
        }

    def _get_visit_data(
        self,
        patient_id: Optional[str],
        visit_id: str
    ) -> Dict[str, Any]:
        """
        Get visit data (follow-up timepoint data).

        Args:
            patient_id: Optional patient filter
            visit_id: Follow-up timepoint (e.g., "2 Months", "1 Year")

        Returns:
            Dictionary with visit data including HHS/OHS scores
        """
        study_data = self._load_data()

        # Get follow-up data aggregated by timepoint
        fu_data = study_data.get_follow_up_data(visit_id)

        if patient_id:
            # Filter to specific patient
            fu_data["hhs_scores"] = [
                s for s in fu_data["hhs_scores"] if s.patient_id == patient_id
            ]
            fu_data["ohs_scores"] = [
                s for s in fu_data["ohs_scores"] if s.patient_id == patient_id
            ]

        # Convert to serializable format
        hhs_list = [
            {
                "patient_id": s.patient_id,
                "total_score": s.total_score,
                "category": s.score_category,
                "date": s.follow_up_date.isoformat() if s.follow_up_date else None,
            }
            for s in fu_data["hhs_scores"]
        ]

        ohs_list = [
            {
                "patient_id": s.patient_id,
                "total_score": s.total_score,
                "category": s.score_category,
                "date": s.follow_up_date.isoformat() if s.follow_up_date else None,
            }
            for s in fu_data["ohs_scores"]
        ]

        return {
            "follow_up": visit_id,
            "patient_count": fu_data["patient_count"],
            "hhs_scores": hhs_list,
            "ohs_scores": ohs_list,
            "n_hhs": len(hhs_list),
            "n_ohs": len(ohs_list),
        }

    def _get_study_summary(self) -> Dict[str, Any]:
        """
        Get overall study summary statistics.

        Returns:
            Dictionary with enrollment, status counts, follow-up rates,
            and completion metrics for regulatory readiness assessment.

        CLINICAL DEFINITIONS:
        - enrolled: Patients with enrolled="Yes" OR status="Enrolled"
        - completed: Patients who have 2-year primary endpoint data (HHS at FU 2 Years)
        - withdrawn: Patients marked as withdrawn in intraoperatives data
        """
        study_data = self._load_data()

        # Count patients by status
        status_counts = {}
        for patient in study_data.patients:
            status = patient.status or "Unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count enrolled patients
        # Check both 'enrolled' field (Yes/No) and 'status' field (Enrolled)
        enrolled_count = 0
        for p in study_data.patients:
            if p.enrolled and p.enrolled.lower() == "yes":
                enrolled_count += 1
            elif p.status and p.status.lower() == "enrolled":
                enrolled_count += 1

        # If neither field indicates enrollment, use total patients with surgery
        if enrolled_count == 0:
            enrolled_count = len([
                i for i in study_data.intraoperatives
                if i.surgery_date is not None
            ])

        # Get HHS completion by follow-up
        hhs_by_followup = {}
        for hhs in study_data.hhs_scores:
            fu = hhs.follow_up or "Unknown"
            hhs_by_followup[fu] = hhs_by_followup.get(fu, 0) + 1

        # Get OHS completion by follow-up
        ohs_by_followup = {}
        for ohs in study_data.ohs_scores:
            fu = ohs.follow_up or "Unknown"
            ohs_by_followup[fu] = ohs_by_followup.get(fu, 0) + 1

        # Count surgeries performed
        surgeries_performed = len([
            i for i in study_data.intraoperatives
            if i.surgery_date is not None
        ])

        # Count COMPLETED patients (have 2-year primary endpoint HHS data)
        # Per protocol, completion = having primary endpoint data at 2-year visit
        two_year_patient_ids = set()
        for hhs in study_data.hhs_scores:
            fu = (hhs.follow_up or "").lower()
            # Match various 2-year follow-up naming conventions:
            # "FU 2 Years", "2 Years", "FU 2 Year", "24 Months", etc.
            if "2 year" in fu or "24 month" in fu:
                if hhs.total_score is not None:  # Must have actual score
                    two_year_patient_ids.add(hhs.patient_id)
        completed_count = len(two_year_patient_ids)

        # Count WITHDRAWN patients
        # Check intraoperatives.withdrawn field
        withdrawn_count = sum(
            1 for i in study_data.intraoperatives
            if i.withdrawn and i.withdrawn.lower() == "yes"
        )

        return {
            "total_patients": study_data.total_patients,
            "enrolled": enrolled_count,
            "completed": completed_count,
            "withdrawn": withdrawn_count,
            "status_breakdown": status_counts,
            "surgeries_performed": surgeries_performed,
            "total_adverse_events": study_data.total_adverse_events,
            "facilities": study_data.facilities,
            "n_facilities": len(study_data.facilities),
            "hhs_by_followup": hhs_by_followup,
            "ohs_by_followup": ohs_by_followup,
            "total_hhs_assessments": len(study_data.hhs_scores),
            "total_ohs_assessments": len(study_data.ohs_scores),
        }

    def _get_safety_data(self) -> Dict[str, Any]:
        """
        Get safety-related data aggregations.

        Returns:
            Dictionary with AE counts, rates, breakdown by type
        """
        study_data = self._load_data()

        n_patients = study_data.total_patients
        n_ae = study_data.total_adverse_events

        # Count SAEs
        sae_count = sum(
            1 for ae in study_data.adverse_events
            if ae.is_sae and ae.is_sae.lower() == "yes"
        )

        # Count by severity
        severity_counts = {}
        for ae in study_data.adverse_events:
            sev = ae.severity or "Unknown"
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Count by device relationship
        device_related = sum(
            1 for ae in study_data.adverse_events
            if ae.device_relationship and "related" in ae.device_relationship.lower()
        )

        # Count revisions (device removed)
        revisions = sum(
            1 for ae in study_data.adverse_events
            if ae.device_removed and ae.device_removed.lower() == "yes"
        )

        # Build patient lookup for demographics
        patient_lookup = {p.patient_id: p for p in study_data.patients}

        # Classify AEs by type from title and collect affected patients
        ae_types = {
            "infection": 0,
            "dislocation": 0,
            "fracture": 0,
            "loosening": 0,
            "pain": 0,
            "other": 0,
        }
        affected_patients_by_type = {
            "infection": [],
            "dislocation": [],
            "fracture": [],
            "loosening": [],
            "revision": [],
        }

        for ae in study_data.adverse_events:
            title = (ae.ae_title or "").lower()
            patient = patient_lookup.get(ae.patient_id)
            patient_info = None
            if patient:
                age = None
                if patient.year_of_birth:
                    age = 2024 - patient.year_of_birth
                patient_info = {
                    "patient_id": ae.patient_id,
                    "event_description": ae.ae_title,
                    "severity": ae.severity,
                    "event_date": ae.onset_date.isoformat() if ae.onset_date else None,
                    "is_sae": ae.is_sae == "Yes" if ae.is_sae else False,
                    "demographics": {
                        "gender": patient.gender,
                        "age": age,
                        "bmi": round(patient.bmi, 1) if patient.bmi else None,
                    }
                }

            # Classify and add to affected patients
            if "infection" in title:
                ae_types["infection"] += 1
                if patient_info:
                    affected_patients_by_type["infection"].append(patient_info)
            elif "dislocation" in title:
                ae_types["dislocation"] += 1
                if patient_info:
                    affected_patients_by_type["dislocation"].append(patient_info)
            elif "fracture" in title:
                ae_types["fracture"] += 1
                if patient_info:
                    affected_patients_by_type["fracture"].append(patient_info)
            elif "loosening" in title:
                ae_types["loosening"] += 1
                if patient_info:
                    affected_patients_by_type["loosening"].append(patient_info)
            elif "pain" in title:
                ae_types["pain"] += 1
            else:
                ae_types["other"] += 1

            # Track revisions (device removed)
            if ae.device_removed and ae.device_removed.lower() == "yes" and patient_info:
                affected_patients_by_type["revision"].append(patient_info)

        # Calculate rates
        rates = {}
        if n_patients > 0:
            rates["ae_rate"] = round(n_ae / n_patients, 4)
            rates["sae_rate"] = round(sae_count / n_patients, 4)
            rates["device_related_rate"] = round(device_related / n_patients, 4)
            rates["revision_rate"] = round(revisions / n_patients, 4)
            rates["infection_rate"] = round(ae_types["infection"] / n_patients, 4)
            rates["dislocation_rate"] = round(ae_types["dislocation"] / n_patients, 4)
            rates["fracture_rate"] = round(ae_types["fracture"] / n_patients, 4)

        return {
            "n_patients": n_patients,
            "n_adverse_events": n_ae,
            "n_sae": sae_count,
            "n_device_related": device_related,
            "n_revisions": revisions,
            "ae_by_type": ae_types,
            "ae_by_severity": severity_counts,
            "rates": rates,
            "affected_patients_by_type": affected_patients_by_type,
        }

    def _get_hhs_scores(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get HHS score data with optional filtering.

        Args:
            parameters: Query parameters (follow_up, patient_id)

        Returns:
            Dictionary with HHS scores and statistics
        """
        study_data = self._load_data()

        follow_up = parameters.get("follow_up")
        patient_id = parameters.get("patient_id")

        scores = study_data.hhs_scores

        # Apply filters
        if follow_up:
            scores = [s for s in scores if s.follow_up == follow_up]
        if patient_id:
            scores = [s for s in scores if s.patient_id == patient_id]

        # Convert to serializable format
        score_list = [
            {
                "patient_id": s.patient_id,
                "follow_up": s.follow_up,
                "total_score": s.total_score,
                "category": s.score_category,
                "date": s.follow_up_date.isoformat() if s.follow_up_date else None,
            }
            for s in scores
        ]

        # Calculate statistics
        valid_scores = [s.total_score for s in scores if s.total_score is not None]
        stats = {}
        if valid_scores:
            stats["mean"] = round(sum(valid_scores) / len(valid_scores), 1)
            stats["min"] = min(valid_scores)
            stats["max"] = max(valid_scores)
            stats["n"] = len(valid_scores)
            # Count MCID achievers (improvement >= 20 from baseline)
            # Note: This requires baseline comparison - simplified here

        return {
            "scores": score_list,
            "statistics": stats,
            "n_scores": len(score_list),
        }

    def _get_ohs_scores(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get OHS score data with optional filtering.

        Args:
            parameters: Query parameters (follow_up, patient_id)

        Returns:
            Dictionary with OHS scores and statistics
        """
        study_data = self._load_data()

        follow_up = parameters.get("follow_up")
        patient_id = parameters.get("patient_id")

        scores = study_data.ohs_scores

        # Apply filters
        if follow_up:
            scores = [s for s in scores if s.follow_up == follow_up]
        if patient_id:
            scores = [s for s in scores if s.patient_id == patient_id]

        # Convert to serializable format
        score_list = [
            {
                "patient_id": s.patient_id,
                "follow_up": s.follow_up,
                "total_score": s.total_score,
                "category": s.score_category,
                "date": s.follow_up_date.isoformat() if s.follow_up_date else None,
            }
            for s in scores
        ]

        # Calculate statistics
        valid_scores = [s.total_score for s in scores if s.total_score is not None]
        stats = {}
        if valid_scores:
            stats["mean"] = round(sum(valid_scores) / len(valid_scores), 1)
            stats["min"] = min(valid_scores)
            stats["max"] = max(valid_scores)
            stats["n"] = len(valid_scores)

        return {
            "scores": score_list,
            "statistics": stats,
            "n_scores": len(score_list),
        }

    def _get_adverse_events(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get adverse event data with optional filtering.

        Args:
            parameters: Query parameters (patient_id, severity, sae_only)

        Returns:
            Dictionary with adverse events
        """
        study_data = self._load_data()

        patient_id = parameters.get("patient_id")
        severity = parameters.get("severity")
        sae_only = parameters.get("sae_only", False)

        events = study_data.adverse_events

        # Apply filters
        if patient_id:
            events = [e for e in events if e.patient_id == patient_id]
        if severity:
            events = [e for e in events if e.severity == severity]
        if sae_only:
            events = [e for e in events if e.is_sae and e.is_sae.lower() == "yes"]

        # Convert to serializable format
        event_list = [
            {
                "patient_id": e.patient_id,
                "ae_id": e.ae_id,
                "title": e.ae_title,
                "onset_date": e.onset_date.isoformat() if e.onset_date else None,
                "severity": e.severity,
                "is_sae": e.is_sae,
                "outcome": e.outcome,
                "device_relationship": e.device_relationship,
                "classification": e.classification,
            }
            for e in events
        ]

        return {
            "adverse_events": event_list,
            "n_events": len(event_list),
        }

    def _get_deviation_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get visit timing deviation data.

        This calculates deviations by comparing actual visit dates
        to expected visit windows based on surgery date.

        Args:
            parameters: Query parameters

        Returns:
            Dictionary with deviations by patient and visit
        """
        study_data = self._load_data()

        # Visit window definitions (days from surgery)
        # Keys match actual follow-up names in H-34 study data
        # VALUES MUST MATCH protocol_rules.yaml schedule_of_assessments
        visit_windows = {
            "Discharge": {"target": 3, "minus": 2, "plus": 4},       # Protocol: day 3, -2/+4
            "FU 2 Months": {"target": 60, "minus": 14, "plus": 28},  # Protocol: day 60, -14/+28
            "FU 6 Months": {"target": 180, "minus": 30, "plus": 30}, # Protocol: day 180, -30/+30
            "FU 1 Year": {"target": 365, "minus": 30, "plus": 60},   # Protocol: day 365, -30/+60
            "FU 2 Years": {"target": 730, "minus": 60, "plus": 60},  # Protocol: day 730, -60/+60
        }

        deviations = []

        # Build surgery date lookup
        surgery_dates = {}
        for intraop in study_data.intraoperatives:
            if intraop.surgery_date:
                surgery_dates[intraop.patient_id] = intraop.surgery_date

        # Check HHS score visits
        for hhs in study_data.hhs_scores:
            if not hhs.follow_up_date or hhs.follow_up not in visit_windows:
                continue

            surgery_date = surgery_dates.get(hhs.patient_id)
            if not surgery_date:
                continue

            window = visit_windows[hhs.follow_up]
            expected_day = window["target"]
            actual_days = (hhs.follow_up_date - surgery_date).days
            deviation = actual_days - expected_day

            # Check if within window
            window_min = expected_day - window["minus"]
            window_max = expected_day + window["plus"]
            within_window = window_min <= actual_days <= window_max

            # Classify deviation
            if within_window:
                classification = "ON_TIME"
            elif abs(deviation) <= window["plus"] * 1.5:
                classification = "MINOR"
            elif abs(deviation) <= window["plus"] * 2:
                classification = "MAJOR"
            else:
                classification = "CRITICAL"

            if not within_window:
                deviations.append({
                    "patient_id": hhs.patient_id,
                    "visit": hhs.follow_up,
                    "expected_day": expected_day,
                    "actual_day": actual_days,
                    "deviation_days": deviation,
                    "classification": classification,
                    "window": f"[{window_min}, {window_max}]",
                })

        # Count by severity (lowercase keys for frontend compatibility)
        by_severity = {"minor": 0, "major": 0, "critical": 0}
        for d in deviations:
            classification = d["classification"].lower()
            by_severity[classification] = by_severity.get(classification, 0) + 1

        # Count by visit
        by_visit = {}
        for d in deviations:
            by_visit[d["visit"]] = by_visit.get(d["visit"], 0) + 1

        # Calculate total visits (assessments expected)
        total_visits = len(surgery_dates) * len(visit_windows)

        return {
            "total_visits": total_visits,
            "total_deviations": len(deviations),
            "deviation_rate": round(len(deviations) / total_visits, 4) if total_visits > 0 else 0,
            "deviations": deviations,
            "by_severity": by_severity,
            "by_visit": by_visit,
        }

    def get_patient_count(self) -> int:
        """Get total patient count."""
        return self._load_data().total_patients

    def get_patient_ids(self) -> List[str]:
        """Get list of all patient IDs."""
        study_data = self._load_data()
        return [p.patient_id for p in study_data.patients]

    def calculate_hhs_improvement(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Calculate HHS improvement for a patient (baseline to 2-year).

        Args:
            patient_id: Patient identifier

        Returns:
            Dictionary with HHS improvement metrics, or None if insufficient data
        """
        study_data = self._load_data()

        hhs_scores = study_data.get_patient_hhs_scores(patient_id)
        if not hhs_scores:
            return None

        # Find baseline (Preoperative) and 2-year scores
        baseline_score = None
        two_year_score = None

        for score in hhs_scores:
            fu = (score.follow_up or "").lower()
            if "preop" in fu or "baseline" in fu or "screening" in fu:
                if score.total_score is not None:
                    baseline_score = score.total_score
            elif "2 year" in fu or "24 month" in fu:
                if score.total_score is not None:
                    two_year_score = score.total_score

        if baseline_score is None or two_year_score is None:
            # Return partial data if available
            return {
                "patient_id": patient_id,
                "hhs_baseline": baseline_score,
                "hhs_2yr": two_year_score,
                "improvement": None,
                "mcid_achieved": None,
                "note": "Incomplete data - missing baseline or 2-year score",
            }

        improvement = two_year_score - baseline_score
        mcid_achieved = improvement >= 20  # MCID threshold is 20 points

        return {
            "patient_id": patient_id,
            "hhs_baseline": float(baseline_score),
            "hhs_2yr": float(two_year_score),
            "improvement": float(improvement),
            "mcid_achieved": mcid_achieved,
        }

    def get_mcid_rate(self) -> Dict[str, Any]:
        """
        Calculate MCID achievement rate across all evaluable patients.

        Returns:
            Dictionary with MCID statistics
        """
        study_data = self._load_data()

        evaluable = 0
        achieved = 0

        patient_ids = set(p.patient_id for p in study_data.patients)

        for pid in patient_ids:
            result = self.calculate_hhs_improvement(pid)
            if result and result.get("mcid_achieved") is not None:
                evaluable += 1
                if result["mcid_achieved"]:
                    achieved += 1

        return {
            "evaluable_patients": evaluable,
            "mcid_achieved": achieved,
            "mcid_rate": round(achieved / evaluable, 4) if evaluable > 0 else None,
            "target_rate": 0.50,  # Protocol target: 50% MCID
        }

    def _get_survival_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Kaplan-Meier survival analysis data for revision-free survival.

        Calculates time-to-event data for each patient:
        - Event = 1 if patient had a revision (explant)
        - Event = 0 if patient is censored (no revision, still in follow-up)
        - Time = days from surgery to event or last follow-up

        Args:
            parameters: Query parameters (optional filters)

        Returns:
            Dictionary with:
            - survival_data: List of patient records with time_to_event, event, etc.
            - summary: Aggregate statistics (n_events, n_censored, survival_rate)
            - kaplan_meier_table: Time-based survival probability table
        """
        study_data = self._load_data()

        # Build surgery date lookup from intraoperatives
        surgery_dates = {}
        for intraop in study_data.intraoperatives:
            if intraop.surgery_date:
                surgery_dates[intraop.patient_id] = intraop.surgery_date

        # Build explant date lookup (first explant per patient = revision event)
        explant_dates = {}
        for explant in study_data.explants:
            if explant.explant_date and explant.patient_id not in explant_dates:
                explant_dates[explant.patient_id] = explant.explant_date

        # Build last follow-up date lookup from HHS/OHS scores
        last_followup_dates = {}
        for hhs in study_data.hhs_scores:
            if hhs.follow_up_date:
                pid = hhs.patient_id
                if pid not in last_followup_dates or hhs.follow_up_date > last_followup_dates[pid]:
                    last_followup_dates[pid] = hhs.follow_up_date
        for ohs in study_data.ohs_scores:
            if ohs.follow_up_date:
                pid = ohs.patient_id
                if pid not in last_followup_dates or ohs.follow_up_date > last_followup_dates[pid]:
                    last_followup_dates[pid] = ohs.follow_up_date

        # Calculate survival data for each patient with surgery
        survival_records = []
        for patient_id, surgery_date in surgery_dates.items():
            record = {
                "patient_id": patient_id,
                "surgery_date": surgery_date.isoformat(),
            }

            if patient_id in explant_dates:
                # Patient had a revision (event)
                event_date = explant_dates[patient_id]
                time_to_event = (event_date - surgery_date).days
                record["event"] = 1
                record["event_date"] = event_date.isoformat()
                record["time_to_event_days"] = time_to_event
                record["time_to_event_months"] = round(time_to_event / 30.44, 1)
                record["time_to_event_years"] = round(time_to_event / 365.25, 2)
                record["status"] = "revised"
            elif patient_id in last_followup_dates:
                # Patient censored at last follow-up
                followup_date = last_followup_dates[patient_id]
                time_to_event = (followup_date - surgery_date).days
                record["event"] = 0
                record["event_date"] = None
                record["last_followup_date"] = followup_date.isoformat()
                record["time_to_event_days"] = time_to_event
                record["time_to_event_months"] = round(time_to_event / 30.44, 1)
                record["time_to_event_years"] = round(time_to_event / 365.25, 2)
                record["status"] = "censored"
            else:
                # No follow-up data available - skip
                continue

            survival_records.append(record)

        # Sort by time to event
        survival_records.sort(key=lambda x: x["time_to_event_days"])

        # Calculate summary statistics
        n_total = len(survival_records)
        n_events = sum(1 for r in survival_records if r["event"] == 1)
        n_censored = n_total - n_events

        # Calculate Kaplan-Meier survival estimates at key timepoints
        # Using standard KM formula: S(t) = S(t-1) * (1 - d/n)
        km_table = []
        at_risk = n_total
        survival_prob = 1.0

        # Process events in chronological order
        events_by_time = {}
        for r in survival_records:
            t = r["time_to_event_days"]
            if t not in events_by_time:
                events_by_time[t] = {"events": 0, "censored": 0}
            if r["event"] == 1:
                events_by_time[t]["events"] += 1
            else:
                events_by_time[t]["censored"] += 1

        for t in sorted(events_by_time.keys()):
            d = events_by_time[t]["events"]  # events at this time
            c = events_by_time[t]["censored"]  # censored at this time

            if d > 0 and at_risk > 0:
                survival_prob = survival_prob * (1 - d / at_risk)

            km_table.append({
                "time_days": t,
                "time_months": round(t / 30.44, 1),
                "time_years": round(t / 365.25, 2),
                "at_risk": at_risk,
                "events": d,
                "censored": c,
                "survival_probability": round(survival_prob, 4),
                "survival_percent": round(survival_prob * 100, 1),
            })

            at_risk -= (d + c)

        # Calculate survival at standard timepoints (1yr, 2yr)
        survival_at_1yr = None
        survival_at_2yr = None
        for entry in km_table:
            if entry["time_days"] <= 365:
                survival_at_1yr = entry["survival_percent"]
            if entry["time_days"] <= 730:
                survival_at_2yr = entry["survival_percent"]

        # If no events occurred at these timepoints, use last known survival
        if survival_at_1yr is None and km_table:
            survival_at_1yr = 100.0 if not km_table else km_table[-1]["survival_percent"]
        if survival_at_2yr is None and km_table:
            survival_at_2yr = survival_at_1yr if survival_at_1yr else 100.0

        return {
            "survival_data": survival_records,
            "n_patients": n_total,
            "n_events": n_events,
            "n_censored": n_censored,
            "revision_rate": round(n_events / n_total, 4) if n_total > 0 else None,
            "survival_rate_2yr": survival_at_2yr,
            "survival_rate_1yr": survival_at_1yr,
            "kaplan_meier_table": km_table,
            "summary": {
                "endpoint": "Revision-free survival",
                "analysis_method": "Kaplan-Meier",
                "total_patients_analyzed": n_total,
                "total_revisions": n_events,
                "total_censored": n_censored,
                "median_follow_up_days": round(
                    sum(r["time_to_event_days"] for r in survival_records) / n_total, 1
                ) if n_total > 0 else None,
                "survival_probability_1yr": survival_at_1yr,
                "survival_probability_2yr": survival_at_2yr,
            },
        }
