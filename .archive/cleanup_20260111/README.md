# Archive: Project Cleanup - January 11, 2026

## Purpose
This archive contains files that are **not required** for the 5 core POC Use Cases (UC1-UC5):
- UC1: Regulatory Submission Readiness Assessment
- UC2: Safety Signal Detection & Contextualization
- UC3: Automated Protocol Deviation Detection
- UC4: Patient Risk Stratification
- UC5: Intelligent Study Health Executive Dashboard

## What Was Archived

### 1. Documentation - Superseded/Redundant
| File | Reason |
|------|--------|
| `agentic_ai_driven_clinical_intelligence_platform_proposal.md` | Original proposal, superseded by HIGH_LEVEL_POC_DESIGN.md v9.0 |
| `ENHANCED_SYSTEM_DESIGN.md` | Old system design, content incorporated into HIGH_LEVEL_POC_DESIGN.md |
| `POC_SCOPE_H34_DELTA_REVISION.md` | Old scope document, superseded |

### 2. Data - Non-H-34 Study Related
| File/Folder | Reason |
|-------------|--------|
| `1211680_S33.csv` | S-33 study data, not H-34 |
| `CIR_H31_24Apr2024_final.pdf` | H-31 clinical investigation report |
| `S-33 SMR HP Reverse Clinical Study Report_Enovis_4DEC2024.pdf` | S-33 study report |
| `DA&Ai_Project_for_Vendors.pdf` | Vendor RFP document |
| `20250704_K-09PhysicaCRandPS.xlsx` | K-09 study data |
| `Sales Data/` | Sales data not relevant to clinical POC |

### 3. Synthetic Data - Intermediate Versions
| File | Reason |
|------|--------|
| `H-34_SYNTHETIC_300patients.xlsx` | Intermediate version, superseded by PRODUCTION |
| `H-34_SYNTHETIC_500patients.xlsx` | Intermediate version, superseded by PRODUCTION |
| `11_DB export/Archive/` | Old data archives |

### 4. TMF/Regulatory Documents (Not Active in POC Phase)
| Folder | Reason |
|--------|--------|
| `02_Ethical approval/` | EC documents - can add back when TMF integration needed |
| `04_Reporting/` | Historical reports |
| `06_Vendors/` | Vendor management documents |
| `07_Congresses_Pubblications/` | Empty folder |
| `08_ISF_TMF management/` | TMF documents |
| `101_Site specific documents/` | Site-specific documents |
| `03_Data management/` (except 11_DB export) | eCRF, queries, trackers |

### 5. Literature - Non-Essential
| Folder | Reason |
|--------|--------|
| `Literature/Review and other Publications/` | General review papers not directly used in benchmarks |

### 6. Empty Directories
| Folder | Reason |
|--------|--------|
| `agents/` | Empty placeholder |
| `prompts/` | Empty placeholder |
| `tests/` | Empty placeholder |
| `ui/` | Empty placeholder |
| `data/processors/` | Empty placeholder |
| `app/api/` | Empty placeholder |

## Files KEPT in Active Workspace

### Core Data Sources (Required for UC1-UC5)
- `03_Data management/11_DB export/H-34DELTARevisionstudy_export_20250912.xlsx` - Main study data
- `03_Data management/11_DB export/H-34_SYNTHETIC_PRODUCTION.xlsx` - Synthetic data for ML
- `01_Study protocol/01_Protocol/CIP_v.2.0/` - Current protocol (v2.0)
- `Literature/Product Publications/` - 12 product-specific literature PDFs
- `Registry data/` - Registry benchmark data

### Code (Required for UC1-UC5)
- `data/loaders/excel_loader.py` - H34ExcelLoader
- `data/generators/synthetic_h34.py` - Synthetic data generator
- `data/models/unified_schema.py` - Data models
- `pipeline/logging_config.py` - Logging configuration
- `app/config.py` - Application configuration

### Documentation (Never Archive)
- `HIGH_LEVEL_POC_DESIGN.md` - Main POC design document (v9.0)
- `USE_CASES.md` - Detailed use case specifications

### Configuration
- `.env.template` - Environment template
- `requirements.txt` - Python dependencies

## Restoration
To restore any archived files:
```bash
cp -r .archive/cleanup_20260111/<folder_or_file> /Users/angshuman.deb/Downloads/enovis_poc/
```

## Archive Date
- **Date:** January 11, 2026
- **Archived By:** Claude Code cleanup operation
- **Reason:** Focus project on UC1-UC5 implementation
