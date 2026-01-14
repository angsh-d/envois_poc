#!/usr/bin/env python3
"""
Registry Data Extraction Script
Uses pdfplumber for text extraction and Gemini for structured data extraction.
Generates registry_norms.yaml with full provenance from official annual reports.
"""

import os
import json
import yaml
import pdfplumber
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from google import genai

AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL   
    }
)


class SurvivalRate(BaseModel):
    timepoint: str
    rate: float
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None
    exact_quote: Optional[str] = None


class RevisionReason(BaseModel):
    reason: str
    percentage: float
    description: Optional[str] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None


class RegistryExtraction(BaseModel):
    registry_name: str
    registry_abbreviation: str
    report_year: int
    data_period: str
    population: str
    n_procedures: Optional[int] = None
    n_primary: Optional[int] = None
    survival_rates: List[SurvivalRate]
    revision_reasons: List[RevisionReason]
    provenance_notes: Optional[str] = None


def is_rate_limit_error(exception: BaseException) -> bool:
    error_msg = str(exception)
    return (
        "429" in error_msg 
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower() 
        or "rate limit" in error_msg.lower()
    )


def extract_text_from_pdf(pdf_path: str, max_pages: int = 100) -> str:
    """Extract text from PDF with page markers."""
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        pages_to_read = min(len(pdf.pages), max_pages)
        for i, page in enumerate(pdf.pages[:pages_to_read], 1):
            page_text = page.extract_text() or ""
            full_text += f"\n\n--- PAGE {i} ---\n\n{page_text}"
    return full_text


def find_revision_hip_sections(pdf_path: str) -> str:
    """Extract sections specifically about revision hip arthroplasty."""
    relevant_text = ""
    keywords = ['revision', 'hip', 'tha', 'total hip', 'survival', 'kaplan-meier', 
                'cumulative', 'revision rate', 'aseptic', 'loosening', 'dislocation',
                'infection', 'fracture']
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            page_text = (page.extract_text() or "").lower()
            if any(kw in page_text for kw in keywords):
                full_text = page.extract_text() or ""
                relevant_text += f"\n\n--- PAGE {i} ---\n\n{full_text}"
                if len(relevant_text) > 60000:
                    break
    
    return relevant_text if relevant_text else extract_text_from_pdf(pdf_path, 50)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def extract_registry_data(text: str, registry_name: str) -> dict:
    """Use Gemini to extract registry data."""
    
    prompt = f"""You are a clinical registry data extraction specialist. Extract REVISION HIP ARTHROPLASTY benchmark data from this registry annual report.

REGISTRY: {registry_name}

TEXT (with page markers like "--- PAGE X ---"):
{text[:70000]}

EXTRACT THE FOLLOWING DATA WITH EXACT PROVENANCE:

1. REGISTRY METADATA:
   - Full registry name
   - Abbreviation (AOANJRR, NJR, SHAR, AJRR, CJRR)
   - Report year
   - Data period covered
   - Population (focus on REVISION hip arthroplasty or all hip if revision not separate)
   - Number of revision hip procedures
   - Number of primary hip procedures (for context)

2. SURVIVAL RATES for REVISION HIP ARTHROPLASTY:
   For each timepoint (1yr, 2yr, 5yr, 10yr, 15yr if available):
   - Survival rate (as decimal 0.0-1.0)
   - 95% confidence interval if provided
   - PAGE NUMBER where found
   - TABLE or FIGURE reference
   - EXACT QUOTE from the document

3. REVISION REASONS (what causes revision surgery):
   For each reason (aseptic loosening, dislocation/instability, infection, periprosthetic fracture, etc.):
   - Percentage of total revisions (as decimal 0.0-1.0)
   - PAGE NUMBER where found
   - TABLE reference

IMPORTANT:
- Focus on REVISION hip arthroplasty data, not primary THA
- If only primary THA survival is available, extract that but note it in provenance
- Always include page numbers from the "--- PAGE X ---" markers
- Report survival rates as decimals (e.g., 0.942 for 94.2%)
- Report revision reason percentages as decimals (e.g., 0.268 for 26.8%)

Return valid JSON matching this schema:
{{
    "registry_name": "Full Registry Name",
    "registry_abbreviation": "ABBREV",
    "report_year": 2024,
    "data_period": "1999-2023",
    "population": "revision_tha" or "all_tha",
    "n_procedures": 45000,
    "n_primary": 800000,
    "survival_rates": [
        {{
            "timepoint": "1yr",
            "rate": 0.962,
            "ci_lower": 0.958,
            "ci_upper": 0.966,
            "page_number": 45,
            "table_reference": "Table 5.1",
            "exact_quote": "1-year survival rate was 96.2% (95% CI: 95.8-96.6)"
        }}
    ],
    "revision_reasons": [
        {{
            "reason": "aseptic_loosening",
            "percentage": 0.268,
            "description": "Aseptic loosening of component",
            "page_number": 52,
            "table_reference": "Figure 5.3"
        }}
    ],
    "provenance_notes": "Data from Chapter 5: Revision Hip Arthroplasty"
}}
"""

    response = client.models.generate_content(
        model='gemini-2.5-pro-preview-05-06',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'temperature': 0.1,
        }
    )
    
    result_text = response.text.strip()
    if result_text.startswith('```'):
        result_text = result_text.split('\n', 1)[1]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
    
    return json.loads(result_text)


