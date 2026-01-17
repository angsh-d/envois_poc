"""
Reasoning Agent for Clinical Intelligence Platform.

Implements autonomous investigation capabilities through:
- Goal-driven planning
- Hypothesis generation and testing
- Multi-step reasoning with reflection
- Self-correction and validation
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType,
    ConfidenceLevel, UncertaintyInfo
)
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class InvestigationStep(str, Enum):
    """Steps in autonomous investigation."""
    QUESTION_ANALYSIS = "question_analysis"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    DATA_GATHERING = "data_gathering"
    EVIDENCE_EVALUATION = "evidence_evaluation"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    RECOMMENDATION = "recommendation"


class HypothesisStatus(str, Enum):
    """Status of a hypothesis."""
    PROPOSED = "proposed"
    INVESTIGATING = "investigating"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


@dataclass
class Hypothesis:
    """A hypothesis to investigate."""
    id: str
    statement: str
    rationale: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    refuting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    investigation_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "statement": self.statement,
            "rationale": self.rationale,
            "status": self.status.value,
            "supporting_evidence": self.supporting_evidence,
            "refuting_evidence": self.refuting_evidence,
            "confidence": self.confidence,
            "investigation_steps": self.investigation_steps,
        }


@dataclass
class InvestigationPlan:
    """Plan for autonomous investigation."""
    goal: str
    hypotheses: List[Hypothesis] = field(default_factory=list)
    data_needs: List[str] = field(default_factory=list)
    agents_to_query: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    findings: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "goal": self.goal,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "data_needs": self.data_needs,
            "agents_to_query": self.agents_to_query,
            "steps": self.steps,
            "current_step": self.current_step,
            "findings": self.findings,
            "confidence": self.confidence,
        }


@dataclass
class ReasoningTrace:
    """Trace of reasoning steps for explainability."""
    step: InvestigationStep
    input_data: Dict[str, Any]
    reasoning: str
    output: Dict[str, Any]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step": self.step.value,
            "input_data": self.input_data,
            "reasoning": self.reasoning,
            "output": self.output,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class ReasoningAgent(BaseAgent):
    """
    Agent for autonomous investigation and complex reasoning.

    Capabilities:
    - Goal-driven investigation planning
    - Hypothesis generation and testing
    - Multi-step reasoning with chain-of-thought
    - Self-validation and confidence assessment
    - Evidence synthesis with provenance
    """

    agent_type = AgentType.SYNTHESIS  # Reuse synthesis type for now

    def __init__(self, **kwargs):
        """Initialize reasoning agent."""
        super().__init__(**kwargs)
        self._reasoning_trace: List[ReasoningTrace] = []
        self._max_reasoning_steps = 10
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Register an agent for data gathering."""
        self._agents[agent_type] = agent

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute autonomous investigation.

        Args:
            context: Execution context with question and parameters

        Returns:
            AgentResult with findings, reasoning trace, and recommendations
        """
        self._reasoning_trace = []

        question = context.parameters.get("question", "")
        if not question:
            return AgentResult.insufficient_data(
                self.agent_type,
                "No question provided for investigation",
                ["question parameter required"]
            )

        try:
            # Step 1: Analyze question and create investigation plan
            plan = await self._analyze_question(question, context)

            # Step 2: Generate hypotheses
            await self._generate_hypotheses(plan, context)

            # Step 3: Gather data for each hypothesis
            await self._gather_evidence(plan, context)

            # Step 4: Evaluate evidence and update hypotheses
            await self._evaluate_evidence(plan)

            # Step 5: Synthesize findings
            synthesis = await self._synthesize_findings(plan, question)

            # Step 6: Validate conclusions
            validation = await self._validate_conclusions(synthesis, plan)

            # Step 7: Generate recommendations
            recommendations = await self._generate_recommendations(plan, synthesis)

            # Build result
            result = AgentResult(
                agent_type=self.agent_type,
                success=True,
                data={
                    "question": question,
                    "investigation_plan": plan.to_dict(),
                    "synthesis": synthesis,
                    "validation": validation,
                    "recommendations": recommendations,
                    "reasoning_trace": [t.to_dict() for t in self._reasoning_trace],
                },
                narrative=synthesis.get("summary", ""),
                confidence=plan.confidence,
                reasoning=self._build_reasoning_explanation(),
            )

            # Add sources from investigation
            for finding in plan.findings:
                if finding.get("source"):
                    result.add_source(
                        SourceType.LLM_INFERENCE,
                        finding["source"],
                        confidence=finding.get("confidence", 0.5),
                        details=finding
                    )

            result.set_uncertainty(
                data_gaps=synthesis.get("data_gaps", []),
                limitations=synthesis.get("limitations", []),
                reasoning=self._build_reasoning_explanation(),
            )

            return result

        except Exception as e:
            logger.exception(f"Reasoning agent failed: {e}")
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                data={"reasoning_trace": [t.to_dict() for t in self._reasoning_trace]},
            )

    async def _analyze_question(
        self,
        question: str,
        context: AgentContext
    ) -> InvestigationPlan:
        """Analyze question and create investigation plan."""
        prompt = f"""Analyze this clinical research question and create an investigation plan.

