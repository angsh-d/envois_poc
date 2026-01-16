"""
UC4 Risk Service for Clinical Intelligence Platform.

Orchestrates agents and ML model for patient risk stratification.
"""
import hashlib
import json
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

import numpy as np
import joblib

# Suppress sklearn feature name warnings (non-critical)
warnings.filterwarnings("ignore", message="X does not have valid feature names")

from app.agents.base_agent import AgentContext
from app.agents.safety_agent import SafetyAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.data_agent import get_study_data
from app.exceptions import LLMServiceError
from data.loaders.yaml_loader import get_hybrid_loader

logger = logging.getLogger(__name__)


class RiskModel:
    """
    XGBoost-based risk prediction model.

    Combines ML predictions with literature-derived hazard ratios
    for robust risk stratification.
    """

    # ML model feature columns (must match training)
    ML_FEATURE_COLUMNS = [
        'age', 'bmi', 'is_female', 'is_smoker', 'is_former_smoker',
        'has_osteoporosis', 'has_prior_surgery', 'bmi_over_30', 'bmi_over_35',
        'age_over_70', 'age_over_80', 'poor_bone_quality', 'surgery_duration_long'
    ]

    def __init__(self):
        """Initialize risk model with trained XGBoost model and load hazard ratios from YAML."""
        self._model = None
        self._scaler = None
        self._model_loaded = False
        self._hazard_ratios = self._load_hazard_ratios_from_yaml()
        self._feature_names = list(self._hazard_ratios.keys())
        self._load_trained_model()

    def _load_hazard_ratios_from_yaml(self) -> Dict[str, float]:
        """Load hazard ratios from literature_benchmarks.yaml."""
        doc_loader = get_hybrid_loader()
        try:
            lit_benchmarks = doc_loader.load_literature_benchmarks()
            # Extract pooled hazard ratios from risk_factor_summary
            hazard_ratios = {}
            for rf in lit_benchmarks.all_risk_factors:
                # Use factor name as key and hazard_ratio as value
                hazard_ratios[rf.factor] = rf.hazard_ratio

            # If we got hazard ratios from YAML, return them
            if hazard_ratios:
                logger.info(f"Loaded {len(hazard_ratios)} hazard ratios from literature_benchmarks.yaml")
                return hazard_ratios
        except Exception as e:
            logger.warning(f"Failed to load hazard ratios from YAML: {e}")

        # This should not happen if YAML is properly configured
        raise ValueError(
            "Failed to load hazard ratios from literature_benchmarks.yaml. "
            "Ensure the YAML file exists and contains risk_factor data."
        )

    @property
    def HAZARD_RATIOS(self) -> Dict[str, float]:
        """Get hazard ratios (loaded from YAML)."""
        return self._hazard_ratios

    def _load_trained_model(self):
        """Load pre-trained XGBoost model and scaler.

        NOTE: ML model is currently disabled because validation showed
        ROC-AUC of 0.51 (no better than random). Using clinical hazard
        ratios only until a properly trained model is available.
        """
        # DISABLED: ML model has AUC of 0.51 (random) - see model_metadata.json
        # This was causing high-risk patients to be misclassified because
        # random ML scores were diluting validated clinical hazard ratios.
        self._model_loaded = False
        logger.info("ML model disabled - using clinical hazard ratios only (AUC was 0.51)")
        return

        # Original code preserved for when a better model is trained:
        # model_dir = Path(__file__).parent.parent.parent / "data" / "ml"
        # model_path = model_dir / "risk_model.joblib"
        # scaler_path = model_dir / "risk_scaler.joblib"
        #
        # if model_path.exists() and scaler_path.exists():
        #     try:
        #         self._model = joblib.load(model_path)
        #         self._scaler = joblib.load(scaler_path)
        #         self._model_loaded = True
        #         logger.info(f"Loaded trained risk model from {model_path}")
        #     except Exception as e:
        #         logger.warning(f"Failed to load trained model: {e}")
        #         self._model_loaded = False
        # else:
        #     logger.warning(f"Trained model not found at {model_path}")
        #     self._model_loaded = False

    def _extract_ml_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Extract ML features from raw features dict."""
        ml_features = []
        for col in self.ML_FEATURE_COLUMNS:
            val = features.get(col, 0)
            if isinstance(val, bool):
                val = 1.0 if val else 0.0
            ml_features.append(float(val) if val is not None else 0.0)
        return np.array(ml_features).reshape(1, -1)

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict risk score for a patient using ensemble of ML + hazard ratios.

        Args:
            features: Patient features dictionary

        Returns:
            Risk prediction with score and contributing factors
        """
        # === ML Model Prediction ===
        ml_score = 0.5  # Default neutral score
        ml_confidence = 0.0

        if self._model_loaded and self._model is not None:
            try:
                ml_features = self._extract_ml_features(features)
                ml_features_scaled = self._scaler.transform(ml_features)
                ml_prob = self._model.predict_proba(ml_features_scaled)[0, 1]
                ml_score = float(ml_prob)
                ml_confidence = 1.0
                logger.debug(f"ML model prediction: {ml_score:.3f}")
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
                ml_confidence = 0.0

        # === Literature Hazard Ratio Calculation (Clinical Factors) ===
        clinical_factors = []
        combined_hr = 1.0

        # Map features to hazard ratio factors
        hr_mapping = {
            "age_over_80": features.get("age_over_80", False) or (features.get("age", 0) >= 80),
            "bmi_over_35": features.get("bmi_over_35", False) or (features.get("bmi", 0) >= 35),
            "diabetes": features.get("diabetes", False),
            "osteoporosis": features.get("has_osteoporosis", False) or features.get("osteoporosis", False),
            "rheumatoid_arthritis": features.get("rheumatoid_arthritis", False),
            "chronic_kidney_disease": features.get("chronic_kidney_disease", False),
            "smoking": features.get("is_smoker", False) or features.get("smoking", False),
            "prior_revision": features.get("has_prior_surgery", False) or features.get("prior_revision", False),
            "severe_bone_loss": features.get("poor_bone_quality", False) or features.get("severe_bone_loss", False),
            "paprosky_3b": features.get("paprosky_3b", False),
        }

        for factor, hr in self.HAZARD_RATIOS.items():
            if hr_mapping.get(factor, False):
                clinical_factors.append({
                    "factor": factor,
                    "hazard_ratio": hr,
                    "contribution": hr - 1.0,
                    "category": "clinical",
                })
                combined_hr *= hr

        # Convert combined HR to score (0-1 scale)
        hr_score = min(0.95, max(0.05, (combined_hr - 1) / 5))

        # === Demographic Factors (from ML model features) ===
        demographic_factors = []
        
        # Age contribution
        age = features.get("age")
        if age is not None and age >= 65:
            age_impact = "moderate" if age < 75 else "high"
            demographic_factors.append({
                "factor": f"age_{int(age)}",
                "display_name": f"Age {int(age)}",
                "value": int(age),
                "impact": age_impact,
                "category": "demographic",
            })
        
        # BMI contribution
        bmi = features.get("bmi")
        if bmi is not None and bmi >= 25:
            if bmi >= 35:
                bmi_impact = "high"
            elif bmi >= 30:
                bmi_impact = "moderate"
            else:
                bmi_impact = "low"
            demographic_factors.append({
                "factor": f"bmi_{bmi:.1f}",
                "display_name": f"BMI {bmi:.1f}",
                "value": round(bmi, 1),
                "impact": bmi_impact,
                "category": "demographic",
            })
        
        # Gender (if female, slight statistical risk difference)
        if features.get("is_female"):
            demographic_factors.append({
                "factor": "female",
                "display_name": "Female",
                "value": True,
                "impact": "low",
                "category": "demographic",
            })

        # === Ensemble Score ===
        # Weight: 60% ML score, 40% HR score (if ML model loaded)
        if self._model_loaded and ml_confidence > 0:
            ensemble_score = 0.6 * ml_score + 0.4 * hr_score
        else:
            ensemble_score = hr_score

        # Determine risk level
        if ensemble_score >= 0.6:
            risk_level = "high"
        elif ensemble_score >= 0.3:
            risk_level = "moderate"
        else:
            risk_level = "low"

        # Combine all contributing factors for backward compatibility
        all_factors = clinical_factors.copy()

        return {
            "risk_score": round(ensemble_score, 3),
            "risk_level": risk_level,
            "ml_score": round(ml_score, 3) if ml_confidence > 0 else None,
            "hr_score": round(hr_score, 3),
            "clinical_risk_score": round(hr_score, 3),
            "demographic_risk_score": round(ml_score, 3) if ml_confidence > 0 else None,
            "combined_hazard_ratio": round(combined_hr, 2),
            "n_risk_factors": len(clinical_factors),
            "n_demographic_factors": len(demographic_factors),
            "contributing_factors": all_factors,
            "clinical_factors": clinical_factors,
            "demographic_factors": demographic_factors,
            "model_loaded": self._model_loaded,
        }

    def get_population_risk_distribution(
        self,
        patients: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get risk distribution across patient population.

        Args:
            patients: List of patient feature dictionaries

        Returns:
            Population risk statistics
        """
        if not patients:
            return {"error": "No patients provided"}

        scores = []
        levels = {"low": 0, "moderate": 0, "high": 0}

        for patient in patients:
            prediction = self.predict(patient)
            scores.append(prediction["risk_score"])
            levels[prediction["risk_level"]] += 1

        return {
            "n_patients": len(patients),
            "mean_risk_score": round(np.mean(scores), 3),
            "median_risk_score": round(np.median(scores), 3),
            "std_risk_score": round(np.std(scores), 3),
            "risk_distribution": levels,
            "high_risk_pct": round(levels["high"] / len(patients) * 100, 1),
        }


class RiskService:
    """
    Service for UC4: Risk Stratification.

    Combines ML model predictions with literature evidence
    for patient-level risk assessment.
    """

    def __init__(self):
        """Initialize risk service."""
        self._risk_model = RiskModel()
        self._safety_agent = SafetyAgent()
        self._literature_agent = LiteratureAgent()
        self._synthesis_agent = SynthesisAgent()
        self._doc_loader = get_hybrid_loader()
        # Cache for LLM-extracted risk factors (avoids redundant API calls)
        self._extraction_cache: Dict[str, Dict[str, bool]] = {}

    def _get_cache_key(
        self,
        medical_history: Optional[str],
        smoking_habits: Optional[str],
        osteoporosis: Optional[str],
        primary_diagnosis: Optional[str]
    ) -> str:
        """Generate cache key from input text fields."""
        content = f"{medical_history}|{smoking_habits}|{osteoporosis}|{primary_diagnosis}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _extract_risk_factors_llm(
        self,
        medical_history: Optional[str],
        smoking_habits: Optional[str],
        osteoporosis: Optional[str],
        primary_diagnosis: Optional[str]
    ) -> Dict[str, bool]:
        """
        Extract risk factors from free-text fields using Gemini Flash.

        Uses LLM to semantically extract risk factors from medical history,
        handling abbreviations and variations (DM, T2DM, diabetes, etc.).

        Returns:
            Dict with boolean flags for each risk factor.
        """
        # Check cache first
        cache_key = self._get_cache_key(medical_history, smoking_habits, osteoporosis, primary_diagnosis)
        if cache_key in self._extraction_cache:
            logger.debug(f"Using cached extraction for key {cache_key[:8]}...")
            return self._extraction_cache[cache_key]

        # Import services lazily to avoid circular imports
        from app.services.llm_service import get_llm_service
        from app.services.prompt_service import get_prompt_service

        try:
            prompt_service = get_prompt_service()
            prompt = prompt_service.load(
                "risk_factor_extraction_patient",
                {
                    "medical_history": medical_history or "None",
                    "smoking_habits": smoking_habits or "None",
                    "osteoporosis": osteoporosis or "None",
                    "primary_diagnosis": primary_diagnosis or "None",
                }
            )

            llm = get_llm_service()
            response = await llm.generate(
                prompt=prompt,
                model="gemini-2.5-flash",
                temperature=0.0,  # Deterministic extraction
                max_tokens=1024  # Generous limit to avoid truncation
            )

            # Parse JSON response (handle markdown code blocks)
            response_text = response.strip()

            if "```json" in response_text:
                # Extract content between ```json and ```
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif response_text.startswith("```"):
                # Generic code block
                lines = response_text.split("\n")
                # Remove first line (```) and last line if it's ```
                response_text = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                ).strip()

            result = json.loads(response_text)

            # Cache the result
            self._extraction_cache[cache_key] = result
            logger.debug(f"LLM extracted risk factors: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise LLMServiceError(
                f"LLM returned invalid JSON for risk factor extraction: {e}. "
                "Check LLM service configuration and prompt format."
            )
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise LLMServiceError(
                f"Risk factor extraction via LLM failed: {e}. "
                "Ensure LLM service is properly configured."
            )

    async def get_patient_risk(self, patient_id: str) -> Dict[str, Any]:
        """
        Get comprehensive risk assessment for a patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Dict with risk score, factors, and recommendations
        """
        request_id = str(uuid.uuid4())

        # Get patient safety data (includes risk factors)
        safety_context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            parameters={"query_type": "patient"}
        )
        safety_result = await self._safety_agent.run(safety_context)

        if not safety_result.success:
            return {
                "success": False,
                "patient_id": patient_id,
                "error": safety_result.error,
            }

        safety_data = safety_result.data

        # Build features from safety data
        features = self._extract_features(safety_data)

        # Get ML prediction
        prediction = self._risk_model.predict(features)

        # Get literature context for risk factors
        lit_context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "risk_factors",
                "outcome": "revision"
            }
        )
        literature_result = await self._literature_agent.run(lit_context)

        # Generate recommendations
        recommendations = self._generate_recommendations(prediction)

        # Synthesize narrative
        synthesis_context = AgentContext(
            request_id=request_id,
            patient_id=patient_id,
            parameters={"synthesis_type": "uc4_risk"},
            shared_data={
                "safety": safety_result.to_dict(),
                "literature": literature_result.to_dict() if literature_result.success else {},
            }
        )
        synthesis_result = await self._synthesis_agent.run(synthesis_context)

        return {
            "success": True,
            "patient_id": patient_id,
            "assessment_date": datetime.utcnow().isoformat(),
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "combined_hazard_ratio": prediction["combined_hazard_ratio"],
            "n_risk_factors": prediction["n_risk_factors"],
            "contributing_factors": prediction["contributing_factors"],
            "recommendations": recommendations,
            "narrative": synthesis_result.narrative if synthesis_result.success else None,
            "sources": [s.to_dict() for s in safety_result.sources],
            "execution_time_ms": safety_result.execution_time_ms,
        }

    async def get_population_risk(self) -> Dict[str, Any]:
        """
        Get risk distribution across the study population.

        Returns:
            Dict with population risk statistics including per-tier cohorts
        """
        # Load actual patient data from study
        study_data = get_study_data()

        if not study_data.patients:
            return {
                "success": False,
                "error": "No patient data available",
                "assessment_date": datetime.utcnow().isoformat(),
            }

        # Extract features for each patient and calculate risk
        patient_features_list = []
        high_risk_patients = []
        moderate_risk_patients = []
        low_risk_patients = []
        
        # Track factor prevalence across population
        factor_counts: Dict[str, int] = {}

        for patient in study_data.patients:
            # Build patient features from demographics and medical history (async LLM extraction)
            features = await self._build_patient_features(patient, study_data)
            patient_features_list.append(features)

            # Get individual prediction
            prediction = self._risk_model.predict(features)
            
            # Count factor prevalence
            for factor_info in prediction["contributing_factors"]:
                factor_name = factor_info["factor"]
                factor_counts[factor_name] = factor_counts.get(factor_name, 0) + 1
            
            # Build patient detail object
            patient_detail = {
                "patient_id": patient.patient_id,
                "risk_score": prediction["risk_score"],
                "clinical_risk_score": prediction.get("clinical_risk_score", prediction["hr_score"]),
                "demographic_risk_score": prediction.get("demographic_risk_score"),
                "n_risk_factors": prediction["n_risk_factors"],
                "n_demographic_factors": prediction.get("n_demographic_factors", 0),
                "contributing_factors": prediction["contributing_factors"],
                "clinical_factors": prediction.get("clinical_factors", []),
                "demographic_factors": prediction.get("demographic_factors", []),
                "recommendations": self._generate_recommendations(prediction),
            }

            if prediction["risk_level"] == "high":
                high_risk_patients.append(patient_detail)
            elif prediction["risk_level"] == "moderate":
                moderate_risk_patients.append(patient_detail)
            else:
                low_risk_patients.append(patient_detail)

        # Get population distribution
        population_stats = self._risk_model.get_population_risk_distribution(patient_features_list)
        
        # Sort patients by risk score (highest first)
        high_risk_patients.sort(key=lambda x: x["risk_score"], reverse=True)
        moderate_risk_patients.sort(key=lambda x: x["risk_score"], reverse=True)
        low_risk_patients.sort(key=lambda x: x["risk_score"], reverse=True)
        
        # Build factor prevalence list
        n_patients = len(study_data.patients)
        factor_prevalence = [
            {
                "factor": factor,
                "count": count,
                "percentage": round(count / n_patients * 100, 1),
                "hazard_ratio": self._risk_model.HAZARD_RATIOS.get(factor, 1.0)
            }
            for factor, count in sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "success": True,
            "assessment_date": datetime.utcnow().isoformat(),
            "n_patients": population_stats.get("n_patients", n_patients),
            "risk_distribution": population_stats.get("risk_distribution", {}),
            "high_risk_patients": high_risk_patients,
            "moderate_risk_patients": moderate_risk_patients,
            "low_risk_patients": low_risk_patients,
            "high_risk_count": len(high_risk_patients),
            "moderate_risk_count": len(moderate_risk_patients),
            "low_risk_count": len(low_risk_patients),
            "high_risk_pct": population_stats.get("high_risk_pct", 0),
            "mean_risk_score": population_stats.get("mean_risk_score", 0),
            "median_risk_score": population_stats.get("median_risk_score", 0),
            "std_risk_score": population_stats.get("std_risk_score", 0),
            "factor_prevalence": factor_prevalence,
        }

    async def _build_patient_features(self, patient, study_data) -> Dict[str, Any]:
        """
        Build risk model features from patient data using LLM extraction.

        Args:
            patient: Patient object from study data
            study_data: Full H34StudyData object

        Returns:
            Dictionary of features for risk model
        """
        features = {}

        # Demographics (numeric - no NLP needed)
        current_year = datetime.now().year
        age = current_year - patient.year_of_birth if patient.year_of_birth else None
        features["age"] = age
        features["age_over_70"] = age >= 70 if age else False
        features["age_over_80"] = age >= 80 if age else False

        features["bmi"] = patient.bmi
        features["bmi_over_30"] = patient.bmi >= 30 if patient.bmi else False
        features["bmi_over_35"] = patient.bmi >= 35 if patient.bmi else False

        features["is_female"] = patient.gender and patient.gender.lower() in ["female", "f"]

        # Get preoperative data for comorbidities - use merged data from Patient first
        # (medical_history and primary_diagnosis are now merged into Patient model)
        preop = None
        for p in study_data.preoperatives:
            if p.patient_id == patient.patient_id:
                preop = p
                break

        # Use patient-level medical_history (preferred) or fall back to preop
        medical_history = getattr(patient, 'medical_history', None) or (preop.medical_history if preop else None)
        primary_diagnosis = getattr(patient, 'primary_diagnosis', None) or (preop.primary_diagnosis if preop else None)
        osteoporosis_field = preop.osteoporosis if preop else None

        # LLM-based extraction for text fields (smoking, medical history, etc.)
        llm_factors = await self._extract_risk_factors_llm(
            medical_history=medical_history,
            smoking_habits=patient.smoking_habits,
            osteoporosis=osteoporosis_field,
            primary_diagnosis=primary_diagnosis,
        )

        # Map LLM results to feature names
        features["is_smoker"] = llm_factors.get("smoking_current", False)
        features["smoking"] = features["is_smoker"]
        features["is_former_smoker"] = llm_factors.get("smoking_former", False)
        features["diabetes"] = llm_factors.get("diabetes", False)
        features["has_osteoporosis"] = llm_factors.get("osteoporosis", False)
        features["osteoporosis"] = features["has_osteoporosis"]
        features["rheumatoid_arthritis"] = llm_factors.get("rheumatoid_arthritis", False)
        features["chronic_kidney_disease"] = llm_factors.get("chronic_kidney_disease", False)

        # Prior surgery (structured field - pattern matching is appropriate)
        if preop:
            prior = (preop.previous_hip_surgery_affected or "").lower()
            features["has_prior_surgery"] = prior != "" and prior != "no" and prior != "none"
            features["prior_revision"] = features["has_prior_surgery"]
        else:
            features["has_prior_surgery"] = False
            features["prior_revision"] = False

        # Get intraoperative data for bone quality
        intraop = None
        for i in study_data.intraoperatives:
            if i.patient_id == patient.patient_id:
                intraop = i
                break

        if intraop:
            bone_quality = (intraop.acetabulum_bone_quality or "").lower()
            features["poor_bone_quality"] = "poor" in bone_quality or "severe" in bone_quality
            features["severe_bone_loss"] = features["poor_bone_quality"]
        else:
            features["poor_bone_quality"] = False
            features["severe_bone_loss"] = False

        # Get surgery data for duration
        surgery = None
        for s in study_data.surgery_data:
            if s.patient_id == patient.patient_id:
                surgery = s
                break

        if surgery and surgery.surgery_time_minutes:
            features["surgery_duration_long"] = surgery.surgery_time_minutes > 180
        else:
            features["surgery_duration_long"] = False

        # Additional factors (default to False if not available)
        features["paprosky_3b"] = False  # Would need specific bone defect classification

        return features

    async def get_risk_factors(self) -> Dict[str, Any]:
        """
        Get all literature-derived risk factors with hazard ratios.

        Returns:
            Dict with risk factor definitions
        """
        request_id = str(uuid.uuid4())

        lit_context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "risk_factors",
                "outcome": "revision"
            }
        )
        literature_result = await self._literature_agent.run(lit_context)

        # Also include model's hazard ratios
        model_factors = [
            {
                "factor": factor,
                "hazard_ratio": hr,
                "source": "literature_aggregate",
            }
            for factor, hr in self._risk_model.HAZARD_RATIOS.items()
        ]

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "model_factors": model_factors,
            "literature_factors": literature_result.data.get("factors", []) if literature_result.success else [],
            "sources": [s.to_dict() for s in literature_result.sources] if literature_result.success else [],
        }

    async def calculate_risk(self, features: Dict[str, bool]) -> Dict[str, Any]:
        """
        Calculate risk score from provided features.

        Args:
            features: Dict of risk factor presence (factor_name: bool)

        Returns:
            Risk prediction
        """
        prediction = self._risk_model.predict(features)

        return {
            "success": True,
            "calculated_at": datetime.utcnow().isoformat(),
            "input_features": features,
            **prediction,
            "recommendations": self._generate_recommendations(prediction),
        }

    def _extract_features(self, safety_data: Dict[str, Any]) -> Dict[str, bool]:
        """Extract model features from safety data."""
        features = {}

        # Map safety data risk factors to model features
        for rf in safety_data.get("risk_factors", []):
            factor = rf.get("factor", "")
            features[factor] = rf.get("present", False)

        return features

    def _generate_recommendations(self, prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on risk prediction."""
        recommendations = []
        risk_level = prediction.get("risk_level", "low")

        if risk_level == "high":
            recommendations.append({
                "action": "Enhanced post-operative monitoring protocol",
                "rationale": f"High risk score ({prediction['risk_score']:.2f}) with {prediction['n_risk_factors']} risk factors",
                "priority": "high",
            })
            recommendations.append({
                "action": "Consider earlier imaging follow-up",
                "rationale": "Early detection of potential complications",
                "priority": "high",
            })
            recommendations.append({
                "action": "Bone health optimization if osteoporosis present",
                "rationale": "Reduce fracture and loosening risk",
                "priority": "medium",
            })

        elif risk_level == "moderate":
            recommendations.append({
                "action": "Standard monitoring with heightened awareness",
                "rationale": f"Moderate risk score ({prediction['risk_score']:.2f})",
                "priority": "medium",
            })
            recommendations.append({
                "action": "Address modifiable risk factors",
                "rationale": "Risk factor optimization",
                "priority": "medium",
            })

        else:
            recommendations.append({
                "action": "Standard follow-up protocol",
                "rationale": f"Low risk score ({prediction['risk_score']:.2f})",
                "priority": "low",
            })

        return recommendations

    def get_hazard_ratio(self, factor: str) -> Optional[float]:
        """Get hazard ratio for a specific risk factor."""
        return self._risk_model.HAZARD_RATIOS.get(factor)


# Singleton instance
_risk_service: Optional[RiskService] = None


def get_risk_service() -> RiskService:
    """Get singleton risk service instance."""
    global _risk_service
    if _risk_service is None:
        _risk_service = RiskService()
    return _risk_service
