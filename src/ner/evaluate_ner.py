"""
Evaluate dictionary-based NER baseline on BC5CDR.

Calculates precision, recall, F1 at span level (exact match).

Usage:
    python src/ner/evaluate_ner.py

Output:
    - Precision, recall, F1
    - Error analysis (false positives, false negatives)
"""

from collections import defaultdict
from pathlib import Path
import json
from load_bc5cdr import load_bc5cdr
from dictionary_baseline import build_dictionary, extract_entities_from_text, normalize_text


def load_dictionary_from_file(dict_path: str):
    """Load dictionary from JSON file."""
    with open(dict_path, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    
    # Convert to defaultdict
    return defaultdict(list, dictionary)


def extract_gold_entities(documents):
    """
    Extract gold-standard entities from documents.
    
    Args:
        documents: List of documents from load_bc5cdr()
    
    Returns:
        List of {text, type, mesh_id, offset, length, doc_id, passage_type}
    """
    gold_entities = []
    
    for doc in documents:
        for passage in doc['passages']:
            for ann in passage['annotations']:
                gold_entities.append({
                    'text': ann['text'].strip(),
                    'type': ann['type'],
                    'mesh_id': ann['mesh_id'],
                    'offset': ann['offset'],
                    'length': len(ann['text'].strip()),
                    'doc_id': doc['id'],
                    'passage_type': passage['type']
                })
    
    return gold_entities


def extract_predicted_entities(documents, dictionary, min_length: int = 3):
    """
    Extract predicted entities from documents using dictionary baseline.
    
    Args:
        documents: List of documents
        dictionary: Entity dictionary
        min_length: Minimum entity length
    
    Returns:
        List of {text, type, mesh_id, offset, length, doc_id, passage_type}
    """
    predicted_entities = []
    
    for doc in documents:
        for passage in doc['passages']:
            matches = extract_entities_from_text(passage['text'], dictionary, min_length)
            
            for match in matches:
                predicted_entities.append({
                    'text': match['text'],
                    'type': match['type'],
                    'mesh_id': match['mesh_id'],
                    'offset': match['offset'],
                    'length': match['length'],
                    'doc_id': doc['id'],
                    'passage_type': passage['type']
                })
    
    return predicted_entities


def entity_to_key(entity):
    """Convert entity to unique key for matching."""
    return (entity['doc_id'], entity['passage_type'], entity['offset'], entity['length'])


def calculate_metrics(gold_entities, predicted_entities):
    """
    Calculate precision, recall, F1 at span level (exact match).
    
    Args:
        gold_entities: List of gold-standard entities
        predicted_entities: List of predicted entities
    
    Returns:
        dict with precision, recall, f1, tp, fp, fn
    """
    # Convert to sets of keys
    gold_keys = set(entity_to_key(e) for e in gold_entities)
    pred_keys = set(entity_to_key(e) for e in predicted_entities)
    
    # True positives: predicted entities that match gold
    tp_keys = gold_keys & pred_keys
    tp = len(tp_keys)
    
    # False positives: predicted entities not in gold
    fp_keys = pred_keys - gold_keys
    fp = len(fp_keys)
    
    # False negatives: gold entities not predicted
    fn_keys = gold_keys - pred_keys
    fn = len(fn_keys)
    
    # Precision, recall, F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'gold_total': len(gold_entities),
        'pred_total': len(predicted_entities)
    }


def analyze_errors(gold_entities, predicted_entities):
    """
    Analyze false positives and false negatives.
    
    Args:
        gold_entities: List of gold-standard entities
        predicted_entities: List of predicted entities
    
    Returns:
        dict with false_positives, false_negatives
    """
    gold_keys = set(entity_to_key(e) for e in gold_entities)
    pred_keys = set(entity_to_key(e) for e in predicted_entities)
    
    # False positives
    fp_keys = pred_keys - gold_keys
    false_positives = [e for e in predicted_entities if entity_to_key(e) in fp_keys]
    
    # False negatives
    fn_keys = gold_keys - pred_keys
    false_negatives = [e for e in gold_entities if entity_to_key(e) in fn_keys]
    
    return {
        'false_positives': false_positives,
        'false_negatives': false_negatives
    }


