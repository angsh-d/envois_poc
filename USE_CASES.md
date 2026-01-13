# Clinical Intelligence Platform - Use Cases
## H-34 DELTA Revision Cup Study - POC Use Case Specifications

**Version:** 1.0 | **Date:** January 11, 2026

---

# Multi-Source Architecture Overview

> **Core Principle:** Each use case leverages multiple data sources orchestrated through specialized AI agents. The architecture below shows how content flows from raw sources through aggregation, agent processing, and finally to user experience.

## System Architecture Visualization

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                  │
│                            CLINICAL INTELLIGENCE PLATFORM ARCHITECTURE                                          │
│                                                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                                    LAYER 1: CONTENT SOURCES                                                ║  │
│  ╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                                                            ║  │
│  ║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                ║  │
│  ║  │   STUDY      │  │   PROTOCOL   │  │  LITERATURE  │  │   REGISTRY   │  │     TMF      │                ║  │
│  ║  │   DATA       │  │   DOCUMENTS  │  │    PDFs      │  │    DATA      │  │  DOCUMENTS   │                ║  │
│  ║  │   (Excel)    │  │   (PDF)      │  │   (PDF)      │  │   (CSV/PDF)  │  │   (Mixed)    │                ║  │
│  ║  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤                ║  │
│  ║  │• Demographics│  │• CIP v2.0    │  │• Meding 2025 │  │• AOANJRR     │  │• EC Approvals│                ║  │
│  ║  │• HHS/OHS     │  │• SOA         │  │• Dixon 2025  │  │• NJR UK      │  │• PD Logs     │                ║  │
│  ║  │• Radiology   │  │• Endpoints   │  │• Harris 2025 │  │• EPRD        │  │• Site Docs   │                ║  │
│  ║  │• AEs/SAEs    │  │• I/E Rules   │  │• Vasios et al│  │              │  │• Training    │                ║  │
│  ║  │• Revisions   │  │• Safety Rules│  │• +12 more    │  │              │  │              │                ║  │
│  ║  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘                ║  │
│  ║          │                │                 │                │                │                            ║  │
│  ╚══════════╪════════════════╪═════════════════╪════════════════╪════════════════╪════════════════════════════╝  │
│             │                │                 │                │                │                               │
│             ▼                ▼                 ▼                ▼                ▼                               │
│  ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                              LAYER 2: DATA INGESTION & NORMALIZATION                                       ║  │
│  ╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                                                            ║  │
│  ║  ┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────────────────┐        ║  │
│  ║  │   STRUCTURED DATA LOADER    │  │    DOCUMENT PROCESSOR       │  │   BENCHMARK EXTRACTOR       │        ║  │
│  ║  ├─────────────────────────────┤  ├─────────────────────────────┤  ├─────────────────────────────┤        ║  │
│  ║  │ • Excel Parser (H34Loader)  │  │ • PDF Text Extraction       │  │ • Literature Benchmarks     │        ║  │
│  ║  │ • Schema Validation         │  │ • Table Detection           │  │ • Registry Norms            │        ║  │
│  ║  │ • Entity Resolution         │  │ • Section Chunking          │  │ • Survival Curves           │        ║  │
│  ║  │ • Temporal Alignment        │  │ • Metadata Tagging          │  │ • Risk Factor HRs           │        ║  │
│  ║  └─────────────────────────────┘  └─────────────────────────────┘  └─────────────────────────────┘        ║  │
│  ║                      │                         │                              │                            ║  │
│  ╚══════════════════════╪═════════════════════════╪══════════════════════════════╪════════════════════════════╝  │
│                         │                         │                              │                               │
│                         ▼                         ▼                              ▼                               │
│  ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                                LAYER 3: AGGREGATION & INDEXING                                             ║  │
│  ╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                                                            ║  │
│  ║  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐  ║  │
│  ║  │                                    UNIFIED DATA LAYER                                                │  ║  │
│  ║  ├─────────────────────────────────────────────────────────────────────────────────────────────────────┤  ║  │
│  ║  │                                                                                                      │  ║  │
│  ║  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │  ║  │
│  ║  │  │  VECTOR STORE   │    │ DOCUMENT-AS-CODE│    │  PATIENT GRAPH  │    │  TIME SERIES DB │          │  ║  │
│  ║  │  │  (ChromaDB)     │    │  (YAML Rules)   │    │  (Entity Links) │    │  (Outcomes)     │          │  ║  │
│  ║  │  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤          │  ║  │
│  ║  │  │ • Protocol RAG  │    │ • protocol_rules│    │ • Patient→Visit │    │ • HHS scores    │          │  ║  │
│  ║  │  │ • Literature RAG│    │ • lit_benchmarks│    │ • Visit→Forms   │    │ • OHS scores    │          │  ║  │
│  ║  │  │ • TMF RAG       │    │ • registry_norms│    │ • Patient→AEs   │    │ • Trajectories  │          │  ║  │
│  ║  │  │                 │    │                 │    │ • Patient→Device│    │                 │          │  ║  │
│  ║  │  └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘          │  ║  │
│  ║  │                                                                                                      │  ║  │
│  ║  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘  ║  │
│  ║                                                    │                                                       ║  │
│  ╚════════════════════════════════════════════════════╪═══════════════════════════════════════════════════════╝  │
│                                                       │                                                          │
│                                                       ▼                                                          │
│  ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                                   LAYER 4: AGENTIC AI ORCHESTRATION                                        ║  │
│  ╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                                                            ║  │
│  ║                              ┌─────────────────────────────────────┐                                       ║  │
│  ║                              │        ORCHESTRATOR AGENT           │                                       ║  │
│  ║                              │   (Query Understanding & Routing)   │                                       ║  │
│  ║                              └─────────────────┬───────────────────┘                                       ║  │
│  ║                                                │                                                            ║  │
│  ║            ┌───────────────┬───────────────────┼───────────────────┬───────────────┐                       ║  │
│  ║            │               │                   │                   │               │                       ║  │
│  ║            ▼               ▼                   ▼                   ▼               ▼                       ║  │
│  ║  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐      ║  │
│  ║  │   PROTOCOL      │ │     DATA        │ │   LITERATURE    │ │    SAFETY       │ │   COMPLIANCE    │      ║  │
│  ║  │   AGENT         │ │    AGENT        │ │    AGENT        │ │    AGENT        │ │    AGENT        │      ║  │
│  ║  ├─────────────────┤ ├─────────────────┤ ├─────────────────┤ ├─────────────────┤ ├─────────────────┤      ║  │
│  ║  │• Visit Windows  │ │• Query Study DB │ │• RAG Literature │ │• AE Analysis    │ │• Deviation Det. │      ║  │
│  ║  │• Endpoint Rules │ │• Compute Stats  │ │• Extract Bench  │ │• Signal Detect  │ │• Rule Validation│      ║  │
│  ║  │• I/E Criteria   │ │• Trajectories   │ │• Compare Rates  │ │• Risk Scoring   │ │• PD Classification│   ║  │
│  ║  │• Safety Thresh  │ │• Subgroups      │ │• Context HRs    │ │• Root Cause     │ │• Gap Analysis   │      ║  │
│  ║  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘      ║  │
│  ║            │               │                   │                   │               │                       ║  │
│  ║            └───────────────┴───────────────────┼───────────────────┴───────────────┘                       ║  │
│  ║                                                │                                                            ║  │
│  ║                              ┌─────────────────┴───────────────────┐                                       ║  │
│  ║                              │        SYNTHESIS AGENT              │                                       ║  │
│  ║                              │ (Combine Results, Generate Output)  │                                       ║  │
│  ║                              └─────────────────────────────────────┘                                       ║  │
│  ║                                                                                                            ║  │
│  ╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝  │
│                                                       │                                                          │
│                                                       ▼                                                          │
│  ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                                       LAYER 5: TOOLS & ANALYTICS                                           ║  │
│  ╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                                                            ║  │
│  ║  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────┐ ║  │
│  ║  │  STATISTICAL  │ │    ML/AI      │ │   SURVIVAL    │ │  TIME SERIES  │ │   REPORT      │ │  ALERT    │ ║  │
│  ║  │   TOOLS       │ │    TOOLS      │ │   ANALYSIS    │ │   TOOLS       │ │   GENERATOR   │ │  ENGINE   │ ║  │
│  ║  ├───────────────┤ ├───────────────┤ ├───────────────┤ ├───────────────┤ ├───────────────┤ ├───────────┤ ║  │
│  ║  │• Descriptive  │ │• XGBoost Risk │ │• Kaplan-Meier │ │• Prophet      │ │• PDF Export   │ │• Threshold│ ║  │
│  ║  │• Subgroup     │ │• Clustering   │ │• Cox PH       │ │• Trajectory   │ │• Excel Export │ │• Anomaly  │ ║  │
│  ║  │• Comparison   │ │• Anomaly Det. │ │• Risk Tables  │ │• Forecasting  │ │• Markdown     │ │• Scheduled│ ║  │
│  ║  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────┘ ║  │
│  ║                                                                                                            ║  │
│  ╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝  │
│                                                       │                                                          │
│                                                       ▼                                                          │
│  ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                                      LAYER 6: USER EXPERIENCE                                              ║  │
│  ╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                                                            ║  │
│  ║  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐  ║  │
│  ║  │                                                                                                      │  ║  │
│  ║  │   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐                       │  ║  │
│  ║  │   │   CHAT INTERFACE    │   │ EXECUTIVE DASHBOARD │   │   ALERT CENTER      │                       │  ║  │
│  ║  │   │   (Streamlit)       │   │   (Visualization)   │   │   (Notifications)   │                       │  ║  │
│  ║  │   ├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤                       │  ║  │
│  ║  │   │ • Natural Language  │   │ • Study Health KPIs │   │ • Safety Signals    │                       │  ║  │
│  ║  │   │ • Context Memory    │   │ • Enrollment Curves │   │ • Protocol Deviations│                      │  ║  │
│  ║  │   │ • Provenance Links  │   │ • Outcome Trends    │   │ • At-Risk Patients  │                       │  ║  │
│  ║  │   │ • Export Actions    │   │ • Benchmarking      │   │ • Action Items      │                       │  ║  │
│  ║  │   └─────────────────────┘   └─────────────────────┘   └─────────────────────┘                       │  ║  │
│  ║  │                                                                                                      │  ║  │
│  ║  │   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐                       │  ║  │
│  ║  │   │   REPORT BUILDER    │   │   PATIENT EXPLORER  │   │    API ACCESS       │                       │  ║  │
│  ║  │   │   (Templates)       │   │   (Individual View) │   │   (Integration)     │                       │  ║  │
│  ║  │   ├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤                       │  ║  │
│  ║  │   │ • Regulatory Ready  │   │ • Timeline View     │   │ • REST Endpoints    │                       │  ║  │
│  ║  │   │ • CSR Sections      │   │ • Risk Factors      │   │ • Webhook Alerts    │                       │  ║  │
│  ║  │   │ • Safety Narratives │   │ • Recommendations   │   │ • Batch Queries     │                       │  ║  │
│  ║  │   └─────────────────────┘   └─────────────────────┘   └─────────────────────┘                       │  ║  │
│  ║  │                                                                                                      │  ║  │
│  ║  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘  ║  │
│  ║                                                                                                            ║  │
│  ╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝  │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        DATA FLOW: QUERY TO INSIGHT                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│   USER QUERY                                                                                                     │
│   "Are we ready to submit? What gaps need to be addressed?"                                                     │
│       │                                                                                                          │
│       ▼                                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ ORCHESTRATOR: Parse intent → Identify required sources → Route to agents                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                                                          │
│       ├────────────────┬────────────────┬────────────────┬────────────────┐                                     │
│       ▼                ▼                ▼                ▼                ▼                                     │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐                                │
│   │ PROTOCOL   │  │   DATA     │  │ LITERATURE │  │  REGISTRY  │  │ COMPLIANCE │                                │
│   │ AGENT      │  │  AGENT     │  │  AGENT     │  │  AGENT     │  │  AGENT     │                                │
│   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                                │
│         │               │               │               │               │                                        │
│         ▼               ▼               ▼               ▼               ▼                                        │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐                                │
│   │ protocol_  │  │ H-34 Excel │  │ literature_│  │ registry_  │  │ Cross-check│                                │
│   │ rules.yaml │  │ (21 sheets)│  │ benchmarks │  │ norms.yaml │  │ all sources│                                │
│   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                                │
│         │               │               │               │               │                                        │
│         ▼               ▼               ▼               ▼               ▼                                        │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐                                │
│   │Requirements│  │Current     │  │Published   │  │Population  │  │Gap         │                                │
│   │extracted   │  │status      │  │benchmarks  │  │norms       │  │analysis    │                                │
│   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                                │
│         │               │               │               │               │                                        │
│         └───────────────┴───────────────┴───────────────┴───────────────┘                                        │
│                                         │                                                                        │
│                                         ▼                                                                        │
│                         ┌─────────────────────────────────────┐                                                  │
│                         │         SYNTHESIS AGENT              │                                                  │
│                         │  Combine all agent outputs into      │                                                  │
│                         │  unified response with provenance    │                                                  │
│                         └─────────────────────────────────────┘                                                  │
│                                         │                                                                        │
│                                         ▼                                                                        │
│                         ┌─────────────────────────────────────┐                                                  │
│                         │         STRUCTURED OUTPUT            │                                                  │
│                         │  • Readiness Score: 72%             │                                                  │
│                         │  • Blockers: 2 critical gaps        │                                                  │
│                         │  • Warnings: 2 items                │                                                  │
│                         │  • Timeline projection              │                                                  │
│                         │  • Action buttons                   │                                                  │
│                         │  • Full provenance trail            │                                                  │
│                         └─────────────────────────────────────┘                                                  │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Use Case Specifications

