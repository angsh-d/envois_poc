"""
Onboarding API Router for Product Data Steward Configuration.

AI-first onboarding experience for configuring new products with
intelligent data source discovery and recommendations.
Supports Server-Sent Events (SSE) for real-time progress tracking.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Header, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.onboarding_service import get_onboarding_service
from app.services.database_service import get_database_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Error Message Formatting ====================

def format_user_error(error: str, context: str = "") -> str:
    """
    Format an internal error into a user-friendly message.

    Args:
        error: The original error message
        context: Additional context (e.g., "during discovery")

    Returns:
        User-friendly error message
    """
    # Map common internal errors to user-friendly messages
    error_lower = error.lower() if error else ""

    if "timed out" in error_lower:
        return f"The operation{' ' + context if context else ''} took too long. Please try again or contact support if the issue persists."

    if "network error" in error_lower or "connection" in error_lower:
        return f"Unable to connect to external services{' ' + context if context else ''}. Please check your internet connection and try again."

    if "rate limit" in error_lower or "429" in error_lower:
        return f"Service temporarily unavailable due to high demand{' ' + context if context else ''}. Please wait a moment and try again."

    if "session not found" in error_lower:
        return "This configuration session could not be found. It may have expired or been deleted."

    if "unauthorized" in error_lower or "permission" in error_lower:
        return "You don't have permission to access this session."

    if "fda" in error_lower:
        return "Unable to retrieve FDA data. The FDA database may be temporarily unavailable."

    if "pubmed" in error_lower or "literature" in error_lower:
        return "Unable to search for publications. PubMed may be temporarily unavailable."

    if "llm" in error_lower or "model" in error_lower:
        return "The AI service is temporarily unavailable. Please try again in a moment."

    # Default message for unknown errors
    return f"An unexpected error occurred{' ' + context if context else ''}. Please try again or contact support."


# ==================== Session Authorization ====================

async def get_current_user_id(
    x_user_id: Optional[str] = Header(None, description="User ID for session authorization")
) -> Optional[str]:
    """
    Extract user ID from request headers.

    In production, this would validate a JWT token or session cookie.
    For now, we use a simple header-based approach.
    """
    return x_user_id


async def verify_session_access(
    session_id: str,
    user_id: Optional[str] = None
) -> bool:
    """
    Verify the current user has access to the specified session.

    Args:
        session_id: The session to check access for
        user_id: The current user's ID

    Returns:
        True if access is allowed

    Raises:
        HTTPException: If access is denied
    """
    # If no user authentication, allow access (development mode)
    if user_id is None:
        logger.warning(f"No user_id provided for session {session_id} - allowing access (no auth)")
        return True

    db = get_database_service()

    if not db.verify_session_ownership(session_id, user_id):
        logger.warning(f"User {user_id} attempted unauthorized access to session {session_id}")
        raise HTTPException(
            status_code=403,
            detail="Access denied: You do not have permission to access this session"
        )

    return True


# Request Models
class StartOnboardingRequest(BaseModel):
    """Request to start a new onboarding session."""
    product_name: str = Field(..., description="Name of the product to configure")
    category: str = Field(default="", description="Product category (e.g., Hip Reconstruction)")
    indication: str = Field(default="", description="Primary indication (e.g., Revision THA)")
    study_phase: str = Field(default="", description="Study phase (e.g., Post-Market Surveillance)")
    protocol_id: str = Field(..., description="Protocol identifier (required - no default)")
    technologies: List[str] = Field(default_factory=list, description="Key technologies (e.g., Trabecular Titanium)")


class AcceptRecommendationsRequest(BaseModel):
    """Request to accept AI recommendations."""
    accepted_sources: List[str] = Field(default_factory=list, description="List of accepted data source IDs")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration settings")


# Response Models
class PhaseProgress(BaseModel):
    """Progress for a single phase."""
    completed: bool = Field(..., description="Whether the phase is complete")
    progress: int = Field(..., description="Progress percentage (0-100)")


class DiscoveryAgentStatus(BaseModel):
    """Status of a discovery agent."""
    status: str = Field(..., description="Agent status (queued, running, completed)")
    progress: int = Field(..., description="Progress percentage")
    items_found: Optional[int] = Field(None, description="Number of items found")


class DataSourceRecommendation(BaseModel):
    """A recommended data source."""
    source: str = Field(..., description="Data source name")
    selected: bool = Field(..., description="Whether selected by default")
    enabled_insights: List[str] = Field(default_factory=list, description="Insights enabled by this source")
    data_preview: Optional[str] = Field(None, description="Preview of available data")


class ResearchReportStatus(BaseModel):
    """Status of a deep research report."""
    status: str = Field(..., description="Report status (queued, running, completed)")
    progress: int = Field(..., description="Progress percentage")
    pages: Optional[int] = Field(None, description="Number of pages if completed")
    sections: Optional[List[str]] = Field(None, description="Report sections")


class OnboardingSessionResponse(BaseModel):
    """Response for onboarding session operations."""
    session_id: str = Field(..., description="Unique session identifier")
    product_name: Optional[str] = Field(None, description="Product name")
    current_phase: str = Field(..., description="Current onboarding phase")
    phase_progress: Dict[str, PhaseProgress] = Field(default_factory=dict)
    message: str = Field(..., description="AI assistant message")
    success: bool = Field(..., description="Operation success status")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Context analysis results")
    discovery_results: Optional[Dict[str, Any]] = Field(None, description="Discovery results")
    recommendations: Optional[Dict[str, Any]] = Field(None, description="Data source recommendations")
    research_status: Optional[Dict[str, Any]] = Field(None, description="Deep research status")
    intelligence_brief: Optional[Dict[str, Any]] = Field(None, description="Final intelligence brief")
    configuration_complete: Optional[bool] = Field(None, description="Whether configuration is complete")


class SessionSummary(BaseModel):
    """Summary of an onboarding session."""
    session_id: str = Field(..., description="Session identifier")
    product_name: str = Field(..., description="Product name")
    current_phase: str = Field(..., description="Current phase")
    created_at: str = Field(..., description="Creation timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp if complete")


class SessionListResponse(BaseModel):
    """Response for listing sessions."""
    sessions: List[SessionSummary] = Field(default_factory=list)
    total: int = Field(..., description="Total number of sessions")


# Endpoints
@router.post("/start", response_model=OnboardingSessionResponse)
async def start_onboarding(
    request: StartOnboardingRequest,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Start a new onboarding session for a product.

    Creates a new session and runs initial context analysis.
    Returns AI welcome message and initial recommendations.
    """
    service = get_onboarding_service()

    result = await service.start_session(
        product_name=request.product_name,
        category=request.category,
        indication=request.indication,
        study_phase=request.study_phase,
        protocol_id=request.protocol_id,
        technologies=request.technologies,
        user_id=user_id,  # Associate session with user
    )

    return OnboardingSessionResponse(
        session_id=result["session_id"],
        product_name=request.product_name,
        current_phase=result["current_phase"],
        phase_progress=result.get("phase_progress", {}),
        message=result["message"],
        success=result["success"],
        analysis=result.get("analysis"),
    )


