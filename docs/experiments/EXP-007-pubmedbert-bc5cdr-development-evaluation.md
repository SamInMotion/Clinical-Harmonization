# EXP-007: PubMedBERT BC5CDR development-set evaluation

**Date:** 2026-10-12  
**Status:** Completed  
**Model checkpoint:** `output/training/pubmedbert_bc5cdr/epoch_3`  
**Evaluation set:** BC5CDR development BioC XML  
**Related experiments:** EXP-004 overfit preflight; EXP-005 CPU feasibility; EXP-006 fine-tuning

## Objective

Evaluate the epoch-3 PubMedBERT BC5CDR NER checkpoint on the development set
using entity-level exact matching.

An entity was counted as correct only when its document-level character span
and entity type both matched a gold entity exactly.

## Evaluation configuration

| Setting | Value |
|---|---|
| Checkpoint | `output/training/pubmedbert_bc5cdr/epoch_3` |
| Development XML | `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_DevelopmentSet.BioC.xml` |
| Documents | 500 |
| Passages | 1,000 |
| Maximum sequence length | 512 |
| Inference batch size | 8 |
| Tokenizer | Fast tokenizer loaded from the epoch-3 checkpoint |
| Match rule | Exact document-level character span and entity type |

## Implementation

`src/ner/evaluate_pubmedbert_exp007.py` loads the development XML through the
verified `load_bc5cdr` interface, tokenizes each passage with character offset
mappings, runs the epoch-3 checkpoint, decodes BIO predictions, maps
passage-local spans to document-level spans, and compares predicted entities
against gold entities.

The evaluator is independent of the uncommitted `transformer_ner.py` rewrite.
It uses the verified `load_bc5cdr` loader and performs its own offset-aware
entity reconstruction and exact-match scoring.

## Results

| Entity type | Gold | Predicted | Exact matches | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 9,797 | 12,956 | 7,154 | 0.5522 | 0.7302 | 0.6288 |
| Chemical | 5,354 | 6,001 | 4,662 | 0.7769 | 0.8708 | 0.8211 |
| Disease | 4,443 | 6,955 | 2,492 | 0.3583 | 0.5609 | 0.4373 |

## Error diagnostics

| Diagnostic | Count |
|---|---:|
| False positives | 5,802 |
| False negatives | 2,643 |
| Distinct predicted entities with a same-type partial overlap | 5,775 |
| Distinct gold entities with a same-type partial overlap | 2,602 |

Partial overlaps are error-analysis diagnostics. They are not counted as
correct entities and do not contribute to precision, recall, or F1.

## Interpretation

The epoch-3 checkpoint achieves an exact-span entity F1 of 0.6288 on the
BC5CDR development set. Chemical extraction is substantially stronger than
disease extraction.

The principal weakness is disease over-prediction: the model produced 6,955
disease predictions against 4,443 gold disease entities, yielding disease
precision of 0.3583.

## Claims boundary

These results apply only to the epoch-3 checkpoint evaluated on the BC5CDR
development set under the stated exact-span, type-aware match rule.

They do not establish:

- BC5CDR test-set performance.
- Generalization beyond BC5CDR.
- Clinical deployment readiness.
- Superiority over another NER system.
- Publication-ready state-of-the-art performance.

Training loss and the EXP-006 fine-tuning result remain separate from this
entity-level evaluation evidence.

## Machine-readable result

The full result, including capped error-analysis examples, is stored locally
at:

```text
output/evaluation/exp007_pubmedbert_bc5cdr_dev_epoch3.json
```