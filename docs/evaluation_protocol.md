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

**Current result (Gate C-2, 2026-10-10):**
- Gold denominator: 9,965 location-level gold spans
- Precision: 0.7981
- Recall: 0.5642
- F1: 0.6611
- TP: 5,617
- FP: 1,421
- FN: 4,339

**Historical one-location result:** F1 0.6614 using 9,928 annotation records; superseded because it retained only the first BioC location per annotation.

---

### 2. Entity Linking

**Metric:** Predicted-mention terminology coverage; not linking accuracy

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

**Metric:** Pass-through routing coverage; not semantic routing accuracy or OMOP CDM validation

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

**Metric:** Pass-through serialization coverage; not FHIR conformance validation

**Definition:**
- **Transformed:** OMOP record has FHIR resource
- **Not transformed:** OMOP record does not have FHIR resource

**Formula:**
- Transformation rate = Transformed / Routed

**Results:**
- Transformed: 785
- Transformation rate: 100%

---

### 5. Raw End-to-End Count Ratio

**Metric:** Raw FHIR-resource-to-gold-location-span count ratio

**Definition:**
- This is a raw pipeline count ratio.
- It does **not** join FHIR resources to gold spans.
- It does **not** verify that a gold mention was correctly extracted, linked, routed, or represented.
- It must not be interpreted as end-to-end accuracy or correctness.

**Current result:**
- Gold location spans: 9,965
- FHIR resources: 785
- Raw count ratio: 7.9%

---

## Error Taxonomy

### Extraction errors
- **False negatives:** Entities not in dictionary (vocabulary coverage limit)
- **False positives:** Real entities not annotated in gold standard (BC5CDR is selective)

### Linking errors
- **Unlinked:** Entities not in terminology (limited coverage)

### OMOP/FHIR limitations
- Routing and serialization are pass-through counts, not validated semantic correctness.
- No OMOP CDM validation or FHIR conformance validation has been performed.

---

## Evaluation Design

**Test set:** BC5CDR Test Set (500 abstracts, 9,965 location-level gold spans)

**Coordinate system:** Passage-local offsets (not document-global)

**Matching:** Exact span match on document ID, passage type, passage-local offset, location length, and entity type.

**Gold representation:** One gold span per BioC `<location>`; annotation-level text and MeSH ID are retained as provenance.

---

## Limitations

1. **Dictionary baseline** — Cannot generalize to unseen entities
2. **Limited terminology** — Only ~20 concepts in mock terminology
3. **No transformer NER** — Hugging Face authentication issues blocked fine-tuning

---

**Last updated:** 2026-10-09
