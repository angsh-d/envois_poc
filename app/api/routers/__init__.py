"""
API routers for the Clinical Intelligence Platform.
Each use case has its own router module.
"""
from app.api.routers import (
    health,
    uc1_readiness,
    uc2_safety,
    uc3_deviations,
    uc4_risk,
    uc5_dashboard,
    protocol_digitization,
    simulation,
    data_browser,
)

__all__ = [
    "health",
    "uc1_readiness",
    "uc2_safety",
    "uc3_deviations",
    "uc4_risk",
    "uc5_dashboard",
    "protocol_digitization",
    "simulation",
    "data_browser",
]
