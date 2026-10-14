"""Evaluate span-reconciliation strategies for the EXP-014A hybrid extractor.

This experiment uses the BC5CDR development set only. It evaluates strategies
for reconciling same-type overlapping dictionary and PubMedBERT predictions.

The confidence threshold remains fixed at 0.95, selected by EXP-014A using
development data.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = PROJECT_ROOT / "output" / "evaluation" / "exp014a"
OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp014c_development_span_reconciliation.json"
)

FROZEN_THRESHOLD = 0.95

STRATEGIES = [
    "dictionary_preferred",
    "transformer_preferred",
    "longer_span_preferred",
    "union_span",
    "intersection_span",
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


def reconcile_span(strategy, dictionary_predictions, transformer_prediction):
    """Return replacement predictions for overlapping same-type pairs."""

    if strategy == "transformer_preferred":
        return [transformer_prediction]

    if strategy == "longer_span_preferred":
        longest_dictionary = max(
            dictionary_predictions,
            key=lambda prediction: prediction["end"] - prediction["start"],
        )
        dictionary_length = (
            longest_dictionary["end"] - longest_dictionary["start"]
        )
        transformer_length = (
            transformer_prediction["end"] - transformer_prediction["start"]
        )

        if transformer_length > dictionary_length:
            return [transformer_prediction]
        return [longest_dictionary]

    if strategy == "union_span":
        start = min(
            [transformer_prediction["start"]]
            + [prediction["start"] for prediction in dictionary_predictions]
        )
        end = max(
            [transformer_prediction["end"]]
            + [prediction["end"] for prediction in dictionary_predictions]
        )
        return [
            {
                "document_id": transformer_prediction["document_id"],
                "start": start,
                "end": end,
                "entity_type": transformer_prediction["entity_type"],
                "mention": transformer_prediction.get("mention", ""),
                "confidence": transformer_prediction.get("confidence"),
                "source": "reconciled_union",
            }
        ]

    if strategy == "intersection_span":
        start = max(
            [transformer_prediction["start"]]
            + [prediction["start"] for prediction in dictionary_predictions]
        )
        end = min(
            [transformer_prediction["end"]]
            + [prediction["end"] for prediction in dictionary_predictions]
        )

        if start < end:
            return [
                {
                    "document_id": transformer_prediction["document_id"],
                    "start": start,
                    "end": end,
                    "entity_type": transformer_prediction["entity_type"],
                    "mention": transformer_prediction.get("mention", ""),
                    "confidence": transformer_prediction.get("confidence"),
                    "source": "reconciled_intersection",
                }
            ]

        longest_dictionary = max(
            dictionary_predictions,
            key=lambda prediction: prediction["end"] - prediction["start"],
        )
        return [longest_dictionary]

    if strategy == "dictionary_preferred":
        return dictionary_predictions

    raise ValueError(f"Unknown reconciliation strategy: {strategy}")

def build_reconciled_hybrid(
    dictionary_predictions,
    transformer_predictions,
    threshold,
    strategy,
):
    """Build a reconciled hybrid without dropping retained dictionary spans."""

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
            # Retain the dictionary predictions and discard the
            # overlapping transformer prediction.
            continue

        counts["dictionary_predictions_replaced"] += len(overlapping)

        for candidate in overlapping:
            records_by_key.pop(prediction_key(candidate), None)

        replacement = reconcile_span(
            strategy,
            overlapping,
            prediction,
        )

        for record in replacement:
            records_by_key[prediction_key(record)] = record

    hybrid = list(records_by_key.values())
    return hybrid, counts





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
    strategy_results = []

    for strategy in STRATEGIES:
        hybrid, counts = build_reconciled_hybrid(
            dictionary_predictions,
            transformer_predictions,
            FROZEN_THRESHOLD,
            strategy,
        )
        metrics = evaluate(hybrid, gold)

        strategy_results.append(
            {
                "strategy": strategy,
                "metrics": metrics,
                "build_counts": counts,
            }
        )

    selected = max(
        strategy_results,
        key=lambda result: (
            result["metrics"]["f1"],
            result["metrics"]["precision"],
        ),
    )

    results = {
        "experiment": "EXP-014C",
        "status": "completed",
        "evaluation_date_utc": datetime.now(timezone.utc).isoformat(),
        "split": "BC5CDR development set",
        "purpose": (
            "Development-only selection of a span-reconciliation strategy "
            "for same-type overlapping dictionary and PubMedBERT predictions"
        ),
        "frozen_confidence_threshold": FROZEN_THRESHOLD,
        "threshold_selection_experiment": "EXP-014A",
        "selection_rule": (
            "Select the strategy with maximum development-set F1; "
            "break ties by higher precision."
        ),
        "dictionary_baseline": dictionary_metrics,
        "strategy_results": strategy_results,
        "selected_strategy": selected["strategy"],
        "selected_metrics": selected["metrics"],
    }

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-014C development span-reconciliation sweep ===")
    print(
        "Dictionary baseline: "
        f"P={dictionary_metrics['precision']:.4f} "
        f"R={dictionary_metrics['recall']:.4f} "
        f"F1={dictionary_metrics['f1']:.4f}"
    )

    for result in strategy_results:
        metrics = result["metrics"]
        marker = (
            " <-- selected"
            if result["strategy"] == selected["strategy"]
            else ""
        )
        print(
            f"{result['strategy']}: "
            f"P={metrics['precision']:.4f} "
            f"R={metrics['recall']:.4f} "
            f"F1={metrics['f1']:.4f} "
            f"TP={metrics['true_positives']} "
            f"FP={metrics['false_positives']} "
            f"FN={metrics['false_negatives']}"
            f"{marker}"
        )

    print(
        "\nSelected strategy: "
        f"{selected['strategy']} "
        f"(P={selected['metrics']['precision']:.4f}, "
        f"R={selected['metrics']['recall']:.4f}, "
        f"F1={selected['metrics']['f1']:.4f})"
    )
    print(f"Results saved to: {OUTPUT}")


if __name__ == "__main__":
    main()