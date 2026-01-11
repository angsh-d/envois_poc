# Critical Fixes TODO - Clinical Intelligence Platform

## Status Overview

| # | Issue | Priority | Status | Tested |
|---|-------|----------|--------|--------|
| 1 | Wire H34ExcelLoader to DataAgent | P0 | **DONE** | Yes |
| 2 | Update LLM models to gemini-3-pro-preview + gpt-5-mini | P0 | **DONE** | Yes |
| 3 | Remove all fallback/exception swallowing logic | P0 | **DONE** | Yes |
| 4 | Connect ChromaDB for real RAG literature search | P1 | **DONE** | Yes |
| 5 | Build actual XGBoost risk model | P1 | **DONE** | Yes |
| 6 | Dynamic hazard ratio extraction from literature | P2 | **DONE** | Yes |

---

## Issue #1: Wire H34ExcelLoader to DataAgent

**Problem:**
- `DataAgent` loads from non-existent CSV files (`patients.csv`, `visits.csv`)
- `H34ExcelLoader` is fully implemented but disconnected
- All data queries return empty results

**Files to modify:**
- `app/agents/data_agent.py`
- `app/config.py` (add Excel file path setting)

**Fix approach:**
1. Add Excel file path to config/settings
2. Modify DataAgent to use H34ExcelLoader instead of CSV loading
3. Map Excel data structure to agent query patterns
4. Test with actual H-34 study data

**Acceptance criteria:**
- DataAgent returns real patient data from Excel
- All query types (patient, visit, summary, safety, deviations) work
- No empty DataFrames or "No data available" errors

---

## Issue #2: Update LLM Models

**Problem:**
- Current: `gemini-2.5-pro-preview-05-06` (outdated)
- Required primary: `gemini-3-pro-preview`
- Required fallback: `gpt-5-mini` (Azure)

**Files to modify:**
- `app/services/llm_service.py`
- `.env` (verify Azure deployment name)

**Fix approach:**
1. Update GEMINI_MODELS mapping
2. Update MAX_TOKENS for new models
3. Add gpt-5-mini to Azure configuration
4. Test both providers work

**Acceptance criteria:**
- Primary calls use gemini-3-pro-preview
- Fallback uses Azure gpt-5-mini
- Token limits correctly configured

---

## Issue #3: Remove Fallback Logic

**Problem:**
Fallback logic masks errors instead of failing fast:
- `literature_agent.py:236-243` - try/except returns simplified text
- `safety_agent.py:413-421` - fallback narrative generation
- `data_agent.py:52-53` - empty DataFrame on missing file
- `synthesis_agent.py` - partial results on failure

**Files to modify:**
- `app/agents/literature_agent.py`
- `app/agents/safety_agent.py`
- `app/agents/data_agent.py`
- `app/agents/synthesis_agent.py`

**Fix approach:**
1. Remove try/except blocks that swallow errors
2. Let exceptions propagate with meaningful messages
3. Add proper error handling at service layer only
4. Fail fast on missing data/configuration

**Acceptance criteria:**
- No silent failures
- Errors propagate with clear messages
- No hardcoded fallback responses

---

## Issue #4: Connect ChromaDB for RAG

**Problem:**
- LiteratureAgent claims RAG but loads static YAML
- ChromaDB exists in codebase but unused by agents
- No semantic search over literature PDFs

**Files to modify:**
- `app/agents/literature_agent.py`
- `data/vectorstore/chroma_store.py` (verify/extend)

**Fix approach:**
1. Verify ChromaDB has literature embeddings
2. Add vector search method to LiteratureAgent
3. Combine semantic search with YAML benchmarks
4. Test retrieval quality

**Acceptance criteria:**
- Semantic search returns relevant literature chunks
- Risk factors retrieved dynamically
- Provenance includes actual document references

---

## Issue #5: Build XGBoost Risk Model

**Problem:**
- `RiskModel._model = None` - never instantiated
- "ML predictions" are hardcoded hazard ratio multiplication
- No actual machine learning

**Files to modify:**
- `app/services/risk_service.py`
- Create: `data/ml/train_risk_model.py`
- Create: `data/ml/risk_model.joblib` (trained model)

**Fix approach:**
1. Define feature set from patient data
2. Create training script with synthetic data augmentation
3. Train XGBoost classifier for revision risk
4. Integrate trained model into RiskModel
5. Ensemble ML score with literature hazard ratios

**Acceptance criteria:**
- Actual trained model loaded at startup
- Predictions use real features
- Model performance metrics available

---

## Issue #6: Dynamic Hazard Ratio Extraction

**Problem:**
- Hazard ratios manually typed in YAML
- Not extracted from literature PDFs dynamically

**Files to modify:**
- `data/loaders/yaml_loader.py`
- Create extraction prompt for hazard ratios

**Fix approach:**
1. Use LLM to extract HRs from literature PDFs
2. Store extracted values with source attribution
3. Validate against manually curated values
4. Update YAML generation process

**Acceptance criteria:**
- HRs traced to specific publications
- Extraction reproducible
- Confidence scores for extracted values

---

## Testing Protocol

For each fix:
1. **Unit test:** Verify component works in isolation
2. **Integration test:** Verify data flows through pipeline
3. **API test:** Verify endpoint returns correct data
4. **Regression test:** Verify other components still work

## Notes

- Fix issues in order (P0 first)
- Each fix must be tested before moving to next
- Document any new dependencies
- Update this file as issues are resolved
