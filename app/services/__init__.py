"""
Service Layer for Clinical Intelligence Platform.

Business logic services that orchestrate agents and provide
use case implementations:

- LLMService: Unified LLM interface (Gemini + Azure OpenAI)
- PromptService: Prompt loading with parameter substitution
- DeviationsService: UC3 Protocol deviation detection
- SafetyService: UC2 Safety signal detection and contextualization
- ReadinessService: UC1 Regulatory submission readiness assessment
- RiskService: UC4 Patient risk stratification
- DashboardService: UC5 Executive dashboard aggregation

Note: Services that depend on agents are NOT imported at package level
to avoid circular imports. Import them directly:
    from app.services.deviations_service import DeviationsService
"""

# Core services that don't depend on agents - safe to import at package level
from app.services.llm_service import LLMService, get_llm_service
from app.services.prompt_service import PromptService, get_prompt_service

# Lazy getters for services that depend on agents
# These avoid circular imports while still providing convenient access

_deviations_service = None
_safety_service = None
_readiness_service = None
_risk_service = None
_dashboard_service = None


def get_deviations_service():
    """Get singleton deviations service instance (lazy load)."""
    global _deviations_service
    if _deviations_service is None:
        from app.services.deviations_service import DeviationsService
        _deviations_service = DeviationsService()
    return _deviations_service


def get_safety_service():
    """Get singleton safety service instance (lazy load)."""
    global _safety_service
    if _safety_service is None:
        from app.services.safety_service import SafetyService
        _safety_service = SafetyService()
    return _safety_service


def get_readiness_service():
    """Get singleton readiness service instance (lazy load)."""
    global _readiness_service
    if _readiness_service is None:
        from app.services.readiness_service import ReadinessService
        _readiness_service = ReadinessService()
    return _readiness_service


def get_risk_service():
    """Get singleton risk service instance (lazy load)."""
    global _risk_service
    if _risk_service is None:
        from app.services.risk_service import RiskService
        _risk_service = RiskService()
    return _risk_service


def get_dashboard_service():
    """Get singleton dashboard service instance (lazy load)."""
    global _dashboard_service
    if _dashboard_service is None:
        from app.services.dashboard_service import DashboardService
        _dashboard_service = DashboardService()
    return _dashboard_service


__all__ = [
    # Core services
    "LLMService",
    "get_llm_service",
    "PromptService",
    "get_prompt_service",
    # Lazy-loaded service getters
    "get_deviations_service",
    "get_safety_service",
    "get_readiness_service",
    "get_risk_service",
    "get_dashboard_service",
]
