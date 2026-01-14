"""
UC5 Dashboard Service for Clinical Intelligence Platform.

Aggregates insights from UC1-UC4 services for executive-level visibility.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.agents.base_agent import AgentContext
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.data_agent import get_study_data
from app.services.readiness_service import get_readiness_service
from app.services.safety_service import get_safety_service
from app.services.deviations_service import get_deviations_service
from app.services.risk_service import get_risk_service
from data.loaders.yaml_loader import get_hybrid_loader

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service for UC5: Executive Dashboard.

    Aggregates insights from all use cases for
    comprehensive study health monitoring.
    """

    def __init__(self):
        """Initialize dashboard service."""
        self._readiness_service = get_readiness_service()
        self._safety_service = get_safety_service()
        self._deviations_service = get_deviations_service()
        self._risk_service = get_risk_service()
        self._synthesis_agent = SynthesisAgent()
        self._doc_loader = get_hybrid_loader()

    async def get_executive_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive executive summary.

        Aggregates:
        - UC1: Regulatory readiness status
        - UC2: Safety signal status
        - UC3: Protocol compliance
        - UC4: Risk stratification

        Returns:
            Dict with aggregated metrics and priorities
        """
        request_id = str(uuid.uuid4())

        # Gather data from all services
        readiness = await self._readiness_service.get_readiness_assessment()
        safety = await self._safety_service.get_safety_summary()
        deviations = await self._deviations_service.get_study_deviations()
        risk_factors = await self._risk_service.get_risk_factors()

        # Calculate overall status
        overall_status = self._calculate_overall_status(
            readiness, safety, deviations
        )

        # Build metrics list
        metrics = self._build_metrics(readiness, safety, deviations)

        # Build priority action items
        priorities = self._build_priorities(readiness, safety, deviations)

        # Extract key findings
        key_findings = self._extract_key_findings(
            readiness, safety, deviations, risk_factors
        )

        # Generate narrative
        synthesis_context = AgentContext(
            request_id=request_id,
            parameters={"synthesis_type": "uc5_dashboard"},
            shared_data={
                "readiness": readiness,
                "safety": safety,
                "deviations": deviations,
            }
        )
        synthesis_result = await self._synthesis_agent.run(synthesis_context)

        # Build headline
        headline = self._generate_headline(overall_status, priorities)

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "headline": headline,
            "metrics": metrics,
            "top_priorities": priorities,
            "key_findings": key_findings,
            "narrative": synthesis_result.narrative if synthesis_result.success else None,
            "data_sources": [
                f"H-34 Study Data ({readiness.get('enrollment', {}).get('enrolled', 0)} patients)",
                f"Protocol CIP {readiness.get('protocol_version', 'v2.0')}",
                "Literature Publications",
                "AOANJRR/NJR Registry Data"
            ],
        }

    async def get_study_progress(self) -> Dict[str, Any]:
        """
        Get detailed study progress metrics.

        Returns:
            Dict with enrollment and follow-up progress
        """
        readiness = await self._readiness_service.get_readiness_assessment()
        protocol = self._readiness_service.get_protocol_requirements()

        enrollment = readiness.get("enrollment", {})
        data_completeness = readiness.get("data_completeness", {})

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "target_enrollment": enrollment.get("target", 49),
            "current_enrollment": enrollment.get("enrolled", 0),
            "enrollment_pct": enrollment.get("percent_complete", 0),
            "evaluable_target": enrollment.get("evaluable_target", 29),
            "status": enrollment.get("status", "unknown"),
            "evaluable_patients": data_completeness.get("evaluable", 0),
            "completion_rate": data_completeness.get("completion_rate", 0),
            "protocol_id": protocol.get("protocol_id"),
            "primary_endpoint": protocol.get("primary_endpoint", {}),
            "sources": readiness.get("sources", []),
        }

    async def get_action_items(self) -> Dict[str, Any]:
        """
        Get all action items from UC1-UC4.

        Returns:
            Dict with prioritized action items
        """
        summary = await self.get_executive_summary()

        # Group by category
        by_category = {}
        for item in summary.get("top_priorities", []):
            cat = item.get("category", "Other")
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "total_items": len(summary.get("top_priorities", [])),
            "by_category": by_category,
            "items": summary.get("top_priorities", []),
        }

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get current metrics summary.

        Returns:
            Dict with all key metrics
        """
        summary = await self.get_executive_summary()

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "overall_status": summary.get("overall_status"),
            "metrics": summary.get("metrics", []),
            "n_metrics": len(summary.get("metrics", [])),
        }

    async def get_data_quality_summary(self) -> Dict[str, Any]:
        """
        Get data quality metrics calculated from actual study data.

        Returns:
            Dict with data quality by domain
        """
        deviations = await self._deviations_service.get_study_deviations()
        compliance_rate = deviations.get("compliance_rate", 1.0)
        n_deviations = deviations.get("total_deviations", 0)

        # Load actual study data to calculate completeness
        study_data = get_study_data()

        # Calculate Demographics completeness
        demographics_fields = 0
        demographics_filled = 0
        for patient in study_data.patients:
            demographics_fields += 6  # bmi, weight, height, gender, year_of_birth, smoking_habits
            if patient.bmi is not None:
                demographics_filled += 1
            if patient.weight is not None:
                demographics_filled += 1
            if patient.height is not None:
                demographics_filled += 1
            if patient.gender:
                demographics_filled += 1
            if patient.year_of_birth:
                demographics_filled += 1
            if patient.smoking_habits:
                demographics_filled += 1

        demographics_pct = (demographics_filled / demographics_fields * 100) if demographics_fields > 0 else 0

        # Calculate Surgical Data completeness
        surgical_fields = 0
        surgical_filled = 0
        for intraop in study_data.intraoperatives:
            surgical_fields += 5  # surgery_date, cup_type, cup_diameter, stem_type, acetabulum_bone_quality
            if intraop.surgery_date:
                surgical_filled += 1
            if intraop.cup_type:
                surgical_filled += 1
            if intraop.cup_diameter:
                surgical_filled += 1
            if intraop.stem_type:
                surgical_filled += 1
            if intraop.acetabulum_bone_quality:
                surgical_filled += 1

        surgical_pct = (surgical_filled / surgical_fields * 100) if surgical_fields > 0 else 0

        # Calculate Adverse Events completeness (count patients with AE records vs total)
        # For AE tracking, 100% means all AEs have required fields filled
        ae_fields = 0
        ae_filled = 0
        for ae in study_data.adverse_events:
            ae_fields += 4  # ae_title, severity, onset_date, outcome
            if ae.ae_title:
                ae_filled += 1
            if ae.severity:
                ae_filled += 1
            if ae.onset_date:
                ae_filled += 1
            if ae.outcome:
                ae_filled += 1

        ae_pct = (ae_filled / ae_fields * 100) if ae_fields > 0 else 100.0  # 100% if no AEs

        # Calculate Outcome Scores completeness (HHS + OHS)
        # Expected: each enrolled patient should have baseline + follow-up scores
        n_patients = len(study_data.patients)
        expected_hhs_per_patient = 6  # Baseline + Discharge + 2mo + 6mo + 1yr + 2yr
        expected_ohs_per_patient = 6

        total_expected_scores = n_patients * (expected_hhs_per_patient + expected_ohs_per_patient)
        actual_scores = len(study_data.hhs_scores) + len(study_data.ohs_scores)

        outcome_pct = (actual_scores / total_expected_scores * 100) if total_expected_scores > 0 else 0

        # Build quality assessment by domain with calculated values
        domains = [
            {
                "domain": "Demographics",
                "completeness_pct": round(demographics_pct, 1),
                "status": "complete" if demographics_pct >= 95 else "needs_attention",
                "fields_checked": demographics_fields,
                "fields_complete": demographics_filled,
            },
            {
                "domain": "Surgical Data",
                "completeness_pct": round(surgical_pct, 1),
                "status": "complete" if surgical_pct >= 95 else "needs_attention",
                "fields_checked": surgical_fields,
                "fields_complete": surgical_filled,
            },
            {
                "domain": "Follow-up Visits",
                "completeness_pct": round(compliance_rate * 100, 1),
                "status": "needs_attention" if compliance_rate < 0.95 else "complete",
            },
            {
                "domain": "Adverse Events",
                "completeness_pct": round(ae_pct, 1),
                "status": "complete" if ae_pct >= 95 else "needs_attention",
                "records_checked": len(study_data.adverse_events),
            },
            {
                "domain": "Outcome Scores",
                "completeness_pct": round(outcome_pct, 1),
                "status": "complete" if outcome_pct >= 80 else "needs_attention",
                "expected_scores": total_expected_scores,
                "actual_scores": actual_scores,
            },
        ]

        overall_quality = sum(d["completeness_pct"] for d in domains) / len(domains)

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "overall_quality_pct": round(overall_quality, 1),
            "by_domain": domains,
            "n_deviations": n_deviations,
            "compliance_rate": compliance_rate,
            "n_patients": n_patients,
        }

    async def get_safety_dashboard(self) -> Dict[str, Any]:
        """
        Get safety-focused dashboard data.

        Returns:
            Dict with safety metrics and signals
        """
        safety = await self._safety_service.get_safety_summary()
        signals = await self._safety_service.detect_signals()

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "overall_status": safety.get("overall_status"),
            "n_signals": safety.get("n_signals", 0),
            "signals": signals.get("signals", []),
            "high_priority": signals.get("high_priority", []),
            "requires_dsmb_review": signals.get("requires_dsmb_review", False),
            "metrics": safety.get("metrics", []),
        }

    async def get_benchmark_comparison(self) -> Dict[str, Any]:
        """
        Get study vs benchmark comparison with actual study values.

        Returns:
            Dict with benchmark comparisons including real study metrics
        """
        safety = await self._safety_service.get_safety_summary()
        lit_benchmarks = self._doc_loader.load_literature_benchmarks()
        registry_norms = self._doc_loader.load_registry_norms()

        # Get actual study data for comparison values
        study_data = get_study_data()
        study_metrics = self._calculate_study_metrics(study_data, safety)

        comparisons = []

        # Add literature benchmark comparisons with actual study values
        # aggregate_benchmarks is a Dict[str, Any] with metric names as keys
        for metric_name, benchmark_data in lit_benchmarks.aggregate_benchmarks.items():
            study_value = study_metrics.get(metric_name)
            benchmark_median = benchmark_data.get("median") if isinstance(benchmark_data, dict) else None
            benchmark_range = benchmark_data.get("range") if isinstance(benchmark_data, dict) else None
            n_studies = benchmark_data.get("n_studies") if isinstance(benchmark_data, dict) else None

            comparison_status = self._get_comparison_status(
                study_value, benchmark_median, benchmark_range, metric_name
            )

            sources_list = benchmark_data.get("sources") if isinstance(benchmark_data, dict) else None
            comparisons.append({
                "metric": metric_name,
                "study_value": study_value,
                "benchmark_value": benchmark_median,
                "benchmark_range": benchmark_range,
                "source": "Literature Aggregate",
                "sources": sources_list,
                "n_studies": n_studies,
                "comparison_status": comparison_status,
            })

        # Add registry comparisons with best available survival rate
        study_survival_2yr = study_metrics.get("survival_2yr")
        for registry in registry_norms.registries:
            # Find best available survival rate (prefer shorter timepoints for comparison)
            survival_timepoints = [
                ("1yr", registry.survival_1yr),
                ("2yr", registry.survival_2yr),
                ("5yr", registry.survival_5yr),
                ("10yr", registry.survival_10yr),
                ("15yr", registry.survival_15yr),
            ]
            # Find shortest available timepoint for most relevant comparison
            benchmark_val = None
            timepoint_label = "Survival"
            for timepoint, value in survival_timepoints:
                if value is not None:
                    benchmark_val = value
                    timepoint_label = f"{timepoint} Survival"
                    break
            
            comparison_status = None
            # For registry comparison, show H-34's 2yr survival vs registry benchmark
            if study_survival_2yr is not None and benchmark_val is not None:
                comparison_status = "favorable" if study_survival_2yr >= benchmark_val else "concerning"

            comparisons.append({
                "metric": f"{registry.name} {timepoint_label}",
                "study_value": study_survival_2yr,
                "benchmark_value": benchmark_val,
                "source": registry.abbreviation or registry.name,
                "year": registry.report_year,
                "comparison_status": comparison_status,
            })

        formatted_citations = [
            {
                "id": p.id,
                "citation": f"{p.id.split('_')[0].title()} et al., {p.year}",
                "title": p.title,
                "year": p.year
            }
            for p in lit_benchmarks.publications
        ]

        return {
            "success": True,
            "generated_at": datetime.utcnow().isoformat(),
            "comparisons": comparisons,
            "literature_sources": [p.id for p in lit_benchmarks.publications],
            "literature_citations": formatted_citations,
            "registry_sources": [r.name for r in registry_norms.registries],
            "study_metrics": study_metrics,
        }

    def _calculate_study_metrics(self, study_data, safety: Dict) -> Dict[str, Any]:
        """
        Calculate study metrics for benchmark comparison.

        Args:
            study_data: H34StudyData object
            safety: Safety summary from safety service

        Returns:
            Dictionary of calculated study metrics
        """
        metrics = {}
        n_patients = len(study_data.patients)

        if n_patients == 0:
            return metrics

        # Calculate HHS improvement from baseline to 2-year
        hhs_baseline_scores = []
        hhs_2yr_scores = []
        hhs_improvements = []

        # Group HHS scores by patient
        patient_hhs = {}
        for hhs in study_data.hhs_scores:
            if hhs.patient_id not in patient_hhs:
                patient_hhs[hhs.patient_id] = {}
            if hhs.total_score is not None:
                fu_lower = (hhs.follow_up or "").lower()
                if "preop" in fu_lower or "baseline" in fu_lower or "screening" in fu_lower:
                    patient_hhs[hhs.patient_id]["baseline"] = hhs.total_score
                elif "2 year" in fu_lower or "24 month" in fu_lower:
                    patient_hhs[hhs.patient_id]["2yr"] = hhs.total_score
                elif "2yr" in fu_lower:
                    patient_hhs[hhs.patient_id]["2yr"] = hhs.total_score

        for patient_id, scores in patient_hhs.items():
            if "baseline" in scores:
                hhs_baseline_scores.append(scores["baseline"])
            if "2yr" in scores:
                hhs_2yr_scores.append(scores["2yr"])
            if "baseline" in scores and "2yr" in scores:
                hhs_improvements.append(scores["2yr"] - scores["baseline"])

        # HHS metrics
        if hhs_baseline_scores:
            metrics["hhs_baseline"] = round(sum(hhs_baseline_scores) / len(hhs_baseline_scores), 1)
        if hhs_2yr_scores:
            metrics["hhs_2yr"] = round(sum(hhs_2yr_scores) / len(hhs_2yr_scores), 1)
        if hhs_improvements:
            metrics["hhs_improvement"] = round(sum(hhs_improvements) / len(hhs_improvements), 1)
            # MCID achievement rate (20+ point improvement)
            mcid_achieved = sum(1 for imp in hhs_improvements if imp >= 20)
            metrics["mcid_achievement"] = round(mcid_achieved / len(hhs_improvements), 3)

        # Calculate OHS improvement
        ohs_improvements = []
        patient_ohs = {}
        for ohs in study_data.ohs_scores:
            if ohs.patient_id not in patient_ohs:
                patient_ohs[ohs.patient_id] = {}
            if ohs.total_score is not None:
                fu_lower = (ohs.follow_up or "").lower()
                if "preop" in fu_lower or "baseline" in fu_lower or "screening" in fu_lower:
                    patient_ohs[ohs.patient_id]["baseline"] = ohs.total_score
                elif "2 year" in fu_lower or "24 month" in fu_lower or "2yr" in fu_lower:
                    patient_ohs[ohs.patient_id]["2yr"] = ohs.total_score

        for patient_id, scores in patient_ohs.items():
            if "baseline" in scores and "2yr" in scores:
                ohs_improvements.append(scores["2yr"] - scores["baseline"])

        if ohs_improvements:
            metrics["ohs_improvement"] = round(sum(ohs_improvements) / len(ohs_improvements), 1)

        # Safety rates from safety service
        safety_rates = safety.get("rates", {})
        if safety_rates:
            if "revision_rate" in safety_rates:
                metrics["revision_rate_2yr"] = safety_rates["revision_rate"]
                metrics["survival_2yr"] = round(1.0 - safety_rates["revision_rate"], 4)
            if "dislocation_rate" in safety_rates:
                metrics["dislocation_rate"] = safety_rates["dislocation_rate"]
            if "infection_rate" in safety_rates:
                metrics["infection_rate"] = safety_rates["infection_rate"]
            if "fracture_rate" in safety_rates:
                metrics["fracture_rate"] = safety_rates["fracture_rate"]

        # If no revision rate from safety, calculate from AEs
        if "revision_rate_2yr" not in metrics:
            revisions = sum(
                1 for ae in study_data.adverse_events
                if ae.device_removed and ae.device_removed.lower() == "yes"
            )
            metrics["revision_rate_2yr"] = round(revisions / n_patients, 4) if n_patients > 0 else 0
            metrics["survival_2yr"] = round(1.0 - metrics["revision_rate_2yr"], 4)

        return metrics

    def _get_comparison_status(
        self,
        study_value: Optional[float],
        benchmark_value: Optional[float],
        benchmark_range: Optional[List[float]],
        metric: str
    ) -> Optional[str]:
        """
        Determine comparison status between study and benchmark.

        Args:
            study_value: Actual study value
            benchmark_value: Literature benchmark value
            benchmark_range: Range from literature [min, max]
            metric: Metric name for context

        Returns:
            Status string: 'favorable', 'acceptable', 'concerning', or None
        """
        if study_value is None or benchmark_value is None:
            return None

        # Metrics where higher is better
        higher_is_better = ["hhs_improvement", "hhs_2yr", "ohs_improvement", "mcid_achievement", "survival_2yr"]

        # Metrics where lower is better
        lower_is_better = ["revision_rate_2yr", "dislocation_rate", "infection_rate", "fracture_rate"]

        if metric in higher_is_better:
            if study_value >= benchmark_value:
                return "favorable"
            elif benchmark_range and study_value >= benchmark_range[0]:
                return "acceptable"
            else:
                return "concerning"

        elif metric in lower_is_better:
            if study_value <= benchmark_value:
                return "favorable"
            elif benchmark_range and study_value <= benchmark_range[1]:
                return "acceptable"
            else:
                return "concerning"

        return None

    def _calculate_overall_status(
        self,
        readiness: Dict,
        safety: Dict,
        deviations: Dict
    ) -> str:
        """Calculate overall dashboard status."""
        # Check for red flags
        if safety.get("overall_status") == "critical":
            return "RED"
        if not readiness.get("safety", {}).get("is_ready"):
            return "RED"

        # Check for yellow flags
        warnings = 0
        if not readiness.get("is_ready"):
            warnings += 1
        if safety.get("n_signals", 0) > 0:
            warnings += 1
        if deviations.get("deviation_rate", 0) > 0.05:
            warnings += 1

        if warnings >= 2:
            return "YELLOW"

        return "GREEN"

    def _build_metrics(
        self,
        readiness: Dict,
        safety: Dict,
        deviations: Dict
    ) -> List[Dict[str, Any]]:
        """Build metrics list for dashboard."""
        metrics = []

        # Regulatory readiness
        enrollment = readiness.get("enrollment", {})
        metrics.append({
            "name": "Regulatory Readiness",
            "value": f"{enrollment.get('percent_complete', 0):.0f}%",
            "target": "100%",
            "status": "GREEN" if readiness.get("is_ready") else "YELLOW",
            "trend": "up" if enrollment.get("status") == "on_track" else "stable",
        })

        # Enrollment
        metrics.append({
            "name": "Enrollment",
            "value": f"{enrollment.get('enrolled', 0)}/{enrollment.get('target', 49)}",
            "target": str(enrollment.get("target", 49)),
            "status": "GREEN" if enrollment.get("is_ready") else "YELLOW",
            "trend": "up",
        })

        # Safety signals
        n_signals = safety.get("n_signals", 0)
        metrics.append({
            "name": "Safety Signals",
            "value": f"{n_signals} active",
            "target": "0",
            "status": "GREEN" if n_signals == 0 else "RED" if n_signals > 1 else "YELLOW",
            "trend": "stable",
        })

        # Protocol compliance
        compliance_rate = 1.0 - deviations.get("deviation_rate", 0)
        metrics.append({
            "name": "Protocol Compliance",
            "value": f"{compliance_rate * 100:.0f}%",
            "target": "95%",
            "status": "GREEN" if compliance_rate >= 0.95 else "YELLOW",
            "trend": "stable",
        })

        return metrics

    def _build_priorities(
        self,
        readiness: Dict,
        safety: Dict,
        deviations: Dict
    ) -> List[Dict[str, Any]]:
        """Build priority action items."""
        priorities = []
        priority_rank = 1

        # Safety signals (highest priority)
        for signal in safety.get("signals", []):
            if signal.get("signal_level") == "high":
                priorities.append({
                    "priority": priority_rank,
                    "category": "Safety",
                    "title": f"Address {signal.get('metric')} Signal",
                    "description": signal.get("recommended_action", "Review with DSMB"),
                    "owner": "Medical Monitor",
                    "source": "UC2",
                })
                priority_rank += 1

        # Blocking issues from readiness
        for issue in readiness.get("blocking_issues", []):
            priorities.append({
                "priority": priority_rank,
                "category": issue.get("category", "Readiness").title(),
                "title": f"Resolve {issue.get('category', '')} Issue",
                "description": issue.get("issue", ""),
                "owner": "Study Team",
                "source": "UC1",
            })
            priority_rank += 1

        # Major deviations
        by_severity = deviations.get("by_severity", {})
        if by_severity.get("major", 0) > 0 or by_severity.get("critical", 0) > 0:
            priorities.append({
                "priority": priority_rank,
                "category": "Documentation",
                "title": "Document Protocol Deviations",
                "description": f"{by_severity.get('major', 0)} major and {by_severity.get('critical', 0)} critical deviations require documentation",
                "owner": "Medical Writer",
                "source": "UC3",
            })
            priority_rank += 1

        return priorities[:5]  # Top 5 priorities

    def _extract_key_findings(
        self,
        readiness: Dict,
        safety: Dict,
        deviations: Dict,
        risk_factors: Dict
    ) -> List[str]:
        """Extract key findings for executive summary."""
        findings = []

        # Enrollment finding
        enrollment = readiness.get("enrollment", {})
        if enrollment.get("is_ready"):
            findings.append(
                f"Enrollment complete: {enrollment.get('enrolled')}/{enrollment.get('target')} patients"
            )
        else:
            findings.append(
                f"Enrollment at {enrollment.get('percent_complete', 0):.0f}% of target"
            )

        # Safety finding
        if safety.get("n_signals", 0) > 0:
            findings.append(
                f"Safety: {safety.get('n_signals')} signal(s) require attention"
            )
        else:
            findings.append("Safety: No active signals, within thresholds")

        # Compliance finding
        deviation_rate = deviations.get("deviation_rate", 0)
        if deviation_rate > 0.05:
            findings.append(
                f"Protocol compliance: {(1-deviation_rate)*100:.0f}% - improvement needed"
            )
        else:
            findings.append(
                f"Protocol compliance: {(1-deviation_rate)*100:.0f}% - acceptable"
            )

        # Risk model finding
        n_factors = len(risk_factors.get("model_factors", []))
        findings.append(
            f"Risk model: {n_factors} literature-derived hazard ratios integrated"
        )

        return findings

    def _generate_headline(
        self,
        status: str,
        priorities: List[Dict]
    ) -> str:
        """Generate executive headline."""
        n_blockers = len([p for p in priorities if p.get("priority", 0) <= 2])

        if status == "GREEN":
            return "Study progressing well; on track for regulatory submission"
        elif status == "YELLOW":
            return f"Study progressing; {n_blockers} item(s) require attention before submission"
        else:
            return f"Study at risk; {n_blockers} critical issue(s) require immediate action"


# Singleton instance
_dashboard_service: Optional[DashboardService] = None


def get_dashboard_service() -> DashboardService:
    """Get singleton dashboard service instance."""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service
