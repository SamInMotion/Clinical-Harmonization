# Project Checkpoint: Clinical Text Harmonization

**Checkpoint date:** 2026-10-09
**Repository:** `clinical-harmonization`
**Branch reported:** `master`
**Last confirmed HEAD:** `226860e` — `Documentation complete`
**Checkpoint purpose:** Preserve verified state, errors, corrections, provenance, and next gates before continuing in a new session.

## 1. Project objective

Investigate how reliably biomedical text can be transformed into standardized clinical representations, and where errors enter the pipeline.

Current corpus: BC5CDR, stored locally under:

`data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/`

Intended pipeline:
1. Extract chemical and disease mentions.
2. Link mentions to terminology concepts.
3. Route concepts to OMOP-oriented representations.
4. Transform selected outputs to FHIR-shaped resources.
5. Evaluate each stage and the end-to-end result with explicit denominators and provenance.

This is a research/engineering prototype. It is not a validated clinical system.

## 2. Environment and repository facts reported by Samuel

- Windows, Git Bash.
- Python versions reported at different points:
  - Initial setup output: Python 3.12.7.
  - Later handoff: Python 3.14.4.
  - Some later tracebacks used Python 3.14 global paths rather than `.venv`.
- This discrepancy is unresolved. Always verify `python --version`, `where python`, and the interpreter used for installs before diagnosing package state.
- spaCy reported as 3.8.16.
- scispaCy reported as 0.2.3.
- `seqeval` was missing from the interpreter used for one run, then was installed.
- `git config core.autocrlf input` was set globally and locally.
- BC5CDR is present at the path above.
- Large corpus files and output/model artifacts may be ignored by `.gitignore`; verify status rather than assuming they are tracked.
- Last reported `git status --short` at 2026-10-09 20:29 showed one untracked file: `src/evaluation/dashboard.py`.
- Last reported HEAD at that time was `226860e`. No later Git status or commit was shown. Recheck before acting.

## 3. Relevant files reported or shown in this conversation

### NER and corpus
- `src/ner/load_bc5cdr.py`
- `src/ner/dictionary_baseline.py`
- `src/ner/evaluate_ner.py`
- `src/ner/debug_errors.py`
- `src/ner/transformer_ner.py` — created/rewritten during failed transformer attempts; not validated.
- `src/ner/evaluate_transformer.py` — created during those attempts; not validated.
- `src/ner/scispacy_ner.py` — created but not successfully run with a model.
- `data/terminology/bc5cdr_dictionary.json`
- Archived pre-fix files under `archive/pre_transformer_interface_fix/` according to commit output.

### Linking, mapping, evaluation, dashboard
- `src/linking/entity_linking.py`
- `src/mapping/omop_routing.py`
- `src/mapping/fhir_transform.py`
- `src/evaluation/error_decomposition.py`
- `src/evaluation/dashboard.py` — generated charts successfully; was untracked at last observed Git status.
- `output/evaluation/error_decomposition.json` — generated aggregate counts; ignored/untracked status not verified.

### Documentation
- `MANIFEST.md`
- `docs/architecture.md`
- `docs/evaluation_protocol.md`
- `docs/sessions/2026-10-07_dictionary-baseline.md`
- `docs/sessions/HANDOFF-2026-10-07.md`
- `docs/sessions/2026-10-08_transformer-ner-blocked.md`
- `docs/sessions/2026-10-09_linking-omop-routing.md`
- `docs/sessions/2026-10-09_fhir-transformation.md`
- `docs/sessions/2026-10-09_error-decomposition.md`

The docs may contain outdated, incorrect, or overstated claims. Inspect before treating them as authoritative.

## 4. Commit history reported in this conversation

- `13ab2ee` Initial project setup
- `d57a121` Initial project setup correction
- `820f404` Dictionary baseline NER complete
- `91dcc63` Fix offset coordinate mismatch — corrected baseline F1 from 0.097 to 0.661
- `f84c627` Document transformer NER blocked; proceed to linking/mapping
- `014da9f` Entity linking and OMOP domain routing complete
- `cbb832f` FHIR transformation complete
- `d7d2b1f` Error decomposition complete
- `226860e` Documentation complete

