# Clinical Intelligence Platform - Solution Outline v0.1

## Current Implementation Scope

**A Multi-Agent AI Platform for Clinical Trial Intelligence**

---

## Executive Summary

The **Clinical Intelligence Platform (CIP)** is an AI-native platform that transforms how clinical teams interact with trial data through a **Persona-Driven Agentic Architecture**. This document describes capabilities across two therapeutic areas: **Total Knee Arthroplasty (TKA)** and **Drug-Eluting Stents (DES)**, with an enterprise-wide vision supporting **six distinct user personas**.

### PoC Scope vs. Future Vision

This document distinguishes between **demonstrable PoC capabilities** and **future enterprise vision**:

| Aspect | PoC Scope (Demonstrable) | Future Vision (Requires Integration) |
|--------|--------------------------|--------------------------------------|
| **Data Sources** | Synthetic clinical trials, public registries, open-access literature | PMS, CRM, eTMF, Financial, Manufacturing QMS |
| **Personas** | 4 with high feasibility (PM, Marketing, Sales, Clinical Ops) | 2 with limited feasibility (Strategy, Quality) |
| **Use Cases** | UC1-UC8 fully demonstrable, UC10-UC12 partially | UC9, UC13-UC20 require enterprise data |
| **Strategic Prompts** | ~38% fully demonstrable | ~62% require enterprise data integration |

**Data Feasibility Legend** (used throughout this document):
- 🟢 **PoC Ready**: Demonstrable with synthetic/public data
- 🟡 **Partial PoC**: Core functionality demonstrable, some features limited
- 🟠 **Synthetic Possible**: Can generate synthetic data for demo (limited realism)
- 🔴 **Future Vision**: Requires real enterprise data integration

---

## Platform Overview

### Scope

| Dimension | Current State |
|-----------|---------------|
| **Products** | 2 (TKA Medical Device, DES Cardiovascular) |
| **TKA Study** | Public protocol from ClinicalTrials.gov (synthetic patient data) |
| **DES Study** | Public protocol from ClinicalTrials.gov |
| **User Personas** | 6 (Product Manager, Sales, Marketing, Clinical Ops, Strategy, Quality) |
| **Dashboard Modules** | 19 functional modules (1 Foundation + 18 Operational) |
| **AI Agents** | 6 Persona Agents + 13 Specialized Agents |
| **ML/DL Models** | 9 predictive capabilities (4 Tier-1, 2 Tier-2, 3 Tier-3) |
| **Core Use Cases** | 20 implemented (UC1-UC20) |
| **Chat Interface** | Multi-agent conversational queries with RBAC |
| **Intelligent Caching** | Multi-tier caching (LLM responses, API endpoints, data layer) |

### Dual-Product Demonstration

```
+------------------------------------------------------------------+
|                    TWO-PRODUCT DEMONSTRATION                       |
|              (Both based on ClinicalTrials.gov protocols)          |
+------------------------------------------------------------------+
|                                                                    |
|  ORTHOPEDICS                         CARDIOVASCULAR                |
|  ───────────                         ──────────────                |
|  ┌─────────────────────┐            ┌─────────────────────┐       |
|  │ TKA (Medical Device)│            │ DES (Drug-Eluting   │       |
|  │                     │            │      Stent)         │       |
|  │ ClinicalTrials.gov  │            │ ClinicalTrials.gov  │       |
|  │ Public Protocol     │            │ Public Protocol     │       |
|  │                     │            │                     │       |
|  │ • Synthetic pts     │            │ • Public endpoints  │       |
|  │ • Revision rates    │            │ • MACE, TLR, TVR    │       |
|  │ • KSS/OKS scores    │            │ • Stent thrombosis  │       |
|  │ • AOANJRR/NJR bench │            │ • NCDR benchmarks   │       |
|  └─────────────────────┘            └─────────────────────┘       |
|            │                                  │                    |
|            └──────────────┬───────────────────┘                    |
|                           │                                        |
|              UNIFIED INTELLIGENCE PLATFORM                         |
|              (Same architecture, different configs)                |
|                                                                    |
+------------------------------------------------------------------+
```

### Architecture

```
+------------------------------------------------------------------+
|                 CLINICAL INTELLIGENCE PLATFORM                     |
+------------------------------------------------------------------+
|                                                                    |
|  ┌────────────────────────────────────────────────────────────┐   |
|  │                    FRONTEND (React)                         │   |
|  │  19 Modules │ Chat Interface │ Data Browser │ Simulation    │   |
|  │  Knowledge Builder (Foundation Module)                      │   |
|  └────────────────────────────────────────────────────────────┘   |
|                              │                                     |
|  ┌────────────────────────────────────────────────────────────┐   |
|  │                  AUTHENTICATION & RBAC                      │   |
|  │         SSO │ Role Assignment │ Permission Policies         │   |
|  └────────────────────────────────────────────────────────────┘   |
|                              │                                     |
|  ┌────────────────────────────────────────────────────────────┐   |
|  │                    API LAYER (FastAPI)                      │   |
|  │  UC1-UC20 Endpoints │ Chat │ Protocol │ Simulation │ Browse │   |
|  └────────────────────────────────────────────────────────────┘   |
|                              │                                     |
|  ┌────────────────────────────────────────────────────────────┐   |
|  │                    PERSONA AGENTS (6)                       │   |
|  │  Product Manager │ Sales │ Marketing │ Clinical Ops │       │   |
|  │  Strategy │ Quality                                         │   |
|  └────────────────────────────────────────────────────────────┘   |
|                              │                                     |
|  ┌────────────────────────────────────────────────────────────┐   |
|  │                 SPECIALIZED AGENTS (13)                     │   |
|  │  Knowledge Builder │ Data │ Safety │ Literature │ Registry │   |
|  │  Protocol │ Compliance │ Synthesis │ Code │ Document │      │   |
|  │  Competitive │ Financial │ Sentiment                        │   |
|  └────────────────────────────────────────────────────────────┘   |
|                              │                                     |
|  ┌────────────────────────────────────────────────────────────┐   |
|  │                    DATA LAYER                               │   |
|  │  PostgreSQL │ pgvector │ YAML Config │ Literature PDFs      │   |
|  │  PMS │ CRM │ eTMF │ Financial │ Manufacturing QMS           │   |
|  └────────────────────────────────────────────────────────────┘   |
|                                                                    |
+------------------------------------------------------------------+
```

---

## Dashboard Modules

### Foundation Module: Product Knowledge Builder

> **This module is the prerequisite for all other platform capabilities.** Before any persona can query the system, a Product Knowledge Base must be configured through a collaborative, AI-assisted onboarding process.

#### Overview

The **Product Knowledge Builder** is a long-running, interactive module where a domain expert collaborates with an AI Agent to construct a comprehensive, validated knowledge corpus for a specific medical device or therapeutic product. This knowledge base then powers all downstream analytics, queries, and document generation.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRODUCT KNOWLEDGE BUILDER                             │
│                    (Foundation for All Modules)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │ PHASE 1         │    │ PHASE 2         │    │ PHASE 3         │      │
│  │ Protocol        │───▶│ Literature      │───▶│ Rule            │      │
│  │ Ingestion       │    │ Corpus          │    │ Derivation      │      │
│  │                 │    │ Building        │    │                 │      │
│  │ • Protocol PDF  │    │ • PubMed search │    │ • Eligibility   │      │
│  │ • USDM 4.0      │    │ • Registry data │    │ • Safety rules  │      │
│  │ • SOA/Endpoints │    │ • Competitor    │    │ • Benchmarks    │      │
│  │ • I/E criteria  │    │   trials        │    │ • Thresholds    │      │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│           │                     │                     │                  │
│           └─────────────────────┼─────────────────────┘                  │
│                                 ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 4: Human-in-the-Loop Validation                           │    │
│  │                                                                  │    │
│  │  Domain Expert ◄──────────────────────────────────► AI Agent    │    │
│  │                                                                  │    │
│  │  • Review derived rules         • Suggest refinements           │    │
│  │  • Validate thresholds          • Identify gaps                 │    │
│  │  • Approve knowledge items      • Request clarification         │    │
│  │  • Add domain expertise         • Cross-reference sources       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                 │                                        │
│                                 ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ PRODUCT KNOWLEDGE BASE (Validated & Versioned)                   │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │ Protocol     │  │ Literature   │  │ Derived      │           │    │
│  │  │ Intelligence │  │ Corpus       │  │ Rules        │           │    │
│  │  │ (structured) │  │ (embeddings) │  │ (validated)  │           │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
│  │                                                                  │    │
│  │  Version: 1.2.0 | Last Updated: 2024-01-15 | Status: Active     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Phase 1: Protocol Ingestion

| Component | What It Does | Output |
|-----------|--------------|--------|
| **Protocol Upload** | Accept protocol PDF from ClinicalTrials.gov or internal source | Raw document |
| **LLM Extraction** | Extract structured data using USDM 4.0 schema | Protocol JSON |
| **SOA Parser** | Parse Schedule of Assessments into visit windows | Visit rules |
| **I/E Extractor** | Extract eligibility criteria with OMOP mappings | Eligibility rules |
| **Endpoint Mapper** | Identify primary/secondary endpoints with definitions | Endpoint specifications |

**AI Agent Interaction Example:**
```
Agent: "I've extracted 12 inclusion criteria and 8 exclusion criteria from the protocol.
        Criterion I3 mentions 'adequate bone stock' - this is subjective.
        How should this be operationalized for the study?"

Expert: "Use Paprosky classification. Type I-II is adequate, Type III is exclusion."

Agent: "Understood. I'll add a derived rule:
        'Paprosky Type III bone loss → Exclusion criterion violation'
        Should this also trigger a higher risk score for patients near the boundary?"

Expert: "Yes, Paprosky IIB should flag as elevated risk but not excluded."
```

#### Phase 2: Literature Corpus Building

| Component | What It Does | Output |
|-----------|--------------|--------|
| **Automated PubMed Search** | Query for relevant publications based on product/indication | Publication list |
| **Deep Research Agent** | Multi-round search expanding to related topics, complications, comparators | Extended corpus |
| **Registry Integration** | Ingest benchmark data from AOANJRR, NJR, NCDR | Benchmark parameters |
| **Competitor Analysis** | Identify and ingest published competitor trial data | Comparative dataset |
| **Embedding Generation** | Generate vector embeddings for RAG retrieval | pgvector corpus |

**Deep Research Agent Workflow:**
```
Round 1: Primary search - "total knee arthroplasty outcomes cemented"
         → 245 papers identified, 78 high-relevance

Round 2: Expand to complications - "TKA infection rates", "periprosthetic fracture"
         → 156 additional papers

Round 3: Comparator search - "ATTUNE knee outcomes", "competitor knee survival"
         → 89 comparative papers

Round 4: Risk factor deep-dive - "BMI TKA outcomes", "diabetes knee replacement"
         → 134 risk factor papers

Agent: "I've built a corpus of 502 papers. Key findings:
        - Infection rate benchmark: 1.2% (95% CI: 0.8-1.6%)
        - Revision rate at 5 years: 2.8% (registry average)
        - BMI >35 increases revision risk by HR 1.52

        Should I continue searching for specific sub-populations?"
```

#### Phase 3: Rule Derivation Engine

| Rule Type | Derivation Source | Example |
|-----------|-------------------|---------|
| **Eligibility Rules** | Protocol I/E criteria | `age >= 22 AND age <= 80` |
| **Visit Window Rules** | Protocol SOA | `Visit 3: Day 90 ± 14 days` |
| **Safety Thresholds** | Literature + Registry | `Infection rate > 2.5% → Signal` |
| **Benchmark Comparators** | Registry data | `NJR 5-year survival: 95.2%` |
| **Risk Factor Weights** | Literature hazard ratios | `Prior revision: HR 2.1` |
| **Deviation Classifiers** | Protocol + GCP | `Missed visit → Minor deviation` |
| **Document Templates** | Regulatory requirements | `DSMB narrative structure` |

