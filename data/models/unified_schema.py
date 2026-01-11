"""
Unified data schema for H-34 DELTA Revision Cup Study.
Pydantic models for type-safe data handling and validation.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class PatientStatus(str, Enum):
    ENROLLED = "Enrolled"
    SCREENING = "Screening"
    WITHDRAWN = "Withdrawn"
    COMPLETED = "Completed"


class AffectedSide(str, Enum):
    LEFT = "Left"
    RIGHT = "Right"
    BILATERAL = "Bilateral"


class FollowUpType(str, Enum):
    DISCHARGE = "Discharge"
    TWO_MONTHS = "2 Months"
    SIX_MONTHS = "6 Months"
    ONE_YEAR = "1 Year"
    TWO_YEARS = "2 Years"


class AdverseEventSeverity(str, Enum):
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"


class HHSCategory(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class OHSCategory(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    MODERATE = "Moderate"
    POOR = "Poor"


class Patient(BaseModel):
    """Patient demographics and enrollment data."""
    facility: str = Field(..., description="Clinical site/facility")
    patient_id: str = Field(..., alias="Id", description="Unique patient identifier")
    year_of_birth: Optional[int] = Field(None, description="Year of birth")
    weight: Optional[float] = Field(None, description="Weight in kg")
    height: Optional[float] = Field(None, description="Height in cm")
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    gender: Optional[str] = Field(None, description="Patient gender")
    race: Optional[str] = Field(None, description="Patient race")
    activity_level: Optional[str] = Field(None, description="Daily activity intensity")
    work_status: Optional[str] = Field(None, description="Employment status")
    smoking_habits: Optional[str] = Field(None, description="Smoking status")
    alcohol_habits: Optional[str] = Field(None, description="Alcohol consumption")
    concomitant_medications: Optional[str] = Field(None, description="Current medications")
    screening_date: Optional[date] = Field(None, description="Screening date")
    consent_date: Optional[date] = Field(None, description="Consent date")
    enrolled: Optional[str] = Field(None, description="Enrollment status")
    status: Optional[str] = Field(None, description="Current patient status")

    class Config:
        populate_by_name = True


class Preoperative(BaseModel):
    """Preoperative assessment data."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    assessment_date: Optional[date] = Field(None, alias="Date")
    affected_side: Optional[str] = Field(None, description="Left/Right/Bilateral")
    primary_diagnosis: Optional[str] = Field(None, description="Primary diagnosis")
    medical_history: Optional[str] = Field(None, description="Relevant medical history")
    previous_hip_surgery_affected: Optional[str] = Field(None, description="Previous surgery on affected side")
    previous_hip_surgery_contralateral: Optional[str] = Field(None, description="Previous surgery on contralateral side")
    pain_description: Optional[str] = Field(None, description="Description of pain")
    pain_therapy: Optional[str] = Field(None, description="Pain management therapy")
    osteoporosis: Optional[str] = Field(None, description="Osteoporosis status")

    class Config:
        populate_by_name = True


class RadiographicEvaluation(BaseModel):
    """Radiographic evaluation data at various follow-up points."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    follow_up: Optional[str] = Field(None, alias="Follow UP", description="Follow-up timepoint")
    follow_up_date: Optional[date] = Field(None, alias="Data FU")
    xray_date: Optional[date] = Field(None, description="X-ray date")
    ap_view: Optional[str] = Field(None, description="AP view performed")
    lat_view: Optional[str] = Field(None, description="Lateral view performed")
    varus_valgus_deformity: Optional[str] = Field(None, description="Varus/Valgus deformity")
    osteoarthritis_severity: Optional[str] = Field(None, description="OA severity grade")
    osteophytes_presence: Optional[str] = Field(None, description="Presence of osteophytes")
    osteophytes_location: Optional[str] = Field(None, description="Osteophyte location")
    cysts_presence: Optional[str] = Field(None, description="Presence of cysts")
    cysts_location: Optional[str] = Field(None, description="Cyst location")
    sclerosis: Optional[str] = Field(None, description="Sclerosis status")
    sclerosis_location: Optional[str] = Field(None, description="Sclerosis location")
    femoral_offset: Optional[float] = Field(None, description="Femoral offset in mm")
    contralateral_femoral_offset: Optional[float] = Field(None, description="Contralateral femoral offset")
    ccd_angle: Optional[float] = Field(None, description="CCD angle in degrees")
    contralateral_ccd_angle: Optional[float] = Field(None, description="Contralateral CCD angle")
    leg_length_discrepancy: Optional[float] = Field(None, description="Leg length discrepancy in mm")

    class Config:
        populate_by_name = True


class Intraoperative(BaseModel):
    """Intraoperative data including implant details."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    surgery_date: Optional[date] = Field(None, description="Date of surgery")
    selected_product: Optional[str] = Field(None, description="Product used")
    withdrawn: Optional[str] = Field(None, description="Patient withdrawn")
    withdraw_reason: Optional[str] = Field(None, description="Reason for withdrawal")

    # Stem details
    stem_type: Optional[str] = Field(None, description="Stem type")
    stem_size: Optional[str] = Field(None, description="Stem size")
    stem_cement: Optional[str] = Field(None, description="Stem cemented")
    stem_modularity: Optional[str] = Field(None, description="Stem modularity")

    # Cup details
    cup_type: Optional[str] = Field(None, description="Cup type")
    cup_diameter: Optional[float] = Field(None, description="Cup diameter in mm")
    cup_cement: Optional[str] = Field(None, description="Cup cemented")
    cup_liner_material: Optional[str] = Field(None, description="Liner material")
    cup_liner_size: Optional[str] = Field(None, description="Liner size")
    cup_plate: Optional[str] = Field(None, description="Cup plate used")
    cup_plate_diameter: Optional[float] = Field(None, description="Cup plate diameter")

    # Head details
    head_type: Optional[str] = Field(None, description="Femoral head type")
    head_material: Optional[str] = Field(None, description="Head material")
    head_diameter: Optional[float] = Field(None, description="Head diameter in mm")
    head_size: Optional[str] = Field(None, description="Head size")

    # Bone stock
    acetabulum_bone_quality: Optional[str] = Field(None, description="Acetabular bone quality")
    acetabulum_bone_grafting: Optional[str] = Field(None, description="Acetabular bone grafting")
    femur_bone_quality: Optional[str] = Field(None, description="Femoral bone quality")
    femur_bone_grafting: Optional[str] = Field(None, description="Femoral bone grafting")

    class Config:
        populate_by_name = True


