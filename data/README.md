# Data Directory

**Purpose:** Store raw and processed data for the clinical harmonization project.

---

## Directory Structure

data/
├── raw/
│ └── bc5cdr/
│ └── CDR_Data/
│ └── CDR.Corpus.v010516/
│ ├── CDR_TrainingSet.BioC.xml # 500 abstracts
│ ├── CDR_DevelopmentSet.BioC.xml # 500 abstracts
│ ├── CDR_TestSet.BioC.xml # 500 abstracts
│ ├── CDR_TrainingSet.PubTator.txt # Alternative format
│ ├── CDR_DevelopmentSet.PubTator.txt
│ └── CDR_TestSet.PubTator.txt
├── processed/
│ └── [processed datasets]
├── terminology/
│ ├── snomed/ # SNOMED-CT terminology
│ ├── icd10cm/ # ICD-10-CM codes
│ ├── rxnorm/ # RxNorm drug terminology
│ └── loinc/ # LOINC laboratory codes
└── synthetic_fhir/ # Synthetic FHIR resources

---

## BC5CDR Corpus

**Source:** Hugging Face (`bigbio/bc5cdr`)  
**License:** CC-BY 3.0  
**Citation:** Li et al. (2016), DOI: 10.1093/database/baw068

### Format

BioC XML format with:
- `<document>`: One PubMed abstract
- `<passage>`: Title or abstract text
- `<annotation>`: Entity mention with:
  - `type`: Chemical or Disease
  - `MESH`: MeSH identifier
  - `location offset` and `length`: Span in text
  - `text`: Entity mention

### Statistics

| Split | Abstracts | Chemicals | Diseases | Relations |
|-------|-----------|-----------|----------|-----------|
| Training | 500 | ~1,470 | ~1,940 | ~1,040 |
| Development | 500 | ~1,470 | ~1,940 | ~1,040 |
| Test | 500 | ~1,469 | ~1,938 | ~1,036 |
| **Total** | **1,500** | **4,409** | **5,818** | **3,116** |

---

## Loading BC5CDR

### Using bioc library (recommended)

```python
from bioc import biocxml

# Load training set
with open("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TrainingSet.BioC.xml") as f:
    collection = biocxml.load(f)

# Iterate over documents
for doc in collection:
    print(f"Document ID: {doc.id}")
    for passage in doc.passages:
        print(f"  Passage type: {passage.infons['type']}")
        print(f"  Text: {passage.text[:100]}...")
        for ann in passage.annotations:
            print(f"    Entity: {ann.text} ({ann.infons['type']}) - MESH: {ann.infons.get('MESH', 'N/A')}")
```

### Manual XML parsing

```python
import xml.etree.ElementTree as ET

tree = ET.parse("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TrainingSet.BioC.xml")
root = tree.getroot()

for doc in root.findall('document'):
    doc_id = doc.find('id').text
    for passage in doc.findall('passage'):
        passage_type = passage.find('infon').text
        passage_text = passage.find('text').text
        for ann in passage.findall('annotation'):
            entity_type = ann.find('infon').text
            mesh_id = ann.find('infon[@key="MESH"]').text
            entity_text = ann.find('text').text
            print(f"{doc_id}: {entity_text} ({entity_type}) - MESH: {mesh_id}")
```

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
