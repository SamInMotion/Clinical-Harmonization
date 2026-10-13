# Project State Register — Clinical Harmonization

**Purpose:** Canonical current-state register for this repository. Read this before making changes. Update the relevant sections at every session closeout.

**Last updated:** 2026-10-13  
**Maintainer:** Samuel Okoe-Mensah  
**Status:** Active research prototype; not a validated clinical system  

---

## 1. Status snapshot

| Item | Current verified state | Last verified |
|---|---|---|
| Repository | `clinical-harmonization` | 2026-10-13 |
| Branch | `master` | 2026-10-13 |
| Remote | `https://github.com/SamInMotion/Clinical-Harmonization.git` | 2026-10-13 |
| HEAD | `2c5ddd6` — `feat: export PubMedBERT span confidence for EXP-013` | 2026-10-13 |
| Working tree | Clean | 2026-10-13 |
| Active Python | Use `.venv/Scripts/python.exe` explicitly | 2026-10-13 |
| Project virtual environment | `.venv/` exists | 2026-10-13 |
| Active extraction strategy | EXP-009 word-boundary dictionary | 2026-10-13 |
| Active harmonization pipeline | EXP-010 | 2026-10-13 |
| Authoritative hybrid evaluation | EXP-014A frozen 0.95-confidence hybrid | 2026-10-13 |
| Hybrid promotion decision | Not made; requires EXP-014B | 2026-10-13 |
| Test suite | Limited focused regression coverage; no comprehensive end-to-end suite | 2026-10-13 |

**Environment rule:** Use `.venv/Scripts/python.exe` explicitly until shell activation is verified. Do not assume `python` refers to the project virtual environment.

---

## 2. Project scope

The project investigates whether biomedical text can be transformed reliably into standardized clinical representations and where errors enter that transformation.

Implemented stages:

1. Chemical/disease mention extraction.
2. Controlled-vocabulary mapping.
3. Domain-safe OMOP-style routing.
4. Unmapped-mention preservation and abstention.
5. Static reporting.

Primary corpus: BC5CDR BioC XML at `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/`.

This is a prototype. Current terminology, mapping logic, routing logic, and pass-through counts do not establish clinical correctness, OMOP CDM validity, FHIR conformance, or end-to-end semantic accuracy.

---

## 3. Current architecture

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

The active vocabulary contains 29 concepts: 17 drugs and 12 conditions. It is deliberately incomplete.

Routing policy:

| OMOP-style domain | Destination |
|---|---|
| Drug | `drug_exposure` |
| Condition | `condition_occurrence` |
| Observation | Not routed |

Unmapped mentions are preserved rather than force-mapped.

---

## 4. Current verified results

### Extraction

| Experiment | System | Split | Predicted | TP | Precision | Recall | F1 | Status |
|---|---|---|---:|---:|---:|---:|---:|---|
| EXP-008 | Base dictionary | Test | 7,038 | 5,617 | 0.7981 | 0.5642 | 0.6611 | Verified baseline |
| EXP-009 | Word-boundary dictionary | Test | 6,338 | 5,616 | 0.8861 | 0.5641 | 0.6893 | Current production extractor |
| EXP-007 | PubMedBERT epoch 3 | Test | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 | Evaluated alternative |

All extraction evaluations use location-level, type-aware exact-span matching.

### Abbreviation expansion

Abbreviation expansion was evaluated on the BC5CDR development set and was a negative result.

| Dictionary | Precision | Recall | F1 |
|---|---:|---:|---:|
| Base dictionary | 0.8158 | 0.5847 | 0.6812 |
| Abbreviation-expanded | 0.7390 | 0.5934 | 0.6583 |

Expansion added 846 predictions, gained 86 true positives, and introduced 760 false positives. It is retained as provenance and is not used in production.

### Harmonization

| Measure | Result |
|---|---:|
| Extracted occurrences | 6,338 |
| Mapped occurrences | 651 |
| Unmapped occurrences | 5,687 |
| Mapping rate over extracted occurrences | 10.3% |
| Routed to `drug_exposure` | 371 |
| Routed to `condition_occurrence` | 280 |
| Not routed | 5,687 |

