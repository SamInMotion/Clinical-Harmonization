"""Analyze false positives from the EXP-014A frozen hybrid extractor.

This experiment analyzes the false positives produced by the development-selected,
frozen 0.95-confidence hybrid on the BC5CDR test set.

It distinguishes dictionary-origin false positives from transformer-added false
positives and characterizes the latter by entity type, confidence, span length,
gold overlap, recurring surface form, and likely boundary or substring behavior.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = PROJECT_ROOT / "output" / "evaluation" / "exp012"
OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp014b_hybrid_false_positive_analysis.json"
)

FROZEN_THRESHOLD = 0.95

CONFIDENCE_BANDS = [
    (0.95, 0.97),
    (0.97, 0.99),
    (0.99, 1.01),
]

SPAN_LENGTH_BANDS = [
    (1, 4),
    (4, 11),
    (11, 21),
    (21, 10_000),
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


def normalize_surface(text):
    return " ".join(text.lower().strip().split())


def confidence_band(confidence):
    for lower, upper in CONFIDENCE_BANDS:
        if lower <= confidence < upper:
            return f"{lower:.2f}-{upper:.2f}"
    return "unknown"


def span_length_band(length):
    for lower, upper in SPAN_LENGTH_BANDS:
        if lower <= length < upper:
            return f"{lower}-{upper - 1} characters"
    return "unknown"


def build_hybrid(dictionary_predictions, transformer_predictions, threshold):
    dictionary_by_document_type = defaultdict(list)

    for prediction in dictionary_predictions:
        key = (
            prediction["document_id"],
            prediction["entity_type"],
        )
        dictionary_by_document_type[key].append(prediction)

    hybrid = []
    origin_by_key = {}
    counts = {
        "dictionary_retained": 0,
        "pubmedbert_overlapping": 0,
        "pubmedbert_below_threshold": 0,
        "pubmedbert_added": 0,
    }

    for prediction in dictionary_predictions:
        hybrid.append(prediction)
        origin_by_key[prediction_key(prediction)] = "dictionary"
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
        origin_by_key[prediction_key(prediction)] = "pubmedbert_added"
        counts["pubmedbert_added"] += 1

    return hybrid, origin_by_key, counts


def overlap_summary(prediction, gold_by_document):
    candidates = gold_by_document.get(prediction["document_id"], [])
    overlapping = [
        gold
        for gold in candidates
        if spans_overlap(prediction, gold)
    ]

    same_type_overlapping = [
        gold
        for gold in overlapping
        if gold["entity_type"] == prediction["entity_type"]
    ]

    partial_overlap = bool(overlapping)
    same_type_partial_overlap = bool(same_type_overlapping)

    boundary_artifact = False
    substring_artifact = False

    prediction_text = normalize_surface(prediction.get("mention", ""))

    for gold in overlapping:
        gold_text = normalize_surface(gold.get("mention", ""))

        if not prediction_text or not gold_text:
            continue

        if prediction_text != gold_text:
            if prediction_text in gold_text or gold_text in prediction_text:
                substring_artifact = True

        starts_inside = (
            gold["start"] <= prediction["start"] < gold["end"]
        )
        ends_inside = (
            gold["start"] < prediction["end"] <= gold["end"]
        )

        if starts_inside or ends_inside:
            boundary_artifact = True

    return {
        "partial_overlap": partial_overlap,
        "same_type_partial_overlap": same_type_partial_overlap,
        "boundary_artifact": boundary_artifact,
        "substring_artifact": substring_artifact,
        "overlapping_gold_count": len(overlapping),
        "same_type_overlapping_gold_count": len(same_type_overlapping),
    }


def summarize_group(records, field):
    return dict(Counter(record[field] for record in records))


def main():
    gold = load_predictions(INPUT_DIR / "gold_entities.json")
    dictionary_predictions = load_predictions(
        INPUT_DIR / "dictionary_predictions.json"
    )
    transformer_predictions = load_predictions(
        INPUT_DIR / "pubmedbert_epoch3_predictions.json"
    )

    gold_by_document = defaultdict(list)
    for entity in gold:
        gold_by_document[entity["document_id"]].append(entity)

    gold_surface_forms = {
        normalize_surface(entity.get("mention", ""))
        for entity in gold
        if entity.get("mention")
    }

    hybrid, origin_by_key, build_counts = build_hybrid(
        dictionary_predictions,
        transformer_predictions,
        FROZEN_THRESHOLD,
    )

    gold_keys = {prediction_key(entity) for entity in gold}
    hybrid_keys = {prediction_key(entity) for entity in hybrid}

    false_positive_keys = hybrid_keys - gold_keys
    false_positives = [
        prediction
        for prediction in hybrid
        if prediction_key(prediction) in false_positive_keys
    ]

    analyzed = []

    for prediction in false_positives:
        key = prediction_key(prediction)
        origin = origin_by_key.get(key, "unknown")
        overlaps = overlap_summary(prediction, gold_by_document)

        surface = normalize_surface(prediction.get("mention", ""))

        analyzed.append(
            {
                "document_id": prediction["document_id"],
                "start": prediction["start"],
                "end": prediction["end"],
                "entity_type": prediction["entity_type"],
                "mention": prediction.get("mention", ""),
                "confidence": prediction.get("confidence"),
                "origin": origin,
                "surface_form_recurs_as_gold_elsewhere": (
                    surface in gold_surface_forms
                ),
                "span_length": prediction["end"] - prediction["start"],
                "confidence_band": confidence_band(
                    prediction.get("confidence", 0.0)
                ),
                "span_length_band": span_length_band(
                    prediction["end"] - prediction["start"]
                ),
                **overlaps,
            }
        )

    transformer_added = [
        record for record in analyzed if record["origin"] == "pubmedbert_added"
    ]
    dictionary_origin = [
        record for record in analyzed if record["origin"] == "dictionary"
    ]

    def error_profile(records):
        return {
            "count": len(records),
            "by_entity_type": summarize_group(records, "entity_type"),
            "by_confidence_band": summarize_group(records, "confidence_band"),
            "by_span_length_band": summarize_group(records, "span_length_band"),
            "partial_overlap": sum(
                1 for record in records if record["partial_overlap"]
            ),
            "same_type_partial_overlap": sum(
                1 for record in records if record["same_type_partial_overlap"]
            ),
            "boundary_artifact": sum(
                1 for record in records if record["boundary_artifact"]
            ),
            "substring_artifact": sum(
                1 for record in records if record["substring_artifact"]
            ),
            "surface_form_recurs_as_gold_elsewhere": sum(
                1
                for record in records
                if record["surface_form_recurs_as_gold_elsewhere"]
            ),
        }

    def representative_examples(records, limit=20):
        return [
            {
                "document_id": record["document_id"],
                "start": record["start"],
                "end": record["end"],
                "entity_type": record["entity_type"],
                "mention": record["mention"],
                "confidence": record["confidence"],
                "origin": record["origin"],
                "partial_overlap": record["partial_overlap"],
                "same_type_partial_overlap": record[
                    "same_type_partial_overlap"
                ],
                "boundary_artifact": record["boundary_artifact"],
                "substring_artifact": record["substring_artifact"],
                "surface_form_recurs_as_gold_elsewhere": record[
                    "surface_form_recurs_as_gold_elsewhere"
                ],
            }
            for record in records[:limit]
        ]

    results = {
        "experiment": "EXP-014B",
        "status": "completed",
        "evaluation_date_utc": datetime.now(timezone.utc).isoformat(),
        "input_split": "BC5CDR test set",
        "frozen_threshold": FROZEN_THRESHOLD,
        "threshold_selection_split": "BC5CDR development set",
        "confidence_definition": (
            "maximum softmax probability assigned to the predicted class "
            "among tokens overlapping the entity span"
        ),
        "matching_policy": (
            "document-level character offsets; location-level gold spans; "
            "type-aware exact-span matching"
        ),
        "hybrid_build_counts": build_counts,
        "total_false_positives": len(false_positives),
        "false_positives_by_origin": dict(
            Counter(record["origin"] for record in analyzed)
        ),
        "transformer_added_profile": error_profile(transformer_added),
        "dictionary_origin_profile": error_profile(dictionary_origin),
        "representative_transformer_added_examples": representative_examples(
            transformer_added
        ),
        "representative_dictionary_origin_examples": representative_examples(
            dictionary_origin
        ),
    }

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-014B frozen hybrid false-positive analysis ===")
    print(f"Frozen threshold: {FROZEN_THRESHOLD:.2f}")
    print(f"Total false positives: {len(false_positives)}")
    print(
        "False positives by origin: "
        f"{results['false_positives_by_origin']}"
    )

    print("\nTransformer-added false-positive profile:")
    for field, value in results["transformer_added_profile"].items():
        print(f"- {field}: {value}")

    print(f"\nResults saved to: {OUTPUT}")


if __name__ == "__main__":
    main()