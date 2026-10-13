# Clinical Harmonization Pipeline — Project Closeout

**Status:** Active research prototype; core extract → harmonize → report workflow complete  
**Date:** 2026-10-13  
**Repository:** `clinical-harmonization`  
**Primary experiments:** EXP-007 through EXP-014A  
**Next planned experiment:** EXP-014B — false-positive analysis of the frozen hybrid configuration  

---

## Objective

Build a reproducible clinical NLP pipeline that:

1. extracts biomedical entity mentions from BC5CDR documents;
2. harmonizes them against a deliberately incomplete, controlled OMOP-style vocabulary;
3. routes mapped concepts to domain-appropriate destination tables;
4. preserves unmapped mentions for review rather than forcing incorrect mappings;
5. reports extraction, mapping, routing, and per-document activity.

The project investigates where errors enter the transformation from biomedical text to standardized clinical concepts. It does not claim end-to-end clinical correctness, OMOP CDM validity, FHIR conformance, or deployment readiness.

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
| False positives | 1,421 |
| False negatives | 4,339 |
| Precision | 0.7981 |
| Recall | 0.5642 |
| F1 | 0.6611 |

### EXP-009: word-boundary strategy

EXP-009 compared lexical strategies. Its word-boundary strategy is used by the active EXP-010 pipeline.

| Metric | Result |
|---|---:|
| Gold entities | 9,956 |
| Predicted entities | 6,338 |
| True positives | 5,616 |
| False positives | 722 |
| False negatives | 4,340 |
| Precision | 0.8861 |
| Recall | 0.5641 |
| F1 | 0.6893 |

Word-boundary matching removed 700 substring false positives and lost one true positive relative to substring matching.

### EXP-007: PubMedBERT alternative

| Extractor | Predicted | True positives | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| EXP-009 word-boundary dictionary | 6,338 | 5,616 | 0.8861 | 0.5641 | 0.6893 |
| PubMedBERT epoch 3 | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |

PubMedBERT improved recall but reduced precision. The dictionary word-boundary extractor remains the production extractor for EXP-010 because it is deterministic, auditable, and aligned with controlled-vocabulary mapping.

### Abbreviation expansion: negative result

On the BC5CDR development set, abbreviation expansion increased recall slightly but reduced precision and F1.

| Metric | Base dictionary | Expanded dictionary | Difference |
|---|---:|---:|---:|
| Precision | 0.8158 | 0.7390 | -0.0768 |
| Recall | 0.5847 | 0.5934 | +0.0088 |
| F1 | 0.6812 | 0.6583 | -0.0229 |

The expanded dictionary is retained as provenance and an evaluated negative result. It is not used in production.

---

## Hybrid extraction results

### EXP-012: unthresholded hybrid

EXP-012 retained every base-dictionary prediction and added a PubMedBERT prediction only when it did not overlap a dictionary prediction of the same entity type in the same document.

| System | Predicted | TP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Base dictionary | 7,038 | 5,617 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT only | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |
| Hybrid union | 12,834 | 8,121 | 0.6328 | 0.8157 | 0.7127 |

The unthresholded hybrid improved F1 by 0.0516 over the dictionary baseline but reduced precision from 0.7981 to 0.6328.

### EXP-013: exploratory test-set threshold sweep

EXP-013 assigned each PubMedBERT prediction a confidence score:

> the maximum softmax probability assigned to the predicted class among tokens overlapping the predicted entity span.

It then swept confidence thresholds on the **BC5CDR test set**.

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| Dictionary baseline | — | 0.7981 | 0.5642 | 0.6611 |
| 0.50 | 5,642 | 0.6399 | 0.8150 | 0.7169 |
| 0.60 | 5,282 | 0.6561 | 0.8119 | 0.7257 |
| 0.70 | 4,949 | 0.6720 | 0.8091 | 0.7342 |
| 0.80 | 4,545 | 0.6908 | 0.8036 | 0.7429 |
| 0.85 | 4,275 | 0.7034 | 0.7992 | 0.7482 |
| 0.90 | 3,876 | 0.7227 | 0.7923 | 0.7559 |
| 0.93 | 3,480 | 0.7418 | 0.7836 | 0.7621 |
| 0.95 | 3,062 | 0.7609 | 0.7719 | 0.7664 |
| 0.97 | 2,307 | 0.7880 | 0.7397 | 0.7631 |
| 0.98 | 1,756 | 0.8044 | 0.7105 | 0.7546 |
| 0.99 | 945 | 0.8072 | 0.6472 | 0.7184 |

**Status:** Exploratory test-set model selection.

