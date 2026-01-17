"""
Data Ingestion Service for Deep Research Pipeline.

Handles processing of approved data sources:
- Structured data (Excel/CSV) -> Database tables
- Unstructured data (PDF) -> Vector embeddings
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.services.vector_service import get_vector_service
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Service for ingesting and processing approved data sources.

    Features:
    - Excel/CSV parsing and validation
    - PDF text extraction and chunking
    - Vector embedding generation
    - Data quality validation
    """

    def __init__(self):
        """Initialize data ingestion service."""
        self._vector_service = get_vector_service()
        self._llm_service = get_llm_service()

    async def ingest_approved_sources(
        self,
        session_id: str,
        product_id: str,
        recommendations: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ingest all approved data sources from recommendations.

        Args:
            session_id: Onboarding session ID
            product_id: Product identifier
            recommendations: Approved recommendations with source details

        Returns:
            Ingestion results with statistics
        """
        results = {
            "session_id": session_id,
            "product_id": product_id,
            "started_at": datetime.utcnow().isoformat(),
            "sources_processed": [],
            "total_documents": 0,
            "total_chunks": 0,
            "errors": [],
        }

        recs = recommendations.get("recommendations", recommendations)

        # Process clinical study data
        clinical_data = recs.get("clinical_study") or recs.get("clinical")
        if clinical_data:
            try:
                clinical_result = await self._process_clinical_data(
                    product_id, clinical_data
                )
                results["sources_processed"].append({
                    "type": "clinical",
                    "status": "completed",
                    "result": clinical_result,
                })
                results["total_documents"] += clinical_result.get("documents", 0)
            except Exception as e:
                logger.error(f"Clinical data ingestion failed: {e}")
                results["errors"].append({
                    "source": "clinical",
                    "error": str(e),
                })

        # Process literature/publications
        literature = recs.get("literature", {})
        if literature:
            try:
                lit_result = await self._process_literature(
                    product_id, literature
                )
                results["sources_processed"].append({
                    "type": "literature",
                    "status": "completed",
                    "result": lit_result,
                })
                results["total_chunks"] += lit_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"Literature ingestion failed: {e}")
                results["errors"].append({
                    "source": "literature",
                    "error": str(e),
                })

        # Process registry data
        registries = recs.get("registries", [])
        if registries:
            try:
                reg_result = await self._process_registries(
                    product_id, registries
                )
                results["sources_processed"].append({
                    "type": "registry",
                    "status": "completed",
                    "result": reg_result,
                })
                results["total_chunks"] += reg_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"Registry ingestion failed: {e}")
                results["errors"].append({
                    "source": "registry",
                    "error": str(e),
                })

        # Process FDA surveillance data
        fda_data = recs.get("fda_surveillance") or recs.get("fda")
        if fda_data:
            try:
                fda_result = await self._process_fda_data(
                    product_id, fda_data
                )
                results["sources_processed"].append({
                    "type": "fda",
                    "status": "completed",
                    "result": fda_result,
                })
                results["total_chunks"] += fda_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"FDA data ingestion failed: {e}")
                results["errors"].append({
                    "source": "fda",
                    "error": str(e),
                })

        # Process competitive intelligence
        competitive = recs.get("competitive", [])
        if competitive:
            try:
                comp_result = await self._process_competitive(
                    product_id, competitive
                )
                results["sources_processed"].append({
                    "type": "competitive",
                    "status": "completed",
                    "result": comp_result,
                })
                results["total_chunks"] += comp_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"Competitive intel ingestion failed: {e}")
                results["errors"].append({
                    "source": "competitive",
                    "error": str(e),
                })

        # Process clinical trials data from ClinicalTrials.gov
        clinical_trials = recs.get("clinical_trials", {})
        if clinical_trials:
            try:
                ct_result = await self._process_clinical_trials(
                    product_id, clinical_trials
                )
                results["sources_processed"].append({
                    "type": "clinical_trials",
                    "status": "completed",
                    "result": ct_result,
                })
                results["total_chunks"] += ct_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"Clinical trials ingestion failed: {e}")
                results["errors"].append({
                    "source": "clinical_trials",
                    "error": str(e),
                })

        # Process earlier phase FDA data
        earlier_phase_fda = recs.get("earlier_phase_fda", {})
        if earlier_phase_fda:
            try:
                epf_result = await self._process_earlier_phase_fda(
                    product_id, earlier_phase_fda
                )
                results["sources_processed"].append({
                    "type": "earlier_phase_fda",
                    "status": "completed",
                    "result": epf_result,
                })
                results["total_chunks"] += epf_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"Earlier phase FDA ingestion failed: {e}")
                results["errors"].append({
                    "source": "earlier_phase_fda",
                    "error": str(e),
                })

        # Process competitor trials from ClinicalTrials.gov
        competitor_trials = recs.get("competitor_trials", {})
        if competitor_trials:
            try:
                ct_comp_result = await self._process_competitor_trials(
                    product_id, competitor_trials
                )
                results["sources_processed"].append({
                    "type": "competitor_trials",
                    "status": "completed",
                    "result": ct_comp_result,
                })
                results["total_chunks"] += ct_comp_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"Competitor trials ingestion failed: {e}")
                results["errors"].append({
                    "source": "competitor_trials",
                    "error": str(e),
                })

        # Process competitor FDA data
        competitor_fda = recs.get("competitor_fda", {})
        if competitor_fda:
            try:
                comp_fda_result = await self._process_competitor_fda(
                    product_id, competitor_fda
                )
                results["sources_processed"].append({
                    "type": "competitor_fda",
                    "status": "completed",
                    "result": comp_fda_result,
                })
                results["total_chunks"] += comp_fda_result.get("chunks", 0)
            except Exception as e:
                logger.error(f"Competitor FDA ingestion failed: {e}")
                results["errors"].append({
                    "source": "competitor_fda",
                    "error": str(e),
                })

        results["completed_at"] = datetime.utcnow().isoformat()
        results["success"] = len(results["errors"]) == 0

        logger.info(
            f"Data ingestion completed for {product_id}: "
            f"{len(results['sources_processed'])} sources, "
            f"{results['total_documents']} documents, "
            f"{results['total_chunks']} chunks"
        )

        return results

    async def _process_clinical_data(
        self,
        product_id: str,
        clinical_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process clinical study data (structured).

        For now, creates vector embeddings from clinical data descriptions.
        In production, would populate relational database tables.
        """
        documents_created = 0
        chunks_created = 0

        # Extract clinical data summary for embedding
        description = clinical_data.get("description", "")
        source_info = clinical_data.get("source", "clinical_study")

        if description:
            # Create a document from clinical data description
            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=description,
                source_id=f"clinical_{source_info}",
                source_type="clinical",
                additional_metadata={
                    "data_type": "clinical_study",
                    "source": source_info,
                },
            )
            chunks_created = result.get("chunks", 0)
            documents_created = 1

        return {
            "documents": documents_created,
            "chunks": chunks_created,
            "source": source_info,
        }

    async def _process_literature(
        self,
        product_id: str,
        literature: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process literature/publications into vector embeddings."""
        chunks_created = 0

        # Get publications list
        publications = literature.get("publications", [])
        if not publications and isinstance(literature, dict):
            # Handle direct literature data
            publications = [literature]

        for i, pub in enumerate(publications[:20]):  # Limit to 20 publications
            title = pub.get("title", f"Publication {i+1}")
            abstract = pub.get("abstract", pub.get("summary", ""))

            if abstract:
                content = f"Title: {title}\n\nAbstract: {abstract}"

                result = await self._vector_service.process_and_store_document(
                    product_id=product_id,
                    document_text=content,
                    source_id=f"pub_{i}_{title[:30].replace(' ', '_')}",
                    source_type="literature",
                    additional_metadata={
                        "title": title,
                        "journal": pub.get("journal", pub.get("journal_abbrev", "")),
                        "year": pub.get("year", ""),
                        "pmid": pub.get("pmid", ""),
                    },
                )
                chunks_created += result.get("chunks", 0)

        return {
            "publications_processed": len(publications),
            "chunks": chunks_created,
        }

    async def _process_registries(
        self,
        product_id: str,
        registries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process registry benchmark data."""
        chunks_created = 0

        for reg in registries:
            name = reg.get("name", "Unknown Registry")
            description = reg.get("description", "")
            why_recommended = reg.get("why_recommended", "")

            # Build registry content
            content_parts = [f"Registry: {name}"]
            if description:
                content_parts.append(f"Description: {description}")
            if why_recommended:
                content_parts.append(f"Relevance: {why_recommended}")

            # Add any benchmark data if available
            benchmarks = reg.get("benchmarks", {})
            if benchmarks:
                content_parts.append(f"Benchmark Data: {str(benchmarks)}")

            content = "\n\n".join(content_parts)

            if content:
                result = await self._vector_service.process_and_store_document(
                    product_id=product_id,
                    document_text=content,
                    source_id=f"registry_{name.replace(' ', '_').lower()}",
                    source_type="registry",
                    additional_metadata={
                        "registry_name": name,
                        "region": reg.get("region", ""),
                    },
                )
                chunks_created += result.get("chunks", 0)

        return {
            "registries_processed": len(registries),
            "chunks": chunks_created,
        }

    async def _process_fda_data(
        self,
        product_id: str,
        fda_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process FDA surveillance data."""
        chunks_created = 0

        # Process MAUDE events if available
        maude_events = fda_data.get("maude_events", [])
        if maude_events:
            # Summarize MAUDE events
            event_summary = f"FDA MAUDE Database: {len(maude_events)} adverse events reported"

            # Add event type breakdown if available
            event_types = {}
            for event in maude_events[:100]:
                event_type = event.get("event_type", "Unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1

            if event_types:
                event_summary += "\n\nEvent Type Distribution:\n"
                for etype, count in sorted(event_types.items(), key=lambda x: -x[1]):
                    event_summary += f"- {etype}: {count} events\n"

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=event_summary,
                source_id="fda_maude_summary",
                source_type="fda_surveillance",
                additional_metadata={
                    "data_source": "FDA MAUDE",
                    "event_count": len(maude_events),
                },
            )
            chunks_created += result.get("chunks", 0)

        # Process 510(k) clearances if available
        clearances = fda_data.get("clearances", {}).get("recent_clearances", [])
        if clearances:
            clearance_text = "FDA 510(k) Clearances for Similar Devices:\n\n"
            for c in clearances[:10]:
                clearance_text += (
                    f"- {c.get('k_number', 'Unknown')}: {c.get('device_name', 'Unknown')}\n"
                    f"  Applicant: {c.get('applicant', 'Unknown')}\n"
                    f"  Decision Date: {c.get('decision_date', 'Unknown')}\n\n"
                )

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=clearance_text,
                source_id="fda_510k_clearances",
                source_type="fda_regulatory",
                additional_metadata={
                    "data_source": "FDA 510(k) Database",
                    "clearance_count": len(clearances),
                },
            )
            chunks_created += result.get("chunks", 0)

        return {
            "maude_events": len(maude_events),
            "clearances": len(clearances),
            "chunks": chunks_created,
        }

    async def _process_competitive(
        self,
        product_id: str,
        competitive: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process competitive intelligence data."""
        chunks_created = 0

        for comp in competitive:
            company = comp.get("manufacturer", comp.get("company", "Unknown"))
            product = comp.get("product", comp.get("product_name", ""))

            content_parts = [f"Competitor: {company}"]
            if product:
                content_parts.append(f"Product: {product}")

            # Add any available competitive data
            for field in ["features", "clinical_evidence", "market_position", "description"]:
                value = comp.get(field)
                if value:
                    if isinstance(value, list):
                        content_parts.append(f"{field.title()}: {', '.join(value)}")
                    else:
                        content_parts.append(f"{field.title()}: {value}")

            content = "\n\n".join(content_parts)

            if content:
                result = await self._vector_service.process_and_store_document(
                    product_id=product_id,
                    document_text=content,
                    source_id=f"competitor_{company.replace(' ', '_').lower()}",
                    source_type="competitive_intel",
                    additional_metadata={
                        "company": company,
                        "product": product,
                    },
                )
                chunks_created += result.get("chunks", 0)

        return {
            "competitors_processed": len(competitive),
            "chunks": chunks_created,
        }

    async def _process_clinical_trials(
        self,
        product_id: str,
        clinical_trials: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process clinical trials data from ClinicalTrials.gov.

        Creates vector embeddings from trial information for RAG retrieval.
        """
        chunks_created = 0

        # Process trials by protocol
        by_protocol = clinical_trials.get("by_protocol", [])
        for trial in by_protocol[:20]:
            nct_id = trial.get("nct_id", "Unknown")
            title = trial.get("title", trial.get("brief_title", ""))
            status = trial.get("status", trial.get("overall_status", ""))
            phase = trial.get("phase", "")
            sponsor = trial.get("sponsor", trial.get("lead_sponsor", ""))

            content_parts = [
                f"ClinicalTrials.gov Registry Entry: {nct_id}",
                f"Title: {title}",
                f"Status: {status}",
                f"Phase: {phase}",
                f"Sponsor: {sponsor}",
            ]

            # Add dates if available
            start_date = trial.get("start_date", "")
            if start_date:
                content_parts.append(f"Start Date: {start_date}")
            completion_date = trial.get("completion_date", trial.get("primary_completion_date", ""))
            if completion_date:
                content_parts.append(f"Completion Date: {completion_date}")

            # Add conditions and interventions
            conditions = trial.get("conditions", [])
            if conditions:
                content_parts.append(f"Conditions: {', '.join(conditions[:5])}")
            interventions = trial.get("interventions", [])
            if interventions:
                int_names = [i.get("name", str(i)) if isinstance(i, dict) else str(i) for i in interventions[:5]]
                content_parts.append(f"Interventions: {', '.join(int_names)}")

            content = "\n".join(content_parts)

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=content,
                source_id=f"clinical_trial_{nct_id}",
                source_type="clinical_trials",
                additional_metadata={
                    "nct_id": nct_id,
                    "source": "ClinicalTrials.gov",
                    "trial_status": status,
                    "phase": phase,
                },
            )
            chunks_created += result.get("chunks", 0)

        # Process trials by title search
        by_title = clinical_trials.get("by_title", [])
        for trial in by_title[:10]:  # Limit to avoid duplicates
            nct_id = trial.get("nct_id", "Unknown")
            if any(t.get("nct_id") == nct_id for t in by_protocol):
                continue  # Skip duplicates

            title = trial.get("title", trial.get("brief_title", ""))
            content = f"Related Trial: {nct_id}\nTitle: {title}\nStatus: {trial.get('status', 'Unknown')}"

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=content,
                source_id=f"related_trial_{nct_id}",
                source_type="clinical_trials",
                additional_metadata={
                    "nct_id": nct_id,
                    "source": "ClinicalTrials.gov",
                    "match_type": "title_search",
                },
            )
            chunks_created += result.get("chunks", 0)

        return {
            "trials_processed": len(by_protocol) + len(by_title),
            "chunks": chunks_created,
        }

    async def _process_earlier_phase_fda(
        self,
        product_id: str,
        earlier_phase_fda: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process FDA data from earlier study phases.

        Creates vector embeddings from historical FDA records.
        """
        chunks_created = 0

        # Process 510(k) clearances from earlier phases
        clearances = earlier_phase_fda.get("clearances", [])
        if clearances:
            clearance_text = "FDA 510(k) Clearances from Earlier Phases:\n\n"
            phases_searched = earlier_phase_fda.get("phases_searched", [])
            if phases_searched:
                clearance_text += f"Phases included: {', '.join(phases_searched)}\n\n"

            for c in clearances[:15]:
                clearance_text += (
                    f"- {c.get('k_number', 'Unknown')}: {c.get('device_name', 'Unknown')}\n"
                    f"  Applicant: {c.get('applicant', 'Unknown')}\n"
                    f"  Decision Date: {c.get('decision_date', 'Unknown')}\n"
                    f"  Product Code: {c.get('product_code', 'Unknown')}\n\n"
                )

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=clearance_text,
                source_id="earlier_phase_510k_clearances",
                source_type="earlier_phase_fda",
                additional_metadata={
                    "data_source": "FDA 510(k) Database",
                    "clearance_count": len(clearances),
                    "phases": phases_searched,
                },
            )
            chunks_created += result.get("chunks", 0)

        # Process adverse events from earlier phases
        adverse_events = earlier_phase_fda.get("adverse_events", [])
        if adverse_events:
            ae_summary = "FDA MAUDE Adverse Events from Earlier Phases:\n\n"
            ae_summary += f"Total events: {len(adverse_events)}\n\n"

            # Group by event type
            event_types = {}
            for event in adverse_events[:100]:
                event_type = event.get("event_type", "Unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1

            if event_types:
                ae_summary += "Event Type Distribution:\n"
                for etype, count in sorted(event_types.items(), key=lambda x: -x[1]):
                    ae_summary += f"- {etype}: {count} events\n"

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=ae_summary,
                source_id="earlier_phase_adverse_events",
                source_type="earlier_phase_fda",
                additional_metadata={
                    "data_source": "FDA MAUDE Database",
                    "event_count": len(adverse_events),
                },
            )
            chunks_created += result.get("chunks", 0)

        return {
            "clearances": len(clearances),
            "adverse_events": len(adverse_events),
            "chunks": chunks_created,
        }

    async def _process_competitor_trials(
        self,
        product_id: str,
        competitor_trials: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process competitor clinical trials from ClinicalTrials.gov.

        Creates vector embeddings for competitive intelligence.
        """
        chunks_created = 0

        # Process by sponsor
        by_sponsor = competitor_trials.get("by_sponsor", {})
        for sponsor, sponsor_trials in by_sponsor.items():
            if not sponsor_trials:
                continue

            sponsor_content = f"Competitor Trials: {sponsor}\n\n"
            trial_count = len(sponsor_trials) if isinstance(sponsor_trials, list) else sponsor_trials

            if isinstance(sponsor_trials, list):
                sponsor_content += f"Total trials: {trial_count}\n\n"
                for trial in sponsor_trials[:5]:
                    nct_id = trial.get("nct_id", "Unknown")
                    title = trial.get("title", trial.get("brief_title", ""))
                    status = trial.get("status", trial.get("overall_status", ""))
                    phase = trial.get("phase", "")

                    sponsor_content += f"- {nct_id}: {title[:100]}...\n"
                    sponsor_content += f"  Status: {status}, Phase: {phase}\n\n"
            else:
                sponsor_content += f"Total trials: {trial_count}\n"

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=sponsor_content,
                source_id=f"competitor_trials_{sponsor.replace(' ', '_').lower()[:30]}",
                source_type="competitor_trials",
                additional_metadata={
                    "competitor": sponsor,
                    "trial_count": trial_count if isinstance(trial_count, int) else len(sponsor_trials),
                    "source": "ClinicalTrials.gov",
                },
            )
            chunks_created += result.get("chunks", 0)

        # Process individual trials list
        trials = competitor_trials.get("trials", competitor_trials.get("top_trials", []))
        for trial in trials[:10]:
            nct_id = trial.get("nct_id", "Unknown")
            title = trial.get("title", trial.get("brief_title", ""))
            sponsor = trial.get("sponsor", trial.get("lead_sponsor", "Unknown"))

            content = f"Competitor Trial: {nct_id}\n"
            content += f"Sponsor: {sponsor}\n"
            content += f"Title: {title}\n"
            content += f"Status: {trial.get('status', 'Unknown')}\n"
            content += f"Phase: {trial.get('phase', 'Unknown')}\n"

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=content,
                source_id=f"competitor_trial_{nct_id}",
                source_type="competitor_trials",
                additional_metadata={
                    "nct_id": nct_id,
                    "competitor": sponsor,
                    "source": "ClinicalTrials.gov",
                },
            )
            chunks_created += result.get("chunks", 0)

        return {
            "sponsors_processed": len(by_sponsor),
            "trials_processed": len(trials),
            "chunks": chunks_created,
        }

    async def _process_competitor_fda(
        self,
        product_id: str,
        competitor_fda: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process competitor FDA data (510(k) clearances and adverse events).

        Creates vector embeddings for competitive regulatory intelligence.
        """
        chunks_created = 0

        # Process top competitors summary
        top_competitors = competitor_fda.get("top_competitors", [])
        if top_competitors:
            comp_summary = "Competitor FDA Regulatory Landscape:\n\n"
            for comp in top_competitors[:10]:
                company = comp.get("company", "Unknown")
                clearances = comp.get("clearance_count", 0)
                comp_summary += f"- {company}: {clearances} 510(k) clearances\n"

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=comp_summary,
                source_id="competitor_fda_overview",
                source_type="competitor_fda",
                additional_metadata={
                    "data_source": "openFDA",
                    "competitor_count": len(top_competitors),
                },
            )
            chunks_created += result.get("chunks", 0)

        # Process competitor clearances
        clearances = competitor_fda.get("clearances", [])
        if clearances:
            clearance_text = "Competitor 510(k) Clearances:\n\n"
            for c in clearances[:20]:
                clearance_text += (
                    f"- {c.get('k_number', 'Unknown')}: {c.get('device_name', 'Unknown')}\n"
                    f"  Applicant: {c.get('applicant', 'Unknown')}\n"
                    f"  Decision Date: {c.get('decision_date', 'Unknown')}\n\n"
                )

            result = await self._vector_service.process_and_store_document(
                product_id=product_id,
                document_text=clearance_text,
                source_id="competitor_510k_clearances",
                source_type="competitor_fda",
                additional_metadata={
                    "data_source": "FDA 510(k) Database",
                    "clearance_count": len(clearances),
                },
            )
            chunks_created += result.get("chunks", 0)

        # Process competitor adverse events by company
        ae_by_company = competitor_fda.get("adverse_events_by_company", {})
        if ae_by_company:
            for company, events in ae_by_company.items():
                event_count = len(events) if isinstance(events, list) else events
                ae_content = f"Competitor Adverse Events: {company}\n\n"
                ae_content += f"Total MAUDE reports: {event_count}\n\n"

                if isinstance(events, list):
                    # Group by event type
                    event_types = {}
                    for event in events[:100]:
                        event_type = event.get("event_type", "Unknown")
                        event_types[event_type] = event_types.get(event_type, 0) + 1

                    if event_types:
                        ae_content += "Event Type Distribution:\n"
                        for etype, count in sorted(event_types.items(), key=lambda x: -x[1])[:10]:
                            ae_content += f"- {etype}: {count} events\n"

                result = await self._vector_service.process_and_store_document(
                    product_id=product_id,
                    document_text=ae_content,
                    source_id=f"competitor_ae_{company.replace(' ', '_').lower()[:30]}",
                    source_type="competitor_fda",
                    additional_metadata={
                        "competitor": company,
                        "event_count": event_count if isinstance(event_count, int) else len(events),
                        "data_source": "FDA MAUDE Database",
                    },
                )
                chunks_created += result.get("chunks", 0)

        return {
            "competitors": len(top_competitors),
            "clearances": len(clearances),
            "ae_companies": len(ae_by_company),
            "chunks": chunks_created,
        }

    async def process_document_file(
        self,
        product_id: str,
        file_path: str,
        source_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a document file (PDF, DOCX) into vector embeddings.

        Args:
            product_id: Product identifier
            file_path: Path to the document file
            source_type: Type of source (protocol, ifu, etc.)
            metadata: Additional metadata

        Returns:
            Processing result
        """
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        # Extract text based on file type
        text = ""
        if path.suffix.lower() == ".pdf":
            text = await self._extract_pdf_text(file_path)
        elif path.suffix.lower() in [".txt", ".md"]:
            text = path.read_text(encoding="utf-8")
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {path.suffix}",
            }

        if not text:
            return {
                "success": False,
                "error": "No text extracted from file",
            }

        # Process and store
        result = await self._vector_service.process_and_store_document(
            product_id=product_id,
            document_text=text,
            source_id=f"{source_type}_{path.stem}",
            source_type=source_type,
            additional_metadata=metadata or {},
        )

        return {
            "success": True,
            "file": str(path),
            "source_type": source_type,
            "chunks": result.get("chunks", 0),
        }

    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            text_parts = []

            for page in doc:
                text_parts.append(page.get_text())

            doc.close()
            return "\n\n".join(text_parts)

        except ImportError:
            logger.warning("PyMuPDF not available, trying pdfplumber")
            try:
                import pdfplumber

                text_parts = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)

                return "\n\n".join(text_parts)

            except Exception as e:
                logger.error(f"PDF extraction failed: {e}")
                return ""

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""

    async def process_excel_file(
        self,
        product_id: str,
        file_path: str,
        source_type: str = "clinical_data",
    ) -> Dict[str, Any]:
        """
        Process Excel file and create embeddings from data summary.

        Args:
            product_id: Product identifier
            file_path: Path to Excel file
            source_type: Type of source

        Returns:
            Processing result with statistics
        """
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        try:
            # Read Excel file
            if path.suffix.lower() == ".xlsx":
                excel_data = pd.read_excel(file_path, sheet_name=None)
            elif path.suffix.lower() == ".csv":
                excel_data = {"data": pd.read_csv(file_path)}
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {path.suffix}",
                }

            # Process each sheet
            total_rows = 0
            chunks_created = 0

            for sheet_name, df in excel_data.items():
                total_rows += len(df)

                # Create a summary of the data
                summary = f"Sheet: {sheet_name}\n"
                summary += f"Rows: {len(df)}\n"
                summary += f"Columns: {', '.join(df.columns.tolist())}\n\n"

                # Add data statistics for numeric columns
                numeric_cols = df.select_dtypes(include=["number"]).columns
                if len(numeric_cols) > 0:
                    summary += "Numeric Summary:\n"
                    for col in numeric_cols[:10]:
                        summary += f"- {col}: mean={df[col].mean():.2f}, std={df[col].std():.2f}\n"

                result = await self._vector_service.process_and_store_document(
                    product_id=product_id,
                    document_text=summary,
                    source_id=f"{source_type}_{sheet_name}",
                    source_type=source_type,
                    additional_metadata={
                        "file": str(path),
                        "sheet": sheet_name,
                        "rows": len(df),
                        "columns": len(df.columns),
                    },
                )
                chunks_created += result.get("chunks", 0)

            return {
                "success": True,
                "file": str(path),
                "sheets": len(excel_data),
                "total_rows": total_rows,
                "chunks": chunks_created,
            }

        except Exception as e:
            logger.error(f"Excel processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# Singleton instance
_data_ingestion_service: Optional[DataIngestionService] = None


def get_data_ingestion_service() -> DataIngestionService:
    """Get singleton data ingestion service instance."""
    global _data_ingestion_service
    if _data_ingestion_service is None:
        _data_ingestion_service = DataIngestionService()
    return _data_ingestion_service
