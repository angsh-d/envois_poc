"""
Chat API endpoint with multi-agent orchestration for natural language queries.

This endpoint dynamically queries specialized agents (Data, Literature, Registry)
based on the user's question to provide comprehensive, evidence-based responses.
"""
import json
import logging
import re
import uuid
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.agents.base_agent import AgentContext, AgentType
from app.agents.data_agent import DataAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.registry_agent import RegistryAgent
from app.agents.code_agent import get_code_agent, CodeLanguage


class IntentClassification(BaseModel):
    """LLM-classified intent for routing queries to appropriate agents."""
    needs_registry: bool = Field(default=False, description="Needs registry benchmark data")
    needs_literature: bool = Field(default=False, description="Needs published literature data")
    needs_clinical_data: bool = Field(default=False, description="Needs study-specific clinical data")
    needs_multi_registry: bool = Field(default=False, description="Needs all 5 registries comparison")
    needs_multi_source_synthesis: bool = Field(default=False, description="Needs cross-source synthesis")
    query_type: str = Field(default="general", description="Specific query type for specialized handling")
    confidence: float = Field(default=0.5, description="Classification confidence 0-1")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class DataLineage(str, Enum):
    """Classification of how data was derived."""
    RAW_DATA = "raw_data"           # Direct observation from source
    CALCULATED = "calculated"        # Derived from raw data via formula
    LLM_SYNTHESIS = "llm_synthesis"  # AI-generated from multiple sources
    AGGREGATED = "aggregated"        # Statistical aggregation of raw data


class SourceMetadata(BaseModel):
    """Rich metadata for provenance tracking."""
    # Registry-specific
    abbreviation: Optional[str] = None
    report_year: Optional[int] = None
    data_years: Optional[str] = None
    n_procedures: Optional[int] = None
    data_completeness: Optional[float] = None

    # Literature-specific
    publication_id: Optional[str] = None
    publication_title: Optional[str] = None
    publication_year: Optional[int] = None
    n_patients: Optional[int] = None
    follow_up_years: Optional[float] = None

    # Quality indicators
    strengths: Optional[List[str]] = None
    limitations: Optional[List[str]] = None


class Source(BaseModel):
    """Enhanced source citation with provenance tracking."""
    type: str  # study_data, protocol, literature, registry
    reference: str
    detail: Optional[str] = None

    # Provenance fields
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    confidence_level: str = Field(default="high", description="high/moderate/low/insufficient")
    lineage: str = Field(default="raw_data", description="Data derivation type")
    metadata: Optional[SourceMetadata] = None


class SourceRawData(BaseModel):
    """Complete raw data from a source for drill-down transparency."""
    full_name: Optional[str] = None
    abbreviation: Optional[str] = None
    report_year: Optional[int] = None
    data_years: Optional[str] = None
    population: Optional[str] = None
    n_procedures: Optional[int] = None
    n_primary: Optional[int] = None
    # All survival rates
    survival_1yr: Optional[float] = None
    survival_2yr: Optional[float] = None
    survival_5yr: Optional[float] = None
    survival_10yr: Optional[float] = None
    survival_15yr: Optional[float] = None
    # All revision rates
    revision_rate_1yr: Optional[float] = None
    revision_rate_2yr: Optional[float] = None
    revision_rate_median: Optional[float] = None
    revision_rate_p75: Optional[float] = None
    revision_rate_p95: Optional[float] = None
    # Revision reasons (top causes)
    revision_reasons: Optional[List[Dict[str, Any]]] = None


class EvidenceDataPoint(BaseModel):
    """Individual data point from a specific source."""
    source: str  # Source name (e.g., "AOANJRR", "NJR", "Berry 2022")
    source_type: str  # registry, literature, study_data
    value: Optional[float] = None  # Numeric value if applicable
    value_formatted: str  # Human-readable value (e.g., "91.2%", "2.3 HR")
    sample_size: Optional[int] = None  # n= for this data point
    year: Optional[str] = None  # Data year or publication year
    context: Optional[str] = None  # Additional context (e.g., "at 5 years")
    raw_data: Optional[SourceRawData] = None  # Full source data for drill-down


class EvidenceMetric(BaseModel):
    """A metric/claim with supporting evidence from multiple sources."""
    metric_name: str  # e.g., "5-Year Survival Rate", "Revision Risk"
    claim: str  # The specific claim made (e.g., "Pooled 5-year survival is 89.8%")
    aggregated_value: Optional[str] = None  # The synthesized/pooled value
    calculation_method: Optional[str] = None  # How it was calculated (e.g., "weighted mean")
    data_points: List[EvidenceDataPoint] = []  # Individual values from each source
    confidence_level: str = "high"  # Confidence in this specific metric


class Evidence(BaseModel):
    """Comprehensive evidence supporting the response."""
    summary: str  # Brief summary of evidence strength
    metrics: List[EvidenceMetric] = []  # Key metrics with their supporting data
    total_sources: int = 0  # Total number of sources consulted
    total_sample_size: Optional[int] = None  # Combined n across all sources


class ChatMessage(BaseModel):
    """Chat message in conversation history."""
    role: str  # user or assistant
    content: str
    sources: Optional[List[Source]] = None
    timestamp: str


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str
    context: str  # Current page context (dashboard, readiness, safety, etc.)
    study_id: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    sources: List[Source]
    evidence: Optional[Evidence] = None  # Detailed evidence supporting the response
    suggested_followups: Optional[List[str]] = None


# Keywords for detecting question intent and required agents
INTENT_KEYWORDS = {
    "literature": [
        "literature", "study", "studies", "publication", "published", "paper",
        "hazard ratio", "hr", "evidence", "research", "findings", "mcid",
        "improvement", "benchmark", "dixon", "bozic", "lombardi", "berry",
        "kurtz", "parvizi", "expected", "literature range"
    ],
    "registry": [
        "registry", "aoanjrr", "njr", "shar", "ajrr", "cjrr", "population",
        "national", "benchmark", "threshold", "concern", "percentile",
        "registry benchmark", "registry data", "real-world"
    ],
    "multi_registry": [
        # Keywords that specifically require ALL registries comparison
        "all registries", "which registries", "each registry", "across registries",
        "registry comparison", "registries have higher", "registries have lower",
        "australian", "swedish", "american", "canadian", "uk registry",
        "compare to registries", "registry ranking", "pooled", "international",
        "5 registries", "five registries"
    ],
    "closest_registry": [
        # Keywords for finding the most similar registry
        "closest registry", "most similar", "similar to our study",
        "best match", "matching registry", "which registry matches"
    ],
    "revision_reasons": [
        # Keywords for revision reason analysis
        "why revision", "revision reason", "revision cause", "aseptic loosening",
        "infection", "dislocation", "fracture", "instability", "wear",
        "causes of revision", "revision breakdown", "why are revisions",
        "loosening vs infection", "primary cause"
    ],
    "threshold_proximity": [
        # Keywords for threshold proximity warnings
        "threshold", "approaching", "near threshold", "close to",
        "proximity", "warning", "signal", "exceeding", "how close",
        "distance from", "safety margin", "buffer"
    ],
    "outcomes_by_indication": [
        # Keywords for indication-specific outcomes
        "indication", "outcomes by", "stratified", "by reason",
        "infection outcomes", "loosening outcomes", "worst outcomes",
        "best outcomes", "outcome by cause", "survival by indication"
    ],
    "registry_metadata": [
        # Keywords for registry quality/metadata
        "data quality", "limitations", "registry coverage", "strengths",
        "weaknesses", "data source", "methodology", "capture rate",
        "follow-up", "completeness", "provenance"
    ],
    "multi_source_registry": [
        # Keywords that require BOTH registry AND literature data for comprehensive answers
        # Product-specific queries that need multiple data sources
        "delta pf", "delta revision cup", "twinsys", "ceramic liner", "ceramic delta",
        "delta liners", "cementless", "cemented", "polyethylene",
        # Outcome metrics that need literature benchmarks + registry data
        "survival rate", "revision rate", "procedures", "case numbers",
        "patients at risk", "population", "patient count", "total cases",
        # Comparison queries needing multi-source synthesis
        "how does our", "compare our", "our study vs", "our outcomes",
        "consistent with literature", "literature comparison", "vs literature",
        # Trend analysis requiring multiple timepoints
        "over time", "3 year", "5 year", "10 year", "trend", "year over year",
        "three year", "five year", "ten year", "longitudinal"
    ],
    "risk": [
        "risk", "hazard", "osteoporosis", "bmi", "diabetes", "smoking",
        "prior revision", "bone loss", "comorbid", "risk factor", "risk score",
        "at-risk", "high-risk", "fracture risk", "revision risk"
    ],
    "safety": [
        "safety", "adverse", "ae", "sae", "complication", "dislocation",
        "infection", "fracture", "signal", "rate", "outcome"
    ],
    "comparison": [
        "compare", "comparison", "versus", "vs", "compared to", "relative to",
        "consistent with", "in line with", "against", "how does"
    ],
    "code_generation": [
        # Keywords for code generation requests
        "write code", "generate code", "code for", "show me code", "python code",
        "r code", "sql query", "sql code", "c code", "script for", "program for",
        "write a script", "write a query", "create code", "give me code",
        "kaplan-meier code", "survival code", "calculate", "compute",
        "write python", "write r", "write sql", "in python", "in r", "using r",
        "query for", "query to", "code to", "script to"
    ]
}


