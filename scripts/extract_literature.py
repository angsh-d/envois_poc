#!/usr/bin/env python3
"""
Literature Data Extraction Script
Uses pdfplumber for text extraction and Gemini 3 Pro Preview for structured data extraction.
Generates literature_benchmarks.yaml with full provenance.
"""

import os
import json
import yaml
import pdfplumber
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from google import genai
from google.genai import types

AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL   
    }
)


class ExtractedPublication(BaseModel):
    """Schema for extracted publication data"""
    pmid: Optional[str] = None
    doi: Optional[str] = None
    title: str
    authors: str
    journal: str
    year: int
    study_type: str
    sample_size: Optional[int] = None
    follow_up_months: Optional[float] = None


class ExtractedOutcome(BaseModel):
    """Schema for extracted outcome data with provenance"""
    metric_name: str
    value: float
    unit: Optional[str] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None
    exact_quote: Optional[str] = None
    context: Optional[str] = None


class ExtractedHazardRatio(BaseModel):
    """Schema for hazard ratio data"""
    risk_factor: str
    hazard_ratio: float
    ci_lower: float
    ci_upper: float
    p_value: Optional[str] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None


class FullExtraction(BaseModel):
    """Complete extraction from a publication"""
    publication: ExtractedPublication
    outcomes: list[ExtractedOutcome]
    hazard_ratios: list[ExtractedHazardRatio]
    mcid_thresholds: list[ExtractedOutcome]
    survival_rates: list[ExtractedOutcome]


def is_rate_limit_error(exception: BaseException) -> bool:
    """Check if the exception is a rate limit error."""
    error_msg = str(exception)
    return (
        "429" in error_msg 
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower() 
        or "rate limit" in error_msg.lower()
    )


def extract_text_from_pdf(pdf_path: str) -> tuple[str, dict]:
    """Extract text from PDF with page numbers."""
    text_by_page = {}
    full_text = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text() or ""
            text_by_page[i] = page_text
            full_text += f"\n\n--- PAGE {i} ---\n\n{page_text}"
    
    return full_text, text_by_page


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def extract_with_gemini(text: str, pdf_filename: str) -> dict:
    """Use Gemini to extract structured data from PDF text."""
    
    prompt = f"""You are a clinical research data extraction specialist. Extract ALL clinical outcome data from this research paper text.

PAPER: {pdf_filename}

TEXT:
{text[:80000]}  # Limit to avoid token limits

EXTRACT THE FOLLOWING DATA WITH EXACT PROVENANCE:

1. PUBLICATION METADATA:
   - Title, Authors, Journal, Year, PMID/DOI if mentioned
   - Study type (RCT, cohort, meta-analysis, registry, etc.)
   - Sample size (n=?)
   - Follow-up period

2. CLINICAL OUTCOMES (look for):
   - Harris Hip Score (HHS) - preoperative, postoperative, improvement
   - Oxford Hip Score (OHS)
   - WOMAC scores
   - VAS pain scores
   - UCLA activity scores
   - SF-12/SF-36 scores
   - Functional outcomes

3. SURVIVAL/COMPLICATION RATES:
   - Implant survival rates (2-year, 5-year, 10-year)
   - Re-revision rates
   - Complication rates
   - Dislocation rates
   - Infection rates
   - Aseptic loosening rates

4. HAZARD RATIOS / RISK FACTORS (if multivariate analysis):
   - Risk factor name
   - Hazard ratio with 95% CI
   - P-value

5. MCID THRESHOLDS (if mentioned):
   - Minimal Clinically Important Difference values
   - Substantial Clinical Benefit thresholds

FOR EACH DATA POINT, INCLUDE:
- page_number: Page where found (from "--- PAGE X ---" markers)
- table_reference: Table/Figure number if applicable (e.g., "Table 2", "Figure 3")
- exact_quote: The exact text from the paper containing this value

Return as JSON with this structure:
{{
  "publication": {{
    "pmid": "string or null",
    "doi": "string or null", 
    "title": "string",
    "authors": "string",
    "journal": "string",
    "year": int,
    "study_type": "string",
    "sample_size": int or null,
    "follow_up_months": float or null
  }},
  "outcomes": [
    {{
      "metric_name": "string (e.g. 'HHS_preoperative', 'HHS_improvement')",
      "value": float,
      "unit": "string or null",
      "confidence_interval_lower": float or null,
      "confidence_interval_upper": float or null,
      "page_number": int or null,
      "table_reference": "string or null",
      "exact_quote": "string or null",
      "context": "string description"
    }}
  ],
  "hazard_ratios": [
    {{
      "risk_factor": "string",
      "hazard_ratio": float,
      "ci_lower": float,
      "ci_upper": float,
      "p_value": "string or null",
      "page_number": int or null,
      "table_reference": "string or null"
    }}
  ],
  "mcid_thresholds": [
    {{
      "metric_name": "string",
      "value": float,
      "unit": "points",
      "page_number": int or null,
      "table_reference": "string or null",
      "exact_quote": "string or null",
      "context": "string"
    }}
  ],
  "survival_rates": [
    {{
      "metric_name": "string (e.g. 'survival_5yr', 'revision_rate')",
      "value": float,
      "unit": "percent",
      "confidence_interval_lower": float or null,
      "confidence_interval_upper": float or null,
      "page_number": int or null,
      "table_reference": "string or null",
      "exact_quote": "string or null",
      "context": "string"
    }}
  ]
}}

Be thorough and extract ALL numerical data with provenance. If a value is not found, don't include it.
Return ONLY valid JSON, no markdown or explanation."""

    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=8192
        )
    )
    
    result_text = response.text or "{}"
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        # Try to clean up the response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        return json.loads(result_text.strip())