class SurgeryData(BaseModel):
    """Surgery procedure data."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    surgical_approach: Optional[str] = Field(None, description="Surgical approach used")
    anaesthesia: Optional[str] = Field(None, description="Type of anaesthesia")
    surgery_time_minutes: Optional[int] = Field(None, description="Surgery duration in minutes")
    intraoperative_complications: Optional[str] = Field(None, description="Complications during surgery")
    intraoperative_haematocrit: Optional[float] = Field(None, description="Intraoperative haematocrit")
    postoperative_haematocrit: Optional[float] = Field(None, description="Immediate postoperative haematocrit")
    antibiotic_prophylaxis: Optional[str] = Field(None, description="Antibiotic prophylaxis used")
    antithrombotic_prophylaxis: Optional[str] = Field(None, description="Antithrombotic prophylaxis")
    antihemorrhagic_prophylaxis: Optional[str] = Field(None, description="Antihemorrhagic prophylaxis")

    class Config:
        populate_by_name = True


class FollowUp(BaseModel):
    """Follow-up visit data."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    follow_up_type: str = Field(..., description="Follow-up timepoint")
    follow_up_date: Optional[date] = Field(None, description="Date of follow-up")

    # Clinical outcomes (varies by follow-up)
    pain_status: Optional[str] = Field(None, description="Pain assessment")
    mobility_status: Optional[str] = Field(None, description="Mobility assessment")
    wound_healing: Optional[str] = Field(None, description="Wound healing status")
    complications: Optional[str] = Field(None, description="Any complications noted")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        populate_by_name = True


class AdverseEvent(BaseModel):
    """Adverse event data."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    ae_id: Optional[str] = Field(None, alias="Id AE", description="Adverse event ID")
    report_type: Optional[str] = Field(None, description="Report type")
    initial_report_date: Optional[date] = Field(None, description="Initial report date")
    report_date: Optional[date] = Field(None, description="Report date")
    onset_date: Optional[date] = Field(None, description="Date of onset")
    ae_title: Optional[str] = Field(None, description="Adverse event title/diagnosis")
    event_narrative: Optional[str] = Field(None, description="Detailed event narrative")
    is_sae: Optional[str] = Field(None, alias="SAE", description="Is serious adverse event")
    classification: Optional[str] = Field(None, description="AE classification")
    outcome: Optional[str] = Field(None, description="Outcome of the event")
    end_date: Optional[date] = Field(None, description="Event end date")
    severity: Optional[str] = Field(None, description="Severity level")
    device_relationship: Optional[str] = Field(None, description="Relationship to device")
    procedure_relationship: Optional[str] = Field(None, description="Relationship to procedure")
    expectedness: Optional[str] = Field(None, description="Expected/Unexpected")
    action_taken: Optional[str] = Field(None, description="Action taken")
    device_removed: Optional[str] = Field(None, description="Was device removed")
    device_removal_date: Optional[date] = Field(None, description="Device removal date")

    class Config:
        populate_by_name = True


class HHSScore(BaseModel):
    """Harris Hip Score data."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    follow_up: Optional[str] = Field(None, alias="Follow UP", description="Follow-up timepoint")
    follow_up_date: Optional[date] = Field(None, alias="Data FU")

    # HHS components
    pain: Optional[int] = Field(None, description="Pain score (0-44)")
    stairs: Optional[int] = Field(None, description="Stairs score")
    shoes_socks: Optional[int] = Field(None, description="Shoes and socks score")
    sitting: Optional[int] = Field(None, description="Sitting score")
    public_transport: Optional[int] = Field(None, description="Public transportation score")
    limp: Optional[int] = Field(None, description="Limp score")
    walking_support: Optional[int] = Field(None, description="Walking support score")
    distance_walked: Optional[int] = Field(None, description="Distance walked score")

    # Range of motion
    flexion: Optional[float] = Field(None, description="Flexion degrees")
    extension: Optional[float] = Field(None, description="Extension degrees")
    abduction: Optional[float] = Field(None, description="Abduction degrees")
    adduction: Optional[float] = Field(None, description="Adduction degrees")
    external_rotation: Optional[float] = Field(None, description="External rotation degrees")
    internal_rotation: Optional[float] = Field(None, description="Internal rotation degrees")

    # Total score
    total_score: Optional[float] = Field(None, description="Total HHS score (0-100)")
    score_category: Optional[str] = Field(None, alias="Total Score Description", description="Score category")

    class Config:
        populate_by_name = True


