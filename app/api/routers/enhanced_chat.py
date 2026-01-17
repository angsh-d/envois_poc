"""
Enhanced Chat API endpoints with advanced agentic capabilities.

Provides:
- Multi-turn conversation with memory
- Chain-of-thought reasoning
- Proactive safety alerts
- Intelligent follow-up suggestions
- Statistical correlation analysis
- Autonomous investigation
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.conversation_service import (
    get_conversation_service, ConversationRole, MessageType
)
from app.services.safety_alert_service import (
    get_safety_alert_service, AlertSeverity, AlertCategory
)
from app.services.followup_suggestion_service import (
    get_followup_service, SuggestionCategory
)
from app.services.statistical_analysis_service import (
    get_statistical_service, CorrelationType, HypothesisType
)
from app.services.llm_service import get_llm_service
from app.services.prompt_service import get_prompt_service
from app.agents.reasoning_agent import get_reasoning_agent
from app.agents.base_agent import AgentContext

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enhanced-chat", tags=["enhanced-chat"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ConversationMessage(BaseModel):
    """Message in conversation history."""
    role: str
    content: str
    timestamp: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None


class EnhancedChatRequest(BaseModel):
    """Request for enhanced chat endpoint."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    study_id: str = Field(default="H-34", description="Study identifier")
    context: str = Field(default="dashboard", description="Current page context")
    enable_reasoning: bool = Field(default=False, description="Enable chain-of-thought reasoning")
    enable_investigation: bool = Field(default=False, description="Enable autonomous investigation")


class EnhancedChatResponse(BaseModel):
    """Response from enhanced chat endpoint."""
    response: str
    session_id: str
    sources: List[Dict[str, Any]]
    reasoning_trace: Optional[List[Dict[str, Any]]] = None
    follow_up_suggestions: List[str]
    safety_alerts: Optional[List[Dict[str, Any]]] = None
    confidence: float
    display_preference: str = "narrative"


class SafetyAlertResponse(BaseModel):
    """Response with safety alerts."""
    total_active: int
    critical_count: int
    warning_count: int
    alerts: List[Dict[str, Any]]
    proactive_insights: List[str]


class CorrelationRequest(BaseModel):
    """Request for correlation analysis."""
    variable_1_name: str
    variable_1_values: List[float]
    variable_2_name: str
    variable_2_values: List[float]
    correlation_type: str = "pearson"


class CorrelationResponse(BaseModel):
    """Response from correlation analysis."""
    variable_1: str
    variable_2: str
    correlation_type: str
    coefficient: float
    p_value: float
    sample_size: int
    significance: str
    interpretation: str
    confidence_interval: Optional[List[float]] = None


class InvestigationRequest(BaseModel):
    """Request for autonomous investigation."""
    question: str = Field(..., description="Question to investigate")
    study_id: str = Field(default="H-34", description="Study identifier")
    max_depth: int = Field(default=5, description="Maximum investigation depth")


class InvestigationResponse(BaseModel):
    """Response from autonomous investigation."""
    question: str
    summary: str
    hypotheses: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    reasoning_trace: List[Dict[str, Any]]
    confidence: float


class ProactiveSuggestionsResponse(BaseModel):
    """Response with proactive suggestions."""
    page_context: str
    suggestions: List[str]
    safety_insights: List[str]
    trending_topics: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("", response_model=EnhancedChatResponse)
