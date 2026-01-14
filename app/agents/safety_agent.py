"""
Safety Agent for Clinical Intelligence Platform.

Responsible for safety signal detection and risk factor analysis.
"""
import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType,
    ConfidenceLevel, CONFIDENCE_THRESHOLDS
)
from app.agents.protocol_agent import ProtocolAgent
from app.agents.data_agent import DataAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.registry_agent import RegistryAgent

logger = logging.getLogger(__name__)


def _get_affected_patients_from_db(event_pattern: str) -> List[Dict[str, Any]]:
    """
    Query database for patients affected by a specific adverse event type.
    
    Returns list of patient info with demographics for provenance.
    """
    try:
        from sqlalchemy import text
        from data.models.database import SessionLocal
        
        if SessionLocal is None:
            return []
            
        session = SessionLocal()
        try:
            query = text("""
                SELECT 
                    p.patient_id,
                    ae.ae_title,
                    ae.severity,
                    ae.onset_date,
                    ae.is_sae,
                    p.gender,
                    EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth as age,
                    p.bmi,
                    p.primary_diagnosis
                FROM study_adverse_events ae
                JOIN study_patients p ON ae.patient_id = p.id
                WHERE LOWER(ae.ae_title) LIKE :pattern
                ORDER BY ae.onset_date
            """)
            result = session.execute(query, {"pattern": f"%{event_pattern.lower()}%"})
            
            patients = []
            for row in result:
                patients.append({
                    "patient_id": row.patient_id,
                    "event_description": row.ae_title,
                    "severity": row.severity,
                    "event_date": row.onset_date.isoformat() if row.onset_date else None,
                    "is_sae": row.is_sae,
                    "demographics": {
                        "gender": row.gender,
                        "age": int(row.age) if row.age else None,
                        "bmi": round(row.bmi, 1) if row.bmi else None,
                        "diagnosis": row.primary_diagnosis,
                    }
                })
            return patients
        finally:
            session.close()
    except Exception as e:
        logger.warning(f"Could not fetch affected patients: {e}")
        return []


def _get_literature_citations(metric_name: str) -> List[Dict[str, Any]]:
    """
    Get literature citations for a specific metric from database.
    Uses the new provenance-based data structure.
    """
    try:
        from sqlalchemy import text
        from data.models.database import SessionLocal
        
        if SessionLocal is None:
            return []
            
        session = SessionLocal()
        try:
            query = text("""
                SELECT 
                    publication_id,
                    title,
                    year,
                    journal,
                    n_patients,
                    benchmarks
                FROM literature_publications
                ORDER BY year DESC
            """)
            result = session.execute(query)
            
            citations = []
            for row in result:
                benchmarks = row.benchmarks or {}
                survival_rates = benchmarks.get("survival_rates", [])
                
                relevant_rate = None
                provenance = None
                
                for surv in survival_rates:
                    metric = (surv.get("metric", "") or "").lower()
                    if metric_name == "revision_rate" and ("revision" in metric or "survival" in metric):
                        relevant_rate = surv.get("value")
                        provenance = surv.get("provenance", {})
                        break
                    elif metric_name == "dislocation_rate" and "dislocation" in metric:
                        relevant_rate = surv.get("value")
                        provenance = surv.get("provenance", {})
                        break
                    elif metric_name == "infection_rate" and "infection" in metric:
                        relevant_rate = surv.get("value")
                        provenance = surv.get("provenance", {})
                        break
                    elif metric_name == "fracture_rate" and "fracture" in metric:
                        relevant_rate = surv.get("value")
                        provenance = surv.get("provenance", {})
                        break
                    elif "complication" in metric or "implant_survival" in metric:
                        relevant_rate = surv.get("value")
                        provenance = surv.get("provenance", {})
                
                authors = benchmarks.get("authors", "")
                doi = benchmarks.get("doi", "")
                
                citations.append({
                    "citation_id": row.publication_id,
                    "title": row.title,
                    "year": row.year,
                    "journal": row.journal,
                    "n_patients": row.n_patients,
                    "authors": authors,
                    "doi": doi,
                    "reported_rate": relevant_rate,
                    "provenance": provenance,
                    "reference": f"{authors.split(',')[0] if authors else 'Unknown'} et al. ({row.year})",
                })
            return citations
        finally:
            session.close()
    except Exception as e:
        logger.warning(f"Could not fetch literature citations: {e}")
        return []