**Rule Validation Interface:**
```
┌─────────────────────────────────────────────────────────────────┐
│ DERIVED RULE REVIEW                                              │
├─────────────────────────────────────────────────────────────────┤
│ Rule ID: SR-007                                                  │
│ Type: Safety Signal Threshold                                    │
│ Source: AOANJRR Annual Report 2023, p.47                        │
│                                                                  │
│ Rule: "Flag safety signal if revision rate exceeds 3.2% at      │
│        2 years (upper 95% CI of registry benchmark)"            │
│                                                                  │
│ Confidence: HIGH (derived from N=245,000 procedures)            │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [✓ Approve]  [✎ Modify]  [✗ Reject]  [? Discuss with Agent] │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Expert Notes: ____________________________________________       │
└─────────────────────────────────────────────────────────────────┘
```

#### Phase 4: Continuous Refinement

The knowledge base is not static - it evolves through:

| Trigger | Action | Agent Behavior |
|---------|--------|----------------|
| **New Literature** | Weekly PubMed scan | "3 new publications found. One reports higher infection rates with cement type X. Review?" |
| **Registry Update** | Annual report ingestion | "NJR 2024 data available. Benchmark revision rate changed from 2.8% to 2.6%. Update thresholds?" |
| **Query Gaps** | User questions without answers | "5 users asked about 'metal allergy outcomes' - no literature in corpus. Initiate search?" |
| **Rule Conflicts** | Contradictory evidence found | "New meta-analysis contradicts BMI threshold. HR now 1.3 (was 1.5). Reconcile?" |
| **Validation Feedback** | Expert corrections | "You corrected 3 Paprosky classifications. Should I adjust the extraction model?" |

#### Knowledge Base Artifacts

| Artifact | Format | Usage |
|----------|--------|-------|
| **Protocol Intelligence** | JSON (USDM 4.0) | Eligibility checks, visit windows, endpoint definitions |
| **Literature Corpus** | pgvector embeddings | RAG retrieval for evidence synthesis |
| **Benchmark Parameters** | YAML config | Safety signals, competitive analysis, registry comparison |
| **Derived Rules** | Rule engine JSON | Deviation detection, risk scoring, signal thresholds |
| **Validation Log** | Audit trail | Provenance of all approved rules with expert attribution |
| **Version History** | Git-like versioning | Rollback, comparison, change tracking |

#### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/knowledge/product/create` | POST | Initialize new product knowledge base |
| `/api/v1/knowledge/protocol/ingest` | POST | Ingest and extract protocol |
| `/api/v1/knowledge/literature/search` | POST | Execute literature corpus building |
| `/api/v1/knowledge/rules/derive` | POST | Generate rules from knowledge base |
| `/api/v1/knowledge/rules/validate` | PUT | Expert validation of derived rules |
| `/api/v1/knowledge/status` | GET | Knowledge base build progress |
| `/api/v1/knowledge/export` | GET | Export knowledge base artifacts |

#### PoC Feasibility: 🟢 PoC Ready

This module is **fully demonstrable** with PoC data:
- Protocol ingestion: ClinicalTrials.gov PDFs ✅
- Literature corpus: PubMed open access ✅
- Registry benchmarks: Public annual reports ✅
- Rule derivation: LLM-based extraction ✅
- Human validation: Interactive workflow ✅

---

### Implemented Modules (18 Total)

| Module | Purpose | Key Features | Primary Persona | Status | PoC Feasibility |
|--------|---------|--------------|-----------------|--------|-----------------|
| **Executive Dashboard** | Study health overview | Aggregated KPIs, action items, progress tracking | All | ✅ Complete | 🟢 PoC Ready |
| **Regulatory Readiness** | Submission assessment | Enrollment, compliance, safety, data completeness scores | Product Manager | ✅ Complete | 🟢 PoC Ready |
| **Safety Monitoring** | AE/SAE tracking | Signal detection, registry comparison, patient safety profiles | Product Manager | ✅ Complete | 🟢 PoC Ready |
| **Protocol Deviations** | Compliance monitoring | Deviation detection, classification, site trends | Clinical Ops | ✅ Complete | 🟢 PoC Ready |
| **Patient Risk** | Risk stratification | Individual risk scores, population distribution, contributing factors | Product Manager | ✅ Complete | 🟢 PoC Ready |
| **Protocol Digitization** | Structured protocol data | USDM 4.0 format, SOA, eligibility criteria with OMOP mappings | Clinical Ops | ✅ Complete | 🟢 PoC Ready |
| **Simulation Studio** | Outcome forecasting | Monte Carlo simulation, scenario comparison, risk-adjusted projections | Strategy | ✅ Complete | 🟢 PoC Ready |
| **Literature Intelligence** | Evidence synthesis | RAG-based search, evidence grading, citation generation | Marketing | ✅ Complete | 🟢 PoC Ready |
| **Document Generation** | Automated narratives | DSMB packages, safety summaries, regulatory sections | Marketing | ✅ Complete | 🟢 PoC Ready |
| **Competitive Benchmarking** | Trial comparison | Compare endpoints to published competitor trials | Sales | ✅ Complete | 🟢 PoC Ready |
| **Data Browser** | Data exploration | Table browsing, filtering, inline editing, export | All | ✅ Complete | 🟢 PoC Ready |
| **Data Sources** | Data lineage | Source transparency, provenance tracking | All | ✅ Complete | 🟢 PoC Ready |
| **Sales Intelligence** | Battle cards & rebuttals | Competitive evidence, surgeon champions, economic modeling | Sales | Planned | 🟡 Partial (literature rebuttals yes, CRM no) |
| **Financial Dashboard** | Study budget tracking | CRO costs, site payments, budget forecasts, change orders | Clinical Ops | Planned | 🟠 Synthetic possible |
| **Complaints Hub** | Complaint triage & MDR | AI categorization, trend detection, vigilance automation | Quality | Planned | 🟠 Synthetic possible |
| **CAPA Dashboard** | Corrective actions | CAPA tracking, effectiveness analysis, root cause linking | Quality | Planned | 🟠 Synthetic possible |
| **Portfolio Health** | Multi-product view | Survivorship trends, sentiment analysis, market positioning | Strategy | Planned | 🔴 Future (requires VoC data) |
| **Content Studio** | Marketing content | SOTA reports, social content, patient materials, claim validation | Marketing | Planned | 🟡 Partial (SOTA yes, social limited) |

### Module-to-Use Case Mapping

| Module | Primary Use Cases | User Personas |
|--------|-------------------|---------------|
| Executive Dashboard | UC5: Executive Study Health | All |
| Regulatory Readiness | UC1: Submission Readiness | Product Manager, Clinical Ops |
| Safety Monitoring | UC2: Safety Signal Detection, UC9: Recall Risk | Product Manager, Quality |
| Protocol Deviations | UC3: Deviation Detection | Clinical Ops |
| Patient Risk | UC4: Risk Stratification | Product Manager |
| Protocol Digitization | Protocol Review, UC14: eTMF Audit | Clinical Ops |
| Simulation Studio | Outcome Forecasting, UC15: Portfolio Health | Strategy |
| Literature Intelligence | UC6: Evidence Synthesis, UC12: SOTA Report | Marketing, Sales |
| Document Generation | UC7: Narrative Generation | Marketing, Clinical Ops |
| Competitive Benchmarking | UC8: Trial Comparison, UC10: Battle Cards | Sales |
| Data Browser | Ad-hoc Exploration | All |
| Data Sources | Data Lineage, Provenance | All |
| Sales Intelligence | UC10: Battle Cards, UC11: Economic Value | Sales |
| Financial Dashboard | UC13: Financial Forecast | Clinical Ops |
| Complaints Hub | UC17: Complaints Triage, UC19: Vigilance | Quality |
| CAPA Dashboard | UC18: CAPA Effectiveness | Quality |
| Portfolio Health | UC15: Portfolio Health, UC16: Sentiment | Strategy |
| Content Studio | UC12: SOTA Report | Marketing |

---

## Use Cases (Implemented)

### Core Use Cases (UC1-UC8)

#### UC1: Regulatory Submission Readiness Assessment

**Endpoint:** `/api/v1/uc1/readiness-assessment`

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Enrollment Status | Tracks enrollment vs. target | study_patients |
| Compliance Status | Protocol adherence metrics | Deviation detectors |
| Safety Status | Safety profile completeness | study_adverse_events |
| Data Completeness | Data quality assessment | All study tables |

**Example Query:** *"Are we ready for regulatory submission?"*

#### UC2: Safety Signal Detection & Contextualization

**Endpoint:** `/api/v1/uc2/safety-summary`

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Safety Summary | Study-wide AE/SAE analysis | study_adverse_events |
| Signal Detection | Identifies concerning patterns | AE rates vs. literature |
| Registry Comparison | Benchmarks vs. AOANJRR/NJR (TKA) or NCDR (DES) | registry_benchmarks |
| Patient Profiles | Individual safety narratives | Patient-level data |

**Example Query (TKA):** *"What's our infection rate compared to NJR benchmark?"*
**Example Query (DES):** *"What's our MACE rate compared to NCDR benchmark?"*

#### UC3: Protocol Deviation Detection

**Endpoint:** `/api/v1/uc3/deviations-summary`

| Detector | What It Detects | Severity |
|----------|-----------------|----------|
| Visit Timing | Visits outside protocol windows | Minor/Major |
| Missing Assessment | Required assessments not completed | Major |
| I/E Violation | Eligibility criteria violations | Critical |
| Consent Timing | Consent date issues | Major |
| Missed Visit | Unscheduled patient absences | Minor |

**Example Query:** *"Which sites have the most protocol deviations?"*

#### UC4: Patient Risk Stratification

**Endpoint:** `/api/v1/uc4/population-risk`

| Component | What It Does | Method |
|-----------|--------------|--------|
| Individual Risk | Per-patient risk score | Clinical hazard ratios |
| Population Distribution | Risk tier breakdown | Statistical binning |
| Contributing Factors | Risk factor analysis | Literature-derived HRs |
| High-Risk List | Prioritized surveillance | Ranked by risk score |

**Risk Factors (Literature-Derived):**
- Age >80 years (HR: 1.8)
- BMI >35 (HR: 1.5)
- Diabetes (HR: 1.4)
- Prior revision surgery (HR: 2.1)
- Severe bone loss / Paprosky 3B (HR: 2.5)

**Example Query:** *"Which patients are at highest risk for early revision?"*

#### UC5: Executive Study Health Dashboard

**Endpoint:** `/api/v1/uc5/executive-summary`

| Component | What It Shows |
|-----------|---------------|
| Study Progress | Enrollment curves, completion rates |
| Safety Overview | AE/SAE counts, signal alerts |
| Compliance Summary | Deviation rates by type |
| Action Items | Prioritized intervention list |

**Example Query:** *"Give me the executive summary for the DSMB meeting"*

#### UC6: Literature Intelligence & Evidence Synthesis

**Endpoint:** `/api/v1/uc6/literature-search`

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Semantic Search | RAG-based literature retrieval | pgvector embeddings |
| Evidence Grading | Rates evidence quality (RCT, meta-analysis, cohort) | Publication metadata |
| Citation Generation | Formats references for regulatory docs | Literature database |
| Comparative Analysis | Synthesizes findings across publications | Multi-document RAG |

**Example Query (TKA):** *"Find evidence on cemented vs. cementless fixation in patients >75 years"*
**Example Query (DES):** *"What do meta-analyses say about DAPT duration after DES implantation?"*

#### UC7: Document Generation

**Endpoint:** `/api/v1/uc7/generate-document`

| Document Type | What It Generates | Data Sources |
|---------------|-------------------|--------------|
| DSMB Package | Safety narratives, enrollment summary, action items | UC1-UC5 outputs |
| Safety Summary | AE/SAE narratives with contextualization | study_adverse_events, literature |
| Regulatory Section | Pre-formatted submission sections | Protocol, safety, efficacy data |
| Executive Brief | One-page study status for leadership | All study data |

**Example Query:** *"Generate a safety narrative for the quarterly DSMB report"*

#### UC8: Competitive Benchmarking

**Endpoint:** `/api/v1/uc8/competitive-analysis`

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Trial Identification | Finds comparable published trials | ClinicalTrials.gov, literature |
| Endpoint Comparison | Compares primary/secondary endpoints | Published results |
| Population Matching | Adjusts for demographic differences | Baseline characteristics |
| Gap Analysis | Identifies competitive advantages/risks | Multi-trial synthesis |

**Example Query (TKA):** *"How does our revision rate compare to the ATTUNE knee study?"*
**Example Query (DES):** *"Compare our MACE endpoint to XIENCE trials at 1 year"*

### Extended Use Cases (UC9-UC20)

