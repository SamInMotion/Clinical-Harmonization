"""
Evaluate dictionary-based NER baseline on BC5CDR.

Calculates precision, recall, and F1 using location-level, type-aware,
exact-span matching.

Usage:
    python src/ner/evaluate_ner.py

Output:
    - Precision, recall, F1
    - Error analysis
"""

from collections import defaultdict
from pathlib import Path
import json

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import (
    build_dictionary,
    extract_entities_from_text,
    normalize_text,
)
from gold_spans import extract_gold_location_spans, entity_to_key


def load_dictionary_from_file(dict_path: str):
    """Load dictionary from JSON file."""
    with open(dict_path, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    return defaultdict(list, dictionary)


def extract_predicted_entities(documents, dictionary, min_length: int = 4):
    """
    Extract predicted entities from documents using the dictionary baseline.
    """
    predicted_entities = []

    for doc in documents:
        for passage in doc["passages"]:
            matches = extract_entities_from_text(
                passage["text"], dictionary, min_length
            )

            for match in matches:
                predicted_entities.append({
                    "text": match["text"],
                    "type": match["type"],
                    "mesh_id": match["mesh_id"],
                    "offset": match["offset"],
                    "length": match["length"],
                    "doc_id": doc["id"],
                    "passage_type": passage["type"],
                })

    return predicted_entities


def calculate_metrics(gold_entities, predicted_entities):
    """
    Calculate location-level, type-aware exact-match metrics.
    """
    gold_keys = set(entity_to_key(entity) for entity in gold_entities)
    pred_keys = set(entity_to_key(entity) for entity in predicted_entities)

    tp_keys = gold_keys & pred_keys
    tp = len(tp_keys)

    fp_keys = pred_keys - gold_keys
    fp = len(fp_keys)

    fn_keys = gold_keys - pred_keys
    fn = len(fn_keys)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "gold_total": len(gold_entities),
        "pred_total": len(predicted_entities),
    }


def analyze_errors(gold_entities, predicted_entities):
    """
    Identify location-level, type-aware false positives and negatives.
    """
    gold_keys = set(entity_to_key(entity) for entity in gold_entities)
    pred_keys = set(entity_to_key(entity) for entity in predicted_entities)

    fp_keys = pred_keys - gold_keys
    fn_keys = gold_keys - pred_keys

    predicted_by_key = {
        entity_to_key(entity): entity
        for entity in predicted_entities
    }
    gold_by_key = {
        entity_to_key(entity): entity
        for entity in gold_entities
    }

    return {
        "false_positives": [
            predicted_by_key[key]
            for key in sorted(fp_keys)
        ],
        "false_negatives": [
            gold_by_key[key]
            for key in sorted(fn_keys)
        ],
    }


def main():
    dict_path = Path("data/terminology/bc5cdr_dictionary.json")
    if not dict_path.exists():
        print(f"ERROR: Dictionary not found: {dict_path}")
        print("Run 'python src/ner/dictionary_baseline.py' first.")
        return

    print(f"Loading dictionary from: {dict_path}")
    dictionary = load_dictionary_from_file(str(dict_path))

    test_path = Path(
        "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        "CDR_TestSet.BioC.xml"
    )
    if not test_path.exists():
        print(f"ERROR: Test set not found: {test_path}")
        return

    print("Loading BC5CDR test set...")
    test_documents = load_bc5cdr(str(test_path))

    print("Extracting location-level gold entities...")
    gold_entities = extract_gold_location_spans(test_documents)
    print(f"Gold location spans: {len(gold_entities)}")

    print("Extracting predicted entities...")
    predicted_entities = extract_predicted_entities(
        test_documents, dictionary, min_length=4
    )
    print(f"Predicted entities: {len(predicted_entities)}")

    print(
        "\n=== Evaluation Results "
        "(Location-Level, Type-Aware Exact Span Match) ==="
    )
    metrics = calculate_metrics(gold_entities, predicted_entities)
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")
    print(f"\nTrue positives: {metrics['tp']}")
    print(f"False positives: {metrics['fp']}")
    print(f"False negatives: {metrics['fn']}")
    print(f"Gold location spans: {metrics['gold_total']}")
    print(f"Predicted entities: {metrics['pred_total']}")

    errors = analyze_errors(gold_entities, predicted_entities)
    print(f"\nFalse positives: {len(errors['false_positives'])}")
    print(f"False negatives: {len(errors['false_negatives'])}")

    print("\n=== Breakdown by Entity Type ===")

    for entity_type in ("Chemical", "Disease"):
        gold_subset = [
            entity
            for entity in gold_entities
            if entity["type"] == entity_type
        ]
        predicted_subset = [
            entity
            for entity in predicted_entities
            if entity["type"] == entity_type
        ]
        subset_metrics = calculate_metrics(
            gold_subset, predicted_subset
        )

        print(f"\n{entity_type}:")
        print(
            f"  Precision: {subset_metrics['precision']:.4f}, "
            f"Recall: {subset_metrics['recall']:.4f}, "
            f"F1: {subset_metrics['f1']:.4f}"
        )
        print(
            f"  TP: {subset_metrics['tp']}, "
            f"FP: {subset_metrics['fp']}, "
            f"FN: {subset_metrics['fn']}"
        )


if __name__ == "__main__":
    main()
