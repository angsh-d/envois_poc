"""
Study Phase Service for Phase-Aware Data Discovery.

Coordinates FDA and ClinicalTrials.gov data discovery based on the
current study phase. For Phase 4 Post-Market Surveillance studies,
this service:

1. Gets FDA data from earlier phases (if exists)
2. Gets relevant ClinicalTrials.gov data (protocol ID, title-based search)
3. Gets competing studies' FDA submission data for same/earlier phases
4. Gets competing trial data from ClinicalTrials.gov
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.fda_service import get_fda_service, HIP_PRODUCT_CODES
from app.services.clinical_trials_service import get_clinical_trials_service

logger = logging.getLogger(__name__)

# Phase hierarchy for determining "earlier" phases
PHASE_HIERARCHY = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]

# Map common phase descriptions to standard names
PHASE_NORMALIZATION = {
    "phase 1": "Phase 1",
    "phase i": "Phase 1",
    "phase 2": "Phase 2",
    "phase ii": "Phase 2",
    "phase 3": "Phase 3",
    "phase iii": "Phase 3",
    "phase 4": "Phase 4",
    "phase iv": "Phase 4",
    "post-market": "Phase 4",
    "post market": "Phase 4",
    "post-market surveillance": "Phase 4",
    "pms": "Phase 4",
}


class StudyPhaseService:
    """
    Service for phase-aware data discovery.

    Provides comprehensive data discovery that considers study phase
    to gather relevant historical data, competitor data, and
    clinical trial information.
    """

    def __init__(self):
        """Initialize study phase service."""
        self._fda_service = get_fda_service()
        self._ct_service = get_clinical_trials_service()

    def normalize_phase(self, phase_str: str) -> str:
        """Normalize phase string to standard format."""
        if not phase_str:
            return "Unknown"
        normalized = PHASE_NORMALIZATION.get(phase_str.lower().strip())
        if normalized:
            return normalized
        # Try partial match
        for key, value in PHASE_NORMALIZATION.items():
            if key in phase_str.lower():
                return value
        return phase_str

    def get_earlier_phases(self, current_phase: str) -> List[str]:
        """Get list of phases earlier than the current phase."""
        normalized = self.normalize_phase(current_phase)
        if normalized not in PHASE_HIERARCHY:
            return []
        idx = PHASE_HIERARCHY.index(normalized)
        return PHASE_HIERARCHY[:idx]

    async def discover_phase_relevant_sources(
        self,
        product_info: Dict[str, Any],
        competitors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Discover all phase-relevant data sources.

        This is the main entry point for phase-aware discovery. Based on
        the study phase, it gathers:
        - FDA data from earlier phases
        - ClinicalTrials.gov data for own and competitor trials
        - Competitor FDA submissions

        Args:
            product_info: Product information including:
                - protocol_id: Study protocol ID
                - product_name: Product name
                - indication: Clinical indication
                - phase: Study phase
                - manufacturer: Company name
                - product_codes: FDA product codes
            competitors: Optional list of known competitors

        Returns:
            Dict with discovered data sources organized by category
        """
        current_phase = self.normalize_phase(product_info.get("phase", ""))
        protocol_id = product_info.get("protocol_id", "")
        product_name = product_info.get("product_name", "")
        indication = product_info.get("indication", "")
        manufacturer = product_info.get("manufacturer", "")
        product_codes = product_info.get("product_codes", [])
        if not product_codes:
            logger.warning(
                f"No FDA product codes provided for {product_name}. "
                "FDA-related discovery will be limited. "
                "Consider configuring product codes for accurate FDA data."
            )

        results = {
            "current_phase": current_phase,
            "earlier_phases": self.get_earlier_phases(current_phase),
            "protocol_id": protocol_id,
            "discovered_at": datetime.utcnow().isoformat(),
            "sources": {},
        }

        # Run all discovery tasks in parallel
        tasks = []

        # 1. Own trial data from ClinicalTrials.gov
        tasks.append(self._discover_own_trials(protocol_id, product_name, indication))

        # 2. FDA data from earlier phases (own company)
        tasks.append(self._discover_earlier_phase_fda(
            current_phase, product_codes, manufacturer
        ))

        # 3. Competitor trial data from ClinicalTrials.gov
        tasks.append(self._discover_competitor_trials(
            indication, product_name, manufacturer, current_phase, competitors
        ))

        # 4. Competitor FDA submission data
        tasks.append(self._discover_competitor_fda(
            product_codes, manufacturer, competitors
        ))

        # Execute all discovery tasks
        discovery_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        task_names = [
            "own_clinical_trials",
            "earlier_phase_fda",
            "competitor_trials",
            "competitor_fda",
        ]

        for name, result in zip(task_names, discovery_results):
            if isinstance(result, Exception):
                logger.error(f"Discovery task {name} failed: {result}")
                results["sources"][name] = {
                    "success": False,
                    "error": str(result),
                }
            else:
                results["sources"][name] = result

        # Generate summary and recommendations
        results["summary"] = self._generate_discovery_summary(results)
        results["recommendations"] = self._generate_source_recommendations(results, current_phase)

        return results

    async def _discover_own_trials(
        self,
        protocol_id: str,
        product_name: str,
        indication: str,
    ) -> Dict[str, Any]:
        """Discover own trials from ClinicalTrials.gov."""
        results = {
            "source_type": "ClinicalTrials.gov",
            "category": "Own Studies",
            "studies": [],
        }

        # Search by protocol ID if available
        if protocol_id:
            protocol_result = await self._ct_service.search_by_protocol_id(protocol_id)
            if protocol_result.get("success") and protocol_result.get("studies"):
                results["studies"].extend(protocol_result["studies"])
                results["protocol_id_match"] = True

        # Search by title/indication keywords
        if product_name or indication:
            title_keywords = f"{product_name} {indication}".strip()
            if title_keywords:
                title_result = await self._ct_service.search_by_title(
                    title_keywords=title_keywords,
                    condition=indication,
                    max_results=20,
                )
                if title_result.get("success"):
                    # Deduplicate by NCT ID
                    existing_ncts = {s.get("nct_id") for s in results["studies"]}
                    for study in title_result.get("studies", []):
                        if study.get("nct_id") not in existing_ncts:
                            results["studies"].append(study)

        results["total_found"] = len(results["studies"])
        results["success"] = True
        return results

    async def _discover_earlier_phase_fda(
        self,
        current_phase: str,
        product_codes: List[str],
        manufacturer: str,
    ) -> Dict[str, Any]:
        """Discover FDA data from earlier phases."""
        earlier_phases = self.get_earlier_phases(current_phase)

        results = {
            "source_type": "FDA",
            "category": "Earlier Phase Data",
            "current_phase": current_phase,
            "earlier_phases_searched": earlier_phases,
            "data": {},
        }

        if not earlier_phases:
            results["message"] = "No earlier phases to search (Phase 1 or Unknown)"
            results["success"] = True
            return results

        # Get FDA surveillance data (MAUDE, 510k, recalls)
        fda_data = await self._fda_service.get_phase_relevant_data(
            current_phase=current_phase,
            product_codes=product_codes,
            manufacturer=manufacturer,
        )

        if fda_data.get("success"):
            results["data"] = {
                "surveillance": fda_data.get("surveillance", {}),
                "own_clearances": fda_data.get("own_clearances", {}),
                "phase_insights": fda_data.get("phase_insights", {}),
            }
            results["success"] = True
        else:
            results["success"] = False
            results["error"] = fda_data.get("error", "Unknown error")

        return results

    async def _discover_competitor_trials(
        self,
        indication: str,
        intervention: str,
        sponsor_exclude: str,
        current_phase: str,
        known_competitors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Discover competitor trials from ClinicalTrials.gov."""
        results = {
            "source_type": "ClinicalTrials.gov",
            "category": "Competitor Trials",
            "trials_by_phase": {},
            "trials_by_sponsor": {},
        }

        # Get current and earlier phases to search
        phases_to_search = [current_phase] + self.get_earlier_phases(current_phase)
        phases_to_search = [p for p in phases_to_search if p in PHASE_HIERARCHY]

        if not phases_to_search:
            phases_to_search = PHASE_HIERARCHY  # Search all phases

        # Search competitor trials
        competitor_result = await self._ct_service.search_competitor_trials(
            condition=indication,
            intervention_type=intervention,
            sponsor_exclude=sponsor_exclude,
            phases=phases_to_search,
            max_results=100,
        )

        if competitor_result.get("success"):
            results["total_found"] = competitor_result.get("total_found", 0)
            results["unique_sponsors"] = competitor_result.get("unique_sponsors", [])
            results["trials_by_sponsor"] = competitor_result.get("by_sponsor", {})

            # Organize by phase
            for study in competitor_result.get("studies", []):
                phase = study.get("phase", "Unknown")
                if phase not in results["trials_by_phase"]:
                    results["trials_by_phase"][phase] = []
                results["trials_by_phase"][phase].append(study)

            # Cross-reference with known competitors if provided
            if known_competitors:
                known_names = [c.get("company", c.get("manufacturer", "")).lower() for c in known_competitors]
                results["matched_known_competitors"] = [
                    sponsor for sponsor in results["unique_sponsors"]
                    if any(kn in sponsor.lower() for kn in known_names)
                ]

            results["success"] = True
        else:
            results["success"] = False
            results["error"] = competitor_result.get("error", "Unknown error")

        return results

    async def _discover_competitor_fda(
        self,
        product_codes: List[str],
        manufacturer_exclude: str,
        known_competitors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Discover competitor FDA submission data."""
        results = {
            "source_type": "FDA",
            "category": "Competitor FDA Data",
            "clearances_by_company": {},
            "adverse_events_by_company": {},
        }

        # Get competitor clearances
        clearance_result = await self._fda_service.search_competitor_clearances(
            product_codes=product_codes,
            exclude_applicants=[manufacturer_exclude] if manufacturer_exclude else None,
            limit=100,
        )

        if clearance_result.get("success"):
            results["clearances_by_company"] = clearance_result.get("by_company", {})
            results["top_competitors"] = clearance_result.get("top_competitors", [])
            results["total_competitor_clearances"] = clearance_result.get("total_clearances", 0)

            # Get adverse events for top competitors
            top_competitors = [c["company"] for c in results["top_competitors"][:5]]

            ae_tasks = []
            for competitor in top_competitors:
                ae_tasks.append(
                    self._fda_service.search_adverse_events_by_manufacturer(
                        manufacturer_name=competitor,
                        product_codes=product_codes,
                        limit=50,
                    )
                )

            if ae_tasks:
                ae_results = await asyncio.gather(*ae_tasks, return_exceptions=True)
                for competitor, ae_result in zip(top_competitors, ae_results):
                    if isinstance(ae_result, Exception):
                        results["adverse_events_by_company"][competitor] = {
                            "success": False,
                            "error": str(ae_result),
                        }
                    elif ae_result.get("success"):
                        results["adverse_events_by_company"][competitor] = {
                            "total_events": ae_result.get("total_events", 0),
                            "by_event_type": ae_result.get("by_event_type", {}),
                            "top_problems": ae_result.get("top_device_problems", [])[:5],
                        }

            results["success"] = True
        else:
            results["success"] = False
            results["error"] = clearance_result.get("error", "Unknown error")

        return results

    def _generate_discovery_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of discovered sources."""
        sources = results.get("sources", {})

        summary = {
            "total_sources_discovered": 0,
            "by_category": {},
        }

        # Own trials
        own_trials = sources.get("own_clinical_trials", {})
        if own_trials.get("success"):
            count = own_trials.get("total_found", 0)
            summary["by_category"]["own_trials"] = count
            summary["total_sources_discovered"] += count

        # Earlier phase FDA
        earlier_fda = sources.get("earlier_phase_fda", {})
        if earlier_fda.get("success"):
            data = earlier_fda.get("data", {})
            clearance_count = data.get("own_clearances", {}).get("total", 0)
            summary["by_category"]["own_fda_clearances"] = clearance_count
            summary["total_sources_discovered"] += clearance_count

        # Competitor trials
        competitor_trials = sources.get("competitor_trials", {})
        if competitor_trials.get("success"):
            count = competitor_trials.get("total_found", 0)
            summary["by_category"]["competitor_trials"] = count
            summary["total_sources_discovered"] += count
            summary["unique_competitor_sponsors"] = len(competitor_trials.get("unique_sponsors", []))

        # Competitor FDA
        competitor_fda = sources.get("competitor_fda", {})
        if competitor_fda.get("success"):
            count = competitor_fda.get("total_competitor_clearances", 0)
            summary["by_category"]["competitor_fda_clearances"] = count
            summary["total_sources_discovered"] += count

        return summary

    def _generate_source_recommendations(
        self,
        results: Dict[str, Any],
        current_phase: str,
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for which sources to use."""
        recommendations = []
        sources = results.get("sources", {})

        # Recommend own trials
        own_trials = sources.get("own_clinical_trials", {})
        if own_trials.get("success") and own_trials.get("total_found", 0) > 0:
            recommendations.append({
                "source_type": "own_clinical_trials",
                "reason": "Found matching trials for your protocol/product on ClinicalTrials.gov",
                "count": own_trials.get("total_found"),
                "priority": "high",
                "value": "Provides context on study design, endpoints, and enrollment",
            })

        # Recommend earlier phase FDA data (especially for Phase 4)
        earlier_fda = sources.get("earlier_phase_fda", {})
        if earlier_fda.get("success"):
            data = earlier_fda.get("data", {})
            if data.get("own_clearances", {}).get("total", 0) > 0:
                recommendations.append({
                    "source_type": "earlier_phase_fda",
                    "reason": f"Found prior FDA clearances for your company",
                    "count": data["own_clearances"]["total"],
                    "priority": "high" if current_phase == "Phase 4" else "medium",
                    "value": "510(k) submission history and predicate device information",
                })

            if data.get("surveillance", {}).get("adverse_events"):
                recommendations.append({
                    "source_type": "fda_surveillance",
                    "reason": "MAUDE adverse event data available for your product category",
                    "priority": "high" if current_phase == "Phase 4" else "medium",
                    "value": "Post-market safety signals and event patterns",
                })

        # Recommend competitor trial data
        competitor_trials = sources.get("competitor_trials", {})
        if competitor_trials.get("success") and competitor_trials.get("total_found", 0) > 0:
            recommendations.append({
                "source_type": "competitor_trials",
                "reason": f"Found {competitor_trials.get('total_found')} competitor trials on ClinicalTrials.gov",
                "count": competitor_trials.get("total_found"),
                "unique_sponsors": len(competitor_trials.get("unique_sponsors", [])),
                "priority": "medium",
                "value": "Competitor study designs, endpoints, and enrollment strategies",
            })

        # Recommend competitor FDA data
        competitor_fda = sources.get("competitor_fda", {})
        if competitor_fda.get("success") and competitor_fda.get("total_competitor_clearances", 0) > 0:
            recommendations.append({
                "source_type": "competitor_fda",
                "reason": f"Found {competitor_fda.get('total_competitor_clearances')} competitor FDA clearances",
                "count": competitor_fda.get("total_competitor_clearances"),
                "top_competitors": [c["company"] for c in competitor_fda.get("top_competitors", [])[:5]],
                "priority": "high" if current_phase == "Phase 4" else "medium",
                "value": "Competitor regulatory strategy, predicate devices, and safety data",
            })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))

        return recommendations

    async def close(self):
        """Clean up resources."""
        await self._fda_service.close()
        await self._ct_service.close()


# Singleton instance
_study_phase_service: Optional[StudyPhaseService] = None


def get_study_phase_service() -> StudyPhaseService:
    """Get singleton study phase service instance."""
    global _study_phase_service
    if _study_phase_service is None:
        _study_phase_service = StudyPhaseService()
    return _study_phase_service
