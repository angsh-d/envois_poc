"""
FDA Agent for Clinical Intelligence Platform.

Integrates with openFDA public APIs to retrieve:
- Device adverse events (MAUDE database)
- 510(k) clearances
- Device recalls

This agent helps close data gaps for Quality persona by providing
real-world device surveillance data.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import httpx

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentResult, AgentType, SourceType
)

logger = logging.getLogger(__name__)


# FDA Product codes for hip prostheses
HIP_PRODUCT_CODES = {
    "LPH": "Hip prosthesis, semi-constrained, metal/polymer, uncemented, acetabular",
    "KWZ": "Hip prosthesis, semi-constrained, porous-coated, uncemented",
    "MBL": "Hip prosthesis, semi-constrained, metal/polymer, porous-coated",
    "LZO": "Hip prosthesis, semi-constrained, acetabular component",
    "MQP": "Hip prosthesis, femoral component, cemented",
    "MQV": "Hip prosthesis, femoral component, uncemented",
}

# openFDA API base URL
OPENFDA_BASE_URL = "https://api.fda.gov"

# Rate limit: 240 requests per minute for unauthenticated, 120 per minute to be safe
FDA_REQUEST_DELAY_SECONDS = 0.5


class FDAAgent(BaseAgent):
    """
    Agent for FDA public data integration.

    Capabilities:
    - Query MAUDE database for device adverse events
    - Retrieve 510(k) clearance information
    - Check device recall status
    - Analyze adverse event trends
    """

    agent_type = AgentType.FDA

    def __init__(self, **kwargs):
        """Initialize FDA agent."""
        super().__init__(**kwargs)
        self._http_client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._http_client

    async def _rate_limited_request(
        self,
        client: httpx.AsyncClient,
        url: str
    ) -> httpx.Response:
        """Make rate-limited request to FDA API."""
        import time
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < FDA_REQUEST_DELAY_SECONDS:
            await asyncio.sleep(FDA_REQUEST_DELAY_SECONDS - elapsed)
        self._last_request_time = time.time()
        return await client.get(url)

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute FDA data retrieval.

        Args:
            context: Execution context with query parameters

        Returns:
            AgentResult with FDA data

        Query Types:
            - adverse_events: Get device adverse events from MAUDE
            - clearances: Get 510(k) clearance information
            - recalls: Get device recall status
            - surveillance: Combined surveillance report
            - trends: Analyze adverse event trends over time
        """
        result = AgentResult(
            agent_type=self.agent_type,
            success=True,
        )

        query_type = context.parameters.get("query_type", "surveillance")
        product_codes = context.parameters.get(
            "product_codes", list(HIP_PRODUCT_CODES.keys())[:3]
        )
        date_range = context.parameters.get("date_range", {})

        if query_type == "adverse_events":
            result.data = await self._get_adverse_events(product_codes, date_range)
        elif query_type == "clearances":
            result.data = await self._get_clearances(product_codes)
        elif query_type == "recalls":
            result.data = await self._get_recalls(product_codes)
        elif query_type == "surveillance":
            result.data = await self._get_full_surveillance(product_codes, date_range)
        elif query_type == "trends":
            result.data = await self._get_adverse_event_trends(product_codes, date_range)
        else:
            result.success = False
            result.error = f"Unknown query_type: {query_type}"
            return result

        # Add source provenance
        self._add_sources(result, query_type)

        return result

    async def _get_adverse_events(
        self,
        product_codes: List[str],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Query MAUDE database for device adverse events.

        Args:
            product_codes: List of FDA product codes to search
            date_range: Optional date range (start, end)

        Returns:
            Dict with adverse event data
        """
        client = await self._get_client()

        # Build search query with proper encoding
        code_parts = [
            f'device.device_report_product_code:"{code}"'
            for code in product_codes
        ]
        code_query = " OR ".join(code_parts)

        # Add date range if provided
        if date_range.get("start") and date_range.get("end"):
            search_query = (
                f'({code_query}) AND date_received:'
                f'[{date_range["start"]} TO {date_range["end"]}]'
            )
        else:
            # Default to last 5 years
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=5*365)).strftime("%Y%m%d")
            search_query = f'({code_query}) AND date_received:[{start_date} TO {end_date}]'

        # URL-encode the search query
        encoded_query = quote(search_query, safe='')

        try:
            # Get total count by event type
            count_url = (
                f"{OPENFDA_BASE_URL}/device/event.json?"
                f"search={encoded_query}&count=event_type.exact"
            )
            count_response = await self._rate_limited_request(client, count_url)

            event_counts = {}
            if count_response.status_code == 200:
                count_data = count_response.json()
                event_counts = {
                    r["term"]: r["count"]
                    for r in count_data.get("results", [])
                }
            elif count_response.status_code != 404:
                # 404 means no results, which is fine; other errors should be logged
                logger.warning(
                    f"FDA count API returned {count_response.status_code}: "
                    f"{count_response.text[:200]}"
                )

            # Get sample events
            events_url = (
                f"{OPENFDA_BASE_URL}/device/event.json?"
                f"search={encoded_query}&limit=100"
            )
            events_response = await self._rate_limited_request(client, events_url)

            events = []
            if events_response.status_code == 200:
                events_data = events_response.json()
                for event in events_data.get("results", [])[:50]:
                    events.append({
                        "report_number": event.get("report_number"),
                        "event_type": event.get("event_type"),
                        "date_received": event.get("date_received"),
                        "device_problem": self._extract_device_problems(event),
                        "patient_problem": self._extract_patient_problems(event),
                        "manufacturer": self._extract_manufacturer(event),
                        "brand_name": self._extract_brand_name(event),
                        "mdr_text": self._extract_mdr_text(event),
                    })
            elif events_response.status_code != 404:
                logger.warning(
                    f"FDA events API returned {events_response.status_code}: "
                    f"{events_response.text[:200]}"
                )

            # Calculate summary statistics
            total_events = sum(event_counts.values())
            injury_count = event_counts.get("Injury", 0)
            malfunction_count = event_counts.get("Malfunction", 0)
            death_count = event_counts.get("Death", 0)

            return {
                "success": True,
                "query_parameters": {
                    "product_codes": product_codes,
                    "date_range": date_range or {"start": start_date, "end": end_date},
                },
                "summary": {
                    "total_events": total_events,
                    "by_event_type": event_counts,
                    "injury_rate": round(injury_count / total_events, 3) if total_events > 0 else 0,
                    "death_rate": round(death_count / total_events, 4) if total_events > 0 else 0,
                    "malfunction_rate": round(malfunction_count / total_events, 3) if total_events > 0 else 0,
                },
                "sample_events": events[:20],
                "data_source": "FDA MAUDE Database",
                "last_updated": datetime.utcnow().isoformat(),
            }

        except httpx.RequestError as e:
            logger.error(f"FDA API request failed: {e}")
            return {
                "success": False,
                "error": f"FDA API request failed: {str(e)}",
                "data_source": "FDA MAUDE Database",
            }
        except Exception as e:
            logger.exception(f"Unexpected error querying FDA API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data_source": "FDA MAUDE Database",
            }

    def _extract_device_problems(self, event: Dict) -> List[str]:
        """Extract device problem codes from event."""
        problems = []
        # Device problems are at device level
        for device in event.get("device", []):
            openfda = device.get("openfda", {})
            # device_problem field contains problem descriptions
            for problem in openfda.get("device_class", []):
                if problem and problem not in problems:
                    problems.append(problem)
        # Also check top-level device_problem field
        for problem in event.get("device_problem", []):
            if problem and problem not in problems:
                problems.append(problem)
        return problems[:5]

    def _extract_patient_problems(self, event: Dict) -> List[str]:
        """Extract patient problem descriptions from event."""
        problems = []
        # Patient problems are in patient array
        for patient in event.get("patient", []):
            for problem in patient.get("patient_problems", []):
                if problem and problem not in problems:
                    problems.append(problem)
        return problems[:5]

    def _extract_mdr_text(self, event: Dict) -> Optional[str]:
        """Extract MDR narrative text from event."""
        # MDR text is in mdr_text array
        mdr_texts = event.get("mdr_text", [])
        for mdr in mdr_texts:
            text = mdr.get("text", "")
            text_type = mdr.get("text_type_code", "")
            # Prefer description of event or additional narrative
            if text_type in ["Description of Event or Problem", "Additional Manufacturer Narrative"]:
                if text:
                    return text[:500]  # Truncate to prevent data bloat
        # Fallback to first available text
        if mdr_texts and mdr_texts[0].get("text"):
            return mdr_texts[0]["text"][:500]
        return None

    def _extract_manufacturer(self, event: Dict) -> Optional[str]:
        """Extract manufacturer name from event."""
        for device in event.get("device", []):
            name = device.get("manufacturer_d_name")
            if name:
                return name
        return None

    def _extract_brand_name(self, event: Dict) -> Optional[str]:
        """Extract brand name from event."""
        for device in event.get("device", []):
            name = device.get("brand_name")
            if name:
                return name
        return None

    async def _get_clearances(self, product_codes: List[str]) -> Dict[str, Any]:
        """
        Get 510(k) clearance information for product codes.

        Args:
            product_codes: List of FDA product codes

        Returns:
            Dict with clearance data
        """
        client = await self._get_client()

        code_query = " OR ".join([
            f'product_code:"{code}"'
            for code in product_codes
        ])
        encoded_query = quote(code_query, safe='')

        try:
            # Get clearances
            url = (
                f"{OPENFDA_BASE_URL}/device/510k.json?"
                f"search={encoded_query}&limit=100"
            )
            response = await self._rate_limited_request(client, url)

            clearances = []
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    clearances.append({
                        "k_number": item.get("k_number"),
                        "device_name": item.get("device_name"),
                        "applicant": item.get("applicant"),
                        "decision_date": item.get("decision_date"),
                        "decision_description": item.get("decision_description"),
                        "product_code": item.get("product_code"),
                        "statement_or_summary": item.get("statement_or_summary"),
                    })
            elif response.status_code != 404:
                logger.warning(
                    f"FDA 510k API returned {response.status_code}: "
                    f"{response.text[:200]}"
                )

            # Count by year
            by_year = {}
            for c in clearances:
                year = c.get("decision_date", "")[:4]
                if year:
                    by_year[year] = by_year.get(year, 0) + 1

            return {
                "success": True,
                "query_parameters": {"product_codes": product_codes},
                "total_clearances": len(clearances),
                "by_year": by_year,
                "recent_clearances": clearances[:20],
                "data_source": "FDA 510(k) Database",
                "last_updated": datetime.utcnow().isoformat(),
            }

        except httpx.RequestError as e:
            logger.error(f"FDA 510k API request failed: {e}")
            return {
                "success": False,
                "error": f"FDA API request failed: {str(e)}",
                "data_source": "FDA 510(k) Database",
            }
        except Exception as e:
            logger.exception(f"Unexpected error querying FDA 510k API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data_source": "FDA 510(k) Database",
            }

    async def _get_recalls(self, product_codes: List[str]) -> Dict[str, Any]:
        """
        Get device recall information.

        Args:
            product_codes: List of FDA product codes

        Returns:
            Dict with recall data
        """
        client = await self._get_client()

        code_query = " OR ".join([
            f'product_code:"{code}"'
            for code in product_codes
        ])
        encoded_query = quote(code_query, safe='')

        try:
            url = (
                f"{OPENFDA_BASE_URL}/device/recall.json?"
                f"search={encoded_query}&limit=100"
            )
            response = await self._rate_limited_request(client, url)

            recalls = []
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    recalls.append({
                        "recall_number": item.get("recall_number"),
                        "product_description": item.get("product_description"),
                        "recalling_firm": item.get("recalling_firm"),
                        "recall_initiation_date": item.get("recall_initiation_date"),
                        "termination_date": item.get("termination_date"),
                        "reason_for_recall": item.get("reason_for_recall"),
                        "event_id": item.get("event_id"),
                        "status": item.get("status"),
                    })
            elif response.status_code != 404:
                logger.warning(
                    f"FDA Recall API returned {response.status_code}: "
                    f"{response.text[:200]}"
                )

            # Categorize by status
            active_recalls = [r for r in recalls if r.get("status") == "Ongoing"]
            terminated_recalls = [r for r in recalls if r.get("status") == "Terminated"]

            return {
                "success": True,
                "query_parameters": {"product_codes": product_codes},
                "total_recalls": len(recalls),
                "active_count": len(active_recalls),
                "terminated_count": len(terminated_recalls),
                "active_recalls": active_recalls[:10],
                "recent_terminated": terminated_recalls[:10],
                "data_source": "FDA Device Recall Database",
                "last_updated": datetime.utcnow().isoformat(),
            }

        except httpx.RequestError as e:
            logger.error(f"FDA Recall API request failed: {e}")
            return {
                "success": False,
                "error": f"FDA API request failed: {str(e)}",
                "data_source": "FDA Device Recall Database",
            }
        except Exception as e:
            logger.exception(f"Unexpected error querying FDA Recall API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data_source": "FDA Device Recall Database",
            }

    async def _get_full_surveillance(
        self,
        product_codes: List[str],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Get comprehensive surveillance report combining all data sources.

        Args:
            product_codes: List of FDA product codes
            date_range: Optional date range

        Returns:
            Combined surveillance data
        """
        # Run all queries in parallel
        adverse_events, clearances, recalls = await asyncio.gather(
            self._get_adverse_events(product_codes, date_range),
            self._get_clearances(product_codes),
            self._get_recalls(product_codes),
        )

        # Calculate risk score based on surveillance data
        risk_score = self._calculate_surveillance_risk_score(
            adverse_events, recalls
        )

        return {
            "success": True,
            "surveillance_date": datetime.utcnow().isoformat(),
            "product_codes": product_codes,
            "product_descriptions": {
                code: HIP_PRODUCT_CODES.get(code, "Unknown")
                for code in product_codes
            },
            "adverse_events": adverse_events,
            "clearances": clearances,
            "recalls": recalls,
            "risk_assessment": risk_score,
            "data_sources": [
                "FDA MAUDE Database",
                "FDA 510(k) Database",
                "FDA Device Recall Database",
            ],
        }

    def _calculate_surveillance_risk_score(
        self,
        adverse_events: Dict,
        recalls: Dict
    ) -> Dict[str, Any]:
        """Calculate overall surveillance risk score."""
        risk_factors = []
        score = 0

        # Check adverse event rates
        ae_summary = adverse_events.get("summary", {})
        death_rate = ae_summary.get("death_rate", 0)
        injury_rate = ae_summary.get("injury_rate", 0)

        if death_rate > 0.01:
            risk_factors.append(f"Elevated death rate: {death_rate*100:.2f}%")
            score += 30
        elif death_rate > 0:
            risk_factors.append(f"Deaths reported: {death_rate*100:.3f}%")
            score += 15

        if injury_rate > 0.5:
            risk_factors.append(f"High injury rate: {injury_rate*100:.1f}%")
            score += 20
        elif injury_rate > 0.3:
            risk_factors.append(f"Moderate injury rate: {injury_rate*100:.1f}%")
            score += 10

        # Check active recalls
        active_recalls = recalls.get("active_count", 0)
        if active_recalls > 0:
            risk_factors.append(f"Active recalls: {active_recalls}")
            score += 25 * min(active_recalls, 3)

        # Determine risk level
        if score >= 50:
            risk_level = "HIGH"
        elif score >= 25:
            risk_level = "MODERATE"
        elif score > 0:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"

        return {
            "risk_score": score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level),
        }

    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level."""
        recommendations = {
            "HIGH": "Immediate review required. Consider enhanced surveillance and regulatory notification.",
            "MODERATE": "Increased monitoring recommended. Review adverse event patterns quarterly.",
            "LOW": "Continue routine surveillance. Annual review sufficient.",
            "MINIMAL": "No immediate concerns. Standard post-market surveillance protocols apply.",
        }
        return recommendations.get(risk_level, "Unable to determine recommendation.")

    async def _get_adverse_event_trends(
        self,
        product_codes: List[str],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyze adverse event trends over time.

        Args:
            product_codes: List of FDA product codes
            date_range: Optional date range

        Returns:
            Trend analysis data
        """
        client = await self._get_client()

        code_query = " OR ".join([
            f'device.device_report_product_code:"{code}"'
            for code in product_codes
        ])
        encoded_query = quote(code_query, safe='')

        try:
            # Get counts by year
            url = (
                f"{OPENFDA_BASE_URL}/device/event.json?"
                f"search={encoded_query}&count=date_received"
            )
            response = await self._rate_limited_request(client, url)

            trends_by_year = {}
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    time_str = item.get("time", "")
                    year = time_str[:4] if time_str else None
                    if year:
                        trends_by_year[year] = trends_by_year.get(year, 0) + item.get("count", 0)
            elif response.status_code != 404:
                logger.warning(
                    f"FDA trends API returned {response.status_code}: "
                    f"{response.text[:200]}"
                )

            # Calculate year-over-year changes
            years = sorted(trends_by_year.keys())
            yoy_changes = []
            for i, year in enumerate(years[1:], 1):
                prev_year = years[i-1]
                if trends_by_year[prev_year] > 0:
                    change = (trends_by_year[year] - trends_by_year[prev_year]) / trends_by_year[prev_year]
                    yoy_changes.append({
                        "year": year,
                        "count": trends_by_year[year],
                        "previous_count": trends_by_year[prev_year],
                        "change_percent": round(change * 100, 1),
                        "direction": "increasing" if change > 0.1 else "decreasing" if change < -0.1 else "stable"
                    })

            # Identify trend direction
            if len(yoy_changes) >= 2:
                recent_changes = [c["change_percent"] for c in yoy_changes[-3:]]
                avg_change = sum(recent_changes) / len(recent_changes)
                if avg_change > 10:
                    overall_trend = "INCREASING"
                elif avg_change < -10:
                    overall_trend = "DECREASING"
                else:
                    overall_trend = "STABLE"
            else:
                overall_trend = "INSUFFICIENT_DATA"

            return {
                "success": True,
                "query_parameters": {"product_codes": product_codes},
                "trends_by_year": trends_by_year,
                "year_over_year_changes": yoy_changes,
                "overall_trend": overall_trend,
                "trend_insight": self._generate_trend_insight(overall_trend, yoy_changes),
                "data_source": "FDA MAUDE Database",
                "last_updated": datetime.utcnow().isoformat(),
            }

        except httpx.RequestError as e:
            logger.error(f"FDA trends API request failed: {e}")
            return {
                "success": False,
                "error": f"FDA API request failed: {str(e)}",
                "data_source": "FDA MAUDE Database",
            }
        except Exception as e:
            logger.exception(f"Unexpected error querying FDA trends API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data_source": "FDA MAUDE Database",
            }

    def _generate_trend_insight(
        self,
        trend: str,
        yoy_changes: List[Dict]
    ) -> str:
        """Generate human-readable trend insight."""
        if trend == "INCREASING":
            return (
                "Adverse event reports are increasing. This may indicate "
                "growing adoption, enhanced reporting, or emerging safety signals. "
                "Root cause analysis recommended."
            )
        elif trend == "DECREASING":
            return (
                "Adverse event reports are decreasing. This may reflect "
                "improved product performance, declining market share, or "
                "changes in reporting practices."
            )
        elif trend == "STABLE":
            return (
                "Adverse event reporting is stable. Continue routine "
                "surveillance and monitor for any emerging patterns."
            )
        else:
            return "Insufficient data to determine trend direction."

    def _add_sources(self, result: AgentResult, query_type: str) -> None:
        """Add source provenance to result."""
        if query_type in ["adverse_events", "trends", "surveillance"]:
            result.add_source(
                SourceType.FDA_MAUDE,
                "FDA MAUDE Database (Manufacturer and User Facility Device Experience)",
                confidence=0.95,
                details={
                    "api_endpoint": f"{OPENFDA_BASE_URL}/device/event.json",
                    "coverage": "1992-present",
                    "update_frequency": "Weekly",
                }
            )

        if query_type in ["clearances", "surveillance"]:
            result.add_source(
                SourceType.FDA_510K,
                "FDA 510(k) Premarket Notification Database",
                confidence=0.98,
                details={
                    "api_endpoint": f"{OPENFDA_BASE_URL}/device/510k.json",
                    "coverage": "1976-present",
                }
            )

        if query_type in ["recalls", "surveillance"]:
            result.add_source(
                SourceType.FDA_RECALL,
                "FDA Device Recall Database",
                confidence=0.98,
                details={
                    "api_endpoint": f"{OPENFDA_BASE_URL}/device/recall.json",
                    "coverage": "All active and recent recalls",
                }
            )

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
