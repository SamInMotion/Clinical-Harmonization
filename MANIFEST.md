# MANIFEST — Clinical Harmonization Project

**Version:** 0.4.1  
**Created:** 2026-10-07  
**Last updated:** 2026-10-13  

---

## Current-state correction — 2026-10-13

The active implementation is EXP-010, evaluated by EXP-011.

- Production extractor: dictionary word-boundary strategy from EXP-009.
- Verified base-dictionary test baseline: EXP-008.
- Active harmonization vocabulary: 29 concepts (17 drugs, 12 conditions).
- Active pipeline output: 6,338 extracted occurrences; 651 mapped; 5,687 unmapped.
- EXP-009 word-boundary extraction: precision 0.8861, recall 0.5641, F1 0.6893.
- EXP-008 base-dictionary extraction: precision 0.7981, recall 0.5642, F1 0.6611.
- Current mapping result: precision 0.9662; vocabulary recall 0.9722.
- Dashboard: implemented at `src/pipeline/build_dashboard.py`; generated HTML remains uncommitted.

**Attribution correction:** EXP-004 was the PubMedBERT tiny-overfit preflight. It did not produce a dictionary extraction result. Earlier documentation incorrectly attributed the EXP-009 word-boundary result to EXP-004.

Earlier E01–E06 entries and historical results remain provenance. They are not deleted.

---

## Data Sources

| ID | Source | Description | License | Location | Status |
|----|--------|-------------|---------|----------|--------|
| D01 | BioCreative V CDR | BC5CDR corpus (1,500 PubMed abstracts, chemical/disease annotations) | CC-BY 3.0 | `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/` | Downloaded |
| D02 | SNOMED-CT | Clinical terminology | IHTSDO | `data/terminology/snomed/` | Not used by EXP-010 |
| D03 | ICD-10-CM | Diagnosis codes | CDC/NCHS | `data/terminology/icd10cm/` | Not used by EXP-010 |
| D04 | RxNorm | Drug terminology | NLM | `data/terminology/rxnorm/` | Not used by EXP-010 |
| D05 | LOINC | Laboratory terminology | Regenstrief | `data/terminology/loinc/` | Not used by EXP-010 |
| D06 | Synthetic FHIR | Synthetic patient records | Generated | `data/synthetic_fhir/` | Not created |
| D07 | Base BC5CDR dictionary | Dictionary built from BC5CDR training annotations | Project artifact | `data/terminology/bc5cdr_dictionary.json` | Implemented |
| D08 | Abbreviation-expanded dictionary | Base dictionary plus training-derived acronym aliases | Project artifact | `data/terminology/bc5cdr_dictionary_abbreviation_expanded.json` | Evaluated negative result |
| D09 | OMOP exercise vocabulary | 29-concept controlled vocabulary | Project artifact | `data/terminology/omop_exercise_vocabulary.json` | Implemented |

---

## Documentation

| ID | Document | Purpose | Status |
|----|----------|---------|--------|
| DOC01 | `docs/PROJECT_CLOSEOUT.md` | Project closeout and claims boundary | Created |
| DOC02 | `docs/PROJECT_STATE.md` | Canonical current-state register | Updated |
| DOC03 | `docs/experiments/` | Experiment records and provenance | Updated |
| DOC04 | `docs/sessions/` | Session logs | Updated |
| DOC05 | `docs/decisions/` | Architecture decision records | Partial |
| DOC06 | `docs/architecture.md` | Pipeline architecture and data flow | Not created |
| DOC07 | `docs/evaluation_protocol.md` | Evaluation metrics and error taxonomy | Requires reconciliation |
| DOC08 | `docs/terminology_versions.md` | Terminology releases used | Not created |

---

## Scripts

| ID | Script | Purpose | Status |
|----|--------|---------|--------|
| S01 | `src/ner/load_bc5cdr.py` | Load BC5CDR corpus from BioC XML | Complete; preserves all annotation locations |
| S02 | `src/ner/dictionary_baseline.py` | Dictionary construction and span extraction | Complete |
| S03 | `src/ner/abbreviation_expansion.py` | Build acronym aliases from training data | Complete; evaluated negative result |
| S04 | `src/ner/evaluate_dictionary_exp008.py` | Base-dictionary test-set evaluation | Complete |
| S05 | `src/ner/evaluate_development_comparison.py` | Compare base and abbreviation-expanded dictionaries | Complete |
| S06 | `src/ner/transformer_ner.py` | Fine-tune PubMedBERT for BC5CDR NER | Complete for evaluated training run |
| S07 | `src/ner/evaluate_pubmedbert_exp007.py` | Evaluate PubMedBERT checkpoint | Complete for epoch-3 checkpoint |
| S08 | `src/ner/analyze_false_negatives.py` | Analyze extractor false negatives | Complete |
| S09 | `src/ner/analyze_partial_overlaps.py` | Analyze partial span overlaps | Complete |
| S10 | `src/pipeline/run_pipeline.py` | End-to-end EXP-010 extraction, harmonization, and routing | Complete |
| S11 | `src/pipeline/build_dashboard.py` | Static HTML dashboard from harmonized records | Complete |
| S12 | `src/evaluation/evaluate_mapping_quality.py` | EXP-011 mapping-quality evaluation | Complete |
| S13 | `src/evaluation/diagnose_unsupported_mappings.py` | Diagnose unsupported mappings | Complete |
| S14 | `src/evaluation/inspect_unsupported_mappings.py` | Inspect unsupported mapping records | Complete |
| S15 | `src/pipeline/compare_exp009_exp010.py` | Compare EXP-009 and EXP-010 outputs | Complete |
| S16 | `src/evaluation/error_decomposition.py` | Earlier error-decomposition workflow | Superseded for current reporting |
| S17 | `src/evaluation/evaluate_hybrid_extraction.py` | EXP-012 hybrid extraction evaluation | Created; requires prediction-export integration |