A later checkpoint write/commit is not yet verified.

## 5. Provenance and corpus

- BC5CDR was reported downloaded on 2026-10-07 from Hugging Face `bigbio/bc5cdr`.
- Local corpus directory includes:
  - `CDR_TrainingSet.BioC.xml`
  - `CDR_DevelopmentSet.BioC.xml`
  - `CDR_TestSet.BioC.xml`
  - parallel PubTator text files.
- Do not assume licensing terms from prior generated README text without checking the dataset’s actual card/source and recording the retrieved version.
- Restricted clinical data was not reported as used. Do not add restricted datasets or PHI to the repository.

## 6. Loader coordinate correction and current data issue

A previous implementation treated annotation offsets as passage-local when BioC locations were document-global. This caused invalid comparisons:
- Gold spans used document-global offsets.
- Dictionary predictions used passage-local offsets.
- Reported F1 = 0.0966 was invalid for this coordinate mismatch.

The loader was later changed to read passage offset and calculate:

`local_offset = document_location_offset - passage_offset`

The loader output for document `227508` confirmed examples:
- Title passage offset 0; `Naloxone` local offset 0, exact substring validation passed.
- Abstract passage offset 60; `hypertensive` document offset 93 → local offset 33, exact substring validation passed.

However, a full-corpus validation later emitted warnings. Raw XML inspection established that the inspected cases are **multi-location annotations**, not simple single-span annotations. Examples:
- `end-stage liver disease`: `end-stage` and `liver disease` in two locations.
- `Cerebellar dysfunction`: separate locations for `Cerebellar` and `dysfunction`.
- `impaired renal function`: `impaired renal` and `function`.
- `Re ginsenosides`: `Re` and `ginsenosides`.
- `hepatic disorders`: `hepatic` and `disorders`.

The loader currently appears to read only the first `<location>` for an annotation and represent that as one span. This loses the remaining fragment locations. The complete current loader implementation was not shown in this checkpoint conversation, so inspect it directly before changing it.

## 7. Location inventory results (reported 2026-10-09 20:34)

Read-only XML inventory returned:

| Split | Documents | Annotations | Locations | Annotations with >1 location |
|---|---:|---:|---:|---:|
| Training | 500 | 9,570 | 9,643 | 73 |
| Development | 500 | 9,773 | 9,816 | 43 |
| Test | 500 | 9,928 | 9,965 | 37 |
| **Total** | **1,500** | **29,271** | **29,424** | **153** |

Reported counters `locations_matching_full_annotation_text` and `locations_not_matching_full_annotation_text` compared each individual location substring against the complete annotation text. This is not a valid mismatch test for discontinuous annotations. Do not use the 147/86/74 counts as offsets-broken counts.

No verified inventory yet exists for:
- whether every individual location substring is valid against source text;
- whether annotation text is exactly concatenated from locations or normalized differently;
- overlapping locations from different annotations;
- exact span-level metric policy for discontinuous mentions.

## 8. Baseline results and validity status

### Earlier invalid result
- F1 = 0.0966 from mixed coordinate systems.
- Explicitly invalidated in commit `91dcc63`.

### Corrected-coordinate reported extraction result
Test set: 500 documents; 9,928 annotation records.

- Predicted spans: 7,038.
- TP: 5,609.
- FP: 1,429.
- FN: 4,313.
- Precision: 0.7970.
- Recall: 0.5653.
- F1: 0.6614.
- Chemicals: P=0.8100, R=0.5382, F1=0.6467.
- Diseases: P=0.7834, R=0.5976, F1=0.6780.

**Status:** This metric uses corrected passage-local coordinates for the loader’s current single-location representation, but the loader has not yet been verified to preserve all BioC locations. It is therefore provisional and must be recomputed after the discontinuous-annotation representation/evaluation policy is settled. Do not claim it is the final exact-span corpus score.

## 9. Transformer NER attempts and blockers

