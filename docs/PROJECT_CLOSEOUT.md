# Clinical Harmonization Pipeline — Project Closeout

**Status:** Complete for the improved extract → harmonize → report exercise  
**Date:** 2026-10-13  
**Repository:** `clinical-harmonization`  
**Primary experiments:** EXP-007 through EXP-011  

---

## Objective

Build a reproducible clinical NLP pipeline that:

1. extracts biomedical entity mentions from BC5CDR documents;
2. harmonizes them against a deliberately incomplete, controlled OMOP-style vocabulary;
3. routes mapped concepts to domain-appropriate destination tables;
4. preserves unmapped mentions for review rather than forcing incorrect mappings;
5. reports pipeline coverage, mapping quality, and per-document activity.

---

## Pipeline architecture

```text
BC5CDR BioC XML
      |
      v
Dictionary word-boundary extractor
      |
      v
Harmonized occurrence records
      |
      +--> Controlled vocabulary mapping
      |
      +--> Domain-safe OMOP-style routing
      |
      +--> Unmapped mention preservation
      |
      v
Static HTML dashboard
```

The active vocabulary contains 29 concepts: 17 drugs and 12 conditions. It is deliberately incomplete, making the project a controlled evaluation of extraction, mapping, routing, and abstention rather than a claim of comprehensive terminology coverage.

---

## Extraction results

### EXP-008: verified base-dictionary baseline

EXP-008 evaluated the base BC5CDR training dictionary on the test set using location-level, type-aware exact-span matching.

| Metric | Result |
|---|---:|
| Gold entities | 9,956 |
| Predicted entities | 7,038 |
| True positives | 5,617 |
| Precision | 0.7981 |
| Recall | 0.5642 |
| F1 | 0.6611 |

### EXP-009: word-boundary strategy

EXP-009 compared lexical strategies. Its word-boundary strategy is used by the active EXP-010 pipeline.

| Metric | Result |
|---|---:|
| Gold entities | 9,956 |
| Predicted entities | 6,338 |
| Exact matches / true positives | 5,616 |
| False positives | 722 |
| False negatives | 4,340 |
| Precision | 0.8861 |
| Recall | 0.5641 |
| F1 | 0.6893 |

### EXP-007: PubMedBERT alternative

| Extractor | Predicted | True positives | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| EXP-009 word-boundary dictionary | 6,338 | 5,616 | 0.8861 | 0.5641 | 0.6893 |
| PubMedBERT epoch 3 | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |
PubMedBERT improved recall but reduced precision. The dictionary word-boundary extractor remains the production extractor because it is deterministic, auditable, and aligned with controlled-vocabulary mapping.

### Abbreviation expansion: negative result

On the BC5CDR development set, abbreviation expansion increased recall slightly but reduced precision and F1.

| Metric | Base dictionary | Expanded dictionary | Difference |
|---|---:|---:|---:|
| Precision | 0.8158 | 0.7390 | -0.0768 |
| Recall | 0.5847 | 0.5934 | +0.0088 |
| F1 | 0.6812 | 0.6583 | -0.0229 |

The expanded dictionary is retained as provenance and an evaluated negative result.

---

## Harmonization results

### EXP-010: controlled harmonization and routing

| Measure | Result |
|---|---:|
| Extracted occurrences | 6,338 |
| Mapped | 651 |
| Unmapped | 5,687 |
| Vocabulary coverage | 10.3% |
| `drug_exposure` | 371 |
| `condition_occurrence` | 280 |
| Not routed | 5,687 |

The low coverage reflects the intentionally incomplete 29-concept vocabulary, not extractor failure.

### EXP-011: mapping quality

A mapped record is gold-supported when its document-level span and entity type match a gold entity, and its mapped concept matches the normalized gold mention or a controlled variant.

| Measure | Result |
|---|---:|
| Mapped records | 651 |
| Gold-supported mappings | 629 |
| Unsupported mappings | 22 |
| Mapping precision | 0.9662 |
| Vocabulary-representable gold entities | 647 |
| Vocabulary-representable mapped entities | 629 |
| Vocabulary recall | 0.9722 |

---

## Key design decisions

### Abstention over forced mapping

Unmapped mentions are preserved with a reason rather than forced into a destination table. This preserves auditability and avoids manufacturing unsupported clinical concepts.

### Controlled vocabulary

The 29-concept vocabulary is intentionally incomplete. This supports a controlled evaluation of mapping and routing behavior.

### Domain-safe routing

Drug-domain concepts route to `drug_exposure`; condition-domain concepts route to `condition_occurrence`. Observation-domain concepts are not routed.

### Evaluation separation

Extraction, mapping, routing, and reporting are evaluated separately. End-to-end counts are not treated as correctness metrics.

---

## Historical corrections

| Result | Status | Reason |
|---|---|---|
| Dictionary F1 = 0.0966 | INVALID | Document-global and passage-local offsets were compared directly. |
| Dictionary F1 = 0.6614 | SUPERSEDED | One-location gold representation and type-blind matching. |
| Gate C-2 dictionary F1 = 0.6611 | Historical baseline | Location-level, type-aware base-dictionary evaluation. |
| EXP-004 dictionary F1 = 0.6893 | MISATTRIBUTED | EXP-004 was PubMedBERT tiny-overfit preflight; the result belongs to EXP-009. |
| End-to-end survival = 7.9% | INVALID AS CORRECTNESS | Raw count ratio without gold-to-concept verification. |

---

## Claims boundary

This project supports the following claim:

> “I built and evaluated a reproducible clinical text harmonization pipeline that extracts biomedical mentions using a word-boundary dictionary strategy, maps them to a deliberately incomplete OMOP-style vocabulary using controlled normalization and domain-safe routing, preserves unmapped mentions for review, and reports per-stage quality against gold annotations.”

It does **not** support claims of:

- production clinical deployment;
- end-to-end OMOP CDM validity;
- FHIR conformance;
- comprehensive medical terminology coverage;
- generalization beyond BC5CDR;
- validated FHIR transformation;
- use of the full SNOMED CT ontology;
- validated hybrid NER performance.

---

## Reproducibility

```bash
python src/pipeline/run_pipeline.py
python src/ner/evaluate_dictionary_exp008.py
python src/evaluation/evaluate_mapping_quality.py
python src/pipeline/build_dashboard.py
```

Core outputs:

```text
output/harmonization/exp010/harmonized_records.csv
output/harmonization/exp010/mapped_records.csv
output/harmonization/exp010/unmapped_mentions.csv
output/evaluation/exp008_dictionary_bc5cdr_test_location_level.json
output/evaluation/exp011_mapping_quality.json
output/dashboard/clinical_harmonization_dashboard.html
```

---

## Future work

1. Confirm and preserve the full EXP-009 evaluation policy and population definitions.
2. Export dictionary and PubMedBERT predictions under a common document-level offset representation.
3. Run EXP-012 hybrid extraction using the verified base dictionary and PubMedBERT epoch-3 checkpoint.
4. Expand the controlled vocabulary and measure the effect on coverage and mapping precision.
5. Add per-mention gold-to-standardized-concept evaluation before making end-to-end correctness claims.