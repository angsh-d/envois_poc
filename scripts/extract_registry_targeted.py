#!/usr/bin/env python3
"""
Targeted registry extraction for specific page ranges.
Extracts from the correct revision hip arthroplasty sections.
"""

import os
import json
import yaml
import pdfplumber
from pathlib import Path
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


REGISTRY_PAGE_RANGES = {
    'SHAR': {
        'file': 'SHAR_2024_Annual_Report.pdf',
        'sections': [(95, 130)],
        'name': 'Swedish Arthroplasty Register',
    },
    'AJRR': {
        'file': 'AJRR_2024_Annual_Report.pdf',
        'sections': [(50, 80)],
        'name': 'American Joint Replacement Registry',
    },
    'AOANJRR': {
        'file': 'AOANJRR_2024_Annual_Report.pdf',
        'sections': [(230, 280), (340, 380)],
        'name': 'Australian Orthopaedic Association National Joint Replacement Registry',
    },
}


def is_rate_limit_error(exception: BaseException) -> bool:
    error_msg = str(exception)
    return (
        "429" in error_msg 
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower() 
        or "rate limit" in error_msg.lower()
    )


def extract_pages(pdf_path: str, page_ranges: list) -> str:
    """Extract text from specific page ranges."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for start, end in page_ranges:
            for page_num in range(start - 1, min(end, len(pdf.pages))):
                page = pdf.pages[page_num]
                page_text = page.extract_text() or ""
                text += f"\n\n--- PAGE {page_num + 1} ---\n\n{page_text}"
    return text


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def extract_registry_data(text: str, registry_name: str) -> dict:
    """Use Gemini to extract registry data."""
    
    prompt = f"""You are a clinical registry data extraction specialist. Extract REVISION HIP ARTHROPLASTY benchmark data from this registry annual report section.

REGISTRY: {registry_name}

TEXT (with page markers like "--- PAGE X ---"):
{text[:70000]}

EXTRACT THE FOLLOWING DATA WITH EXACT PROVENANCE:

1. REGISTRY METADATA:
   - Full registry name
   - Abbreviation (AOANJRR, NJR, SHAR, AJRR, CJRR)
   - Report year
   - Data period covered
   - Population: "revision_tha" if data is specifically for revision hip procedures
   - Number of revision hip procedures
   - Number of primary hip procedures (for context)

2. SURVIVAL RATES for REVISION HIP ARTHROPLASTY (time to re-revision):
   For each timepoint (1yr, 2yr, 5yr, 10yr, 15yr if available):
   - Survival rate (as decimal 0.0-1.0) - this is 1.0 minus the cumulative revision rate
   - 95% confidence interval if provided (ci_lower, ci_upper as decimals)
   - PAGE NUMBER where found (from "--- PAGE X ---" markers)
   - TABLE or FIGURE reference
   - EXACT QUOTE from the document

3. REVISION REASONS (indications for revision surgery):
   For each reason (aseptic loosening, dislocation/instability, infection, periprosthetic fracture, etc.):
   - Percentage of total revisions (as decimal 0.0-1.0)
   - Description
   - PAGE NUMBER where found
   - TABLE reference

IMPORTANT:
- Focus on REVISION hip arthroplasty data (re-revision rates), not primary THA survival
- If you see "Cumulative Percent Revision" or "Cumulative Re-revision", convert to survival by: survival = 1 - CPR
- Report ALL survival rates as decimals between 0.0 and 1.0 (e.g., 94.2% → 0.942)
- Report revision reason percentages as decimals (e.g., 26.8% → 0.268)
- Always include the exact page number from the markers

Return valid JSON matching this schema:
{{
    "registry_name": "Full Registry Name",
    "registry_abbreviation": "ABBREV",
    "report_year": 2024,
    "data_period": "1999-2023",
    "population": "revision_tha",
    "n_procedures": 45000,
    "n_primary": 800000,
    "survival_rates": [
        {{
            "timepoint": "2yr",
            "rate": 0.942,
            "ci_lower": 0.938,
            "ci_upper": 0.946,
            "page_number": 105,
            "table_reference": "Figure 5.1",
            "exact_quote": "2-year re-revision rate of 5.8% (94.2% survival)"
        }}
    ],
    "revision_reasons": [
        {{
            "reason": "aseptic_loosening",
            "percentage": 0.268,
            "description": "Aseptic loosening of component",
            "page_number": 110,
            "table_reference": "Table 5.3"
        }}
    ],
    "provenance_notes": "Data from Revision Hip Arthroplasty chapter"
}}
"""

    response = client.models.generate_content(
        model='gemini-2.5-pro',
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


def main():
    registry_dir = Path("data/raw/downloaded_registry")
    
    for abbrev, config in REGISTRY_PAGE_RANGES.items():
        pdf_path = registry_dir / config['file']
        if not pdf_path.exists():
            print(f"Skipping {abbrev}: file not found")
            continue
            
        print(f"\nProcessing {abbrev}...")
        print(f"  Extracting pages: {config['sections']}")
        text = extract_pages(str(pdf_path), config['sections'])
        print(f"  Extracted {len(text)} characters")
        
        print(f"  Calling Gemini...")
        data = extract_registry_data(text, config['name'])
        print(f"  Extracted: {len(data.get('survival_rates', []))} survival rates, "
              f"{len(data.get('revision_reasons', []))} revision reasons")
        
        output_file = Path(f"data/processed/registry_{abbrev.lower()}_extracted.json")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved to {output_file}")


if __name__ == "__main__":
    main()
