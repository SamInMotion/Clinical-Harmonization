## Session Log: 2026-10-07 13:00-20:00

**Type:** Implementation + Evaluation

**Goal:** Implement and evaluate dictionary baseline NER on BC5CDR

**What we did:**
1. Created `src/ner/load_bc5cdr.py` — BioC XML parser
2. Created `src/ner/dictionary_baseline.py` — Dictionary builder and matcher
3. Created `src/ner/evaluate_ner.py` — Evaluation script (precision, recall, F1)
4. Created `src/ner/debug_errors.py` — Error analysis tool
5. Built dictionary from training set (2,328 unique forms after filtering)
6. Evaluated on test set (9,928 gold entities)
7. Updated MANIFEST.md with results

**What we learned:**
- Dictionary baseline F1 = 0.097 (precision 0.116, recall 0.083)
- Filtering common words ("ist", "str", "all") improved precision from 0.065 to 0.116 (+79%)
- Main limitations: vocabulary coverage (can't generalize to unseen entities), context blindness (matches everywhere, not just relevant contexts)
- Transformer NER needed for contextual understanding and generalization

**Files Changed:**
- `src/ner/load_bc5cdr.py` — NEW
- `src/ner/dictionary_baseline.py` — NEW
- `src/ner/evaluate_ner.py` — NEW
- `src/ner/debug_errors.py` — NEW
- `data/terminology/bc5cdr_dictionary.json` — NEW
- `MANIFEST.md` — UPDATED with results
- `docs/sessions/2026-10-07_dictionary-baseline.md` — NEW

**Golden Tests:**
- ✅ Placeholder tests pass (trivial)
- ⚠️ Need real golden tests for NER (specific documents with known entities)

**Next Session:**
- Implement transformer NER (fine-tune PubMedBERT/BioBERT)
- Compare against dictionary baseline
- Analyze which entities transformer captures that dictionary misses

**Session Duration:** ~7 hours (including debugging and analysis)
