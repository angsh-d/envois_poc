"""
Code Generation Agent for Clinical Intelligence Platform.

Specialized agent that generates R, Python, SQL, and C code for ad-hoc queries,
with deep understanding of:
- Clinical domain language (Kaplan-Meier, HHS, revision rates, etc.)
- H-34 DELTA study data model and database schema
- Statistical methodologies for clinical research
"""
import logging
import json
import re
import subprocess
import tempfile
import os
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.llm_service import get_llm_service, LLMService
from app.services.prompt_service import get_prompt_service, PromptService

logger = logging.getLogger(__name__)


class CodeLanguage(str, Enum):
    """Supported programming languages for code generation."""
    PYTHON = "python"
    R = "r"
    SQL = "sql"
    C = "c"


@dataclass
class CodeGenerationResult:
    """Result of code generation."""
    success: bool
    language: str
    code: str
    explanation: str
    execution_result: Optional[str] = None
    execution_error: Optional[str] = None
    data_preview: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def get_warnings(self) -> List[str]:
        return self.warnings if self.warnings else []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "language": self.language,
            "code": self.code,
            "explanation": self.explanation,
            "execution_result": self.execution_result,
            "execution_error": self.execution_error,
            "data_preview": self.data_preview,
            "warnings": self.warnings
        }