Because the threshold was selected by comparing F1 across thresholds on the same test set used for reporting, the EXP-013 optimum is optimistically biased. Thresholds 0.95 and 0.97 are exploratory candidates, not independently validated operating points.

EXP-013 is retained as provenance and as a sensitivity analysis of the precision-recall trade-off. It must not be used as the final hybrid evaluation or as the basis for production promotion.

### EXP-014A: authoritative frozen hybrid evaluation

EXP-014A corrected the evaluation design:

1. It exported development-set gold, dictionary, and PubMedBERT predictions.
2. It ran the threshold sweep only on the development set.
3. It selected the threshold with maximum development F1, breaking ties by higher precision.
4. It froze threshold 0.95.
5. It evaluated the frozen configuration once on the untouched BC5CDR test set.

Development-set selection result:

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| Dictionary baseline | — | 0.8158 | 0.5847 | 0.6812 |
| **0.95** | **2,869** | **0.7660** | **0.7733** | **0.7696** |

Final test-set evaluation:

| System | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dictionary | 7,038 | 5,617 | 1,421 | 4,339 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT epoch 3 | 13,316 | 7,290 | 6,026 | 2,666 | 0.5475 | 0.7322 | 0.6265 |
| Frozen hybrid, threshold 0.95 | 10,100 | 7,685 | 2,415 | 2,271 | 0.7609 | 0.7719 | 0.7664 |

The development-selected 0.95 hybrid improves recall from 0.5642 to 0.7719 relative to the dictionary while reducing precision from 0.7981 to 0.7609. It improves F1 from 0.6611 to 0.7664.

EXP-014A is the current authoritative hybrid result. The hybrid is not promoted to the production pipeline until EXP-014B analyzes its false positives.

---

## Harmonization results

### EXP-010: controlled harmonization and routing

| Measure | Result |
|---|---:|
| Extracted occurrences | 6,338 |
| Mapped occurrences | 651 |
| Unmapped occurrences | 5,687 |
| Mapping rate over extracted occurrences | 10.3% |
| Routed to `drug_exposure` | 371 |
| Routed to `condition_occurrence` | 280 |
| Not routed | 5,687 |

The 10.3% figure is a **mapping rate over extracted occurrences**. It is not vocabulary coverage, mapping precision, or end-to-end correctness.

The low mapping rate reflects the intentionally incomplete 29-concept vocabulary, not extractor failure.

### EXP-011: mapping quality

A mapped record is **gold-supported** when:

1. its document-level character span matches a gold entity;
2. its entity type matches;
3. its mapped concept matches the normalized gold mention or a controlled variant.

This establishes gold-supported lexical mapping. It does not by itself establish semantic equivalence between a BC5CDR chemical or disease mention and an OMOP drug or condition concept.

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

## Metric definitions

| Metric | Denominator | Meaning |
|---|---|---|
| Extraction precision | Predicted entities | Share of predicted spans that exactly match a gold span and type |
| Extraction recall | Gold entities | Share of gold spans that are exactly predicted |
| Mapping rate | Extracted occurrences | Share of extracted occurrences that received a mapped concept |
| Vocabulary coverage | Vocabulary-representable gold entities | Share of eligible gold entities for which the vocabulary contains a candidate |
| Mapping precision | Accepted mappings | Share of accepted mappings supported by gold evidence |
| Vocabulary recall | Vocabulary-representable gold entities | Share of eligible gold entities that were mapped |
| End-to-end yield | Defined gold population | Share of gold mentions that become correct standardized representations |

No validated end-to-end yield metric currently exists.

---

## Key design decisions

### Abstention over forced mapping

Unmapped mentions are preserved with a reason rather than forced into a destination table. This preserves auditability and avoids manufacturing unsupported clinical concepts.

### Controlled vocabulary

The 29-concept vocabulary is intentionally incomplete. This supports a controlled evaluation of mapping and routing behavior.

### Domain-safe routing

Drug-domain concepts route to `drug_exposure`; condition-domain concepts route to `condition_occurrence`. Observation-domain concepts are not routed.

### Evaluation separation

Extraction, mapping, routing, and reporting are evaluated separately. Pass-through counts are not treated as correctness, accuracy, validity, or conformance metrics.

### Threshold-selection separation

Model-selection decisions must be made on development data. The test set is reserved for final evaluation of a frozen configuration.

---

## Historical corrections

