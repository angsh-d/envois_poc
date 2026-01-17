"""
Report Generation Agent for Clinical Intelligence Platform.

Compiles research findings into structured reports and intelligence briefs.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)

logger = logging.getLogger(__name__)


class ReportGenerationAgent(BaseAgent):
    """
    Agent for generating compiled reports and intelligence briefs.

    Capabilities:
    - Compile multi-source research into cohesive reports
    - Generate executive summaries
    - Create product intelligence briefs
    - Format reports for different audiences
    """

    agent_type = AgentType.REPORT_GENERATION

    def __init__(self, **kwargs):
        """Initialize report generation agent."""
        super().__init__(**kwargs)

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute report generation.

        Args:
            context: Execution context with report parameters

        Returns:
            AgentResult with generated report

        Parameters:
            - report_type: Type of report to generate
                - intelligence_brief: Comprehensive product brief
                - executive_summary: High-level summary
                - technical_report: Detailed technical analysis
            - product_info: Product information
            - research_data: Data from research agents
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        report_type = context.parameters.get("report_type", "intelligence_brief")

        if report_type == "intelligence_brief":
            result.data = await self._generate_intelligence_brief(context)
        elif report_type == "executive_summary":
            result.data = await self._generate_executive_summary(context)
        elif report_type == "technical_report":
            result.data = await self._generate_technical_report(context)
        elif report_type == "onboarding_summary":
            result.data = await self._generate_onboarding_summary(context)
        else:
            result.success = False
            result.error = f"Unknown report type: {report_type}"
            return result

        result.add_source(
            SourceType.LLM_INFERENCE,
            f"Report Generation - {report_type}",
            confidence=0.9,
        )

        return result

    async def _generate_intelligence_brief(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate comprehensive product intelligence brief.

        Compiles all research findings into a single document.
        """
        product_info = context.parameters.get("product_info", {})
        research_data = context.parameters.get("research_data", {})
        recommendations = context.parameters.get("recommendations", {})

        prompt = self.load_prompt("report_intelligence_brief", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "protocol_id": product_info.get("protocol_id", "Unknown"),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "competitive_summary": self._summarize_competitive(research_data.get("competitive", {})),
            "sota_summary": self._summarize_sota(research_data.get("sota", {})),
            "regulatory_summary": self._summarize_regulatory(research_data.get("regulatory", {})),
            "data_sources": self._summarize_data_sources(recommendations),
        })

        try:
            brief = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

            return {
                "report_type": "intelligence_brief",
                "status": "completed",
                "generated_at": datetime.utcnow().isoformat(),
                "product_name": product_info.get("product_name"),
                "brief": {
                    "executive_overview": brief.get("executive_overview", ""),
                    "product_profile": {
                        "name": product_info.get("product_name"),
                        "category": product_info.get("category"),
                        "indication": product_info.get("indication"),
                        "key_technologies": product_info.get("technologies", []),
                        "differentiators": brief.get("differentiators", []),
                    },
                    "intelligence_capabilities": brief.get("intelligence_capabilities", {}),
                    "data_sources_configured": brief.get("data_sources", {}),
                    "key_metrics_available": brief.get("key_metrics", []),
                    "generated_reports": brief.get("reports_available", []),
                    "enabled_modules": brief.get("enabled_modules", []),
                    "persona_access": brief.get("persona_access", {}),
                    "recommendations": brief.get("recommendations", []),
                },
                "metadata": {
                    "version": "1.0",
                    "pages_estimated": 15,
                    "last_updated": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Error generating intelligence brief: {e}")
            return {
                "report_type": "intelligence_brief",
                "status": "error",
                "error": str(e),
            }

    async def _generate_executive_summary(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate executive summary of product configuration.
        """
        product_info = context.parameters.get("product_info", {})
        research_data = context.parameters.get("research_data", {})

        prompt = self.load_prompt("report_executive_summary", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "key_findings": self._extract_key_findings(research_data),
        })

        try:
            summary = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

            return {
                "report_type": "executive_summary",
                "status": "completed",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "headline": summary.get("headline", ""),
                    "key_points": summary.get("key_points", []),
                    "strategic_implications": summary.get("strategic_implications", []),
                    "recommended_actions": summary.get("recommended_actions", []),
                    "risk_factors": summary.get("risk_factors", []),
                },
            }

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {
                "report_type": "executive_summary",
                "status": "error",
                "error": str(e),
            }

    async def _generate_technical_report(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate detailed technical analysis report.
        """
        product_info = context.parameters.get("product_info", {})
        research_data = context.parameters.get("research_data", {})

        return {
            "report_type": "technical_report",
            "status": "completed",
            "generated_at": datetime.utcnow().isoformat(),
            "product_name": product_info.get("product_name"),
            "sections": {
                "product_overview": self._generate_product_section(product_info),
                "competitive_analysis": research_data.get("competitive", {}),
                "state_of_the_art": research_data.get("sota", {}),
                "regulatory_landscape": research_data.get("regulatory", {}),
                "data_infrastructure": self._generate_data_section(context),
            },
            "metadata": {
                "pages_estimated": 25,
                "detail_level": "comprehensive",
            },
        }

    async def _generate_onboarding_summary(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate summary of completed onboarding configuration.
        """
        product_info = context.parameters.get("product_info", {})
        discovery_results = context.parameters.get("discovery_results", {})
        recommendations = context.parameters.get("recommendations", {})
        research_reports = context.parameters.get("research_reports", {})

        return {
            "report_type": "onboarding_summary",
            "status": "completed",
            "generated_at": datetime.utcnow().isoformat(),
            "product_configured": product_info.get("product_name"),
            "configuration": {
                "product_info": product_info,
                "data_sources_configured": {
                    "clinical_study": True,
                    "registries": len(recommendations.get("registries", [])),
                    "literature": recommendations.get("literature", {}).get("selected_papers", 0),
                    "fda_surveillance": True,
                },
                "discovery_summary": {
                    "papers_found": discovery_results.get("literature_discovery", {}).get("papers_found", 0),
                    "registries_evaluated": discovery_results.get("registry_discovery", {}).get("registries_found", 0),
                    "competitors_identified": discovery_results.get("competitive_discovery", {}).get("competitors_identified", 0),
                },
                "reports_generated": [
                    {"name": name, "status": data.get("status", "pending")}
                    for name, data in research_reports.items()
                ],
                "enabled_modules": [
                    "Safety Intelligence",
                    "Risk Stratification",
                    "Regulatory Readiness",
                    "Competitive Intel",
                    "Claim Validation",
                    "Executive Dashboard",
                ],
            },
            "next_steps": [
                "Review generated research reports",
                "Configure user access permissions",
                "Set up monitoring alerts",
                "Schedule periodic refresh",
            ],
        }

    def _summarize_competitive(self, competitive_data: Dict) -> str:
        """Summarize competitive research findings."""
        if not competitive_data:
            return "No competitive analysis available"
        report = competitive_data.get("report", {})
        summary = report.get("executive_summary", "")
        if summary:
            return summary[:500]
        return "Competitive landscape analysis completed"

    def _summarize_sota(self, sota_data: Dict) -> str:
        """Summarize SOTA research findings."""
        if not sota_data:
            return "No SOTA analysis available"
        report = sota_data.get("report", {})
        summary = report.get("executive_summary", "")
        if summary:
            return summary[:500]
        return "State of the art analysis completed"

    def _summarize_regulatory(self, regulatory_data: Dict) -> str:
        """Summarize regulatory research findings."""
        if not regulatory_data:
            return "No regulatory analysis available"
        report = regulatory_data.get("report", {})
        summary = report.get("executive_summary", "")
        if summary:
            return summary[:500]
        return "Regulatory precedents analysis completed"

    def _summarize_data_sources(self, recommendations: Dict) -> str:
        """Summarize configured data sources."""
        sources = []
        if recommendations.get("clinical_study"):
            sources.append("Clinical Study Database")
        registries = recommendations.get("registries", [])
        if registries:
            sources.append(f"{len(registries)} Registry Benchmarks")
        lit = recommendations.get("literature", {})
        if lit:
            sources.append(f"{lit.get('selected_papers', 0)} Publications")
        if recommendations.get("fda_surveillance"):
            sources.append("FDA Surveillance")
        return ", ".join(sources) if sources else "No data sources configured"

    def _extract_key_findings(self, research_data: Dict) -> str:
        """Extract key findings from research data."""
        findings = []
        for category, data in research_data.items():
            if isinstance(data, dict) and data.get("report"):
                report = data["report"]
                if report.get("executive_summary"):
                    findings.append(f"{category}: {report['executive_summary'][:200]}")
        return "\n".join(findings) if findings else "No research findings available"

    def _generate_product_section(self, product_info: Dict) -> Dict:
        """Generate product overview section."""
        return {
            "name": product_info.get("product_name", "Unknown"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "technologies": product_info.get("technologies", []),
            "protocol_id": product_info.get("protocol_id", "Unknown"),
        }

    def _generate_data_section(self, context: AgentContext) -> Dict:
        """Generate data infrastructure section."""
        recommendations = context.parameters.get("recommendations", {})
        return {
            "clinical_data": recommendations.get("clinical_study", {}),
            "registry_data": recommendations.get("registries", []),
            "literature_base": recommendations.get("literature", {}),
            "surveillance_data": recommendations.get("fda_surveillance", {}),
        }
