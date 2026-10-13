# EXP-011: unsupported mapping analysis

**Date:** 2026-10-13  
**Status:** Completed  
**Scope:** All 22 EXP-010 mapped records without exact gold span/type support  

## Finding

All 22 unsupported mapped records are boundary mismatches. In each case, the
pipeline extracts and maps a valid shorter clinical term, while the BC5CDR
gold annotation marks a longer phrase containing that term.

Examples:

| Pipeline mention | Mapped concept | Gold annotation |
|---|---|---|
| `mania` | Mania | `bipolar mania` |
| `seizures` | Seizure | `grand mal seizures` |
| `morphine` | morphine | `morphine sulfate` |
| `tachycardia` | Tachycardia | `sinus tachycardia` |
| `anxiety` | Anxiety | `anxiety disorders` |
| `tremors` | Tremor | `muscle tremors` |
| `quinine` | quinine | `quinine sulfate` |

## Interpretation

The mappings are conceptually plausible, but they do not satisfy the project's
strict exact-span match rule. Under that rule, they are correctly counted as
unsupported mappings.

No case indicates that controlled plural normalization or domain routing
produced an implausible concept assignment.

## Engineering decision

Retain the strict exact-span evaluation rule.

Do not expand short dictionary matches into longer phrases automatically. Such
an expansion could improve exact-span recall but would require validated
boundary rules and could introduce false positives.

## Claims boundary

EXP-010 has 629 exact-span gold-supported mappings out of 651 mapped records.
The remaining 22 records are boundary mismatches with plausible mapped
concepts, but they are not counted as correct.