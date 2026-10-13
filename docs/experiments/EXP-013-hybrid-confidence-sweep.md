# EXP-013: Confidence-Thresholded Hybrid Extraction

**Date:** 2026-10-13  
**Status:** Complete; exploratory test-set model selection  
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

## Extended threshold sweep

| Threshold | PubMedBERT added | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| Dictionary baseline | — | 0.7981 | 0.5642 | 0.6611 |
| 0.50 | 5,642 | 0.6399 | 0.8150 | 0.7169 |
| 0.60 | 5,282 | 0.6561 | 0.8119 | 0.7257 |
| 0.70 | 4,949 | 0.6720 | 0.8091 | 0.7342 |
| 0.80 | 4,545 | 0.6908 | 0.8036 | 0.7429 |
| 0.85 | 4,275 | 0.7034 | 0.7992 | 0.7482 |
| 0.90 | 3,876 | 0.7227 | 0.7923 | 0.7559 |
| 0.93 | 3,480 | 0.7418 | 0.7836 | 0.7621 |
| 0.95 | 3,062 | 0.7609 | 0.7719 | 0.7664 |
| 0.97 | 2,307 | 0.7880 | 0.7397 | 0.7631 |
| 0.98 | 1,756 | 0.8044 | 0.7105 | 0.7546 |
| 0.99 | 945 | 0.8072 | 0.6472 | 0.7184 |

## Findings

1. F1 peaks at threshold 0.95 with F1 0.7664.
2. The 0.95 hybrid improves recall from 0.5642 to 0.7719 while reducing precision from 0.7981 to 0.7609.
3. The 0.97 hybrid is a conservative alternative: precision 0.7880 is close to the dictionary baseline, while recall rises to 0.7397.
4. Threshold 0.98 exceeds dictionary precision but loses too much recall, reducing F1 to 0.7546.
5. The confidence score is effective for ranking transformer predictions, but it is not calibrated probability.

## Decision

EXP-013 is an exploratory test-set threshold sweep. Its thresholds were selected by comparing F1 across thresholds on the same BC5CDR test set used for reporting.

Therefore, threshold 0.95 and threshold 0.97 are exploratory, test-informed candidates. They are **not independently selected operating points** and must not be presented as final hybrid results.

EXP-014A subsequently selected threshold 0.95 using the BC5CDR development set only and evaluated the frozen configuration once on the untouched test set. EXP-014A is the authoritative hybrid evaluation.

Do not promote either EXP-013 candidate to the production pipeline. EXP-014B must analyze the false positives introduced by the frozen hybrid before deciding whether the precision trade-off is acceptable.

## Claims boundary

EXP-013 establishes an exploratory sensitivity analysis of confidence-thresholded hybrid extraction on the BC5CDR test set. It does not establish an independently selected operating point, production readiness, clinical correctness, OMOP validity, FHIR conformance, or generalization beyond BC5CDR.

The authoritative frozen hybrid result is provided by EXP-014A.