Question: {question}

Study Context: {context.protocol_id} - DELTA Revision Cup Study

Available Data Sources:
- Study clinical data (patient demographics, outcomes, adverse events)
- Registry benchmarks (AOANJRR, NJR, SHAR, AJRR, CJRR)
- Published literature (meta-analyses, clinical studies)
- Protocol requirements

Task: Create a structured investigation plan.

Return a JSON object with:
{{
    "goal": "Clear statement of investigation goal",
    "question_type": "safety|efficacy|comparison|trend|risk|regulatory",
    "complexity": "simple|moderate|complex",
    "data_needs": ["list of specific data needed"],
    "agents_to_query": ["data", "registry", "literature"],
    "investigation_steps": [
        {{"step": 1, "action": "what to do", "purpose": "why"}}
    ],
    "potential_hypotheses": ["hypothesis 1", "hypothesis 2"]
}}"""

        response = await self.call_llm_json(prompt, temperature=0.2)

        plan = InvestigationPlan(
            goal=response.get("goal", question),
            data_needs=response.get("data_needs", []),
            agents_to_query=response.get("agents_to_query", ["data"]),
            steps=response.get("investigation_steps", []),
        )

        # Log reasoning trace
        self._reasoning_trace.append(ReasoningTrace(
            step=InvestigationStep.QUESTION_ANALYSIS,
            input_data={"question": question},
            reasoning=f"Analyzed question to determine investigation approach",
            output=response,
            confidence=0.8,
        ))

        return plan

    async def _generate_hypotheses(
        self,
        plan: InvestigationPlan,
        context: AgentContext
    ):
        """Generate testable hypotheses from investigation plan."""
        prompt = f"""Generate specific, testable hypotheses for this clinical investigation.

Investigation Goal: {plan.goal}

Data Available:
{json.dumps(plan.data_needs, indent=2)}

Generate 2-3 hypotheses that:
1. Are specific and testable with available data
2. Address the core question
3. Consider alternative explanations

Return a JSON array:
[
    {{
        "id": "H1",
        "statement": "Specific hypothesis statement",
        "rationale": "Why this hypothesis makes sense",
        "test_approach": "How to test with available data",
        "supporting_data_needed": ["data1", "data2"]
    }}
]"""

        response = await self.call_llm_json(prompt, temperature=0.3)

        if isinstance(response, list):
            for h_data in response[:3]:  # Limit to 3 hypotheses
                hypothesis = Hypothesis(
                    id=h_data.get("id", f"H{len(plan.hypotheses)+1}"),
                    statement=h_data.get("statement", ""),
                    rationale=h_data.get("rationale", ""),
                    investigation_steps=h_data.get("supporting_data_needed", []),
                )
                plan.hypotheses.append(hypothesis)

        self._reasoning_trace.append(ReasoningTrace(
            step=InvestigationStep.HYPOTHESIS_GENERATION,
            input_data={"goal": plan.goal},
            reasoning=f"Generated {len(plan.hypotheses)} testable hypotheses",
            output={"hypotheses": [h.to_dict() for h in plan.hypotheses]},
            confidence=0.7,
        ))

    async def _gather_evidence(
        self,
        plan: InvestigationPlan,
        context: AgentContext
    ):
        """Gather evidence by querying relevant agents."""
        for agent_type in plan.agents_to_query:
            if agent_type in self._agents:
                try:
                    agent = self._agents[agent_type]
                    agent_context = AgentContext(
                        request_id=f"{context.request_id}-{agent_type}",
                        protocol_id=context.protocol_id,
                        parameters=context.parameters.copy(),
                    )

                    result = await agent.run(agent_context)

                    if result.success:
                        plan.findings.append({
                            "source": agent_type,
                            "data": result.data,
                            "confidence": result.confidence,
                            "narrative": result.narrative,
                        })

                except Exception as e:
                    logger.warning(f"Failed to gather evidence from {agent_type}: {e}")

        # Also gather from shared context
        if context.shared_data:
            for source, data in context.shared_data.items():
                plan.findings.append({
                    "source": f"shared_{source}",
                    "data": data,
                    "confidence": 0.8,
                })

        self._reasoning_trace.append(ReasoningTrace(
            step=InvestigationStep.DATA_GATHERING,
            input_data={"agents_queried": plan.agents_to_query},
            reasoning=f"Gathered evidence from {len(plan.findings)} sources",
            output={"n_findings": len(plan.findings)},
            confidence=0.8 if plan.findings else 0.3,
        ))

    async def _evaluate_evidence(self, plan: InvestigationPlan):
        """Evaluate gathered evidence against hypotheses."""
        for hypothesis in plan.hypotheses:
            hypothesis.status = HypothesisStatus.INVESTIGATING

            # Build evidence summary for LLM evaluation (safely truncate)
            evidence_json = json.dumps(plan.findings, default=str)
            if len(evidence_json) > 3000:
                # Truncate findings list rather than string to preserve valid JSON
                truncated_findings = plan.findings[:min(5, len(plan.findings))]
                evidence_summary = json.dumps(truncated_findings, default=str)
                if len(evidence_summary) > 3000:
                    evidence_summary = evidence_summary[:2997] + "..."
            else:
                evidence_summary = evidence_json

            prompt = f"""Evaluate the evidence for this hypothesis:

Hypothesis: {hypothesis.statement}
Rationale: {hypothesis.rationale}

Available Evidence:
{evidence_summary}

Evaluate whether the evidence supports, refutes, or is inconclusive for this hypothesis.

Return a JSON object:
{{
    "status": "supported|refuted|inconclusive",
    "confidence": 0.0-1.0,
    "supporting_points": ["evidence that supports"],
    "refuting_points": ["evidence that refutes"],
    "key_findings": ["main findings relevant to hypothesis"],
    "reasoning": "Explanation of evaluation"
}}"""

            response = await self.call_llm_json(prompt, temperature=0.1)

            status_map = {
                "supported": HypothesisStatus.SUPPORTED,
                "refuted": HypothesisStatus.REFUTED,
                "inconclusive": HypothesisStatus.INCONCLUSIVE,
            }
            hypothesis.status = status_map.get(
                response.get("status", "inconclusive"),
                HypothesisStatus.INCONCLUSIVE
            )
            hypothesis.confidence = response.get("confidence", 0.5)
            hypothesis.supporting_evidence = response.get("supporting_points", [])
            hypothesis.refuting_evidence = response.get("refuting_points", [])

        self._reasoning_trace.append(ReasoningTrace(
            step=InvestigationStep.EVIDENCE_EVALUATION,
            input_data={"n_hypotheses": len(plan.hypotheses), "n_findings": len(plan.findings)},
            reasoning="Evaluated evidence against each hypothesis",
            output={"hypotheses": [h.to_dict() for h in plan.hypotheses]},
            confidence=sum(h.confidence for h in plan.hypotheses) / max(len(plan.hypotheses), 1),
        ))

    async def _synthesize_findings(
        self,
        plan: InvestigationPlan,
        question: str
    ) -> Dict[str, Any]:
        """Synthesize all findings into coherent conclusions."""
        # Prepare synthesis input
        hypotheses_summary = "\n".join([
            f"- {h.statement}: {h.status.value} (confidence: {h.confidence:.2f})"
            for h in plan.hypotheses
        ])

        # Safely truncate findings for synthesis
        findings_json = json.dumps(plan.findings, default=str)
        if len(findings_json) > 4000:
            truncated = plan.findings[:min(8, len(plan.findings))]
            findings_summary = json.dumps(truncated, default=str)
        else:
            findings_summary = findings_json

        prompt = f"""Synthesize the investigation findings to answer the original question.

Original Question: {question}

Investigation Goal: {plan.goal}

Hypotheses Evaluated:
{hypotheses_summary}

Evidence Gathered:
{findings_summary}

Create a comprehensive synthesis that:
1. Directly answers the original question
2. Integrates findings from all sources
3. Acknowledges uncertainty and limitations
4. Provides specific data citations