> **PoC Data Feasibility Note**: Extended use cases vary in demonstrability based on data requirements. Use cases marked 🟠 can use synthetic data for workflow demonstration but lack realistic business value. Use cases marked 🔴 require actual enterprise data integration.

#### UC9: Recall Risk Assessment 🔴

**Endpoint:** `/api/v1/uc9/recall-risk`
**Primary Persona:** Product Manager
**PoC Feasibility:** 🔴 **Future Vision** - Requires real device deficiency reports, complaint data, and manufacturing lot information. Synthetic data would not meaningfully demonstrate recall risk assessment logic.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Deficiency Trend Analysis | Identifies rising trends in device failures | Device deficiency reports |
| Field Safety Assessment | Determines need for proactive notices | Complaint data, manufacturing lots |
| Regulatory Threshold Check | Compares against MDR/FDA thresholds | Regulatory guidelines |
| Risk Scoring | Calculates recall probability | Multi-factor risk model |

**Example Query:** *"Review the last 12 months of device deficiency reports. Is there a rising trend in specific mechanical failures that warrants a proactive field safety notice?"*

#### UC10: Competitive Battle Cards 🟡

**Endpoint:** `/api/v1/uc10/battle-card`
**Primary Persona:** Sales
**PoC Feasibility:** 🟡 **Partial PoC** - Literature-based rebuttals and published trial comparisons demonstrable. CRM-based surgeon champion identification requires enterprise data.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Rebuttal Generation | Creates evidence-based competitive responses | Literature, internal studies |
| Weakness Identification | Cross-references competitor complications | Published literature, study data |
| Champion Identification | Finds surgeons with high success rates | Registry data, CRM |
| Sales Scripting | Generates elevator pitches from evidence | Internal white papers |

**Example Query:** *"Draft a rebuttal for a surgeon currently using a competitor system, specifically highlighting our 88.5% success rate versus their 76.3%."*

#### UC11: Economic Value Modeling 🟡

**Endpoint:** `/api/v1/uc11/economic-value`
**Primary Persona:** Sales
**PoC Feasibility:** 🟡 **Partial PoC** - Revision cost calculations and ROI projections from survival data demonstrable. Hospital-specific economics require procurement integration.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Revision Cost Calculation | Calculates avoided revision costs | Survival data, cost models |
| ROI Projection | Projects 5-year cost savings | Survival rates, procedure costs |
| Hospital Economics | Models procurement value proposition | Volume data, pricing |
| Comparative Economics | Compares vs. competitor economics | Market data |

**Example Query:** *"Calculate the predicted 5-year revision cost savings for a hospital if they switch from a competitor with 94% survival to our observed 100% survival."*

#### UC12: SOTA Report Generation 🟢

**Endpoint:** `/api/v1/uc12/sota-report`
**Primary Persona:** Marketing
**PoC Feasibility:** 🟢 **PoC Ready** - Fully demonstrable using PubMed open-access literature and synthetic CSR data.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Literature Synthesis | Aggregates recent publications | PubMed, internal CSRs |
| Trend Analysis | Identifies market and clinical trends | Congress abstracts, literature |
| Claim Validation | Validates marketing claims against evidence | Study data, literature |
| Content Generation | Creates SOTA narrative documents | Multi-source synthesis |

**Example Query:** *"Generate a comprehensive 'State-of-the-Art' report for stemless shoulder arthroplasty using internal CSRs and the last 3 years of PubMed publications."*

#### UC13: Financial Forecast 🟠

**Endpoint:** `/api/v1/uc13/financial-forecast`
**Primary Persona:** Clinical Operations
**PoC Feasibility:** 🟠 **Synthetic Possible** - Can demonstrate workflow with synthetic budget/payment data, but synthetic financials lack realistic business patterns and decision value.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Budget Analysis | Analyzes CRO change orders and projections | Financial systems |
| Site Payment Calculation | Calculates payments from eCRF completion | Site contracts, eCRF data |
| Site Risk Alert | Identifies budget/enrollment mismatches | Budget data, enrollment |
| Forecast Modeling | Projects remaining study costs | Historical spend, timeline |

**Example Query:** *"Analyze the current CRO change orders and provide a budget estimate for the remaining 24 months of the 5-year follow-up period."*

#### UC14: eTMF Audit 🔴

**Endpoint:** `/api/v1/uc14/etmf-audit`
**Primary Persona:** Clinical Operations
**PoC Feasibility:** 🔴 **Future Vision** - eTMF documents are complex regulatory artifacts with specific legal language, signatures, and audit trails. Synthetic eTMF documents would be meaningless and cannot demonstrate real compliance capabilities.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Document Completeness | Checks TMF for missing documents | eTMF/ISF |
| License Verification | Flags expired investigator credentials | Regulatory documents |
| Compliance Check | Validates against ICH E6 requirements | GCP guidelines |
| Audit Preparation | Generates audit-ready reports | All trial documentation |

**Example Query:** *"Review the electronic Trial Master File and flag any sites where the Principal Investigator's medical license has expired."*

#### UC15: Portfolio Health Analysis 🟡

**Endpoint:** `/api/v1/uc15/portfolio-health`
**Primary Persona:** Strategy
**PoC Feasibility:** 🟡 **Partial PoC** - Survivorship trends from public registry data demonstrable. Market positioning and sentiment analysis require CRM/VoC data integration.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Survivorship Trends | Compares 10-year survival across products | Registry data |
| Market Positioning | Analyzes competitive positioning | Market data, registries |
| R&D Recommendations | Suggests portfolio focus areas | Demographic trends, outcomes |
| Threat Assessment | Evaluates competitive threats | Registry trends, literature |

**Example Query:** *"Compare 10-year survivorship trends of our cemented vs. uncemented portfolios. Should we shift R&D focus based on aging demographic trends?"*

#### UC16: Sentiment Analysis (VoC) 🔴

**Endpoint:** `/api/v1/uc16/sentiment-analysis`
**Primary Persona:** Strategy
**PoC Feasibility:** 🔴 **Future Vision** - Sentiment analysis requires real human feedback (surgeon surveys, IIS data). Synthetic "opinions" would be fabricated sentiment with zero analytical value - meaningless for demonstrating VoC capabilities.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Surgeon Feedback Analysis | Analyzes IIS and survey feedback | IIS data, surveys |
| Trend Detection | Identifies improving/declining sentiment | Historical surveys |
| Refinement Identification | Extracts requested product improvements | Feedback data |
| Competitive Sentiment | Compares sentiment vs. competitors | Market research |

**Example Query:** *"Perform a sentiment analysis on the last 100 internal surveys regarding instrumentation. Is feedback on 'ease of use' improving or declining compared to 2022?"*

#### UC17: Complaints Triage 🟠

**Endpoint:** `/api/v1/uc17/complaints-triage`
**Primary Persona:** Quality
**PoC Feasibility:** 🟠 **Synthetic Possible** - Can generate synthetic complaints with failure modes (loosening, infection, pain) to demonstrate triage workflows and categorization. However, synthetic complaints lack realistic business patterns for trend detection.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| AI Categorization | Auto-categorizes incoming complaints | Complaint reports |
| Trend Detection | Identifies trending failure modes | Complaint data |
| CPM Calculation | Calculates complaints per million | Complaints, sales volume |
| Batch Correlation | Links complaints to manufacturing lots | Complaints, lot data |

**Example Query:** *"Analyze the complaint rate over the last 18 months. Normalize against sales volume (CPM) and identify if the increase in 'liner wear' reports is statistically significant or a byproduct of market growth."*

#### UC18: CAPA Effectiveness 🟠

**Endpoint:** `/api/v1/uc18/capa-effectiveness`
**Primary Persona:** Quality
**PoC Feasibility:** 🟠 **Synthetic Possible** - Can generate synthetic CAPA records to demonstrate tracking workflows and before/after analysis. However, real CAPA effectiveness requires actual implementation dates and real incident data correlation.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Before/After Analysis | Compares incident rates pre/post CAPA | CAPA records, complaints |
| Effectiveness Scoring | Quantifies CAPA effectiveness | Incident data |
| Root Cause Linking | Links CAPAs to triggering events | CAPA records, clinical data |
| Trend Monitoring | Tracks CAPA closure and recurrence | CAPA database |

**Example Query:** *"Review the effectiveness of CAPA-2023-004. Compare the incident rate in products manufactured before the fix versus those manufactured after implementation."*

#### UC19: Vigilance Reporting 🔴

**Endpoint:** `/api/v1/uc19/vigilance-report`
**Primary Persona:** Quality
**PoC Feasibility:** 🔴 **Future Vision** - Vigilance reports (MDR, EU MDR Article 87) have specific formatting, coding, and narrative requirements. Synthetic vigilance reports could misrepresent regulatory compliance capabilities and would be meaningless for demonstration.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Threshold Assessment | Determines reportability per FDA/MDR | Regulatory guidelines |
| Report Drafting | Auto-generates vigilance report drafts | Complaint data |
| RMF Cross-Check | Compares events to Risk Management File | RMF, complaint data |
| Deadline Tracking | Monitors reporting timelines | Regulatory requirements |

**Example Query:** *"A surgeon reported a 'suspected' material failure. Based on FDA 21 CFR 803 and EU MDR Article 87, determine if this event meets the 'Serious Deterioration of Health' threshold and draft the initial Vigilance report."*

#### UC20: PMS Analytics (CPM) 🔴

**Endpoint:** `/api/v1/uc20/pms-analytics`
**Primary Persona:** Quality
**PoC Feasibility:** 🔴 **Future Vision** - CPM calculation requires real sales volume data and complaint data. Geographic clustering and supplier correlation require real manufacturing data. Synthetic data cannot demonstrate meaningful post-market surveillance analytics.

| Component | What It Does | Data Sources |
|-----------|--------------|--------------|
| Geographic Clustering | Identifies regional quality patterns | Complaints, geography |
| Batch-Specific Analysis | Detects lot-specific issues | Complaints, lot data |
| Supplier Correlation | Links complaints to suppliers | Complaints, supplier data |
| Silent Signal Search | Finds unelevated issues in service logs | Service & repair logs |

**Example Query:** *"Cross-reference recent complaints regarding 'baseplate loosening' with manufacturing lot numbers and clean-room environmental logs. Is there a correlation with the batch produced in Q3 2024?"*

---

## Chat Interface

### Capabilities

| Feature | Implementation |
|---------|----------------|
| **Intent Classification** | Routes queries to appropriate agents |
| **Multi-Agent Orchestration** | Coordinates Data, Literature, Registry, Safety agents |
| **Natural Language Queries** | Supports conversational clinical questions |
| **Source Attribution** | Every response includes provenance |
| **Confidence Scoring** | HIGH / MODERATE / LOW / INSUFFICIENT |

### Supported Query Types by Persona

**Product Manager (The "Product Guardian"):**

| Query Type | Example | Primary Agent |
|------------|---------|---------------|
| Safety Correlation | "Identify statistical correlation between component size and complication incidence" | Safety Agent + Data Agent |
| Benchmark Analysis | "Compare 2-year survivorship against bottom 25% in registry" | Registry Agent |
| Recall Risk | "Review device deficiency reports for rising trends" | Safety Agent + Compliance Agent |
| Demographic Impact | "Are revision rates significantly higher in patients with BMI >35?" | Data Agent + Synthesis |
| Regulatory Gap | "List required CERs that are missing or expire within 6 months" | Document Agent |

**Sales (The "Competitive Closer"):**

| Query Type | Example | Primary Agent |
|------------|---------|---------------|
| Rebuttal Generation | "Draft rebuttal highlighting our 88.5% vs competitor's 76.3% success rate" | Competitive Agent + Literature |
| Outcome Visualization | "Extract functional score improvements and generate mobility summary" | Data Agent + Synthesis |
| Competitor Weakness | "Search literature for known competitor complications" | Literature Agent + Competitive |
| Economic Modeling | "Calculate 5-year revision cost savings for switching hospitals" | Financial Agent |
| Champion Identification | "Identify surgeons with high success rates using our implants" | Data Agent (CRM data) |

**Marketing (The "Brand Storyteller"):**

