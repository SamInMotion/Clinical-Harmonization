## Session Log: 2026-10-09 — Error Decomposition

**Type:** Implementation + Evaluation

**Goal:** Implement error decomposition (track errors through pipeline)

**What we did:**
1. Created `src/evaluation/error_decomposition.py` — Tracks errors through pipeline
2. Ran evaluation on test set
3. Documented error breakdown by stage

**What we learned:**
- **Extraction is the bottleneck** — 4,313 false negatives (43% of gold entities missed)
- **Linking is the major bottleneck** — Only 11.2% of predicted entities link (limited terminology)
- **OMOP and FHIR are lossless** — 100% routing and transformation rates
- **End-to-end survival is 7.9%** — Only 785 of 9,928 gold entities survive as FHIR resources

**Results:**
- Extraction: P=0.797, R=0.565 (5,609 TP, 1,429 FP, 4,313 FN)
- Linking: 785 linked (11.2% of 7,038 predicted)
- OMOP Routing: 785 routed (100% of linked)
- FHIR Transformation: 785 resources (100% of OMOP)
- End-to-end survival: 7.9% (785 FHIR / 9,928 gold)

**Files Changed:**
- `src/evaluation/error_decomposition.py` — NEW
- `output/evaluation/error_decomposition.json` — NEW
- `docs/sessions/2026-10-09_error-decomposition.md` — NEW (this file)

**Next Session:**
- Documentation (architecture.md, evaluation_protocol.md)
- Dashboard (visualize results)
- MANIFEST.md update with error decomposition results

**Session Duration:** ~1 hour
