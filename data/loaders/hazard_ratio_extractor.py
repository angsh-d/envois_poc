"""
Dynamic hazard ratio extraction from literature PDFs.

Uses RAG + LLM to extract hazard ratios from indexed literature
and stores them with full source attribution.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from data.vectorstore.chroma_store import get_vector_store, ChromaVectorStore
from app.services.llm_service import get_llm_service, LLMService
from app.services.prompt_service import get_prompt_service, PromptService

logger = logging.getLogger(__name__)


class HazardRatioExtractor:
    """
    Extracts hazard ratios from literature using RAG + LLM.

    Searches indexed literature for risk factor content,
    uses LLM to extract hazard ratios, and stores with attribution.
    """

    # Risk factors to search for
    RISK_FACTORS = [
        "age elderly over 70 80 years",
        "BMI body mass index obesity overweight",
        "osteoporosis bone density",
        "diabetes mellitus diabetic",
        "smoking smoker tobacco",
        "prior revision previous surgery",
        "bone quality bone loss defect",
        "renal kidney disease",
        "rheumatoid arthritis inflammatory",
        "gender sex male female",
        "comorbidity medical history",
    ]

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
    ):
        """Initialize extractor."""
        self._vector_store = vector_store or get_vector_store()
        self._llm = llm_service or get_llm_service()
        self._prompts = prompt_service or get_prompt_service()
        self._extracted_hrs: List[Dict[str, Any]] = []

    async def extract_from_literature(self, n_results_per_factor: int = 5) -> List[Dict[str, Any]]:
        """
        Extract hazard ratios from all indexed literature.

        Args:
            n_results_per_factor: Number of search results per risk factor

        Returns:
            List of extracted hazard ratios with source attribution
        """
        logger.info("Starting hazard ratio extraction from literature...")
        all_extracted = []
        seen_chunks = set()

        for factor_query in self.RISK_FACTORS:
            logger.info(f"Searching for: {factor_query}")

            # Search literature for this factor
            results = self._vector_store.search(
                query=f"hazard ratio risk factor {factor_query} revision",
                source_type="literature",
                n_results=n_results_per_factor,
                include_distances=True
            )

            if not results:
                continue

            # Build context from unique chunks
            chunks_for_extraction = []
            for r in results:
                chunk_id = f"{r['metadata'].get('source_file', '')}_{r['metadata'].get('page_number', '')}"
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    chunks_for_extraction.append({
                        "content": r["content"],
                        "source_file": r["metadata"].get("source_file", "unknown"),
                        "page_number": r["metadata"].get("page_number", "N/A"),
                    })

            if not chunks_for_extraction:
                continue

            # Build context string
            context = "\n\n---\n\n".join([
                f"Source: {c['source_file']} (Page {c['page_number']})\n{c['content']}"
                for c in chunks_for_extraction
            ])

            # Extract hazard ratios using LLM
            try:
                extracted = await self._extract_hrs_from_context(context)
                if extracted:
                    all_extracted.extend(extracted)
            except Exception as e:
                logger.warning(f"Extraction failed for {factor_query}: {e}")

        self._extracted_hrs = all_extracted
        logger.info(f"Extracted {len(all_extracted)} hazard ratios from literature")
        return all_extracted

    async def _extract_hrs_from_context(self, context: str) -> List[Dict[str, Any]]:
        """Extract hazard ratios from context using LLM."""
        prompt = self._prompts.load("hazard_ratio_extraction", {"context": context})

        response = await self._llm.generate(
            prompt=prompt,
            model="gemini-3-pro-preview",
            temperature=0.0,
            max_tokens=4096,
        )

        # Parse JSON response
        try:
            # Find JSON in response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                return parsed.get("extracted_hazard_ratios", [])
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return []

        return []

    def get_extracted_hrs(self) -> List[Dict[str, Any]]:
        """Get all extracted hazard ratios."""
        return self._extracted_hrs

    def merge_with_manual_hrs(
        self,
        manual_hrs: Dict[str, float],
        prefer_extracted: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Merge extracted HRs with manually curated values.

        Args:
            manual_hrs: Dictionary of manually curated hazard ratios
            prefer_extracted: If True, prefer extracted values over manual

        Returns:
            Merged dictionary with source attribution
        """
        merged = {}

        # Add manual values first
        for factor, hr in manual_hrs.items():
            merged[factor] = {
                "hazard_ratio": hr,
                "source": "manual_curation",
                "confidence": 0.9,  # High confidence for manual values
            }

        # Add/override with extracted values
        for extracted in self._extracted_hrs:
            factor = extracted.get("risk_factor", "").lower().replace(" ", "_")
            hr = extracted.get("hazard_ratio")

            if not factor or hr is None:
                continue

            # Normalize factor name
            factor_mapping = {
                "age": "age_over_80",
                "elderly": "age_over_80",
                "bmi": "bmi_over_35",
                "obesity": "bmi_over_35",
                "osteoporosis": "osteoporosis",
                "diabetes": "diabetes",
                "smoking": "smoking",
                "prior_revision": "prior_revision",
                "bone_loss": "severe_bone_loss",
            }

            for key, mapped in factor_mapping.items():
                if key in factor:
                    factor = mapped
                    break

            if prefer_extracted or factor not in merged:
                merged[factor] = {
                    "hazard_ratio": hr,
                    "confidence_interval": extracted.get("confidence_interval"),
                    "source": f"{extracted.get('source_file', 'unknown')} p.{extracted.get('page_number', 'N/A')}",
                    "original_text": extracted.get("original_text"),
                    "confidence": 0.7,  # Lower confidence for extracted
                }

        return merged

    def save_to_yaml(self, output_path: Path) -> Path:
        """
        Save extracted hazard ratios to YAML file.

        Args:
            output_path: Path to save YAML file

        Returns:
            Path to saved file
        """
        output = {
            "extracted_at": datetime.utcnow().isoformat(),
            "n_extracted": len(self._extracted_hrs),
            "hazard_ratios": self._extracted_hrs,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved extracted hazard ratios to {output_path}")
        return output_path


async def extract_hazard_ratios_from_literature() -> List[Dict[str, Any]]:
    """
    Convenience function to extract hazard ratios from literature.

    Returns:
        List of extracted hazard ratios
    """
    extractor = HazardRatioExtractor()
    return await extractor.extract_from_literature()


async def main():
    """Run hazard ratio extraction."""
    import asyncio

    logging.basicConfig(level=logging.INFO)

    extractor = HazardRatioExtractor()
    extracted = await extractor.extract_from_literature()

    print(f"\n=== Extracted {len(extracted)} Hazard Ratios ===")
    for hr in extracted:
        print(f"\nFactor: {hr.get('risk_factor', 'unknown')}")
        print(f"  HR: {hr.get('hazard_ratio', 'N/A')}")
        print(f"  CI: {hr.get('confidence_interval', 'N/A')}")
        print(f"  Source: {hr.get('source_file', 'unknown')} p.{hr.get('page_number', 'N/A')}")

    # Save to YAML
    output_path = Path(__file__).parent.parent / "processed" / "extracted_hazard_ratios.yaml"
    extractor.save_to_yaml(output_path)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
