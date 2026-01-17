"""
Follow-up Suggestion Engine for Clinical Intelligence Platform.

Generates intelligent follow-up questions and investigation suggestions
based on conversation context, user queries, and data patterns.
"""
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SuggestionCategory(str, Enum):
    """Category of follow-up suggestion."""
    DEEP_DIVE = "deep_dive"           # Explore topic in more detail
    COMPARISON = "comparison"          # Compare with benchmarks
    TREND_ANALYSIS = "trend_analysis"  # Analyze trends over time
    RISK_ASSESSMENT = "risk_assessment"  # Assess risks
    CLINICAL_DETAIL = "clinical_detail"  # Get clinical specifics
    REGULATORY = "regulatory"          # Regulatory-related
    STRATEGIC = "strategic"            # Strategic/business insights


@dataclass
class FollowUpSuggestion:
    """A suggested follow-up question or investigation."""
    question: str
    category: SuggestionCategory
    rationale: str
    priority: int = 1  # 1 = highest
    related_metrics: List[str] = field(default_factory=list)
    agents_needed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "category": self.category.value,
            "rationale": self.rationale,
            "priority": self.priority,
            "related_metrics": self.related_metrics,
            "agents_needed": self.agents_needed,
        }


# Context-based suggestion templates
TOPIC_SUGGESTIONS = {
    "safety": [
        FollowUpSuggestion(
            question="How do our adverse event rates compare to registry benchmarks?",
            category=SuggestionCategory.COMPARISON,
            rationale="Understanding relative safety performance vs. population data",
            priority=1,
            related_metrics=["ae_rate", "sae_rate"],
            agents_needed=["data", "registry"],
        ),
        FollowUpSuggestion(
            question="What patient risk factors are associated with higher complication rates?",
            category=SuggestionCategory.RISK_ASSESSMENT,
            rationale="Identify modifiable risk factors for intervention",
            priority=2,
            related_metrics=["risk_factors", "ae_rate"],
            agents_needed=["data", "literature"],
        ),
        FollowUpSuggestion(
            question="Are there site-specific differences in adverse event reporting?",
            category=SuggestionCategory.DEEP_DIVE,
            rationale="Detect potential site quality or reporting variability",
            priority=2,
            related_metrics=["ae_rate", "site_metrics"],
            agents_needed=["data"],
        ),
        FollowUpSuggestion(
            question="What are the revision reasons and how do they compare to literature?",
            category=SuggestionCategory.COMPARISON,
            rationale="Understand failure modes vs. expected patterns",
            priority=1,
            related_metrics=["revision_reasons", "revision_rate"],
            agents_needed=["data", "literature", "registry"],
        ),
    ],
    "efficacy": [
        FollowUpSuggestion(
            question="What percentage of patients achieved MCID in functional scores?",
            category=SuggestionCategory.CLINICAL_DETAIL,
            rationale="Primary efficacy endpoint assessment",
            priority=1,
            related_metrics=["mcid_rate", "hhs_improvement"],
            agents_needed=["data"],
        ),
        FollowUpSuggestion(
            question="How does our survival rate compare to all international registries?",
            category=SuggestionCategory.COMPARISON,
            rationale="Benchmark against population-level outcomes",
            priority=1,
            related_metrics=["survival_rate", "revision_rate"],
            agents_needed=["data", "registry"],
        ),
        FollowUpSuggestion(
            question="Which patient subgroups have the best and worst outcomes?",
            category=SuggestionCategory.RISK_ASSESSMENT,
            rationale="Identify factors for patient selection optimization",
            priority=2,
            related_metrics=["hhs_improvement", "demographics"],
            agents_needed=["data"],
        ),
    ],
    "readiness": [
        FollowUpSuggestion(
            question="What are the current data quality gaps for regulatory submission?",
            category=SuggestionCategory.REGULATORY,
            rationale="Identify completion requirements",
            priority=1,
            related_metrics=["data_completeness", "follow_up_rate"],
            agents_needed=["data"],
        ),
        FollowUpSuggestion(
            question="Are all protocol-defined endpoints captured adequately?",
            category=SuggestionCategory.REGULATORY,
            rationale="Ensure regulatory evidence package completeness",
            priority=1,
            related_metrics=["endpoint_completion"],
            agents_needed=["data", "protocol"],
        ),
        FollowUpSuggestion(
            question="What narrative support is needed for the CER?",
            category=SuggestionCategory.REGULATORY,
            rationale="Plan clinical evaluation report content",
            priority=2,
            related_metrics=["cer_requirements"],
            agents_needed=["data", "literature", "registry"],
        ),
    ],
    "compliance": [
        FollowUpSuggestion(
            question="Which sites have the highest protocol deviation rates?",
            category=SuggestionCategory.DEEP_DIVE,
            rationale="Target site-specific interventions",
            priority=1,
            related_metrics=["deviation_rate", "site_compliance"],
            agents_needed=["data"],
        ),
        FollowUpSuggestion(
            question="Are visit timing deviations affecting data quality?",
            category=SuggestionCategory.RISK_ASSESSMENT,
            rationale="Assess impact of non-compliance",
            priority=2,
            related_metrics=["visit_timing", "data_quality"],
            agents_needed=["data"],
        ),
    ],
    "risk": [
        FollowUpSuggestion(
            question="Which patients are at highest risk for revision?",
            category=SuggestionCategory.RISK_ASSESSMENT,
            rationale="Enable proactive monitoring",
            priority=1,
            related_metrics=["risk_score", "hazard_ratio"],
            agents_needed=["data", "literature"],
        ),
        FollowUpSuggestion(
            question="How do our risk factors compare to published hazard ratios?",
            category=SuggestionCategory.COMPARISON,
            rationale="Validate risk model against evidence",
            priority=2,
            related_metrics=["hazard_ratio", "risk_factors"],
            agents_needed=["data", "literature"],
        ),
        FollowUpSuggestion(
            question="Is there a correlation between BMI and revision risk in our cohort?",
            category=SuggestionCategory.RISK_ASSESSMENT,
            rationale="Identify modifiable risk factors",
            priority=2,
            related_metrics=["bmi", "revision_rate"],
            agents_needed=["data"],
        ),
        FollowUpSuggestion(
            question="How does cup positioning affect dislocation risk?",
            category=SuggestionCategory.CLINICAL_DETAIL,
            rationale="Surgical technique optimization",
            priority=2,
            related_metrics=["cup_inclination", "cup_anteversion", "dislocation_rate"],
            agents_needed=["data", "literature"],
        ),
    ],
    "competitive": [
        FollowUpSuggestion(
            question="How does our revision rate compare to competitor products?",
            category=SuggestionCategory.STRATEGIC,
            rationale="Competitive positioning intelligence",
            priority=1,
            related_metrics=["revision_rate", "competitor_data"],
            agents_needed=["registry", "literature"],
        ),
        FollowUpSuggestion(
            question="What are the key differentiators in published outcomes?",
            category=SuggestionCategory.STRATEGIC,
            rationale="Identify messaging opportunities",
            priority=2,
            related_metrics=["survival_rate", "functional_outcomes"],
            agents_needed=["literature"],
        ),
    ],
}