The 10.3% figure is a mapping rate over extracted occurrences. It is not vocabulary coverage, mapping precision, or end-to-end correctness.

### Mapping quality

| Measure | Result |
|---|---:|
| Mapped records | 651 |
| Gold-supported mappings | 629 |
| Unsupported mappings | 22 |
| Mapping precision | 0.9662 |
| Vocabulary-representable gold entities | 647 |
| Vocabulary-representable mapped entities | 629 |
| Vocabulary recall | 0.9722 |

A gold-supported mapping means that the mapped record matches a gold entity’s document-level span and type, and its mapped concept matches the normalized gold mention or a controlled variant. This does not establish semantic equivalence to an OMOP concept.

---

## 5. Hybrid extraction status

### EXP-012: unthresholded hybrid

**Status:** Complete.

| System | Predicted | TP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Base dictionary | 7,038 | 5,617 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT only | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |
| Hybrid union | 12,834 | 8,121 | 0.6328 | 0.8157 | 0.7127 |

The unthresholded hybrid improved F1 by 0.0516 over the dictionary baseline but reduced precision from 0.7981 to 0.6328.

### EXP-013: exploratory test-set threshold sweep

**Status:** Complete; exploratory test-set model selection.

EXP-013 assigned each PubMedBERT prediction a confidence score:

> the maximum softmax probability assigned to the predicted class among tokens overlapping the predicted entity span.

It then swept thresholds directly on the BC5CDR test set. Because the threshold was selected by comparing F1 across test-set thresholds, its optimum is optimistically biased.

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| Dictionary baseline | — | 0.7981 | 0.5642 | 0.6611 |
| 0.90 | 3,876 | 0.7227 | 0.7923 | 0.7559 |
| 0.95 | 3,062 | 0.7609 | 0.7719 | 0.7664 |
| 0.97 | 2,307 | 0.7880 | 0.7397 | 0.7631 |
| 0.98 | 1,756 | 0.8044 | 0.7105 | 0.7546 |
| 0.99 | 945 | 0.8072 | 0.6472 | 0.7184 |

EXP-013 is retained as exploratory provenance. Its 0.95 and 0.97 results must not be presented as independently selected operating points.

### EXP-014A: authoritative frozen hybrid evaluation

**Status:** Complete; authoritative hybrid evaluation.

Protocol:

1. Export development-set gold, dictionary, and PubMedBERT predictions.
2. Sweep confidence thresholds using development data only.
3. Select the threshold with maximum development F1; break ties by higher precision.
4. Freeze the selected threshold.
5. Evaluate the frozen configuration once on the untouched BC5CDR test set.

Development-set selection:

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| **0.95** | **2,869** | **0.7660** | **0.7733** | **0.7696** |

Frozen test evaluation:

| System | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dictionary | 7,038 | 5,617 | 1,421 | 4,339 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT epoch 3 | 13,316 | 7,290 | 6,026 | 2,666 | 0.5475 | 0.7322 | 0.6265 |
| Frozen hybrid, threshold 0.95 | 10,100 | 7,685 | 2,415 | 2,271 | 0.7609 | 0.7719 | 0.7664 |

The frozen hybrid improves recall from 0.5642 to 0.7719 relative to the dictionary while reducing precision from 0.7981 to 0.7609. It improves F1 from 0.6611 to 0.7664.

The hybrid is **not promoted** to the production pipeline. EXP-014B must analyze its false positives before a promote, modify, or reject decision.

---

## 6. Result register

### R-001: Historical dictionary NER F1

- **Value:** 0.0966
- **Status:** INVALID
- **Reason:** Compared document-global gold offsets with passage-local predicted offsets.
- **Action:** Do not cite as project performance.

### R-002: One-location dictionary NER F1

- **Value:** 0.6614
- **Precision:** 0.7970
- **Recall:** 0.5653
- **Status:** SUPERSEDED
- **Limitation:** Used the first BioC location only and excluded entity type from matching.
- **Action:** Retain as historical provenance.

### R-003: Linking coverage

- **Value:** 785 linked / 7,038 predictions = 11.15%
- **Status:** PROTOTYPE COVERAGE, NOT LINKING ACCURACY
- **Action:** Do not describe as linking accuracy or correctness.

