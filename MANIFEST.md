# MANIFEST — Clinical Harmonization Project

**Version:** 0.1.0
**Created:** 2026-10-07
**Last updated:** 2026-10-07

---

## Data Sources

| ID | Source | Description | License | Location | Status |
|----|--------|-------------|---------|----------|--------|
| D01 | BioCreative V CDR | BC5CDR corpus (1,500 PubMed abstracts, chemical/disease annotations) | CC-BY 3.0 | `data/raw/bc5cdr/` | Downloaded |
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
| S01 | `src/ner/dictionary_baseline.py` | Dictionary/rule-based NER baseline | Not created |
| S02 | `src/ner/transformer_ner.py` | Fine-tuned biomedical transformer NER | Not created |
| S03 | `src/ner/evaluate_ner.py` | NER evaluation with span-level metrics | Not created |
| S04 | `src/linking/candidate_retrieval.py` | Candidate terminology retrieval | Not created |
| S05 | `src/linking/reranking.py` | Candidate reranking | Not created |
| S06 | `src/linking/evaluate_linking.py` | Linking evaluation | Not created |
| S07 | `src/mapping/omop_routing.py` | OMOP domain routing | Not created |
| S08 | `src/mapping/fhir_transform.py` | FHIR→OMOP transformation | Not created |
| S09 | `src/mapping/loinc_mapping.py` | LOINC laboratory mapping | Not created |
| S10 | `src/phi/deidentification.py` | PHI detection module | Not created |
| S11 | `src/evaluation/error_decomposition.py` | Error decomposition pipeline | Not created |
| S12 | `src/evaluation/dashboard.py` | Results dashboard | Not created |

---

## Experiments

| ID | Experiment | Research Question | Status |
|----|------------|-------------------|--------|
| E01 | Extraction baseline | How accurately can dictionary methods extract chemicals/diseases? | Not run |
| E02 | Transformer NER | Does fine-tuned biomedical transformer improve extraction? | Not run |
| E03 | Vocabulary coverage | How much of gold-standard entity set can available terminology represent? | Not run |
| E04 | Matching strategies | How do exact, lexical, fuzzy, semantic retrieval compare? | Not run |
| E05 | Forced vs abstaining | What is the cost of forcing every entity to map? | Not run |
| E06 | Domain constraints | How many errors does domain filtering prevent? | Not run |

---

## Provenance Notes

- **P01:** BC5CDR downloaded from Hugging Face (`bigbio/bc5cdr`) on 2026-10-07
- **P02:** Terminology versions to be recorded in `docs/terminology_versions.md` before first mapping experiment
- **P03:** No restricted clinical data will be committed to this repository

---

## Verification Status

| Check | Status | Notes |
|-------|--------|-------|
| Data downloaded | ✅ | BC5CDR only |
| Environment set up | ⏳ | In progress |
| Golden tests created | ❌ | Not started |
| ADRs written | ❌ | Not started |
