"""Evaluate confidence-thresholded EXP-013 hybrid extraction.

The dictionary predictions are always retained. A PubMedBERT prediction is
added only when:
1. it does not overlap a dictionary prediction of the same entity type; and
2. its maximum span-token confidence is at least the threshold.
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
    / "exp013_hybrid_confidence_sweep.json"
)

THRESHOLDS = [
    0.50, 0.60, 0.70, 0.80, 0.85,
    0.90, 0.93, 0.95, 0.97, 0.98, 0.99,
]


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
            f"{missing_confidence} PubMedBERT predictions lack confidence. "
            "Rerun export_exp012_predictions.py after adding confidence."
        )

    sweep = []

    for threshold in THRESHOLDS:
        hybrid, counts = build_hybrid(
            dictionary_predictions,
            transformer_predictions,
            threshold,
        )
        metrics = evaluate(hybrid, gold)

        sweep.append(
            {
                "threshold": threshold,
                **metrics,
                **counts,
            }
        )

    results = {
        "experiment": "EXP-013",
        "status": "completed",
        "evaluation_date_utc": datetime.now(timezone.utc).isoformat(),
        "confidence_definition": (
            "maximum softmax probability assigned to the predicted class "
            "among tokens overlapping the entity span"
        ),
        "dictionary_baseline": evaluate(dictionary_predictions, gold),
        "threshold_sweep": sweep,
    }

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-013 hybrid confidence sweep ===")
    print(
        "Dictionary baseline: "
        f"P={results['dictionary_baseline']['precision']:.4f} "
        f"R={results['dictionary_baseline']['recall']:.4f} "
        f"F1={results['dictionary_baseline']['f1']:.4f}"
    )

    for row in sweep:
        print(
            f"threshold={row['threshold']:.2f} "
            f"P={row['precision']:.4f} "
            f"R={row['recall']:.4f} "
            f"F1={row['f1']:.4f} "
            f"added={row['pubmedbert_added']}"
        )

    print(f"Results saved to: {OUTPUT}")


if __name__ == "__main__":
    main()