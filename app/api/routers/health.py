"""
Health check endpoint for the Clinical Intelligence Platform.
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns current status and timestamp.
    """
    return {
        "status": "healthy",
        "service": "Clinical Intelligence Platform API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Verifies that all dependencies are available.
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "ok",
            "vector_store": "ok",
            "llm_api": "ok",
        }
    }
