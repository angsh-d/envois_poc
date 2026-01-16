"""
Data Browser API Router.
Provides endpoints for viewing and editing database tables.
"""
import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from data.models.database import (
    SessionLocal, Base, engine,
    StudyPatient, StudyAdverseEvent, StudyScore, StudySurgery, StudyVisit,
    RegistryBenchmark, LiteraturePublication, ProtocolRule,
    ProtocolVisit, ProtocolEndpoint, LiteratureRiskFactor,
    AggregateBenchmark, RegistryPooledNorm, HazardRatioEstimate, ProtocolDocument
)

router = APIRouter()

# Map table names to SQLAlchemy models
TABLE_MODELS = {
    "study_patients": StudyPatient,
    "study_adverse_events": StudyAdverseEvent,
    "study_scores": StudyScore,
    "study_surgeries": StudySurgery,
    "study_visits": StudyVisit,
    "registry_benchmarks": RegistryBenchmark,
    "literature_publications": LiteraturePublication,
    "protocol_rules": ProtocolRule,
    "protocol_visits": ProtocolVisit,
    "protocol_endpoints": ProtocolEndpoint,
    "literature_risk_factors": LiteratureRiskFactor,
    "aggregate_benchmarks": AggregateBenchmark,
    "registry_pooled_norms": RegistryPooledNorm,
    "hazard_ratio_estimates": HazardRatioEstimate,
    "protocol_documents": ProtocolDocument,
}

TABLE_DESCRIPTIONS = {
    "study_patients": "Patient demographics and enrollment data",
    "study_adverse_events": "Adverse events reported during study",
    "study_scores": "HHS and OHS functional scores",
    "study_surgeries": "Surgery and intraoperative data",
    "study_visits": "Patient visit records",
    "registry_benchmarks": "International registry benchmark data",
    "literature_publications": "Literature publications and benchmarks",
    "protocol_rules": "Protocol configuration and rules",
    "protocol_visits": "Protocol visit windows",
    "protocol_endpoints": "Protocol endpoints",
    "literature_risk_factors": "Risk factors from literature",
    "aggregate_benchmarks": "Aggregate benchmark statistics",
    "registry_pooled_norms": "Pooled norms across registries",
    "hazard_ratio_estimates": "Extracted hazard ratios",
    "protocol_documents": "Protocol JSON documents",
}


class TableInfo(BaseModel):
    name: str
    row_count: int
    description: str


class ColumnSchema(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool


class TableDataResponse(BaseModel):
    rows: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    columns: List[ColumnSchema]


def serialize_value(value: Any) -> Any:
    """Serialize a value for JSON output."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return value
    return value


def row_to_dict(row: Any, columns: List[str]) -> Dict[str, Any]:
    """Convert a SQLAlchemy model instance to a dictionary."""
    result = {}
    for col in columns:
        value = getattr(row, col, None)
        result[col] = serialize_value(value)
    return result


@router.get("/tables", response_model=List[TableInfo])
async def list_tables():
    """List all browsable tables with row counts."""
    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured")

    tables = []
    db = SessionLocal()
    try:
        for table_name, model in TABLE_MODELS.items():
            try:
                count = db.query(model).count()
                tables.append(TableInfo(
                    name=table_name,
                    row_count=count,
                    description=TABLE_DESCRIPTIONS.get(table_name, "")
                ))
            except Exception:
                tables.append(TableInfo(
                    name=table_name,
                    row_count=0,
                    description=TABLE_DESCRIPTIONS.get(table_name, "")
                ))
    finally:
        db.close()

    return sorted(tables, key=lambda t: t.name)


@router.get("/tables/{table_name}/schema", response_model=List[ColumnSchema])
async def get_table_schema(table_name: str):
    """Get column schema for a table."""
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    model = TABLE_MODELS[table_name]
    inspector = inspect(model)

    columns = []
    for col in inspector.mapper.columns:
        columns.append(ColumnSchema(
            name=col.name,
            type=str(col.type),
            nullable=col.nullable or False,
            primary_key=col.primary_key
        ))

    return columns


@router.get("/tables/{table_name}", response_model=TableDataResponse)
async def get_table_data(
    table_name: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default=None),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$")
):
    """Get paginated table data."""
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured")

    model = TABLE_MODELS[table_name]
    inspector = inspect(model)
    column_names = [col.name for col in inspector.mapper.columns]

    db = SessionLocal()
    try:
        query = db.query(model)

        # Apply sorting
        if sort_by and sort_by in column_names:
            col = getattr(model, sort_by)
            query = query.order_by(col.desc() if sort_dir == "desc" else col.asc())
        else:
            # Default sort by primary key
            pk_cols = [col for col in inspector.mapper.columns if col.primary_key]
            if pk_cols:
                query = query.order_by(pk_cols[0].asc())

        total = query.count()
        offset = (page - 1) * limit
        rows = query.offset(offset).limit(limit).all()

        # Build column schema
        columns = []
        for col in inspector.mapper.columns:
            columns.append(ColumnSchema(
                name=col.name,
                type=str(col.type),
                nullable=col.nullable or False,
                primary_key=col.primary_key
            ))

        return TableDataResponse(
            rows=[row_to_dict(row, column_names) for row in rows],
            total=total,
            page=page,
            limit=limit,
            columns=columns
        )
    finally:
        db.close()


@router.put("/tables/{table_name}/{row_id}")
async def update_table_row(
    table_name: str,
    row_id: int,
    data: Dict[str, Any]
):
    """Update a single row in a table."""
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured")

    model = TABLE_MODELS[table_name]
    inspector = inspect(model)
    column_names = [col.name for col in inspector.mapper.columns]

    # Find primary key column
    pk_cols = [col.name for col in inspector.mapper.columns if col.primary_key]
    if not pk_cols:
        raise HTTPException(status_code=400, detail="Table has no primary key")
    pk_col = pk_cols[0]

    db = SessionLocal()
    try:
        row = db.query(model).filter(getattr(model, pk_col) == row_id).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Row with {pk_col}={row_id} not found")

        # Update allowed fields
        for key, value in data.items():
            if key in column_names and key != pk_col:
                setattr(row, key, value)

        db.commit()
        db.refresh(row)

        return {"success": True, "updated": row_to_dict(row, column_names)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