| Query Type | Example | Primary Agent |
|------------|---------|---------------|
| SOTA Generation | "Generate State-of-the-Art report using CSRs and PubMed" | Literature Agent + Synthesis |
| Claim Validation | "Check if 'industry-leading safety' claim is supported by AE rates" | Safety Agent + Literature |
| Patient Narrative | "Identify super-responders and draft de-identified success story" | Data Agent + Document |
| Congress Intelligence | "Scan competitor abstracts for top marketing themes" | Literature Agent + Competitive |
| Channel Content | "Draft LinkedIn posts highlighting 0% device-related AEs" | Document Agent |

**Clinical Operations (The "Compliance & Financial Lead"):**

| Query Type | Example | Primary Agent |
|------------|---------|---------------|
| Financial Forecast | "Analyze CRO change orders and estimate remaining budget" | Financial Agent |
| Site Payments | "Calculate Q4 site payments from eCRF completion" | Financial Agent + Data |
| Site Risk | "Identify sites with <50% enrollment but >80% budget consumed" | Data Agent + Financial |
| MedDRA Coding | "Suggest correct MedDRA codes for 'other' AE entries" | Safety Agent |
| Document Audit | "Flag sites with expired PI medical licenses" | Compliance Agent |

**Strategy (The "Visionary"):**

| Query Type | Example | Primary Agent |
|------------|---------|---------------|
| Sentiment Analysis | "Analyze surgeon feedback for top 3 requested refinements" | Sentiment Agent |
| Portfolio Sustainability | "Compare 10-year survivorship of cemented vs uncemented portfolios" | Registry Agent + Data |
| VoC Trends | "Is feedback on 'ease of use' improving or declining?" | Sentiment Agent |
| Competitive Threat | "Evaluate risk of robotics-assisted systems on manual portfolio" | Competitive Agent + Registry |
| Market Entry | "Simulate evidence requirements for Japanese market entry" | Compliance Agent + Literature |

**Quality Head:**

| Query Type | Example | Primary Agent |
|------------|---------|---------------|
| CPM Analysis | "Normalize complaint rate against sales volume" | Data Agent + Safety |
| Root Cause | "Cross-reference complaints with lot numbers and environmental logs" | Data Agent + Compliance |
| CAPA Effectiveness | "Compare incident rates before vs after CAPA implementation" | Compliance Agent |
| Vigilance Logic | "Determine if event meets 'Serious Deterioration of Health' threshold" | Safety Agent + Compliance |
| RMF Update | "Identify new hazardous situations not in Risk Management File" | Safety Agent |

### Example Interactions

**Product Manager Example:**
```
User: "Compare our 2-year survivorship against the bottom 25% of systems in the registry"

Agent Response:
├── Registry Agent: Retrieves registry benchmark distribution
├── Data Agent: Calculates study survivorship
├── Synthesis Agent: Generates comparative analysis
└── Response: "Your product shows 98.1% 2-year survivorship, which exceeds
              the bottom 25% threshold of 95.2% by 2.9 percentage points.
              [Source: Study data, Registry Annual Report 2023]"
              Confidence: HIGH
```

**Quality Head Example:**
```
User: "Review CAPA-2023-004 effectiveness for glenosphere locking screw issues"

Agent Response:
├── Compliance Agent: Retrieves CAPA records and implementation date
├── Data Agent: Calculates pre/post incident rates
├── Synthesis Agent: Generates effectiveness analysis
└── Response: "CAPA-2023-004 shows 78% reduction in incidents.
              Pre-fix rate: 2.3 per 1000 units. Post-fix rate: 0.5 per 1000 units.
              Implementation date: March 2023. N=45,000 units analyzed.
              [Source: CAPA Database, Complaint Records]"
              Confidence: HIGH
```

---

## AI Agents

