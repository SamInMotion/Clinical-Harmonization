# EXP-012: Hybrid Extraction Evaluation

**Date:** 2026-10-13  
**Status:** Completed  
**Input:** BC5CDR test set  
**Dictionary baseline:** EXP-009 word-boundary dictionary  
**Transformer alternative:** EXP-007 PubMedBERT epoch-3 checkpoint  
**Gold policy:** Location-level, type-aware exact document-character-span matching  

## Research question

Can non-overlapping PubMedBERT predictions improve dictionary extraction recall enough to improve F1 without losing the dictionary extractor’s precision advantage?

## Hybrid rule

1. Retain every EXP-009 word-boundary dictionary prediction.
2. Add a PubMedBERT prediction only when it does not overlap any dictionary prediction of the same entity type in the same document.
3. Evaluate dictionary-only, PubMedBERT-only, and hybrid predictions against gold entity spans.

All systems used document-level character offsets and the same gold-entity representation.

## Results

| System | Predicted | True positives | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Dictionary only | 6,338 | 5,616 | 0.8861 | 0.5641 | 0.6893 |
| PubMedBERT only | 13,316 | 7,290 | 0.5475 | 0.7322 | 0.6265 |
| Hybrid union | 12,834 | 8,121 | 0.6328 | 0.8157 | 0.7127 |

## Source contribution

| Measure | Count |
|---|---:|
| Dictionary predictions retained | 7,038 exported; 6,338 unique evaluation keys |
| PubMedBERT predictions exported | 13,316 |
| PubMedBERT predictions overlapping dictionary | 7,520 |
| PubMedBERT predictions added | 5,796 |
| New hybrid true positives | 2,505 |
| New hybrid false positives | approximately 3,291 |

## Findings

1. The hybrid rule improved F1 from 0.6893 to 0.7127, a gain of 0.0516.
2. Recall improved from 0.5641 to 0.8157.
3. Precision fell from 0.8861 to 0.6328.
4. PubMedBERT contributed 2,505 additional true positives but also introduced substantial additional false positives.
5. The result validates the shared document-level offset representation: dictionary-only and PubMedBERT-only metrics reproduce EXP-009 and EXP-007 exactly.

## Decision

Retain the word-boundary dictionary extractor as the production EXP-010 extractor.

Do **not** promote the hybrid extractor yet. Although it improves F1, its precision reduction is substantial and would increase false positives entering harmonization.

## Next evaluation options

1. Add a transformer confidence threshold and evaluate precision-recall trade-offs.
2. Require transformer predictions to have dictionary-supported entity-type evidence before acceptance.
3. Evaluate a hybrid variant that accepts transformer predictions only for mentions absent from the dictionary but present in gold training terminology.
4. Analyze false positives introduced by the transformer before changing the production pipeline.

## Claims boundary

EXP-012 establishes an evaluated hybrid extraction candidate on BC5CDR. It does not establish clinical correctness, OMOP validity, FHIR conformance, deployment readiness, or generalization beyond BC5CDR.