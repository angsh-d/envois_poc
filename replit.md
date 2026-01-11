# H-34 Clinical Intelligence Platform

## Overview
A multi-agent AI system for clinical data analysis, risk assessment, and regulatory compliance for the H-34 DELTA Revision Cup post-market clinical study.

## Project Structure
```
├── app/
│   ├── agents/          # AI agents (data, protocol, literature, etc.)
│   ├── api/             # FastAPI routers
│   ├── services/        # Business logic services
│   ├── config.py        # Configuration settings
│   └── main.py          # FastAPI application entry point
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
The API server runs on port 5000 using uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

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
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key (alternative)
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL

## Tech Stack
- Python 3.11
- FastAPI (web framework)
- LangChain (LLM orchestration)
- ChromaDB (vector store)
- Google Gemini / Azure OpenAI (LLM providers)

## Recent Changes
- 2026-01-11: Initial setup in Replit environment, configured to run on port 5000
