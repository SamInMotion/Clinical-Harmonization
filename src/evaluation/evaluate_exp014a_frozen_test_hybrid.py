"""Evaluate the EXP-014A frozen hybrid configuration on the BC5CDR test set.

The confidence threshold was selected using the BC5CDR development set only.
This script performs one final test-set evaluation of:

1. the word-boundary/base dictionary extractor;
2. the PubMedBERT epoch-3 extractor;
3. the frozen-threshold hybrid extractor.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp012"
)

OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp014a_frozen_test_evaluation.json"
)

FROZEN_THRESHOLD = 0.95


def load_predictions(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def prediction_key(record):
    return (
        record["document_id"],
        record["start"],
        record["end"],
        record["entity_type"],
    )


def spans_overlap(first, second):
    return first["start"] < second["end"] and second["start"] < first["end"]


def build_hybrid(dictionary_predictions, transformer_predictions, threshold):
    dictionary_by_document_type = {}

    for prediction in dictionary_predictions:
        key = (
            prediction["document_id"],
            prediction["entity_type"],
        )
        dictionary_by_document_type.setdefault(key, []).append(prediction)

    hybrid = []
    counts = {
        "dictionary_retained": 0,
        "pubmedbert_overlapping": 0,
        "pubmedbert_below_threshold": 0,
        "pubmedbert_added": 0,
    }

    for prediction in dictionary_predictions:
        hybrid.append(prediction)
        counts["dictionary_retained"] += 1

    for prediction in transformer_predictions:
        candidates = dictionary_by_document_type.get(
            (
                prediction["document_id"],
                prediction["entity_type"],
            ),
            [],
        )

        if any(spans_overlap(prediction, candidate) for candidate in candidates):
            counts["pubmedbert_overlapping"] += 1
            continue

        if prediction["confidence"] < threshold:
            counts["pubmedbert_below_threshold"] += 1
            continue

        hybrid.append(prediction)
        counts["pubmedbert_added"] += 1

    return hybrid, counts


def evaluate(predictions, gold):
    gold_keys = {prediction_key(entity) for entity in gold}
    prediction_keys = {prediction_key(entity) for entity in predictions}

    true_positives = len(gold_keys & prediction_keys)
    false_positives = len(prediction_keys - gold_keys)
    false_negatives = len(gold_keys - prediction_keys)

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "predicted_entities": len(prediction_keys),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main():
    gold = load_predictions(INPUT_DIR / "gold_entities.json")
    dictionary_predictions = load_predictions(
        INPUT_DIR / "dictionary_predictions.json"
    )
    transformer_predictions = load_predictions(
        INPUT_DIR / "pubmedbert_epoch3_predictions.json"
    )

    missing_confidence = sum(
        1 for prediction in transformer_predictions
        if "confidence" not in prediction
    )

    if missing_confidence:
        raise ValueError(
            f"{missing_confidence} PubMedBERT predictions lack confidence."
        )

    dictionary_metrics = evaluate(dictionary_predictions, gold)
    transformer_metrics = evaluate(transformer_predictions, gold)

    hybrid, counts = build_hybrid(
        dictionary_predictions,
        transformer_predictions,
        FROZEN_THRESHOLD,
    )
    hybrid_metrics = evaluate(hybrid, gold)

    results = {
        "experiment": "EXP-014A",
        "status": "completed",
        "evaluation_date_utc": datetime.now(timezone.utc).isoformat(),
        "split": "BC5CDR test set",
        "evaluation_type": "final frozen-configuration evaluation",
        "threshold_selection_split": "BC5CDR development set",
        "frozen_threshold": FROZEN_THRESHOLD,
        "confidence_definition": (
            "maximum softmax probability assigned to the predicted class "
            "among tokens overlapping the entity span"
        ),
        "matching_policy": (
            "document-level character offsets; location-level gold spans; "
            "type-aware exact-span matching"
        ),
        "dictionary_baseline": dictionary_metrics,
        "pubmedbert_only": transformer_metrics,
        "frozen_hybrid": {
            **hybrid_metrics,
            **counts,
        },
    }

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-014A frozen test-set evaluation ===")
    print(f"Frozen development-selected threshold: {FROZEN_THRESHOLD:.2f}")

    for label, metrics in (
        ("Dictionary", dictionary_metrics),
        ("PubMedBERT only", transformer_metrics),
        ("Frozen hybrid", hybrid_metrics),
    ):
        print(
            f"{label}: "
            f"P={metrics['precision']:.4f} "
            f"R={metrics['recall']:.4f} "
            f"F1={metrics['f1']:.4f} "
            f"TP={metrics['true_positives']} "
            f"FP={metrics['false_positives']} "
            f"FN={metrics['false_negatives']}"
        )

    print(f"\nResults saved to: {OUTPUT}")


if __name__ == "__main__":
    main()