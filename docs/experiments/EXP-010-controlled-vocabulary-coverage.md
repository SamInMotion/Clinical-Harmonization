# EXP-010: controlled vocabulary coverage

**Date:** 2026-10-12  
**Status:** Planned  
**Baseline:** EXP-009 word-boundary dictionary pipeline  
**Input:** 500 raw BC5CDR test-set JSON abstracts  
**Vocabulary:** 29-concept OMOP exercise vocabulary  

## Objective

Increase useful vocabulary coverage while preserving domain-safe routing and
explicit abstention.

## Baseline

EXP-009 produced:

- 6,338 extracted occurrences;
- 540 mapped occurrences;
- 5,798 unmapped occurrences;
- 8.5% vocabulary coverage;
- 371 drug_exposure records;
- 169 condition_occurrence records.

## Planned conditions

| Condition | Matching strategy |
|---|---|
| A: EXP-009 baseline | Exact normalized match |
| B: Controlled aliases | Exact match after curated spelling/variant aliases |
| C: Inflectional normalization | Exact match after limited plural/possessive normalization |
| D: Candidate review | RapidFuzz candidates retained for inspection only |

## Non-goals

- Automatic fuzzy mapping.
- LLM-based mapping.
- Embedding retrieval.
- Forcing unmapped mentions into incorrect concepts.

## Evaluation

Measure:

- mapped occurrences;
- vocabulary coverage;
- new mappings introduced;
- mappings changed;
- domain-routing correctness;
- extraction F1, which must remain unchanged unless extraction changes.

## Claims boundary

Coverage growth is meaningful only when the added mappings are correct and
domain-safe. This experiment does not establish end-to-end OMOP correctness or
clinical deployment readiness.