"""
Publication Discovery Agent for Clinical Intelligence Platform.

Discovers relevant publications from PubMed and other sources
for product onboarding and knowledge base building.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from app.services.pubmed_service import get_pubmed_service, PubMedService

logger = logging.getLogger(__name__)


class PublicationDiscoveryAgent(BaseAgent):
    """
    Agent for discovering and curating relevant publications.

    Capabilities:
    - Search PubMed for product-relevant publications
    - Rank publications by relevance
    - Extract key insights from abstracts
    - Build curated reading lists
    """

    agent_type = AgentType.PUBLICATION_DISCOVERY

    def __init__(self, pubmed_service: Optional[PubMedService] = None, **kwargs):
        """Initialize publication discovery agent."""
        super().__init__(**kwargs)
        self._pubmed = pubmed_service or get_pubmed_service()

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute publication discovery.

        Args:
            context: Execution context with search parameters

        Returns:
            AgentResult with discovered publications

        Parameters:
            - action: Discovery action
                - search: General publication search
                - product_search: Search for product-specific publications
                - build_reading_list: Create curated reading list
            - query: Search query (for search action)
            - product_info: Product information (for product_search)
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        action = context.parameters.get("action", "search")

        if action == "search":
            result.data = await self._search_publications(context)
        elif action == "product_search":
            result.data = await self._product_publication_search(context)
        elif action == "build_reading_list":
            result.data = await self._build_reading_list(context)
        elif action == "analyze_publications":
            result.data = await self._analyze_publications(context)
        else:
            result.success = False
            result.error = f"Unknown action: {action}"
            return result

        # Add source provenance
        result.add_source(
            SourceType.PUBMED,
            "PubMed/MEDLINE Database via NCBI E-utilities",
            confidence=0.95,
            details={
                "action": action,
                "search_date": datetime.utcnow().isoformat(),
            }
        )

        return result

    async def _search_publications(self, context: AgentContext) -> Dict[str, Any]:
        """
        Perform general publication search.

        Args:
            context: Context with query parameters

        Returns:
            Search results
        """
        query = context.parameters.get("query", "")
        max_results = context.parameters.get("max_results", 50)
        min_date = context.parameters.get("min_date")
        max_date = context.parameters.get("max_date")

        if not query:
            return {
                "success": False,
                "error": "No search query provided",
                "publications": [],
            }

        results = await self._pubmed.search_publications(
            query=query,
            max_results=max_results,
            min_date=min_date,
            max_date=max_date,
        )

        return {
            "success": results.get("success", False),
            "query": query,
            "total_found": results.get("total_count", 0),
            "returned": results.get("returned_count", 0),
            "publications": results.get("articles", []),
            "search_timestamp": datetime.utcnow().isoformat(),
        }

    async def _product_publication_search(self, context: AgentContext) -> Dict[str, Any]:
        """
        Search for publications relevant to a specific product.

        Args:
            context: Context with product information

        Returns:
            Categorized publication results
        """
        product_info = context.parameters.get("product_info", {})
        product_name = product_info.get("product_name", "")
        indication = product_info.get("indication", "")
        technologies = product_info.get("technologies", [])
        max_results = context.parameters.get("max_results", 50)

        # Build search strategy
        search_strategies = []

        # Strategy 1: Direct product/technology search
        if technologies:
            tech_results = await self._pubmed.search_for_product(
                product_name=product_name,
                indication=indication,
                technologies=technologies,
                max_results=max_results,
            )
            if tech_results.get("success"):
                search_strategies.append({
                    "strategy": "technology_based",
                    "results": tech_results,
                })

        # Strategy 2: Indication-focused search
        if indication:
            indication_query = f'"{indication}"[Title/Abstract] AND (outcomes OR survival OR revision OR failure)'
            indication_results = await self._pubmed.search_publications(
                query=indication_query,
                max_results=max_results // 2,
                min_date="2018",
            )
            if indication_results.get("success"):
                search_strategies.append({
                    "strategy": "indication_focused",
                    "results": indication_results,
                })

        # Merge and deduplicate results
        all_publications = []
        seen_pmids = set()

        for strategy in search_strategies:
            for article in strategy.get("results", {}).get("articles", []):
                pmid = article.get("pmid")
                if pmid and pmid not in seen_pmids:
                    seen_pmids.add(pmid)
                    article["discovery_strategy"] = strategy["strategy"]
                    all_publications.append(article)

        # Sort by relevance
        all_publications.sort(
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )

        # Categorize publications
        categories = self._categorize_publications(all_publications)

        return {
            "success": True,
            "product_name": product_name,
            "indication": indication,
            "total_found": len(all_publications),
            "publications": all_publications[:max_results],
            "categories": categories,
            "top_papers": all_publications[:10],
            "search_strategies_used": [s["strategy"] for s in search_strategies],
            "search_timestamp": datetime.utcnow().isoformat(),
        }

    def _categorize_publications(self, publications: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize publications by type and topic."""
        categories = {
            "clinical_outcomes": [],
            "safety_studies": [],
            "registry_reports": [],
            "reviews_meta_analyses": [],
            "device_design": [],
            "other": [],
        }

        for pub in publications:
            title_lower = pub.get("title", "").lower()
            pub_types = [pt.lower() for pt in pub.get("pub_types", [])]

            # Categorize based on title and publication type
            if "review" in pub_types or "meta-analysis" in pub_types:
                categories["reviews_meta_analyses"].append(pub)
            elif "registry" in title_lower or "report" in title_lower:
                categories["registry_reports"].append(pub)
            elif any(term in title_lower for term in ["safety", "adverse", "complication", "failure"]):
                categories["safety_studies"].append(pub)
            elif any(term in title_lower for term in ["outcome", "survival", "follow-up", "result"]):
                categories["clinical_outcomes"].append(pub)
            elif any(term in title_lower for term in ["design", "biomechanical", "material", "coating"]):
                categories["device_design"].append(pub)
            else:
                categories["other"].append(pub)

        return {k: v[:10] for k, v in categories.items()}  # Limit each category

    async def _build_reading_list(self, context: AgentContext) -> Dict[str, Any]:
        """
        Build a curated reading list for a product.

        Uses LLM to analyze and recommend publications.
        """
        product_info = context.parameters.get("product_info", {})
        publications = context.parameters.get("publications", [])

        if not publications:
            # First search for publications
            search_result = await self._product_publication_search(context)
            publications = search_result.get("publications", [])

        if not publications:
            return {
                "success": False,
                "error": "No publications found to build reading list",
                "reading_list": [],
            }

        # Use LLM to analyze and rank publications
        prompt = self.load_prompt("publication_ranking", {
            "product_name": product_info.get("product_name", "the product"),
            "indication": product_info.get("indication", "unknown indication"),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "publications": self._format_publications_for_prompt(publications[:30]),
        })

        try:
            analysis = await self.call_llm_json(prompt, model="gemini-3-pro-preview")
            reading_list = analysis.get("reading_list", [])

            # Match back to full publication data
            enriched_list = []
            for item in reading_list:
                pmid = item.get("pmid", "")
                for pub in publications:
                    if pub.get("pmid") == pmid:
                        enriched_list.append({
                            **pub,
                            "recommendation_reason": item.get("reason", ""),
                            "priority": item.get("priority", "medium"),
                        })
                        break

            return {
                "success": True,
                "reading_list": enriched_list,
                "total_analyzed": len(publications),
                "total_recommended": len(enriched_list),
                "analysis_summary": analysis.get("summary", ""),
            }

        except Exception as e:
            logger.error(f"Error building reading list: {e}")
            # Fall back to top-ranked publications
            return {
                "success": True,
                "reading_list": publications[:15],
                "total_analyzed": len(publications),
                "total_recommended": min(15, len(publications)),
                "analysis_summary": "Ranked by relevance score",
            }

    def _format_publications_for_prompt(self, publications: List[Dict]) -> str:
        """Format publications for LLM prompt."""
        lines = []
        for i, pub in enumerate(publications, 1):
            lines.append(
                f"{i}. [{pub.get('pmid')}] {pub.get('title', 'No title')} "
                f"({pub.get('journal_abbrev', 'Unknown')}, {pub.get('year', 'Unknown')})"
            )
        return "\n".join(lines)

    async def _analyze_publications(self, context: AgentContext) -> Dict[str, Any]:
        """
        Analyze a set of publications to extract insights.

        Uses LLM to synthesize findings across publications.
        """
        publications = context.parameters.get("publications", [])
        analysis_focus = context.parameters.get("focus", "general")

        if not publications:
            return {
                "success": False,
                "error": "No publications to analyze",
                "insights": [],
            }

        # Fetch abstracts for top publications
        abstracts = []
        for pub in publications[:10]:
            pmid = pub.get("pmid")
            if pmid:
                abstract = await self._pubmed.get_article_abstract(pmid)
                if abstract:
                    abstracts.append({
                        "pmid": pmid,
                        "title": pub.get("title"),
                        "abstract": abstract[:1000],  # Truncate long abstracts
                    })

        prompt = self.load_prompt("publication_analysis", {
            "focus": analysis_focus,
            "publication_count": len(abstracts),
            "abstracts": self._format_abstracts_for_prompt(abstracts),
        })

        try:
            analysis = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

            return {
                "success": True,
                "focus": analysis_focus,
                "publications_analyzed": len(abstracts),
                "key_findings": analysis.get("key_findings", []),
                "themes": analysis.get("themes", []),
                "evidence_gaps": analysis.get("evidence_gaps", []),
                "synthesis": analysis.get("synthesis", ""),
            }

        except Exception as e:
            logger.error(f"Error analyzing publications: {e}")
            return {
                "success": False,
                "error": str(e),
                "insights": [],
            }

    def _format_abstracts_for_prompt(self, abstracts: List[Dict]) -> str:
        """Format abstracts for LLM prompt."""
        lines = []
        for i, item in enumerate(abstracts, 1):
            lines.append(f"--- Publication {i}: {item['title']} ---")
            lines.append(item.get("abstract", "No abstract available"))
            lines.append("")
        return "\n".join(lines)