# Complete database schema for the H-34 study
DATABASE_SCHEMA = """
-- H-34 DELTA Revision Cup Study Database Schema

-- Core patient demographics and enrollment
CREATE TABLE study_patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR UNIQUE,        -- Study patient identifier (e.g., 'PAT001')
    facility VARCHAR,                 -- Enrolling site
    year_of_birth INTEGER,
    weight DOUBLE PRECISION,          -- kg
    height DOUBLE PRECISION,          -- cm
    bmi DOUBLE PRECISION,             -- Calculated BMI
    gender VARCHAR,                   -- 'Male' or 'Female'
    race VARCHAR,
    activity_level VARCHAR,           -- 'Low', 'Moderate', 'High'
    work_status VARCHAR,
    smoking_habits VARCHAR,           -- 'Never', 'Former', 'Current'
    alcohol_habits VARCHAR,
    concomitant_medications TEXT,
    screening_date DATE,
    consent_date DATE,
    enrolled VARCHAR,                 -- 'Yes' or 'No'
    status VARCHAR,                   -- 'Active', 'Completed', 'Withdrawn', 'Lost to Follow-up'
    surgery_date DATE,
    affected_side VARCHAR,            -- 'Left' or 'Right'
    primary_diagnosis VARCHAR,        -- Surgical indication
    medical_history TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Surgery details and implant information
CREATE TABLE study_surgeries (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES study_patients(id),
    surgery_date DATE,
    surgical_approach VARCHAR,        -- 'Posterior', 'Anterior', 'Lateral'
    anaesthesia VARCHAR,
    surgery_time_minutes INTEGER,
    intraoperative_complications TEXT,
    stem_type VARCHAR,
    stem_size VARCHAR,
    cup_type VARCHAR,                 -- H-34 DELTA Revision Cup
    cup_diameter DOUBLE PRECISION,    -- mm
    cup_liner_material VARCHAR,       -- 'Ceramic', 'Polyethylene'
    head_type VARCHAR,
    head_material VARCHAR,
    head_diameter DOUBLE PRECISION,   -- mm
    implant_details JSON,
    created_at TIMESTAMP
);

-- Patient outcome scores (HHS, WOMAC, SF-36, etc.)
CREATE TABLE study_scores (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES study_patients(id),
    score_type VARCHAR,               -- 'HHS' (Harris Hip Score), 'WOMAC', 'SF-36', 'EQ-5D', 'UCLA'
    follow_up VARCHAR,                -- 'Baseline', '6 weeks', '3 months', '6 months', '1 year', '2 years'
    follow_up_date DATE,
    total_score DOUBLE PRECISION,     -- Total/composite score
    score_category VARCHAR,           -- 'Poor', 'Fair', 'Good', 'Excellent'
    components JSON,                  -- Individual score components
    created_at TIMESTAMP
);
-- HHS interpretation: <70 Poor, 70-79 Fair, 80-89 Good, 90-100 Excellent
-- MCID (Minimal Clinically Important Difference) for HHS: typically 10-15 points

-- Patient visits and assessments
CREATE TABLE study_visits (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES study_patients(id),
    visit_type VARCHAR,               -- 'Screening', 'Surgery', '6 weeks', '3 months', etc.
    visit_date DATE,
    days_from_surgery INTEGER,
    visit_data JSON,                  -- Visit-specific data
    radiographic_data JSON,           -- X-ray findings, cup position, etc.
    created_at TIMESTAMP
);

-- Adverse events and safety data
CREATE TABLE study_adverse_events (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES study_patients(id),
    ae_id VARCHAR,                    -- Adverse event identifier
    report_type VARCHAR,              -- 'Initial', 'Follow-up', 'Final'
    initial_report_date DATE,
    report_date DATE,
    onset_date DATE,
    ae_title VARCHAR,                 -- Short description
    event_narrative TEXT,             -- Detailed description
    is_sae BOOLEAN,                   -- Serious Adverse Event flag
    classification VARCHAR,           -- 'Revision', 'Reoperation', 'Medical', etc.
    outcome VARCHAR,                  -- 'Resolved', 'Ongoing', 'Death'
    end_date DATE,
    severity VARCHAR,                 -- 'Mild', 'Moderate', 'Severe'
    device_relationship VARCHAR,      -- 'Related', 'Possibly Related', 'Not Related'
    procedure_relationship VARCHAR,
    expectedness VARCHAR,             -- 'Expected', 'Unexpected'
    action_taken VARCHAR,
    device_removed BOOLEAN,           -- Revision surgery performed
    device_removal_date DATE,
    created_at TIMESTAMP
);

-- Registry benchmark data (9 international registries)
CREATE TABLE registry_benchmarks (
    id SERIAL PRIMARY KEY,
    registry_id VARCHAR,              -- 'NJR', 'SHAR', 'NAR', 'NZJR', 'DHR', 'EPRD', 'AJRR', 'CJRR', 'AOANJRR'
    name VARCHAR,                     -- Full registry name
    abbreviation VARCHAR,
    report_year INTEGER,
    data_years VARCHAR,               -- Data coverage period
    population VARCHAR,               -- 'Primary THA', 'Revision THA', 'All THA'
    n_procedures INTEGER,             -- Total procedures in registry
    n_primary INTEGER,
    revision_burden DOUBLE PRECISION, -- % of procedures that are revisions
    survival_1yr DOUBLE PRECISION,    -- Kaplan-Meier survival at 1 year
    survival_2yr DOUBLE PRECISION,
    survival_5yr DOUBLE PRECISION,
    survival_10yr DOUBLE PRECISION,
    survival_15yr DOUBLE PRECISION,
    revision_rate_1yr DOUBLE PRECISION,
    revision_rate_2yr DOUBLE PRECISION,
    revision_rate_median DOUBLE PRECISION,
    revision_rate_p75 DOUBLE PRECISION,
    revision_rate_p95 DOUBLE PRECISION,
    revision_reasons JSON,            -- Array of {reason, percentage}
    outcomes_by_indication JSON,
    created_at TIMESTAMP
);

-- Literature benchmarks from published studies
CREATE TABLE literature_publications (
    id SERIAL PRIMARY KEY,
    publication_id VARCHAR,           -- e.g., 'Berry2022'
    title VARCHAR,
    year INTEGER,
    journal VARCHAR,
    n_patients INTEGER,
    follow_up_years DOUBLE PRECISION,
    revision_indication VARCHAR,      -- 'Primary', 'Revision', 'All'
    benchmarks JSON,                  -- Outcome benchmarks
    created_at TIMESTAMP
);

-- Risk factors from literature (hazard ratios)
CREATE TABLE literature_risk_factors (
    id SERIAL PRIMARY KEY,
    publication_id INTEGER REFERENCES literature_publications(id),
    factor VARCHAR,                   -- 'Age', 'BMI', 'Diabetes', 'Smoking', etc.
    hazard_ratio DOUBLE PRECISION,
    confidence_interval_low DOUBLE PRECISION,
    confidence_interval_high DOUBLE PRECISION,
    outcome VARCHAR,                  -- 'Revision', 'Infection', 'Dislocation'
    source VARCHAR
);

-- Protocol definitions and rules
CREATE TABLE protocol_rules (
    id SERIAL PRIMARY KEY,
    protocol_id VARCHAR,              -- 'H-34'
    protocol_version VARCHAR,
    effective_date DATE,
    title VARCHAR,
    sponsor VARCHAR,
    phase VARCHAR,
    sample_size_target INTEGER,
    sample_size_interim INTEGER,
    sample_size_evaluable INTEGER,
    ltfu_assumption NUMERIC,          -- Lost to follow-up assumption
    safety_thresholds JSON,           -- e.g., {"revision_rate_2yr": 0.10}
    deviation_classification JSON,
    inclusion_criteria JSON,
    exclusion_criteria JSON,
    provenance JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Protocol visit schedule
CREATE TABLE protocol_visits (
    id SERIAL PRIMARY KEY,
    protocol_id INTEGER REFERENCES protocol_rules(id),
    visit_id VARCHAR,                 -- 'V1', 'V2', etc.
    name VARCHAR,                     -- 'Screening', '6 Week Follow-up'
    target_day INTEGER,               -- Days from surgery
    window_minus INTEGER,             -- Visit window (days before)
    window_plus INTEGER,              -- Visit window (days after)
    required_assessments JSON,        -- Required forms/tests
    is_primary_endpoint BOOLEAN,
    sequence INTEGER
);

-- Protocol endpoints
CREATE TABLE protocol_endpoints (
    id SERIAL PRIMARY KEY,
    protocol_id INTEGER REFERENCES protocol_rules(id),
    endpoint_id VARCHAR,
    name VARCHAR,
    endpoint_type VARCHAR,            -- 'Primary', 'Secondary', 'Safety'
    timepoint VARCHAR,                -- '2 years', '5 years'
    calculation VARCHAR,              -- Statistical method
    success_threshold DOUBLE PRECISION,
    mcid_threshold DOUBLE PRECISION,  -- Minimal Clinically Important Difference
    success_criterion VARCHAR
);
"""