### Two-Tier Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER PERSONAS (6)                         │
│  Product Manager │ Sales │ Marketing │ Clinical Ops │           │
│  Strategy │ Quality                                              │
│            (authenticated via SSO/RBAC)                          │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PERSONA AGENTS (6)                          │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │ Product Mgr   │  │ Sales Agent   │  │ Marketing     │        │
│  │ Agent         │  │               │  │ Agent         │        │
│  │ • Safety focus│  │ • Competitive │  │ • Content gen │        │
│  │ • Regulatory  │  │   positioning │  │ • Claim valid │        │
│  │ • Recall risk │  │ • HCP targets │  │ • SOTA synth  │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │ Clinical Ops  │  │ Strategy      │  │ Quality       │        │
│  │ Agent         │  │ Agent         │  │ Agent         │        │
│  │ • Financial   │  │ • Portfolio   │  │ • Complaints  │        │
│  │ • Compliance  │  │ • Sentiment   │  │ • CAPA/Vigil  │        │
│  │ • eTMF audit  │  │ • Market sim  │  │ • RMF/PMS     │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SPECIALIZED AGENTS (12)                        │
│  Data │ Safety │ Literature │ Registry │ Protocol │ Compliance  │
│  Synthesis │ Code │ Document │ Competitive │ Financial │        │
│  Sentiment                                                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│  PostgreSQL │ pgvector │ YAML Config │ Literature │ PMS │ CRM   │
│  eTMF │ Financial │ Manufacturing QMS │ Service Logs            │
└─────────────────────────────────────────────────────────────────┘
```

### Persona Agents (Goal-Based Orchestration)

| Agent | Persona | Key Capabilities | RBAC Policy |
|-------|---------|------------------|-------------|
| **Product Manager Agent** | Product Manager | Safety/recall focus, regulatory orchestration, benchmark analysis, demographic impact assessment | Full safety data, registry access, regulatory documents |
| **Sales Agent** | Sales | Competitive positioning, surgeon targeting, economic modeling, rebuttal generation | Aggregated clinical data, competitive data, surgeon performance |
| **Marketing Agent** | Marketing | Content generation, claim validation, SOTA synthesis, channel optimization | Published data, evidence summaries, no raw patient data |
| **Clinical Ops Agent** | Clinical Operations | Financial tracking, compliance monitoring, eTMF audit, site management | Full study data, financial data, compliance documents |
| **Strategy Agent** | Strategy | Portfolio analysis, sentiment tracking, market simulation, trend analysis | Cross-portfolio data, market trends, aggregated feedback |
| **Quality Agent** | Quality | Complaints triage, CAPA tracking, vigilance automation, RMF maintenance | All quality data, manufacturing data, complaint records |

**Persona Agent Responsibilities:**
- **Goal-Based Planning**: Decomposes complex user objectives into actionable sub-tasks
- **Query Orchestration**: Routes sub-tasks to appropriate specialized agents
- **Response Synthesis**: Aggregates multi-agent outputs into coherent narratives
- **RBAC Enforcement**: Filters data and actions based on persona permissions
- **Context Management**: Maintains conversation state and user intent

### Specialized Agents (Domain Expertise)

| Agent | Domain | Key Functions |
|-------|--------|---------------|
| **Knowledge Builder Agent** | Product onboarding | Protocol extraction, literature corpus building, rule derivation, human-in-the-loop validation |
| **Data Agent** | Study database | Patient queries, cohort analysis, statistical summaries |
| **Safety Agent** | AE/SAE analysis | Signal detection, severity assessment, safety narratives |
| **Literature Agent** | Evidence search | RAG-based PDF search, evidence grading, citation generation |
| **Registry Agent** | Benchmarking | AOANJRR/NJR (TKA), NCDR (DES), registry comparison |
| **Protocol Agent** | Compliance | Eligibility verification, visit window checks |
| **Compliance Agent** | Deviations | Deviation detection, GCP compliance, eTMF audit |
| **Synthesis Agent** | Narrative generation | Multi-source synthesis, provenance tracking |
| **Code Agent** | Query generation | SQL generation for ad-hoc analysis |
| **Document Agent** | Content generation | DSMB packages, regulatory sections, marketing content |
| **Competitive Agent** | Trial comparison | Endpoint comparison, population matching, gap analysis |
| **Financial Agent** | Budget analysis | CRO costs, site payments, forecast modeling |
| **Sentiment Agent** | VoC analysis | Survey sentiment, feedback trends, NPS analysis |

> **Note**: The Knowledge Builder Agent is unique in that it operates in a long-running, conversational mode with domain experts during the product onboarding phase. It coordinates with Literature Agent, Protocol Agent, and Registry Agent to build the foundational knowledge base.

### RBAC Policy Framework

| Permission | PM | Sales | Mktg | ClinOps | Strategy | Quality |
|------------|:--:|:-----:|:----:|:-------:|:--------:|:-------:|
| Patient-level data | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| Safety narratives | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Risk scores | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Financial data | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Complaints data | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Manufacturing data | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Surgeon CRM data | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Competitive data | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Document generation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Data modifications | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| Simulation runs | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |

### Agent Capabilities

- **Provenance Tracking**: Every response cites specific data sources
- **Confidence Scoring**: Quantified uncertainty (HIGH/MODERATE/LOW)
- **Async Execution**: Concurrent agent processing for complex queries
- **Error Handling**: Graceful fallbacks with informative messages
- **RBAC Filtering**: Responses automatically filtered by persona permissions

---

## Data Universe

### Data Source Strategy

The platform integrates multiple data sources for comprehensive enterprise intelligence.

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCE STRATEGY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CLINICAL TRIAL DATA                  COMMERCIAL DATA           │
│   ──────────────────                   ───────────────           │
│   ┌─────────────────┐                 ┌─────────────────┐       │
│   │ ClinicalTrials  │                 │ CRM/Surgeon     │       │
│   │ .gov Protocols  │                 │ Database        │       │
│   │ (TKA + DES)     │                 │                 │       │
│   └─────────────────┘                 └─────────────────┘       │
│                                                                  │
│   ┌─────────────────┐                 ┌─────────────────┐       │
│   │ Registry Annual │                 │ Sales Volume    │       │
│   │ Reports         │                 │ Data            │       │
│   │ AOANJRR/NJR/NCDR│                 │                 │       │
│   └─────────────────┘                 └─────────────────┘       │
│                                                                  │
│   QUALITY & COMPLIANCE                 FINANCIAL DATA            │
│   ────────────────────                 ──────────────            │
│   ┌─────────────────┐                 ┌─────────────────┐       │
│   │ Post-Market     │                 │ CRO Contracts   │       │
│   │ Surveillance    │                 │ Site Payments   │       │
│   │ Complaints/MDR  │                 │ Budget Data     │       │
│   └─────────────────┘                 └─────────────────┘       │
│                                                                  │
│   ┌─────────────────┐                 ┌─────────────────┐       │
│   │ Manufacturing   │                 │ eTMF/ISF        │       │
│   │ QMS/Lot Data    │                 │ Regulatory Docs │       │
│   │ CAPA Records    │                 │                 │       │
│   └─────────────────┘                 └─────────────────┘       │
│                                                                  │
│   EVIDENCE & INTELLIGENCE                                        │
│   ───────────────────────                                        │
│   ┌─────────────────┐                 ┌─────────────────┐       │
│   │ PubMed Open     │                 │ Congress        │       │
│   │ Access Papers   │                 │ Abstracts       │       │
│   │ (literature)    │                 │                 │       │
│   └─────────────────┘                 └─────────────────┘       │
│                                                                  │
│   ┌─────────────────┐                 ┌─────────────────┐       │
│   │ IIS/Surgeon     │                 │ Service &       │       │
│   │ Feedback        │                 │ Repair Logs     │       │
│   └─────────────────┘                 └─────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Sources by Category

#### Clinical Trial Data (Current)

| Source | Data Extracted | Usage | Status |
|--------|----------------|-------|--------|
| **ClinicalTrials.gov** | Protocol PDFs for TKA and DES studies | Eligibility criteria, endpoints, SOA, study design | ✅ Active |
| **AOANJRR Annual Report** | TKA revision rates, survival curves by age/gender | Registry benchmarking for orthopedics | ✅ Active |
| **NJR Annual Report** | UK TKA outcomes, infection rates, implant survival | Registry benchmarking for orthopedics | ✅ Active |
| **NCDR CathPCI Registry** | DES MACE rates, stent thrombosis benchmarks | Registry benchmarking for cardiovascular | ✅ Active |
| **PubMed Open Access** | Published RCTs, meta-analyses, cohort studies | Literature RAG, hazard ratios, evidence synthesis | ✅ Active |
| **Published Trial Results** | Competitor trial endpoints | Competitive benchmarking | ✅ Active |

#### Enterprise Data Sources (Planned)

> **Synthetic Data Feasibility Analysis**: The following table includes assessment of whether synthetic data can meaningfully demonstrate each data source's capabilities.

| Source | Data Type | Usage | Primary Persona | Status | Synthetic Feasibility |
|--------|-----------|-------|-----------------|--------|-----------------------|
| **Post-Market Surveillance** | Complaints, MDR reports, vigilance | Quality monitoring, Product Manager alerts | Quality, PM | Planned | 🟠 Complaints: Yes. MDR reports: No (regulatory artifacts) |
| **CRM/Surgeon Database** | Surgeon profiles, implant history, preferences | Sales targeting, champion identification | Sales | Planned | 🟡 Basic profiles: Yes. Real surgeon data: No |
| **eTMF/ISF** | Trial documents, site files, regulatory docs | Clinical Ops compliance, audit prep | Clinical Ops | Planned | 🔴 No - complex legal documents with signatures/audit trails |
| **Financial Systems** | CRO contracts, site payments, budgets | Budget tracking, forecasting | Clinical Ops | Planned | 🟠 Workflow demo: Yes. Realistic patterns: No |
| **Manufacturing QMS** | Lot data, CAPA records, environmental logs | Root cause analysis, quality trends | Quality | Planned | 🟠 CAPA records: Yes. Environmental logs: No (sensor data) |
| **Service & Repair Logs** | Technician notes, repairs, silent signals | Early quality detection | Quality | Planned | 🔴 No - requires real operational context |
| **SharePoint/DMS** | Regulatory documents, CERs, technical files | Regulatory gap analysis | Product Manager | Planned | 🔴 No - CERs are formal regulatory submissions |
| **Surgeon Feedback/IIS** | Investigator-initiated studies, surveys | Product refinement, sentiment | Strategy | Planned | 🔴 No - synthetic opinions are meaningless |
| **Congress Abstracts** | Competitor presentations, market themes | Competitive intelligence | Marketing | Planned | 🔴 No - copyrighted content |
| **Sales Volume Data** | Units sold by region/product/lot | CPM calculation, market analysis | Quality, Sales | Planned | 🟠 Basic structure: Yes. Business patterns: No |

### Synthetic Data Generation Strategy

Synthetic data is generated programmatically to create realistic clinical trial datasets that:
- Match protocol-defined eligibility criteria
- Reflect literature-reported event rates
- Follow protocol schedule of assessments
- Exhibit realistic statistical distributions

#### Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                 SYNTHETIC DATA GENERATION PIPELINE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: PROTOCOL EXTRACTION                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ClinicalTrials.gov PDF                                   │    │
│  │     ↓                                                    │    │
│  │ LLM-based extraction (Gemini)                            │    │
│  │     ↓                                                    │    │
│  │ Structured USDM 4.0 JSON:                                │    │
│  │   • Eligibility criteria (I/E)                           │    │
│  │   • Schedule of Assessments (SOA)                        │    │
│  │   • Primary/Secondary endpoints                          │    │
│  │   • Visit windows and timing                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ↓                                   │
│  STEP 2: PARAMETER EXTRACTION FROM LITERATURE                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Published studies + Meta-analyses                        │    │
│  │     ↓                                                    │    │
│  │ Extract statistical parameters:                          │    │
│  │   • Event rates (AE incidence by type)                   │    │
│  │   • Demographic distributions (age, BMI, comorbidities)  │    │
│  │   • Outcome score distributions (mean, SD)               │    │
│  │   • Hazard ratios for risk factors                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ↓                                   │
│  STEP 3: COHORT GENERATION                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Generate patient cohort matching:                        │    │
│  │   • Protocol eligibility criteria                        │    │
│  │   • Literature-derived demographic distributions         │    │
│  │   • Realistic comorbidity profiles                       │    │
│  │   • Appropriate sample size (e.g., 400 patients)         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ↓                                   │
│  STEP 4: EVENT & OUTCOME GENERATION                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Generate realistic:                                      │    │
│  │   • Adverse events (type, severity, timing)              │    │
│  │   • Visit compliance (within protocol windows)           │    │
│  │   • Functional scores (with expected trajectories)       │    │
│  │   • Protocol deviations (realistic patterns)             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ↓                                   │
│  STEP 5: VALIDATION                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Validate synthetic data:                                 │    │
│  │   • All patients meet I/E criteria                       │    │
│  │   • Event rates within literature confidence intervals   │    │
│  │   • Distributions pass statistical normality tests       │    │
│  │   • No impossible combinations (clinical plausibility)   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### TKA Synthetic Data Specification

| Data Type | Records | Generation Method | Validation |
|-----------|---------|-------------------|------------|
| **Patients** | 400 | Demographics from literature distributions; comorbidities from TKA population studies | All meet protocol I/E criteria |
| **Enrollment Timeline** | 400 | Dates following S-curve ramp-up; site staggering; 12-month enrollment period | Realistic enrollment curve shape |
| **Adverse Events** | ~60 | Event types and rates from AOANJRR/NJR; severity distribution from literature | Rates within registry CI |
| **Visits** | ~2,400 | 6 visits per patient per protocol SOA; timing with realistic variance | 95% within protocol windows |
| **Surgeries** | 400 | Procedure details from protocol; implant data randomized | Matches protocol device specs |
| **Functional Scores** | ~1,600 | KSS/OKS at each timepoint; improvement trajectories from literature | Mean/SD matches published data |

#### DES Synthetic Data Specification

| Data Type | Records | Generation Method | Validation |
|-----------|---------|-------------------|------------|
| **Patients** | 300 | Demographics from PCI population; cardiac risk factors from literature | All meet protocol I/E criteria |
| **Enrollment Timeline** | 300 | Dates following S-curve ramp-up; site staggering; 10-month enrollment period | Realistic enrollment curve shape |
| **MACE Events** | ~24 | 8% event rate from literature; time-to-event from survival curves | Rates within NCDR CI |
| **TLR/TVR Events** | ~15 | Rates from published DES trials; correlated with lesion complexity | Matches literature benchmarks |
| **Visits** | ~1,800 | 6 visits per patient; angiographic follow-up per protocol | Per protocol SOA |
| **Lab Values** | ~3,600 | Cardiac biomarkers with realistic ranges and trajectories | Within clinical reference ranges |

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA FLOW ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ ClinicalTrials   │    │ Registry Reports │                   │
│  │ .gov Protocols   │    │ (AOANJRR/NJR/    │                   │
│  │ (PDF)            │    │  NCDR)           │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ Protocol         │    │ Benchmark        │                   │
│  │ Extraction       │    │ Extraction       │                   │
│  │ (LLM Pipeline)   │    │ (Manual Curation)│                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│  ┌────────┴───────────────────────┴────────┐                    │
│  │                                         │                    │
│  │  ┌──────────────┐    ┌──────────────┐  │                    │
│  │  │ PMS/Complaints│    │ CRM/Surgeon  │  │                    │
│  │  │ Data         │    │ Database     │  │                    │
│  │  └──────────────┘    └──────────────┘  │                    │
│  │                                         │                    │
│  │  ┌──────────────┐    ┌──────────────┐  │                    │
│  │  │ Financial    │    │ eTMF/ISF     │  │                    │
│  │  │ Systems      │    │ Documents    │  │                    │
│  │  └──────────────┘    └──────────────┘  │                    │
│  │                                         │                    │
│  │  ┌──────────────┐    ┌──────────────┐  │                    │
│  │  │ Manufacturing│    │ Service &    │  │                    │
│  │  │ QMS          │    │ Repair Logs  │  │                    │
│  │  └──────────────┘    └──────────────┘  │                    │
│  │                                         │                    │
│  └─────────────────────┬───────────────────┘                    │
│                        │                                        │
│                        ▼                                        │
│  ┌──────────────────────────────────────────┐                   │
│  │              YAML CONFIGURATION           │                   │
│  │  protocol.json │ benchmarks.yaml │ hr.yaml│                   │
│  └──────────────────────────────────────────┘                   │
│                          │                                       │
│           ┌──────────────┼──────────────┐                       │
│           ▼              ▼              ▼                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │ Synthetic   │ │ Literature  │ │ PostgreSQL  │                │
│  │ Data        │ │ Embeddings  │ │ Database    │                │
│  │ Generator   │ │ (pgvector)  │ │ (study data)│                │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                │
│         │               │               │                        │
│         └───────────────┼───────────────┘                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────┐                   │
│  │           SPECIALIZED AGENTS (12)         │                   │
│  │  Data │ Safety │ Literature │ Registry │  │                   │
│  │  Financial │ Sentiment │ Competitive      │                   │
│  └──────────────────────────────────────────┘                   │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────┐                   │
│  │            PERSONA AGENTS (6)             │                   │
│  │  PM │ Sales │ Marketing │ ClinOps │       │                   │
│  │  Strategy │ Quality                       │                   │
│  └──────────────────────────────────────────┘                   │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────┐                   │
│  │           API + FRONTEND                  │                   │
│  │  Dashboards │ Chat │ Reports │ Export     │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema (PostgreSQL)

#### Core Study Tables

| Table | Purpose | Key Columns | Source |
|-------|---------|-------------|--------|
| `study_patients` | Patient demographics | patient_id, age, gender, bmi, comorbidities | Synthetic |
| `study_adverse_events` | AE/SAE records | patient_id, ae_term, severity, is_sae, outcome | Synthetic |
| `study_visits` | Visit compliance | patient_id, visit_type, visit_date, status | Synthetic |
| `study_surgeries` | Procedure data (TKA) | patient_id, surgery_date, implant_type | Synthetic |
| `study_scores` | Functional outcomes | patient_id, score_type, timepoint, value | Synthetic |
| `study_labs` | Lab values (DES) | patient_id, lab_type, value, date | Synthetic |

#### Reference & Intelligence Tables

| Table | Purpose | Key Columns | Source |
|-------|---------|-------------|--------|
| `registry_benchmarks` | Registry comparators | registry_id, metric, value, ci_lower, ci_upper | Public (curated) |
| `literature_publications` | Paper metadata | pub_id, title, year, pmid, evidence_level | Public (PubMed) |
| `literature_embeddings` | RAG vectors | pub_id, chunk_id, embedding (pgvector) | Generated |
| `protocol_rules` | Protocol configuration | rule_type, parameters, thresholds | Extracted |

#### Enterprise Tables (Planned)

| Table | Purpose | Key Columns | Source |
|-------|---------|-------------|--------|
| `complaints` | Complaint records | complaint_id, product, failure_mode, severity, date | PMS |
| `capa_records` | CAPA tracking | capa_id, trigger, status, effectiveness, impl_date | QMS |
| `site_budgets` | Financial data | site_id, budget_total, spent, forecast, variance | Finance |
| `surgeon_profiles` | HCP data | surgeon_id, specialty, volume, products, region | CRM |
| `manufacturing_lots` | Lot tracking | lot_id, product, facility, date, env_conditions | QMS |
| `service_logs` | Repair records | log_id, device_id, technician_notes, issue_type | Service |

---

## ML/DL Predictive Capabilities

The platform incorporates 9 ML/DL predictive models organized in three tiers, designed to work with limited synthetic training data (400 TKA patients + 300 DES patients = 700 total).

### Capability Summary

| Tier | Capability | Model Type | Libraries | Status |
|------|------------|------------|-----------|--------|
| **1** | Enrollment Forecasting | Prophet/ARIMA | prophet, statsmodels | Planned |
| **1** | Survival Analysis | Kaplan-Meier, Cox PH | lifelines, scikit-survival | Planned |
| **1** | Safety Signal Detection | Bayesian SPRT, CUSUM | scipy, pymc | Planned |
| **1** | Risk Stratification (Enhanced) | Ensemble + Calibration | xgboost, lightgbm | Partial |
| **2** | Outcome Trajectory Prediction | LSTM/GRU + LMM fallback | pytorch, statsmodels | Planned |
| **2** | Protocol Deviation Prediction | Gradient Boosting | catboost | Planned |
| **3** | NLP Safety Signal Extraction | LLM (Gemini/Azure OpenAI) | google-generativeai, openai | Planned |
| **3** | Literature Evidence Classification | LLM (Gemini/Azure OpenAI) | google-generativeai, openai | Planned |
| **3** | Functional Recovery Prediction | GMM (simplified) | sklearn.mixture | Planned |

### Tier Definitions

| Tier | Focus | Data Requirements | Implementation Priority |
|------|-------|-------------------|------------------------|
| **Tier 1** | Foundation statistical methods | Works with current dataset | High - enables core analytics |
| **Tier 2** | Advanced predictive models | Benefits from larger datasets | Medium - enhances forecasting |
| **Tier 3** | Deep learning & NLP | Requires transfer learning | Lower - specialized use cases |

### Tier 1: Foundation Capabilities

#### 1.1 Enrollment Forecasting

**Models:** Prophet + ARIMA ensemble

| Component | Details |
|-----------|---------|
| **Features** | Historical enrollment rates, site activation dates, screening-to-enrollment ratios, seasonal patterns |
| **Output** | Enrollment timeline with confidence intervals, site-level forecasts, completion probability |
| **Integration** | Enhances `simulation_service.py` with time-series enrollment forecasting |
| **Applicability** | Both (TKA and DES) |

**Note:** Demonstrates technical integration with synthetic enrollment curves. Production deployment requires real historical enrollment data for accurate forecasting. Synthetic patterns are algorithmically generated and may not reflect real-world enrollment dynamics (COVID disruptions, site ramp-up variability, seasonal effects).

#### 1.2 Survival Analysis

**Models:** Kaplan-Meier, Cox Proportional Hazards, Weibull AFT

| Component | Details |
|-----------|---------|
| **Features** | Time-to-event (TKA: revision; DES: MACE, TLR, TVR), patient covariates (age, BMI, comorbidities), device/procedural characteristics |
| **Output** | Survival curves, hazard ratios with CI, benchmark comparisons (AOANJRR/NJR for TKA, NCDR for DES) |
| **Integration** | Provides statistical foundation for risk stratification and regulatory analysis |
| **Applicability** | Both (TKA and DES) |

#### 1.3 Safety Signal Detection

**Models:** Bayesian Sequential Probability Ratio Test (SPRT), CUSUM charts

| Component | Details |
|-----------|---------|
| **Features** | AE counts by type, expected event rates from literature, temporal patterns |
| **Output** | Signal scores, early warning alerts, disproportionality metrics (PRR, ROR) |
| **Integration** | Enhances `safety_service.py` with statistical signal detection |
| **Applicability** | Both (TKA and DES) |

**Note:** Statistical power limited with ~100 total events. Signals require clinical validation before action.

#### 1.4 Enhanced Risk Stratification

**Models:** Ensemble (XGBoost + LightGBM + Logistic Regression) with SHAP explanations

| Component | Details |
|-----------|---------|
| **Features** | 50+ covariates (demographics, functional scores, comorbidities, surgical/procedural factors) |
| **Output** | Calibrated risk probabilities, feature importance rankings, individual explanations |
| **Integration** | Enhances `risk_service.py` with ensemble predictions and model interpretability |
| **Applicability** | Both (TKA and DES) |

### Tier 2: Advanced Capabilities

#### 2.1 Outcome Trajectory Prediction

**Model:** LSTM/GRU neural network with linear mixed models (LMM) fallback

| Component | Details |
|-----------|---------|
| **Features** | Longitudinal functional scores (KSS/OKS for TKA, Seattle Angina Questionnaire for DES), visit patterns, interventions, baseline characteristics |
| **Output** | Predicted score trajectories at future timepoints, trajectory cluster assignments, deviation alerts |
| **Integration** | Enhances `simulation_service.py` with patient-specific outcome forecasting |
| **Applicability** | Both (TKA and DES) |

**Note:** Falls back to linear mixed models if LSTM performance inadequate due to sample size.

#### 2.2 Protocol Deviation Prediction

**Model:** CatBoost gradient boosting

| Component | Details |
|-----------|---------|
| **Features** | Site history, patient complexity, scheduling patterns, coordinator workload |
| **Output** | Per-patient deviation probability, deviation type predictions, risk flags |
| **Integration** | Enhances `deviation_service.py` with predictive alerts for proactive intervention |
| **Applicability** | Both (TKA and DES) |

**Note:** Uses SMOTE oversampling or class weights to handle expected 90%+ non-deviation rate.

### Tier 3: Deep Learning & NLP Capabilities

#### 3.1 NLP Safety Signal Extraction

**Model:** LLM-based extraction (Gemini/Azure OpenAI)

| Component | Details |
|-----------|---------|
| **Features** | Free-text adverse event narratives, clinical notes |
| **Output** | Standardized MedDRA terms, severity classification, causality assessment |
| **Method** | Zero-shot/few-shot prompting with structured output schemas |
| **Integration** | Enhances `safety_service.py` with automated AE coding |
| **Applicability** | Both (TKA and DES) |

#### 3.2 Literature Evidence Classification

**Model:** LLM-based classification (Gemini/Azure OpenAI)

| Component | Details |
|-----------|---------|
| **Features** | Publication abstracts, full-text sections, study design metadata |
| **Output** | Evidence level (I-IV per Oxford CEBM), quality scores, relevance ranking |
| **Method** | Structured prompts with Oxford CEBM criteria; chain-of-thought reasoning |
| **Integration** | Enhances `literature_service.py` with automated evidence grading |
| **Applicability** | Both (TKA and DES) |

#### 3.3 Functional Recovery Prediction

**Model:** Gaussian Mixture Models (simplified)

| Component | Details |
|-----------|---------|
| **Features** | Subgroup characteristics, early functional scores, baseline biomarkers, surgical/procedural factors |
| **Output** | Recovery phenotype classification (2-3 phenotypes: optimal/suboptimal; TKA: KSS/OKS trajectory; DES: angina relief), trajectory predictions |
| **Integration** | Supports patient counseling on expected recovery and identifies candidates for enhanced rehabilitation |
| **Applicability** | Both (TKA and DES) |

**Note:** Limited to 2-3 recovery phenotypes (optimal/suboptimal) rather than fine-grained clustering due to sample size constraints.

### Data Strategy for Synthetic Training Data

Given the synthetic training data (400 TKA patients + 300 DES patients = 700 total), the platform employs several strategies to maximize model performance:

| Strategy | Application | Benefit |
|----------|-------------|---------|
| **Transfer Learning** | Prophet pre-trained seasonality; LLM zero-shot for NLP | Leverage pre-trained knowledge |
| **LLM Zero-Shot/Few-Shot** | Gemini/Azure OpenAI for NLP tasks | Leverage pre-trained knowledge without fine-tuning |
| **Cross-Study Learning** | Combined TKA + DES datasets for shared features (demographics, comorbidities, visit compliance) | Increase effective sample size for common patterns |
| **Bayesian Priors** | Literature-derived informative priors for all models | Incorporate external knowledge to stabilize estimates |
| **Cross-Validation** | Stratified k-fold (k=5) with careful train/test splits | Maximize use of data for validation |
| **Ensemble Methods** | Combine multiple weak learners | Reduce variance and improve generalization |
| **Strong Regularization** | L1/L2 penalties, dropout, early stopping | Prevent overfitting on synthetic datasets |

**Recommended Data Split (per therapeutic area):**
- Training: 70% (~490 patients total: 280 TKA + 210 DES)
- Validation: 15% (~105 patients total: 60 TKA + 45 DES)
- Test: 15% (~105 patients total: 60 TKA + 45 DES)

### Model Validation Requirements

| Requirement | Metric | Target |
|-------------|--------|--------|
| **Discrimination** | AUC-ROC | ≥0.70 for clinical utility |
| **Calibration** | Hosmer-Lemeshow | p > 0.05 |
| **Survival Models** | C-index (Harrell's) | ≥0.65 |
| **Trajectory Models** | MAE (Mean Absolute Error) | Model-specific |
| **Classification (NLP)** | F1-score (macro) | ≥0.75 |
| **External Validation** | Independent test set | Required before deployment |
| **Clinical Review** | SME sign-off | Required for each model |
| **Monitoring** | Drift detection | Continuous post-deployment |

### Service Integration Points

| Existing Service | ML Enhancement |
|------------------|----------------|
| `risk_service.py` | + Enhanced ensemble models + SHAP explanations |
| `safety_service.py` | + Bayesian signal detection + LLM-based AE extraction |
| `simulation_service.py` | + Prophet enrollment forecasting + LSTM outcome trajectory |
| `deviation_service.py` | + Protocol deviation predictive alerts |
| `literature_service.py` | + LLM-based evidence classification |

---

## Technology Stack

### Backend

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI (Python 3.10+) |
| **Database** | PostgreSQL + pgvector |
| **ORM** | SQLAlchemy |
| **Data Processing** | pandas, numpy |
| **Validation** | Pydantic |

### ML/DL Libraries

| Category | Libraries |
|----------|-----------|
| **Time Series** | prophet, statsmodels (ARIMA, linear mixed models) |
| **Survival Analysis** | lifelines, scikit-survival |
| **Statistical** | scipy, pymc (Bayesian) |
| **Gradient Boosting** | xgboost, lightgbm, catboost |
| **Deep Learning** | pytorch (LSTM/GRU) |
| **LLM APIs** | google-generativeai (Gemini), openai (Azure OpenAI) |
| **Mixture Models** | sklearn.mixture (GMM) |
| **Explainability** | shap |

### Frontend

| Component | Technology |
|-----------|------------|
| **Framework** | React 18 + TypeScript |
| **Build** | Vite |
| **UI Components** | Shadcn/ui |
| **Charts** | Recharts |

### LLM Integration

| Provider | Usage |
|----------|-------|
| **Google Gemini** | Primary LLM for reasoning |
| **Azure OpenAI** | Fallback / consensus |

### Configuration

```
GEMINI_API_KEY          # Google API key
AZURE_OPENAI_API_KEY    # Azure API key
AZURE_OPENAI_ENDPOINT   # Azure endpoint
DATABASE_URL            # PostgreSQL connection
```

### Intelligent Caching

Multi-tier caching architecture optimizes performance and reduces API costs across all platform layers.

```
┌─────────────────────────────────────────────────────────────────┐
│                   INTELLIGENT CACHING ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIER 1: LLM RESPONSE CACHE                                     │
│  ─────────────────────────                                       │
│  • Semantic query hashing for similar prompt detection           │
│  • TTL-based expiration (configurable per query type)            │
│  • Cost reduction for repeated LLM API calls                     │
│                                                                  │
│  TIER 2: API ENDPOINT CACHE                                     │
│  ─────────────────────────                                       │
│  • Async warmup on application startup                           │
│  • Background refresh (15-minute default interval)               │
│  • Endpoint-specific TTL configuration                           │
│                                                                  │
│  TIER 3: DATA LAYER CACHE                                       │
│  ─────────────────────────                                       │
│  • Query result caching for expensive computations               │
│  • Invalidation on data updates                                  │
│  • Memory-efficient LRU eviction policy                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Cache Tier | Target | Strategy | TTL | Benefit |
|------------|--------|----------|-----|---------|
| **LLM Response** | Gemini/Azure OpenAI calls | Semantic hash matching | 1-24 hours | 60-80% API cost reduction |
| **API Endpoint** | UC1-UC20 endpoints | Async warmup + refresh | 15 minutes | Sub-second response times |
| **Data Layer** | PostgreSQL queries | LRU with invalidation | Query-dependent | Reduced DB load |