### R-004: OMOP routing and FHIR conversion

- **Values:** 785 routed / 785 linked = 100%; 785 FHIR resources / 785 OMOP records = 100%
- **Status:** FUNCTION PASS-THROUGH COUNTS
- **Action:** Do not describe as standards compliance or clinical validity.

### R-005: End-to-end survival

- **Value:** 7.9%
- **Status:** INVALID AS A CORRECTNESS METRIC
- **Reason:** Raw count ratio; no gold-to-standardized-concept verification.
- **Action:** Do not cite as end-to-end accuracy.

### R-006: Gate C-2 base-dictionary baseline

- **Value:** F1 0.6611
- **Precision:** 0.7981
- **Recall:** 0.5642
- **Status:** Historical baseline; retained as provenance
- **Date:** 2026-10-10
- **Gold denominator:** 9,965 location-level gold spans
- **Predicted entities:** 7,038
- **Evidence:** `output/evaluation/evaluate_ner_gate_c2_2026-10-10.txt`

### R-007: EXP-008 base-dictionary test evaluation

- **Value:** F1 0.6611
- **Precision:** 0.7981
- **Recall:** 0.5642
- **Status:** CURRENT verified base-dictionary test-set baseline
- **Date:** 2026-10-12
- **Dictionary:** `data/terminology/bc5cdr_dictionary.json`
- **Gold denominator:** 9,956 location-level gold entities
- **Predicted entities:** 7,038
- **True positives:** 5,617
- **False positives:** 1,421
- **False negatives:** 4,339
- **Evidence:** `output/evaluation/exp008_dictionary_bc5cdr_test_location_level.json`

### R-008: EXP-009 word-boundary extraction

- **Value:** F1 0.6893
- **Precision:** 0.8861
- **Recall:** 0.5641
- **Status:** CURRENT extraction strategy used by EXP-010
- **Gold denominator:** 9,956 gold entities
- **Predicted entities:** 6,338
- **True positives:** 5,616
- **False positives:** 722
- **False negatives:** 4,340
- **Evidence:** `docs/experiments/EXP-009-lexical-strategy-upgrade.md`
- **Attribution correction:** Previously misattributed to EXP-004. EXP-004 was the PubMedBERT tiny-overfit preflight.
- **Count correction:** Earlier documentation incorrectly reported 11,476 predictions and 8,821 true positives. The verified EXP-009 record reports 6,338 predictions and 5,616 true positives.

### R-009: EXP-007 PubMedBERT epoch-3 evaluation

- **Value:** F1 0.6265
- **Precision:** 0.5475
- **Recall:** 0.7322
- **Status:** Evaluated alternative; not production extractor
- **Gold denominator:** 9,956 gold entities
- **Predicted entities:** 13,316
- **Evidence:** `output/evaluation/exp007_pubmedbert_bc5cdr_test_epoch3.json`

### R-010: Abbreviation-expanded dictionary

- **Development F1:** 0.6583
- **Development precision:** 0.7390
- **Development recall:** 0.5934
- **Status:** EVALUATED NEGATIVE RESULT
- **Comparison:** Base dictionary achieved F1 0.6812 under the same development policy.
- **Interpretation:** Expansion added 846 predictions, gained 86 true positives, and introduced 760 false positives.
- **Action:** Retain as provenance; do not use as production extractor.

### R-011: EXP-010 harmonization and routing

- **Extracted occurrences:** 6,338
- **Mapped:** 651
- **Unmapped:** 5,687
- **Mapping rate over extracted occurrences:** 10.3%
- **`drug_exposure`:** 371
- **`condition_occurrence`:** 280
- **Not routed:** 5,687
- **Status:** CURRENT
- **Scope limitation:** The low mapping rate reflects the intentionally incomplete 29-concept vocabulary.

### R-012: EXP-011 mapping quality

- **Mapped records:** 651
- **Gold-supported mappings:** 629
- **Unsupported mappings:** 22
- **Mapping precision:** 0.9662
- **Vocabulary-representable gold entities:** 647
- **Vocabulary-representable mapped entities:** 629
- **Vocabulary recall:** 0.9722
- **Status:** CURRENT
- **Evidence:** `output/evaluation/exp011_mapping_quality.json`

