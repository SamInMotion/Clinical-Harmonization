# EXP-006: PubMedBERT BC5CDR fine-tuning

**Date:** 2026-10-11  
**Status:** Completed  
**Environment:** Windows, CPU, Python 3.14.4, Transformers 5.8.0  
**Model:** Local PubMedBERT checkpoint  
**Dataset:** BC5CDR training BioC XML  
**Related experiments:** EXP-004 tiny overfit preflight; EXP-005 feasibility estimate  

## Objective

Fine-tune the local PubMedBERT model for five-label BIO NER on the BC5CDR training set and retain reproducible per-epoch checkpoints.

## Configuration

| Setting | Value |
|---|---:|
| Seed | 42 |
| Device | CPU |
| Epochs | 3 |
| Batch size | 16 |
| Learning rate | 2e-5 |
| Maximum sequence length | 512 |
| Optimizer | AdamW |
| Weight decay | 0.01 |
| Warmup ratio | 0.1 |
| Gradient clipping | 1.0 |
| Training documents | 500 |
| Training examples | 1,000 |
| Optimizer steps per epoch | 63 |
| Total optimizer steps | 189 |

## Training result

| Epoch | Average training loss | Runtime | Checkpoint |
|---:|---:|---:|---|
| 1 | 0.6170 | 39.62 minutes | `output/training/pubmedbert_bc5cdr/epoch_1` |
| 2 | 0.1247 | 40.12 minutes | `output/training/pubmedbert_bc5cdr/epoch_2` |
| 3 | 0.0838 | 41.12 minutes | `output/training/pubmedbert_bc5cdr/epoch_3` |

Total runtime: **2.01 hours**.

The loss decreased monotonically:

\[
0.6170 \rightarrow 0.1247 \rightarrow 0.0838
\]

## Implementation correction

The initial training script was corrected before execution for project-relative path handling, the loader/dataset interface, and explicit validation that the tokenizer is fast. The training configuration, optimizer, scheduler, logging approach, checkpointing approach, and three-epoch plan were preserved.

## Model-loading interpretation

The load report is expected:

- `UNEXPECTED` entries are pretrained masked-language-model and pooler parameters not used by the token-classification architecture.
- `MISSING` classifier weights indicate that the five-label NER head was newly initialized before fine-tuning.

## Claims boundary

EXP-006 establishes:

- The model completed three full training epochs.
- Training loss decreased substantially.
- Checkpoints were saved after each epoch.
- The training workflow is reproducible from the committed script and recorded configuration.

EXP-006 does **not** establish:

- Entity-level precision, recall, or F1.
- Generalization beyond the training set.
- Correct entity-boundary extraction.
- Readiness for public reporting or deployment.

The next required step is evaluation on the designated held-out BC5CDR evaluation set using entity-level metrics.
