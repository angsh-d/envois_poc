"""
Statistical Analysis Service for Clinical Intelligence Platform.

Provides statistical correlation analysis, hypothesis testing, and
advanced analytics to transform data into actionable intelligence.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

logger = logging.getLogger(__name__)

# Try to import scipy and numpy for statistical functions
try:
    import numpy as np
    from scipy import stats
    from scipy.stats import pearsonr, spearmanr, chi2_contingency, ttest_ind, mannwhitneyu
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy/numpy not available - statistical functions will be limited")


class CorrelationType(str, Enum):
    """Type of correlation analysis."""
    PEARSON = "pearson"      # Linear correlation
    SPEARMAN = "spearman"    # Rank correlation
    POINT_BISERIAL = "point_biserial"  # Continuous vs binary


class HypothesisType(str, Enum):
    """Type of hypothesis test."""
    T_TEST = "t_test"
    MANN_WHITNEY = "mann_whitney"
    CHI_SQUARE = "chi_square"
    FISHER_EXACT = "fisher_exact"
    ANOVA = "anova"


class SignificanceLevel(str, Enum):
    """Significance level interpretation."""
    HIGHLY_SIGNIFICANT = "highly_significant"  # p < 0.001
    SIGNIFICANT = "significant"                 # p < 0.05
    MARGINALLY_SIGNIFICANT = "marginally_significant"  # p < 0.10
    NOT_SIGNIFICANT = "not_significant"         # p >= 0.10


@dataclass
class CorrelationResult:
    """Result of correlation analysis."""
    variable_1: str
    variable_2: str
    correlation_type: CorrelationType
    coefficient: float
    p_value: float
    sample_size: int
    significance: SignificanceLevel
    interpretation: str
    confidence_interval: Optional[Tuple[float, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "variable_1": self.variable_1,
            "variable_2": self.variable_2,
            "correlation_type": self.correlation_type.value,
            "coefficient": round(self.coefficient, 4),
            "p_value": round(self.p_value, 6),
            "sample_size": self.sample_size,
            "significance": self.significance.value,
            "interpretation": self.interpretation,
            "confidence_interval": [round(ci, 4) for ci in self.confidence_interval] if self.confidence_interval else None,
        }


@dataclass
class HypothesisTestResult:
    """Result of hypothesis test."""
    test_type: HypothesisType
    test_statistic: float
    p_value: float
    degrees_of_freedom: Optional[int]
    sample_sizes: Dict[str, int]
    significance: SignificanceLevel
    null_hypothesis: str
    alternative_hypothesis: str
    conclusion: str
    effect_size: Optional[float] = None
    effect_size_interpretation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_type": self.test_type.value,
            "test_statistic": round(self.test_statistic, 4),
            "p_value": round(self.p_value, 6),
            "degrees_of_freedom": self.degrees_of_freedom,
            "sample_sizes": self.sample_sizes,
            "significance": self.significance.value,
            "null_hypothesis": self.null_hypothesis,
            "alternative_hypothesis": self.alternative_hypothesis,
            "conclusion": self.conclusion,
            "effect_size": round(self.effect_size, 4) if self.effect_size else None,
            "effect_size_interpretation": self.effect_size_interpretation,
        }


@dataclass
class RiskFactorAnalysis:
    """Analysis of a risk factor's association with outcome."""
    factor_name: str
    factor_type: str  # "continuous" or "categorical"
    outcome_name: str
    association_strength: str  # "strong", "moderate", "weak", "none"
    statistical_test: str
    test_result: Dict[str, Any]
    odds_ratio: Optional[float] = None
    hazard_ratio: Optional[float] = None
    relative_risk: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    interpretation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "factor_name": self.factor_name,
            "factor_type": self.factor_type,
            "outcome_name": self.outcome_name,
            "association_strength": self.association_strength,
            "statistical_test": self.statistical_test,
            "test_result": self.test_result,
            "odds_ratio": round(self.odds_ratio, 2) if self.odds_ratio else None,
            "hazard_ratio": round(self.hazard_ratio, 2) if self.hazard_ratio else None,
            "relative_risk": round(self.relative_risk, 2) if self.relative_risk else None,
            "confidence_interval": [round(ci, 2) for ci in self.confidence_interval] if self.confidence_interval else None,
            "interpretation": self.interpretation,
        }