# Cache for intent classification (simple TTL-less cache, cleared on restart)
_intent_cache: Dict[str, Set[str]] = {}
_prompt_service: Optional[PromptService] = None
_llm_service: Optional[LLMService] = None

# Confidence threshold - below this, fall back to keywords
INTENT_CONFIDENCE_THRESHOLD = 0.7


def _get_prompt_service() -> PromptService:
    """Get singleton prompt service."""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service


def _get_llm_service() -> LLMService:
    """Get singleton LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def _extract_json(response: str) -> dict:
    """Robustly extract JSON from LLM response."""
    response = response.strip()

    # Try direct parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Remove markdown code blocks
    if "```" in response:
        # Extract content between first ``` and last ```
        parts = response.split("```")
        if len(parts) >= 3:
            json_part = parts[1]
            # Remove language identifier if present
            if json_part.startswith("json"):
                json_part = json_part[4:]
            try:
                return json.loads(json_part.strip())
            except json.JSONDecodeError:
                pass

    # Try to find JSON object with regex
    json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from response: {response[:200]}")


async def detect_question_intent_llm(question: str, page_context: str) -> Set[str]:
    """
    Use LLM to intelligently classify question intent for agent routing.

    Features:
    - Caches results for identical questions
    - Falls back to keywords if confidence < threshold
    - Falls back to keywords on any error

    Returns set of agent types needed.
    """
    # Check cache first
    cache_key = f"{question.lower().strip()}|{page_context}"
    if cache_key in _intent_cache:
        logger.debug(f"Intent cache hit for: {question[:50]}...")
        return _intent_cache[cache_key]

    try:
        # Load prompt and call LLM
        prompt = _get_prompt_service().load(
            "intent_classification",
            parameters={"question": question, "page_context": page_context}
        )

        response = await _get_llm_service().generate(
            prompt=prompt,
            model="gemini-3-pro-preview",
            temperature=0.0,  # Zero temperature for deterministic classification
            max_tokens=256    # Reduced - we only need a small JSON
        )

        # Parse response
        classification = _extract_json(response)
        intent_obj = IntentClassification(**classification)

        # Check confidence - fall back to keywords if too low
        if intent_obj.confidence < INTENT_CONFIDENCE_THRESHOLD:
            logger.info(f"LLM confidence {intent_obj.confidence:.2f} below threshold, using keywords")
            intents = detect_question_intent_keywords(question)
            _intent_cache[cache_key] = intents
            return intents

        # Convert classification to intent set (conservative approach)
        intents = set()

        if intent_obj.needs_clinical_data:
            intents.add("data")

        if intent_obj.needs_literature:
            intents.add("literature")

        if intent_obj.needs_registry:
            intents.add("registry")

        if intent_obj.needs_multi_registry:
            intents.add("registry")
            intents.add("multi_registry")

        # multi_source only adds the flag, doesn't force all sources
        if intent_obj.needs_multi_source_synthesis:
            intents.add("multi_source")

        # Map query_type to specific intents
        # Some query types require specific sources (e.g., revision_reasons needs registry)
        query_type_intents = {
            "revision_reasons": ["revision_reasons", "registry", "multi_registry"],  # Revision data comes from registries
            "threshold_proximity": ["threshold_proximity", "registry"],  # Thresholds are registry-based
            "outcomes_by_indication": ["outcomes_by_indication", "registry"],
            "registry_metadata": ["registry_metadata", "registry", "multi_registry"],
            "closest_registry": ["closest_registry", "registry", "multi_registry", "data"],  # Need our data to compare
            "product_specific": ["registry", "multi_registry", "literature", "data"],  # Product queries need all context
            "risk_factors": [],      # Sources already set by needs_* flags
            "safety_signals": [],    # Sources already set by needs_* flags
        }

        if intent_obj.query_type in query_type_intents:
            for intent in query_type_intents[intent_obj.query_type]:
                intents.add(intent)

        # Default to data agent if no intents detected
        if not intents:
            intents.add("data")

        # Cache and return
        _intent_cache[cache_key] = intents
        logger.info(f"LLM intent: {sorted(intents)} (confidence: {intent_obj.confidence:.2f})")
        return intents

    except Exception as e:
        logger.warning(f"LLM intent detection failed: {e}, falling back to keywords")
        intents = detect_question_intent_keywords(question)
        _intent_cache[cache_key] = intents  # Cache fallback result too
        return intents


def detect_question_intent_keywords(question: str) -> Set[str]:
    """
    Detect what agents to query based on question keywords.

    Returns set of agent types needed:
        'data', 'literature', 'registry', 'multi_registry',
        'revision_reasons', 'threshold_proximity', 'outcomes_by_indication', 'registry_metadata'
    """
    question_lower = question.lower()
    intents = set()

    # Check for multi-registry keywords FIRST (takes precedence over single registry)
    for keyword in INTENT_KEYWORDS["multi_registry"]:
        if keyword in question_lower:
            intents.add("registry")
            intents.add("multi_registry")  # Flag to fetch ALL registries
            break

    # Check for revision reasons keywords
    for keyword in INTENT_KEYWORDS["revision_reasons"]:
        if keyword in question_lower:
            intents.add("registry")
            intents.add("multi_registry")
            intents.add("revision_reasons")
            break

    # Check for threshold proximity keywords
    for keyword in INTENT_KEYWORDS["threshold_proximity"]:
        if keyword in question_lower:
            intents.add("registry")
            intents.add("threshold_proximity")
            break

    # Check for outcomes by indication keywords
    for keyword in INTENT_KEYWORDS["outcomes_by_indication"]:
        if keyword in question_lower:
            intents.add("registry")
            intents.add("outcomes_by_indication")
            break

    # Check for registry metadata keywords
    for keyword in INTENT_KEYWORDS["registry_metadata"]:
        if keyword in question_lower:
            intents.add("registry")
            intents.add("multi_registry")
            intents.add("registry_metadata")
            break

    # Check for closest registry keywords
    for keyword in INTENT_KEYWORDS["closest_registry"]:
        if keyword in question_lower:
            intents.add("registry")
            intents.add("multi_registry")
            intents.add("closest_registry")
            break

    # Check for multi-source registry keywords (Registry + Literature for comprehensive answers)
    for keyword in INTENT_KEYWORDS["multi_source_registry"]:
        if keyword in question_lower:
            intents.add("registry")
            intents.add("multi_registry")  # Use all registries for comprehensive comparison
            intents.add("literature")      # Also need literature benchmarks
            intents.add("data")            # Include clinical study data
            intents.add("multi_source")    # Flag for multi-source synthesis
            break

    # Check for literature-related keywords
    for keyword in INTENT_KEYWORDS["literature"]:
        if keyword in question_lower:
            intents.add("literature")
            break

    # Check for registry-related keywords (if not already flagged for multi)
    if "registry" not in intents:
        for keyword in INTENT_KEYWORDS["registry"]:
            if keyword in question_lower:
                intents.add("registry")
                break

    # Check for risk-related keywords (needs literature for hazard ratios)
    for keyword in INTENT_KEYWORDS["risk"]:
        if keyword in question_lower:
            intents.add("data")
            intents.add("literature")  # For hazard ratios
            break

    # Check for safety-related keywords
    for keyword in INTENT_KEYWORDS["safety"]:
        if keyword in question_lower:
            intents.add("data")
            break

    # Check for comparison keywords (needs multiple sources)
    for keyword in INTENT_KEYWORDS["comparison"]:
        if keyword in question_lower:
            intents.add("literature")
            intents.add("registry")
            intents.add("data")
            # Comparisons should always use all registries
            intents.add("multi_registry")
            break

    # Default to data agent if no specific intent detected
    if not intents:
        intents.add("data")

    return intents


async def query_agents(intents: Set[str], study_id: str) -> Dict[str, Any]:
    """
    Query relevant agents based on detected intents.

    Returns aggregated data from all queried agents.
    """
    results = {
        "data": None,
        "literature": None,
        "registry": None,
        "sources": [],
        "evidence": {
            "metrics": [],
            "total_sources": 0,
            "total_sample_size": 0
        }
    }

    request_id = str(uuid.uuid4())[:8]

    # Query Data Agent
    if "data" in intents:
        try:
            data_agent = DataAgent()
            context = AgentContext(
                request_id=f"{request_id}-data",
                protocol_id=study_id,
                parameters={"query_type": "safety"}
            )
            result = await data_agent.run(context)
            if result.success:
                results["data"] = result.data
                n_patients = result.data.get('n_patients', 0)
                results["sources"].append({
                    "type": "study_data",
                    "reference": f"H-34 Study Data (n={n_patients})",
                    "confidence": 0.95,
                    "confidence_level": "high",
                    "lineage": DataLineage.RAW_DATA.value,
                    "metadata": {
                        "n_patients": n_patients if isinstance(n_patients, int) else None,
                        "abbreviation": "H-34",
                        "data_completeness": 0.92,
                        "strengths": ["Prospective multi-center study", "Standardized data collection"],
                        "limitations": ["Limited follow-up duration", "Single device type"]
                    }
                })
                
                # === BUILD EVIDENCE FROM STUDY DATA ===
                rates = result.data.get("rates", {})
                n_adverse_events = result.data.get("n_adverse_events", 0)
                
                # Build study data evidence points
                study_data_points = []
                
                # Add adverse event rates if available
                if rates:
                    for rate_name, rate_value in rates.items():
                        if isinstance(rate_value, (int, float)) and rate_value > 0:
                            formatted_name = rate_name.replace("_", " ").title()
                            study_data_points.append({
                                "source": "H-34 Study",
                                "source_type": "study_data",
                                "value": rate_value if rate_value <= 1 else rate_value / 100,
                                "value_formatted": f"{rate_value*100:.1f}%" if rate_value <= 1 else f"{rate_value:.1f}%",
                                "sample_size": n_patients,
                                "year": "2024",
                                "context": f"from {n_patients} enrolled patients",
                                "raw_data": {
                                    "full_name": "H-34 DELTA Revision Cup Study",
                                    "abbreviation": "H-34",
                                    "n_procedures": n_patients,
                                    "population": "Revision THA patients"
                                }
                            })
                
                if study_data_points:
                    results["evidence"]["metrics"].append({
                        "metric_name": "H-34 Study Safety Metrics",
                        "claim": f"Current study has {n_adverse_events} adverse events across {n_patients} patients",
                        "aggregated_value": f"{n_adverse_events} AEs",
                        "calculation_method": "Direct count from study database",
                        "data_points": study_data_points[:5],  # Limit to top 5
                        "confidence_level": "high"
                    })
                    results["evidence"]["total_sources"] += 1
                    results["evidence"]["total_sample_size"] += n_patients
                    
        except Exception as e:
            logger.warning(f"Data agent error: {e}")

    # Query Literature Agent
    if "literature" in intents:
        try:
            lit_agent = LiteratureAgent()

            # Get all benchmarks
            context = AgentContext(
                request_id=f"{request_id}-lit",
                protocol_id=study_id,
                parameters={"query_type": "all"}
            )
            result = await lit_agent.run(context)
            if result.success:
                results["literature"] = result.data
                n_pubs = result.data.get('n_publications', 0)
                # Build publication list from available data
                pub_list = result.data.get('publications', [])
                pub_years = [p.get('year') for p in pub_list if p.get('year')]
                year_range = f"{min(pub_years)}-{max(pub_years)}" if pub_years else None
                results["sources"].append({
                    "type": "literature",
                    "reference": f"Literature benchmarks ({n_pubs} publications)",
                    "confidence": 0.85,
                    "confidence_level": "high",
                    "lineage": DataLineage.AGGREGATED.value,
                    "metadata": {
                        "n_patients": sum(p.get('n_patients', 0) for p in pub_list) or None,
                        "data_years": year_range,
                        "data_completeness": 0.88,
                        "strengths": ["Peer-reviewed publications", "Multi-center data"],
                        "limitations": ["Heterogeneous populations", "Variable follow-up periods"]
                    }
                })
                
                # === BUILD EVIDENCE FROM LITERATURE DATA ===
                if pub_list:
                    lit_data_points = []
                    total_lit_patients = 0
                    
                    for pub in pub_list[:5]:  # Top 5 publications
                        pub_n = pub.get('n_patients', 0)
                        total_lit_patients += pub_n
                        
                        # Get the primary outcome/rate from publication
                        revision_rate = pub.get('revision_rate') or pub.get('dislocation_rate') or pub.get('infection_rate')
                        if revision_rate:
                            lit_data_points.append({
                                "source": pub.get('title', 'Unknown')[:50] + "..." if len(pub.get('title', '')) > 50 else pub.get('title', 'Unknown'),
                                "source_type": "literature",
                                "value": revision_rate,
                                "value_formatted": f"{revision_rate*100:.1f}%" if revision_rate <= 1 else f"{revision_rate:.1f}%",
                                "sample_size": pub_n,
                                "year": str(pub.get('year', '')),
                                "context": f"{pub.get('journal', 'N/A')} ({pub.get('year', 'N/A')})",
                                "raw_data": {
                                    "full_name": pub.get('title'),
                                    "abbreviation": pub.get('first_author', 'Unknown')[:10],
                                    "n_procedures": pub_n,
                                    "population": pub.get('population', 'Revision THA')
                                }
                            })
                    
                    if lit_data_points:
                        results["evidence"]["metrics"].append({
                            "metric_name": "Literature Benchmarks",
                            "claim": f"Published studies report outcomes from {n_pubs} peer-reviewed publications",
                            "aggregated_value": f"{n_pubs} studies",
                            "calculation_method": f"Aggregated from {len(lit_data_points)} publications with combined n={total_lit_patients:,}",
                            "data_points": lit_data_points,
                            "confidence_level": "high"
                        })
                        results["evidence"]["total_sources"] += n_pubs
                        results["evidence"]["total_sample_size"] += total_lit_patients

            # Also get risk factors with hazard ratios
            risk_context = AgentContext(
                request_id=f"{request_id}-lit-hr",
                protocol_id=study_id,
                parameters={"query_type": "risk_factors", "outcome": "revision"}
            )
            risk_result = await lit_agent.run(risk_context)
            if risk_result.success:
                if results["literature"] is None:
                    results["literature"] = {}
                results["literature"]["risk_factors"] = risk_result.data
        except Exception as e:
            logger.warning(f"Literature agent error: {e}")

    # Query Registry Agent
    if "registry" in intents:
        try:
            reg_agent = RegistryAgent()

            # Determine query type: ALL registries or just primary
            if "multi_registry" in intents:
                # Fetch ALL 5 registries for comprehensive comparison
                context = AgentContext(
                    request_id=f"{request_id}-reg-all",
                    protocol_id=study_id,
                    parameters={"query_type": "all"}
                )
                result = await reg_agent.run(context)
                if result.success:
                    results["registry"] = result.data
                    n_regs = result.data.get("n_registries", 5)
                    total_procs = result.data.get("total_procedures", 0)
                    results["sources"].append({
                        "type": "registry",
                        "reference": f"International Registry Benchmarks ({n_regs} registries, n={total_procs:,})",
                        "confidence": 0.92,
                        "confidence_level": "high",
                        "lineage": DataLineage.AGGREGATED.value,
                        "metadata": {
                            "abbreviation": "Multi-Registry",
                            "n_procedures": total_procs,
                            "data_years": "1999-2023",
                            "data_completeness": 0.88,
                            "strengths": ["Large population-level data", "Multiple geographic regions", "Long-term follow-up"],
                            "limitations": ["Registry heterogeneity", "Variable outcome definitions"]
                        }
                    })

                # Also get pooled norms
                pooled_context = AgentContext(
                    request_id=f"{request_id}-reg-pooled",
                    protocol_id=study_id,
                    parameters={"query_type": "pooled"}
                )
                pooled_result = await reg_agent.run(pooled_context)
                if pooled_result.success:
                    if results["registry"] is None:
                        results["registry"] = {}
                    results["registry"]["pooled_norms"] = pooled_result.data

                # === BUILD EVIDENCE FROM REGISTRY DATA ===
                # Extract individual registry values for transparency
                if result.success and result.data.get("registries"):
                    registries = result.data["registries"]
                    total_n = sum(r.get("n_procedures", 0) for r in registries)

                    # Helper to build raw_data for drill-down
                    def build_raw_data(reg: Dict[str, Any]) -> Dict[str, Any]:
                        surv = reg.get("survival_rates", {})
                        rev = reg.get("revision_rates", {})
                        return {
                            "full_name": reg.get("name"),
                            "abbreviation": reg.get("abbreviation"),
                            "report_year": reg.get("report_year"),
                            "data_years": reg.get("data_years"),
                            "population": reg.get("population"),
                            "n_procedures": reg.get("n_procedures"),
                            "n_primary": reg.get("n_primary"),
                            "survival_1yr": surv.get("1yr"),
                            "survival_2yr": surv.get("2yr"),
                            "survival_5yr": surv.get("5yr"),
                            "survival_10yr": surv.get("10yr"),
                            "survival_15yr": surv.get("15yr"),
                            "revision_rate_1yr": rev.get("1yr"),
                            "revision_rate_2yr": rev.get("2yr"),
                            "revision_rate_median": rev.get("median"),
                            "revision_rate_p75": rev.get("p75"),
                            "revision_rate_p95": rev.get("p95"),
                            "revision_reasons": reg.get("revision_reasons")
                        }

                    # Build evidence for 5-year survival
                    survival_5yr_points = []
                    for reg in registries:
                        surv_rates = reg.get("survival_rates", {})
                        if surv_rates.get("5yr"):
                            survival_5yr_points.append({
                                "source": reg.get("abbreviation", reg.get("name", "Unknown")),
                                "source_type": "registry",
                                "value": surv_rates["5yr"],
                                "value_formatted": f"{surv_rates['5yr']*100:.1f}%",
                                "sample_size": reg.get("n_procedures"),
                                "year": reg.get("data_years", "").split("-")[-1] if reg.get("data_years") else None,
                                "context": f"at 5 years (n={reg.get('n_procedures', 0):,})",
                                "raw_data": build_raw_data(reg)
                            })

                    if survival_5yr_points:
                        # Calculate pooled value
                        values = [p["value"] for p in survival_5yr_points]
                        pooled_mean = sum(values) / len(values)
                        pooled_range = f"[{min(values)*100:.1f}%, {max(values)*100:.1f}%]"

                        results["evidence"]["metrics"].append({
                            "metric_name": "5-Year Survival Rate",
                            "claim": f"Pooled 5-year survival rate is {pooled_mean*100:.1f}% across {len(survival_5yr_points)} registries",
                            "aggregated_value": f"{pooled_mean*100:.1f}%",
                            "calculation_method": f"Simple mean of {len(survival_5yr_points)} registries, range {pooled_range}",
                            "data_points": survival_5yr_points,
                            "confidence_level": "high"
                        })

                    # Build evidence for 2-year survival
                    survival_2yr_points = []
                    for reg in registries:
                        surv_rates = reg.get("survival_rates", {})
                        if surv_rates.get("2yr"):
                            survival_2yr_points.append({
                                "source": reg.get("abbreviation", reg.get("name", "Unknown")),
                                "source_type": "registry",
                                "value": surv_rates["2yr"],
                                "value_formatted": f"{surv_rates['2yr']*100:.1f}%",
                                "sample_size": reg.get("n_procedures"),
                                "year": reg.get("data_years", "").split("-")[-1] if reg.get("data_years") else None,
                                "context": f"at 2 years (n={reg.get('n_procedures', 0):,})",
                                "raw_data": build_raw_data(reg)
                            })

                    if survival_2yr_points:
                        values = [p["value"] for p in survival_2yr_points]
                        pooled_mean = sum(values) / len(values)
                        results["evidence"]["metrics"].append({
                            "metric_name": "2-Year Survival Rate",
                            "claim": f"Pooled 2-year survival rate is {pooled_mean*100:.1f}%",
                            "aggregated_value": f"{pooled_mean*100:.1f}%",
                            "calculation_method": f"Simple mean of {len(survival_2yr_points)} registries",
                            "data_points": survival_2yr_points,
                            "confidence_level": "high"
                        })

                    # Build evidence for revision rates
                    revision_2yr_points = []
                    for reg in registries:
                        rev_rates = reg.get("revision_rates", {})
                        if rev_rates.get("2yr"):
                            revision_2yr_points.append({
                                "source": reg.get("abbreviation", reg.get("name", "Unknown")),
                                "source_type": "registry",
                                "value": rev_rates["2yr"],
                                "value_formatted": f"{rev_rates['2yr']*100:.1f}%",
                                "sample_size": reg.get("n_procedures"),
                                "year": reg.get("data_years", "").split("-")[-1] if reg.get("data_years") else None,
                                "context": f"at 2 years (n={reg.get('n_procedures', 0):,})",
                                "raw_data": build_raw_data(reg)
                            })

                    if revision_2yr_points:
                        values = [p["value"] for p in revision_2yr_points]
                        pooled_mean = sum(values) / len(values)
                        results["evidence"]["metrics"].append({
                            "metric_name": "2-Year Revision Rate",
                            "claim": f"Pooled 2-year revision rate is {pooled_mean*100:.1f}%",
                            "aggregated_value": f"{pooled_mean*100:.1f}%",
                            "calculation_method": f"Simple mean of {len(revision_2yr_points)} registries",
                            "data_points": revision_2yr_points,
                            "confidence_level": "high"
                        })

                    # Update evidence totals
                    results["evidence"]["total_sources"] = len(registries)
                    results["evidence"]["total_sample_size"] = total_n

            else:
                # Fetch only primary registry (AOANJRR) for simpler queries
                context = AgentContext(
                    request_id=f"{request_id}-reg",
                    protocol_id=study_id,
                    parameters={"query_type": "primary"}
                )
                result = await reg_agent.run(context)
                if result.success:
                    results["registry"] = result.data
                    results["sources"].append({
                        "type": "registry",
                        "reference": f"{result.data.get('name', 'Registry')} ({result.data.get('report_year', '')})",
                        "confidence": 0.90,
                        "confidence_level": "high",
                        "lineage": DataLineage.RAW_DATA.value,
                        "metadata": {
                            "abbreviation": result.data.get("abbreviation", "AOANJRR"),
                            "report_year": result.data.get("report_year"),
                            "data_years": result.data.get("data_years", "1999-2023"),
                            "n_procedures": result.data.get("n_procedures"),
                            "data_completeness": 0.95,
                            "strengths": ["Comprehensive national coverage", "Mandatory reporting"],
                            "limitations": ["Single country population"]
                        }
                    })

            # Also get thresholds
            thresh_context = AgentContext(
                request_id=f"{request_id}-reg-th",
                protocol_id=study_id,
                parameters={"query_type": "thresholds"}
            )
            thresh_result = await reg_agent.run(thresh_context)
            if thresh_result.success:
                if results["registry"] is None:
                    results["registry"] = {}
                results["registry"]["thresholds"] = thresh_result.data

            # ==== NEW QUERY TYPES FOR 100% ACCURACY ====

            # Fetch revision reasons if requested
            if "revision_reasons" in intents:
                rev_context = AgentContext(
                    request_id=f"{request_id}-reg-rev",
                    protocol_id=study_id,
                    parameters={"query_type": "revision_reasons"}
                )
                rev_result = await reg_agent.run(rev_context)
                if rev_result.success:
                    if results["registry"] is None:
                        results["registry"] = {}
                    results["registry"]["revision_reasons"] = rev_result.data
                    n_rev_regs = rev_result.data.get('n_registries_with_data', 0)
                    results["sources"].append({
                        "type": "registry",
                        "reference": f"Revision Reason Analysis ({n_rev_regs} registries)",
                        "confidence": 0.88,
                        "confidence_level": "high",
                        "lineage": DataLineage.AGGREGATED.value,
                        "metadata": {
                            "abbreviation": "Rev-Analysis",
                            "n_procedures": rev_result.data.get("total_revisions"),
                            "data_completeness": 0.82,
                            "strengths": ["Cross-registry comparison", "Detailed reason breakdown"],
                            "limitations": ["Variable classification systems between registries"]
                        }
                    })

            # Fetch threshold proximity analysis if requested
            if "threshold_proximity" in intents:
                # Need study data for proximity check
                study_data = results.get("data", {}).get("rates", {})
                prox_context = AgentContext(
                    request_id=f"{request_id}-reg-prox",
                    protocol_id=study_id,
                    parameters={
                        "query_type": "threshold_proximity",
                        "study_data": study_data
                    }
                )
                prox_result = await reg_agent.run(prox_context)
                if prox_result.success:
                    if results["registry"] is None:
                        results["registry"] = {}
                    results["registry"]["threshold_proximity"] = prox_result.data
                    n_warnings = prox_result.data.get("n_warnings", 0)
                    if n_warnings > 0:
                        results["sources"].append({
                            "type": "registry",
                            "reference": f"Threshold Proximity Analysis ({n_warnings} warnings)",
                            "confidence": 0.95,
                            "confidence_level": "high" if n_warnings < 2 else "moderate",
                            "lineage": DataLineage.CALCULATED.value,
                            "metadata": {
                                "abbreviation": "Threshold-Check",
                                "data_completeness": 1.0,
                                "strengths": ["Real-time comparison to safety thresholds"],
                                "limitations": ["Based on current snapshot of study data"]
                            }
                        })

            # Fetch outcomes by indication if requested
            if "outcomes_by_indication" in intents:
                ind_context = AgentContext(
                    request_id=f"{request_id}-reg-ind",
                    protocol_id=study_id,
                    parameters={"query_type": "outcomes_by_indication"}
                )
                ind_result = await reg_agent.run(ind_context)
                if ind_result.success:
                    if results["registry"] is None:
                        results["registry"] = {}
                    results["registry"]["outcomes_by_indication"] = ind_result.data
                    n_ind_regs = ind_result.data.get('n_registries_with_data', 0)
                    results["sources"].append({
                        "type": "registry",
                        "reference": f"Indication-Stratified Outcomes ({n_ind_regs} registries)",
                        "confidence": 0.85,
                        "confidence_level": "high",
                        "lineage": DataLineage.AGGREGATED.value,
                        "metadata": {
                            "abbreviation": "Ind-Outcomes",
                            "data_completeness": 0.78,
                            "strengths": ["Stratified by revision indication", "Long-term outcome data"],
                            "limitations": ["Variable indication definitions", "Not all registries report"]
                        }
                    })

            # Fetch registry metadata if requested
            if "registry_metadata" in intents:
                meta_context = AgentContext(
                    request_id=f"{request_id}-reg-meta",
                    protocol_id=study_id,
                    parameters={"query_type": "metadata"}
                )
                meta_result = await reg_agent.run(meta_context)
                if meta_result.success:
                    if results["registry"] is None:
                        results["registry"] = {}
                    results["registry"]["metadata"] = meta_result.data
                    n_meta_regs = meta_result.data.get('n_registries', 0)
                    results["sources"].append({
                        "type": "registry",
                        "reference": f"Registry Data Quality Assessment ({n_meta_regs} registries)",
                        "confidence": 0.95,
                        "confidence_level": "high",
                        "lineage": DataLineage.RAW_DATA.value,
                        "metadata": {
                            "abbreviation": "Quality-Meta",
                            "data_completeness": 1.0,
                            "strengths": ["Registry methodology documentation", "Completeness metrics"],
                            "limitations": ["Self-reported quality metrics"]
                        }
                    })

            # Find closest registry match if requested
            if "closest_registry" in intents:
                # Need study metrics for closest match
                study_data = results.get("data", {}).get("rates", {})
                study_metrics = {}
                if "revision_rate" in study_data:
                    study_metrics["revision_rate_2yr"] = study_data["revision_rate"]
                if "survival_2yr" in study_data:
                    study_metrics["survival_2yr"] = study_data["survival_2yr"]

                if study_metrics:
                    closest_context = AgentContext(
                        request_id=f"{request_id}-reg-closest",
                        protocol_id=study_id,
                        parameters={
                            "query_type": "closest",
                            "study_metrics": study_metrics
                        }
                    )
                    closest_result = await reg_agent.run(closest_context)
                    if closest_result.success:
                        if results["registry"] is None:
                            results["registry"] = {}
                        results["registry"]["closest_match"] = closest_result.data
                        closest_reg = closest_result.data.get("closest_registry", {})
                        distance = closest_result.data.get('distance', 0)
                        results["sources"].append({
                            "type": "registry",
                            "reference": f"Closest Match: {closest_reg.get('name', 'Unknown')} (distance: {distance:.4f})",
                            "confidence": max(0.5, 1.0 - distance),  # Confidence inversely related to distance
                            "confidence_level": "high" if distance < 0.1 else "moderate" if distance < 0.2 else "low",
                            "lineage": DataLineage.CALCULATED.value,
                            "metadata": {
                                "abbreviation": closest_reg.get("abbreviation"),
                                "report_year": closest_reg.get("report_year"),
                                "n_procedures": closest_reg.get("n_procedures"),
                                "data_completeness": 0.90,
                                "strengths": ["Statistical similarity matching", "Multi-metric comparison"],
                                "limitations": ["Distance metric may not capture all relevant factors"]
                            }
                        })

        except Exception as e:
            logger.warning(f"Registry agent error: {e}")

    return results


def build_agent_context(agent_results: Dict[str, Any], page_context: str) -> str:
    """
    Build comprehensive context from agent results for LLM prompt.
    """
    context_parts = []

    context_parts.append(f"You are an AI assistant for the H-34 DELTA Revision Cup clinical study ({page_context} view).")
    context_parts.append("")

    # Add study data context
    if agent_results.get("data"):
        data = agent_results["data"]
        context_parts.append("=== STUDY DATA ===")
        context_parts.append(f"Total patients: {data.get('n_patients', 'N/A')}")
        context_parts.append(f"Total adverse events: {data.get('n_adverse_events', 'N/A')}")
        context_parts.append(f"SAEs: {data.get('n_sae', 'N/A')}")

        rates = data.get("rates", {})
        if rates:
            context_parts.append(f"Revision rate: {rates.get('revision_rate', 'N/A')}")
            context_parts.append(f"Fracture rate: {rates.get('fracture_rate', 'N/A')}")
            context_parts.append(f"Dislocation rate: {rates.get('dislocation_rate', 'N/A')}")
            context_parts.append(f"Infection rate: {rates.get('infection_rate', 'N/A')}")
        context_parts.append("")

    # Add literature benchmarks context
    if agent_results.get("literature"):
        lit = agent_results["literature"]
        context_parts.append("=== LITERATURE BENCHMARKS ===")

        benchmarks = lit.get("aggregate_benchmarks", {})
        if benchmarks:
            if "revision_rate_2yr" in benchmarks:
                rev = benchmarks["revision_rate_2yr"]
                context_parts.append(f"Literature revision rate (2yr): mean {rev.get('mean', 'N/A')}, range {rev.get('range', 'N/A')}")
            if "mcid_achievement" in benchmarks:
                mcid = benchmarks["mcid_achievement"]
                context_parts.append(f"MCID achievement rate: mean {mcid.get('mean', 'N/A')}, range {mcid.get('range', 'N/A')}")
            if "hhs_improvement" in benchmarks:
                hhs = benchmarks["hhs_improvement"]
                context_parts.append(f"HHS improvement: mean {hhs.get('mean', 'N/A')} points, range {hhs.get('range', 'N/A')}")

        # Add risk factors with hazard ratios
        risk_factors = lit.get("risk_factors", {})
        if risk_factors and "factors" in risk_factors:
            context_parts.append("")
            context_parts.append("Literature-derived hazard ratios for revision risk:")
            for rf in risk_factors.get("factors", [])[:10]:  # Top 10 risk factors
                hr = rf.get("hazard_ratio", "N/A")
                ci = rf.get("confidence_interval", [])
                source = rf.get("source", "literature")
                context_parts.append(f"  - {rf.get('factor', 'Unknown')}: HR {hr} (95% CI: {ci}) - Source: {source}")
        context_parts.append("")

    # Add registry benchmarks context
    if agent_results.get("registry"):
        reg = agent_results["registry"]
        context_parts.append("=== REGISTRY BENCHMARKS ===")

        # Check if we have multi-registry data (all 5 registries)
        if "registries" in reg and isinstance(reg["registries"], list):
            # Multi-registry format
            context_parts.append(f"Total registries: {reg.get('n_registries', len(reg['registries']))}")
            context_parts.append(f"Total procedures across all registries: {reg.get('total_procedures', 'N/A'):,}")
            context_parts.append("")
            context_parts.append("Individual Registry Data:")

            for registry in reg["registries"]:
                abbr = registry.get("abbreviation", registry.get("id", "Unknown"))
                context_parts.append(f"  {abbr}:")
                context_parts.append(f"    - Full name: {registry.get('name', 'N/A')}")
                context_parts.append(f"    - Procedures: {registry.get('n_procedures', 'N/A'):,}")
                context_parts.append(f"    - 2-year survival: {registry.get('survival_2yr', 'N/A')}")
                context_parts.append(f"    - 2-year revision rate: {registry.get('revision_rate_2yr', 'N/A')}")
                context_parts.append(f"    - Revision rate (median): {registry.get('revision_rate_median', 'N/A')}")
                if registry.get("survival_5yr"):
                    context_parts.append(f"    - 5-year survival: {registry.get('survival_5yr')}")
                if registry.get("survival_10yr"):
                    context_parts.append(f"    - 10-year survival: {registry.get('survival_10yr')}")

            # Add summary statistics
            summary = reg.get("summary", {})
            if summary:
                context_parts.append("")
                context_parts.append("Summary across all registries:")
                rev_summary = summary.get("revision_rate_2yr", {})
                if rev_summary:
                    context_parts.append(f"  Revision rate range: {rev_summary.get('min', 'N/A')} - {rev_summary.get('max', 'N/A')}")
                    context_parts.append(f"  Best performing registry: {rev_summary.get('best_registry', 'N/A')}")
                surv_summary = summary.get("survival_2yr", {})
                if surv_summary:
                    context_parts.append(f"  Survival rate range: {surv_summary.get('min', 'N/A')} - {surv_summary.get('max', 'N/A')}")
                    context_parts.append(f"  Best performing registry: {surv_summary.get('best_registry', 'N/A')}")

            # Add pooled norms if available
            pooled = reg.get("pooled_norms", {})
            if pooled:
                context_parts.append("")
                context_parts.append("Pooled norms (aggregated from all registries):")
                surv_rates = pooled.get("survival_rates", {})
                if "survival_1yr" in surv_rates:
                    s1 = surv_rates["survival_1yr"]
                    context_parts.append(f"  Pooled 1-year survival: mean {s1.get('mean', 'N/A')}, range {s1.get('range', 'N/A')}")
                if "survival_2yr" in surv_rates:
                    s2 = surv_rates["survival_2yr"]
                    context_parts.append(f"  Pooled 2-year survival: mean {s2.get('mean', 'N/A')}, range {s2.get('range', 'N/A')}")
                if "survival_5yr" in surv_rates:
                    s5 = surv_rates["survival_5yr"]
                    context_parts.append(f"  Pooled 5-year survival: mean {s5.get('mean', 'N/A')}, range {s5.get('range', 'N/A')}")
                if "survival_10yr" in surv_rates:
                    s10 = surv_rates["survival_10yr"]
                    context_parts.append(f"  Pooled 10-year survival: mean {s10.get('mean', 'N/A')}, range {s10.get('range', 'N/A')}")
                rev_rates = pooled.get("revision_rates", {})
                if "revision_rate_2yr" in rev_rates:
                    r2 = rev_rates["revision_rate_2yr"]
                    context_parts.append(f"  Pooled 2-year revision rate: mean {r2.get('mean', 'N/A')}, range {r2.get('range', 'N/A')}")

        else:
            # Single registry format (legacy - primary registry only)
            context_parts.append(f"Registry: {reg.get('name', 'N/A')}")
            context_parts.append(f"Report year: {reg.get('report_year', 'N/A')}")
            context_parts.append(f"Total procedures: {reg.get('n_procedures', 'N/A')}")
            context_parts.append(f"2-year survival: {reg.get('survival_2yr', 'N/A')}")
            context_parts.append(f"2-year revision rate (median): {reg.get('revision_rate_median', 'N/A')}")
            context_parts.append(f"2-year revision rate (75th percentile): {reg.get('revision_rate_p75', 'N/A')}")
            context_parts.append(f"2-year revision rate (95th percentile): {reg.get('revision_rate_p95', 'N/A')}")

        thresholds = reg.get("thresholds", {})
        if thresholds:
            context_parts.append("")
            context_parts.append("Registry concern thresholds:")
            concern = thresholds.get("concern_thresholds", {})
            for metric, value in concern.items():
                context_parts.append(f"  - {metric}: {value}")
            context_parts.append("")
            context_parts.append("Registry risk thresholds:")
            risk = thresholds.get("risk_thresholds", {})
            for metric, value in risk.items():
                context_parts.append(f"  - {metric}: {value}")

        # Add revision reasons analysis
        rev_reasons = reg.get("revision_reasons", {})
        if rev_reasons and isinstance(rev_reasons, dict) and rev_reasons.get("by_registry"):
            context_parts.append("")
            context_parts.append("=== REVISION REASONS ANALYSIS ===")
            context_parts.append(f"Registries with revision reason data: {rev_reasons.get('n_registries_with_data', 0)}")

            # Show cross-registry comparison
            cross_compare = rev_reasons.get("cross_registry_comparison", {})
            if cross_compare:
                context_parts.append("")
                context_parts.append("Revision reasons across registries:")
                for reason_name, reason_data in list(cross_compare.items())[:5]:  # Top 5 reasons
                    stats = reason_data.get("statistics", {})
                    context_parts.append(f"  {reason_data.get('reason', reason_name)}:")
                    context_parts.append(f"    - Range: {stats.get('range_formatted', 'N/A')}")
                    context_parts.append(f"    - Highest: {reason_data.get('highest_registry', 'N/A')}")
                    context_parts.append(f"    - Lowest: {reason_data.get('lowest_registry', 'N/A')}")

            # Add insights
            insights = rev_reasons.get("insights", [])
            if insights:
                context_parts.append("")
                context_parts.append("Key insights:")
                for insight in insights:
                    context_parts.append(f"  - {insight}")

        # Add threshold proximity warnings
        prox_data = reg.get("threshold_proximity", {})
        if prox_data and isinstance(prox_data, dict):
            context_parts.append("")
            context_parts.append("=== THRESHOLD PROXIMITY ANALYSIS ===")
            context_parts.append(f"Number of warnings: {prox_data.get('n_warnings', 0)}")
            context_parts.append(f"Proximity threshold: {prox_data.get('proximity_threshold_used', '20%')}")

            warnings = prox_data.get("proximity_warnings", [])
            if warnings:
                context_parts.append("")
                context_parts.append("Proximity warnings:")
                for w in warnings:
                    context_parts.append(f"  - {w.get('message', 'Warning')}")

            recommendation = prox_data.get("recommendation", "")
            if recommendation:
                context_parts.append("")
                context_parts.append(f"Recommendation: {recommendation}")

        # Add outcomes by indication
        ind_data = reg.get("outcomes_by_indication", {})
        if ind_data and isinstance(ind_data, dict) and ind_data.get("by_registry"):
            context_parts.append("")
            context_parts.append("=== OUTCOMES BY REVISION INDICATION ===")

            for reg_outcomes in ind_data.get("by_registry", []):
                context_parts.append(f"  {reg_outcomes.get('registry_name', 'Unknown')}:")
                for ind in reg_outcomes.get("indications", [])[:5]:  # Top 5
                    context_parts.append(f"    - {ind.get('indication_formatted', ind.get('indication'))}: " +
                                       f"5yr survival {ind.get('survival_5yr_formatted', 'N/A')}")

            insights = ind_data.get("insights", [])
            if insights:
                context_parts.append("")
                context_parts.append("Key insights:")
                for insight in insights:
                    context_parts.append(f"  - {insight}")

        # Add registry metadata/quality
        meta_data = reg.get("metadata", {})
        if meta_data and isinstance(meta_data, dict) and meta_data.get("registries"):
            context_parts.append("")
            context_parts.append("=== REGISTRY DATA QUALITY ===")
            context_parts.append(f"Total global procedures: {meta_data.get('total_global_procedures', 0):,}")
            context_parts.append(f"Data years range: {meta_data.get('data_years_range', 'N/A')}")

            for reg_meta in meta_data.get("registries", []):
                abbr = reg_meta.get("abbreviation", "Unknown")
                completeness = reg_meta.get("data_completeness", {})
                context_parts.append(f"  {abbr}:")
                context_parts.append(f"    - Data completeness: {completeness.get('score', 'N/A')}")
                strengths = reg_meta.get("strengths", [])
                if strengths:
                    context_parts.append(f"    - Strengths: {strengths[0]}")
                limitations = reg_meta.get("limitations", [])
                if limitations:
                    context_parts.append(f"    - Limitation: {limitations[0]}")

            general_limitations = meta_data.get("general_limitations", [])
            if general_limitations:
                context_parts.append("")
                context_parts.append("General limitations to note:")
                for lim in general_limitations[:3]:
                    context_parts.append(f"  - {lim}")

        # Add closest registry match
        closest = reg.get("closest_match", {})
        if closest and isinstance(closest, dict) and closest.get("closest_registry"):
            context_parts.append("")
            context_parts.append("=== CLOSEST REGISTRY MATCH ===")
            closest_reg = closest.get("closest_registry", {})
            context_parts.append(f"Most similar registry: {closest_reg.get('name', 'Unknown')}")
            context_parts.append(f"Similarity distance: {closest.get('distance', 'N/A')}")
            context_parts.append(f"Metric contributions to match:")
            for metric, contrib in closest.get("metric_contributions", {}).items():
                context_parts.append(f"  - {metric}: {contrib}")

        context_parts.append("")

    return "\n".join(context_parts)


# Fallback context prompts (used if agents fail)
FALLBACK_CONTEXT = {
    "dashboard": "Executive dashboard for H-34 clinical study overview.",
    "readiness": "Regulatory submission readiness assessment.",
    "safety": "Safety signal analysis and monitoring.",
    "deviations": "Protocol deviation detection and analysis.",
    "risk": "Patient risk stratification and prediction."
}


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a natural language query with multi-agent orchestration.

    This endpoint:
    1. Detects question intent (what data sources are needed)
    2. Queries relevant agents (Data, Literature, Registry)
    3. Builds comprehensive context from agent responses
    4. Generates response with full source provenance
    """
    try:
        llm = LLMService()

        # Step 1: Detect what agents to query based on question (LLM-based with keyword fallback)
        intents = await detect_question_intent_llm(request.message, request.context)
        logger.info(f"Detected intents for question: {intents}")

        # Step 2: Query relevant agents
        agent_results = await query_agents(intents, request.study_id)

        # Step 3: Build context from agent results
        agent_context = build_agent_context(agent_results, request.context)

        # Fallback if no agent data retrieved
        if not agent_context.strip() or agent_context == f"You are an AI assistant for the H-34 DELTA Revision Cup clinical study ({request.context} view).\n":
            agent_context = FALLBACK_CONTEXT.get(request.context, FALLBACK_CONTEXT["dashboard"])

        # Build conversation history
        history_text = ""
        if request.history:
            for msg in request.history[-5:]:  # Last 5 messages for context
                history_text += f"\n{msg.role.upper()}: {msg.content}"

        # Build multi-source synthesis instructions if applicable
        multi_source_instructions = ""
        if "multi_source" in intents:
            multi_source_instructions = """

MULTI-SOURCE SYNTHESIS REQUIREMENTS:
This query requires synthesizing data from multiple sources. You MUST:
1. Cross-reference registry data with literature benchmarks - show where they agree/differ
2. Include our clinical study data as the primary comparison point
3. Structure your response to clearly show:
   - Our study results (H-34 clinical data)
   - Registry benchmarks (international real-world data)
   - Literature benchmarks (published research)
4. Highlight any discrepancies or concordances between sources
5. Provide a synthesized conclusion that integrates all data sources
6. For product-specific queries (Delta PF, ceramic liners, etc.), cite product-specific literature where available
"""

        # Build full prompt with agent context
        prompt = f"""{agent_context}

CONVERSATION HISTORY:{history_text}

USER QUESTION: {request.message}
{multi_source_instructions}
RESPONSE REQUIREMENTS:

1. STRUCTURE YOUR RESPONSE:
   - Start with a direct answer to the question
   - Provide supporting data with explicit citations
   - End with context or caveats if applicable

2. CITATION FORMAT (MANDATORY):
   - ALWAYS cite specific numbers with their source: "revision rate of 4.8% (AOANJRR 2023)"
   - For literature: "HR 2.42 (della_valle_2020)"
   - For registry data: "survival rate 97.2% (NJR, n=45,892)"
   - For study data: "15 adverse events (H-34 Study, n=37)"

3. WHEN PRODUCT-SPECIFIC DATA IS MISSING:
   - First state: "Product-specific data for [product] is not available in the current dataset."
   - Then provide: "However, here is the relevant general data that may provide context:"
   - Include available registry benchmarks, survival rates, and revision data
   - This helps users understand the broader landscape even without product-specific data

4. COMPLETENESS CHECKLIST:
   - Include relevant numbers/percentages from the data
   - Compare across registries when multi-registry data is available
   - Reference thresholds or benchmarks when discussing rates
   - Mention sample sizes for context (n=X)

ANTI-HALLUCINATION RULES (STRICT):
- NEVER fabricate citations, authors, or data not in the context above
- For completely out-of-scope queries (weather, stocks, unrelated topics): "This question is outside the scope of the H-34 clinical study data."
- Only cite sources explicitly listed in STUDY DATA, LITERATURE BENCHMARKS, or REGISTRY BENCHMARKS sections

Respond in a professional tone suitable for clinical and regulatory stakeholders."""

        # Call LLM with comprehensive prompt
        response_text = await llm.generate(
            prompt=prompt,
            model="gemini-3-pro-preview",
            temperature=0.3,
            max_tokens=2048  # Increased for comprehensive responses
        )

        # Step 4: Build sources from agent results (real provenance)
        sources = []
        for source_info in agent_results.get("sources", []):
            # Extract metadata if present and convert to SourceMetadata
            metadata_dict = source_info.get("metadata")
            metadata = SourceMetadata(**metadata_dict) if metadata_dict else None

            sources.append(Source(
                type=source_info["type"],
                reference=source_info["reference"],
                confidence=source_info.get("confidence", 1.0),
                confidence_level=source_info.get("confidence_level", "high"),
                lineage=source_info.get("lineage", "raw_data"),
                metadata=metadata
            ))

        # Add inferred sources from response content
        response_lower = response_text.lower()
        source_refs = set(s.reference for s in sources)

        if "protocol" in response_lower and "CIP" not in str(source_refs):
            sources.append(Source(type="protocol", reference="H-34 CIP v2.0"))

        # Generate contextual follow-up suggestions based on intents
        followups = _generate_followups(intents, request.context)

        # Build Evidence object from agent results
        evidence_data = agent_results.get("evidence", {})
        evidence = None
        if evidence_data.get("metrics"):
            evidence_metrics = []
            for metric in evidence_data.get("metrics", []):
                data_points = []
                for dp in metric.get("data_points", []):
                    # Convert raw_data dict to SourceRawData if present
                    raw_data = None
                    if dp.get("raw_data"):
                        raw_data = SourceRawData(**dp["raw_data"])
                    data_points.append(EvidenceDataPoint(
                        source=dp["source"],
                        source_type=dp["source_type"],
                        value=dp.get("value"),
                        value_formatted=dp["value_formatted"],
                        sample_size=dp.get("sample_size"),
                        year=dp.get("year"),
                        context=dp.get("context"),
                        raw_data=raw_data
                    ))
                evidence_metrics.append(EvidenceMetric(
                    metric_name=metric["metric_name"],
                    claim=metric["claim"],
                    aggregated_value=metric.get("aggregated_value"),
                    calculation_method=metric.get("calculation_method"),
                    data_points=data_points,
                    confidence_level=metric.get("confidence_level", "high")
                ))

            evidence = Evidence(
                summary=f"Based on {evidence_data.get('total_sources', 0)} sources with combined n={evidence_data.get('total_sample_size', 0):,}",
                metrics=evidence_metrics,
                total_sources=evidence_data.get("total_sources", 0),
                total_sample_size=evidence_data.get("total_sample_size")
            )

        return ChatResponse(
            response=response_text,
            sources=sources if sources else [Source(type="study_data", reference="H-34 Study Data")],
            evidence=evidence,
            suggested_followups=followups
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_followups(intents: Set[str], context: str) -> List[str]:
    """Generate contextual follow-up suggestions based on query intents."""
    followups = []

    # Multi-source queries get synthesis-focused follow-ups
    if "multi_source" in intents:
        followups.append("How do our outcomes compare to both registries and literature?")
        followups.append("Where do registry benchmarks differ from published literature?")
        followups.append("What is the synthesized view of revision rates across all sources?")

    if "risk" in intents or "literature" in intents:
        followups.append("How do other risk factors compare to literature hazard ratios?")
        followups.append("Which patients have the highest risk scores?")

    if "revision_reasons" in intents:
        followups.append("How do aseptic loosening rates compare across registries?")
        followups.append("What is the primary cause of revision across all registries?")
    elif "threshold_proximity" in intents:
        followups.append("What metrics are closest to exceeding concern thresholds?")
        followups.append("What is the safety margin on our revision rate?")
    elif "outcomes_by_indication" in intents:
        followups.append("Which revision indications have the worst survival outcomes?")
        followups.append("How does infection-related revision survival compare to loosening?")
    elif "registry_metadata" in intents:
        followups.append("What are the key limitations of AOANJRR data?")
        followups.append("Which registry has the most complete long-term data?")
    elif "closest_registry" in intents:
        followups.append("How does our study compare to the closest matching registry?")
        followups.append("What differentiates our outcomes from the closest registry?")
    elif "multi_registry" in intents:
        followups.append("Which registry has outcomes most similar to our study?")
        followups.append("How do we rank against all 5 international registries?")
    elif "registry" in intents:
        followups.append("Compare our rates to all 5 international registries")
        followups.append("What percentile is our revision rate across all registries?")

    if "data" in intents:
        followups.append("What are the most common adverse event types?")
        followups.append("How close are we to any concern thresholds?")

    if context == "safety":
        followups.append("Are there any safety signals requiring DSMB review?")
        followups.append("What is the threshold proximity for our key metrics?")
    elif context == "risk":
        followups.append("What interventions could reduce risk for high-risk patients?")

    # Add new capability-focused suggestions if no specific intent
    if len(followups) < 3:
        followups.extend([
            "What are the primary causes of revision across registries?",
            "How close are our metrics to concern thresholds?",
            "Which registry has outcomes most similar to our study?",
            "What are the data quality limitations to consider?"
        ])

    # Ensure we have at least some suggestions
    if not followups:
        followups = [
            "What should I focus on next?",
            "How does this compare across all registries?",
            "What are the threshold proximity warnings?"
        ]

    return followups[:4]  # Limit to 4 suggestions


# ============================================================================
# CODE GENERATION ENDPOINT
# ============================================================================

class CodeGenerationRequest(BaseModel):
    """Request for code generation."""
    request: str = Field(..., description="Natural language description of the code to generate")
    language: Optional[str] = Field(None, description="Programming language: python, r, sql, c (auto-detected if not specified)")
    execute: bool = Field(default=False, description="Whether to execute the code (only SQL supported)")
    study_id: str = Field(default="H-34", description="Study identifier")


class CodeGenerationResponse(BaseModel):
    """Response from code generation endpoint."""
    success: bool
    language: str
    code: str
    explanation: str
    execution_result: Optional[str] = None
    execution_error: Optional[str] = None
    data_preview: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    suggested_followups: List[str] = []


def is_code_generation_request(message: str) -> bool:
    """Check if a message is requesting code generation."""
    message_lower = message.lower()
    for keyword in INTENT_KEYWORDS["code_generation"]:
        if keyword in message_lower:
            return True
    return False


@router.post("/generate-code", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """
    Generate R, Python, SQL, or C code for clinical research ad-hoc queries.
    
    The code agent understands:
    - Clinical domain language (Kaplan-Meier, HHS, revision rates, etc.)
    - H-34 DELTA study data model and database schema
    - Statistical methodologies for clinical research
    
    Examples:
    - "Write R code for a Kaplan-Meier curve comparing our cohort to the 94% registry benchmark"
    - "Show me Python code to calculate mean HHS improvement from baseline to 2-year follow-up"
    - "SQL query to find all patients with revision surgery"
    """
    try:
        code_agent = get_code_agent()
        
        # Parse language if provided
        language = None
        if request.language:
            try:
                language = CodeLanguage(request.language.lower())
            except ValueError:
                pass
        
        result = await code_agent.generate_code(
            request=request.request,
            language=language,
            execute=request.execute
        )
        
        # Generate follow-up suggestions
        followups = []
        request_lower = request.request.lower()
        
        if "kaplan" in request_lower or "survival" in request_lower:
            followups.extend([
                "Generate code to compare survival curves by patient subgroups",
                "Write code for Cox proportional hazards regression"
            ])
        elif "hhs" in request_lower or "score" in request_lower:
            followups.extend([
                "Generate code to calculate MCID achievement rates",
                "Write code to plot score distributions by follow-up visit"
            ])
        elif "adverse" in request_lower or "safety" in request_lower:
            followups.extend([
                "Generate code to calculate adverse event rates by type",
                "Write code for safety signal detection analysis"
            ])
        else:
            followups.extend([
                "Generate a Kaplan-Meier survival analysis",
                "Write code to analyze HHS improvement from baseline"
            ])
        
        return CodeGenerationResponse(
            success=result.success,
            language=result.language,
            code=result.code,
            explanation=result.explanation,
            execution_result=result.execution_result,
            execution_error=result.execution_error,
            data_preview=result.data_preview,
            warnings=result.warnings,
            suggested_followups=followups[:3]
        )
        
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
