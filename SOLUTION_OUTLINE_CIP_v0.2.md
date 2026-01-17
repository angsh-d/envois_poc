# Clinical Intelligence Platform (CIP) - Solution Outline v0.2

> **Document Version:** 0.2 | **Focus:** Current Implementation + Enterprise Roadmap
> **Study:** H-34 DELTA Revision Cup Study | **Product Domain:** Hip Revision
> **Date:** January 2026

---

## Executive Summary

This document describes the **Clinical Intelligence Platform (CIP)** as currently implemented for the H-34 DELTA Revision Cup Study, and maps the enterprise vision for 6 organizational personas to the existing capabilities. The platform is a production-grade, AI-powered clinical study analytics system built on FastAPI, React, PostgreSQL, and multi-model LLM orchestration.

### Current Implementation vs. Enterprise Vision

| Dimension | ✅ Currently Implemented | 🎯 Enterprise Vision |
|-----------|-------------------------|----------------------|
| **Study Focus** | H-34 DELTA Revision Cup (Hip Revision) | Multi-product, multi-indication |
| **Primary Persona** | Clinical Operations | 6 Personas (PM, Sales, Marketing, ClinOps, Strategy, Quality) |
| **API Endpoints** | 10 functional endpoints | 20+ use case endpoints |
| **Specialized Agents** | 8 functional agents | 12 specialized + 6 persona agents |
| **Database Tables** | 15 tables (PostgreSQL + pgvector) | 25+ tables (PMS, CRM, eTMF, Finance) |
| **ML Models** | 1 (XGBoost Risk Stratification) | 9 ML/DL models |
| **Services** | 10 backend services | 15+ services |
| **Protocol Deviation Detectors** | 6 detectors | 10+ detectors |

### Feasibility Legend

| Icon | Status | Description |
|------|--------|-------------|
| 🟢 | **Implemented** | Fully functional in current system |
| 🟡 | **Demonstrable** | Can be demonstrated with current data/synthetic data |
| 🟠 | **Near-term** | Achievable within 2-3 sprints |
| 🔴 | **Future Vision** | Requires new data integrations |

---

