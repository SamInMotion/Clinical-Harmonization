# Handoff: Clinical Harmonization Project

**Handoff date:** 2026-10-09  
**Repository:** `clinical-harmonization`  
**Branch:** `master` (last reported)  
**Checkpoint commit:** `b27abb2` — `docs: add clinical harmonization session checkpoint`  
**Next session mode:** Gate A verification, then BioC annotation audit  
**Do not begin with:** model training, broad rewrites, dashboard edits, or new clinical claims

## 1. Start here

Read this handoff and then inspect the committed checkpoint:

`docs/sessions/CHECKPOINT-2026-10-09.md`

The checkpoint is committed at `b27abb2`. It records project history, known limitations, previous errors, commands/results reported, and a proposed gated next-session sequence. Treat it as a handoff record, not as proof that every described current-state fact remains true.

Before changing anything, run:

```bash
git status --short
git log -5 --oneline
python --version
where python
python -m pip --version
```

Last reported Git state after checkpoint commit:

```text
HEAD: b27abb2
Untracked: src/evaluation/dashboard.py
```

That status must be rechecked. Keep the untracked dashboard separate unless Samuel explicitly decides what to do with it. Do not use `git add .`.

## 2. Project objective and scope

The project investigates how reliably biomedical text can be transformed into standardized clinical representations and where errors enter the pipeline.

Primary corpus: BC5CDR BioC XML at:

`data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/`

Intended stages:
1. Chemical/disease mention extraction.
2. Terminology linking.
3. OMOP-oriented routing/representation.
4. FHIR representation.
5. Stage-wise and end-to-end evaluation with explicit denominators.

This is currently a prototype. It is not a validated clinical system. Current hard-coded terminology and conversion code do not establish clinical correctness, OMOP CDM validity, or FHIR conformance.

## 3. Current reported project state

### Implemented or attempted
- BioC XML loader: `src/ner/load_bc5cdr.py`
- Dictionary NER: `src/ner/dictionary_baseline.py`
- Extraction evaluation: `src/ner/evaluate_ner.py`
- Linking: `src/linking/entity_linking.py`
- OMOP routing prototype: `src/mapping/omop_routing.py`
- FHIR-shaped output prototype: `src/mapping/fhir_transform.py`
- Aggregate error decomposition: `src/evaluation/error_decomposition.py`
- Transformer scripts were attempted but not validated.
- scispaCy evaluation script was attempted but no model ran.
- `src/evaluation/dashboard.py` generated charts successfully, but was untracked at last reported status.

### Last reported tracked HEAD/history
- `b27abb2` checkpoint commit
- `226860e` documentation complete
- `d7d2b1f` error decomposition complete
- `cbb832f` FHIR transformation complete
- `014da9f` entity linking and OMOP routing complete

Recheck actual history in the next session.

## 4. Critical data/loader finding

The loader was changed after discovering that BioC location offsets are document-global while each passage’s text is passage-local:

`local_offset = document_location_offset - passage_offset`

A sample from document `227508` validated this conversion:
- Abstract passage offset: 60
- `hypertensive` document offset: 93
- Passage-local offset: 33
- Passage text slice at local offset matched the annotation fragment.

However, later all-split inspection found multi-location annotations. The loader appears to use only the first `<location>` for an annotation, so it loses additional spans.

Raw XML examples inspected:
- `end-stage liver disease`: locations for `end-stage` and `liver disease`.
- `Cerebellar dysfunction`: locations for `Cerebellar` and `dysfunction`.
- `impaired renal function`: locations for `impaired renal` and `function`.
- `Re ginsenosides`: locations for `Re` and `ginsenosides`.
- `hepatic disorders`: locations for `hepatic` and `disorders`.

### Inventory reported on 2026-10-09
| Split | Documents | Annotations | Locations | Annotations with multiple locations |
|---|---:|---:|---:|---:|
| Training | 500 | 9,570 | 9,643 | 73 |
| Development | 500 | 9,773 | 9,816 | 43 |
| Test | 500 | 9,928 | 9,965 | 37 |
| Total | 1,500 | 29,271 | 29,424 | 153 |

A prior diagnostic compared each location substring with the *entire* annotation text. Its “not matching full annotation text” counts (147/86/74) are not valid mismatch counts for multi-location annotations. Do not repeat that test or cite those counts as broken offsets.

No verified all-location substring audit or mention-level scoring policy exists yet.

## 5. Metrics: correction and current validity

### Invalid historical result
A previously reported F1 = 0.0966 compared document-global gold offsets to passage-local predicted offsets. It was invalid and was explicitly corrected in commit `91dcc63`.

### Provisional corrected-coordinate dictionary score
Reported test-set figures:
- Gold annotation records: 9,928.
- Predicted spans: 7,038.
- TP: 5,609.
- FP: 1,429.
- FN: 4,313.
- Precision: 0.7970.
- Recall: 0.5653.
- F1: 0.6614.
- Chemicals F1: 0.6467.
- Diseases F1: 0.6780.

These results use a loader representation that appears to take one location per annotation. They are **provisional** until all locations are preserved and a scoring policy for discontinuous annotations is documented. Do not repeat them as final exact-span corpus performance.

