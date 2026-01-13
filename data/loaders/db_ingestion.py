"""
Database ingestion script for H-34 Clinical Intelligence Platform.
Loads data from YAML, JSON, and Excel files into PostgreSQL tables.
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import yaml
from sqlalchemy.orm import Session

from data.models.database import (
    SessionLocal, init_db,
    ProtocolRule, ProtocolVisit, ProtocolEndpoint,
    LiteraturePublication, LiteratureRiskFactor, AggregateBenchmark,
    RegistryBenchmark, RegistryPooledNorm,
    StudyPatient, StudyAdverseEvent, StudyScore, StudyVisit, StudySurgery,
    HazardRatioEstimate, ProtocolDocument
)
from app.config import settings

logger = logging.getLogger(__name__)


class DataIngestion:
    """Ingests data from files into PostgreSQL database."""

    def __init__(self):
        self.base_path = settings.project_root / "data"
        self.processed_path = self.base_path / "processed" / "document_as_code"
        self.raw_path = self.base_path / "raw"

    def _get_session(self) -> Session:
        """Get database session."""
        if SessionLocal is None:
            raise RuntimeError("Database not configured")
        return SessionLocal()

    def ingest_protocol_rules(self) -> int:
        """Ingest protocol rules from YAML."""
        yaml_path = self.processed_path / "protocol_rules.yaml"
        if not yaml_path.exists():
            logger.warning(f"Protocol rules not found: {yaml_path}")
            return 0

        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        session = self._get_session()
        try:
            existing = session.query(ProtocolRule).filter_by(
                protocol_id=data.get("protocol", {}).get("id", "")
            ).first()
            if existing:
                session.delete(existing)
                session.commit()

            protocol = ProtocolRule(
                protocol_id=data.get("protocol", {}).get("id", ""),
                protocol_version=data.get("protocol", {}).get("version", ""),
                effective_date=datetime.strptime(
                    data.get("protocol", {}).get("effective_date", "2024-01-01"),
                    "%Y-%m-%d"
                ).date() if data.get("protocol", {}).get("effective_date") else None,
                title=data.get("protocol", {}).get("title", ""),
                sponsor=data.get("protocol", {}).get("sponsor", ""),
                phase=data.get("protocol", {}).get("phase", ""),
                sample_size_target=data.get("sample_size", {}).get("target_enrollment", 50),
                sample_size_interim=data.get("sample_size", {}).get("interim_analysis", 25),
                safety_thresholds=data.get("safety_thresholds", {}),
                deviation_classification=data.get("deviation_classification", {}),
                inclusion_criteria=data.get("ie_criteria", {}).get("inclusion", []),
                exclusion_criteria=data.get("ie_criteria", {}).get("exclusion", []),
            )
            session.add(protocol)
            session.flush()

            for i, visit in enumerate(data.get("schedule_of_assessments", {}).get("visits", [])):
                pv = ProtocolVisit(
                    protocol_id=protocol.id,
                    visit_id=visit.get("id", ""),
                    name=visit.get("name", ""),
                    target_day=visit.get("target_day", 0),
                    window_minus=visit.get("window_minus", 0),
                    window_plus=visit.get("window_plus", 0),
                    required_assessments=visit.get("required_assessments", []),
                    is_primary_endpoint=visit.get("is_primary_endpoint", False),
                    sequence=i
                )
                session.add(pv)

            primary = data.get("endpoints", {}).get("primary", {})
            if primary:
                pe = ProtocolEndpoint(
                    protocol_id=protocol.id,
                    endpoint_id=primary.get("id", ""),
                    name=primary.get("name", ""),
                    endpoint_type="primary",
                    timepoint=primary.get("timepoint"),
                    calculation=primary.get("calculation"),
                    success_threshold=primary.get("success_threshold"),
                    mcid_threshold=primary.get("mcid_threshold"),
                    success_criterion=primary.get("success_criterion")
                )
                session.add(pe)

            for secondary in data.get("endpoints", {}).get("secondary", []):
                se = ProtocolEndpoint(
                    protocol_id=protocol.id,
                    endpoint_id=secondary.get("id", ""),
                    name=secondary.get("name", ""),
                    endpoint_type="secondary",
                    timepoint=secondary.get("timepoint"),
                    calculation=secondary.get("calculation"),
                    success_threshold=secondary.get("success_threshold"),
                    mcid_threshold=secondary.get("mcid_threshold")
                )
                session.add(se)

            session.commit()
            logger.info(f"Ingested protocol rules: {protocol.protocol_id}")
            return 1
        except Exception as e:
            session.rollback()
            logger.error(f"Error ingesting protocol rules: {e}")
            raise
        finally:
            session.close()

    def ingest_literature_benchmarks(self) -> int:
        """Ingest literature benchmarks from YAML."""
        yaml_path = self.processed_path / "literature_benchmarks.yaml"
        if not yaml_path.exists():
            logger.warning(f"Literature benchmarks not found: {yaml_path}")
            return 0

        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        session = self._get_session()
        try:
            session.query(LiteratureRiskFactor).delete()
            session.query(LiteraturePublication).delete()
            session.query(AggregateBenchmark).delete()
            session.commit()

            count = 0
            for pub_id, pub_data in data.get("publications", {}).items():
                pub = LiteraturePublication(
                    publication_id=pub_id,
                    title=pub_data.get("title", ""),
                    year=pub_data.get("year"),
                    journal=pub_data.get("journal"),
                    n_patients=pub_data.get("n_patients"),
                    follow_up_years=pub_data.get("follow_up_years"),
                    revision_indication=pub_data.get("revision_indication"),
                    benchmarks=pub_data.get("benchmarks", {})
                )
                session.add(pub)
                session.flush()

                for rf_data in pub_data.get("risk_factors", []):
                    ci = rf_data.get("confidence_interval", [])
                    rf = LiteratureRiskFactor(
                        publication_id=pub.id,
                        factor=rf_data.get("factor", ""),
                        hazard_ratio=rf_data.get("hazard_ratio", 1.0),
                        confidence_interval_low=ci[0] if len(ci) >= 1 else None,
                        confidence_interval_high=ci[1] if len(ci) >= 2 else None,
                        outcome=rf_data.get("outcome"),
                        source=rf_data.get("source", pub_id)
                    )
                    session.add(rf)
                count += 1

            for metric, values in data.get("aggregate_benchmarks", {}).items():
                ab = AggregateBenchmark(
                    metric=metric,
                    mean=values.get("mean"),
                    median=values.get("median"),
                    sd=values.get("sd"),
                    range_low=values.get("range", [None, None])[0] if values.get("range") else None,
                    range_high=values.get("range", [None, None])[1] if values.get("range") and len(values.get("range", [])) > 1 else None,
                    p25=values.get("p25"),
                    p75=values.get("p75"),
                    concern_threshold=values.get("concern_threshold"),
                    data=values
                )
                session.add(ab)

            session.commit()
            logger.info(f"Ingested {count} literature publications")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error ingesting literature benchmarks: {e}")
            raise
        finally:
            session.close()

    def ingest_registry_norms(self) -> int:
        """Ingest registry norms from YAML."""
        yaml_path = self.processed_path / "registry_norms.yaml"
        if not yaml_path.exists():
            logger.warning(f"Registry norms not found: {yaml_path}")
            return 0

        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        session = self._get_session()
        try:
            session.query(RegistryBenchmark).delete()
            session.query(RegistryPooledNorm).delete()
            session.commit()

            count = 0
            for reg_id, reg_data in data.get("registries", {}).items():
                rb = RegistryBenchmark(
                    registry_id=reg_id,
                    name=reg_data.get("name", reg_id),
                    abbreviation=reg_data.get("abbreviation", reg_id.upper()),
                    report_year=reg_data.get("report_year"),
                    data_years=reg_data.get("data_years"),
                    population=reg_data.get("population"),
                    n_procedures=reg_data.get("n_procedures"),
                    n_primary=reg_data.get("n_primary"),
                    revision_burden=reg_data.get("revision_burden"),
                    survival_1yr=reg_data.get("survival_1yr"),
                    survival_2yr=reg_data.get("survival_2yr"),
                    survival_5yr=reg_data.get("survival_5yr"),
                    survival_10yr=reg_data.get("survival_10yr"),
                    survival_15yr=reg_data.get("survival_15yr"),
                    revision_rate_1yr=reg_data.get("revision_rate_1yr"),
                    revision_rate_2yr=reg_data.get("revision_rate_2yr"),
                    revision_rate_median=reg_data.get("revision_rate_median"),
                    revision_rate_p75=reg_data.get("revision_rate_p75"),
                    revision_rate_p95=reg_data.get("revision_rate_p95"),
                    revision_reasons=reg_data.get("revision_reasons", []),
                    outcomes_by_indication=reg_data.get("outcomes_by_indication", {})
                )
                session.add(rb)
                count += 1

            pooled = data.get("pooled_norms", {})
            if pooled:
                pn = RegistryPooledNorm(
                    total_procedures=pooled.get("total_procedures", 0),
                    total_registries=pooled.get("total_registries", 0),
                    survival_rates=pooled.get("survival_rates", {}),
                    revision_rates=pooled.get("revision_rates", {}),
                    revision_reasons_pooled=pooled.get("revision_reasons_pooled", {}),
                    concern_thresholds=data.get("concern_thresholds", {}),
                    risk_thresholds=data.get("risk_thresholds", {})
                )
                session.add(pn)

            session.commit()
            logger.info(f"Ingested {count} registry benchmarks")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error ingesting registry norms: {e}")
            raise
        finally:
            session.close()

    def ingest_hazard_ratios(self) -> int:
        """Ingest extracted hazard ratios from YAML."""
        yaml_path = self.base_path / "processed" / "extracted_hazard_ratios.yaml"
        if not yaml_path.exists():
            logger.warning(f"Hazard ratios not found: {yaml_path}")
            return 0

        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        session = self._get_session()
        try:
            session.query(HazardRatioEstimate).delete()
            session.commit()

            count = 0
            for hr_data in data.get("hazard_ratios", []):
                ci = hr_data.get("confidence_interval", [])
                hr = HazardRatioEstimate(
                    source_file=hr_data.get("source_file"),
                    factor=hr_data.get("factor", "unknown"),
                    hazard_ratio=hr_data.get("hazard_ratio", 1.0),
                    confidence_interval_low=ci[0] if len(ci) >= 1 else None,
                    confidence_interval_high=ci[1] if len(ci) >= 2 else None,
                    p_value=hr_data.get("p_value"),
                    outcome=hr_data.get("outcome"),
                    context=hr_data.get("context")
                )
                session.add(hr)
                count += 1

            session.commit()
            logger.info(f"Ingested {count} hazard ratio estimates")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error ingesting hazard ratios: {e}")
            raise
        finally:
            session.close()

    def ingest_protocol_documents(self) -> int:
        """Ingest protocol JSON documents (USDM, SOA, Eligibility)."""
        protocol_path = self.raw_path / "protocol"
        
        documents = [
            ("soa_usdm", "CIP_H-34_v.2.0_05Nov2024_fully signed_soa_usdm_draft.json"),
            ("eligibility", "CIP_H-34_v.2.0_05Nov2024_fully signed_eligibility_criteria.json"),
            ("usdm_4.0", "CIP_H-34_v.2.0_05Nov2024_fully signed_usdm_4.0.json"),
        ]

        session = self._get_session()
        try:
            session.query(ProtocolDocument).delete()
            session.commit()

            count = 0
            for doc_type, filename in documents:
                file_path = protocol_path / filename
                if not file_path.exists():
                    logger.warning(f"Protocol document not found: {file_path}")
                    continue

                with open(file_path, 'r') as f:
                    content = json.load(f)

                pd = ProtocolDocument(
                    document_type=doc_type,
                    document_name=filename,
                    content=content,
                    source_file=str(file_path),
                    version="2.0"
                )
                session.add(pd)
                count += 1

            session.commit()
            logger.info(f"Ingested {count} protocol documents")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error ingesting protocol documents: {e}")
            raise
        finally:
            session.close()

    def ingest_study_data(self) -> Dict[str, int]:
        """Ingest study data from Excel file."""
        from data.loaders.excel_loader import H34ExcelLoader
        
        excel_files = list((self.raw_path / "study").glob("*.xlsx"))
        if not excel_files:
            logger.warning("No Excel study files found")
            return {"patients": 0, "adverse_events": 0, "scores": 0}

        excel_path = excel_files[0]
        logger.info(f"Loading study data from: {excel_path}")

        loader = H34ExcelLoader(excel_path)
        study_data = loader.load()

        session = self._get_session()
        try:
            session.query(StudyScore).delete()
            session.query(StudyVisit).delete()
            session.query(StudySurgery).delete()
            session.query(StudyAdverseEvent).delete()
            session.query(StudyPatient).delete()
            session.commit()

            patient_map = {}
            for patient in study_data.patients:
                pid = getattr(patient, 'patient_id', None) or getattr(patient, 'Id', None)
                if not pid:
                    continue
                p = StudyPatient(
                    patient_id=pid,
                    facility=patient.facility,
                    year_of_birth=patient.year_of_birth,
                    weight=patient.weight,
                    height=patient.height,
                    bmi=patient.bmi,
                    gender=patient.gender,
                    race=patient.race,
                    activity_level=patient.activity_level,
                    work_status=patient.work_status,
                    smoking_habits=patient.smoking_habits,
                    alcohol_habits=patient.alcohol_habits,
                    concomitant_medications=patient.concomitant_medications,
                    screening_date=patient.screening_date,
                    consent_date=patient.consent_date,
                    enrolled=patient.enrolled,
                    status=patient.status
                )
                session.add(p)
                session.flush()
                patient_map[pid] = p.id

            for ae in study_data.adverse_events:
                ae_pid = getattr(ae, 'patient_id', None) or getattr(ae, 'Id', None)
                if ae_pid not in patient_map:
                    continue
                sae = StudyAdverseEvent(
                    patient_id=patient_map[ae_pid],
                    ae_id=ae.ae_id,
                    report_type=ae.report_type,
                    initial_report_date=ae.initial_report_date,
                    report_date=ae.report_date,
                    onset_date=ae.onset_date,
                    ae_title=ae.ae_title,
                    event_narrative=ae.event_narrative,
                    is_sae=ae.is_sae == "Yes" if ae.is_sae else False,
                    classification=ae.classification,
                    outcome=ae.outcome,
                    end_date=ae.end_date,
                    severity=ae.severity,
                    device_relationship=ae.device_relationship,
                    procedure_relationship=ae.procedure_relationship,
                    expectedness=ae.expectedness,
                    action_taken=ae.action_taken,
                    device_removed=ae.device_removed == "Yes" if ae.device_removed else False,
                    device_removal_date=ae.device_removal_date
                )
                session.add(sae)

            for hhs in study_data.hhs_scores:
                hhs_pid = getattr(hhs, 'patient_id', None) or getattr(hhs, 'Id', None)
                if hhs_pid not in patient_map:
                    continue
                score = StudyScore(
                    patient_id=patient_map[hhs_pid],
                    score_type="HHS",
                    follow_up=hhs.follow_up,
                    follow_up_date=hhs.follow_up_date,
                    total_score=hhs.total_score,
                    score_category=hhs.score_category,
                    components={
                        "pain": hhs.pain,
                        "stairs": hhs.stairs,
                        "shoes_socks": hhs.shoes_socks,
                        "sitting": hhs.sitting,
                        "public_transport": hhs.public_transport,
                        "limp": hhs.limp,
                        "walking_support": hhs.walking_support,
                        "distance_walked": hhs.distance_walked,
                        "flexion": hhs.flexion,
                        "extension": hhs.extension,
                        "abduction": hhs.abduction,
                        "adduction": hhs.adduction,
                        "external_rotation": hhs.external_rotation,
                        "internal_rotation": hhs.internal_rotation
                    }
                )
                session.add(score)

            for ohs in study_data.ohs_scores:
                ohs_pid = getattr(ohs, 'patient_id', None) or getattr(ohs, 'Id', None)
                if ohs_pid not in patient_map:
                    continue
                score = StudyScore(
                    patient_id=patient_map[ohs_pid],
                    score_type="OHS",
                    follow_up=ohs.follow_up,
                    follow_up_date=ohs.follow_up_date,
                    total_score=ohs.total_score,
                    score_category=ohs.score_category,
                    components={f"q{i}": getattr(ohs, f"q{i}") for i in range(1, 13)}
                )
                session.add(score)

            for intraop in study_data.intraoperatives:
                intraop_pid = getattr(intraop, 'patient_id', None) or getattr(intraop, 'Id', None)
                if intraop_pid not in patient_map:
                    continue
                surgery = StudySurgery(
                    patient_id=patient_map[intraop_pid],
                    surgery_date=intraop.surgery_date,
                    stem_type=intraop.stem_type,
                    stem_size=intraop.stem_size,
                    cup_type=intraop.cup_type,
                    cup_diameter=intraop.cup_diameter,
                    cup_liner_material=intraop.cup_liner_material,
                    head_type=intraop.head_type,
                    head_material=intraop.head_material,
                    head_diameter=intraop.head_diameter,
                    implant_details={
                        "cup_cement": intraop.cup_cement,
                        "stem_cement": intraop.stem_cement,
                        "cup_liner_size": intraop.cup_liner_size,
                        "cup_plate": intraop.cup_plate,
                        "cup_plate_diameter": intraop.cup_plate_diameter,
                        "head_size": intraop.head_size,
                        "acetabulum_bone_quality": intraop.acetabulum_bone_quality,
                        "acetabulum_bone_grafting": intraop.acetabulum_bone_grafting,
                        "femur_bone_quality": intraop.femur_bone_quality,
                        "femur_bone_grafting": intraop.femur_bone_grafting
                    }
                )
                session.add(surgery)

            for surgery_data in study_data.surgery_data:
                sd_pid = getattr(surgery_data, 'patient_id', None) or getattr(surgery_data, 'Id', None)
                if sd_pid in patient_map:
                    existing = session.query(StudySurgery).filter_by(
                        patient_id=patient_map[sd_pid]
                    ).first()
                    if existing:
                        existing.surgical_approach = surgery_data.surgical_approach
                        existing.anaesthesia = surgery_data.anaesthesia
                        existing.surgery_time_minutes = surgery_data.surgery_time_minutes
                        existing.intraoperative_complications = surgery_data.intraoperative_complications

            session.commit()
            result = {
                "patients": len(study_data.patients),
                "adverse_events": len(study_data.adverse_events),
                "scores": len(study_data.hhs_scores) + len(study_data.ohs_scores)
            }
            logger.info(f"Ingested study data: {result}")
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Error ingesting study data: {e}")
            raise
        finally:
            session.close()

    def ingest_all(self) -> Dict[str, Any]:
        """Run all ingestion tasks."""
        logger.info("Starting full data ingestion...")

        init_db()
        logger.info("Database tables initialized")

        results = {
            "protocol_rules": self.ingest_protocol_rules(),
            "literature_publications": self.ingest_literature_benchmarks(),
            "registry_benchmarks": self.ingest_registry_norms(),
            "hazard_ratios": self.ingest_hazard_ratios(),
            "protocol_documents": self.ingest_protocol_documents(),
        }

        try:
            study_results = self.ingest_study_data()
            results.update(study_results)
        except Exception as e:
            logger.error(f"Study data ingestion failed: {e}")
            results["study_error"] = str(e)

        logger.info(f"Data ingestion complete: {results}")
        return results


def run_ingestion():
    """Run the data ingestion process."""
    ingestion = DataIngestion()
    return ingestion.ingest_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_ingestion()
    print(f"Ingestion results: {results}")
