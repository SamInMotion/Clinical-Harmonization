"""
OMOP domain routing for BC5CDR.

Maps linked entities to OMOP tables based on concept domain.

Usage:
    python src/mapping/omop_routing.py --demo

Output:
    - OMOP-routed entities
    - Routing statistics
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


def route_to_omop(linked_entity: Dict) -> Optional[Dict]:
    """
    Route linked entity to OMOP table based on domain.
    
    Args:
        linked_entity: Linked entity dict with concept_id, type, vocabulary
    
    Returns:
        OMOP record dict or None if not routable
    """
    if not linked_entity.get('concept_id'):
        return None
    
    # Determine OMOP table based on entity type
    if linked_entity['type'] == 'Chemical':
        omop_table = 'drug_exposure'
        omop_domain = 'Drug'
    elif linked_entity['type'] == 'Disease':
        omop_table = 'condition_occurrence'
        omop_domain = 'Condition'
    else:
        return None
    
    return {
        'entity_text': linked_entity['entity_text'],
        'concept_id': linked_entity['concept_id'],
        'vocabulary': linked_entity['vocabulary'],
        'omop_table': omop_table,
        'omop_domain': omop_domain,
        'doc_id': linked_entity.get('doc_id', 'N/A'),  # Use .get() to avoid KeyError
        'passage_type': linked_entity.get('passage_type', 'N/A'),
        'offset': linked_entity.get('offset', 0),
        'length': linked_entity.get('length', 0)
    }


def route_entities_from_documents(documents, dictionary, terminology):
    """
    Route all linked entities to OMOP tables.
    
    Args:
        documents: List of documents
        dictionary: Entity dictionary
        terminology: Terminology dictionary
    
    Returns:
        List of OMOP records
    """
    omop_records = []
    
    # Link entities first
    linked_entities = link_entities_from_documents(documents, dictionary, terminology)
    
    # Route each linked entity
    for linked in linked_entities:
        omop_record = route_to_omop(linked)
        if omop_record:
            omop_records.append(omop_record)
    
    return omop_records


def demo():
    """Run demonstration on sample text."""
    print(f"=== OMOP Domain Routing Demo ===")
    
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
                    print(f"  - '{match['text']}' → {omop['omop_table']} (domain: {omop['omop_domain']})")
                else:
                    print(f"  - '{match['text']}' → NOT ROUTED")
            else:
                print(f"  - '{match['text']}' → UNLINKED")


def evaluate_routing(
    test_path: str = "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml",
):
    """
    Evaluate OMOP routing on BC5CDR test set.
    """
    print(f"=== OMOP Domain Routing Evaluation ===")
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
    
    # Route entities
    print(f"Routing entities to OMOP...")
    omop_records = route_entities_from_documents(test_docs, dictionary, TERMINOLOGY)
    
    # Statistics
    total_linked = len([e for e in link_entities_from_documents(test_docs, dictionary, TERMINOLOGY) if e.get('concept_id')])
    total_routed = len(omop_records)
    
    print(f"\n=== Routing Statistics ===")
    print(f"Total linked entities: {total_linked}")
    print(f"Total routed to OMOP: {total_routed}")
    print(f"Routing rate: {100*total_routed/total_linked:.1f}%" if total_linked > 0 else "N/A")
    
    # By OMOP table
    table_counts = defaultdict(int)
    for record in omop_records:
        table_counts[record['omop_table']] += 1
    
    print(f"\n=== By OMOP Table ===")
    for table, count in sorted(table_counts.items(), key=lambda x: -x[1]):
        print(f"  {table}: {count} ({100*count/total_routed:.1f}%)")
    
    # Sample records
    print(f"\n=== Sample OMOP Records ===")
    for record in omop_records[:10]:
        print(f"  '{record['entity_text']}' → {record['omop_table']} (domain: {record['omop_domain']}) in doc {record['doc_id']}")


def main():
    parser = argparse.ArgumentParser(description="OMOP domain routing for BC5CDR")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate on test set")
    
    args = parser.parse_args()
    
    if args.demo:
        demo()
    elif args.evaluate:
        evaluate_routing()
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/mapping/omop_routing.py --demo")
        print("  python src/mapping/omop_routing.py --evaluate")


if __name__ == "__main__":
    main()