---

## UC1: Regulatory Submission Readiness Assessment

### Overview

| Attribute | Value |
|-----------|-------|
| **UC ID** | UC1 |
| **Name** | Regulatory Submission Readiness Assessment |
| **Category** | Compliance & Regulatory |
| **Trigger** | User query or scheduled assessment |
| **Complexity** | High (5 agents, 4+ data sources) |

### Business Problem

Clinical teams spend **3-5 days** manually cross-referencing protocol requirements, study data, literature benchmarks, and regulatory expectations to assess submission readiness. Gaps are discovered late, causing delays and rework.

### User Query Examples

- "Are we ready to submit? What gaps need to be addressed?"
- "What's our submission readiness status?"
- "Generate regulatory readiness report"

### Input Data Sources

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC1: INPUT DATA SOURCES                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 1: PROTOCOL (Document-as-Code)                                                                     │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: protocol_rules.yaml (extracted from CIP v2.0)                                                       │   │
│  │ Fields Used:                                                                                              │   │
│  │   • endpoints.primary.success_threshold → "20 points HHS improvement"                                     │   │
│  │   • schedule_of_assessments.visits[].required_assessments → Visit completion requirements                 │   │
│  │   • sample_size.interim → "n≥25 evaluable"                                                               │   │
│  │   • safety_requirements.sae_narrative → "All SAEs require narratives"                                    │   │
│  │   • radiographic_requirements → "All timepoints must have imaging review"                                │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 2: STUDY DATA (Structured)                                                                         │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: H-34DELTARevisionstudy_export_20250912.xlsx                                                         │   │
│  │ Sheets Used:                                                                                              │   │
│  │   • Sheet 1 (Patients) → Enrollment count, patient status                                                │   │
│  │   • Sheet 18 (Score HHS) → Primary endpoint data, MCID calculation                                        │   │
│  │   • Sheet 17 (Adverse Events) → Safety completeness, SAE narratives                                       │   │
│  │   • Sheets 7-16 (Follow-ups) → Visit completion, radiographic data availability                          │   │
│  │   • Sheet 20 (Explants) → Revision event counts                                                           │   │
│  │ Key Calculations:                                                                                         │   │
│  │   • Patients with 2-year HHS: 8/37                                                                        │   │
│  │   • MCID achieved: 5/8 (62%)                                                                              │   │
│  │   • SAEs with narratives: 12/12                                                                           │   │
│  │   • Missing radiographic: 3 patients at 1-year                                                            │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 3: LITERATURE BENCHMARKS (Document-as-Code)                                                        │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: literature_benchmarks.yaml                                                                          │   │
│  │ Publications Indexed:                                                                                     │   │
│  │   • Meding et al 2025 → mcid_achievement: 72%, revision_rate: 6.2%                                       │   │
│  │   • Vasios et al → hhs_improvement_range: [28, 42]                                                       │   │
│  │   • Dixon et al 2025 → Osteoporosis fracture risk HR: 2.4                                                │   │
│  │   • Harris et al 2025 → ae_rate_range: [28%, 40%]                                                        │   │
│  │ Comparison Points:                                                                                        │   │
│  │   • H-34 MCID 62% vs Literature 72% → Within acceptable range                                            │   │
│  │   • H-34 revision 8.1% vs Literature 6.2% → Upper boundary                                               │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 4: REGISTRY NORMS (Document-as-Code)                                                               │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: registry_norms.yaml                                                                                 │   │
│  │ Registries Indexed:                                                                                       │   │
│  │   • AOANJRR 2024 → survival_2yr: 94%, revision_rate_median: 6.2%, revision_rate_p95: 12%                 │   │
│  │   • NJR UK → Similar benchmarks for UK population                                                         │   │
│  │ Validation Points:                                                                                        │   │
│  │   • H-34 survival ~92% vs Registry 94% → Within CI                                                       │   │
│  │   • H-34 revision 8.1% vs Registry median 6.2% → Above median, below p95                                 │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Orchestration

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC1: AGENT ORCHESTRATION                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  STEP 1: PROTOCOL AGENT                                                     Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Load protocol_rules.yaml                                                                               │   │
│  │ • Extract submission requirements:                                                                        │   │
│  │   - Primary endpoint: HHS improvement ≥20 points at 2 years                                              │   │
│  │   - Sample size: n≥25 evaluable for interim, n=50 for final                                              │   │
│  │   - Safety: Complete AE documentation, SAE narratives                                                     │   │
│  │   - Radiographic: All timepoint imaging reviewed                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 2: DATA AGENT                                                         Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Query H-34 study database                                                                               │   │
│  │ • Calculate current status:                                                                               │   │
│  │   - Primary endpoint: 5/8 achieved MCID (62%), n=8 evaluable                                             │   │
│  │   - Safety: 15 AEs documented, 12 SAEs with narratives                                                    │   │
│  │   - Radiographic: 3 patients missing 1yr imaging                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 3: LITERATURE AGENT                                                   Execution: ~3 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Load literature_benchmarks.yaml                                                                         │   │
│  │ • Retrieve comparators:                                                                                   │   │
│  │   - Meding et al: 72% MCID (our 62% within range)                                                        │   │
│  │   - Revision rate benchmark: 6.2% (our 8.1% at upper boundary)                                            │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 4: REGISTRY AGENT                                                     Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Load registry_norms.yaml                                                                                │   │
│  │ • External validation:                                                                                    │   │
│  │   - AOANJRR 2yr survival: 94% (our ~92% within CI)                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 5: COMPLIANCE AGENT                                                   Execution: ~8 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Cross-reference all sources                                                                             │   │
│  │ • Generate gap analysis:                                                                                  │   │
│  │   - Protocol vs Data: Sample size gap, radiographic gaps                                                  │   │
│  │   - Literature comparison: Performance validation                                                         │   │
│  │   - Registry validation: External benchmarking                                                            │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 6: SYNTHESIS AGENT                                                    Execution: ~10 seconds             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Combine all agent outputs                                                                               │   │
│  │ • Generate structured report with:                                                                        │   │
│  │   - Overall readiness score                                                                               │   │
│  │   - Category-by-category status                                                                           │   │
│  │   - Blockers and warnings                                                                                 │   │
│  │   - Timeline projection                                                                                   │   │
│  │   - Action buttons                                                                                        │   │
│  │   - Complete provenance                                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  TOTAL EXECUTION TIME: <30 seconds                                                                              │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Output Specification

