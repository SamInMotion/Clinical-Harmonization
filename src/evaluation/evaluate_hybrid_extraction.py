"""Evaluate EXP-012 hybrid extraction.

Baseline: EXP-009 word-boundary dictionary predictions.
Alternative: EXP-007 PubMedBERT epoch-3 predictions.
Hybrid rule: retain all dictionary predictions; add transformer predictions
only when they do not overlap a dictionary prediction of the same entity type.
"""

import json
from collections import Counter
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
    / "exp012_hybrid_extraction.json"
)


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


def build_hybrid(dictionary_predictions, transformer_predictions):
    dictionary_by_document_type = {}

    for prediction in dictionary_predictions:
        key = (
            prediction["document_id"],
            prediction["entity_type"],
        )
        dictionary_by_document_type.setdefault(key, []).append(prediction)

    hybrid = []
    source_counts = Counter()
    overlap_counts = Counter()

    for prediction in dictionary_predictions:
        hybrid.append({**prediction, "hybrid_source": "dictionary"})
        source_counts["dictionary_retained"] += 1

    for prediction in transformer_predictions:
        candidates = dictionary_by_document_type.get(
            (
                prediction["document_id"],
                prediction["entity_type"],
            ),
            [],
        )

        if any(spans_overlap(prediction, candidate) for candidate in candidates):
            overlap_counts["transformer_overlaps_dictionary"] += 1
            continue

        hybrid.append({**prediction, "hybrid_source": "pubmedbert"})
        source_counts["pubmedbert_added"] += 1

    return hybrid, source_counts, overlap_counts


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
        "gold_entities": len(gold_keys),
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

    hybrid, source_counts, overlap_counts = build_hybrid(
        dictionary_predictions,
        transformer_predictions,
    )

    results = {
        "experiment": "EXP-012",
        "status": "completed",
        "evaluation_date_utc": datetime.now(timezone.utc).isoformat(),
        "dictionary_baseline": "EXP-009 word-boundary dictionary",
        "transformer_alternative": "EXP-007 PubMedBERT epoch 3",
        "hybrid_rule": (
            "retain dictionary predictions; add non-overlapping "
            "PubMedBERT predictions of the same entity type"
        ),
        "dictionary_only": evaluate(dictionary_predictions, gold),
        "pubmedbert_only": evaluate(transformer_predictions, gold),
        "hybrid": evaluate(hybrid, gold),
        "source_counts": dict(source_counts),
        "overlap_counts": dict(overlap_counts),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-012 hybrid extraction evaluation ===")

    for name in ("dictionary_only", "pubmedbert_only", "hybrid"):
        metrics = results[name]
        print(
            f"{name}: "
            f"P={metrics['precision']:.4f} "
            f"R={metrics['recall']:.4f} "
            f"F1={metrics['f1']:.4f}"
        )

    print(f"Source counts: {results['source_counts']}")
    print(f"Overlap counts: {results['overlap_counts']}")
    print(f"Results saved to: {OUTPUT}")


if __name__ == "__main__":
    main()