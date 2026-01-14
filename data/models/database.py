"""
SQLAlchemy database models for H-34 Clinical Intelligence Platform.
All structured data is stored in PostgreSQL tables.
"""
import os
from datetime import date, datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Text, Boolean, 
    Date, DateTime, JSON, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
import enum

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
) if DATABASE_URL else None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()


def get_db():
    """Get database session."""
    if SessionLocal is None:
        raise RuntimeError("Database not configured - DATABASE_URL not set")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ProtocolRule(Base):
    """Protocol rules and configuration.
    
    Protocol H-34 v2.0 Sample Size (p.11):
    - sample_size_target: 49 (total enrollment accounting for 40% LTFU)
    - sample_size_evaluable: 29 (required for 90% power on HHS endpoint)
    """
    __tablename__ = "protocol_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(String(50), nullable=False, index=True)
    protocol_version = Column(String(20), nullable=False)
    effective_date = Column(Date)
    title = Column(String(500))
    sponsor = Column(String(200))
    phase = Column(String(50))
    sample_size_target = Column(Integer)
    sample_size_evaluable = Column(Integer)
    safety_thresholds = Column(JSON, default={})
    deviation_classification = Column(JSON, default={})
    inclusion_criteria = Column(JSON, default=[])
    exclusion_criteria = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    visits = relationship("ProtocolVisit", back_populates="protocol")
    endpoints = relationship("ProtocolEndpoint", back_populates="protocol")


class ProtocolVisit(Base):
    """Protocol visit windows."""
    __tablename__ = "protocol_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(Integer, ForeignKey("protocol_rules.id"), nullable=False)
    visit_id = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    target_day = Column(Integer, nullable=False)
    window_minus = Column(Integer, default=0)
    window_plus = Column(Integer, default=0)
    required_assessments = Column(JSON, default=[])
    is_primary_endpoint = Column(Boolean, default=False)
    sequence = Column(Integer, default=0)

    protocol = relationship("ProtocolRule", back_populates="visits")


class ProtocolEndpoint(Base):
    """Protocol endpoints."""
    __tablename__ = "protocol_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(Integer, ForeignKey("protocol_rules.id"), nullable=False)
    endpoint_id = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    endpoint_type = Column(String(20), default="secondary")
    timepoint = Column(String(50))
    calculation = Column(String(500))
    success_threshold = Column(Float)
    mcid_threshold = Column(Float)
    success_criterion = Column(String(500))

    protocol = relationship("ProtocolRule", back_populates="endpoints")


class LiteraturePublication(Base):
    """Literature publications and benchmarks."""
    __tablename__ = "literature_publications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    year = Column(Integer)
    journal = Column(String(300))
    n_patients = Column(Integer)
    follow_up_years = Column(Float)
    revision_indication = Column(String(100))
    benchmarks = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    risk_factors = relationship("LiteratureRiskFactor", back_populates="publication")


class LiteratureRiskFactor(Base):
    """Risk factors from literature."""
    __tablename__ = "literature_risk_factors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    publication_id = Column(Integer, ForeignKey("literature_publications.id"))
    factor = Column(String(100), nullable=False)
    hazard_ratio = Column(Float, nullable=False)
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    outcome = Column(String(100))
    source = Column(String(100))

    publication = relationship("LiteraturePublication", back_populates="risk_factors")

    __table_args__ = (
        Index("idx_risk_factors_outcome", "outcome"),
    )


class AggregateBenchmark(Base):
    """Aggregate benchmarks from literature."""
    __tablename__ = "aggregate_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric = Column(String(100), unique=True, nullable=False)
    mean = Column(Float)
    median = Column(Float)
    sd = Column(Float)
    range_low = Column(Float)
    range_high = Column(Float)
    p25 = Column(Float)
    p75 = Column(Float)
    concern_threshold = Column(Float)
    data = Column(JSON, default={})


class RegistryBenchmark(Base):
    """Registry benchmarks."""
    __tablename__ = "registry_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registry_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    abbreviation = Column(String(50))
    report_year = Column(Integer)
    data_years = Column(String(50))
    population = Column(String(200))
    n_procedures = Column(Integer)
    n_primary = Column(Integer)
    revision_burden = Column(Float)
    survival_1yr = Column(Float)
    survival_2yr = Column(Float)
    survival_5yr = Column(Float)
    survival_10yr = Column(Float)
    survival_15yr = Column(Float)
    revision_rate_1yr = Column(Float)
    revision_rate_2yr = Column(Float)
    revision_rate_median = Column(Float)
    revision_rate_p75 = Column(Float)
    revision_rate_p95 = Column(Float)
    revision_reasons = Column(JSON, default=[])
    outcomes_by_indication = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class RegistryPooledNorm(Base):
    """Pooled norms across registries."""
    __tablename__ = "registry_pooled_norms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total_procedures = Column(Integer)
    total_registries = Column(Integer)
    survival_rates = Column(JSON, default={})
    revision_rates = Column(JSON, default={})
    revision_reasons_pooled = Column(JSON, default={})
    concern_thresholds = Column(JSON, default={})
    risk_thresholds = Column(JSON, default={})


