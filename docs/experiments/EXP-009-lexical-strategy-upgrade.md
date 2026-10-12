# EXP-009: lexical strategy upgrade

**Date:** 2026-10-12  
**Status:** Completed  
**Input:** 500 raw BC5CDR test-set JSON abstracts  
**Extractor:** BC5CDR training dictionary  
**Vocabulary:** 29-concept OMOP exercise vocabulary  

## Change

Replaced substring dictionary matching with whole-word-boundary matching.

## Extraction evaluation

| Strategy | Predicted | Exact matches | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Substring | 7,038 | 5,617 | 0.7981 | 0.5642 | 0.6611 |
| Word boundary | 6,338 | 5,616 | 0.8861 | 0.5641 | 0.6893 |

Word-boundary matching removed 700 false positives and lost one true positive.
It improved precision by 8.8 percentage points and F1 by 2.8 percentage points.

## Harmonization result

To be completed from `output/harmonization/exp009/summary.json`.

## Decision

Adopt word-boundary dictionary matching as the EXP-009 Stage 1 extractor.

Retain exact normalized vocabulary matching and controlled aliases. Do not
enable automatic fuzzy matching.

## Claims boundary

This improves extraction precision and harmonization input quality. It does not
establish end-to-end OMOP correctness, clinical deployment readiness, or
generalization beyond BC5CDR.