def process_pdf(pdf_path: Path) -> dict:
    """Process a single PDF and extract data."""
    print(f"Processing: {pdf_path.name}")
    
    try:
        full_text, text_by_page = extract_text_from_pdf(str(pdf_path))
        print(f"  Extracted {len(text_by_page)} pages, {len(full_text)} chars")
        
        extraction = extract_with_gemini(full_text, pdf_path.name)
        extraction['source_file'] = pdf_path.name
        print(f"  Extracted: {len(extraction.get('outcomes', []))} outcomes, "
              f"{len(extraction.get('hazard_ratios', []))} hazard ratios, "
              f"{len(extraction.get('survival_rates', []))} survival rates")
        
        return extraction
    except Exception as e:
        print(f"  ERROR: {e}")
        return {"error": str(e), "source_file": pdf_path.name}


def generate_yaml_with_provenance(extractions: list[dict]) -> dict:
    """Generate literature_benchmarks.yaml structure with full provenance."""
    
    benchmarks = {
        "metadata": {
            "version": "2.0.0",
            "generated_date": "2026-01-14",
            "extraction_method": "Gemini 3 Pro Preview with pdfplumber",
            "provenance_standard": "Full traceability with page numbers and exact quotes"
        },
        "publications": [],
        "outcome_benchmarks": {
            "harris_hip_score": [],
            "survival_rates": [],
            "complication_rates": []
        },
        "risk_factors": [],
        "mcid_thresholds": []
    }
    
    for ext in extractions:
        if "error" in ext:
            continue
            
        pub = ext.get("publication", {})
        source_file = ext.get("source_file", "unknown")
        
        # Build publication entry
        pub_entry = {
            "id": f"pub_{pub.get('year', 'unknown')}_{source_file.split('.')[0].lower().replace(' ', '_')[:20]}",
            "pmid": pub.get("pmid"),
            "doi": pub.get("doi"),
            "title": pub.get("title", source_file),
            "authors": pub.get("authors", "Unknown"),
            "journal": pub.get("journal", "Unknown"),
            "year": pub.get("year", 2025),
            "study_type": pub.get("study_type", "clinical_study"),
            "sample_size": pub.get("sample_size"),
            "follow_up_months": pub.get("follow_up_months"),
            "source_file": source_file
        }
        benchmarks["publications"].append(pub_entry)
        
        pub_id = pub_entry["id"]
        
        # Process outcomes
        for outcome in ext.get("outcomes", []):
            metric = outcome.get("metric_name", "").lower()
            entry = {
                "publication_id": pub_id,
                "metric": outcome.get("metric_name"),
                "value": outcome.get("value"),
                "unit": outcome.get("unit"),
                "ci_lower": outcome.get("confidence_interval_lower"),
                "ci_upper": outcome.get("confidence_interval_upper"),
                "provenance": {
                    "page": outcome.get("page_number"),
                    "table": outcome.get("table_reference"),
                    "quote": outcome.get("exact_quote"),
                    "context": outcome.get("context")
                }
            }
            
            if "hhs" in metric or "harris" in metric:
                benchmarks["outcome_benchmarks"]["harris_hip_score"].append(entry)
            elif "survival" in metric or "revision" in metric:
                benchmarks["outcome_benchmarks"]["survival_rates"].append(entry)
            else:
                benchmarks["outcome_benchmarks"]["complication_rates"].append(entry)
        
        # Process survival rates
        for survival in ext.get("survival_rates", []):
            entry = {
                "publication_id": pub_id,
                "metric": survival.get("metric_name"),
                "value": survival.get("value"),
                "unit": survival.get("unit", "percent"),
                "ci_lower": survival.get("confidence_interval_lower"),
                "ci_upper": survival.get("confidence_interval_upper"),
                "provenance": {
                    "page": survival.get("page_number"),
                    "table": survival.get("table_reference"),
                    "quote": survival.get("exact_quote"),
                    "context": survival.get("context")
                }
            }
            benchmarks["outcome_benchmarks"]["survival_rates"].append(entry)
        
        # Process hazard ratios
        for hr in ext.get("hazard_ratios", []):
            entry = {
                "publication_id": pub_id,
                "risk_factor": hr.get("risk_factor"),
                "hazard_ratio": hr.get("hazard_ratio"),
                "ci_lower": hr.get("ci_lower"),
                "ci_upper": hr.get("ci_upper"),
                "p_value": hr.get("p_value"),
                "provenance": {
                    "page": hr.get("page_number"),
                    "table": hr.get("table_reference")
                }
            }
            benchmarks["risk_factors"].append(entry)
        
        # Process MCID thresholds
        for mcid in ext.get("mcid_thresholds", []):
            entry = {
                "publication_id": pub_id,
                "metric": mcid.get("metric_name"),
                "threshold_value": mcid.get("value"),
                "threshold_type": "MCID",
                "provenance": {
                    "page": mcid.get("page_number"),
                    "table": mcid.get("table_reference"),
                    "quote": mcid.get("exact_quote"),
                    "context": mcid.get("context")
                }
            }
            benchmarks["mcid_thresholds"].append(entry)
    
    return benchmarks


