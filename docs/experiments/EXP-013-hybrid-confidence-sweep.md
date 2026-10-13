# EXP-013: Confidence-Thresholded Hybrid Extraction

**Date:** 2026-10-13  
**Status:** Completed initial sweep  
**Input:** BC5CDR test set  
**Dictionary baseline:** EXP-008 base dictionary  
**Transformer alternative:** EXP-007 PubMedBERT epoch-3 checkpoint  
**Gold policy:** Location-level, type-aware exact document-character-span matching  

## Research question

Can a confidence threshold on non-overlapping PubMedBERT predictions retain the hybrid recall gain while reducing the precision loss observed in EXP-012?

## Hybrid rule

1. Retain every base-dictionary prediction.
2. Consider a PubMedBERT prediction only when it does not overlap a dictionary prediction of the same entity type in the same document.
3. Accept that prediction only when its maximum span-token softmax confidence is at least the threshold.

Confidence is the maximum probability assigned to the predicted class among tokens overlapping the predicted span. It is a ranking signal, not a calibrated probability.

## Initial threshold sweep

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| Dictionary baseline | — | 0.7981 | 0.5642 | 0.6611 |
| 0.50 | 5,642 | 0.6399 | 0.8150 | 0.7169 |
| 0.60 | 5,282 | 0.6561 | 0.8119 | 0.7257 |
| 0.70 | 4,949 | 0.6720 | 0.8091 | 0.7342 |
| 0.80 | 4,545 | 0.6908 | 0.8036 | 0.7429 |
| 0.85 | 4,275 | 0.7034 | 0.7992 | 0.7482 |
| 0.90 | 3,876 | 0.7227 | 0.7923 | 0.7559 |
| 0.95 | 3,062 | 0.7609 | 0.7719 | 0.7664 |

## Findings

1. Confidence thresholding improves the precision-recall trade-off monotonically across the evaluated range.
2. At threshold 0.95, hybrid F1 reaches 0.7664, a gain of 0.1053 over the base dictionary.
3. Recall improves from 0.5642 to 0.7719.
4. Precision falls from 0.7981 to 0.7609, a much smaller loss than the unthresholded EXP-012 hybrid.
5. F1 was still increasing at 0.95, so higher thresholds must be evaluated before selecting an operating point.

## Decision

No operating threshold is selected yet. The sweep must be extended to 0.97, 0.98, and 0.99.

The base dictionary remains the production extractor until a thresholded hybrid demonstrates a defensible operating point and its false positives are analyzed.

## Claims boundary

EXP-013 evaluates a hybrid extraction candidate on BC5CDR. It does not establish clinical correctness, OMOP validity, FHIR conformance, deployment readiness, or generalization beyond BC5CDR.