async def enhanced_chat(request: EnhancedChatRequest):
    """
    Enhanced chat endpoint with conversation memory and advanced reasoning.

    Features:
    - Persistent conversation sessions
    - Context-aware responses
    - Chain-of-thought reasoning (optional)
    - Autonomous investigation (optional)
    - Proactive safety alerts
    """
    try:
        conv_service = get_conversation_service()
        followup_service = get_followup_service()
        alert_service = get_safety_alert_service()
        llm = get_llm_service()
        prompt_service = get_prompt_service()

        # Get or create conversation session
        session_id, conversation = await conv_service.get_or_create_session(
            session_id=request.session_id,
            study_id=request.study_id,
            page_context=request.context,
        )

        # Add user message to conversation
        await conv_service.add_user_message(
            session_id=session_id,
            content=request.message,
            metadata={"context": request.context},
        )

        # Build context window from conversation history
        context_window = conv_service.get_context_window(session_id)

        # Get conversation context for enhanced understanding
        conv_context = await conv_service.get_conversation_context(session_id)

        sources = []
        reasoning_trace = None
        confidence = 0.7

        # Option 1: Autonomous investigation mode
        if request.enable_investigation:
            reasoning_agent = get_reasoning_agent()
            agent_context = AgentContext(
                request_id=str(uuid.uuid4())[:8],
                protocol_id=request.study_id,
                parameters={
                    "question": request.message,
                    "conversation_context": conv_context.to_dict() if conv_context else {},
                }
            )
            result = await reasoning_agent.run(agent_context)

            if result.success:
                response_text = result.data.get("synthesis", {}).get("summary", result.narrative or "")
                reasoning_trace = result.data.get("reasoning_trace", [])
                confidence = result.confidence
                sources = [s.to_dict() for s in result.sources]
            else:
                response_text = f"Investigation could not be completed: {result.error}"

        # Option 2: Chain-of-thought reasoning mode
        elif request.enable_reasoning:
            # Load chain-of-thought prompt
            cot_prompt = prompt_service.load(
                "chain_of_thought_reasoning",
                parameters={
                    "question": request.message,
                    "page_context": request.context,
                    "conversation_history": context_window,
                    "extracted_context": str(conv_context.to_dict() if conv_context else {}),
                    "study_data_summary": "DELTA Revision Cup Study (Protocol H-34, n=37 patients)",
                    "registry_summary": "5 international registries (AOANJRR, NJR, SHAR, AJRR, CJRR)",
                    "literature_summary": "Peer-reviewed publications and meta-analyses",
                    "n_patients": "37",
                },
                strict=False,
            )

            cot_response = await llm.generate_json(
                prompt=cot_prompt,
                model="gemini-3-pro-preview",
                temperature=0.2,
                max_tokens=4096,
            )

            response_text = cot_response.get("answer", {}).get("summary", "")
            reasoning_trace = cot_response.get("reasoning_steps", [])
            confidence = 0.8 if cot_response.get("answer", {}).get("confidence") == "high" else 0.6
            sources = [{"type": "reasoning", "reference": "Chain-of-thought analysis"}]

        # Option 3: Standard enhanced response
        else:
            # Build prompt with conversation context
            prompt = f"""You are a Clinical Intelligence Analyst for the DELTA Revision Cup Study (Protocol H-34).

Conversation Context:
{context_window}

User Question: {request.message}

Page Context: {request.context}

Provide a helpful, accurate response based on available data.
Include specific citations where applicable.
Be concise but thorough.
"""
            response_text = await llm.generate(
                prompt=prompt,
                model="gemini-3-pro-preview",
                temperature=0.3,
                max_tokens=2048,
            )
            sources = [{"type": "study_data", "reference": "H-34 Study Data"}]

        # Add assistant response to conversation
        await conv_service.add_assistant_message(
            session_id=session_id,
            content=response_text,
            sources=sources,
            metadata={"reasoning_enabled": request.enable_reasoning},
        )

        # Generate follow-up suggestions (with null safety)
        mentioned_metrics = conv_context.mentioned_metrics if conv_context and hasattr(conv_context, 'mentioned_metrics') else []
        followups = followup_service.generate_suggestions(
            topic=request.context,
            mentioned_metrics=mentioned_metrics,
            exclude_asked=[request.message],
            max_suggestions=4,
        )
        followup_questions = [s.question for s in followups]

        # Check for safety alerts (async, don't block response)
        safety_alerts = None
        try:
            alert_summary = await alert_service.get_alert_summary()
            if alert_summary["total_active"] > 0:
                safety_alerts = alert_summary["top_alerts"]
        except Exception as e:
            logger.warning(f"Failed to get safety alerts: {e}")

        return EnhancedChatResponse(
            response=response_text,
            session_id=session_id,
            sources=sources,
            reasoning_trace=reasoning_trace,
            follow_up_suggestions=followup_questions,
            safety_alerts=safety_alerts,
            confidence=confidence,
            display_preference="narrative",
        )

    except Exception as e:
        logger.error(f"Enhanced chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-alerts", response_model=SafetyAlertResponse)