# Domain knowledge for clinical research
DOMAIN_KNOWLEDGE = """
## Clinical Research Domain Knowledge for H-34 DELTA Study

### Study Overview
- H-34 DELTA Revision Cup is a post-market clinical study
- Multi-center prospective study of revision total hip arthroplasty (THA)
- Current data: 37 enrolled patients, 2 revisions (5.4% revision rate)
- Primary endpoint: 2-year revision rate vs FDA 510(k) benchmark (≤10%)

### Key Clinical Metrics

#### Harris Hip Score (HHS)
- Range: 0-100 (higher is better)
- Categories: <70 Poor, 70-79 Fair, 80-89 Good, 90-100 Excellent
- MCID (Minimal Clinically Important Difference): 10-15 points
- Typical baseline for revision patients: 40-55
- Target improvement: ≥15 points from baseline

#### Kaplan-Meier Survival Analysis
- Standard method for implant survivorship
- Endpoint: Revision surgery (device removal)
- Report survival at 1, 2, 5, 10, 15 years
- Registry benchmarks use K-M methodology

#### Revision Rate Benchmarks
- FDA 510(k): ≤10% at 2 years
- MDR PMCF: ≤12% at 2 years
- Registry parity (NJR): ~9% at 2 years
- Pooled international benchmark: ~6% at 2 years (94% survival)

### Registry Abbreviations
- AOANJRR: Australian Orthopaedic Association National Joint Replacement Registry
- NJR: National Joint Registry (UK)
- SHAR: Swedish Hip Arthroplasty Register
- AJRR: American Joint Replacement Registry
- CJRR: Canadian Joint Replacement Registry
- NAR: Norwegian Arthroplasty Register
- NZJR: New Zealand Joint Registry
- DHR: Danish Hip Arthroplasty Register
- EPRD: German Arthroplasty Registry

### Common Revision Reasons
1. Aseptic loosening (30-40%)
2. Infection (15-25%)
3. Dislocation/Instability (10-20%)
4. Periprosthetic fracture (5-15%)
5. Wear/Osteolysis (5-10%)

### Statistical Methods
- Beta-binomial for revision rate inference
- Kaplan-Meier for survival curves
- Log-rank test for comparing survival curves
- Cox proportional hazards for risk factors
- Monte Carlo simulation for probability estimation

### Database Connection
- PostgreSQL database accessible via DATABASE_URL environment variable
- Use psycopg2 or sqlalchemy for Python
- Use RPostgres or DBI for R
"""