class OHSScore(BaseModel):
    """Oxford Hip Score data."""
    facility: str
    patient_id: str = Field(..., alias="Id")
    follow_up: Optional[str] = Field(None, alias="Follow UP", description="Follow-up timepoint")
    follow_up_date: Optional[date] = Field(None, alias="Data FU")

    # OHS questions (12 questions, each scored 0-4)
    q1: Optional[int] = Field(None, alias="Question 1")
    q2: Optional[int] = Field(None, alias="Question 2")
    q3: Optional[int] = Field(None, alias="Question 3")
    q4: Optional[int] = Field(None, alias="Question 4")
    q5: Optional[int] = Field(None, alias="Question 5")
    q6: Optional[int] = Field(None, alias="Question 6")
    q7: Optional[int] = Field(None, alias="Question 7")
    q8: Optional[int] = Field(None, alias="Question 8")
    q9: Optional[int] = Field(None, alias="Question 9")
    q10: Optional[int] = Field(None, alias="Question 10")
    q11: Optional[int] = Field(None, alias="Question 11")
    q12: Optional[int] = Field(None, alias="Question 12")

    # Total score
    total_score: Optional[float] = Field(None, description="Total OHS score (0-48)")
    score_category: Optional[str] = Field(None, alias="Total Score Description", description="Score category")

    class Config:
        populate_by_name = True


class H34StudyData(BaseModel):
    """Complete H-34 DELTA Revision Cup Study dataset."""
    study_name: str = "H-34 DELTA Revision Cup Study"
    study_id: str = "H-34"
    data_export_date: Optional[date] = None

    # Core data
    patients: List[Patient] = Field(default_factory=list)
    preoperatives: List[Preoperative] = Field(default_factory=list)
    radiographic_evaluations: List[RadiographicEvaluation] = Field(default_factory=list)
    intraoperatives: List[Intraoperative] = Field(default_factory=list)
    surgery_data: List[SurgeryData] = Field(default_factory=list)
    follow_ups: List[FollowUp] = Field(default_factory=list)
    adverse_events: List[AdverseEvent] = Field(default_factory=list)
    hhs_scores: List[HHSScore] = Field(default_factory=list)
    ohs_scores: List[OHSScore] = Field(default_factory=list)

    # Metadata
    total_patients: int = 0
    total_adverse_events: int = 0
    facilities: List[str] = Field(default_factory=list)

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        for patient in self.patients:
            if patient.patient_id == patient_id:
                return patient
        return None

    def get_patient_hhs_scores(self, patient_id: str) -> List[HHSScore]:
        """Get all HHS scores for a patient."""
        return [s for s in self.hhs_scores if s.patient_id == patient_id]

    def get_patient_ohs_scores(self, patient_id: str) -> List[OHSScore]:
        """Get all OHS scores for a patient."""
        return [s for s in self.ohs_scores if s.patient_id == patient_id]

    def get_patient_adverse_events(self, patient_id: str) -> List[AdverseEvent]:
        """Get all adverse events for a patient."""
        return [ae for ae in self.adverse_events if ae.patient_id == patient_id]

    def get_follow_up_data(self, follow_up_type: str) -> Dict[str, Any]:
        """Get aggregated data for a specific follow-up timepoint."""
        hhs = [s for s in self.hhs_scores if s.follow_up == follow_up_type]
        ohs = [s for s in self.ohs_scores if s.follow_up == follow_up_type]
        radios = [r for r in self.radiographic_evaluations if r.follow_up == follow_up_type]

        return {
            "follow_up": follow_up_type,
            "hhs_scores": hhs,
            "ohs_scores": ohs,
            "radiographic_evaluations": radios,
            "patient_count": len(set(s.patient_id for s in hhs + ohs)),
        }

    class Config:
        populate_by_name = True
