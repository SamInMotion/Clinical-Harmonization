# MANIFEST — Clinical Harmonization Project

**Version:** 0.3.0
**Created:** 2026-10-07
**Last updated:** 2026-10-08

---
## Current-state correction — 2026-10-13

The active implementation is now EXP-010, evaluated by EXP-011.

- Production extractor: curated dictionary word-boundary extractor.
- Active harmonization vocabulary: 29 concepts (17 drugs, 12 conditions).
- Active pipeline output: 6,338 extracted occurrences; 651 mapped; 5,687 unmapped.
- Current extraction result: precision 0.8861, recall 0.5641, F1 0.6893 on 9,956 EXP-004 gold entities.
- Current mapping result: precision 0.9662; vocabulary recall 0.9722.
- Dashboard: implemented at `src/pipeline/build_dashboard.py`; generated HTML remains uncommitted.

Earlier E01–E06 entries and R-001 through R-006 remain historical provenance. They are not replaced by deletion; their status is recorded below.

## Data Sources

| ID | Source | Description | License | Location | Status |
|----|--------|-------------|---------|----------|--------|
| D01 | BioCreative V CDR | BC5CDR corpus (1,500 PubMed abstracts, chemical/disease annotations) | CC-BY 3.0 | `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/` | Downloaded |
| D02 | SNOMED-CT | Clinical terminology (version to be recorded) | IHTSDO | `data/terminology/snomed/` | Pending |
| D03 | ICD-10-CM | Diagnosis codes (version to be recorded) | CDC/NCHS | `data/terminology/icd10cm/` | Pending |
| D04 | RxNorm | Drug terminology | NLM | `data/terminology/rxnorm/` | Pending |
| D05 | LOINC | Laboratory terminology | Regenstrief | `data/terminology/loinc/` | Pending |
| D06 | Synthetic FHIR | Synthetic patient records | Generated | `data/synthetic_fhir/` | Not created |

---

## Documentation

| ID | Document | Purpose | Status |
|----|----------|---------|--------|
| DOC01 | `docs/architecture.md` | Pipeline architecture and data flow | Not created |
| DOC02 | `docs/evaluation_protocol.md` | Evaluation metrics and error taxonomy | Not created |
| DOC03 | `docs/terminology_versions.md` | Terminology releases used | Not created |
| DOC04 | `docs/sessions/` | Session logs (per Vibe Code protocol) | Updated |
| DOC05 | `docs/decisions/` | Architecture decision records (ADRs) | Not created |

---

## Scripts

| ID | Script | Purpose | Status |
|----|--------|---------|--------|
| S01 | `src/ner/load_bc5cdr.py` | Load BC5CDR corpus from BioC XML | ✅ Complete (fixed offsets) |
| S02 | `src/ner/dictionary_baseline.py` | Dictionary/rule-based NER baseline | ✅ Complete |
| S03 | `src/ner/evaluate_ner.py` | NER evaluation with span-level metrics | ✅ Complete (fixed offsets) |
| S04 | `src/ner/debug_errors.py` | Debug false positives/negatives | ✅ Complete |
| S05 | `src/ner/transformer_ner.py` | Fine-tuned biomedical transformer NER | Not created |
| S06 | `src/linking/candidate_retrieval.py` | Candidate terminology retrieval | Not created |
| S07 | `src/linking/reranking.py` | Candidate reranking | Not created |
| S08 | `src/linking/evaluate_linking.py` | Linking evaluation | Not created |
| S09 | `src/mapping/omop_routing.py` | OMOP domain routing | Not created |
| S10 | `src/mapping/fhir_transform.py` | FHIR→OMOP transformation | Not created |
| S11 | `src/mapping/loinc_mapping.py` | LOINC laboratory mapping | Not created |
| S12 | `src/phi/deidentification.py` | PHI detection module | Not created |
| S13 | `src/evaluation/error_decomposition.py` | Error decomposition pipeline | Not created |
| S14 | `src/pipeline/build_dashboard.py` | Static HTML dashboard from harmonized records | Complete |
| S15 | `src/pipeline/run_pipeline.py` | End-to-end EXP-010 extraction, harmonization, and routing | Complete |
| S16 | `src/evaluation/evaluate_mapping_quality.py` | EXP-011 mapping-quality evaluation | Complete |

---

## Experiments

