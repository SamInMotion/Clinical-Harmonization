# MANIFEST — Clinical Harmonization Project

**Version:** 0.2.0
**Created:** 2026-10-07
**Last updated:** 2026-10-07

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
| DOC04 | `docs/sessions/` | Session logs (per Vibe Code protocol) | Not created |
| DOC05 | `docs/decisions/` | Architecture decision records (ADRs) | Not created |

---

## Scripts

| ID | Script | Purpose | Status |
|----|--------|---------|--------|
| S01 | `src/ner/load_bc5cdr.py` | Load BC5CDR corpus from BioC XML | ✅ Complete |
| S02 | `src/ner/dictionary_baseline.py` | Dictionary/rule-based NER baseline | ✅ Complete |
| S03 | `src/ner/evaluate_ner.py` | NER evaluation with span-level metrics | ✅ Complete |
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
| E01 | Dictionary baseline NER | How accurately can dictionary methods extract chemicals/diseases? | ✅ Complete (F1 = 0.097) |
| E02 | Transformer NER | Does fine-tuned biomedical transformer improve extraction? | Not started |
| E03 | Vocabulary coverage | How much of gold-standard entity set can available terminology represent? | Not started |
| E04 | Matching strategies | How do exact, lexical, fuzzy, semantic retrieval compare? | Not started |
| E05 | Forced vs abstaining | What is the cost of forcing every entity to map? | Not started |
| E06 | Domain constraints | How many errors does domain filtering prevent? | Not started |

---

## Results: Dictionary Baseline NER

**Date:** 2026-10-07
**Test set:** BC5CDR Test Set (500 abstracts, 9,928 gold entities)

### Overall Performance (Exact Span Match)

| Metric | Value |
|--------|-------|
| Precision | 0.1164 |
| Recall | 0.0825 |
| F1 | 0.0966 |
| True positives | 819 |
| False positives | 6,219 |
| False negatives | 9,103 |

### By Entity Type

| Type | Precision | Recall | F1 | TP | FP | FN |
|------|-----------|--------|-----|----|----|----|
| Chemicals | 0.1161 | 0.0771 | 0.0927 | 416 | 3,168 | 4,978 |
| Diseases | 0.1161 | 0.0886 | 0.1005 | 401 | 3,053 | 4,127 |

### Key Findings

1. **Vocabulary coverage limit** — Dictionary only contains entities from training set; new entities in test set (e.g., "Famotidine") are false negatives
2. **Context blindness** — Dictionary matches entities everywhere they appear, but BC5CDR only annotates entities relevant to the paper's main findings
3. **Short entity filtering** — Increasing min_length from 3 to 4 and filtering common words improved precision from 0.065 to 0.116 (+79%)
4. **Fundamental limitation** — Dictionary approach cannot generalize to unseen entities; transformer NER needed for contextual understanding

### Next Steps

- Fine-tune biomedical transformer (PubMedBERT/BioBERT) for NER
- Compare transformer performance against dictionary baseline
- Analyze error patterns: which entities does transformer capture that dictionary misses?

---

## Provenance Notes

- **P01:** BC5CDR downloaded from Hugging Face (`bigbio/bc5cdr`) on 2026-10-07
- **P02:** Dictionary built from BC5CDR Training Set (500 abstracts, 2,328 unique entity forms after filtering)
- **P03:** Evaluation on BC5CDR Test Set (500 abstracts, 9,928 gold entities)
- **P04:** Terminology versions to be recorded in `docs/terminology_versions.md` before first mapping experiment
- **P05:** No restricted clinical data will be committed to this repository

---

## Verification Status

| Check | Status | Notes |
|-------|--------|-------|
| Data downloaded | ✅ | BC5CDR complete |
| Environment set up | ✅ | Python venv, scispacy installed |
| Dictionary baseline | ✅ | F1 = 0.097 on test set |
| Transformer NER | ❌ | Not started |
| Golden tests created | ⚠️ | Placeholder tests only |
| ADRs written | ⚠️ | ADR-001 only |