---

## Experiments

| ID | Experiment | Research question | Status |
|----|------------|-------------------|--------|
| E01 | Dictionary baseline NER | How accurately can dictionary methods extract chemicals/diseases? | Superseded by EXP-008 and EXP-009 |
| E02 | Transformer NER | Does a fine-tuned biomedical transformer improve extraction? | EXP-007 completed for epoch-3 checkpoint |
| E03 | Vocabulary coverage | How much of the gold entity set can a controlled vocabulary represent? | EXP-010/011 completed for 29-concept vocabulary |
| E04 | Matching strategies | How do exact, lexical, fuzzy, and semantic retrieval compare? | Partially addressed by EXP-009 lexical strategies |
| E05 | Forced vs abstaining | What is the cost of forcing every entity to map? | Partially addressed; EXP-010 uses abstention |
| E06 | Domain constraints | How many errors does domain filtering prevent? | Partially addressed; EXP-010 uses domain-safe routing |
| EXP-004 | PubMedBERT tiny-overfit preflight | Can the transformer training path overfit a tiny controlled sample? | Complete |
| EXP-005 | PubMedBERT training feasibility | Is transformer fine-tuning feasible in the available environment? | Complete |
| EXP-006 | PubMedBERT fine-tuning | Can PubMedBERT be fine-tuned on BC5CDR? | Complete |
| EXP-007 | PubMedBERT evaluation | What is span-level transformer performance on the BC5CDR test set? | Complete for epoch-3 checkpoint |
| EXP-008 | Base-dictionary evaluation | What is the location-level performance of the base dictionary? | Complete |
| EXP-009 | Lexical strategy comparison | Which lexical matching strategy best supports extraction? | Complete |
| EXP-010 | Controlled harmonization and routing | How many mentions map, route, or remain unmapped? | Complete |
| EXP-011 | Mapping-quality evaluation | Are produced mappings supported by gold spans, types, and controlled variants? | Complete |
| EXP-012 | Hybrid extraction evaluation | Does adding non-overlapping transformer predictions improve the dictionary extractor? | In progress |

---

## Results: Biomedical Entity Extraction

### Correction notice — 2026-10-08

The original dictionary NER result of **F1 = 0.0966 was INVALID**.

- Gold annotations used document-global offsets.
- Predictions used passage-local offsets.
- The evaluator compared these coordinate systems directly, producing systematic false negatives.

The loader and evaluation logic were corrected so that gold annotations and predictions use consistent passage-local offsets. The invalid result is retained only as provenance.

---

### Attribution correction — 2026-10-13

EXP-004 was the **PubMedBERT tiny-overfit preflight**. It did not produce a dictionary extraction result.

The extraction metrics below—

- precision 0.8861;
- recall 0.5641;
- F1 0.6893—

belong to **EXP-009’s word-boundary lexical strategy**, not EXP-004.

Earlier documentation incorrectly labeled this as an EXP-004 result. The error is retained here as provenance and corrected throughout the repository documentation.

---

### Verified base-dictionary baseline: EXP-008

**Status:** Verified dictionary baseline  
**Date:** 2026-10-12  
**Dictionary:** `data/terminology/bc5cdr_dictionary.json`  
**Test set:** BC5CDR test set; 500 documents  
**Gold denominator:** 9,956 location-level gold entities  
**Matching:** Exact document-level character span and entity type  
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

---

### Current word-boundary result: EXP-009

**Status:** Current extraction strategy used by EXP-010  
**Strategy:** Dictionary word-boundary matching  
**Gold denominator:** 9,956 gold entities  
**Extracted occurrences:** 6,338  
**Unique mentions:** 5,616  

| Metric | Value |
|---|---:|
| Precision | 0.8861 |
| Recall | 0.5641 |
| F1 | 0.6893 |
| True positives | 8,821 |

The precise interpretation of occurrence and unique-mention counts must follow the original EXP-009 experiment record.

---

### Alternative extractor: EXP-007 PubMedBERT

**Status:** Evaluated alternative; not the production extractor  
**Model:** PubMedBERT, epoch-3 checkpoint  
**Test set:** BC5CDR test set  
**Gold denominator:** 9,956 gold entities  
**Predicted entities:** 13,316  

