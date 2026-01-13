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
- `/docs` - API documentation (Swagger UI)
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
- ChromaDB (vector store)
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

## Recent Changes
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

## Current Status
- Frontend: React + Vite + Tailwind running on port 5000
- Backend: FastAPI running on port 8000
- Chat: Gemini 2.0 Flash with context-aware prompts for each module
- All 5 use case pages rendering with mock study data
- Chat panel available on all study pages for contextual AI assistance
