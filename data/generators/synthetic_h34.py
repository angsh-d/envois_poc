"""
Synthetic Data Generator for H-34 DELTA Revision Cup Study.

Generates clinically-realistic synthetic patient data based on:
1. Actual H-34 study distributions (N=37)
2. Published literature benchmarks for hip revision outcomes

Purpose: Enable ML model training for POC demonstration.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SyntheticConfig:
    """Configuration for synthetic data generation."""

    n_patients: int = 300
    random_seed: int = 42

    # Study period
    study_start_date: date = date(2021, 9, 1)
    study_end_date: date = date(2025, 9, 30)

    # Demographics (from real H-34 data)
    female_ratio: float = 0.68
    age_mean: float = 66.4
    age_std: float = 10.9
    age_min: int = 43
    age_max: int = 91
    bmi_mean: float = 28.6
    bmi_std: float = 5.1
    bmi_min: float = 18.5
    bmi_max: float = 42.0

    # HHS trajectory (from real H-34 + literature)
    hhs_preop_mean: float = 37.7
    hhs_preop_std: float = 17.2
    hhs_2mo_mean: float = 57.1
    hhs_2mo_std: float = 16.0
    hhs_6mo_mean: float = 70.1
    hhs_6mo_std: float = 16.5
    hhs_1yr_mean: float = 74.3
    hhs_1yr_std: float = 20.5
    hhs_2yr_mean: float = 72.6
    hhs_2yr_std: float = 19.2

    # Adverse events (from real H-34 + literature)
    ae_rate: float = 0.35  # 35% of patients have AE
    sae_ratio: float = 0.80  # 80% of AEs are serious

    # Revision rates (literature: 5-10% for revision cups)
    revision_rate: float = 0.08  # 8% overall
    early_revision_ratio: float = 0.70  # 70% of revisions are early (<90 days)

    # Follow-up completion rates (adjusted for synthetic to enable ML)
    fu_completion_rates: Dict[str, float] = field(default_factory=lambda: {
        '2mo': 0.85,
        '6mo': 0.75,
        '1yr': 0.60,
        '2yr': 0.45,  # Increased from 22% to enable trajectory clustering
    })

    # Facilities (from real H-34)
    facilities: List[str] = field(default_factory=lambda: [
        "Samodzielny Publiczny Szpital Kliniczny im. Prof. A. Grucy",
        "Klinikum rechts der Isar, Technical University Munich",
        "Synthetic Site Alpha",
        "Synthetic Site Beta",
    ])


class SyntheticH34Generator:
    """
    Generates synthetic H-34 DELTA Revision Cup Study data.

    All generated data is marked with is_synthetic=True for transparency.
    """

    def __init__(self, config: Optional[SyntheticConfig] = None):
        self.config = config or SyntheticConfig()
        self.rng = np.random.default_rng(self.config.random_seed)

        # Generated data storage
        self.patients: List[Dict] = []
        self.preoperatives: List[Dict] = []
        self.intraoperatives: List[Dict] = []
        self.surgery_data: List[Dict] = []
        self.hhs_scores: List[Dict] = []
        self.ohs_scores: List[Dict] = []
        self.adverse_events: List[Dict] = []
        self.explants: List[Dict] = []

        # Tracking
        self._patient_outcomes: Dict[str, Dict] = {}  # patient_id -> outcome data

    def _generate_patient_id(self, idx: int) -> str:
        """Generate synthetic patient ID."""
        return f"SYN-{idx:04d}"

    def _generate_surgery_date(self) -> date:
        """Generate random surgery date within study period."""
        days_range = (self.config.study_end_date - self.config.study_start_date).days
        random_days = int(self.rng.integers(0, days_range))
        return self.config.study_start_date + timedelta(days=random_days)

    def _generate_demographics(self, patient_id: str) -> Dict:
        """Generate patient demographics."""
        is_female = self.rng.random() < self.config.female_ratio

        # Age
        age = self.rng.normal(self.config.age_mean, self.config.age_std)
        age = int(np.clip(age, self.config.age_min, self.config.age_max))
        year_of_birth = 2025 - age

        # BMI and weight/height
        bmi = self.rng.normal(self.config.bmi_mean, self.config.bmi_std)
        bmi = np.clip(bmi, self.config.bmi_min, self.config.bmi_max)

        # Height based on gender
        height_mean = 162 if is_female else 175
        height = self.rng.normal(height_mean, 7)
        height = np.clip(height, 145, 195)

        # Weight from BMI
        weight = bmi * (height / 100) ** 2

        return {
            'Facility': self.rng.choice(self.config.facilities),
            'Id': patient_id,
            'Year of birth': int(year_of_birth),
            'Weight': round(weight, 1),
            'Height': round(height, 1),
            'BMI': round(bmi, 1),
            'Gender': 'Female' if is_female else 'Male',
            'Race': self.rng.choice(['Caucasian', 'Caucasian', 'Caucasian', 'Other'], p=[0.85, 0.05, 0.05, 0.05]),
            'Smoking habits': self.rng.choice(['Never', 'Previous', 'Current'], p=[0.6, 0.3, 0.1]),
            'Alcohol drinking habits': self.rng.choice(['No', 'Occasionally', 'Regularly'], p=[0.5, 0.4, 0.1]),
            'Status': 'Enrolled',
            'is_synthetic': True,
        }

    def _generate_preoperative(self, patient_id: str, facility: str, surgery_date: date) -> Dict:
        """Generate preoperative assessment data."""
        diagnoses = [
            "Revision of previous unsuccessful femoral head replacement, cup arthroplasty or other procedure",
            "Presence of bone stock of poor quality or inadequate for other reconstructive techniques",
            "Clinical management problem where arthrodesis or alternative reconstruction techniques are less likely",
        ]

        return {
            'Facility': facility,
            'Id': patient_id,
            'Date': surgery_date - timedelta(days=int(self.rng.integers(7, 60))),
            'Affected Side': self.rng.choice(['Left', 'Right']),
            'Primary diagnosis': self.rng.choice(diagnoses, p=[0.55, 0.35, 0.10]),
            'Medical history': self.rng.choice(['Hypertension', 'Diabetes Type 2', 'None significant', 'Osteoporosis']),
            'Osteoporosis': self.rng.choice(['Yes', 'No'], p=[0.25, 0.75]),
            'is_synthetic': True,
        }

    def _generate_intraoperative(self, patient_id: str, facility: str, surgery_date: date) -> Dict:
        """Generate intraoperative/implant data."""
        cup_sizes = [50, 54, 58, 62, 66]
        cup_probs = [0.15, 0.30, 0.30, 0.15, 0.10]

        return {
            'Facility': facility,
            'Id': patient_id,
            'Surgery date': surgery_date,
            'Selected product': 'DELTA Revision TT Cup',
            'Cup Type': 'DELTA Revision TT',
            'Cup Diameter': self.rng.choice(cup_sizes, p=cup_probs),
            'Cup Cement': 'No',
            'Cup Liner Material': self.rng.choice(['Ceramic', 'Polyethylene'], p=[0.7, 0.3]),
            'Stem Type': self.rng.choice(['Cemented', 'Cementless'], p=[0.4, 0.6]),
            'Head Diameter': self.rng.choice([28, 32, 36], p=[0.2, 0.5, 0.3]),
            'Head Material': self.rng.choice(['Ceramic', 'Metal'], p=[0.7, 0.3]),
            'Acetabulum Bone Stock Quality': self.rng.choice(['Good', 'Fair', 'Poor'], p=[0.3, 0.5, 0.2]),
            'is_synthetic': True,
        }

    def _generate_surgery_data(self, patient_id: str, facility: str) -> Dict:
        """Generate surgery procedure data."""
        surgery_time = self.rng.normal(153.5, 38.1)
        surgery_time = int(np.clip(surgery_time, 80, 280))

        # Intraoperative complications (rare but important)
        has_complication = self.rng.random() < 0.08
        complication = 'Intraoperative fracture' if has_complication else 'None'

        return {
            'Facility': facility,
            'Id': patient_id,
            'Surgical Approach': 'Postero-lateral',
            'Anaesthesia': self.rng.choice(['Spinal', 'General'], p=[0.6, 0.4]),
            'Surgery time (from skin to skin)': surgery_time,
            'Intraoperative complications': complication,
            'Antibiotic Prophylaxis': 'Yes',
            'Antithrombotic Prophylaxis': 'Yes',
            'is_synthetic': True,
        }

    def _generate_hhs_trajectory(
        self,
        patient_id: str,
        facility: str,
        surgery_date: date,
        has_revision: bool,
        revision_day: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate realistic HHS trajectory for a patient.

        Uses a modified exponential recovery curve with individual variation.
        Patients who have revisions show declining or poor scores.
        """
        scores = []

        # Generate baseline preoperative score
        preop_score = self.rng.normal(self.config.hhs_preop_mean, self.config.hhs_preop_std)
        preop_score = np.clip(preop_score, 10, 75)

        # Individual recovery potential (some patients recover better than others)
        # Increased variation to create more realistic MCID distribution (60-80% achieving MCID)
        recovery_potential = self.rng.normal(1.0, 0.25)
        recovery_potential = np.clip(recovery_potential, 0.3, 1.4)

        # Noise factor for individual variation
        noise_factor = self.rng.normal(0, 3)

        # Calculate expected scores at each timepoint
        timepoints = [
            ('Preoperative', 0, preop_score),
            ('FU 2 Months', 60, self.config.hhs_2mo_mean),
            ('FU 6 Months', 180, self.config.hhs_6mo_mean),
            ('FU 1 Year', 365, self.config.hhs_1yr_mean),
            ('FU 2 Years', 730, self.config.hhs_2yr_mean),
        ]

        for fu_label, days_post_surgery, target_mean in timepoints:
            # Check if patient should have this follow-up
            if fu_label != 'Preoperative':
                fu_key = fu_label.replace('FU ', '').replace(' ', '').lower()
                fu_key = {'2months': '2mo', '6months': '6mo', '1year': '1yr', '2years': '2yr'}.get(fu_key, fu_key)

                if self.rng.random() > self.config.fu_completion_rates.get(fu_key, 0.5):
                    continue  # Patient missed this follow-up

                # Check if revision happened before this timepoint
                if has_revision and revision_day and days_post_surgery > revision_day:
                    continue  # No follow-up after revision

            # Calculate score
            if fu_label == 'Preoperative':
                score = preop_score
            else:
                # Recovery curve with individual variation
                expected_improvement = (target_mean - self.config.hhs_preop_mean) * recovery_potential
                score = preop_score + expected_improvement + noise_factor

                # Add timepoint-specific noise
                score += self.rng.normal(0, 5)

                # If approaching revision, show declining scores
                if has_revision and revision_day and days_post_surgery > revision_day - 60:
                    decline = self.rng.uniform(10, 25)
                    score -= decline

            score = np.clip(score, 10, 100)

            # Determine score category
            if score >= 90:
                category = 'Excellent'
            elif score >= 80:
                category = 'Good'
            elif score >= 70:
                category = 'Fair'
            else:
                category = 'Poor'

            fu_date = surgery_date + timedelta(days=days_post_surgery) if days_post_surgery > 0 else surgery_date - timedelta(days=7)

            scores.append({
                'Facility': facility,
                'Id': patient_id,
                'Follow UP': fu_label,
                'Data FU': fu_date,
                'Total Score': round(score, 1),
                'Total Score Description': category,
                'Pain': self._hhs_component_from_total(score, 'pain'),
                'Limp': self._hhs_component_from_total(score, 'limp'),
                'Walking support': self._hhs_component_from_total(score, 'support'),
                'Distance walked': self._hhs_component_from_total(score, 'distance'),
                'is_synthetic': True,
            })

        return scores

    def _hhs_component_from_total(self, total: float, component: str) -> int:
        """Estimate HHS component score from total (approximate)."""
        # HHS components and their max values
        max_scores = {'pain': 44, 'limp': 11, 'support': 11, 'distance': 11}
        max_val = max_scores.get(component, 10)

        # Approximate component as proportion of total
        ratio = total / 100
        component_score = int(ratio * max_val)
        return np.clip(component_score, 0, max_val)

    def _generate_ohs_trajectory(
        self,
        patient_id: str,
        facility: str,
        surgery_date: date,
        hhs_scores: List[Dict]
    ) -> List[Dict]:
        """Generate OHS scores correlated with HHS scores."""
        ohs_scores = []

        for hhs in hhs_scores:
            # OHS is correlated with HHS but on 0-48 scale
            # Higher OHS = better (like HHS)
            hhs_total = hhs['Total Score']

            # Convert HHS (0-100) to OHS (0-48) with some noise
            ohs_total = (hhs_total / 100) * 48 + self.rng.normal(0, 3)
            ohs_total = np.clip(ohs_total, 0, 48)

            if ohs_total >= 42:
                category = 'Excellent'
            elif ohs_total >= 34:
                category = 'Good'
            elif ohs_total >= 27:
                category = 'Moderate'
            else:
                category = 'Poor'

            ohs_scores.append({
                'Facility': facility,
                'Id': patient_id,
                'Follow UP': hhs['Follow UP'],
                'Data FU': hhs['Data FU'],
                'Total Score': round(ohs_total, 1),
                'Total Score Description': category,
                'is_synthetic': True,
            })

        return ohs_scores

    def _generate_adverse_event(
        self,
        patient_id: str,
        facility: str,
        surgery_date: date,
        is_revision_related: bool = False
    ) -> Dict:
        """Generate an adverse event."""

        if is_revision_related:
            ae_types = [
                ('Cup loosening', 'Severe', True),
                ('Dislocation', 'Severe', True),
                ('Periprosthetic fracture', 'Severe', True),
                ('Periprosthetic Joint Infection', 'Severe', True),
            ]
        else:
            ae_types = [
                ('Intraoperative fracture of greater trochanter', 'Moderate', True),
                ('Dislocation', 'Moderate', True),
                ('Wound healing complication', 'Mild', False),
                ('Deep vein thrombosis', 'Moderate', True),
                ('Urinary tract infection', 'Mild', False),
                ('Peroneal nerve palsy', 'Moderate', True),
            ]

        ae_type, severity, is_sae = ae_types[self.rng.integers(0, len(ae_types))]

        # Onset date (most AEs occur early)
        if is_revision_related:
            days_to_onset = int(self.rng.integers(7, 90))
        else:
            days_to_onset = int(self.rng.integers(0, 180))

        onset_date = surgery_date + timedelta(days=days_to_onset)

        return {
            'Facility': facility,
            'Id': patient_id,
            'Id AE': f"AE-{patient_id}-{int(self.rng.integers(1, 999)):03d}",
            'Report Date': onset_date + timedelta(days=int(self.rng.integers(1, 7))),
            'Date of Onset': onset_date,
            'Adverse Event (diagnosis, if known, or signs/ symptoms)': ae_type,
            'SAE': 'Yes' if is_sae else 'No',
            'Severity': severity,
            'Causality: relationship to study medical device': self.rng.choice(
                ['Not Related', 'Possible', 'Probable'],
                p=[0.7, 0.2, 0.1]
            ),
            'Outcome': self.rng.choice(['Resolved', 'Resolving', 'Resolved with sequelae'], p=[0.6, 0.3, 0.1]),
            'is_synthetic': True,
        }

    def _generate_explant(
        self,
        patient_id: str,
        facility: str,
        surgery_date: date,
        is_early: bool
    ) -> Dict:
        """Generate revision/explant record."""

        if is_early:
            days_to_revision = int(self.rng.integers(7, 90))
        else:
            days_to_revision = int(self.rng.integers(180, 730))

        explant_date = surgery_date + timedelta(days=days_to_revision)

        # Components explanted depend on reason
        cup_explanted = self.rng.choice(['Yes', 'No'], p=[0.7, 0.3])
        stem_explanted = self.rng.choice(['Yes', 'No'], p=[0.4, 0.6])

        return {
            'Facility': facility,
            'Id': patient_id,
            'Explant date': explant_date,
            'Stem Explanted': stem_explanted,
            'Cup Explanted': cup_explanted,
            'Cup Liner Explanted': 'Yes' if cup_explanted == 'Yes' else 'No',
            'Head Explanted': self.rng.choice(['Yes', 'No']),
            'days_to_revision': days_to_revision,
            'is_synthetic': True,
        }

    def generate(self) -> Dict[str, pd.DataFrame]:
        """
        Generate complete synthetic dataset.

        Returns:
            Dictionary of DataFrames matching H-34 structure
        """
        logger.info(f"Generating {self.config.n_patients} synthetic patients...")

        # Reset storage
        self.patients = []
        self.preoperatives = []
        self.intraoperatives = []
        self.surgery_data = []
        self.hhs_scores = []
        self.ohs_scores = []
        self.adverse_events = []
        self.explants = []

        # Determine which patients will have revisions
        n_revisions = int(self.config.n_patients * self.config.revision_rate)
        revision_patient_indices = set(self.rng.choice(
            self.config.n_patients, size=n_revisions, replace=False
        ))

        # Determine which patients will have AEs (excluding revision patients who get their own)
        n_aes = int(self.config.n_patients * self.config.ae_rate)
        ae_patient_indices = set(self.rng.choice(
            self.config.n_patients, size=n_aes, replace=False
        ))

        for idx in range(self.config.n_patients):
            patient_id = self._generate_patient_id(idx + 1)

            # Demographics
            patient = self._generate_demographics(patient_id)
            self.patients.append(patient)

            facility = patient['Facility']
            surgery_date = self._generate_surgery_date()

            # Preoperative
            self.preoperatives.append(
                self._generate_preoperative(patient_id, facility, surgery_date)
            )

            # Intraoperative
            self.intraoperatives.append(
                self._generate_intraoperative(patient_id, facility, surgery_date)
            )

            # Surgery data
            self.surgery_data.append(
                self._generate_surgery_data(patient_id, facility)
            )

            # Determine if this patient has revision
            has_revision = idx in revision_patient_indices
            revision_day = None

            if has_revision:
                is_early = self.rng.random() < self.config.early_revision_ratio
                explant = self._generate_explant(patient_id, facility, surgery_date, is_early)
                self.explants.append(explant)
                revision_day = explant['days_to_revision']

                # Add revision-related AE
                self.adverse_events.append(
                    self._generate_adverse_event(patient_id, facility, surgery_date, is_revision_related=True)
                )

            # Generate HHS trajectory
            hhs = self._generate_hhs_trajectory(
                patient_id, facility, surgery_date, has_revision, revision_day
            )
            self.hhs_scores.extend(hhs)

            # Generate OHS trajectory (correlated with HHS)
            ohs = self._generate_ohs_trajectory(patient_id, facility, surgery_date, hhs)
            self.ohs_scores.extend(ohs)

            # Non-revision AEs
            if idx in ae_patient_indices and idx not in revision_patient_indices:
                self.adverse_events.append(
                    self._generate_adverse_event(patient_id, facility, surgery_date, is_revision_related=False)
                )

        # Convert to DataFrames
        result = {
            '1 Patients': pd.DataFrame(self.patients),
            '2 Preoperatives': pd.DataFrame(self.preoperatives),
            '4 Intraoperatives': pd.DataFrame(self.intraoperatives),
            '5 Surgery Data': pd.DataFrame(self.surgery_data),
            '17 Adverse Events V2': pd.DataFrame(self.adverse_events),
            '18 Score HHS': pd.DataFrame(self.hhs_scores),
            '19 Score OHS': pd.DataFrame(self.ohs_scores),
            '20 Explants': pd.DataFrame(self.explants),
        }

        # Log summary
        logger.info(f"Generated synthetic data summary:")
        logger.info(f"  Patients: {len(self.patients)}")
        logger.info(f"  HHS Scores: {len(self.hhs_scores)}")
        logger.info(f"  Adverse Events: {len(self.adverse_events)}")
        logger.info(f"  Revisions: {len(self.explants)}")

        return result

    def get_summary_stats(self) -> Dict:
        """Get summary statistics of generated data."""
        hhs_df = pd.DataFrame(self.hhs_scores)

        stats = {
            'total_patients': len(self.patients),
            'total_hhs_scores': len(self.hhs_scores),
            'total_adverse_events': len(self.adverse_events),
            'total_revisions': len(self.explants),
            'revision_rate': len(self.explants) / len(self.patients) * 100,
            'hhs_by_timepoint': {},
        }

        if len(hhs_df) > 0:
            for fu in hhs_df['Follow UP'].unique():
                subset = hhs_df[hhs_df['Follow UP'] == fu]['Total Score']
                stats['hhs_by_timepoint'][fu] = {
                    'n': len(subset),
                    'mean': round(subset.mean(), 1),
                    'std': round(subset.std(), 1),
                }

        return stats

    def save_to_excel(self, filepath: str) -> None:
        """Save generated data to Excel file matching H-34 format."""
        data = self.generate()

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Saved synthetic data to: {filepath}")


