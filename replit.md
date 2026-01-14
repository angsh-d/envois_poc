# H-34 Clinical Intelligence Platform

## Overview
A multi-agent AI system for clinical data analysis, risk assessment, and regulatory compliance for the H-34 DELTA Revision Cup post-market clinical study. Features an Apple-inspired React frontend with comprehensive dashboards for all 5 use cases.

## Project Structure
```
├── app/
│   ├── agents/          # AI agents (data, protocol, literature, etc.)
│   ├── api/             # FastAPI routers
│   ├── services/        # Business logic services
│   ├── config.py        # Configuration settings
│   └── main.py          # FastAPI application entry point
├── client/              # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── components/  # Reusable UI components (Card, Button, Badge, etc.)
│   │   ├── pages/       # Page components for each use case
│   │   ├── lib/         # Utility functions
│   │   └── App.tsx      # Main application with routing
│   └── vite.config.ts   # Vite configuration
├── data/
│   ├── loaders/         # Data loading utilities
│   ├── ml/              # Machine learning models
│   ├── processed/       # Processed YAML rules
│   ├── raw/             # Raw study data, PDFs
│   └── vectorstore/     # ChromaDB vector store
├── prompts/             # LLM prompt templates
└── requirements.txt     # Python dependencies
```

## Running the Application
Single consolidated workflow:
- **Full Stack App** (port 5000): FastAPI (port 5000) reverse-proxies to Vite dev server (port 5173)
- Run command: `bash -c "cd client && npm run dev & sleep 2 && uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload"`

## Frontend Pages
- `/` - Landing page with platform overview
- `/study/h34-delta` or `/study/h34-delta/dashboard` - Executive Dashboard (UC5) with KPIs, readiness, safety signals
- `/study/h34-delta/readiness` - Regulatory Readiness (UC1) with gap analysis
- `/study/h34-delta/safety` - Safety Signals (UC2) with cross-source contextualization
- `/study/h34-delta/deviations` - Protocol Deviations (UC3) with Document-as-Code detection
- `/study/h34-delta/risk` - Patient Risk (UC4) with ML-powered stratification
- `/study/h34-delta/protocol` - Digital Protocol with SOA, Eligibility, and Domain views
- `/study/h34-delta/data-agents` - Data & Agents catalog with data sources, AI/ML models, and agent architecture

## API Endpoints
- `/health` - Health check
- `/ready` - Readiness check
- `/api/docs` - API documentation (Swagger UI)
- `/api/v1/uc1/*` - Regulatory Readiness endpoints
- `/api/v1/uc2/*` - Safety Signals endpoints
- `/api/v1/uc3/*` - Protocol Deviations endpoints
- `/api/v1/uc4/*` - Risk Stratification endpoints
- `/api/v1/uc5/*` - Executive Dashboard endpoints

## Environment Variables
The application uses the following environment variables (optional):
- `GEMINI_API_KEY` - Google Gemini API key for LLM features

## Tech Stack
### Backend
- Python 3.11
- FastAPI (web framework)
- LangChain (LLM orchestration)
- PostgreSQL with pgvector (vector store)
- Google Gemini (LLM provider)

### Frontend
- React 18 + TypeScript
- Vite 7 (build tool)
- Tailwind CSS 4 (styling)
- React Query (data fetching)
- Wouter (routing)
- Lucide React (icons)

## Design System
Apple-inspired design with:
- Clean, minimal aesthetic with generous whitespace
- SF Pro / Inter typography
- Black/white/gray color palette with semantic accents
- Rounded corners (2xl) and subtle shadows
- Smooth transitions and hover states

## Database Architecture
All structured and vector data is stored in PostgreSQL with the following tables:
- **protocol_rules**: Protocol definitions (protocol_id, version, sample sizes, thresholds)
- **protocol_visits**: Visit windows and timing rules
- **protocol_endpoints**: Primary and secondary endpoint definitions
- **protocol_documents**: USDM JSON documents (SOA, eligibility criteria, full USDM)
- **literature_publications**: Published study benchmarks and outcomes
- **literature_risk_factors**: Risk factor hazard ratios from literature
- **registry_benchmarks**: International registry norms (AOANJRR, NJR, SHAR, AJRR, CJRR)
- **study_patients**: H-34 study patient demographics
- **study_adverse_events**: Adverse event records
- **study_scores**: Patient outcome scores (HHS, VAS, etc.)
- **study_surgeries**: Surgical procedure details
- **embeddings**: pgvector-indexed document embeddings for RAG