def process_registry_pdf(pdf_path: str) -> dict:
    """Process a single registry PDF."""
    filename = os.path.basename(pdf_path)
    print(f"\nProcessing: {filename}")
    
    print("  Extracting relevant sections...")
    text = find_revision_hip_sections(pdf_path)
    print(f"  Extracted {len(text)} characters")
    
    print("  Calling Gemini for extraction...")
    data = extract_registry_data(text, filename)
    print(f"  Extracted: {len(data.get('survival_rates', []))} survival rates, "
          f"{len(data.get('revision_reasons', []))} revision reasons")
    
    return data


def convert_to_yaml_format(extractions: List[dict]) -> dict:
    """Convert extracted data to registry_norms.yaml format."""
    registries = {}
    
    for ext in extractions:
        abbrev = ext.get('registry_abbreviation', '').lower()
        if not abbrev:
            continue
            
        registry_data = {
            'name': ext.get('registry_name', ''),
            'abbreviation': ext.get('registry_abbreviation', ''),
            'report_year': ext.get('report_year', 2024),
            'data_years': ext.get('data_period', ''),
            'population': ext.get('population', 'revision_tha'),
            'n_procedures': ext.get('n_procedures'),
            'n_primary': ext.get('n_primary'),
        }
        
        for sr in ext.get('survival_rates', []):
            timepoint = sr.get('timepoint', '').replace('yr', '').replace('-', '')
            if timepoint.isdigit():
                registry_data[f'survival_{timepoint}yr'] = sr.get('rate')
                revision_rate = 1.0 - sr.get('rate', 1.0) if sr.get('rate') else None
                if revision_rate is not None:
                    registry_data[f'revision_rate_{timepoint}yr'] = round(revision_rate, 4)
        
        registry_data['revision_reasons'] = [
            {
                'reason': rr.get('reason', ''),
                'percentage': rr.get('percentage'),
                'description': rr.get('description', ''),
            }
            for rr in ext.get('revision_reasons', [])
        ]
        
        registry_data['provenance'] = {
            'source_file': f"data/raw/downloaded_registry/{abbrev.upper()}_2024_Annual_Report.pdf",
            'extraction_date': '2026-01-14',
            'extraction_method': 'Gemini 2.5 Pro Preview with pdfplumber',
            'survival_rates_provenance': [
                {
                    'timepoint': sr.get('timepoint'),
                    'page': sr.get('page_number'),
                    'table': sr.get('table_reference'),
                    'quote': sr.get('exact_quote'),
                }
                for sr in ext.get('survival_rates', [])
            ],
            'revision_reasons_provenance': [
                {
                    'reason': rr.get('reason'),
                    'page': rr.get('page_number'),
                    'table': rr.get('table_reference'),
                }
                for rr in ext.get('revision_reasons', [])
            ],
            'notes': ext.get('provenance_notes', '')
        }
        
        registries[abbrev] = registry_data
    
    return {
        'metadata': {
            'version': '2.0.0',
            'generated_date': '2026-01-14',
            'extraction_method': 'Gemini 2.5 Pro Preview with pdfplumber',
            'provenance_standard': 'Full traceability with page numbers and table references',
        },
        'registries': registries,
    }


def main():
    registry_dir = Path("data/raw/downloaded_registry")
    output_file = Path("data/processed/document_as_code/registry_norms.yaml")
    
    pdf_files = list(registry_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} registry PDFs to process")
    
    extractions = []
    for pdf_path in pdf_files:
        try:
            data = process_registry_pdf(str(pdf_path))
            extractions.append(data)
        except Exception as e:
            print(f"  ERROR processing {pdf_path.name}: {e}")
    
    print("\nConverting to YAML format...")
    yaml_data = convert_to_yaml_format(extractions)
    
    print(f"Writing to {output_file}...")
    with open(output_file, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"\nExtraction complete!")
    print(f"  Registries processed: {len(yaml_data.get('registries', {}))}")
    for abbrev, data in yaml_data.get('registries', {}).items():
        survival_count = sum(1 for k in data.keys() if k.startswith('survival_'))
        print(f"  - {abbrev.upper()}: {survival_count} survival rates, "
              f"{len(data.get('revision_reasons', []))} revision reasons")


if __name__ == "__main__":
    main()