# Code templates for common operations
CODE_TEMPLATES = {
    "python_db_connection": '''
import os
import pandas as pd
from sqlalchemy import create_engine

# Connect to the H-34 study database
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
''',
    
    "r_db_connection": '''
library(DBI)
library(RPostgres)

# Connect to the H-34 study database
con <- dbConnect(
  Postgres(),
  dbname = Sys.getenv("PGDATABASE"),
  host = Sys.getenv("PGHOST"),
  port = Sys.getenv("PGPORT"),
  user = Sys.getenv("PGUSER"),
  password = Sys.getenv("PGPASSWORD")
)
''',

    "python_kaplan_meier": '''
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test
import matplotlib.pyplot as plt

# Prepare survival data
# Time: days from surgery to event or last follow-up
# Event: 1 if revision occurred, 0 if censored

kmf = KaplanMeierFitter()
kmf.fit(durations=time_to_event, event_observed=event_occurred)

# Plot survival curve
plt.figure(figsize=(10, 6))
kmf.plot_survival_function()
plt.xlabel('Days from Surgery')
plt.ylabel('Survival Probability')
plt.title('Kaplan-Meier Survival Curve - H-34 DELTA Study')
''',

    "r_kaplan_meier": '''
library(survival)
library(survminer)

# Create survival object
surv_obj <- Surv(time = data$time_to_event, event = data$revision)

# Fit Kaplan-Meier model
km_fit <- survfit(surv_obj ~ 1)

# Plot with confidence intervals
ggsurvplot(
  km_fit,
  data = data,
  risk.table = TRUE,
  conf.int = TRUE,
  xlab = "Days from Surgery",
  ylab = "Survival Probability",
  title = "Kaplan-Meier Survival Curve - H-34 DELTA Study",
  ggtheme = theme_minimal()
)
''',

    "sql_hhs_improvement": '''
-- Calculate HHS improvement from baseline to follow-up
WITH baseline AS (
    SELECT patient_id, total_score as baseline_hhs
    FROM study_scores
    WHERE score_type = 'HHS' AND follow_up = 'Baseline'
),
followup AS (
    SELECT patient_id, follow_up, total_score as followup_hhs
    FROM study_scores
    WHERE score_type = 'HHS' AND follow_up != 'Baseline'
)
SELECT 
    b.patient_id,
    b.baseline_hhs,
    f.follow_up,
    f.followup_hhs,
    (f.followup_hhs - b.baseline_hhs) as improvement,
    CASE 
        WHEN (f.followup_hhs - b.baseline_hhs) >= 15 THEN 'MCID Achieved'
        WHEN (f.followup_hhs - b.baseline_hhs) >= 10 THEN 'Clinically Meaningful'
        ELSE 'Below MCID'
    END as clinical_significance
FROM baseline b
JOIN followup f ON b.patient_id = f.patient_id
ORDER BY f.follow_up, improvement DESC;
'''
}


