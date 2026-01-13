# File Inventory - Clinical Intelligence Platform POC
## H-34 DELTA Revision Cup Study

**Last Updated:** January 11, 2026
**Purpose:** Active files required for UC1-UC5 implementation

---

## Project Structure

```
enovis_poc/
├── .archive/                          # Archived files (not active)
├── .claude/                           # Claude Code settings
├── .env.template                      # Environment variable template
├── requirements.txt                   # Python dependencies
│
├── HIGH_LEVEL_POC_DESIGN.md          # Main POC design document (v9.0)
├── USE_CASES.md                       # Detailed use case specifications
├── FILE_INVENTORY.md                  # This file
│
├── data/                              # ALL DATA AND DATA CODE
│   ├── __init__.py                   # Module docstring with structure
│   │
│   ├── raw/                          # Original source files (IMMUTABLE)
│   │   ├── study/                    # H-34 study data
│   │   │   ├── H-34DELTARevisionstudy_export_20250912.xlsx  # Real (N=37)
│   │   │   └── H-34_SYNTHETIC_PRODUCTION.xlsx               # Synthetic (N=700)
│   │   ├── protocol/                 # Protocol documents
│   │   │   └── CIP_H-34_v.2.0_05Nov2024_fully signed.pdf
│   │   ├── literature/               # 12 literature PDFs
│   │   │   ├── Meding et al, 2025.pdf
│   │   │   ├── Dixon et al 2025.pdf
│   │   │   ├── Harris et al2025.pdf
│   │   │   └── ... (9 more)
│   │   └── registry/                 # Registry benchmark data
│   │       ├── Relevant data output from registry reports.docx
│   │       └── Example reports/
│   │
│   ├── processed/                    # Processed/extracted data
│   │   └── document_as_code/         # YAML extractions (to be generated)
│   │       ├── protocol_rules.yaml   # (pending)
│   │       ├── literature_benchmarks.yaml  # (pending)
│   │       └── registry_norms.yaml   # (pending)
│   │
│   ├── vectorstore/                  # RAG Vector Store
│   │   ├── __init__.py              # Exports ChromaVectorStore
│   │   ├── chroma_store.py          # ChromaDB + Gemini embeddings
│   │   └── chroma_db/               # Persistent storage (auto-created)
│   │
│   ├── loaders/                      # Data loading utilities
│   │   ├── __init__.py
│   │   └── excel_loader.py          # H34ExcelLoader
│   │
│   ├── generators/                   # Synthetic data generation
│   │   ├── __init__.py
│   │   └── synthetic_h34.py         # SyntheticH34Generator
│   │
│   └── models/                       # Data models
│       ├── __init__.py
│       └── unified_schema.py        # Pydantic models
│
├── pipeline/                          # Pipeline utilities
│   ├── __init__.py
│   └── logging_config.py             # Centralized logging
│
├── app/                               # Application code
│   ├── __init__.py
│   └── config.py                     # Configuration
│
├── tmp/                               # Temporary/log files
└── venv/                              # Python virtual environment
```

---

## Data Sources (data/raw/)

### 1. Study Data (data/raw/study/)

| File | Records | Purpose | Used In |
|------|---------|---------|---------|
| `H-34DELTARevisionstudy_export_20250912.xlsx` | 37 patients | Real H-34 study data | UC1-UC5 |
| `H-34_SYNTHETIC_PRODUCTION.xlsx` | 700 patients | Synthetic data for ML | UC4 |

**H-34 Study Data Sheets:**
| Sheet | Content | Records |
|-------|---------|---------|
| 1 Patients | Demographics | 37 |
| 2 Preoperatives | Diagnosis, history | 36 |
| 3 Radiographical (Preop) | Baseline imaging | 36 |
| 4 Intraoperatives | Surgery details | 36 |
| 5 Surgery Data | Procedure info | 35 |
| 6 Batch Numbers | Lot tracking | 33 |
| 7-16 Follow-ups | Visit data + Radiology | Varies |
| 17 Adverse Events | Safety events | 15 |
| 18 Score HHS | Primary endpoint | 112 |
| 19 Score OHS | Secondary endpoint | 112 |
| 20 Explants | Revisions | 4 |
| 21 Reimplants | Revision surgery | 3 |

### 2. Protocol Documents (data/raw/protocol/)

| File | Version | Used In |
|------|---------|---------|
| `CIP_H-34_v.2.0_05Nov2024_fully signed.pdf` | v2.0 (Current) | UC1, UC2, UC3, UC5 |

### 3. Literature PDFs (data/raw/literature/)

| File | Purpose | Used In |
|------|---------|---------|
| `Meding et al, 2025.pdf` | Outcome benchmarks, MCID rates | UC1, UC2, UC4 |
| `Dixon et al 2025.pdf` | Fracture risk factors, HRs | UC2, UC4 |
| `Harris et al2025.pdf` | AE rate benchmarks | UC2, UC5 |
| `Vasios et al.pdf` | Functional outcomes | UC1, UC5 |
| `Zucchet et al 2025.pdf` | Revision outcomes | UC2 |
| `Willems et al 2025.pdf` | Additional benchmarks | UC4 |
| `Merolla et al 2025.pdf` | Clinical outcomes | UC5 |
| `Bazan et al.pdf` | Product data | RAG context |
| `Chirico et al.pdf` | Product data | RAG context |
| `hert et al.pdf` | Product data | RAG context |
| `Kinoshita et al.pdf` | Product data | RAG context |
| `steckel.pdf` | Product data | RAG context |

### 4. Registry Data (data/raw/registry/)

