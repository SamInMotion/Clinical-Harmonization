# Reliable Clinical Text Harmonization

**Version:** 0.4.1  
**Status:** Active research prototype  
**Last updated:** 2026-10-13

---

## Research Question

> How reliably can biomedical text be transformed into standardized clinical concepts and interoperable clinical data, and where do errors enter that transformation?

This repository investigates that question through a controlled, evaluable pipeline built on BC5CDR. It measures extraction quality, controlled-vocabulary mapping, domain-safe routing, abstention, and reporting separately rather than treating an end-to-end count as a correctness metric.

---

## Current Implementation

The currently implemented pipeline is **EXP-010**, with mapping-quality evaluation in **EXP-011**.

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

The pipeline uses a deliberately incomplete controlled vocabulary of 29 concepts:

- 17 drug concepts;
- 12 condition concepts.

This makes the project a controlled test of extraction, mapping, routing, and abstention behavior. It does **not** provide comprehensive clinical terminology coverage.

### Extraction

The production extractor uses curated dictionary entries with word-boundary matching. It records document-level character spans, passage type, entity type, and extraction method.

A fine-tuned PubMedBERT extractor was evaluated as an alternative. It achieved higher recall but lower precision than the dictionary extractor.

### Harmonization

Mentions are normalized using controlled rules and matched against the 29-concept vocabulary. Mapped concepts are routed only when their domain has an approved destination:

| OMOP-style domain | Destination |
|---|---|
| Drug | `drug_exposure` |
| Condition | `condition_occurrence` |
| Observation | Not routed |

Observation-domain concepts are retained as unmapped or non-routed rather than assigned to an unsupported destination table.

Unmapped mentions are preserved with a reason. The pipeline does not force every mention into a standardized representation.

### Reporting

`src/pipeline/build_dashboard.py` generates a static HTML dashboard from `harmonized_records.csv`. It reports totals, destination distribution, extraction-method distribution, entity-type distribution, per-document activity, and a filterable occurrence-level table.

The generated dashboard is local output and is not committed.

---

## Verified Results

### Extraction: EXP-009 word-boundary strategy

EXP-009 evaluated lexical matching strategies for dictionary extraction. Its word-boundary strategy is the extraction strategy used by the active EXP-010 pipeline.

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

Word-boundary matching removed 700 substring false positives and lost one true positive relative to substring matching. It improved precision by 8.8 percentage points and F1 by 2.8 percentage points.

**Correction:** an earlier version of this documentation incorrectly attributed these metrics to EXP-004 and reported incorrect prediction and true-positive counts. EXP-004 was the PubMedBERT tiny-overfit preflight. The verified EXP-009 result is 6,338 predictions and 5,616 exact matches.

### Verified base-dictionary baseline: EXP-008

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

| Entity type | Precision | Recall | F1 |
|---|---:|---:|---:|
| Chemicals | 0.8103 | 0.5380 | 0.6466 |
| Diseases | 0.7855 | 0.5952 | 0.6772 |

### Alternative extractor: EXP-007 PubMedBERT

| Extractor | Precision | Recall | F1 |
|---|---:|---:|---:|
| EXP-009 word-boundary dictionary | 0.8861 | 0.5641 | 0.6893 |
| PubMedBERT epoch 3 | 0.5475 | 0.7322 | 0.6265 |

PubMedBERT improves recall but reduces precision. The dictionary word-boundary extractor remains the production extractor because it is deterministic, auditable, and better aligned with controlled-vocabulary mapping.

### Abbreviation expansion: evaluated negative result

Abbreviation expansion was evaluated on the BC5CDR development set. It slightly improved recall but substantially reduced precision and F1.

| Metric | Base dictionary | Expanded dictionary | Difference |
|---|---:|---:|---:|
| Precision | 0.8158 | 0.7390 | -0.0768 |
| Recall | 0.5847 | 0.5934 | +0.0088 |
| F1 | 0.6812 | 0.6583 | -0.0229 |

The expanded dictionary is retained as provenance and an evaluated negative result. It is not the production extractor.

### Harmonization: EXP-010

| Measure | Result |
|---|---:|
| Extracted occurrences | 6,338 |
| Mapped | 651 |
| Unmapped | 5,687 |
| Vocabulary coverage | 10.3% |

The low coverage is expected because the vocabulary is intentionally incomplete. It is not evidence that extraction failed.

### Mapping quality: EXP-011

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

### Routing

| Destination | Records |
|---|---:|
| `drug_exposure` | 371 |
| `condition_occurrence` | 280 |
| Not routed | 5,687 |

---

## Historical Corrections

The project retains earlier invalid, superseded, and misattributed results as provenance.

