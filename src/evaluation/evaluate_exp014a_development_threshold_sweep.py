"""Evaluate confidence-thresholded hybrid extraction on the BC5CDR development set.

This experiment selects one hybrid confidence threshold using development data
only. It does not evaluate or select a threshold using the BC5CDR test set.

Hybrid rule:
1. Retain every base-dictionary prediction.
2. Add a PubMedBERT prediction only when it does not overlap a dictionary
   prediction of the same entity type in the same document.
3. Accept that prediction only when its span confidence is at least the
   threshold.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp014a"
)

OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp014a_development_threshold_sweep.json"
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
            f"{missing_confidence} PubMedBERT predictions lack confidence."
        )

    dictionary_metrics = evaluate(dictionary_predictions, gold)

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

    selected = max(
        sweep,
        key=lambda row: (row["f1"], row["precision"]),
    )

    results = {
        "experiment": "EXP-014A",
        "status": "completed",
        "evaluation_date_utc": datetime.now(timezone.utc).isoformat(),
        "split": "BC5CDR development set",
        "purpose": (
            "Development-only confidence-threshold selection for the "
            "dictionary and PubMedBERT hybrid extractor"
        ),
        "confidence_definition": (
            "maximum softmax probability assigned to the predicted class "
            "among tokens overlapping the entity span"
        ),
        "selection_rule": (
            "Select the threshold with maximum development-set F1; "
            "break ties by higher precision."
        ),
        "dictionary_baseline": dictionary_metrics,
        "threshold_sweep": sweep,
        "selected_threshold": selected["threshold"],
        "selected_metrics": selected,
    }

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-014A development-set threshold sweep ===")
    print(
        "Dictionary baseline: "
        f"P={dictionary_metrics['precision']:.4f} "
        f"R={dictionary_metrics['recall']:.4f} "
        f"F1={dictionary_metrics['f1']:.4f}"
    )

    for row in sweep:
        marker = " <-- selected" if row["threshold"] == selected["threshold"] else ""
        print(
            f"threshold={row['threshold']:.2f} "
            f"P={row['precision']:.4f} "
            f"R={row['recall']:.4f} "
            f"F1={row['f1']:.4f} "
            f"added={row['pubmedbert_added']}"
            f"{marker}"
        )

    print(
        "\nSelected threshold: "
        f"{selected['threshold']:.2f} "
        f"(P={selected['precision']:.4f}, "
        f"R={selected['recall']:.4f}, "
        f"F1={selected['f1']:.4f})"
    )
    print(f"Results saved to: {OUTPUT}")


if __name__ == "__main__":
    main()