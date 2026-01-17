"""
Onboarding Service for Clinical Intelligence Platform.

Manages onboarding sessions for Product Data Stewards, coordinating
the AI-first configuration experience.

Uses SQLite database for persistent session storage.
Implements Interactive Approval workflow for data source recommendations.
"""
import asyncio
import logging
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.agents.base_agent import AgentContext, AgentType
from app.services.database_service import get_database_service

logger = logging.getLogger(__name__)


# ==================== Cache Configuration ====================
CACHE_MAX_SIZE = 100  # Maximum number of sessions to cache
CACHE_TTL_SECONDS = 3600  # Cache entries expire after 1 hour


@dataclass
class CacheEntry:
    """A cache entry with metadata for eviction."""
    session: "OnboardingSession"
    accessed_at: float  # Unix timestamp of last access
    created_at: float   # Unix timestamp when added to cache

    def is_expired(self, ttl_seconds: float = CACHE_TTL_SECONDS) -> bool:
        """Check if this entry has expired."""
        return (time.time() - self.created_at) > ttl_seconds

    def touch(self) -> None:
        """Update the access time."""
        self.accessed_at = time.time()


class OnboardingPhase(str, Enum):
    """Phases of the onboarding process."""
    CONTEXT_CAPTURE = "context_capture"
    DISCOVERY = "discovery"
    RECOMMENDATIONS = "recommendations"
    DEEP_RESEARCH = "deep_research"
    COMPLETE = "complete"


ApprovalStatus = Literal["pending", "approved", "rejected"]


class SourceApproval(BaseModel):
    """
    Approval status for a data source recommendation.

    Every recommendation can be approved, rejected, or pending.
    Rejections require a reason to improve AI recommendations.
    """
    source_id: str = Field(..., description="Unique identifier for the source")
    source_type: str = Field(..., description="Type: clinical, registry, literature, fda")
    status: ApprovalStatus = Field(default="pending", description="Approval status")
    reason: Optional[str] = Field(None, description="Required if rejected - reason for rejection")
    approved_at: Optional[datetime] = Field(None, description="When approval decision was made")
    approved_by: Optional[str] = Field(None, description="User who made the decision")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Custom settings for this source")


