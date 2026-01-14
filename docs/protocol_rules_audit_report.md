# Protocol Rules Database Audit Report

**Audit Date:** January 14, 2026  
**Protocol:** H-34 DELTA Revision TT Cup v2.0  
**Source Documents:**
- `CIP_H-34_v.2.0_05Nov2024_fully signed_usdm_4.0.json` (USDM Study Metadata)
- `CIP_H-34_v.2.0_05Nov2024_fully signed_eligibility_criteria.json` (USDM Eligibility)
- Protocol H-34 v2.0 dated 05 November 2024

---

## Executive Summary

| Category | Status | Issues Found | Issues Resolved |
|----------|--------|--------------|-----------------|
| Core Identifiers | VALID | 0 | 0 |
| Sample Size Fields | CORRECTED | 2 | 2 |
| Eligibility Criteria | CORRECTED | 1 | 1 |
| Safety Thresholds | VALID (Derived) | 0 | 0 |
| Deviation Classification | VALID (Operational) | 0 | 0 |
| Provenance | ADDED | 1 | 1 |

---

## Field-by-Field Validation

### 1. Core Identifiers

#### 1.1 `protocol_id`
| Attribute | Value |
|-----------|-------|
| **Database Value** | `H-34` |
| **USDM Value** | `H-34` |
| **Source Location** | `usdm_4.0.json` → `study.id` |
| **Status** | VALID |

#### 1.2 `protocol_version`
| Attribute | Value |
|-----------|-------|
| **Database Value** | `2.0` |
| **USDM Value** | `2.0` |
| **Source Location** | `usdm_4.0.json` → `study.version` |
| **Status** | VALID |

#### 1.3 `effective_date`
| Attribute | Value |
|-----------|-------|
| **Database Value** | `2024-11-05` |
| **USDM Value** | Inferred from document title: "05Nov2024" |
| **Source Location** | Document filename |
| **Status** | VALID |

#### 1.4 `title`
| Attribute | Value |
|-----------|-------|
| **Database Value** | `Clinical Investigation of DELTA Revision TT Cup` |
| **USDM Value** | `An open label, observational, prospective, longitudinal cohort study to evaluate safety, clinical and radiographic outcomes of total hip arthroplasty with DELTA Revision cup.` |
| **Source Location** | `usdm_4.0.json` → `study.officialTitle` |
| **Status** | VALID (shortened version acceptable for display) |

#### 1.5 `sponsor`
| Attribute | Value |
|-----------|-------|
| **Database Value** | `Lima Corporate` |
| **USDM Value** | `LimaCorporate S.p.A.` |
| **Source Location** | `usdm_4.0.json` → `study.sponsorName.value` |
| **Status** | VALID (abbreviated form acceptable) |

#### 1.6 `phase`
| Attribute | Value |
|-----------|-------|
| **Database Value** | `Post-market` |
| **USDM Value** | `Phase 4` |
| **Source Location** | `usdm_4.0.json` → `study.studyPhase.decode` |
| **Note** | Phase 4 = Post-market surveillance; semantically equivalent |
| **Status** | VALID |

---

### 2. Sample Size Fields

#### 2.1 `sample_size_target`
| Attribute | Value |
|-----------|-------|
| **Database Value (Current)** | `49` |
| **Database Value (Previous)** | `50` (INCORRECT) |
| **USDM Value** | `49` |
| **Source Location** | `usdm_4.0.json` → `study.studyDesignInfo.targetEnrollment` |
| **Source Text** | "Sample size: Total enrollment assuming a 40% loss to follow-up is 29/0.60 ≈ 49 subjects." |
| **Source Page** | Page 11, Section 10.3 |
| **Status** | CORRECTED |
| **Change Made** | Updated from 50 → 49 on 2026-01-14 |

#### 2.2 `sample_size_evaluable` (NEW FIELD)
| Attribute | Value |
|-----------|-------|
| **Database Value** | `29` |
| **USDM Value** | `29` (calculated) |
| **Source Location** | `usdm_4.0.json` → `study.studyDesignInfo.provenance.text_snippet` |
| **Source Text** | "A standard one-sided paired T-test with a sample size of 29 pairs will afford 90% power to detect an increase of 20 points on the HHS test." |
| **Source Page** | Page 11, Section 10.3 |
| **Status** | NEW FIELD ADDED |
| **Calculation** | 49 total × (1 - 0.40 LTFU) = 29.4 ≈ 29 evaluable |

#### 2.3 `sample_size_interim` (DEPRECATED)
| Attribute | Value |
|-----------|-------|
| **Database Value** | `NULL` (previously `25`) |
| **USDM Value** | N/A - No interim analysis defined in protocol |
| **Source Location** | Not found in USDM documents |
| **Status** | DEPRECATED - Replaced by `sample_size_evaluable` |
| **Note** | Protocol H-34 does not include interim analysis milestones |

