# EXP-009: Submitted MVP parity reconstruction

**Date:** 2026-10-12  
**Status:** Planned  
**Goal:** exceed the submitted MVP on measured extraction and harmonization quality while preserving explicit unmapped reporting.

Understood: the submitted MVP is the **engineering baseline to exceed**, not something to reproduce exactly. That is the right framing. Your submitted system established a working, honest pipeline; the repository should now turn it into a more capable, evaluated clinical harmonization system.

## Baseline to beat

| Baseline metric | Submitted MVP |
|---|---:|
| Raw abstracts processed | 500 |
| Extracted occurrences | 1,715 |
| Mapped occurrences | 579 |
| Unmapped occurrences | 1,136 |
| Vocabulary coverage | 33.8% |
| OMOP-routed records | 579 |
| Extraction evaluation | Not formally measured |
| Linking evaluation | Not formally measured |
| Domain-routing evaluation | Not formally measured |

The submitted system’s main strengths were pipeline completeness, transparent unmapped reporting, and correct use of the supplied vocabulary. Its main improvement opportunities are extraction recall, mapping coverage without sacrificing precision, and formal per-stage evaluation.

## Define the engineering target

The project should not aim merely for “more mapped mentions.” The meaningful target is:

> Increase useful harmonized coverage while maintaining high mapping precision, preserving explicit abstention, and improving measured extraction quality.

A good Phase 1 target would be:

| Metric | Submitted baseline | Phase 1 target |
|---|---:|---|
| Extraction F1 against BC5CDR gold | Not measured | Establish measured baseline, then improve |
| Extracted occurrences | 1,715 | Justified by evaluation, not maximized |
| Mapped occurrences | 579 | Increase without forcing weak matches |
| Vocabulary coverage | 33.8% | Increase through better normalization/candidate matching |
| Mapping precision | Not measured | Measure and keep high |
| Incorrect domain routing | Not measured | Zero for routed records |
| Unmapped visibility | Yes | Preserve and improve |

“More mapped” is only good if the added mappings are correct. Otherwise the system merely converts extraction false positives into plausible-looking OMOP records.

## Preserve the submitted schema

Your submitted CSV schema is already strong and should remain the pipeline’s core occurrence record:

```text
document_id
passage_type
mention_text
normalized_mention
start_char
end_char
entity_type
extraction_method
extraction_confidence
concept_id
concept_name
domain
vocabulary
destination_table
mapping_status
mapping_method
```

For the improved system, retain these fields and add provenance/evaluation fields only where they earn their place:

```text
mention_id
document_id
passage_type
passage_offset
mention_text
normalized_mention
start_char
end_char
entity_type
extraction_method
extraction_confidence
candidate_concept_ids
selected_concept_id
selected_concept_name
concept_domain
vocabulary
match_type
match_score
domain_eligible
mapping_status
mapping_method
destination_table
```

The important addition is `domain_eligible`: a mention may match `Hyperactivity level`, but because its domain is `Observation`, it must be recorded as unmapped or out-of-scope rather than routed to `condition_occurrence`.

## Improved pipeline design

```text
500 raw BC5CDR abstracts
  ↓
Passage-aware extraction
  ├─ Dictionary/rules baseline
  ├─ PubMedBERT NER
  └─ Optional hybrid: high-precision rules + contextual NER
  ↓
Occurrence records
  ↓
Normalization
  ↓
Candidate retrieval
  ├─ Exact normalized match
  ├─ Lexical / fuzzy match
  └─ Later: embedding retrieval
  ↓
Domain validation
  ↓
Accept, rerank, or abstain
  ↓
OMOP-oriented records
  ↓
Dashboard + per-stage evaluation
```

The first improved system should still use the **dictionary extractor**, because it is the submitted baseline and has much higher precision. PubMedBERT becomes a second extraction condition once the harmonization and evaluation layers work.

## First upgrade: EXP-009

Rather than “submitted-MVP parity,” name it:

### `EXP-009: Baseline harmonization upgrade`

**Objective:** exceed the submitted MVP on measured extraction and harmonization quality while preserving explicit unmapped reporting.

**Baseline:**

- 1,715 extracted occurrences.
- 579 mapped occurrences.
- 33.8% vocabulary coverage.
- Dictionary lexical/heuristic extraction.
- Exact normalized vocabulary matching.
- Domain-aware routing.

**Conditions:**

| Condition | Extraction | Matching | Purpose |
|---|---|---|---|
| A: Submitted baseline | Dictionary lexical/heuristic | Exact normalized match | Reproduce baseline behavior |
| B: Improved lexical matching | Dictionary | Normalization, aliases, word-boundary matching | Improve coverage without semantic risk |
| C: PubMedBERT extraction | PubMedBERT epoch 3 | Exact normalized match | Test whether contextual NER improves candidate coverage |
| D: Hybrid | Dictionary plus PubMedBERT, with overlap resolution | Exact/lexical matching | Test whether contextual coverage adds useful mappings |

Condition A establishes the baseline; Condition B is likely the first genuine engineering improvement; Conditions C and D test whether the transformer helps the actual harmonization task.

