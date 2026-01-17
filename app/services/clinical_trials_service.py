"""
ClinicalTrials.gov Service for Clinical Intelligence Platform.

Provides integration with ClinicalTrials.gov API to retrieve:
- Study data by NCT ID or protocol ID
- Related studies by condition/intervention
- Competitor trials for similar indications
- Phase-specific trial data
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# ClinicalTrials.gov API v2 base URL
CT_GOV_API_BASE = "https://clinicaltrials.gov/api/v2"

# Rate limiting
CT_REQUEST_DELAY_SECONDS = 0.3

# Study phase mapping
STUDY_PHASES = {
    "Phase 1": ["PHASE1", "EARLY_PHASE1"],
    "Phase 2": ["PHASE2"],
    "Phase 3": ["PHASE3"],
    "Phase 4": ["PHASE4"],
    "Not Applicable": ["NA"],
}

# Reverse mapping for display
PHASE_DISPLAY_MAP = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE2": "Phase 2",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
    "NA": "Not Applicable",
}


class ClinicalTrialsService:
    """
    Service for ClinicalTrials.gov integration.

    Provides:
    - Study lookup by NCT ID or protocol ID
    - Search for related trials by condition/intervention
    - Competitor trial discovery
    - Phase-based trial filtering
    """

    def __init__(self):
        """Initialize ClinicalTrials.gov service."""
        self._http_client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._http_client

    async def _rate_limited_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Optional[Dict] = None,
    ) -> httpx.Response:
        """Make rate-limited request to ClinicalTrials.gov API."""
        import time
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < CT_REQUEST_DELAY_SECONDS:
            await asyncio.sleep(CT_REQUEST_DELAY_SECONDS - elapsed)
        self._last_request_time = time.time()
        return await client.get(url, params=params)

    async def search_by_protocol_id(
        self,
        protocol_id: str,
        include_similar: bool = True,
    ) -> Dict[str, Any]:
        """
        Search for studies by protocol ID.

        Args:
            protocol_id: Protocol identifier (e.g., H-34)
            include_similar: Whether to include similar studies

        Returns:
            Dict with matching studies
        """
        client = await self._get_client()

        # Search for exact protocol ID match in various ID fields
        query = f'AREA[OrgStudyId]{protocol_id} OR AREA[SecondaryId]{protocol_id}'

        params = {
            "query.term": query,
            "pageSize": 20,
            "format": "json",
            "fields": "NCTId,OrgStudyId,BriefTitle,OfficialTitle,Phase,OverallStatus,"
                      "Condition,InterventionName,EnrollmentCount,StartDate,CompletionDate,"
                      "StudyType,Sponsor,LeadSponsor,Collaborator,ResultsFirstPostDate",
        }

        try:
            response = await self._rate_limited_request(
                client, f"{CT_GOV_API_BASE}/studies", params
            )

            if response.status_code != 200:
                logger.warning(f"ClinicalTrials.gov API error: {response.status_code}")
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            studies = data.get("studies", [])

            return {
                "success": True,
                "protocol_id": protocol_id,
                "total_found": len(studies),
                "studies": [self._parse_study(s) for s in studies],
                "source": "ClinicalTrials.gov",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search ClinicalTrials.gov: {e}")
            return {"success": False, "error": str(e)}

    async def search_by_title(
        self,
        title_keywords: str,
        condition: Optional[str] = None,
        intervention: Optional[str] = None,
        phases: Optional[List[str]] = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for studies by title keywords.

        Args:
            title_keywords: Keywords to search in study title
            condition: Optional condition filter
            intervention: Optional intervention filter
            phases: Optional list of phases to filter
            max_results: Maximum number of results

        Returns:
            Dict with matching studies
        """
        client = await self._get_client()

        # Build query
        query_parts = [f'AREA[BriefTitle]{title_keywords}']

        if condition:
            query_parts.append(f'AREA[Condition]{condition}')

        if intervention:
            query_parts.append(f'AREA[InterventionName]{intervention}')

        query = ' AND '.join(query_parts)

        params = {
            "query.term": query,
            "pageSize": min(max_results, 100),
            "format": "json",
            "fields": "NCTId,OrgStudyId,BriefTitle,OfficialTitle,Phase,OverallStatus,"
                      "Condition,InterventionName,EnrollmentCount,StartDate,CompletionDate,"
                      "StudyType,Sponsor,LeadSponsor,ResultsFirstPostDate",
        }

        # Add phase filter if specified
        if phases:
            phase_values = []
            for phase in phases:
                if phase in STUDY_PHASES:
                    phase_values.extend(STUDY_PHASES[phase])
            if phase_values:
                params["filter.advanced"] = f"AREA[Phase]({' OR '.join(phase_values)})"

        try:
            response = await self._rate_limited_request(
                client, f"{CT_GOV_API_BASE}/studies", params
            )

            if response.status_code != 200:
                logger.warning(f"ClinicalTrials.gov API error: {response.status_code}")
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            studies = data.get("studies", [])

            return {
                "success": True,
                "query": title_keywords,
                "total_found": len(studies),
                "studies": [self._parse_study(s) for s in studies],
                "filters_applied": {
                    "condition": condition,
                    "intervention": intervention,
                    "phases": phases,
                },
                "source": "ClinicalTrials.gov",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search ClinicalTrials.gov: {e}")
            return {"success": False, "error": str(e)}

    async def search_competitor_trials(
        self,
        condition: str,
        intervention_type: str,
        sponsor_exclude: Optional[str] = None,
        phases: Optional[List[str]] = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for competitor trials with similar conditions/interventions.

        Args:
            condition: Medical condition (e.g., "Revision Total Hip Arthroplasty")
            intervention_type: Type of intervention (e.g., "hip prosthesis")
            sponsor_exclude: Sponsor name to exclude (own company)
            phases: Optional list of phases to filter
            max_results: Maximum number of results

        Returns:
            Dict with competitor trials
        """
        client = await self._get_client()

        # Build query for condition and intervention
        query = f'AREA[Condition]{condition} AND AREA[InterventionName]{intervention_type}'

        params = {
            "query.term": query,
            "pageSize": min(max_results, 100),
            "format": "json",
            "fields": "NCTId,OrgStudyId,BriefTitle,OfficialTitle,Phase,OverallStatus,"
                      "Condition,InterventionName,EnrollmentCount,StartDate,CompletionDate,"
                      "StudyType,Sponsor,LeadSponsor,Collaborator,ResultsFirstPostDate,"
                      "PrimaryOutcome,SecondaryOutcome",
        }

        # Add phase filter if specified
        if phases:
            phase_values = []
            for phase in phases:
                if phase in STUDY_PHASES:
                    phase_values.extend(STUDY_PHASES[phase])
            if phase_values:
                params["filter.advanced"] = f"AREA[Phase]({' OR '.join(phase_values)})"

        try:
            response = await self._rate_limited_request(
                client, f"{CT_GOV_API_BASE}/studies", params
            )

            if response.status_code != 200:
                logger.warning(f"ClinicalTrials.gov API error: {response.status_code}")
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            studies = data.get("studies", [])

            # Parse and filter out own company if specified
            parsed_studies = []
            for study in studies:
                parsed = self._parse_study(study)
                if sponsor_exclude and parsed.get("lead_sponsor", "").lower() == sponsor_exclude.lower():
                    continue
                parsed_studies.append(parsed)

            # Group by sponsor for competitive analysis
            sponsors = {}
            for study in parsed_studies:
                sponsor = study.get("lead_sponsor", "Unknown")
                if sponsor not in sponsors:
                    sponsors[sponsor] = []
                sponsors[sponsor].append(study)

            return {
                "success": True,
                "condition": condition,
                "intervention_type": intervention_type,
                "total_found": len(parsed_studies),
                "studies": parsed_studies,
                "by_sponsor": sponsors,
                "unique_sponsors": list(sponsors.keys()),
                "phases_included": phases,
                "source": "ClinicalTrials.gov",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search competitor trials: {e}")
            return {"success": False, "error": str(e)}

    async def get_earlier_phase_trials(
        self,
        current_phase: str,
        condition: str,
        intervention: str,
        sponsor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get trials from earlier phases for the same condition/intervention.

        Args:
            current_phase: Current study phase (e.g., "Phase 4")
            condition: Medical condition
            intervention: Intervention type
            sponsor: Optional sponsor filter

        Returns:
            Dict with earlier phase trials
        """
        # Determine earlier phases
        phase_order = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
        current_idx = phase_order.index(current_phase) if current_phase in phase_order else -1

        if current_idx <= 0:
            return {
                "success": True,
                "message": "No earlier phases exist",
                "studies": [],
                "earlier_phases": [],
            }

        earlier_phases = phase_order[:current_idx]

        client = await self._get_client()

        # Build phase filter
        phase_values = []
        for phase in earlier_phases:
            if phase in STUDY_PHASES:
                phase_values.extend(STUDY_PHASES[phase])

        # Build query
        query = f'AREA[Condition]{condition} AND AREA[InterventionName]{intervention}'
        if sponsor:
            query += f' AND AREA[LeadSponsorName]{sponsor}'

        params = {
            "query.term": query,
            "pageSize": 100,
            "format": "json",
            "filter.advanced": f"AREA[Phase]({' OR '.join(phase_values)})" if phase_values else None,
            "fields": "NCTId,OrgStudyId,BriefTitle,OfficialTitle,Phase,OverallStatus,"
                      "Condition,InterventionName,EnrollmentCount,StartDate,CompletionDate,"
                      "StudyType,LeadSponsor,ResultsFirstPostDate,PrimaryOutcome",
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            response = await self._rate_limited_request(
                client, f"{CT_GOV_API_BASE}/studies", params
            )

            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code}"}

            data = response.json()
            studies = data.get("studies", [])

            # Group by phase
            studies_by_phase = {phase: [] for phase in earlier_phases}
            for study in studies:
                parsed = self._parse_study(study)
                study_phase = parsed.get("phase", "Unknown")
                for phase in earlier_phases:
                    if phase in study_phase or study_phase in phase:
                        studies_by_phase[phase].append(parsed)
                        break

            return {
                "success": True,
                "current_phase": current_phase,
                "earlier_phases": earlier_phases,
                "total_found": len(studies),
                "studies": [self._parse_study(s) for s in studies],
                "by_phase": studies_by_phase,
                "source": "ClinicalTrials.gov",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get earlier phase trials: {e}")
            return {"success": False, "error": str(e)}

    async def get_study_details(self, nct_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific study by NCT ID.

        Args:
            nct_id: ClinicalTrials.gov NCT identifier

        Returns:
            Dict with full study details
        """
        client = await self._get_client()

        try:
            response = await self._rate_limited_request(
                client, f"{CT_GOV_API_BASE}/studies/{nct_id}"
            )

            if response.status_code != 200:
                return {"success": False, "error": f"Study not found: {nct_id}"}

            data = response.json()
            study = data.get("protocolSection", {})

            return {
                "success": True,
                "nct_id": nct_id,
                "study": self._parse_full_study(study),
                "source": "ClinicalTrials.gov",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get study details: {e}")
            return {"success": False, "error": str(e)}

    def _parse_study(self, study_data: Dict) -> Dict[str, Any]:
        """Parse study data from API response."""
        protocol = study_data.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        design_module = protocol.get("designModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        interventions_module = protocol.get("armsInterventionsModule", {})
        results_module = study_data.get("resultsSection", {})

        # Get phases
        phases = design_module.get("phases", [])
        phase_display = ", ".join([PHASE_DISPLAY_MAP.get(p, p) for p in phases]) if phases else "Not Specified"

        # Get interventions
        interventions = interventions_module.get("interventions", [])
        intervention_names = [i.get("name", "") for i in interventions]

        # Get lead sponsor
        lead_sponsor = sponsor_module.get("leadSponsor", {})

        return {
            "nct_id": id_module.get("nctId", ""),
            "org_study_id": id_module.get("orgStudyIdInfo", {}).get("id", ""),
            "brief_title": id_module.get("briefTitle", ""),
            "official_title": id_module.get("officialTitle", ""),
            "phase": phase_display,
            "phases_raw": phases,
            "status": status_module.get("overallStatus", ""),
            "conditions": conditions_module.get("conditions", []),
            "interventions": intervention_names,
            "enrollment": design_module.get("enrollmentInfo", {}).get("count"),
            "start_date": status_module.get("startDateStruct", {}).get("date", ""),
            "completion_date": status_module.get("completionDateStruct", {}).get("date", ""),
            "lead_sponsor": lead_sponsor.get("name", ""),
            "sponsor_type": lead_sponsor.get("class", ""),
            "has_results": results_module.get("participantFlowModule") is not None,
            "study_type": design_module.get("studyType", ""),
        }

    def _parse_full_study(self, protocol: Dict) -> Dict[str, Any]:
        """Parse full study details from API response."""
        basic = self._parse_study({"protocolSection": protocol})

        # Add additional details
        desc_module = protocol.get("descriptionModule", {})
        eligibility_module = protocol.get("eligibilityModule", {})
        outcomes_module = protocol.get("outcomesModule", {})
        contacts_module = protocol.get("contactsLocationsModule", {})

        # Get primary outcomes
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])
        secondary_outcomes = outcomes_module.get("secondaryOutcomes", [])

        basic.update({
            "brief_summary": desc_module.get("briefSummary", ""),
            "detailed_description": desc_module.get("detailedDescription", ""),
            "eligibility_criteria": eligibility_module.get("eligibilityCriteria", ""),
            "minimum_age": eligibility_module.get("minimumAge", ""),
            "maximum_age": eligibility_module.get("maximumAge", ""),
            "sex": eligibility_module.get("sex", ""),
            "primary_outcomes": [
                {
                    "measure": o.get("measure", ""),
                    "time_frame": o.get("timeFrame", ""),
                    "description": o.get("description", ""),
                }
                for o in primary_outcomes
            ],
            "secondary_outcomes": [
                {
                    "measure": o.get("measure", ""),
                    "time_frame": o.get("timeFrame", ""),
                    "description": o.get("description", ""),
                }
                for o in secondary_outcomes
            ],
            "locations_count": len(contacts_module.get("locations", [])),
        })

        return basic

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()


# Singleton instance
_clinical_trials_service: Optional[ClinicalTrialsService] = None


def get_clinical_trials_service() -> ClinicalTrialsService:
    """Get singleton ClinicalTrials.gov service instance."""
    global _clinical_trials_service
    if _clinical_trials_service is None:
        _clinical_trials_service = ClinicalTrialsService()
    return _clinical_trials_service
