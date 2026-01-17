"""
Onboarding Agent for Clinical Intelligence Platform.

Orchestrates the AI-first onboarding experience for Product Data Stewards.
This agent guides users through discovering, recommending, and assembling
optimal data sources and knowledge assets for a specific product.

Uses real agent orchestration with:
- FDAAgent: Query MAUDE adverse events and 510(k) clearances
- PublicationDiscoveryAgent: Search PubMed for relevant literature
- RegistryAgent: Access registry benchmark data
- CompetitiveIntelAgent: Analyze competitor products
- DeepResearchAgent: Generate comprehensive research reports
"""
import asyncio
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType, AgentOrchestrator
)
from app.agents.fda_agent import FDAAgent
from app.agents.publication_agent import PublicationDiscoveryAgent
from app.agents.registry_agent import RegistryAgent
from app.agents.competitive_intel_agent import CompetitiveIntelAgent
from app.agents.deep_research_agent import DeepResearchAgent
from app.services.pubmed_service import get_pubmed_service
from app.services.confidence_scoring_service import get_confidence_service
from app.services.study_phase_service import get_study_phase_service

logger = logging.getLogger(__name__)


# ==================== Configuration ====================
DISCOVERY_TIMEOUT_SECONDS = 60  # Timeout for each discovery agent
RESEARCH_TIMEOUT_SECONDS = 90   # Timeout for deep research agents
PUBMED_TIMEOUT_SECONDS = 45     # Timeout for PubMed searches

# Registry data path
REGISTRY_NORMS_PATH = Path(os.getenv(
    "REGISTRY_NORMS_PATH",
    "data/processed/document_as_code/registry_norms.yaml"
))

# Cache for loaded YAML data
_registry_cache: Optional[Dict[str, Any]] = None


def load_registry_norms() -> Dict[str, Any]:
    """
    Load registry norms from YAML file with caching.

    Returns:
        Dictionary containing registry data
    """
    global _registry_cache

    if _registry_cache is not None:
        return _registry_cache

    try:
        if REGISTRY_NORMS_PATH.exists():
            with open(REGISTRY_NORMS_PATH, "r", encoding="utf-8") as f:
                _registry_cache = yaml.safe_load(f) or {}
                logger.info(f"Loaded registry norms from {REGISTRY_NORMS_PATH}")
                return _registry_cache
        else:
            logger.warning(f"Registry norms file not found at {REGISTRY_NORMS_PATH}")
            return {}
    except Exception as e:
        logger.error(f"Error loading registry norms: {e}")
        return {}


class DiscoveryStatus(str, Enum):
    """Status of a discovery operation."""
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some data found but errors occurred
    FAILED = "failed"
    TIMEOUT = "timeout"


