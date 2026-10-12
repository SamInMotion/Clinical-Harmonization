# EXP-008: Dictionary versus PubMedBERT extraction comparison

**Date:** 2026-10-12  
**Status:** Preliminary; gold-denominator reconciliation pending  
**Dataset:** BC5CDR test set  
**Match rule:** Exact document-level character span and entity type  

## Purpose

Compare the dictionary baseline and fine-tuned PubMedBERT epoch-3 checkpoint
as Stage 1 extractors for the clinical harmonization pipeline.

## Results

| System | Gold | Predicted | TP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Dictionary baseline | 9,928 | 7,038 | 5,609 | 0.7970 | 0.5653 | 0.6614 |
| PubMedBERT epoch 3 | 9,956 | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |

## Interpretation

PubMedBERT improves recall by 16.7 percentage points but reduces precision by
24.9 percentage points. Its overall exact-span F1 is 3.5 points below the
dictionary baseline.

For the interview-exercise pipeline, the dictionary baseline remains the
preferred default extractor because of its higher precision, lower false-positive
rate, determinism, and suitability for a deliberately incomplete OMOP vocabulary.

PubMedBERT may be useful where recall is prioritized or where downstream
linking includes robust filtering and abstention.

## Comparison caveat

The dictionary evaluation counted 9,928 gold entities, while EXP-007 counted
9,956. The likely cause is different handling of multi-location BioC
annotations. A final comparison requires both systems to use the same
location-level gold-entity policy.

## Claims boundary

This comparison concerns Stage 1 extraction only. It does not measure linking
accuracy, OMOP routing correctness, FHIR validity, or end-to-end harmonization
quality.