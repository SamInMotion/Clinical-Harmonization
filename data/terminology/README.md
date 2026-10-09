# Terminology Files

This directory contains standardized clinical terminologies for entity linking.

## Files

### bc5cdr_dictionary.json
- Built from BC5CDR training set
- 2,328 unique entity forms (after filtering)
- Used for dictionary baseline NER

### snomed_ct_subset.json (to be created)
- SNOMED-CT concepts relevant to BC5CDR
- Format: concept_id, term, type (Chemical/Disease)

### icd10cm_subset.json (to be created)
- ICD-10-CM codes relevant to BC5CDR
- Format: code, description, type

### rxnorm_subset.json (to be created)
- RxNorm drug concepts relevant to BC5CDR
- Format: rxcui, name, type

## Data Sources

### SNOMED-CT
- Source: IHTSDO Snowstorm API or UMLS
- License: IHTSDO license (requires registration)
- URL: https://snowstorm.ihtsdotools.org/snowstorm/snomed-ct

### ICD-10-CM
- Source: CDC/NCHS
- License: Public domain
- URL: https://www.cdc.gov/nchs/icd/icd10cm.html

### RxNorm
- Source: NLM
- License: Public domain
- URL: https://www.nlm.nih.gov/research/umls/rxnorm/docs/rel.html

## Usage

Entity linking maps extracted entities (e.g., "hypertensive") to standardized concepts:
- SNOMED-CT: 38341003 (Hypertensive disorder)
- ICD-10-CM: I10 (Essential hypertension)

This enables interoperability across systems and research studies.
