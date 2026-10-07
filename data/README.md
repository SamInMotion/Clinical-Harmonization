# Data Directory

**Purpose:** Store raw and processed data for the clinical harmonization project.

---

## Directory Structure

data/
├── raw/
│ └── CDR_Data/ # BC5CDR corpus (CDR_TrainingSet, CDR_DevelopmentSet, CDR_TestSet)
├── processed/
│ └── [processed datasets]
├── terminology/
│ ├── snomed/ # SNOMED-CT terminology
│ ├── icd10cm/ # ICD-10-CM codes
│ ├── rxnorm/ # RxNorm drug terminology
│ └── loinc/ # LOINC laboratory codes
└── synthetic_fhir/ # Synthetic FHIR resources

text


---

## BC5CDR Download

**Source:** Hugging Face (`bigbio/bc5cdr`)  
**License:** CC-BY 3.0  
**Citation:** Li et al. (2016), DOI: 10.1093/database/baw068

### Current location

data/raw/CDR_Data/
├── CDR_TrainingSet/ # 500 PubMed abstracts (BioC XML format)
├── CDR_DevelopmentSet/ # 500 PubMed abstracts (BioC XML format)
├── CDR_TestSet/ # 500 PubMed abstracts (BioC XML format)
└── [other files]

Total: 1,500 abstracts with chemical and disease annotations.

---

## Verify download

```python
import os

# Count files
bc5cdr_dir = "data/raw/CDR_Data"
train_files = len([f for f in os.listdir(os.path.join(bc5cdr_dir, "CDR_TrainingSet")) if f.endswith(".BioC.XML")])
dev_files = len([f for f in os.listdir(os.path.join(bc5cdr_dir, "CDR_DevelopmentSet")) if f.endswith(".BioC.XML")])
test_files = len([f for f in os.listdir(os.path.join(bc5cdr_dir, "CDR_TestSet")) if f.endswith(".BioC.XML")])

print(f"Training: {train_files} files")
print(f"Development: {dev_files} files")
print(f"Test: {test_files} files")
print(f"Total: {train_files + dev_files + test_files} files (expected: 1500)")
```

Expected output:
- Training: 500 files
- Development: 500 files
- Test: 500 files
- Total: 1500 files

---

## Terminology Downloads

### SNOMED-CT

**Source:** IHTSDO Snowstorm or UMLS  
**License:** IHTSDO license (requires registration)  
**Note:** For this project, use a subset or UMLS-derived SNOMED-CT concepts

### ICD-10-CM

**Source:** CDC/NCHS  
**License:** Public domain  
**URL:** `https://www.cdc.gov/nchs/icd/icd10cm.html`

### RxNorm

**Source:** NLM  
**License:** Public domain  
**URL:** `https://www.nlm.nih.gov/research/umls/rxnorm/docs/rel.html`

### LOINC

**Source:** Regenstrief Institute  
**License:** LOINC license (requires agreement)  
**URL:** `https://loinc.org/use/loinc-tables`

---

## Data Provenance

See `MANIFEST.md` for complete data source inventory and `docs/terminology_versions.md` for specific terminology releases used in experiments.

---

## Restricted Data

**Important:** No restricted clinical data (e.g., n2c2, MIMIC-III) will be committed to this repository. If such data is used locally under DUA, it must remain in a separate, non-committed directory and never appear in public outputs.

---

**Last updated:** 2026-10-07