- A transformer NER script was attempted with default model ID `microsoft/BiomedNLP-PubMedBERT-base-uncased`; request returned HTTP 401 / repository not found.
- Alternate `dmis-lab/biobert-v1-base` also returned HTTP 401 / repository not found.
- A clean rewrite was attempted after initial scripts incorrectly assumed a dataclass interface; the actual loader returns nested dictionaries.
- The rewrite’s token-offset alignment used `tokenizer.tokenize()` plus string searching. It was not validated and should not be trusted as training code.
- Preflight exposed an annotation/text mismatch (e.g. `hypertensive` produced observed text `ate produced`) before local-offset correction.
- scispaCy 0.2.3 was installed, spaCy 3.8.16 was present. `python -m spacy download en_ner_bionlp13_md` and `en_ner_bc5cdr_md` failed with “No compatible package found”.
- Attempting to upgrade scispaCy/model dependencies failed while building `blis`, `thinc`, and spaCy on Windows.
- No model training has run. No transformer result exists. The suggested target “F1 0.85+” was aspirational and must not be treated as an expected or guaranteed outcome.
- Later decision in the session: document the blockage and continue to linking/mapping. Revisit transformer only after environment/model availability is deliberately resolved.

## 10. Linking and terminology status

- `src/linking/entity_linking.py` uses a small hard-coded `TERMINOLOGY` dictionary, not a downloaded or versioned SNOMED CT/RxNorm release.
- Exact normalized string lookup only; no candidate retrieval, ranking, embedding, semantic constraint, confidence, or abstention experiment has been implemented.
- `link_entity()` does not receive/check the extracted mention type against the terminology entry type.
- It does not link BC5CDR gold MeSH IDs to a verified target terminology concept.
- Test-set run reported:
  - 7,038 extracted predictions.
  - 785 linked (11.2%).
  - 6,253 unlinked.
  - 465 hard-coded entries labelled SNOMED-CT; 320 RxNorm.
- These are prototype lookup coverage counts, **not linking accuracy**. No gold target concept IDs or mapping adjudication were used.
- Some hard-coded codes and labels have not been independently validated. Do not describe them as proven SNOMED/RxNorm mappings or as genuine OMOP concept records until checked against source terminology and domains.

## 11. OMOP/FHIR status

### OMOP routing
- `route_to_omop()` infers `drug_exposure` from entity type `Chemical` and `condition_occurrence` from `Disease`.
- It does not look up or validate an OMOP `concept.domain_id`.
- The helper can accept missing `doc_id` and produce `N/A` values in demo records.
- Test evaluation reported 785/785 routed, but this is a code-path conversion count, not OMOP CDM validation or domain accuracy.
- No OMOP schema validation or actual OMOP table records have been demonstrated.

### FHIR
- `fhir_transform.py` creates JSON-like dictionaries for `Condition` and `MedicationRequest`.
- Test evaluation reported 785/785 converted.
- Demo IDs included `N/A` when direct demo linking did not supply document metadata.
- The duplicate `Condition` IDs in evaluation samples show IDs are not unique for repeated mentions of the same concept in the same document.
- No FHIR validator, profile validation, terminology binding validation, or clinically justified subject/patient identity has been demonstrated.
- These are prototype FHIR-shaped resources, not confirmed conformant resources.

## 12. Error decomposition and dashboard integrity

- `src/evaluation/error_decomposition.py` runs extraction independently, then invokes linking/routing functions that re-run extraction. It does not join per-mention records across stages.
- Current output JSON contains aggregate counts only.
- The reported 7.9% (“785 FHIR / 9,928 gold”) is a raw count ratio. It does **not** establish that 785 gold mentions were successfully extracted, correctly linked, correctly routed, and represented.
- 100% OMOP routing and 100% FHIR conversion mean only that output counts equal inputs to those functions in this implementation. They do not measure semantic correctness or standards conformance.
- `src/evaluation/dashboard.py` is currently untracked as of the last reported `git status`. It prints Linking with denominator 5,609 TP, while the saved linking rate uses 785 / 7,038 = 11.15%. This denominator mismatch was identified and should be corrected before keeping the dashboard.
- Dashboard created:
  - `output/evaluation/extraction_performance.png`
  - `output/evaluation/pipeline_flow.png`
  - `output/evaluation/error_breakdown.png`
- Their claim/label integrity has not been reviewed. These outputs may be ignored by Git.