**Cache Invalidation Triggers:**
- Manual refresh via API endpoint
- Data modification events (patient updates, new AEs)
- TTL expiration with background refresh
- Memory pressure (LRU eviction)

---

## Limitations & Guardrails

### Current Limitations

| Limitation | Status | Mitigation |
|------------|--------|------------|
| **LLM Hallucination** | Mitigated | All responses cite specific sources; confidence scoring |
| **ML Risk Model** | Disabled | Model AUC=0.51; using clinical hazard ratios instead |
| **Query Latency** | Acceptable | Caching with async warmup (15-min refresh) |
| **Token Limits** | Managed | Chunked document processing; max_output_tokens enforced |

### Data Constraints

- Both protocols from **ClinicalTrials.gov** (publicly available)
- TKA patient data is **synthetic** (no real PHI)
- Registry data from **public annual reports** only (AOANJRR, NJR, NCDR)
- Literature from **PubMed open access** subset

### What's NOT Implemented

| Feature | Status |
|---------|--------|
| Commercial/Sales data integration | Planned |
| Post-market surveillance (MDR, complaints) | Planned |
| Manufacturing/Quality data | Planned |
| Real-world evidence (claims, EHR) | Not implemented |
| Production validation (IQ/OQ/PQ) | Not completed |
| Multi-study support | Single study only |