def main():
    """Main extraction pipeline."""
    print("=" * 60)
    print("LITERATURE DATA EXTRACTION WITH PROVENANCE")
    print("Using Gemini 3 Pro Preview for structured extraction")
    print("=" * 60)
    
    # Find all PDFs in downloaded_literature
    pdf_dir = Path("data/raw/downloaded_literature")
    pdfs = list(pdf_dir.glob("*.pdf"))
    
    print(f"\nFound {len(pdfs)} PDFs to process:")
    for pdf in pdfs:
        print(f"  - {pdf.name}")
    
    # Process each PDF
    extractions = []
    for pdf in pdfs:
        result = process_pdf(pdf)
        extractions.append(result)
        print()
    
    # Generate YAML
    print("=" * 60)
    print("GENERATING LITERATURE_BENCHMARKS.YAML")
    print("=" * 60)
    
    benchmarks = generate_yaml_with_provenance(extractions)
    
    # Save raw extractions for reference
    with open("data/processed/document_as_code/raw_extractions.json", "w") as f:
        json.dump(extractions, f, indent=2)
    print("Saved raw extractions to raw_extractions.json")
    
    # Save YAML
    yaml_path = "data/processed/document_as_code/literature_benchmarks.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(benchmarks, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"Saved literature benchmarks to {yaml_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Publications processed: {len(benchmarks['publications'])}")
    print(f"HHS outcomes: {len(benchmarks['outcome_benchmarks']['harris_hip_score'])}")
    print(f"Survival rates: {len(benchmarks['outcome_benchmarks']['survival_rates'])}")
    print(f"Complication rates: {len(benchmarks['outcome_benchmarks']['complication_rates'])}")
    print(f"Risk factors (hazard ratios): {len(benchmarks['risk_factors'])}")
    print(f"MCID thresholds: {len(benchmarks['mcid_thresholds'])}")


if __name__ == "__main__":
    main()
