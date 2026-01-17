"""
UC9 State-of-the-Art (SOTA) Report Service for Clinical Intelligence Platform.

Generates comprehensive SOTA reports for regulatory submissions and marketing.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext
from app.agents.literature_agent import LiteratureAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.services.llm_service import get_llm_service
from app.services.prompt_service import get_prompt_service
from data.loaders.yaml_loader import get_hybrid_loader

logger = logging.getLogger(__name__)


# Default SOTA sections
DEFAULT_SECTIONS = [
    "epidemiology",
    "current_treatment_options",
    "clinical_outcomes",
    "emerging_technologies",
    "unmet_needs",
]

SECTION_TITLES = {
    "epidemiology": "Epidemiology of Revision Total Hip Arthroplasty",
    "current_treatment_options": "Current Treatment Options",
    "clinical_outcomes": "Clinical Outcomes and Evidence",
    "emerging_technologies": "Emerging Technologies and Innovations",
    "unmet_needs": "Unmet Clinical Needs",
}


class SOTAService:
    """
    Service for UC9: SOTA Report Generation.

    Generates State-of-the-Art reports by:
    - Synthesizing literature evidence via RAG
    - Incorporating registry benchmark data
    - Generating structured regulatory-grade content
    """

    def __init__(self):
        """Initialize SOTA service."""
        self._literature_agent = LiteratureAgent()
        self._synthesis_agent = SynthesisAgent()
        self._llm = get_llm_service()
        self._prompts = get_prompt_service()
        self._doc_loader = get_hybrid_loader()

    async def generate_sota_report(
        self,
        topic: str = "hip_revision",
        sections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive SOTA report.

        Args:
            topic: Report topic (e.g., "hip_revision")
            sections: Specific sections to include (default: all)

        Returns:
            Dict with complete SOTA report
        """
        request_id = str(uuid.uuid4())
        sections = sections or DEFAULT_SECTIONS

        # Get literature data
        lit_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "all"}
        )
        literature_result = await self._literature_agent.run(lit_context)
        lit_data = literature_result.data if literature_result.success else {}

        # Get registry data for context
        from app.agents.registry_agent import RegistryAgent
        registry_agent = RegistryAgent()
        reg_context = AgentContext(
            request_id=request_id,
            parameters={"query_type": "all"}
        )
        registry_result = await registry_agent.run(reg_context)
        reg_data = registry_result.data if registry_result.success else {}

        # Generate each section
        report_sections = []
        for section in sections:
            section_content = await self._generate_section(
                topic=topic,
                section_name=section,
                literature_data=lit_data,
                registry_data=reg_data
            )
            report_sections.append(section_content)

        # Generate executive summary
        executive_summary = await self._generate_executive_summary(
            topic, report_sections, lit_data, reg_data
        )

        # Build references list
        references = self._build_references(lit_data, reg_data)

        # Compile final report
        return {
            "success": True,
            "report_type": "sota_report",
            "generated_at": datetime.utcnow().isoformat(),
            "title": self._get_report_title(topic),
            "topic": topic,
            "executive_summary": executive_summary,
            "sections": report_sections,
            "references": references,
            "summary_table": self._build_summary_table(lit_data, reg_data),
            "sources": self._collect_sources(literature_result, registry_result),
            "confidence": 0.85,
            "metadata": {
                "n_literature_sources": lit_data.get("n_publications", 0),
                "n_registries": reg_data.get("n_registries", 0),
                "sections_generated": len(report_sections),
            }
        }

    async def _generate_section(
        self,
        topic: str,
        section_name: str,
        literature_data: Dict,
        registry_data: Dict
    ) -> Dict[str, Any]:
        """Generate a single SOTA section."""
        # Format data for prompt
        lit_text = self._format_literature_for_section(section_name, literature_data)
        reg_text = self._format_registry_for_section(section_name, registry_data)

        # Get section title
        section_title = SECTION_TITLES.get(
            section_name,
            section_name.replace("_", " ").title()
        )

        # Generate section content
        prompt = self._prompts.load("sota_section_generation", {
            "topic": topic.replace("_", " ").title(),
            "section_name": section_title,
            "literature_data": lit_text,
            "registry_data": reg_text,
        })

        content = await self._llm.generate(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
            max_tokens=1500
        )

        return {
            "section_id": section_name,
            "title": section_title,
            "content": content.strip(),
            "word_count": len(content.split()),
        }

    async def _generate_executive_summary(
        self,
        topic: str,
        sections: List[Dict],
        lit_data: Dict,
        reg_data: Dict
    ) -> str:
        """Generate executive summary for the SOTA report."""
        # Build summary of key points
        section_summaries = "\n".join([
            f"- {s['title']}: {len(s['content'].split())} words"
            for s in sections
        ])

        # Get key statistics
        n_pubs = lit_data.get("n_publications", 0)
        n_regs = reg_data.get("n_registries", 0)

        prompt = f"""Generate a 2-3 paragraph executive summary for a State-of-the-Art report on {topic.replace('_', ' ')}.

Key facts:
- Report covers {len(sections)} sections: {', '.join([s['title'] for s in sections])}
- Based on {n_pubs} literature publications
- Includes data from {n_regs} international registries

Registry survival rates (2-year):
{self._format_survival_rates(reg_data)}

The executive summary should:
1. State the purpose of the SOTA review
2. Summarize the current state of revision hip arthroplasty
3. Highlight key findings from the evidence review
4. Note the clinical relevance for medical device development

Write in formal regulatory documentation style. Be concise and factual."""

        summary = await self._llm.generate(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
            max_tokens=800
        )

        return summary.strip()

    def _format_literature_for_section(
        self,
        section_name: str,
        lit_data: Dict
    ) -> str:
        """Format literature data relevant to a specific section."""
        if not lit_data:
            return "No literature data available."

        lines = [f"Literature Summary ({lit_data.get('n_publications', 0)} publications):"]

        # Add benchmarks
        benchmarks = lit_data.get("aggregate_benchmarks", {})
        for metric, data in benchmarks.items():
            if isinstance(data, dict):
                mean = data.get("mean")
                if mean is not None:
                    if mean < 1:
                        lines.append(f"- {metric}: {mean*100:.1f}% (mean)")
                    else:
                        lines.append(f"- {metric}: {mean:.1f} (mean)")

        # Add risk factors if relevant to outcomes section
        if section_name in ["clinical_outcomes", "unmet_needs"]:
            n_risk = lit_data.get("n_risk_factors", 0)
            if n_risk > 0:
                lines.append(f"- {n_risk} risk factors identified in literature")

        return "\n".join(lines)

    def _format_registry_for_section(
        self,
        section_name: str,
        reg_data: Dict
    ) -> str:
        """Format registry data relevant to a specific section."""
        if not reg_data:
            return "No registry data available."

        lines = [f"Registry Data ({reg_data.get('n_registries', 0)} registries, "
                 f"{reg_data.get('total_procedures', 0):,} procedures):"]

        registries = reg_data.get("registries", [])

        # Add relevant metrics based on section
        if section_name in ["epidemiology", "clinical_outcomes"]:
            for reg in registries[:5]:  # Top 5 registries
                abbr = reg.get("abbreviation", "Unknown")
                n_proc = reg.get("n_procedures", 0)
                survival = reg.get("survival_rates", {}).get("2yr")
                revision = reg.get("revision_rates", {}).get("2yr")

                line = f"- {abbr}: n={n_proc:,}"
                if survival:
                    line += f", 2yr survival: {survival*100:.1f}%"
                if revision:
                    line += f", 2yr revision: {revision*100:.1f}%"
                lines.append(line)

        # Add summary stats
        summary = reg_data.get("summary", {})
        rev_summary = summary.get("revision_rate_2yr", {})
        if rev_summary:
            range_str = rev_summary.get("range_formatted", "N/A")
            lines.append(f"- Global revision rate range: {range_str}")

        return "\n".join(lines)

    def _format_survival_rates(self, reg_data: Dict) -> str:
        """Format survival rates for executive summary."""
        if not reg_data:
            return "Registry survival data not available."

        lines = []
        registries = reg_data.get("registries", [])

        for reg in registries[:5]:
            abbr = reg.get("abbreviation", "Unknown")
            survival = reg.get("survival_rates", {}).get("2yr")
            if survival:
                lines.append(f"- {abbr}: {survival*100:.1f}%")

        return "\n".join(lines) if lines else "Survival data not available."

    def _get_report_title(self, topic: str) -> str:
        """Get formatted report title."""
        topic_titles = {
            "hip_revision": "State-of-the-Art: Revision Total Hip Arthroplasty",
            "acetabular_reconstruction": "State-of-the-Art: Acetabular Reconstruction",
            "porous_tantalum": "State-of-the-Art: Porous Tantalum in Orthopedic Surgery",
        }
        return topic_titles.get(topic, f"State-of-the-Art: {topic.replace('_', ' ').title()}")

    def _build_summary_table(
        self,
        lit_data: Dict,
        reg_data: Dict
    ) -> Dict[str, Any]:
        """Build summary statistics table."""
        table = {
            "registry_summary": [],
            "outcome_benchmarks": [],
        }

        # Registry summary
        registries = reg_data.get("registries", [])
        for reg in registries:
            table["registry_summary"].append({
                "registry": reg.get("abbreviation"),
                "n_procedures": reg.get("n_procedures"),
                "survival_2yr": reg.get("survival_rates", {}).get("2yr"),
                "revision_rate_2yr": reg.get("revision_rates", {}).get("2yr"),
            })

        # Outcome benchmarks from literature
        benchmarks = lit_data.get("aggregate_benchmarks", {})
        for metric, data in benchmarks.items():
            if isinstance(data, dict):
                table["outcome_benchmarks"].append({
                    "metric": metric,
                    "mean": data.get("mean"),
                    "range_low": data.get("min"),
                    "range_high": data.get("max"),
                })

        return table

    def _build_references(
        self,
        lit_data: Dict,
        reg_data: Dict
    ) -> List[Dict[str, Any]]:
        """Build references list."""
        references = []

        # Add literature references
        publications = lit_data.get("publications", [])
        for i, pub in enumerate(publications, 1):
            references.append({
                "id": f"L{i}",
                "type": "literature",
                "reference": f"{pub.get('title', 'Unknown')} ({pub.get('year', 'N/A')})",
                "n_patients": pub.get("n_patients"),
            })

        # Add registry references
        registries = reg_data.get("registries", [])
        for i, reg in enumerate(registries, 1):
            references.append({
                "id": f"R{i}",
                "type": "registry",
                "reference": f"{reg.get('name', reg.get('abbreviation', 'Unknown'))} "
                             f"Annual Report {reg.get('report_year', 'N/A')}",
                "n_procedures": reg.get("n_procedures"),
            })

        return references

    def _collect_sources(self, literature_result, registry_result) -> List[Dict]:
        """Collect all sources from agent results."""
        sources = []

        if literature_result.success:
            for source in literature_result.sources:
                sources.append(source.to_dict())

        if registry_result.success:
            for source in registry_result.sources:
                sources.append(source.to_dict())

        return sources

    async def get_available_sections(self) -> Dict[str, Any]:
        """Get list of available SOTA sections."""
        return {
            "available_sections": [
                {"id": section, "title": SECTION_TITLES.get(section, section)}
                for section in DEFAULT_SECTIONS
            ],
            "default_sections": DEFAULT_SECTIONS,
        }


# Singleton instance
_sota_service: Optional[SOTAService] = None


def get_sota_service() -> SOTAService:
    """Get singleton SOTA service instance."""
    global _sota_service
    if _sota_service is None:
        _sota_service = SOTAService()
    return _sota_service
