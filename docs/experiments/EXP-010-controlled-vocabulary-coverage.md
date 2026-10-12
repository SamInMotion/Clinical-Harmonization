# EXP-010: controlled vocabulary coverage

**Date:** 2026-10-12  
**Status:** Completed  
**Baseline:** EXP-009 word-boundary dictionary pipeline  
**Input:** 500 raw BC5CDR test-set JSON abstracts  
**Vocabulary:** 29-concept OMOP exercise vocabulary  

## Objective

Increase useful vocabulary coverage while preserving domain-safe routing and
explicit abstention.

## Method

Added controlled normalization before exact vocabulary lookup:

- lowercase and whitespace normalization;
- curated spelling aliases;
- limited possessive normalization;
- limited plural normalization.

The aliases map British spellings to their supplied vocabulary equivalents:

- `hyperglycaemia` to `hyperglycemia`;
- `hypoglycaemia` to `hypoglycemia`.

The plural rule maps regular plural forms to their singular vocabulary forms.
It does not use fuzzy matching, embedding similarity, or automatic semantic
matching.

## Result

| Measure | EXP-009 baseline | EXP-010 controlled normalization |
|---|---:|---:|
| Extracted occurrences | 6,338 | 6,338 |
| Mapped | 540 | 651 |
| Unmapped | 5,798 | 5,687 |
| Vocabulary coverage | 8.5% | 10.3% |
| `drug_exposure` | 371 | 371 |
| `condition_occurrence` | 169 | 280 |

Controlled normalization added 111 mapped occurrences. All additional mappings
were routed to `condition_occurrence`.

## New mappings

| Mention | Concept | Occurrences |
|---|---|---:|
| `seizures` | Seizure | 103 |
| `Seizures` | Seizure | 5 |
| `tremors` | Tremor | 3 |

All new mappings are regular plural variants of existing Condition-domain
vocabulary concepts. No Observation-domain concept was routed to an OMOP
clinical table.

## Decision

Adopt controlled normalization in the EXP-010 harmonization pipeline.

Retain explicit abstention for mentions without an exact normalized, alias, or
controlled inflectional match. Do not enable automatic fuzzy matching.

## Comparison with submitted MVP

| Measure | Submitted MVP | EXP-010 |
|---|---:|---:|
| Extracted occurrences | 1,715 | 6,338 |
| Mapped | 579 | 651 |
| Unmapped | 1,136 | 5,687 |
| Vocabulary coverage | 33.8% | 10.3% |

EXP-010 maps more occurrences than the submitted MVP, but its coverage rate is
lower because its broader BC5CDR dictionary extractor produces many valid
biomedical mentions that are absent from the deliberately incomplete 29-concept
vocabulary.

## Claims boundary

This demonstrates improved vocabulary coverage through controlled
normalization. It does not establish independent mapping accuracy, end-to-end
OMOP correctness, clinical deployment readiness, or generalization beyond
BC5CDR.