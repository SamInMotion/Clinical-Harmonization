# EXP-005: PubMedBERT BC5CDR training feasibility

**Date:** 2026-10-11  
**Status:** Completed  
**Environment:** Windows, Python 3.14.4, Transformers 5.8.0, Tokenizers 0.22.2, CPU  
**Model:** Local PubMedBERT checkpoint at `models/pubmedbert-local`  
**Dataset:** BC5CDR training BioC XML  
**Related experiment:** EXP-004 tiny overfit preflight  

## Objective

Estimate whether full PubMedBERT fine-tuning for BC5CDR NER is practical on the local CPU before committing to a full training run.

## Root-cause correction

The earlier failures were caused by incompatibilities between the NER dataset implementation and Transformers 5.8.0, not by the BC5CDR XML data or the local PubMedBERT checkpoint.

The original implementation used tokenizer APIs that are unavailable in the installed Transformers version:

- `tokenizer.build_inputs_with_special_tokens(...)`
- `tokenizer.prepare_for_model(...)`

The corrected implementation uses the standard tokenizer call:

```python
tokenizer(
    text,
    add_special_tokens=True,
    return_offsets_mapping=True,
    return_special_tokens_mask=True,
    truncation=True,
    max_length=max_length,
)
```

This produces input IDs, attention mask, character offsets, and special-token masks in one aligned encoding step.

## Label alignment

The dataset assigns BIO labels from BioC character-span annotations using tokenizer offset mappings.

- The first token of an entity receives `B-Chemical` or `B-Disease`.
- Subsequent WordPiece tokens in the same entity receive the corresponding `I-` label.
- Non-entity text tokens receive `O`.
- `[CLS]`, `[SEP]`, and other special tokens receive `-100`, the conventional token-classification ignore index.

The implementation also checks that `input_ids`, `attention_mask`, `labels`, and offset mappings have matching lengths.

## Preflight evidence

The repaired dataset implementation passed its preflight:

| Check | Result |
|---|---|
| BC5CDR documents loaded | 500 |
| Dataset examples constructed | 1,000 |
| Token-classification labels generated | 127,063 |
| Synthetic metric smoke test | Passed |
| Local fast tokenizer offset mappings | Available |

Label distribution:

| Label | Count |
|---|---:|
| `O` | 106,678 |
| `B-Chemical` | 5,187 |
| `I-Chemical` | 6,521 |
| `B-Disease` | 4,259 |
| `I-Disease` | 4,418 |
| **Total** | **127,063** |

The synthetic metric result of precision 1.00, recall 1.00, and F1 1.00 is a metric smoke test only. It does **not** measure model performance.

## Feasibility result

| Measure | Result |
|---|---:|
| Training documents | 500 |
| Training examples | 1,000 |
| Batch size | 16 |
| Batches per epoch | 63 |
| Benchmark batches | 5 |
| Average CPU batch time | 27.393 seconds |
| Estimated time per epoch | 0.48 hours |
| Estimated time for three epochs | 1.44 hours |
| Estimated optimizer steps for three epochs | 189 |

The benchmark performed forward passes, backward passes, and optimizer updates on five batches. It did not complete an epoch, save a model checkpoint, or evaluate NER quality.

The estimate excludes evaluation, checkpoint writing, logging, and possible variation from CPU load or thermal throttling.

## Model-loading interpretation

The local PubMedBERT checkpoint is a pretrained masked-language model. Loading it as a five-label `AutoModelForTokenClassification` produces expected warnings:

- `UNEXPECTED`: pretrained masked-language-model and pooler weights are not used by the token-classification architecture.
- `MISSING`: the five-label NER classifier head is newly initialized and must be learned during fine-tuning.

These warnings do not indicate a failed model load.

## Decision

A bounded three-epoch CPU fine-tuning run is feasible. Before full training, validate entity-label alignment on selected passages with known Chemical and Disease annotations, then run a short one-epoch training trial to verify loss decrease and checkpoint saving.

## Claims boundary

EXP-005 establishes:

- The local model and tokenizer load correctly.
- The BC5CDR XML loader and dataset construction run.
- Token-level BIO labels are structurally generated.
- CPU training is operationally feasible.

EXP-005 does **not** establish:

- That every entity boundary is correctly aligned.
- That the model achieves useful NER performance.
- That the eventual evaluation F1 is valid.
- Readiness to report BC5CDR results publicly.