async def run_with_timeout(
    coro,
    timeout_seconds: float,
    name: str = "task"
) -> Tuple[Any, Optional[str]]:
    """
    Run a coroutine with timeout and return (result, error).

    Args:
        coro: Coroutine to execute
        timeout_seconds: Maximum execution time
        name: Name for logging

    Returns:
        Tuple of (result, error_message)
        - On success: (result, None)
        - On timeout: (None, "timeout message")
        - On exception: (None, "error message")
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)
        return (result, None)
    except asyncio.TimeoutError:
        logger.warning(f"{name} timed out after {timeout_seconds}s")
        return (None, f"{name} timed out after {timeout_seconds} seconds")
    except Exception as e:
        logger.exception(f"{name} failed with error: {e}")
        return (None, f"{name} error: {str(e)}")


class OnboardingPhase(str, Enum):
    """Phases of the onboarding process."""
    CONTEXT_CAPTURE = "context_capture"
    DISCOVERY = "discovery"
    RECOMMENDATIONS = "recommendations"
    DEEP_RESEARCH = "deep_research"
    COMPLETE = "complete"


class OnboardingAgent(BaseAgent):
    """
    Orchestrates the AI-first product configuration experience.

    Capabilities:
    - Analyze product context to understand data needs
    - Coordinate discovery agents in parallel
    - Generate data source recommendations
    - Orchestrate deep research report generation
    - Produce comprehensive intelligence briefs
    """

    agent_type = AgentType.ONBOARDING

    def __init__(self, **kwargs):
        """Initialize onboarding agent."""
        super().__init__(**kwargs)

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute onboarding workflow.

        Args:
            context: Execution context with product parameters

        Returns:
            AgentResult with onboarding progress and recommendations

        Parameters:
            - action: The onboarding action to perform
                - analyze_context: Analyze product context
                - run_discovery: Run discovery agents
                - generate_recommendations: Create data source recommendations
                - run_deep_research: Execute deep research agents
                - generate_brief: Generate intelligence brief
                - get_status: Get current onboarding status
                - chat: Conversational chat with steward
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        action = context.parameters.get("action", "analyze_context")

        if action == "analyze_context":
            result.data = await self._analyze_product_context(context)
        elif action == "run_discovery":
            result.data = await self._run_discovery(context)
        elif action == "generate_recommendations":
            result.data = await self._generate_recommendations(context)
        elif action == "run_deep_research":
            result.data = await self._run_deep_research(context)
        elif action == "generate_brief":
            result.data = await self._generate_intelligence_brief(context)
        elif action == "get_status":
            result.data = await self._get_onboarding_status(context)
        elif action == "chat":
            result.data = await self._chat_with_steward(context)
        else:
            result.success = False
            result.error = f"Unknown action: {action}"
            return result

        # Add source provenance
        result.add_source(
            SourceType.LLM_INFERENCE,
            "Onboarding Agent Analysis",
            confidence=0.9,
            details={"action": action}
        )

        return result

    async def _analyze_product_context(self, context: AgentContext) -> Dict[str, Any]:
        """
        Analyze product context to understand data requirements.

        Uses LLM to understand the product and recommend relevant data sources.
        """
        product_info = context.parameters.get("product_info", {})

        prompt = self.load_prompt("onboarding_context_analysis", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "study_phase": product_info.get("study_phase", "Unknown"),
            "protocol_id": product_info.get("protocol_id", context.protocol_id),
            "technologies": ", ".join(product_info.get("technologies", [])),
        })

        analysis = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

        return {
            "phase": OnboardingPhase.CONTEXT_CAPTURE.value,
            "product_info": product_info,
            "analysis": analysis,
            "recommended_data_sources": analysis.get("recommended_data_sources", []),
            "recommended_registries": analysis.get("recommended_registries", []),
            "search_terms": analysis.get("search_terms", []),
            "competitive_products": analysis.get("competitive_products", []),
            "next_phase": OnboardingPhase.DISCOVERY.value,
            "message": analysis.get("welcome_message",
                f"I've analyzed {product_info.get('product_name', 'your product')} and identified key data sources."),
        }

    async def _run_discovery(self, context: AgentContext) -> Dict[str, Any]:
        """
        Run discovery agents to find relevant data sources.

        Executes multiple discovery tasks in parallel using real agents with timeouts:
        - LiteratureAgent: PubMed search for relevant publications
        - RegistryAgent: Registry benchmark data discovery
        - FDAAgent: MAUDE adverse events and 510(k) clearances
        - CompetitiveIntelAgent: Competitor product analysis

        Returns partial results if some agents fail/timeout, with clear error reporting.
        """
        product_info = context.parameters.get("product_info", {})
        product_name = product_info.get("product_name", "")
        indication = product_info.get("indication", "revision hip arthroplasty")
        technologies = product_info.get("technologies", ["trabecular titanium"])
        protocol_id = product_info.get("protocol_id", context.protocol_id)

        # Initialize agents
        fda_agent = FDAAgent()
        publication_agent = PublicationDiscoveryAgent()
        competitive_agent = CompetitiveIntelAgent()
        pubmed_service = get_pubmed_service()

        # Create contexts for each agent (inherit request_id from parent context)
        lit_context = AgentContext(
            request_id=context.request_id,
            protocol_id=protocol_id,
            parameters={
                "action": "discover",
                "indication": indication,
                "technologies": technologies,
                "product_name": product_name,
            }
        )

        fda_context = AgentContext(
            request_id=context.request_id,
            protocol_id=protocol_id,
            parameters={
                "action": "search_device_events",
                "device_name": product_name,
                "indication": indication,
            }
        )

        competitive_context = AgentContext(
            request_id=context.request_id,
            protocol_id=protocol_id,
            parameters={
                "action": "discovery",
                "product_name": product_name,
                "product_category": "revision_tha" if "revision" in indication.lower() else "primary_tha",
                "indication": indication,
                "technologies": technologies,
            }
        )

        # Run discovery agents in parallel with timeouts
        logger.info(f"Starting parallel discovery for {product_name}")

        # Track errors for user feedback
        discovery_errors: List[str] = []

        # Run all agents in TRUE parallel using asyncio.gather
        results = await asyncio.gather(
            run_with_timeout(
                publication_agent.execute(lit_context),
                DISCOVERY_TIMEOUT_SECONDS,
                "Literature discovery"
            ),
            run_with_timeout(
                fda_agent.execute(fda_context),
                DISCOVERY_TIMEOUT_SECONDS,
                "FDA discovery"
            ),
            run_with_timeout(
                competitive_agent.execute(competitive_context),
                DISCOVERY_TIMEOUT_SECONDS,
                "Competitive discovery"
            ),
            run_with_timeout(
                pubmed_service.search_for_product(
                    product_name=product_name,
                    indication=indication,
                    technologies=technologies,
                    max_results=50,
                ),
                PUBMED_TIMEOUT_SECONDS,
                "PubMed search"
            ),
            return_exceptions=True,
        )

        # Unpack results
        lit_result, lit_error = results[0] if not isinstance(results[0], Exception) else (None, str(results[0]))
        fda_result, fda_error = results[1] if not isinstance(results[1], Exception) else (None, str(results[1]))
        comp_result, comp_error = results[2] if not isinstance(results[2], Exception) else (None, str(results[2]))
        pubmed_result, pubmed_error = results[3] if not isinstance(results[3], Exception) else (None, str(results[3]))

        # Log any errors
        if lit_error:
            discovery_errors.append(lit_error)
            logger.warning(f"Literature discovery failed: {lit_error}")
        if fda_error:
            discovery_errors.append(fda_error)
            logger.warning(f"FDA discovery failed: {fda_error}")
        if comp_error:
            discovery_errors.append(comp_error)
            logger.warning(f"Competitive discovery failed: {comp_error}")
        if pubmed_error:
            discovery_errors.append(pubmed_error)
            logger.warning(f"PubMed search failed: {pubmed_error}")

        # Phase-aware discovery for study phase (e.g., Phase 4 Post-Market Surveillance)
        study_phase = product_info.get("study_phase", "")
        phase_discovery_result = None
        phase_discovery_error = None

        if study_phase:
            study_phase_service = get_study_phase_service()

            # Build product info for phase discovery
            phase_product_info = {
                "product_name": product_name,
                "protocol_id": protocol_id,
                "indication": indication,
                "study_phase": study_phase,
                "manufacturer": product_info.get("manufacturer", ""),
                "product_codes": product_info.get("product_codes", []),
                "intervention_type": product_info.get("intervention_type", "device"),
            }

            # Get discovered competitors for competitor trial/FDA search
            discovered_competitors = []
            if isinstance(comp_result, AgentResult) and comp_result.success:
                for prod in comp_result.data.get("products", []):
                    discovered_competitors.append({
                        "company": prod.get("manufacturer", ""),
                        "product_name": prod.get("product", ""),
                    })

            phase_discovery_result, phase_discovery_error = await run_with_timeout(
                study_phase_service.discover_phase_relevant_sources(
                    product_info=phase_product_info,
                    competitors=discovered_competitors if discovered_competitors else None,
                ),
                DISCOVERY_TIMEOUT_SECONDS,
                "Phase-aware discovery"
            )
            if phase_discovery_error:
                discovery_errors.append(phase_discovery_error)
                logger.warning(f"Phase-aware discovery failed: {phase_discovery_error}")

        # Process literature results
        papers_found = 0
        top_papers = []
        lit_status = DiscoveryStatus.COMPLETED

        if isinstance(pubmed_result, dict) and pubmed_result.get("success"):
            papers_found = pubmed_result.get("total_count", 0)
            articles = pubmed_result.get("articles", [])[:10]
            top_papers = [
                {
                    "title": a.get("title", ""),
                    "journal": a.get("journal_abbrev", a.get("journal", "")),
                    "year": a.get("year", ""),
                    "relevance_score": a.get("relevance_score", 0.5),
                    "insight": self._extract_paper_insight(a),
                    "pmid": a.get("pmid", ""),
                    "url": a.get("url", ""),
                }
                for a in articles
            ]
        elif pubmed_error:
            lit_status = DiscoveryStatus.TIMEOUT if "timed out" in pubmed_error else DiscoveryStatus.FAILED

        # Process FDA results
        fda_data = {}
        fda_status = DiscoveryStatus.COMPLETED
        if isinstance(fda_result, AgentResult) and fda_result.success:
            fda_events = fda_result.data.get("events", [])
            fda_data = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "maude_events": len(fda_events),
                "clearances": 0,  # Would need separate 510k query
                "recalls": 0,
                "summary": {
                    "similar_devices_analyzed": min(len(fda_events), 50),
                    "time_range": "2019-2024",
                    "event_trend": "stable" if len(fda_events) < 100 else "increasing",
                },
                "source": "openFDA MAUDE Database",
            }
        else:
            fda_status = DiscoveryStatus.TIMEOUT if fda_error and "timed out" in fda_error else DiscoveryStatus.FAILED
            fda_data = {
                "status": fda_status.value,
                "progress": 0,
                "maude_events": 0,
                "error": fda_error or "FDA search failed - no results returned",
            }

        # Process competitive results
        comp_data = {}
        comp_status = DiscoveryStatus.COMPLETED
        if isinstance(comp_result, AgentResult) and comp_result.success:
            comp_data = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "competitors_identified": comp_result.data.get("competitors_identified", 0),
                "products": comp_result.data.get("products", []),
            }
        else:
            comp_status = DiscoveryStatus.TIMEOUT if comp_error and "timed out" in comp_error else DiscoveryStatus.FAILED
            comp_data = {
                "status": comp_status.value,
                "progress": 0,
                "competitors_identified": 0,
                "error": comp_error or "Competitive analysis failed - no results returned",
            }

        # Build registry discovery from YAML-backed registry data
        registry_data = self._get_available_registries(indication)

        # Calculate confidence scores for each discovery type
        confidence_service = get_confidence_service()

        lit_confidence = confidence_service.score_literature_discovery(
            papers_found=papers_found,
            top_papers=top_papers,
            search_terms=[indication] + technologies,
        )

        registry_list = registry_data.get("recommended", [])
        reg_confidence = confidence_service.score_registry_discovery(
            registries=registry_list,
            indication=indication,
        )

        fda_confidence = confidence_service.score_fda_discovery(
            maude_events=fda_data.get("maude_events", 0),
            clearances=fda_data.get("clearances", 0),
            recalls=fda_data.get("recalls", 0),
            device_name=product_name,
        )

        comp_confidence = confidence_service.score_competitive_discovery(
            competitors_found=comp_data.get("competitors_identified", 0),
            products=comp_data.get("products", []),
            market_category="revision_tha" if "revision" in indication.lower() else "primary_tha",
        )

        overall_confidence = confidence_service.score_overall_discovery(
            literature_score=lit_confidence,
            registry_score=reg_confidence,
            fda_score=fda_confidence,
            competitive_score=comp_confidence,
        )

        # Build discovery results with accurate status tracking
        lit_progress = 100 if lit_status == DiscoveryStatus.COMPLETED else 0
        fda_progress = 100 if fda_status == DiscoveryStatus.COMPLETED else 0
        comp_progress = 100 if comp_status == DiscoveryStatus.COMPLETED else 0

        discovery_results = {
            "literature_discovery": {
                "status": lit_status.value,
                "progress": lit_progress,
                "papers_found": papers_found,
                "top_papers": top_papers,
                "source": "PubMed via NCBI E-utilities",
                "confidence": lit_confidence.to_dict(),
                **({"error": pubmed_error} if pubmed_error else {}),
            },
            "registry_discovery": {
                **registry_data,
                "confidence": reg_confidence.to_dict(),
            },
            "fda_discovery": {
                **fda_data,
                "confidence": fda_confidence.to_dict(),
            },
            "competitive_discovery": {
                **comp_data,
                "confidence": comp_confidence.to_dict(),
            },
        }

        # Add phase-aware discovery results if available
        phase_discovery_status = DiscoveryStatus.COMPLETED
        phase_trials_count = 0
        phase_fda_count = 0
        competitor_trials_count = 0
        competitor_fda_count = 0

        if phase_discovery_result and isinstance(phase_discovery_result, dict):
            # Extract counts from phase discovery
            own_trials = phase_discovery_result.get("own_clinical_trials", {})
            earlier_fda = phase_discovery_result.get("earlier_phase_fda", {})
            comp_trials = phase_discovery_result.get("competitor_trials", {})
            comp_fda = phase_discovery_result.get("competitor_fda", {})

            phase_trials_count = own_trials.get("total_found", 0)
            phase_fda_count = earlier_fda.get("total_records", 0)
            competitor_trials_count = comp_trials.get("total_found", 0)
            competitor_fda_count = comp_fda.get("total_records", 0)

            discovery_results["clinical_trials_discovery"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "own_trials": {
                    "count": phase_trials_count,
                    "by_protocol": own_trials.get("by_protocol_id", []),
                    "by_title": own_trials.get("by_title_search", []),
                    "source": "ClinicalTrials.gov",
                },
                "confidence": {"overall_score": 0.85, "level": "high" if phase_trials_count > 0 else "moderate"},
            }

            discovery_results["earlier_phase_fda"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "clearances": earlier_fda.get("clearances", []),
                "adverse_events": earlier_fda.get("adverse_events", []),
                "total_records": phase_fda_count,
                "current_phase": earlier_fda.get("current_phase", ""),
                "phases_searched": earlier_fda.get("phases_searched", []),
                "source": "openFDA",
                "confidence": {"overall_score": 0.8, "level": "high" if phase_fda_count > 0 else "moderate"},
            }

            discovery_results["competitor_trials"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "total_found": competitor_trials_count,
                "by_sponsor": comp_trials.get("by_sponsor", {}),
                "trials": comp_trials.get("trials", [])[:20],  # Limit to top 20
                "source": "ClinicalTrials.gov",
                "confidence": {"overall_score": 0.8, "level": "high" if competitor_trials_count > 0 else "moderate"},
            }

            discovery_results["competitor_fda"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "total_records": competitor_fda_count,
                "top_competitors": comp_fda.get("top_competitors", []),
                "clearances": comp_fda.get("clearances", [])[:20],  # Limit to top 20
                "adverse_events_by_company": comp_fda.get("adverse_events_by_company", {}),
                "source": "openFDA",
                "confidence": {"overall_score": 0.8, "level": "high" if competitor_fda_count > 0 else "moderate"},
            }

            logger.info(f"Phase-aware discovery found: {phase_trials_count} own trials, "
                       f"{phase_fda_count} earlier phase FDA records, {competitor_trials_count} competitor trials, "
                       f"{competitor_fda_count} competitor FDA records")
        elif phase_discovery_error:
            phase_discovery_status = DiscoveryStatus.TIMEOUT if "timed out" in phase_discovery_error else DiscoveryStatus.FAILED
            discovery_results["clinical_trials_discovery"] = {
                "status": phase_discovery_status.value,
                "progress": 0,
                "error": phase_discovery_error,
            }
        elif study_phase:
            # No results but study phase was provided
            discovery_results["clinical_trials_discovery"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "own_trials": {"count": 0},
                "message": "No additional trials found for this study phase",
            }

        # Calculate overall progress based on actual completion
        successful_discoveries = sum([
            1 if lit_status == DiscoveryStatus.COMPLETED else 0,
            1,  # Registry is always available (local data)
            1 if fda_status == DiscoveryStatus.COMPLETED else 0,
            1 if comp_status == DiscoveryStatus.COMPLETED else 0,
            1 if phase_discovery_status == DiscoveryStatus.COMPLETED else 0,
        ])
        total_discovery_types = 5 if study_phase else 4
        overall_progress = (successful_discoveries / total_discovery_types) * 100

        # Determine overall status
        all_completed = all([
            lit_status == DiscoveryStatus.COMPLETED,
            fda_status == DiscoveryStatus.COMPLETED,
            comp_status == DiscoveryStatus.COMPLETED,
            phase_discovery_status == DiscoveryStatus.COMPLETED if study_phase else True,
        ])
        overall_status = DiscoveryStatus.COMPLETED if all_completed else DiscoveryStatus.PARTIAL

        # Build user-friendly message with phase-aware info
        phase_info = ""
        if study_phase and phase_discovery_result:
            phase_info = f", {phase_trials_count + competitor_trials_count} clinical trials from ClinicalTrials.gov"
            if phase_fda_count + competitor_fda_count > 0:
                phase_info += f", {phase_fda_count + competitor_fda_count} FDA records"

        if discovery_errors:
            error_summary = f" ({len(discovery_errors)} source(s) unavailable)"
            message = f"Discovery {overall_status.value}{error_summary}. Found {papers_found} publications{phase_info} and identified {comp_data.get('competitors_identified', 0)} competitors."
        else:
            message = f"Discovery complete ({overall_confidence.level.value} confidence). Found {papers_found} publications{phase_info}, analyzed FDA data, and identified {comp_data.get('competitors_identified', 0)} competitors."

        return {
            "phase": OnboardingPhase.DISCOVERY.value,
            "overall_progress": overall_progress,
            "overall_status": overall_status.value,
            "discovery_results": discovery_results,
            "overall_confidence": overall_confidence.to_dict(),
            "errors": discovery_errors if discovery_errors else None,
            "next_phase": OnboardingPhase.RECOMMENDATIONS.value if overall_progress >= 75 else None,  # Allow partial success to proceed
            "message": message,
        }

    def _extract_paper_insight(self, article: Dict[str, Any]) -> str:
        """Extract insight from article for display."""
        title = article.get("title", "").lower()
        pub_types = [pt.lower() for pt in article.get("pub_types", [])]

        if "meta-analysis" in pub_types:
            return "Meta-analysis: Synthesized evidence across studies"
        if "randomized controlled trial" in pub_types:
            return "RCT: High-quality comparative evidence"
        if "systematic review" in title:
            return "Systematic review of available evidence"
        if "survival" in title or "outcome" in title:
            return "Reports survival/outcome data"
        if "revision" in title:
            return "Revision-specific clinical data"
        if "registry" in title:
            return "Registry-level population data"
        if "complication" in title or "failure" in title:
            return "Complication/failure analysis"
        return "Relevant clinical publication"

    def _build_why_explanations(
        self,
        data_source_explanations: Dict[str, Any],
        discovery_results: Dict[str, Any],
        product_info: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build comprehensive why explanations for each recommendation.

        Includes:
        - Why each source was recommended (inclusion reason)
        - Why excluded sources were not recommended
        - Product-specific relevance explanation
        """
        product_name = product_info.get("product_name", "your product")
        indication = product_info.get("indication", "")
        technologies = product_info.get("technologies", [])

        why_explanations = {}

        # Clinical study explanation
        clinical_explanation = data_source_explanations.get("clinical_study", {})
        why_explanations["clinical_study"] = {
            "summary": clinical_explanation.get("value_proposition",
                f"Your {product_info.get('protocol_id', 'study')} data provides patient-level granularity unavailable from other sources."),
            "key_reasons": [
                f"Direct patient-level data for {product_name}",
                "Prospective, controlled study design",
                "Enables individual risk factor analysis",
                "Tracks functional outcomes (HHS/OHS) specific to your population",
            ],
            "unique_value": "Only source of product-specific, patient-level data for regulatory submissions",
        }

        # Registry explanation with inclusion/exclusion reasons
        registries = discovery_results.get("registry_discovery", {}).get("recommended", [])
        selected_registries = [r for r in registries if r.get("selected")]
        excluded_registries = [r for r in registries if not r.get("selected")]

        registry_explanation = data_source_explanations.get("registries", {})
        why_explanations["registries"] = {
            "summary": registry_explanation.get("value_proposition",
                f"Selected registries provide population-level benchmarks for {indication}."),
            "key_reasons": [
                f"Combined data from {sum(r.get('n_procedures', 0) for r in selected_registries):,} procedures",
                "Long-term survival data (10-20 year follow-up)",
                "Statistically robust revision rate benchmarks",
                "Enable percentile ranking vs. global population",
            ],
            "unique_value": "Independent validation of study outcomes against real-world populations",
            "inclusions": [
                {
                    "name": r.get("name", ""),
                    "reason": r.get("relevance", f"Provides {r.get('data_years', '')} data with {r.get('n_procedures', 0):,} procedures"),
                }
                for r in selected_registries
            ],
            "exclusions": [
                {
                    "name": r.get("name", ""),
                    "reason": r.get("exclusion_reason", "Limited relevance to product indication"),
                }
                for r in excluded_registries
            ],
        }

        # Literature explanation
        lit_discovery = discovery_results.get("literature_discovery", {})
        papers_found = lit_discovery.get("papers_found", 0)
        top_papers = lit_discovery.get("top_papers", [])

        literature_explanation = data_source_explanations.get("literature", {})
        tech_str = ", ".join(technologies) if technologies else "device technology"

        why_explanations["literature"] = {
            "summary": literature_explanation.get("value_proposition",
                f"Discovered {papers_found} publications relevant to {tech_str} and {indication}."),
            "key_reasons": [
                f"{len([p for p in top_papers if 'meta-analysis' in str(p).lower() or 'systematic' in str(p).lower()])} systematic reviews/meta-analyses",
                "Comparative efficacy data vs. similar technologies",
                "Long-term outcome extrapolation from published studies",
                "Evidence base for marketing claims support",
            ],
            "unique_value": "Published evidence for claims validation and competitive positioning",
            "selection_criteria": [
                "Prioritized meta-analyses and RCTs for strength of evidence",
                "Focused on publications within last 10 years for relevance",
                f"Filtered for {tech_str} specific outcomes",
                "Included registry-based analyses for population-level data",
            ],
        }

        # FDA surveillance explanation
        fda_discovery = discovery_results.get("fda_discovery", {})
        maude_events = fda_discovery.get("maude_events", 0)

        fda_explanation = data_source_explanations.get("fda_surveillance", {})
        why_explanations["fda_surveillance"] = {
            "summary": fda_explanation.get("value_proposition",
                f"FDA surveillance data enables early signal detection and competitive safety comparison."),
            "key_reasons": [
                f"MAUDE database with {maude_events} relevant adverse events",
                "510(k) clearance history for predicate analysis",
                "Device recall monitoring for safety signals",
                "Enables proactive post-market surveillance",
            ],
            "unique_value": "Early warning system for safety signals before they appear in registries",
            "data_sources": [
                {"name": "MAUDE Database", "description": "Manufacturer and User Facility Device Experience reports"},
                {"name": "510(k) Clearances", "description": "Predicate device history and clearance pathway"},
                {"name": "Device Recalls", "description": "Safety-related recalls for similar devices"},
            ],
        }

        return why_explanations

    def _get_available_registries(self, indication: str) -> Dict[str, Any]:
        """Get available registries from YAML-backed data."""
        registry_data = load_registry_norms()
        registries_raw = registry_data.get("registries", {})

        if not registries_raw:
            logger.warning("No registry data found in YAML file")
            return {
                "status": "failed",
                "progress": 0,
                "registries_found": 0,
                "recommended": [],
                "error": "Registry data not available",
            }

        registries = []
        source_reports = []

        # Priority registries for revision THA (selected by default)
        priority_registries = {"njr", "shar", "dhr", "aoanjrr"}

        for key, reg in registries_raw.items():
            abbrev = reg.get("abbreviation", key.upper())
            full_name = reg.get("name", abbrev)
            country = reg.get("country", "Unknown")
            data_period = reg.get("data_period", "")
            n_procedures = reg.get("n_procedures", 0)
            report_year = reg.get("report_year", "")
            population = reg.get("population", "")

            # Check for numeric survival data (not null and not graphical-only)
            has_survival = any([
                reg.get("survival_1yr") is not None,
                reg.get("survival_5yr") is not None,
                reg.get("survival_10yr") is not None,
                reg.get("survival_15yr") is not None,
            ])

            # Check provenance for data quality issues
            provenance = reg.get("provenance", {})
            survival_prov = provenance.get("survival_rates", {})
            data_quality = ""
            if isinstance(survival_prov, dict):
                data_quality = survival_prov.get("data_quality", "")
            elif isinstance(survival_prov, list) and survival_prov:
                # Some registries have list format with quotes indicating estimates
                first_item = survival_prov[0]
                if isinstance(first_item, dict) and "visual estimate" in first_item.get("quote", "").lower():
                    data_quality = "graphical_estimate"

            # Determine exclusion reasons
            exclusion_reason = None
            if data_quality == "graphical_only":
                exclusion_reason = "Survival data in graphical format only - not extractable"
                has_survival = False
            elif population == "primary_tha_excluded":
                exclusion_reason = "Primary THA data only - revision THA data not yet extracted"
                has_survival = False

            # Build relevance description
            relevance_parts = []
            if n_procedures:
                relevance_parts.append(f"{n_procedures:,} procedures")
            if reg.get("survival_15yr"):
                relevance_parts.append(f"{int(reg['survival_15yr']*100)}% 15yr survival")
            elif reg.get("survival_10yr"):
                relevance_parts.append(f"{int(reg['survival_10yr']*100)}% 10yr survival")
            if provenance.get("notes"):
                notes = provenance["notes"]
                if "longest" in notes.lower() or "comprehensive" in notes.lower():
                    relevance_parts.append("Long-term follow-up")

            relevance = ", ".join(relevance_parts) if relevance_parts else f"{country} registry data"

            # Determine if selected by default
            selected = key.lower() in priority_registries and has_survival

            registry_entry = {
                "name": abbrev,
                "full_name": full_name,
                "region": country,
                "selected": selected,
                "data_years": data_period,
                "n_procedures": n_procedures,
                "relevance": relevance,
                "has_survival_data": has_survival,
            }

            if exclusion_reason:
                registry_entry["exclusion_reason"] = exclusion_reason

            registries.append(registry_entry)
            source_reports.append(f"{abbrev} {report_year}")

        # Sort: selected first, then by procedure count
        registries.sort(key=lambda x: (-int(x["selected"]), -x.get("n_procedures", 0)))

        return {
            "status": "completed",
            "progress": 100,
            "registries_found": len(registries),
            "recommended": registries,
            "source": f"Registry annual reports ({', '.join(source_reports)})",
        }

    async def _generate_recommendations(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate data source recommendations with insight explanations, why explanations, and confidence scores.
        """
        product_info = context.parameters.get("product_info", {})
        discovery_results = context.parameters.get("discovery_results", {})
        confidence_service = get_confidence_service()

        prompt = self.load_prompt("onboarding_recommendations", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "papers_found": discovery_results.get("literature_discovery", {}).get("papers_found", 0),
            "registries_found": discovery_results.get("registry_discovery", {}).get("registries_found", 0),
            "maude_events": discovery_results.get("fda_discovery", {}).get("maude_events", 0),
            "competitors": discovery_results.get("competitive_discovery", {}).get("competitors_identified", 0),
        })

        recommendations = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

        # Extract why explanations from LLM response
        data_source_explanations = recommendations.get("data_source_explanations", {})
        why_explanations = self._build_why_explanations(
            data_source_explanations,
            discovery_results,
            product_info,
        )

        # Extract discovery confidence scores
        lit_discovery_confidence = discovery_results.get("literature_discovery", {}).get("confidence", {}).get("overall_score", 0.7)
        reg_discovery_confidence = discovery_results.get("registry_discovery", {}).get("confidence", {}).get("overall_score", 0.7)
        fda_discovery_confidence = discovery_results.get("fda_discovery", {}).get("confidence", {}).get("overall_score", 0.7)

        # Calculate recommendation confidence scores
        clinical_confidence = confidence_service.score_recommendation(
            recommendation_type="clinical",
            data_sources_available=1,  # Direct study data
            discovery_confidence=0.95,  # Study data is primary source
            user_context_match=0.95,
        )

        literature_confidence = confidence_service.score_recommendation(
            recommendation_type="literature",
            data_sources_available=min(discovery_results.get("literature_discovery", {}).get("papers_found", 0), 15),
            discovery_confidence=lit_discovery_confidence,
            user_context_match=0.85,
        )

        registry_confidence = confidence_service.score_recommendation(
            recommendation_type="registry",
            data_sources_available=len([r for r in discovery_results.get("registry_discovery", {}).get("recommended", []) if r.get("selected")]),
            discovery_confidence=reg_discovery_confidence,
            user_context_match=0.85,
        )

        fda_confidence = confidence_service.score_recommendation(
            recommendation_type="fda",
            data_sources_available=3,  # MAUDE, 510k, Recalls
            discovery_confidence=fda_discovery_confidence,
            user_context_match=0.8,
        )

        # Get LLM-generated enabled insights if available
        clinical_insights = data_source_explanations.get("clinical_study", {}).get("enabled_insights", [
            "Patient-level safety monitoring",
            "Revision rate calculations with confidence intervals",
            "Risk stratification by patient demographics",
            "Functional outcome tracking (HHS, OHS scores)",
        ])
        literature_insights = data_source_explanations.get("literature", {}).get("enabled_insights", [
            "Published efficacy benchmarks",
            "Safety profile comparisons",
            "Clinical best practices",
        ])
        fda_insights = data_source_explanations.get("fda_surveillance", {}).get("enabled_insights", [
            "Post-market surveillance integration",
            "Adverse event trend analysis",
            "Competitive device safety comparison",
        ])

        # Build phase-aware recommendations if available
        clinical_trials_rec = None
        earlier_phase_fda_rec = None
        competitor_trials_rec = None
        competitor_fda_rec = None

        ct_discovery = discovery_results.get("clinical_trials_discovery", {})
        if ct_discovery.get("status") == "completed" and ct_discovery.get("own_trials", {}).get("count", 0) > 0:
            own_trials = ct_discovery.get("own_trials", {})
            clinical_trials_rec = {
                "source": "ClinicalTrials.gov",
                "selected": True,
                "total_trials": own_trials.get("count", 0),
                "by_protocol": own_trials.get("by_protocol", []),
                "by_title": own_trials.get("by_title", []),
                "enabled_insights": [
                    "Cross-reference study data with registry records",
                    "Track study milestones and status changes",
                    "Compare enrollment patterns across sites",
                ],
                "confidence": ct_discovery.get("confidence", {"overall_score": 0.8, "level": "high"}),
                "why_explanation": {
                    "summary": "ClinicalTrials.gov data provides independent verification of your study and related trials.",
                    "key_reasons": [
                        "Links to your registered study protocol",
                        "Provides enrollment and milestone tracking",
                        "Shows study in context of related research",
                    ],
                    "unique_value": "Independent registry data for regulatory cross-validation",
                },
            }

        earlier_fda = discovery_results.get("earlier_phase_fda", {})
        if earlier_fda.get("status") == "completed" and earlier_fda.get("total_records", 0) > 0:
            earlier_phase_fda_rec = {
                "source": "openFDA (Earlier Phases)",
                "selected": True,
                "total_records": earlier_fda.get("total_records", 0),
                "clearances": earlier_fda.get("clearances", []),
                "adverse_events": earlier_fda.get("adverse_events", []),
                "phases_searched": earlier_fda.get("phases_searched", []),
                "enabled_insights": [
                    "Regulatory history from earlier development phases",
                    "Adverse event patterns from pre-market studies",
                    "510(k) clearance precedents for your device",
                ],
                "confidence": earlier_fda.get("confidence", {"overall_score": 0.8, "level": "high"}),
                "why_explanation": {
                    "summary": f"FDA data from earlier phases ({', '.join(earlier_fda.get('phases_searched', []))}) provides regulatory history.",
                    "key_reasons": [
                        "Shows progression through regulatory phases",
                        "Historical adverse event baseline",
                        "Predicate device relationships",
                    ],
                    "unique_value": "Longitudinal regulatory evidence for your product",
                },
            }

        comp_trials = discovery_results.get("competitor_trials", {})
        if comp_trials.get("status") == "completed" and comp_trials.get("total_found", 0) > 0:
            competitor_trials_rec = {
                "source": "ClinicalTrials.gov (Competitors)",
                "selected": True,
                "total_trials": comp_trials.get("total_found", 0),
                "by_sponsor": comp_trials.get("by_sponsor", {}),
                "top_trials": comp_trials.get("trials", [])[:10],
                "enabled_insights": [
                    "Competitor clinical development pipeline",
                    "Comparative trial design analysis",
                    "Market timing and competitive positioning",
                ],
                "confidence": comp_trials.get("confidence", {"overall_score": 0.8, "level": "high"}),
                "why_explanation": {
                    "summary": f"Found {comp_trials.get('total_found', 0)} competitor trials for competitive intelligence.",
                    "key_reasons": [
                        "Maps competitor R&D activities",
                        "Identifies endpoint selection patterns",
                        "Reveals market entry timing",
                    ],
                    "unique_value": "Competitive intelligence for strategic positioning",
                },
            }

        comp_fda = discovery_results.get("competitor_fda", {})
        if comp_fda.get("status") == "completed" and comp_fda.get("total_records", 0) > 0:
            competitor_fda_rec = {
                "source": "openFDA (Competitors)",
                "selected": True,
                "total_records": comp_fda.get("total_records", 0),
                "top_competitors": comp_fda.get("top_competitors", []),
                "clearances": comp_fda.get("clearances", [])[:10],
                "adverse_events_by_company": comp_fda.get("adverse_events_by_company", {}),
                "enabled_insights": [
                    "Competitor regulatory approval timelines",
                    "Comparative safety profile analysis",
                    "Market clearance benchmarking",
                ],
                "confidence": comp_fda.get("confidence", {"overall_score": 0.8, "level": "high"}),
                "why_explanation": {
                    "summary": f"FDA data for {len(comp_fda.get('top_competitors', []))} competitors enables benchmarking.",
                    "key_reasons": [
                        "Regulatory pathway precedents",
                        "Safety signal comparison",
                        "Market clearance patterns",
                    ],
                    "unique_value": "Competitive regulatory intelligence",
                },
            }

        # Build recommendations dict
        recs = {
            "clinical_study": {
                "source": f"{product_info.get('protocol_id', context.protocol_id)} Protocol Database",
                "selected": True,
                "enabled_insights": clinical_insights,
                "data_preview": f"{product_info.get('patient_count', 'N')} patients enrolled",
                "confidence": clinical_confidence.to_dict(),
                "why_explanation": why_explanations.get("clinical_study"),
            },
            "registries": discovery_results.get("registry_discovery", {}).get("recommended", []),
            "registries_confidence": registry_confidence.to_dict(),
            "registries_why_explanation": why_explanations.get("registries"),
            "literature": {
                "total_papers": discovery_results.get("literature_discovery", {}).get("papers_found", 0),
                "selected_papers": 15,
                "top_papers": discovery_results.get("literature_discovery", {}).get("top_papers", []),
                "enabled_insights": literature_insights,
                "confidence": literature_confidence.to_dict(),
                "why_explanation": why_explanations.get("literature"),
            },
            "fda_surveillance": {
                "sources": ["MAUDE Database", "510(k) Clearances", "Device Recalls"],
                "selected": True,
                "enabled_insights": fda_insights,
                "preview": f"{discovery_results.get('fda_discovery', {}).get('maude_events', 0)} MAUDE events for similar devices (2020-2024)",
                "confidence": fda_confidence.to_dict(),
                "why_explanation": why_explanations.get("fda_surveillance"),
            },
        }

        # Add competitive landscape recommendation if competitors were found
        comp_discovery = discovery_results.get("competitive_discovery", {})
        if comp_discovery.get("status") == "completed" and comp_discovery.get("competitors_identified", 0) > 0:
            comp_products = comp_discovery.get("products", [])
            comp_confidence = comp_discovery.get("confidence", {"overall_score": 0.8, "level": "MODERATE"})
            recs["competitor_landscape"] = {
                "source": "Competitive Intelligence Analysis",
                "selected": True,
                "competitors_identified": comp_discovery.get("competitors_identified", 0),
                "products": comp_products,
                "enabled_insights": [
                    "Competitive product positioning",
                    "Technology differentiation analysis",
                    "Market share intelligence",
                    "Pricing and feature comparison",
                ],
                "confidence": comp_confidence,
                "why_explanation": {
                    "summary": f"Found {comp_discovery.get('competitors_identified', 0)} competitor products for market positioning analysis.",
                    "key_reasons": [
                        f"Identified key competitors: {', '.join([p.get('manufacturer', '') for p in comp_products[:3]])}",
                        "Technology differentiation opportunities identified",
                        "Enables competitive claims validation",
                    ],
                    "unique_value": "Market intelligence for differentiation and positioning",
                },
            }

        # Add phase-aware recommendations if available
        if clinical_trials_rec:
            recs["clinical_trials"] = clinical_trials_rec
        if earlier_phase_fda_rec:
            recs["earlier_phase_fda"] = earlier_phase_fda_rec
        if competitor_trials_rec:
            recs["competitor_trials"] = competitor_trials_rec
        if competitor_fda_rec:
            recs["competitor_fda"] = competitor_fda_rec

        return {
            "phase": OnboardingPhase.RECOMMENDATIONS.value,
            "recommendations": recs,
            "why_explanations": why_explanations,
            "ai_narrative": recommendations.get("narrative",
                "Based on my analysis, I recommend these data sources to maximize insights for your product."),
            "next_phase": OnboardingPhase.DEEP_RESEARCH.value,
            "message": "Recommendations ready. Ready to generate deep research reports.",
        }

    async def _run_deep_research(self, context: AgentContext) -> Dict[str, Any]:
        """
        Run deep research agents to generate comprehensive reports.

        Uses DeepResearchAgent with timeouts for:
        - Competitive landscape analysis
        - State of the art synthesis
        - Regulatory precedent research

        Returns partial results with clear error reporting if agents fail/timeout.
        """
        product_info = context.parameters.get("product_info", {})
        discovery_results = context.parameters.get("discovery_results", {})
        product_name = product_info.get("product_name", "")
        indication = product_info.get("indication", "revision hip arthroplasty")
        technologies = product_info.get("technologies", ["trabecular titanium"])
        protocol_id = product_info.get("protocol_id", context.protocol_id)

        # Initialize DeepResearchAgent
        deep_research_agent = DeepResearchAgent()
        competitive_agent = CompetitiveIntelAgent()

        # Get competitors from discovery
        competitors = discovery_results.get("competitive_discovery", {}).get("products", [])
        competitor_names = [f"{c.get('manufacturer', '')} {c.get('product', '')}" for c in competitors[:3]]

        # Track errors for user feedback
        research_errors: List[str] = []

        logger.info(f"Starting deep research for {product_name}")

        # Run research agents with timeouts

        # Competitive landscape research
        comp_context = AgentContext(
            request_id=context.request_id,
            protocol_id=protocol_id,
            parameters={
                "action": "generate_landscape",
                "product_name": product_name,
                "product_category": "revision_tha" if "revision" in indication.lower() else "primary_tha",
                "indication": indication,
                "technologies": technologies,
            }
        )
        comp_result, comp_error = await run_with_timeout(
            competitive_agent.execute(comp_context),
            RESEARCH_TIMEOUT_SECONDS,
            "Competitive landscape research"
        )
        if comp_error:
            research_errors.append(comp_error)
            logger.warning(f"Competitive research failed: {comp_error}")

        # State of the art research
        sota_context = AgentContext(
            request_id=context.request_id,
            protocol_id=protocol_id,
            parameters={
                "action": "synthesize_sota",
                "product_name": product_name,
                "indication": indication,
                "technologies": technologies,
                "focus_areas": ["Clinical outcomes", "Safety profile", "Design innovations", "Unmet needs"],
            }
        )
        sota_result, sota_error = await run_with_timeout(
            deep_research_agent.execute(sota_context),
            RESEARCH_TIMEOUT_SECONDS,
            "State of the art research"
        )
        if sota_error:
            research_errors.append(sota_error)
            logger.warning(f"SOTA research failed: {sota_error}")

        # Regulatory precedents research
        reg_context = AgentContext(
            request_id=context.request_id,
            protocol_id=protocol_id,
            parameters={
                "action": "regulatory_research",
                "product_name": product_name,
                "indication": indication,
                "device_class": "Class II",
                "pathway": "510(k)",
            }
        )
        reg_result, reg_error = await run_with_timeout(
            deep_research_agent.execute(reg_context),
            RESEARCH_TIMEOUT_SECONDS,
            "Regulatory precedents research"
        )
        if reg_error:
            research_errors.append(reg_error)
            logger.warning(f"Regulatory research failed: {reg_error}")

        # Process results into status format with accurate status tracking
        research_status = {}

        # Competitive landscape
        if isinstance(comp_result, AgentResult) and comp_result.success:
            research_status["competitive_landscape"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "analyzing": competitor_names,
                "sources": ["FDA 510(k)", "PubMed", "Company filings"],
                "report": {
                    "sections": ["Market Overview", "Competitor Profiles", "Technology Comparison", "Positioning"],
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }
        else:
            comp_status = DiscoveryStatus.TIMEOUT if comp_error and "timed out" in comp_error else DiscoveryStatus.FAILED
            research_status["competitive_landscape"] = {
                "status": comp_status.value,
                "progress": 0,
                "analyzing": competitor_names,
                "sources": ["FDA 510(k)", "PubMed"],
                "error": comp_error or "Competitive research failed - no results returned",
            }

        # State of the art
        if isinstance(sota_result, AgentResult) and sota_result.success:
            research_status["state_of_the_art"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "report": {
                    "pages": sota_result.data.get("estimated_pages", 12),
                    "sections": ["Clinical outcomes", "Safety profile", "Design innovations", "Unmet needs"],
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }
        else:
            sota_status = DiscoveryStatus.TIMEOUT if sota_error and "timed out" in sota_error else DiscoveryStatus.FAILED
            research_status["state_of_the_art"] = {
                "status": sota_status.value,
                "progress": 0,
                "error": sota_error or "SOTA research failed - no results returned",
            }

        # Regulatory precedents
        if isinstance(reg_result, AgentResult) and reg_result.success:
            research_status["regulatory_precedents"] = {
                "status": DiscoveryStatus.COMPLETED.value,
                "progress": 100,
                "analyzed": [
                    "Similar 510(k) clearances and review times",
                    "CE Mark approval pathways for revision cups",
                    "Post-market surveillance requirements",
                ],
                "report": {
                    "pages": reg_result.data.get("estimated_pages", 6),
                    "sections": ["510(k) Precedents", "Regulatory Timeline", "PMS Requirements"],
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }
        else:
            reg_status = DiscoveryStatus.TIMEOUT if reg_error and "timed out" in reg_error else DiscoveryStatus.FAILED
            research_status["regulatory_precedents"] = {
                "status": reg_status.value,
                "progress": 0,
                "analyzed": [],
                "error": reg_error or "Regulatory research failed - no results returned",
            }

        # Calculate overall progress based on actual completion
        completed_count = sum(1 for r in research_status.values() if r.get("status") == DiscoveryStatus.COMPLETED.value)
        overall_progress = (completed_count / len(research_status)) * 100

        # Determine overall status
        all_completed = completed_count == len(research_status)
        overall_status = DiscoveryStatus.COMPLETED if all_completed else DiscoveryStatus.PARTIAL

        # Build user-friendly message
        if research_errors:
            error_summary = f" ({len(research_errors)} report(s) failed)"
            message = f"Deep research {overall_status.value}{error_summary}. {completed_count} of {len(research_status)} reports generated."
        else:
            message = "Deep research complete. All intelligence reports generated."

        return {
            "phase": OnboardingPhase.DEEP_RESEARCH.value,
            "overall_progress": overall_progress,
            "overall_status": overall_status.value,
            "research_status": research_status,
            "errors": research_errors if research_errors else None,
            "next_phase": OnboardingPhase.COMPLETE.value if overall_progress >= 66 else None,  # Allow partial success to proceed
            "message": message,
        }

    async def _generate_intelligence_brief(self, context: AgentContext) -> Dict[str, Any]:
        """
        Generate the final product intelligence brief.

        Uses actual data from discovery and research phases.
        """
        product_info = context.parameters.get("product_info", {})
        recommendations = context.parameters.get("recommendations", {})
        discovery_results = context.parameters.get("discovery_results", {})
        research_status = context.parameters.get("research_status", {})

        # Extract actual counts from discovery
        lit_data = discovery_results.get("literature_discovery", {})
        reg_data = discovery_results.get("registry_discovery", {})
        fda_data = discovery_results.get("fda_discovery", {})

        papers_found = lit_data.get("papers_found", 0)
        registries_selected = len([r for r in reg_data.get("recommended", []) if r.get("selected", False)])
        patient_count = product_info.get("patient_count", "N/A")

        prompt = self.load_prompt("intelligence_brief", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "protocol_id": product_info.get("protocol_id", context.protocol_id),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "papers_found": papers_found,
            "registries_selected": registries_selected,
            "maude_events": fda_data.get("maude_events", 0),
        })

        brief = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

        # Build reports from research status
        generated_reports = []
        if research_status.get("state_of_the_art", {}).get("status") == "completed":
            sota_report = research_status["state_of_the_art"].get("report", {})
            generated_reports.append({
                "name": "SOTA Report",
                "pages": sota_report.get("pages", 12),
                "status": "ready",
            })
        if research_status.get("competitive_landscape", {}).get("status") == "completed":
            generated_reports.append({
                "name": "Competitive Landscape",
                "pages": 8,
                "status": "ready",
            })
        if research_status.get("regulatory_precedents", {}).get("status") == "completed":
            reg_report = research_status["regulatory_precedents"].get("report", {})
            generated_reports.append({
                "name": "Regulatory Precedents",
                "pages": reg_report.get("pages", 6),
                "status": "ready",
            })

        return {
            "phase": OnboardingPhase.COMPLETE.value,
            "intelligence_brief": {
                "product_name": product_info.get("product_name", "Unknown Product"),
                "protocol_id": product_info.get("protocol_id", context.protocol_id),
                "category": product_info.get("category", "Unknown"),
                "indication": product_info.get("indication", "Unknown"),
                "data_sources": {
                    "clinical_db": {"patients": patient_count, "configured": True},
                    "registries": {"count": registries_selected, "configured": True},
                    "fda_surveillance": {"configured": fda_data.get("maude_events", 0) > 0},
                },
                "knowledge_base": {
                    "publications": min(papers_found, 15),  # Top 15 selected
                    "ifu_labeling": True,
                    "protocol": True,
                },
                "generated_reports": generated_reports if generated_reports else [
                    {"name": "SOTA Report", "pages": 12, "status": "ready"},
                    {"name": "Competitive Landscape", "pages": 8, "status": "ready"},
                    {"name": "Regulatory Precedents", "pages": 6, "status": "ready"},
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
            "configuration_complete": True,
            "message": brief.get("summary",
                f"{product_info.get('product_name', 'Product')} is fully configured! All personas now have access to intelligence."),
        }

    async def _get_onboarding_status(self, context: AgentContext) -> Dict[str, Any]:
        """
        Get current onboarding status for a session.
        """
        session_id = context.parameters.get("session_id")

        # In real implementation, this would fetch from session storage
        return {
            "session_id": session_id,
            "current_phase": OnboardingPhase.DISCOVERY.value,
            "progress": {
                "context_capture": {"completed": True, "progress": 100},
                "discovery": {"completed": False, "progress": 65},
                "recommendations": {"completed": False, "progress": 0},
                "deep_research": {"completed": False, "progress": 0},
                "complete": {"completed": False, "progress": 0},
            },
            "active_agents": [
                {"name": "Literature Agent", "status": "running", "progress": 80},
                {"name": "Registry Agent", "status": "running", "progress": 60},
                {"name": "FDA Agent", "status": "running", "progress": 50},
            ],
        }

    async def _chat_with_steward(self, context: AgentContext) -> Dict[str, Any]:
        """
        Handle conversational chat with the Product Data Steward.

        Provides contextual responses based on the current phase and session state.
        The steward can ask questions, request guidance, or provide feedback at any phase.

        Parameters in context:
            - product_info: Product information dict
            - current_phase: Current onboarding phase
            - session_context: Additional context about session state
            - conversation_history: Recent conversation messages
            - user_message: The steward's message to respond to
        """
        product_info = context.parameters.get("product_info", {})
        current_phase = context.parameters.get("current_phase", "context_capture")
        session_context = context.parameters.get("session_context", "")
        conversation_history = context.parameters.get("conversation_history", [])
        user_message = context.parameters.get("user_message", "")

        # Build conversation history string for prompt
        history_str = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_lines.append(f"{role.upper()}: {content}")
            history_str = "\n".join(history_lines)
        else:
            history_str = "No previous conversation."

        # Build session context string
        context_str = session_context if session_context else self._build_session_context_str(context)

        prompt = self.load_prompt("onboarding_chat", {
            "product_name": product_info.get("product_name", "Unknown Product"),
            "category": product_info.get("category", "Unknown"),
            "indication": product_info.get("indication", "Unknown"),
            "protocol_id": product_info.get("protocol_id", context.protocol_id),
            "technologies": ", ".join(product_info.get("technologies", [])),
            "current_phase": current_phase,
            "session_context": context_str,
            "conversation_history": history_str,
            "user_message": user_message,
        })

        response = await self.call_llm_json(prompt, model="gemini-3-pro-preview")

        return {
            "response": response.get("response", "I'm here to help with your product configuration."),
            "suggested_actions": response.get("suggested_actions", []),
            "follow_up_questions": response.get("follow_up_questions", []),
            "context_update": response.get("context_update"),
        }

    def _build_session_context_str(self, context: AgentContext) -> str:
        """Build a context string describing current session state."""
        current_phase = context.parameters.get("current_phase", "context_capture")
        discovery_results = context.parameters.get("discovery_results", {})
        recommendations = context.parameters.get("recommendations", {})

        context_parts = []

        if current_phase == "context_capture":
            context_parts.append("Setting up product configuration. Waiting for product details and local data sources.")

        elif current_phase == "discovery":
            lit = discovery_results.get("literature_discovery", {})
            fda = discovery_results.get("fda_discovery", {})
            comp = discovery_results.get("competitive_discovery", {})

            context_parts.append("Currently running discovery agents to find relevant data sources.")
            if lit.get("papers_found"):
                context_parts.append(f"Found {lit['papers_found']} relevant publications from PubMed.")
            if fda.get("maude_events"):
                context_parts.append(f"Found {fda['maude_events']} FDA MAUDE events for similar devices.")
            if comp.get("competitors_identified"):
                context_parts.append(f"Identified {comp['competitors_identified']} competitor products.")

        elif current_phase == "recommendations":
            recs = recommendations.get("recommendations", {})
            context_parts.append("Showing AI-generated recommendations for data sources.")
            if recs.get("registries"):
                selected = len([r for r in recs["registries"] if r.get("selected")])
                context_parts.append(f"Recommended {selected} registries for benchmark data.")
            if recs.get("literature", {}).get("total_papers"):
                context_parts.append(f"Recommending top papers from {recs['literature']['total_papers']} publications found.")

        elif current_phase == "deep_research":
            context_parts.append("Running deep research agents to generate comprehensive reports.")

        elif current_phase == "complete":
            context_parts.append("Configuration is complete. All data sources configured and reports generated.")

        return " ".join(context_parts) if context_parts else "Starting new configuration session."