class StudyPatient(Base):
    """Study patients."""
    __tablename__ = "study_patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), unique=True, nullable=False, index=True)
    facility = Column(String(200))
    year_of_birth = Column(Integer)
    weight = Column(Float)
    height = Column(Float)
    bmi = Column(Float)
    gender = Column(String(20))
    race = Column(String(50))
    activity_level = Column(String(100))
    work_status = Column(String(100))
    smoking_habits = Column(String(100))
    alcohol_habits = Column(String(100))
    concomitant_medications = Column(Text)
    screening_date = Column(Date)
    consent_date = Column(Date)
    enrolled = Column(String(20))
    status = Column(String(50))
    surgery_date = Column(Date)
    affected_side = Column(String(20))
    primary_diagnosis = Column(String(200))
    medical_history = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    adverse_events = relationship("StudyAdverseEvent", back_populates="patient")
    scores = relationship("StudyScore", back_populates="patient")
    visits = relationship("StudyVisit", back_populates="patient")


class StudyAdverseEvent(Base):
    """Adverse events from study."""
    __tablename__ = "study_adverse_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("study_patients.id"), nullable=False)
    ae_id = Column(String(50))
    report_type = Column(String(50))
    initial_report_date = Column(Date)
    report_date = Column(Date)
    onset_date = Column(Date)
    ae_title = Column(String(500))
    event_narrative = Column(Text)
    is_sae = Column(Boolean, default=False)
    classification = Column(String(100))
    outcome = Column(String(100))
    end_date = Column(Date)
    severity = Column(String(50))
    device_relationship = Column(String(100))
    procedure_relationship = Column(String(100))
    expectedness = Column(String(50))
    action_taken = Column(String(200))
    device_removed = Column(Boolean, default=False)
    device_removal_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("StudyPatient", back_populates="adverse_events")

    __table_args__ = (
        Index("idx_adverse_events_severity", "severity"),
        Index("idx_adverse_events_sae", "is_sae"),
    )


class StudyScore(Base):
    """HHS and OHS scores."""
    __tablename__ = "study_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("study_patients.id"), nullable=False)
    score_type = Column(String(10), nullable=False)
    follow_up = Column(String(50))
    follow_up_date = Column(Date)
    total_score = Column(Float)
    score_category = Column(String(50))
    components = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("StudyPatient", back_populates="scores")

    __table_args__ = (
        Index("idx_scores_type_followup", "score_type", "follow_up"),
    )


class StudyVisit(Base):
    """Study visits and assessments."""
    __tablename__ = "study_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("study_patients.id"), nullable=False)
    visit_type = Column(String(50), nullable=False)
    visit_date = Column(Date)
    days_from_surgery = Column(Integer)
    visit_data = Column(JSON, default={})
    radiographic_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("StudyPatient", back_populates="visits")

    __table_args__ = (
        Index("idx_visits_type", "visit_type"),
    )


class StudySurgery(Base):
    """Surgery and intraoperative data."""
    __tablename__ = "study_surgeries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("study_patients.id"), nullable=False, unique=True)
    surgery_date = Column(Date)
    surgical_approach = Column(String(100))
    anaesthesia = Column(String(100))
    surgery_time_minutes = Column(Integer)
    intraoperative_complications = Column(Text)
    stem_type = Column(String(100))
    stem_size = Column(String(50))
    cup_type = Column(String(100))
    cup_diameter = Column(Float)
    cup_liner_material = Column(String(100))
    head_type = Column(String(100))
    head_material = Column(String(100))
    head_diameter = Column(Float)
    implant_details = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class HazardRatioEstimate(Base):
    """Extracted hazard ratios."""
    __tablename__ = "hazard_ratio_estimates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String(200))
    extraction_date = Column(DateTime, default=datetime.utcnow)
    factor = Column(String(100), nullable=False)
    hazard_ratio = Column(Float, nullable=False)
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    p_value = Column(Float)
    outcome = Column(String(100))
    context = Column(Text)

    __table_args__ = (
        Index("idx_hazard_ratios_factor", "factor"),
    )


class ProtocolDocument(Base):
    """Protocol JSON documents (USDM, SOA, Eligibility)."""
    __tablename__ = "protocol_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_type = Column(String(50), nullable=False, unique=True)
    document_name = Column(String(200))
    content = Column(JSON, nullable=False)
    source_file = Column(String(200))
    extraction_date = Column(DateTime, default=datetime.utcnow)
    version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Initialize database tables."""
    if engine is None:
        raise RuntimeError("Database not configured")
    Base.metadata.create_all(bind=engine)
    return True


def drop_all_tables():
    """Drop all tables (for testing only)."""
    if engine is None:
        raise RuntimeError("Database not configured")
    Base.metadata.drop_all(bind=engine)
    return True
