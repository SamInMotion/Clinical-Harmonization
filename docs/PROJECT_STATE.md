# Project State Register — Clinical Harmonization

**Purpose:** Canonical current-state register for this repository. Read this before making changes. Update the relevant sections at every session closeout.

**Last updated:** 2026-10-10  
**Maintainer:** Samuel Okoe-Mensah  
**Status:** Active prototype; not a validated clinical system

---

## 1. Status snapshot

| Item | Current verified state | Last verified |
|---|---|---|
| Repository | `clinical-harmonization` | 2026-10-10 |
| Branch | `master` | 2026-10-10 |
| HEAD before this register | `95ca969` — `docs: add gated project handoff` | 2026-10-10 |
| Checkpoint anchor | `b27abb2` — `docs: add clinical harmonization session checkpoint` | 2026-10-10 |
| Working tree | Clean except untracked `src/evaluation/dashboard.py` | 2026-10-10 |
| Dashboard | Untracked; not part of committed project state | 2026-10-10 |
| Active Python | Global Python 3.14.4 (`C:\Users\samue.KITAB\AppData\Local\Programs\Python\Python314\python.exe`) | 2026-10-10 |
| Project virtual environment | `.venv/` exists and was created with Python 3.14.4 | 2026-10-10 |
| Active interpreter caveat | Shell `python` resolves to global Python, not necessarily `.venv\Scripts\python.exe` | 2026-10-10 |
| Test suite | `tests/golden/test_ner.py` contains placeholder tests only; no executable NER regression coverage | 2026-10-10 |

**Environment rule:** Use `.venv/Scripts/python.exe` explicitly until shell activation is verified. Do not assume `python` refers to the project virtual environment.

---

## 2. Project scope

The project investigates whether biomedical text can be transformed reliably into standardized clinical representations and where errors enter the pipeline.

Intended stages:

1. Chemical/disease mention extraction.
2. Terminology linking.
3. OMOP-oriented routing/representation.
4. FHIR-shaped serialization.
5. Stage-wise and end-to-end evaluation with explicit denominators.

Primary corpus: BC5CDR BioC XML at `data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/`.

This is a prototype. Current hard-coded terminology, conversion logic, and pass-through counts do not establish clinical correctness, OMOP CDM validity, FHIR conformance, or end-to-end semantic accuracy.

---

## 3. Verified component state

| Component | Path | Current state | Gate C impact |
|---|---|---|---|
| BioC loader | `src/ner/load_bc5cdr.py` | Reads only the first `<location>` per annotation | Must preserve all locations |
| Dictionary NER | `src/ner/dictionary_baseline.py` | Extracts predictions from passage text; does not consume gold annotations | No functional change required |
| NER evaluator | `src/ner/evaluate_ner.py` | Builds one gold entity per annotation; uses full annotation-text length; excludes entity type from match key | Must use location-level gold spans and type-aware matching |
| Debug utility | `src/ner/debug_errors.py` | Displays annotation metadata; not evaluation-critical | No change required |
| scispaCy evaluator | `src/ner/scispacy_ner.py` | Duplicates flawed gold construction and type-blind matching | Must be updated consistently |
| Transformer NER | `src/ner/transformer_ner.py` | Builds BIO labels from annotation-level offset/length; uses only first location implicitly | Must label every location |
| Transformer evaluator | `src/ner/evaluate_transformer.py` | Broken/stale: imports nonexistent symbols from `evaluate_ner`; expects `doc.all_entities` | Do not modify in Gate C; record as blocked |
| Entity linking | `src/linking/entity_linking.py` | Re-extracts predicted mentions from passage text; does not consume gold annotations | No functional change required |
| OMOP routing | `src/mapping/omop_routing.py` | Routes prediction-derived linked entities by mention type | No functional change required |
| FHIR transformation | `src/mapping/fhir_transform.py` | Transforms OMOP records derived from predictions | No functional change required |
| Error decomposition | `src/evaluation/error_decomposition.py` | Duplicates evaluator gold construction and type-blind matching | Must use location-level gold spans and type-aware matching |
| Dashboard | `src/evaluation/dashboard.py` | Untracked; reads `output/evaluation/error_decomposition.json` | Do not treat as committed project state |

---

## 4. Dependency map