async def get_safety_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
):
    """
    Get current safety alerts.

    Provides proactive safety intelligence without requiring explicit queries.
    """
    try:
        alert_service = get_safety_alert_service()

        # Filter by severity if specified
        severity_filter = None
        if severity:
            severity_filter = AlertSeverity(severity)

        alerts = await alert_service.get_active_alerts(
            severity=severity_filter,
            acknowledged=acknowledged,
        )

        proactive_insights = await alert_service.generate_proactive_insights()

        return SafetyAlertResponse(
            total_active=len(alerts),
            critical_count=len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
            warning_count=len([a for a in alerts if a.severity == AlertSeverity.WARNING]),
            alerts=[a.to_dict() for a in alerts[:10]],
            proactive_insights=proactive_insights,
        )

    except Exception as e:
        logger.error(f"Safety alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety-alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: str = "user"):
    """Acknowledge a safety alert."""
    try:
        alert_service = get_safety_alert_service()
        success = await alert_service.acknowledge_alert(alert_id, acknowledged_by)

        if success:
            return {"success": True, "message": f"Alert {alert_id} acknowledged"}
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Acknowledge alert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/correlation", response_model=CorrelationResponse)
async def analyze_correlation(request: CorrelationRequest):
    """
    Perform correlation analysis between two variables.

    Supports Pearson and Spearman correlation.
    """
    try:
        stat_service = get_statistical_service()

        correlation_type = CorrelationType(request.correlation_type)

        result = stat_service.calculate_correlation(
            x=request.variable_1_values,
            y=request.variable_2_values,
            x_name=request.variable_1_name,
            y_name=request.variable_2_name,
            correlation_type=correlation_type,
        )

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Could not calculate correlation. Ensure sufficient valid data pairs."
            )

        return CorrelationResponse(
            variable_1=result.variable_1,
            variable_2=result.variable_2,
            correlation_type=result.correlation_type.value,
            coefficient=result.coefficient,
            p_value=result.p_value,
            sample_size=result.sample_size,
            significance=result.significance.value,
            interpretation=result.interpretation,
            confidence_interval=list(result.confidence_interval) if result.confidence_interval else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Correlation analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigate", response_model=InvestigationResponse)
async def autonomous_investigation(request: InvestigationRequest):
    """
    Perform autonomous investigation on a clinical question.

    Uses the reasoning agent to:
    - Generate hypotheses
    - Gather evidence
    - Evaluate findings
    - Provide recommendations
    """
    try:
        reasoning_agent = get_reasoning_agent()

        context = AgentContext(
            request_id=str(uuid.uuid4())[:8],
            protocol_id=request.study_id,
            parameters={
                "question": request.question,
                "max_depth": request.max_depth,
            }
        )

        result = await reasoning_agent.run(context)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        data = result.data
        synthesis = data.get("synthesis", {})
        plan = data.get("investigation_plan", {})

        return InvestigationResponse(
            question=request.question,
            summary=synthesis.get("summary", result.narrative or ""),
            hypotheses=plan.get("hypotheses", []),
            findings=synthesis.get("key_findings", []),
            recommendations=data.get("recommendations", []),
            reasoning_trace=data.get("reasoning_trace", []),
            confidence=result.confidence,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Investigation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{page_context}", response_model=ProactiveSuggestionsResponse)
async def get_proactive_suggestions(page_context: str):
    """
    Get proactive suggestions for a page context.

    Returns "What would you like to know?" suggestions tailored to the current view.
    """
    try:
        followup_service = get_followup_service()
        alert_service = get_safety_alert_service()

        # Get page-specific suggestions
        suggestions = followup_service.get_proactive_suggestions(page_context)

        # Get safety insights
        safety_insights = await alert_service.generate_proactive_insights()

        # Trending topics based on page
        trending = {
            "dashboard": ["Registry comparison", "Safety signals", "Enrollment status"],
            "safety": ["Adverse event trends", "Threshold proximity", "Device-related events"],
            "readiness": ["Data completeness", "CER preparation", "Endpoint status"],
            "risk": ["High-risk patients", "Hazard ratios", "Risk factors"],
            "competitive": ["Market positioning", "Competitor outcomes", "Claims support"],
        }

        return ProactiveSuggestionsResponse(
            page_context=page_context,
            suggestions=suggestions,
            safety_insights=safety_insights,
            trending_topics=trending.get(page_context.lower(), ["Study outcomes"]),
        )

    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a conversation session."""
    try:
        conv_service = get_conversation_service()
        conversation = await conv_service.get_session(session_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": conversation.session_id,
            "study_id": conversation.study_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "message_count": len(conversation.messages),
            "page_context": conversation.page_context,
            "context": conversation.context.to_dict(),
            "has_summary": conversation.summary is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a conversation session."""
    try:
        conv_service = get_conversation_service()
        conversation = await conv_service.get_session(session_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")

        # Remove from active sessions using public method
        deleted = await conv_service.delete_session(session_id)

        return {"success": deleted, "message": f"Session {session_id} ended"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"End session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
