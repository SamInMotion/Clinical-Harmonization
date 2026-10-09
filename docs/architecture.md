# Architecture — Clinical Harmonization Pipeline

**Version:** 1.0  
**Last updated:** 2026-10-09

---

## Overview

This project implements a pipeline that transforms biomedical text (BC5CDR) into standardized clinical representations (OMOP/FHIR).

[200~Raw text (BC5CDR)
↓
NER (dictionary baseline)
↓
Entity mentions
↓
Entity linking (SNOMED-CT, RxNorm)
↓
OMOP domain routing (drug_exposure, condition_occurrence)
↓
FHIR transformation (Condition, MedicationRequest)
↓
Error decomposition~
---

## Pipeline Stages

### 1. Entity Extraction (NER)

**Input:** Raw text (BC5CDR abstracts)  
**Output:** Entity mentions with offsets  
**Method:** Dictionary baseline (exact match after normalization)  
**Performance:** P=0.797, R=0.565, F1=0.661

**Script:** `src/ner/dictionary_baseline.py`

---

### 2. Entity Linking

**Input:** Extracted entity mentions  
**Output:** Linked entities with concept IDs  
**Method:** Exact match against terminology (SNOMED-CT, RxNorm)  
**Coverage:** 11.2% (785 of 7,038 entities)

**Script:** `src/linking/entity_linking.py`

---

### 3. OMOP Domain Routing

**Input:** Linked entities  
**Output:** OMOP records (drug_exposure, condition_occurrence)  
**Method:** Domain-based routing (Chemical → Drug, Disease → Condition)  
**Routing rate:** 100%

**Script:** `src/mapping/omop_routing.py`

---

### 4. FHIR Transformation

**Input:** OMOP records  
**Output:** FHIR resources (Condition, MedicationRequest)  
**Method:** Direct transformation (OMOP → FHIR)  
**Transformation rate:** 100%

**Script:** `src/mapping/fhir_transform.py`

---

### 5. Error Decomposition

**Input:** Gold entities, predicted entities, linked entities, OMOP records, FHIR resources  
**Output:** Error breakdown by stage  
**End-to-end survival:** 7.9% (785 FHIR / 9,928 gold)

**Script:** `src/evaluation/error_decomposition.py`

---

## Data Flow
BC5CDR Test Set (500 abstracts, 9,928 gold entities)
↓
Dictionary NER (7,038 predicted entities)
↓
Entity Linking (785 linked, 6,253 unlinked)
↓
OMOP Routing (785 records: 465 conditions, 320 drugs)
↓
FHIR Transformation (785 resources: 465 Conditions, 320 MedicationRequests)
↓
Error Decomposition (7.9% end-to-end survival)

text

---

## Key Metrics

| Stage | Metric | Value |
|-------|--------|-------|
| Extraction | Precision | 0.797 |
| Extraction | Recall | 0.565 |
| Extraction | F1 | 0.661 |
| Linking | Linking rate | 11.2% |
| OMOP Routing | Routing rate | 100% |
| FHIR Transformation | Transformation rate | 100% |
| End-to-End | Survival rate | 7.9% |

---

## Error Analysis

### Extraction errors
- **False negatives (4,313):** Entities not in dictionary (vocabulary coverage limit)
- **False positives (1,429):** Real entities not annotated in gold standard (BC5CDR is selective)

### Linking errors
- **Unlinked (6,253):** Entities not in terminology (limited coverage)

### OMOP/FHIR errors
- **None** — 100% routing and transformation rates

---

## Limitations

1. **Dictionary baseline** — Cannot generalize to unseen entities
2. **Limited terminology** — Only ~20 concepts in mock terminology
3. **No transformer NER** — Hugging Face authentication issues blocked fine-tuning
4. **No scispaCy** — Version mismatch (scispaCy 0.2.3 vs spaCy 3.8.16)

---

## Future Work

1. **Transformer NER** — Fine-tune BioBERT/PubMedBERT for better generalization
2. **Full terminology** — Load complete SNOMED-CT, RxNorm, ICD-10-CM
3. **Fuzzy matching** — Handle entity variants and abbreviations
4. **Embedding-based linking** — Semantic similarity for better coverage

---

**Last updated:** 2026-10-09