| Output Element | Description | Format |
|----------------|-------------|--------|
| Readiness Score | Overall percentage (0-100%) | Progress bar + number |
| Category Status | Pass/Gap/Watch per requirement | Table with icons |
| Blockers | Critical items preventing submission | Numbered list |
| Warnings | Items needing attention | Numbered list |
| Timeline | Projected path to readiness | Timeline visualization |
| Actions | One-click action buttons | Button array |
| Provenance | Source citations for every finding | Footer text |

### Value Delivered

| Metric | Traditional | With Platform |
|--------|-------------|---------------|
| Time to assess | 3-5 days | 30 seconds |
| Sources consulted | Manual cross-reference | 4 sources automated |
| Gap detection | Often late discovery | Real-time identification |
| Actionability | Data only | Specific remediation steps |

---

## UC2: Safety Signal Detection & Contextualization

### Overview

| Attribute | Value |
|-----------|-------|
| **UC ID** | UC2 |
| **Name** | Safety Signal Detection & Contextualization |
| **Category** | Safety & Vigilance |
| **Trigger** | Proactive (data refresh) or user query |
| **Complexity** | High (5 agents, 5+ data sources) |

### Business Problem

Safety signals in small studies are hard to interpret without external context. A 13% fracture rate looks concerning in isolation, but teams must manually search literature and registries to determine if it's actually elevated or expected for the patient population.

### User Query Examples

