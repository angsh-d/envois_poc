"""
Conversation Memory Service for Clinical Intelligence Platform.

Provides persistent multi-turn conversation management with:
- Session-based conversation storage
- Context window optimization
- Memory summarization for long conversations
- Conversation retrieval and continuation
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConversationRole(str, Enum):
    """Role of message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Type of message content."""
    TEXT = "text"
    QUERY = "query"
    RESPONSE = "response"
    SUMMARY = "summary"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"


@dataclass
class ConversationMessage:
    """Single message in a conversation."""
    id: str
    role: ConversationRole
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    agent_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "sources": self.sources,
            "agent_results": self.agent_results,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            role=ConversationRole(data["role"]),
            content=data["content"],
            message_type=MessageType(data.get("message_type", "text")),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            sources=data.get("sources", []),
            agent_results=data.get("agent_results", {}),
        )


@dataclass
class ConversationContext:
    """Extracted context from conversation history."""
    key_topics: List[str] = field(default_factory=list)
    mentioned_metrics: List[str] = field(default_factory=list)
    patient_ids: List[str] = field(default_factory=list)
    time_periods: List[str] = field(default_factory=list)
    active_comparisons: List[Dict[str, str]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    unresolved_questions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_topics": self.key_topics,
            "mentioned_metrics": self.mentioned_metrics,
            "patient_ids": self.patient_ids,
            "time_periods": self.time_periods,
            "active_comparisons": self.active_comparisons,
            "user_preferences": self.user_preferences,
            "unresolved_questions": self.unresolved_questions,
        }


@dataclass
class Conversation:
    """Full conversation with metadata."""
    session_id: str
    study_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessage] = field(default_factory=list)
    context: ConversationContext = field(default_factory=ConversationContext)
    summary: Optional[str] = None
    page_context: str = "dashboard"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "study_id": self.study_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context.to_dict(),
            "summary": self.summary,
            "page_context": self.page_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dictionary."""
        context_data = data.get("context", {})
        context = ConversationContext(
            key_topics=context_data.get("key_topics", []),
            mentioned_metrics=context_data.get("mentioned_metrics", []),
            patient_ids=context_data.get("patient_ids", []),
            time_periods=context_data.get("time_periods", []),
            active_comparisons=context_data.get("active_comparisons", []),
            user_preferences=context_data.get("user_preferences", {}),
            unresolved_questions=context_data.get("unresolved_questions", []),
        )
        return cls(
            session_id=data["session_id"],
            study_id=data["study_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=[ConversationMessage.from_dict(m) for m in data.get("messages", [])],
            context=context,
            summary=data.get("summary"),
            page_context=data.get("page_context", "dashboard"),
        )

    def add_message(
        self,
        role: ConversationRole,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        sources: List[Dict[str, Any]] = None,
        agent_results: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> ConversationMessage:
        """Add a message to the conversation."""
        message = ConversationMessage(
            id=str(uuid.uuid4())[:8],
            role=role,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow(),
            sources=sources or [],
            agent_results=agent_results or {},
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message

    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """Get most recent messages."""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages

    def get_context_window(self, max_tokens: int = 4000) -> str:
        """
        Build context window from recent messages.

        Includes summary of older messages + recent full messages.
        """
        parts = []

        # Add summary if exists and conversation is long
        if self.summary and len(self.messages) > 10:
            parts.append(f"[Previous conversation summary: {self.summary}]")

        # Add recent messages (last 5)
        recent = self.get_recent_messages(5)
        for msg in recent:
            role_label = "User" if msg.role == ConversationRole.USER else "Assistant"
            parts.append(f"{role_label}: {msg.content}")

        return "\n\n".join(parts)


class ConversationService:
    """
    Service for managing conversation sessions.

    Features:
    - In-memory storage with TTL
    - Session creation and retrieval
    - Context extraction and summarization
    - Multi-turn memory management
    """

    def __init__(
        self,
        ttl_hours: int = 24,
        max_messages_before_summarize: int = 20,
    ):
        """
        Initialize conversation service.

        Args:
            ttl_hours: Hours to keep inactive conversations
            max_messages_before_summarize: Trigger summarization threshold
        """
        self._conversations: Dict[str, Conversation] = {}
        self._lock = asyncio.Lock()
        self._ttl = timedelta(hours=ttl_hours)
        self._max_messages = max_messages_before_summarize
        self._llm_service = None

    def _get_llm_service(self):
        """Lazy load LLM service to avoid circular imports."""
        if self._llm_service is None:
            from app.services.llm_service import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    async def create_session(
        self,
        study_id: str,
        page_context: str = "dashboard",
    ) -> str:
        """
        Create a new conversation session.

        Args:
            study_id: Study identifier
            page_context: Current page context

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        conversation = Conversation(
            session_id=session_id,
            study_id=study_id,
            created_at=now,
            updated_at=now,
            page_context=page_context,
        )

        async with self._lock:
            self._conversations[session_id] = conversation

        logger.info(f"Created conversation session: {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID."""
        async with self._lock:
            conv = self._conversations.get(session_id)
            if conv:
                # Check TTL
                if datetime.utcnow() - conv.updated_at > self._ttl:
                    del self._conversations[session_id]
                    return None
            return conv

    async def get_or_create_session(
        self,
        session_id: Optional[str],
        study_id: str,
        page_context: str = "dashboard",
    ) -> tuple[str, Conversation]:
        """
        Get existing session or create new one.

        Args:
            session_id: Optional existing session ID
            study_id: Study identifier
            page_context: Current page context

        Returns:
            Tuple of (session_id, conversation)
        """
        if session_id:
            conv = await self.get_session(session_id)
            if conv:
                return session_id, conv

        # Create new session
        new_session_id = await self.create_session(study_id, page_context)
        conv = await self.get_session(new_session_id)
        return new_session_id, conv

    async def add_user_message(
        self,
        session_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> Optional[ConversationMessage]:
        """Add a user message to the conversation."""
        conv = await self.get_session(session_id)
        if not conv:
            logger.warning(f"Session not found: {session_id}")
            return None

        message = conv.add_message(
            role=ConversationRole.USER,
            content=content,
            message_type=MessageType.QUERY,
            metadata=metadata,
        )

        # Update context with extracted information
        await self._update_context(conv, content)

        return message

    async def add_assistant_message(
        self,
        session_id: str,
        content: str,
        sources: List[Dict[str, Any]] = None,
        agent_results: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> Optional[ConversationMessage]:
        """Add an assistant response to the conversation."""
        conv = await self.get_session(session_id)
        if not conv:
            logger.warning(f"Session not found: {session_id}")
            return None

        message = conv.add_message(
            role=ConversationRole.ASSISTANT,
            content=content,
            message_type=MessageType.RESPONSE,
            sources=sources,
            agent_results=agent_results,
            metadata=metadata,
        )

        # Check if summarization needed
        if len(conv.messages) >= self._max_messages:
            await self._summarize_conversation(conv)

        return message

    async def _update_context(self, conv: Conversation, user_message: str):
        """
        Extract and update conversation context from user message.

        Uses pattern matching and LLM for context extraction.
        """
        message_lower = user_message.lower()

        # Extract patient IDs (e.g., "patient 123", "P-001")
        import re
        patient_patterns = [
            r"patient[\s-]*(\d+)",
            r"p[\s-]*(\d+)",
            r"subject[\s-]*(\d+)",
        ]
        for pattern in patient_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                if match not in conv.context.patient_ids:
                    conv.context.patient_ids.append(match)

        # Extract time periods with actual units
        time_patterns = [
            (r"(\d+)\s*(?:year|yr)s?", "years"),
            (r"(\d+)\s*(?:month|mo)s?", "months"),
            (r"(\d+)\s*(?:week|wk)s?", "weeks"),
            (r"(\d+)\s*(?:day)s?", "days"),
        ]
        for pattern, unit in time_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                period = f"{match} {unit}"
                if period not in conv.context.time_periods:
                    conv.context.time_periods.append(period)

        # Extract mentioned metrics (clinically relevant terms)
        metric_keywords = [
            "hhs", "ohs", "survival", "revision", "infection",
            "dislocation", "loosening", "fracture", "ae", "sae",
            "mcid", "benchmark", "threshold", "complication",
            "mortality", "failure", "aseptic", "periprosthetic",
            "cup", "liner", "stem", "head", "bearing",
        ]
        for keyword in metric_keywords:
            if keyword in message_lower and keyword not in conv.context.mentioned_metrics:
                conv.context.mentioned_metrics.append(keyword)

        # Extract topics
        topic_keywords = [
            "safety", "efficacy", "readiness", "compliance", "deviation",
            "risk", "outcome", "registry", "literature", "competitive",
        ]
        for keyword in topic_keywords:
            if keyword in message_lower and keyword not in conv.context.key_topics:
                conv.context.key_topics.append(keyword)

    async def _summarize_conversation(self, conv: Conversation):
        """
        Summarize older messages to manage context window.

        Keeps last 5 messages full, summarizes the rest.
        """
        if len(conv.messages) < 10:
            return

        # Get messages to summarize (all but last 5)
        to_summarize = conv.messages[:-5]

        # Build summary prompt
        messages_text = "\n".join([
            f"{m.role.value}: {m.content[:200]}..."
            for m in to_summarize
        ])

        summary_prompt = f"""Summarize the following conversation history into a concise summary
that captures:
1. Key questions asked by the user
2. Main findings and insights provided
3. Any unresolved questions or topics to follow up on
4. Important data points or metrics discussed

Conversation:
{messages_text}

Provide a summary in 2-3 sentences that would help continue this conversation:"""

        try:
            llm = self._get_llm_service()
            conv.summary = await llm.generate(
                prompt=summary_prompt,
                model="gemini-3-pro-preview",
                temperature=0.3,
                max_tokens=300,
            )
            logger.info(f"Summarized conversation {conv.session_id}")
        except Exception as e:
            logger.warning(f"Failed to summarize conversation: {e}")

    def get_context_window(self, session_id: str, max_tokens: int = 4000) -> str:
        """Build context window for LLM from conversation history."""
        conv = self._conversations.get(session_id)
        if not conv:
            return ""
        return conv.get_context_window(max_tokens)

    async def get_conversation_context(
        self,
        session_id: str
    ) -> Optional[ConversationContext]:
        """Get extracted context from conversation."""
        conv = await self.get_session(session_id)
        if not conv:
            return None
        return conv.context

    async def cleanup_expired(self):
        """Remove expired conversations."""
        now = datetime.utcnow()
        async with self._lock:
            expired = [
                sid for sid, conv in self._conversations.items()
                if now - conv.updated_at > self._ttl
            ]
            for sid in expired:
                del self._conversations[sid]
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired conversations")

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if session was deleted, False if not found
        """
        async with self._lock:
            if session_id in self._conversations:
                del self._conversations[session_id]
                logger.info(f"Deleted conversation session: {session_id}")
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "active_sessions": len(self._conversations),
            "ttl_hours": self._ttl.total_seconds() / 3600,
            "max_messages_before_summarize": self._max_messages,
        }


# Singleton instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get singleton conversation service instance."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
