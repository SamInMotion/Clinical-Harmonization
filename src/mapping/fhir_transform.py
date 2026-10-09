"""
FHIR representation for BC5CDR.

Transforms OMOP records to FHIR resources (Condition, MedicationRequest).

Usage:
    python src/mapping/fhir_transform.py --demo

Output:
    - FHIR resources
    - Transformation statistics
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ner.load_bc5cdr import load_bc5cdr
from ner.dictionary_baseline import build_dictionary, extract_entities_from_text, load_dictionary
from linking.entity_linking import link_entity, link_entities_from_documents, TERMINOLOGY
from mapping.omop_routing import route_to_omop, route_entities_from_documents


def omop_to_fhir(omop_record: Dict) -> Optional[Dict]:
    """
    Transform OMOP record to FHIR resource.
    
    Args:
        omop_record: OMOP record dict with omop_table, concept_id, etc.
    
    Returns:
        FHIR resource dict or None if not transformable
    """
    if not omop_record.get('concept_id'):
        return None
    
    # Transform based on OMOP table
    if omop_record['omop_table'] == 'condition_occurrence':
        fhir_resource = {
            'resourceType': 'Condition',
            'id': f"condition-{omop_record['concept_id']}-{omop_record['doc_id']}",
            'clinicalStatus': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                    'code': 'active',
                    'display': 'Active'
                }]
            },
            'code': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': omop_record['concept_id'],
                    'display': omop_record['entity_text']
                }]
            },
            'subject': {
                'reference': f"Patient/{omop_record['doc_id']}"
            },
            'extension': [{
                'url': 'http://example.org/fhir/StructureDefinition/source-document',
                'valueString': omop_record['doc_id']
            }, {
                'url': 'http://example.org/fhir/StructureDefinition/offset',
                'valueInteger': omop_record['offset']
            }, {
                'url': 'http://example.org/fhir/StructureDefinition/length',
                'valueInteger': omop_record['length']
            }]
        }
    elif omop_record['omop_table'] == 'drug_exposure':
        fhir_resource = {
            'resourceType': 'MedicationRequest',
            'id': f"medication-{omop_record['concept_id']}-{omop_record['doc_id']}",
            'status': 'active',
            'medicationCodeableConcept': {
                'coding': [{
                    'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'code': omop_record['concept_id'],
                    'display': omop_record['entity_text']
                }]
            },
            'subject': {
                'reference': f"Patient/{omop_record['doc_id']}"
            },
            'extension': [{
                'url': 'http://example.org/fhir/StructureDefinition/source-document',
                'valueString': omop_record['doc_id']
            }, {
                'url': 'http://example.org/fhir/StructureDefinition/offset',
                'valueInteger': omop_record['offset']
            }, {
                'url': 'http://example.org/fhir/StructureDefinition/length',
                'valueInteger': omop_record['length']
            }]
        }
    else:
        return None
    
    return fhir_resource


def transform_omop_to_fhir(omop_records: List[Dict]) -> List[Dict]:
    """
    Transform all OMOP records to FHIR resources.
    
    Args:
        omop_records: List of OMOP records
    
    Returns:
        List of FHIR resources
    """
    fhir_resources = []
    
    for omop_record in omop_records:
        fhir_resource = omop_to_fhir(omop_record)
        if fhir_resource:
            fhir_resources.append(fhir_resource)
    
    return fhir_resources


def demo():
    """Run demonstration on sample text."""
    print(f"=== FHIR Transformation Demo ===")
    
    # Load dictionary
    dict_path = Path("data/terminology/bc5cdr_dictionary.json")
    if not dict_path.exists():
        print(f"ERROR: Dictionary not found: {dict_path}")
        return
    dictionary = load_dictionary(str(dict_path))
    
    # Sample texts
    sample_texts = [
        "Naloxone reverses the antihypertensive effect of clonidine.",
        "Morphine induces hypertension and seizures in rats.",
        "Cocaine toxicity causes myocardial infarction.",
    ]
    
    for text in sample_texts:
        print(f"\nText: {text}")
        matches = extract_entities_from_text(text, dictionary, min_length=4)
        print(f"Extracted {len(matches)} entities:")
        for match in matches:
            linked = link_entity(match['text'], TERMINOLOGY)
            if linked:
                omop = route_to_omop(linked)
                if omop:
                    fhir = omop_to_fhir(omop)
                    if fhir:
                        print(f"  - '{match['text']}' → FHIR {fhir['resourceType']} (id: {fhir['id'][:30]}...)")
                    else:
                        print(f"  - '{match['text']}' → NOT TRANSFORMED")
                else:
                    print(f"  - '{match['text']}' → NOT ROUTED")
            else:
                print(f"  - '{match['text']}' → UNLINKED")


def evaluate_fhir(
    test_path: str = "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml",
):
    """
    Evaluate FHIR transformation on BC5CDR test set.
    """
    print(f"=== FHIR Transformation Evaluation ===")
    print(f"Test path: {test_path}")
    
    # Load dictionary
    dict_path = Path("data/terminology/bc5cdr_dictionary.json")
    if not dict_path.exists():
        print(f"ERROR: Dictionary not found: {dict_path}")
        return
    dictionary = load_dictionary(str(dict_path))
    
    # Load test data
    test_docs = load_bc5cdr(test_path)
    print(f"Test documents: {len(test_docs)}")
    
    # Route entities to OMOP
    print(f"Routing entities to OMOP...")
    omop_records = route_entities_from_documents(test_docs, dictionary, TERMINOLOGY)
    print(f"OMOP records: {len(omop_records)}")
    
    # Transform to FHIR
    print(f"Transforming to FHIR...")
    fhir_resources = transform_omop_to_fhir(omop_records)
    print(f"FHIR resources: {len(fhir_resources)}")
    
    # Statistics
    print(f"\n=== Transformation Statistics ===")
    print(f"Total OMOP records: {len(omop_records)}")
    print(f"Total FHIR resources: {len(fhir_resources)}")
    print(f"Transformation rate: {100*len(fhir_resources)/len(omop_records):.1f}%" if omop_records else "N/A")
    
    # By resource type
    resource_counts = defaultdict(int)
    for resource in fhir_resources:
        resource_counts[resource['resourceType']] += 1
    
    print(f"\n=== By FHIR Resource Type ===")
    for resource_type, count in sorted(resource_counts.items(), key=lambda x: -x[1]):
        print(f"  {resource_type}: {count} ({100*count/len(fhir_resources):.1f}%)")
    
    # Sample FHIR resources
    print(f"\n=== Sample FHIR Resources ===")
    for resource in fhir_resources[:3]:
        print(f"\nResource type: {resource['resourceType']}")
        print(f"ID: {resource['id']}")
        print(f"Code: {resource.get('code', resource.get('medicationCodeableConcept', {})).get('coding', [{}])[0].get('display', 'N/A')}")
        print(f"Subject: {resource['subject']['reference']}")


def main():
    parser = argparse.ArgumentParser(description="FHIR transformation for BC5CDR")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate on test set")
    
    args = parser.parse_args()
    
    if args.demo:
        demo()
    elif args.evaluate:
        evaluate_fhir()
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/mapping/fhir_transform.py --demo")
        print("  python src/mapping/fhir_transform.py --evaluate")


if __name__ == "__main__":
    main()
