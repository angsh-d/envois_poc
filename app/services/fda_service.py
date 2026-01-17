"""
UC11 FDA Surveillance Service for Clinical Intelligence Platform.

Provides public FDA data integration for Quality persona, closing data gaps
for complaint triage, trend analysis, and vigilance reporting.

Enhanced with phase-based and competitor search capabilities for
Deep Research data discovery.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import uuid

import httpx

from app.agents.base_agent import AgentContext
from app.agents.fda_agent import FDAAgent, HIP_PRODUCT_CODES

logger = logging.getLogger(__name__)

# openFDA API endpoints
OPENFDA_BASE_URL = "https://api.fda.gov"
FDA_REQUEST_DELAY_SECONDS = 0.5


class FDAService:
    """
    Service for UC11: FDA Surveillance Integration.

    Provides:
    - Device adverse event analysis (MAUDE)
    - 510(k) clearance lookup
    - Recall monitoring
    - Complaint trend analysis
    - Vigilance report generation
    """

    def __init__(self):
        """Initialize FDA service."""
        self._fda_agent = FDAAgent()

    async def get_surveillance_report(
        self,
        product_codes: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive FDA surveillance report.

        Args:
            product_codes: List of FDA product codes (defaults to hip prostheses)
            date_range: Optional date range (start, end in YYYYMMDD format)

        Returns:
            Dict with comprehensive surveillance data
        """
        request_id = str(uuid.uuid4())

        if product_codes is None:
            logger.warning(
                "No FDA product codes provided for surveillance report. "
                "Results will be limited without product code filtering."
            )
            product_codes = []

        context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "surveillance",
                "product_codes": product_codes,
                "date_range": date_range or {},
            }
        )

        result = await self._fda_agent.run(context)

        if not result.success:
            return {
                "success": False,
                "error": result.error,
                "generated_at": datetime.utcnow().isoformat(),
            }

        return {
            "success": True,
            "report_type": "FDA Surveillance Report",
            "generated_at": datetime.utcnow().isoformat(),
            "product_codes": product_codes,
            "product_descriptions": result.data.get("product_descriptions", {}),
            "adverse_events_summary": result.data.get("adverse_events", {}).get("summary", {}),
            "clearances_summary": {
                "total": result.data.get("clearances", {}).get("total_clearances", 0),
                "by_year": result.data.get("clearances", {}).get("by_year", {}),
            },
            "recalls_summary": {
                "total": result.data.get("recalls", {}).get("total_recalls", 0),
                "active": result.data.get("recalls", {}).get("active_count", 0),
                "active_recalls": result.data.get("recalls", {}).get("active_recalls", []),
            },
            "risk_assessment": result.data.get("risk_assessment", {}),
            "sources": [s.to_dict() for s in result.sources],
            "confidence": result.confidence,
        }

    async def get_adverse_event_trends(
        self,
        product_codes: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze adverse event trends over time.

        Args:
            product_codes: List of FDA product codes
            date_range: Optional date range

        Returns:
            Dict with trend analysis
        """
        request_id = str(uuid.uuid4())

        if product_codes is None:
            logger.warning(
                "No FDA product codes provided for trend analysis. "
                "Results will be limited without product code filtering."
            )
            product_codes = []

        context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "trends",
                "product_codes": product_codes,
                "date_range": date_range or {},
            }
        )

        result = await self._fda_agent.run(context)

        if not result.success:
            return {
                "success": False,
                "error": result.error,
            }

        return {
            "success": True,
            "report_type": "Adverse Event Trend Analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "product_codes": product_codes,
            "trends_by_year": result.data.get("trends_by_year", {}),
            "year_over_year_changes": result.data.get("year_over_year_changes", []),
            "overall_trend": result.data.get("overall_trend"),
            "trend_insight": result.data.get("trend_insight"),
            "sources": [s.to_dict() for s in result.sources],
        }

    async def triage_complaints(
        self,
        product_codes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Provide complaint triage guidance based on FDA adverse event data.

        This helps close the Quality persona data gap for:
        "How should I triage today's complaints?"

        Args:
            product_codes: List of FDA product codes

        Returns:
            Dict with triage recommendations
        """
        request_id = str(uuid.uuid4())

        if product_codes is None:
            logger.warning(
                "No FDA product codes provided for complaint triage. "
                "Results will be limited without product code filtering."
            )
            product_codes = []

        # Get recent adverse events
        context = AgentContext(
            request_id=request_id,
            parameters={
                "query_type": "adverse_events",
                "product_codes": product_codes,
                "date_range": {},
            }
        )

        result = await self._fda_agent.run(context)

        if not result.success:
            return {
                "success": False,
                "error": result.error,
            }

        ae_data = result.data
        summary = ae_data.get("summary", {})

        # Generate triage categories based on FDA patterns
        triage_categories = self._generate_triage_categories(ae_data)

        return {
            "success": True,
            "report_type": "Complaint Triage Guidance",
            "generated_at": datetime.utcnow().isoformat(),
            "fda_context": {
                "total_reported_events": summary.get("total_events", 0),
                "injury_rate": summary.get("injury_rate", 0),
                "death_rate": summary.get("death_rate", 0),
                "malfunction_rate": summary.get("malfunction_rate", 0),
            },
            "triage_categories": triage_categories,
            "priority_guidance": self._generate_priority_guidance(summary),
            "common_complaint_patterns": self._extract_common_patterns(ae_data),
            "regulatory_considerations": [
                "Reports involving death require MDR filing within 30 days",
                "Serious injury reports require MDR filing within 30 days",
                "Malfunctions that could cause death/injury require MDR",
                "Track complaint trends for periodic reporting",
            ],
            "sources": [s.to_dict() for s in result.sources],
        }

    def _generate_triage_categories(self, ae_data: Dict) -> List[Dict[str, Any]]:
        """Generate triage categories based on FDA adverse event patterns."""
        event_types = ae_data.get("summary", {}).get("by_event_type", {})

        categories = [
            {
                "priority": "CRITICAL",
                "description": "Patient death or life-threatening condition",
                "fda_event_type": "Death",
                "historical_frequency": event_types.get("Death", 0),
                "action": "Immediate investigation, MDR filing within 30 days",
                "escalation": "Notify Quality Director and Regulatory Affairs immediately",
            },
            {
                "priority": "HIGH",
                "description": "Serious injury requiring intervention",
                "fda_event_type": "Injury",
                "historical_frequency": event_types.get("Injury", 0),
                "action": "48-hour investigation, MDR evaluation",
                "escalation": "Quality Manager review within 24 hours",
            },
            {
                "priority": "MEDIUM",
                "description": "Device malfunction without patient harm",
                "fda_event_type": "Malfunction",
                "historical_frequency": event_types.get("Malfunction", 0),
                "action": "Standard investigation protocol, trend monitoring",
                "escalation": "Weekly review in quality meeting",
            },
            {
                "priority": "LOW",
                "description": "Minor issues, usability concerns",
                "fda_event_type": "Other",
                "historical_frequency": event_types.get("Other", 0),
                "action": "Log and monitor, include in periodic trend analysis",
                "escalation": "Monthly review",
            },
        ]

        return categories

    def _generate_priority_guidance(self, summary: Dict) -> Dict[str, Any]:
        """Generate priority guidance based on FDA data patterns."""
        death_rate = summary.get("death_rate", 0)
        injury_rate = summary.get("injury_rate", 0)

        if death_rate > 0.01:
            alert_level = "ELEVATED"
            guidance = (
                "FDA data shows elevated death rate for this product category. "
                "Prioritize any complaints involving patient deterioration or "
                "unexpected clinical outcomes. Consider proactive outreach to "
                "high-volume sites."
            )
        elif injury_rate > 0.4:
            alert_level = "CAUTION"
            guidance = (
                "FDA data shows significant injury reporting. Focus on complaints "
                "involving device loosening, dislocation, or infection. Ensure "
                "timely investigation of all injury-related complaints."
            )
        else:
            alert_level = "STANDARD"
            guidance = (
                "FDA data shows typical adverse event patterns for this category. "
                "Follow standard triage protocols. Monitor for any emerging "
                "complaint clusters or unusual patterns."
            )

        return {
            "alert_level": alert_level,
            "guidance": guidance,
            "key_metrics": {
                "death_rate": f"{death_rate*100:.3f}%",
                "injury_rate": f"{injury_rate*100:.1f}%",
            }
        }

    def _extract_common_patterns(self, ae_data: Dict) -> List[Dict[str, Any]]:
        """Extract common complaint patterns from FDA data."""
        sample_events = ae_data.get("sample_events", [])

        # Count device problems
        problem_counts = {}
        for event in sample_events:
            for problem in event.get("device_problem", []):
                problem_counts[problem] = problem_counts.get(problem, 0) + 1

        # Sort by frequency
        sorted_problems = sorted(
            problem_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        patterns = []
        for problem, count in sorted_problems[:5]:
            patterns.append({
                "issue": problem,
                "frequency": count,
                "investigation_focus": self._get_investigation_focus(problem),
            })

        return patterns

    def _get_investigation_focus(self, problem: str) -> str:
        """Get investigation focus based on problem type."""
        focus_map = {
            "loosening": "Assess surgical technique, patient bone quality, component sizing",
            "dislocation": "Review surgical approach, component positioning, patient activity",
            "infection": "Evaluate sterile processing, surgical environment, patient factors",
            "fracture": "Assess implant design, material properties, patient loading",
            "wear": "Review articulation materials, patient activity level, follow-up compliance",
        }

        problem_lower = problem.lower() if problem else ""
        for key, focus in focus_map.items():
            if key in problem_lower:
                return focus

        return "Standard root cause analysis protocol"

    async def generate_vigilance_report(
        self,
        product_codes: Optional[List[str]] = None,
        reporting_period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a vigilance report combining internal and FDA data.

        This helps close the Quality persona data gap for:
        "Generate a vigilance report for the current period"

        Args:
            product_codes: List of FDA product codes
            reporting_period: Reporting period description

        Returns:
            Dict with vigilance report data
        """
        # Get surveillance data
        surveillance = await self.get_surveillance_report(product_codes)

        # Get trends
        trends = await self.get_adverse_event_trends(product_codes)

        if not surveillance.get("success") or not trends.get("success"):
            return {
                "success": False,
                "error": "Failed to retrieve FDA data for vigilance report",
            }

        return {
            "success": True,
            "report_type": "Vigilance Report",
            "reporting_period": reporting_period or "Current Period",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": self._generate_vigilance_summary(
                surveillance, trends
            ),
            "adverse_event_section": {
                "total_fda_reports": surveillance.get("adverse_events_summary", {}).get("total_events", 0),
                "by_event_type": surveillance.get("adverse_events_summary", {}).get("by_event_type", {}),
                "trend_direction": trends.get("overall_trend"),
                "trend_insight": trends.get("trend_insight"),
            },
            "recall_section": surveillance.get("recalls_summary", {}),
            "risk_assessment": surveillance.get("risk_assessment", {}),
            "regulatory_actions": self._get_regulatory_actions(surveillance),
            "sources": surveillance.get("sources", []) + trends.get("sources", []),
        }

    def _generate_vigilance_summary(
        self,
        surveillance: Dict,
        trends: Dict
    ) -> str:
        """Generate executive summary for vigilance report."""
        ae_summary = surveillance.get("adverse_events_summary", {})
        risk = surveillance.get("risk_assessment", {})
        trend = trends.get("overall_trend", "UNKNOWN")

        total_events = ae_summary.get("total_events", 0)
        risk_level = risk.get("risk_level", "UNKNOWN")

        summary = (
            f"This vigilance report covers FDA surveillance data for hip prosthesis products. "
            f"The FDA MAUDE database contains {total_events:,} adverse event reports for the "
            f"monitored product codes. Current risk assessment: {risk_level}. "
            f"Adverse event trend: {trend}. "
        )

        if surveillance.get("recalls_summary", {}).get("active", 0) > 0:
            active_recalls = surveillance["recalls_summary"]["active"]
            summary += f"ALERT: {active_recalls} active recall(s) identified. "

        summary += (
            "Continue routine post-market surveillance activities and monitor for "
            "any emerging safety signals."
        )

        return summary

    def _get_regulatory_actions(self, surveillance: Dict) -> List[Dict[str, str]]:
        """Get recommended regulatory actions based on surveillance data."""
        actions = []
        risk = surveillance.get("risk_assessment", {})
        risk_level = risk.get("risk_level", "MINIMAL")

        if risk_level == "HIGH":
            actions.append({
                "action": "Prepare field safety corrective action evaluation",
                "priority": "IMMEDIATE",
                "deadline": "Within 48 hours",
            })
            actions.append({
                "action": "Notify competent authority of potential safety issue",
                "priority": "HIGH",
                "deadline": "Within 10 working days",
            })
        elif risk_level == "MODERATE":
            actions.append({
                "action": "Enhanced trend monitoring",
                "priority": "MEDIUM",
                "deadline": "Implement within 30 days",
            })
            actions.append({
                "action": "Review and update risk management file",
                "priority": "MEDIUM",
                "deadline": "Within 60 days",
            })
        else:
            actions.append({
                "action": "Continue routine surveillance",
                "priority": "STANDARD",
                "deadline": "Ongoing",
            })
            actions.append({
                "action": "Include findings in periodic safety update report",
                "priority": "STANDARD",
                "deadline": "Next reporting cycle",
            })

        return actions

    # ========================================================================
    # Phase-Based and Competitor Search Methods (for Deep Research Discovery)
    # ========================================================================

    async def _get_direct_client(self) -> httpx.AsyncClient:
        """Get HTTP client for direct FDA API calls."""
        if not hasattr(self, '_direct_client') or self._direct_client is None or self._direct_client.is_closed:
            self._direct_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._direct_client

    async def _rate_limited_request(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> httpx.Response:
        """Make rate-limited request to FDA API."""
        import time
        if not hasattr(self, '_last_request_time'):
            self._last_request_time = 0
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < FDA_REQUEST_DELAY_SECONDS:
            await asyncio.sleep(FDA_REQUEST_DELAY_SECONDS - elapsed)
        self._last_request_time = time.time()
        return await client.get(url)

    async def search_510k_by_applicant(
        self,
        applicant_name: str,
        product_codes: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Search 510(k) clearances by applicant (manufacturer) name.

        Args:
            applicant_name: Company/manufacturer name
            product_codes: Optional list of product codes to filter
            date_range: Optional date range for clearance dates
            limit: Maximum results to return

        Returns:
            Dict with clearance data
        """
        client = await self._get_direct_client()

        # Build search query
        search_parts = [f'applicant:"{applicant_name}"']

        if product_codes:
            code_query = " OR ".join([f'product_code:"{code}"' for code in product_codes])
            search_parts.append(f'({code_query})')

        if date_range:
            if date_range.get("start"):
                search_parts.append(f'decision_date:[{date_range["start"]} TO *]')
            if date_range.get("end"):
                search_parts.append(f'decision_date:[* TO {date_range["end"]}]')

        search_query = " AND ".join(search_parts)
        url = f"{OPENFDA_BASE_URL}/device/510k.json?search={quote(search_query)}&limit={limit}"

        try:
            response = await self._rate_limited_request(client, url)

            if response.status_code != 200:
                logger.warning(f"FDA 510k search error: {response.status_code}")
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            results = data.get("results", [])

            clearances = []
            for result in results:
                clearances.append({
                    "k_number": result.get("k_number", ""),
                    "applicant": result.get("applicant", ""),
                    "device_name": result.get("device_name", ""),
                    "product_code": result.get("product_code", ""),
                    "decision_date": result.get("decision_date", ""),
                    "decision_description": result.get("decision_description", ""),
                    "statement_or_summary": result.get("statement_or_summary", ""),
                    "clearance_type": result.get("clearance_type", ""),
                    "third_party_flag": result.get("third_party_flag", ""),
                })

            return {
                "success": True,
                "applicant": applicant_name,
                "total_found": len(clearances),
                "clearances": clearances,
                "source": "FDA 510(k) Database",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search FDA 510k: {e}")
            return {"success": False, "error": str(e)}

    async def search_competitor_clearances(
        self,
        product_codes: List[str],
        exclude_applicants: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Search for competitor 510(k) clearances by product code.

        Args:
            product_codes: List of FDA product codes
            exclude_applicants: List of applicant names to exclude (own company)
            date_range: Optional date range for clearance dates
            limit: Maximum results to return

        Returns:
            Dict with competitor clearance data grouped by applicant
        """
        client = await self._get_direct_client()

        # Build search query for product codes
        code_query = " OR ".join([f'product_code:"{code}"' for code in product_codes])
        search_parts = [f'({code_query})']

        if date_range:
            if date_range.get("start"):
                search_parts.append(f'decision_date:[{date_range["start"]} TO *]')
            if date_range.get("end"):
                search_parts.append(f'decision_date:[* TO {date_range["end"]}]')

        search_query = " AND ".join(search_parts)
        url = f"{OPENFDA_BASE_URL}/device/510k.json?search={quote(search_query)}&limit={limit}"

        try:
            response = await self._rate_limited_request(client, url)

            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            results = data.get("results", [])

            # Filter out excluded applicants and group by company
            clearances_by_company = {}
            excluded_lower = [a.lower() for a in (exclude_applicants or [])]

            for result in results:
                applicant = result.get("applicant", "Unknown")
                if applicant.lower() in excluded_lower:
                    continue

                if applicant not in clearances_by_company:
                    clearances_by_company[applicant] = []

                clearances_by_company[applicant].append({
                    "k_number": result.get("k_number", ""),
                    "device_name": result.get("device_name", ""),
                    "product_code": result.get("product_code", ""),
                    "decision_date": result.get("decision_date", ""),
                    "decision_description": result.get("decision_description", ""),
                })

            # Sort companies by number of clearances
            sorted_companies = sorted(
                clearances_by_company.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )

            return {
                "success": True,
                "product_codes": product_codes,
                "total_companies": len(clearances_by_company),
                "total_clearances": sum(len(c) for c in clearances_by_company.values()),
                "by_company": dict(sorted_companies),
                "top_competitors": [
                    {"company": company, "clearance_count": len(clearances)}
                    for company, clearances in sorted_companies[:10]
                ],
                "source": "FDA 510(k) Database",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search competitor clearances: {e}")
            return {"success": False, "error": str(e)}

    async def get_predicate_chain(
        self,
        k_number: str,
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Get the predicate device chain for a 510(k) clearance.

        Args:
            k_number: The 510(k) number to analyze
            max_depth: Maximum depth of predicate chain to follow

        Returns:
            Dict with predicate chain information
        """
        client = await self._get_direct_client()

        async def get_clearance_details(k_num: str) -> Optional[Dict]:
            url = f"{OPENFDA_BASE_URL}/device/510k.json?search=k_number:{quote(k_num)}&limit=1"
            try:
                response = await self._rate_limited_request(client, url)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        return results[0]
            except Exception as e:
                logger.warning(f"Failed to get clearance {k_num}: {e}")
            return None

        # Build predicate chain
        chain = []
        current_k = k_number
        visited = set()

        for depth in range(max_depth + 1):
            if current_k in visited:
                break
            visited.add(current_k)

            details = await get_clearance_details(current_k)
            if not details:
                break

            chain.append({
                "depth": depth,
                "k_number": details.get("k_number", ""),
                "device_name": details.get("device_name", ""),
                "applicant": details.get("applicant", ""),
                "decision_date": details.get("decision_date", ""),
                "product_code": details.get("product_code", ""),
            })

            # Try to find predicate from statement/summary (FDA doesn't provide direct predicate link)
            # This is a heuristic - in practice, predicates are extracted from submission documents
            break  # Stop after first level as predicates aren't directly available via API

        return {
            "success": True,
            "k_number": k_number,
            "chain_depth": len(chain),
            "predicate_chain": chain,
            "note": "Predicate information may require document review for complete chain",
            "source": "FDA 510(k) Database",
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    async def search_adverse_events_by_manufacturer(
        self,
        manufacturer_name: str,
        product_codes: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Search MAUDE adverse events by manufacturer name.

        Args:
            manufacturer_name: Manufacturer/company name
            product_codes: Optional product codes to filter
            date_range: Optional date range
            limit: Maximum results

        Returns:
            Dict with adverse event summary for the manufacturer
        """
        client = await self._get_direct_client()

        # Build search query
        search_parts = [f'device.manufacturer_d_name:"{manufacturer_name}"']

        if product_codes:
            code_query = " OR ".join([f'device.device_report_product_code:"{code}"' for code in product_codes])
            search_parts.append(f'({code_query})')

        if date_range:
            if date_range.get("start"):
                search_parts.append(f'date_received:[{date_range["start"]} TO *]')

        search_query = " AND ".join(search_parts)
        url = f"{OPENFDA_BASE_URL}/device/event.json?search={quote(search_query)}&limit={limit}"

        try:
            response = await self._rate_limited_request(client, url)

            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            results = data.get("results", [])
            total = data.get("meta", {}).get("results", {}).get("total", 0)

            # Summarize by event type
            event_types = {"Death": 0, "Injury": 0, "Malfunction": 0, "Other": 0}
            device_problems = {}

            for event in results:
                event_type = event.get("event_type", "Other")
                if event_type in event_types:
                    event_types[event_type] += 1
                else:
                    event_types["Other"] += 1

                for problem in event.get("device", [{}])[0].get("device_problem_code", []):
                    device_problems[problem] = device_problems.get(problem, 0) + 1

            return {
                "success": True,
                "manufacturer": manufacturer_name,
                "total_events": total,
                "sample_size": len(results),
                "by_event_type": event_types,
                "top_device_problems": sorted(
                    device_problems.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                "source": "FDA MAUDE Database",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search manufacturer events: {e}")
            return {"success": False, "error": str(e)}

    async def get_phase_relevant_data(
        self,
        current_phase: str,
        product_codes: List[str],
        manufacturer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get FDA data relevant to the current study phase.

        For Phase 4 (Post-Market Surveillance):
        - Gets adverse events from earlier cleared devices
        - Gets 510(k) clearances history
        - Gets any recalls for similar devices

        Args:
            current_phase: Current study phase (e.g., "Phase 4")
            product_codes: List of FDA product codes
            manufacturer: Optional manufacturer name for filtering

        Returns:
            Dict with phase-relevant FDA data
        """
        results = {
            "phase": current_phase,
            "product_codes": product_codes,
            "retrieved_at": datetime.utcnow().isoformat(),
        }

        # Get surveillance data using existing methods
        surveillance = await self.get_surveillance_report(product_codes)
        if surveillance.get("success"):
            results["surveillance"] = {
                "adverse_events": surveillance.get("adverse_events_summary", {}),
                "recalls": surveillance.get("recalls_summary", {}),
                "risk_assessment": surveillance.get("risk_assessment", {}),
            }

        # Get clearance history
        if manufacturer:
            clearances = await self.search_510k_by_applicant(manufacturer, product_codes)
            if clearances.get("success"):
                results["own_clearances"] = {
                    "total": clearances.get("total_found", 0),
                    "recent": clearances.get("clearances", [])[:10],
                }

        # Get competitor clearances
        competitor_data = await self.search_competitor_clearances(
            product_codes,
            exclude_applicants=[manufacturer] if manufacturer else None
        )
        if competitor_data.get("success"):
            results["competitor_clearances"] = {
                "total_companies": competitor_data.get("total_companies", 0),
                "total_clearances": competitor_data.get("total_clearances", 0),
                "top_competitors": competitor_data.get("top_competitors", []),
            }

        # Phase-specific insights
        if current_phase == "Phase 4":
            results["phase_insights"] = {
                "focus": "Post-Market Surveillance",
                "key_data_points": [
                    "MAUDE adverse event trends",
                    "Competitor safety signals",
                    "Recall patterns in product category",
                    "510(k) predicate device performance",
                ],
                "recommended_analyses": [
                    "Compare adverse event rates to competitor devices",
                    "Identify emerging safety signals",
                    "Review post-market commitments from similar clearances",
                ],
            }
        elif current_phase in ["Phase 2", "Phase 3"]:
            results["phase_insights"] = {
                "focus": "Clinical Trial Support",
                "key_data_points": [
                    "Prior clearances for predicate selection",
                    "Safety endpoints from MAUDE data",
                    "Competitor clinical evidence requirements",
                ],
                "recommended_analyses": [
                    "Identify appropriate predicate devices",
                    "Benchmark safety endpoints against real-world data",
                    "Understand FDA expectations for similar devices",
                ],
            }

        results["success"] = True
        return results

    async def close(self):
        """Clean up resources."""
        await self._fda_agent.close()
        if hasattr(self, '_direct_client') and self._direct_client:
            await self._direct_client.aclose()


# Singleton instance
_fda_service: Optional[FDAService] = None


def get_fda_service() -> FDAService:
    """Get singleton FDA service instance."""
    global _fda_service
    if _fda_service is None:
        _fda_service = FDAService()
    return _fda_service
