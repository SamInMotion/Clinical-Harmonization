# Clinical Harmonization Pipeline — Project Closeout

**Status:** Complete for the improved extract → harmonize → report exercise  
**Date:** 2026-10-13  
**Repository:** `clinical-harmonization`  
**Evaluation experiments:** EXP-004 through EXP-011  

## Objective

Build a reproducible clinical NLP pipeline that:

1. extracts biomedical entity mentions from BC5CDR documents;
2. harmonizes them against a deliberately incomplete, controlled OMOP-style vocabulary;
3. routes mapped concepts to domain-appropriate destination tables;
4. preserves unmapped mentions for review rather than forcing incorrect mappings;
5. reports pipeline coverage, mapping quality, and per-document activity.

The project improves the original submitted MVP by adding gold-standard extraction evaluation, controlled normalization, domain-safe routing, abstention, and an auditable reporting layer.

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

### Stage 1 — Extraction

The production extractor uses a curated dictionary with word-boundary matching.

It extracts occurrences of clinical drugs and conditions from title and abstract passages, records document-level character offsets, and preserves the source passage type and extraction method.

### Stage 2 — Harmonization

Mapped mentions are normalized using controlled rules and matched against a 29-concept vocabulary.

The vocabulary contains 17 drug concepts and 12 condition concepts. Mapping uses exact normalized-name matching and controlled morphological variants.

Mapped concepts are routed according to their OMOP domain:

| Domain | Destination table |
|---|---|
| Drug | `drug_exposure` |
| Condition | `condition_occurrence` |
| Observation | Not routed |

Observation-domain concepts are intentionally not routed. This prevents unsafe or unsupported destination-table assignments.

### Stage 3 — Reporting

The dashboard is generated from `harmonized_records.csv`. It reports:

- total extracted occurrences;
- mapped and unmapped counts;
- vocabulary coverage;
- destination-table distribution;
- extraction-method distribution;
- entity-type distribution;
- per-document extracted, mapped, and unmapped counts;
- a searchable and filterable occurrence-level table.

The dashboard is generated locally and is not committed to version control.

## Evaluation results

### Extraction quality

EXP-004 evaluated dictionary extraction against BC5CDR test-set gold entity locations.

| Metric | Result |
|---|---:|
| Gold entities | 9,956 |
| Predicted entities | 11,476 |
| True positives | 8,821 |
| Precision | 0.8861 |
| Recall | 0.5641 |
| F1 | 0.6893 |

The extractor has high precision but incomplete recall. This is expected because the dictionary is deliberately small and does not attempt to cover the full BC5CDR entity distribution.

### Alternative extractor

EXP-005 evaluated a fine-tuned PubMedBERT model.

| Model | Precision | Recall | F1 |
|---|---:|---:|---:|
| PubMedBERT epoch 3 | 0.5475 | 0.7322 | 0.6265 |
| Dictionary extractor | 0.8861 | 0.5641 | 0.6893 |

PubMedBERT achieved higher recall but lower precision. The dictionary extractor remains the production extractor because it is more precise, deterministic, auditable, and better aligned with the controlled-vocabulary mapping stage.

### Harmonization coverage

EXP-010 produced the following results:

| Measure | Count |
|---|---:|
| Extracted occurrences | 6,338 |
| Mapped | 651 |
| Unmapped | 5,687 |
| Vocabulary coverage | 10.3% |

The low coverage rate is expected because the controlled vocabulary contains only 29 concepts. It is not evidence that the extractor failed; it reflects the deliberately incomplete vocabulary.

### Mapping quality

EXP-011 evaluated mapped records against BC5CDR gold entities.

A mapped record was considered gold-supported when:

1. its document-level character span matched a gold entity;
2. its entity type matched the gold entity type;
3. its mapped concept matched the normalized gold mention or a controlled variant.

| Measure | Result |
|---|---:|
| Unique gold entities | 9,956 |
| Mapped records | 651 |
| Gold-supported mapped records | 629 |
| Unsupported mapped records | 22 |
| Mapping precision | 0.9662 |
| Vocabulary-representable gold entities | 647 |
| Vocabulary-representable mapped entities | 629 |
| Vocabulary recall | 0.9722 |

### Routing distribution

| Destination table | Records |
|---|---:|
| `drug_exposure` | 371 |
| `condition_occurrence` | 280 |
| Not routed | 5,687 |

## Key design decisions

### Abstention over forced mapping

The pipeline does not force unmapped mentions into a destination table. Instead, it records them as unmapped with a reason.

This preserves auditability and avoids manufacturing false clinical concepts.

### Controlled vocabulary

The vocabulary is intentionally incomplete. This makes the project a controlled test of extraction, mapping, routing, and reporting behavior rather than a claim of comprehensive clinical terminology coverage.

### Domain-safe routing

Only drug-domain concepts route to `drug_exposure`, and only condition-domain concepts route to `condition_occurrence`. Observation-domain concepts are retained but not routed.

### Evaluation boundary

The evaluation measures:

- extraction against gold entity locations;
- mapping precision for produced mappings;
- vocabulary recall for gold entities representable by the controlled vocabulary.

It does not measure full OMOP transformation correctness, clinical validity, deployment readiness, or generalization beyond BC5CDR.

## Claims boundary

The project supports the following claim:

> “I built and evaluated a reproducible clinical text harmonization pipeline that extracts biomedical mentions, maps them to a deliberately incomplete OMOP-style vocabulary using controlled normalization and domain-safe routing, preserves unmapped mentions for review, and reports per-stage quality against gold annotations.”

The project does **not** support claims of:

- production clinical deployment;
- end-to-end OMOP correctness;
- comprehensive medical terminology coverage;
- generalization to other clinical corpora;
- validated FHIR transformation;
- use of the full SNOMED CT ontology;
- validated hybrid NER performance.

## Future work

Potential next steps include:

1. hybrid dictionary and transformer extraction with explicit overlap resolution;
2. expansion of the controlled vocabulary;
3. evaluation of mapping quality as vocabulary size changes;
4. confidence scoring and human-in-the-loop review;
5. formal OMOP CDM validation using approved test data;
6. evaluation on an external clinical corpus.

## Reproducibility

Main commands:

```bash
python src/pipeline/run_pipeline.py
python src/evaluation/evaluate_ner.py
python src/evaluation/evaluate_mapping_quality.py
python src/pipeline/build_dashboard.py
```

Core outputs:

```text
output/harmonization/exp010/harmonized_records.csv
output/harmonization/exp010/mapped_records.csv
output/harmonization/exp010/unmapped_mentions.csv
output/evaluation/exp011_mapping_quality.json
output/dashboard/clinical_harmonization_dashboard.html
```