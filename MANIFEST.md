# MANIFEST — Clinical Harmonization Project

**Version:** 0.3.0
**Created:** 2026-10-07
**Last updated:** 2026-10-08

---

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
| S14 | `src/evaluation/dashboard.py` | Results dashboard | Not created |

---

## Experiments

| ID | Experiment | Research Question | Status |
|----|------------|-------------------|--------|
| E01 | Dictionary baseline NER | How accurately can dictionary methods extract chemicals/diseases? | ✅ Complete (F1 = 0.661) |
| E02 | Transformer NER | Does fine-tuned biomedical transformer improve extraction? | Not started |
| E03 | Vocabulary coverage | How much of gold-standard entity set can available terminology represent? | Not started |
| E04 | Matching strategies | How do exact, lexical, fuzzy, semantic retrieval compare? | Not started |
| E05 | Forced vs abstaining | What is the cost of forcing every entity to map? | Not started |
| E06 | Domain constraints | How many errors does domain filtering prevent? | Not started |

---

## Results: Dictionary Baseline NER

### Correction notice (2026-10-08)

**Previous results (F1 = 0.097) were INVALID** due to offset coordinate mismatch:
- Gold annotations used document-global offsets
- Predictions used passage-local offsets
- Evaluation compared them directly, causing systematic false negatives

**Corrected results** use passage-local offsets for both gold and predictions.

---

### Overall Performance (Exact Span Match, LOCAL OFFSETS)

**Date:** 2026-10-08 (corrected)  
**Test set:** BC5CDR Test Set (500 abstracts, 9,928 gold entities)

| Metric | Value |
|--------|-------|
| **Precision** | **0.7970** |
| **Recall** | **0.5653** |
| **F1** | **0.6614** |
| True positives | 5,609 |
| False positives | 1,429 |
| False negatives | 4,313 |

### By Entity Type

| Type | Precision | Recall | F1 | TP | FP | FN |
|------|-----------|--------|-----|----|----|----|
| Chemicals | 0.8100 | 0.5382 | 0.6467 | 2,903 | 681 | 2,491 |
| Diseases | 0.7834 | 0.5976 | 0.6780 | 2,706 | 748 | 1,822 |

### Key Findings

1. **Dictionary baseline is strong** — F1 = 0.66 when evaluated correctly (not 0.097)
2. **High precision (0.80)** — When dictionary matches, it's usually correct
3. **Moderate recall (0.57)** — Limited by vocabulary coverage (unseen entities in test set)
4. **False positives** — Often real entities ("histamine", "steroid") not annotated in gold standard for specific documents
5. **False negatives** — Unseen entities ("Famotidine", "IDM"), abbreviations, and entities with low training frequency

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
| Data downloaded | ✅ | BC5CDR complete |
| Environment set up | ✅ | Python venv, scispacy installed |
| Loader offset fix | ✅ | Passage-local offsets verified |
| Dictionary baseline | ✅ | F1 = 0.661 (corrected from 0.097) |
| Transformer NER | ❌ | Not started |
| Golden tests created | ⚠️ | Placeholder tests only |
| ADRs written | ⚠️ | ADR-001 only |
