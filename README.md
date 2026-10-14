# Clinical Text Harmonization: Evaluating Extraction and Terminology Mapping

**Status:** Active research prototype

This project investigates how reliably biomedical text can be transformed into standardized clinical concepts, and where errors enter that process.

It implements and evaluates a pipeline for biomedical entity extraction, controlled-vocabulary mapping, domain-aware OMOP-style routing, and preservation of unmapped mentions. Using the BC5CDR corpus, the project separates extraction performance from mapping quality instead of treating the number of generated structured records as evidence of correctness.

The central objective is to understand how extraction methods, confidence-based hybrid filtering, and vocabulary constraints affect the reliability of structured biomedical representations.

## At a glance

Using BC5CDR, this project compares a deterministic dictionary extractor, a fine-tuned PubMedBERT extractor, and confidence-thresholded hybrids. It then asks whether better extraction actually produces more reliable standardized clinical representations.

The main finding is that improved extraction does not automatically solve harmonization. A development-selected, frozen hybrid combining dictionary predictions with high-confidence PubMedBERT predictions achieved **0.7806 precision, 0.7904 recall, and 0.7854 F1** on the BC5CDR test set—higher recall and F1 than the dictionary alone, with only a small precision reduction.

However, error analysis showed that many remaining hybrid errors were span-boundary disagreements rather than entirely invented mentions. Because those errors can still produce incorrect normalized mentions or concept candidates, the hybrid is retained as an evaluated research configuration rather than promoted to production.

The active harmonization pipeline maps only 10.3% of extracted occurrences because it intentionally uses a small 29-concept vocabulary. This makes mapping failures visible instead of forcing unsupported clinical concepts into OMOP-style destination tables.
## Research Question

> How reliably can biomedical text be transformed into standardized clinical concepts and interoperable clinical data, and where do errors enter that transformation?

The investigation examines five related questions:

- How do dictionary-based extraction and transformer-based extraction differ in precision and recall?
- How do lexical matching choices affect false positives and missed mentions?
- Can a confidence-thresholded hybrid retain transformer recall while limiting precision loss?
- How does a deliberately incomplete controlled vocabulary affect mapping rate and mapping quality?
- How should unmapped mentions and unsupported mappings be handled and evaluated?

The current experiments focus on extraction and controlled-vocabulary mapping using BC5CDR. They do not establish end-to-end clinical correctness or interoperability conformance.

## Pipeline Overview

```text
                  BC5CDR BioC XML
                         |
                         v
              Biomedical entity extraction
                         |
                         v
                Occurrence-level records
                         |
                         v
              Controlled-vocabulary mapping
                         |
                         v
                Mapping-status assessment
                         |
               +---------+---------+
               |                   |
               v                   v
       Approved domain       Unmapped or
           routing           non-routed record
               |                   |
               +---------+---------+
                         |
                         v
                  Reporting dashboard
```

The active harmonization pipeline uses dictionary-based extraction with word-boundary matching. A fine-tuned PubMedBERT extractor and a confidence-thresholded dictionary–transformer hybrid have also been evaluated.

The pipeline separates several decisions:

1. **Extraction:** identify biomedical mentions and their document-level character spans.
2. **Hybrid filtering:** retain dictionary predictions and add high-confidence, non-overlapping PubMedBERT predictions.
3. **Mapping:** match extracted mentions against a controlled vocabulary using normalization and controlled variants.
4. **Routing:** assign mapped concepts to an approved OMOP-style destination only when the domain has an explicitly supported destination.
5. **Unmapped-record handling:** preserve mentions that cannot be mapped or safely routed instead of forcing them into a standardized representation.
6. **Evaluation and reporting:** assess extraction and mapping separately and expose pipeline outputs through a static HTML dashboard.

## Current Implementation

### Biomedical entity extraction

The active EXP-010 pipeline uses a curated dictionary derived from BC5CDR training annotations.