| File | Purpose | Used In |
|------|---------|---------|
| `Relevant data output from registry reports.docx` | AOANJRR/NJR benchmarks | UC1, UC2, UC4, UC5 |
| `Example reports/` | Sample registry reports | Reference |

---

## Vector Store Architecture

### Technology Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌────────────────────┐     ┌──────────────────────┐  │
│  │   Raw PDFs   │ ──► │  PDF Extraction    │ ──► │    Text Chunks       │  │
│  │  (13 files)  │     │  (PyMuPDF)         │     │  (500-1000 tokens)   │  │
│  └──────────────┘     └────────────────────┘     └──────────┬───────────┘  │
│                                                              │              │
│                                                              ▼              │
│  ┌──────────────┐     ┌────────────────────┐     ┌──────────────────────┐  │
│  │   ChromaDB   │ ◄── │  Gemini Embeddings │ ◄── │    Chunked Text      │  │
│  │  (Persist)   │     │  text-embedding-004│     │                      │  │
│  └──────┬───────┘     └────────────────────┘     └──────────────────────┘  │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        COLLECTIONS                                    │  │
│  │  • h34_protocol   - Protocol document chunks                         │  │
│  │  • h34_literature - Literature PDF chunks                            │  │
│  │  • h34_registry   - Registry document chunks                         │  │
│  │  • h34_all        - Combined for cross-source search                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Usage

```python
from data.vectorstore import ChromaVectorStore, get_vector_store

# Get singleton instance
store = get_vector_store()

# Search protocol documents
results = store.search(
    query="What are the visit windows for follow-up?",
    source_type="protocol",
    n_results=5
)

# Cross-source search
results = store.search_multi_source(
    query="fracture risk factors",
    source_types=["literature", "registry"],
    n_results_per_source=3
)
```

---

## Code Files

### Data Loading (data/loaders/)

| File | Class | Purpose | Used In |
|------|-------|---------|---------|
| `excel_loader.py` | `H34ExcelLoader` | Load and validate H-34 study data | UC1-UC5 |

### Synthetic Data (data/generators/)

| File | Class | Purpose | Used In |
|------|-------|---------|---------|
| `synthetic_h34.py` | `SyntheticH34Generator` | Generate synthetic patients for ML | UC4 |

### Data Models (data/models/)

| File | Classes | Purpose | Used In |
|------|---------|---------|---------|
| `unified_schema.py` | Pydantic models | Data validation and schema | UC1-UC5 |

### Vector Store (data/vectorstore/)

| File | Class | Purpose | Used In |
|------|-------|---------|---------|
| `chroma_store.py` | `ChromaVectorStore`, `DocumentChunk` | RAG retrieval with ChromaDB + Gemini | UC1, UC2, UC5 |
| `pdf_extractor.py` | `PDFExtractor` | PDF extraction and chunking for indexing | UC1, UC2, UC5 |

### Pipeline (pipeline/)

| File | Purpose | Used In |
|------|---------|---------|
| `logging_config.py` | Centralized logging to ./tmp/ | All modules |

### Application (app/)

| File | Purpose | Used In |
|------|---------|---------|
| `config.py` | Environment config, API keys | All modules |
| `main.py` | FastAPI application entry point | API server |

### API Routers (app/api/routers/)

| File | Purpose | Endpoints |
|------|---------|-----------|
| `health.py` | Health check endpoints | `/health`, `/ready` |
| `uc1_readiness.py` | UC1: Regulatory Readiness | `/api/v1/uc1/readiness/*` |
| `uc2_safety.py` | UC2: Safety Signals | `/api/v1/uc2/safety/*` |
| `uc3_deviations.py` | UC3: Protocol Deviations | `/api/v1/uc3/deviations/*` |
| `uc4_risk.py` | UC4: Risk Stratification | `/api/v1/uc4/risk/*` |
| `uc5_dashboard.py` | UC5: Executive Dashboard | `/api/v1/uc5/dashboard/*` |

---

## Document-as-Code (data/processed/document_as_code/)

**Status: Pending extraction**

| File | Source | Purpose | Used In |
|------|--------|---------|---------|
| `protocol_rules.yaml` | CIP v2.0 | Visit windows, endpoints, I/E criteria | UC1, UC3 |
| `literature_benchmarks.yaml` | Literature PDFs | Outcome benchmarks, HRs | UC1, UC2, UC4 |
| `registry_norms.yaml` | Registry reports | AOANJRR/NJR population norms | UC1, UC2, UC4, UC5 |

---

## Use Case → File Dependencies

| Use Case | Raw Data | Vector Store | Doc-as-Code | Code |
|----------|----------|--------------|-------------|------|
| **UC1** Readiness | Study, Protocol, Lit, Reg | ✅ All | protocol_rules, lit_bench, reg_norms | excel_loader |
| **UC2** Safety | Study (AEs), Protocol, Lit, Reg | ✅ Lit, Reg | lit_bench, reg_norms | excel_loader |
| **UC3** Deviations | Study (visits), Protocol | ❌ | protocol_rules | excel_loader |
| **UC4** Risk | Study, Synthetic, Lit | ✅ Lit | lit_bench | excel_loader, synthetic_h34 |
| **UC5** Dashboard | All above | ✅ All | All | All above |

---

## Configuration

| File | Purpose |
|------|---------|
| `.env.template` | Template for environment variables |
| `requirements.txt` | Python package dependencies |

### Required Environment Variables

```bash
# Gemini API (for embeddings and LLM)
GEMINI_API_KEY=your_key_here

# Azure OpenAI (optional, for consensus)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## Archived Files

See `.archive/cleanup_20260111/README.md` for complete list of archived files.

---

*Inventory maintained for UC1-UC5 implementation*
*Last update: January 11, 2026*