```text
load_bc5cdr()
├── dictionary_baseline.py
│   └── builds terminology dictionary from annotation text/type/mesh_id
├── evaluate_ner.py
│   └── builds gold entities and exact-span metrics  [GATE C: UPDATE]
├── debug_errors.py
│   └── displays annotations; non-evaluation-critical
├── scispacy_ner.py
│   └── builds gold entities and exact-span metrics  [GATE C: UPDATE]
├── transformer_ner.py
│   └── builds BIO labels from annotation spans       [GATE C: UPDATE]
├── evaluate_transformer.py
│   └── broken/stale; imports nonexistent evaluator symbols [BLOCKED]
├── entity_linking.py
│   └── extracts predictions from passage text; no gold-annotation dependency
├── omop_routing.py
│   └── routes prediction-derived linked entities
├── fhir_transform.py
│   └── transforms OMOP records derived from predictions
└── error_decomposition.py
    └── builds gold entities and extraction metrics   [GATE C: UPDATE]
```

**Compatibility rule:** Preserve existing annotation-level fields (`text`, `type`, `mesh_id`, first-location `offset`, `local_offset`, `length`) while adding a complete `locations` list. This minimizes breakage in display/debug code while enabling location-level evaluation.

---

## 5. BioC location audit

**Audit date:** 2026-10-10  
**Scope:** All 1,500 documents; 29,271 annotations; 29,424 `<location>` elements across training, development, and test splits.

| Split | Documents | Annotations | Locations | Two-location annotations | Exact full-text location matches | Valid multi-location fragments | Genuine anomalies | Out-of-bounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Training | 500 | 9,570 | 9,643 | 73 | 9,496 | 146 | 1 | 0 |
| Development | 500 | 9,773 | 9,816 | 43 | 9,730 | 85 | 1 | 0 |
| Test | 500 | 9,928 | 9,965 | 37 | 9,891 | 74 | 0 | 0 |
| **Total** | **1,500** | **29,271** | **29,424** | **153** | **29,117** | **305** | **2** | **0** |

### Established findings

- Every multi-location annotation has exactly two locations.
- The current loader reads only the first location, losing 153 valid gold spans corpus-wide.
- Passage-local conversion (`document_offset - passage_offset`) produced zero out-of-bounds locations.
- The earlier 307 “mismatches” were mostly expected fragment behavior: 305 valid fragments plus two genuine anomalies.
- Do not compare an individual location slice with the entire annotation text for multi-location annotations.

### Corpus exceptions

| ID | Split / document | Issue | Policy |
|---|---|---|---|
| CE-001 | Training / `15863244` | Annotation `midline (MD) defects`; location slice is `d midline (MD) defec`, indicating a source offset/length irregularity | Retain as-is; count and document; do not silently alter source XML |
| CE-002 | Development / `6415512` | Annotation `atypical absence seizures`; first location slice is ` atypical absenc`; annotation text is not contiguous in passage | Retain as-is; count and document; do not silently alter source XML |

---

## 6. Result register

### R-001: Historical dictionary NER F1

- **Value:** 0.0966
- **Status:** INVALID
- **Reason:** Compared document-global gold offsets with passage-local predicted offsets.
- **Correction provenance:** Corrected in commit `91dcc63`; recorded in `MANIFEST.md`.
- **Action:** Do not cite as project performance.

### R-002: Provisional dictionary NER F1

- **Value:** 0.6614
- **Precision:** 0.7970
- **Recall:** 0.5653
- **Status:** SUPERSEDED by R-006; retained as historical one-location-representation result
- **Dataset:** BC5CDR test set; 500 documents
- **Denominator:** 9,928 gold annotation records under one-location representation
- **Matching:** Exact span; document, passage type, offset, and length; entity type excluded
- **Known limitation:** Uses first BioC location only; multi-location annotations are misrepresented
- **Action:** Rerun after location-level gold spans and type-aware matching. Preserve this value as historical provenance.

### R-006: Gate C-2 dictionary NER F1

- **Value:** 0.6611
- **Precision:** 0.7981
- **Recall:** 0.5642
- **Status:** CURRENT under Gate C-2 policy
- **Date:** 2026-10-10
- **Dataset:** BC5CDR test set; 500 documents
- **Gold denominator:** 9,965 location-level gold spans
- **Predicted entities:** 7,038
- **Matching:** Exact match on document ID, passage type, passage-local offset, location length, and entity type
- **Confusion matrix:** TP 5,617; FP 1,421; FN 4,339
- **Chemical results:** Precision 0.8103; recall 0.5380; F1 0.6466; TP 2,904; FP 680; FN 2,494
- **Disease results:** Precision 0.7855; recall 0.5952; F1 0.6772; TP 2,713; FP 741; FN 1,845
- **Evidence:** `output/evaluation/evaluate_ner_gate_c2_2026-10-10.txt`
- **Scope limitation:** Exact span matching only; no semantic correctness, terminology-linking accuracy, OMOP validity, or FHIR conformance claim
- **Supersedes:** R-002 for current reporting

### R-003: Linking coverage