- "Are there any safety concerns I should know about?"
- "Analyze our AE rates compared to published data"
- "Is our fracture rate concerning?"
- **PROACTIVE:** System alerts without user query

### Input Data Sources

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC2: INPUT DATA SOURCES                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 1: ADVERSE EVENTS (Structured)                                                                     │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: H-34DELTARevisionstudy_export_20250912.xlsx → Sheet 17 (Adverse Events)                            │   │
│  │ Fields Used:                                                                                              │   │
│  │   • AE Term → "Periprosthetic fracture", "Dislocation", "Infection", etc.                                │   │
│  │   • Seriousness → SAE/Non-SAE classification                                                              │   │
│  │   • Device Relationship → Related/Not related determination                                               │   │
│  │   • Onset Date → Timing correlation with surgery                                                          │   │
│  │   • Patient ID → Link to demographics and outcomes                                                        │   │
│  │ Key Calculations:                                                                                         │   │
│  │   • Fracture rate: 5/37 (13%)                                                                             │   │
│  │   • Dislocation rate: 2/37 (5%)                                                                           │   │
│  │   • Infection rate: 1/37 (3%)                                                                             │   │
│  │   • Overall AE rate: 13/37 (35%)                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 2: PATIENT DEMOGRAPHICS (Structured)                                                               │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: H-34DELTARevisionstudy_export_20250912.xlsx → Sheet 1 (Patients), Sheet 2 (Preoperatives)          │   │
│  │ Fields Used:                                                                                              │   │
│  │   • Age, Gender, BMI → Risk factor analysis                                                               │   │
│  │   • Primary Diagnosis → Underlying condition                                                              │   │
│  │   • Comorbidities → Osteoporosis, diabetes, etc.                                                          │   │
│  │ Key Findings:                                                                                             │   │
│  │   • Osteoporosis prevalence: 12/37 (32%)                                                                  │   │
│  │   • Fractures in osteoporotic patients: 5/5 (100%)                                                        │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 3: LITERATURE (RAG + Document-as-Code)                                                             │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Files: 12 indexed PDFs + literature_benchmarks.yaml                                                       │   │
│  │ Key Publications:                                                                                         │   │
│  │   • Dixon et al 2025 → Osteoporosis as primary fracture risk factor, expected rate 15-20% in osteoporotic│   │
│  │   • Harris et al 2025 → AE rate benchmarks 28-40%                                                        │   │
│  │   • Meding et al 2025 → Overall fracture rate in non-osteoporotic: 4-8%                                  │   │
│  │ Risk Factor Extraction:                                                                                   │   │
│  │   • Osteoporosis HR for fracture: 2.4 (Dixon)                                                            │   │
│  │   • Expected fracture rate with 32% osteoporosis prevalence: 10-15%                                      │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 4: REGISTRY NORMS (Document-as-Code)                                                               │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: registry_norms.yaml                                                                                 │   │
│  │ Benchmarks Used:                                                                                          │   │
│  │   • AOANJRR fracture rate threshold: >10% triggers concern                                               │   │
│  │   • Risk-adjusted expectation for high-osteoporosis cohort: 10-15%                                       │   │
│  │   • H-34 rate (13%) within risk-adjusted expectation                                                     │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 5: PROTOCOL (Document-as-Code)                                                                     │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: protocol_rules.yaml (extracted from CIP v2.0)                                                       │   │
│  │ Relevant Sections:                                                                                        │   │
│  │   • Section 5.2 I/E Criteria → Osteoporosis NOT an exclusion criterion                                   │   │
│  │   • Section 9.1 Safety → SAE reporting requirements                                                       │   │
│  │   • Safety thresholds → fracture_rate_concern: 0.08 (8%)                                                 │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Orchestration

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC2: AGENT ORCHESTRATION                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  TRIGGER: Data refresh OR user query OR scheduled surveillance                                                  │
│                                                                                                                  │
│  STEP 1: SAFETY AGENT                                                       Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Scan AE table for rate anomalies                                                                        │   │
│  │ • Calculate event rates by type                                                                           │   │
│  │ • Compare to protocol safety thresholds                                                                   │   │
│  │ • Identify: Fracture rate 13% > threshold 8%  → SIGNAL DETECTED                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 2: DATA AGENT                                                         Execution: ~3 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Cross-reference AEs with patient characteristics                                                        │   │
│  │ • Pattern analysis:                                                                                       │   │
│  │   - 4/5 fractures within 90 days (early postop)                                                          │   │
│  │   - 5/5 fractures in osteoporotic patients (100% correlation)                                            │   │
│  │ • Temporal clustering identified                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 3: LITERATURE AGENT                                                   Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • RAG query: "fracture risk osteoporosis revision THA"                                                    │   │
│  │ • Retrieve:                                                                                               │   │
│  │   - Dixon et al: Osteoporosis primary risk factor                                                        │   │
│  │   - Expected rate in osteoporotic: 15-20%                                                                │   │
│  │   - Non-osteoporotic expected: 4-8%                                                                      │   │
│  │ • Context: H-34 32% osteoporosis is higher than typical                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 4: REGISTRY AGENT                                                     Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Load registry_norms.yaml                                                                                │   │
│  │ • Risk-adjusted benchmark:                                                                                │   │
│  │   - Overall threshold: >10%                                                                              │   │
│  │   - High-osteoporosis cohort expectation: 10-15%                                                         │   │
│  │   - H-34 13% WITHIN risk-adjusted expectation                                                            │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 5: PROTOCOL AGENT                                                     Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Check I/E criteria: Osteoporosis not excluded                                                          │   │
│  │ • Check monitoring protocol: No enhanced bone quality protocol specified                                  │   │
│  │ • Identify protocol gap for future consideration                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 6: SYNTHESIS AGENT                                                    Execution: ~8 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Combine all findings                                                                                    │   │
│  │ • Generate interpretation:                                                                                │   │
│  │   - CONCLUSION: Signal EXPLAINED by population characteristics                                           │   │
│  │   - NOT indicative of device defect                                                                      │   │
│  │   - Rate within literature-predicted range for risk profile                                              │   │
│  │ • Generate actionable recommendations                                                                     │   │
│  │ • Complete provenance trail                                                                               │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  TOTAL EXECUTION TIME: <25 seconds                                                                              │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Output Specification

| Output Element | Description | Format |
|----------------|-------------|--------|
| Signal Identification | Rate comparison table | Table with status icons |
| Cross-Source Context | Evidence from each source | Bulleted sections |
| Interpretation | High-confidence conclusion | Boxed summary |
| Regulatory Implication | Documentation requirements | Text paragraph |
| Recommended Actions | Specific next steps with buttons | Action button array |
| Provenance | All sources cited | Footer citations |

### Value Delivered

| Metric | Traditional | With Platform |
|--------|-------------|---------------|
| Signal detection | Manual monitoring | Automated on data refresh |
| Context gathering | Weeks of research | 25 seconds |
| Interpretation | Subjective clinical judgment | Evidence-based, multi-source |
| Recommendations | Generic | Specific, actionable |

---

## UC3: Automated Protocol Deviation Detection & Classification

### Overview

| Attribute | Value |
|-----------|-------|
| **UC ID** | UC3 |
| **Name** | Automated Protocol Deviation Detection & Classification |
| **Category** | Compliance & Quality |
| **Trigger** | Automatic on data refresh |
| **Complexity** | Medium (3 agents, 2+ data sources) |

