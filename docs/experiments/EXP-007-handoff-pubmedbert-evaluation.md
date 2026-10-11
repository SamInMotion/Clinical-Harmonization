# EXP-007 handoff: PubMedBERT BC5CDR evaluation

**Date:** 2026-10-11  
**Status:** Paused before evaluation  
**Purpose:** Preserve context and prevent repetition of interface-assumption errors.

## Verified completed work

- EXP-004 passed: PubMedBERT tiny overfit preflight.
- EXP-005 completed: CPU feasibility benchmark.
- EXP-006 completed: three-epoch PubMedBERT BC5CDR fine-tuning.
- Training loss decreased from 0.6170 to 0.0838.
- Checkpoints saved for epochs 1, 2, and 3 under
  `output/training/pubmedbert_bc5cdr/`.
- Total training runtime: 2.01 hours.
- EXP-006 committed as `32b985a`.

## Current blocker

The next task is EXP-007: held-out entity-level evaluation of the epoch-3
checkpoint.

Before writing the evaluator, verify the actual repository interfaces. The
following commands returned no output, indicating that the assumed source
paths may be wrong:

```bash
grep -n -E "^(def |class |    def )" src/ner/load_bc5cdr.py src/ner/transformer_ner.py
grep -n -A 30 "def load_bc5cdr" src/ner/load_bc5cdr.py
grep -n -A 55 "class BC5CDRDataset" src/ner/transformer_ner.py
grep -n -A 30 "def __getitem__" src/ner/transformer_ner.py
```

Do not assume that `load_bc5cdr.py` and `transformer_ner.py` exist at
`src/ner/`. First run:

```bash
ls -la src
ls -la src/ner
git status --short
git ls-files | grep -E "(load_bc5cdr|transformer_ner)"
```

## Known interface corrections

Earlier assumptions that caused failures:

- `load_bc5cdr()` requires an XML path argument.
- It returns a list of documents, not a dictionary of development/train/test splits.
- `BC5CDRDataset` accepts `documents`, `tokenizer`, and `max_length`;
  it does not accept `passages` or `label2id`.
- The tokenizer must be fast and support `return_offsets_mapping=True`.
- Transformers 5.8.0 does not support the earlier
  `build_inputs_with_special_tokens` / `prepare_for_model` approach.
- Token classification requires `-100` labels for special tokens.

## Process rule for the next chat

1. Inspect the actual module files and function signatures before writing code.
2. Run a tiny read-only diagnostic before any training or evaluation script.
3. Do not use long terminal heredocs; create scripts in VS Code and run them
   as files.
4. Do not infer dataset fields, entity formats, or return types.
5. Evaluate only after confirming the development XML path, document schema,
   gold-entity schema, and tokenizer offset field.
6. Report entity-level precision, recall, and F1; never treat training loss
   or the synthetic metric test as model-quality evidence.

## Immediate next actions

1. Run the repository-layout commands above.
2. Locate the actual data-loader and transformer-dataset modules.
3. Inspect their function signatures, return values, and dataset fields.
4. Confirm the development XML path:
   `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_DevelopmentSet.BioC.xml`.
5. Create EXP-007 only after those interfaces are verified.
6. Evaluate the epoch-3 checkpoint first:
   `output/training/pubmedbert_bc5cdr/epoch_3`.
7. Optionally compare epochs 1–3 after the evaluation pipeline is validated.

## Claims boundary

EXP-006 demonstrates successful fine-tuning, not NER quality. No entity-level
precision, recall, F1, generalization, or deployment-readiness claim may be
made until EXP-007 is completed against a properly verified held-out set.