# EXP-009: extraction-difference diagnostic

**Date:** 2026-10-12  
**Status:** Diagnostic completed  
**Input:** 500 raw BC5CDR JSON abstracts  
**Dictionary:** `data/terminology/bc5cdr_dictionary.json`  
**Vocabulary:** 29-concept OMOP exercise vocabulary  

## Purpose

Explain why the current dictionary extractor produced 7,038 occurrences while
the submitted interview-exercise MVP produced 1,715.

## Results

| Extraction strategy | Occurrences |
|---|---:|
| Submitted MVP lexical heuristic | 1,715 |
| Current dictionary substring matching | 7,038 |
| Current dictionary with word-boundary filtering | 6,338 |

Word-boundary filtering removed 700 occurrences, but did not explain the main
difference. The dominant cause is the broader 2,328-form BC5CDR training
dictionary used by the current extractor.

## Harmonization result

| Measure | Submitted MVP | Current dictionary pipeline |
|---|---:|---:|
| Extracted occurrences | 1,715 | 7,038 |
| Mapped | 579 | 552 |
| Unmapped | 1,136 | 6,486 |
| Vocabulary coverage | 33.8% | 7.8% |

The current pipeline found a similar number of vocabulary matches despite
producing far more candidate mentions. Most additional extractions are
biomedical mentions absent from the deliberately incomplete 29-concept
vocabulary.

## Interpretation

The current extractor is broader and likely has higher candidate recall, but
this has not yet been demonstrated against gold annotations. The submitted
extractor was more conservative and produced a higher vocabulary-coverage rate.

Extraction volume is not a quality measure. The next step is to evaluate both
extraction strategies against the BC5CDR gold annotations for the same 500
documents.

## Claims boundary

No extraction-quality or end-to-end improvement claim may be made until
span-level precision, recall, and F1 are computed against the appropriate gold
set.