### Business Problem

Protocol deviations are identified manually by comparing visit dates to protocol windows—a tedious, error-prone process often discovered late during monitoring visits. This delays corrective action and increases regulatory risk.

### User Query Examples

- "What protocol deviations exist in our data?"
- "Show me patients outside their visit windows"
- "Generate protocol deviation report"
- **AUTOMATIC:** Runs on every data refresh

### Input Data Sources

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC3: INPUT DATA SOURCES                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 1: PROTOCOL RULES (Document-as-Code) — PRIMARY                                                     │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: protocol_rules.yaml (extracted from CIP v2.0 Section 6.2, 7.2)                                      │   │
│  │                                                                                                           │   │
│  │ Visit Window Rules:                                                                                       │   │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐    │   │
│  │   │ Visit        │ Target Day │ Window         │ Required Assessments                               │    │   │
│  │   ├──────────────┼────────────┼────────────────┼────────────────────────────────────────────────────┤    │   │
│  │   │ 2-Month      │ Day 60     │ [-14, +28]     │ HHS, OHS, Radiology, AE Review                     │    │   │
│  │   │ 6-Month      │ Day 180    │ [-30, +30]     │ HHS, OHS, Radiology, AE Review                     │    │   │
│  │   │ 1-Year       │ Day 365    │ [-30, +60]     │ HHS, OHS, Radiology, AE Review                     │    │   │
│  │   │ 2-Year       │ Day 730    │ [-60, +60]     │ HHS, OHS, Radiology, AE Review (Primary Endpoint)  │    │   │
│  │   └─────────────────────────────────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                                                           │   │
│  │ Deviation Classification Rules (Section 7.2):                                                            │   │
│  │   • MINOR: Within 1.5x window extension                                                                  │   │
│  │   • MAJOR: Beyond 1.5x window OR missing critical assessment                                             │   │
│  │   • CRITICAL: Affects primary endpoint evaluability                                                      │   │
│  │                                                                                                           │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 2: VISIT DATA (Structured)                                                                         │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: H-34DELTARevisionstudy_export_20250912.xlsx                                                         │   │
│  │ Sheets Used:                                                                                              │   │
│  │   • Sheet 4 (Intraoperatives) → Surgery dates (Day 0 reference)                                          │   │
│  │   • Sheets 7-16 (Follow-ups) → Actual visit dates by timepoint                                           │   │
│  │   • Sheet 18 (Score HHS) → Assessment completion                                                          │   │
│  │   • Sheet 19 (Score OHS) → Assessment completion                                                          │   │
│  │   • Radiology sheets → Imaging completion                                                                 │   │
│  │                                                                                                           │   │
│  │ Data Points Per Patient:                                                                                  │   │
│  │   • Surgery date → Reference point                                                                        │   │
│  │   • Visit date per timepoint → Actual vs expected                                                        │   │
│  │   • Assessment completion flags → Form presence check                                                     │   │
│  │                                                                                                           │   │
│  │ Calculation Example (Patient 15):                                                                         │   │
│  │   • Surgery: Sep 15, 2024                                                                                │   │
│  │   • Expected 6mo: Mar 15, 2025 (Day 180) ± 30 days                                                       │   │
│  │   • Window: Feb 13 - Apr 14, 2025                                                                        │   │
│  │   • Actual: Apr 22, 2025 → +38 days outside window → MINOR deviation                                     │   │
│  │                                                                                                           │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Orchestration

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC3: AGENT ORCHESTRATION                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  EXECUTION: Automatic on data refresh (batch processing)                                                        │
│                                                                                                                  │
│  STEP 1: PROTOCOL AGENT                                                     Execution: ~1 second               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Load protocol_rules.yaml                                                                               │   │
│  │ • Initialize visit window validators                                                                      │   │
│  │ • Initialize deviation classifiers                                                                        │   │
│  │ • Initialize required assessment checkers                                                                 │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 2: DATA AGENT (Batch Processing)                                      Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ FOR EACH patient (n=37):                                                                                  │   │
│  │   FOR EACH expected visit (4 timepoints):                                                                │   │
│  │     1. Get surgery date (Day 0)                                                                          │   │
│  │     2. Calculate expected visit date                                                                      │   │
│  │     3. Calculate window boundaries                                                                        │   │
│  │     4. Get actual visit date (if exists)                                                                 │   │
│  │     5. Calculate delta days                                                                               │   │
│  │     6. Check required assessments                                                                         │   │
│  │                                                                                                           │   │
│  │ Total evaluations: 37 patients × 4 visits = 148 visit-assessments                                        │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 3: COMPLIANCE AGENT                                                   Execution: ~3 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ FOR EACH visit-assessment:                                                                               │   │
│  │   1. Apply deviation classification rules                                                                 │   │
│  │   2. Determine severity: MINOR / MAJOR / CRITICAL                                                        │   │
│  │   3. Assess impact on endpoint evaluability                                                               │   │
│  │   4. Generate PD log entry (pre-populated)                                                               │   │
│  │                                                                                                           │   │
│  │ Results:                                                                                                  │   │
│  │   • 142 compliant visit-assessments                                                                      │   │
│  │   • 6 deviations detected (4.1% rate)                                                                    │   │
│  │     - 3 MINOR (timing within extended window)                                                            │   │
│  │     - 2 MAJOR (outside window or missing visit)                                                          │   │
│  │     - 1 CRITICAL (affects primary endpoint)                                                              │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 4: OUTPUT GENERATION                                                  Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ Generate automated outputs:                                                                               │   │
│  │   ✅ PD Log entries pre-populated (requires PI signature)                                                │   │
│  │   ✅ Site query forms generated for MAJOR/CRITICAL                                                       │   │
│  │   ✅ CSR deviation table updated                                                                          │   │
│  │   ✅ Monitoring visit agenda updated                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  TOTAL EXECUTION TIME: ~11 seconds (batch for all 37 patients)                                                 │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Output Specification

| Output Element | Description | Format |
|----------------|-------------|--------|
| Summary Statistics | Total evaluations, deviation count, rate | Header text |
| Deviation Detail Table | Patient, visit, expected, actual, delta, class, impact | Sortable table |
| Deviation Breakdown | Count by severity category | Summary list |
| Auto-Generated Outputs | PD log, queries, CSR table | Status checklist |
| Action Buttons | Download, send queries, update CSR, trends | Button array |
| Provenance | Protocol sections, data sheets | Footer citations |

### Value Delivered

| Metric | Traditional | With Platform |
|--------|-------------|---------------|
| Detection timing | Monitoring visits (months) | Real-time (seconds) |
| Time per patient | 15-30 minutes | <1 second |
| Classification accuracy | Human interpretation | Protocol-defined rules |
| Documentation | Manual transcription | Auto-generated |

---

## UC4: Patient Risk Stratification with Actionable Monitoring Lists

### Overview

| Attribute | Value |
|-----------|-------|
| **UC ID** | UC4 |
| **Name** | Patient Risk Stratification with Actionable Monitoring Lists |
| **Category** | Clinical Decision Support |
| **Trigger** | User query or scheduled refresh |
| **Complexity** | High (4 models, 4+ data sources) |

### Business Problem