@router.get("/{session_id}/status", response_model=OnboardingSessionResponse)
async def get_session_status(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Get current status of an onboarding session.

    Returns detailed progress across all phases.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = service.get_session_status(session_id)

    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    return OnboardingSessionResponse(
        session_id=result["session_id"],
        product_name=result.get("product_name"),
        current_phase=result["current_phase"],
        phase_progress=result.get("phase_progress", {}),
        message="Session status retrieved",
        success=True,
        discovery_results=result.get("discovery_results"),
        recommendations=result.get("recommendations"),
        research_status=result.get("research_reports"),
        intelligence_brief=result.get("intelligence_brief"),
    )


@router.post("/{session_id}/discovery", response_model=OnboardingSessionResponse)
async def run_discovery(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Run discovery phase to find relevant data sources.

    Executes discovery agents in parallel:
    - Literature discovery
    - Registry discovery
    - FDA surveillance discovery
    - Competitive product discovery
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = await service.run_discovery(session_id)

    if not result.get("success"):
        error_msg = result.get("error", "Discovery failed")
        if error_msg == "Session not found":
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg, "during discovery"))

    # Include any partial errors in the response
    errors = result.get("errors")
    message = result["message"]
    if errors:
        message = f"{message} Note: Some data sources were unavailable."

    return OnboardingSessionResponse(
        session_id=result["session_id"],
        current_phase=result["current_phase"],
        phase_progress=result.get("phase_progress", {}),
        message=message,
        success=True,
        discovery_results=result.get("discovery_results"),
    )


@router.post("/{session_id}/recommendations", response_model=OnboardingSessionResponse)
async def generate_recommendations(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Generate data source recommendations.

    Creates AI-driven recommendations with insight explanations
    for each data source.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = await service.generate_recommendations(session_id)

    if not result.get("success"):
        error_msg = result.get("error", "Recommendation generation failed")
        if error_msg == "Session not found":
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg, "while generating recommendations"))

    return OnboardingSessionResponse(
        session_id=result["session_id"],
        current_phase=result["current_phase"],
        phase_progress=result.get("phase_progress", {}),
        message=result["message"],
        success=True,
        recommendations=result.get("recommendations"),
    )


@router.post("/{session_id}/recommendations/accept", response_model=OnboardingSessionResponse)
async def accept_recommendations(
    session_id: str,
    request: AcceptRecommendationsRequest,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Accept AI recommendations and proceed to deep research.

    Allows customization of recommended data sources before
    generating deep research reports.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()

    # First get current status
    status = service.get_session_status(session_id)
    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    # Then proceed to deep research
    result = await service.run_deep_research(session_id)

    return OnboardingSessionResponse(
        session_id=result["session_id"],
        current_phase=result["current_phase"],
        phase_progress=result.get("phase_progress", {}),
        message=result["message"],
        success=True,
        research_status=result.get("research_status"),
    )


@router.post("/{session_id}/research", response_model=OnboardingSessionResponse)
async def run_deep_research(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Run deep research agents to generate reports.

    Generates comprehensive research reports:
    - Competitive Landscape Report
    - State of the Art Report
    - Regulatory Precedents Report
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = await service.run_deep_research(session_id)

    if not result.get("success"):
        error_msg = result.get("error", "Deep research failed")
        if error_msg == "Session not found":
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg, "during deep research"))

    # Include any partial errors in the response
    errors = result.get("errors")
    message = result["message"]
    if errors:
        message = f"{message} Note: Some reports could not be generated."

    return OnboardingSessionResponse(
        session_id=result["session_id"],
        current_phase=result["current_phase"],
        phase_progress=result.get("phase_progress", {}),
        message=message,
        success=True,
        research_status=result.get("research_status"),
    )


@router.get("/{session_id}/reports")
async def get_reports(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Get generated research reports for a session.

    Returns download links for all completed reports.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "reports": status.get("research_reports", {}),
        "message": "Reports retrieved successfully",
    }


