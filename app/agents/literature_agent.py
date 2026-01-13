"""
Literature Agent for Clinical Intelligence Platform.

Responsible for RAG-based literature search and benchmark extraction.
Uses ChromaDB vector store for semantic search over literature PDFs.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)
from data.loaders.yaml_loader import (
    get_doc_loader, LiteratureBenchmarks, RiskFactor, PublicationBenchmark
)
from data.vectorstore import get_vector_store, ChromaVectorStore
from data.loaders.hazard_ratio_extractor import HazardRatioExtractor

logger = logging.getLogger(__name__)


class LiteratureAgent(BaseAgent):
    """
    Agent for literature benchmark extraction and comparison.

    Capabilities:
    - Semantic search over literature PDFs via ChromaDB RAG
    - Load literature benchmarks from Document-as-Code YAML
    - Extract risk factors with hazard ratios
    - Compare study results against published benchmarks
    - Generate literature-supported narratives
    """

    agent_type = AgentType.LITERATURE

    def __init__(self, **kwargs):
        """Initialize literature agent."""
        super().__init__(**kwargs)
        self._loader = get_doc_loader()
        self._benchmarks: Optional[LiteratureBenchmarks] = None
        self._vector_store: Optional[ChromaVectorStore] = None

    def _get_vector_store(self) -> ChromaVectorStore:
        """Get vector store with lazy initialization."""
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store

    def _load_benchmarks(self) -> LiteratureBenchmarks:
        """Load literature benchmarks with caching."""
        if self._benchmarks is None:
            self._benchmarks = self._loader.load_literature_benchmarks()
        return self._benchmarks

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute literature benchmark extraction.

        Args:
            context: Execution context with query parameters

        Returns:
            AgentResult with benchmark data
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        benchmarks = self._load_benchmarks()
        query_type = context.parameters.get("query_type", "all")

        if query_type == "all":
            result.data = self._get_all_benchmarks(benchmarks)
        elif query_type == "metric":
            metric = context.parameters.get("metric")
            if not metric:
                result.success = False
                result.error = "metric parameter required"
                return result
            result.data = self._get_metric_benchmark(benchmarks, metric)
        elif query_type == "risk_factors":
            outcome = context.parameters.get("outcome", "revision")
            result.data = self._get_risk_factors(benchmarks, outcome)
        elif query_type == "compare":
            result.data = await self._compare_to_benchmarks(context, benchmarks)
        elif query_type == "search":
            query = context.parameters.get("query")
            if not query:
                result.success = False
                result.error = "query parameter required for search"
                return result
            n_results = context.parameters.get("n_results", 5)
            result.data = await self._search_literature(query, n_results)
        elif query_type == "rag":
            query = context.parameters.get("query")
            if not query:
                result.success = False
                result.error = "query parameter required for RAG"
                return result
            result.data = await self._rag_query(query, context)
        else:
            result.success = False
            result.error = f"Unknown query_type: {query_type}"
            return result

        # Add source
        result.add_source(
            SourceType.LITERATURE,
            f"Literature benchmarks ({len(benchmarks.publications)} publications)",
            confidence=0.9,
            details={"n_publications": len(benchmarks.publications)}
        )

        return result

    def _get_all_benchmarks(self, benchmarks: LiteratureBenchmarks) -> Dict[str, Any]:
        """Get all aggregate benchmarks."""
        return {
            "n_publications": len(benchmarks.publications),
            "publications": [
                {
                    "id": pub.id,
                    "title": pub.title,
                    "year": pub.year,
                    "n_patients": pub.n_patients,
                    "follow_up_years": pub.follow_up_years,
                }
                for pub in benchmarks.publications
            ],
            "aggregate_benchmarks": benchmarks.aggregate_benchmarks,
            "n_risk_factors": len(benchmarks.all_risk_factors),
        }

    def _get_metric_benchmark(
        self,
        benchmarks: LiteratureBenchmarks,
        metric: str
    ) -> Dict[str, Any]:
        """Get benchmark for a specific metric."""
        benchmark = benchmarks.get_benchmark(metric)
        if not benchmark:
            return {"error": f"No benchmark found for metric: {metric}"}

        # Get per-publication values for this metric
        publication_values = []
        for pub in benchmarks.publications:
            if metric in pub.benchmarks:
                publication_values.append({
                    "publication": pub.id,
                    "year": pub.year,
                    "value": pub.benchmarks[metric],
                })

        return {
            "metric": metric,
            "aggregate": benchmark,
            "publications": publication_values,
        }

    def _get_risk_factors(
        self,
        benchmarks: LiteratureBenchmarks,
        outcome: str
    ) -> Dict[str, Any]:
        """Get risk factors for a specific outcome."""
        factors = benchmarks.get_risk_factors_for_outcome(outcome)

        return {
            "outcome": outcome,
            "n_factors": len(factors),
            "factors": [
                {
                    "factor": rf.factor,
                    "hazard_ratio": rf.hazard_ratio,
                    "confidence_interval": rf.confidence_interval,
                    "source": rf.source,
                }
                for rf in factors
            ],
        }

    async def _compare_to_benchmarks(
        self,
        context: AgentContext,
        benchmarks: LiteratureBenchmarks
    ) -> Dict[str, Any]:
        """Compare study results to literature benchmarks with LLM analysis."""
        study_data = context.parameters.get("study_data", {})

        comparison = {
            "comparisons": [],
            "overall_assessment": None,
        }

        # Compare each metric
        for metric, value in study_data.items():
            benchmark = benchmarks.get_benchmark(metric)
            if benchmark and isinstance(value, (int, float)):
                bench_mean = benchmark.get("mean") or benchmark.get("median")
                if bench_mean:
                    diff = value - bench_mean
                    pct_diff = (diff / bench_mean) * 100 if bench_mean != 0 else 0

                    comparison["comparisons"].append({
                        "metric": metric,
                        "study_value": value,
                        "benchmark_mean": bench_mean,
                        "difference": round(diff, 3),
                        "percent_difference": round(pct_diff, 1),
                        "favorable": self._is_favorable(metric, diff),
                    })

        # Generate LLM narrative if comparisons exist
        if comparison["comparisons"]:
            comparison["overall_assessment"] = await self._generate_comparison_narrative(
                comparison["comparisons"]
            )

        return comparison

    def _is_favorable(self, metric: str, difference: float) -> bool:
        """Determine if a difference is favorable based on metric type."""
        # Higher is better for these metrics
        higher_is_better = [
            "hhs_improvement", "mcid_achievement", "survival",
            "ohs_improvement", "radiographic_stability"
        ]
        # Lower is better for these metrics
        lower_is_better = [
            "revision_rate", "dislocation_rate", "infection_rate",
            "fracture_rate", "complication_rate"
        ]

        for pattern in higher_is_better:
            if pattern in metric.lower():
                return difference >= 0

        for pattern in lower_is_better:
            if pattern in metric.lower():
                return difference <= 0

        return difference >= 0  # Default: higher is better

    async def _search_literature(
        self,
        query: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Semantic search over literature documents using ChromaDB.

        Args:
            query: Search query text
            n_results: Number of results to return

        Returns:
            Search results with content and metadata
        """
        store = self._get_vector_store()
        results = store.search(
            query=query,
            source_type="literature",
            n_results=n_results,
            include_distances=True
        )

        return {
            "query": query,
            "n_results": len(results),
            "results": [
                {
                    "content": r["content"],
                    "source_file": r["metadata"].get("source_file", "unknown"),
                    "page_number": r["metadata"].get("page_number"),
                    "relevance_score": 1 - r.get("distance", 0),  # Convert distance to score
                }
                for r in results
            ],
        }

    async def _rag_query(
        self,
        query: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        RAG-based query: retrieve relevant literature chunks and synthesize with LLM.

        Args:
            query: User question about literature
            context: Execution context

        Returns:
            Synthesized answer with sources
        """
        # Step 1: Retrieve relevant chunks
        n_results = context.parameters.get("n_results", 5)
        search_results = await self._search_literature(query, n_results)

        if not search_results["results"]:
            return {
                "query": query,
                "answer": "No relevant literature found for this query.",
                "sources": [],
            }

        # Step 2: Build context from retrieved chunks
        context_text = "\n\n---\n\n".join([
            f"Source: {r['source_file']} (Page {r['page_number']})\n{r['content']}"
            for r in search_results["results"]
        ])

        # Step 3: Generate answer using LLM
        prompt = self.load_prompt("literature_rag", {
            "query": query,
            "context": context_text,
        })

        answer = await self.call_llm(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.1,
        )

        # Step 4: Return answer with provenance
        return {
            "query": query,
            "answer": answer.strip(),
            "sources": [
                {
                    "file": r["source_file"],
                    "page": r["page_number"],
                    "relevance": round(r["relevance_score"], 3),
                }
                for r in search_results["results"]
            ],
            "n_sources": len(search_results["results"]),
        }

    def search_sync(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Synchronous search for use by other agents.

        Args:
            query: Search query
            n_results: Number of results

        Returns:
            List of search results
        """
        store = self._get_vector_store()
        return store.search(
            query=query,
            source_type="literature",
            n_results=n_results,
            include_distances=True
        )

    async def _generate_comparison_narrative(
        self,
        comparisons: List[Dict[str, Any]]
    ) -> str:
        """Generate narrative comparing results to benchmarks."""
        prompt = self.load_prompt("literature_comparison", {
            "comparisons": str(comparisons),
        })

        narrative = await self.call_llm(
            prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
        )
        return narrative.strip()

    def get_hhs_benchmark(self) -> Dict[str, Any]:
        """Get HHS improvement benchmark."""
        benchmarks = self._load_benchmarks()
        return benchmarks.get_benchmark("hhs_improvement") or {}

    def get_mcid_benchmark(self) -> Dict[str, Any]:
        """Get MCID achievement rate benchmark."""
        benchmarks = self._load_benchmarks()
        return benchmarks.get_benchmark("mcid_achievement") or {}

    def get_revision_rate_benchmark(self) -> Dict[str, Any]:
        """Get revision rate benchmark."""
        benchmarks = self._load_benchmarks()
        return benchmarks.get_benchmark("revision_rate_2yr") or {}

    def get_risk_factor_hr(self, factor: str) -> Optional[float]:
        """Get hazard ratio for a specific risk factor."""
        benchmarks = self._load_benchmarks()
        for rf in benchmarks.all_risk_factors:
            if rf.factor.lower() == factor.lower():
                return rf.hazard_ratio
        return None

    async def extract_hazard_ratios(
        self,
        n_results_per_factor: int = 5
    ) -> Dict[str, Any]:
        """
        Extract hazard ratios dynamically from indexed literature.

        Uses RAG + LLM to find and extract hazard ratios from PDFs,
        with full source attribution.

        Args:
            n_results_per_factor: Number of search results per risk factor

        Returns:
            Dict with extracted hazard ratios and metadata
        """
        extractor = HazardRatioExtractor(
            vector_store=self._get_vector_store(),
            llm_service=self.llm,
            prompt_service=self.prompts,
        )

        # Extract from literature
        extracted = await extractor.extract_from_literature(
            n_results_per_factor=n_results_per_factor
        )

        # Get manually curated HRs from YAML
        benchmarks = self._load_benchmarks()
        manual_hrs = {}
        for rf in benchmarks.all_risk_factors:
            manual_hrs[rf.factor] = rf.hazard_ratio

        # Merge extracted with manual
        merged = extractor.merge_with_manual_hrs(manual_hrs, prefer_extracted=False)

        return {
            "n_extracted": len(extracted),
            "extracted_hrs": extracted,
            "n_curated": len(manual_hrs),
            "curated_hrs": manual_hrs,
            "merged_hrs": merged,
            "extraction_timestamp": datetime.now().isoformat() if extracted else None,
        }

    def get_all_hazard_ratios(self) -> Dict[str, Any]:
        """
        Get all hazard ratios from Document-as-Code YAML.

        Returns:
            Dict with all risk factors and their hazard ratios
        """
        benchmarks = self._load_benchmarks()
        return {
            "n_risk_factors": len(benchmarks.all_risk_factors),
            "risk_factors": [
                {
                    "factor": rf.factor,
                    "hazard_ratio": rf.hazard_ratio,
                    "confidence_interval": rf.confidence_interval,
                    "outcome": rf.outcome,
                    "source": rf.source,
                }
                for rf in benchmarks.all_risk_factors
            ],
            "source": "literature_benchmarks.yaml (Document-as-Code)",
        }