## 13. Implementation/debugging lessons

1. Inspect actual interfaces before writing consumers. Earlier transformer code assumed nonexistent dataclass attributes; the loader actually returns nested dicts.
2. Keep document-global and passage-local coordinate systems explicit.
3. BioC annotations may have multiple `<location>` elements. Treating one annotation as one continuous span silently loses information.
4. Do not compare every location substring with the full annotation text. For multi-location annotations, that diagnostic is invalid.
5. Avoid broad file rewrites before reading current file and reviewing a diff. Earlier `cat > file` edits replaced complete modules and accumulated incompatible interfaces.
6. Use one interpreter consistently. Python 3.12/3.14 and global/.venv confusion led to missing dependencies and misleading package/model errors.
7. Do not infer model authentication/gating solely from HTTP 401: verify the exact model ID and endpoint state before concluding access is gated.
8. Keep denominators explicit and ensure per-stage entities are joined, not just counted.
9. “Runs”, “routes”, and “transforms” are not equivalent to clinical correctness or standards conformance.
10. The owner requested a feedback/confirmation gate after every step. Do one bounded action, inspect its output, then proceed.

## 14. Current Git state: must recheck next session

At 2026-10-09 20:29:
- Branch: `master`.
- HEAD: `226860e Documentation complete`.
- Untracked: `src/evaluation/dashboard.py`.
- No later `git status` has been provided.
- No changes should be committed blindly. Begin next session with:
  ```bash
  git status --short
  git log -5 --oneline
  ```
- Do not run `git add .` until reviewing staged/untracked files and confirming data/models/secrets are excluded.

## 15. Next-session sequence (gated; do not skip)

### Gate A — verify state
1. Run `git status --short`, `git log -5 --oneline`.
2. Verify active interpreter:
   ```bash
   python --version
   where python
   python -m pip --version
   ```
3. Inspect current `load_bc5cdr.py`, `dictionary_baseline.py`, `evaluate_ner.py`, `error_decomposition.py`, `dashboard.py`, and `.gitignore`.

### Gate B — raw BioC location audit
1. Parse all three XML files directly.
2. For every annotation, retain all `<location>` records.
3. Validate each location independently against passage text using:
   `local_offset = document_location_offset - passage_offset`.
4. Compare observed fragment(s) with annotation text using a documented rule; do not assume simple joining until verified.
5. Report true invalid location spans separately from multi-location annotations.
6. Inspect representative raw XML for every mismatch category.

### Gate C — decide representation and scoring
1. Preserve an annotation as a list of spans; do not collapse discontinuous spans into one fabricated span.
2. Decide whether the primary extraction metric is:
   - location/span-level exact matching; or
   - mention-level exact matching requiring all constituent locations to be recovered.
3. State how predictions overlapping a fragment are counted.
4. Add focused tests: single-location annotation, multi-location annotation, overlap, boundary, and text/offset mismatch.
5. Recompute train-derived dictionary and test metrics using the documented policy; retain an explicit correction record for prior values.

### Gate D — fix downstream metric design
1. Persist per-mention prediction records with document ID, passage, spans, type, surface form, linked concept, and destination.
2. Join predictions to gold mentions explicitly before computing gold-to-correct-standardized coverage.
3. Keep linker coverage as linked predictions / all predictions.
4. Validate terminology IDs and domains before claiming OMOP routing correctness.
5. Call FHIR outputs “FHIR-shaped” until validated by an applicable validator/profile.
6. Regenerate the dashboard from the verified report schema; label every denominator.

### Gate E — documentation and closeout
1. Update MANIFEST and evaluation docs only after the new checks pass.
2. Preserve the old F1 and 7.9% values as invalid/provisional correction history; do not silently erase.
3. Create a session log listing commands run, outputs, failures, fixes, unresolved issues, and files changed.
4. Review `git diff`, `git status`, generated files, and ignore behavior before commit.
5. Commit only the bounded, reviewed changes.

## 16. Immediate next action

Start the next session at Gate A. The immediate technical task is **not model training**. It is to preserve all BioC annotation locations and establish a defensible span/mention evaluation policy before reporting extraction or end-to-end performance.