The extraction strategy uses word-boundary matching to reduce substring-related false positives. Occurrence records include document-level character spans, entity type, passage information, and extraction method.

A fine-tuned PubMedBERT model was evaluated as an alternative. It achieved higher recall but lower precision than the word-boundary dictionary in the reported test evaluation.

The current dictionary extractor was retained for EXP-010 because it is deterministic, auditable, and more precise under the evaluated conditions. This is a choice for the current prototype, not a claim that dictionary extraction is universally preferable to transformer-based methods.

### Hybrid extraction

EXP-014A evaluated a hybrid extractor with the following rule:

1. Retain every dictionary prediction.
2. Consider a PubMedBERT prediction only when it does not overlap a dictionary prediction of the same entity type in the same document.
3. Accept that prediction only when its span confidence is at least 0.95.

Confidence is the maximum softmax probability assigned to the predicted class among tokens overlapping the predicted entity span. It is a ranking signal, not a calibrated probability.

The 0.95 threshold was selected using the BC5CDR development set only. The frozen configuration was then evaluated once on the untouched BC5CDR test set.

The hybrid is **not promoted to the production harmonization pipeline**. Its false positives must first be analyzed in EXP-014B.

### Controlled-vocabulary mapping

The active harmonization pipeline uses a deliberately incomplete vocabulary of 29 concepts:

- 17 drug concepts
- 12 condition concepts

Mentions are normalized using controlled rules and matched against vocabulary entries and approved variants.

The limited vocabulary makes it possible to investigate mapping behavior under constrained terminology coverage. It is not intended to represent a comprehensive clinical terminology.

A successful lexical match is not, by itself, proof of clinical equivalence. In particular, BC5CDR chemical annotations do not automatically correspond to valid OMOP drug concepts, and disease annotations do not automatically establish valid OMOP condition mappings.

### Domain-aware routing

The current implementation uses the following OMOP-style routing rules:

| Concept domain | Destination |
|---|---|
| Drug | `drug_exposure` |
| Condition | `condition_occurrence` |
| Observation | Not routed |

The routing logic does not treat the existence of a mapped concept as sufficient justification for assigning it to a destination table.

This is an experimental routing policy. It does not implement or validate the complete OMOP Common Data Model, its full set of constraints, or clinical data transformation requirements.

### Unmapped mentions

Mentions that cannot be mapped are retained with a mapping status and reason where available.

This makes mapping failures inspectable and prevents the pipeline from representing every extracted mention as a successful standardized concept.

The project therefore distinguishes extraction yield, mapping rate, mapping support, and routing outcome.

### Reporting dashboard

`src/pipeline/build_dashboard.py` generates a static HTML dashboard from the harmonized occurrence records.

The dashboard includes:

- Overall occurrence counts
- Destination distribution
- Extraction-method distribution
- Entity-type distribution
- Per-document activity
- A filterable occurrence-level table

The generated dashboard is local output and is not committed to the repository.

## Results

The results below describe specific experiments and their evaluation protocols. Metrics from different experiments should not be interpreted as directly interchangeable when their data splits or evaluation procedures differ.

### Extraction comparison

The following results were reported for the BC5CDR test set using location-level, type-aware exact-span matching.

| Extractor | Precision | Recall | F1 |
|---|---:|---:|---:|
| Base dictionary, EXP-008 | 0.7981 | 0.5642 | 0.6611 |
| Word-boundary dictionary, EXP-009 | 0.8861 | 0.5641 | 0.6893 |
| PubMedBERT, epoch 3, EXP-007 | 0.5475 | 0.7322 | 0.6265 |

The word-boundary dictionary achieved higher precision than PubMedBERT, while PubMedBERT recovered more gold mentions at the cost of more false positives.

These findings motivate hybrid extraction and confidence-based filtering. They do not establish that any one approach is optimal across other datasets or clinical settings.

### Word-boundary dictionary: EXP-009

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

Compared with substring matching, word-boundary matching removed 700 false positives while losing one true positive.

