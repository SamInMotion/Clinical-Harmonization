"""
Error decomposition for BC5CDR pipeline.

Tracks errors through the pipeline: extraction → linking → OMOP → FHIR.

Usage:
    python src/evaluation/error_decomposition.py --evaluate

Output:
    - Error breakdown by stage
    - Error taxonomy
    - Pipeline statistics
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
from ner.gold_spans import extract_gold_location_spans, entity_to_key
from ner.dictionary_baseline import build_dictionary, extract_entities_from_text, load_dictionary
from linking.entity_linking import link_entity, link_entities_from_documents, TERMINOLOGY
from mapping.omop_routing import route_to_omop, route_entities_from_documents
from mapping.fhir_transform import omop_to_fhir, transform_omop_to_fhir


def decompose_errors(
    test_path: str = "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml",
):
    """
    Decompose errors through the pipeline.
    
    Args:
        test_path: Path to BC5CDR test set
    
    Returns:
        Error decomposition results
    """
    print(f"=== Error Decomposition ===")
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
    
    # Extract location-level gold entities.
    gold_entities = extract_gold_location_spans(test_docs)

    print(f"Gold entities: {len(gold_entities)}")
    
    # Extract predicted entities
    predicted_entities = []
    for doc in test_docs:
        for passage in doc['passages']:
            matches = extract_entities_from_text(passage['text'], dictionary, min_length=4)
            for match in matches:
                predicted_entities.append({
                    'text': match['text'],
                    'type': match['type'],
                    'offset': match['offset'],
                    'length': match['length'],
                    'doc_id': doc['id'],
                    'passage_type': passage['type']
                })
    
    print(f"Predicted entities: {len(predicted_entities)}")
    
    # Link entities
    linked_entities = link_entities_from_documents(test_docs, dictionary, TERMINOLOGY)
    linked_count = sum(1 for e in linked_entities if e.get('concept_id'))
    print(f"Linked entities: {linked_count}")
    
    # Route to OMOP
    omop_records = route_entities_from_documents(test_docs, dictionary, TERMINOLOGY)
    print(f"OMOP records: {len(omop_records)}")
    
    # Transform to FHIR
    fhir_resources = transform_omop_to_fhir(omop_records)
    print(f"FHIR resources: {len(fhir_resources)}")
    
    # Error decomposition
    print(f"\n=== Error Decomposition ===")
    
    # Stage 1: Extraction
    gold_keys = set(entity_to_key(e) for e in gold_entities)
    pred_keys = set(entity_to_key(e) for e in predicted_entities)
    
    extraction_tp = len(gold_keys & pred_keys)
    extraction_fp = len(pred_keys - gold_keys)
    extraction_fn = len(gold_keys - pred_keys)
    
    print(f"\n1. Extraction:")
    print(f"   True positives: {extraction_tp}")
    print(f"   False positives: {extraction_fp}")
    print(f"   False negatives: {extraction_fn}")
    print(f"   Precision: {extraction_tp/(extraction_tp+extraction_fp):.4f}" if (extraction_tp+extraction_fp) > 0 else "   Precision: N/A")
    print(f"   Recall: {extraction_tp/(extraction_tp+extraction_fn):.4f}" if (extraction_tp+extraction_fn) > 0 else "   Recall: N/A")
    
    # Stage 2: Linking
    linked_keys = set((e['doc_id'], e['passage_type'], e['offset'], e['length']) for e in linked_entities if e.get('concept_id'))
    linking_rate = linked_count / len(predicted_entities) if predicted_entities else 0.0
    
    print(f"\n2. Linking:")
    print(f"   Predicted entities: {len(predicted_entities)}")
    print(f"   Linked: {linked_count}")
    print(f"   Unlinked: {len(predicted_entities) - linked_count}")
    print(f"   Linking rate: {100*linking_rate:.1f}%")
    
    # Stage 3: OMOP routing
    omop_rate = len(omop_records) / linked_count if linked_count else 0.0
    print(f"\n3. OMOP Routing:")
    print(f"   Linked entities: {linked_count}")
    print(f"   OMOP records: {len(omop_records)}")
    print(f"   Routing rate: {100*omop_rate:.1f}%")
    
    # Stage 4: FHIR transformation
    fhir_rate = len(fhir_resources) / len(omop_records) if omop_records else 0.0
    print(f"\n4. FHIR Transformation:")
    print(f"   OMOP records: {len(omop_records)}")
    print(f"   FHIR resources: {len(fhir_resources)}")
    print(f"   Transformation rate: {100*fhir_rate:.1f}%")
    
    # End-to-end survival
    print(f"\n=== End-to-End Survival ===")
    print(f"Gold entities: {len(gold_entities)}")
    print(f"Extracted (TP): {extraction_tp}")
    print(f"Linked: {linked_count}")
    print(f"Routed to OMOP: {len(omop_records)}")
    print(f"FHIR resources: {len(fhir_resources)}")
    print(f"Survival rate: {100*len(fhir_resources)/len(gold_entities):.1f}%" if gold_entities else "N/A")
    
    # Save results
    results = {
        'gold_entities': len(gold_entities),
        'predicted_entities': len(predicted_entities),
        'extraction': {
            'tp': extraction_tp,
            'fp': extraction_fp,
            'fn': extraction_fn,
        },
        'linking': {
            'linked': linked_count,
            'unlinked': len(predicted_entities) - linked_count,
            'rate': linking_rate,
        },
        'omop_routing': {
            'routed': len(omop_records),
            'rate': omop_rate,
        },
        'fhir_transformation': {
            'fhir_resources': len(fhir_resources),
            'rate': fhir_rate,
        },
        'end_to_end': {
            'gold_entities': len(gold_entities),
            'fhir_resources': len(fhir_resources),
            'survival_rate': len(fhir_resources)/len(gold_entities) if gold_entities else 0.0,
        }
    }
    
    output_path = Path("output/evaluation/error_decomposition.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Error decomposition for BC5CDR pipeline")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate on test set")
    
    args = parser.parse_args()
    
    if args.evaluate:
        decompose_errors()
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/evaluation/error_decomposition.py --evaluate")


if __name__ == "__main__":
    main()
