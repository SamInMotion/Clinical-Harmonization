# ADR-001: Extraction Architecture

**Date:** 2026-10-07  
**Status:** Proposed  
**Context:** BC5CDR NER baseline and transformer fine-tuning

---

## Decision

Implement two extraction methods for comparison:

1. **Dictionary/rule-based baseline** — Simple normalization + terminology lookup
2. **Fine-tuned biomedical transformer** — PubMedBERT or BioBERT for contextual NER

---

## Rationale

**Dictionary baseline:**
- Transparent, interpretable
- Fast to implement and debug
- Establishes lower bound for extraction performance
- Handles exact matches reliably

**Transformer NER:**
- Demonstrates model-engineering capability (PyTorch fine-tuning)
- Captures contextual information (abbreviations, long entities)
- Addresses dictionary blind spots (rare entities, variant mentions)
- Aligns with state-of-the-art biomedical NER approaches

**Why both:**
- Enables controlled ablation: what does contextual modelling actually buy?
- Dictionary baseline serves as sanity check and failure-mode analysis tool
- Transformer can be evaluated under reduced training data (sensitivity analysis)

---

## Consequences

**Positive:**
- Clear comparison between lexical and contextual extraction
- Transformer fine-tuning fills PyTorch/model-engineering gap
- Baseline provides error analysis anchor

**Negative:**
- Two implementations to maintain
- Transformer requires GPU for efficient training
- Additional complexity in evaluation (must compare both methods)

**Neutral:**
- Dictionary method will have lower recall but higher precision on exact matches
- Transformer will require hyperparameter tuning (learning rate, batch size, epochs)

---

## Alternatives Considered

**scispaCy with biomedical models:**
- Pros: Pre-trained, fast, no fine-tuning required
- Cons: Less control over architecture, harder to demonstrate model-engineering capability
- Decision: Use as additional baseline, not primary method

**Only transformer:**
- Pros: Simpler implementation, state-of-the-art performance
- Cons: No interpretable baseline, harder to analyze failure modes
- Decision: Rejected — need baseline for controlled comparison

---

## Implementation Notes

- Dictionary baseline: Normalize mentions (lowercase, strip punctuation), lookup in terminology
- Transformer: BIO tagging, sequence labeling head on PubMedBERT
- Evaluation: Precision, recall, F1 at span level (exact and relaxed matching)
- Training: Start with default hyperparameters from biomedical NER literature

---

**Next ADR:** ADR-002 (Linking architecture — candidate retrieval and ranking)