### R-013: EXP-012 hybrid extraction

- **Dictionary baseline:** EXP-009 word-boundary dictionary
- **Transformer alternative:** EXP-007 PubMedBERT epoch 3
- **Hybrid rule:** Retain dictionary predictions; add non-overlapping same-type PubMedBERT predictions
- **Hybrid precision:** 0.6328
- **Hybrid recall:** 0.8157
- **Hybrid F1:** 0.7127
- **Status:** COMPLETE; EVALUATED CANDIDATE; NOT PROMOTED
- **Finding:** F1 improved by 0.0516 over the dictionary baseline, but precision fell from 0.7981 to 0.6328.
- **Evidence:** `output/evaluation/exp012_hybrid_extraction.json`

### R-014: EXP-013 confidence-thresholded hybrid

- **Dictionary baseline:** EXP-008 base dictionary
- **Transformer:** EXP-007 PubMedBERT epoch 3
- **Rule:** Add non-overlapping, same-type PubMedBERT predictions above a confidence threshold
- **F1-optimal threshold:** 0.95
- **F1-optimal result:** P 0.7609; R 0.7719; F1 0.7664
- **Precision-preserving threshold:** 0.97
- **Precision-preserving result:** P 0.7880; R 0.7397; F1 0.7631
- **Status:** COMPLETE; EXPLORATORY TEST-SET MODEL SELECTION
- **Decision:** Do not use EXP-013 to select or promote a production operating point.
- **Evidence:** `output/evaluation/exp013_hybrid_confidence_sweep.json`

### R-015: EXP-014A development threshold selection

- **Split:** BC5CDR development set
- **Selection rule:** Maximum development F1; ties broken by higher precision
- **Selected threshold:** 0.95
- **Development result:** P 0.7660; R 0.7733; F1 0.7696
- **Status:** COMPLETE; threshold frozen
- **Evidence:** `output/evaluation/exp014a_development_threshold_sweep.json`

### R-016: EXP-014A frozen test evaluation

- **Split:** BC5CDR test set
- **Frozen threshold:** 0.95
- **Dictionary:** P 0.7981; R 0.5642; F1 0.6611
- **PubMedBERT only:** P 0.5475; R 0.7322; F1 0.6265
- **Frozen hybrid:** P 0.7609; R 0.7719; F1 0.7664
- **Hybrid confusion matrix:** TP 7,685; FP 2,415; FN 2,271
- **Status:** CURRENT AUTHORITATIVE HYBRID RESULT; NOT PROMOTED
- **Evidence:** `output/evaluation/exp014a_frozen_test_evaluation.json`

---

## 7. Approved decisions

### D-001: Location-level gold representation

**Approved:** 2026-10-10  
**Decision:** Use one gold span per BioC `<location>`. Preserve annotation-level text, MeSH ID, and provenance.  
**Scope:** NER evaluation, error decomposition, scispaCy evaluation, and transformer BIO labeling.

### D-002: Type-aware exact matching

**Approved:** 2026-10-10  
**Decision:** A prediction matches gold only when document ID, character span, and entity type all match. Current export and hybrid evaluation use document-level character offsets.  
**Scope:** Primary exact-span metric.

### D-003: Corpus anomalies are retained

**Approved:** 2026-10-10  
**Decision:** Do not modify source BioC XML. Retain, count, and document CE-001 and CE-002.  
**Scope:** All current and future corpus audits.

### D-004: Historical results remain provenance

**Approved:** 2026-10-10  
**Decision:** Do not delete invalid or provisional historical results. Label their validity, limitation, and replacement condition.  
**Scope:** All metric reporting and documentation.

### D-005: Separate threshold selection from final evaluation

**Approved:** 2026-10-13  
**Decision:** Select model configurations and thresholds using development data only. Evaluate a frozen configuration once on the test set.  
**Scope:** All future hybrid, model-selection, and operating-point experiments.

### D-006: Do not promote a hybrid without false-positive analysis