class ApprovalAuditEntry(BaseModel):
    """
    Audit trail entry for approval decisions.

    Records all approval actions for compliance and review.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_id: str = Field(..., description="Source being acted upon")
    source_type: str = Field(..., description="Type of source")
    action: str = Field(..., description="Action: approved, rejected, overridden, feedback, added")
    reason: Optional[str] = Field(None, description="Reason for the action")
    user_id: Optional[str] = Field(None, description="User who performed the action")
    previous_status: Optional[str] = Field(None, description="Status before this action")


class ApprovalSummary(BaseModel):
    """Summary of all approval decisions for a session."""
    total_sources: int = Field(..., description="Total number of sources recommended")
    approved_count: int = Field(..., description="Number approved")
    rejected_count: int = Field(..., description="Number rejected")
    pending_count: int = Field(..., description="Number pending decision")
    by_type: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Counts by source type")
    can_proceed: bool = Field(..., description="Whether minimum approvals met to proceed")
    minimum_required: int = Field(default=1, description="Minimum sources required to proceed")


class OnboardingSession(BaseModel):
    """Represents an active onboarding session."""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User who owns this session")
    product_name: str = Field(..., description="Product being configured")
    category: str = Field(default="", description="Product category")
    indication: str = Field(default="", description="Primary indication")
    study_phase: str = Field(default="", description="Study phase")
    protocol_id: str = Field(..., description="Protocol ID - must be provided")
    technologies: List[str] = Field(default_factory=list, description="Key technologies")
    current_phase: OnboardingPhase = Field(default=OnboardingPhase.CONTEXT_CAPTURE)
    phase_progress: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    discovery_results: Dict[str, Any] = Field(default_factory=dict)
    recommendations: Dict[str, Any] = Field(default_factory=dict)
    research_reports: Dict[str, Any] = Field(default_factory=dict)
    intelligence_brief: Dict[str, Any] = Field(default_factory=dict)
    # Interactive Approval state
    source_approvals: Dict[str, SourceApproval] = Field(default_factory=dict, description="Approval status per source")
    approval_audit: List[ApprovalAuditEntry] = Field(default_factory=list, description="Audit trail")
    steward_feedback: List[str] = Field(default_factory=list, description="Feedback from steward")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class OnboardingService:
    """
    Service for managing product onboarding sessions.

    Orchestrates the AI-first configuration flow:
    1. Context Capture - Gather product information
    2. Discovery - Run discovery agents in parallel
    3. Recommendations - Generate data source recommendations
    4. Deep Research - Run research agents to generate reports
    5. Complete - Generate intelligence brief

    Uses SQLite database for persistent session storage.
    """

    def __init__(self):
        """Initialize onboarding service with database persistence."""
        self._db = get_database_service()
        # LRU cache: OrderedDict maintains insertion order for LRU eviction
        self._session_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._onboarding_agent = None
        self._last_cleanup_time: float = time.time()

    def _get_onboarding_agent(self):
        """Lazy load onboarding agent to avoid circular imports."""
        if self._onboarding_agent is None:
            from app.agents.onboarding_agent import OnboardingAgent
            self._onboarding_agent = OnboardingAgent()
        return self._onboarding_agent

    def _evict_expired_entries(self) -> int:
        """
        Remove expired entries from the cache.

        Returns:
            Number of entries evicted
        """
        expired_keys = [
            key for key, entry in self._session_cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self._session_cache[key]

        if expired_keys:
            logger.debug(f"Evicted {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def _evict_lru_entries(self, count: int = 1) -> int:
        """
        Evict least recently used entries from the cache.

        Args:
            count: Number of entries to evict

        Returns:
            Number of entries evicted
        """
        evicted = 0
        while evicted < count and self._session_cache:
            # OrderedDict.popitem(last=False) removes oldest (LRU) entry
            session_id, _ = self._session_cache.popitem(last=False)
            evicted += 1
            logger.debug(f"LRU evicted session {session_id} from cache")

        return evicted

    def _maybe_cleanup_cache(self) -> None:
        """
        Periodically clean up expired entries.
        Called on cache access to avoid separate cleanup thread.
        """
        # Only run cleanup every 5 minutes
        if time.time() - self._last_cleanup_time > 300:
            self._evict_expired_entries()
            self._last_cleanup_time = time.time()

    def _cache_get(self, session_id: str) -> Optional[OnboardingSession]:
        """
        Get a session from cache with LRU update.

        Args:
            session_id: Session to retrieve

        Returns:
            Session if found and not expired, None otherwise
        """
        self._maybe_cleanup_cache()

        entry = self._session_cache.get(session_id)
        if entry is None:
            return None

        # Check if expired
        if entry.is_expired():
            del self._session_cache[session_id]
            logger.debug(f"Cache entry for {session_id} expired")
            return None

        # Move to end (most recently used)
        self._session_cache.move_to_end(session_id)
        entry.touch()

        return entry.session

    def _cache_put(self, session: OnboardingSession) -> None:
        """
        Add or update a session in the cache.

        Args:
            session: Session to cache
        """
        session_id = session.session_id
        now = time.time()

        # If already in cache, update and move to end
        if session_id in self._session_cache:
            self._session_cache[session_id].session = session
            self._session_cache[session_id].touch()
            self._session_cache.move_to_end(session_id)
            return

        # Evict if at capacity
        if len(self._session_cache) >= CACHE_MAX_SIZE:
            # First try to evict expired entries
            evicted = self._evict_expired_entries()
            # If still at capacity, evict LRU
            if len(self._session_cache) >= CACHE_MAX_SIZE:
                self._evict_lru_entries(1)

        # Add new entry
        self._session_cache[session_id] = CacheEntry(
            session=session,
            accessed_at=now,
            created_at=now,
        )

    def _load_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Load session from cache or database."""
        # Try cache first
        session = self._cache_get(session_id)
        if session is not None:
            return session

        # Load from database
        db_session = self._db.get_session(session_id)
        if db_session:
            session = OnboardingSession(**db_session)
            self._cache_put(session)
            return session

        return None

    def _save_session(self, session: OnboardingSession):
        """Save session to database and update cache."""
        session.updated_at = datetime.utcnow()
        self._cache_put(session)
        self._db.save_session(session.model_dump())

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with cache size, hit rate info, etc.
        """
        expired_count = sum(1 for e in self._session_cache.values() if e.is_expired())

        return {
            "size": len(self._session_cache),
            "max_size": CACHE_MAX_SIZE,
            "ttl_seconds": CACHE_TTL_SECONDS,
            "expired_entries": expired_count,
            "utilization_pct": (len(self._session_cache) / CACHE_MAX_SIZE) * 100,
        }

    async def start_session(
        self,
        product_name: str,
        category: str = "",
        indication: str = "",
        study_phase: str = "",
        protocol_id: str = "",
        technologies: List[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a new onboarding session.

        Args:
            product_name: Name of the product to configure
            category: Product category
            indication: Primary indication
            study_phase: Study phase
            protocol_id: Protocol identifier (required - no default)
            technologies: List of key technologies
            user_id: User ID for session ownership (optional for backward compatibility)

        Returns:
            Session info with AI welcome message
        """
        if not protocol_id:
            return {
                "success": False,
                "error": "protocol_id is required - no default value allowed",
            }

        session_id = str(uuid.uuid4())

        session = OnboardingSession(
            session_id=session_id,
            user_id=user_id,
            product_name=product_name,
            category=category,
            indication=indication,
            study_phase=study_phase,
            protocol_id=protocol_id,
            technologies=technologies or [],
            phase_progress={
                OnboardingPhase.CONTEXT_CAPTURE.value: {"completed": False, "progress": 0},
                OnboardingPhase.DISCOVERY.value: {"completed": False, "progress": 0},
                OnboardingPhase.RECOMMENDATIONS.value: {"completed": False, "progress": 0},
                OnboardingPhase.DEEP_RESEARCH.value: {"completed": False, "progress": 0},
                OnboardingPhase.COMPLETE.value: {"completed": False, "progress": 0},
            },
        )

        # Save to database
        self._save_session(session)

        # Run context analysis
        agent = self._get_onboarding_agent()
        context = AgentContext(
            request_id=session_id,
            protocol_id=protocol_id,
            parameters={
                "action": "analyze_context",
                "product_info": {
                    "product_name": product_name,
                    "category": category,
                    "indication": indication,
                    "study_phase": study_phase,
                    "protocol_id": protocol_id,
                    "technologies": technologies or [],
                },
            },
        )

        result = await agent.run(context)

        if result.success:
            session.phase_progress[OnboardingPhase.CONTEXT_CAPTURE.value] = {
                "completed": True,
                "progress": 100,
            }
            session.current_phase = OnboardingPhase.DISCOVERY
            self._save_session(session)

        return {
            "session_id": session_id,
            "product_name": product_name,
            "current_phase": session.current_phase.value if isinstance(session.current_phase, OnboardingPhase) else session.current_phase,
            "phase_progress": session.phase_progress,
            "analysis": result.data if result.success else {},
            "message": result.data.get("message", f"Welcome! Starting configuration for {product_name}."),
            "success": result.success,
        }

    async def run_discovery(self, session_id: str) -> Dict[str, Any]:
        """
        Run discovery phase to find relevant data sources.

        Args:
            session_id: Session identifier

        Returns:
            Discovery results and progress
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        agent = self._get_onboarding_agent()
        context = AgentContext(
            request_id=session_id,
            protocol_id=session.protocol_id,
            parameters={
                "action": "run_discovery",
                "product_info": {
                    "product_name": session.product_name,
                    "category": session.category,
                    "indication": session.indication,
                    "technologies": session.technologies,
                    "protocol_id": session.protocol_id,
                },
            },
        )

        result = await agent.run(context)

        if result.success:
            session.discovery_results = result.data.get("discovery_results", {})
            discovery_progress = result.data.get("overall_progress", 0)
            session.phase_progress[OnboardingPhase.DISCOVERY.value] = {
                "completed": discovery_progress >= 100,
                "progress": int(discovery_progress),  # Ensure integer for Pydantic validation
            }
            if discovery_progress >= 100:
                session.current_phase = OnboardingPhase.RECOMMENDATIONS
            self._save_session(session)

        return {
            "session_id": session_id,
            "current_phase": session.current_phase.value if isinstance(session.current_phase, OnboardingPhase) else session.current_phase,
            "phase_progress": session.phase_progress,
            "discovery_results": result.data if result.success else {},
            "message": result.data.get("message", "Discovery in progress..."),
            "success": result.success,
        }

    async def generate_recommendations(self, session_id: str) -> Dict[str, Any]:
        """
        Generate data source recommendations.

        Args:
            session_id: Session identifier

        Returns:
            Recommendations with insight explanations
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        agent = self._get_onboarding_agent()
        context = AgentContext(
            request_id=session_id,
            protocol_id=session.protocol_id,
            parameters={
                "action": "generate_recommendations",
                "product_info": {
                    "product_name": session.product_name,
                    "category": session.category,
                    "indication": session.indication,
                    "protocol_id": session.protocol_id,
                    "technologies": session.technologies,
                },
                "discovery_results": session.discovery_results,
            },
        )

        result = await agent.run(context)

        if result.success:
            session.recommendations = result.data.get("recommendations", {})
            # Mark recommendations as ready but DON'T advance to DEEP_RESEARCH yet
            # The steward must review and approve sources first via finalize_approvals
            session.phase_progress[OnboardingPhase.RECOMMENDATIONS.value] = {
                "completed": False,  # Not complete until steward approves
                "progress": 100,  # Discovery is done, waiting for approval
            }
            # Stay on RECOMMENDATIONS phase for Interactive Approval workflow
            session.current_phase = OnboardingPhase.RECOMMENDATIONS
            self._save_session(session)

        return {
            "session_id": session_id,
            "current_phase": session.current_phase.value if isinstance(session.current_phase, OnboardingPhase) else session.current_phase,
            "phase_progress": session.phase_progress,
            "recommendations": result.data if result.success else {},
            "message": result.data.get("message", "Recommendations ready. Please review and approve before proceeding."),
            "success": result.success,
        }

    async def run_deep_research(self, session_id: str) -> Dict[str, Any]:
        """
        Run deep research agents to generate reports.

        Args:
            session_id: Session identifier

        Returns:
            Research progress and report status
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        agent = self._get_onboarding_agent()
        context = AgentContext(
            request_id=session_id,
            protocol_id=session.protocol_id,
            parameters={
                "action": "run_deep_research",
                "product_info": {
                    "product_name": session.product_name,
                    "category": session.category,
                    "indication": session.indication,
                    "technologies": session.technologies,
                    "protocol_id": session.protocol_id,
                },
                "discovery_results": session.discovery_results,
                "recommendations": session.recommendations,
            },
        )

        result = await agent.run(context)

        if result.success:
            session.research_reports = result.data.get("research_status", {})
            overall_progress = result.data.get("overall_progress", 0)
            session.phase_progress[OnboardingPhase.DEEP_RESEARCH.value] = {
                "completed": overall_progress >= 100,
                "progress": int(overall_progress),  # Ensure integer for Pydantic validation
            }
            if result.data.get("overall_progress", 0) >= 100:
                session.current_phase = OnboardingPhase.COMPLETE
            self._save_session(session)

        return {
            "session_id": session_id,
            "current_phase": session.current_phase.value if isinstance(session.current_phase, OnboardingPhase) else session.current_phase,
            "phase_progress": session.phase_progress,
            "research_status": result.data if result.success else {},
            "message": result.data.get("message", "Deep research in progress..."),
            "success": result.success,
        }

    async def complete_onboarding(self, session_id: str) -> Dict[str, Any]:
        """
        Complete the onboarding and generate intelligence brief.

        Args:
            session_id: Session identifier

        Returns:
            Final intelligence brief and configuration summary
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        agent = self._get_onboarding_agent()
        context = AgentContext(
            request_id=session_id,
            protocol_id=session.protocol_id,
            parameters={
                "action": "generate_brief",
                "product_info": {
                    "product_name": session.product_name,
                    "category": session.category,
                    "indication": session.indication,
                    "protocol_id": session.protocol_id,
                    "technologies": session.technologies,
                },
                "discovery_results": session.discovery_results,
                "recommendations": session.recommendations,
                "research_status": session.research_reports,
            },
        )

        result = await agent.run(context)

        if result.success:
            session.intelligence_brief = result.data.get("intelligence_brief", {})
            session.phase_progress[OnboardingPhase.COMPLETE.value] = {
                "completed": True,
                "progress": 100,
            }
            session.completed_at = datetime.utcnow()
            self._save_session(session)

        return {
            "session_id": session_id,
            "current_phase": OnboardingPhase.COMPLETE.value,
            "phase_progress": session.phase_progress,
            "intelligence_brief": result.data if result.success else {},
            "configuration_complete": result.data.get("configuration_complete", False),
            "message": result.data.get("message", "Configuration complete!"),
            "success": result.success,
        }

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current status of an onboarding session.

        Args:
            session_id: Session identifier

        Returns:
            Session status and progress
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        created_at = session.created_at
        updated_at = session.updated_at
        completed_at = session.completed_at

        return {
            "session_id": session_id,
            "product_name": session.product_name,
            "current_phase": session.current_phase.value if isinstance(session.current_phase, OnboardingPhase) else session.current_phase,
            "phase_progress": session.phase_progress,
            "discovery_results": session.discovery_results,
            "recommendations": session.recommendations,
            "research_reports": session.research_reports,
            "intelligence_brief": session.intelligence_brief,
            "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
            "updated_at": updated_at.isoformat() if isinstance(updated_at, datetime) else updated_at,
            "completed_at": completed_at.isoformat() if isinstance(completed_at, datetime) else completed_at,
            "success": True,
        }

    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all active onboarding sessions from database.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        return self._db.list_sessions(limit=limit)

    # ==================== Interactive Approval Methods ====================

    def update_source_approval(
        self,
        session_id: str,
        source_type: str,
        source_id: str,
        status: ApprovalStatus,
        reason: Optional[str] = None,
        user_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update approval status for a specific data source.

        Args:
            session_id: Session identifier
            source_type: Type of source (clinical, registry, literature, fda)
            source_id: Unique identifier for the source
            status: New approval status (pending, approved, rejected)
            reason: Required if rejecting - reason for rejection
            user_id: User making the decision
            settings: Optional custom settings for this source

        Returns:
            Updated approval status and summary
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Validate rejection has reason
        if status == "rejected" and not reason:
            return {"success": False, "error": "Reason is required when rejecting a source"}

        # Create composite key for source
        approval_key = f"{source_type}:{source_id}"

        # Get previous status for audit
        previous_status = None
        if approval_key in session.source_approvals:
            previous_status = session.source_approvals[approval_key].status

        # Update or create approval
        session.source_approvals[approval_key] = SourceApproval(
            source_id=source_id,
            source_type=source_type,
            status=status,
            reason=reason,
            approved_at=datetime.utcnow() if status != "pending" else None,
            approved_by=user_id,
            settings=settings or {},
        )

        # Add audit entry
        session.approval_audit.append(ApprovalAuditEntry(
            source_id=source_id,
            source_type=source_type,
            action=status,
            reason=reason,
            user_id=user_id,
            previous_status=previous_status,
        ))

        self._save_session(session)

        return {
            "success": True,
            "session_id": session_id,
            "source_type": source_type,
            "source_id": source_id,
            "status": status,
            "approval_summary": self._get_approval_summary(session),
        }

    def submit_feedback(
        self,
        session_id: str,
        feedback: str,
        request_reanalysis: bool = False,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit steward feedback for the recommendations.

        Args:
            session_id: Session identifier
            feedback: The feedback text
            request_reanalysis: Whether to request AI re-analysis
            user_id: User submitting feedback

        Returns:
            Confirmation and updated session state
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Add feedback to session
        session.steward_feedback.append(feedback)

        # Add audit entry
        session.approval_audit.append(ApprovalAuditEntry(
            source_id="session",
            source_type="feedback",
            action="feedback",
            reason=feedback,
            user_id=user_id,
        ))

        self._save_session(session)

        return {
            "success": True,
            "session_id": session_id,
            "feedback_count": len(session.steward_feedback),
            "request_reanalysis": request_reanalysis,
            "message": "Feedback submitted successfully",
        }

    def get_approval_audit(self, session_id: str) -> Dict[str, Any]:
        """
        Get the full audit trail for a session.

        Args:
            session_id: Session identifier

        Returns:
            Complete audit history of approval decisions
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Convert audit entries to dicts for JSON serialization
        audit_entries = []
        for entry in session.approval_audit:
            entry_dict = entry.model_dump()
            # Convert datetime to ISO string
            if entry_dict.get("timestamp"):
                entry_dict["timestamp"] = entry_dict["timestamp"].isoformat()
            audit_entries.append(entry_dict)

        return {
            "success": True,
            "session_id": session_id,
            "audit_entries": audit_entries,
            "total_entries": len(audit_entries),
            "approval_summary": self._get_approval_summary(session),
        }

    def finalize_approvals(
        self,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Finalize all approvals and proceed to deep research.

        Only proceeds if minimum required sources are approved.

        Args:
            session_id: Session identifier
            user_id: User finalizing approvals

        Returns:
            Success status and next phase information
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        summary = self._get_approval_summary(session)

        if not summary.can_proceed:
            return {
                "success": False,
                "error": f"Minimum {summary.minimum_required} approved source(s) required to proceed",
                "approval_summary": summary.model_dump(),
            }

        # Add finalization audit entry
        session.approval_audit.append(ApprovalAuditEntry(
            source_id="session",
            source_type="finalization",
            action="finalized",
            reason=f"Approved {summary.approved_count} of {summary.total_sources} sources",
            user_id=user_id,
        ))

        # Mark RECOMMENDATIONS phase as completed
        session.phase_progress[OnboardingPhase.RECOMMENDATIONS.value] = {
            "completed": True,
            "progress": 100,
        }

        # Transition to deep research phase
        session.current_phase = OnboardingPhase.DEEP_RESEARCH
        self._save_session(session)

        return {
            "success": True,
            "session_id": session_id,
            "current_phase": session.current_phase.value if isinstance(session.current_phase, OnboardingPhase) else session.current_phase,
            "approval_summary": summary.model_dump(),
            "message": f"Approvals finalized. {summary.approved_count} sources approved. Proceeding to deep research.",
        }

    def get_approval_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current approval status for all sources in a session.

        Args:
            session_id: Session identifier

        Returns:
            All source approvals and summary
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Convert approvals to serializable dict
        approvals = {}
        for key, approval in session.source_approvals.items():
            approval_dict = approval.model_dump()
            if approval_dict.get("approved_at"):
                approval_dict["approved_at"] = approval_dict["approved_at"].isoformat()
            approvals[key] = approval_dict

        return {
            "success": True,
            "session_id": session_id,
            "source_approvals": approvals,
            "approval_summary": self._get_approval_summary(session).model_dump(),
            "steward_feedback": session.steward_feedback,
        }

    def _get_approval_summary(self, session: OnboardingSession) -> ApprovalSummary:
        """
        Calculate approval summary from session state.

        Args:
            session: The onboarding session

        Returns:
            Summary of all approval decisions
        """
        approved = 0
        rejected = 0
        pending = 0
        by_type: Dict[str, Dict[str, int]] = {}

        for approval in session.source_approvals.values():
            source_type = approval.source_type

            # Initialize type counters if needed
            if source_type not in by_type:
                by_type[source_type] = {"approved": 0, "rejected": 0, "pending": 0}

            if approval.status == "approved":
                approved += 1
                by_type[source_type]["approved"] += 1
            elif approval.status == "rejected":
                rejected += 1
                by_type[source_type]["rejected"] += 1
            else:
                pending += 1
                by_type[source_type]["pending"] += 1

        total = approved + rejected + pending
        minimum_required = 1

        return ApprovalSummary(
            total_sources=total,
            approved_count=approved,
            rejected_count=rejected,
            pending_count=pending,
            by_type=by_type,
            can_proceed=approved >= minimum_required,
            minimum_required=minimum_required,
        )

    def initialize_approvals_from_recommendations(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Initialize approval status for all recommendations in a session.

        Called after recommendations are generated to set up the approval workflow.

        Args:
            session_id: Session identifier

        Returns:
            Initialized approvals with pending status
        """
        session = self._load_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        recommendations = session.recommendations
        if not recommendations:
            return {"success": False, "error": "No recommendations available"}

        # Initialize approvals for each recommendation type
        recs = recommendations.get("recommendations", recommendations)

        # Clinical study
        if recs.get("clinical_study"):
            key = "clinical:clinical_study"
            if key not in session.source_approvals:
                session.source_approvals[key] = SourceApproval(
                    source_id="clinical_study",
                    source_type="clinical",
                    status="pending",
                )

        # Registries
        registries = recs.get("registries", [])
        for i, reg in enumerate(registries):
            reg_name = reg.get("name", f"registry_{i}")
            key = f"registry:{reg_name}"
            if key not in session.source_approvals:
                # Check if registry was recommended (not excluded)
                is_excluded = bool(reg.get("exclusion_reason"))
                session.source_approvals[key] = SourceApproval(
                    source_id=reg_name,
                    source_type="registry",
                    status="rejected" if is_excluded else "pending",
                    reason=reg.get("exclusion_reason") if is_excluded else None,
                )

        # Literature
        if recs.get("literature"):
            key = "literature:literature"
            if key not in session.source_approvals:
                session.source_approvals[key] = SourceApproval(
                    source_id="literature",
                    source_type="literature",
                    status="pending",
                )

        # FDA surveillance
        if recs.get("fda_surveillance"):
            key = "fda:fda_surveillance"
            if key not in session.source_approvals:
                session.source_approvals[key] = SourceApproval(
                    source_id="fda_surveillance",
                    source_type="fda",
                    status="pending",
                )

        # Phase-aware sources (from ClinicalTrials.gov and earlier FDA phases)
        if recs.get("clinical_trials"):
            key = "clinical_trials:clinical_trials"
            if key not in session.source_approvals:
                session.source_approvals[key] = SourceApproval(
                    source_id="clinical_trials",
                    source_type="clinical_trials",
                    status="pending",
                )

        if recs.get("earlier_phase_fda"):
            key = "earlier_phase_fda:earlier_phase_fda"
            if key not in session.source_approvals:
                session.source_approvals[key] = SourceApproval(
                    source_id="earlier_phase_fda",
                    source_type="earlier_phase_fda",
                    status="pending",
                )

        if recs.get("competitor_trials"):
            key = "competitor_trials:competitor_trials"
            if key not in session.source_approvals:
                session.source_approvals[key] = SourceApproval(
                    source_id="competitor_trials",
                    source_type="competitor_trials",
                    status="pending",
                )

        if recs.get("competitor_fda"):
            key = "competitor_fda:competitor_fda"
            if key not in session.source_approvals:
                session.source_approvals[key] = SourceApproval(
                    source_id="competitor_fda",
                    source_type="competitor_fda",
                    status="pending",
                )

        self._save_session(session)

        return {
            "success": True,
            "session_id": session_id,
            "approval_summary": self._get_approval_summary(session).model_dump(),
            "message": "Approvals initialized for all recommendations",
        }


# Singleton pattern
_onboarding_service: Optional[OnboardingService] = None


def get_onboarding_service() -> OnboardingService:
    """Get singleton onboarding service instance."""
    global _onboarding_service
    if _onboarding_service is None:
        _onboarding_service = OnboardingService()
    return _onboarding_service