def _get_registry_breakdown() -> List[Dict[str, Any]]:
    """
    Get all registry benchmarks for comparison breakdown.
    """
    try:
        from sqlalchemy import text
        from data.models.database import SessionLocal
        
        if SessionLocal is None:
            return []
            
        session = SessionLocal()
        try:
            query = text("""
                SELECT 
                    registry_id,
                    name,
                    abbreviation,
                    report_year,
                    n_procedures,
                    revision_rate_2yr,
                    survival_2yr
                FROM registry_benchmarks
                ORDER BY n_procedures DESC
            """)
            result = session.execute(query)
            
            registries = []
            for row in result:
                registries.append({
                    "registry_id": row.registry_id,
                    "name": row.name,
                    "abbreviation": row.abbreviation,
                    "report_year": row.report_year,
                    "n_procedures": row.n_procedures,
                    "revision_rate_2yr": row.revision_rate_2yr,
                    "survival_2yr": row.survival_2yr,
                })
            return registries
        finally:
            session.close()
    except Exception as e:
        logger.warning(f"Could not fetch registry breakdown: {e}")
        return []


class SafetyAgent(BaseAgent):
    """
    Agent for safety signal detection and analysis.

    Capabilities:
    - Detect safety signals (revision, dislocation, infection, fracture)
    - Compare rates against protocol thresholds
    - Compare rates against registry benchmarks
    - Identify patients with elevated risk factors
    - Generate safety narratives with recommendations
    """

    agent_type = AgentType.SAFETY

    def __init__(self, **kwargs):
        """Initialize safety agent."""
        super().__init__(**kwargs)
        self._protocol_agent = ProtocolAgent()
        self._data_agent = DataAgent()
        self._literature_agent = LiteratureAgent()
        self._registry_agent = RegistryAgent()

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute safety analysis.

        Args:
            context: Execution context with analysis parameters

        Returns:
            AgentResult with safety findings
        """
        query_type = context.parameters.get("query_type", "study")

        # Execute the appropriate analysis
        if query_type == "study":
            data = await self._analyze_study_safety(context)
        elif query_type == "patient":
            data = await self._analyze_patient_safety(context)
        elif query_type == "signals":
            data = await self._detect_signals(context)
        elif query_type == "trends":
            data = await self._analyze_trends(context)
        else:
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=f"Unknown query_type: {query_type}",
            )

        # Check for error or insufficient data
        if data.get("error"):
            return AgentResult.insufficient_data(
                agent_type=self.agent_type,
                reason=data["error"],
                data_gaps=self._identify_data_gaps(data, query_type),
                available_data={"query_type": query_type}
            )

        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
            data=data,
        )

        # Add sources with proper provenance
        result.add_source(
            SourceType.STUDY_DATA,
            "H-34 Study Database",
            confidence=1.0,
            details={"n_patients": data.get("n_patients", 0)}
        )
        result.add_source(
            SourceType.PROTOCOL,
            "protocol_rules.yaml",
            confidence=1.0,
            details={"thresholds_used": list(self._protocol_agent.get_safety_thresholds().keys())}
        )
        if data.get("registry_comparison"):
            result.add_source(
                SourceType.REGISTRY,
                "registry_norms.yaml",
                confidence=0.95,
                details={"comparisons": list(data["registry_comparison"].keys())}
            )

        # Calculate overall confidence
        result.confidence = self._calculate_confidence(data)

        # Check minimum confidence threshold for safety signals
        min_confidence = CONFIDENCE_THRESHOLDS["safety_signal"]
        if result.confidence < min_confidence:
            logger.warning(
                f"Safety analysis confidence ({result.confidence:.2f}) below "
                f"threshold ({min_confidence:.2f})"
            )
            data["confidence_warning"] = (
                f"Low confidence ({result.confidence:.2f}). "
                f"Safety findings should be verified with additional data."
            )

        # Set uncertainty information
        result.set_uncertainty(
            data_gaps=self._identify_data_gaps(data, query_type),
            limitations=self._identify_limitations(data),
            reasoning=self._generate_reasoning(data, query_type)
        )

        # Add explicit reasoning
        result.reasoning = self._generate_reasoning(data, query_type)

        # Generate narrative
        try:
            result.narrative = await self._generate_safety_narrative(data)
        except ValueError as e:
            logger.warning(f"Could not generate safety narrative: {e}")
            result.narrative = self._generate_fallback_narrative(data)

        return result

    def _identify_data_gaps(self, data: Dict, query_type: str) -> List[str]:
        """Identify data gaps in safety analysis."""
        gaps = []

        if query_type == "study":
            if not data.get("n_patients"):
                gaps.append("No patient data available")
            if not data.get("metrics"):
                gaps.append("Safety metrics could not be calculated")
            if not data.get("registry_comparison"):
                gaps.append("Registry comparison not available")

        elif query_type == "patient":
            if not data.get("patient_id"):
                gaps.append("Patient ID not provided")
            if not data.get("adverse_events") and data.get("adverse_events") != []:
                gaps.append("Adverse event data not available")

        return gaps

    def _identify_limitations(self, data: Dict) -> List[str]:
        """Identify limitations in safety analysis."""
        limitations = []

        n_patients = data.get("n_patients", 0)
        if n_patients < 10:
            limitations.append(f"Small sample size (n={n_patients})")
        if n_patients < 50:
            limitations.append("Wide confidence intervals expected due to sample size")

        if data.get("overall_status") == "unknown":
            limitations.append("Unable to determine overall safety status")

        return limitations

    def _generate_reasoning(self, data: Dict, query_type: str) -> str:
        """Generate explicit reasoning for safety findings."""
        n_patients = data.get("n_patients", 0)
        n_signals = data.get("n_signals", 0)
        status = data.get("overall_status", "unknown")

        if query_type == "study":
            reasoning = (
                f"Study-level safety analysis based on {n_patients} patients. "
                f"Compared {len(data.get('metrics', []))} safety metrics against protocol thresholds. "
            )
            if n_signals > 0:
                signals = data.get("signals", [])
                signal_names = [s.get("metric", "unknown") for s in signals]
                reasoning += f"Detected {n_signals} signal(s): {', '.join(signal_names)}. "
            reasoning += f"Overall status: {status}."
            return reasoning

        elif query_type == "patient":
            patient_id = data.get("patient_id", "unknown")
            n_events = data.get("n_adverse_events", 0)
            risk_level = data.get("risk_level", "unknown")
            return (
                f"Patient-level safety analysis for {patient_id}. "
                f"Found {n_events} adverse event(s). Risk level: {risk_level}. "
                f"Based on demographics, comorbidities, and literature-derived hazard ratios."
            )

        return f"Safety analysis of type '{query_type}' completed."

    def _generate_fallback_narrative(self, data: Dict) -> str:
        """Generate a basic narrative when LLM is unavailable."""
        n_patients = data.get("n_patients", 0)
        n_signals = data.get("n_signals", 0)
        status = data.get("overall_status", "unknown")

        if n_signals == 0:
            return (
                f"Safety analysis of {n_patients} patients shows no signals. "
                f"All metrics within protocol thresholds. Status: {status}."
            )
        else:
            return (
                f"Safety analysis of {n_patients} patients identified {n_signals} signal(s). "
                f"Status: {status}. Review recommended."
            )

    async def _analyze_study_safety(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze safety across entire study.

        CLINICAL RATIONALE:
        Per FDA 21 CFR 812 and ICH GCP, safety monitoring is required throughout
        the study with defined action limits. This analysis compares observed rates
        against protocol-defined concern thresholds.

        THRESHOLDS (from protocol_rules.yaml):
        - revision_rate_concern: 10% (major surgical failure)
        - dislocation_rate_concern: 8% (common early complication)
        - infection_rate_concern: 5% (serious complication)
        - fracture_rate_concern: 8% (intraoperative complication)
        """
        # Get study safety data
        data_context = AgentContext(
            request_id=context.request_id,
            parameters={"query_type": "safety"}
        )
        data_result = await self._data_agent.run(data_context)

        if not data_result.success:
            return {"error": data_result.error}

        safety_data = data_result.data
        n_patients = safety_data.get("n_patients", 0)

        if n_patients == 0:
            return {"error": "No patient data available"}

        # Get protocol thresholds
        protocol_thresholds = self._protocol_agent.get_safety_thresholds()

        # Extract rates from nested 'rates' dict returned by data_agent
        rates = safety_data.get("rates", {})
        ae_by_type = safety_data.get("ae_by_type", {})

        # Calculate rates and compare to thresholds with full provenance
        metrics = []
        signals = []

        # Revision rate (device removal)
        revision_rate = rates.get("revision_rate", 0)
        revision_count = safety_data.get("n_revisions", 0)
        threshold = protocol_thresholds.get("revision_rate_concern", 0.10)
        revision_patients = _get_affected_patients_from_db("loosening")
        metric = self._analyze_metric(
            "revision_rate", revision_rate, threshold,
            revision_count, n_patients,
            affected_patients=revision_patients,
            threshold_source="protocol_rules.safety_thresholds.revision_rate_concern (10%)"
        )
        metric["literature_citations"] = _get_literature_citations("revision_rate")
        metrics.append(metric)
        if metric["signal"]:
            signals.append(metric)

        # Dislocation rate
        dislocation_rate = rates.get("dislocation_rate", 0)
        dislocation_count = ae_by_type.get("dislocation", 0)
        threshold = protocol_thresholds.get("dislocation_rate_concern", 0.08)
        dislocation_patients = _get_affected_patients_from_db("dislocation")
        metric = self._analyze_metric(
            "dislocation_rate", dislocation_rate, threshold,
            dislocation_count, n_patients,
            affected_patients=dislocation_patients,
            threshold_source="protocol_rules.safety_thresholds.dislocation_rate_concern (8%)"
        )
        metric["literature_citations"] = _get_literature_citations("dislocation_rate")
        metrics.append(metric)
        if metric["signal"]:
            signals.append(metric)

        # Infection rate
        infection_rate = rates.get("infection_rate", 0)
        infection_count = ae_by_type.get("infection", 0)
        threshold = protocol_thresholds.get("infection_rate_concern", 0.05)
        infection_patients = _get_affected_patients_from_db("infection")
        metric = self._analyze_metric(
            "infection_rate", infection_rate, threshold,
            infection_count, n_patients,
            affected_patients=infection_patients,
            threshold_source="protocol_rules.safety_thresholds.infection_rate_concern (5%)"
        )
        metric["literature_citations"] = _get_literature_citations("infection_rate")
        metrics.append(metric)
        if metric["signal"]:
            signals.append(metric)

        # Fracture rate
        fracture_rate = rates.get("fracture_rate", 0)
        fracture_count = ae_by_type.get("fracture", 0)
        threshold = protocol_thresholds.get("fracture_rate_concern", 0.08)
        fracture_patients = _get_affected_patients_from_db("fracture")
        metric = self._analyze_metric(
            "fracture_rate", fracture_rate, threshold,
            fracture_count, n_patients,
            affected_patients=fracture_patients,
            threshold_source="protocol_rules.safety_thresholds.fracture_rate_concern (8%)"
        )
        metric["literature_citations"] = _get_literature_citations("fracture_rate")
        metrics.append(metric)
        if metric["signal"]:
            signals.append(metric)

        # Compare to registry (may timeout - handle gracefully)
        registry_comparison = {}
        try:
            registry_comparison = await self._compare_to_registry({
                "revision_rate": revision_rate,
                "dislocation_rate": dislocation_rate,
                "infection_rate": infection_rate,
                "fracture_rate": fracture_rate,
            }, context)
        except Exception as e:
            logger.warning(f"Registry comparison failed: {e}")
            registry_comparison = {"error": str(e)}

        # Get all registry benchmarks for breakdown
        registry_breakdown = _get_registry_breakdown()

        return {
            "n_patients": n_patients,
            "n_adverse_events": safety_data.get("n_adverse_events", 0),
            "n_sae": safety_data.get("n_sae", 0),
            "metrics": metrics,
            "signals": signals,
            "n_signals": len(signals),
            "registry_comparison": registry_comparison,
            "registry_breakdown": registry_breakdown,
            "overall_status": self._determine_status(signals),
        }

    async def _analyze_patient_safety(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze safety for a specific patient."""
        patient_id = context.patient_id
        if not patient_id:
            return {"error": "patient_id required"}

        # Get patient data
        data_context = AgentContext(
            request_id=context.request_id,
            patient_id=patient_id,
            parameters={"query_type": "patient"}
        )
        data_result = await self._data_agent.run(data_context)

        if not data_result.success:
            return {"error": data_result.error}

        patient_data = data_result.data

        # Identify adverse events
        adverse_events = []
        if patient_data.get("has_revision"):
            adverse_events.append({"type": "revision", "severity": "serious"})
        if patient_data.get("has_dislocation"):
            adverse_events.append({"type": "dislocation", "severity": "moderate"})
        if patient_data.get("has_infection"):
            adverse_events.append({"type": "infection", "severity": "serious"})
        if patient_data.get("has_fracture"):
            adverse_events.append({"type": "fracture", "severity": "serious"})

        # Identify risk factors
        risk_factors = await self._identify_risk_factors(patient_data)

        return {
            "patient_id": patient_id,
            "adverse_events": adverse_events,
            "n_adverse_events": len(adverse_events),
            "has_sae": any(ae["severity"] == "serious" for ae in adverse_events),
            "risk_factors": risk_factors,
            "risk_level": self._calculate_risk_level(risk_factors),
        }

    async def _detect_signals(self, context: AgentContext) -> Dict[str, Any]:
        """Detect safety signals in study data."""
        study_safety = await self._analyze_study_safety(context)
        signals = study_safety.get("signals", [])

        # Classify signals
        classified_signals = []
        for signal in signals:
            classified = {
                **signal,
                "signal_level": self._classify_signal_level(signal),
                "recommended_action": self._get_recommended_action(signal),
            }
            classified_signals.append(classified)

        return {
            "signals": classified_signals,
            "n_signals": len(classified_signals),
            "high_priority": [s for s in classified_signals if s["signal_level"] == "high"],
            "medium_priority": [s for s in classified_signals if s["signal_level"] == "medium"],
            "requires_dsmb_review": any(s["signal_level"] == "high" for s in classified_signals),
        }

    async def _analyze_trends(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze safety trends over time."""
        # This would analyze temporal patterns in safety data
        # Simplified implementation
        return {
            "trend_analysis": "Not enough data for trend analysis",
            "data_points": 0,
        }

    def _analyze_metric(
        self,
        name: str,
        rate: float,
        threshold: float,
        count: int,
        total: int,
        affected_patients: List[Dict[str, Any]] = None,
        threshold_source: str = None,
    ) -> Dict[str, Any]:
        """Analyze a single safety metric with full provenance."""
        # Map metric name to event type for SQL query
        event_type_map = {
            "revision_rate": "revision",
            "dislocation_rate": "Dislocation",
            "infection_rate": "Infection",
            "fracture_rate": "fracture",
        }
        event_pattern = event_type_map.get(name, name.replace("_rate", ""))
        
        # Build data source provenance
        provenance = {
            "data_sources": {
                "event_count": f"study_adverse_events (WHERE ae_title ILIKE '%{event_pattern}%')",
                "patient_count": "study_patients (WHERE enrolled='Yes')",
                "threshold": f"protocol_rules.safety_thresholds.{name.replace('_rate', '_rate_concern')}",
            },
            "methodology": f"Count adverse events matching '{event_pattern}' pattern divided by enrolled patient count",
            "calculation": f"{count} events ÷ {total} patients = {round(rate * 100, 2)}%",
            "threshold_source": threshold_source or f"protocol_rules.yaml (safety_thresholds.{name.replace('_rate', '_rate_concern')})",
            "threshold_rationale": "Set at ~1.5x published literature rate per protocol H-34 v2.0",
            "regulatory_reference": "FDA 21 CFR 812.150 - Safety Reporting Requirements",
        }
        
        return {
            "metric": name,
            "rate": round(rate, 4),
            "count": count,
            "total": total,
            "threshold": threshold,
            "signal": rate >= threshold,
            "threshold_exceeded_by": round(rate - threshold, 4) if rate >= threshold else 0,
            "provenance": provenance,
            "affected_patients": affected_patients or [],
        }

    async def _compare_to_registry(
        self,
        rates: Dict[str, float],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Compare rates to registry benchmarks."""
        registry_context = AgentContext(
            request_id=context.request_id,
            parameters={
                "query_type": "compare",
                "study_data": rates
            }
        )
        registry_result = await self._registry_agent.run(registry_context)

        if not registry_result.success:
            return {"error": registry_result.error}

        return registry_result.data

    async def _identify_risk_factors(self, patient_data: Dict) -> List[Dict[str, Any]]:
        """Identify risk factors for a patient."""
        risk_factors = []

        # Check age
        age = patient_data.get("age")
        if age and age > 80:
            hr = self._literature_agent.get_risk_factor_hr("age_over_80") or 1.54
            risk_factors.append({
                "factor": "age_over_80",
                "present": True,
                "hazard_ratio": hr,
            })

        # Check BMI
        bmi = patient_data.get("bmi")
        if bmi and bmi > 35:
            hr = self._literature_agent.get_risk_factor_hr("bmi_over_35") or 1.38
            risk_factors.append({
                "factor": "bmi_over_35",
                "present": True,
                "hazard_ratio": hr,
            })

        # Check diabetes
        if patient_data.get("has_diabetes"):
            hr = self._literature_agent.get_risk_factor_hr("diabetes") or 1.28
            risk_factors.append({
                "factor": "diabetes",
                "present": True,
                "hazard_ratio": hr,
            })

        # Check osteoporosis
        if patient_data.get("has_osteoporosis"):
            hr = self._literature_agent.get_risk_factor_hr("osteoporosis") or 2.42
            risk_factors.append({
                "factor": "osteoporosis",
                "present": True,
                "hazard_ratio": hr,
            })

        return risk_factors

    def _calculate_risk_level(self, risk_factors: List[Dict]) -> str:
        """Calculate overall risk level from risk factors."""
        if not risk_factors:
            return "low"

        # Calculate combined hazard ratio (multiplicative)
        combined_hr = 1.0
        for rf in risk_factors:
            combined_hr *= rf.get("hazard_ratio", 1.0)

        if combined_hr >= 3.0:
            return "high"
        elif combined_hr >= 1.8:
            return "moderate"
        else:
            return "low"

    def _determine_status(self, signals: List[Dict]) -> str:
        """Determine overall safety status."""
        if not signals:
            return "acceptable"

        high_count = sum(1 for s in signals if s.get("threshold_exceeded_by", 0) > 0.02)
        if high_count > 0:
            return "concerning"
        return "monitoring"

    def _classify_signal_level(self, signal: Dict) -> str:
        """Classify signal priority level."""
        exceeded_by = signal.get("threshold_exceeded_by", 0)
        if exceeded_by > 0.03:
            return "high"
        elif exceeded_by > 0.01:
            return "medium"
        else:
            return "low"

    def _get_recommended_action(self, signal: Dict) -> str:
        """Get recommended action for a signal."""
        level = self._classify_signal_level(signal)
        metric = signal.get("metric", "")

        if level == "high":
            return f"Immediate DSMB review required for {metric}"
        elif level == "medium":
            return f"Enhanced monitoring and trending for {metric}"
        else:
            return f"Continue standard monitoring for {metric}"

    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate confidence in safety assessment."""
        n_patients = data.get("n_patients", 0)

        if n_patients >= 50:
            return 0.95
        elif n_patients >= 25:
            return 0.85
        elif n_patients >= 10:
            return 0.75
        else:
            return 0.65

    async def _generate_safety_narrative(self, data: Dict) -> str:
        """Generate safety narrative."""
        signals = data.get("signals", [])
        n_patients = data.get("n_patients", 0)
        status = data.get("overall_status", "unknown")

        if not n_patients:
            raise ValueError("Cannot generate safety narrative: no patient data available")

        prompt = self.load_prompt("safety_narrative", {
            "n_patients": n_patients,
            "n_signals": len(signals),
            "status": status,
            "signals": str(signals[:3]),  # Limit for context
        })

        narrative = await self.call_llm(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
        )
        return narrative.strip()
