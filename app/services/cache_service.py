"""
Cache Service for Clinical Intelligence Platform.

Provides in-memory caching with startup precomputation and background refresh
to eliminate long initial load times for dashboard data.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached data entry with metadata."""
    data: Any
    generated_at: datetime
    expires_at: datetime
    is_stale: bool = False


class CacheService:
    """
    In-memory cache with TTL and background refresh.
    
    Features:
    - Startup precomputation (warmers)
    - Background refresh every 4 hours
    - Stale-while-revalidate pattern
    """
    
    def __init__(self, ttl_minutes: int = 2880):  # 48 hours default
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._ttl = timedelta(minutes=ttl_minutes)
        self._is_warming = False
        self._warmup_complete = asyncio.Event()
        self._refresh_task: Optional[asyncio.Task] = None
        
    @property
    def is_warmed(self) -> bool:
        """Check if initial warmup is complete."""
        return self._warmup_complete.is_set()
    
    async def wait_for_warmup(self, timeout: float = 60.0) -> bool:
        """Wait for initial warmup to complete."""
        try:
            await asyncio.wait_for(self._warmup_complete.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data with metadata.
        
        Returns:
            Dict with 'data', 'generated_at', 'is_stale' or None if not cached
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            now = datetime.utcnow()
            is_expired = now > entry.expires_at
            
            return {
                "data": entry.data,
                "generated_at": entry.generated_at.isoformat(),
                "is_stale": is_expired or entry.is_stale,
                "cache_age_seconds": (now - entry.generated_at).total_seconds(),
            }
    
    async def set(self, key: str, data: Any) -> None:
        """Store data in cache."""
        async with self._lock:
            now = datetime.utcnow()
            self._cache[key] = CacheEntry(
                data=data,
                generated_at=now,
                expires_at=now + self._ttl,
            )
            logger.info(f"Cache updated: {key}")
    
    async def invalidate(self, key: str) -> None:
        """Mark cache entry as stale (will be refreshed but still served)."""
        async with self._lock:
            if key in self._cache:
                self._cache[key].is_stale = True
    
    async def clear(self) -> None:
        """Clear all cached data."""
        async with self._lock:
            self._cache.clear()
            self._warmup_complete.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get cache status for monitoring."""
        now = datetime.utcnow()
        entries = {}
        for key, entry in self._cache.items():
            entries[key] = {
                "generated_at": entry.generated_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "is_stale": entry.is_stale or now > entry.expires_at,
                "age_seconds": (now - entry.generated_at).total_seconds(),
            }
        return {
            "is_warmed": self.is_warmed,
            "is_warming": self._is_warming,
            "entries": entries,
            "ttl_minutes": self._ttl.total_seconds() / 60,
        }


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(ttl_minutes=2880)  # 48 hours
    return _cache_service


async def warmup_cache() -> None:
    """
    Precompute and cache all data on startup.
    
    This runs in the background and populates the cache
    so all requests are fast.
    """
    cache = get_cache_service()
    
    if cache._is_warming:
        logger.info("Cache warmup already in progress")
        return
    
    cache._is_warming = True
    logger.info("Starting cache warmup...")
    
    try:
        start_time = datetime.utcnow()
        
        # Dashboard service endpoints
        try:
            from app.services.dashboard_service import get_dashboard_service
            dashboard = get_dashboard_service()
            
            logger.info("Warming: executive-summary")
            summary = await dashboard.get_executive_summary()
            await cache.set("executive-summary", summary)
            
            logger.info("Warming: study-progress")
            progress = await dashboard.get_study_progress()
            await cache.set("study-progress", progress)
            
            logger.info("Warming: data-quality")
            quality = await dashboard.get_data_quality_summary()
            await cache.set("data-quality", quality)
            
            logger.info("Warming: safety-dashboard")
            safety = await dashboard.get_safety_dashboard()
            await cache.set("safety-dashboard", safety)
            
            logger.info("Warming: benchmarks")
            benchmarks = await dashboard.get_benchmark_comparison()
            await cache.set("benchmarks", benchmarks)
        except Exception as e:
            logger.error(f"Failed to warm dashboard endpoints: {e}")
        
        # Readiness service endpoints
        try:
            from app.services.readiness_service import get_readiness_service
            readiness = get_readiness_service()
            
            logger.info("Warming: readiness-assessment")
            readiness_data = await readiness.get_readiness_assessment()
            await cache.set("readiness-assessment", readiness_data)
        except Exception as e:
            logger.error(f"Failed to warm readiness: {e}")
        
        # Safety service endpoints
        try:
            from app.services.safety_service import get_safety_service
            safety_svc = get_safety_service()
            
            logger.info("Warming: safety-summary")
            safety_data = await safety_svc.get_safety_summary()
            await cache.set("safety-summary", safety_data)
        except Exception as e:
            logger.error(f"Failed to warm safety: {e}")
        
        # Deviations service endpoints
        try:
            from app.services.deviations_service import get_deviations_service
            deviations = get_deviations_service()
            
            logger.info("Warming: deviations-summary")
            deviations_data = await deviations.get_study_deviations()
            await cache.set("deviations-summary", deviations_data)
        except Exception as e:
            logger.error(f"Failed to warm deviations: {e}")
        
        # Risk service endpoints
        try:
            from app.services.risk_service import get_risk_service
            risk = get_risk_service()
            
            logger.info("Warming: risk-population")
            risk_data = await risk.get_population_risk()
            await cache.set("risk-population", risk_data)
        except Exception as e:
            logger.error(f"Failed to warm risk: {e}")
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Cache warmup complete in {elapsed:.1f}s")
        
        cache._warmup_complete.set()
        
    except Exception as e:
        logger.error(f"Cache warmup failed: {e}")
    finally:
        cache._is_warming = False


async def start_background_refresh(interval_minutes: int = 240) -> asyncio.Task:  # 4 hours
    """
    Start background task to periodically refresh cache.
    
    Args:
        interval_minutes: Refresh interval
        
    Returns:
        The background task
    """
    async def refresh_loop():
        cache = get_cache_service()
        await cache.wait_for_warmup(timeout=120)
        
        while True:
            await asyncio.sleep(interval_minutes * 60)
            logger.info("Starting periodic cache refresh...")
            try:
                await warmup_cache()
            except Exception as e:
                logger.error(f"Periodic cache refresh failed: {e}")
    
    task = asyncio.create_task(refresh_loop())
    return task