---

## User Personas

> **PoC Feasibility Summary by Persona:**
> | Persona | Overall Feasibility | Demonstrable Prompts | Notes |
> |---------|---------------------|---------------------|-------|
> | Product Manager | 🟡 **55%** | 4 of 7 | Safety/clinical yes, recall risk/regulatory docs limited |
> | Sales | 🟡 **45%** | 3 of 7 | Literature rebuttals yes, CRM/surgeon data no |
> | Marketing | 🟢 **65%** | 5 of 7 | SOTA/literature strong, congress abstracts limited |
> | Clinical Ops | 🟡 **55%** | 4 of 7 | Protocol compliance yes, eTMF/financial limited |
> | Strategy | 🔴 **25%** | 2 of 7 | Registry trends yes, VoC/sentiment no |
> | Quality Head | 🟠 **30%** | 2 of 7 | Synthetic complaints possible, vigilance/RMF no |

### Persona 1: Product Manager (The "Product Guardian") 🟡

**Objective:** Oversee product lifecycle health, safety signals, and clinical success to prevent recalls and maintain market leadership.

**PoC Feasibility: 55%** - Strong on clinical trial analytics and safety monitoring. Limited on recall risk (requires real complaint data) and regulatory document gaps (requires real eTMF).

**Primary Modules:**
- Safety Monitoring
- Executive Dashboard
- Regulatory Readiness
- Patient Risk
- Data Sources

**Core Use Cases:**
- **Safety Risk Monitoring**: Identifying early-warning signals in adverse events (AEs)
- **Clinical Performance Tracking**: Monitoring revision rates vs. industry benchmarks
- **Regulatory Compliance**: Tracking document completeness for MDR/FDA

**RBAC Policy:** Full safety data, registry access, regulatory documents, patient-level data for safety analysis

**Strategic AI Prompts:**

1. 🟢 **Safety Correlation:** *"Analyze the study and identify if there is any statistical correlation between component size and the incidence of complications across all study sites."*

2. 🟢 **Benchmark Analysis:** *"Compare the 2-year survivorship of our product (98.1%) against the bottom 25% of similar systems in the National Joint Registry."*

3. 🔴 **Recall Risk Assessment:** *"Review the last 12 months of device deficiency reports. Is there a rising trend in specific mechanical failures that warrants a proactive field safety notice?"* *(Requires real complaint/deficiency data)*

4. 🟢 **Demographic Impact:** *"Identify if revision rates are significantly higher in patients with a BMI over 35, and recommend if instructions for use (IFU) should be updated."*

5. 🔴 **Regulatory Gap Analysis:** *"Check the document repository and list all required 'Clinical Evaluation Reports' (CER) that are missing or will expire within the next 6 months."* *(Requires real eTMF/document repository)*

6. 🟢 **Site-Specific Performance:** *"Identify which clinical study sites have a revision rate that is >2 standard deviations away from the study mean, and list the common surgeons at those sites."*

7. 🟢 **Data Synthesis:** *"Summarize all intraoperative complications reported in the study and categorize them by 'Device-Related' vs. 'Procedure-Related'."*

---

### Persona 2: Sales (The "Competitive Closer") 🟡

**Objective:** Use real-world evidence and clinical data to defend market share and convert competitor surgeons.

**PoC Feasibility: 45%** - Literature-based competitive analysis strong. CRM/surgeon database integration not available for champion identification.

**Primary Modules:**
- Sales Intelligence
- Competitive Benchmarking
- Literature Intelligence
- Data Browser

**Core Use Cases:**
- **Competitive Battle Cards**: Instant evidence-based rebuttals
- **Economic Value Modeling**: Proving cost-savings via clinical superiority
- **HCP Relationship Management**: Identifying brand champions through data

**RBAC Policy:** Aggregated clinical data, competitive data, surgeon performance metrics, no patient-level data

**Strategic AI Prompts:**

1. 🟢 **The Rebuttal:** *"Draft a rebuttal for a surgeon currently using a competitor system, specifically highlighting our 88.5% success rate versus the 76.3% found in our control group."*

2. 🟢 **Outcome Visualizer:** *"Extract the functional score improvements (from 43.9 to 92.9) and generate a summary showing mobility gains for sedentary patients."*

3. 🟢 **Competitor Weakness:** *"Search recent literature for known complications of 'Competitive Product X' and cross-reference them with our study to show how our product avoids those issues."*

4. 🟡 **Procurement Pitch:** *"Calculate the predicted 5-year revision cost savings for a hospital if they switch from a competitor with a 94% survival rate to our observed 100% survival."* *(Survival data available; hospital-specific economics limited)*

5. 🟢 **Technical Deep-Dive:** *"Provide a simple explanation of the material benefits in our liners compared to standard UHMWPE for a surgeon who is concerned about long-term wear."*

6. 🔴 **Champion Identification:** *"Based on recent registry data, identify surgeons in the Northeast region who are publishing high-success rates using our implants."* *(Requires CRM/surgeon database)*

7. 🔴 **Sales Scripting:** *"Generate a 30-second elevator pitch for our stemless system based on the anatomical restoration data found in our internal white papers."* *(Requires internal white papers)*

---

### Persona 3: Marketing (The "Brand Storyteller") 🟢

**Objective:** Translate complex clinical data into compelling market claims and "State-of-the-Art" content.

**PoC Feasibility: 65%** - Literature synthesis and SOTA generation are strong. Congress abstracts (copyrighted competitor content) and internal CSRs limited.

**Primary Modules:**
- Literature Intelligence
- Document Generation
- Content Studio
- Competitive Benchmarking

**Core Use Cases:**
- **State-of-the-Art (SOTA) Reporting**: Automated synthesis of market trends
- **Claim Validation**: Ensuring all marketing copy is clinically supported
- **Patient Education**: Simplifying clinical outcomes for patient-facing content

**RBAC Policy:** Published data, evidence summaries, aggregated outcomes, no raw patient data or PII

**Strategic AI Prompts:**

1. 🟢 **SOTA Generation:** *"Generate a comprehensive 'State-of-the-Art' report for stemless arthroplasty using internal CSRs and the last 3 years of PubMed publications."*

2. 🟢 **Claim Validator:** *"Check if the claim 'Industry-leading safety' is supported by the AE rates in our study compared to three major competitors."*

3. 🟢 **Patient Success Narrative:** *"Identify 'super-responder' patients in the study (those with >50 point functional score improvement) and draft a de-identified patient success story for our website."*

4. 🟢 **Visual Data Extraction:** *"Create a table comparing the responder rates (89.8%) from our latest study against the industry average for similar procedures."*

5. 🔴 **Congress Intelligence:** *"Scan competitor abstracts from the latest major meeting and identify the top three themes being used to market competitive products."* *(Requires copyrighted congress abstracts - cannot synthesize)*

6. 🟢 **Channel Optimization:** *"Draft a series of LinkedIn posts targeting orthopedic surgeons that highlight the 0% device-related adverse events in our study."*

7. 🟡 **Brand Perception:** *"Analyze the language used in recent Clinical Investigation Reports to identify the most frequently used positive adjectives to describe our system."* *(Limited to available synthetic CSR data)*

---

### Persona 4: Clinical Operations (The "Compliance & Financial Lead") 🟡

**Objective:** Manage the execution, data integrity, and complex financials of global clinical studies.

**PoC Feasibility: 55%** - Protocol compliance and deviation monitoring strong with synthetic data. Financial systems and eTMF require enterprise integration.

**Primary Modules:**
- Financial Dashboard
- Protocol Deviations
- Protocol Digitization
- Data Browser

**Core Use Cases:**
- **Financial Tracking**: Monitoring CRO costs, site payments, and budget forecasts
- **Study Oversight**: Enrollment tracking and protocol deviation monitoring
- **GCP Compliance**: Ensuring eTMF and ISF completeness

**RBAC Policy:** Full study data, financial data, compliance documents, patient-level data for data management

**Strategic AI Prompts:**

1. 🟠 **Financial Forecast:** *"Analyze the current CRO change orders and provide a budget estimate for the remaining 24 months of the 5-year follow-up period."* *(Can demo with synthetic financials; limited business value)*

2. 🟠 **Automated Site Payments:** *"Calculate the total site payments due for Q4 by cross-referencing completed eCRF visits with the per-patient fee schedule in the site contracts."* *(Can demo workflow; requires real contracts)*

3. 🟢 **Site Risk Alert:** *"Identify study sites that have an enrollment rate <50% of their target but have consumed >80% of their allocated budget."*

4. 🟢 **MedDRA Coding Check:** *"Scan the 'Other' category in our AE reports and suggest the correct MedDRA coding for entries that mention 'persistent joint discomfort'."*

5. 🔴 **Document Audit:** *"Review the electronic Trial Master File (eTMF) and flag any sites where the Principal Investigator's medical license has expired."* *(Requires real eTMF - cannot synthesize)*

6. 🟢 **Missing Data Analysis:** *"Identify sites with a >20% rate of 'Lost to Follow-up' and analyze if there is a correlation between patient age and study withdrawal."*

7. 🟢 **Protocol Compliance:** *"Search for all reported protocol deviations related to 'post-operative imaging window' and identify which sites require additional training."*

---

### Persona 5: Strategy (The "Visionary") 🔴

**Objective:** Refine the product portfolio, monitor user sentiment, and identify long-term market opportunities.

**PoC Feasibility: 25%** - Most strategy prompts require VoC/sentiment data (real human feedback). Registry survivorship trends are demonstrable with public data.

**Primary Modules:**
- Portfolio Health
- Simulation Studio
- Competitive Benchmarking
- Data Browser

**Core Use Cases:**
- **Portfolio Health & Sentiment**: Analyzing the "Voice of the Customer" from registries and surveys
- **Product Refinement Strategy**: Identifying gaps in current designs based on clinical feedback
- **Macro-Trend Analysis**: Monitoring the impact of regulatory changes and market shifts

**RBAC Policy:** Cross-portfolio data, market trends, aggregated feedback, surgeon CRM data for market analysis

**Strategic AI Prompts:**

1. 🔴 **Sentiment Gap Analysis:** *"Analyze surgeon feedback from Investigator-Initiated Studies (IIS) and identify the top 3 requested refinements for the next generation of our product."* *(Requires real IIS/surgeon feedback - synthetic opinions are meaningless)*

2. 🟢 **Portfolio Sustainability:** *"Compare 10-year survivorship trends of our cemented vs. uncemented portfolios. Should we shift R&D focus based on the aging demographic trends in the EU?"*

3. 🔴 **Voice of Customer (VoC):** *"Perform a sentiment analysis on the last 100 internal surveys regarding our instrumentation. Is the feedback on 'ease of use' improving or declining compared to 2022?"* *(Requires real survey data - cannot synthesize sentiment)*

4. 🟡 **Competitive Threat Assessment:** *"Evaluate the risk of new 'robotics-assisted' systems on our current manual portfolio based on clinical success trends in registry data."* *(Registry trends available; market data limited)*

5. 🟢 **Refinement Opportunity:** *"Examine the fracture rate in our study. Based on patient bone-density data, should we develop a 'reinforced' version for high-risk osteoporotic patients?"*

6. 🔴 **Global Market Entry:** *"Simulate the clinical evidence requirements needed to launch our portfolio in the Japanese market based on recent PMDA regulatory shifts."* *(Requires regulatory intelligence feeds)*

7. 🔴 **Interdisciplinary Advice:** *"Based on all clinical and sales data, recommend whether we should pursue a 'value-segment' product or continue focusing on 'premium-tech' revisions."* *(Requires real sales data)*

---

### Persona 6: Quality Head 🟠

**Mission:** To ensure zero-defect manufacturing, proactive risk mitigation, and a state of "perpetual audit readiness." This persona owns the feedback loop between real-world complaints and internal process improvements.

**PoC Feasibility: 30%** - Can demonstrate workflow with synthetic complaints/CAPA data. However, vigilance reporting, RMF updates, and manufacturing correlation require real enterprise data that cannot be meaningfully synthesized.

**Primary Modules:**
- Complaints Hub
- CAPA Dashboard
- Safety Monitoring
- Data Sources

