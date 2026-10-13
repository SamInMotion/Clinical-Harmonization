"""
Analyze partial-overlap false negatives on the BC5CDR development set.

Gate D-3 diagnostic. This script does not modify the dictionary baseline,
evaluator, corpus, linking, OMOP, FHIR, or transformer components.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import extract_entities_from_text
from gold_spans import extract_gold_location_spans, entity_to_key


def categorize_overlap(gold, prediction):
    gold_start = gold["offset"]
    gold_end = gold_start + gold["length"]
    prediction_start = prediction["offset"]
    prediction_end = prediction_start + prediction["length"]

    if (
        prediction_start <= gold_start
        and prediction_end >= gold_end
    ):
        return "prediction_contains_gold"

    if (
        gold_start <= prediction_start
        and gold_end >= prediction_end
    ):
        return "gold_contains_prediction"

    if prediction_start < gold_start:
        return "prediction_starts_earlier"

    if prediction_end > gold_end:
        return "prediction_ends_later"

    return "internal_offset_mismatch"


def main():
    development_path = Path(
        "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        "CDR_DevelopmentSet.BioC.xml"
    )
    dictionary_path = Path(
        "data/terminology/bc5cdr_dictionary.json"
    )

    with dictionary_path.open("r", encoding="utf-8") as file:
        dictionary = json.load(file)

    documents = load_bc5cdr(str(development_path))
    gold_spans = extract_gold_location_spans(documents)

    predictions_by_document = defaultdict(list)

    for doc in documents:
        for passage in doc["passages"]:
            matches = extract_entities_from_text(
                passage["text"], dictionary, min_length=4
            )

            for match in matches:
                predictions_by_document[
                    (doc["id"], passage["type"])
                ].append({
                    **match,
                    "doc_id": doc["id"],
                    "passage_type": passage["type"],
                })

    gold_keys = {
        entity_to_key(span): span for span in gold_spans
    }

    false_negative_spans = [
        span
        for key, span in gold_keys.items()
        if key not in {
            entity_to_key(prediction)
            for prediction in predictions_by_document[
                (span["doc_id"], span["passage_type"])
            ]
        }
    ]

    category_counts = Counter()
    overlap_records = []

    for gold in false_negative_spans:
        candidates = predictions_by_document[
            (gold["doc_id"], gold["passage_type"])
        ]

        overlapping = [
            prediction
            for prediction in candidates
            if (
                prediction["offset"]
                < gold["offset"] + gold["length"]
                and prediction["offset"] + prediction["length"]
                > gold["offset"]
            )
        ]

        if not overlapping:
            continue

        best_prediction = max(
            overlapping,
            key=lambda prediction: (
                min(
                    prediction["offset"] + prediction["length"],
                    gold["offset"] + gold["length"],
                )
                - max(
                    prediction["offset"], gold["offset"]
                )
            ),
        )

        category = categorize_overlap(gold, best_prediction)
        category_counts[category] += 1

        overlap_records.append({
            "doc_id": gold["doc_id"],
            "passage_type": gold["passage_type"],
            "gold_text": gold["text"],
            "gold_type": gold["type"],
            "gold_offset": gold["offset"],
            "gold_length": gold["length"],
            "predicted_text": best_prediction["text"],
            "predicted_type": best_prediction["type"],
            "predicted_offset": best_prediction["offset"],
            "predicted_length": best_prediction["length"],
            "overlap_category": category,
            "overlapping_prediction_count": len(overlapping),
        })

    summary = {
        "date": "2026-10-11",
        "dataset": "BC5CDR development set",
        "evaluation_policy": (
            "Gate C-2 location-level, type-aware exact-span matching"
        ),
        "gold_location_spans": len(gold_spans),
        "false_negative_spans": len(false_negative_spans),
        "partial_overlap_false_negatives": len(overlap_records),
        "category_counts": dict(category_counts),
        "overlaps": overlap_records,
    }

    output_directory = Path("output/evaluation")
    output_directory.mkdir(parents=True, exist_ok=True)

    json_path = output_directory / "partial_overlap_analysis.json"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    markdown_path = output_directory / "partial_overlap_analysis.md"
    with markdown_path.open("w", encoding="utf-8") as file:
        file.write("# Partial-Overlap False-Negative Analysis\n\n")
        file.write(
            "Diagnostic analysis of development-set false negatives "
            "that overlap at least one dictionary prediction.\n\n"
        )
        file.write("## Overlap categories\n\n")
        file.write("| Category | False negatives |\n")
        file.write("|---|---:|\n")
        for category, count in sorted(
            category_counts.items(),
            key=lambda item: -item[1],
        ):
            file.write(f"| {category} | {count} |\n")

        file.write("\n## Representative examples\n\n")
        for record in overlap_records[:30]:
            file.write(
                f"- `{record['gold_text']}` "
                f"({record['gold_type']}) versus "
                f"`{record['predicted_text']}` "
                f"({record['predicted_type']}) — "
                f"{record['overlap_category']}\n"
            )

    print(f"Gold location spans: {len(gold_spans)}")
    print(f"False-negative spans: {len(false_negative_spans)}")
    print(f"Partial-overlap false negatives: {len(overlap_records)}")
    print("\nOverlap categories:")
    for category, count in sorted(
        category_counts.items(), key=lambda item: -item[1]
    ):
        print(f"  {category}: {count}")

    print(f"\nJSON written to: {json_path}")
    print(f"Markdown written to: {markdown_path}")


if __name__ == "__main__":
    main()
