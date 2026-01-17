"""
Competitive Intelligence Agent for Clinical Intelligence Platform.

Analyzes competitor products using real data from openFDA 510(k) database
and PubMed comparative studies.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from app.services.pubmed_service import get_pubmed_service

logger = logging.getLogger(__name__)

# openFDA API endpoints
OPENFDA_510K_URL = "https://api.fda.gov/device/510k.json"

# Known competitor products for hip reconstruction/revision
COMPETITOR_MAPPING = {
    "revision_tha": {
        "Zimmer Biomet": {
            "products": ["Trabecular Metal", "G7 Acetabular System", "Continuum"],
            "technology": "Porous tantalum",
            "510k_search": "trabecular metal hip",
        },
        "Smith+Nephew": {
            "products": ["REDAPT", "R3 Acetabular System", "Polarstem"],
            "technology": "Modular revision system",
            "510k_search": "redapt revision hip",
        },
        "Stryker": {
            "products": ["Trident II", "Restoration Modular", "Accolade"],
            "technology": "Tritanium porous coating",
            "510k_search": "trident hip acetabular",
        },
        "DePuy Synthes": {
            "products": ["Pinnacle", "GRIPTION", "Corail"],
            "technology": "GRIPTION porous coating",
            "510k_search": "pinnacle acetabular hip",
        },
        "Lima Corporate": {
            "products": ["DELTA TT", "Lima Revision", "Trabecular Titanium"],
            "technology": "Trabecular Titanium 3D printed",
            "510k_search": "lima trabecular titanium",
        },
        "Medacta": {
            "products": ["Mpact", "Quadra-H", "Versafit"],
            "technology": "Highly porous titanium",
            "510k_search": "medacta hip acetabular",
        },
    },
    "primary_tha": {
        # Can be extended for primary THA products
    },
}


class CompetitiveIntelAgent(BaseAgent):
    """
    Competitive intelligence agent using real FDA and PubMed data.

    Capabilities:
    - Query FDA 510(k) database for competitor clearances
    - Search PubMed for comparative studies
    - Analyze competitor product features
    - Generate competitive landscape reports
    """

    agent_type = AgentType.RESEARCH

    def __init__(self, **kwargs):
        """Initialize competitive intelligence agent."""
        super().__init__(**kwargs)
        self._http_client: Optional[httpx.AsyncClient] = None
        self._pubmed = get_pubmed_service()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._http_client

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute competitive intelligence analysis.

        Parameters:
            - action: analyze_competitors, search_510k, comparative_studies, generate_landscape
            - product_category: "revision_tha", "primary_tha"
            - product_name: Name of the focus product
            - indication: Clinical indication
            - technologies: Key technologies to compare
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        action = context.parameters.get("action", "analyze_competitors")

        if action == "analyze_competitors":
            result.data = await self._analyze_competitors(context)
        elif action == "search_510k":
            result.data = await self._search_510k_clearances(context)
        elif action == "comparative_studies":
            result.data = await self._find_comparative_studies(context)
        elif action == "generate_landscape":
            result.data = await self._generate_landscape(context)
        elif action == "discovery":
            # Quick discovery for onboarding flow
            result.data = await self._quick_discovery(context)
        else:
            result.success = False
            result.error = f"Unknown action: {action}"
            return result

        # Add source provenance
        result.add_source(
            SourceType.FDA_510K,
            "Competitive Intelligence Analysis",
            confidence=0.85,
            details={"action": action}
        )

        return result

    async def _quick_discovery(self, context: AgentContext) -> Dict[str, Any]:
        """
        Quick competitor discovery for onboarding flow.
        Returns competitor list without full analysis.
        """
        product_category = context.parameters.get("product_category", "revision_tha")
        product_name = context.parameters.get("product_name", "")

        competitors = COMPETITOR_MAPPING.get(product_category, {})

        # Filter out the focus product's manufacturer
        focus_manufacturer = None
        for mfr, data in competitors.items():
            if any(prod.lower() in product_name.lower() for prod in data["products"]):
                focus_manufacturer = mfr
                break

        competitor_list = []
        for manufacturer, data in competitors.items():
            if manufacturer == focus_manufacturer:
                continue
            competitor_list.append({
                "manufacturer": manufacturer,
                "product": data["products"][0],
                "technology": data["technology"],
            })

        return {
            "status": "completed",
            "progress": 100,
            "competitors_identified": len(competitor_list),
            "products": competitor_list[:5],  # Top 5 competitors
        }

    async def _analyze_competitors(self, context: AgentContext) -> Dict[str, Any]:
        """
        Comprehensive competitor analysis.
        """
        product_category = context.parameters.get("product_category", "revision_tha")
        product_name = context.parameters.get("product_name", "DELTA TT")

        competitors = COMPETITOR_MAPPING.get(product_category, {})

        # Run parallel analysis
        results = await asyncio.gather(
            self._search_510k_clearances(context),
            self._find_comparative_studies(context),
            return_exceptions=True
        )

        fda_results = results[0] if not isinstance(results[0], Exception) else {}
        pubmed_results = results[1] if not isinstance(results[1], Exception) else {}

        # Compile competitor profiles
        profiles = []
        for manufacturer, data in competitors.items():
            profile = {
                "manufacturer": manufacturer,
                "primary_product": data["products"][0],
                "all_products": data["products"],
                "technology": data["technology"],
                "clearances": [],
                "publications": [],
            }

            # Match FDA clearances
            for clearance in fda_results.get("clearances", []):
                if manufacturer.lower() in clearance.get("applicant", "").lower():
                    profile["clearances"].append(clearance)

            profiles.append(profile)

        return {
            "focus_product": product_name,
            "category": product_category,
            "competitors": profiles,
            "total_clearances": fda_results.get("total_count", 0),
            "comparative_publications": pubmed_results.get("total_count", 0),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    async def _search_510k_clearances(self, context: AgentContext) -> Dict[str, Any]:
        """
        Search FDA 510(k) database for competitor clearances.
        """
        product_category = context.parameters.get("product_category", "revision_tha")
        competitors = COMPETITOR_MAPPING.get(product_category, {})

        client = await self._get_client()
        all_clearances = []

        # Search for each competitor
        for manufacturer, data in competitors.items():
            search_term = data.get("510k_search", "")
            if not search_term:
                continue

            try:
                # Query openFDA 510(k) endpoint
                params = {
                    "search": f'device_name:"{search_term}" OR applicant:"{manufacturer}"',
                    "limit": 10,
                    "sort": "decision_date:desc",
                }

                # Add API key if available
                import os
                api_key = os.getenv("OPENFDA_API_KEY", "")
                if api_key:
                    params["api_key"] = api_key

                response = await client.get(OPENFDA_510K_URL, params=params)

                if response.status_code == 200:
                    data_response = response.json()
                    results = data_response.get("results", [])

                    for r in results:
                        clearance = {
                            "k_number": r.get("k_number", ""),
                            "applicant": r.get("applicant", ""),
                            "device_name": r.get("device_name", ""),
                            "decision_date": r.get("decision_date", ""),
                            "product_code": r.get("product_code", ""),
                            "regulation_number": r.get("regulation_number", ""),
                            "statement_or_summary": r.get("statement_or_summary", ""),
                            "manufacturer": manufacturer,
                        }
                        all_clearances.append(clearance)

                elif response.status_code != 404:
                    logger.warning(f"FDA 510(k) search failed for {manufacturer}: {response.status_code}")

            except httpx.RequestError as e:
                logger.error(f"Network error searching 510(k) for {manufacturer}: {e}")
            except Exception as e:
                logger.error(f"Error searching 510(k) for {manufacturer}: {e}")

            # Rate limit: 240 requests per minute
            await asyncio.sleep(0.3)

        # Deduplicate by K number
        seen = set()
        unique_clearances = []
        for c in all_clearances:
            k_num = c.get("k_number")
            if k_num and k_num not in seen:
                seen.add(k_num)
                unique_clearances.append(c)

        return {
            "success": True,
            "clearances": unique_clearances,
            "total_count": len(unique_clearances),
            "search_timestamp": datetime.utcnow().isoformat(),
            "source": "openFDA 510(k) Database",
        }

    async def _find_comparative_studies(self, context: AgentContext) -> Dict[str, Any]:
        """
        Search PubMed for comparative studies.
        """
        indication = context.parameters.get("indication", "revision hip arthroplasty")
        technologies = context.parameters.get("technologies", ["trabecular titanium"])

        # Build comparative study query
        tech_terms = " OR ".join([f'"{t}"' for t in technologies])
        query = f'({tech_terms}) AND ({indication}) AND (comparative[ti] OR comparison[ti] OR versus[ti] OR outcomes[ti])'

        try:
            results = await self._pubmed.search_publications(
                query=query,
                max_results=30,
                min_date="2015",
            )

            # Add insight extraction for top articles
            if results.get("success") and results.get("articles"):
                for article in results["articles"][:10]:
                    article["insight"] = self._extract_insight(article, technologies)

            return results

        except Exception as e:
            logger.error(f"Error searching comparative studies: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_count": 0,
                "articles": [],
            }

    def _extract_insight(self, article: Dict, technologies: List[str]) -> str:
        """Extract potential insight from article title."""
        title = article.get("title", "").lower()

        if "survival" in title or "outcome" in title:
            return "Reports survival/outcome data for comparison"
        if "revision" in title:
            return "Revision-specific outcomes data"
        if "registry" in title:
            return "Registry-level comparative data"
        if "meta-analysis" in title or "systematic review" in title:
            return "Synthesized evidence across multiple studies"
        if any(t.lower() in title for t in technologies):
            return f"Technology-specific outcomes"
        return "General comparative evidence"

    async def _generate_landscape(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate comprehensive competitive landscape.
        """
        # Get full analysis
        analysis = await self._analyze_competitors(context)

        # Use LLM to synthesize landscape report
        prompt = self.load_prompt("competitive_landscape", {
            "focus_product": analysis.get("focus_product", ""),
            "category": analysis.get("category", ""),
            "competitors": str(analysis.get("competitors", [])),
            "clearances": str(analysis.get("total_clearances", 0)),
            "publications": str(analysis.get("comparative_publications", 0)),
        })

        landscape = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

        return {
            "analysis": analysis,
            "landscape_summary": landscape,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