### Base dictionary: EXP-008

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

Results by entity type:

| Entity type | Precision | Recall | F1 |
|---|---:|---:|---:|
| Chemicals | 0.8103 | 0.5380 | 0.6466 |
| Diseases | 0.7855 | 0.5952 | 0.6772 |

### Abbreviation expansion: evaluated negative result

Abbreviation expansion was evaluated on the BC5CDR development set.

| Metric | Base dictionary | Expanded dictionary | Difference |
|---|---:|---:|---:|
| Precision | 0.8158 | 0.7390 | -0.0768 |
| Recall | 0.5847 | 0.5934 | +0.0088 |
| F1 | 0.6812 | 0.6583 | -0.0229 |

Abbreviation expansion increased recall slightly but introduced enough additional false positives to reduce F1. The expanded dictionary is retained as an evaluated alternative, not used by the active pipeline.

## Hybrid Extraction Results

### EXP-012: unthresholded hybrid

EXP-012 retained every dictionary prediction and added a PubMedBERT prediction only when it did not overlap a dictionary prediction of the same entity type in the same document.

| System | Predicted | True positives | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Base dictionary | 7,038 | 5,617 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT only | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |
| Hybrid union | 12,834 | 8,121 | 0.6328 | 0.8157 | 0.7127 |

The unthresholded hybrid improved F1 by 0.0516 over the dictionary baseline but reduced precision from 0.7981 to 0.6328.

### EXP-013: exploratory test-set threshold sweep

EXP-013 swept PubMedBERT confidence thresholds directly on the BC5CDR test set.

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| Dictionary baseline | — | 0.7981 | 0.5642 | 0.6611 |
| 0.90 | 3,876 | 0.7227 | 0.7923 | 0.7559 |
| 0.95 | 3,062 | 0.7609 | 0.7719 | 0.7664 |
| 0.97 | 2,307 | 0.7880 | 0.7397 | 0.7631 |
| 0.98 | 1,756 | 0.8044 | 0.7105 | 0.7546 |
| 0.99 | 945 | 0.8072 | 0.6472 | 0.7184 |

**Status:** Exploratory test-set model selection.

Because the threshold was selected by comparing F1 across thresholds on the same test set used for reporting, the EXP-013 optimum is optimistically biased. EXP-013 is retained as a sensitivity analysis, not as the final hybrid evaluation.

### EXP-014A: development-selected frozen hybrid

EXP-014A corrected the evaluation design:

1. It swept confidence thresholds using the BC5CDR development set only.
2. It selected threshold 0.95 by maximum development F1, with higher precision as a tie-breaker.
3. It froze that threshold.
4. It evaluated the frozen configuration once on the untouched BC5CDR test set.

Development-set selection:

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| **0.95** | **2,869** | **0.7660** | **0.7733** | **0.7696** |

Final test-set evaluation:

| System | Predicted | True positives | False positives | False negatives | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dictionary | 7,038 | 5,617 | 1,421 | 4,339 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT epoch 3 | 13,316 | 7,290 | 6,026 | 2,666 | 0.5475 | 0.7322 | 0.6265 |
| Frozen hybrid, threshold 0.95 | 10,100 | 7,685 | 2,415 | 2,271 | 0.7609 | 0.7719 | 0.7664 |

The development-selected hybrid improves recall from 0.5642 to 0.7719 relative to the dictionary while reducing precision from 0.7981 to 0.7609. It improves F1 from 0.6611 to 0.7664.

This is the current authoritative hybrid result. It does not establish production readiness; EXP-014B false-positive analysis is required before any promotion decision.

## Harmonization and Mapping Evaluation

### Active pipeline: EXP-010

The active EXP-010 pipeline processed 6,338 extracted occurrences using the controlled vocabulary of 29 concepts.

| Measure | Result |
|---|---:|
| Extracted occurrences | 6,338 |
| Mapped occurrences | 651 |
| Unmapped occurrences | 5,687 |
| Mapping rate among extracted occurrences | 10.3% |

