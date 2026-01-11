"""
Agent Framework for Clinical Intelligence Platform.

This module contains specialized AI agents that work together to provide
multi-source clinical intelligence:

- ProtocolAgent: Extracts and validates protocol rules
- DataAgent: Queries and analyzes study data
- LiteratureAgent: RAG-based literature search and benchmark extraction
- RegistryAgent: Population norms and external validation
- ComplianceAgent: Protocol deviation detection and classification
- SafetyAgent: Safety signal detection and risk factor analysis
- SynthesisAgent: Multi-agent output combination and narrative generation
"""

from app.agents.base_agent import (
    BaseAgent,
    AgentContext,
    AgentResult,
    AgentType,
    AgentOrchestrator,
    Source,
    SourceType,
    get_orchestrator,
)
from app.agents.protocol_agent import ProtocolAgent
from app.agents.data_agent import DataAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.registry_agent import RegistryAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.synthesis_agent import SynthesisAgent

__all__ = [
    # Base framework
    "BaseAgent",
    "AgentContext",
    "AgentResult",
    "AgentType",
    "AgentOrchestrator",
    "Source",
    "SourceType",
    "get_orchestrator",
    # Specialized agents
    "ProtocolAgent",
    "DataAgent",
    "LiteratureAgent",
    "RegistryAgent",
    "ComplianceAgent",
    "SafetyAgent",
    "SynthesisAgent",
]


def initialize_agents() -> AgentOrchestrator:
    """
    Initialize and register all agents with the orchestrator.

    Returns:
        Configured AgentOrchestrator instance
    """
    orchestrator = get_orchestrator()

    # Register all specialized agents
    orchestrator.register(ProtocolAgent())
    orchestrator.register(DataAgent())
    orchestrator.register(LiteratureAgent())
    orchestrator.register(RegistryAgent())
    orchestrator.register(ComplianceAgent())
    orchestrator.register(SafetyAgent())
    orchestrator.register(SynthesisAgent())

    return orchestrator
