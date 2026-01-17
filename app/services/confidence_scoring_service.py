"""
Confidence Scoring Service for Clinical Intelligence Platform.

Provides dynamic confidence scoring methodology for:
- Discovery results (literature, registry, FDA, competitive)
- Data source recommendations
- Research findings

Confidence scores are calculated based on multiple factors:
- Data completeness: How much data was found vs expected
- Data recency: How recent the data is
- Source diversity: Number and variety of sources
- Query relevance: How well results match the search criteria
- Statistical quality: Sample sizes, confidence intervals, etc.

Confidence Levels:
- HIGH (>= 0.8): Strong evidence from multiple recent sources
- MODERATE (0.6-0.79): Good evidence with some limitations
- LOW (0.4-0.59): Limited evidence, use with caution
- INSUFFICIENT (< 0.4): Not enough data for reliable conclusions
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """Confidence level classifications."""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass
class ConfidenceScore:
    """Represents a confidence score with breakdown."""
    overall_score: float
    level: ConfidenceLevel
    factors: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""
    methodology: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_score": round(self.overall_score, 2),
            "level": self.level.value,
            "factors": {k: round(v, 2) for k, v in self.factors.items()},
            "explanation": self.explanation,
            "methodology": self.methodology,
        }


class ConfidenceScoringService:
    """
    Service for calculating dynamic confidence scores.

    Uses a multi-factor weighted scoring system:
    - Completeness (30%): Did we find sufficient data?
    - Recency (25%): How recent is the data?
    - Diversity (20%): Multiple independent sources?
    - Relevance (15%): How well do results match criteria?
    - Quality (10%): Statistical quality indicators
    """

    # Factor weights for overall score calculation
    WEIGHTS = {
        "completeness": 0.30,
        "recency": 0.25,
        "diversity": 0.20,
        "relevance": 0.15,
        "quality": 0.10,
    }

    # Thresholds for confidence levels
    LEVEL_THRESHOLDS = {
        ConfidenceLevel.HIGH: 0.80,
        ConfidenceLevel.MODERATE: 0.60,
        ConfidenceLevel.LOW: 0.40,
    }

    def __init__(self):
        """Initialize confidence scoring service."""
        pass

    def _get_level(self, score: float) -> ConfidenceLevel:
        """Determine confidence level from numeric score."""
        if score >= self.LEVEL_THRESHOLDS[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif score >= self.LEVEL_THRESHOLDS[ConfidenceLevel.MODERATE]:
            return ConfidenceLevel.MODERATE
        elif score >= self.LEVEL_THRESHOLDS[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.INSUFFICIENT

    def _calculate_weighted_score(self, factors: Dict[str, float]) -> float:
        """Calculate weighted overall score from factors."""
        score = 0.0
        for factor, weight in self.WEIGHTS.items():
            factor_value = factors.get(factor, 0.5)
            score += factor_value * weight
        return min(max(score, 0.0), 1.0)

    def score_literature_discovery(
        self,
        papers_found: int,
        top_papers: List[Dict[str, Any]],
        search_terms: List[str],
        expected_min: int = 10,
        expected_max: int = 100,
    ) -> ConfidenceScore:
        """
        Calculate confidence score for literature discovery results.

        Args:
            papers_found: Total number of papers found
            top_papers: List of top paper metadata
            search_terms: Search terms used
            expected_min: Minimum expected papers for good confidence
            expected_max: Papers above which diminishing returns

        Returns:
            ConfidenceScore with breakdown
        """
        factors = {}

        # Completeness: Did we find enough papers?
        if papers_found >= expected_max:
            factors["completeness"] = 1.0
        elif papers_found >= expected_min:
            factors["completeness"] = 0.7 + 0.3 * (papers_found - expected_min) / (expected_max - expected_min)
        elif papers_found > 0:
            factors["completeness"] = 0.3 + 0.4 * (papers_found / expected_min)
        else:
            factors["completeness"] = 0.0

        # Recency: How recent are the publications?
        current_year = datetime.now().year
        if top_papers:
            def get_year(p):
                year = p.get("year", 0)
                try:
                    return int(year) if year else 0
                except (ValueError, TypeError):
                    return 0
            recent_count = sum(1 for p in top_papers if get_year(p) >= current_year - 3)
            factors["recency"] = min(recent_count / min(len(top_papers), 5), 1.0)
        else:
            factors["recency"] = 0.0

        # Diversity: Publication type diversity
        if top_papers:
            pub_types = set()
            for p in top_papers:
                insight = p.get("insight", "").lower()
                if "meta-analysis" in insight:
                    pub_types.add("meta-analysis")
                elif "rct" in insight or "randomized" in insight:
                    pub_types.add("rct")
                elif "systematic" in insight:
                    pub_types.add("systematic_review")
                elif "registry" in insight:
                    pub_types.add("registry")
                else:
                    pub_types.add("clinical")
            factors["diversity"] = min(len(pub_types) / 3, 1.0)  # Target 3 types
        else:
            factors["diversity"] = 0.0

        # Relevance: Based on relevance scores if available
        if top_papers:
            avg_relevance = sum(p.get("relevance_score", 0.5) for p in top_papers) / len(top_papers)
            factors["relevance"] = avg_relevance
        else:
            factors["relevance"] = 0.0

        # Quality: Higher weight for high-quality publications
        if top_papers:
            quality_count = sum(
                1 for p in top_papers
                if any(q in p.get("insight", "").lower() for q in ["meta-analysis", "rct", "systematic"])
            )
            factors["quality"] = min(quality_count / min(len(top_papers), 5) * 1.5, 1.0)
        else:
            factors["quality"] = 0.0

        overall = self._calculate_weighted_score(factors)
        level = self._get_level(overall)

        explanation = self._generate_literature_explanation(papers_found, factors, level)

        return ConfidenceScore(
            overall_score=overall,
            level=level,
            factors=factors,
            explanation=explanation,
            methodology="Weighted scoring: Completeness (30%), Recency (25%), Source Diversity (20%), Relevance (15%), Quality (10%)",
        )

    def score_registry_discovery(
        self,
        registries: List[Dict[str, Any]],
        indication: str,
    ) -> ConfidenceScore:
        """
        Calculate confidence score for registry discovery results.

        Args:
            registries: List of registry data
            indication: Clinical indication

        Returns:
            ConfidenceScore with breakdown
        """
        factors = {}

        selected_registries = [r for r in registries if r.get("selected", False)]

        # Completeness: Number of registries with data
        factors["completeness"] = min(len(selected_registries) / 3, 1.0)  # Target 3 registries

        # Recency: Data recency based on data_years
        current_year = datetime.now().year
        recent_count = 0
        for r in selected_registries:
            data_years = r.get("data_years", "")
            if "-" in data_years:
                end_year = data_years.split("-")[-1]
                try:
                    if int(end_year) >= current_year - 2:
                        recent_count += 1
                except ValueError:
                    pass
        factors["recency"] = min(recent_count / max(len(selected_registries), 1), 1.0)

        # Diversity: Geographic diversity
        regions = set(r.get("region", "") for r in selected_registries)
        factors["diversity"] = min(len(regions) / 3, 1.0)  # Target 3 regions

        # Relevance: Based on registry relevance descriptions
        relevance_keywords = ["revision", indication.lower(), "survival", "outcome"]
        relevance_score = 0
        for r in selected_registries:
            rel_text = r.get("relevance", "").lower()
            matches = sum(1 for kw in relevance_keywords if kw in rel_text)
            relevance_score += min(matches / 2, 1.0)
        factors["relevance"] = relevance_score / max(len(selected_registries), 1)

        # Quality: Sample size and survival data availability
        total_procedures = sum(r.get("n_procedures", 0) for r in selected_registries)
        has_survival = sum(1 for r in selected_registries if r.get("has_survival_data", False))

        size_score = min(total_procedures / 100000, 1.0)  # Target 100k procedures
        survival_score = has_survival / max(len(selected_registries), 1)
        factors["quality"] = (size_score + survival_score) / 2

        overall = self._calculate_weighted_score(factors)
        level = self._get_level(overall)

        explanation = self._generate_registry_explanation(selected_registries, factors, level)

        return ConfidenceScore(
            overall_score=overall,
            level=level,
            factors=factors,
            explanation=explanation,
            methodology="Weighted scoring: Completeness (30%), Recency (25%), Geographic Diversity (20%), Relevance (15%), Sample Size & Survival Data (10%)",
        )

    def score_fda_discovery(
        self,
        maude_events: int,
        clearances: int = 0,
        recalls: int = 0,
        device_name: str = "",
    ) -> ConfidenceScore:
        """
        Calculate confidence score for FDA discovery results.

        Args:
            maude_events: Number of MAUDE adverse events found
            clearances: Number of 510(k) clearances found
            device_name: Device name searched

        Returns:
            ConfidenceScore with breakdown
        """
        factors = {}

        # Completeness: Did we find FDA data?
        if maude_events > 0 or clearances > 0:
            factors["completeness"] = 0.8 + 0.2 * min((maude_events + clearances) / 100, 1.0)
        else:
            factors["completeness"] = 0.3  # Some data from API response

        # Recency: FDA data is typically recent
        factors["recency"] = 0.9 if maude_events > 0 else 0.5

        # Diversity: Multiple FDA sources
        sources_used = sum([maude_events > 0, clearances > 0, recalls >= 0])
        factors["diversity"] = sources_used / 3

        # Relevance: Based on event count (some events expected for similar devices)
        if maude_events >= 50:
            factors["relevance"] = 0.9  # Good sample of adverse events
        elif maude_events >= 10:
            factors["relevance"] = 0.7
        elif maude_events > 0:
            factors["relevance"] = 0.5
        else:
            factors["relevance"] = 0.3

        # Quality: FDA is authoritative source
        factors["quality"] = 0.95 if maude_events > 0 else 0.6

        overall = self._calculate_weighted_score(factors)
        level = self._get_level(overall)

        explanation = self._generate_fda_explanation(maude_events, factors, level)

        return ConfidenceScore(
            overall_score=overall,
            level=level,
            factors=factors,
            explanation=explanation,
            methodology="Weighted scoring: Completeness (30%), Recency (25%), Source Coverage (20%), Event Relevance (15%), Data Authority (10%)",
        )

    def score_competitive_discovery(
        self,
        competitors_found: int,
        products: List[Dict[str, Any]],
        market_category: str = "",
    ) -> ConfidenceScore:
        """
        Calculate confidence score for competitive intelligence discovery.

        Args:
            competitors_found: Number of competitors identified
            products: List of competitive products found
            market_category: Product category for context

        Returns:
            ConfidenceScore with breakdown
        """
        factors = {}

        # Completeness: Number of competitors found
        factors["completeness"] = min(competitors_found / 5, 1.0)  # Target 5 competitors

        # Recency: Product data freshness (assume current if found)
        factors["recency"] = 0.85 if competitors_found > 0 else 0.3

        # Diversity: Manufacturer diversity
        if products:
            manufacturers = set(p.get("manufacturer", "") for p in products)
            factors["diversity"] = min(len(manufacturers) / 3, 1.0)
        else:
            factors["diversity"] = 0.0

        # Relevance: Same category products
        if products:
            same_category = sum(1 for p in products if market_category.lower() in p.get("category", "").lower())
            factors["relevance"] = min(same_category / max(len(products), 1) + 0.3, 1.0)
        else:
            factors["relevance"] = 0.3

        # Quality: Products with pricing/feature data
        if products:
            quality_products = sum(1 for p in products if p.get("key_features") or p.get("510k_number"))
            factors["quality"] = min(quality_products / max(len(products), 1) + 0.4, 1.0)
        else:
            factors["quality"] = 0.4

        overall = self._calculate_weighted_score(factors)
        level = self._get_level(overall)

        explanation = self._generate_competitive_explanation(competitors_found, factors, level)

        return ConfidenceScore(
            overall_score=overall,
            level=level,
            factors=factors,
            explanation=explanation,
            methodology="Weighted scoring: Coverage (30%), Recency (25%), Manufacturer Diversity (20%), Category Match (15%), Data Quality (10%)",
        )

    def score_recommendation(
        self,
        recommendation_type: str,
        data_sources_available: int,
        discovery_confidence: float,
        user_context_match: float = 0.8,
    ) -> ConfidenceScore:
        """
        Calculate confidence score for a data source recommendation.

        Args:
            recommendation_type: Type of recommendation (clinical, registry, literature, fda)
            data_sources_available: Number of available data sources
            discovery_confidence: Confidence from discovery phase
            user_context_match: How well recommendation matches user needs

        Returns:
            ConfidenceScore with breakdown
        """
        factors = {}

        # Completeness: Data availability
        factors["completeness"] = min(data_sources_available / 3, 1.0)

        # Recency: Inherit from discovery
        factors["recency"] = discovery_confidence

        # Diversity: Type-specific diversity
        type_diversity = {
            "clinical": 0.9,  # Single source but authoritative
            "registry": 0.85,  # Multiple registries
            "literature": 0.95,  # Many publications
            "fda": 0.8,  # Single regulatory source
        }
        factors["diversity"] = type_diversity.get(recommendation_type, 0.7)

        # Relevance: User context match
        factors["relevance"] = user_context_match

        # Quality: Type-specific quality
        type_quality = {
            "clinical": 0.95,  # Direct patient data
            "registry": 0.90,  # Large population data
            "literature": 0.85,  # Peer-reviewed
            "fda": 0.95,  # Regulatory authority
        }
        factors["quality"] = type_quality.get(recommendation_type, 0.8)

        overall = self._calculate_weighted_score(factors)
        level = self._get_level(overall)

        explanation = f"Recommendation confidence based on {data_sources_available} available data sources with {level.value} discovery evidence."

        return ConfidenceScore(
            overall_score=overall,
            level=level,
            factors=factors,
            explanation=explanation,
            methodology="Weighted scoring: Data Availability (30%), Discovery Confidence (25%), Source Diversity (20%), Context Match (15%), Data Quality (10%)",
        )

    def score_overall_discovery(
        self,
        literature_score: ConfidenceScore,
        registry_score: ConfidenceScore,
        fda_score: ConfidenceScore,
        competitive_score: ConfidenceScore,
    ) -> ConfidenceScore:
        """
        Calculate overall confidence score for entire discovery phase.

        Args:
            literature_score: Literature discovery confidence
            registry_score: Registry discovery confidence
            fda_score: FDA discovery confidence
            competitive_score: Competitive discovery confidence

        Returns:
            Overall ConfidenceScore
        """
        # Weighted average of component scores
        component_weights = {
            "literature": 0.30,
            "registry": 0.30,
            "fda": 0.25,
            "competitive": 0.15,
        }

        overall = (
            literature_score.overall_score * component_weights["literature"] +
            registry_score.overall_score * component_weights["registry"] +
            fda_score.overall_score * component_weights["fda"] +
            competitive_score.overall_score * component_weights["competitive"]
        )

        level = self._get_level(overall)

        factors = {
            "literature": literature_score.overall_score,
            "registry": registry_score.overall_score,
            "fda": fda_score.overall_score,
            "competitive": competitive_score.overall_score,
        }

        explanation = f"Overall discovery confidence: {level.value}. " + self._summarize_discovery_confidence(factors)

        return ConfidenceScore(
            overall_score=overall,
            level=level,
            factors=factors,
            explanation=explanation,
            methodology="Component-weighted: Literature (30%), Registry (30%), FDA (25%), Competitive (15%)",
        )

    def _generate_literature_explanation(
        self,
        papers_found: int,
        factors: Dict[str, float],
        level: ConfidenceLevel,
    ) -> str:
        """Generate human-readable explanation for literature confidence."""
        explanations = []

        if level == ConfidenceLevel.HIGH:
            explanations.append(f"Found {papers_found} relevant publications with strong evidence base.")
        elif level == ConfidenceLevel.MODERATE:
            explanations.append(f"Found {papers_found} relevant publications with moderate evidence.")
        elif level == ConfidenceLevel.LOW:
            explanations.append(f"Limited to {papers_found} publications; additional research recommended.")
        else:
            explanations.append(f"Insufficient publications ({papers_found}) for reliable conclusions.")

        if factors.get("recency", 0) >= 0.8:
            explanations.append("Recent publications (last 3 years) available.")
        elif factors.get("recency", 0) < 0.4:
            explanations.append("Many publications are dated; newer evidence may exist.")

        if factors.get("quality", 0) >= 0.7:
            explanations.append("High-quality evidence (meta-analyses, RCTs) included.")

        return " ".join(explanations)

    def _generate_registry_explanation(
        self,
        registries: List[Dict[str, Any]],
        factors: Dict[str, float],
        level: ConfidenceLevel,
    ) -> str:
        """Generate human-readable explanation for registry confidence."""
        n_registries = len(registries)
        total_procedures = sum(r.get("n_procedures", 0) for r in registries)

        explanations = []

        if level == ConfidenceLevel.HIGH:
            explanations.append(f"{n_registries} registries selected with {total_procedures:,} total procedures.")
        elif level == ConfidenceLevel.MODERATE:
            explanations.append(f"{n_registries} registries available with {total_procedures:,} procedures.")
        else:
            explanations.append(f"Limited registry coverage ({n_registries} registries).")

        if factors.get("diversity", 0) >= 0.8:
            explanations.append("Good geographic diversity across regions.")

        has_survival = sum(1 for r in registries if r.get("has_survival_data", False))
        if has_survival > 0:
            explanations.append(f"{has_survival} registries with survival data.")

        return " ".join(explanations)

    def _generate_fda_explanation(
        self,
        maude_events: int,
        factors: Dict[str, float],
        level: ConfidenceLevel,
    ) -> str:
        """Generate human-readable explanation for FDA confidence."""
        if level == ConfidenceLevel.HIGH:
            return f"Comprehensive FDA surveillance data with {maude_events} adverse events for analysis."
        elif level == ConfidenceLevel.MODERATE:
            return f"FDA data available with {maude_events} events; good baseline for safety monitoring."
        elif level == ConfidenceLevel.LOW:
            return f"Limited FDA events ({maude_events}); may indicate newer device or limited market presence."
        else:
            return "Insufficient FDA data; device may be new to market or have limited US distribution."

    def _generate_competitive_explanation(
        self,
        competitors_found: int,
        factors: Dict[str, float],
        level: ConfidenceLevel,
    ) -> str:
        """Generate human-readable explanation for competitive confidence."""
        if level == ConfidenceLevel.HIGH:
            return f"Identified {competitors_found} key competitors with comprehensive market coverage."
        elif level == ConfidenceLevel.MODERATE:
            return f"Found {competitors_found} competitors; reasonable market landscape view."
        elif level == ConfidenceLevel.LOW:
            return f"Limited competitive data ({competitors_found} products); niche market or emerging category."
        else:
            return "Insufficient competitive intelligence; may indicate novel product category."

    def _summarize_discovery_confidence(self, factors: Dict[str, float]) -> str:
        """Summarize overall discovery confidence."""
        strengths = []
        weaknesses = []

        for source, score in factors.items():
            if score >= 0.8:
                strengths.append(source)
            elif score < 0.5:
                weaknesses.append(source)

        parts = []
        if strengths:
            parts.append(f"Strong evidence from: {', '.join(strengths)}.")
        if weaknesses:
            parts.append(f"Limited data from: {', '.join(weaknesses)}.")

        return " ".join(parts) if parts else "Balanced evidence across sources."


# Singleton instance
_confidence_service: Optional[ConfidenceScoringService] = None


def get_confidence_service() -> ConfidenceScoringService:
    """Get singleton confidence scoring service instance."""
    global _confidence_service
    if _confidence_service is None:
        _confidence_service = ConfidenceScoringService()
    return _confidence_service
