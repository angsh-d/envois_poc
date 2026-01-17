"""
Proactive Safety Alert Service for Clinical Intelligence Platform.

Monitors safety signals and generates alerts when thresholds are approached or exceeded.
Provides real-time safety intelligence without requiring explicit user queries.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Severity level for safety alerts."""
    CRITICAL = "critical"     # Immediate action required
    WARNING = "warning"       # Approaching threshold
    INFO = "info"            # Notable but not concerning
    RESOLVED = "resolved"    # Previously flagged, now resolved


class AlertCategory(str, Enum):
    """Category of safety alert."""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    THRESHOLD_APPROACHING = "threshold_approaching"
    TREND_DETECTED = "trend_detected"
    OUTLIER_DETECTED = "outlier_detected"
    DATA_QUALITY = "data_quality"
    COMPLIANCE_ISSUE = "compliance_issue"


@dataclass
class SafetyAlert:
    """Individual safety alert."""
    id: str
    category: AlertCategory
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold_value: Optional[float] = None
    benchmark_value: Optional[float] = None
    trend_direction: Optional[str] = None  # "increasing", "decreasing", "stable"
    affected_patients: List[str] = field(default_factory=list)
    data_source: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    related_alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "benchmark_value": self.benchmark_value,
            "trend_direction": self.trend_direction,
            "affected_patients": self.affected_patients,
            "data_source": self.data_source,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "recommendations": self.recommendations,
            "related_alerts": self.related_alerts,
        }


@dataclass
class ThresholdConfig:
    """Configuration for a monitored threshold."""
    metric_name: str
    warning_threshold: float  # Trigger warning when approaching this
    critical_threshold: float  # Trigger critical when exceeding this
    direction: str = "above"  # "above" or "below"
    registry_benchmark: Optional[float] = None
    protocol_threshold: Optional[float] = None
    description: str = ""

    def check_value(self, value: float) -> Optional[AlertSeverity]:
        """Check if value triggers an alert."""
        if self.direction == "above":
            if value >= self.critical_threshold:
                return AlertSeverity.CRITICAL
            elif value >= self.warning_threshold:
                return AlertSeverity.WARNING
        else:  # below
            if value <= self.critical_threshold:
                return AlertSeverity.CRITICAL
            elif value <= self.warning_threshold:
                return AlertSeverity.WARNING
        return None


# Default safety thresholds based on registry benchmarks and protocol
DEFAULT_THRESHOLDS = [
    ThresholdConfig(
        metric_name="revision_rate",
        warning_threshold=0.04,  # 4% - approaching concern
        critical_threshold=0.05,  # 5% - above registry median
        direction="above",
        registry_benchmark=0.035,  # AOANJRR median ~3.5% at 2yr
        protocol_threshold=0.05,
        description="Cumulative revision rate"
    ),
    ThresholdConfig(
        metric_name="infection_rate",
        warning_threshold=0.015,  # 1.5%
        critical_threshold=0.02,  # 2%
        direction="above",
        registry_benchmark=0.012,  # ~1.2% typical
        protocol_threshold=0.02,
        description="Deep infection rate"
    ),
    ThresholdConfig(
        metric_name="dislocation_rate",
        warning_threshold=0.03,  # 3%
        critical_threshold=0.04,  # 4%
        direction="above",
        registry_benchmark=0.025,  # ~2.5% typical
        protocol_threshold=0.04,
        description="Dislocation rate"
    ),
    ThresholdConfig(
        metric_name="fracture_rate",
        warning_threshold=0.015,  # 1.5%
        critical_threshold=0.02,  # 2%
        direction="above",
        registry_benchmark=0.01,  # ~1% typical
        protocol_threshold=0.02,
        description="Periprosthetic fracture rate"
    ),
    ThresholdConfig(
        metric_name="sae_rate",
        warning_threshold=0.08,  # 8%
        critical_threshold=0.10,  # 10%
        direction="above",
        protocol_threshold=0.10,
        description="Serious adverse event rate"
    ),
    ThresholdConfig(
        metric_name="survival_rate_2yr",
        warning_threshold=95.0,  # Below 95%
        critical_threshold=93.0,  # Below 93%
        direction="below",
        registry_benchmark=96.0,  # Registry median ~96%
        protocol_threshold=95.0,
        description="2-year implant survival rate"
    ),
    ThresholdConfig(
        metric_name="mcid_achievement",
        warning_threshold=45.0,  # Below 45% (using whole number for consistency)
        critical_threshold=40.0,  # Below 40%
        direction="below",
        protocol_threshold=50.0,  # Protocol: 50% target
        description="MCID achievement rate (HHS improvement >= 20 points)"
    ),
    ThresholdConfig(
        metric_name="loosening_rate",
        warning_threshold=0.02,  # 2%
        critical_threshold=0.03,  # 3%
        direction="above",
        registry_benchmark=0.015,  # ~1.5% typical
        protocol_threshold=0.03,
        description="Aseptic loosening rate"
    ),
    ThresholdConfig(
        metric_name="follow_up_compliance",
        warning_threshold=0.85,  # Below 85%
        critical_threshold=0.80,  # Below 80%
        direction="below",
        protocol_threshold=0.90,
        description="Follow-up visit compliance rate"
    ),
]