def generate_synthetic_h34(
    n_patients: int = 300,
    output_path: Optional[str] = None,
    random_seed: int = 42
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to generate synthetic H-34 data.

    Args:
        n_patients: Number of synthetic patients to generate
        output_path: Optional path to save Excel file
        random_seed: Random seed for reproducibility

    Returns:
        Dictionary of DataFrames with synthetic data
    """
    config = SyntheticConfig(n_patients=n_patients, random_seed=random_seed)
    generator = SyntheticH34Generator(config)
    data = generator.generate()

    if output_path:
        generator.save_to_excel(output_path)

    return data


if __name__ == "__main__":
    # Test generation
    logging.basicConfig(level=logging.INFO)

    generator = SyntheticH34Generator(SyntheticConfig(n_patients=300))
    data = generator.generate()

    print("\n" + "=" * 80)
    print("SYNTHETIC DATA GENERATION COMPLETE")
    print("=" * 80)

    stats = generator.get_summary_stats()
    print(f"\nPatients: {stats['total_patients']}")
    print(f"Revisions: {stats['total_revisions']} ({stats['revision_rate']:.1f}%)")
    print(f"Adverse Events: {stats['total_adverse_events']}")
    print(f"\nHHS Scores by Timepoint:")
    for fu, s in stats['hhs_by_timepoint'].items():
        print(f"  {fu}: n={s['n']}, mean={s['mean']}, std={s['std']}")
