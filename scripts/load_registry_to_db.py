#!/usr/bin/env python3
"""
Load verified registry data to PostgreSQL database.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data.models.database import Base, RegistryBenchmark, RegistryPooledNorm

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def load_registry_data():
    """Load registry data from YAML to database."""
    yaml_path = Path("data/processed/document_as_code/registry_norms.yaml")
    
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    
    session = Session()
    
    try:
        session.query(RegistryBenchmark).delete()
        session.query(RegistryPooledNorm).delete()
        
        registries = data.get('registries', {})
        loaded = 0
        
        for registry_id, reg_data in registries.items():
            revision_reasons = []
            for reason in reg_data.get('revision_reasons', []):
                revision_reasons.append({
                    'reason': reason.get('reason'),
                    'percentage': reason.get('percentage'),
                    'description': reason.get('description'),
                })
            
            provenance = reg_data.get('provenance', {})
            
            benchmark = RegistryBenchmark(
                registry_id=registry_id,
                name=reg_data.get('name', ''),
                abbreviation=reg_data.get('abbreviation', registry_id.upper()),
                report_year=reg_data.get('report_year'),
                data_years=reg_data.get('data_period', ''),
                population=reg_data.get('population', ''),
                n_procedures=reg_data.get('n_procedures'),
                n_primary=reg_data.get('n_primary'),
                survival_1yr=reg_data.get('survival_1yr'),
                survival_2yr=reg_data.get('survival_2yr'),
                survival_5yr=reg_data.get('survival_5yr'),
                survival_10yr=reg_data.get('survival_10yr'),
                survival_15yr=reg_data.get('survival_15yr'),
                revision_rate_1yr=reg_data.get('revision_rate_1yr'),
                revision_rate_2yr=reg_data.get('revision_rate_2yr'),
                revision_reasons=revision_reasons,
                outcomes_by_indication={
                    'provenance': provenance,
                    'country': reg_data.get('country', ''),
                }
            )
            
            session.add(benchmark)
            loaded += 1
            print(f"  Loaded: {registry_id.upper()} - {reg_data.get('name', '')}")
        
        total_procedures = sum(
            r.get('n_procedures', 0) or 0 
            for r in registries.values()
        )
        
        survival_rates = {}
        for timepoint in ['1yr', '2yr', '5yr', '10yr', '15yr']:
            values = [
                r.get(f'survival_{timepoint}') 
                for r in registries.values() 
                if r.get(f'survival_{timepoint}')
            ]
            if values:
                survival_rates[timepoint] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'n_registries': len(values),
                }
        
        pooled_revision_reasons = {}
        for registry_id, reg_data in registries.items():
            for reason in reg_data.get('revision_reasons', []):
                reason_name = reason.get('reason', '')
                if reason_name not in pooled_revision_reasons:
                    pooled_revision_reasons[reason_name] = {
                        'values': [],
                        'registries': [],
                    }
                if reason.get('percentage'):
                    pooled_revision_reasons[reason_name]['values'].append(reason.get('percentage'))
                    pooled_revision_reasons[reason_name]['registries'].append(registry_id)
        
        for reason_name, reason_data in pooled_revision_reasons.items():
            values = reason_data['values']
            if values:
                pooled_revision_reasons[reason_name]['mean'] = sum(values) / len(values)
                pooled_revision_reasons[reason_name]['min'] = min(values)
                pooled_revision_reasons[reason_name]['max'] = max(values)
        
        pooled = RegistryPooledNorm(
            total_procedures=total_procedures,
            total_registries=len(registries),
            survival_rates=survival_rates,
            revision_rates={
                timepoint: 1.0 - sr.get('mean', 1.0)
                for timepoint, sr in survival_rates.items()
            },
            revision_reasons_pooled=pooled_revision_reasons,
            concern_thresholds={
                'dislocation_rate': 0.05,
                'infection_rate': 0.02,
                'fracture_rate': 0.02,
            },
            risk_thresholds={
                'high_risk_revision_rate_2yr': 0.10,
                'moderate_risk_revision_rate_2yr': 0.06,
            }
        )
        session.add(pooled)
        
        session.commit()
        print(f"\nLoaded {loaded} registry benchmarks to database")
        print(f"Total procedures across registries: {total_procedures:,}")
        print(f"Pooled survival rates: {list(survival_rates.keys())}")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("Loading verified registry data to database...")
    load_registry_data()
    print("Done!")
