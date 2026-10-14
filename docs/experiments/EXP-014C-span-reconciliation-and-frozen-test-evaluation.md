# EXP-014C: Span Reconciliation and Frozen Test Evaluation

**Date:** 2026-10-14  
**Status:** Complete  
**Input:** BC5CDR development set for strategy selection; BC5CDR test set for final evaluation  
**Purpose:** Evaluate whether reconciling same-type overlapping dictionary and PubMedBERT spans improves the frozen hybrid configuration.

## Research question

Can span reconciliation reduce the same-type boundary mismatch errors identified in EXP-014B while preserving the hybrid’s recall improvement?

## Motivation

EXP-014B found that 716 of 994 transformer-added false positives in the EXP-014A dictionary-preferred hybrid partially overlapped a same-type gold entity. The dominant error mode was therefore span-boundary disagreement rather than entirely disjoint false predictions.

EXP-014C evaluates strategies that reconcile overlapping same-type dictionary and PubMedBERT predictions instead of always retaining the dictionary span.

## Configuration

- Confidence threshold: 0.95, selected by EXP-014A on development data
- Strategy-selection split: BC5CDR development set
- Final-evaluation split: BC5CDR test set
- Matching policy: document-level character offsets; location-level gold spans; type-aware exact-span matching

Non-overlapping PubMedBERT predictions with confidence at least 0.95 were added to the dictionary predictions. Overlapping same-type predictions were reconciled using one of five strategies.

## Strategies evaluated

| Strategy | Rule |
|---|---|
| `dictionary_preferred` | Retain dictionary span; discard overlapping transformer prediction |
| `transformer_preferred` | Replace overlapping dictionary span with transformer span |
| `longer_span_preferred` | Retain the longer span; ties prefer dictionary |
| `union_span` | Merge overlapping same-type spans into their minimum start and maximum end |
| `intersection_span` | Retain only the overlapping character range |

## Development-set selection

| Strategy | Precision | Recall | F1 |
|---|---:|---:|---:|
| Dictionary baseline | 0.8158 | 0.5847 | 0.6812 |
| `dictionary_preferred` | 0.7660 | 0.7733 | 0.7696 |
| `transformer_preferred` | 0.6773 | 0.7183 | 0.6972 |
| `longer_span_preferred` | 0.7793 | 0.7861 | 0.7827 |
| **`union_span`** | **0.7808** | **0.7876** | **0.7842** |
| `intersection_span` | 0.6653 | 0.7055 | 0.6848 |

Selection rule: maximum development F1, with higher precision as a tie-breaker.

**Selected strategy: `union_span`.**

The `dictionary_preferred` strategy reproduced the EXP-014A development result exactly, validating the implementation before strategy selection.

## Frozen test-set evaluation

| System | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dictionary | 7,038 | 5,617 | 1,421 | 4,339 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT epoch 3 | 13,316 | 7,290 | 6,026 | 2,666 | 0.5475 | 0.7322 | 0.6265 |
| EXP-014A dictionary-preferred hybrid | 10,100 | 7,685 | 2,415 | 2,271 | 0.7609 | 0.7719 | 0.7664 |
| **EXP-014C union-span reconciled hybrid** | **10,081** | **7,869** | **2,212** | **2,087** | **0.7806** | **0.7904** | **0.7854** |

Union-span reconciliation improves both precision and recall relative to the dictionary-preferred hybrid. It improves F1 from 0.7664 to 0.7854.

Relative to the dictionary baseline, it improves recall by 0.2262 while reducing precision by 0.0175.

## Decision

**EXP-014C union-span is the current best evaluated hybrid configuration.**

It is not promoted to the production harmonization pipeline yet. EXP-014B analyzed the dictionary-preferred hybrid, not the union-span configuration. Before promotion, EXP-014D should analyze the false positives introduced by the union-span hybrid to confirm that reconciliation has not introduced a new problematic error class.

## Artifacts

- `src/evaluation/evaluate_exp014c_development_span_reconciliation.py`
- `src/evaluation/evaluate_exp014c_frozen_test_span_reconciliation.py`
- `output/evaluation/exp014c_development_span_reconciliation.json`
- `output/evaluation/exp014c_frozen_test_span_reconciliation.json`

Generated files under `output/` are not committed.

## Claims boundary

EXP-014C establishes that a development-selected union-span reconciliation strategy improves the frozen hybrid’s test-set performance under location-level, type-aware exact-span matching.

It does not establish clinical correctness, OMOP CDM validity, FHIR conformance, deployment readiness, generalization beyond BC5CDR, or that the reconciled hybrid is safe for downstream harmonization without error analysis.