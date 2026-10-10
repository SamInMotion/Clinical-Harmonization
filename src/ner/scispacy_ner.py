"""
Use scispaCy biomedical NER for BC5CDR.

This is a simpler alternative to transformer fine-tuning when Hugging Face
download is not available.

Usage:
    python src/ner/scispacy_ner.py --evaluate

Output:
    - Evaluation results in output/evaluation/
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict

import spacy
from seqeval.metrics import classification_report

from load_bc5cdr import load_bc5cdr
from gold_spans import extract_gold_location_spans, entity_to_key


# Label mapping for BC5CDR (scispaCy uses different labels)
# We'll map scispaCy labels to BIO format
LABEL2ID = {
    "O": 0,
    "B-Chemical": 1,
    "I-Chemical": 2,
    "B-Disease": 3,
    "I-Disease": 4,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


def extract_scispacy_entities(nlp, text):
    """
    Extract entities using scispaCy.
    
    Args:
        nlp: scispaCy model
        text: Input text
    
    Returns:
        List of {text, type, offset, length}
    """
    doc = nlp(text)
    entities = []
    
    for ent in doc.ents:
        # Map scispaCy labels to Chemical/Disease
        if ent.label_ in ['CHEMICAL', 'DRUG', 'GENE_OR_GENE_PRODUCT']:
            entity_type = 'Chemical'
        elif ent.label_ in ['DISEASE_OR_PHENOTYPE', 'SPECIES']:
            entity_type = 'Disease'
        else:
            continue
        
        entities.append({
            'text': ent.text,
            'type': entity_type,
            'offset': ent.start_char,
            'length': len(ent.text)
        })
    
    return entities


def evaluate_scispacy(
    test_path: str = "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml",
    model_name: str = "en_ner_bionlp13_md",
):
    """
    Evaluate scispaCy NER on BC5CDR test set.
    """
    print(f"=== scispaCy NER Evaluation ===")
    print(f"Model: {model_name}")
    print(f"Test path: {test_path}")
    
    # Load scispaCy model
    print(f"Loading scispaCy model...")
    try:
        nlp = spacy.load(model_name)
        print(f"✅ Model loaded")
    except OSError:
        print(f"ERROR: Model '{model_name}' not found.")
        print(f"Install with: python -m spacy download {model_name}")
        return
    
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
            entities = extract_scispacy_entities(nlp, passage['text'])
            for ent in entities:
                predicted_entities.append({
                    'text': ent['text'],
                    'type': ent['type'],
                    'offset': ent['offset'],
                    'length': ent['length'],
                    'doc_id': doc['id'],
                    'passage_type': passage['type']
                })
    
    print(f"Predicted entities: {len(predicted_entities)}")
    
    # Calculate metrics (exact span match)
    gold_keys = set(entity_to_key(e) for e in gold_entities)
    pred_keys = set(entity_to_key(e) for e in predicted_entities)
    
    tp = len(gold_keys & pred_keys)
    fp = len(pred_keys - gold_keys)
    fn = len(gold_keys - pred_keys)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    print(f"\n=== Results (Exact Span Match) ===")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1:.4f}")
    print(f"TP: {tp}, FP: {fp}, FN: {fn}")
    
    # By entity type
    print(f"\n=== By Entity Type ===")
    
    # Chemicals
    gold_chem = [e for e in gold_entities if e['type'] == 'Chemical']
    pred_chem = [e for e in predicted_entities if e['type'] == 'Chemical']
    gold_chem_keys = set(entity_to_key(e) for e in gold_chem)
    pred_chem_keys = set(entity_to_key(e) for e in pred_chem)
    tp_chem = len(gold_chem_keys & pred_chem_keys)
    fp_chem = len(pred_chem_keys - gold_chem_keys)
    fn_chem = len(gold_chem_keys - pred_chem_keys)
    p_chem = tp_chem / (tp_chem + fp_chem) if (tp_chem + fp_chem) > 0 else 0.0
    r_chem = tp_chem / (tp_chem + fn_chem) if (tp_chem + fn_chem) > 0 else 0.0
    f1_chem = 2 * p_chem * r_chem / (p_chem + r_chem) if (p_chem + r_chem) > 0 else 0.0
    print(f"Chemicals: P={p_chem:.4f}, R={r_chem:.4f}, F1={f1_chem:.4f}")
    
    # Diseases
    gold_disease = [e for e in gold_entities if e['type'] == 'Disease']
    pred_disease = [e for e in predicted_entities if e['type'] == 'Disease']
    gold_disease_keys = set(entity_to_key(e) for e in gold_disease)
    pred_disease_keys = set(entity_to_key(e) for e in pred_disease)
    tp_disease = len(gold_disease_keys & pred_disease_keys)
    fp_disease = len(pred_disease_keys - gold_disease_keys)
    fn_disease = len(gold_disease_keys - pred_disease_keys)
    p_disease = tp_disease / (tp_disease + fp_disease) if (tp_disease + fp_disease) > 0 else 0.0
    r_disease = tp_disease / (tp_disease + fn_disease) if (tp_disease + fn_disease) > 0 else 0.0
    f1_disease = 2 * p_disease * r_disease / (p_disease + r_disease) if (p_disease + r_disease) > 0 else 0.0
    print(f"Diseases: P={p_disease:.4f}, R={r_disease:.4f}, F1={f1_disease:.4f}")
    
    # Save results
    results = {
        'model': model_name,
        'overall': {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn
        },
        'chemicals': {
            'precision': p_chem,
            'recall': r_chem,
            'f1': f1_chem,
            'tp': tp_chem,
            'fp': fp_chem,
            'fn': fn_chem
        },
        'diseases': {
            'precision': p_disease,
            'recall': r_disease,
            'f1': f1_disease,
            'tp': tp_disease,
            'fp': fp_disease,
            'fn': fn_disease
        }
    }
    
    output_path = Path("output/evaluation/scispacy_bc5cdr_test_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate scispaCy NER on BC5CDR")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate on test set")
    parser.add_argument("--model", type=str, default="en_ner_bionlp13_md", help="scispaCy model name")
    
    args = parser.parse_args()
    
    if args.evaluate:
        evaluate_scispacy(model_name=args.model)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/ner/scispacy_ner.py --evaluate")


if __name__ == "__main__":
    main()
