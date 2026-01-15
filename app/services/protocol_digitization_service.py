"""
Protocol Digitization Service for Clinical Intelligence Platform.

Provides access to digitized protocol content extracted from the CIP document:
- USDM 4.0 structured data (study metadata, endpoints, safety, etc.)
- Schedule of Assessments (SOA) with visits, activities, and footnotes
- Eligibility Criteria with OMOP CDM mappings
- Protocol Rules (Document-as-Code YAML)
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.config import settings

logger = logging.getLogger(__name__)


class ProtocolDigitizationService:
    """
    Service for loading and serving digitized protocol data.

    Data sources:
    - USDM 4.0 JSON: Full protocol extraction
    - SOA USDM JSON: Schedule of Assessments
    - Eligibility Criteria JSON: IE criteria with OMOP mappings
    """

    _instance: Optional["ProtocolDigitizationService"] = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize service with data paths."""
        if self._initialized:
            return

        self._protocol_dir = settings.project_root / "data" / "raw" / "protocol"
        self._rules_dir = settings.project_root / "data" / "processed" / "document_as_code"
        self._usdm_path = self._protocol_dir / "CIP_H-34_v.2.0_05Nov2024_fully signed_usdm_4.0.json"
        self._soa_path = self._protocol_dir / "CIP_H-34_v.2.0_05Nov2024_fully signed_soa_usdm_draft.json"
        self._eligibility_path = self._protocol_dir / "CIP_H-34_v.2.0_05Nov2024_fully signed_eligibility_criteria.json"
        self._rules_path = self._rules_dir / "protocol_rules.yaml"

        # Cache for loaded data
        self._usdm_data: Optional[Dict[str, Any]] = None
        self._soa_data: Optional[Dict[str, Any]] = None
        self._eligibility_data: Optional[Dict[str, Any]] = None
        self._rules_data: Optional[Dict[str, Any]] = None

        self._initialized = True
        logger.info("ProtocolDigitizationService initialized")

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file from path."""
        if not path.exists():
            raise FileNotFoundError(f"Protocol data file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file from path."""
        if not path.exists():
            raise FileNotFoundError(f"Protocol rules file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_usdm_data(self) -> Dict[str, Any]:
        """Get full USDM 4.0 extraction data."""
        if self._usdm_data is None:
            self._usdm_data = self._load_json(self._usdm_path)
        return self._usdm_data

    def get_soa_data(self) -> Dict[str, Any]:
        """Get Schedule of Assessments data."""
        if self._soa_data is None:
            self._soa_data = self._load_json(self._soa_path)
        return self._soa_data

    def get_eligibility_data(self) -> Dict[str, Any]:
        """Get Eligibility Criteria data."""
        if self._eligibility_data is None:
            self._eligibility_data = self._load_json(self._eligibility_path)
        return self._eligibility_data

    def get_overview(self) -> Dict[str, Any]:
        """Get high-level overview of all digitized protocol data."""
        usdm = self.get_usdm_data()
        soa = self.get_soa_data()
        eligibility = self.get_eligibility_data()

        # Extract study metadata
        study = usdm.get("study", {})
        extraction_meta = usdm.get("extractionMetadata", {})
        source_doc = usdm.get("sourceDocument", {})

        return {
            "protocol_id": study.get("id"),
            "protocol_name": study.get("name"),
            "official_title": study.get("officialTitle"),
            "version": study.get("version"),
            "study_type": study.get("studyType", {}).get("decode"),
            "study_phase": study.get("studyPhase", {}).get("decode"),
            "source_document": {
                "filename": source_doc.get("filename"),
                "page_count": source_doc.get("pageCount"),
            },
            "extraction_metadata": {
                "timestamp": extraction_meta.get("extractionTimestamp"),
                "pipeline_version": extraction_meta.get("pipelineVersion"),
                "quality_score": extraction_meta.get("averageQualityScore"),
                "agents_used": len(extraction_meta.get("successfulAgents", [])),
            },
            "soa_summary": {
                "total_visits": soa.get("qualityMetrics", {}).get("totalVisits", 0),
                "total_activities": soa.get("qualityMetrics", {}).get("totalActivities", 0),
                "scheduled_instances": soa.get("qualityMetrics", {}).get("totalScheduledInstances", 0),
                "footnotes": soa.get("qualityMetrics", {}).get("footnotesLinked", 0),
            },
            "eligibility_summary": {
                "total_criteria": eligibility.get("summary", {}).get("totalCriteria", 0),
                "inclusion_count": eligibility.get("summary", {}).get("inclusionCount", 0),
                "exclusion_count": eligibility.get("summary", {}).get("exclusionCount", 0),
                "atomic_count": eligibility.get("summary", {}).get("atomicCount", 0),
            },
        }

    def get_usdm_study_metadata(self) -> Dict[str, Any]:
        """Get study metadata from USDM data."""
        usdm = self.get_usdm_data()
        study = usdm.get("study", {})

        return {
            "id": study.get("id"),
            "name": study.get("name"),
            "official_title": study.get("officialTitle"),
            "version": study.get("version"),
            "study_type": study.get("studyType"),
            "study_phase": study.get("studyPhase"),
            "protocol_versions": study.get("studyProtocolVersions", []),
            "study_population": study.get("studyPopulation"),
        }

    def get_usdm_quality_summary(self) -> Dict[str, Any]:
        """Get quality metrics from USDM extraction."""
        usdm = self.get_usdm_data()
        extraction_meta = usdm.get("extractionMetadata", {})

        quality_summary = extraction_meta.get("qualitySummary", {})
        agents = []
        for agent_name, metrics in quality_summary.items():
            agents.append({
                "name": agent_name,
                "score": metrics.get("overallScore"),
                "from_cache": metrics.get("fromCache", False),
            })

        # Sort by score descending
        agents.sort(key=lambda x: x["score"] or 0, reverse=True)

        return {
            "average_score": extraction_meta.get("averageQualityScore"),
            "pipeline_version": extraction_meta.get("pipelineVersion"),
            "primary_model": extraction_meta.get("primaryModel"),
            "successful_agents": extraction_meta.get("successfulAgents", []),
            "failed_agents": extraction_meta.get("failedAgents", []),
            "agent_details": agents,
        }

    def get_soa_visits(self) -> List[Dict[str, Any]]:
        """Get visit schedule from SOA data."""
        soa = self.get_soa_data()
        visits = soa.get("visits", [])

        return [
            {
                "id": v.get("id"),
                "name": v.get("name"),
                "original_name": v.get("originalName"),
                "visit_type": v.get("visitType"),
                "timing": v.get("timing"),
                "window": v.get("window"),
                "type_code": v.get("type", {}).get("decode"),
                "provenance": v.get("provenance"),
            }
            for v in visits
        ]

    def get_soa_activities(self) -> List[Dict[str, Any]]:
        """Get activities from SOA data."""
        soa = self.get_soa_data()
        activities = soa.get("activities", [])

        return [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "category": a.get("category"),
                "cdash_domain": a.get("cdashDomain"),
                "provenance": a.get("provenance"),
            }
            for a in activities
        ]

    def get_soa_matrix(self) -> Dict[str, Any]:
        """Get full SOA matrix (activities x visits)."""
        soa = self.get_soa_data()
        visits = soa.get("visits", [])
        activities = soa.get("activities", [])
        instances = soa.get("scheduledActivityInstances", [])

        # Build matrix
        matrix = {}
        for activity in activities:
            activity_id = activity.get("id")
            matrix[activity_id] = {
                "activity": activity.get("name"),
                "category": activity.get("category"),
                "cdash_domain": activity.get("cdashDomain"),
                "visits": {},
            }

        for instance in instances:
            activity_id = instance.get("activityId")
            visit_id = instance.get("visitId")
            if activity_id in matrix:
                matrix[activity_id]["visits"][visit_id] = {
                    "is_required": instance.get("isRequired"),
                    "footnotes": instance.get("footnoteMarkers", []),
                    "condition": instance.get("condition"),
                }

        return {
            "visits": [{"id": v.get("id"), "name": v.get("name")} for v in visits],
            "activities": list(matrix.values()),
            "quality_metrics": soa.get("qualityMetrics"),
        }

    def get_soa_footnotes(self) -> List[Dict[str, Any]]:
        """Get footnotes from SOA data."""
        soa = self.get_soa_data()
        footnotes = soa.get("footnotes", [])

        return [
            {
                "marker": f.get("marker"),
                "text": f.get("text"),
                "rule_type": f.get("ruleType"),
                "category": f.get("category"),
                "subcategory": f.get("subcategory"),
                "edc_impact": f.get("edcImpact"),
                "structured_rule": f.get("structuredRule"),
                "applies_to": f.get("appliesTo"),
                "provenance": f.get("provenance"),
            }
            for f in footnotes
        ]

    def get_eligibility_criteria(self) -> Dict[str, Any]:
        """Get eligibility criteria with OMOP mappings."""
        eligibility = self.get_eligibility_data()
        criteria = eligibility.get("criteria", [])

        inclusion = []
        exclusion = []

        for c in criteria:
            criterion = {
                "id": c.get("criterionId"),
                "original_id": c.get("originalCriterionId"),
                "original_text": c.get("originalText"),
                "type": c.get("type"),
                "logic_operator": c.get("logicOperator"),
                "decomposition_strategy": c.get("decompositionStrategy"),
                "expression": c.get("expression"),
                "atomic_criteria": c.get("atomicCriteria", []),
                "sql_template": c.get("sqlTemplate"),
                "provenance": c.get("provenance"),
            }

            if c.get("type") == "Inclusion":
                inclusion.append(criterion)
            else:
                exclusion.append(criterion)

        return {
            "protocol_id": eligibility.get("protocolId"),
            "summary": eligibility.get("summary"),
            "inclusion_criteria": inclusion,
            "exclusion_criteria": exclusion,
        }

    def get_usdm_agents(self) -> List[Dict[str, Any]]:
        """Get all USDM agent outputs with their data."""
        usdm = self.get_usdm_data()
        extraction_meta = usdm.get("extractionMetadata", {})
        quality_summary = extraction_meta.get("qualitySummary", {})
        domain_sections = usdm.get("domainSections", {})

        agents = []
        for agent_name in extraction_meta.get("successfulAgents", []):
            agent_info = {
                "name": agent_name,
                "display_name": agent_name.replace("_", " ").title(),
                "score": quality_summary.get(agent_name, {}).get("overallScore"),
                "from_cache": quality_summary.get(agent_name, {}).get("fromCache", False),
                "data": None,
            }

            # Map agent names to their data sections
            agent_data_map = {
                "study_metadata": usdm.get("study"),
                "arms_design": domain_sections.get("studyDesign", {}).get("data"),
                "endpoints_estimands_sap": domain_sections.get("endpoints", {}).get("data"),
                "adverse_events": domain_sections.get("adverseEvents", {}).get("data"),
                "safety_decision_points": domain_sections.get("safetyDecisionPoints", {}).get("data"),
                "concomitant_medications": domain_sections.get("concomitantMedications", {}).get("data"),
                "biospecimen_handling": domain_sections.get("biospecimenHandling", {}).get("data"),
                "laboratory_specifications": domain_sections.get("laboratorySpecifications", {}).get("data"),
                "informed_consent": domain_sections.get("informedConsent", {}).get("data"),
                "pro_specifications": domain_sections.get("proSpecifications", {}).get("data"),
                "data_management": domain_sections.get("dataManagement", {}).get("data"),
                "site_operations_logistics": domain_sections.get("siteOperationsLogistics", {}).get("data"),
                "quality_management": domain_sections.get("qualityManagement", {}).get("data"),
                "withdrawal_procedures": domain_sections.get("withdrawalProcedures", {}).get("data"),
                "imaging_central_reading": domain_sections.get("imagingCentralReading", {}).get("data"),
                "pkpd_sampling": domain_sections.get("pkpdSampling", {}).get("data"),
            }

            agent_info["data"] = agent_data_map.get(agent_name)
            agents.append(agent_info)

        return agents

    def get_domain_sections(self) -> List[Dict[str, Any]]:
        """Get all domain sections with structured data for display."""
        usdm = self.get_usdm_data()
        domain_sections = usdm.get("domainSections", {})

        # Define domain metadata for display
        domain_config = [
            {
                "id": "studyDesign",
                "name": "Study Design",
                "icon": "GitBranch",
                "color": "blue",
                "description": "Arms, epochs, and study cells",
            },
            {
                "id": "endpointsEstimandsSAP",
                "name": "Endpoints & SAP",
                "icon": "Target",
                "color": "green",
                "description": "Objectives, endpoints, estimands, and analysis populations",
            },
            {
                "id": "adverseEvents",
                "name": "Adverse Events",
                "icon": "AlertTriangle",
                "color": "red",
                "description": "AE definitions, SAE criteria, grading systems",
            },
            {
                "id": "safetyDecisionPoints",
                "name": "Safety Decisions",
                "icon": "Shield",
                "color": "orange",
                "description": "Stopping rules, dose modifications",
            },
            {
                "id": "concomitantMedications",
                "name": "Concomitant Meds",
                "icon": "Pill",
                "color": "purple",
                "description": "Prohibited, restricted, and required medications",
            },
            {
                "id": "biospecimenHandling",
                "name": "Biospecimens",
                "icon": "TestTube",
                "color": "cyan",
                "description": "Collection, processing, and storage requirements",
            },
            {
                "id": "laboratorySpecifications",
                "name": "Laboratory",
                "icon": "FlaskConical",
                "color": "emerald",
                "description": "Lab panels, tests, and schedules",
            },
            {
                "id": "informedConsent",
                "name": "Informed Consent",
                "icon": "FileSignature",
                "color": "indigo",
                "description": "Study overview, procedures, risks, and benefits",
            },
            {
                "id": "proSpecifications",
                "name": "PRO/eCOA",
                "icon": "ClipboardList",
                "color": "pink",
                "description": "Patient-reported outcome instruments",
            },
            {
                "id": "dataManagement",
                "name": "Data Management",
                "icon": "Database",
                "color": "slate",
                "description": "EDC specifications, data standards, quality",
            },
            {
                "id": "siteOperationsLogistics",
                "name": "Site Operations",
                "icon": "Building",
                "color": "amber",
                "description": "Site selection, monitoring, training",
            },
            {
                "id": "qualityManagement",
                "name": "Quality Management",
                "icon": "CheckCircle",
                "color": "teal",
                "description": "RBQM, monitoring approach",
            },
            {
                "id": "withdrawalProcedures",
                "name": "Withdrawal",
                "icon": "LogOut",
                "color": "rose",
                "description": "Discontinuation procedures, follow-up",
            },
            {
                "id": "imagingCentralReading",
                "name": "Imaging",
                "icon": "Scan",
                "color": "sky",
                "description": "Imaging modalities, assessment schedules",
            },
            {
                "id": "pkpdSampling",
                "name": "PK/PD Sampling",
                "icon": "Activity",
                "color": "violet",
                "description": "Pharmacokinetic sampling and parameters",
            },
        ]

        domains = []
        for config in domain_config:
            domain_id = config["id"]
            domain_data = domain_sections.get(domain_id, {})

            # Get the actual data (may be nested under 'data' key)
            if isinstance(domain_data, dict):
                data = domain_data.get("data", domain_data)
            else:
                data = domain_data

            domains.append({
                **config,
                "data": data,
            })

        return domains


    def get_protocol_rules(self) -> Dict[str, Any]:
        """Get protocol rules from Document-as-Code YAML."""
        if self._rules_data is None:
            self._rules_data = self._load_yaml(self._rules_path)
        return self._rules_data

    def update_protocol_rule(self, field_path: str, new_value: Any) -> Dict[str, Any]:
        """
        Update a specific field in protocol rules.

        Args:
            field_path: Dot-separated path to the field (e.g., 'protocol.version', 'sample_size.target_enrollment')
            new_value: The new value to set

        Returns:
            Updated protocol rules
        """
        # Load current rules (fresh from file to avoid cache issues)
        rules = self._load_yaml(self._rules_path)

        # Navigate to the parent and update the field
        keys = field_path.split('.')
        target = rules
        for key in keys[:-1]:
            if key.isdigit():
                target = target[int(key)]
            else:
                target = target[key]

        final_key = keys[-1]
        if final_key.isdigit():
            target[int(final_key)] = new_value
        else:
            target[final_key] = new_value

        # Write back to YAML file
        with open(self._rules_path, 'w', encoding='utf-8') as f:
            yaml.dump(rules, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Update cache
        self._rules_data = rules

        logger.info(f"Updated protocol rule: {field_path} = {new_value}")
        return rules

    def update_protocol_rules_batch(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update multiple fields in protocol rules at once.

        Args:
            updates: List of dicts with 'field_path' and 'value' keys

        Returns:
            Updated protocol rules
        """
        # Load current rules
        rules = self._load_yaml(self._rules_path)

        for update in updates:
            field_path = update['field_path']
            new_value = update['value']

            keys = field_path.split('.')
            target = rules
            for key in keys[:-1]:
                if key.isdigit():
                    target = target[int(key)]
                else:
                    target = target[key]

            final_key = keys[-1]
            if final_key.isdigit():
                target[int(final_key)] = new_value
            else:
                target[final_key] = new_value

        # Write back to YAML file
        with open(self._rules_path, 'w', encoding='utf-8') as f:
            yaml.dump(rules, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Update cache
        self._rules_data = rules

        logger.info(f"Batch updated {len(updates)} protocol rules")
        return rules


def get_protocol_digitization_service() -> ProtocolDigitizationService:
    """Get singleton instance of ProtocolDigitizationService."""
    return ProtocolDigitizationService()