# Metric-triggered suggestions
METRIC_SUGGESTIONS = {
    "revision_rate": [
        FollowUpSuggestion(
            question="What are the primary reasons for revisions in our study?",
            category=SuggestionCategory.DEEP_DIVE,
            rationale="Understand failure modes",
            priority=1,
            related_metrics=["revision_reasons"],
            agents_needed=["data"],
        ),
        FollowUpSuggestion(
            question="How does our revision rate trend over time?",
            category=SuggestionCategory.TREND_ANALYSIS,
            rationale="Detect improving or worsening signal",
            priority=2,
            related_metrics=["revision_rate"],
            agents_needed=["data"],
        ),
    ],
    "infection_rate": [
        FollowUpSuggestion(
            question="Are infections early or late onset, and what organisms are involved?",
            category=SuggestionCategory.CLINICAL_DETAIL,
            rationale="Guide prevention strategies",
            priority=1,
            related_metrics=["infection_timing", "organisms"],
            agents_needed=["data"],
        ),
    ],
    "dislocation_rate": [
        FollowUpSuggestion(
            question="What cup positions are associated with dislocations?",
            category=SuggestionCategory.RISK_ASSESSMENT,
            rationale="Identify surgical technique factors",
            priority=1,
            related_metrics=["cup_angle", "cup_position"],
            agents_needed=["data"],
        ),
    ],
    "hhs_scores": [
        FollowUpSuggestion(
            question="What is the HHS improvement trajectory from baseline to 2 years?",
            category=SuggestionCategory.TREND_ANALYSIS,
            rationale="Visualize functional recovery pattern",
            priority=1,
            related_metrics=["hhs_baseline", "hhs_2yr"],
            agents_needed=["data"],
        ),
    ],
    "survival_rate": [
        FollowUpSuggestion(
            question="Can you generate a Kaplan-Meier survival curve for our data?",
            category=SuggestionCategory.CLINICAL_DETAIL,
            rationale="Visualize implant survivorship",
            priority=1,
            related_metrics=["survival_data"],
            agents_needed=["data"],
        ),
    ],
}

