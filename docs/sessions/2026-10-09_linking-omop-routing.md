## Session Log: 2026-10-09 — Entity Linking and OMOP Routing

**Type:** Implementation + Evaluation

**Goal:** Implement entity linking and OMOP domain routing

**What we did:**
1. Created `src/linking/entity_linking.py` — Maps entities to SNOMED-CT/RxNorm
2. Created `src/mapping/omop_routing.py` — Routes entities to OMOP tables
3. Fixed import path issues (sys.path.insert)
4. Fixed KeyError in route_to_omop (use .get() for optional keys)
5. Ran demo and full evaluation on test set

**What we learned:**
- **Entity linking works** — 785 entities linked (11.2% of 7,038 extracted)
- **Low linking rate expected** — Mock terminology has only ~20 concepts
- **OMOP routing is 100%** — All linked entities route successfully
- **Domain routing correct** — Chemicals → drug_exposure, Diseases → condition_occurrence

**Results:**
- Total extracted: 7,038
- Linked: 785 (11.2%)
- Unlinked: 6,253 (88.8%)
- Routed to OMOP: 785 (100% of linked)
- condition_occurrence: 465 (59.2%)
- drug_exposure: 320 (40.8%)

**Files Changed:**
- `src/linking/entity_linking.py` — NEW
- `src/mapping/omop_routing.py` — NEW
- `src/ner/dictionary_baseline.py` — Fixed import path
- `docs/sessions/2026-10-09_linking-omop-routing.md` — NEW (this file)

**Next Session:**
- FHIR representation (transform OMOP records to FHIR resources)
- Error decomposition (track errors through pipeline)
- Documentation (architecture.md, evaluation_protocol.md)

**Session Duration:** ~2 hours