| E01 | Dictionary baseline NER | How accurately can dictionary methods extract chemicals/diseases? | SUPERSEDED by EXP-004 for current reporting |
| E02 | Transformer NER | Does fine-tuned biomedical transformer improve extraction? | EXP-005 completed for epoch-3 checkpoint; production extractor remains dictionary |
| E03 | Vocabulary coverage | How much of gold-standard entity set can available terminology represent? | EXP-010/011 completed for 29-concept vocabulary |
| E04 | Matching strategies | How do exact, lexical, fuzzy, semantic retrieval compare? | Not started |
| E05 | Forced vs abstaining | What is the cost of forcing every entity to map? | Partially addressed: EXP-010 uses abstention; no forced-mapping ablation |
| E06 | Domain constraints | How many errors does domain filtering prevent? | Partially addressed: EXP-010 uses domain-safe routing; no counterfactual ablation |
| EXP-004 | Current dictionary extractor evaluation | What is the span-level precision, recall, and F1 of the active extractor? | Complete |
| EXP-005 | PubMedBERT alternative extractor | Does a fine-tuned transformer improve recall relative to the dictionary extractor? | Complete for epoch-3 checkpoint |
| EXP-010 | Controlled harmonization and routing | How many extracted mentions map, route, or remain unmapped under a 29-concept vocabulary? | Complete |
| EXP-011 | Mapping-quality evaluation | Are produced mappings supported by gold spans, types, and controlled concept variants? | Complete |

---

## Results: Biomedical Entity Extraction

### Correction notice — 2026-10-08

The original dictionary NER result of **F1 = 0.0966 was INVALID**.

- Gold annotations used document-global offsets.
- Predictions used passage-local offsets.
- The evaluator compared these coordinate systems directly, producing systematic false negatives.

The loader and evaluation logic were corrected so that gold annotations and predictions use consistent passage-local offsets. The invalid result is retained only as provenance and must not be cited as project performance.

---

### Historical result: one-location representation

**Status:** SUPERSEDED  
**Date:** 2026-10-08  
**Test set:** BC5CDR test set; 500 abstracts  
**Gold denominator:** 9,928 annotation records  
**Matching:** Exact span; document, passage type, offset, and length; entity type excluded  
**Known limitation:** Used only the first BioC `<location>` per annotation and excluded entity type from the match key.

| Metric | Value |
|---|---:|
| Precision | 0.7970 |
| Recall | 0.5653 |
| F1 | 0.6614 |
| True positives | 5,609 |
| False positives | 1,429 |
| False negatives | 4,313 |

| Entity type | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Chemicals | 0.8100 | 0.5382 | 0.6467 | 2,903 | 681 | 2,491 |
| Diseases | 0.7834 | 0.5976 | 0.6780 | 2,706 | 748 | 1,822 |

This result corrected the original offset error but was later superseded by location-level, type-aware evaluation.

---

### Historical result: Gate C-2 dictionary baseline

**Status:** SUPERSEDED for current reporting; retained as historical provenance  
**Date:** 2026-10-10  
**Test set:** BC5CDR test set; 500 documents  
**Gold denominator:** 9,965 location-level gold spans  
**Matching:** Exact match on document ID, passage type, passage-local offset, location length, and entity type  
**Predicted entities:** 7,038

| Metric | Value |
|---|---:|
| Precision | 0.7981 |
| Recall | 0.5642 |
| F1 | 0.6611 |
| True positives | 5,617 |
| False positives | 1,421 |
| False negatives | 4,339 |

| Entity type | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Chemicals | 0.8103 | 0.5380 | 0.6466 | 2,904 | 680 | 2,494 |
| Diseases | 0.7855 | 0.5952 | 0.6772 | 2,713 | 741 | 1,845 |

This was the Gate C-2 corrected baseline. It is not directly comparable with EXP-004 because EXP-004 uses the later active extractor configuration and reports 9,956 gold entities rather than 9,965 location-level gold spans. The denominator difference requires explicit reconciliation before cross-experiment comparison.

---

### Current result: EXP-004 active dictionary extractor

**Status:** CURRENT for the active EXP-010 pipeline  
**Date:** 2026-10-12  
**Extractor:** Curated dictionary word-boundary extractor  
**Test set:** BC5CDR test set  
**Gold denominator:** 9,956 EXP-004 gold entities  
**Matching:** Exact document-level character span and entity type  
**Predicted entities:** 11,476

| Metric | Value |
|---|---:|
| Precision | 0.8861 |
| Recall | 0.5641 |
| F1 | 0.6893 |
| True positives | 8,821 |
| False positives | 2,655 |
| False negatives | 1,135 |

### Current result: EXP-005 PubMedBERT alternative

**Status:** Evaluated alternative; not the production extractor  
**Model:** PubMedBERT, epoch 3 checkpoint  
**Test set:** BC5CDR test set  

| Extractor | Precision | Recall | F1 |
|---|---:|---:|---:|
| Active dictionary extractor | 0.8861 | 0.5641 | 0.6893 |
| PubMedBERT epoch 3 | 0.5475 | 0.7322 | 0.6265 |