Return a JSON object:
{{
    "summary": "Direct answer to the question (2-3 sentences)",
    "key_findings": [
        {{"finding": "specific finding", "source": "data source", "confidence": 0.0-1.0}}
    ],
    "data_gaps": ["missing data that would improve analysis"],
    "limitations": ["limitations of current analysis"],
    "overall_confidence": 0.0-1.0,
    "confidence_explanation": "Why this confidence level"
}}"""

        synthesis = await self.call_llm_json(prompt, temperature=0.2)

        plan.confidence = synthesis.get("overall_confidence", 0.5)

        self._reasoning_trace.append(ReasoningTrace(
            step=InvestigationStep.SYNTHESIS,
            input_data={"n_hypotheses": len(plan.hypotheses), "n_findings": len(plan.findings)},
            reasoning="Synthesized findings into conclusions",
            output=synthesis,
            confidence=plan.confidence,
        ))

        return synthesis

    async def _validate_conclusions(
        self,
        synthesis: Dict[str, Any],
        plan: InvestigationPlan
    ) -> Dict[str, Any]:
        """Validate conclusions through self-reflection."""
        prompt = f"""Critically evaluate these conclusions for a clinical research question.

Conclusions:
{json.dumps(synthesis, indent=2)}

Evidence Base:
- Number of sources: {len(plan.findings)}
- Hypotheses supported: {sum(1 for h in plan.hypotheses if h.status == HypothesisStatus.SUPPORTED)}
- Hypotheses refuted: {sum(1 for h in plan.hypotheses if h.status == HypothesisStatus.REFUTED)}

Validate by checking:
1. Are conclusions supported by evidence?
2. Are there logical gaps or assumptions?
3. Could alternative interpretations be valid?
4. Are confidence levels appropriate?

Return a JSON object:
{{
    "is_valid": true|false,
    "validation_score": 0.0-1.0,
    "issues_found": ["any issues with reasoning"],
    "alternative_interpretations": ["other possible explanations"],
    "confidence_adjustment": "increase|decrease|maintain",
    "reasoning": "explanation of validation"
}}"""

        validation = await self.call_llm_json(prompt, temperature=0.1)

        # Adjust confidence based on validation
        if validation.get("confidence_adjustment") == "decrease":
            plan.confidence *= 0.8
        elif validation.get("confidence_adjustment") == "increase":
            plan.confidence = min(1.0, plan.confidence * 1.1)

        self._reasoning_trace.append(ReasoningTrace(
            step=InvestigationStep.VALIDATION,
            input_data={"synthesis": synthesis},
            reasoning="Validated conclusions through self-reflection",
            output=validation,
            confidence=validation.get("validation_score", 0.5),
        ))

        return validation

    async def _generate_recommendations(
        self,
        plan: InvestigationPlan,
        synthesis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on findings."""
        prompt = f"""Based on the investigation findings, generate actionable recommendations.

Findings:
{json.dumps(synthesis.get('key_findings', []), indent=2)}

Data Gaps:
{json.dumps(synthesis.get('data_gaps', []), indent=2)}

Limitations:
{json.dumps(synthesis.get('limitations', []), indent=2)}

Generate 3-5 specific, actionable recommendations that:
1. Address the original question
2. Suggest follow-up investigations
3. Highlight areas needing attention

Return a JSON array:
[
    {{
        "recommendation": "Specific action or next step",
        "priority": "high|medium|low",
        "rationale": "Why this is recommended",
        "effort": "high|medium|low",
        "expected_impact": "Description of expected benefit"
    }}
]"""

        recommendations = await self.call_llm_json(prompt, temperature=0.3)

        if not isinstance(recommendations, list):
            recommendations = []

        self._reasoning_trace.append(ReasoningTrace(
            step=InvestigationStep.RECOMMENDATION,
            input_data={"synthesis": synthesis},
            reasoning="Generated actionable recommendations",
            output={"n_recommendations": len(recommendations)},
            confidence=0.7,
        ))

        return recommendations[:5]  # Limit to 5 recommendations

    def _build_reasoning_explanation(self) -> str:
        """Build human-readable explanation of reasoning process."""
        if not self._reasoning_trace:
            return "No reasoning trace available"

        parts = ["Investigation Process:"]
        for i, trace in enumerate(self._reasoning_trace, 1):
            parts.append(f"{i}. {trace.step.value}: {trace.reasoning}")

        return "\n".join(parts)


# Factory function
def get_reasoning_agent(**kwargs) -> ReasoningAgent:
    """Create a reasoning agent instance."""
    return ReasoningAgent(**kwargs)