### Invalid end-to-end interpretation
The reported `785 / 9,928 = 7.9%` is only a raw count ratio. Existing code does not join each FHIR output to a gold mention and verify that the standardized concept is correct. It is not a valid “fraction of gold entities correctly standardized” metric.

The reported 100% OMOP routing and FHIR conversion are function pass-through counts, not semantic accuracy, OMOP CDM validation, or FHIR conformance.

## 6. Linking, OMOP, and FHIR limits

- Linker uses a small hard-coded terminology dictionary, exact normalized lookup only.
- It does not validate a mention’s extracted type against the terminology type/domain.
- It does not map BC5CDR gold MeSH IDs to verified target vocabulary concepts.
- Reported 785 linked / 7,038 predictions = 11.15% prototype lookup coverage, not linking accuracy.
- OMOP routing uses the mention type to choose `drug_exposure` or `condition_occurrence`; it does not validate a concept’s actual OMOP domain.
- FHIR code creates JSON-like `Condition` and `MedicationRequest` resources, but there is no reported validator/profile check.
- Duplicate resource IDs occurred for repeated same-concept mentions in a document.
- Do not claim standards compliance or clinically valid output without new validation evidence.

## 7. Transformer/model setup history

No model training has run.

Reported blockers:
- `microsoft/BiomedNLP-PubMedBERT-base-uncased` download returned HTTP 401 / repository-not-found response.
- `dmis-lab/biobert-v1-base` returned the same class of response.
- This does not by itself prove the repositories are gated; exact model IDs and current access need verification before drawing that conclusion.
- scispaCy 0.2.3 with spaCy 3.8.16 could not load the named models.
- Upgrade/build attempt failed compiling `blis`, `thinc`, and spaCy on Windows.
- Transformer token alignment code was not validated; do not reuse as trusted training code.
- Python interpreter discrepancy: Python 3.12.7 initially, Python 3.14.4 later, with some package installs/tracebacks apparently using global Python rather than `.venv`.

Do not resume transformer work until the active interpreter and model access strategy have been explicitly checked.

## 8. Immediate next-session gates

### Gate A — current-state verification
1. Run the Git and Python commands in section 1.
2. Inspect:
   - `src/ner/load_bc5cdr.py`
   - `src/ner/dictionary_baseline.py`
   - `src/ner/evaluate_ner.py`
   - `src/evaluation/error_decomposition.py`
   - `src/evaluation/dashboard.py`
   - `.gitignore`
   - `MANIFEST.md`
   - `docs/evaluation_protocol.md`
3. Do not edit until the actual code and status are inspected.

### Gate B — BioC locations audit
Use direct XML parsing to retain every `<location>` for each annotation.
For each location:
- compute passage-local offset from document offset minus passage offset;
- compare the location slice with the corresponding annotation fragment under a documented rule;
- keep multi-location annotations as multiple spans;
- report genuine out-of-bounds or substring errors separately from expected multi-location behavior.
Inspect representative raw XML for every remaining anomaly.
Do not assume that joining location fragments reconstructs the annotation text without checking corpus behavior.

### Gate C — representation and metric policy
Before changing the loader/evaluator, decide and document:
- whether predictions and gold are scored as individual location spans or complete annotation mentions;
- how multiple/discontinuous locations are represented;
- how entity type is included in matching;
- how overlaps and partial fragment matches count;
- whether a relaxed/overlap metric is secondary to exact matching.

Add focused tests for:
- single-location annotation;
- multi-location annotation;
- multiple annotations sharing/overlapping text;
- passage-local offset conversion;
- annotation/location boundary errors.

Then recompute dictionary results. Record corrections without deleting the invalid/provisional historical values.

### Gate D — downstream evaluation integrity
Create or persist per-mention records before computing linked/gold-to-correct-standardized coverage. Match across stages using stable identity (document, passage, location set/span, type, and concept as applicable), not aggregate counts alone.
Keep these separate:
- extraction metrics;
- predicted mention terminology coverage;
- gold-to-correct-concept accuracy/coverage;
- domain/routing checks;
- structural serialization checks;
- standards-conformance validation.

### Gate E — closeout
Update documentation only after checks are run and reviewed.
Before commit:
```bash
git status --short
git diff --check
git diff
```
Stage only the intended files. Do not stage the untracked dashboard accidentally. Record exact command, scope, outputs, errors, fixes, and unresolved items in the session log.

## 9. Process requirements for the next chat

- Begin with Gate A, not code generation.
- Use one bounded change/check at a time; Samuel will provide its output before proceeding.
- Do not assume paths, file contents, imports, Python environment, package versions, model IDs, data schema, or current Git state.
- Inspect the real interface before writing callers.
- After any failure, classify it, inspect actual inputs/code, and identify root cause before proposing a patch.
- Avoid replacing whole files with `cat >` unless the current file has been inspected and the intended complete rewrite is justified. Prefer a minimal diff, then review it.
- No “perfect”, “fully valid”, “correct”, “complete”, “production-ready”, or standards-compliant claims without a stated verification scope.
- Preserve all result corrections and their provenance.
- User requested feedback/confirmation gates after each step.

## 10. First message for the next session

“I have read the committed handoff and checkpoint. I will not edit code yet. First, please run the Gate A Git/interpreter verification commands and share their exact output. We will then inspect the current files before deciding the smallest next action.”