def main():
    # Load dictionary
    dict_path = Path("data/terminology/bc5cdr_dictionary.json")
    if not dict_path.exists():
        print(f"ERROR: Dictionary not found: {dict_path}")
        print("Run 'python src/ner/dictionary_baseline.py' first.")
        return
    
    print(f"Loading dictionary from: {dict_path}")
    dictionary = load_dictionary_from_file(str(dict_path))
    
    # Load test set
    test_path = Path("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml")
    if not test_path.exists():
        print(f"ERROR: Test set not found: {test_path}")
        return
    
    print(f"Loading BC5CDR test set...")
    test_documents = load_bc5cdr(str(test_path))
    
    # Extract gold-standard entities
    print(f"Extracting gold-standard entities...")
    gold_entities = extract_gold_entities(test_documents)
    print(f"Gold entities: {len(gold_entities)}")
    
    # Extract predicted entities
    print(f"Extracting predicted entities (dictionary baseline)...")
    predicted_entities = extract_predicted_entities(test_documents, dictionary, min_length=3)
    print(f"Predicted entities: {len(predicted_entities)}")
    
    # Calculate metrics
    print(f"\n=== Evaluation Results (Exact Span Match) ===")
    metrics = calculate_metrics(gold_entities, predicted_entities)
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")
    print(f"\nTrue positives: {metrics['tp']}")
    print(f"False positives: {metrics['fp']}")
    print(f"False negatives: {metrics['fn']}")
    print(f"Gold total: {metrics['gold_total']}")
    print(f"Predicted total: {metrics['pred_total']}")
    
    # Error analysis
    print(f"\n=== Error Analysis ===")
    errors = analyze_errors(gold_entities, predicted_entities)
    
    print(f"False positives: {len(errors['false_positives'])}")
    print(f"False negatives: {len(errors['false_negatives'])}")
    
    # Show sample false positives
    print(f"\n--- Sample False Positives (first 10) ---")
    for i, fp in enumerate(errors['false_positives'][:10]):
        print(f"  {i+1}. '{fp['text']}' ({fp['type']}) in doc {fp['doc_id']} ({fp['passage_type']}) @ offset {fp['offset']}")
    
    # Show sample false negatives
    print(f"\n--- Sample False Negatives (first 10) ---")
    for i, fn in enumerate(errors['false_negatives'][:10]):
        print(f"  {i+1}. '{fn['text']}' ({fn['type']}) in doc {fn['doc_id']} ({fn['passage_type']}) @ offset {fn['offset']}")
    
    # Breakdown by entity type
    print(f"\n=== Breakdown by Entity Type ===")
    
    # Chemicals
    gold_chem = [e for e in gold_entities if e['type'] == 'Chemical']
    pred_chem = [e for e in predicted_entities if e['type'] == 'Chemical']
    metrics_chem = calculate_metrics(gold_chem, pred_chem)
    print(f"\nChemicals:")
    print(f"  Precision: {metrics_chem['precision']:.4f}, Recall: {metrics_chem['recall']:.4f}, F1: {metrics_chem['f1']:.4f}")
    print(f"  TP: {metrics_chem['tp']}, FP: {metrics_chem['fp']}, FN: {metrics_chem['fn']}")
    
    # Diseases
    gold_disease = [e for e in gold_entities if e['type'] == 'Disease']
    pred_disease = [e for e in predicted_entities if e['type'] == 'Disease']
    metrics_disease = calculate_metrics(gold_disease, pred_disease)
    print(f"\nDiseases:")
    print(f"  Precision: {metrics_disease['precision']:.4f}, Recall: {metrics_disease['recall']:.4f}, F1: {metrics_disease['f1']:.4f}")
    print(f"  TP: {metrics_disease['tp']}, FP: {metrics_disease['fp']}, FN: {metrics_disease['fn']}")


if __name__ == "__main__":
    main()
