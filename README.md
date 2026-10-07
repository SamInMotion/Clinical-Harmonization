# Reliable Clinical Text Harmonization

**Version:** 0.1.0  
**Status:** Initial setup  
**Last updated:** 2026-10-07

---

## Research Question

> How reliably can biomedical text be transformed into standardized clinical concepts and interoperable clinical data, and where do errors enter that transformation?

---

## Overview

This project investigates the reliability of clinical text harmonization pipelines through controlled ablations. It quantifies how extraction quality, vocabulary coverage, candidate retrieval, semantic constraints, and abstention jointly determine the correctness of standardized OMOP/FHIR representations.

**Primary corpus:** BC5CDR (BioCreative V Chemical-Disease Relation)  
**Secondary:** Synthetic FHIR records, LOINC laboratory mapping data

---

## Pipeline Architecture

[200~Raw text (BC5CDR)
↓
NER (dictionary baseline vs transformer)
↓
Entity mentions
↓
Candidate retrieval (exact → lexical → fuzzy → embedding → reranking)
↓
Domain/semantic filtering
↓
Abstain or accept mapping
↓
Standardized concept (SNOMED-CT, ICD-10-CM, RxNorm, LOINC)
↓
OMOP representation (NOTE_NLP) / FHIR representation
↓
Evaluation + error decomposition~

---

## Key Experiments

| Experiment | Research Question |
|------------|-------------------|
| E01: Extraction baseline | How accurately can dictionary methods extract chemicals/diseases? |
| E02: Transformer NER | Does fine-tuned biomedical transformer improve extraction? |
| E03: Vocabulary coverage | How much of gold-standard entity set can available terminology represent? |
| E04: Matching strategies | How do exact, lexical, fuzzy, semantic retrieval compare? |
| E05: Forced vs abstaining | What is the cost of forcing every entity to map? |
| E06: Domain constraints | How many errors does domain filtering prevent? |

---

## Installation

```bash
# Clone repository
git clone <repository-url>
cd clinical-harmonization

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install dependencies
pip install -r requirements.txt

# Download data (BC5CDR)
# See data/README.md for download instructions
```

---

## Data

| Dataset | Source | License | Location |
|---------|--------|---------|----------|
| BC5CDR | Hugging Face (`bigbio/bc5cdr`) | CC-BY 3.0 | `data/raw/bc5cdr/` |
| SNOMED-CT | IHTSDO | IHTSDO license | `data/terminology/snomed/` |
| ICD-10-CM | CDC/NCHS | Public domain | `data/terminology/icd10cm/` |
| RxNorm | NLM | Public domain | `data/terminology/rxnorm/` |
| LOINC | Regenstrief | LOINC license | `data/terminology/loinc/` |

**Note:** See `MANIFEST.md` for complete data provenance and `docs/terminology_versions.md` for specific terminology releases used.

---

## Usage

```bash
# Run NER evaluation
python src/ner/evaluate_ner.py

# Run linking experiments
python src/linking/evaluate_linking.py

# Run full pipeline with error decomposition
python src/evaluation/error_decomposition.py
```

---

## Documentation

- **Architecture:** `docs/architecture.md`
- **Evaluation protocol:** `docs/evaluation_protocol.md`
- **Terminology versions:** `docs/terminology_versions.md`
- **Session logs:** `docs/sessions/`
- **Architecture decisions:** `docs/decisions/`

---

## Citation

If you use this code or methodology, please cite:

```bibtex
@article{DBLP:journals/biodb/LiSJSWLDMWL16,
  author = {Jiao Li and Yueping Sun and Robin J. Johnson and Daniela Sciaky and Chih{-}Hsuan Wei and Robert Leaman and Allan Peter Davis and Carolyn J. Mattingly and Thomas C. Wiegers and Zhiyong Lu},
  title = {BioCreative {V} {CDR} task corpus: a resource for chemical disease relation extraction},
  journal = {Database J. Biol. Databases Curation},
  volume = {2016},
  year = {2016},
  url = {[https://doi.org/10.1093/database/baw068](https://doi.org/10.1093/database/baw068)},
  doi = {10.1093/database/baw068}
}
```

---

## License

[To be determined — MIT or Apache-2.0]

---

## Contact

Samuel Okoe-Mensah  
[GitHub profile link]

---

**Last verified:** 2026-10-07