| Extractor | Precision | Recall | F1 |
|---|---:|---:|---:|
| EXP-009 word-boundary dictionary | 0.8861 | 0.5641 | 0.6893 |
| PubMedBERT epoch 3 | 0.5475 | 0.7322 | 0.6265 |

PubMedBERT improved recall but reduced precision. The dictionary word-boundary extractor remains the production extractor because it is deterministic, auditable, and better aligned with controlled-vocabulary mapping.

---

### Abbreviation expansion: evaluated negative result

**Status:** Evaluated negative result  
**Dataset:** BC5CDR development set  
**Gold spans:** 9,816  
**Evaluation policy:** Gate C-2 location-level, type-aware exact-span matching

| Metric | Base dictionary | Expanded dictionary | Difference |
|---|---:|---:|---:|
| Precision | 0.8158 | 0.7390 | -0.0768 |
| Recall | 0.5847 | 0.5934 | +0.0088 |
| F1 | 0.6812 | 0.6583 | -0.0229 |
| True positives | 5,728 | 5,814 | +86 |
| False positives | 1,293 | 2,053 | +760 |
| False negatives | 4,069 | 3,983 | -86 |
| Predicted entities | 7,021 | 7,867 | +846 |

Abbreviation expansion is retained as provenance and an evaluated negative result. It is not used as the production extractor.

---

## Harmonization and mapping results

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

### EXP-011: mapping quality

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

## Historical results

### One-location representation

**Status:** SUPERSEDED  
**Date:** 2026-10-08  
**Gold denominator:** 9,928 annotation records  
**Matching:** Exact span; document, passage type, offset, and length; entity type excluded  

| Metric | Value |
|---|---:|
| Precision | 0.7970 |
| Recall | 0.5653 |
| F1 | 0.6614 |

### Gate C-2 base-dictionary baseline

**Status:** Historical baseline; retained as provenance  
**Date:** 2026-10-10  
**Gold denominator:** 9,965 location-level gold spans  
**Predicted entities:** 7,038  

| Metric | Value |
|---|---:|
| Precision | 0.7981 |
| Recall | 0.5642 |
| F1 | 0.6611 |

### End-to-end survival

**Status:** INVALID AS A CORRECTNESS METRIC  
**Value:** 7.9%  
**Reason:** Raw count ratio with no gold-to-standardized-concept verification.

---

## Provenance Notes

- **P01:** BC5CDR downloaded from Hugging Face (`bigbio/bc5cdr`) on 2026-10-07.
- **P02:** Base dictionary built from BC5CDR training-set annotations.
- **P03:** Abbreviation aliases derived only from training-set text and annotations.
- **P04:** Loader updated to preserve all BioC annotation locations and use passage-local offsets.
- **P05:** EXP-008 evaluates the base dictionary on 9,956 test-set gold entities.
- **P06:** EXP-009 evaluates lexical strategies; its word-boundary strategy is used by EXP-010.
- **P07:** Abbreviation expansion reduced development-set F1 and is retained as a negative result.
- **P08:** No restricted clinical data will be committed to this repository.
- **P09:** EXP-004 was a PubMedBERT tiny-overfit preflight, not a dictionary evaluation.

---

## Verification Status

| Check | Status | Notes |
|-------|--------|-------|
| BC5CDR data downloaded | ✅ Complete | Corpus available at `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/`. |
| Environment set up | ✅ Complete | `.venv/` exists; use `.venv/Scripts/python.exe` until shell activation is verified. |
| BioC loader location handling | ✅ Complete | All annotation locations are preserved; passage-local conversion verified. |
| Base-dictionary extraction | ✅ Complete | EXP-008: precision 0.7981, recall 0.5642, F1 0.6611. |
| Word-boundary extraction | ✅ Complete | EXP-009: precision 0.8861, recall 0.5641, F1 0.6893. |
| Abbreviation expansion | ⚠️ Negative result | Improved recall slightly but reduced precision and F1 on development data. |
| Transformer NER | ⚠️ Partially complete | EXP-007 evaluated PubMedBERT epoch 3; broader training and tokenizer-alignment validation remain separate work. |
| Controlled harmonization | ✅ Complete | EXP-010: 6,338 occurrences; 651 mapped; 5,687 unmapped. |
| Domain-safe routing | ✅ Complete | 371 `drug_exposure`; 280 `condition_occurrence`; Observation-domain concepts not routed. |
| Mapping-quality evaluation | ✅ Complete | EXP-011: mapping precision 0.9662; vocabulary recall 0.9722. |
| Dashboard | ✅ Implemented | `src/pipeline/build_dashboard.py`; generated HTML remains uncommitted. |
| Golden tests | ⚠️ Limited | Focused Gate C regression tests exist; comprehensive end-to-end coverage remains limited. |
| Architecture decision records | ⚠️ Partial | Gate C/D decisions are recorded in the state register; standalone ADRs remain incomplete. |
| OMOP CDM validation | ❌ Not performed | Routing is domain-safe but does not establish OMOP CDM validity. |
| FHIR conformance validation | ❌ Not performed | Existing FHIR-shaped output is not conformance-tested. |
| End-to-end correctness evaluation | ❌ Not performed | No validated gold-to-correct-standardized-concept metric exists. |