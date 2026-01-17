"""
Base Agent Framework for Clinical Intelligence Platform.

Provides the foundation for specialized AI agents that perform multi-source
clinical intelligence tasks with full provenance tracking.
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar

import re

from pydantic import BaseModel, Field

# Import directly from modules to avoid circular import via services/__init__.py
from app.services.llm_service import get_llm_service, LLMService
from app.services.prompt_service import get_prompt_service, PromptService

logger = logging.getLogger(__name__)


# ==================== Input Sanitization for LLM Prompts ====================

# Patterns that could indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions?",
    r"disregard\s+(previous|above|all)\s+instructions?",
    r"forget\s+(previous|above|all)\s+instructions?",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"<\s*/?\s*instruction\s*>",
    r"```\s*(system|instruction)",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<\s*SYS\s*>>",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
]

# Characters that should be escaped in user input
SPECIAL_CHARS_TO_ESCAPE = {
    '"': '\\"',
    "'": "\\'",
    "\\": "\\\\",
    "\n": " ",  # Replace newlines with spaces
    "\r": "",   # Remove carriage returns
    "\t": " ",  # Replace tabs with spaces
}


def sanitize_prompt_input(value: str, max_length: int = 1000, field_name: str = "input") -> str:
    """
    Sanitize user input before interpolating into LLM prompts.

    Protections:
    - Truncates to max_length to prevent token overflow
    - Escapes special characters that could break prompt structure
    - Detects and flags potential prompt injection attempts
    - Normalizes whitespace

    Args:
        value: The user input to sanitize
        max_length: Maximum allowed length (default 1000)
        field_name: Name of the field for logging

    Returns:
        Sanitized string safe for prompt interpolation
    """
    if not isinstance(value, str):
        value = str(value) if value is not None else ""

    # Truncate to max length
    if len(value) > max_length:
        logger.warning(f"Truncating {field_name} from {len(value)} to {max_length} chars")
        value = value[:max_length] + "..."

    # Check for prompt injection patterns
    value_lower = value.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            logger.warning(f"Potential prompt injection detected in {field_name}: {pattern}")
            # Remove the suspicious pattern
            value = re.sub(pattern, "[FILTERED]", value, flags=re.IGNORECASE)

    # Escape special characters
    for char, escaped in SPECIAL_CHARS_TO_ESCAPE.items():
        value = value.replace(char, escaped)

    # Normalize whitespace (collapse multiple spaces)
    value = " ".join(value.split())

    return value


def sanitize_prompt_parameters(parameters: Dict[str, Any], max_lengths: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Sanitize all string parameters in a dictionary for LLM prompt interpolation.

    Args:
        parameters: Dictionary of parameter name -> value
        max_lengths: Optional dict of field name -> max length overrides

    Returns:
        Dictionary with all string values sanitized
    """
    # Default max lengths for specific field types that need more space
    default_field_lengths = {
        "signals": 15000,           # Safety signals can be large
        "context": 10000,           # Context fields need room
        "data": 10000,              # Data fields need room
        "analysis": 8000,           # Analysis results
        "recommendations": 8000,    # Recommendation lists
        "narrative": 5000,          # Narrative text
        "description": 3000,        # Descriptions
    }
    max_lengths = {**default_field_lengths, **(max_lengths or {})}
    default_max_length = 1000

    sanitized = {}
    for key, value in parameters.items():
        if isinstance(value, str):
            max_len = max_lengths.get(key, default_max_length)
            sanitized[key] = sanitize_prompt_input(value, max_length=max_len, field_name=key)
        elif isinstance(value, list):
            # Sanitize list elements if they're strings
            sanitized[key] = [
                sanitize_prompt_input(str(v), max_length=200, field_name=f"{key}[{i}]")
                if isinstance(v, str) else v
                for i, v in enumerate(value)
            ]
        else:
            sanitized[key] = value

    return sanitized


class AgentType(str, Enum):
    """Types of specialized agents."""
    PROTOCOL = "protocol"
    DATA = "data"
    LITERATURE = "literature"
    REGISTRY = "registry"
    COMPLIANCE = "compliance"
    SAFETY = "safety"
    SYNTHESIS = "synthesis"
    FDA = "fda"
    # Onboarding and Research agents
    ONBOARDING = "onboarding"
    PUBLICATION_DISCOVERY = "publication_discovery"
    DEEP_RESEARCH = "deep_research"
    REPORT_GENERATION = "report_generation"
    RESEARCH = "research"  # For competitive intelligence and general research


