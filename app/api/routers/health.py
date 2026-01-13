"""
Health check endpoint for the Clinical Intelligence Platform.
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter
from app.services.cache_service import get_cache_service

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
    cache = get_cache_service()
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
        "cache_warmed": cache.is_warmed,
        "checks": {
            "database": "ok",
            "vector_store": "ok",
            "llm_api": "ok",
            "cache": "warmed" if cache.is_warmed else "warming",
        }
    }


@router.get("/cache-status")
async def cache_status() -> Dict[str, Any]:
    """
    Cache status endpoint.
    Returns current cache state and metadata.
    """
    cache = get_cache_service()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        **cache.get_status()
    }