class CodeAgent:
    """Agent for generating clinical research code with domain knowledge."""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.prompt_service = get_prompt_service()
    
    def _detect_language(self, request: str) -> CodeLanguage:
        """Detect requested programming language from the query."""
        request_lower = request.lower()
        
        if any(kw in request_lower for kw in ['r code', 'in r', 'using r', 'r script', 'ggplot', 'survfit', 'dplyr']):
            return CodeLanguage.R
        elif any(kw in request_lower for kw in ['sql', 'query', 'select', 'database query']):
            return CodeLanguage.SQL
        elif any(kw in request_lower for kw in ['c code', 'in c', 'c program']):
            return CodeLanguage.C
        else:
            # Default to Python
            return CodeLanguage.PYTHON
    
    def _detect_analysis_type(self, request: str) -> str:
        """Detect the type of analysis requested."""
        request_lower = request.lower()
        
        if any(kw in request_lower for kw in ['kaplan', 'survival', 'km curve', 'survivorship']):
            return "survival_analysis"
        elif any(kw in request_lower for kw in ['hhs', 'harris hip', 'hip score', 'improvement', 'outcome score']):
            return "outcome_scores"
        elif any(kw in request_lower for kw in ['adverse', 'safety', 'complication', 'ae', 'sae']):
            return "safety_analysis"
        elif any(kw in request_lower for kw in ['revision', 'rate', 'benchmark', 'registry']):
            return "revision_analysis"
        elif any(kw in request_lower for kw in ['risk', 'hazard', 'cox', 'regression']):
            return "risk_analysis"
        elif any(kw in request_lower for kw in ['demographics', 'patient', 'baseline', 'characteristics']):
            return "demographics"
        else:
            return "general"
    
    async def generate_code(
        self, 
        request: str,
        language: Optional[CodeLanguage] = None,
        execute: bool = False
    ) -> CodeGenerationResult:
        """
        Generate code for the given clinical research request.
        
        Args:
            request: Natural language description of what code to generate
            language: Optional override for programming language
            execute: Whether to execute the code and return results
        
        Returns:
            CodeGenerationResult with generated code and optional execution results
        """
        # Detect language if not specified
        if language is None:
            language = self._detect_language(request)
        
        analysis_type = self._detect_analysis_type(request)
        
        # Build the prompt
        prompt = self._build_prompt(request, language, analysis_type)
        
        max_correction_attempts = 2
        current_prompt = prompt
        all_warnings = []
        
        try:
            for attempt in range(max_correction_attempts + 1):
                # Generate code using LLM
                response = await self.llm_service.generate(
                    prompt=current_prompt,
                    model="gemini-3-pro-preview",
                    temperature=0.2,  # Low temperature for code generation
                    max_tokens=4096
                )
                
                # Parse the response
                code, explanation = self._parse_response(response, language)
                
                # Validate the generated code against the schema
                validation = await self.validate_code(code, language)
                
                # If validation passed or we've exhausted attempts, proceed
                if validation["valid"] or attempt == max_correction_attempts:
                    warnings = []
                    if not validation["valid"]:
                        warnings.extend(validation["issues"])
                    if validation["suggestions"]:
                        warnings.extend(validation["suggestions"])
                    if all_warnings:
                        warnings.insert(0, f"Code was auto-corrected after {attempt} attempt(s)")
                    
                    result = CodeGenerationResult(
                        success=True,
                        language=language.value,
                        code=code,
                        explanation=explanation,
                        warnings=warnings if warnings else None
                    )
                    break
                
                # Self-correction: regenerate with error feedback
                logger.info(f"Code validation failed (attempt {attempt + 1}), auto-correcting...")
                all_warnings.extend(validation["issues"])
                
                correction_prompt = self._build_correction_prompt(
                    original_request=request,
                    generated_code=code,
                    validation_errors=validation["issues"],
                    language=language
                )
                current_prompt = correction_prompt
            
            # Execute if requested (only for SQL - safer)
            if execute and language == CodeLanguage.SQL:
                exec_result, exec_error, preview = await self._execute_sql(code)
                result.execution_result = exec_result
                result.execution_error = exec_error
                result.data_preview = preview
                
                # If execution failed, try self-correction
                if exec_error and not result.data_preview:
                    logger.info("SQL execution failed, attempting self-correction...")
                    corrected_result = await self._self_correct_sql(
                        original_request=request,
                        failed_code=code,
                        error_message=exec_error,
                        language=language
                    )
                    if corrected_result:
                        return corrected_result
                        
            elif execute:
                result.warnings = result.warnings or []
                result.warnings.append(
                    f"Code execution for {language.value} is available but disabled for safety. "
                    "The code has been validated against the schema."
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return CodeGenerationResult(
                success=False,
                language=language.value,
                code="",
                explanation=f"Failed to generate code: {str(e)}"
            )
    
    def _build_prompt(self, request: str, language: CodeLanguage, analysis_type: str) -> str:
        """Build the prompt for code generation."""
        
        # Get relevant code template
        template_key = None
        if analysis_type == "survival_analysis":
            template_key = f"{language.value}_kaplan_meier" if language != CodeLanguage.SQL else None
        
        template_example = ""
        if template_key and template_key in CODE_TEMPLATES:
            template_example = f"\n\nHere's a relevant template you can adapt:\n```\n{CODE_TEMPLATES[template_key]}\n```"
        
        # Database connection template
        db_connection = ""
        if language == CodeLanguage.PYTHON:
            db_connection = CODE_TEMPLATES["python_db_connection"]
        elif language == CodeLanguage.R:
            db_connection = CODE_TEMPLATES["r_db_connection"]
        
        prompt = f"""You are an expert clinical research programmer generating {language.value.upper()} code for the H-34 DELTA Revision Cup post-market study.

## User Request
{request}

## Database Schema
{DATABASE_SCHEMA}

## Domain Knowledge
{DOMAIN_KNOWLEDGE}

## Database Connection Template
```{language.value}
{db_connection}
```
{template_example}

## Instructions
1. Generate complete, executable {language.value.upper()} code that fulfills the request
2. Use the exact table and column names from the schema
3. Include appropriate comments explaining the code
4. For statistical analyses, use standard clinical research methodologies
5. Handle edge cases (missing data, small sample sizes)
6. Format output for easy interpretation

## Output Format
Return your response in this exact format:

```{language.value}
[YOUR CODE HERE]
```

**Explanation:**
[Brief explanation of what the code does and any important notes]
"""
        return prompt
    
    def _build_correction_prompt(
        self, 
        original_request: str, 
        generated_code: str, 
        validation_errors: List[str],
        language: CodeLanguage
    ) -> str:
        """Build a prompt for self-correction based on validation errors."""
        
        errors_text = "\n".join(f"- {err}" for err in validation_errors)
        
        return f"""You are an expert clinical research programmer. The previous code generation had validation errors that need to be fixed.

## Original Request
{original_request}

## Generated Code (with errors)
```{language.value}
{generated_code}
```

## Validation Errors
{errors_text}

## Database Schema (for reference)
{DATABASE_SCHEMA}

## Instructions
1. Fix ALL the validation errors listed above
2. Use the EXACT table and column names from the schema
3. Do NOT use tables that don't exist in the schema
4. Maintain the same functionality as the original request

## Output Format
Return ONLY the corrected code in this format:

```{language.value}
[CORRECTED CODE HERE]
```

**Explanation:**
[Brief explanation of what was fixed]
"""
    
    async def _self_correct_sql(
        self,
        original_request: str,
        failed_code: str,
        error_message: str,
        language: CodeLanguage
    ) -> Optional[CodeGenerationResult]:
        """Attempt to self-correct SQL code after execution failure."""
        
        correction_prompt = f"""You are an expert SQL programmer. The following SQL query failed with an error. Fix it.

## Original Request
{original_request}

## Failed SQL Query
```sql
{failed_code}
```

## Database Error
{error_message}

## Database Schema
{DATABASE_SCHEMA}

## Instructions
1. Fix the SQL error based on the error message
2. Use ONLY tables and columns that exist in the schema
3. Ensure the query is syntactically correct
4. Keep the query as close to the original intent as possible

## Output Format
Return ONLY the corrected SQL:

```sql
[CORRECTED SQL HERE]
```

**Explanation:**
[What was wrong and how it was fixed]
"""
        
        try:
            response = await self.llm_service.generate(
                prompt=correction_prompt,
                model="gemini-3-pro-preview",
                temperature=0.1,
                max_tokens=2048
            )
            
            code, explanation = self._parse_response(response, language)
            
            # Validate the corrected code
            validation = await self.validate_code(code, language)
            if not validation["valid"]:
                return None  # Correction failed validation too
            
            # Try executing the corrected code
            exec_result, exec_error, preview = await self._execute_sql(code)
            
            if exec_error:
                return None  # Correction still failed
            
            return CodeGenerationResult(
                success=True,
                language=language.value,
                code=code,
                explanation=explanation,
                execution_result=exec_result,
                data_preview=preview,
                warnings=["Code was auto-corrected after execution error"]
            )
            
        except Exception as e:
            logger.error(f"SQL self-correction failed: {e}")
            return None
    
    def _parse_response(self, response: str, language: CodeLanguage) -> Tuple[str, str]:
        """Parse the LLM response to extract code and explanation."""
        
        # Try multiple patterns to extract code block
        patterns = [
            rf"```{language.value}\s*\n(.*?)```",  # With language tag
            rf"```{language.value.upper()}\s*\n(.*?)```",  # Uppercase language
            r"```\w*\s*\n(.*?)```",  # Any language tag
            r"```\n?(.*?)```",  # No language tag
        ]
        
        code = ""
        for pattern in patterns:
            code_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if code_match:
                code = code_match.group(1).strip()
                break
        
        # If no code block found, check if the response itself looks like code
        if not code:
            lines = response.strip().split('\n')
            code_indicators = ['import', 'library(', 'SELECT', 'FROM', '#include', 'def ', 'function(']
            if any(indicator in response for indicator in code_indicators):
                code = response.strip()
            else:
                code = "# Code generation failed - please try rephrasing your request"
        
        # Extract explanation - try multiple patterns
        explanation = ""
        explanation_patterns = [
            r"\*\*Explanation:\*\*\s*(.*?)(?:$|\n\n\*\*)",
            r"Explanation:\s*(.*?)(?:$|\n\n)",
            r"(?:^|\n\n)([A-Z][^`]*?)$",  # Last paragraph after code
        ]
        
        for pattern in explanation_patterns:
            explanation_match = re.search(pattern, response, re.DOTALL)
            if explanation_match:
                explanation = explanation_match.group(1).strip()
                if len(explanation) > 20:  # Ensure it's meaningful
                    break
        
        # Fallback: extract text after last code block
        if not explanation or len(explanation) < 20:
            parts = response.split("```")
            if len(parts) >= 3:
                last_part = parts[-1].strip()
                # Remove markdown formatting
                last_part = re.sub(r'\*\*[^*]+\*\*:?', '', last_part).strip()
                if len(last_part) > 20:
                    explanation = last_part
        
        # Default explanation if none found
        if not explanation:
            explanation = f"Generated {language.value.upper()} code for your request."
        
        return code, explanation
    
    async def _execute_sql(self, sql: str) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
        """Execute SQL query and return results (read-only queries only)."""
        import os
        
        # Safety check - only allow SELECT statements
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            return None, "Only SELECT queries can be executed for safety", None
        
        # Check for dangerous patterns even in SELECT
        dangerous_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER', 'CREATE']
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                return None, f"Query contains disallowed keyword: {pattern}", None
        
        try:
            import psycopg2
            from psycopg2 import sql as psycopg2_sql
            
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                return None, "DATABASE_URL not configured", None
            
            # Use context manager for proper cleanup
            with psycopg2.connect(database_url) as conn:
                with conn.cursor() as cursor:
                    # Set statement timeout to prevent long-running queries
                    cursor.execute("SET statement_timeout = '10s'")
                    
                    # Execute with a limit for safety
                    limited_sql = sql.rstrip(';')
                    if 'LIMIT' not in sql_upper:
                        limited_sql += ' LIMIT 100'
                    
                    cursor.execute(limited_sql)
                    
                    if cursor.description is None:
                        return "Query executed but returned no results", None, None
                    
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Format results
                    result_text = f"Query returned {len(rows)} rows\n"
                    result_text += "Columns: " + ", ".join(columns)
                    
                    # Create preview with JSON-serializable values
                    def serialize_value(v):
                        if v is None:
                            return None
                        if isinstance(v, (int, float, str, bool)):
                            return v
                        return str(v)
                    
                    preview = {
                        "columns": columns,
                        "row_count": len(rows),
                        "sample_rows": [
                            {col: serialize_value(val) for col, val in zip(columns, row)}
                            for row in rows[:5]
                        ]
                    }
                    
                    return result_text, None, preview
            
        except psycopg2.Error as e:
            logger.error(f"SQL execution error: {e}")
            return None, f"Database error: {e.pgerror or str(e)}", None
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return None, str(e), None
    
    async def validate_code(self, code: str, language: CodeLanguage) -> Dict[str, Any]:
        """Validate generated code against the schema without executing."""
        
        validation_result = {
            "valid": True,
            "issues": [],
            "suggestions": []
        }
        
        # Valid tables and their columns from the schema
        schema_tables = {
            'study_patients': ['id', 'patient_id', 'facility', 'year_of_birth', 'weight', 'height', 'bmi', 'gender', 'race', 'enrollment_date', 'informed_consent_date', 'surgery_date'],
            'study_surgeries': ['id', 'patient_id', 'surgery_date', 'procedure_type', 'implant_type', 'surgeon_id', 'facility', 'primary_diagnosis', 'laterality', 'bone_defect_classification', 'cup_size', 'liner_type', 'augment_used', 'revision_surgery', 'revision_date', 'revision_reason'],
            'study_scores': ['id', 'patient_id', 'visit_id', 'assessment_date', 'hhs_total', 'hhs_pain', 'hhs_function', 'hhs_deformity', 'hhs_rom', 'womac_total', 'womac_pain', 'womac_stiffness', 'womac_function', 'eq5d_index', 'eq5d_vas', 'satisfaction_score'],
            'study_visits': ['id', 'patient_id', 'visit_type', 'scheduled_date', 'actual_date', 'status', 'notes', 'xray_performed', 'xray_findings'],
            'study_adverse_events': ['id', 'patient_id', 'event_date', 'event_type', 'severity', 'seriousness', 'relatedness', 'description', 'action_taken', 'outcome', 'resolution_date'],
            'registry_benchmarks': ['id', 'registry_name', 'country', 'revision_rate_5yr', 'revision_rate_10yr', 'sample_size', 'year', 'implant_category'],
            'literature_publications': ['id', 'title', 'authors', 'journal', 'year', 'doi', 'pmid', 'study_type', 'sample_size', 'followup_years'],
            'literature_risk_factors': ['id', 'publication_id', 'risk_factor', 'hazard_ratio', 'confidence_interval', 'p_value'],
            'protocol_rules': ['id', 'rule_type', 'rule_id', 'description', 'threshold', 'operator', 'action'],
            'protocol_visits': ['id', 'visit_name', 'visit_window_days', 'required_assessments'],
            'protocol_endpoints': ['id', 'endpoint_type', 'endpoint_name', 'definition', 'timepoint']
        }
        
        valid_tables = list(schema_tables.keys())
        all_columns = set()
        for cols in schema_tables.values():
            all_columns.update(cols)
        
        # Check for common issues
        if language == CodeLanguage.SQL:
            code_lower = code.lower()
            
            # Check table references
            table_pattern = r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)'
            matches = re.findall(table_pattern, code, re.IGNORECASE)
            referenced_tables = []
            for match in matches:
                table_name = (match[0] or match[1]).lower()
                referenced_tables.append(table_name)
                if table_name not in valid_tables:
                    validation_result["issues"].append(
                        f"Unknown table '{table_name}'. Valid tables: {', '.join(valid_tables)}"
                    )
                    validation_result["valid"] = False
            
            # Check for common column typos in referenced tables
            if referenced_tables and validation_result["valid"]:
                # Get valid columns for referenced tables
                valid_cols = set()
                for t in referenced_tables:
                    if t in schema_tables:
                        valid_cols.update(schema_tables[t])
                
                # Suggest using correct column names
                if 'patient_id' in code_lower and 'study_patients' in referenced_tables:
                    if 'id' in code_lower and 'patient_id' not in code_lower:
                        validation_result["suggestions"].append(
                            "Note: study_patients uses 'patient_id' (varchar) as the study identifier, not 'id' (serial)"
                        )
        
        elif language == CodeLanguage.PYTHON:
            # Check for required imports
            if 'pandas' not in code and 'pd' not in code:
                validation_result["suggestions"].append(
                    "Consider using pandas for data manipulation"
                )
            # Check for database connection
            if 'DATABASE_URL' not in code and 'psycopg2' not in code and 'sqlalchemy' not in code:
                validation_result["suggestions"].append(
                    "Remember to use DATABASE_URL environment variable for database connection"
                )
        
        elif language == CodeLanguage.R:
            # Check for required packages
            if 'library' not in code.lower():
                validation_result["suggestions"].append(
                    "Consider explicitly loading required libraries (e.g., library(DBI), library(survival))"
                )
            # Check for database connection
            if 'DATABASE_URL' not in code and 'dbConnect' not in code:
                validation_result["suggestions"].append(
                    "Remember to use Sys.getenv('DATABASE_URL') for database connection"
                )
        
        return validation_result


# Singleton instance
_code_agent: Optional[CodeAgent] = None


def get_code_agent() -> CodeAgent:
    """Get singleton code agent instance."""
    global _code_agent
    if _code_agent is None:
        _code_agent = CodeAgent()
    return _code_agent
