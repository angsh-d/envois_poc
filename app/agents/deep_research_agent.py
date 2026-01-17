"""
Deep Research Agent for Clinical Intelligence Platform.

Generates comprehensive research reports by synthesizing data from
multiple sources including literature, FDA data, and web research.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)

logger = logging.getLogger(__name__)


class DeepResearchAgent(BaseAgent):
    """
    Agent for conducting deep research and generating comprehensive reports.

    Report Types:
    - Competitive Landscape: Analysis of competing products
    - State of the Art: Current clinical/technological landscape
    - Regulatory Precedents: Similar device approvals and requirements
    """

    agent_type = AgentType.DEEP_RESEARCH

    def __init__(self, **kwargs):
        """Initialize deep research agent."""
        super().__init__(**kwargs)

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute deep research.

        Args:
            context: Execution context with research parameters

        Returns:
            AgentResult with research report

        Parameters:
            - report_type: Type of report to generate
                - competitive_landscape
                - state_of_the_art
                - regulatory_precedents
            - product_info: Product information for context
            - data_sources: Available data sources
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        report_type = context.parameters.get("report_type", "competitive_landscape")

        if report_type == "competitive_landscape":
            result.data = await self._generate_competitive_report(context)
        elif report_type == "state_of_the_art":
            result.data = await self._generate_sota_report(context)
        elif report_type == "regulatory_precedents":
            result.data = await self._generate_regulatory_report(context)
        else:
            result.success = False
            result.error = f"Unknown report type: {report_type}"
            return result

        # Add source provenance
        self._add_sources(result, report_type, context)

        return result

    async def _generate_competitive_report(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate competitive landscape report.

        Analyzes competing products, their features, clinical evidence,
        and market positioning.
        """
        product_info = context.parameters.get("product_info", {})
        competitors = context.parameters.get("competitors", [])

        prompt = self.load_prompt("deep_research_competitive", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "competitors": self._format_competitors(competitors),
        })

        try:
            report = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

            return {
                "report_type": "competitive_landscape",
                "status": "completed",
                "generated_at": datetime.utcnow().isoformat(),
                "product_analyzed": product_info.get("product_name"),
                "report": {
                    "executive_summary": report.get("executive_summary", ""),
                    "market_overview": report.get("market_overview", {}),
                    "competitor_profiles": report.get("competitor_profiles", []),
                    "feature_comparison": report.get("feature_comparison", {}),
                    "clinical_evidence_comparison": report.get("clinical_evidence", {}),
                    "positioning_opportunities": report.get("opportunities", []),
                    "competitive_threats": report.get("threats", []),
                    "recommendations": report.get("recommendations", []),
                },
                "estimated_pages": 8,
            }

        except Exception as e:
            logger.error(f"Error generating competitive report: {e}")
            return {
                "report_type": "competitive_landscape",
                "status": "error",
                "error": str(e),
            }

    async def _generate_sota_report(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate State of the Art report.

        Synthesizes current clinical knowledge, best practices,
        and emerging trends.
        """
        product_info = context.parameters.get("product_info", {})
        publications = context.parameters.get("publications", [])
        registries = context.parameters.get("registries", [])

        prompt = self.load_prompt("deep_research_sota", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "publication_count": len(publications),
            "key_publications": self._format_top_publications(publications[:10]),
            "registries": ", ".join([r.get("name", "") for r in registries]),
        })

        try:
            report = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

            return {
                "report_type": "state_of_the_art",
                "status": "completed",
                "generated_at": datetime.utcnow().isoformat(),
                "product_analyzed": product_info.get("product_name"),
                "report": {
                    "executive_summary": report.get("executive_summary", ""),
                    "clinical_outcomes_overview": report.get("clinical_outcomes", {}),
                    "safety_profile": report.get("safety_profile", {}),
                    "design_innovations": report.get("design_innovations", []),
                    "surgical_techniques": report.get("surgical_techniques", {}),
                    "patient_selection": report.get("patient_selection", {}),
                    "outcome_predictors": report.get("outcome_predictors", []),
                    "unmet_needs": report.get("unmet_needs", []),
                    "future_directions": report.get("future_directions", []),
                    "key_references": report.get("key_references", []),
                },
                "estimated_pages": 12,
            }

        except Exception as e:
            logger.error(f"Error generating SOTA report: {e}")
            return {
                "report_type": "state_of_the_art",
                "status": "error",
                "error": str(e),
            }

    async def _generate_regulatory_report(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate regulatory precedents report.

        Analyzes similar device approvals, regulatory pathways,
        and post-market requirements.
        """
        product_info = context.parameters.get("product_info", {})
        fda_data = context.parameters.get("fda_data", {})

        prompt = self.load_prompt("deep_research_regulatory", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "clearances_count": fda_data.get("clearances", {}).get("total_clearances", 0),
            "recent_clearances": self._format_clearances(
                fda_data.get("clearances", {}).get("recent_clearances", [])
            ),
        })

        try:
            report = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

            return {
                "report_type": "regulatory_precedents",
                "status": "completed",
                "generated_at": datetime.utcnow().isoformat(),
                "product_analyzed": product_info.get("product_name"),
                "report": {
                    "executive_summary": report.get("executive_summary", ""),
                    "regulatory_pathway_analysis": report.get("pathway_analysis", {}),
                    "predicate_devices": report.get("predicate_devices", []),
                    "clinical_data_requirements": report.get("clinical_requirements", {}),
                    "safety_testing_requirements": report.get("safety_testing", []),
                    "post_market_requirements": report.get("post_market", {}),
                    "international_considerations": report.get("international", {}),
                    "timeline_estimates": report.get("timelines", {}),
                    "recommendations": report.get("recommendations", []),
                },
                "estimated_pages": 6,
            }

        except Exception as e:
            logger.error(f"Error generating regulatory report: {e}")
            return {
                "report_type": "regulatory_precedents",
                "status": "error",
                "error": str(e),
            }

    def _format_competitors(self, competitors: List[Dict]) -> str:
        """Format competitors for prompt."""
        if not competitors:
            return "No specific competitors identified"
        lines = []
        for comp in competitors:
            lines.append(f"- {comp.get('manufacturer', 'Unknown')}: {comp.get('product', 'Unknown')}")
        return "\n".join(lines)

    def _format_top_publications(self, publications: List[Dict]) -> str:
        """Format publications for prompt."""
        if not publications:
            return "No publications available"
        lines = []
        for i, pub in enumerate(publications, 1):
            lines.append(
                f"{i}. {pub.get('title', 'Untitled')} "
                f"({pub.get('journal_abbrev', 'Unknown')}, {pub.get('year', 'Unknown')})"
            )
        return "\n".join(lines)

    def _format_clearances(self, clearances: List[Dict]) -> str:
        """Format FDA clearances for prompt."""
        if not clearances:
            return "No recent clearances available"
        lines = []
        for c in clearances[:10]:
            lines.append(
                f"- {c.get('k_number', 'Unknown')}: {c.get('device_name', 'Unknown')} "
                f"({c.get('applicant', 'Unknown')}, {c.get('decision_date', 'Unknown')})"
            )
        return "\n".join(lines)

    def _add_sources(
        self,
        result: AgentResult,
        report_type: str,
        context: AgentContext
    ) -> None:
        """Add source provenance to result."""
        result.add_source(
            SourceType.LLM_INFERENCE,
            f"Deep Research Analysis - {report_type}",
            confidence=0.85,
            details={
                "report_type": report_type,
                "model": "gemini-3-pro-preview",
            }
        )

        if report_type == "competitive_landscape":
            result.add_source(
                SourceType.COMPETITIVE_INTEL,
                "Competitive Intelligence Synthesis",
                confidence=0.8,
            )
        elif report_type == "regulatory_precedents":
            result.add_source(
                SourceType.REGULATORY_INTEL,
                "FDA Regulatory Database Analysis",
                confidence=0.9,
            )
        elif report_type == "state_of_the_art":
            result.add_source(
                SourceType.LITERATURE,
                "PubMed Literature Synthesis",
                confidence=0.85,
            )
