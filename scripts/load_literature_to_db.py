#!/usr/bin/env python3
"""
Load extracted literature benchmarks into PostgreSQL database.
Updates literature_publications, literature_risk_factors, and aggregate_benchmarks tables.
Stores provenance in JSON benchmarks field.
"""

import yaml
import logging
from datetime import datetime
from sqlalchemy import text
from data.models.database import (
    SessionLocal,
    LiteraturePublication,
    LiteratureRiskFactor,
    AggregateBenchmark
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_literature_to_database():
    """Load extracted literature data into database."""
    
    with open("data/processed/document_as_code/literature_benchmarks.yaml", "r") as f:
        data = yaml.safe_load(f)
    
    session = SessionLocal()
    
    try:
        logger.info("Clearing existing literature data...")
        session.query(LiteratureRiskFactor).delete()
        session.query(AggregateBenchmark).delete()
        session.query(LiteraturePublication).delete()
        session.commit()
        
        pub_id_to_db_id = {}
        
        logger.info("Loading publications...")
        for pub in data.get("publications", []):
            hhs_outcomes = [o for o in data.get("outcome_benchmarks", {}).get("harris_hip_score", [])
                          if o.get("publication_id") == pub["id"]]
            survival_rates = [s for s in data.get("outcome_benchmarks", {}).get("survival_rates", [])
                            if s.get("publication_id") == pub["id"]]
            mcid_thresholds = [m for m in data.get("mcid_thresholds", [])
                             if m.get("publication_id") == pub["id"]]
            complication_rates = [c for c in data.get("outcome_benchmarks", {}).get("complication_rates", [])
                                 if c.get("publication_id") == pub["id"]]
            
            benchmarks_json = {
                "doi": pub.get("doi"),
                "pmid": pub.get("pmid"),
                "authors": pub.get("authors"),
                "study_type": pub.get("study_type"),
                "source_file": pub.get("source_file"),
                "hhs_outcomes": hhs_outcomes,
                "survival_rates": survival_rates,
                "mcid_thresholds": mcid_thresholds,
                "complication_rates": complication_rates,
                "metadata": data.get("metadata", {})
            }
            
            follow_up_years = None
            if pub.get("follow_up_months"):
                follow_up_years = pub["follow_up_months"] / 12.0
            
            db_pub = LiteraturePublication(
                publication_id=pub["id"],
                title=pub.get("title", ""),
                year=pub.get("year", 2025),
                journal=pub.get("journal") or "Unknown",
                n_patients=pub.get("sample_size"),
                follow_up_years=follow_up_years,
                revision_indication="hip_arthroplasty",
                benchmarks=benchmarks_json
            )
            session.add(db_pub)
            session.flush()
            pub_id_to_db_id[pub["id"]] = db_pub.id
            logger.info(f"  Added publication: {pub['id']} ({pub.get('year')})")
        
        session.commit()
        
        logger.info("Loading risk factors (hazard ratios)...")
        risk_factor_count = 0
        for rf in data.get("risk_factors", []):
            if rf.get("hazard_ratio") is None:
                continue
            
            pub_db_id = pub_id_to_db_id.get(rf["publication_id"])
            if not pub_db_id:
                continue
                
            prov = rf.get("provenance", {})
            db_rf = LiteratureRiskFactor(
                publication_id=pub_db_id,
                factor=rf.get("risk_factor", ""),
                hazard_ratio=rf.get("hazard_ratio"),
                confidence_interval_low=rf.get("ci_lower"),
                confidence_interval_high=rf.get("ci_upper"),
                outcome="revision_risk",
                source=f"Page {prov.get('page')}, {prov.get('table')}"
            )
            session.add(db_rf)
            risk_factor_count += 1
        
        session.commit()
        logger.info(f"  Added {risk_factor_count} risk factors")
        
        logger.info("Loading aggregate benchmarks...")
        benchmark_count = 0
        
        for mcid in data.get("mcid_thresholds", []):
            prov = mcid.get("provenance", {})
            metric_name = mcid.get("metric", "")
            db_bench = AggregateBenchmark(
                metric=metric_name,
                mean=mcid.get("threshold_value"),
                median=None,
                sd=None,
                range_low=None,
                range_high=None,
                p25=None,
                p75=None,
                concern_threshold=None,
                data={
                    "category": "mcid_threshold",
                    "publication_id": mcid.get("publication_id"),
                    "provenance": {
                        "page": prov.get("page"),
                        "table": prov.get("table"),
                        "quote": prov.get("quote"),
                        "context": prov.get("context")
                    }
                }
            )
            session.add(db_bench)
            benchmark_count += 1
        
        hhs_metrics_added = set()
        for hhs in data.get("outcome_benchmarks", {}).get("harris_hip_score", []):
            prov = hhs.get("provenance", {})
            metric_name = f"HHS_{hhs.get('metric', '')}_{hhs.get('publication_id', '')[:20]}"
            if metric_name in hhs_metrics_added:
                continue
            hhs_metrics_added.add(metric_name)
            
            db_bench = AggregateBenchmark(
                metric=metric_name[:100],
                mean=hhs.get("value"),
                median=None,
                sd=None,
                range_low=hhs.get("ci_lower"),
                range_high=hhs.get("ci_upper"),
                p25=None,
                p75=None,
                concern_threshold=None,
                data={
                    "category": "harris_hip_score",
                    "unit": hhs.get("unit"),
                    "publication_id": hhs.get("publication_id"),
                    "provenance": {
                        "page": prov.get("page"),
                        "table": prov.get("table"),
                        "quote": prov.get("quote"),
                        "context": prov.get("context")
                    }
                }
            )
            session.add(db_bench)
            benchmark_count += 1
        
        survival_metrics_added = set()
        for surv in data.get("outcome_benchmarks", {}).get("survival_rates", []):
            prov = surv.get("provenance", {})
            metric_name = f"survival_{surv.get('metric', '')[:30]}_{surv.get('publication_id', '')[:20]}"
            if metric_name in survival_metrics_added:
                continue
            survival_metrics_added.add(metric_name)
            
            db_bench = AggregateBenchmark(
                metric=metric_name[:100],
                mean=surv.get("value"),
                median=None,
                sd=None,
                range_low=surv.get("ci_lower"),
                range_high=surv.get("ci_upper"),
                p25=None,
                p75=None,
                concern_threshold=None,
                data={
                    "category": "survival_rate",
                    "unit": surv.get("unit", "percent"),
                    "publication_id": surv.get("publication_id"),
                    "provenance": {
                        "page": prov.get("page"),
                        "table": prov.get("table"),
                        "quote": prov.get("quote"),
                        "context": prov.get("context")
                    }
                }
            )
            session.add(db_bench)
            benchmark_count += 1
        
        session.commit()
        logger.info(f"  Added {benchmark_count} aggregate benchmarks")
        
        pub_count = session.query(LiteraturePublication).count()
        rf_count = session.query(LiteratureRiskFactor).count()
        bench_count = session.query(AggregateBenchmark).count()
        
        logger.info("=" * 60)
        logger.info("DATABASE UPDATE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Publications: {pub_count}")
        logger.info(f"Risk Factors: {rf_count}")
        logger.info(f"Aggregate Benchmarks: {bench_count}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error loading data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    load_literature_to_database()