- **Value:** 785 linked / 7,038 predictions = 11.15%
- **Status:** PROTOTYPE COVERAGE, NOT LINKING ACCURACY
- **Reason:** Uses a small hard-coded terminology dictionary and exact normalized lookup.
- **Action:** Do not describe as linking accuracy or correctness.

### R-004: OMOP routing and FHIR conversion

- **Values:** 785 routed / 785 linked = 100%; 785 FHIR resources / 785 OMOP records = 100%
- **Status:** FUNCTION PASS-THROUGH COUNTS
- **Reason:** Routing uses mention type; FHIR transformation creates JSON-like resources. Neither validates semantic correctness, OMOP CDM validity, or FHIR conformance.
- **Action:** Do not describe as standards compliance or clinical validity.

### R-005: End-to-end survival

- **Value:** 785 / 9,928 = 7.9%
- **Status:** INVALID AS A CORRECTNESS METRIC
- **Reason:** Raw count ratio; does not join FHIR output to gold mentions or verify standardized-concept correctness.
- **Action:** Replace with per-mention join and explicit gold-to-correct-standardized-concept evaluation before making any end-to-end accuracy claim.

---

## 7. Documentation reconciliation

| Document claim | Verified reality | Required action |
|---|---|---|
| `MANIFEST.md`: dashboard “Not created” | `src/evaluation/dashboard.py` exists but is untracked | Reconcile only after deciding its committed status |
| `MANIFEST.md`: OMOP routing and FHIR transformation “Not created” | Prototype scripts exist | Reconcile after verification |
| `docs/evaluation_protocol.md`: “Survival rate” | Raw FHIR-resource/gold-entity count ratio | Rename or redefine; do not imply correctness |
| `docs/evaluation_protocol.md`: OMOP/FHIR “None — 100%” errors | Pass-through counts, not validation | Reword; no conformance claim |
| `docs/evaluation_protocol.md`: exact match definition | Current key excludes entity type | Update after Gate C matching policy is implemented |
| `docs/evaluation_protocol.md`: NER results | Based on one-location gold representation | Mark provisional; replace after Gate C rerun |

---

## 8. Approved decisions

### D-001: Location-level gold representation

**Approved:** 2026-10-10  
**Decision:** Use one gold span per BioC `<location>`. Preserve annotation-level text, MeSH ID, and provenance.  
**Scope:** NER evaluation, error decomposition, scispaCy evaluation, and transformer BIO labeling.

### D-002: Type-aware exact matching

**Approved:** 2026-10-10  
**Decision:** A prediction matches gold only when document ID, passage type, passage-local offset, location length, and entity type all match.  
**Scope:** Primary exact-span metric.

### D-003: Corpus anomalies are retained

**Approved:** 2026-10-10  
**Decision:** Do not modify source BioC XML. Retain, count, and document CE-001 and CE-002.  
**Scope:** All current and future corpus audits.

### D-004: Historical results remain provenance

**Approved:** 2026-10-10  
**Decision:** Do not delete invalid or provisional historical results. Label their validity, limitation, and replacement condition.  
**Scope:** All metric reporting and documentation.

---

## 9. Next gated actions

### Gate C-1: Preserve all BioC locations

**Status:** APPROVED, NOT IMPLEMENTED  
**Scope:** `src/ner/load_bc5cdr.py` and focused tests only.  
**Requirement:** Preserve existing annotation-level fields for backward compatibility; add a complete `locations` list containing document offset, passage-local offset, length, and observed text.  
**Acceptance evidence:** Tests pass for single-location, two-location, offset conversion, annotation metadata, and known corpus anomalies.

### Gate C-2: Location-level evaluation

**Status:** IMPLEMENTED; tests passed; baseline rerun on 2026-10-10
**Scope:** `evaluate_ner.py`, `error_decomposition.py`, and `scispacy_ner.py`.  
**Requirement:** One gold entity per location; use location-specific offset/length; include entity type in match key.  
**Acceptance evidence:** Focused tests pass; dictionary baseline is rerun; new result recorded as a correction with provenance.

### Gate C-3: Transformer location labeling

**Status:** APPROVED, NOT IMPLEMENTED  
**Scope:** `transformer_ner.py` BIO-label construction and focused tests only.  
**Requirement:** Iterate all annotation locations when assigning BIO labels.  
**Acceptance evidence:** Synthetic two-location BIO test passes. This does not establish model, tokenizer-alignment, or training readiness.

### Blocked / out of scope

- `evaluate_transformer.py`: broken imports and incompatible `doc.all_entities` interface; do not modify during Gate C.
- Transformer training, model access, tokenizer alignment, and training-run validation: separate gates.
- Dashboard staging/committing: separate decision; remains untracked.