class SourceType(str, Enum):
    """Types of evidence sources."""
    PROTOCOL = "protocol"
    STUDY_DATA = "study_data"
    LITERATURE = "literature"
    REGISTRY = "registry"
    LLM_INFERENCE = "llm_inference"
    CALCULATION = "calculation"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    SAFETY_ANALYSIS = "safety_analysis"
    FDA_MAUDE = "fda_maude"
    FDA_510K = "fda_510k"
    FDA_RECALL = "fda_recall"
    # Onboarding and Research sources
    PUBMED = "pubmed"
    WEB_RESEARCH = "web_research"
    COMPETITIVE_INTEL = "competitive_intel"
    REGULATORY_INTEL = "regulatory_intel"


class ConfidenceLevel(str, Enum):
    """Confidence levels for AI-generated content."""
    HIGH = "high"           # >= 0.8: Strong evidence, multiple sources
    MODERATE = "moderate"   # >= 0.6: Adequate evidence, single source
    LOW = "low"             # >= 0.4: Limited evidence, inference required
    INSUFFICIENT = "insufficient"  # < 0.4: Cannot make reliable statement


# Minimum confidence thresholds for different response types
CONFIDENCE_THRESHOLDS = {
    "clinical_recommendation": 0.7,  # Recommendations need high confidence
    "safety_signal": 0.6,            # Safety signals need moderate+ confidence
    "risk_assessment": 0.6,          # Risk assessments need moderate+ confidence
    "narrative_generation": 0.5,     # Narratives need some data support
    "data_summary": 0.4,             # Summaries can work with limited data
}


@dataclass
class UncertaintyInfo:
    """Information about response uncertainty and limitations."""
    confidence_level: ConfidenceLevel
    confidence_score: float
    data_gaps: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "confidence_level": self.confidence_level.value,
            "confidence_score": self.confidence_score,
            "data_gaps": self.data_gaps,
            "limitations": self.limitations,
            "reasoning": self.reasoning,
        }

    @property
    def is_sufficient(self) -> bool:
        """Check if confidence is sufficient for response."""
        return self.confidence_level != ConfidenceLevel.INSUFFICIENT


@dataclass
class Source:
    """Evidence source for provenance tracking."""
    type: SourceType
    reference: str
    confidence: float = 1.0
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "reference": self.reference,
            "confidence": self.confidence,
            "details": self.details,
        }


class AgentContext(BaseModel):
    """Context passed to agents for task execution."""
    request_id: str = Field(..., description="Unique request identifier")
    patient_id: Optional[str] = Field(None, description="Patient ID if applicable")
    visit_id: Optional[str] = Field(None, description="Visit ID if applicable")
    protocol_id: str = Field(default="H-34", description="Protocol identifier")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")

    # Shared context from other agents
    shared_data: Dict[str, Any] = Field(default_factory=dict, description="Data from other agents")

    # Execution constraints
    max_llm_calls: int = Field(default=10, description="Maximum LLM calls allowed")
    timeout_seconds: float = Field(default=120.0, description="Execution timeout")
    require_provenance: bool = Field(default=True, description="Require source tracking")

    class Config:
        extra = "allow"


