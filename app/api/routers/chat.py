"""
Chat API endpoint with orchestration for natural language queries.
"""
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class Source(BaseModel):
    """Source citation for AI response."""
    type: str  # study_data, protocol, literature, registry
    reference: str
    detail: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message in conversation history."""
    role: str  # user or assistant
    content: str
    sources: Optional[List[Source]] = None
    timestamp: str


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str
    context: str  # Current page context (dashboard, readiness, safety, etc.)
    study_id: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    sources: List[Source]
    suggested_followups: Optional[List[str]] = None


# Context prompts for each module
CONTEXT_PROMPTS = {
    "dashboard": """You are an AI assistant for the H-34 DELTA Revision Cup clinical study executive dashboard.
The user is viewing the overall study status including:
- Readiness: 72% (2 blockers: sample size gap, missing imaging)
- Safety: 1 monitored signal (fracture rate 13%, explained by osteoporosis)
- Compliance: 96% (6 deviations out of 148 assessments)
- At-Risk: 4 high-risk patients flagged

Key metrics: 37/50 enrolled (74%), 62% MCID achievement, +34.9 HHS improvement.""",

    "readiness": """You are an AI assistant for regulatory submission readiness assessment.
Current status: 72% ready with 2 critical blockers.
- Sample size: Only 8/25 patients evaluable at 2-year endpoint
- Missing imaging: 3 patients (015, 023, 031) missing 1-year radiographic data
- MCID: 62% achievement (5/8), within literature range 60-80%
- Safety documentation: Complete (12/12 SAE narratives)""",

    "safety": """You are an AI assistant for safety signal analysis.
Current signals:
- Periprosthetic fracture: 13% rate vs 8% threshold - MONITORED but EXPLAINED
  - 5/5 fractures in osteoporotic patients (32% prevalence)
  - Literature (Dixon 2025): Expected 15-20% in osteoporotic cohorts
  - Registry (AOANJRR): Risk-adjusted expectation 10-15%
- Dislocation: 5% (within threshold)
- Infection: 3% (below threshold)""",

    "deviations": """You are an AI assistant for protocol deviation detection.
Current status: 6 deviations detected from 148 visit-assessments (4.1% rate)
- 3 Minor: Timing deviations within extended window
- 2 Major: Beyond window or missing assessment  
- 1 Critical: Patient 023 missing 2-year visit (affects primary endpoint)
Most common issue: 6-month visit scheduling delays.""",

    "risk": """You are an AI assistant for patient risk stratification.
Risk distribution: 4 high (>20%), 8 moderate (10-20%), 25 low (<10%)
Top risk factors:
- Osteoporosis (HR 2.4 from Dixon 2025)
- Prior revision (HR 2.1 from Meding 2025)
- BMI > 35 (HR 1.6 from AOANJRR)
High-risk patients: 017 (82%), 031 (71%), 023 (68%), 009 (55%)"""
}


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a natural language query with context awareness.
    """
    try:
        llm = LLMService()
        
        # Get context-specific system prompt
        context_prompt = CONTEXT_PROMPTS.get(request.context, CONTEXT_PROMPTS["dashboard"])
        
        # Build conversation history
        history_text = ""
        if request.history:
            for msg in request.history[-5:]:  # Last 5 messages for context
                history_text += f"\n{msg.role.upper()}: {msg.content}"
        
        # Build full prompt
        prompt = f"""{context_prompt}

CONVERSATION HISTORY:{history_text}

USER QUESTION: {request.message}

Provide a helpful, accurate response based on the study data. Be concise but thorough.
Always cite your sources when referencing specific data points.
If you don't have enough information, say so rather than making things up.

Respond in a natural, conversational tone suitable for a clinical affairs professional."""

        # Call LLM - returns a string
        response_text = await llm.generate(
            prompt=prompt,
            model="gemini-2.0-flash",
            temperature=0.3,
            max_tokens=1024
        )
        
        # Extract sources based on content (simplified)
        sources = []
        response_lower = response_text.lower()
        if "protocol" in response_lower:
            sources.append(Source(type="protocol", reference="CIP v2.0"))
        if "dixon" in response_lower or "literature" in response_lower:
            sources.append(Source(type="literature", reference="Dixon et al 2025"))
        if "aoanjrr" in response_lower or "registry" in response_lower:
            sources.append(Source(type="registry", reference="AOANJRR 2024"))
        if "patient" in response_lower or "%" in response_text:
            sources.append(Source(type="study_data", reference="H-34 Study Data"))
        
        # Generate follow-up suggestions
        followups = [
            "What should I focus on next?",
            "How does this compare to other studies?",
            "What actions should I take?"
        ]
        
        return ChatResponse(
            response=response_text,
            sources=sources if sources else [Source(type="study_data", reference="H-34 Study Data")],
            suggested_followups=followups
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