**Specialized Module Features (Quality-Specific):**
- **Complaints Management Hub**: AI-driven triage center that categorizes incoming reports, detects trending failure modes, and automates Medical Device Reporting (MDR/Vigilance) decisions
- **CAPA & Vigilance Dashboard**: Real-time tracking of Corrective and Preventive Actions (CAPAs), linking them directly to the clinical or manufacturing data that triggered them
- **Risk Management File (RMF) Live Link**: Automatically flags when a "Real-World" complaint or adverse event exceeds the predicted "Risk Occurrence" levels defined in the product's technical file
- **Post-Market Surveillance (PMS) Analytics**: Correlates complaint data with sales volumes to calculate "Complaints Per Million" (CPM) and identify geographic or batch-specific quality clusters

**Core Use Cases:**
- **Complaints Management**: AI-driven categorization and trend detection
- **CAPA & Vigilance**: Tracking corrective actions and regulatory reporting
- **Post-Market Surveillance Analytics**: CPM calculation and cluster identification

**RBAC Policy:** All quality data, manufacturing data, complaint records, patient-level data for vigilance reporting

**Strategic AI Prompts:**

1. 🔴 **Trend Detection vs. Sales Volume:** *"Analyze the complaint rate over the last 18 months. Normalize the data against sales volume (CPM) and identify if the 5% increase in 'liner wear' reports is statistically significant or a byproduct of market growth."* *(Requires real complaints + sales volume data)*

2. 🔴 **Root Cause Cross-Analysis:** *"Cross-reference recent complaints regarding 'baseplate loosening' with manufacturing lot numbers and clean-room environmental logs. Is there a correlation between these events and the batch produced in Q3 2024 at a specific facility?"* *(Requires real manufacturing/environmental data - cannot synthesize sensor logs)*

3. 🟠 **CAPA Effectiveness Check:** *"Review the effectiveness of CAPA-2023-004 (designed to address locking screw issues). Compare the incident rate in products manufactured before the fix versus those manufactured after the implementation."* *(Can demo workflow with synthetic CAPA; limited real value)*

4. 🔴 **Vigilance Reporting Logic:** *"A surgeon reported a 'suspected' material failure during a revision surgery. Based on FDA 21 CFR 803 and EU MDR Article 87, determine if this event meets the 'Serious Deterioration of Health' threshold and draft the initial Vigilance report."* *(Vigilance reports are regulatory artifacts - cannot meaningfully synthesize)*

5. 🔴 **Risk File Update:** *"Scan all post-market data. Identify any 'new' hazardous situations reported by surgeons that are not currently listed in the existing Risk Management File (RMF) for this device class."* *(Requires real RMF and post-market data)*

6. 🔴 **Silent Quality Signal Search:** *"Perform a sentiment analysis on the last 100 entries in the 'Service & Repair' logs. Are there recurring technician comments regarding 'instrument stiffness' that have not yet been escalated to a formal complaint?"* *(Requires real technician notes - synthetic comments are meaningless)*

7. 🟠 **Supplier Quality Audit Preparation:** *"Generate a 'Quality Scorecard' for our primary material supplier by aggregating all material-related complaints, incoming inspection failures, and clinical study deviations from the last 24 months."* *(Can demo workflow with synthetic data; limited real value)*

---

## API Endpoints

### Use Case Endpoints (UC1-UC8)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/uc1/readiness-assessment` | GET | Regulatory readiness report |
| `/api/v1/uc2/safety-summary` | GET | Safety signal analysis |
| `/api/v1/uc3/deviations-summary` | GET | Deviation detection |
| `/api/v1/uc4/population-risk` | GET | Risk stratification |
| `/api/v1/uc5/executive-summary` | GET | Executive dashboard |
| `/api/v1/uc6/literature-search` | POST | Literature intelligence & evidence synthesis |
| `/api/v1/uc7/generate-document` | POST | Document generation (DSMB, narratives) |
| `/api/v1/uc8/competitive-analysis` | GET | Competitive benchmarking |

### Extended Use Case Endpoints (UC9-UC20)

| Endpoint | Method | Purpose | Primary Persona |
|----------|--------|---------|-----------------|
| `/api/v1/uc9/recall-risk` | POST | Recall risk assessment | Product Manager |
| `/api/v1/uc10/battle-card` | POST | Competitive battle cards | Sales |
| `/api/v1/uc11/economic-value` | POST | Economic value modeling | Sales |
| `/api/v1/uc12/sota-report` | POST | SOTA report generation | Marketing |
| `/api/v1/uc13/financial-forecast` | POST | Financial forecast | Clinical Ops |
| `/api/v1/uc14/etmf-audit` | GET | eTMF audit | Clinical Ops |
| `/api/v1/uc15/portfolio-health` | GET | Portfolio health analysis | Strategy |
| `/api/v1/uc16/sentiment-analysis` | POST | Sentiment analysis (VoC) | Strategy |
| `/api/v1/uc17/complaints-triage` | POST | Complaints triage | Quality |
| `/api/v1/uc18/capa-effectiveness` | GET | CAPA effectiveness | Quality |
| `/api/v1/uc19/vigilance-report` | POST | Vigilance reporting | Quality |
| `/api/v1/uc20/pms-analytics` | GET | PMS analytics (CPM) | Quality |

### Supporting Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/chat/chat` | POST | Natural language queries |
| `/api/v1/protocol/overview` | GET | Protocol metadata |
| `/api/v1/simulation/monte-carlo` | POST | Outcome simulation |
| `/api/v1/data-browser/tables` | GET | Available tables |
| `/health/ready` | GET | Health check |

### ML/DL Predictive Endpoints

| Endpoint | Method | Purpose | Tier |
|----------|--------|---------|------|
| `/api/v1/ml/enrollment-forecast` | POST | Enrollment projections with confidence intervals | 1 |
| `/api/v1/ml/survival-analysis` | POST | Survival curves and hazard ratios | 1 |
| `/api/v1/ml/safety-signals` | POST | Bayesian signal detection and alerts | 1 |
| `/api/v1/ml/risk-stratification` | POST | Enhanced risk scores with SHAP explanations | 1 |
| `/api/v1/ml/outcome-trajectory` | POST | Patient outcome trajectory predictions | 2 |
| `/api/v1/ml/deviation-risk` | POST | Protocol deviation probability scores | 2 |
| `/api/v1/ml/extract-safety-terms` | POST | LLM-based MedDRA term extraction from narratives | 3 |
| `/api/v1/ml/classify-evidence` | POST | LLM-based literature evidence classification | 3 |
| `/api/v1/ml/functional-recovery` | POST | Recovery phenotype classification and prediction | 3 |

---

## Deployment

### Current Environment

| Aspect | Configuration |
|--------|---------------|
| **Backend** | FastAPI with uvicorn |
| **Frontend** | React SPA (Vite build) |
| **Database** | PostgreSQL with pgvector extension |
| **Hosting** | Replit (development) |

### Production Considerations (Future)

- HIPAA compliance for real patient data
- 21 CFR Part 11 validation
- SSO integration
- Audit logging
- Load balancing

---

## Summary

The Clinical Intelligence Platform v0.1 delivers a **functional proof-of-concept** demonstrating capabilities across **two therapeutic areas** with a **Persona-Driven Agentic Architecture** supporting **six enterprise personas**.

### PoC Feasibility Summary

| Category | PoC Ready | Partial | Synthetic Possible | Future Vision |
|----------|:---------:|:-------:|:------------------:|:-------------:|
| **Dashboard Modules** | 12 | 2 | 3 | 1 |
| **Use Cases (UC1-UC20)** | 9 | 4 | 3 | 4 |
| **Strategic Prompts (42)** | 16 (38%) | 6 (14%) | 4 (10%) | 16 (38%) |
| **Enterprise Data Sources** | 0 | 2 | 4 | 4 |

**Key Insight**: The PoC demonstrates strong value for **clinical trial intelligence** (safety, compliance, literature, competitive analysis) but has limited coverage for **post-market/enterprise workflows** (Quality, Strategy personas) that require real organizational data.

### Capability Matrix by Persona

| Capability | PM | Sales | Mktg | ClinOps | Strategy | Quality |
|------------|:--:|:-----:|:----:|:-------:|:--------:|:-------:|
| Safety signal detection | ✅ | — | — | ✅ | — | ✅ |
| Registry benchmarking | ✅ | ✅ | ✅ | — | ✅ | — |
| Competitive analysis | ✅ | ✅ | ✅ | — | ✅ | — |
| Literature intelligence | ✅ | ✅ | ✅ | — | ✅ | — |
| Document generation | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| Risk stratification | ✅ | — | — | ✅ | — | ✅ |
| Financial tracking | — | — | — | ✅ | ✅ | — |
| Complaints management | ✅ | — | — | — | — | ✅ |
| CAPA tracking | — | — | — | — | — | ✅ |
| Sentiment analysis | — | — | — | — | ✅ | ✅ |
| Portfolio analysis | — | — | — | — | ✅ | — |
| Protocol compliance | ✅ | — | — | ✅ | — | — |

### Platform Summary

| Capability | TKA | DES | Status |
|------------|-----|-----|--------|
| Two-tier agent architecture (6 Persona + 12 Specialized) | ✅ | ✅ | Operational |
| Goal-based planning & orchestration | ✅ | ✅ | Operational |
| RBAC-controlled data access (6 personas) | ✅ | ✅ | Operational |
| Natural language clinical queries | ✅ | ✅ | Operational |
| Regulatory readiness assessment | ✅ | ✅ | Operational |
| Safety signal detection | ✅ | ✅ | Operational |
| Protocol deviation detection | ✅ | — | TKA Only |
| Patient risk stratification | ✅ | — | TKA Only |
| Registry benchmarking | ✅ | ✅ | Operational |
| Literature intelligence & evidence synthesis | ✅ | ✅ | Operational |
| Document generation (DSMB, narratives) | ✅ | ✅ | Operational |
| Competitive benchmarking | ✅ | ✅ | Operational |
| Monte Carlo simulation | ✅ | ✅ | Operational |
| Provenance tracking | ✅ | ✅ | Operational |
| Protocol digitization (USDM 4.0) | ✅ | ✅ | Operational |
| ML/DL Predictive Capabilities (9 models) | ✅ | ✅ | Planned |
| Extended Use Cases (UC9-UC20) | ✅ | ✅ | Planned |
| Enterprise Data Integration (PMS, CRM, eTMF, Financial) | ✅ | ✅ | Planned |

**Key Differentiators**:
- **Persona-Driven Architecture**: 6 Goal-based Persona Agents orchestrate 12 Specialized Agents with RBAC enforcement
- **Enterprise-Wide Coverage**: Supports Product Manager, Sales, Marketing, Clinical Ops, Strategy, and Quality personas
- **42 Strategic AI Prompts**: 7 pre-built prompts per persona demonstrating platform capabilities
- **Cross-Therapeutic Extensibility**: Same architecture supports orthopedics (TKA) and cardiovascular (DES) with configuration-only changes
- **Evidence-to-Document Pipeline**: Seamless flow from literature search to regulatory document generation
- **Advanced ML/DL Stack**: 9 predictive models across 3 tiers (foundation, advanced, LLM-powered NLP)
- **20 Use Cases**: Comprehensive coverage from regulatory readiness to vigilance reporting

---

*Document Version: 0.1.2*
*Full Scope: TKA + DES | 6 Personas | 19 Modules (1 Foundation + 18 Operational) | 6 Persona Agents + 13 Specialized Agents | 9 ML/DL Models | 20 Use Cases | 42 Strategic Prompts*

**PoC Demonstrable Scope:**
- *Data: Synthetic clinical trials + Public registries (AOANJRR/NJR/NCDR) + PubMed open-access literature*
- *Personas: 4 with high feasibility (PM 55%, Marketing 65%, Sales 45%, Clinical Ops 55%)*
- *Use Cases: UC1-UC8 fully demonstrable, UC10-UC12 partially*
- *Strategic Prompts: 16 fully demonstrable (38%), 6 partial (14%), 4 synthetic workflow (10%)*

**Future Vision (Requires Enterprise Data Integration):**
- *Personas: Strategy (25%), Quality (30%) - require VoC/PMS/manufacturing data*
- *Use Cases: UC9, UC13-UC14, UC16, UC19-UC20 require enterprise systems*
- *Strategic Prompts: 16 require enterprise data (38%)*

*Status: Proof-of-Concept with clear PoC vs Future Vision separation*