@dataclass
class AgentResult:
    """Result from agent execution with full provenance."""
    agent_type: AgentType
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    sources: List[Source] = field(default_factory=list)
    narrative: Optional[str] = None
    confidence: float = 1.0
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    llm_calls: int = 0
    uncertainty: Optional[UncertaintyInfo] = None
    reasoning: Optional[str] = None  # Explicit reasoning for AI-generated content
    # Display configuration for intelligent response rendering
    preferred_display: str = "narrative"  # narrative, table, chart, metric_grid, mixed
    chart_data: Optional[Dict[str, Any]] = None
    table_data: Optional[Dict[str, Any]] = None
    metric_grid: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with serialized sources."""
        result = {
            "agent_type": self.agent_type.value,
            "success": self.success,
            "data": self.data,
            "sources": [s.to_dict() for s in self.sources],
            "narrative": self.narrative,
            "confidence": self.confidence,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "llm_calls": self.llm_calls,
            "preferred_display": self.preferred_display,
        }
        if self.uncertainty:
            result["uncertainty"] = self.uncertainty.to_dict()
        if self.reasoning:
            result["reasoning"] = self.reasoning
        if self.chart_data:
            result["chart_data"] = self.chart_data
        if self.table_data:
            result["table_data"] = self.table_data
        if self.metric_grid:
            result["metric_grid"] = self.metric_grid
        return result

    def add_source(
        self,
        source_type: SourceType,
        reference: str,
        confidence: float = 1.0,
        details: Optional[Dict[str, Any]] = None
    ):
        """Add a source to the result."""
        self.sources.append(Source(
            type=source_type,
            reference=reference,
            confidence=confidence,
            details=details,
        ))

    def get_confidence_level(self) -> ConfidenceLevel:
        """Get confidence level based on score."""
        if self.confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.6:
            return ConfidenceLevel.MODERATE
        elif self.confidence >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.INSUFFICIENT

    def set_uncertainty(
        self,
        data_gaps: List[str] = None,
        limitations: List[str] = None,
        reasoning: str = ""
    ):
        """Set uncertainty information for the result."""
        self.uncertainty = UncertaintyInfo(
            confidence_level=self.get_confidence_level(),
            confidence_score=self.confidence,
            data_gaps=data_gaps or [],
            limitations=limitations or [],
            reasoning=reasoning,
        )

    @staticmethod
    def insufficient_data(
        agent_type: AgentType,
        reason: str,
        data_gaps: List[str],
        available_data: Dict[str, Any] = None
    ) -> "AgentResult":
        """
        Create a result indicating insufficient data to make a determination.

        This is the "I don't know" response - used when data is insufficient
        to make a reliable statement rather than guessing or hallucinating.

        Args:
            agent_type: The agent type
            reason: Human-readable explanation of why data is insufficient
            data_gaps: List of specific data that is missing
            available_data: What data IS available (for transparency)

        Returns:
            AgentResult with insufficient_data flag and explanation
        """
        result = AgentResult(
            agent_type=agent_type,
            success=True,  # Not a failure - correctly identifying limitations
            data={
                "insufficient_data": True,
                "reason": reason,
                "data_gaps": data_gaps,
                "available_data": available_data or {},
            },
            confidence=0.0,
            narrative=f"Unable to provide assessment: {reason}. Missing data: {', '.join(data_gaps)}.",
            reasoning=f"Insufficient data prevents reliable analysis. Specific gaps: {data_gaps}",
        )
        result.set_uncertainty(
            data_gaps=data_gaps,
            limitations=["Insufficient data for reliable analysis"],
            reasoning=reason,
        )
        return result

    @property
    def has_sufficient_data(self) -> bool:
        """Check if result has sufficient data for the response type."""
        if self.data.get("insufficient_data"):
            return False
        return self.confidence >= CONFIDENCE_THRESHOLDS.get("data_summary", 0.4)


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.

    Provides:
    - LLM and prompt service integration
    - Execution timing and monitoring
    - Provenance tracking infrastructure
    - Error handling and retry logic
    """

    agent_type: AgentType = None

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
    ):
        """
        Initialize base agent.

        Args:
            llm_service: LLM service instance (uses singleton if not provided)
            prompt_service: Prompt service instance (uses singleton if not provided)
        """
        self.llm = llm_service or get_llm_service()
        self.prompts = prompt_service or get_prompt_service()
        self._llm_call_count = 0

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent's primary task.

        Args:
            context: Execution context with parameters and constraints

        Returns:
            AgentResult with data, sources, and optional narrative
        """
        pass

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Run the agent with timing and error handling.

        Args:
            context: Execution context

        Returns:
            AgentResult with execution metadata
        """
        start_time = time.time()
        self._llm_call_count = 0

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self.execute(context),
                timeout=context.timeout_seconds
            )
            result.execution_time_ms = (time.time() - start_time) * 1000
            result.llm_calls = self._llm_call_count

            logger.info(
                f"{self.agent_type.value} agent completed in {result.execution_time_ms:.0f}ms "
                f"with {result.llm_calls} LLM calls"
            )
            return result

        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"{self.agent_type.value} agent timed out after {context.timeout_seconds}s")
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=f"Agent timed out after {context.timeout_seconds}s",
                execution_time_ms=execution_time,
                llm_calls=self._llm_call_count,
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.exception(f"{self.agent_type.value} agent failed: {e}")
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                llm_calls=self._llm_call_count,
            )

    async def call_llm(
        self,
        prompt: str,
        model: str = "gemini-3-pro-preview",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Call LLM with tracking.

        Args:
            prompt: The prompt text
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            LLM response text
        """
        self._llm_call_count += 1
        return await self.llm.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def call_llm_json(
        self,
        prompt: str,
        model: str = "gemini-3-pro-preview",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Call LLM expecting JSON response.

        Args:
            prompt: The prompt text (should request JSON output)
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            Parsed JSON dictionary
        """
        self._llm_call_count += 1
        return await self.llm.generate_json(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def load_prompt(
        self,
        prompt_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        strict: bool = False,
        sanitize: bool = True,
    ) -> str:
        """
        Load a prompt template with parameter substitution.

        Args:
            prompt_name: Name of the prompt file (without .txt)
            parameters: Values to substitute into the template
            strict: If True, raise error on missing parameters
            sanitize: If True, sanitize parameters to prevent prompt injection (default True)

        Returns:
            Populated prompt string
        """
        params = parameters or {}
        if sanitize and params:
            params = sanitize_prompt_parameters(params)
        return self.prompts.load(prompt_name, params, strict)


class AgentOrchestrator:
    """
    Orchestrates multi-agent workflows.

    Coordinates agent execution, manages shared context, and combines results.
    """

    def __init__(self):
        """Initialize orchestrator."""
        self._agents: Dict[AgentType, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """
        Register an agent with the orchestrator.

        Args:
            agent: Agent instance to register
        """
        if agent.agent_type is None:
            raise ValueError(f"Agent {type(agent).__name__} has no agent_type defined")
        self._agents[agent.agent_type] = agent
        logger.info(f"Registered {agent.agent_type.value} agent")

    def get_agent(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """Get registered agent by type."""
        return self._agents.get(agent_type)

    async def run_agent(
        self,
        agent_type: AgentType,
        context: AgentContext
    ) -> AgentResult:
        """
        Run a single agent.

        Args:
            agent_type: Type of agent to run
            context: Execution context

        Returns:
            Agent result
        """
        agent = self._agents.get(agent_type)
        if not agent:
            raise ValueError(f"No agent registered for type: {agent_type}")
        return await agent.run(context)

    async def run_parallel(
        self,
        agent_types: List[AgentType],
        context: AgentContext
    ) -> Dict[AgentType, AgentResult]:
        """
        Run multiple agents in parallel.

        Args:
            agent_types: List of agent types to run
            context: Shared execution context

        Returns:
            Dictionary mapping agent types to results
        """
        agents = []
        for agent_type in agent_types:
            agent = self._agents.get(agent_type)
            if agent:
                agents.append((agent_type, agent.run(context)))
            else:
                logger.warning(f"No agent registered for type: {agent_type}")

        # Run all agents in parallel
        results = await asyncio.gather(
            *[task for _, task in agents],
            return_exceptions=True
        )

        # Map results back to agent types
        result_map = {}
        for (agent_type, _), result in zip(agents, results):
            if isinstance(result, Exception):
                result_map[agent_type] = AgentResult(
                    agent_type=agent_type,
                    success=False,
                    error=str(result),
                )
            else:
                result_map[agent_type] = result

        return result_map

    async def run_pipeline(
        self,
        pipeline: List[List[AgentType]],
        initial_context: AgentContext
    ) -> Dict[AgentType, AgentResult]:
        """
        Run agents in a pipeline with stages.

        Each stage runs in parallel, and results are shared with subsequent stages.

        Args:
            pipeline: List of stages, each stage is a list of agent types to run in parallel
            initial_context: Starting context

        Returns:
            All agent results
        """
        context = initial_context.model_copy()
        all_results: Dict[AgentType, AgentResult] = {}

        for stage_index, stage_agents in enumerate(pipeline):
            logger.info(f"Running pipeline stage {stage_index + 1}/{len(pipeline)}: {stage_agents}")

            # Run stage in parallel
            stage_results = await self.run_parallel(stage_agents, context)

            # Collect results
            all_results.update(stage_results)

            # Share successful results with next stage
            for agent_type, result in stage_results.items():
                if result.success:
                    context.shared_data[agent_type.value] = result.to_dict()

        return all_results


# Singleton orchestrator
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
