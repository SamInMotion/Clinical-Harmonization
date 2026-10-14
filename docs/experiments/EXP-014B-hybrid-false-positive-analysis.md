# EXP-014B: Frozen Hybrid False-Positive Analysis

**Date:** 2026-10-14  
**Status:** Complete  
**Input:** BC5CDR test set  
**Analyzed configuration:** EXP-014A frozen hybrid, confidence threshold 0.95  
**Purpose:** Characterize the false positives introduced by the frozen hybrid before making a promotion decision.

## Research question

Are the false positives added by the frozen dictionary and PubMedBERT hybrid understandable, bounded, and unlikely to harm downstream harmonization quality?

## Configuration analyzed

- Dictionary: EXP-009 word-boundary dictionary predictions
- Transformer: EXP-007 PubMedBERT epoch-3 predictions
- Hybrid threshold: 0.95
- Threshold-selection split: BC5CDR development set
- Evaluation split: BC5CDR test set
- Matching policy: document-level character offsets; location-level gold spans; type-aware exact-span matching

Confidence is the maximum softmax probability assigned to the predicted class among tokens overlapping the predicted entity span. It is a ranking signal, not a calibrated probability.

## False-positive origin

| Origin | False positives |
|---|---:|
| Dictionary-origin | 1,421 |
| PubMedBERT-added | 994 |
| **Total** | **2,415** |

The analysis focuses on the 994 false positives added by the hybrid’s transformer component.

## Transformer-added false-positive profile

| Measure | Result |
|---|---:|
| Transformer-added false positives | 994 |
| Disease | 552 |
| Chemical | 442 |
| Partial overlap with any gold entity | 722 |
| Same-type partial overlap | 716 |
| Boundary artifact | 722 |
| Substring artifact | 720 |
| Surface form recurs as gold elsewhere | 77 |

### Confidence distribution

| Confidence band | False positives |
|---|---:|
| 0.95–0.97 | 434 |
| 0.97–0.99 | 442 |
| 0.99–1.01 | 118 |

### Span-length distribution

| Span length | False positives |
|---|---:|
| 1–3 characters | 121 |
| 4–10 characters | 662 |
| 11–20 characters | 197 |
| 21 characters or more | 14 |

## Findings

1. Most transformer-added false positives are not fully disjoint from gold annotations. 722 of 994 partially overlap a gold entity.
2. 716 partially overlap a gold entity of the same type, indicating that span-boundary disagreement is the dominant error mode.
3. 720 are substring artifacts: either the predicted mention is contained within a gold mention or a gold mention is contained within the prediction.
4. High confidence does not eliminate these errors. 118 transformer-added false positives have confidence of at least 0.99.
5. Only 272 transformer-added false positives are fully disjoint from gold entities.
6. The 121 false positives with 1–3 character spans are a potentially important short-mention error class, but they require qualitative inspection before drawing a stronger conclusion.

## Decision

**Do not promote the EXP-014A frozen 0.95 hybrid as-is.**

Although the hybrid improves recall and F1, 72% of its transformer-added false positives are same-type partial overlaps. These errors may still produce incorrect normalized mentions, incorrect concept candidates, or incorrect routed records downstream.

Raising the confidence threshold alone is not a sufficient remedy because 118 false positives occur at confidence 0.99 or above.

## Next evaluation

Run EXP-014C: evaluate span-reconciliation strategies for same-type overlapping dictionary and PubMedBERT predictions using development data only. Candidate strategies include dictionary-span preference, transformer-span preference, longer-span preference, span union, and span intersection.

Freeze the best development-selected strategy before performing a final test-set evaluation.

## Artifacts

- `src/evaluation/analyze_exp014b_hybrid_false_positives.py`
- `output/evaluation/exp014b_hybrid_false_positive_analysis.json`

Generated files under `output/` are not committed.

## Claims boundary

EXP-014B characterizes false positives from the frozen 0.95 hybrid on the BC5CDR test set. It does not establish clinical correctness, OMOP validity, FHIR conformance, production readiness, or generalization beyond BC5CDR.