## Part 1: Current Implementation

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        REACT FRONTEND                                │
│  Dashboard │ Chat │ Simulation │ Data Browser │ Protocol Viewer      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (v1.0.0)                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    API ROUTERS (10)                              │ │
│  │  UC1: Readiness │ UC2: Safety │ UC3: Deviations │ UC4: Risk     │ │
│  │  UC5: Dashboard │ Chat │ Simulation │ Data Browser │ Health     │ │
│  │  Protocol Digitization                                           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                    │                                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                  SPECIALIZED AGENTS (9)                          │ │
│  │  Data │ Protocol │ Literature │ Registry │ Safety │ Synthesis   │ │
│  │  Compliance │ Code │ Base                                        │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                    │                                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │             PROTOCOL DEVIATION DETECTORS (6)                     │ │
│  │  Visit Timing │ Missing Assessment │ Missed Visit │ I/E Violation│ │
│  │  Consent Timing │ AE Reporting                                   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                    │                                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     SERVICES LAYER                               │ │
│  │  LLM Service │ Cache Service │ Prompt Service                    │ │
│  │  Readiness │ Safety │ Deviations │ Risk │ Dashboard │ MonteCarlo │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌─────────────────────────────────────┐    ┌─────────────────┐
│           PostgreSQL                │    │   ML Models     │
│   15 tables + pgvector (RAG)        │    │   (XGBoost)     │
│   Gemini text-embedding-004         │    │                 │
└─────────────────────────────────────┘    └─────────────────┘
```

### 1.2 Implemented API Endpoints

| Endpoint | Use Case | Description | Status |
|----------|----------|-------------|--------|
| `GET /api/v1/uc1/readiness` | Study Readiness | Protocol rules, visit windows, endpoints, enrollment metrics | 🟢 |
| `GET /api/v1/uc2/safety` | Safety Analysis | AE rates, revision rates, safety signals with LLM synthesis | 🟢 |
| `GET /api/v1/uc3/deviations` | Protocol Deviations | 6-detector automated deviation identification | 🟢 |
| `GET /api/v1/uc4/risk` | Risk Stratification | ML-based patient risk scoring | 🟢 |
| `GET /api/v1/uc5/dashboard` | Executive Dashboard | Comprehensive study overview | 🟢 |
| `POST /api/v1/chat` | Conversational AI | Multi-agent chat interface | 🟢 |
| `POST /api/v1/simulation/monte-carlo` | Trial Simulation | Monte Carlo outcome projections | 🟢 |
| `GET /api/v1/data-browser/*` | Data Browser | Paginated data exploration across tables | 🟢 |
| `POST /api/v1/protocol/digitize` | Protocol Digitization | AI-powered protocol parsing | 🟢 |
| `GET /health` | Health Check | System health monitoring | 🟢 |

### 1.3 Implemented Agents (8 Functional + Base Infrastructure)

| Agent | Purpose | Key Capabilities |
|-------|---------|------------------|
| **Data Agent** | Data retrieval & transformation | SQL generation, data validation, aggregation |
| **Protocol Agent** | Protocol compliance | Rule extraction, visit window validation |
| **Literature Agent** | Evidence synthesis | pgvector RAG-based literature search, benchmark extraction |
| **Registry Agent** | Registry benchmarking | AAOS/NJR/AOANJRR data comparison |
| **Safety Agent** | Safety monitoring | AE classification, signal detection |
| **Synthesis Agent** | Multi-source synthesis | Cross-agent orchestration, narrative generation |
| **Compliance Agent** | Deviation detection | Visit window checking, missing assessment detection |
| **Code Agent** | Dynamic code execution | Statistical analysis, visualization |

*Note: Base Agent provides shared infrastructure (not a functional agent)*

### 1.4 Backend Services (10 Services)

| Service | Purpose | Key Functions |
|---------|---------|---------------|
| **LLM Service** | Model orchestration | Gemini/Azure OpenAI calls, prompt rendering |
| **Prompt Service** | Template management | Load/render prompts from /prompts/*.txt |
| **Cache Service** | Response caching | TTL cache, warmup, background refresh |
| **Readiness Service** | UC1 orchestration | Protocol rules, enrollment metrics |
| **Safety Service** | UC2 orchestration | AE analysis, revision rates, signals |
| **Deviations Service** | UC3 orchestration | 6-detector coordination |
| **Risk Service** | UC4 orchestration | ML model + hazard ratio integration |
| **Dashboard Service** | UC5 orchestration | Aggregate metrics, narratives |
| **Monte Carlo Service** | Simulation | Trial outcome projections |
| **Protocol Digitization** | Protocol parsing | PDF → structured JSON extraction |

### 1.5 Database Schema (15 Tables)

**Protocol & Configuration (4 tables)**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `protocol_rules` | Protocol configuration | protocol_id, version, sample_size_target, safety_thresholds |
| `protocol_visits` | Visit windows | visit_id, target_day, window_minus/plus, required_assessments |
| `protocol_endpoints` | Endpoints | endpoint_id, endpoint_type, success_threshold, mcid_threshold |
| `protocol_documents` | Protocol JSON (USDM, SOA) | document_type, content (JSON), source_file |

**Literature & Benchmarks (5 tables)**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `literature_publications` | Literature corpus | publication_id, year, journal, n_patients, benchmarks |
| `literature_risk_factors` | Risk factors | factor, hazard_ratio, confidence_interval_low/high |
| `aggregate_benchmarks` | Pooled benchmarks | metric, mean, median, sd, concern_threshold |
| `registry_benchmarks` | Registry data | registry_id, survival_1yr-15yr, revision_rates |
| `registry_pooled_norms` | Pooled norms | total_procedures, survival_rates, concern_thresholds |

**Study Data (5 tables)**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `study_patients` | Patient records | patient_id, demographics, status, surgery_date |
| `study_adverse_events` | Safety data | ae_id, is_sae, severity, device_relationship |
| `study_scores` | HHS/OHS scores | score_type, follow_up, total_score, components |
| `study_visits` | Visit data | visit_type, visit_date, days_from_surgery |
| `study_surgeries` | Surgery data | surgical_approach, implant_details, surgery_time |

**Derived Data (1 table)**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `hazard_ratio_estimates` | Extracted HRs | factor, hazard_ratio, p_value, outcome |

*Note: Deviations, risk scores, and simulation results are calculated at runtime, not persisted*

### 1.6 Protocol Deviation Detectors

| Detector | Logic | Severity Classification |
|----------|-------|------------------------|
| **Visit Timing** | Actual vs. protocol window | Major: >30 days | Minor: ≤30 days |
| **Missing Assessment** | Required assessments not collected | Major: Primary endpoint | Minor: Secondary |
| **Missed Visit** | Scheduled visit not performed | Major: Primary timepoint | Minor: Other |
| **I/E Violation** | Inclusion/Exclusion criteria breach | Major: All I/E violations |
| **Consent Timing** | ICF signed after study procedures | Major: All consent violations |
| **AE Reporting** | SAE reporting timeline (24-72hr) | Major: SAE >24hr | Minor: AE >72hr |

### 1.7 ML Model: Risk Stratification

```
Model: XGBoost Classifier
Training: Literature-derived risk factors + study data
Features:
  - Patient demographics (age, sex, BMI)
  - Surgical factors (ASA score, revision indication)
  - Clinical history (prior surgeries, comorbidities)
Output: Risk score (0-100) with factor attribution
Files: risk_model.joblib, risk_scaler.joblib
```

---

## Part 2: Persona Mapping to Current Capabilities

The CIP enterprise vision encompasses 6 organizational personas. Below we map each persona's requirements to current implementation status.

### 2.1 Persona 1: Clinical Operations (The "Compliance & Financial Lead") 🟢

**Objective:** Manage study execution, data integrity, and compliance

**Current Implementation Mapping:**

| Core Use Case | Current Capability | Status |
|--------------|-------------------|--------|
| Study Oversight | UC1 Readiness + UC5 Dashboard | 🟢 |
| Protocol Deviation Management | UC3 Deviations (6 detectors) | 🟢 |
| Safety Monitoring | UC2 Safety Analysis | 🟢 |
| Risk Stratification | UC4 ML-based Risk | 🟢 |
| Trial Simulation | Monte Carlo Simulation | 🟢 |
| GCP Compliance | Compliance Agent (deviation focus only) | 🟡 |
| Financial Tracking | Site budgets, CRO costs | 🔴 |
| eTMF Audit | Document completeness | 🔴 |

**Strategic AI Prompts:**

| Prompt | Status | Implementation |
|--------|--------|----------------|
| "What is the current enrollment pace, and are we on track to hit 29 evaluable by Month 36?" | 🟢 | UC1 + Simulation |
| "Flag any upcoming visit windows at risk of protocol deviations." | 🟢 | UC3 Deviations |
| "Summarize all major deviations this quarter with root cause analysis." | 🟢 | UC3 + Synthesis Agent |
| "Which patients are at highest risk for study discontinuation?" | 🟢 | UC4 Risk |
| "Generate a Monte Carlo projection for primary endpoint achievement." | 🟢 | Simulation endpoint |
| "Show me site-level financial burn rate vs. contract." | 🔴 | Requires Finance data |
| "What eTMF documents are missing for FDA inspection readiness?" | 🔴 | Requires eTMF integration |

---

### 2.2 Persona 2: Product Manager (The "Product Guardian") 🟡

**Objective:** Oversee product lifecycle health, safety signals, and clinical success

**Current Implementation Mapping:**

| Core Use Case | Current Capability | Status |
|--------------|-------------------|--------|
| Safety Risk Monitoring | UC2 Safety + Safety Agent | 🟢 |
| Clinical Performance Tracking | UC5 Dashboard | 🟢 |
| Revision Rate Analysis | Revision rate calculations | 🟢 |
| Literature Benchmarking | Literature Agent + RAG | 🟢 |
| Regulatory Readiness (MDR/FDA) | Compliance Agent (partial) | 🟡 |
| Recall Risk Assessment | Not implemented | 🔴 |
| Post-Market Surveillance | Not implemented | 🔴 |

**Strategic AI Prompts:**

| Prompt | Status | Implementation |
|--------|--------|----------------|
| "What is the current revision rate for H-34 vs. published benchmarks?" | 🟢 | UC2 + Literature Agent |
| "Are there any emerging safety signals that require attention?" | 🟢 | UC2 Safety Analysis |
| "Summarize the clinical evidence supporting product claims." | 🟢 | Literature Agent RAG |
| "Compare our outcomes to AAOS registry data." | 🟢 | Registry Agent |
| "Which patients show early signs of implant failure?" | 🟡 | UC4 Risk (partial) |
| "Generate a safety summary for regulatory submission." | 🟡 | Synthesis Agent |
| "What is the recall risk based on current complaint trends?" | 🔴 | Requires PMS data |

---

### 2.3 Persona 3: Strategy (The "Visionary") 🟡

**Objective:** Portfolio refinement, sentiment analysis, market opportunities

**Current Implementation Mapping:**

| Core Use Case | Current Capability | Status |
|--------------|-------------------|--------|
| Portfolio Health Analysis | Single-study dashboard | 🟡 |
| Trial Outcome Projections | Monte Carlo Simulation | 🟢 |
| Literature Trend Analysis | Literature Agent | 🟢 |
| Competitive Benchmarking | Registry Agent (partial) | 🟡 |
| Sentiment Analysis (VoC) | Not implemented | 🔴 |
| Product Refinement Strategy | Not implemented | 🔴 |
| Macro-Trend Analysis | Not implemented | 🔴 |

**Strategic AI Prompts:**

| Prompt | Status | Implementation |
|--------|--------|----------------|
| "What is the probability distribution of trial success?" | 🟢 | Monte Carlo Simulation |
| "How do our outcomes compare to published literature?" | 🟢 | Literature Agent |
| "What are the key risk factors affecting patient outcomes?" | 🟢 | UC4 + Literature Agent |
| "Summarize the competitive landscape for hip revision." | 🟡 | Literature Agent (partial) |
| "What is the 5-year survivorship trend across our portfolio?" | 🔴 | Requires multi-product data |
| "Analyze surgeon feedback sentiment for product refinement." | 🔴 | Requires VoC data |
| "What emerging technologies threaten our market position?" | 🔴 | Requires market intelligence |

---

### 2.4 Persona 4: Sales (The "Competitive Closer") 🟠

**Objective:** Use real-world evidence to defend market share and convert surgeons

**Current Implementation Mapping:**

| Core Use Case | Current Capability | Status |
|--------------|-------------------|--------|
| Evidence Summaries | Literature Agent | 🟢 |
| Registry Benchmarking | Registry Agent | 🟢 |
| Competitive Battle Cards | Not implemented | 🔴 |
| Economic Value Modeling | Not implemented | 🔴 |
| Surgeon Targeting | Not implemented | 🔴 |
| HCP Relationship Management | Not implemented | 🔴 |

**Strategic AI Prompts:**

| Prompt | Status | Implementation |
|--------|--------|----------------|
| "What is the clinical evidence supporting H-34 DELTA Cup?" | 🟢 | Literature Agent |
| "How do our revision rates compare to competitors?" | 🟡 | Registry Agent (can adapt) |
| "Generate talking points for orthopedic surgeon meeting." | 🟡 | Synthesis Agent (can adapt) |
| "Create a competitive rebuttal for [competitor product]." | 🔴 | Requires competitive data |
| "Which surgeons are high-volume hip revision specialists?" | 🔴 | Requires CRM data |
| "What is the economic value proposition vs. alternatives?" | 🔴 | Requires economic model |
| "Build a battle card for [competitor]." | 🔴 | Requires competitive data |

---

### 2.5 Persona 5: Marketing (The "Brand Storyteller") 🟠

**Objective:** Translate clinical data into market claims and SOTA content

**Current Implementation Mapping:**

| Core Use Case | Current Capability | Status |
|--------------|-------------------|--------|
| Literature Evidence | Literature Agent + RAG | 🟢 |
| State-of-the-Art Reporting | Literature Agent (partial) | 🟡 |
| Claim Validation | Not implemented | 🔴 |
| Patient Education Content | Not implemented | 🔴 |
| Congress Content | Not implemented | 🔴 |
| Social Media Content | Not implemented | 🔴 |

**Strategic AI Prompts:**

| Prompt | Status | Implementation |
|--------|--------|----------------|
| "What published evidence supports our product claims?" | 🟢 | Literature Agent |
| "Summarize the state-of-the-art for hip revision." | 🟡 | Literature Agent (can adapt) |
| "What are the key differentiators vs. competitors?" | 🟡 | Literature Agent (partial) |
| "Generate a SOTA report for regulatory submission." | 🔴 | Requires structured template |
| "Validate this marketing claim against clinical data." | 🔴 | Requires claim validation engine |
| "Create patient-friendly educational content." | 🔴 | Requires content generation |
| "Draft social media posts for upcoming congress." | 🔴 | Requires content generation |

---

### 2.6 Persona 6: Quality Head (The "Zero-Defect Leader") 🔴

**Objective:** Zero-defect manufacturing, complaints management, vigilance

**Current Implementation Mapping:**

| Core Use Case | Current Capability | Status |
|--------------|-------------------|--------|
| Safety Monitoring | UC2 Safety (clinical only) | 🟡 |
| Complaints Management | Not implemented | 🔴 |
| CAPA Management | Not implemented | 🔴 |
| Post-Market Surveillance | Not implemented | 🔴 |
| Vigilance Reporting | Not implemented | 🔴 |
| Manufacturing Analytics | Not implemented | 🔴 |

**Strategic AI Prompts:**

| Prompt | Status | Implementation |
|--------|--------|----------------|
| "What safety signals have emerged in clinical trials?" | 🟢 | UC2 Safety Analysis |
| "Correlate clinical outcomes with patient risk factors." | 🟢 | UC4 Risk |
| "Triage incoming complaints by severity and failure mode." | 🔴 | Requires PMS integration |
| "What is the complaint rate trend for this product family?" | 🔴 | Requires PMS data |
| "Generate a vigilance report for this MDR event." | 🔴 | Requires PMS + templates |
| "What CAPAs are overdue or ineffective?" | 🔴 | Requires CAPA system |
| "Analyze manufacturing lot quality vs. complaint rates." | 🔴 | Requires Manufacturing QMS |

---

## Part 3: Capability Expansion Roadmap

### 3.1 Phase 1: Near-term Enhancements (2-3 Sprints) 🟠

Build on existing infrastructure to expand persona coverage:

| Enhancement | Target Personas | Effort |
|-------------|-----------------|--------|
| **Competitive Benchmarking Module** | Sales, Marketing, PM | Medium |
| Extend Literature Agent to extract competitor data from publications | | |
| Add structured competitor comparison endpoint | | |
| | | |
| **SOTA Report Generation** | Marketing, PM | Medium |
| Create structured SOTA template | | |
| Add document generation endpoint | | |
| | | |
| **Financial Tracking Foundation** | Clinical Ops | Medium |
| Add site_budgets, cro_contracts tables | | |
| Create financial dashboard endpoint | | |
| | | |
| **Portfolio View Extension** | Strategy, PM | Low |
| Adapt dashboard for multi-product view | | |
| Add product-level aggregation | | |

### 3.2 Phase 2: New Data Integrations (3-6 Months) 🔴

| Data Source | Target Personas | Dependencies |
|-------------|-----------------|--------------|
| **Post-Market Surveillance (PMS)** | Quality, PM | MDR/complaint feeds |
| **eTMF/ISF** | Clinical Ops | Document management integration |
| **CRM/Surgeon Database** | Sales | Salesforce/Veeva integration |
| **Manufacturing QMS** | Quality | QMS API access |
| **Financial Systems** | Clinical Ops | ERP integration |

### 3.3 New Agents Required

| Agent | Purpose | Priority |
|-------|---------|----------|
| **Product Manager Agent** | Persona orchestration for PM | Phase 2 |
| **Sales Agent** | Competitive positioning, surgeon targeting | Phase 2 |
| **Marketing Agent** | Content generation, claim validation | Phase 2 |
| **Quality Agent** | Complaints triage, vigilance automation | Phase 2 |
| **Strategy Agent** | Portfolio analysis, sentiment synthesis | Phase 2 |
| **Financial Agent** | Budget analysis, forecasting | Phase 1 |
| **Sentiment Agent** | VoC analysis, feedback trends | Phase 2 |

---

## Part 4: Product Knowledge Builder (Foundation Module)

*Carried forward from v0.1 as essential infrastructure for multi-product expansion*

### 4.1 Concept

The **Product Knowledge Builder** is a human-in-the-loop module that configures the platform for a specific product by constructing a comprehensive knowledge corpus through collaborative AI-assisted curation.

### 4.2 Four-Phase Knowledge Construction

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCT KNOWLEDGE BUILDER                         │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 1: Protocol Ingestion                                         │
│  ├── Upload protocol PDF → AI extracts structured rules             │
│  ├── Human validates: visits, windows, endpoints, I/E criteria      │
│  └── Store in protocol_rules, protocol_visits, protocol_endpoints    │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 2: Literature Corpus Building                                 │
│  ├── AI performs deep research (PubMed, Cochrane, registries)       │
│  ├── Human curates: relevant publications, benchmark selection      │
│  └── Populate literature_publications, aggregate_benchmarks          │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 3: Rule Derivation                                            │
│  ├── AI proposes: deviation thresholds, safety rules, risk factors  │
│  ├── Human approves/modifies derived rules                          │
│  └── Store in deviation_classification, safety_thresholds            │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 4: Knowledge Validation                                       │
│  ├── AI generates test queries against knowledge base               │
│  ├── Human validates responses, identifies gaps                     │
│  └── Iterative refinement until knowledge base is complete          │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Implementation Status: 🟡 Demonstrable

The current H-34 DELTA study implementation demonstrates Phase 1-3 capabilities. The Protocol Digitization endpoint (`/api/v1/protocol/digitize`) provides the foundation for automated protocol ingestion.

---

## Part 5: Technical Implementation Details

### 5.1 LLM Integration

```yaml
Primary Models:
  - Gemini 2.5 Flash (fast inference)
  - Gemini 2.5 Pro (complex reasoning)
  - Azure OpenAI GPT-4 (consensus validation)

Configuration:
  - Max output tokens: Model-specific limits
  - Temperature: 0.1 (deterministic analysis)
  - Prompt templates: 11 external .txt files in /prompts/

Orchestration:
  - Multi-model consensus for critical decisions
  - Agent-specific model selection
  - Fallback chain on model failures
```

### 5.2 RAG Implementation (pgvector)

```yaml
Vector Store:
  - PostgreSQL with pgvector extension
  - Gemini text-embedding-004 for embeddings
  - Cosine similarity search

Document Types:
  - Protocol documents (USDM, SOA, eligibility)
  - Literature publications (PubMed, Cochrane)
  - Registry reports (AAOS, NJR, AOANJRR)

Chunking:
  - Document → PDF extraction → Text chunking → Embeddings → pgvector
```

### 5.3 Caching Strategy

```yaml
Cache Service:
  - In-memory cache with TTL
  - Background refresh for frequently accessed data
  - Cache warmup on startup

Cached Endpoints:
  - UC1 Readiness (60s TTL)
  - UC5 Dashboard (60s TTL)
  - Literature benchmarks (300s TTL)
```

### 5.4 Error Handling

```yaml
Custom Exceptions:
  - DatabaseUnavailableError → 503
  - DataNotFoundError → 404
  - DatabaseQueryError → 500
  - LLMServiceError → 503
  - StudyDataLoadError → 500
  - ConfigurationError → 500
```

---

## Part 6: RBAC Policy Framework

### 6.1 Current Implementation

Role-Based Access Control is designed but not yet enforced in the current PoC.

### 6.2 Planned Permission Matrix

| Permission | PM | Sales | Mktg | ClinOps | Strategy | Quality |
|------------|:--:|:-----:|:----:|:-------:|:--------:|:-------:|
| Patient-level data | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| Aggregated data | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Financial data | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Complaints data | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Manufacturing data | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Surgeon CRM data | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Competitive data | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Regulatory docs | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |

---

## Summary

### Current Capabilities

| Component | Count | Details |
|-----------|-------|---------|
| API Endpoints | 10 | UC1-UC5 + Chat + Simulation + Data Browser + Health + Protocol |
| Specialized Agents | 8 | Data, Protocol, Literature, Registry, Safety, Synthesis, Compliance, Code |
| Database Tables | 15 | Protocol (4), Literature/Registry (5), Study (5), Derived (1) |
| Protocol Deviation Detectors | 6 | Visit Timing, Missing Assessment, Missed Visit, I/E, Consent, AE |
| Services | 10 | LLM, Cache, Prompt, Readiness, Safety, Deviations, Risk, Dashboard, MonteCarlo, ProtocolDigitization |
| Prompt Templates | 11 | Narrative generation, extraction, RAG queries |
| ML Models | 1 | XGBoost Risk Stratification |
| Frontend Pages | 18 | Dashboard, Chat, Simulation, Data Browser, etc. |

### Persona Readiness (Realistic Assessment)

| Persona | Readiness | Implemented Prompts | Key Gaps |
|---------|-----------|---------------------|----------|
| Clinical Operations | 🟢 **5/7 (71%)** | Study oversight, deviations, safety, risk, simulation | Financial, eTMF |
| Product Manager | 🟡 **5/7 (71%)** | Safety, performance, literature, registry, risk | PMS, recall risk |
| Strategy | 🟡 **3/7 (43%)** | Simulation, literature, risk factors | Portfolio, VoC, market intel |
| Sales | 🟠 **2/7 (29%)** | Evidence, registry | Battle cards, CRM, economic |
| Marketing | 🟠 **2/7 (29%)** | Literature, differentiators | SOTA gen, claim validation |
| Quality | 🔴 **2/7 (29%)** | Clinical safety, risk correlation | PMS, CAPA, Manufacturing |

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, TailwindCSS |
| Backend | FastAPI, Python 3.10 |
| Database | PostgreSQL + pgvector (RAG) |
| Embeddings | Gemini text-embedding-004 |
| ML | XGBoost, scikit-learn, joblib |
| LLM | Gemini 2.5 Flash/Pro, Azure OpenAI GPT-4 |
| Deployment | Production-ready with CORS, error handling, caching |

---

*Version 0.2 | January 2026 | H-34 DELTA Revision Cup Study*
*Scope: Single Study (Current) → 6 Personas (Roadmap) | 10 Endpoints | 8 Agents | 15 Tables | 10 Services | 11 Prompts | 1 ML Model*