class StatisticalAnalysisService:
    """
    Service for statistical analysis of clinical data.

    Features:
    - Correlation analysis (Pearson, Spearman)
    - Hypothesis testing (t-test, chi-square, Mann-Whitney)
    - Risk factor analysis
    - Trend detection
    """

    def __init__(self):
        """Initialize statistical analysis service."""
        if not SCIPY_AVAILABLE:
            logger.warning("Statistical analysis will be limited without scipy")

    def _get_significance_level(self, p_value: float) -> SignificanceLevel:
        """Determine significance level from p-value."""
        if p_value < 0.001:
            return SignificanceLevel.HIGHLY_SIGNIFICANT
        elif p_value < 0.05:
            return SignificanceLevel.SIGNIFICANT
        elif p_value < 0.10:
            return SignificanceLevel.MARGINALLY_SIGNIFICANT
        else:
            return SignificanceLevel.NOT_SIGNIFICANT

    def _interpret_correlation(self, coefficient: float) -> str:
        """Interpret correlation coefficient strength."""
        abs_coef = abs(coefficient)
        direction = "positive" if coefficient > 0 else "negative"

        if abs_coef >= 0.7:
            strength = "strong"
        elif abs_coef >= 0.4:
            strength = "moderate"
        elif abs_coef >= 0.2:
            strength = "weak"
        else:
            return "negligible correlation"

        return f"{strength} {direction} correlation"

    def calculate_correlation(
        self,
        x: List[float],
        y: List[float],
        x_name: str = "Variable X",
        y_name: str = "Variable Y",
        correlation_type: CorrelationType = CorrelationType.PEARSON,
    ) -> Optional[CorrelationResult]:
        """
        Calculate correlation between two variables.

        Args:
            x: First variable values
            y: Second variable values
            x_name: Name of first variable
            y_name: Name of second variable
            correlation_type: Type of correlation to calculate

        Returns:
            CorrelationResult or None if calculation fails
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available for correlation calculation")
            return None

        # Filter out None/NaN values
        valid_pairs = [(xi, yi) for xi, yi in zip(x, y) if xi is not None and yi is not None]
        if len(valid_pairs) < 3:
            logger.warning("Insufficient valid data pairs for correlation")
            return None

        x_valid, y_valid = zip(*valid_pairs)
        x_arr = np.array(x_valid, dtype=float)
        y_arr = np.array(y_valid, dtype=float)

        # Check for constant values
        if np.std(x_arr) == 0 or np.std(y_arr) == 0:
            logger.warning("Constant values - correlation undefined")
            return None

        try:
            if correlation_type == CorrelationType.PEARSON:
                coefficient, p_value = pearsonr(x_arr, y_arr)
            elif correlation_type == CorrelationType.SPEARMAN:
                coefficient, p_value = spearmanr(x_arr, y_arr)
            else:
                coefficient, p_value = pearsonr(x_arr, y_arr)

            n = len(x_arr)
            significance = self._get_significance_level(p_value)
            interpretation = self._interpret_correlation(coefficient)

            # Calculate confidence interval for correlation
            # Using Fisher's z-transformation (with bounds checking)
            ci = None
            if n > 3 and abs(coefficient) < 0.9999:  # Avoid numerical issues near ±1
                # Clip coefficient to avoid log(0) or log(negative)
                coef_clipped = np.clip(coefficient, -0.9999, 0.9999)
                z = 0.5 * np.log((1 + coef_clipped) / (1 - coef_clipped))
                se = 1 / np.sqrt(n - 3)
                z_low = z - 1.96 * se
                z_high = z + 1.96 * se
                ci_low = (np.exp(2 * z_low) - 1) / (np.exp(2 * z_low) + 1)
                ci_high = (np.exp(2 * z_high) - 1) / (np.exp(2 * z_high) + 1)
                ci = (float(np.clip(ci_low, -1, 1)), float(np.clip(ci_high, -1, 1)))

            return CorrelationResult(
                variable_1=x_name,
                variable_2=y_name,
                correlation_type=correlation_type,
                coefficient=float(coefficient),
                p_value=float(p_value),
                sample_size=n,
                significance=significance,
                interpretation=f"{interpretation} (r={coefficient:.3f}, p={p_value:.4f})",
                confidence_interval=ci,
            )

        except Exception as e:
            logger.error(f"Correlation calculation failed: {e}")
            return None

    def perform_hypothesis_test(
        self,
        group_1: List[float],
        group_2: List[float],
        group_1_name: str = "Group 1",
        group_2_name: str = "Group 2",
        test_type: HypothesisType = HypothesisType.T_TEST,
    ) -> Optional[HypothesisTestResult]:
        """
        Perform hypothesis test comparing two groups.

        Args:
            group_1: Values for first group
            group_2: Values for second group
            group_1_name: Name of first group
            group_2_name: Name of second group
            test_type: Type of statistical test

        Returns:
            HypothesisTestResult or None if test fails
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available for hypothesis testing")
            return None

        # Filter None values
        g1 = [v for v in group_1 if v is not None]
        g2 = [v for v in group_2 if v is not None]

        if len(g1) < 2 or len(g2) < 2:
            logger.warning("Insufficient data for hypothesis test")
            return None

        g1_arr = np.array(g1, dtype=float)
        g2_arr = np.array(g2, dtype=float)

        try:
            if test_type == HypothesisType.T_TEST:
                statistic, p_value = ttest_ind(g1_arr, g2_arr)
                df = len(g1) + len(g2) - 2
                null_h = f"Mean of {group_1_name} equals mean of {group_2_name}"
                alt_h = f"Means of {group_1_name} and {group_2_name} are different"

                # Cohen's d for effect size
                pooled_std = np.sqrt(((len(g1) - 1) * np.var(g1_arr) + (len(g2) - 1) * np.var(g2_arr)) / (len(g1) + len(g2) - 2))
                effect_size = (np.mean(g1_arr) - np.mean(g2_arr)) / pooled_std if pooled_std > 0 else 0

            elif test_type == HypothesisType.MANN_WHITNEY:
                statistic, p_value = mannwhitneyu(g1_arr, g2_arr, alternative='two-sided')
                df = None
                null_h = f"Distribution of {group_1_name} equals {group_2_name}"
                alt_h = f"Distributions are different"
                # Effect size r for Mann-Whitney
                effect_size = 1 - (2 * statistic) / (len(g1) * len(g2))

            else:
                statistic, p_value = ttest_ind(g1_arr, g2_arr)
                df = len(g1) + len(g2) - 2
                null_h = f"No difference between groups"
                alt_h = f"Groups are different"
                effect_size = None

            significance = self._get_significance_level(p_value)

            # Interpret effect size
            effect_interp = None
            if effect_size is not None:
                abs_effect = abs(effect_size)
                if abs_effect >= 0.8:
                    effect_interp = "large effect"
                elif abs_effect >= 0.5:
                    effect_interp = "medium effect"
                elif abs_effect >= 0.2:
                    effect_interp = "small effect"
                else:
                    effect_interp = "negligible effect"

            # Generate conclusion
            if significance in [SignificanceLevel.HIGHLY_SIGNIFICANT, SignificanceLevel.SIGNIFICANT]:
                conclusion = f"Reject null hypothesis. There is a statistically significant difference between {group_1_name} and {group_2_name} (p={p_value:.4f})."
            else:
                conclusion = f"Fail to reject null hypothesis. No statistically significant difference found (p={p_value:.4f})."

            return HypothesisTestResult(
                test_type=test_type,
                test_statistic=float(statistic),
                p_value=float(p_value),
                degrees_of_freedom=df,
                sample_sizes={group_1_name: len(g1), group_2_name: len(g2)},
                significance=significance,
                null_hypothesis=null_h,
                alternative_hypothesis=alt_h,
                conclusion=conclusion,
                effect_size=float(effect_size) if effect_size is not None else None,
                effect_size_interpretation=effect_interp,
            )

        except Exception as e:
            logger.error(f"Hypothesis test failed: {e}")
            return None

    def analyze_risk_factor(
        self,
        factor_values: List[Any],
        outcome_values: List[bool],
        factor_name: str = "Risk Factor",
        outcome_name: str = "Outcome",
        factor_type: str = "categorical",
    ) -> Optional[RiskFactorAnalysis]:
        """
        Analyze association between a risk factor and binary outcome.

        Args:
            factor_values: Risk factor values
            outcome_values: Binary outcome (True/False for event)
            factor_name: Name of risk factor
            outcome_name: Name of outcome
            factor_type: "categorical" or "continuous"

        Returns:
            RiskFactorAnalysis or None if analysis fails
        """
        # Filter valid pairs
        valid_pairs = [
            (f, o) for f, o in zip(factor_values, outcome_values)
            if f is not None and o is not None
        ]
        if len(valid_pairs) < 10:
            logger.warning("Insufficient data for risk factor analysis")
            return None

        factors, outcomes = zip(*valid_pairs)

        if factor_type == "categorical":
            return self._analyze_categorical_risk_factor(
                list(factors), list(outcomes), factor_name, outcome_name
            )
        else:
            return self._analyze_continuous_risk_factor(
                list(factors), list(outcomes), factor_name, outcome_name
            )

    def _analyze_categorical_risk_factor(
        self,
        factors: List[Any],
        outcomes: List[bool],
        factor_name: str,
        outcome_name: str,
    ) -> Optional[RiskFactorAnalysis]:
        """Analyze categorical risk factor."""
        if not SCIPY_AVAILABLE:
            return None

        # Build contingency table
        factor_levels = list(set(factors))
        if len(factor_levels) < 2:
            return None

        # For binary factor, calculate odds ratio
        if len(factor_levels) == 2:
            level_1, level_2 = factor_levels

            # Count outcomes by level
            a = sum(1 for f, o in zip(factors, outcomes) if f == level_1 and o)  # Exposed, event
            b = sum(1 for f, o in zip(factors, outcomes) if f == level_1 and not o)  # Exposed, no event
            c = sum(1 for f, o in zip(factors, outcomes) if f == level_2 and o)  # Not exposed, event
            d = sum(1 for f, o in zip(factors, outcomes) if f == level_2 and not o)  # Not exposed, no event

            # Calculate odds ratio with proper handling of zero cells
            # Add 0.5 continuity correction when any cell is zero (Haldane-Anscombe correction)
            if a == 0 or b == 0 or c == 0 or d == 0:
                a_adj, b_adj, c_adj, d_adj = a + 0.5, b + 0.5, c + 0.5, d + 0.5
            else:
                a_adj, b_adj, c_adj, d_adj = a, b, c, d

            if b_adj > 0 and c_adj > 0:
                odds_ratio = (a_adj * d_adj) / (b_adj * c_adj)
                # CI for OR using log transformation
                se_log_or = math.sqrt(1/a_adj + 1/b_adj + 1/c_adj + 1/d_adj)
                ci_low = math.exp(math.log(odds_ratio) - 1.96 * se_log_or)
                ci_high = math.exp(math.log(odds_ratio) + 1.96 * se_log_or)
            else:
                odds_ratio = None
                ci_low, ci_high = None, None

            # Chi-square test
            contingency = [[a, b], [c, d]]
            try:
                chi2, p_value, dof, expected = chi2_contingency(contingency)
                test_result = {
                    "chi2": float(chi2),
                    "p_value": float(p_value),
                    "degrees_of_freedom": dof,
                }
            except Exception:
                test_result = {}
                p_value = 1.0

            # Interpret association strength
            if odds_ratio:
                if odds_ratio > 3 or odds_ratio < 0.33:
                    strength = "strong"
                elif odds_ratio > 1.5 or odds_ratio < 0.67:
                    strength = "moderate"
                elif odds_ratio > 1.2 or odds_ratio < 0.83:
                    strength = "weak"
                else:
                    strength = "none"
            else:
                strength = "unknown"

            interpretation = f"{factor_name} shows {strength} association with {outcome_name}"
            if odds_ratio:
                interpretation += f" (OR={odds_ratio:.2f}, 95% CI: {ci_low:.2f}-{ci_high:.2f})"

            return RiskFactorAnalysis(
                factor_name=factor_name,
                factor_type="categorical",
                outcome_name=outcome_name,
                association_strength=strength,
                statistical_test="chi-square",
                test_result=test_result,
                odds_ratio=odds_ratio,
                confidence_interval=(ci_low, ci_high) if ci_low and ci_high else None,
                interpretation=interpretation,
            )

        return None

    def _analyze_continuous_risk_factor(
        self,
        factors: List[float],
        outcomes: List[bool],
        factor_name: str,
        outcome_name: str,
    ) -> Optional[RiskFactorAnalysis]:
        """Analyze continuous risk factor."""
        if not SCIPY_AVAILABLE:
            return None

        # Split by outcome
        with_outcome = [f for f, o in zip(factors, outcomes) if o]
        without_outcome = [f for f, o in zip(factors, outcomes) if not o]

        if len(with_outcome) < 2 or len(without_outcome) < 2:
            return None

        # Mann-Whitney test (non-parametric)
        try:
            statistic, p_value = mannwhitneyu(with_outcome, without_outcome, alternative='two-sided')
            test_result = {
                "U_statistic": float(statistic),
                "p_value": float(p_value),
            }
        except Exception:
            test_result = {}
            p_value = 1.0

        # Calculate effect size (r = Z / sqrt(N))
        n = len(with_outcome) + len(without_outcome)
        z = (statistic - (len(with_outcome) * len(without_outcome) / 2)) / math.sqrt(
            len(with_outcome) * len(without_outcome) * (n + 1) / 12
        )
        effect_r = abs(z) / math.sqrt(n)

        # Interpret strength
        if effect_r > 0.5:
            strength = "strong"
        elif effect_r > 0.3:
            strength = "moderate"
        elif effect_r > 0.1:
            strength = "weak"
        else:
            strength = "none"

        # Compare means
        mean_with = sum(with_outcome) / len(with_outcome)
        mean_without = sum(without_outcome) / len(without_outcome)

        interpretation = (
            f"{factor_name} shows {strength} association with {outcome_name}. "
            f"Mean {factor_name} with {outcome_name}: {mean_with:.2f}, "
            f"without: {mean_without:.2f} (p={p_value:.4f})"
        )

        return RiskFactorAnalysis(
            factor_name=factor_name,
            factor_type="continuous",
            outcome_name=outcome_name,
            association_strength=strength,
            statistical_test="Mann-Whitney U",
            test_result=test_result,
            interpretation=interpretation,
        )

    def detect_trend(
        self,
        values: List[float],
        timestamps: List[Any] = None,
    ) -> Dict[str, Any]:
        """
        Detect trend in time series data.

        Args:
            values: Numeric values over time
            timestamps: Optional timestamps (uses index if not provided)

        Returns:
            Dictionary with trend analysis
        """
        valid_values = [v for v in values if v is not None]
        if len(valid_values) < 3:
            return {"trend": "insufficient_data", "confidence": 0.0}

        n = len(valid_values)
        x = list(range(n))

        if SCIPY_AVAILABLE:
            x_arr = np.array(x)
            y_arr = np.array(valid_values)

            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_arr, y_arr)

            # Interpret trend
            if p_value < 0.05:
                if slope > 0:
                    trend = "increasing"
                else:
                    trend = "decreasing"
                confidence = 1 - p_value
            else:
                trend = "stable"
                confidence = p_value

            return {
                "trend": trend,
                "slope": float(slope),
                "r_squared": float(r_value ** 2),
                "p_value": float(p_value),
                "confidence": float(confidence),
                "interpretation": f"{trend.capitalize()} trend (slope={slope:.4f}, R²={r_value**2:.3f})",
            }

        else:
            # Simple trend without scipy
            first_half = valid_values[:n//2]
            second_half = valid_values[n//2:]

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            diff = second_avg - first_avg
            if abs(diff) < 0.01 * abs(first_avg):
                trend = "stable"
            elif diff > 0:
                trend = "increasing"
            else:
                trend = "decreasing"

            return {
                "trend": trend,
                "first_period_mean": float(first_avg),
                "second_period_mean": float(second_avg),
                "confidence": 0.5,
                "interpretation": f"{trend.capitalize()} trend based on period comparison",
            }

    def calculate_summary_statistics(
        self,
        values: List[float],
        variable_name: str = "Variable",
    ) -> Dict[str, Any]:
        """Calculate summary statistics for a variable."""
        valid = [v for v in values if v is not None]
        if not valid:
            return {"error": "No valid values"}

        n = len(valid)
        mean = sum(valid) / n
        sorted_valid = sorted(valid)

        # Median
        if n % 2 == 0:
            median = (sorted_valid[n//2 - 1] + sorted_valid[n//2]) / 2
        else:
            median = sorted_valid[n//2]

        # Variance and SD
        variance = sum((v - mean) ** 2 for v in valid) / (n - 1) if n > 1 else 0
        std_dev = math.sqrt(variance)

        # Quartiles
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = sorted_valid[q1_idx]
        q3 = sorted_valid[q3_idx]
        iqr = q3 - q1

        return {
            "variable": variable_name,
            "n": n,
            "mean": round(mean, 4),
            "median": round(median, 4),
            "std_dev": round(std_dev, 4),
            "min": round(min(valid), 4),
            "max": round(max(valid), 4),
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
            "range": round(max(valid) - min(valid), 4),
        }


# Singleton instance
_stat_service: Optional[StatisticalAnalysisService] = None


def get_statistical_service() -> StatisticalAnalysisService:
    """Get singleton statistical analysis service instance."""
    global _stat_service
    if _stat_service is None:
        _stat_service = StatisticalAnalysisService()
    return _stat_service