Without predictive tools, all patients receive the same monitoring attention. This wastes resources on low-risk patients while potentially missing early warning signs in high-risk patients who need enhanced surveillance.

### User Query Examples

- "Which patients should I be most concerned about?"
- "Who needs enhanced monitoring?"
- "Generate prioritized patient list"
- "What are the highest risk patients?"

### Input Data Sources

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC4: INPUT DATA SOURCES                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 1: ML RISK MODEL (Trained on Synthetic + Real Data)                                                │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Model: XGBoost Revision Risk Classifier                                                                   │   │
│  │ Training Data: 737 patients (37 real + 700 synthetic)                                                    │   │
│  │ Events: 60 revision events (sufficient for ML training)                                                   │   │
│  │                                                                                                           │   │
│  │ Input Features:                                                                                           │   │
│  │   • Demographics: Age, Gender, BMI                                                                        │   │
│  │   • Clinical: Baseline HHS, Diagnosis, Comorbidities                                                     │   │
│  │   • Trajectory: HHS slope, recovery pattern cluster                                                       │   │
│  │   • Radiographic: Lucency scores, bone quality                                                           │   │
│  │   • Compliance: Visit adherence, deviation count                                                          │   │
│  │                                                                                                           │   │
│  │ Output: Probability of revision within 2 years (0-100%)                                                  │   │
│  │ Validation: Cross-validated on synthetic, calibrated to real                                             │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 2: LITERATURE HAZARD RATIOS (Document-as-Code)                                                     │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: literature_benchmarks.yaml                                                                          │   │
│  │                                                                                                           │   │
│  │ Risk Factor Hazard Ratios:                                                                                │   │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐    │   │
│  │   │ Risk Factor              │ HR    │ Source              │ Application                           │    │   │
│  │   ├──────────────────────────┼───────┼─────────────────────┼───────────────────────────────────────┤    │   │
│  │   │ Osteoporosis             │ 2.4   │ Dixon et al 2025    │ Fracture/revision risk multiplier     │    │   │
│  │   │ BMI > 35                 │ 1.6   │ AOANJRR 2024        │ Mechanical failure risk               │    │   │
│  │   │ Age > 75                 │ 1.4   │ Harris et al 2025   │ Complication risk                     │    │   │
│  │   │ Prior revision           │ 2.1   │ Meding et al 2025   │ Re-revision risk                      │    │   │
│  │   │ Baseline HHS < 30        │ 1.8   │ Vasios et al        │ Poor recovery predictor               │    │   │
│  │   └─────────────────────────────────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                                                           │   │
│  │ Applied as: Risk score = Baseline × Π(HR for each present factor)                                        │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 3: REGISTRY BENCHMARKS (Document-as-Code)                                                          │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: registry_norms.yaml                                                                                 │   │
│  │                                                                                                           │   │
│  │ Population Norms:                                                                                         │   │
│  │   • Base revision risk (cohort average): 8%                                                              │   │
│  │   • Risk-adjusted thresholds by factor count                                                             │   │
│  │   • Survival curve percentiles for comparison                                                             │   │
│  │                                                                                                           │   │
│  │ Risk Thresholds:                                                                                          │   │
│  │   • LOW: <10% (standard protocol)                                                                        │   │
│  │   • MODERATE: 10-20% (enhanced monitoring)                                                               │   │
│  │   • HIGH: >20% (intensive surveillance)                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 4: STUDY DATA (Structured)                                                                         │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: H-34DELTARevisionstudy_export_20250912.xlsx                                                         │   │
│  │                                                                                                           │   │
│  │ Sheets Used:                                                                                              │   │
│  │   • Sheet 1 (Patients) → Demographics, BMI                                                               │   │
│  │   • Sheet 2 (Preoperatives) → Diagnosis, comorbidities, prior surgeries                                  │   │
│  │   • Sheet 18 (Score HHS) → Baseline scores, trajectories                                                 │   │
│  │   • Radiology sheets → Bone quality, lucency findings                                                    │   │
│  │   • Sheet 17 (AEs) → Complication history                                                                │   │
│  │                                                                                                           │   │
│  │ Derived Features:                                                                                         │   │
│  │   • HHS trajectory slope (improvement rate)                                                               │   │
│  │   • Recovery cluster assignment (K-Means on trajectories)                                                │   │
│  │   • Protocol compliance score                                                                             │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 5: PROTOCOL COMPLIANCE (Document-as-Code)                                                          │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Derived from UC3 output:                                                                                  │   │
│  │   • Deviation count per patient                                                                           │   │
│  │   • Deviation severity accumulation                                                                       │   │
│  │   • Visit adherence rate                                                                                  │   │
│  │                                                                                                           │   │
│  │ Compliance Score = f(deviation count, severity, missed visits)                                           │   │
│  │ Low compliance correlates with poor outcomes and loss to follow-up risk                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Orchestration

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC4: AGENT ORCHESTRATION                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  MULTI-MODEL ENSEMBLE APPROACH                                                                                  │
│                                                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                  MODEL ARCHITECTURE                                                      │   │
│  │                                                                                                          │   │
│  │   Patient Data ──┬──► Model 1: ML Revision Risk (XGBoost) ──────────────┐                              │   │
│  │                  │                                                       │                              │   │
│  │                  ├──► Model 2: Literature HR Score ──────────────────────┼──► Weighted Ensemble        │   │
│  │                  │                                                       │    Score (0-100%)            │   │
│  │                  ├──► Model 3: Registry Benchmark Comparison ────────────┤                              │   │
│  │                  │                                                       │                              │   │
│  │                  └──► Model 4: Protocol Compliance Score ────────────────┘                              │   │
│  │                                                                                                          │   │
│  │   Final Score = w1×ML + w2×Literature + w3×Registry + w4×Compliance                                     │   │
│  │   Weights calibrated to maximize discrimination while maintaining explainability                        │   │
│  │                                                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 1: DATA AGENT (Feature Assembly)                                      Execution: ~3 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ FOR EACH patient (n=37):                                                                                  │   │
│  │   • Gather demographics, clinical history                                                                │   │
│  │   • Calculate HHS trajectory features                                                                     │   │
│  │   • Aggregate radiographic findings                                                                       │   │
│  │   • Retrieve compliance score from UC3                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 2: ML SCORING (Parallel Execution)                                    Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ Model 1: XGBoost prediction for each patient                                                              │   │
│  │ Model 2: Literature HR multiplication for each patient                                                    │   │
│  │ Model 3: Registry percentile lookup for each patient                                                      │   │
│  │ Model 4: Compliance score retrieval                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 3: ENSEMBLE & UNCERTAINTY                                             Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Combine model outputs with weighted ensemble                                                            │   │
│  │ • Calculate prediction interval (uncertainty quantification)                                              │   │
│  │ • Assign risk tier: HIGH / MODERATE / LOW                                                                │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 4: EXPLAINABILITY AGENT                                               Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ FOR EACH high-risk patient:                                                                               │   │
│  │   • Generate SHAP-like factor contribution breakdown                                                      │   │
│  │   • Link each factor to source (ML, literature, registry)                                                │   │
│  │   • Generate specific monitoring recommendation                                                           │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 5: OUTPUT GENERATION                                                  Execution: ~3 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Generate prioritized patient list by risk tier                                                         │   │
│  │ • Detailed risk factor breakdown for HIGH priority                                                        │   │
│  │ • Specific action recommendations per patient                                                             │   │
│  │ • Confidence scores and provenance                                                                        │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  TOTAL EXECUTION TIME: ~18 seconds                                                                              │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Output Specification