# Query pattern suggestions
QUERY_PATTERN_SUGGESTIONS = {
    "compare": [
        FollowUpSuggestion(
            question="Which registry is most similar to our study population?",
            category=SuggestionCategory.COMPARISON,
            rationale="Identify most relevant benchmark",
            priority=1,
            related_metrics=["demographics", "indication"],
            agents_needed=["data", "registry"],
        ),
    ],
    "trend": [
        FollowUpSuggestion(
            question="Is the trend statistically significant?",
            category=SuggestionCategory.TREND_ANALYSIS,
            rationale="Validate observed pattern",
            priority=1,
            related_metrics=["trend_analysis"],
            agents_needed=["data"],
        ),
    ],
    "threshold": [
        FollowUpSuggestion(
            question="What interventions could reduce this metric?",
            category=SuggestionCategory.STRATEGIC,
            rationale="Actionable improvement planning",
            priority=1,
            related_metrics=["interventions"],
            agents_needed=["literature"],
        ),
    ],
}


class FollowUpSuggestionService:
    """
    Service for generating intelligent follow-up suggestions.

    Uses context from:
    - Current topic/page
    - Conversation history
    - Mentioned metrics
    - Query patterns
    """

    def __init__(self):
        """Initialize follow-up suggestion service."""
        self._llm_service = None

    def _get_llm_service(self):
        """Lazy load LLM service."""
        if self._llm_service is None:
            from app.services.llm_service import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    def generate_suggestions(
        self,
        topic: str = "dashboard",
        mentioned_metrics: List[str] = None,
        query_patterns: List[str] = None,
        conversation_context: Dict[str, Any] = None,
        exclude_asked: List[str] = None,
        max_suggestions: int = 4,
    ) -> List[FollowUpSuggestion]:
        """
        Generate follow-up suggestions based on context.

        Args:
            topic: Current topic/page context
            mentioned_metrics: Metrics mentioned in conversation
            query_patterns: Detected query patterns
            conversation_context: Extracted conversation context
            exclude_asked: Questions already asked (to avoid repetition)
            max_suggestions: Maximum suggestions to return

        Returns:
            List of prioritized follow-up suggestions
        """
        suggestions = []
        exclude_asked = exclude_asked or []
        mentioned_metrics = mentioned_metrics or []
        query_patterns = query_patterns or []

        # Get topic-based suggestions
        topic_key = topic.lower()
        if topic_key in TOPIC_SUGGESTIONS:
            suggestions.extend(TOPIC_SUGGESTIONS[topic_key])

        # Get metric-triggered suggestions
        for metric in mentioned_metrics:
            metric_key = metric.lower()
            if metric_key in METRIC_SUGGESTIONS:
                suggestions.extend(METRIC_SUGGESTIONS[metric_key])

        # Get query pattern suggestions
        for pattern in query_patterns:
            pattern_key = pattern.lower()
            if pattern_key in QUERY_PATTERN_SUGGESTIONS:
                suggestions.extend(QUERY_PATTERN_SUGGESTIONS[pattern_key])

        # Add context-aware suggestions
        if conversation_context:
            context_suggestions = self._generate_context_suggestions(conversation_context)
            suggestions.extend(context_suggestions)

        # Filter out already asked questions
        filtered = []
        for s in suggestions:
            q_lower = s.question.lower()
            if not any(q_lower in asked.lower() or asked.lower() in q_lower for asked in exclude_asked):
                filtered.append(s)

        # Remove duplicates by question
        seen = set()
        unique = []
        for s in filtered:
            if s.question not in seen:
                seen.add(s.question)
                unique.append(s)

        # Sort by priority
        unique.sort(key=lambda x: x.priority)

        return unique[:max_suggestions]

    def _generate_context_suggestions(
        self,
        context: Dict[str, Any]
    ) -> List[FollowUpSuggestion]:
        """Generate suggestions based on conversation context."""
        suggestions = []

        # If specific patients mentioned, suggest patient-specific analysis
        patient_ids = context.get("patient_ids", [])
        if patient_ids:
            suggestions.append(FollowUpSuggestion(
                question=f"What is the detailed outcome profile for patient {patient_ids[0]}?",
                category=SuggestionCategory.CLINICAL_DETAIL,
                rationale="Drill down on specific case",
                priority=2,
                related_metrics=["patient_outcomes"],
                agents_needed=["data"],
            ))

        # If time periods mentioned, suggest trend analysis
        time_periods = context.get("time_periods", [])
        if time_periods:
            suggestions.append(FollowUpSuggestion(
                question="How have outcomes evolved across different time periods?",
                category=SuggestionCategory.TREND_ANALYSIS,
                rationale="Temporal pattern analysis",
                priority=2,
                related_metrics=["outcomes", "time"],
                agents_needed=["data"],
            ))

        # If active comparisons, suggest deeper comparison
        comparisons = context.get("active_comparisons", [])
        if comparisons:
            suggestions.append(FollowUpSuggestion(
                question="What factors explain the differences observed in the comparison?",
                category=SuggestionCategory.DEEP_DIVE,
                rationale="Understand comparison drivers",
                priority=1,
                related_metrics=["comparison_factors"],
                agents_needed=["data", "literature"],
            ))

        # If unresolved questions, prioritize those
        unresolved = context.get("unresolved_questions", [])
        for q in unresolved[:2]:
            suggestions.append(FollowUpSuggestion(
                question=q,
                category=SuggestionCategory.DEEP_DIVE,
                rationale="Follow up on previous question",
                priority=1,
                related_metrics=[],
                agents_needed=["data", "literature", "registry"],
            ))

        return suggestions

    async def generate_dynamic_suggestions(
        self,
        user_query: str,
        response_content: str,
        topic: str = "dashboard",
    ) -> List[str]:
        """
        Use LLM to generate dynamic follow-up suggestions.

        Args:
            user_query: The user's original query
            response_content: The assistant's response
            topic: Current topic context

        Returns:
            List of suggested follow-up questions
        """
        prompt = f"""Based on this clinical intelligence conversation, suggest 3-4 relevant follow-up questions the user might want to ask.

User Query: {user_query}

Response Summary: {response_content[:500]}...

Current Topic: {topic}

Generate follow-up questions that:
1. Dig deeper into the topic
2. Compare to benchmarks or other data
3. Identify actionable insights
4. Explore related clinical aspects

Return ONLY a JSON array of strings (questions), no other text:
["Question 1?", "Question 2?", "Question 3?"]"""

        try:
            llm = self._get_llm_service()
            result = await llm.generate_json(
                prompt=prompt,
                model="gemini-3-pro-preview",
                temperature=0.5,
                max_tokens=500,
            )

            if isinstance(result, list):
                return result[:4]
            return []

        except Exception as e:
            logger.warning(f"Failed to generate dynamic suggestions: {e}")
            return []

    def get_proactive_suggestions(self, page_context: str = "dashboard") -> List[str]:
        """
        Get proactive "What would you like to know?" suggestions for a page.

        Args:
            page_context: Current page/view context

        Returns:
            List of suggested starting questions
        """
        page_suggestions = {
            "dashboard": [
                "How is our study performing compared to registry benchmarks?",
                "Are there any safety signals I should be aware of?",
                "What is the current enrollment status and data completeness?",
                "Which metrics are approaching threshold levels?",
            ],
            "safety": [
                "What are our current adverse event rates?",
                "How do our complication rates compare to published literature?",
                "Are there any trending safety signals?",
                "Which patients experienced serious adverse events?",
            ],
            "readiness": [
                "What is our current regulatory readiness status?",
                "What data gaps exist for CER submission?",
                "Are primary and secondary endpoints adequately captured?",
                "What follow-up compliance rate do we have?",
            ],
            "risk": [
                "Which patients are at highest risk for revision?",
                "What risk factors are most predictive of poor outcomes?",
                "How do our risk factors compare to literature hazard ratios?",
                "Can you show me the risk stratification of our population?",
            ],
            "competitive": [
                "How do we compare to competitor products in registry data?",
                "What are our key competitive advantages based on outcomes?",
                "Generate a battle card for our top competitor comparison",
                "What claims can we support with our data?",
            ],
        }

        return page_suggestions.get(page_context.lower(), page_suggestions["dashboard"])


# Singleton instance
_followup_service: Optional[FollowUpSuggestionService] = None


def get_followup_service() -> FollowUpSuggestionService:
    """Get singleton follow-up suggestion service instance."""
    global _followup_service
    if _followup_service is None:
        _followup_service = FollowUpSuggestionService()
    return _followup_service
