"""
Synthesis Agent for Clinical Intelligence Platform.

Responsible for combining outputs from multiple agents into coherent narratives.
"""
import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType, Source,
    ConfidenceLevel, CONFIDENCE_THRESHOLDS, UncertaintyInfo
)

logger = logging.getLogger(__name__)


class SynthesisAgent(BaseAgent):
    """
    Agent for multi-agent output synthesis.

    Capabilities:
    - Combine outputs from multiple specialized agents
    - Generate coherent narratives with full provenance
    - Resolve conflicting information across sources
    - Create executive summaries for different use cases
    """

    agent_type = AgentType.SYNTHESIS

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute synthesis of agent outputs.

        Args:
            context: Execution context with shared_data from other agents

        Returns:
            AgentResult with synthesized output
        """
        synthesis_type = context.parameters.get("synthesis_type", "summary")

        # Check if we have sufficient data for synthesis
        insufficient_result = self._check_data_sufficiency(context.shared_data, synthesis_type)
        if insufficient_result:
            return insufficient_result

        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        if synthesis_type == "summary":
            result.data = await self._synthesize_summary(context)
        elif synthesis_type == "uc1_readiness":
            result.data = await self._synthesize_readiness(context)
        elif synthesis_type == "uc2_safety":
            result.data = await self._synthesize_safety(context)
        elif synthesis_type == "uc3_deviations":
            result.data = await self._synthesize_deviations(context)
        elif synthesis_type == "uc4_risk":
            result.data = await self._synthesize_risk(context)
        elif synthesis_type == "uc5_dashboard":
            result.data = await self._synthesize_dashboard(context)
        else:
            result.success = False
            result.error = f"Unknown synthesis_type: {synthesis_type}"
            return result

        # Collect sources from all agent outputs
        result.sources = self._collect_sources(context.shared_data)

        # Calculate overall confidence
        result.confidence = self._calculate_confidence(context.shared_data)

        # Check if confidence meets threshold for this synthesis type
        confidence_threshold = self._get_confidence_threshold(synthesis_type)
        if result.confidence < confidence_threshold:
            result.data["confidence_warning"] = (
                f"Confidence ({result.confidence:.2f}) below threshold ({confidence_threshold:.2f}) "
                f"for {synthesis_type}. Findings should be interpreted with caution."
            )
            logger.warning(
                f"Low confidence synthesis: {result.confidence:.2f} < {confidence_threshold:.2f} "
                f"for {synthesis_type}"
            )

        # Set uncertainty information
        result.set_uncertainty(
            data_gaps=self._identify_data_gaps(context.shared_data, synthesis_type),
            limitations=self._identify_limitations(context.shared_data),
            reasoning=f"Synthesis based on {len(context.shared_data)} agent outputs with "
                      f"average confidence {result.confidence:.2f}."
        )

        # Add explicit reasoning to the result
        result.reasoning = self._generate_reasoning(context.shared_data, synthesis_type, result.confidence)

        # Generate narrative
        result.narrative = result.data.get("narrative", "")

        return result

    def _check_data_sufficiency(
        self,
        shared_data: Dict,
        synthesis_type: str
    ) -> Optional[AgentResult]:
        """
        Check if we have sufficient data to perform synthesis.

        Returns an AgentResult with insufficient_data if data is lacking,
        otherwise returns None to proceed with synthesis.
        """
        if not shared_data:
            return AgentResult.insufficient_data(
                agent_type=self.agent_type,
                reason="No agent data available for synthesis",
                data_gaps=["All agent outputs missing"],
                available_data={}
            )

        # Check for required agents based on synthesis type
        required_agents = self._get_required_agents(synthesis_type)
        missing_agents = []
        failed_agents = []

        for agent_type in required_agents:
            if agent_type not in shared_data:
                missing_agents.append(agent_type)
            elif not shared_data[agent_type].get("success", False):
                failed_agents.append(agent_type)

        # All required agents missing
        if len(missing_agents) == len(required_agents):
            return AgentResult.insufficient_data(
                agent_type=self.agent_type,
                reason=f"All required agents ({', '.join(required_agents)}) missing for {synthesis_type}",
                data_gaps=[f"Missing {a} agent output" for a in missing_agents],
                available_data={"available_agents": list(shared_data.keys())}
            )

        # Check if any successful agent has actual data
        # Handle both formats:
        # - Agent result format: {"success": True, "data": {...}}
        # - Service result format: {"success": True, "enrollment": {...}, ...}
        has_valid_data = False
        for agent_type, agent_data in shared_data.items():
            if agent_data.get("success"):
                # Check for nested data key (agent format)
                if agent_data.get("data"):
                    data = agent_data["data"]
                    if not data.get("error") and not data.get("insufficient_data"):
                        has_valid_data = True
                        break
                # Check for flat structure (service format) - has success but no nested data key
                elif not agent_data.get("error") and not agent_data.get("insufficient_data"):
                    # Has meaningful data keys beyond just success
                    data_keys = [k for k in agent_data.keys() if k not in ("success", "generated_at", "assessment_date")]
                    if data_keys:
                        has_valid_data = True
                        break

        if not has_valid_data:
            return AgentResult.insufficient_data(
                agent_type=self.agent_type,
                reason="All available agent outputs contain errors or insufficient data",
                data_gaps=["No valid data from any agent"],
                available_data={"agents_attempted": list(shared_data.keys())}
            )

        return None  # Proceed with synthesis

    def _get_required_agents(self, synthesis_type: str) -> List[str]:
        """Get list of required agent types for a synthesis type."""
        requirements = {
            "summary": [],  # Summary can work with any available data
            "uc1_readiness": ["compliance"],
            "uc2_safety": ["safety"],
            "uc3_deviations": ["compliance"],
            "uc4_risk": ["safety"],
            "uc5_dashboard": ["readiness"],  # Dashboard uses readiness, safety, deviations
        }
        return requirements.get(synthesis_type, [])

    def _get_confidence_threshold(self, synthesis_type: str) -> float:
        """Get confidence threshold for a synthesis type."""
        threshold_mapping = {
            "summary": CONFIDENCE_THRESHOLDS["data_summary"],
            "uc1_readiness": CONFIDENCE_THRESHOLDS["clinical_recommendation"],
            "uc2_safety": CONFIDENCE_THRESHOLDS["safety_signal"],
            "uc3_deviations": CONFIDENCE_THRESHOLDS["data_summary"],
            "uc4_risk": CONFIDENCE_THRESHOLDS["risk_assessment"],
            "uc5_dashboard": CONFIDENCE_THRESHOLDS["data_summary"],
        }
        return threshold_mapping.get(synthesis_type, 0.5)

    def _identify_data_gaps(self, shared_data: Dict, synthesis_type: str) -> List[str]:
        """Identify data gaps in agent outputs."""
        gaps = []

        required_agents = self._get_required_agents(synthesis_type)
        for agent in required_agents:
            if agent not in shared_data:
                gaps.append(f"Missing {agent} agent data")
            elif not shared_data[agent].get("success"):
                gaps.append(f"{agent} agent failed: {shared_data[agent].get('error', 'unknown error')}")

        # Check for specific data gaps
        if synthesis_type == "uc2_safety":
            safety_data = shared_data.get("safety", {}).get("data", {})
            if not safety_data.get("n_patients"):
                gaps.append("No patient count available for safety analysis")
            if not safety_data.get("metrics"):
                gaps.append("No safety metrics calculated")

        if synthesis_type == "uc4_risk":
            safety_data = shared_data.get("safety", {}).get("data", {})
            if not safety_data.get("risk_factors"):
                gaps.append("No risk factors identified")

        return gaps

    def _identify_limitations(self, shared_data: Dict) -> List[str]:
        """Identify limitations in the synthesis."""
        limitations = []

        # Check overall confidence
        avg_confidence = self._calculate_confidence(shared_data)
        if avg_confidence < 0.6:
            limitations.append(f"Low overall confidence ({avg_confidence:.2f})")

        # Check for single-source data
        source_count = sum(len(agent.get("sources", [])) for agent in shared_data.values())
        if source_count < 2:
            limitations.append("Limited to single data source")

        # Check for agent failures
        failed_count = sum(1 for agent in shared_data.values() if not agent.get("success"))
        if failed_count > 0:
            limitations.append(f"{failed_count} agent(s) failed, synthesis may be incomplete")

        return limitations

    def _generate_reasoning(
        self,
        shared_data: Dict,
        synthesis_type: str,
        confidence: float
    ) -> str:
        """Generate explicit reasoning for the synthesis."""
        successful_agents = [
            agent_type for agent_type, data in shared_data.items()
            if data.get("success")
        ]

        source_summary = []
        for agent_type, data in shared_data.items():
            if data.get("success"):
                sources = data.get("sources", [])
                source_types = set(s.get("type", "unknown") for s in sources)
                if source_types:
                    source_summary.append(f"{agent_type}: {', '.join(source_types)}")

        reasoning = (
            f"Synthesis type: {synthesis_type}. "
            f"Based on {len(successful_agents)} successful agent(s): {', '.join(successful_agents)}. "
            f"Overall confidence: {confidence:.2f}. "
        )

        if source_summary:
            reasoning += f"Data sources: {'; '.join(source_summary)}."

        return reasoning

    async def _synthesize_summary(self, context: AgentContext) -> Dict[str, Any]:
        """Synthesize a general summary from all agent outputs."""
        shared = context.shared_data

        summary = {
            "request_id": context.request_id,
            "agents_executed": list(shared.keys()),
            "overall_status": "complete",
            "key_findings": [],
            "data": {},
            "narrative": "",
        }

        # Extract key findings from each agent
        for agent_type, agent_data in shared.items():
            if not agent_data.get("success"):
                continue

            data = agent_data.get("data", {})
            summary["data"][agent_type] = data

            # Extract notable findings
            if agent_type == "safety":
                if data.get("n_signals", 0) > 0:
                    summary["key_findings"].append({
                        "source": "safety",
                        "finding": f"{data['n_signals']} safety signal(s) detected",
                        "priority": "high" if data["n_signals"] > 0 else "normal",
                    })

            elif agent_type == "compliance":
                if data.get("n_deviations", 0) > 0:
                    summary["key_findings"].append({
                        "source": "compliance",
                        "finding": f"{data['n_deviations']} protocol deviation(s) detected",
                        "priority": "medium",
                    })

        # Generate narrative
        summary["narrative"] = await self._generate_summary_narrative(summary)

        return summary

    async def _synthesize_readiness(self, context: AgentContext) -> Dict[str, Any]:
        """Synthesize UC1 Readiness Assessment output."""
        shared = context.shared_data
        patient_id = context.patient_id

        readiness = {
            "patient_id": patient_id,
            "visit_id": context.visit_id,
            "is_ready": True,
            "blocking_issues": [],
            "warnings": [],
            "visit_status": {},
            "assessments_status": {},
            "narrative": "",
        }

        # Check compliance data
        compliance = shared.get("compliance", {}).get("data", {})
        if compliance:
            deviations = compliance.get("deviations", [])
            for dev in deviations:
                if dev.get("affects_evaluability"):
                    readiness["is_ready"] = False
                    readiness["blocking_issues"].append({
                        "type": "deviation",
                        "description": f"Critical deviation at {dev.get('visit_name')}",
                        "details": dev,
                    })
                elif dev.get("classification") == "major":
                    readiness["warnings"].append({
                        "type": "deviation",
                        "description": f"Major deviation at {dev.get('visit_name')}",
                    })

        # Check for missing assessments
        missing = compliance.get("missing_assessments", [])
        for item in missing:
            if item.get("is_primary_endpoint"):
                readiness["is_ready"] = False
                readiness["blocking_issues"].append({
                    "type": "missing_assessment",
                    "description": f"Missing {item['assessment']} at {item['visit_id']}",
                })

        # Check protocol data
        protocol = shared.get("protocol", {}).get("data", {})
        if protocol:
            readiness["visit_status"]["scheduled_visits"] = len(protocol.get("visit_windows", []))

        # Use passed readiness status if available (from readiness_service)
        readiness_status = shared.get("readiness_status", {})
        if readiness_status:
            readiness["is_ready"] = readiness_status.get("is_ready", readiness["is_ready"])
            # Merge blocking issues from service calculation
            service_blocking = readiness_status.get("blocking_issues", [])
            if service_blocking:
                readiness["blocking_issues"] = service_blocking

        # Generate narrative
        readiness["narrative"] = await self._generate_readiness_narrative(readiness)

        return readiness

    async def _synthesize_safety(self, context: AgentContext) -> Dict[str, Any]:
        """Synthesize UC2 Safety Analysis output."""
        shared = context.shared_data

        safety_result = {
            "overall_status": "acceptable",
            "signals": [],
            "metrics": [],
            "registry_comparison": {},
            "literature_context": {},
            "recommendations": [],
            "narrative": "",
        }

        # Get safety agent output
        safety = shared.get("safety", {}).get("data", {})
        if safety:
            safety_result["overall_status"] = safety.get("overall_status", "unknown")
            safety_result["signals"] = safety.get("signals", [])
            safety_result["metrics"] = safety.get("metrics", [])
            safety_result["registry_comparison"] = safety.get("registry_comparison", {})

        # Get literature context
        literature = shared.get("literature", {}).get("data", {})
        if literature:
            safety_result["literature_context"] = {
                "n_publications": literature.get("n_publications", 0),
                "benchmarks": literature.get("aggregate_benchmarks", {}),
            }

        # Generate recommendations
        for signal in safety_result["signals"]:
            safety_result["recommendations"].append({
                "signal": signal.get("metric"),
                "action": self._get_safety_recommendation(signal),
                "priority": "high" if signal.get("threshold_exceeded_by", 0) > 0.02 else "medium",
            })

        # Generate narrative
        safety_result["narrative"] = await self._generate_safety_synthesis_narrative(safety_result)

        return safety_result

    async def _synthesize_deviations(self, context: AgentContext) -> Dict[str, Any]:
        """Synthesize UC3 Deviations Analysis output."""
        shared = context.shared_data
        patient_id = context.patient_id

        deviations_result = {
            "patient_id": patient_id,
            "deviations": [],
            "summary": {},
            "protocol_context": {},
            "impact_analysis": {},
            "narrative": "",
        }

        # Get compliance agent output
        compliance = shared.get("compliance", {}).get("data", {})
        if compliance:
            deviations_result["deviations"] = compliance.get("deviations", [])
            deviations_result["summary"] = compliance.get("deviation_summary", {})
            deviations_result["compliance_rate"] = compliance.get("compliance_rate", 1.0)

        # Get protocol context
        protocol = shared.get("protocol", {}).get("data", {})
        if protocol:
            deviations_result["protocol_context"] = {
                "protocol_id": protocol.get("protocol_id"),
                "deviation_rules": protocol.get("deviation_classification", {}),
            }

        # Analyze impact
        deviations_result["impact_analysis"] = self._analyze_deviation_impact(
            deviations_result["deviations"]
        )

        # Generate narrative
        deviations_result["narrative"] = await self._generate_deviations_narrative(deviations_result)

        return deviations_result

    async def _synthesize_risk(self, context: AgentContext) -> Dict[str, Any]:
        """Synthesize UC4 Risk Prediction output."""
        shared = context.shared_data
        patient_id = context.patient_id

        risk_result = {
            "patient_id": patient_id,
            "risk_score": 0.0,
            "risk_level": "low",
            "risk_factors": [],
            "literature_support": {},
            "recommendations": [],
            "narrative": "",
        }

        # Get safety agent risk analysis
        safety = shared.get("safety", {}).get("data", {})
        if safety:
            risk_result["risk_factors"] = safety.get("risk_factors", [])
            risk_result["risk_level"] = safety.get("risk_level", "low")

        # Get literature risk factor context
        literature = shared.get("literature", {}).get("data", {})
        if literature:
            risk_result["literature_support"] = {
                "risk_factors_from_literature": literature.get("n_risk_factors", 0),
            }

        # Calculate risk score
        risk_result["risk_score"] = self._calculate_risk_score(risk_result["risk_factors"])

        # Generate recommendations based on risk level
        risk_result["recommendations"] = self._generate_risk_recommendations(risk_result)

        # Generate narrative
        risk_result["narrative"] = await self._generate_risk_narrative(risk_result)

        return risk_result

    async def _synthesize_dashboard(self, context: AgentContext) -> Dict[str, Any]:
        """Synthesize UC5 Dashboard output."""
        shared = context.shared_data

        dashboard = {
            "study_overview": {},
            "safety_summary": {},
            "enrollment_status": {},
            "compliance_summary": {},
            "key_metrics": [],
            "alerts": [],
            "narrative": "",
        }

        # Collect from readiness data (passed from dashboard_service)
        readiness = shared.get("readiness", {})
        if readiness:
            enrollment = readiness.get("enrollment", {})
            dashboard["study_overview"] = {
                "enrolled": enrollment.get("enrolled", 0),
                "active": enrollment.get("enrolled", 0) - readiness.get("data_completeness", {}).get("completed", 0),
                "completed": readiness.get("data_completeness", {}).get("completed", 0),
            }
            dashboard["enrollment_status"] = enrollment

        # Collect from safety data
        safety = shared.get("safety", {})
        if safety:
            dashboard["safety_summary"] = {
                "status": safety.get("overall_status", "unknown"),
                "signals": safety.get("n_signals", 0),
            }

        # Collect from deviations data
        deviations = shared.get("deviations", {})
        if deviations:
            dashboard["compliance_summary"] = {
                "deviation_rate": deviations.get("deviation_rate", 0),
                "critical_deviations": deviations.get("by_severity", {}).get("critical", 0),
            }

        # Generate alerts
        dashboard["alerts"] = self._generate_dashboard_alerts(shared)

        # Generate narrative
        dashboard["narrative"] = await self._generate_dashboard_narrative(dashboard)

        return dashboard

    def _collect_sources(self, shared_data: Dict) -> List[Source]:
        """Collect all sources from agent outputs."""
        sources = []
        seen = set()

        for agent_type, agent_data in shared_data.items():
            for source_dict in agent_data.get("sources", []):
                key = (source_dict.get("type"), source_dict.get("reference"))
                if key not in seen:
                    seen.add(key)
                    sources.append(Source(
                        type=SourceType(source_dict.get("type", "study_data")),
                        reference=source_dict.get("reference", ""),
                        confidence=source_dict.get("confidence", 1.0),
                        details=source_dict.get("details"),
                    ))

        return sources

    def _calculate_confidence(self, shared_data: Dict) -> float:
        """Calculate overall confidence from agent outputs."""
        if not shared_data:
            return 0.5

        confidences = []
        for agent_data in shared_data.values():
            if agent_data.get("success"):
                confidences.append(agent_data.get("confidence", 0.9))

        if not confidences:
            return 0.5

        return round(sum(confidences) / len(confidences), 3)

    def _analyze_deviation_impact(self, deviations: List[Dict]) -> Dict[str, Any]:
        """Analyze impact of deviations."""
        if not deviations:
            return {"impact_level": "none", "evaluability_affected": False}

        critical = sum(1 for d in deviations if d.get("classification") == "critical")
        major = sum(1 for d in deviations if d.get("classification") == "major")
        affects_eval = any(d.get("affects_evaluability") for d in deviations)

        if critical > 0:
            impact_level = "high"
        elif major > 0:
            impact_level = "medium"
        else:
            impact_level = "low"

        return {
            "impact_level": impact_level,
            "evaluability_affected": affects_eval,
            "critical_count": critical,
            "major_count": major,
        }

    def _calculate_risk_score(self, risk_factors: List[Dict]) -> float:
        """Calculate composite risk score from risk factors."""
        if not risk_factors:
            return 0.1

        # Use geometric mean of hazard ratios, normalized to 0-1 scale
        combined_hr = 1.0
        for rf in risk_factors:
            combined_hr *= rf.get("hazard_ratio", 1.0)

        # Normalize: HR of 1 = 0.1, HR of 5 = 0.9
        normalized = min(0.9, max(0.1, (combined_hr - 1) / 4 * 0.8 + 0.1))
        return round(normalized, 2)

    def _generate_risk_recommendations(self, risk_result: Dict) -> List[Dict]:
        """Generate recommendations based on risk level."""
        recommendations = []
        risk_level = risk_result.get("risk_level", "low")

        if risk_level == "high":
            recommendations.append({
                "action": "Enhanced post-operative monitoring",
                "rationale": "Multiple elevated risk factors identified",
                "priority": "high",
            })
            recommendations.append({
                "action": "Consider additional imaging at early follow-up",
                "rationale": "Early detection of complications",
                "priority": "medium",
            })
        elif risk_level == "moderate":
            recommendations.append({
                "action": "Standard monitoring with attention to risk factors",
                "rationale": "Moderate risk profile",
                "priority": "medium",
            })

        return recommendations

    def _get_safety_recommendation(self, signal: Dict) -> str:
        """Get recommendation for a safety signal."""
        metric = signal.get("metric", "unknown")
        exceeded_by = signal.get("threshold_exceeded_by", 0)

        if exceeded_by > 0.03:
            return f"Immediate DSMB review for {metric}"
        elif exceeded_by > 0.01:
            return f"Enhanced monitoring for {metric}"
        else:
            return f"Continue monitoring {metric}"

    def _generate_dashboard_alerts(self, shared_data: Dict) -> List[Dict]:
        """Generate dashboard alerts from agent outputs."""
        alerts = []

        # Check safety signals (data passed directly from dashboard_service)
        safety = shared_data.get("safety", {})
        for signal in safety.get("signals", []):
            alerts.append({
                "type": "safety",
                "severity": "high" if signal.get("threshold_exceeded_by", 0) > 0.02 else "medium",
                "message": f"Safety signal: {signal.get('metric')} exceeds threshold",
            })

        # Check deviations
        deviations = shared_data.get("deviations", {})
        critical = deviations.get("by_severity", {}).get("critical", 0)
        if critical > 0:
            alerts.append({
                "type": "compliance",
                "severity": "high",
                "message": f"{critical} critical deviation(s) detected",
            })

        return alerts

    async def _generate_summary_narrative(
        self,
        summary: Dict,
        confidence: float = 0.9,
        sources: List[str] = None
    ) -> str:
        """Generate summary narrative using LLM."""
        sources_str = ", ".join(sources) if sources else "H-34 Study Database"
        prompt = self.load_prompt("synthesis_summary", {
            "agents": str(summary.get("agents_executed", [])),
            "findings": str(summary.get("key_findings", [])),
            "confidence": f"{confidence:.2f}",
            "sources": sources_str,
        })
        return await self.call_llm(prompt, model="gemini-3-pro-preview", temperature=0.3)

    async def _generate_readiness_narrative(self, readiness: Dict) -> str:
        """Generate readiness narrative for study-level regulatory submission readiness."""
        if readiness.get("is_ready"):
            return "Study is ready for regulatory submission with all readiness criteria met."
        else:
            n_blocking = len(readiness.get("blocking_issues", []))
            return f"Study has {n_blocking} blocking issue(s) that must be resolved before regulatory submission."

    async def _generate_safety_synthesis_narrative(self, safety: Dict) -> str:
        """Generate safety synthesis narrative."""
        status = safety.get("overall_status", "unknown")
        n_signals = len(safety.get("signals", []))

        if status == "acceptable":
            return "Safety analysis shows all metrics within acceptable thresholds based on protocol requirements and registry benchmarks."
        else:
            return f"Safety analysis identified {n_signals} signal(s) requiring attention. Status: {status}."

    async def _generate_deviations_narrative(self, deviations: Dict) -> str:
        """Generate deviations narrative."""
        n_dev = len(deviations.get("deviations", []))
        if n_dev == 0:
            return "No protocol deviations detected for this patient."

        summary = deviations.get("summary", {})
        return (
            f"Detected {n_dev} protocol deviation(s): "
            f"{summary.get('minor', 0)} minor, {summary.get('major', 0)} major, "
            f"{summary.get('critical', 0)} critical."
        )

    async def _generate_risk_narrative(self, risk: Dict) -> str:
        """Generate risk narrative."""
        level = risk.get("risk_level", "low")
        n_factors = len(risk.get("risk_factors", []))
        score = risk.get("risk_score", 0)

        return (
            f"Risk assessment: {level.upper()} level (score: {score:.2f}). "
            f"Identified {n_factors} contributing risk factor(s) from literature-derived hazard ratios."
        )

    async def _generate_dashboard_narrative(self, dashboard: Dict) -> str:
        """Generate dashboard narrative."""
        overview = dashboard.get("study_overview", {})
        n_alerts = len(dashboard.get("alerts", []))

        return (
            f"Study status: {overview.get('enrolled', 0)} enrolled, "
            f"{overview.get('active', 0)} active, {overview.get('completed', 0)} completed. "
            f"{n_alerts} alert(s) requiring attention."
        )