The mapping rate is the proportion of extracted occurrences assigned a vocabulary concept. It is **not** a measure of vocabulary coverage, extraction accuracy, or end-to-end correctness.

The relatively low mapping rate is expected to be influenced by the deliberately limited vocabulary. It should not be interpreted as evidence of extraction failure or as a general estimate of coverage for comprehensive clinical terminologies.

### Mapping-quality evaluation: EXP-011

EXP-011 evaluates the support for mappings produced by the controlled-vocabulary pipeline.

Under the project’s evaluation criteria, a mapped record is considered gold-supported when its document-level span and entity type match a gold entity and its mapped concept matches the normalized gold mention or an approved variant.

| Measure | Result |
|---|---:|
| Mapped records | 651 |
| Gold-supported mappings | 629 |
| Unsupported mappings | 22 |
| Mapping precision under the defined criteria | 0.9662 |
| Vocabulary-representable gold entities | 647 |
| Vocabulary-representable mapped entities | 629 |
| Vocabulary recall under the defined criteria | 0.9722 |

These results indicate that most produced mappings satisfy the project’s span, type, and lexical-support criteria.

They should not be interpreted as definitive clinical semantic validation. Lexical agreement and entity-type agreement do not, by themselves, establish that a standardized concept is clinically equivalent to the source mention or suitable for a particular OMOP destination.

### Routing results

The active pipeline produced the following routing distribution:

| Destination or status | Records |
|---|---:|
| `drug_exposure` | 371 |
| `condition_occurrence` | 280 |
| Not routed | 5,687 |

These counts describe the current pipeline’s routing behavior. They do not establish that the resulting records satisfy all OMOP CDM constraints or are ready for use in clinical research.

## Evaluation Protocol

Extraction evaluation uses document-level character spans, entity types, and exact-span matching against gold annotations. The implementation accounts for multiple gold locations and avoids treating a span match with the wrong entity type as a true positive.

The project has undergone corrections to offset handling and evaluation logic. Earlier evaluation approaches produced invalid or superseded results; the detailed history is maintained in the project documentation.

The reported experiments distinguish:

- Extraction precision, recall, and F1
- Mapping rate among extracted occurrences
- Mapping support under the defined evaluation criteria
- Vocabulary-representable gold entities
- Routing outcomes

These measures answer different questions and should not be collapsed into a single end-to-end correctness score.

For experiments involving model thresholds or hybrid predictions, threshold selection is separated from final test evaluation. EXP-014A selects its threshold on development data and evaluates the frozen configuration once on test data. EXP-013, which selected a threshold using test data, is labeled exploratory.



## Installation

Clone the repository and create a virtual environment:

```bash
git clone [https://github.com/SamInMotion/Clinical-Harmonization.git](https://github.com/SamInMotion/Clinical-Harmonization.git)
cd clinical-harmonization

python -m venv .venv
```

Activate the environment in Git Bash on Windows:

