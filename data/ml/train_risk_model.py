"""
Training script for XGBoost risk prediction model.

Combines real H-34 study data with synthetic data to train a model
for predicting revision/complication risk in hip revision arthroplasty.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, average_precision_score
)
import xgboost as xgb
import joblib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loaders.excel_loader import H34ExcelLoader
from data.models.unified_schema import H34StudyData, Patient, Preoperative, Intraoperative, AdverseEvent
from app.config import Settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RiskModelTrainer:
    """
    Trains XGBoost model for revision/complication risk prediction.

    Features extracted from:
    - Patient demographics (age, BMI, gender, smoking)
    - Preoperative data (osteoporosis, prior surgery)
    - Intraoperative data (bone quality, surgery time)
    """

    FEATURE_COLUMNS = [
        'age', 'bmi', 'is_female', 'is_smoker', 'is_former_smoker',
        'has_osteoporosis', 'has_prior_surgery', 'bmi_over_30', 'bmi_over_35',
        'age_over_70', 'age_over_80', 'poor_bone_quality', 'surgery_duration_long'
    ]

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize trainer."""
        self.settings = settings or Settings()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}

    def load_data(self) -> Tuple[H34StudyData, H34StudyData]:
        """Load real and synthetic study data."""
        logger.info("Loading study data...")

        real_loader = H34ExcelLoader(self.settings.get_h34_study_data_path())
        real_data = real_loader.load()
        logger.info(f"Loaded {len(real_data.patients)} real patients")

        synth_loader = H34ExcelLoader(self.settings.get_h34_synthetic_data_path())
        synth_data = synth_loader.load()
        logger.info(f"Loaded {len(synth_data.patients)} synthetic patients")

        return real_data, synth_data

    def extract_features(
        self,
        patient: Patient,
        preop: Optional[Preoperative],
        intraop: Optional[Intraoperative],
        surgery_time: Optional[int]
    ) -> Dict[str, float]:
        """Extract ML features from patient data."""
        features = {}

        # Age (from year of birth)
        if patient.year_of_birth:
            age = datetime.now().year - patient.year_of_birth
        else:
            age = 65  # Default median age
        features['age'] = age
        features['age_over_70'] = 1.0 if age >= 70 else 0.0
        features['age_over_80'] = 1.0 if age >= 80 else 0.0

        # BMI
        bmi = patient.bmi or 27.0  # Default median BMI
        features['bmi'] = bmi
        features['bmi_over_30'] = 1.0 if bmi >= 30 else 0.0
        features['bmi_over_35'] = 1.0 if bmi >= 35 else 0.0

        # Gender
        gender = (patient.gender or '').lower()
        features['is_female'] = 1.0 if 'female' in gender else 0.0

        # Smoking
        smoking = (patient.smoking_habits or '').lower()
        features['is_smoker'] = 1.0 if 'current' in smoking or smoking == 'yes' else 0.0
        features['is_former_smoker'] = 1.0 if 'former' in smoking or 'ex' in smoking else 0.0

        # Preoperative factors
        if preop:
            osteo = (preop.osteoporosis or '').lower()
            features['has_osteoporosis'] = 1.0 if 'yes' in osteo else 0.0

            prior_affected = (preop.previous_hip_surgery_affected or '').lower()
            prior_contra = (preop.previous_hip_surgery_contralateral or '').lower()
            features['has_prior_surgery'] = 1.0 if 'yes' in prior_affected or 'yes' in prior_contra else 0.0
        else:
            features['has_osteoporosis'] = 0.0
            features['has_prior_surgery'] = 0.0

        # Intraoperative factors
        if intraop:
            bone_quality = (intraop.acetabulum_bone_quality or '').lower()
            features['poor_bone_quality'] = 1.0 if 'poor' in bone_quality or 'severe' in bone_quality else 0.0
        else:
            features['poor_bone_quality'] = 0.0

        # Surgery duration
        if surgery_time and surgery_time > 0:
            features['surgery_duration_long'] = 1.0 if surgery_time > 120 else 0.0  # >2 hours
        else:
            features['surgery_duration_long'] = 0.0

        return features

    def create_label(
        self,
        patient_id: str,
        adverse_events: List[AdverseEvent]
    ) -> int:
        """
        Create binary label for risk prediction.

        High risk (1) if:
        - Device was removed (revision)
        - Patient had a Serious Adverse Event (SAE)
        - Severe adverse event related to device
        """
        patient_aes = [ae for ae in adverse_events if ae.patient_id == patient_id]

        for ae in patient_aes:
            # Revision (device removed)
            if ae.device_removed and ae.device_removed.lower() == 'yes':
                return 1

            # Serious adverse event
            if ae.is_sae and ae.is_sae.lower() == 'yes':
                return 1

            # Severe AE related to device
            severity = (ae.severity or '').lower()
            device_rel = (ae.device_relationship or '').lower()
            if severity == 'severe' and device_rel in ('probable', 'possible'):
                return 1

        return 0

    def build_dataset(
        self,
        real_data: H34StudyData,
        synth_data: H34StudyData
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Build feature matrix and labels from study data."""
        logger.info("Building dataset...")

        features_list = []
        labels_list = []

        # Process real data
        for patient in real_data.patients:
            pid = patient.patient_id
            preop = next((p for p in real_data.preoperatives if p.patient_id == pid), None)
            intraop = next((i for i in real_data.intraoperatives if i.patient_id == pid), None)
            surgery = next((s for s in real_data.surgery_data if s.patient_id == pid), None)
            surgery_time = surgery.surgery_time_minutes if surgery else None

            features = self.extract_features(patient, preop, intraop, surgery_time)
            label = self.create_label(pid, real_data.adverse_events)

            features_list.append(features)
            labels_list.append(label)

        # Process synthetic data
        for patient in synth_data.patients:
            pid = patient.patient_id
            preop = next((p for p in synth_data.preoperatives if p.patient_id == pid), None)
            intraop = next((i for i in synth_data.intraoperatives if i.patient_id == pid), None)
            surgery = next((s for s in synth_data.surgery_data if s.patient_id == pid), None)
            surgery_time = surgery.surgery_time_minutes if surgery else None

            features = self.extract_features(patient, preop, intraop, surgery_time)
            label = self.create_label(pid, synth_data.adverse_events)

            features_list.append(features)
            labels_list.append(label)

        X = pd.DataFrame(features_list)
        y = pd.Series(labels_list)

        logger.info(f"Dataset: {len(X)} samples, {sum(y)} positive cases ({100*sum(y)/len(y):.1f}%)")

        return X, y

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """Train XGBoost model with cross-validation."""
        logger.info("Training XGBoost model...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Calculate scale_pos_weight for imbalanced data
        n_neg = sum(y_train == 0)
        n_pos = sum(y_train == 1)
        scale_pos_weight = n_neg / max(n_pos, 1)

        # XGBoost parameters
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 4,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': scale_pos_weight,
            'random_state': 42,
            'use_label_encoder': False
        }

        # Train model
        self.model = xgb.XGBClassifier(**params)
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )

        # Cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=cv, scoring='roc_auc'
        )

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_prob = self.model.predict_proba(X_test_scaled)[:, 1]

        # Feature importance
        for i, col in enumerate(X.columns):
            self.feature_importance[col] = float(self.model.feature_importances_[i])

        # Sort feature importance
        self.feature_importance = dict(
            sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
        )

        # Metrics
        metrics = {
            'roc_auc': roc_auc_score(y_test, y_prob),
            'cv_auc_mean': float(cv_scores.mean()),
            'cv_auc_std': float(cv_scores.std()),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'n_train': len(X_train),
            'n_test': len(X_test),
            'n_positive_train': int(sum(y_train)),
            'n_positive_test': int(sum(y_test)),
            'feature_importance': self.feature_importance,
        }

        logger.info(f"ROC AUC: {metrics['roc_auc']:.3f}")
        logger.info(f"CV AUC: {metrics['cv_auc_mean']:.3f} (+/- {metrics['cv_auc_std']:.3f})")
        logger.info(f"Top features: {list(self.feature_importance.items())[:5]}")

        return metrics

    def save_model(self, model_dir: Path) -> Tuple[Path, Path]:
        """Save trained model and scaler."""
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = model_dir / 'risk_model.joblib'
        scaler_path = model_dir / 'risk_scaler.joblib'

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

        logger.info(f"Saved model to: {model_path}")
        logger.info(f"Saved scaler to: {scaler_path}")

        return model_path, scaler_path

    def save_metadata(self, model_dir: Path, metrics: Dict[str, Any]) -> Path:
        """Save model metadata."""
        import json

        metadata = {
            'trained_at': datetime.utcnow().isoformat(),
            'feature_columns': self.FEATURE_COLUMNS,
            'metrics': metrics,
        }

        metadata_path = model_dir / 'model_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info(f"Saved metadata to: {metadata_path}")
        return metadata_path


def main():
    """Train and save risk model."""
    settings = Settings()
    trainer = RiskModelTrainer(settings)

    # Load data
    real_data, synth_data = trainer.load_data()

    # Build dataset
    X, y = trainer.build_dataset(real_data, synth_data)

    # Train model
    metrics = trainer.train(X, y)

    # Save model
    model_dir = Path(__file__).parent
    trainer.save_model(model_dir)
    trainer.save_metadata(model_dir, metrics)

    print("\n" + "=" * 60)
    print("Risk Model Training Complete")
    print("=" * 60)
    print(f"Samples: {len(X)} ({sum(y)} positive)")
    print(f"ROC AUC: {metrics['roc_auc']:.3f}")
    print(f"CV AUC: {metrics['cv_auc_mean']:.3f} (+/- {metrics['cv_auc_std']:.3f})")
    print("\nTop Risk Factors:")
    for i, (feat, imp) in enumerate(trainer.feature_importance.items()):
        if i >= 5:
            break
        print(f"  {feat}: {imp:.3f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
