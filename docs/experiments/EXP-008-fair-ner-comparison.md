# EXP-008: Dictionary versus PubMedBERT extraction comparison

**Date:** 2026-10-12  
**Status:** Completed  
**Dataset:** BC5CDR test set  
**Gold policy:** One entity per BioC annotation location  
**Match rule:** Exact document-level character span and entity type  

## Purpose

Compare the dictionary baseline and the fine-tuned PubMedBERT epoch-3
checkpoint as Stage 1 extractors for the clinical harmonization pipeline.

Both systems were evaluated on the BC5CDR test set using the same
location-level gold policy and exact-span, type-aware match rule.

## Systems

| System | Extraction method | Source |
|---|---|---|
| Dictionary baseline | Exact normalized dictionary matching | `src/ner/evaluate_dictionary_exp008.py` |
| PubMedBERT | Fine-tuned token-classification model | `src/ner/evaluate_pubmedbert_exp007.py` |

The dictionary was built from the BC5CDR training set. PubMedBERT was
fine-tuned on the same training set for three epochs.

## Results

| System | Gold | Predicted | Exact matches | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Dictionary baseline | 9,956 | 7,038 | 5,617 | 0.7981 | 0.5642 | 0.6611 |
| PubMedBERT epoch 3 | 9,956 | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |

## Interpretation

PubMedBERT improves recall by 16.8 percentage points but reduces precision by
25.1 percentage points. Its overall exact-span F1 is 3.5 percentage points
below the dictionary baseline.

The dictionary baseline is therefore the preferred default extractor for the
current precision-sensitive harmonization pipeline. It produces fewer false
positives, is deterministic, and is more suitable for a deliberately incomplete
OMOP vocabulary.

PubMedBERT may be useful when recall is prioritized or when downstream linking
includes robust candidate filtering, confidence scoring, and abstention.

## Engineering decision

Use the dictionary baseline as the Stage 1 extractor for EXP-009 and the
clinical harmonization pipeline.

Retain PubMedBERT as an evaluated alternative extraction condition. A hybrid
extractor may be explored later, but only after the harmonization and
domain-routing layers are evaluated.

## Claims boundary

This comparison concerns Stage 1 extraction only. It does not measure linking
accuracy, OMOP routing correctness, FHIR validity, or end-to-end harmonization
quality.

The PubMedBERT result is based on the epoch-3 checkpoint and does not establish
generalization beyond BC5CDR or deployment readiness.