class SafetyAlertService:
    """
    Service for proactive safety monitoring and alerting.

    Features:
    - Real-time threshold monitoring
    - Trend detection
    - Proactive alerts without user queries
    - Alert aggregation and deduplication
    - Recommendation generation
    """

    def __init__(self, thresholds: List[ThresholdConfig] = None):
        """
        Initialize safety alert service.

        Args:
            thresholds: Custom threshold configurations (uses defaults if not provided)
        """
        self._thresholds = thresholds or DEFAULT_THRESHOLDS
        self._alerts: Dict[str, SafetyAlert] = {}
        self._alert_history: List[SafetyAlert] = []
        self._lock = asyncio.Lock()
        self._last_check: Optional[datetime] = None
        self._historical_values: Dict[str, List[tuple]] = {}  # metric -> [(timestamp, value)]

    async def check_safety_metrics(
        self,
        metrics: Dict[str, float],
        data_source: str = "study_data",
        affected_patients_by_metric: Dict[str, List[str]] = None,
    ) -> List[SafetyAlert]:
        """
        Check current metrics against thresholds.

        Args:
            metrics: Dictionary of metric_name -> current_value
            data_source: Source of the metrics
            affected_patients_by_metric: Optional mapping of metric to affected patient IDs

        Returns:
            List of generated alerts
        """
        new_alerts = []
        now = datetime.utcnow()
        affected_patients = affected_patients_by_metric or {}

        async with self._lock:
            for threshold in self._thresholds:
                if threshold.metric_name not in metrics:
                    continue

                current_value = metrics[threshold.metric_name]
                severity = threshold.check_value(current_value)

                # Store historical value for trend detection
                if threshold.metric_name not in self._historical_values:
                    self._historical_values[threshold.metric_name] = []
                self._historical_values[threshold.metric_name].append((now, current_value))

                # Keep only last 30 days of history
                cutoff = now - timedelta(days=30)
                self._historical_values[threshold.metric_name] = [
                    (ts, val) for ts, val in self._historical_values[threshold.metric_name]
                    if ts > cutoff
                ]

                if severity:
                    # Determine trend
                    trend = self._calculate_trend(threshold.metric_name)

                    # Generate alert
                    alert_id = f"{threshold.metric_name}_{now.strftime('%Y%m%d_%H%M%S')}"

                    # Check for existing similar alert (deduplication)
                    existing = self._find_similar_alert(threshold.metric_name, severity)
                    if existing and not existing.acknowledged:
                        # Update existing alert instead of creating new one
                        existing.current_value = current_value
                        existing.trend_direction = trend
                        continue

                    # Build recommendations
                    recommendations = self._generate_recommendations(
                        threshold, current_value, trend
                    )

                    alert = SafetyAlert(
                        id=alert_id,
                        category=(
                            AlertCategory.THRESHOLD_EXCEEDED
                            if severity == AlertSeverity.CRITICAL
                            else AlertCategory.THRESHOLD_APPROACHING
                        ),
                        severity=severity,
                        title=self._generate_alert_title(threshold, severity),
                        description=self._generate_alert_description(
                            threshold, current_value, severity
                        ),
                        metric_name=threshold.metric_name,
                        current_value=current_value,
                        threshold_value=(
                            threshold.critical_threshold
                            if severity == AlertSeverity.CRITICAL
                            else threshold.warning_threshold
                        ),
                        benchmark_value=threshold.registry_benchmark,
                        trend_direction=trend,
                        affected_patients=affected_patients.get(threshold.metric_name, []),
                        data_source=data_source,
                        recommendations=recommendations,
                    )

                    self._alerts[alert_id] = alert
                    new_alerts.append(alert)

            self._last_check = now

        if new_alerts:
            logger.info(f"Generated {len(new_alerts)} safety alerts")

        return new_alerts

    def _calculate_trend(self, metric_name: str) -> Optional[str]:
        """Calculate trend direction for a metric."""
        history = self._historical_values.get(metric_name, [])
        if len(history) < 3:
            return None

        # Simple linear trend over last 5 data points
        recent = history[-5:]
        if len(recent) < 2:
            return None

        values = [v for _, v in recent]
        half_len = max(len(values) // 2, 1)  # Prevent division by zero
        first_half_avg = sum(values[:half_len]) / half_len
        second_half_values = values[half_len:] if values[half_len:] else values
        second_half_avg = sum(second_half_values) / len(second_half_values)

        diff = second_half_avg - first_half_avg
        if abs(diff) < 0.001:  # Less than 0.1% change
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"

    def _find_similar_alert(
        self,
        metric_name: str,
        severity: AlertSeverity
    ) -> Optional[SafetyAlert]:
        """Find existing similar alert for deduplication."""
        for alert in self._alerts.values():
            if (
                alert.metric_name == metric_name
                and alert.severity == severity
                and (datetime.utcnow() - alert.created_at) < timedelta(hours=24)
            ):
                return alert
        return None

    def _generate_alert_title(
        self,
        threshold: ThresholdConfig,
        severity: AlertSeverity
    ) -> str:
        """Generate alert title."""
        metric_display = threshold.metric_name.replace("_", " ").title()
        if severity == AlertSeverity.CRITICAL:
            return f"CRITICAL: {metric_display} Threshold Exceeded"
        else:
            return f"WARNING: {metric_display} Approaching Threshold"

    def _generate_alert_description(
        self,
        threshold: ThresholdConfig,
        current_value: float,
        severity: AlertSeverity
    ) -> str:
        """Generate detailed alert description."""
        metric_display = threshold.metric_name.replace("_", " ").title()

        # Format value as percentage if appropriate
        if current_value <= 1 and "rate" in threshold.metric_name:
            value_str = f"{current_value * 100:.1f}%"
            thresh_str = f"{threshold.critical_threshold * 100:.1f}%"
            bench_str = f"{threshold.registry_benchmark * 100:.1f}%" if threshold.registry_benchmark else "N/A"
        else:
            value_str = f"{current_value:.1f}"
            thresh_str = f"{threshold.critical_threshold:.1f}"
            bench_str = f"{threshold.registry_benchmark:.1f}" if threshold.registry_benchmark else "N/A"

        parts = [
            f"Current {threshold.description}: {value_str}",
        ]

        if severity == AlertSeverity.CRITICAL:
            parts.append(f"Exceeds critical threshold of {thresh_str}")
        else:
            parts.append(f"Approaching warning threshold of {thresh_str}")

        if threshold.registry_benchmark:
            parts.append(f"Registry benchmark: {bench_str}")

        return ". ".join(parts) + "."

    def _generate_recommendations(
        self,
        threshold: ThresholdConfig,
        current_value: float,
        trend: Optional[str]
    ) -> List[str]:
        """Generate actionable recommendations based on alert."""
        recommendations = []

        # Metric-specific recommendations
        metric = threshold.metric_name

        if metric == "revision_rate":
            recommendations.extend([
                "Review revision cases for common failure modes",
                "Compare revision reasons to registry data",
                "Assess surgical technique consistency across sites",
            ])
        elif metric == "infection_rate":
            recommendations.extend([
                "Review infection prevention protocols at all sites",
                "Analyze time-to-infection for early vs late onset patterns",
                "Compare antibiotic prophylaxis practices",
            ])
        elif metric == "dislocation_rate":
            recommendations.extend([
                "Review component positioning data",
                "Assess patient compliance with post-operative protocols",
                "Analyze dislocation timing and mechanism",
            ])
        elif metric == "sae_rate":
            recommendations.extend([
                "Conduct SAE case review for patterns",
                "Verify SAE reporting consistency across sites",
                "Review patient selection criteria adherence",
            ])
        elif metric == "survival_rate_2yr":
            recommendations.extend([
                "Perform detailed failure mode analysis",
                "Compare survival curves by indication/site",
                "Review patient risk factor distribution",
            ])
        elif metric == "mcid_achievement":
            recommendations.extend([
                "Analyze baseline HHS score distribution",
                "Identify patient subgroups with poor outcomes",
                "Review rehabilitation protocol compliance",
            ])
        elif metric == "follow_up_compliance":
            recommendations.extend([
                "Contact sites with high loss-to-follow-up",
                "Implement additional patient retention strategies",
                "Review scheduling and reminder protocols",
            ])

        # Trend-based recommendations
        if trend == "increasing" and threshold.direction == "above":
            recommendations.append("URGENT: Trend is worsening - schedule immediate review meeting")
        elif trend == "increasing" and threshold.direction == "below":
            recommendations.append("Positive trend detected - continue current strategies")
        elif trend == "decreasing" and threshold.direction == "above":
            recommendations.append("Trend improving - document interventions for correlation")
        elif trend == "decreasing" and threshold.direction == "below":
            recommendations.append("URGENT: Trend is worsening - schedule immediate review meeting")

        return recommendations[:5]  # Limit to top 5

    async def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        category: Optional[AlertCategory] = None,
        acknowledged: Optional[bool] = None,
    ) -> List[SafetyAlert]:
        """
        Get current active alerts with optional filtering.

        Args:
            severity: Filter by severity level
            category: Filter by alert category
            acknowledged: Filter by acknowledgment status

        Returns:
            List of matching alerts
        """
        async with self._lock:
            alerts = list(self._alerts.values())

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if category:
            alerts = [a for a in alerts if a.category == category]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        # Sort by severity (critical first) then by creation time
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.INFO: 2,
            AlertSeverity.RESOLVED: 3,
        }
        alerts.sort(key=lambda a: (severity_order.get(a.severity, 99), -a.created_at.timestamp()))

        return alerts

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str = "user"
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: User who acknowledged

        Returns:
            True if successfully acknowledged
        """
        async with self._lock:
            if alert_id not in self._alerts:
                return False

            alert = self._alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by

            # Move to history
            self._alert_history.append(alert)

            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True

    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts for dashboard display."""
        alerts = await self.get_active_alerts(acknowledged=False)

        summary = {
            "total_active": len(alerts),
            "by_severity": {
                "critical": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
                "warning": len([a for a in alerts if a.severity == AlertSeverity.WARNING]),
                "info": len([a for a in alerts if a.severity == AlertSeverity.INFO]),
            },
            "top_alerts": [a.to_dict() for a in alerts[:5]],
            "last_checked": self._last_check.isoformat() if self._last_check else None,
        }

        return summary

    async def generate_proactive_insights(self) -> List[str]:
        """
        Generate proactive insights based on current alerts and trends.

        Returns a list of insights that could be surfaced to users without
        explicit queries.
        """
        alerts = await self.get_active_alerts(acknowledged=False)
        insights = []

        # Check for critical alerts
        critical = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        if critical:
            insights.append(
                f"ATTENTION: {len(critical)} critical safety signal(s) require immediate review. "
                f"Most urgent: {critical[0].title}"
            )

        # Check for worsening trends
        worsening = [a for a in alerts if a.trend_direction == "increasing" and a.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]]
        if worsening:
            metrics = [a.metric_name.replace("_", " ") for a in worsening]
            insights.append(
                f"Trend alert: {', '.join(metrics)} showing worsening trajectory"
            )

        # Check for metrics approaching thresholds
        approaching = [a for a in alerts if a.category == AlertCategory.THRESHOLD_APPROACHING]
        if approaching:
            insights.append(
                f"{len(approaching)} metric(s) approaching threshold levels - consider proactive review"
            )

        return insights


# Singleton instance
_safety_alert_service: Optional[SafetyAlertService] = None


def get_safety_alert_service() -> SafetyAlertService:
    """Get singleton safety alert service instance."""
    global _safety_alert_service
    if _safety_alert_service is None:
        _safety_alert_service = SafetyAlertService()
    return _safety_alert_service
