# EXP-014A: Development Threshold Selection and Frozen Test Evaluation

**Date:** 2026-10-13  
**Status:** Completed  
**Purpose:** Select one hybrid confidence threshold using development data only, then evaluate the frozen configuration once on the BC5CDR test set.  
**Supersedes:** EXP-013 as the basis for selecting a hybrid operating threshold.  
**Does not supersede:** EXP-013 as an exploratory sensitivity analysis.

## Research question

Can a confidence threshold for the dictionary and PubMedBERT hybrid extractor be selected without using the test set, and what performance does the frozen configuration achieve on the untouched test set?

## Motivation

EXP-013 ran a confidence-threshold sweep directly on the BC5CDR test set and identified 0.95 as the F1-maximizing threshold. That made 0.95 and 0.97 exploratory, test-informed candidates rather than independently validated operating points.

EXP-014A corrects the evaluation design by moving threshold selection to the development set and freezing the selected configuration before test evaluation.

## Data and configuration

- Corpus: BC5CDR
- Threshold-selection split: `CDR_DevelopmentSet.BioC.xml`
- Final-evaluation split: `CDR_TestSet.BioC.xml`
- Dictionary: `data/terminology/bc5cdr_dictionary.json`
- Transformer: PubMedBERT epoch-3 checkpoint
- Gold policy: location-level, type-aware exact document-character-span matching
- Offset policy: document-level character offsets

## Hybrid rule

1. Retain every base-dictionary prediction.
2. Consider a PubMedBERT prediction only when it does not overlap a dictionary prediction of the same entity type in the same document.
3. Accept that prediction only when its span confidence is at least the selected threshold.

Confidence is the maximum softmax probability assigned to the predicted class among tokens overlapping the predicted entity span. It is a ranking signal, not a calibrated probability.

## Development-only threshold selection

Selection rule:

1. Compute development-set F1 for each threshold.
2. Select the threshold with maximum development F1.
3. Break ties by higher development precision.
4. Freeze the selected threshold before any test-set evaluation.

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| Dictionary baseline | — | 0.8158 | 0.5847 | 0.6812 |
| 0.50 | 5,350 | 0.6455 | 0.8151 | 0.7205 |
| 0.60 | 5,056 | 0.6594 | 0.8129 | 0.7282 |
| 0.70 | 4,723 | 0.6748 | 0.8089 | 0.7358 |
| 0.80 | 4,302 | 0.6965 | 0.8050 | 0.7469 |
| 0.85 | 4,061 | 0.7079 | 0.8008 | 0.7515 |
| 0.90 | 3,687 | 0.7279 | 0.7955 | 0.7602 |
| 0.93 | 3,303 | 0.7473 | 0.7875 | 0.7669 |
| **0.95** | **2,869** | **0.7660** | **0.7733** | **0.7696** |
| 0.97 | 2,233 | 0.7906 | 0.7468 | 0.7680 |
| 0.98 | 1,791 | 0.8082 | 0.7270 | 0.7654 |
| 0.99 | 1,018 | 0.8198 | 0.6727 | 0.7390 |

**Selected threshold: 0.95.**

## Frozen test-set evaluation

| System | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dictionary | 7,038 | 5,617 | 1,421 | 4,339 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT epoch 3 | 13,316 | 7,290 | 6,026 | 2,666 | 0.5475 | 0.7322 | 0.6265 |
| Frozen hybrid, threshold 0.95 | 10,100 | 7,685 | 2,415 | 2,271 | 0.7609 | 0.7719 | 0.7664 |

The frozen hybrid increases recall from 0.5642 to 0.7719 relative to the dictionary while reducing precision from 0.7981 to 0.7609. It improves F1 from 0.6611 to 0.7664.

## Interpretation

The development-selected threshold coincides with the exploratory EXP-013 optimum, but EXP-014A provides the defensible final estimate because the threshold was chosen without reference to test-set performance.

The hybrid trades a modest amount of dictionary precision for a substantial recall improvement. Whether that trade-off is acceptable depends on the downstream cost of false-positive harmonization candidates.

## Artifacts

- `src/evaluation/export_exp014a_development_predictions.py`
- `src/evaluation/evaluate_exp014a_development_threshold_sweep.py`
- `src/evaluation/evaluate_exp014a_frozen_test_hybrid.py`
- `output/evaluation/exp014a_development_threshold_sweep.json`
- `output/evaluation/exp014a_frozen_test_evaluation.json`

Generated files under `output/` are not committed.

## Claims boundary

EXP-014A supports the claim that a development-selected, frozen 0.95-confidence hybrid achieves P 0.7609, R 0.7719, and F1 0.7664 on the BC5CDR test set under location-level, type-aware exact-span matching.

It does not establish clinical correctness, OMOP CDM validity, FHIR conformance, deployment readiness, generalization beyond BC5CDR, or that the hybrid should be promoted to the production harmonization pipeline. EXP-014B false-positive analysis is required before any promotion decision.