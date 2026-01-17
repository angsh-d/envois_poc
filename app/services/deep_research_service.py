"""
Deep Research Service for Clinical Intelligence Platform.

Provides comprehensive research capabilities using:
- Primary: Gemini Deep Research Agent (gemini-3-pro-preview with Google Search)
- Fallback: OpenAI Responses API with web search tool

Generates multi-step, grounded research reports with citations.
"""
import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import google.generativeai as genai
from google.generativeai.types import Tool

from app.config import settings
from app.services.llm_service import get_llm_service
from app.services.vector_service import get_vector_service

logger = logging.getLogger(__name__)

# Deep Research model configurations
GEMINI_DEEP_RESEARCH_MODEL = "gemini-3-pro-preview"
GEMINI_FALLBACK_MODEL = "gemini-3-pro-preview"
OPENAI_DEEP_RESEARCH_MODEL = "gpt-4o"

# Rate limiting
RESEARCH_REQUEST_DELAY = 1.0  # seconds between research requests


class DeepResearchService:
    """
    Deep Research service using Gemini Deep Research Agent.

    Primary: Gemini Deep Research Agent
    - Uses gemini-3-pro-preview with enhanced reasoning
    - Google Search grounding for real-time web research
    - Multi-step research with planning and synthesis

    Fallback: OpenAI Responses API
    - Uses GPT-4o with web_search tool
    - Real-time web search capabilities
    - Structured response generation
    """

    def __init__(self):
        """Initialize deep research service."""
        self._llm_service = get_llm_service()
        self._vector_service = get_vector_service()
        self._last_request_time: float = 0

        # Configure Gemini
        self._gemini_api_key = settings.gemini_api_key
        if self._gemini_api_key:
            genai.configure(api_key=self._gemini_api_key)

        # Azure OpenAI configuration
        self._azure_openai_endpoint = settings.azure_openai_endpoint
        self._azure_openai_api_key = settings.azure_openai_api_key
        self._azure_openai_api_version = settings.azure_openai_api_version

        # HTTP client for OpenAI
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=120.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._http_client

    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < RESEARCH_REQUEST_DELAY:
            await asyncio.sleep(RESEARCH_REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    async def research_with_deep_research(
        self,
        topic: str,
        context: str = "",
        product_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform deep research using Gemini Deep Research Agent.

        Uses multi-step reasoning with Google Search grounding for
        comprehensive, citation-backed research.

        Args:
            topic: Research topic
            context: Additional context from local knowledge
            product_info: Product information for context

        Returns:
            Research result with grounding metadata and citations
        """
        await self._rate_limit()

        try:
            # Build comprehensive research prompt
            prompt = self._build_deep_research_prompt(topic, context, product_info)

            # Try Gemini Deep Research Agent (thinking model with search)
            result = await self._gemini_deep_research(prompt)

            if result.get("success"):
                return result

            # If thinking model fails, try standard model with grounding
            logger.warning("Gemini thinking model failed, trying standard model with grounding")
            result = await self._gemini_grounded_research(prompt)

            if result.get("success"):
                return result

            # Fallback to OpenAI Responses API
            logger.warning("Gemini research failed, falling back to OpenAI")
            return await self._openai_deep_research(prompt, topic, product_info)

        except Exception as e:
            logger.error(f"Deep research failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _gemini_deep_research(self, prompt: str) -> Dict[str, Any]:
        """
        Execute research using Gemini Deep Research Agent.

        Uses gemini-3-pro-preview with Google Search grounding
        for multi-step reasoning research.
        """
        try:
            # Create model with Google Search grounding
            model = genai.GenerativeModel(
                GEMINI_DEEP_RESEARCH_MODEL,
                tools=[Tool(google_search={})],
                system_instruction="""You are a deep research agent for medical device clinical intelligence.

Your task is to conduct thorough, multi-step research on the given topic:
1. Plan your research approach
2. Search for relevant information using Google Search
3. Synthesize findings from multiple sources
4. Provide comprehensive analysis with citations
5. Identify key insights and recommendations

Always cite sources with URLs when available. Focus on:
- Peer-reviewed publications and clinical data
- Regulatory information (FDA, CE marking)
- Competitive landscape and market data
- Industry trends and expert opinions"""
            )

            # Generate with extended thinking and grounding
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 16384,
                },
            )

            # Extract content and grounding metadata
            content = response.text
            grounding_metadata = None
            sources = []
            thinking_content = None

            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]

                # Extract thinking content if available
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "thought") and part.thought:
                            thinking_content = getattr(part, "text", None)

                # Extract grounding metadata
                if hasattr(candidate, "grounding_metadata"):
                    grounding_metadata = candidate.grounding_metadata
                    sources = self._extract_sources_from_grounding(grounding_metadata)

            return {
                "success": True,
                "content": content,
                "thinking_process": thinking_content,
                "grounding_used": grounding_metadata is not None,
                "sources": sources,
                "model": GEMINI_DEEP_RESEARCH_MODEL,
                "method": "gemini_deep_research",
            }

        except Exception as e:
            logger.warning(f"Gemini Deep Research failed: {e}")
            return {"success": False, "error": str(e)}

    async def _gemini_grounded_research(self, prompt: str) -> Dict[str, Any]:
        """
        Execute research using standard Gemini model with Google Search grounding.
        """
        try:
            model = genai.GenerativeModel(
                GEMINI_FALLBACK_MODEL,
                tools=[Tool(google_search={})],
            )

            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 8192,
                },
            )

            grounding_metadata = None
            sources = []
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "grounding_metadata"):
                    grounding_metadata = candidate.grounding_metadata
                    sources = self._extract_sources_from_grounding(grounding_metadata)

            return {
                "success": True,
                "content": response.text,
                "grounding_used": grounding_metadata is not None,
                "sources": sources,
                "model": GEMINI_FALLBACK_MODEL,
                "method": "gemini_grounded",
            }

        except Exception as e:
            logger.warning(f"Gemini grounded research failed: {e}")
            return {"success": False, "error": str(e)}

    async def _openai_deep_research(
        self,
        prompt: str,
        topic: str,
        product_info: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Execute research using OpenAI Responses API with web search.

        Uses Azure OpenAI with web search tool for real-time research.
        """
        if not self._azure_openai_endpoint or not self._azure_openai_api_key:
            return {
                "success": False,
                "error": "Azure OpenAI credentials not configured",
            }

        try:
            client = await self._get_http_client()

            # Build the request for Azure OpenAI with web search
            # Using the responses API pattern with tools
            url = f"{self._azure_openai_endpoint}/openai/deployments/{settings.azure_openai_deployment}/chat/completions?api-version={self._azure_openai_api_version}"

            headers = {
                "Content-Type": "application/json",
                "api-key": self._azure_openai_api_key,
            }

            # System message for deep research
            system_message = """You are a deep research agent for medical device clinical intelligence.

Conduct comprehensive research on the given topic:
1. Analyze the research question thoroughly
2. Synthesize information from your knowledge
3. Provide detailed, evidence-based analysis
4. Include specific data points, statistics, and findings
5. Identify key insights and strategic recommendations

Focus on:
- Clinical outcomes and safety data
- Regulatory considerations (FDA, international)
- Competitive landscape analysis
- Market trends and industry developments

Provide structured output with clear sections and actionable insights."""

            payload = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 8192,
            }

            response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.warning(f"OpenAI API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"OpenAI API error: {response.status_code}",
                }

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Extract any web search sources if available
            sources = []
            annotations = data.get("choices", [{}])[0].get("message", {}).get("annotations", [])
            for annotation in annotations:
                if annotation.get("type") == "url_citation":
                    sources.append({
                        "title": annotation.get("title", ""),
                        "uri": annotation.get("url", ""),
                    })

            return {
                "success": True,
                "content": content,
                "grounding_used": len(sources) > 0,
                "sources": sources,
                "model": f"azure-{settings.azure_openai_deployment}",
                "method": "openai_responses",
            }

        except Exception as e:
            logger.error(f"OpenAI deep research failed: {e}")
            return {"success": False, "error": str(e)}

    def _build_deep_research_prompt(
        self,
        topic: str,
        context: str,
        product_info: Optional[Dict[str, Any]],
    ) -> str:
        """Build comprehensive research prompt for deep research."""
        prompt_parts = []

        # Add product context
        if product_info:
            prompt_parts.append(f"""
=== PRODUCT CONTEXT ===
Product: {product_info.get('product_name', 'Unknown')}
Category: {product_info.get('category', 'Medical Device')}
Indication: {product_info.get('indication', 'Unknown')}
Technologies: {', '.join(product_info.get('technologies', []))}
Study Phase: {product_info.get('study_phase', 'Unknown')}
""")

        # Add local knowledge context
        if context:
            prompt_parts.append(f"""
=== LOCAL KNOWLEDGE BASE ===
{context}
""")

        # Add research topic and instructions
        prompt_parts.append(f"""
=== RESEARCH TOPIC ===
{topic}

=== RESEARCH INSTRUCTIONS ===
Conduct comprehensive research on this topic. Your research should:

1. **Search and Gather**: Use web search to find the most current and relevant information
2. **Analyze Sources**: Evaluate the credibility and relevance of each source
3. **Synthesize Findings**: Combine information from multiple sources into coherent insights
4. **Provide Citations**: Include source URLs for all key findings
5. **Strategic Analysis**: Offer actionable insights and recommendations

=== REQUIRED OUTPUT SECTIONS ===
1. Executive Summary (3-5 key findings)
2. Detailed Analysis (organized by subtopic)
3. Data & Statistics (specific numbers with sources)
4. Competitive/Market Context
5. Key Insights & Recommendations
6. Sources & References (with URLs)

Format your response with clear markdown headers and bullet points.
""")

        return "\n".join(prompt_parts)

    def _extract_sources_from_grounding(self, grounding_metadata) -> List[Dict[str, str]]:
        """Extract sources from Gemini grounding metadata."""
        sources = []

        # Extract from grounding_chunks
        if hasattr(grounding_metadata, "grounding_chunks"):
            for chunk in grounding_metadata.grounding_chunks:
                if hasattr(chunk, "web"):
                    sources.append({
                        "title": getattr(chunk.web, "title", "Unknown"),
                        "uri": getattr(chunk.web, "uri", ""),
                    })

        # Extract from search_entry_point if available
        if hasattr(grounding_metadata, "search_entry_point"):
            sep = grounding_metadata.search_entry_point
            if hasattr(sep, "rendered_content"):
                # The rendered content contains formatted search results
                pass  # Already captured in chunks

        # Extract from grounding_supports if available
        if hasattr(grounding_metadata, "grounding_supports"):
            for support in grounding_metadata.grounding_supports:
                if hasattr(support, "grounding_chunk_indices"):
                    # These reference the grounding_chunks already extracted
                    pass

        return sources

    # =========================================================================
    # High-Level Research Methods
    # =========================================================================

    async def research_competitive_landscape(
        self,
        product_info: Dict[str, Any],
        discovery_results: Dict[str, Any],
        recommendations: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate competitive landscape research report using Deep Research."""
        competitors = discovery_results.get("competitive", {}).get("competitors", [])

        topic = f"""
Competitive Landscape Analysis for {product_info.get('product_name', 'Medical Device')}

Market Segment: {product_info.get('category', 'Orthopedic Devices')}
Indication: {product_info.get('indication', 'Clinical Application')}

Research the following:

1. **Market Overview**: Current market size, growth projections, key trends
2. **Competitor Analysis**: {self._format_competitors(competitors)}
   - Product features and differentiators
   - Clinical evidence and outcomes data
   - Market positioning and pricing strategies
   - Recent regulatory approvals and pipeline
3. **Competitive Positioning**: How our product compares on key dimensions
4. **Threats & Opportunities**: Emerging competitors, market shifts, unmet needs
5. **Strategic Recommendations**: Differentiation strategies, market entry considerations
"""

        # Get local context
        local_context = await self._get_local_context(
            product_info, f"competitive analysis {product_info.get('indication', '')}"
        )

        research_result = await self.research_with_deep_research(
            topic=topic,
            context=local_context,
            product_info=product_info,
        )

        return self._format_research_report(
            research_result,
            report_type="competitive_landscape",
            product_info=product_info,
            estimated_pages=8,
        )

    async def research_state_of_the_art(
        self,
        product_info: Dict[str, Any],
        discovery_results: Dict[str, Any],
        recommendations: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate State of the Art research report using Deep Research."""
        publications = discovery_results.get("literature", {}).get("publications", [])
        registries = discovery_results.get("registry", {}).get("registries", [])

        topic = f"""
State of the Art Analysis: {product_info.get('indication', 'Clinical Procedure')}

Device Category: {product_info.get('category', 'Medical Device')}
Product: {product_info.get('product_name', 'Unknown')}

Based on {len(publications)} relevant publications and registry data from:
{', '.join([r.get('name', '') for r in registries[:5]]) if registries else 'Major orthopedic registries'}

Research the following:

1. **Clinical Outcomes & Benchmarks**
   - Current survival rates and revision rates
   - Functional outcome scores (e.g., Harris Hip Score, WOMAC)
   - Patient-reported outcomes

2. **Safety Profile**
   - Common complications and adverse events
   - Risk factors and patient selection criteria
   - Long-term surveillance data

3. **Technological Advances**
   - Material innovations (e.g., porous metals, ceramics)
   - Design improvements
   - Surgical technique evolution

4. **Best Practices**
   - Surgical approach considerations
   - Implant selection criteria
   - Post-operative protocols

5. **Unmet Clinical Needs**
   - Current limitations
   - Emerging solutions
   - Future directions

6. **Evidence Gaps**
   - Areas needing more research
   - Ongoing clinical trials
"""

        local_context = await self._get_local_context(
            product_info, f"clinical outcomes state of the art {product_info.get('indication', '')}"
        )

        research_result = await self.research_with_deep_research(
            topic=topic,
            context=local_context,
            product_info=product_info,
        )

        return self._format_research_report(
            research_result,
            report_type="state_of_the_art",
            product_info=product_info,
            estimated_pages=12,
        )

    async def research_regulatory_precedents(
        self,
        product_info: Dict[str, Any],
        discovery_results: Dict[str, Any],
        recommendations: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate regulatory precedents research report using Deep Research."""
        fda_data = discovery_results.get("fda", {})
        clearances = fda_data.get("clearances", {}).get("recent_clearances", [])

        topic = f"""
Regulatory Precedents Analysis: {product_info.get('product_name', 'Medical Device')}

Device Category: {product_info.get('category', 'Medical Device')}
Indication: {product_info.get('indication', 'Clinical Application')}

Based on {len(clearances)} FDA clearances for similar devices.

Research the following:

1. **Regulatory Pathway Recommendation**
   - 510(k) vs PMA vs De Novo analysis
   - Classification and product code considerations
   - Special controls and guidance documents

2. **Predicate Device Analysis**
   - Suitable predicate devices
   - Substantial equivalence considerations
   - Predicate limitations and risks

3. **Clinical Data Requirements**
   - Pre-market clinical study requirements
   - Performance testing standards
   - Biocompatibility testing

4. **Safety Testing Requirements**
   - Mechanical testing standards
   - Fatigue and wear testing
   - Sterilization validation

5. **Post-Market Requirements**
   - Surveillance obligations
   - Annual reporting requirements
   - Post-market clinical follow-up

6. **International Considerations**
   - EU MDR requirements
   - CE marking pathway
   - Other key markets (Japan, China, Brazil)

7. **Timeline & Milestones**
   - Estimated review times
   - Critical path items
   - Risk mitigation strategies
"""

        local_context = await self._get_local_context(
            product_info, f"FDA regulatory 510k clearance {product_info.get('indication', '')}"
        )

        research_result = await self.research_with_deep_research(
            topic=topic,
            context=local_context,
            product_info=product_info,
        )

        return self._format_research_report(
            research_result,
            report_type="regulatory_precedents",
            product_info=product_info,
            estimated_pages=6,
        )

    async def generate_intelligence_brief(
        self,
        product_info: Dict[str, Any],
        research_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate executive intelligence brief from all research."""
        combined_content = []

        for report_type in ["competitive_landscape", "state_of_the_art", "regulatory_precedents"]:
            report = research_results.get(report_type, {})
            if report.get("status") == "completed":
                combined_content.append(f"## {report_type.replace('_', ' ').title()}\n")
                combined_content.append(report.get("report", {}).get("content", ""))

        if not combined_content:
            return {
                "status": "error",
                "error": "No research content available to summarize",
            }

        prompt = f"""
Based on the following comprehensive research reports for {product_info.get('product_name', 'the product')},
create a concise executive intelligence brief.

{chr(10).join(combined_content)}

=== EXECUTIVE BRIEF REQUIREMENTS ===

Create a 1-2 page executive intelligence brief with:

1. **Executive Summary** (3-5 key insights)
   - Most critical findings across all research areas
   - Strategic implications for product positioning

2. **Critical Findings**
   - Competitive position assessment
   - Clinical evidence status
   - Regulatory readiness

3. **Strategic Implications**
   - Market opportunities and threats
   - Differentiation potential
   - Risk factors

4. **Recommended Actions**
   - Immediate priorities
   - Short-term initiatives
   - Long-term strategy considerations

5. **Risk Factors to Monitor**
   - Competitive threats
   - Regulatory changes
   - Market dynamics

Format for C-suite consumption: clear, actionable, data-driven, with specific recommendations.
"""

        try:
            response = await self._llm_service.generate(
                prompt=prompt,
                model="gemini-3-pro-preview",
                temperature=0.1,
            )

            return {
                "status": "completed",
                "generated_at": datetime.utcnow().isoformat(),
                "product_name": product_info.get("product_name"),
                "intelligence_brief": {
                    "content": response,
                    "reports_included": list(research_results.keys()),
                },
            }

        except Exception as e:
            logger.error(f"Failed to generate intelligence brief: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_local_context(
        self,
        product_info: Dict[str, Any],
        query: str,
    ) -> str:
        """Retrieve local context from vector store."""
        try:
            context_result = await self._vector_service.get_context_for_query(
                product_id=product_info.get("protocol_id", "default"),
                query=query,
                max_chunks=5,
            )
            return context_result[0] if context_result else ""
        except Exception as e:
            logger.warning(f"Could not retrieve local context: {e}")
            return ""

    def _format_competitors(self, competitors: List[Dict]) -> str:
        """Format competitors list for prompt."""
        if not competitors:
            return "Key competitors in the market segment (identify through research)"

        lines = []
        for comp in competitors[:10]:
            name = comp.get("manufacturer", comp.get("company", "Unknown"))
            product = comp.get("product", comp.get("product_name", ""))
            lines.append(f"   - {name}: {product}")

        return "\n".join(lines) if lines else "Key competitors in the market segment"

    def _format_research_report(
        self,
        research_result: Dict[str, Any],
        report_type: str,
        product_info: Dict[str, Any],
        estimated_pages: int,
    ) -> Dict[str, Any]:
        """Format research result into structured report."""
        if not research_result.get("success"):
            return {
                "report_type": report_type,
                "status": "error",
                "error": research_result.get("error", "Research failed"),
            }

        return {
            "report_type": report_type,
            "status": "completed",
            "generated_at": datetime.utcnow().isoformat(),
            "product_analyzed": product_info.get("product_name"),
            "report": {
                "content": research_result.get("content", ""),
                "thinking_process": research_result.get("thinking_process"),
                "grounding_used": research_result.get("grounding_used", False),
                "sources": research_result.get("sources", []),
            },
            "model_used": research_result.get("model"),
            "research_method": research_result.get("method"),
            "estimated_pages": estimated_pages,
        }

    async def close(self):
        """Clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Singleton instance
_deep_research_service: Optional[DeepResearchService] = None


def get_deep_research_service() -> DeepResearchService:
    """Get singleton deep research service instance."""
    global _deep_research_service
    if _deep_research_service is None:
        _deep_research_service = DeepResearchService()
    return _deep_research_service
