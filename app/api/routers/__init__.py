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
    uc6_regulatory,
    uc7_competitive,
    uc8_sales,
    uc9_sota,
    uc10_claims,
    uc11_fda,
    chat,
    enhanced_chat,
    protocol_digitization,
    simulation,
    data_browser,
    onboarding,
    products,
)

__all__ = [
    "health",
    "uc1_readiness",
    "uc2_safety",
    "uc3_deviations",
    "uc4_risk",
    "uc5_dashboard",
    "uc6_regulatory",
    "uc7_competitive",
    "uc8_sales",
    "uc9_sota",
    "uc10_claims",
    "uc11_fda",
    "chat",
    "enhanced_chat",
    "protocol_digitization",
    "simulation",
    "data_browser",
    "onboarding",
    "products",
]
