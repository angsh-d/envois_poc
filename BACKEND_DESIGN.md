# Clinical Intelligence Platform - Backend System Design

## Document Information

| Field | Value |
|-------|-------|
| Version | 2.0 |
| Last Updated | 2026-01-11 |
| Status | Implementation Complete |
| Study | H-34 DELTA Revision Cup Study |

---

## Executive Summary

The Clinical Intelligence Platform is a **multi-agent AI system** for clinical trial analysis, providing regulatory readiness assessment, safety signal detection, protocol deviation tracking, patient risk stratification, and executive dashboards for the H-34 hip revision arthroplasty study.

**Key Capabilities:**
- RAG-based literature search over indexed PDFs
- XGBoost risk prediction with literature hazard ratio ensemble
- Document-as-Code execution patterns (YAML rule files)
- **Full provenance tracking for all outputs**
- **Confidence thresholds with "I don't know" responses**
- **Explicit reasoning and uncertainty quantification**
- Multi-source reasoning across protocol, study data, literature, and registry

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLINICAL INTELLIGENCE PLATFORM                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   UC1       │  │   UC2       │  │   UC3       │  │   UC4       │        │
│  │ Readiness   │  │  Safety     │  │ Deviations  │  │   Risk      │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                    │                                         │
│                          ┌─────────▼─────────┐                              │
│                          │       UC5         │                              │
│                          │    Dashboard      │                              │
│                          └─────────┬─────────┘                              │
│                                    │                                         │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐  │
│  │                          API ROUTERS                                   │  │
│  │  /uc1/* | /uc2/* | /uc3/* | /uc4/* | /uc5/* | /health                │  │
│  └─────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐  │
│  │                       SERVICE LAYER                                    │  │
│  │  readiness_service | safety_service | deviations_service              │  │
│  │  risk_service | dashboard_service | llm_service | prompt_service      │  │
│  └─────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐  │
│  │                       AGENT FRAMEWORK                                  │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │              CONFIDENCE & UNCERTAINTY LAYER                    │    │  │
│  │  │  ConfidenceLevel | UncertaintyInfo | CONFIDENCE_THRESHOLDS    │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │  ProtocolAgent | DataAgent | LiteratureAgent | RegistryAgent          │  │
│  │  ComplianceAgent | SafetyAgent | SynthesisAgent                       │  │
│  └─────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐  │
│  │                       DATA LAYER                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐ │  │
│  │  │ Study Data   │  │ Vector Store │  │    Document-as-Code          │ │  │
│  │  │ (Excel)      │  │ (ChromaDB)   │  │    (YAML Rules)              │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────────┘ │  │
│  │  ┌──────────────┐  ┌──────────────┐                                   │  │
│  │  │ ML Models    │  │ Prompts      │                                   │  │
│  │  │ (XGBoost)    │  │ (.txt)       │                                   │  │
│  │  └──────────────┘  └──────────────┘                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
enovis_poc/
├── app/
│   ├── api/
│   │   └── routers/                    # FastAPI route handlers
│   │       ├── health.py               # Health check endpoint
│   │       ├── uc1_readiness.py        # UC1: Regulatory readiness
│   │       ├── uc2_safety.py           # UC2: Safety signals
│   │       ├── uc3_deviations.py       # UC3: Protocol deviations
│   │       ├── uc4_risk.py             # UC4: Risk stratification
│   │       └── uc5_dashboard.py        # UC5: Executive dashboard
│   │
│   ├── agents/                         # Multi-agent framework
│   │   ├── base_agent.py               # Abstract base + orchestrator + confidence
│   │   ├── protocol_agent.py           # Protocol rules extraction
│   │   ├── data_agent.py               # Study data queries
│   │   ├── literature_agent.py         # RAG + benchmark extraction
│   │   ├── registry_agent.py           # Population norms
│   │   ├── compliance_agent.py         # Deviation detection
│   │   ├── safety_agent.py             # Signal detection + uncertainty
│   │   └── synthesis_agent.py          # Multi-agent combination + validation
│   │
│   ├── services/                       # Business logic layer
│   │   ├── llm_service.py              # Gemini + Azure OpenAI integration
│   │   ├── prompt_service.py           # Prompt template loading
│   │   ├── readiness_service.py        # UC1 orchestration
│   │   ├── safety_service.py           # UC2 orchestration
│   │   ├── deviations_service.py       # UC3 orchestration
│   │   ├── risk_service.py             # UC4 + ML model (real data)
│   │   └── dashboard_service.py        # UC5 aggregation (real data)
│   │
│   └── config.py                       # Configuration management
│
├── data/
│   ├── raw/
│   │   ├── study/                      # Excel data exports
│   │   ├── protocol/                   # Protocol PDF
│   │   ├── literature/                 # Literature PDFs (12 files)
│   │   └── registry/                   # Registry reports
│   │
│   ├── processed/
│   │   ├── document_as_code/           # Executable YAML rules
│   │   │   ├── protocol_rules.yaml     # Visit windows, endpoints
│   │   │   ├── literature_benchmarks.yaml  # Published benchmarks, HRs
│   │   │   └── registry_norms.yaml     # AOANJRR/NJR norms
│   │   └── extracted_hazard_ratios.yaml
│   │
│   ├── vectorstore/                    # ChromaDB + indexing
│   │   ├── chroma_store.py             # Vector store wrapper
│   │   ├── pdf_extractor.py            # PDF parsing + chunking
│   │   └── chroma_db/                  # Persisted embeddings
│   │
│   ├── loaders/                        # Data loading utilities
│   │   ├── excel_loader.py             # H34ExcelLoader
│   │   ├── yaml_loader.py              # Document-as-Code loader
│   │   └── hazard_ratio_extractor.py   # Dynamic HR extraction
│   │
│   ├── models/
│   │   └── unified_schema.py           # Pydantic data models
│   │
│   └── ml/                             # Machine learning
│       ├── train_risk_model.py         # XGBoost training script
│       ├── risk_model.joblib           # Trained model
│       ├── risk_scaler.joblib          # Feature scaler
│       └── model_metadata.json         # Model metrics
│
├── prompts/                            # LLM prompt templates
│   ├── literature_rag.txt
│   ├── hazard_ratio_extraction.txt
│   ├── safety_narrative.txt            # Updated with anti-hallucination
│   ├── deviation_narrative.txt
│   ├── risk_narrative.txt              # Updated with provenance requirements
│   ├── readiness_narrative.txt
│   ├── dashboard_narrative.txt
│   ├── literature_comparison.txt
│   └── synthesis_summary.txt           # Updated with confidence requirements
│
├── main.py                             # FastAPI application entry
└── .env                                # Environment configuration
```

---

## Agent Framework

### Base Agent Architecture

All agents inherit from `BaseAgent` which provides:
- LLM service integration (Gemini + Azure OpenAI)
- Prompt template loading
- Execution timing and monitoring
- **Provenance tracking infrastructure**
- **Confidence level calculation**
- **Uncertainty information tracking**
- **"I don't know" response capability**

```python
class BaseAgent(ABC):
    agent_type: AgentType

    async def execute(self, context: AgentContext) -> AgentResult
    async def call_llm(self, prompt, model, temperature) -> str
    async def call_llm_json(self, prompt, model, temperature) -> Dict
    def load_prompt(self, prompt_name, parameters) -> str
```

### Confidence and Uncertainty Framework

The platform implements a comprehensive confidence and uncertainty tracking system to prevent hallucination and ensure transparent AI outputs.

#### Confidence Levels

```python
class ConfidenceLevel(str, Enum):
    HIGH = "high"           # >= 0.8: Strong evidence, multiple sources
    MODERATE = "moderate"   # >= 0.6: Adequate evidence, single source
    LOW = "low"             # >= 0.4: Limited evidence, inference required
    INSUFFICIENT = "insufficient"  # < 0.4: Cannot make reliable statement
```

#### Confidence Thresholds by Response Type

| Response Type | Minimum Confidence | Rationale |
|--------------|-------------------|-----------|
| `clinical_recommendation` | 0.70 | High stakes clinical decisions |
| `safety_signal` | 0.60 | Safety-critical information |
| `risk_assessment` | 0.60 | Patient risk stratification |
| `narrative_generation` | 0.50 | General AI-generated text |
| `data_summary` | 0.40 | Basic data aggregation |

#### Uncertainty Information

```python
@dataclass
class UncertaintyInfo:
    confidence_level: ConfidenceLevel
    confidence_score: float
    data_gaps: List[str]        # What data is missing
    limitations: List[str]      # Known limitations
    reasoning: str              # Why this confidence level
```

#### "I Don't Know" Response Pattern

When data is insufficient, agents return explicit insufficient data responses instead of guessing:

```python
@staticmethod
def insufficient_data(
    agent_type: AgentType,
    reason: str,
    data_gaps: List[str],
    available_data: Dict[str, Any] = None
) -> "AgentResult":
    """
    Create a result indicating insufficient data to make a determination.

    This is the "I don't know" response - used when data is insufficient
    to make a reliable statement rather than guessing or hallucinating.
    """
    result = AgentResult(
        agent_type=agent_type,
        success=True,  # Not a failure - correctly identifying limitations
        data={
            "insufficient_data": True,
            "reason": reason,
            "data_gaps": data_gaps,
            "available_data": available_data or {},
        },
        confidence=0.0,
        narrative=f"Unable to provide assessment: {reason}. Missing data: {', '.join(data_gaps)}.",
    )
    return result
```

### Agent Types and Responsibilities

| Agent | Type | Primary Data Source | Key Methods |
|-------|------|---------------------|-------------|
| **ProtocolAgent** | PROTOCOL | protocol_rules.yaml | `get_visit_windows()`, `validate_visit_timing()`, `classify_deviation()` |
| **DataAgent** | DATA | H-34 Excel | `get_patient_data()`, `get_visit_data()`, `get_safety_summary()` |
| **LiteratureAgent** | LITERATURE | ChromaDB + YAML | `_search_literature()`, `_rag_query()`, `get_all_hazard_ratios()` |
| **RegistryAgent** | REGISTRY | registry_norms.yaml | `get_norms()`, `get_percentile()`, `compare_to_benchmark()` |
| **ComplianceAgent** | COMPLIANCE | Protocol + Data | `_check_patient_compliance()`, `_check_study_compliance()` |
| **SafetyAgent** | SAFETY | Data + Literature | `_analyze_adverse_events()`, `_detect_signals()`, **`_identify_data_gaps()`**, **`_generate_reasoning()`** |
| **SynthesisAgent** | SYNTHESIS | All agents | `_synthesize_uc1()` through `_synthesize_uc5()`, **`_check_data_sufficiency()`**, **`_identify_limitations()`** |

### Agent Result Structure

Every agent result includes full provenance and uncertainty:

```python
@dataclass
class AgentResult:
    agent_type: AgentType
    success: bool
    data: Dict[str, Any]
    sources: List[Source]           # Full provenance chain
    narrative: Optional[str]
    confidence: float               # 0.0 - 1.0
    error: Optional[str]
    execution_time_ms: float
    llm_calls: int
    uncertainty: Optional[UncertaintyInfo]  # Data gaps and limitations
    reasoning: Optional[str]                # Explicit reasoning for AI content
```

### Source Attribution

All data sources are tracked with confidence scores:

```python
@dataclass
class Source:
    type: SourceType              # PROTOCOL, STUDY_DATA, LITERATURE, REGISTRY, LLM_INFERENCE
    reference: str                # e.g., "Meding et al 2025"
    confidence: float             # Source reliability (0.0 - 1.0)
    details: Optional[Dict]       # e.g., {"page": 5, "section": "Results"}
```

### Agent Orchestrator

The `AgentOrchestrator` coordinates multi-agent workflows:

```python
class AgentOrchestrator:
    def register(self, agent: BaseAgent)
    async def run_agent(self, agent_type, context) -> AgentResult
    async def run_parallel(self, agent_types, context) -> Dict[AgentType, AgentResult]
    async def run_pipeline(self, pipeline, context) -> Dict[AgentType, AgentResult]
```

**Execution Pipelines:**
```python
execution_plans = {
    "UC1": [["protocol", "data"], ["literature", "registry"], ["compliance"], ["synthesis"]],
    "UC2": [["safety", "data"], ["literature", "registry"], ["synthesis"]],
    "UC3": [["protocol", "data"], ["compliance"]],
    "UC4": [["data"], ["literature", "registry"], ["risk_model"]],
    "UC5": [["uc1", "uc2", "uc3", "uc4"], ["synthesis"]]
}
```

---

## Service Layer

### LLM Service (`llm_service.py`)

Unified interface for LLM providers:

| Provider | Model | Use Case | Max Tokens |
|----------|-------|----------|------------|
| **Gemini** | gemini-3-pro-preview | Primary synthesis | 65536 |
| **Azure** | gpt-5-mini | Fallback/consensus | 16384 |

```python
class LLMService:
    async def generate(self, prompt, model, temperature, max_tokens) -> str
    async def generate_json(self, prompt, model, temperature, max_tokens) -> Dict
```

### Risk Service (`risk_service.py`)

XGBoost-based risk prediction with **literature hazard ratios loaded from YAML** (no hardcoding):

```python
class RiskModel:
    ML_FEATURE_COLUMNS = [
        'age', 'bmi', 'is_female', 'is_smoker', 'is_former_smoker',
        'has_osteoporosis', 'has_prior_surgery', 'bmi_over_30', 'bmi_over_35',
        'age_over_70', 'age_over_80', 'poor_bone_quality', 'surgery_duration_long'
    ]

    def __init__(self):
        # Load hazard ratios from literature_benchmarks.yaml - NOT hardcoded
        self._hazard_ratios = self._load_hazard_ratios_from_yaml()

    def _load_hazard_ratios_from_yaml(self) -> Dict[str, float]:
        """Load hazard ratios from literature_benchmarks.yaml."""
        doc_loader = get_doc_loader()
        lit_benchmarks = doc_loader.load_literature_benchmarks()
        hazard_ratios = {}
        for rf in lit_benchmarks.all_risk_factors:
            hazard_ratios[rf.factor] = rf.hazard_ratio
        return hazard_ratios

    def predict(self, features) -> Dict:
        # Ensemble: 60% ML score + 40% HR score
        ensemble_score = 0.6 * ml_score + 0.4 * hr_score
```

**Population Risk Analysis:**
```python
async def get_population_risk(self) -> Dict[str, Any]:
    """Calculate risk distribution across all real patients."""
    study_data = get_study_data()
    if not study_data.patients:
        return {"success": False, "error": "No patient data available"}

    # Iterate over actual patients - no stub/mock data
    for patient in study_data.patients:
        features = self._build_patient_features(patient, study_data)
        prediction = self._risk_model.predict(features)
        # ...
```

**Model Performance:**
- Training samples: 737 (37 real + 700 synthetic)
- ROC AUC: 0.541
- CV AUC: 0.513 (+/- 0.073)

### Dashboard Service (`dashboard_service.py`)

All metrics calculated from **real study data** (no hardcoded percentages):

```python
async def get_data_quality_summary(self) -> Dict[str, Any]:
    """Calculate actual data completeness from study data."""
    study_data = get_study_data()

    # Calculate Demographics completeness from actual patient records
    demographics_fields = 0
    demographics_filled = 0
    for patient in study_data.patients:
        demographics_fields += 6  # bmi, weight, height, gender, yob, smoking
        if patient.bmi is not None:
            demographics_filled += 1
        # ... calculate actual completeness

    demographics_pct = (demographics_filled / demographics_fields * 100)
```

---

## Anti-Hallucination System

### Prompt Templates with Guardrails

All prompts include explicit anti-hallucination requirements:

**synthesis_summary.txt:**
```
## Critical Requirements

- ONLY include findings that are directly supported by the provided data
- If data is insufficient or missing, explicitly state: "Unable to assess [X] due to insufficient data"
- DO NOT invent, extrapolate, or assume any clinical data
- Every statement must be traceable to the agent outputs provided
- Include the confidence level in your summary
- If confidence is below 0.6, add a caveat about data limitations
```

**safety_narrative.txt:**
```
## Critical Requirements for Avoiding Hallucination

- ONLY report data that is explicitly provided above
- If n_patients is 0 or missing, respond: "Unable to perform safety assessment: no patient data available"
- If signals list is empty, explicitly state "No safety signals detected"
- DO NOT invent adverse event rates, patient outcomes, or signal details
- Every rate or count mentioned must come from the provided data
- Reference the specific threshold when discussing a signal

## Provenance Statement

Include at the end: "Based on analysis of {n_patients} patients from the H-34 Study Database against protocol-defined thresholds."
```

**risk_narrative.txt:**
```
## Critical Requirements for Avoiding Hallucination

- ONLY use risk factors and hazard ratios provided in the data above
- If no risk factors are provided, state: "No elevated risk factors identified for this patient"
- If patient_id is missing, state: "Unable to perform risk assessment: patient identifier not provided"
- DO NOT invent additional risk factors, hazard ratios, or patient characteristics
- Each risk factor mentioned must reference its specific hazard ratio from the provided data

## Provenance Statement

End with: "Risk assessment based on literature-derived hazard ratios from literature_benchmarks.yaml."
```

### Synthesis Agent Data Validation

The SynthesisAgent validates data sufficiency before generating outputs:

```python
def _check_data_sufficiency(self, shared_data: Dict, synthesis_type: str) -> Optional[AgentResult]:
    """
    Check if we have sufficient data to perform synthesis.
    Returns an AgentResult with insufficient_data if data is lacking.
    """
    if not shared_data:
        return AgentResult.insufficient_data(
            agent_type=self.agent_type,
            reason="No agent data available for synthesis",
            data_gaps=["All agent outputs missing"],
        )

    # Check for required agents based on synthesis type
    required_agents = self._get_required_agents(synthesis_type)
    # ... validation logic

    # Check if any successful agent has actual data
    has_valid_data = False
    for agent_type, agent_data in shared_data.items():
        if agent_data.get("success") and agent_data.get("data"):
            if not data.get("error") and not data.get("insufficient_data"):
                has_valid_data = True
                break

    if not has_valid_data:
        return AgentResult.insufficient_data(
            agent_type=self.agent_type,
            reason="All available agent outputs contain errors or insufficient data",
            data_gaps=["No valid data from any agent"],
        )

    return None  # Proceed with synthesis
```

### Safety Agent Uncertainty Tracking

```python
async def execute(self, context: AgentContext) -> AgentResult:
    # ... execute analysis

    # Check for error or insufficient data
    if data.get("error"):
        return AgentResult.insufficient_data(
            agent_type=self.agent_type,
            reason=data["error"],
            data_gaps=self._identify_data_gaps(data, query_type),
        )

    # Set uncertainty information
    result.set_uncertainty(
        data_gaps=self._identify_data_gaps(data, query_type),
        limitations=self._identify_limitations(data),
        reasoning=self._generate_reasoning(data, query_type)
    )

    # Add explicit reasoning
    result.reasoning = self._generate_reasoning(data, query_type)
```

---

## Data Layer

### Study Data (`excel_loader.py`)

Loads H-34 study data from 21-sheet Excel export:

```python
class H34ExcelLoader:
    def load(self) -> H34StudyData

class H34StudyData:
    patients: List[Patient]           # 37 real patients
    preoperatives: List[Preoperative]
    intraoperatives: List[Intraoperative]
    surgery_data: List[SurgeryData]
    adverse_events: List[AdverseEvent]
    hhs_scores: List[HHSScore]
    ohs_scores: List[OHSScore]
    radiographic_evaluations: List[RadiographicEvaluation]
```

### Vector Store (`chroma_store.py`)

ChromaDB for semantic search over documents:

```python
class ChromaVectorStore:
    embedding_model = "text-embedding-004"  # Gemini

    def index_document(self, text, source_type, metadata)
    def search(self, query, source_type, n_results, include_distances) -> List[Dict]
```

**Indexed Content:**
- Protocol chunks: 55
- Literature chunks: 168

### Document-as-Code (`yaml_loader.py`)

Executable YAML rule files:

| File | Content | Records |
|------|---------|---------|
| `protocol_rules.yaml` | Visit windows, endpoints, thresholds | 5 visits, 12 assessments |
| `literature_benchmarks.yaml` | Published benchmarks, HRs | 6 publications, 16 risk factors |
| `registry_norms.yaml` | AOANJRR/NJR population norms | 15 metrics |

---

## API Endpoints

### UC1: Regulatory Readiness

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uc1/readiness` | GET | Overall readiness assessment |
| `/uc1/readiness/{patient_id}` | GET | Patient-level readiness |
| `/uc1/gaps` | GET | Gap analysis against protocol |
| `/uc1/timeline` | GET | Timeline projection |

### UC2: Safety Signals

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uc2/signals` | GET | All detected signals |
| `/uc2/signals/{patient_id}` | GET | Patient-level safety |
| `/uc2/adverse-events` | GET | AE summary |
| `/uc2/contextualize` | POST | Signal contextualization |

### UC3: Protocol Deviations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uc3/deviations` | GET | All deviations |
| `/uc3/deviations/{patient_id}` | GET | Patient deviations |
| `/uc3/compliance` | GET | Study compliance rate |
| `/uc3/classify` | POST | Classify deviation |

### UC4: Risk Stratification

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uc4/risk/{patient_id}` | GET | Patient risk assessment |
| `/uc4/population` | GET | Population risk distribution |
| `/uc4/factors` | GET | All risk factors with HRs |
| `/uc4/calculate` | POST | Calculate risk from features |

### UC5: Executive Dashboard

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uc5/dashboard` | GET | Full dashboard data |
| `/uc5/summary` | GET | Executive summary |
| `/uc5/benchmarks` | GET | Benchmark comparison table |
| `/uc5/priorities` | GET | Top attention items |

---

## Response Structure with Provenance

All API responses include uncertainty and provenance information:

```json
{
  "success": true,
  "data": { /* ... */ },
  "confidence": 0.85,
  "confidence_level": "high",
  "reasoning": "Study-level safety analysis based on 37 patients. Compared 4 safety metrics against protocol thresholds. Overall status: acceptable.",
  "uncertainty": {
    "confidence_level": "high",
    "confidence_score": 0.85,
    "data_gaps": [],
    "limitations": ["Wide confidence intervals expected due to sample size"],
    "reasoning": "Based on 37 patients with complete adverse event data"
  },
  "sources": [
    {
      "type": "study_data",
      "reference": "H-34 Study Database",
      "confidence": 1.0,
      "details": {"n_patients": 37}
    },
    {
      "type": "protocol",
      "reference": "protocol_rules.yaml",
      "confidence": 1.0,
      "details": {"thresholds_used": ["revision_rate_concern", "dislocation_rate_concern"]}
    }
  ]
}
```

---

## Implementation Status

### Critical Fixes - All Complete

| # | Issue | Priority | Status |
|---|-------|----------|--------|
| 1 | Wire H34ExcelLoader to DataAgent | P0 | **DONE** |
| 2 | Update LLM models to gemini-3-pro-preview + gpt-5-mini | P0 | **DONE** |
| 3 | Remove all fallback/exception swallowing logic | P0 | **DONE** |
| 4 | Connect ChromaDB for real RAG literature search | P1 | **DONE** |
| 5 | Build actual XGBoost risk model | P1 | **DONE** |
| 6 | Dynamic hazard ratio extraction from literature | P2 | **DONE** |
| 7 | **Remove hardcoded data quality percentages** | P0 | **DONE** |
| 8 | **Remove stub get_population_risk()** | P0 | **DONE** |
| 9 | **Load hazard ratios from YAML (not hardcoded)** | P0 | **DONE** |
| 10 | **Implement confidence thresholds** | P1 | **DONE** |
| 11 | **Implement "I don't know" responses** | P1 | **DONE** |
| 12 | **Add provenance to all AI outputs** | P1 | **DONE** |
| 13 | **Update prompts with anti-hallucination rules** | P1 | **DONE** |

### Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Agent Framework** | Complete | All 7 agents + confidence layer |
| **LLM Integration** | Complete | Gemini + Azure OpenAI |
| **Data Loading** | Complete | Excel + YAML loaders |
| **Vector Store** | Complete | ChromaDB with 223 chunks |
| **ML Risk Model** | Complete | XGBoost trained on 737 samples |
| **Prompt Templates** | Complete | 9 prompts with anti-hallucination |
| **API Routers** | Complete | All 5 UCs + health endpoint |
| **Services** | Complete | All UC services (real data only) |
| **Confidence System** | Complete | Thresholds + uncertainty tracking |
| **Provenance Tracking** | Complete | Full source attribution |

---

## Key Design Decisions

### 1. No Fallback/Exception Swallowing
All exceptions propagate with meaningful messages. No silent failures or hardcoded fallback responses.

### 2. No Hardcoded Data
All data comes from real sources:
- Patient data from Excel exports
- Hazard ratios from literature_benchmarks.yaml
- Thresholds from protocol_rules.yaml
- Benchmarks from registry_norms.yaml

### 3. Ensemble Risk Scoring
Risk scores combine ML predictions (60%) with literature hazard ratios (40%) for robust stratification.

### 4. Document-as-Code Pattern
Protocol rules, benchmarks, and norms stored as YAML for version control and auditability.

### 5. Full Provenance Tracking
Every output includes source attribution:
```python
result.add_source(
    SourceType.LITERATURE,
    "Meding et al 2025",
    confidence=0.9,
    details={"page": 5}
)
```

### 6. Confidence-Gated Outputs
AI outputs are gated by confidence thresholds:
- Clinical recommendations require 0.70 confidence
- Safety signals require 0.60 confidence
- Below threshold: warning added to output

### 7. "I Don't Know" > Hallucination
When data is insufficient, agents return explicit `insufficient_data` responses rather than guessing.

### 8. RAG for Literature Search
Semantic search via ChromaDB + LLM synthesis for evidence-based responses.

---

## Configuration

### Environment Variables (`.env`)

```bash
# LLM Providers
GEMINI_API_KEY=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini

