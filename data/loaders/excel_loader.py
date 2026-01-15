"""
Excel data loader for H-34 DELTA Revision Cup Study.
Loads and parses the multi-sheet Excel export file.
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import date, datetime

import pandas as pd
from pydantic import ValidationError

from data.models.unified_schema import (
    Patient,
    Preoperative,
    RadiographicEvaluation,
    Intraoperative,
    SurgeryData,
    FollowUp,
    AdverseEvent,
    HHSScore,
    OHSScore,
    Explant,
    H34StudyData,
)

logger = logging.getLogger(__name__)


class H34ExcelLoader:
    """
    Loader for H-34 DELTA Revision Cup Study Excel export files.

    Handles the 21-sheet structure:
    - 1 Patients
    - 2 Preoperatives
    - 3-16 Radiographical/Follow-up data at various timepoints
    - 17 Adverse Events
    - 18-19 Score data (HHS, OHS)
    - 20-21 Explants/Reimplants
    """

    SHEET_MAPPING = {
        "1 Patients": "patients",
        "2 Preoperatives": "preoperatives",
        "3 Radiographical evaluation": "radio_preop",
        "4 Intraoperatives": "intraoperatives",
        "5 Surgery Data": "surgery_data",
        "6 Batch number expiry date": "batch_info",
        "7 FU at discharge": "fu_discharge",
        "8 Radiographical Evaluation": "radio_discharge",
        "9 FU 2 Months": "fu_2months",
        "10 Radiographical Evaluation": "radio_2months",
        "11 FU 6 Months": "fu_6months",
        "12 Radiographical Evaluation": "radio_6months",
        "13 FU 1 Year": "fu_1year",
        "14 Radiographical Evaluation": "radio_1year",
        "15 FU 2 Years": "fu_2years",
        "16 Radiographical Evaluation": "radio_2years",
        "17 Adverse Events V2": "adverse_events",
        "18 Score HHS": "hhs_scores",
        "19 Score OHS": "ohs_scores",
        "20 Explants": "explants",
        "21 Reimplants": "reimplants",
    }

    def __init__(self, file_path: str | Path):
        """
        Initialize the loader with path to Excel file.

        Args:
            file_path: Path to the H-34 study Excel export file
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        self._excel_file: Optional[pd.ExcelFile] = None
        self._raw_data: Dict[str, pd.DataFrame] = {}

    def _open_excel(self) -> pd.ExcelFile:
        """Open Excel file and cache the ExcelFile object."""
        if self._excel_file is None:
            logger.info(f"Opening Excel file: {self.file_path}")
            self._excel_file = pd.ExcelFile(self.file_path)
            logger.info(f"Found {len(self._excel_file.sheet_names)} sheets")
        return self._excel_file

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame: handle NaN, strip strings, standardize column names."""
        # Strip whitespace from column names
        df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]

        # Strip whitespace from string values
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

        return df

    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse various date formats to date object."""
        if pd.isna(value) or value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            # Try multiple date formats
            formats = [
                "%Y-%m-%d",      # 2021-09-09
                "%d/%m/%Y",      # 09/09/2021
                "%d-%b-%Y",      # 09-Sep-2021
                "%d-%B-%Y",      # 09-September-2021
                "%m/%d/%Y",      # 09/09/2021 (US format)
                "%Y/%m/%d",      # 2021/09/09
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            logger.warning(f"Could not parse date: {value}")
            return None
        return None

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _safe_str(self, value: Any) -> Optional[str]:
        """Safely convert value to string."""
        if pd.isna(value) or value is None:
            return None
        return str(value).strip()

    def load_raw_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load all sheets as raw DataFrames.

        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        xl = self._open_excel()

        for sheet_name in xl.sheet_names:
            logger.debug(f"Loading sheet: {sheet_name}")
            df = pd.read_excel(xl, sheet_name=sheet_name)
            df = self._clean_dataframe(df)
            self._raw_data[sheet_name] = df
            logger.debug(f"  Loaded {len(df)} rows")

        return self._raw_data

    def _load_patients(self, df: pd.DataFrame) -> List[Patient]:
        """Parse patient data from DataFrame."""
        patients = []
        for _, row in df.iterrows():
            try:
                patient = Patient(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    year_of_birth=self._safe_int(row.get("Year of birth")),
                    weight=self._safe_float(row.get("Weight")),
                    height=self._safe_float(row.get("Height")),
                    bmi=self._safe_float(row.get("BMI")),
                    gender=self._safe_str(row.get("Gender", row.get("Gender "))),
                    race=self._safe_str(row.get("Race")),
                    activity_level=self._safe_str(row.get("Intensity of activity daily living")),
                    work_status=self._safe_str(row.get("Work Status")),
                    smoking_habits=self._safe_str(row.get("Smoking habits")),
                    alcohol_habits=self._safe_str(row.get("Alcohol drinking habits")),
                    concomitant_medications=self._safe_str(row.get("if Yes, please detail API and dosage")),
                    screening_date=self._parse_date(row.get("Screening date")),
                    consent_date=self._parse_date(row.get("Consensus date")),
                    enrolled=self._safe_str(row.get("Enroled")),
                    status=self._safe_str(row.get("Status")),
                )
                patients.append(patient)
            except ValidationError as e:
                logger.warning(f"Validation error for patient row: {e}")
        return patients

    def _load_preoperatives(self, df: pd.DataFrame) -> List[Preoperative]:
        """Parse preoperative data from DataFrame."""
        preoperatives = []
        for _, row in df.iterrows():
            try:
                preop = Preoperative(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    Date=self._parse_date(row.get("Date")),
                    affected_side=self._safe_str(row.get("Affected Side")),
                    primary_diagnosis=self._safe_str(row.get("Primary diagnosis")),
                    medical_history=self._safe_str(row.get("Relevant medical history including any significant disease")),
                    previous_hip_surgery_affected=self._safe_str(row.get("Previous hip treatments or surgeries on the affected side")),
                    previous_hip_surgery_contralateral=self._safe_str(row.get("Previous hip treatments or surgeries on the contralateral side")),
                    pain_description=self._safe_str(row.get("Description of pain")),
                    pain_therapy=self._safe_str(row.get("Pain therapy")),
                    osteoporosis=self._safe_str(row.get("Is the patient affected by osteoporosis?")),
                )
                preoperatives.append(preop)
            except ValidationError as e:
                logger.warning(f"Validation error for preoperative row: {e}")
        return preoperatives

    def _load_radiographic(self, df: pd.DataFrame, follow_up_label: str = None) -> List[RadiographicEvaluation]:
        """Parse radiographic evaluation data from DataFrame."""
        evaluations = []
        for _, row in df.iterrows():
            try:
                eval_data = RadiographicEvaluation(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    follow_up=self._safe_str(row.get("Follow UP", follow_up_label)),
                    follow_up_date=self._parse_date(row.get("Data FU")),
                    xray_date=self._parse_date(row.get("X-rays date")),
                    ap_view=self._safe_str(row.get("X-rays views performedAP view")),
                    lat_view=self._safe_str(row.get("X-rays views performedLAT view")),
                    varus_valgus_deformity=self._safe_str(row.get("Varus/Valgus Deformity")),
                    osteoarthritis_severity=self._safe_str(row.get("Osteoarthritis severity")),
                    osteophytes_presence=self._safe_str(row.get("Presence of osteophytes")),
                    osteophytes_location=self._safe_str(row.get("if Yes please specify the location")),
                    cysts_presence=self._safe_str(row.get("Presence of cystis")),
                    cysts_location=self._safe_str(row.get("if Yes please specify the location.1")),
                    sclerosis=self._safe_str(row.get("Sclerosis")),
                    sclerosis_location=self._safe_str(row.get("if present, please specify the location")),
                    femoral_offset=self._safe_float(row.get("Femoral Offset")),
                    contralateral_femoral_offset=self._safe_float(row.get("Contralateral Femoral Offset")),
                    ccd_angle=self._safe_float(row.get("CCD Angle")),
                    contralateral_ccd_angle=self._safe_float(row.get("Contralateral CCD Angle")),
                    leg_length_discrepancy=self._safe_float(row.get("Leg-Length discrepancy")),
                )
                evaluations.append(eval_data)
            except ValidationError as e:
                logger.warning(f"Validation error for radiographic row: {e}")
        return evaluations

    def _load_intraoperatives(self, df: pd.DataFrame) -> List[Intraoperative]:
        """Parse intraoperative data from DataFrame."""
        intraoperatives = []
        for _, row in df.iterrows():
            try:
                intraop = Intraoperative(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    surgery_date=self._parse_date(row.get("Surgery date")),
                    selected_product=self._safe_str(row.get("Selected product")),
                    withdrawn=self._safe_str(row.get("Withdrawn")),
                    withdraw_reason=self._safe_str(row.get("Withdraw reason")),
                    stem_type=self._safe_str(row.get("Stem Type")),
                    stem_size=self._safe_str(row.get("Stem Size")),
                    stem_cement=self._safe_str(row.get("Stem Cement")),
                    stem_modularity=self._safe_str(row.get("Stem Modularity")),
                    cup_type=self._safe_str(row.get("Cup Type")),
                    cup_diameter=self._safe_float(row.get("Cup Diameter")),
                    cup_cement=self._safe_str(row.get("Cup Cement")),
                    cup_liner_material=self._safe_str(row.get("Cup Liner Material")),
                    cup_liner_size=self._safe_str(row.get("Cup Liner Size")),
                    cup_plate=self._safe_str(row.get("Cup Plate")),
                    cup_plate_diameter=self._safe_float(row.get("Cup Plate Diameter")),
                    head_type=self._safe_str(row.get("Head Type")),
                    head_material=self._safe_str(row.get("Head Material")),
                    head_diameter=self._safe_float(row.get("Head Diameter")),
                    head_size=self._safe_str(row.get("Head Size")),
                    acetabulum_bone_quality=self._safe_str(row.get("Acetabulum Bone Stock Quality")),
                    acetabulum_bone_grafting=self._safe_str(row.get("Acetabulum Bone Grafting")),
                    femur_bone_quality=self._safe_str(row.get("Femur Bone Stock Quality")),
                    femur_bone_grafting=self._safe_str(row.get("Femur Bone Grafting")),
                )
                intraoperatives.append(intraop)
            except ValidationError as e:
                logger.warning(f"Validation error for intraoperative row: {e}")
        return intraoperatives

    def _load_surgery_data(self, df: pd.DataFrame) -> List[SurgeryData]:
        """Parse surgery data from DataFrame."""
        surgeries = []
        for _, row in df.iterrows():
            try:
                surgery = SurgeryData(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    surgical_approach=self._safe_str(row.get("Surgical Approach")),
                    anaesthesia=self._safe_str(row.get("Anaesthesia")),
                    surgery_time_minutes=self._safe_int(row.get("Surgery time (from skin to skin)")),
                    intraoperative_complications=self._safe_str(row.get("Intraoperative complications")),
                    intraoperative_haematocrit=self._safe_float(row.get("Intraoperative haematocrit")),
                    postoperative_haematocrit=self._safe_float(row.get("Immediate postoperative haematocrit")),
                    antibiotic_prophylaxis=self._safe_str(row.get("Antibiotic Prophylaxis")),
                    antithrombotic_prophylaxis=self._safe_str(row.get("Antithrombotic  Prophylaxis")),
                    antihemorrhagic_prophylaxis=self._safe_str(row.get("Antihemorrhagic  Prophylaxis")),
                )
                surgeries.append(surgery)
            except ValidationError as e:
                logger.warning(f"Validation error for surgery data row: {e}")
        return surgeries

    def _load_adverse_events(self, df: pd.DataFrame) -> List[AdverseEvent]:
        """Parse adverse event data from DataFrame."""
        events = []
        for _, row in df.iterrows():
            try:
                ae = AdverseEvent(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    ae_id=self._safe_str(row.get("Id AE")),
                    report_type=self._safe_str(row.get("Report type")),
                    initial_report_date=self._parse_date(row.get("Initial Report Date")),
                    report_date=self._parse_date(row.get("Report Date")),
                    onset_date=self._parse_date(row.get("Date of Onset")),
                    ae_title=self._safe_str(row.get("Adverse Event (diagnosis, if known, or signs/ symptoms)")),
                    event_narrative=self._safe_str(row.get("Event narrative")),
                    is_sae=self._safe_str(row.get("SAE")),
                    classification=self._safe_str(row.get("Classification of the adverse event")),
                    outcome=self._safe_str(row.get("Outcome of the event")),
                    end_date=self._parse_date(row.get("End Date")),
                    severity=self._safe_str(row.get("Severity")),
                    device_relationship=self._safe_str(row.get("Causality: relationship to study medical device")),
                    procedure_relationship=self._safe_str(row.get("Causality: relationship to study procedure")),
                    expectedness=self._safe_str(row.get("Expectedness")),
                    action_taken=self._safe_str(row.get("Action taken")),
                    device_removed=self._safe_str(row.get("Was the device permanently removed?")),
                    device_removal_date=self._parse_date(row.get("Device removal date")),
                )
                events.append(ae)
            except ValidationError as e:
                logger.warning(f"Validation error for adverse event row: {e}")
        return events

    def _load_hhs_scores(self, df: pd.DataFrame) -> List[HHSScore]:
        """Parse Harris Hip Score data from DataFrame."""
        scores = []
        for _, row in df.iterrows():
            try:
                hhs = HHSScore(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    follow_up=self._safe_str(row.get("Follow UP")),
                    follow_up_date=self._parse_date(row.get("Data FU")),
                    pain=self._safe_int(row.get("Pain")),
                    stairs=self._safe_int(row.get("Stairs")),
                    shoes_socks=self._safe_int(row.get("Shoes and socks")),
                    sitting=self._safe_int(row.get("Sitting")),
                    public_transport=self._safe_int(row.get("Public transportation")),
                    limp=self._safe_int(row.get("Limp")),
                    walking_support=self._safe_int(row.get("Walking support")),
                    distance_walked=self._safe_int(row.get("Distance walked")),
                    flexion=self._safe_float(row.get("Flexion")),
                    extension=self._safe_float(row.get("Extension")),
                    abduction=self._safe_float(row.get("Abduction")),
                    adduction=self._safe_float(row.get("Adduction")),
                    external_rotation=self._safe_float(row.get("External rotation")),
                    internal_rotation=self._safe_float(row.get("Internal rotation")),
                    total_score=self._safe_float(row.get("Total Score")),
                    score_category=self._safe_str(row.get("Total Score Description")),
                )
                scores.append(hhs)
            except ValidationError as e:
                logger.warning(f"Validation error for HHS score row: {e}")
        return scores

    def _load_ohs_scores(self, df: pd.DataFrame) -> List[OHSScore]:
        """Parse Oxford Hip Score data from DataFrame."""
        scores = []
        for _, row in df.iterrows():
            try:
                ohs = OHSScore(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    follow_up=self._safe_str(row.get("Follow UP")),
                    follow_up_date=self._parse_date(row.get("Data FU")),
                    q1=self._safe_int(row.get("Question 1")),
                    q2=self._safe_int(row.get("Question 2")),
                    q3=self._safe_int(row.get("Question 3")),
                    q4=self._safe_int(row.get("Question 4")),
                    q5=self._safe_int(row.get("Question 5")),
                    q6=self._safe_int(row.get("Question 6")),
                    q7=self._safe_int(row.get("Question 7")),
                    q8=self._safe_int(row.get("Question 8")),
                    q9=self._safe_int(row.get("Question 9")),
                    q10=self._safe_int(row.get("Question 10")),
                    q11=self._safe_int(row.get("Question 11")),
                    q12=self._safe_int(row.get("Question 12")),
                    total_score=self._safe_float(row.get("Total Score")),
                    score_category=self._safe_str(row.get("Total Score Description")),
                )
                scores.append(ohs)
            except ValidationError as e:
                logger.warning(f"Validation error for OHS score row: {e}")
        return scores

    def _load_explants(self, df: pd.DataFrame) -> List[Explant]:
        """Parse explant/revision data from DataFrame."""
        explants = []
        for _, row in df.iterrows():
            try:
                explant = Explant(
                    facility=self._safe_str(row.get("Facility", "")),
                    Id=self._safe_str(row.get("Id", "")),
                    explant_date=self._parse_date(row.get("Explant date")),
                    stem_explanted=self._safe_str(row.get("Stem Explanted")),
                    cup_explanted=self._safe_str(row.get("Cup Explanted")),
                    cup_liner_explanted=self._safe_str(row.get("Cup Liner Explanted")),
                    cup_plate_explanted=self._safe_str(row.get("Cup Plate Explanted")),
                    head_explanted=self._safe_str(row.get("Head Explanted")),
                    head_adaptor_explanted=self._safe_str(row.get("Head Adaptor Explanted")),
                    notes=self._safe_str(row.get("Notes")),
                )
                explants.append(explant)
            except ValidationError as e:
                logger.warning(f"Validation error for explant row: {e}")
        return explants

    def load(self) -> H34StudyData:
        """
        Load and parse the complete H-34 study data.

        Returns:
            H34StudyData object with all parsed data
        """
        logger.info(f"Loading H-34 study data from: {self.file_path}")

        # Load raw data first
        if not self._raw_data:
            self.load_raw_data()

        # Parse each data type
        patients = self._load_patients(self._raw_data.get("1 Patients", pd.DataFrame()))
        preoperatives = self._load_preoperatives(self._raw_data.get("2 Preoperatives", pd.DataFrame()))
        intraoperatives = self._load_intraoperatives(self._raw_data.get("4 Intraoperatives", pd.DataFrame()))
        surgery_data = self._load_surgery_data(self._raw_data.get("5 Surgery Data", pd.DataFrame()))
        adverse_events = self._load_adverse_events(self._raw_data.get("17 Adverse Events V2", pd.DataFrame()))
        hhs_scores = self._load_hhs_scores(self._raw_data.get("18 Score HHS", pd.DataFrame()))
        ohs_scores = self._load_ohs_scores(self._raw_data.get("19 Score OHS", pd.DataFrame()))
        explants = self._load_explants(self._raw_data.get("20 Explants", pd.DataFrame()))

        # Load all radiographic evaluations with timepoint labels
        radiographic_evals = []
        radio_sheets = [
            ("3 Radiographical evaluation", "Preoperative"),
            ("8 Radiographical Evaluation", "Discharge"),
            ("10 Radiographical Evaluation", "2 Months"),
            ("12 Radiographical Evaluation", "6 Months"),
            ("14 Radiographical Evaluation", "1 Year"),
            ("16 Radiographical Evaluation", "2 Years"),
        ]
        for sheet_name, label in radio_sheets:
            if sheet_name in self._raw_data:
                radiographic_evals.extend(
                    self._load_radiographic(self._raw_data[sheet_name], label)
                )

        # Extract unique facilities
        facilities = list(set(p.facility for p in patients if p.facility))

        # Create the complete study data object
        study_data = H34StudyData(
            patients=patients,
            preoperatives=preoperatives,
            radiographic_evaluations=radiographic_evals,
            intraoperatives=intraoperatives,
            surgery_data=surgery_data,
            adverse_events=adverse_events,
            hhs_scores=hhs_scores,
            ohs_scores=ohs_scores,
            explants=explants,
            total_patients=len(patients),
            total_adverse_events=len(adverse_events),
            facilities=facilities,
        )

        logger.info(f"Loaded H-34 study data:")
        logger.info(f"  Patients: {study_data.total_patients}")
        logger.info(f"  Preoperatives: {len(study_data.preoperatives)}")
        logger.info(f"  Intraoperatives: {len(study_data.intraoperatives)}")
        logger.info(f"  Surgery records: {len(study_data.surgery_data)}")
        logger.info(f"  Radiographic evaluations: {len(study_data.radiographic_evaluations)}")
        logger.info(f"  Adverse events: {study_data.total_adverse_events}")
        logger.info(f"  HHS scores: {len(study_data.hhs_scores)}")
        logger.info(f"  OHS scores: {len(study_data.ohs_scores)}")
        logger.info(f"  Explants: {len(study_data.explants)}")
        logger.info(f"  Facilities: {study_data.facilities}")

        return study_data

    def get_dataframe(self, sheet_name: str) -> pd.DataFrame:
        """
        Get raw DataFrame for a specific sheet.

        Args:
            sheet_name: Name of the sheet

        Returns:
            DataFrame for the sheet
        """
        if not self._raw_data:
            self.load_raw_data()
        return self._raw_data.get(sheet_name, pd.DataFrame())

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the loaded data.

        Returns:
            Dictionary with summary statistics
        """
        if not self._raw_data:
            self.load_raw_data()

        stats = {
            "file_path": str(self.file_path),
            "total_sheets": len(self._raw_data),
            "sheets": {},
        }

        for sheet_name, df in self._raw_data.items():
            stats["sheets"][sheet_name] = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
            }

        return stats