**Approved:** 2026-10-13  
**Decision:** Do not promote a hybrid extractor merely because it has the highest F1. Promote only if EXP-014B shows that its added false positives are understandable, bounded, and unlikely to harm downstream harmonization quality.  
**Scope:** EXP-014A frozen hybrid and future extractor variants.

---

## 8. Documentation reconciliation

| Document claim | Verified reality | Required action |
|---|---|---|
| EXP-004 produced dictionary F1 0.6893 | EXP-004 was the PubMedBERT tiny-overfit preflight | Corrected; result belongs to EXP-009 |
| EXP-009 produced 11,476 predictions and 8,821 true positives | Verified EXP-009 result is 6,338 predictions and 5,616 true positives | Corrected |
| EXP-010 coverage is 10.3% | 10.3% is mapping rate over extracted occurrences | Relabel; do not call it vocabulary coverage |
| EXP-013 threshold 0.95 is a final operating point | Threshold was selected on test data | Reclassify as exploratory; use EXP-014A |
| EXP-014A hybrid F1 0.7664 | Development-selected frozen threshold evaluated once on test set | Current authoritative hybrid result |
| Hybrid is production-ready | No false-positive analysis or deployment validation exists | Do not promote until EXP-014B |

---

## 9. BioC location audit

**Audit date:** 2026-10-10  
**Scope:** All 1,500 documents; 29,271 annotations; 29,424 `<location>` elements across training, development, and test splits.

| Split | Documents | Annotations | Locations | Two-location annotations | Exact full-text location matches | Valid multi-location fragments | Genuine anomalies | Out-of-bounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Training | 500 | 9,570 | 9,643 | 73 | 9,496 | 146 | 1 | 0 |
| Development | 500 | 9,773 | 9,816 | 43 | 9,730 | 85 | 1 | 0 |
| Test | 500 | 9,928 | 9,965 | 37 | 9,891 | 74 | 0 | 0 |
| **Total** | **1,500** | **29,271** | **29,424** | **153** | **29,117** | **305** | **2** | **0** |

### Established findings

- Every multi-location annotation has exactly two locations.
- The original loader read only the first location, losing 153 valid gold spans corpus-wide.
- Passage-local conversion produced zero out-of-bounds locations.
- The earlier 307 “mismatches” were mostly expected fragment behavior: 305 valid fragments plus two genuine anomalies.
- Do not compare an individual location slice with the entire annotation text for multi-location annotations.

### Corpus exceptions

| ID | Split / document | Issue | Policy |
|---|---|---|---|
| CE-001 | Training / `15863244` | Annotation `midline (MD) defects`; location slice is `d midline (MD) defec`, indicating a source offset/length irregularity | Retain as-is; count and document; do not silently alter source XML |
| CE-002 | Development / `6415512` | Annotation `atypical absence seizures`; first location slice is ` atypical absenc`; annotation text is not contiguous in passage | Retain as-is; count and document; do not silently alter source XML |

---

## 10. Release and provenance constraints

Before presenting the repository as a public portfolio showcase:

1. Confirm whether `data/terminology/omop_exercise_vocabulary.json` may be redistributed.
2. Replace assessment-supplied vocabulary with a synthetic fixture or independently sourced, appropriately licensed vocabulary if redistribution is not permitted.
3. Document the source, license, and acquisition instructions for BC5CDR.
4. Review BC5CDR-derived dictionaries for redistribution permissions.
5. Review `.llm-provenance.md`, assessment-specific wording, and session notes for confidential material.
6. Do not commit generated files under `output/`.

---

## 11. Next gated actions

1. Create the EXP-014A experiment record.
2. Update `README.md` to make EXP-014A the authoritative hybrid result and EXP-013 exploratory.
3. Run EXP-014B: analyze false positives introduced by the frozen 0.95 hybrid.
4. Decide whether to promote, modify, or reject the frozen hybrid based on EXP-014B.
5. Correct dashboard metric labels and separate mapping rate, vocabulary coverage, mapping precision, and end-to-end yield.
6. Complete the terminology and assessment-artifact redistribution audit.
7. Add a clean setup and one-command reproduction path.
8. Add per-mention gold-to-standardized-concept evaluation before making end-to-end correctness claims.