@router.post("/{session_id}/complete", response_model=OnboardingSessionResponse)
async def complete_onboarding(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Complete the onboarding and generate intelligence brief.

    Finalizes configuration and enables product access for all personas.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = await service.complete_onboarding(session_id)

    if not result.get("success"):
        error_msg = result.get("error", "Completion failed")
        if error_msg == "Session not found":
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg, "while completing configuration"))

    return OnboardingSessionResponse(
        session_id=result["session_id"],
        current_phase=result["current_phase"],
        phase_progress=result.get("phase_progress", {}),
        message=result["message"],
        success=True,
        intelligence_brief=result.get("intelligence_brief"),
        configuration_complete=result.get("configuration_complete"),
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """
    List all onboarding sessions.

    Returns summary of all active and completed sessions.
    """
    service = get_onboarding_service()
    sessions = service.list_sessions()

    return SessionListResponse(
        sessions=[SessionSummary(**s) for s in sessions],
        total=len(sessions),
    )


# Track cancelled sessions (in-memory for simplicity; production would use Redis/DB)
_cancelled_sessions: set = set()


@router.post("/{session_id}/cancel")
async def cancel_session(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Cancel an in-progress onboarding session.

    Marks the session as cancelled, which will:
    - Stop any running agents at next check point
    - Close any active SSE connections
    - Allow the session to be resumed later if needed
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    current_phase = status.get("current_phase", "")

    # Check if session can be cancelled
    if current_phase == "complete":
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a completed session"
        )

    # Mark session as cancelled
    _cancelled_sessions.add(session_id)

    logger.info(f"Session {session_id} cancelled by user {user_id}")

    return {
        "session_id": session_id,
        "status": "cancelled",
        "previous_phase": current_phase,
        "message": "Session cancelled. You can start a new session or resume this one later.",
    }


@router.post("/{session_id}/resume")
async def resume_session(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Resume a previously cancelled session.

    Removes the cancellation flag and allows the session to continue
    from where it left off.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove cancellation flag
    _cancelled_sessions.discard(session_id)

    current_phase = status.get("current_phase", "")

    logger.info(f"Session {session_id} resumed by user {user_id}")

    return {
        "session_id": session_id,
        "status": "resumed",
        "current_phase": current_phase,
        "phase_progress": status.get("phase_progress", {}),
        "message": f"Session resumed at phase: {current_phase}",
    }


def is_session_cancelled(session_id: str) -> bool:
    """Check if a session has been cancelled."""
    return session_id in _cancelled_sessions


# ==================== SSE Progress Streaming ====================

class ProgressEvent(BaseModel):
    """Progress event for SSE streaming."""
    event_type: str = Field(..., description="Event type: progress, agent_update, phase_change, complete, error, partial_failure")
    phase: str = Field(..., description="Current phase")
    overall_progress: int = Field(..., description="Overall progress 0-100")
    overall_status: Optional[str] = Field(default=None, description="Status: completed, partial, failed, timeout")
    agent_updates: Optional[Dict[str, Any]] = Field(default=None, description="Agent-specific progress")
    message: Optional[str] = Field(default=None, description="Status message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")
    errors: Optional[List[str]] = Field(default=None, description="List of errors if any")


async def generate_progress_events(session_id: str) -> AsyncGenerator[str, None]:
    """
    Generate SSE events for onboarding progress.

    Yields Server-Sent Events in the format:
    event: <event_type>
    data: <json_data>
    """
    service = get_onboarding_service()
    last_phase = None
    last_progress = -1

    try:
        while True:
            # Check for cancellation
            if is_session_cancelled(session_id):
                event = ProgressEvent(
                    event_type="cancelled",
                    phase=last_phase or "unknown",
                    overall_progress=last_progress if last_progress >= 0 else 0,
                    message="Session was cancelled by user",
                )
                yield f"event: cancelled\ndata: {event.model_dump_json()}\n\n"
                break

            # Get current session status
            status = service.get_session_status(session_id)

            if not status.get("success"):
                yield f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"
                break

            current_phase = status.get("current_phase", "unknown")
            phase_progress = status.get("phase_progress", {})

            # Calculate overall progress
            phases = ["context_capture", "discovery", "recommendations", "deep_research", "complete"]
            phase_weights = {"context_capture": 10, "discovery": 30, "recommendations": 20, "deep_research": 30, "complete": 10}

            overall_progress = 0
            for phase in phases:
                pp = phase_progress.get(phase, {})
                if pp.get("completed"):
                    overall_progress += phase_weights.get(phase, 0)
                elif phase == current_phase:
                    overall_progress += int(phase_weights.get(phase, 0) * pp.get("progress", 0) / 100)

            # Detect phase change
            if current_phase != last_phase:
                event = ProgressEvent(
                    event_type="phase_change",
                    phase=current_phase,
                    overall_progress=overall_progress,
                    message=f"Entered phase: {current_phase}",
                )
                yield f"event: phase_change\ndata: {event.model_dump_json()}\n\n"
                last_phase = current_phase

            # Send progress update if changed
            if overall_progress != last_progress:
                # Gather agent-specific updates based on phase
                agent_updates = {}
                errors = []
                overall_status = "completed"

                if current_phase == "discovery":
                    discovery = status.get("discovery_results", {})
                    agent_updates = {
                        "literature": discovery.get("literature_discovery", {}),
                        "registry": discovery.get("registry_discovery", {}),
                        "fda": discovery.get("fda_discovery", {}),
                        "competitive": discovery.get("competitive_discovery", {}),
                    }
                    # Check for errors in discovery results
                    for agent_name, agent_data in agent_updates.items():
                        if isinstance(agent_data, dict) and agent_data.get("error"):
                            errors.append(f"{agent_name}: {agent_data.get('error')}")
                        if isinstance(agent_data, dict) and agent_data.get("status") in ["failed", "timeout"]:
                            overall_status = "partial"

                elif current_phase in ["recommendations", "deep_research", "complete"]:
                    # Also send discovery results for phases after discovery
                    # so frontend can catch up if it connected late
                    discovery = status.get("discovery_results", {})
                    if discovery:
                        agent_updates = {
                            "literature": discovery.get("literature_discovery", {}),
                            "registry": discovery.get("registry_discovery", {}),
                            "fda": discovery.get("fda_discovery", {}),
                            "competitive": discovery.get("competitive_discovery", {}),
                        }
                    # For deep_research, also include research reports
                    if current_phase == "deep_research":
                        research = status.get("research_reports", {})
                        agent_updates["research"] = research
                        # Check for errors in research results
                        for report_name, report_data in research.items():
                            if isinstance(report_data, dict) and report_data.get("error"):
                                errors.append(f"{report_name}: {report_data.get('error')}")
                            if isinstance(report_data, dict) and report_data.get("status") in ["failed", "timeout"]:
                                overall_status = "partial"

                # Determine event type based on errors
                event_type = "progress"
                if errors:
                    event_type = "partial_failure"

                event = ProgressEvent(
                    event_type=event_type,
                    phase=current_phase,
                    overall_progress=overall_progress,
                    overall_status=overall_status if overall_status != "completed" else None,
                    agent_updates=agent_updates if agent_updates else None,
                    errors=errors if errors else None,
                )
                yield f"event: {event_type}\ndata: {event.model_dump_json()}\n\n"
                last_progress = overall_progress

            # Check for completion
            if current_phase == "complete" and phase_progress.get("complete", {}).get("completed"):
                event = ProgressEvent(
                    event_type="complete",
                    phase="complete",
                    overall_progress=100,
                    message="Configuration complete!",
                    data=status.get("intelligence_brief"),
                )
                yield f"event: complete\ndata: {event.model_dump_json()}\n\n"
                break

            # Wait before next poll
            await asyncio.sleep(1.0)

    except asyncio.CancelledError:
        logger.info(f"SSE connection cancelled for session {session_id}")
    except Exception as e:
        logger.error(f"Error in SSE stream for session {session_id}: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.get("/{session_id}/progress/stream")
async def stream_progress(session_id: str):
    """
    Stream real-time progress updates via Server-Sent Events.

    Connect to this endpoint to receive live progress updates during
    the onboarding process. Events include:
    - phase_change: When moving to a new phase
    - progress: Overall and agent-specific progress updates
    - complete: When onboarding is finished
    - error: If an error occurs
    """
    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    return StreamingResponse(
        generate_progress_events(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# Conversation History Models
class AddMessageRequest(BaseModel):
    """Request to add a message to conversation history."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class ConversationMessage(BaseModel):
    """A message in conversation history."""
    id: int = Field(..., description="Message ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")
    created_at: str = Field(..., description="Creation timestamp")


class ConversationHistoryResponse(BaseModel):
    """Response containing conversation history."""
    session_id: str = Field(..., description="Session identifier")
    messages: List[ConversationMessage] = Field(default_factory=list)
    total: int = Field(..., description="Total number of messages")


# Chat Request/Response Models
class ChatRequest(BaseModel):
    """Request to chat with the onboarding AI."""
    message: str = Field(..., description="The user's message")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context (phase, focus, etc.)")


class ChatResponse(BaseModel):
    """Response from the onboarding AI chat."""
    session_id: str = Field(..., description="Session identifier")
    response: str = Field(..., description="AI response message")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested actions the user can take")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    context_update: Optional[Dict[str, Any]] = Field(default=None, description="Updated context information")


class AddMessageResponse(BaseModel):
    """Response after adding a message."""
    session_id: str = Field(..., description="Session identifier")
    message_id: int = Field(..., description="ID of the added message")
    success: bool = Field(..., description="Operation success status")


# Conversation History Endpoints
@router.post("/{session_id}/messages", response_model=AddMessageResponse)
async def add_message(session_id: str, request: AddMessageRequest):
    """
    Add a message to the conversation history.

    Records user or assistant messages for the onboarding chat interface.
    """
    from app.services.database_service import get_database_service

    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    db = get_database_service()
    message_id = db.add_message(
        session_id=session_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )

    return AddMessageResponse(
        session_id=session_id,
        message_id=message_id,
        success=True,
    )


@router.get("/{session_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum messages to return")
):
    """
    Get conversation history for a session.

    Returns all messages in chronological order for the chat interface.
    """
    from app.services.database_service import get_database_service

    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    db = get_database_service()
    messages = db.get_conversation_history(session_id=session_id, limit=limit)

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[ConversationMessage(**m) for m in messages],
        total=len(messages),
    )


# ==================== Conversational Chat Endpoint ====================

@router.post("/{session_id}/chat", response_model=ChatResponse)
async def chat_with_ai(
    session_id: str,
    request: ChatRequest,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Send a message to the onboarding AI and receive a response.

    The steward can converse with the AI at any phase of the onboarding process:
    - Ask questions about the configuration process
    - Request clarification on recommendations
    - Provide feedback or additional context
    - Get guidance on next steps

    The AI response is contextually aware of the current phase and session state.
    """
    from app.services.database_service import get_database_service
    from app.agents.onboarding_agent import OnboardingAgent
    from app.agents.base_agent import AgentContext

    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    db = get_database_service()

    # Store user message in conversation history
    db.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        metadata={"phase": status.get("current_phase")},
    )

    # Get recent conversation history for context
    messages = db.get_conversation_history(session_id=session_id, limit=10)
    conversation_history = [
        {"role": m.get("role"), "content": m.get("content")}
        for m in messages
    ]

    # Build product info from session
    product_info = {
        "product_name": status.get("product_name", "Unknown Product"),
        "category": status.get("category", ""),
        "indication": status.get("indication", ""),
        "protocol_id": status.get("protocol_id", ""),
        "technologies": status.get("technologies", []),
    }

    # Get additional context from session state
    discovery_results = status.get("discovery_results", {})
    recommendations = status.get("recommendations", {})

    # Create agent context for chat
    agent_context = AgentContext(
        request_id=f"chat-{session_id}-{datetime.utcnow().isoformat()}",
        protocol_id=status.get("protocol_id", "H-34"),
        parameters={
            "action": "chat",
            "product_info": product_info,
            "current_phase": status.get("current_phase", "context_capture"),
            "session_context": request.context.get("session_context") if request.context else "",
            "conversation_history": conversation_history,
            "user_message": request.message,
            "discovery_results": discovery_results,
            "recommendations": recommendations,
        }
    )

    # Execute chat with OnboardingAgent
    agent = OnboardingAgent()
    try:
        result = await agent.execute(agent_context)

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=format_user_error(result.error or "Chat failed", "during conversation")
            )

        chat_data = result.data

        # Store AI response in conversation history
        ai_response = chat_data.get("response", "I'm here to help with your product configuration.")
        db.add_message(
            session_id=session_id,
            role="assistant",
            content=ai_response,
            metadata={
                "phase": status.get("current_phase"),
                "suggested_actions": chat_data.get("suggested_actions", []),
            },
        )

        return ChatResponse(
            session_id=session_id,
            response=ai_response,
            suggested_actions=chat_data.get("suggested_actions", []),
            follow_up_questions=chat_data.get("follow_up_questions", []),
            context_update=chat_data.get("context_update"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Chat error for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=format_user_error(str(e), "during conversation")
        )


# ==================== Interactive Approval Endpoints ====================

class UpdateApprovalRequest(BaseModel):
    """Request to update source approval status."""
    status: str = Field(..., description="Approval status: approved, rejected, or pending")
    reason: Optional[str] = Field(None, description="Required if rejecting - reason for rejection")
    settings: Optional[Dict[str, Any]] = Field(None, description="Optional custom settings for this source")


class UpdateApprovalResponse(BaseModel):
    """Response after updating approval status."""
    success: bool = Field(..., description="Operation success status")
    session_id: str = Field(..., description="Session identifier")
    source_type: str = Field(..., description="Type of source")
    source_id: str = Field(..., description="Source identifier")
    status: str = Field(..., description="New approval status")
    approval_summary: Dict[str, Any] = Field(..., description="Updated approval summary")


class SubmitFeedbackRequest(BaseModel):
    """Request to submit steward feedback."""
    feedback: str = Field(..., description="The feedback text")
    request_reanalysis: bool = Field(default=False, description="Whether to request AI re-analysis")


class SubmitFeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    success: bool = Field(..., description="Operation success status")
    session_id: str = Field(..., description="Session identifier")
    feedback_count: int = Field(..., description="Total number of feedback entries")
    message: str = Field(..., description="Status message")


class ApprovalAuditResponse(BaseModel):
    """Response containing approval audit trail."""
    success: bool = Field(..., description="Operation success status")
    session_id: str = Field(..., description="Session identifier")
    audit_entries: List[Dict[str, Any]] = Field(..., description="List of audit entries")
    total_entries: int = Field(..., description="Total number of audit entries")
    approval_summary: Dict[str, Any] = Field(..., description="Current approval summary")


class FinalizeApprovalsResponse(BaseModel):
    """Response after finalizing approvals."""
    success: bool = Field(..., description="Operation success status")
    session_id: str = Field(..., description="Session identifier")
    current_phase: str = Field(..., description="Current onboarding phase")
    approval_summary: Dict[str, Any] = Field(..., description="Final approval summary")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")


class ApprovalStatusResponse(BaseModel):
    """Response containing current approval status."""
    success: bool = Field(..., description="Operation success status")
    session_id: str = Field(..., description="Session identifier")
    source_approvals: Dict[str, Dict[str, Any]] = Field(..., description="All source approvals")
    approval_summary: Dict[str, Any] = Field(..., description="Approval summary")
    steward_feedback: List[str] = Field(default_factory=list, description="Steward feedback entries")


@router.patch("/{session_id}/recommendations/{source_type}/{source_id}")
async def update_source_approval(
    session_id: str,
    source_type: str,
    source_id: str,
    request: UpdateApprovalRequest,
    user_id: Optional[str] = Depends(get_current_user_id)
) -> UpdateApprovalResponse:
    """
    Update approval status for a specific data source.

    Allows the steward to approve, reject, or reset a source recommendation.
    Rejections require a reason to help improve future AI recommendations.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    # Validate status
    valid_statuses = ["pending", "approved", "rejected"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    service = get_onboarding_service()
    result = service.update_source_approval(
        session_id=session_id,
        source_type=source_type,
        source_id=source_id,
        status=request.status,
        reason=request.reason,
        user_id=user_id,
        settings=request.settings,
    )

    if not result.get("success"):
        error_msg = result.get("error", "Failed to update approval")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=400, detail=format_user_error(error_msg))

    # Convert ApprovalSummary to dict if needed
    approval_summary = result.get("approval_summary", {})
    if hasattr(approval_summary, "model_dump"):
        approval_summary = approval_summary.model_dump()

    return UpdateApprovalResponse(
        success=True,
        session_id=session_id,
        source_type=source_type,
        source_id=source_id,
        status=result.get("status", request.status),
        approval_summary=approval_summary,
    )


@router.post("/{session_id}/recommendations/feedback")
async def submit_feedback(
    session_id: str,
    request: SubmitFeedbackRequest,
    user_id: Optional[str] = Depends(get_current_user_id)
) -> SubmitFeedbackResponse:
    """
    Submit steward feedback for the recommendations.

    Feedback helps the AI understand steward preferences and can trigger
    re-analysis of recommendations if requested.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = service.submit_feedback(
        session_id=session_id,
        feedback=request.feedback,
        request_reanalysis=request.request_reanalysis,
        user_id=user_id,
    )

    if not result.get("success"):
        error_msg = result.get("error", "Failed to submit feedback")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg))

    return SubmitFeedbackResponse(
        success=True,
        session_id=session_id,
        feedback_count=result.get("feedback_count", 0),
        message=result.get("message", "Feedback submitted"),
    )


@router.get("/{session_id}/recommendations/audit")
async def get_approval_audit(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
) -> ApprovalAuditResponse:
    """
    Get the full audit trail for approval decisions.

    Returns a complete history of all approval actions, feedback submissions,
    and status changes for compliance and review purposes.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = service.get_approval_audit(session_id)

    if not result.get("success"):
        error_msg = result.get("error", "Failed to get audit trail")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg))

    # Convert ApprovalSummary to dict if needed
    approval_summary = result.get("approval_summary", {})
    if hasattr(approval_summary, "model_dump"):
        approval_summary = approval_summary.model_dump()

    return ApprovalAuditResponse(
        success=True,
        session_id=session_id,
        audit_entries=result.get("audit_entries", []),
        total_entries=result.get("total_entries", 0),
        approval_summary=approval_summary,
    )


@router.post("/{session_id}/recommendations/finalize")
async def finalize_approvals(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
) -> FinalizeApprovalsResponse:
    """
    Finalize all approvals and proceed to deep research.

    Confirms all approval decisions and transitions the session to the
    deep research phase. Only proceeds if minimum required sources are approved.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = service.finalize_approvals(
        session_id=session_id,
        user_id=user_id,
    )

    if not result.get("success"):
        error_msg = result.get("error", "Failed to finalize approvals")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        # Return error in response for minimum requirements not met
        approval_summary = result.get("approval_summary", {})
        return FinalizeApprovalsResponse(
            success=False,
            session_id=session_id,
            current_phase="recommendations",
            approval_summary=approval_summary,
            message=error_msg,
            error=error_msg,
        )

    # Convert ApprovalSummary to dict if needed
    approval_summary = result.get("approval_summary", {})
    if hasattr(approval_summary, "model_dump"):
        approval_summary = approval_summary.model_dump()

    return FinalizeApprovalsResponse(
        success=True,
        session_id=session_id,
        current_phase=result.get("current_phase", "deep_research"),
        approval_summary=approval_summary,
        message=result.get("message", "Approvals finalized"),
    )


@router.get("/{session_id}/recommendations/status")
async def get_approval_status(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
) -> ApprovalStatusResponse:
    """
    Get current approval status for all sources in a session.

    Returns the approval status for each recommended source along with
    the overall approval summary and any steward feedback.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = service.get_approval_status(session_id)

    if not result.get("success"):
        error_msg = result.get("error", "Failed to get approval status")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg))

    return ApprovalStatusResponse(
        success=True,
        session_id=session_id,
        source_approvals=result.get("source_approvals", {}),
        approval_summary=result.get("approval_summary", {}),
        steward_feedback=result.get("steward_feedback", []),
    )


@router.post("/{session_id}/recommendations/initialize")
async def initialize_approvals(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Initialize approval status for all recommendations.

    Called after recommendations are generated to set up the approval workflow.
    Sets all sources to pending status initially.
    """
    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    result = service.initialize_approvals_from_recommendations(session_id)

    if not result.get("success"):
        error_msg = result.get("error", "Failed to initialize approvals")
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=format_user_error(error_msg))
        raise HTTPException(status_code=500, detail=format_user_error(error_msg))

    return {
        "success": True,
        "session_id": session_id,
        "approval_summary": result.get("approval_summary", {}),
        "message": result.get("message", "Approvals initialized"),
    }


# ==================== Async Deep Research Endpoints ====================

class StartResearchRequest(BaseModel):
    """Request to start deep research (optional custom settings)."""
    custom_settings: Optional[Dict[str, Any]] = Field(default=None, description="Custom research settings")


class StartResearchResponse(BaseModel):
    """Response after initiating deep research."""
    job_id: str = Field(..., description="Background job identifier")
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")
    redirect_to: str = Field(..., description="URL to redirect user to")


class ResearchJobStatus(BaseModel):
    """Status of a research job stage."""
    name: str = Field(..., description="Stage name")
    status: str = Field(..., description="Stage status")
    progress: int = Field(..., description="Stage progress (0-100)")
    label: str = Field(..., description="Human-readable label")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class ResearchStatusResponse(BaseModel):
    """Response containing research job status."""
    success: bool = Field(..., description="Operation success status")
    job_id: str = Field(..., description="Job identifier")
    session_id: str = Field(..., description="Session identifier")
    product_id: str = Field(..., description="Product identifier")
    status: str = Field(..., description="Job status")
    progress: int = Field(..., description="Overall progress (0-100)")
    current_stage: Optional[str] = Field(None, description="Current stage name")
    current_stage_label: str = Field(default="", description="Current stage label")
    stages: List[ResearchJobStatus] = Field(default_factory=list, description="All stages with status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="Job creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")


@router.post("/{session_id}/research/start", response_model=StartResearchResponse)
async def start_deep_research_async(
    session_id: str,
    request: Optional[StartResearchRequest] = None,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Start deep research as a background job.

    This endpoint returns immediately after creating the job.
    The user should be redirected to the product landing page
    and can poll the /research/status endpoint for progress.

    The research pipeline runs in background:
    1. Data Ingestion - Process approved sources
    2. Competitive Analysis - Grounded web research
    3. State of the Art - Literature synthesis
    4. Regulatory Analysis - FDA pathway analysis
    5. Report Generation - Intelligence brief
    """
    from app.services.job_service import get_job_service

    # Verify session ownership
    await verify_session_access(session_id, user_id)

    service = get_onboarding_service()
    status = service.get_session_status(session_id)

    if not status.get("success"):
        raise HTTPException(status_code=404, detail="Session not found")

    # Get product_id (use protocol_id as product identifier)
    product_id = status.get("protocol_id", session_id)

    # Create background job
    job_service = get_job_service()
    job_id = await job_service.create_job(
        session_id=session_id,
        product_id=product_id,
    )

    logger.info(f"Started research job {job_id} for session {session_id}")

    return StartResearchResponse(
        job_id=job_id,
        session_id=session_id,
        status="pending",
        message="Deep research initiated. You will be notified when complete.",
        redirect_to=f"/product/{product_id}",
    )


@router.get("/{session_id}/research/status", response_model=ResearchStatusResponse)
async def get_research_status(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Get the status of the deep research job.

    Poll this endpoint to track research progress.
    Returns detailed stage-by-stage status.
    """
    from app.services.job_service import get_job_service

    # Verify session ownership
    await verify_session_access(session_id, user_id)

    job_service = get_job_service()
    job = job_service.get_job_by_session(session_id)

    if not job:
        # No job found - check if research already complete in session
        service = get_onboarding_service()
        status = service.get_session_status(session_id)

        if not status.get("success"):
            raise HTTPException(status_code=404, detail="Session not found")

        # If session is complete, return completion status
        if status.get("current_phase") == "complete":
            return ResearchStatusResponse(
                success=True,
                job_id="",
                session_id=session_id,
                product_id=status.get("protocol_id", session_id),
                status="complete",
                progress=100,
                current_stage=None,
                current_stage_label="Complete",
                stages=[],
                completed_at=status.get("completed_at"),
            )

        raise HTTPException(status_code=404, detail="No research job found for this session")

    # Convert stages to response model
    stages = [
        ResearchJobStatus(
            name=s.get("name", ""),
            status=s.get("status", "pending"),
            progress=s.get("progress", 0),
            label=s.get("label", s.get("name", "")),
            started_at=s.get("started_at"),
            completed_at=s.get("completed_at"),
            error=s.get("error"),
        )
        for s in job.get("stages", [])
    ]

    # Get current stage label
    current_stage_label = ""
    current_stage = job.get("current_stage")
    if current_stage:
        for stage in stages:
            if stage.name == current_stage:
                current_stage_label = stage.label
                break

    return ResearchStatusResponse(
        success=True,
        job_id=job.get("job_id", ""),
        session_id=job.get("session_id", session_id),
        product_id=job.get("product_id", ""),
        status=job.get("status", "unknown"),
        progress=job.get("progress", 0),
        current_stage=current_stage,
        current_stage_label=current_stage_label,
        stages=stages,
        error_message=job.get("error_message"),
        created_at=job.get("created_at"),
        updated_at=job.get("updated_at"),
        completed_at=job.get("completed_at"),
    )


@router.post("/{session_id}/research/cancel")
async def cancel_research(
    session_id: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Cancel an in-progress research job.

    Stops the background job if still running.
    """
    from app.services.job_service import get_job_service

    # Verify session ownership
    await verify_session_access(session_id, user_id)

    job_service = get_job_service()
    job = job_service.get_job_by_session(session_id)

    if not job:
        raise HTTPException(status_code=404, detail="No research job found for this session")

    job_id = job.get("job_id")
    success = await job_service.cancel_job(job_id)

    return {
        "success": success,
        "job_id": job_id,
        "session_id": session_id,
        "message": "Research job cancelled" if success else "Failed to cancel job",
    }


# ==================== Folder Analysis Endpoint ====================

class FolderAnalysisRequest(BaseModel):
    """Request to analyze a local folder for data sources."""
    folder_path: str = Field(..., description="Path to the folder containing study data")


class StudyDataAnalysis(BaseModel):
    """Analysis results for study data files (Excel/CSV)."""
    fileName: str = Field(..., description="File name")
    rows: int = Field(..., description="Number of rows")
    columns: int = Field(..., description="Number of columns")
    columnNames: List[str] = Field(default_factory=list, description="Column names")
    dataTypes: Dict[str, str] = Field(default_factory=dict, description="Column data types")
    sampleValues: Dict[str, List[str]] = Field(default_factory=dict, description="Sample values per column")
    dateRange: Optional[Dict[str, str]] = Field(None, description="Date range if applicable")
    keyInsights: Optional[List[str]] = Field(None, description="Key insights from the data")


class ProtocolAnalysis(BaseModel):
    """Analysis results for protocol document."""
    fileName: str = Field(..., description="File name")
    pages: int = Field(..., description="Number of pages")
    studyTitle: str = Field(default="", description="Study title")
    indication: str = Field(default="", description="Indication")
    studyPhase: str = Field(default="", description="Study phase")
    primaryEndpoints: List[str] = Field(default_factory=list, description="Primary endpoints")
    secondaryEndpoints: List[str] = Field(default_factory=list, description="Secondary endpoints")
    populationSize: str = Field(default="", description="Population size")
    followUpDuration: str = Field(default="", description="Follow-up duration")
    inclusionCriteriaSummary: Optional[str] = Field(None, description="Inclusion criteria summary")
    extractedSections: Optional[List[str]] = Field(None, description="Extracted sections")


class LiteratureAnalysis(BaseModel):
    """Analysis results for literature PDFs."""
    fileName: str = Field(..., description="File name")
    title: str = Field(default="", description="Paper title")
    authors: str = Field(default="", description="Authors")
    journal: str = Field(default="", description="Journal name")
    year: int = Field(default=0, description="Publication year")
    pages: int = Field(..., description="Number of pages")
    relevanceScore: float = Field(default=0.0, description="Relevance score")
    keyFindings: List[str] = Field(default_factory=list, description="Key findings")
    studyType: Optional[str] = Field(None, description="Study type")
    sampleSize: Optional[str] = Field(None, description="Sample size")


class ExtractedJsonAnalysis(BaseModel):
    """Analysis results for extracted JSON files."""
    fileName: str = Field(..., description="File name")
    schemaType: str = Field(default="", description="Schema type")
    recordCount: int = Field(default=0, description="Number of records")
    keyFields: List[str] = Field(default_factory=list, description="Key fields")
    dataPreview: Dict[str, Any] = Field(default_factory=dict, description="Data preview")
    lastUpdated: Optional[str] = Field(None, description="Last updated timestamp")


class FolderContentsResponse(BaseModel):
    """Response containing folder analysis results."""
    path: str = Field(..., description="Folder path")
    validated: bool = Field(..., description="Whether the folder was successfully validated")
    studyData: Dict[str, Any] = Field(default_factory=dict, description="Study data files")
    protocol: Dict[str, Any] = Field(default_factory=dict, description="Protocol document")
    literature: Dict[str, Any] = Field(default_factory=dict, description="Literature files")
    extractedJson: Dict[str, Any] = Field(default_factory=dict, description="Extracted JSON files")


@router.post("/analyze-folder", response_model=FolderContentsResponse)
async def analyze_folder(request: FolderAnalysisRequest):
    """
    Analyze a local folder for study data sources.

    Scans the folder and returns detailed analysis of:
    - Study data files (Excel, CSV)
    - Protocol documents (PDF)
    - Literature PDFs
    - Extracted JSON files
    """
    import os
    import json as json_module
    from pathlib import Path as PathLib
    import pandas as pd

    folder_path = request.folder_path

    # Resolve relative paths from project root
    if folder_path.startswith("./") or folder_path.startswith("../") or not folder_path.startswith("/"):
        # Get the project root (parent of app directory)
        project_root = PathLib(__file__).parent.parent.parent.parent
        path = (project_root / folder_path).resolve()
    else:
        path = PathLib(folder_path)

    # Validate folder exists
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path} (resolved to {path})")

    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")

    # Initialize result structure
    result = {
        "path": folder_path,
        "validated": True,
        "studyData": {"count": 0, "files": [], "analysis": []},
        "protocol": {"found": False, "file": None, "analysis": None},
        "literature": {"count": 0, "files": [], "analysis": []},
        "extractedJson": {"count": 0, "files": [], "analysis": []},
    }

    try:
        # Scan for all files in the folder (including subdirectories)
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue

            file_name = file_path.name
            file_ext = file_path.suffix.lower()
            relative_path = str(file_path.relative_to(path))

            # Study Data Files (Excel, CSV)
            if file_ext in [".xlsx", ".xls", ".csv"]:
                try:
                    analysis = await _analyze_study_data_file(str(file_path), file_name)
                    result["studyData"]["files"].append(file_name)
                    result["studyData"]["analysis"].append(analysis)
                    result["studyData"]["count"] += 1
                except Exception as e:
                    logger.warning(f"Could not analyze study data file {file_name}: {e}")
                    result["studyData"]["files"].append(file_name)
                    result["studyData"]["count"] += 1

            # Protocol Documents (PDF with 'protocol' in name or in protocol subfolder)
            elif file_ext == ".pdf":
                is_protocol = (
                    "protocol" in file_name.lower() or
                    "protocol" in relative_path.lower()
                )
                is_literature = (
                    "literature" in relative_path.lower() or
                    "publication" in relative_path.lower() or
                    "papers" in relative_path.lower()
                )

                if is_protocol and not result["protocol"]["found"]:
                    try:
                        analysis = await _analyze_protocol_file(str(file_path), file_name)
                        result["protocol"]["found"] = True
                        result["protocol"]["file"] = file_name
                        result["protocol"]["analysis"] = analysis
                    except Exception as e:
                        logger.warning(f"Could not analyze protocol {file_name}: {e}")
                        result["protocol"]["found"] = True
                        result["protocol"]["file"] = file_name
                elif is_literature or not is_protocol:
                    try:
                        analysis = await _analyze_literature_file(str(file_path), file_name)
                        result["literature"]["files"].append(file_name)
                        result["literature"]["analysis"].append(analysis)
                        result["literature"]["count"] += 1
                    except Exception as e:
                        logger.warning(f"Could not analyze literature {file_name}: {e}")
                        result["literature"]["files"].append(file_name)
                        result["literature"]["count"] += 1

            # Extracted JSON Files
            elif file_ext == ".json":
                try:
                    analysis = await _analyze_json_file(str(file_path), file_name)
                    result["extractedJson"]["files"].append(file_name)
                    result["extractedJson"]["analysis"].append(analysis)
                    result["extractedJson"]["count"] += 1
                except Exception as e:
                    logger.warning(f"Could not analyze JSON file {file_name}: {e}")
                    result["extractedJson"]["files"].append(file_name)
                    result["extractedJson"]["count"] += 1

        return FolderContentsResponse(**result)

    except Exception as e:
        logger.error(f"Error analyzing folder {folder_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing folder: {str(e)}")


async def _analyze_study_data_file(file_path: str, file_name: str) -> Dict[str, Any]:
    """Analyze Excel/CSV file and return metadata."""
    import pandas as pd

    file_ext = file_name.lower().split(".")[-1]

    try:
        if file_ext == "csv":
            df = pd.read_csv(file_path, nrows=1000)  # Read first 1000 rows for analysis
        else:
            df = pd.read_excel(file_path, nrows=1000)  # Read first 1000 rows

        # Get full row count
        if file_ext == "csv":
            with open(file_path, "r") as f:
                total_rows = sum(1 for _ in f) - 1  # Subtract header
        else:
            full_df = pd.read_excel(file_path)
            total_rows = len(full_df)

        # Get column data types
        data_types = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if "int" in dtype:
                data_types[col] = "integer"
            elif "float" in dtype:
                data_types[col] = "decimal"
            elif "datetime" in dtype:
                data_types[col] = "date"
            elif "bool" in dtype:
                data_types[col] = "boolean"
            else:
                data_types[col] = "text"

        # Get sample values (first 3 non-null values per column)
        sample_values = {}
        for col in df.columns[:20]:  # Limit to first 20 columns
            non_null = df[col].dropna().head(3)
            sample_values[col] = [str(v)[:50] for v in non_null.tolist()]

        # Try to find date range if there's a date column
        date_range = None
        date_cols = [c for c in df.columns if any(d in c.lower() for d in ["date", "time", "created", "updated"])]
        if date_cols:
            try:
                date_col = date_cols[0]
                dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
                if len(dates) > 0:
                    date_range = {
                        "start": dates.min().strftime("%Y-%m-%d"),
                        "end": dates.max().strftime("%Y-%m-%d"),
                    }
            except Exception:
                pass

        # Generate key insights
        key_insights = []
        key_insights.append(f"Contains {total_rows} patient records across {len(df.columns)} variables")

        # Check for specific column patterns
        col_lower = [c.lower() for c in df.columns]
        if any("adverse" in c or "ae" in c for c in col_lower):
            key_insights.append("Contains adverse event data")
        if any("revision" in c for c in col_lower):
            key_insights.append("Contains revision surgery data")
        if any("outcome" in c or "endpoint" in c for c in col_lower):
            key_insights.append("Contains clinical outcome measures")
        if any("demog" in c or "age" in c or "gender" in c or "sex" in c for c in col_lower):
            key_insights.append("Contains demographic information")

        return {
            "fileName": file_name,
            "rows": total_rows,
            "columns": len(df.columns),
            "columnNames": df.columns.tolist()[:30],  # Limit to first 30
            "dataTypes": data_types,
            "sampleValues": sample_values,
            "dateRange": date_range,
            "keyInsights": key_insights,
        }

    except Exception as e:
        logger.error(f"Error analyzing {file_name}: {e}")
        return {
            "fileName": file_name,
            "rows": 0,
            "columns": 0,
            "columnNames": [],
            "dataTypes": {},
            "sampleValues": {},
            "dateRange": None,
            "keyInsights": [f"Error reading file: {str(e)}"],
        }


async def _analyze_protocol_file(file_path: str, file_name: str) -> Dict[str, Any]:
    """Analyze protocol PDF and extract metadata."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        num_pages = len(doc)

        # Extract text from first few pages for analysis
        text = ""
        for i, page in enumerate(doc):
            if i >= 10:  # Only analyze first 10 pages
                break
            text += page.get_text()

        doc.close()

        # Try to extract protocol metadata from text
        study_title = ""
        indication = ""
        study_phase = ""
        primary_endpoints = []
        secondary_endpoints = []
        population_size = ""
        follow_up_duration = ""
        extracted_sections = []

        # Extract title (usually in first 500 chars)
        first_part = text[:2000]
        lines = first_part.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 20 and len(line) < 200:
                if not study_title:
                    study_title = line
                    break

        # Extract sections found
        section_keywords = [
            "synopsis", "introduction", "objectives", "endpoints",
            "study design", "population", "methods", "statistical",
            "adverse events", "safety", "efficacy", "inclusion", "exclusion"
        ]
        text_lower = text.lower()
        for keyword in section_keywords:
            if keyword in text_lower:
                extracted_sections.append(keyword.title())

        # Try to extract phase
        phase_patterns = ["phase iv", "phase 4", "phase iii", "phase 3", "phase ii", "phase 2", "phase i", "phase 1", "post-market"]
        for pattern in phase_patterns:
            if pattern in text_lower:
                study_phase = pattern.replace("phase", "Phase").strip().title()
                break

        return {
            "fileName": file_name,
            "pages": num_pages,
            "studyTitle": study_title[:200] if study_title else "Protocol Document",
            "indication": indication,
            "studyPhase": study_phase,
            "primaryEndpoints": primary_endpoints,
            "secondaryEndpoints": secondary_endpoints,
            "populationSize": population_size,
            "followUpDuration": follow_up_duration,
            "inclusionCriteriaSummary": None,
            "extractedSections": extracted_sections[:10],
        }

    except ImportError:
        logger.warning("PyMuPDF not available for protocol analysis")
        return {
            "fileName": file_name,
            "pages": 0,
            "studyTitle": "Protocol Document",
            "indication": "",
            "studyPhase": "",
            "primaryEndpoints": [],
            "secondaryEndpoints": [],
            "populationSize": "",
            "followUpDuration": "",
            "inclusionCriteriaSummary": None,
            "extractedSections": [],
        }
    except Exception as e:
        logger.error(f"Error analyzing protocol {file_name}: {e}")
        return {
            "fileName": file_name,
            "pages": 0,
            "studyTitle": "Protocol Document",
            "indication": "",
            "studyPhase": "",
            "primaryEndpoints": [],
            "secondaryEndpoints": [],
            "populationSize": "",
            "followUpDuration": "",
            "inclusionCriteriaSummary": None,
            "extractedSections": [],
        }


async def _analyze_literature_file(file_path: str, file_name: str) -> Dict[str, Any]:
    """Analyze literature PDF and extract metadata."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        num_pages = len(doc)

        # Extract text from first page for metadata
        first_page_text = doc[0].get_text() if num_pages > 0 else ""
        doc.close()

        # Try to extract metadata
        title = ""
        authors = ""
        journal = ""
        year = 0

        lines = first_page_text.split("\n")
        for i, line in enumerate(lines[:15]):
            line = line.strip()
            if len(line) > 30 and len(line) < 300 and not title:
                title = line
            elif not authors and ("," in line or "and" in line.lower()) and len(line) < 200:
                if any(c.isupper() for c in line[:10]):
                    authors = line[:100]

        # Try to extract year
        import re
        year_match = re.search(r"(19|20)\d{2}", first_page_text[:1000])
        if year_match:
            year = int(year_match.group())

        return {
            "fileName": file_name,
            "title": title[:200] if title else file_name.replace(".pdf", ""),
            "authors": authors[:100] if authors else "",
            "journal": journal,
            "year": year,
            "pages": num_pages,
            "relevanceScore": 0.8,  # Default relevance
            "keyFindings": [],
            "studyType": None,
            "sampleSize": None,
        }

    except ImportError:
        return {
            "fileName": file_name,
            "title": file_name.replace(".pdf", ""),
            "authors": "",
            "journal": "",
            "year": 0,
            "pages": 0,
            "relevanceScore": 0.5,
            "keyFindings": [],
            "studyType": None,
            "sampleSize": None,
        }
    except Exception as e:
        logger.error(f"Error analyzing literature {file_name}: {e}")
        return {
            "fileName": file_name,
            "title": file_name.replace(".pdf", ""),
            "authors": "",
            "journal": "",
            "year": 0,
            "pages": 0,
            "relevanceScore": 0.5,
            "keyFindings": [],
            "studyType": None,
            "sampleSize": None,
        }


async def _analyze_json_file(file_path: str, file_name: str) -> Dict[str, Any]:
    """Analyze JSON file and extract metadata."""
    import json as json_module
    import os

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json_module.load(f)

        # Determine schema type and record count
        schema_type = "unknown"
        record_count = 0
        key_fields = []
        data_preview = {}

        if isinstance(data, list):
            record_count = len(data)
            if len(data) > 0 and isinstance(data[0], dict):
                key_fields = list(data[0].keys())[:10]
                data_preview = data[0]
                # Try to determine schema type from keys
                keys_lower = [k.lower() for k in key_fields]
                if "adverse_event" in keys_lower or "ae_" in str(keys_lower):
                    schema_type = "adverse_events"
                elif "endpoint" in keys_lower:
                    schema_type = "endpoints"
                elif "patient" in keys_lower or "subject" in keys_lower:
                    schema_type = "patient_data"
                elif "protocol" in keys_lower:
                    schema_type = "protocol_extract"
                else:
                    schema_type = "extracted_data"
        elif isinstance(data, dict):
            record_count = 1
            key_fields = list(data.keys())[:10]
            data_preview = {k: data[k] for k in key_fields[:5] if k in data}
            schema_type = "configuration" if "config" in file_name.lower() else "structured_data"

        # Get last modified time
        last_updated = None
        try:
            mtime = os.path.getmtime(file_path)
            from datetime import datetime
            last_updated = datetime.fromtimestamp(mtime).isoformat()
        except Exception:
            pass

        return {
            "fileName": file_name,
            "schemaType": schema_type,
            "recordCount": record_count,
            "keyFields": key_fields,
            "dataPreview": data_preview,
            "lastUpdated": last_updated,
        }

    except Exception as e:
        logger.error(f"Error analyzing JSON {file_name}: {e}")
        return {
            "fileName": file_name,
            "schemaType": "unknown",
            "recordCount": 0,
            "keyFields": [],
            "dataPreview": {},
            "lastUpdated": None,
        }


# ==================== ClinicalTrials.gov Search ====================

class CTSearchRequest(BaseModel):
    """Request model for ClinicalTrials.gov search."""
    sponsor: Optional[str] = Field(None, description="Sponsor/organization name for own trials")
    condition: Optional[str] = Field(None, description="Medical condition")
    intervention: Optional[str] = Field(None, description="Intervention/device type")
    phases: Optional[List[str]] = Field(default_factory=list, description="Study phases to filter")
    statuses: Optional[List[str]] = Field(default_factory=list, description="Study statuses to filter")
    competitor_sponsors: Optional[List[str]] = Field(default_factory=list, description="Competitor sponsor names")
    search_type: str = Field("own", description="Search type: 'own' or 'competitor'")


class CTSearchResponse(BaseModel):
    """Response model for ClinicalTrials.gov search."""
    count: int
    trials: List[Dict[str, Any]]


@router.post("/search-clinical-trials", response_model=CTSearchResponse)
async def search_clinical_trials(request: CTSearchRequest):
    """
    Search ClinicalTrials.gov for trials.

    Supports two search types:
    - 'own': Search for own organization's trials
    - 'competitor': Search for competitor trials
    """
    from app.services.clinical_trials_service import ClinicalTrialsService

    ct_service = ClinicalTrialsService()

    try:
        if request.search_type == "own":
            # Search for own trials by sponsor
            result = await ct_service.search_by_title(
                title_keywords=request.intervention or "",
                condition=request.condition,
                intervention=request.intervention,
                phases=request.phases if request.phases else None,
                max_results=50,
            )

            # Filter by sponsor if provided
            trials = result.get("studies", [])
            if request.sponsor:
                sponsor_lower = request.sponsor.lower()
                trials = [
                    t for t in trials
                    if sponsor_lower in (t.get("sponsor", "") or "").lower()
                    or sponsor_lower in (t.get("lead_sponsor", "") or "").lower()
                ]

            return {
                "count": len(trials),
                "trials": [
                    {
                        "nctId": t.get("nct_id", ""),
                        "title": t.get("title", ""),
                        "phase": t.get("phase", "N/A"),
                        "status": t.get("status", "Unknown"),
                        "sponsor": t.get("lead_sponsor", t.get("sponsor", "")),
                        "startDate": t.get("start_date"),
                        "completionDate": t.get("completion_date"),
                        "enrollment": t.get("enrollment"),
                    }
                    for t in trials[:50]
                ]
            }
        else:
            # Search for competitor trials
            result = await ct_service.search_competitor_trials(
                condition=request.condition or "",
                intervention_type=request.intervention or "",
                sponsor_exclude=request.sponsor,  # Exclude own company
                phases=request.phases if request.phases else None,
                max_results=50,
            )

            trials = result.get("studies", [])

            # Filter to only include specified competitors if provided
            if request.competitor_sponsors:
                competitors_lower = [s.lower() for s in request.competitor_sponsors]
                trials = [
                    t for t in trials
                    if any(
                        comp in (t.get("lead_sponsor", "") or "").lower()
                        for comp in competitors_lower
                    )
                ]

            return {
                "count": len(trials),
                "trials": [
                    {
                        "nctId": t.get("nct_id", ""),
                        "title": t.get("title", ""),
                        "sponsor": t.get("lead_sponsor", t.get("sponsor", "")),
                        "phase": t.get("phase", "N/A"),
                        "status": t.get("status", "Unknown"),
                        "startDate": t.get("start_date"),
                        "enrollment": t.get("enrollment"),
                    }
                    for t in trials[:50]
                ]
            }

    except Exception as e:
        logger.error(f"ClinicalTrials.gov search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ==================== FDA 510(k) Search ====================

class FDASearchRequest(BaseModel):
    """Request model for FDA 510(k) search."""
    applicant: Optional[str] = Field(None, description="Applicant/manufacturer name for own submissions")
    product_codes: Optional[List[str]] = Field(default_factory=list, description="FDA product codes")
    competitor_applicants: Optional[List[str]] = Field(default_factory=list, description="Competitor applicant names")
    date_start: Optional[str] = Field(None, description="Start date (YYYYMMDD)")
    date_end: Optional[str] = Field(None, description="End date (YYYYMMDD)")
    search_type: str = Field("own", description="Search type: 'own' or 'competitor'")


class FDASearchResponse(BaseModel):
    """Response model for FDA 510(k) search."""
    count: int
    submissions: List[Dict[str, Any]]


@router.post("/search-fda-submissions", response_model=FDASearchResponse)
async def search_fda_submissions(request: FDASearchRequest):
    """
    Search FDA 510(k) database for clearances.

    Supports two search types:
    - 'own': Search for own organization's submissions
    - 'competitor': Search for competitor submissions
    """
    from app.services.fda_service import FDAService

    fda_service = FDAService()

    # Build date range
    date_range = None
    if request.date_start or request.date_end:
        date_range = {
            "start": request.date_start or "20100101",
            "end": request.date_end or datetime.now().strftime("%Y%m%d"),
        }

    try:
        if request.search_type == "own":
            # Search for own submissions by applicant
            if not request.applicant:
                raise HTTPException(status_code=400, detail="Applicant name required for own submissions search")

            result = await fda_service.search_510k_by_applicant(
                applicant_name=request.applicant,
                product_codes=request.product_codes if request.product_codes else None,
                date_range=date_range,
                limit=100,
            )

            clearances = result.get("clearances", [])

            return {
                "count": len(clearances),
                "submissions": [
                    {
                        "kNumber": c.get("k_number", ""),
                        "deviceName": c.get("device_name", ""),
                        "applicant": c.get("applicant", request.applicant),
                        "decisionDate": c.get("decision_date", ""),
                        "productCode": c.get("product_code", ""),
                        "clearanceType": c.get("clearance_type", ""),
                        "reviewAdviseComm": c.get("review_advisory_committee", ""),
                    }
                    for c in clearances[:100]
                ]
            }
        else:
            # Search for competitor submissions
            if not request.product_codes:
                raise HTTPException(status_code=400, detail="Product codes required for competitor search")

            result = await fda_service.search_competitor_clearances(
                product_codes=request.product_codes,
                exclude_applicants=[request.applicant] if request.applicant else None,
                date_range=date_range,
                limit=100,
            )

            clearances = result.get("clearances", [])

            # Filter to only include specified competitors if provided
            if request.competitor_applicants:
                competitors_lower = [a.lower() for a in request.competitor_applicants]
                clearances = [
                    c for c in clearances
                    if any(
                        comp in (c.get("applicant", "") or "").lower()
                        for comp in competitors_lower
                    )
                ]

            return {
                "count": len(clearances),
                "submissions": [
                    {
                        "kNumber": c.get("k_number", ""),
                        "deviceName": c.get("device_name", ""),
                        "applicant": c.get("applicant", ""),
                        "decisionDate": c.get("decision_date", ""),
                        "productCode": c.get("product_code", ""),
                        "clearanceType": c.get("clearance_type", ""),
                    }
                    for c in clearances[:100]
                ]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FDA search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
