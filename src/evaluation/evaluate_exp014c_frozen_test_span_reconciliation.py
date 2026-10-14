"""Evaluate the EXP-014C frozen union-span reconciliation strategy on test data.

The reconciliation strategy was selected using the BC5CDR development set only.
The confidence threshold was selected by EXP-014A using development data only.

This script performs one final test-set evaluation of:

1. the dictionary extractor;
2. the PubMedBERT-only extractor;
3. the EXP-014A dictionary-preferred hybrid;
4. the EXP-014C frozen union-span reconciled hybrid.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = PROJECT_ROOT / "output" / "evaluation" / "exp012"
OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp014c_frozen_test_span_reconciliation.json"
)

FROZEN_THRESHOLD = 0.95
FROZEN_STRATEGY = "union_span"


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


def build_reconciled_hybrid(
    dictionary_predictions,
    transformer_predictions,
    threshold,
    strategy,
):
    dictionary_by_document_type = defaultdict(list)

    for prediction in dictionary_predictions:
        key = (
            prediction["document_id"],
            prediction["entity_type"],
        )
        dictionary_by_document_type[key].append(prediction)

    records_by_key = {}

    for prediction in dictionary_predictions:
        records_by_key[prediction_key(prediction)] = prediction

    counts = {
        "dictionary_retained": len(dictionary_predictions),
        "pubmedbert_added_non_overlapping": 0,
        "pubmedbert_below_threshold": 0,
        "reconciled_groups": 0,
        "dictionary_predictions_replaced": 0,
    }

    for prediction in transformer_predictions:
        if prediction["confidence"] < threshold:
            counts["pubmedbert_below_threshold"] += 1
            continue

        overlapping = [
            candidate
            for candidate in dictionary_by_document_type.get(
                (
                    prediction["document_id"],
                    prediction["entity_type"],
                ),
                [],
            )
            if spans_overlap(prediction, candidate)
        ]

        if not overlapping:
            records_by_key[prediction_key(prediction)] = prediction
            counts["pubmedbert_added_non_overlapping"] += 1
            continue

        counts["reconciled_groups"] += 1

        if strategy == "dictionary_preferred":
            continue

        counts["dictionary_predictions_replaced"] += len(overlapping)

        for candidate in overlapping:
            records_by_key.pop(prediction_key(candidate), None)

        if strategy == "transformer_preferred":
            replacement = [prediction]
        elif strategy == "longer_span_preferred":
            longest_dictionary = max(
                overlapping,
                key=lambda item: item["end"] - item["start"],
            )
            dictionary_length = (
                longest_dictionary["end"] - longest_dictionary["start"]
            )
            transformer_length = (
                prediction["end"] - prediction["start"]
            )

            replacement = (
                [prediction]
                if transformer_length > dictionary_length
                else [longest_dictionary]
            )
        elif strategy == "union_span":
            start = min(
                [prediction["start"]]
                + [item["start"] for item in overlapping]
            )
            end = max(
                [prediction["end"]]
                + [item["end"] for item in overlapping]
            )
            replacement = [
                {
                    "document_id": prediction["document_id"],
                    "start": start,
                    "end": end,
                    "entity_type": prediction["entity_type"],
                    "mention": prediction.get("mention", ""),
                    "confidence": prediction.get("confidence"),
                    "source": "reconciled_union",
                }
            ]
        elif strategy == "intersection_span":
            start = max(
                [prediction["start"]]
                + [item["start"] for item in overlapping]
            )
            end = min(
                [prediction["end"]]
                + [item["end"] for item in overlapping]
            )

            if start < end:
                replacement = [
                    {
                        "document_id": prediction["document_id"],
                        "start": start,
                        "end": end,
                        "entity_type": prediction["entity_type"],
                        "mention": prediction.get("mention", ""),
                        "confidence": prediction.get("confidence"),
                        "source": "reconciled_intersection",
                    }
                ]
            else:
                replacement = [
                    max(
                        overlapping,
                        key=lambda item: item["end"] - item["start"],
                    )
                ]
        else:
            raise ValueError(f"Unknown reconciliation strategy: {strategy}")

        for record in replacement:
            records_by_key[prediction_key(record)] = record

    return list(records_by_key.values()), counts


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

    dictionary_preferred, dictionary_preferred_counts = build_reconciled_hybrid(
        dictionary_predictions,
        transformer_predictions,
        FROZEN_THRESHOLD,
        "dictionary_preferred",
    )
    dictionary_preferred_metrics = evaluate(dictionary_preferred, gold)

    reconciled, reconciled_counts = build_reconciled_hybrid(
        dictionary_predictions,
        transformer_predictions,
        FROZEN_THRESHOLD,
        FROZEN_STRATEGY,
    )
    reconciled_metrics = evaluate(reconciled, gold)

    results = {
        "experiment": "EXP-014C",
        "status": "completed",
        "evaluation_date_utc": datetime.now(timezone.utc).isoformat(),
        "split": "BC5CDR test set",
        "evaluation_type": "final frozen-configuration evaluation",
        "frozen_confidence_threshold": FROZEN_THRESHOLD,
        "frozen_reconciliation_strategy": FROZEN_STRATEGY,
        "threshold_selection_split": "BC5CDR development set",
        "strategy_selection_split": "BC5CDR development set",
        "matching_policy": (
            "document-level character offsets; location-level gold spans; "
            "type-aware exact-span matching"
        ),
        "dictionary_baseline": dictionary_metrics,
        "pubmedbert_only": transformer_metrics,
        "dictionary_preferred_hybrid": {
            **dictionary_preferred_metrics,
            **dictionary_preferred_counts,
        },
        "frozen_reconciled_hybrid": {
            **reconciled_metrics,
            **reconciled_counts,
        },
    }

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-014C frozen test-set evaluation ===")
    print(
        f"Frozen threshold: {FROZEN_THRESHOLD:.2f}; "
        f"frozen strategy: {FROZEN_STRATEGY}"
    )

    for label, metrics in (
        ("Dictionary", dictionary_metrics),
        ("PubMedBERT only", transformer_metrics),
        ("EXP-014A dictionary-preferred hybrid", dictionary_preferred_metrics),
        ("EXP-014C union-span reconciled hybrid", reconciled_metrics),
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