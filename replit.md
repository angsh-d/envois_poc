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
Two workflows run concurrently:
- **Frontend** (port 5000): `cd client && npm run dev` - React frontend with Apple-inspired UI
- **API Server** (port 8000): `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` - FastAPI backend

## Frontend Pages
- `/` - Executive Dashboard (UC5) with KPIs, readiness, safety signals
- `/readiness` - Regulatory Readiness (UC1) with gap analysis
- `/safety` - Safety Signals (UC2) with cross-source contextualization
- `/deviations` - Protocol Deviations (UC3) with Document-as-Code detection
- `/risk` - Patient Risk (UC4) with ML-powered stratification

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
