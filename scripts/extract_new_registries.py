#!/usr/bin/env python3
"""
Extract revision THA survival data from new registry annual reports.
Uses Gemini 2.5 Pro with PDF content for accurate extraction with provenance.
"""

import os
import json
import yaml
from pathlib import Path
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

REGISTRY_FILES = {
    "nar": {
        "name": "Norwegian Arthroplasty Register",
        "abbreviation": "NAR",
        "country": "Norway",
        "file": "data/raw/downloaded_registry/NAR_2023_Annual_Report.pdf",
        "report_year": 2023,
    },
    "nzjr": {
        "name": "New Zealand Joint Registry",
        "abbreviation": "NZJR",
        "country": "New Zealand",
        "file": "data/raw/downloaded_registry/NZJR_26_Year_Report.pdf",
        "report_year": 2024,
    },
    "dhr": {
        "name": "Danish Hip Arthroplasty Register",
        "abbreviation": "DHR",
        "country": "Denmark",
        "file": "data/raw/downloaded_registry/DHR_2024_Annual_Report.pdf",
        "report_year": 2024,
    },
    "eprd": {
        "name": "German Arthroplasty Registry",
        "abbreviation": "EPRD",
        "country": "Germany",
        "file": "data/raw/downloaded_registry/EPRD_2024_Annual_Report.pdf",
        "report_year": 2024,
    },
}

EXTRACTION_PROMPT = """You are a clinical data extraction specialist. Your task is to extract REVISION hip arthroplasty survival data from this registry annual report.

CRITICAL REQUIREMENTS:
1. ONLY extract data for REVISION total hip arthroplasty (re-revision rates, survival of revision implants)
2. DO NOT extract PRIMARY hip arthroplasty data - we need revision-specific outcomes
3. Provide EXACT page numbers and table/figure references for EVERY data point
4. If revision-specific survival data is not available, clearly state "NOT_AVAILABLE"

Extract the following data:
1. Total number of revision hip procedures in the registry
2. Survival rates at various timepoints (1yr, 2yr, 5yr, 10yr, 15yr) for REVISION THA
   - These should represent "time to re-revision" or "survival of revision implant"
3. Revision reasons (indications for re-revision of the revision implant)
4. Data period covered

Return your response as a JSON object with this structure:
{
    "population": "revision_tha" or "primary_tha_only" if revision data not available,
    "data_available": true/false,
    "n_procedures": <number of revision procedures or null>,
    "data_period": "<start year>-<end year>",
    "survival_rates": {
        "1yr": {"rate": <decimal 0-1 or null>, "page": <int>, "table_or_figure": "<reference>", "exact_quote": "<text from report>"},
        "2yr": {"rate": <decimal or null>, "page": <int>, "table_or_figure": "<reference>", "exact_quote": "<text>"},
        "5yr": {"rate": <decimal or null>, "page": <int>, "table_or_figure": "<reference>", "exact_quote": "<text>"},
        "10yr": {"rate": <decimal or null>, "page": <int>, "table_or_figure": "<reference>", "exact_quote": "<text>"},
        "15yr": {"rate": <decimal or null>, "page": <int>, "table_or_figure": "<reference>", "exact_quote": "<text>"}
    },
    "revision_reasons": [
        {"reason": "<category>", "percentage": <decimal>, "description": "<full name>", "page": <int>, "table_or_figure": "<ref>"}
    ],
    "notes": "<any important context about the data or limitations>",
    "provenance_notes": "<description of where in the report this data was found>"
}

Remember: We need REVISION THA data (survival of revision implants), not PRIMARY THA data.
If the report only contains Kaplan-Meier figures without tabulated values, indicate this.
If survival rates are presented as cumulative revision rates, convert to survival (1 - revision_rate).
"""

def extract_registry_data(registry_id: str, registry_info: dict) -> dict:
    """Extract revision THA data from a registry PDF using Gemini."""
    pdf_path = Path(registry_info["file"])
    
    if not pdf_path.exists():
        print(f"  ERROR: File not found: {pdf_path}")
        return None
    
    print(f"  Uploading PDF ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)...")
    
    try:
        uploaded_file = genai.upload_file(str(pdf_path))
        print(f"  PDF uploaded successfully")
        
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        prompt = f"""Registry: {registry_info['name']} ({registry_info['abbreviation']})
Country: {registry_info['country']}
Report Year: {registry_info['report_year']}

{EXTRACTION_PROMPT}"""
        
        print(f"  Extracting revision THA data...")
        response = model.generate_content(
            [uploaded_file, prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            )
        )
        
        result = json.loads(response.text)
        result["registry_id"] = registry_id
        result["registry_name"] = registry_info["name"]
        result["abbreviation"] = registry_info["abbreviation"]
        result["country"] = registry_info["country"]
        result["report_year"] = registry_info["report_year"]
        result["source_file"] = str(pdf_path)
        
        return result
        
    except Exception as e:
        print(f"  ERROR extracting from {registry_id}: {e}")
        return None

def main():
    print("=" * 60)
    print("EXTRACTING REVISION THA DATA FROM NEW REGISTRIES")
    print("=" * 60)
    
    results = {}
    
    for registry_id, registry_info in REGISTRY_FILES.items():
        print(f"\n[{registry_id.upper()}] {registry_info['name']}")
        print("-" * 40)
        
        result = extract_registry_data(registry_id, registry_info)
        if result:
            results[registry_id] = result
            
            if result.get("data_available"):
                print(f"  SUCCESS: Found revision THA data")
                survival = result.get("survival_rates", {})
                for timepoint in ["1yr", "5yr", "10yr", "15yr"]:
                    if survival.get(timepoint, {}).get("rate"):
                        rate = survival[timepoint]["rate"]
                        page = survival[timepoint].get("page", "?")
                        print(f"    {timepoint}: {rate*100:.1f}% (page {page})")
            else:
                print(f"  WARNING: Revision THA data not available")
                print(f"  Notes: {result.get('notes', 'No notes')}")
    
    output_path = Path("data/processed/extracted_registries_new.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Extraction complete. Results saved to: {output_path}")
    print(f"{'=' * 60}")
    
    return results

if __name__ == "__main__":
    main()
