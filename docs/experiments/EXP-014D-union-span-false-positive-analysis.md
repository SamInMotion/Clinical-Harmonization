# EXP-014D: Union-Span Hybrid False-Positive Analysis

**Date:** 2026-10-14  
**Status:** Complete  
**Input:** BC5CDR test set  
**Analyzed configuration:** EXP-014C frozen union-span hybrid  
**Purpose:** Determine whether union-span reconciliation improves the hybrid error profile sufficiently to support promotion.

## Research question

Does union-span reconciliation reduce false positives without introducing a new dominant error class?

## Configuration analyzed

- Confidence threshold: 0.95, selected on development data by EXP-014A
- Reconciliation strategy: `union_span`, selected on development data by EXP-014C
- Evaluation split: BC5CDR test set
- Matching policy: document-level character offsets; location-level gold spans; type-aware exact-span matching

## False-positive origin

| Origin | False positives |
|---|---:|
| Dictionary-origin | 844 |
| PubMedBERT-added | 994 |
| Reconciled union | 374 |
| **Total** | **2,212** |

The union-span hybrid produces 2,212 false positives, compared with 2,415 for the EXP-014A dictionary-preferred hybrid. Reconciliation therefore reduces total false positives by 203.

## Reconciled-union error profile

| Measure | Result |
|---|---:|
| Reconciled-union false positives | 374 |
| Disease | 239 |
| Chemical | 135 |
| Partial overlap with gold | 355 |
| Same-type partial overlap | 351 |
| Boundary artifact | 355 |
| Substring artifact | 339 |
| Surface form recurs as gold elsewhere | 245 |

### Confidence distribution

| Confidence band | False positives |
|---|---:|
| 0.95–0.97 | 143 |
| 0.97–0.99 | 185 |
| 0.99–1.01 | 46 |

### Span-length distribution

| Span length | False positives |
|---|---:|
| 4–10 characters | 206 |
| 11–20 characters | 147 |
| 21 characters or more | 21 |

## Findings

1. Union-span reconciliation improves the overall error profile: total false positives fall from 2,415 to 2,212.
2. The improvement is consistent with the frozen test result: precision rises from 0.7609 to 0.7806, recall rises from 0.7719 to 0.7904, and F1 rises from 0.7664 to 0.7854.
3. Most reconciled-union false positives remain boundary artifacts: 355 of 374 partially overlap gold, and 351 overlap a same-type gold entity.
4. Reconciliation reduces the number of boundary errors but does not eliminate span-boundary disagreement as the dominant failure mode.
5. Dictionary-origin false positives often involve surface forms that occur as gold entities elsewhere: 571 of 844. This indicates contextual disambiguation remains a material limitation.

## Decision

**Retain EXP-014C union-span as the current best evaluated hybrid configuration. Do not promote it to production.**

The union-span hybrid has the strongest frozen test-set performance, but its remaining false positives are still predominantly boundary artifacts. These errors may propagate into incorrect normalized mentions, concept candidates, or routed records.

A production promotion decision would require evidence about how these errors affect downstream harmonization, mapping quality, routing, and review workload.

## Artifacts

- `src/evaluation/analyze_exp014d_union_span_false_positives.py`
- `output/evaluation/exp014d_union_span_false_positive_analysis.json`

Generated files under `output/` are not committed.

## Claims boundary

EXP-014D characterizes false positives from the frozen union-span hybrid on the BC5CDR test set. It does not establish clinical correctness, OMOP CDM validity, FHIR conformance, production readiness, or generalization beyond BC5CDR.