```bash
source .venv/Scripts/activate
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

If activation has not been verified, invoke the project interpreter explicitly.

For Git Bash on Windows:

```bash
./.venv/Scripts/python.exe --version
```

For Linux or macOS:

```bash
./.venv/bin/python --version
```

The commands below assume the environment has been activated successfully. Reproducing reported results also requires the BC5CDR corpus, the project dictionary, and the trained PubMedBERT checkpoint.

## Usage

### Run the active harmonization pipeline

```bash
python src/pipeline/run_pipeline.py
```

### Evaluate the base dictionary extractor

```bash
python src/ner/evaluate_dictionary_exp008.py
```

### Evaluate mapping quality

```bash
python src/evaluation/evaluate_mapping_quality.py
```

### Reproduce EXP-014A hybrid evaluation

Export development-set predictions:

```bash
python src/evaluation/export_exp014a_development_predictions.py
```

Run development-only threshold selection:

```bash
python src/evaluation/evaluate_exp014a_development_threshold_sweep.py
```

Evaluate the frozen 0.95 hybrid on the BC5CDR test set:

```bash
python src/evaluation/evaluate_exp014a_frozen_test_hybrid.py
```

### Generate the dashboard

```bash
python src/pipeline/build_dashboard.py
```

The generated dashboard is located at:

```text
output/dashboard/clinical_harmonization_dashboard.html
```

## Key Outputs

The pipeline and evaluation scripts generate artifacts under `output/`, including:

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

Generated artifacts are not committed by default. Run the relevant pipeline or evaluation command to regenerate them.

## Data and Terminology

The primary corpus is BC5CDR, the BioCreative V Chemical Disease Relation corpus.

The project uses a controlled vocabulary for the active harmonization experiments. Additional terminology resources may be considered in future work, but their presence in the repository or local environment does not imply that they are used by the active pipeline.

Before distributing the repository, verify the source, version, license, and redistribution permissions of every dataset and terminology resource included in the public release. In particular, ensure that any vocabulary supplied as part of an interview or assessment exercise is not redistributed without permission.

### BC5CDR citation

Li, J. et al. (2016). *BioCreative V CDR task corpus: a resource for chemical disease relation extraction*. Database, 2016. [https://doi.org/10.1093/database/baw068](https://doi.org/10.1093/database/baw068)

BibTeX:

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
### Reproduce the core results

After placing the required BC5CDR files, trained PubMedBERT checkpoint, and local assessment vocabulary in their documented locations, run:

```bash
./scripts/reproduce_core_results.sh
```

The script checks for the required local inputs, runs the main pipeline and evaluation experiments, and regenerates the principal result and dashboard artifacts. It does not download or redistribute the BC5CDR corpus, trained model checkpoint, or assessment-supplied vocabulary.

## Scope and Limitations

This repository is an active research prototype, not a validated clinical system.

The current experiments support claims about:

- Dictionary extraction performance on BC5CDR under the specified evaluation policies
- The precision-recall trade-off observed between the evaluated dictionary and PubMedBERT extractors
- The effect of unthresholded and confidence-thresholded hybrid extraction
- A development-selected, frozen 0.95-confidence hybrid evaluated once on the BC5CDR test set
- Mapping rates under a deliberately incomplete controlled vocabulary
- Mapping support under the project’s defined evaluation criteria
- Domain-aware routing behavior in the current implementation
- Preservation and reporting of unmapped mentions

The current experiments do **not** establish:

- End-to-end clinical correctness
- Definitive semantic equivalence between every source mention and mapped concept
- Full OMOP Common Data Model implementation or conformance
- FHIR conformance or interoperability validation
- Comprehensive SNOMED CT, ICD-10-CM, RxNorm, or LOINC coverage
- Generalization beyond the evaluated BC5CDR data
- Production readiness of the hybrid extractor
- Clinical deployment readiness or suitability for clinical decision-making

## Documentation

Additional project records are maintained separately from this overview:

- `MANIFEST.md` — data, script, experiment, and provenance register
- `.llm-provenance.md` — environment, dependencies, constraints, and AI-assistance provenance
- `docs/PROJECT_STATE.md` — canonical current-state register
- `docs/PROJECT_CLOSEOUT.md` — closeout summary and claims boundary
- `docs/experiments/` — experiment records and provenance
- `docs/sessions/` — development session logs
- `docs/decisions/` — architecture decision records

Historical corrections and superseded results are documented in the project records so that the rationale for methodological changes remains traceable.

## License

The repository license has not yet been finalised.

Before public release, select a license appropriate to the project’s code and verify that the included datasets, terminology resources, and other artifacts can legally be distributed under the proposed arrangement. A code license does not override the terms governing third-party data or terminology.

## Contact

**Samuel Okoe-Mensah**

[GitHub profile](https://github.com/SamInMotion)
