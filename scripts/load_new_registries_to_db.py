#!/usr/bin/env python3
"""
Load newly extracted registry data (NAR, NZJR, DHR, EPRD) to PostgreSQL database.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data.models.database import RegistryBenchmark

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def load_new_registries():
    """Load new registry data from extracted JSON to database."""
    json_path = Path("data/processed/extracted_registries_new.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    session = Session()
    
    try:
        loaded = 0
        
        for registry_id, reg_data in data.items():
            existing = session.query(RegistryBenchmark).filter_by(registry_id=registry_id).first()
            if existing:
                session.delete(existing)
                session.flush()
                print(f"  Removed existing: {registry_id.upper()}")
            
            survival = reg_data.get('survival_rates', {})
            
            def get_rate(timepoint):
                rate_data = survival.get(timepoint, {})
                return rate_data.get('rate') if rate_data else None
            
            revision_reasons = []
            for reason in reg_data.get('revision_reasons', []):
                pct = reason.get('percentage')
                if pct is not None and pct > 1:
                    pct = pct / 100.0
                revision_reasons.append({
                    'reason': reason.get('reason'),
                    'percentage': pct,
                    'description': reason.get('description'),
                    'page': reason.get('page'),
                    'table_or_figure': reason.get('table_or_figure'),
                })
            
            provenance = {
                'extraction_notes': reg_data.get('provenance_notes', ''),
                'notes': reg_data.get('notes', ''),
                'source_file': reg_data.get('source_file', ''),
                'survival_provenance': {}
            }
            for timepoint in ['1yr', '2yr', '5yr', '10yr', '15yr']:
                rate_data = survival.get(timepoint, {})
                if rate_data and rate_data.get('rate'):
                    provenance['survival_provenance'][timepoint] = {
                        'page': rate_data.get('page'),
                        'table_or_figure': rate_data.get('table_or_figure'),
                        'exact_quote': rate_data.get('exact_quote'),
                    }
            
            benchmark = RegistryBenchmark(
                registry_id=registry_id,
                name=reg_data.get('registry_name', ''),
                abbreviation=reg_data.get('abbreviation', registry_id.upper()),
                report_year=reg_data.get('report_year'),
                data_years=reg_data.get('data_period', ''),
                population=reg_data.get('population', ''),
                n_procedures=reg_data.get('n_procedures'),
                survival_1yr=get_rate('1yr'),
                survival_2yr=get_rate('2yr'),
                survival_5yr=get_rate('5yr'),
                survival_10yr=get_rate('10yr'),
                survival_15yr=get_rate('15yr'),
                revision_reasons=revision_reasons,
                outcomes_by_indication={
                    'provenance': provenance,
                    'country': reg_data.get('country', ''),
                }
            )
            
            session.add(benchmark)
            loaded += 1
            
            rates = []
            for tp in ['1yr', '5yr', '10yr', '15yr']:
                rate = get_rate(tp)
                if rate:
                    rates.append(f"{tp}={rate*100:.1f}%")
            
            print(f"  Loaded: {reg_data.get('abbreviation')} ({reg_data.get('country')}) - {', '.join(rates)}")
        
        session.commit()
        print(f"\nSuccessfully loaded {loaded} new registries")
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def verify_database():
    """Verify all registry data in database."""
    session = Session()
    
    try:
        registries = session.query(RegistryBenchmark).all()
        
        print("\n" + "=" * 60)
        print("REGISTRY BENCHMARKS IN DATABASE")
        print("=" * 60)
        
        revision_count = 0
        for reg in registries:
            population_label = "REVISION" if reg.population == "revision_tha" else "PRIMARY"
            print(f"\n{reg.abbreviation} ({reg.name})")
            print(f"  Population: {population_label}")
            print(f"  Data Period: {reg.data_years}")
            print(f"  N Procedures: {reg.n_procedures:,}" if reg.n_procedures else "  N Procedures: N/A")
            
            rates = []
            if reg.survival_1yr: rates.append(f"1yr={reg.survival_1yr*100:.1f}%")
            if reg.survival_2yr: rates.append(f"2yr={reg.survival_2yr*100:.1f}%")
            if reg.survival_5yr: rates.append(f"5yr={reg.survival_5yr*100:.1f}%")
            if reg.survival_10yr: rates.append(f"10yr={reg.survival_10yr*100:.1f}%")
            if reg.survival_15yr: rates.append(f"15yr={reg.survival_15yr*100:.1f}%")
            print(f"  Survival: {', '.join(rates) if rates else 'N/A'}")
            
            if reg.population == "revision_tha":
                revision_count += 1
        
        print(f"\n{'=' * 60}")
        print(f"Total registries: {len(registries)} ({revision_count} with revision THA data)")
        print("=" * 60)
        
    finally:
        session.close()


if __name__ == "__main__":
    print("Loading new registry data to database...")
    load_new_registries()
    verify_database()
