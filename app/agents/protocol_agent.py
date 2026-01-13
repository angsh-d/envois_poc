"""
Protocol Agent for Clinical Intelligence Platform.

Responsible for extracting and validating protocol rules, visit windows,
and endpoint definitions from Document-as-Code YAML files.
"""
import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from data.loaders.yaml_loader import get_hybrid_loader, ProtocolRules, VisitWindow

logger = logging.getLogger(__name__)


class ProtocolAgent(BaseAgent):
    """
    Agent for protocol rule extraction and validation.

    Capabilities:
    - Load protocol rules from Document-as-Code YAML
    - Validate visit windows and calculate allowed date ranges
    - Extract endpoint definitions and success criteria
    - Provide protocol context for other agents
    """

    agent_type = AgentType.PROTOCOL

    def __init__(self, **kwargs):
        """Initialize protocol agent."""
        super().__init__(**kwargs)
        self._loader = get_hybrid_loader()
        self._protocol_rules: Optional[ProtocolRules] = None

    def _load_protocol(self) -> ProtocolRules:
        """Load protocol rules with caching."""
        if self._protocol_rules is None:
            self._protocol_rules = self._loader.load_protocol_rules()
        return self._protocol_rules

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute protocol rule extraction.

        Args:
            context: Execution context with parameters

        Returns:
            AgentResult with protocol data and visit windows
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        # Load protocol rules
        protocol = self._load_protocol()

        # Build comprehensive protocol data
        result.data = {
            "protocol_id": protocol.protocol_id,
            "protocol_version": protocol.protocol_version,
            "title": protocol.title,
            "effective_date": protocol.effective_date,
            "sample_size": {
                "target": protocol.sample_size_target,
                "interim": protocol.sample_size_interim,
            },
            "primary_endpoint": {
                "id": protocol.primary_endpoint.id,
                "name": protocol.primary_endpoint.name,
                "success_threshold": protocol.primary_endpoint.success_threshold,
                "mcid_threshold": protocol.primary_endpoint.mcid_threshold,
                "success_criterion": protocol.primary_endpoint.success_criterion,
            },
            "secondary_endpoints": [
                {
                    "id": ep.id,
                    "name": ep.name,
                    "mcid_threshold": ep.mcid_threshold,
                }
                for ep in protocol.secondary_endpoints
            ],
            "visit_windows": self._get_visit_windows_data(protocol),
            "safety_thresholds": protocol.safety_thresholds,
            "deviation_classification": protocol.deviation_classification,
        }

        # Add source
        result.add_source(
            SourceType.PROTOCOL,
            f"protocol_rules.yaml v{protocol.protocol_version}",
            confidence=1.0,
            details={"effective_date": protocol.effective_date}
        )

        return result

    def _get_visit_windows_data(self, protocol: ProtocolRules) -> List[Dict[str, Any]]:
        """Extract visit window data with calculated ranges."""
        windows = []
        for visit in protocol.visits:
            min_day, max_day = visit.get_window_range()
            windows.append({
                "id": visit.id,
                "name": visit.name,
                "target_day": visit.target_day,
                "window_minus": visit.window_minus,
                "window_plus": visit.window_plus,
                "min_day": min_day,
                "max_day": max_day,
                "required_assessments": visit.required_assessments,
                "is_primary_endpoint": visit.is_primary_endpoint,
            })
        return windows

    def get_visit_window(self, visit_id: str) -> Optional[VisitWindow]:
        """
        Get a specific visit window by ID.

        Args:
            visit_id: The visit identifier (e.g., "fu_2yr")

        Returns:
            VisitWindow object or None if not found
        """
        protocol = self._load_protocol()
        return protocol.get_visit(visit_id)

    def validate_visit_timing(
        self,
        visit_id: str,
        actual_day: int
    ) -> Dict[str, Any]:
        """
        Validate if a visit occurred within the allowed window.

        Args:
            visit_id: The visit identifier
            actual_day: Actual day of visit (from surgery)

        Returns:
            Validation result with deviation details
        """
        visit = self.get_visit_window(visit_id)
        if not visit:
            return {
                "valid": False,
                "error": f"Unknown visit ID: {visit_id}",
            }

        is_within = visit.is_within_window(actual_day)
        deviation_days = visit.get_deviation_days(actual_day)
        min_day, max_day = visit.get_window_range()

        return {
            "visit_id": visit_id,
            "visit_name": visit.name,
            "actual_day": actual_day,
            "target_day": visit.target_day,
            "allowed_range": [min_day, max_day],
            "is_within_window": is_within,
            "deviation_days": deviation_days,
            "is_primary_endpoint": visit.is_primary_endpoint,
        }

    def classify_deviation(
        self,
        visit_id: str,
        deviation_days: int
    ) -> Dict[str, Any]:
        """
        Classify a visit deviation based on protocol rules.

        Args:
            visit_id: The visit identifier
            deviation_days: Days outside the allowed window

        Returns:
            Classification with severity and required actions
        """
        protocol = self._load_protocol()
        visit = self.get_visit_window(visit_id)

        if not visit:
            return {"classification": "unknown", "error": f"Unknown visit: {visit_id}"}

        if deviation_days == 0:
            return {
                "classification": "none",
                "description": "Visit within allowed window",
                "action": None,
                "affects_evaluability": False,
            }

        # Get window size for relative calculation
        window_size = visit.window_plus + visit.window_minus
        extension_factor = deviation_days / window_size if window_size > 0 else 0

        classification_rules = protocol.deviation_classification

        if extension_factor <= classification_rules["minor"].get("max_extension_factor", 1.5):
            classification = "minor"
        elif extension_factor <= classification_rules["major"].get("max_extension_factor", 2.0):
            classification = "major"
        else:
            classification = "critical"

        rules = classification_rules[classification]

        return {
            "classification": classification,
            "description": rules.get("description", ""),
            "action": rules.get("action", ""),
            "requires_explanation": rules.get("requires_explanation", False),
            "requires_pi_notification": rules.get("requires_pi_notification", False),
            "affects_evaluability": rules.get("affects_evaluability", False),
            "deviation_days": deviation_days,
            "extension_factor": round(extension_factor, 2),
            "is_primary_endpoint_visit": visit.is_primary_endpoint,
        }

    def get_safety_thresholds(self) -> Dict[str, float]:
        """Get protocol-defined safety monitoring thresholds."""
        protocol = self._load_protocol()
        return protocol.safety_thresholds

    def get_all_visit_ids(self) -> List[str]:
        """Get list of all visit IDs in order."""
        protocol = self._load_protocol()
        return [v.id for v in protocol.visits]