### Hybrid Data Loader
Data loading uses a hybrid approach (database-first with file fallback):
- `get_hybrid_loader()` tries database first, falls back to local YAML files
- Enables seamless transition and zero-downtime migration
- All services and agents use database-backed loaders

## Recent Changes
- 2026-01-14: REGISTRY BENCHMARKS EXTRACTION - Downloaded 5 official registry annual reports (AOANJRR 43MB/629pg, NJR 26MB/406pg, SHAR 17MB/294pg, AJRR 11MB/145pg, CJRR 1.8MB/89pg). Extracted verified survival rates and revision reasons with full provenance. NJR: 6 survival timepoints from Table 3.H16 (page 165). SHAR: 15yr survival from Figure 5.4.19 (page 123). CJRR: 11 revision reasons from Table 11 (page 28). AJRR survival excluded (graphical-only presentation). Scripts: extract_registry.py, extract_registry_targeted.py, load_registry_to_db.py
- 2026-01-14: LITERATURE BENCHMARKS RE-EXTRACTION - Complete re-extraction of literature data using Gemini 3 Pro Preview. 4 publications (Singh 2016, Steckel 2025, Bazan 2025, Vasios 2025) processed with full provenance (page numbers, table references, exact quotes). Database updated with 8 verified hazard ratios and 33 aggregate benchmarks. MCID thresholds: 18 points (2yr), 15.9 points (5yr). Scripts: extract_literature.py, load_literature_to_db.py
- 2026-01-14: LITERATURE BENCHMARKS AUDIT - CRITICAL FAILURE: Complete mismatch between YAML citations and actual PDFs. YAML contains 6 fabricated publications (bozic_2015, della_valle_2020, etc.) that DO NOT EXIST in the 12 PDFs in data/raw/literature/. Actual PDFs are 2025 papers by Bazan, Steckel, Vasios, etc. on hip/shoulder/knee arthroplasty. Data is synthetic/demonstration only. Full audit in docs/literature_benchmarks_audit_report.md
- 2026-01-14: CHAT KEY EVIDENCE FIX - Fixed issue where Key Evidence always showed registry data regardless of question. Added evidence building for Data Agent (study safety metrics, adverse events) and Literature Agent (publication benchmarks). Evidence is now contextual based on which agents are queried for each question.
- 2026-01-14: SAFETY UI/UX REFINEMENTS - Enhanced Safety Metrics table with visual rate bars (green/red progress indicators), color-coded severity dots (pulsing red for HIGH, amber for LOW), improved event display ("3 of 37 patients"), gradient backgrounds for expanded panels, premium card styling with shadows, rose-themed affected patients panel, purple-themed literature panel, and enhanced formula/methodology display with icons.
- 2026-01-14: SAFETY SIGNALS TRANSPARENCY - Enhanced Safety page with comprehensive data provenance for each metric: SQL query sources (study_adverse_events, study_patients, protocol_rules), methodology explanations, calculation formulas, threshold attribution. Added affected patients panel with demographics (gender, age, BMI) from database. Added literature citations panel from literature_publications table. Fixed API URL mismatch (signals vs summary endpoint). Rewrote Safety.tsx with expandable detail rows for full transparency.
- 2026-01-14: PROTOCOL DATA AUDIT - Comprehensive field-by-field validation of protocol_rules against USDM source documents. Fixed: sample_size_target (50→49), age requirement (≥21→≥18), added evaluable_population (29), ltfu_assumption (0.40), updated power calculation (90% power, alpha=0.025, one-sided paired t-test). Full audit report in docs/protocol_rules_audit_report.md
- 2026-01-14: Updated protocol_rules.yaml with correct USDM values and provenance citations for sample size, eligibility criteria, and safety thresholds
- 2026-01-14: Fixed Digital Protocol → Protocol Rules tab to display correct values (evaluable population instead of interim analysis, LTFU assumption instead of dropout allowance)
- 2026-01-13: Enhanced Benchmarking table in Dashboard - fixed metric casing (HHS, OHS, MCID), added tooltips with explanations and examples, clarified data sources (H-34 Study vs Published Literature)
- 2026-01-13: CRITICAL BUG FIX - Fixed compliance rate calculation showing -54% instead of ~70%. Changed deviation_rate from (total_deviations/total_visits) to (visits_with_timing_deviations/total_visits). Added visits_with_deviations and compliant_visits fields to API response.
- 2026-01-13: Migrated all structured data from files to PostgreSQL - protocol rules, literature benchmarks, registry norms, study data (patients, AEs, scores, surgeries)
- 2026-01-13: Created hybrid data loader with database-first and file-fallback strategy
- 2026-01-13: Updated all services and agents to use get_hybrid_loader() instead of get_doc_loader()
- 2026-01-13: Redesigned Protocol Domains tab with modern UI - insight pills in card headers, visual timeline for study epochs, premium arm cards with interventions, improved generic renderer with better visual hierarchy, Apple-inspired greyscale styling
- 2026-01-13: Migrated vector store from ChromaDB to PostgreSQL with pgvector - using Replit's managed database for persistent vector embeddings storage with HNSW index
- 2026-01-13: Enhanced Data & Agents page - added Protocol-as-Code & USDM JSON data section (soa_usdm.json, eligibility_criteria.json, usdm_4.0.json), Vector Store & Semantic Index section, Structured Rules (YAML) section, and data sources layer in architecture diagram with agent mapping table
- 2026-01-13: Added expandable detail rows to Safety Metrics table - clicking on active signals (Dislocation Rate, Fracture Rate) expands to show Affected Patients (with contributing factors), Literature Context (benchmarks from literature_benchmarks), and Recommendations panels
- 2026-01-13: Added Data & Agents page - moved data sources from Dashboard modal to dedicated page in side nav, added Agents tab with multi-agent architecture visualization and detailed agent documentation
- 2026-01-13: Added download endpoints for protocol JSON files (SOA USDM, Eligibility Criteria, USDM 4.0) with download buttons on Digital Protocol tabs
- 2026-01-13: Renamed "Protocol" to "Digital Protocol" in side navigation
- 2026-01-13: Fixed Dashboard and Safety page routing - added `/study/:studyId/dashboard` route to App.tsx, updated React Query to use staleTime: 0 with refetchOnMount: 'always' for immediate data fetching
- 2026-01-13: Fixed caching issues for Dashboard, Readiness, and Safety pages - updated global QueryClient settings (refetchOnMount: true, staleTime: 5min) and fixed cache warmup service method calls
- 2026-01-13: Enhanced Concomitant Meds domain - now shows required medications, rescue/supportive medications, prohibited/restricted meds, washout requirements, drug interactions, herbal supplements policy, and vaccine policy with full detail cards (purpose, timing, dosing, impact on endpoints)
- 2026-01-13: Fixed Protocol Domains rendering - applied safeRenderValue helper across all domain renderers (Laboratory, PRO, Imaging, etc.) to handle code objects
- 2026-01-13: Enhanced Patient Risk module with detailed cohorts, factor prevalence, and actionable recommendations
- 2026-01-13: Fixed React rendering error in Readiness.tsx - added safeRenderValue helpers for code objects
- 2026-01-12: Added Saama-branded top navbar with search and user profile
- 2026-01-11: Full platform operational with all 5 use case modules
- 2026-01-11: Contextual AI chat integrated with Gemini LLM
- 2026-01-11: Apple-inspired frontend with clean, minimal design
- 2026-01-11: Landing page, Dashboard, Readiness, Safety, Deviations, Risk pages complete
- 2026-01-11: Chat API endpoint with context-aware prompting
- 2026-01-11: Initial setup in Replit environment

## Deployment Configuration
- **Deployment Target**: Autoscale (stateless, scales based on traffic)
- **Build Command**: `cd client && npm install && npm run build`
- **Run Command**: `uvicorn app.main:app --host 0.0.0.0 --port 5000`
- **Production Detection**: `REPLIT_DEPLOYMENT=1` environment variable
- **Static Files**: Served from `client/dist` in production mode

## Current Status
- Frontend: React + Vite + Tailwind running on port 5000
- Backend: FastAPI reverse-proxying to Vite on port 5000 (development) or serving static files (production)
- Database: All data loaded from PostgreSQL (37 patients, 15 AEs, 224 scores, 4 verified publications with provenance, 8 hazard ratios, 33 benchmarks, 5 registries)
- Chat: Gemini 2.0 Flash with context-aware prompts for each module
- All 5 use case pages rendering with real study data from database
- Chat panel available on all study pages for contextual AI assistance
- Production-ready with optimized 486KB JS bundle
