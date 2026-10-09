# Evaluation Protocol — Clinical Harmonization Pipeline

**Version:** 1.0  
**Last updated:** 2026-10-09

---

## Overview

This document describes the evaluation protocol for the clinical harmonization pipeline.

---

## Evaluation Metrics

### 1. Entity Extraction (NER)

**Metric:** Precision, Recall, F1 (exact span match)

**Definition:**
- **True Positive (TP):** Predicted entity matches gold entity (doc_id, passage_type, offset, length)
- **False Positive (FP):** Predicted entity does not match any gold entity
- **False Negative (FN):** Gold entity not predicted

**Formula:**
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = 2 * Precision * Recall / (Precision + Recall)

**Results:**
- Precision: 0.797
- Recall: 0.565
- F1: 0.661

---

### 2. Entity Linking

**Metric:** Linking rate

**Definition:**
- **Linked:** Entity has concept_id (matched to terminology)
- **Unlinked:** Entity does not have concept_id

**Formula:**
- Linking rate = Linked / Total predicted

**Results:**
- Linked: 785
- Unlinked: 6,253
- Linking rate: 11.2%

---

### 3. OMOP Domain Routing

**Metric:** Routing rate

**Definition:**
- **Routed:** Entity has omop_table (drug_exposure or condition_occurrence)
- **Not routed:** Entity does not have omop_table

**Formula:**
- Routing rate = Routed / Linked

**Results:**
- Routed: 785
- Routing rate: 100%

---

### 4. FHIR Transformation

**Metric:** Transformation rate

**Definition:**
- **Transformed:** OMOP record has FHIR resource
- **Not transformed:** OMOP record does not have FHIR resource

**Formula:**
- Transformation rate = Transformed / Routed

**Results:**
- Transformed: 785
- Transformation rate: 100%

---

### 5. End-to-End Survival

**Metric:** Survival rate

**Definition:**
- **Survived:** Gold entity has corresponding FHIR resource
- **Lost:** Gold entity does not have FHIR resource

**Formula:**
- Survival rate = FHIR resources / Gold entities

**Results:**
- Gold entities: 9,928
- FHIR resources: 785
- Survival rate: 7.9%

---

## Error Taxonomy

### Extraction errors
- **False negatives:** Entities not in dictionary (vocabulary coverage limit)
- **False positives:** Real entities not annotated in gold standard (BC5CDR is selective)

### Linking errors
- **Unlinked:** Entities not in terminology (limited coverage)

### OMOP/FHIR errors
- **None** — 100% routing and transformation rates

---

## Evaluation Design

**Test set:** BC5CDR Test Set (500 abstracts, 9,928 gold entities)

**Coordinate system:** Passage-local offsets (not document-global)

**Matching:** Exact span match (doc_id, passage_type, offset, length)

---

## Limitations

1. **Dictionary baseline** — Cannot generalize to unseen entities
2. **Limited terminology** — Only ~20 concepts in mock terminology
3. **No transformer NER** — Hugging Face authentication issues blocked fine-tuning

---

**Last updated:** 2026-10-09