| Result | Status | Reason |
|---|---|---|
| Dictionary F1 = 0.0966 | INVALID | Document-global and passage-local offsets were compared directly. |
| Dictionary F1 = 0.6614 | SUPERSEDED | One-location gold representation and type-blind matching. |
| Gate C-2 dictionary F1 = 0.6611 | Historical baseline | Location-level, type-aware base-dictionary evaluation. |
| EXP-004 dictionary F1 = 0.6893 | MISATTRIBUTED | EXP-004 was the PubMedBERT tiny-overfit preflight; the result belongs to EXP-009. |
| End-to-end survival = 7.9% | INVALID AS CORRECTNESS | Raw count ratio without gold-to-concept verification. |
| EXP-013 threshold 0.95 as final operating point | SUPERSEDED BY EXP-014A | Threshold was selected on the test set; EXP-014A provides the development-selected frozen evaluation. |

---

## Claims boundary

This project supports the following claims:

- EXP-008 base-dictionary extraction achieves P 0.7981, R 0.5642, and F1 0.6611 on the BC5CDR test set.
- EXP-009 word-boundary extraction achieves P 0.8861, R 0.5641, and F1 0.6893 on the BC5CDR test set.
- EXP-007 PubMedBERT epoch 3 achieves P 0.5475, R 0.7322, and F1 0.6265 on the BC5CDR test set.
- EXP-010 maps 651 of 6,338 extracted occurrences, a 10.3% mapping rate, using a deliberately incomplete 29-concept vocabulary.
- EXP-011 finds mapping precision 0.9662 and vocabulary recall 0.9722.
- EXP-012 finds that an unthresholded dictionary and PubMedBERT hybrid achieves P 0.6328, R 0.8157, and F1 0.7127.
- EXP-013 is an exploratory test-set threshold sweep; its 0.95 result is not an independently selected operating point.
- EXP-014A finds that a development-selected, frozen 0.95-confidence hybrid achieves P 0.7609, R 0.7719, and F1 0.7664 on the BC5CDR test set.

This project does **not** support claims of:

- production clinical deployment;
- end-to-end OMOP CDM validity;
- FHIR conformance;
- clinical correctness;
- comprehensive SNOMED CT, ICD-10-CM, RxNorm, or LOINC coverage;
- generalization beyond BC5CDR;
- validated hybrid production readiness;
- semantic equivalence established solely by lexical mapping.

---

## Release and provenance constraints

Before presenting the repository as a public portfolio showcase:

1. Confirm whether `data/terminology/omop_exercise_vocabulary.json` may be redistributed.
2. Replace assessment-supplied vocabulary with a synthetic fixture or independently sourced, appropriately licensed vocabulary if redistribution is not permitted.
3. Document the source, license, and acquisition instructions for BC5CDR.
4. Review BC5CDR-derived dictionaries for redistribution permissions.
5. Review `.llm-provenance.md`, assessment-specific wording, and session notes for confidential material.
6. Do not commit generated files under `output/`.

---

## Reproducibility

```bash
.venv/Scripts/python.exe src/pipeline/run_pipeline.py
.venv/Scripts/python.exe src/ner/evaluate_dictionary_exp008.py
.venv/Scripts/python.exe src/evaluation/evaluate_mapping_quality.py
.venv/Scripts/python.exe src/evaluation/export_exp014a_development_predictions.py
.venv/Scripts/python.exe src/evaluation/evaluate_exp014a_development_threshold_sweep.py
.venv/Scripts/python.exe src/evaluation/evaluate_exp014a_frozen_test_hybrid.py
.venv/Scripts/python.exe src/pipeline/build_dashboard.py
```

Core outputs:

```text
output/harmonization/exp010/harmonized_records.csv
output/harmonization/exp010/mapped_records.csv
output/harmonization/exp010/unmapped_mentions.csv
output/evaluation/exp008_dictionary_bc5cdr_test_location_level.json
output/evaluation/exp011_mapping_quality.json
output/evaluation/exp014a_development_threshold_sweep.json
output/evaluation/exp014a_frozen_test_evaluation.json
output/dashboard/clinical_harmonization_dashboard.html
```

---

## Future work

1. Complete EXP-014B: analyze false positives introduced by the frozen 0.95 hybrid.
2. Decide whether to promote, modify, or reject the hybrid based on the error analysis.
3. Correct metric labels in the dashboard and separate mapping rate, vocabulary coverage, mapping precision, and end-to-end yield.
4. Complete the terminology and assessment-artifact redistribution audit.
5. Add a clean setup and one-command reproduction path.
6. Add per-mention gold-to-standardized-concept evaluation before making end-to-end correctness claims.
7. Expand the controlled vocabulary and measure the effect on mapping rate, vocabulary coverage, and mapping precision.