PubMedBERT improved recall but reduced precision. The dictionary extractor remains the production extractor because it is deterministic, auditable, and better aligned with the controlled-vocabulary harmonization stage.

---

### Key findings

1. **The active dictionary extractor is high-precision.** Under EXP-004, it achieved precision 0.8861 and F1 0.6893.
2. **Recall remains the main extraction limitation.** The extractor identifies 56.41% of EXP-004 gold entities, reflecting the deliberately limited dictionary rather than a claim of comprehensive clinical NER coverage.
3. **The transformer alternative trades precision for recall.** PubMedBERT reached 73.22% recall but only 54.75% precision.
4. **Earlier low results were evaluation errors, not extractor failures.** The original F1 of 0.0966 resulted from incompatible offset coordinate systems.
5. **Historical metrics must not be silently replaced.** The 0.6614 and 0.6611 results remain recorded as provenance for the one-location and Gate C-2 evaluation policies respectively.
6. **Cross-experiment comparison requires denominator reconciliation.** The 9,928, 9,965, and 9,956 gold denominators reflect different evaluation representations and policies.

### Next Steps

- Fine-tune biomedical transformer (PubMedBERT/BioBERT) for NER
- Target: F1 = 0.85+ (transformer should generalize to unseen entities)
- Compare transformer performance against corrected dictionary baseline (F1 = 0.661)

---

## Provenance Notes

- **P01:** BC5CDR downloaded from Hugging Face (`bigbio/bc5cdr`) on 2026-10-07
- **P02:** Dictionary built from BC5CDR Training Set (500 abstracts, 2,328 unique entity forms after filtering)
- **P03:** Evaluation on BC5CDR Test Set (500 abstracts, 9,928 gold entities)
- **P04:** **CRITICAL FIX (2026-10-08):** Loader updated to use passage-local offsets; previous results (F1 = 0.097) were invalid due to coordinate mismatch
- **P05:** Corrected baseline F1 = 0.6614 (precision 0.797, recall 0.565)
- **P06:** Terminology versions to be recorded in `docs/terminology_versions.md` before first mapping experiment
- **P07:** No restricted clinical data will be committed to this repository

---

## Verification Status

| Check | Status | Notes |
|-------|--------|-------|
| BC5CDR data downloaded | ✅ Complete | Corpus available at `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/`. |
| Environment set up | ✅ Complete | `.venv/` exists; scispaCy and core dependencies installed. Shell `python` may resolve to the global interpreter, so use `.venv/Scripts/python.exe` until activation is verified. |
| BioC loader location handling | ✅ Complete | All annotation locations are preserved; passage-local conversion verified. |
| Historical dictionary baseline | ⚠️ Superseded | F1 0.6611 under Gate C-2 location-level, type-aware evaluation; retained as historical provenance. |
| Current dictionary extractor | ✅ Complete | EXP-004: precision 0.8861, recall 0.5641, F1 0.6893 on 9,956 gold entities. |
| Transformer NER | ⚠️ Partially complete | EXP-005 evaluated a PubMedBERT epoch-3 checkpoint: precision 0.5475, recall 0.7322, F1 0.6265. Not the production extractor; broader training and tokenizer-alignment validation remain separate work. |
| Controlled harmonization | ✅ Complete | EXP-010: 6,338 occurrences; 651 mapped; 5,687 unmapped; 10.3% coverage under the 29-concept vocabulary. |
| Domain-safe routing | ✅ Complete | 371 `drug_exposure`; 280 `condition_occurrence`; Observation-domain concepts are not routed. |
| Mapping-quality evaluation | ✅ Complete | EXP-011: mapping precision 0.9662; vocabulary recall 0.9722. |
| Dashboard | ✅ Implemented | `src/pipeline/build_dashboard.py` generates a static HTML dashboard; generated output remains uncommitted. |
| Golden tests | ⚠️ Limited | Focused regression tests exist for Gate C loader, evaluation, and BIO-labeling behavior. The suite is not yet comprehensive end-to-end regression coverage. |
| Architecture decision records | ⚠️ Partial | ADR-001 exists; Gate C decisions D-001 to D-004 are recorded in the project state register but should be promoted to standalone ADRs. |
| OMOP CDM validation | ❌ Not performed | Current routing is domain-safe but does not establish OMOP CDM validity. |
| FHIR conformance validation | ❌ Not performed | Existing FHIR-shaped output is not conformance-tested. |
| End-to-end correctness evaluation | ❌ Not performed | No validated gold-to-correct-standardized-concept end-to-end metric exists. |
