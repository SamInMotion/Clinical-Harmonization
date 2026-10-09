"""
Entity linking for BC5CDR.

Maps extracted entities to standardized terminologies (SNOMED-CT, ICD-10-CM, RxNorm).

Usage:
    python src/linking/entity_linking.py --demo

Output:
    - Linked entities with concept IDs
    - Linking statistics
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ner.load_bc5cdr import load_bc5cdr
from ner.dictionary_baseline import build_dictionary, extract_entities_from_text, load_dictionary


# Simple terminology lookup (mock data for demonstration)
# In production, this would load from SNOMED-CT, ICD-10-CM, RxNorm files
TERMINOLOGY = {
    # Chemicals (RxNorm-style)
    "naloxone": {"concept_id": "7187", "type": "Chemical", "vocabulary": "RxNorm"},
    "clonidine": {"concept_id": "2612", "type": "Chemical", "vocabulary": "RxNorm"},
    "morphine": {"concept_id": "7052", "type": "Chemical", "vocabulary": "RxNorm"},
    "cocaine": {"concept_id": "2594", "type": "Chemical", "vocabulary": "RxNorm"},
    "dopamine": {"concept_id": "3498", "type": "Chemical", "vocabulary": "RxNorm"},
    "nicotine": {"concept_id": "7231", "type": "Chemical", "vocabulary": "RxNorm"},
    "lithium": {"concept_id": "6320", "type": "Chemical", "vocabulary": "RxNorm"},
    "haloperidol": {"concept_id": "4938", "type": "Chemical", "vocabulary": "RxNorm"},
    
    # Diseases (SNOMED-CT-style)
    "hypertensive": {"concept_id": "38341003", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "hypertension": {"concept_id": "38341003", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "pain": {"concept_id": "22253000", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "toxicity": {"concept_id": "405816006", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "seizures": {"concept_id": "91175000", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "seizure": {"concept_id": "91175000", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "hepatitis": {"concept_id": "30214006", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "myocardial infarction": {"concept_id": "22298006", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "migraine": {"concept_id": "37796009", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "delirium": {"concept_id": "48694002", "type": "Disease", "vocabulary": "SNOMED-CT"},
    "ulcers": {"concept_id": "95219008", "type": "Disease", "vocabulary": "SNOMED-CT"},
}


def normalize_term(term: str) -> str:
    """
    Normalize term for terminology lookup.
    
    Operations:
    - Lowercase
    - Strip whitespace
    - Normalize internal whitespace
    """
    term = term.lower().strip()
    term = ' '.join(term.split())
    return term


def link_entity(entity_text: str, terminology: Dict) -> Optional[Dict]:
    """
    Link entity to standardized terminology.
    
    Args:
        entity_text: Extracted entity text
        terminology: Terminology dictionary
    
    Returns:
        Linked concept dict or None if not found
    """
    normalized = normalize_term(entity_text)
    
    # Exact match
    if normalized in terminology:
        return {
            'entity_text': entity_text,
            'normalized': normalized,
            'concept_id': terminology[normalized]['concept_id'],
            'type': terminology[normalized]['type'],
            'vocabulary': terminology[normalized]['vocabulary'],
            'match_type': 'exact'
        }
    
    # No match
    return None


def link_entities_from_documents(documents, dictionary, terminology):
    """
    Link all extracted entities from documents.
    
    Args:
        documents: List of documents
        dictionary: Entity dictionary
        terminology: Terminology dictionary
    
    Returns:
        List of linked entities
    """
    linked_entities = []
    
    for doc in documents:
        for passage in doc['passages']:
            # Extract entities
            matches = extract_entities_from_text(passage['text'], dictionary, min_length=4)
            
            # Link each entity
            for match in matches:
                linked = link_entity(match['text'], terminology)
                
                if linked:
                    linked['doc_id'] = doc['id']
                    linked['passage_type'] = passage['type']
                    linked['offset'] = match['offset']
                    linked['length'] = match['length']
                    linked_entities.append(linked)
                else:
                    # Unlinked entity
                    unlinked = {
                        'entity_text': match['text'],
                        'normalized': normalize_term(match['text']),
                        'concept_id': None,
                        'type': match['type'],
                        'vocabulary': None,
                        'match_type': 'unlinked',
                        'doc_id': doc['id'],
                        'passage_type': passage['type'],
                        'offset': match['offset'],
                        'length': match['length']
                    }
                    linked_entities.append(unlinked)
    
    return linked_entities


def demo():
    """Run demonstration on sample text."""
    print(f"=== Entity Linking Demo ===")
    
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
        "Famotidine is used for stress ulcers.",  # Famotidine not in terminology
    ]
    
    for text in sample_texts:
        print(f"\nText: {text}")
        matches = extract_entities_from_text(text, dictionary, min_length=4)
        print(f"Extracted {len(matches)} entities:")
        for match in matches:
            linked = link_entity(match['text'], TERMINOLOGY)
            if linked:
                print(f"  - '{match['text']}' → {linked['concept_id']} ({linked['vocabulary']}, {linked['match_type']})")
            else:
                print(f"  - '{match['text']}' → UNLINKED")


def evaluate_linking(
    test_path: str = "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml",
):
    """
    Evaluate entity linking on BC5CDR test set.
    """
    print(f"=== Entity Linking Evaluation ===")
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
    
    # Link entities
    print(f"Linking entities...")
    linked_entities = link_entities_from_documents(test_docs, dictionary, TERMINOLOGY)
    
    # Statistics
    total = len(linked_entities)
    linked = sum(1 for e in linked_entities if e['concept_id'] is not None)
    unlinked = total - linked
    
    print(f"\n=== Linking Statistics ===")
    print(f"Total extracted: {total}")
    print(f"Linked: {linked} ({100*linked/total:.1f}%)")
    print(f"Unlinked: {unlinked} ({100*unlinked/total:.1f}%)")
    
    # By vocabulary
    vocab_counts = defaultdict(int)
    for e in linked_entities:
        if e['vocabulary']:
            vocab_counts[e['vocabulary']] += 1
        else:
            vocab_counts['unlinked'] += 1
    
    print(f"\n=== By Vocabulary ===")
    for vocab, count in sorted(vocab_counts.items(), key=lambda x: -x[1]):
        print(f"  {vocab}: {count} ({100*count/total:.1f}%)")
    
    # Sample linked entities
    print(f"\n=== Sample Linked Entities ===")
    for e in linked_entities[:10]:
        if e['concept_id']:
            print(f"  '{e['entity_text']}' → {e['concept_id']} ({e['vocabulary']}) in doc {e['doc_id']}")
    
    # Sample unlinked entities
    print(f"\n=== Sample Unlinked Entities ===")
    unlinked_entities = [e for e in linked_entities if not e['concept_id']]
    for e in unlinked_entities[:10]:
        print(f"  '{e['entity_text']}' → UNLINKED in doc {e['doc_id']}")


def main():
    parser = argparse.ArgumentParser(description="Entity linking for BC5CDR")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate on test set")
    
    args = parser.parse_args()
    
    if args.demo:
        demo()
    elif args.evaluate:
        evaluate_linking()
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/linking/entity_linking.py --demo")
        print("  python src/linking/entity_linking.py --evaluate")


if __name__ == "__main__":
    main()
