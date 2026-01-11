# H-34 DELTA Revision Cup Study - Clinical Intelligence Platform

A multi-agent AI system for clinical data analysis, risk assessment, and regulatory compliance for the H-34 DELTA Revision Cup post-market clinical study.

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/angsh-d/envois_poc.git
cd envois_poc
```

### 2. Create Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.template .env
# Edit .env with your API keys:
# - GEMINI_API_KEY
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_DEPLOYMENT
# - AZURE_OPENAI_API_VERSION
```

### 4. Initialize Data (First Run Only)
```bash
# Train the risk prediction model
python -m data.ml.train_risk_model

# Build ChromaDB vector store (happens automatically on first query)
```

### 5. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API at: http://localhost:8000
API Documentation: http://localhost:8000/docs

## Architecture

The system uses a **Multi-Agent AI Architecture** with 7 specialized agents:

| Agent | Purpose |
|-------|---------|
| **Orchestrator** | Routes queries, coordinates agents, synthesizes responses |
| **Data Agent** | Patient data retrieval, cohort analysis, statistical queries |
| **Protocol Agent** | Protocol compliance, eligibility verification |
| **Literature Agent** | RAG-based literature search using ChromaDB |
| **Registry Agent** | Registry benchmarking (AOANJRR, NJR, AJRR) |
| **Risk Agent** | XGBoost risk prediction with hazard ratio calculation |
| **Synthesis Agent** | Response generation with confidence scoring |

## Key Features

- **Confidence Thresholds**: All responses include confidence levels (HIGH/MODERATE/LOW/INSUFFICIENT)
- **"I Don't Know" Capability**: System admits uncertainty rather than hallucinating
- **Provenance Tracking**: Every response includes source attribution
- **Anti-Hallucination Guardrails**: Prompts enforce data-grounded responses

## Project Structure

```
enovis_poc/
├── app/
│   ├── agents/          # AI agents (orchestrator, data, protocol, etc.)
│   ├── api/             # FastAPI endpoints
│   ├── core/            # Configuration, dependencies
│   └── services/        # Business logic services
├── data/
│   ├── loaders/         # Excel, YAML, hazard ratio loaders
│   ├── ml/              # Risk model training
│   ├── processed/       # Document-as-code YAML rules
│   ├── raw/             # Study data, literature PDFs
│   └── vectorstore/     # ChromaDB for RAG
├── prompts/             # LLM prompt templates
└── docs/                # Additional documentation
```

## Documentation

- [BACKEND_DESIGN.md](BACKEND_DESIGN.md) - Technical backend architecture
- [HIGH_LEVEL_POC_DESIGN.md](HIGH_LEVEL_POC_DESIGN.md) - POC overview and business context
- [USE_CASES.md](USE_CASES.md) - Detailed use case specifications
- [FILE_INVENTORY.md](FILE_INVENTORY.md) - Complete file inventory

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Natural language query interface |
| `/api/patients/{id}` | GET | Patient data retrieval |
| `/api/patients/{id}/risk` | GET | Patient risk assessment |
| `/api/cohort/analysis` | POST | Cohort statistical analysis |
| `/api/protocol/compliance` | POST | Protocol compliance check |

## Environment Requirements

- Python 3.10+
- API Keys: Gemini API and/or Azure OpenAI
- ~500MB disk space for vector store and models

## Regenerating Data Assets

If ChromaDB or ML models are missing, they will be regenerated:

```bash
# Retrain risk model
python -m data.ml.train_risk_model

# ChromaDB rebuilds automatically when Literature Agent is first used
```

## License

Proprietary - Enovis Corporation