| Output Element | Description | Format |
|----------------|-------------|--------|
| High Priority List | Patients >20% risk with details | Detailed table |
| Moderate Priority List | Patients 10-20% risk | Collapsible list |
| Low Priority List | Patients <10% risk | Summary count |
| Factor Contribution | Visual breakdown per patient | Waterfall chart |
| Confidence Score | Model reliability indicator | Percentage |
| Recommendations | Specific actions per patient | Action text |
| Action Buttons | Generate protocol, email site, schedule | Button array |

### Value Delivered

| Metric | Traditional | With Platform |
|--------|-------------|---------------|
| Prioritization method | Subjective judgment | Multi-model ensemble |
| Explainability | "Clinical intuition" | Factor-by-factor breakdown |
| Resource allocation | Uniform attention | Risk-stratified focus |
| Early intervention | Often too late | Proactive identification |

---

## UC5: Intelligent Study Health Executive Dashboard

### Overview

| Attribute | Value |
|-----------|-------|
| **UC ID** | UC5 |
| **Name** | Intelligent Study Health Executive Dashboard |
| **Category** | Executive Decision Support |
| **Trigger** | Real-time (auto-refresh) or on-demand |
| **Complexity** | High (aggregates all agents, 6+ data sources) |

### Business Problem

Executives need a single view of study status, but information is scattered across data exports, protocol documents, safety databases, and regulatory trackers. Preparing a status update takes days of manual synthesis.

### User Query Examples

- "Give me the executive summary"
- "What's the overall study status?"
- "Prepare a board presentation"
- **AUTOMATIC:** Dashboard updates on data refresh

### Input Data Sources

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC5: INPUT DATA SOURCES                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  This use case AGGREGATES outputs from UC1-UC4 plus additional sources:                                         │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 1: UC1 OUTPUT — Regulatory Readiness                                                               │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Feeds:                                                                                                    │   │
│  │   • Overall readiness score (72%)                                                                         │   │
│  │   • Blocker count (2 critical)                                                                            │   │
│  │   • Timeline projection                                                                                   │   │
│  │   • Category status breakdown                                                                             │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 2: UC2 OUTPUT — Safety Signal Summary                                                              │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Feeds:                                                                                                    │   │
│  │   • Active signals (fracture rate monitored)                                                              │   │
│  │   • Signal status (explained by population)                                                               │   │
│  │   • Required actions                                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 3: UC3 OUTPUT — Protocol Compliance                                                                │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Feeds:                                                                                                    │   │
│  │   • Compliance rate (96%)                                                                                 │   │
│  │   • Deviation count by severity                                                                           │   │
│  │   • SAE reporting compliance                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 4: UC4 OUTPUT — At-Risk Patient Summary                                                            │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Feeds:                                                                                                    │   │
│  │   • High-risk patient count (4)                                                                           │   │
│  │   • Patients overdue for follow-up (7)                                                                    │   │
│  │   • Retention risk assessment                                                                             │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 5: STUDY DATA — Enrollment & Efficacy (Direct)                                                     │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ File: H-34DELTARevisionstudy_export_20250912.xlsx                                                         │   │
│  │ Feeds:                                                                                                    │   │
│  │   • Enrollment: 37/50 (74%)                                                                               │   │
│  │   • Efficacy: 62% MCID achieved (n=8)                                                                    │   │
│  │   • Data quality: 87% (23 queries open, 3 critical)                                                      │   │
│  │   • Mean HHS improvement: +34.9 points                                                                   │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 6: LITERATURE + REGISTRY — External Benchmarking                                                   │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Files: literature_benchmarks.yaml, registry_norms.yaml                                                    │   │
│  │ Feeds:                                                                                                    │   │
│  │   • HHS improvement comparison: H-34 +34.9 vs Literature +28-45 vs Registry +32                          │   │
│  │   • MCID comparison: H-34 62% vs Literature 60-80% vs Registry 68%                                       │   │
│  │   • Revision rate: H-34 8.1% vs Literature 5-8% vs Registry 6.2%                                         │   │
│  │   • AE rate: H-34 35% vs Literature 28-40% vs Registry 35%                                               │   │
│  │   • 2yr survival: H-34 92% vs Literature 90-96% vs Registry 94%                                          │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SOURCE 7: TMF/REGULATORY STATUS (When Available)                                                          │   │
│  ├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Files: EC approval documents, prior reports                                                               │   │
│  │ Feeds:                                                                                                    │   │
│  │   • Regulatory approval status                                                                            │   │
│  │   • Prior report references (Intermediate Report Dec 2023)                                               │   │
│  │   • Milestone tracking                                                                                    │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Orchestration

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   UC5: AGENT ORCHESTRATION                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  AGGREGATION ARCHITECTURE                                                                                       │
│                                                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                                                          │   │
│  │   UC1 Output ─────┐                                                                                     │   │
│  │                   │                                                                                     │   │
│  │   UC2 Output ─────┼────► DASHBOARD AGGREGATION AGENT ────► EXECUTIVE DASHBOARD                         │   │
│  │                   │                                                                                     │   │
│  │   UC3 Output ─────┤      • Synthesize KPIs                                                              │   │
│  │                   │      • Identify top priorities                                                       │   │
│  │   UC4 Output ─────┤      • Generate attention items                                                      │   │
│  │                   │      • Compile benchmarking table                                                    │   │
│  │   Direct Data ────┤      • Project timeline                                                              │   │
│  │                   │      • Format for executive view                                                     │   │
│  │   Benchmarks ─────┘                                                                                     │   │
│  │                                                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 1: COLLECT UC OUTPUTS (Cached or Fresh)                               Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Retrieve latest UC1 readiness assessment                                                               │   │
│  │ • Retrieve latest UC2 safety signal summary                                                              │   │
│  │ • Retrieve latest UC3 compliance report                                                                  │   │
│  │ • Retrieve latest UC4 risk stratification                                                                │   │
│  │ Note: If cached results are stale, trigger fresh execution                                               │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 2: DIRECT DATA QUERIES                                                Execution: ~3 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Enrollment status: 37/50                                                                               │   │
│  │ • Efficacy summary: 62% MCID, +34.9 mean improvement                                                     │   │
│  │ • Data quality metrics: 87%, 23 queries, 3 critical                                                      │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 3: BENCHMARK COMPARISON                                               Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Load literature_benchmarks.yaml                                                                        │   │
│  │ • Load registry_norms.yaml                                                                               │   │
│  │ • Generate comparison table with status indicators                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 4: PRIORITY SYNTHESIS                                                 Execution: ~5 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Rank issues by impact and urgency                                                                      │   │
│  │ • Generate "Attention Required" list (top 3-5 items)                                                     │   │
│  │ • Cross-reference sources for each item                                                                  │   │
│  │ • Assign action recommendations                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 5: TIMELINE PROJECTION                                                Execution: ~3 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Current milestone: Q1 2026                                                                             │   │
│  │ • Project future milestones based on enrollment rate                                                     │   │
│  │ • Identify risks to timeline                                                                             │   │
│  │ • Generate visual timeline                                                                               │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  STEP 6: DASHBOARD RENDERING                                                Execution: ~2 seconds              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ • Overall health score calculation                                                                       │   │
│  │ • KPI progress bars                                                                                      │   │
│  │ • Attention items with source attribution                                                                │   │
│  │ • Benchmarking table                                                                                     │   │
│  │ • Timeline visualization                                                                                 │   │
│  │ • Export action buttons                                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                  │
│  TOTAL EXECUTION TIME: ~20 seconds (full refresh) or ~5 seconds (cached)                                       │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Output Specification