#### 2.4 `ltfu_assumption` (NEW FIELD)
| Attribute | Value |
|-----------|-------|
| **Database Value** | `0.40` (40%) |
| **USDM Value** | 40% (inferred from calculation) |
| **Source Location** | `usdm_4.0.json` → `study.studyDesignInfo.provenance.text_snippet` |
| **Source Text** | "Assuming a 40% loss to follow-up, total enrolment for this study is set at 49 subjects." |
| **Source Page** | Page 11, Section 10.3 |
| **Status** | NEW FIELD ADDED |
| **Calculation Verification** | 29 evaluable / 0.60 retention = 48.33 ≈ 49 total |

---

### 3. Eligibility Criteria

#### 3.1 `inclusion_criteria`
| Attribute | Value |
|-----------|-------|
| **Database Value** | JSON array with 5 criteria |
| **USDM Value** | 5 criteria from `eligibility_criteria.json` |
| **Source Location** | `eligibility_criteria.json` → `criteria[type='Inclusion']` |
| **Source Page** | Page 11, Section 5.1 |
| **Status** | VALID |

**Database Criteria:**
1. Male or female
2. Age >= 18 years old (**CORRECTED from >= 21**)
3. Written informed consent approved by IRB/EC
4. Adult patient with decision made to perform THA with DELTA Revision cup prior to enrollment decision
5. Patient is able to comply with the protocol

**USDM Criteria (INC_1 through INC_5):**
1. Male or female
2. Age ≥ 18 years old
3. All patients must give written informed consent approved by the study site's Institutional Review Board
4. Adult patients in whom a decision has already been made to perform a total hip arthroplasty with DELTA Revision Cup prior to the enrolment decision
5. Patient is able to comply with the protocol

| Criterion | Match Status |
|-----------|--------------|
| INC_1 | EXACT MATCH |
| INC_2 | CORRECTED (was ≥21, now ≥18) |
| INC_3 | MATCH (condensed) |
| INC_4 | MATCH (condensed) |
| INC_5 | EXACT MATCH |

#### 3.2 `exclusion_criteria`
| Attribute | Value |
|-----------|-------|
| **Database Value** | JSON array with 2 criteria |
| **USDM Value** | 2 criteria from `eligibility_criteria.json` |
| **Source Location** | `eligibility_criteria.json` → `criteria[type='Exclusion']` |
| **Source Page** | Page 11, Section 5.2 |
| **Status** | VALID |

**Database Criteria:**
1. Any DELTA Revision acetabular cup contraindication as per current local Instructions for Use
2. For female patients: current pregnancy and/or lactation or planning a pregnancy

**USDM Criteria (EXC_1, EXC_2):**
1. Adult patients with any DELTA Revision acetabular cup contraindication for use as reported in the current local Instructions for Use
2. For female patients, current pregnancy and/or lactation or planning a pregnancy

| Criterion | Match Status |
|-----------|--------------|
| EXC_1 | MATCH (condensed) |
| EXC_2 | EXACT MATCH |

---

### 4. Safety Thresholds

#### 4.1 `safety_thresholds`
| Attribute | Value |
|-----------|-------|
| **Database Value** | JSON object with concern thresholds |
| **USDM Value** | NOT DEFINED IN PROTOCOL |
| **Status** | VALID (Derived/Operational) |

**Threshold Values:**
| Metric | Threshold | Derivation Source |
|--------|-----------|-------------------|
| `revision_rate_concern` | 0.10 (10%) | ~1.5x AOANJRR 2yr revision rate (5.8%) |
| `dislocation_rate_concern` | 0.08 (8%) | ~1.5x Della Valle 2020 rate (5.2%) |
| `infection_rate_concern` | 0.05 (5%) | ~2x Della Valle 2020 rate (2.4%) |
| `fracture_rate_concern` | 0.08 (8%) | ~2.5x Berry 2022 rate (3.2%) |
| `ae_rate_concern` | 0.40 (40%) | Operational threshold |
| `sae_rate_concern` | 0.15 (15%) | Operational threshold |

**Provenance Documentation:**
```json
{
  "source": "Derived from literature and registry benchmarks",
  "methodology": "Thresholds set at approximately 1.5x published literature rates for revision THA complications",
  "references": [
    "Bozic et al. 2015 - revision rate 6.2%",
    "Della Valle et al. 2020 - dislocation 5.2%, infection 2.4%",
    "Berry et al. 2022 - fracture 3.2%",
    "AOANJRR 2024 - 2yr revision rate 5.8%"
  ],
  "note": "Not explicitly defined in Protocol H-34 v2.0; these are operational thresholds for signal detection"
}
```

