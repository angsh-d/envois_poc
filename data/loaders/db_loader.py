"""
Database-backed loaders for H-34 Clinical Intelligence Platform.
Reads structured data from PostgreSQL tables instead of local files.
"""
import logging
from typing import Dict, Any, List, Optional
from functools import lru_cache

from sqlalchemy.orm import Session, joinedload

from data.models.database import (
    SessionLocal, 
    ProtocolRule, ProtocolVisit, ProtocolEndpoint,
    LiteraturePublication, LiteratureRiskFactor, AggregateBenchmark,
    RegistryBenchmark, RegistryPooledNorm,
    StudyPatient, StudyAdverseEvent, StudyScore, StudyVisit, StudySurgery,
    HazardRatioEstimate, ProtocolDocument
)
from data.loaders.yaml_loader import (
    ProtocolRules, VisitWindow, Endpoint,
    LiteratureBenchmarks, PublicationBenchmark, RiskFactor,
    RegistryNorms, RegistryBenchmark as RegistryBenchmarkModel, PooledNorms,
    ComparativeCriteria, PerformanceLevel, DeviceBenchmark
)

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Loads structured data from PostgreSQL database."""

    def __init__(self):
        self._db_available = SessionLocal is not None

    def _get_session(self) -> Optional[Session]:
        """Get database session."""
        if not self._db_available:
            return None
        return SessionLocal()

    def is_available(self) -> bool:
        """Check if database is available."""
        return self._db_available

    def load_protocol_rules(self) -> Optional[ProtocolRules]:
        """Load protocol rules from database."""
        session = self._get_session()
        if not session:
            return None

        try:
            protocol = session.query(ProtocolRule).options(
                joinedload(ProtocolRule.visits),
                joinedload(ProtocolRule.endpoints)
            ).first()

            if not protocol:
                return None

            visits = [
                VisitWindow(
                    id=v.visit_id,
                    name=v.name,
                    target_day=v.target_day,
                    window_minus=v.window_minus,
                    window_plus=v.window_plus,
                    required_assessments=v.required_assessments or [],
                    is_primary_endpoint=v.is_primary_endpoint
                )
                for v in sorted(protocol.visits, key=lambda x: x.sequence)
            ]

            primary_ep = None
            secondary_eps = []
            for ep in protocol.endpoints:
                endpoint = Endpoint(
                    id=ep.endpoint_id,
                    name=ep.name,
                    calculation=ep.calculation,
                    success_threshold=ep.success_threshold,
                    mcid_threshold=ep.mcid_threshold,
                    success_criterion=ep.success_criterion
                )
                if ep.endpoint_type == "primary":
                    primary_ep = endpoint
                else:
                    secondary_eps.append(endpoint)

            if not primary_ep:
                primary_ep = Endpoint(id="default", name="Default Endpoint")

            return ProtocolRules(
                protocol_id=protocol.protocol_id,
                protocol_version=protocol.protocol_version,
                effective_date=protocol.effective_date.isoformat() if protocol.effective_date else "",
                title=protocol.title or "",
                visits=visits,
                primary_endpoint=primary_ep,
                secondary_endpoints=secondary_eps,
                sample_size_target=protocol.sample_size_target or 50,
                sample_size_interim=protocol.sample_size_interim or 25,
                safety_thresholds=protocol.safety_thresholds or {},
                deviation_classification=protocol.deviation_classification or {},
                inclusion_criteria=protocol.inclusion_criteria or [],
                exclusion_criteria=protocol.exclusion_criteria or []
            )
        except Exception as e:
            logger.error(f"Error loading protocol rules from DB: {e}")
            return None
        finally:
            session.close()

    def load_literature_benchmarks(self) -> Optional[LiteratureBenchmarks]:
        """Load literature benchmarks from database."""
        session = self._get_session()
        if not session:
            return None

        try:
            publications_db = session.query(LiteraturePublication).options(
                joinedload(LiteraturePublication.risk_factors)
            ).all()

            if not publications_db:
                return None

            publications = []
            all_risk_factors = []

            for pub in publications_db:
                risk_factors = [
                    RiskFactor(
                        factor=rf.factor,
                        hazard_ratio=rf.hazard_ratio,
                        confidence_interval=[rf.confidence_interval_low, rf.confidence_interval_high] if rf.confidence_interval_low else None,
                        outcome=rf.outcome or "",
                        source=rf.source or pub.publication_id
                    )
                    for rf in pub.risk_factors
                ]
                all_risk_factors.extend(risk_factors)

                publications.append(PublicationBenchmark(
                    id=pub.publication_id,
                    title=pub.title,
                    year=pub.year or 0,
                    n_patients=pub.n_patients,
                    follow_up_years=pub.follow_up_years,
                    benchmarks=pub.benchmarks or {},
                    risk_factors=risk_factors
                ))

            agg_benchmarks_db = session.query(AggregateBenchmark).all()
            aggregate_benchmarks = {
                ab.metric: ab.data or {
                    "mean": ab.mean,
                    "median": ab.median,
                    "sd": ab.sd,
                    "range": [ab.range_low, ab.range_high] if ab.range_low else None,
                    "concern_threshold": ab.concern_threshold
                }
                for ab in agg_benchmarks_db
            }

            return LiteratureBenchmarks(
                publications=publications,
                aggregate_benchmarks=aggregate_benchmarks,
                all_risk_factors=all_risk_factors
            )
        except Exception as e:
            logger.error(f"Error loading literature benchmarks from DB: {e}")
            return None
        finally:
            session.close()

    def load_registry_norms(self) -> Optional[RegistryNorms]:
        """Load registry norms from database."""
        session = self._get_session()
        if not session:
            return None

        try:
            registries_db = session.query(RegistryBenchmark).all()
            if not registries_db:
                return None

            registries = [
                RegistryBenchmarkModel(
                    id=r.registry_id,
                    name=r.name,
                    abbreviation=r.abbreviation or r.registry_id.upper(),
                    report_year=r.report_year or 0,
                    data_years=r.data_years,
                    population=r.population,
                    n_procedures=r.n_procedures,
                    n_primary=r.n_primary,
                    revision_burden=r.revision_burden,
                    survival_1yr=r.survival_1yr,
                    survival_2yr=r.survival_2yr,
                    survival_5yr=r.survival_5yr,
                    survival_10yr=r.survival_10yr,
                    survival_15yr=r.survival_15yr,
                    revision_rate_1yr=r.revision_rate_1yr,
                    revision_rate_2yr=r.revision_rate_2yr,
                    revision_rate_median=r.revision_rate_median,
                    revision_rate_p75=r.revision_rate_p75,
                    revision_rate_p95=r.revision_rate_p95,
                    revision_reasons=r.revision_reasons,
                    outcomes_by_indication=r.outcomes_by_indication
                )
                for r in registries_db
            ]

            pooled_db = session.query(RegistryPooledNorm).first()
            pooled_norms = None
            concern_thresholds = {}
            risk_thresholds = {}

            if pooled_db:
                pooled_norms = PooledNorms(
                    total_procedures=pooled_db.total_procedures or 0,
                    total_registries=pooled_db.total_registries or 0,
                    survival_rates=pooled_db.survival_rates or {},
                    revision_rates=pooled_db.revision_rates or {},
                    revision_reasons_pooled=pooled_db.revision_reasons_pooled or {}
                )
                concern_thresholds = pooled_db.concern_thresholds or {}
                risk_thresholds = pooled_db.risk_thresholds or {}

            return RegistryNorms(
                registries=registries,
                pooled_norms=pooled_norms,
                concern_thresholds=concern_thresholds,
                risk_thresholds=risk_thresholds,
                comparative_criteria=None,
                device_benchmarks={}
            )
        except Exception as e:
            logger.error(f"Error loading registry norms from DB: {e}")
            return None
        finally:
            session.close()

    def load_protocol_document(self, document_type: str) -> Optional[Dict[str, Any]]:
        """Load a protocol JSON document (USDM, SOA, Eligibility)."""
        session = self._get_session()
        if not session:
            return None

        try:
            doc = session.query(ProtocolDocument).filter_by(
                document_type=document_type
            ).first()
            return doc.content if doc else None
        except Exception as e:
            logger.error(f"Error loading protocol document {document_type} from DB: {e}")
            return None
        finally:
            session.close()

    def load_study_patients(self) -> List[Dict[str, Any]]:
        """Load all study patients from database."""
        session = self._get_session()
        if not session:
            return []

        try:
            patients = session.query(StudyPatient).all()
            return [
                {
                    "id": p.id,
                    "patient_id": p.patient_id,
                    "facility": p.facility,
                    "year_of_birth": p.year_of_birth,
                    "weight": p.weight,
                    "height": p.height,
                    "bmi": p.bmi,
                    "gender": p.gender,
                    "race": p.race,
                    "activity_level": p.activity_level,
                    "work_status": p.work_status,
                    "smoking_habits": p.smoking_habits,
                    "alcohol_habits": p.alcohol_habits,
                    "enrolled": p.enrolled,
                    "status": p.status
                }
                for p in patients
            ]
        except Exception as e:
            logger.error(f"Error loading study patients from DB: {e}")
            return []
        finally:
            session.close()

    def load_adverse_events(self) -> List[Dict[str, Any]]:
        """Load all adverse events from database."""
        session = self._get_session()
        if not session:
            return []

        try:
            events = session.query(StudyAdverseEvent).options(
                joinedload(StudyAdverseEvent.patient)
            ).all()
            return [
                {
                    "id": e.id,
                    "patient_id": e.patient.patient_id if e.patient else None,
                    "ae_id": e.ae_id,
                    "report_type": e.report_type,
                    "onset_date": e.onset_date.isoformat() if e.onset_date else None,
                    "ae_title": e.ae_title,
                    "event_narrative": e.event_narrative,
                    "is_sae": e.is_sae,
                    "classification": e.classification,
                    "outcome": e.outcome,
                    "severity": e.severity,
                    "device_relationship": e.device_relationship,
                    "procedure_relationship": e.procedure_relationship,
                    "expectedness": e.expectedness,
                    "action_taken": e.action_taken
                }
                for e in events
            ]
        except Exception as e:
            logger.error(f"Error loading adverse events from DB: {e}")
            return []
        finally:
            session.close()

    def load_scores(self, score_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load HHS/OHS scores from database."""
        session = self._get_session()
        if not session:
            return []

        try:
            query = session.query(StudyScore).options(
                joinedload(StudyScore.patient)
            )
            if score_type:
                query = query.filter(StudyScore.score_type == score_type)

            scores = query.all()
            return [
                {
                    "id": s.id,
                    "patient_id": s.patient.patient_id if s.patient else None,
                    "score_type": s.score_type,
                    "follow_up": s.follow_up,
                    "follow_up_date": s.follow_up_date.isoformat() if s.follow_up_date else None,
                    "total_score": s.total_score,
                    "score_category": s.score_category,
                    "components": s.components
                }
                for s in scores
            ]
        except Exception as e:
            logger.error(f"Error loading scores from DB: {e}")
            return []
        finally:
            session.close()

    def load_surgeries(self) -> List[Dict[str, Any]]:
        """Load surgery data from database."""
        session = self._get_session()
        if not session:
            return []

        try:
            surgeries = session.query(StudySurgery).all()
            return [
                {
                    "id": s.id,
                    "patient_id": s.patient_id,
                    "surgery_date": s.surgery_date.isoformat() if s.surgery_date else None,
                    "surgical_approach": s.surgical_approach,
                    "anaesthesia": s.anaesthesia,
                    "surgery_time_minutes": s.surgery_time_minutes,
                    "stem_type": s.stem_type,
                    "cup_type": s.cup_type,
                    "cup_diameter": s.cup_diameter,
                    "head_type": s.head_type,
                    "head_material": s.head_material,
                    "implant_details": s.implant_details
                }
                for s in surgeries
            ]
        except Exception as e:
            logger.error(f"Error loading surgeries from DB: {e}")
            return []
        finally:
            session.close()

    def get_study_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the study."""
        session = self._get_session()
        if not session:
            return {}

        try:
            patient_count = session.query(StudyPatient).count()
            ae_count = session.query(StudyAdverseEvent).count()
            sae_count = session.query(StudyAdverseEvent).filter_by(is_sae=True).count()
            hhs_count = session.query(StudyScore).filter_by(score_type="HHS").count()
            ohs_count = session.query(StudyScore).filter_by(score_type="OHS").count()
            surgery_count = session.query(StudySurgery).count()

            return {
                "total_patients": patient_count,
                "total_adverse_events": ae_count,
                "total_saes": sae_count,
                "total_hhs_scores": hhs_count,
                "total_ohs_scores": ohs_count,
                "total_surgeries": surgery_count
            }
        except Exception as e:
            logger.error(f"Error getting study summary from DB: {e}")
            return {}
        finally:
            session.close()


_db_loader: Optional[DatabaseLoader] = None


def get_db_loader() -> DatabaseLoader:
    """Get the database loader singleton."""
    global _db_loader
    if _db_loader is None:
        _db_loader = DatabaseLoader()
    return _db_loader