| Output Element | Description | Format |
|----------------|-------------|--------|
| Overall Health Score | Composite 0-100 with trend | Score + progress bar |
| KPI Summary | Enrollment, Efficacy, Safety, Compliance, Quality | Icon + progress bars |
| Attention Required | Top 3-5 prioritized issues | Numbered list with actions |
| Benchmarking Table | H-34 vs Literature vs Registry | Comparison table |
| Regulatory Timeline | Milestone projection | Timeline visual |
| Export Actions | PDF, presentation, drill-down | Button array |
| Provenance Summary | Data currency timestamp | Footer |

### Value Delivered

| Metric | Traditional | With Platform |
|--------|-------------|---------------|
| Time to prepare | 2-3 days | 20 seconds |
| Data sources synthesized | Manual aggregation | 6+ automated |
| Currency | Point-in-time snapshot | Real-time refresh |
| Benchmarking | Manual literature search | Automated comparison |
| Actionability | Status report only | Prioritized action items |

---

# Summary: Use Case Data Source Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              USE CASE → DATA SOURCE DEPENDENCY MATRIX                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│                              UC1      UC2      UC3      UC4      UC5                                            │
│  DATA SOURCE                Readiness Safety   Deviation Risk    Dashboard                                       │
│  ──────────────────────────────────────────────────────────────────────────                                     │
│  Study Data (Excel)           ●        ●        ●        ●        ●                                             │
│  Protocol Rules (YAML)        ●        ●        ●        ○        ●                                             │
│  Literature Benchmarks        ●        ●        ○        ●        ●                                             │
│  Registry Norms               ●        ●        ○        ●        ●                                             │
│  ML Risk Model                ○        ○        ○        ●        ○                                             │
│  UC1-UC4 Outputs              ○        ○        ○        ○        ●                                             │
│  TMF Documents                ○        ○        ○        ○        ○                                             │
│                                                                                                                  │
│  Legend: ● = Primary source | ○ = Optional/indirect                                                             │
│                                                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                    AGENTS PER USE CASE                                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  UC1: Protocol Agent → Data Agent → Literature Agent → Registry Agent → Compliance Agent → Synthesis           │
│  UC2: Safety Agent → Data Agent → Literature Agent → Registry Agent → Protocol Agent → Synthesis               │
│  UC3: Protocol Agent → Data Agent → Compliance Agent → Output Generation                                        │
│  UC4: Data Agent → ML Scoring (4 models) → Explainability Agent → Output Generation                            │
│  UC5: Aggregation Agent (UC1-4 outputs) → Direct Query → Benchmark Compare → Priority Synthesis → Render       │
│                                                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                    EXECUTION TIMES                                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                  │
│  UC1: ~30 seconds    | UC2: ~25 seconds    | UC3: ~11 seconds                                                   │
│  UC4: ~18 seconds    | UC5: ~20 seconds (full) / ~5 seconds (cached)                                           │
│                                                                                                                  │
│  Traditional manual approach: Days to weeks                                                                     │
│                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Appendix: Document-as-Code File Specifications

## protocol_rules.yaml

```yaml
# Source: CIP_H-34_v.2.0.pdf
# Extraction Method: LLM-assisted structured extraction
# Last Updated: 2026-01-11

protocol:
  id: "H-34"
  version: "2.0"
  title: "DELTA Revision Cup Clinical Investigation"

schedule_of_assessments:
  visits:
    - id: "fu_2mo"
      day_offset: 60
      window: [-14, +28]
      required_assessments: ["hhs", "ohs", "radiology", "ae_review"]
    - id: "fu_6mo"
      day_offset: 180
      window: [-30, +30]
      required_assessments: ["hhs", "ohs", "radiology", "ae_review"]
    - id: "fu_1yr"
      day_offset: 365
      window: [-30, +60]
      required_assessments: ["hhs", "ohs", "radiology", "ae_review"]
    - id: "fu_2yr"
      day_offset: 730
      window: [-60, +60]
      required_assessments: ["hhs", "ohs", "radiology", "ae_review"]
      critical: true

endpoints:
  primary:
    id: "hhs_improvement"
    calculation: "hhs_2yr - hhs_baseline"
    success_threshold: 20
    success_criterion: "improvement >= 20 points"

safety_thresholds:
  revision_rate_concern: 0.10
  sae_rate_concern: 0.40
  fracture_rate_concern: 0.08

deviation_classification:
  minor: "within_1.5x_window"
  major: "beyond_1.5x_window_or_missing_critical"
  critical: "affects_primary_endpoint"
```

## literature_benchmarks.yaml

```yaml
# Source: 15 indexed publications
# Extraction Method: LLM-assisted benchmark extraction
# Last Updated: 2026-01-11

publications:
  - id: "meding_2025"
    title: "Long-term outcomes of cementless revision THA"
    benchmarks:
      hhs_improvement: {mean: 38.2, sd: 14.3, ci_95: [35.7, 40.7]}
      revision_rate: {value: 0.062, ci_95: [0.041, 0.089]}
      mcid_achievement: {value: 0.72}

  - id: "dixon_2025"
    title: "Risk factors for periprosthetic fracture"
    risk_factors:
      osteoporosis: {revision_hr: 1.8, fracture_hr: 2.4}
      fracture_rate_osteoporotic: {min: 0.15, max: 0.20}
      fracture_rate_non_osteoporotic: {min: 0.04, max: 0.08}

  - id: "harris_2025"
    title: "Adverse events in revision THA"
    benchmarks:
      ae_rate: {min: 0.28, max: 0.40}

  - id: "vasios_et_al"
    title: "Functional outcomes following revision"
    benchmarks:
      hhs_improvement_range: {min: 28, max: 42}
```

## registry_norms.yaml

```yaml
# Source: AOANJRR 2024, NJR UK
# Extraction Method: Structured data extraction
# Last Updated: 2026-01-11

registries:
  - id: "aoanjrr_2024"
    name: "Australian Orthopaedic Association National Joint Replacement Registry"
    benchmarks:
      revision_tha:
        cementless_cup:
          survival_2yr: 0.94
          revision_rate_median: 0.062
          revision_rate_p95: 0.12
    risk_factors:
      osteoporosis: {revision_hr: 1.8, fracture_hr: 2.4}
      bmi_over_35: {revision_hr: 1.6}
    thresholds:
      fracture_rate_concern: 0.10

  - id: "njr_uk"
    name: "National Joint Registry UK"
    benchmarks:
      revision_tha:
        survival_2yr: 0.93
        revision_rate_median: 0.065
```

---

*Version 1.0 — Use Case Specifications with Multi-Source Architecture*

*Document generated: January 11, 2026*