# Model Selection
PRIMARY_LLM=gemini-3-pro-preview
EMBEDDING_MODEL=text-embedding-004

# Data Paths
H34_STUDY_DATA_PATH=data/raw/study/H-34DELTARevisionstudy_export_20250912.xlsx
H34_SYNTHETIC_DATA_PATH=data/raw/study/H-34_SYNTHETIC_PRODUCTION.xlsx

# Logging
LOG_LEVEL=INFO
LOG_DIR=./tmp
```

---

## Testing

### Unit Tests
- Agent logic (protocol validation, deviation classification)
- Service layer calculations (MCID rates, AE rates)
- Risk model predictions
- **Confidence threshold validation**
- **Insufficient data response generation**

### Integration Tests
- Agent orchestration (full UC execution)
- API endpoints (response schemas, provenance)
- ChromaDB search accuracy
- **Data sufficiency checks**

### Verification Commands

```bash
# Test risk model
python3 -c "from app.services.risk_service import RiskModel; m=RiskModel(); print(f'Model loaded: {m._model_loaded}')"

# Test literature search
python3 -c "from data.vectorstore import get_vector_store; s=get_vector_store(); print(s.search('revision rate', n_results=3))"

# Test data loading
python3 -c "from app.agents.data_agent import get_study_data; d=get_study_data(); print(f'Patients: {len(d.patients)}')"

# Test confidence thresholds
python3 -c "from app.agents.base_agent import CONFIDENCE_THRESHOLDS; print(CONFIDENCE_THRESHOLDS)"
```

---

## Performance Targets

| Use Case | Target Response Time | Notes |
|----------|---------------------|-------|
| UC1-UC4 | <30 seconds | Full analysis |
| UC5 | <20 seconds | Aggregation |
| UC5 (cached) | <5 seconds | With 5-min TTL |
| Literature Search | <3 seconds | ChromaDB query |

---

## Future Enhancements

1. **Real-time AE monitoring** - WebSocket updates for new adverse events
2. **Model retraining pipeline** - Automated retraining as study progresses
3. **Multi-study support** - Extend beyond H-34 to other protocols
4. **Audit logging** - Comprehensive audit trail for regulatory submissions
5. **PDF report generation** - Export analyses as formatted PDF reports
6. **Confidence calibration** - Track and calibrate confidence scores against actual outcomes
7. **Human-in-the-loop** - Flag low-confidence outputs for human review
