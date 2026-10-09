## Session Log: 2026-10-08 — Transformer NER Blocked

**Type:** Implementation + Documentation

**Goal:** Fine-tune transformer (BioBERT/PubMedBERT) for BC5CDR NER

**What we did:**
1. Fixed loader offset bug (local_offset = doc_offset - passage_offset)
2. Corrected baseline evaluation (F1 = 0.661, not 0.097)
3. Attempted transformer NER implementation
4. Encountered Hugging Face authentication issues (401 Unauthorized)
5. Attempted scispaCy alternative — version mismatch (scispaCy 0.2.3 vs spaCy 3.8.16)
6. Attempted upgrade — build failures (blis, thinc, spaCy compilation errors)
7. Decided to document and proceed to linking/mapping

**What we learned:**
- **Dictionary baseline is strong** — F1 = 0.661 when evaluated correctly (not 0.097)
- **Model download issues** — Hugging Face requires authentication for some models (PubMedBERT, BioBERT)
- **scispaCy version mismatch** — Old scispaCy (0.2.3) incompatible with new spaCy (3.8.16)
- **Build issues** — spaCy/scispaCy upgrade requires compilation (blis, thinc) which fails on Windows

**Decision:** Proceed to entity linking and OMOP mapping without transformer NER.

**Rationale:**
1. Dictionary baseline already demonstrates key insights:
   - High precision (0.80) when entities are in vocabulary
   - Moderate recall (0.57) due to unseen entities
   - This motivates the need for terminology integration (linking/mapping)
2. Linking/mapping is the more novel contribution for this project
3. Transformer NER can be added later when model download issues are resolved

**Files Changed:**
- `src/ner/load_bc5cdr.py` — Fixed offset calculation
- `src/ner/evaluate_ner.py` — Use local_offset for gold entities
- `src/ner/transformer_ner.py` — Created but not validated (Hugging Face blocked)
- `src/ner/scispacy_ner.py` — Created but not validated (scispaCy version mismatch)
- `MANIFEST.md` — Updated with corrected baseline results
- `docs/sessions/2026-10-08_transformer-ner-blocked.md` — NEW (this file)

**Next Session:**
- Implement entity linking (candidate retrieval, ranking)
- Implement OMOP domain routing
- Demonstrate terminology integration (SNOMED-CT, ICD-10-CM, RxNorm)

**Session Duration:** ~3 hours