| Result | Status | Reason |
|---|---|---|
| Dictionary F1 = 0.0966 | INVALID | Document-global gold offsets were compared with passage-local predicted offsets. |
| Dictionary F1 = 0.6614 | SUPERSEDED | Used one-location gold representation and type-blind matching. |
| Gate C-2 dictionary F1 = 0.6611 | Historical baseline | Location-level, type-aware evaluation of the base dictionary. |
| EXP-004 dictionary extraction claim | MISATTRIBUTED | EXP-004 was the PubMedBERT tiny-overfit preflight; the 0.6893 F1 result belongs to EXP-009. |
| End-to-end survival = 7.9% | INVALID AS CORRECTNESS | Raw count ratio; no gold-to-standardized-concept verification. |

Historical results are retained to document how evaluation errors were found and corrected. They must not be cited as current performance.

---

## Installation

```bash
git clone <repository-url>
cd clinical-harmonization

python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
# or: source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
```

**Environment rule:** until shell activation is verified, invoke the project interpreter explicitly:

```bash
.venv/Scripts/python.exe
```

---

## Data

| Dataset | Source | License | Location | Status |
|---|---|---|---|---|
| BC5CDR | BioCreative V CDR | CC-BY 3.0 | `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/` | Downloaded |
| Base BC5CDR dictionary | Project-defined | Project artifact | `data/terminology/bc5cdr_dictionary.json` | Implemented |
| Abbreviation-expanded dictionary | Project-defined | Project artifact | `data/terminology/bc5cdr_dictionary_abbreviation_expanded.json` | Evaluated negative result |
| Controlled harmonization vocabulary | Project-defined | Project artifact | `data/terminology/omop_exercise_vocabulary.json` | Implemented |
| SNOMED CT | IHTSDO | IHTSDO license | `data/terminology/snomed/` | Not used by EXP-010 |
| ICD-10-CM | CDC/NCHS | Public domain | `data/terminology/icd10cm/` | Not used by EXP-010 |
| RxNorm | NLM | Public domain | `data/terminology/rxnorm/` | Not used by EXP-010 |
| LOINC | Regenstrief | LOINC license | `data/terminology/loinc/` | Not used by EXP-010 |

BC5CDR should be cited as:

```bibtex
@article{DBLP:journals/biodb/LiSJSWLDMWL16,
  author = {Jiao Li and Yueping Sun and Robin J. Johnson and Daniela Sciaky and Chih{-}Hsuan Wei and Robert Leaman and Allan Peter Davis and Carolyn J. Mattingly and Thomas C. Wiegers and Zhiyong Lu},
  title = {BioCreative {V} {CDR} task corpus: a resource for chemical disease relation extraction},
  journal = {Database},
  volume = {2016},
  year = {2016},
  doi = {10.1093/database/baw068}
}
```

---

## Usage

Run the active harmonization pipeline:

```bash
python src/pipeline/run_pipeline.py
```

Evaluate the base dictionary extractor:

```bash
python src/ner/evaluate_dictionary_exp008.py
```

Evaluate mapping quality:

```bash
python src/evaluation/evaluate_mapping_quality.py
```

Build the dashboard:

```bash
python src/pipeline/build_dashboard.py
```

Open the generated dashboard:

```text
output/dashboard/clinical_harmonization_dashboard.html
```

---

## Key Outputs

```text
output/harmonization/exp010/harmonized_records.csv
output/harmonization/exp010/mapped_records.csv
output/harmonization/exp010/unmapped_mentions.csv
output/evaluation/exp008_dictionary_bc5cdr_test_location_level.json
output/evaluation/exp011_mapping_quality.json
output/dashboard/clinical_harmonization_dashboard.html
```

Generated artifacts under `output/` are not committed.

---

## Scope and Claims Boundary

This is a research prototype, not a validated clinical system.

The current results support claims about:

- word-boundary dictionary extraction performance on BC5CDR under the EXP-009 policy;
- base-dictionary extraction performance under the EXP-008 policy;
- controlled-vocabulary mapping coverage;
- mapping precision and vocabulary recall for produced mappings;
- domain-safe routing behavior;
- preservation and reporting of unmapped mentions.

They do **not** establish:

- end-to-end OMOP CDM validity;
- FHIR conformance;
- clinical correctness;
- deployment readiness;
- comprehensive SNOMED CT, ICD-10-CM, RxNorm, or LOINC coverage;
- generalization beyond BC5CDR;
- validated hybrid NER performance.

---

## Documentation

- `MANIFEST.md` — data, script, experiment, and provenance register
- `.llm-provenance.md` — environment, dependencies, constraints, and AI-assistance provenance
- `docs/PROJECT_STATE.md` — canonical current-state register
- `docs/PROJECT_CLOSEOUT.md` — closeout summary and claims boundary
- `docs/sessions/` — session logs
- `docs/decisions/` — architecture decision records

---

## License

To be determined — MIT or Apache-2.0.

---

## Contact

Samuel Okoe-Mensah  
[GitHub profile link]