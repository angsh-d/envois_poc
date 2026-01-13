"""
Clinical Intelligence Platform - FastAPI Application
Main entry point for the API server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routers import uc1_readiness, uc2_safety, uc3_deviations, uc4_risk, uc5_dashboard, health, chat, protocol_digitization

# Initialize FastAPI app
app = FastAPI(
    title="Clinical Intelligence Platform API",
    description="AI-powered clinical study analytics for H-34 DELTA Revision Cup Study",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(uc1_readiness.router, prefix="/api/v1/uc1", tags=["UC1: Regulatory Readiness"])
app.include_router(uc2_safety.router, prefix="/api/v1/uc2", tags=["UC2: Safety Signals"])
app.include_router(uc3_deviations.router, prefix="/api/v1/uc3", tags=["UC3: Protocol Deviations"])
app.include_router(uc4_risk.router, prefix="/api/v1/uc4", tags=["UC4: Risk Stratification"])
app.include_router(uc5_dashboard.router, prefix="/api/v1/uc5", tags=["UC5: Executive Dashboard"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(protocol_digitization.router, prefix="/api/v1/protocol", tags=["Protocol Digitization"])


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # Ensure log directory exists
    settings.get_log_dir()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