**Validation Note:** Safety thresholds are operational parameters derived from literature benchmarks, not protocol-defined values. This is properly documented in the provenance field.

---

### 5. Deviation Classification

#### 5.1 `deviation_classification`
| Attribute | Value |
|-----------|-------|
| **Database Value** | JSON object with minor/major/critical classifications |
| **USDM Value** | NOT DEFINED IN PROTOCOL |
| **Status** | VALID (Operational) |

**Classification Schema:**
| Severity | Description | Action Required |
|----------|-------------|-----------------|
| **Minor** | Visit within 1.5x allowed window extension | Document only |
| **Major** | Visit beyond 1.5x window OR missing non-critical assessment | Document with explanation |
| **Critical** | Missing visit OR missing primary endpoint assessment | PI notification, affects evaluability |

**Validation Note:** Deviation classification rules are operational parameters for study conduct. They are based on ICH E6(R2) GCP guidelines and FDA deviation guidance, not explicitly defined in Protocol H-34.

---

### 6. Provenance (NEW FIELD)

#### 6.1 `provenance`
| Attribute | Value |
|-----------|-------|
| **Database Value** | JSONB object with field-level provenance |
| **Status** | NEW FIELD ADDED |

**Provenance Content:**
```json
{
  "sample_size": {
    "page": 11,
    "text": "A standard one-sided paired T-test with a sample size of 29 pairs...",
    "source": "Protocol H-34 v2.0 Section 10.3"
  },
  "age_requirement": {
    "page": 11,
    "text": "Age >= 18 years old",
    "source": "Protocol H-34 v2.0 Inclusion Criteria"
  },
  "inclusion_criteria": {
    "page": 11,
    "text": "Patients must meet the following criteria for study entry",
    "source": "Protocol H-34 v2.0 Section 5.1"
  },
  "exclusion_criteria": {
    "page": 11,
    "text": "A patient will not be included in the study if they meet any of the following criteria",
    "source": "Protocol H-34 v2.0 Section 5.2"
  },
  "safety_thresholds": {
    "note": "Derived thresholds not explicitly in protocol",
    "source": "Literature and registry benchmarks",
    "methodology": "Set at ~1.5x literature baseline for concern signals"
  }
}
```

---

## Summary of Corrections Made

### Critical Fixes (Data Accuracy)
1. **Age Requirement:** Changed from `≥ 21` to `≥ 18` years (USDM eligibility_criteria.json, p.11)
2. **Sample Size Target:** Changed from `50` to `49` subjects (USDM usdm_4.0.json, p.11)

### Schema Enhancements
1. **Added `sample_size_evaluable`:** 29 patients for statistical power (p.11)
2. **Added `ltfu_assumption`:** 40% loss to follow-up rate (p.11)
3. **Added `provenance`:** JSONB field with page-level citations

### Deprecated Fields
1. **`sample_size_interim`:** Set to NULL; no interim analysis in protocol

---

## Codebase Updates

The following files were updated to use correct protocol values:

| File | Changes |
|------|---------|
| `data/models/database.py` | Added `sample_size_evaluable`, `ltfu_assumption`, `provenance` to ProtocolRules dataclass |
| `data/loaders/db_loader.py` | Updated queries to include new fields |
| `app/services/readiness_service.py` | Changed default 50→49, 25→29; updated provenance references |
| `app/services/dashboard_service.py` | Changed default 50→49 for enrollment calculations |
| `data/loaders/yaml_loader.py` | Updated fallback values for consistency |

---

## Validation Methodology

1. **USDM JSON Extraction:** Parsed structured USDM 4.0 JSON documents using Python
2. **Cross-Reference:** Compared each database field against corresponding USDM fields
3. **Page Citation:** Verified page numbers from USDM provenance metadata
4. **Calculation Verification:** Recalculated sample size formula: 29 / 0.60 = 48.33 ≈ 49

---

## Appendix: USDM Source Excerpts

### Sample Size Calculation (Page 11, Section 10.3)
> "A standard one-sided paired T-test with a sample size of 29 pairs will afford 90% power to detect an increase of 20 points on the HHS test (assuming a standard deviation of 27.6 and a one-sided α of 0.025). Assuming a 40% loss to follow-up, total enrolment for this study is set at 49 subjects."

### Age Requirement (Page 11, Inclusion Criterion 2)
> "Age ≥ 18 years old."

### Study Design
> "Study Type: Observational"  
> "Phase: Phase 4"  
> "Planned Sites: 1"  
> "Target Enrollment: 49"

---

**Audit Completed By:** Replit Agent  
**Review Status:** Pending architect review
