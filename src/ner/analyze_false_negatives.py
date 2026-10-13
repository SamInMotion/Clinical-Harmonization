"""
Analyze false negatives from the Gate C-2 dictionary NER evaluation.

Usage:
    python src/ner/analyze_false_negatives.py

Output:
    - output/evaluation/false_negative_analysis.json
    - output/evaluation/false_negative_analysis.md

This script does not modify the dictionary baseline, evaluator, corpus,
linking, OMOP, FHIR, or transformer components.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import (
    extract_entities_from_text,
    normalize_text,
)
from gold_spans import extract_gold_location_spans, entity_to_key


def is_abbreviation_like(text: str) -> bool:
    """
    Identify a conservative abbreviation/acronym-like surface form.
    """
    stripped = text.strip()
    return (
        len(stripped) <= 5
        and stripped.isupper()
        and any(character.isalpha() for character in stripped)
    )


def main():
    dictionary_path = Path(
        "data/terminology/bc5cdr_dictionary.json"
    )
    test_path = Path(
        "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        "CDR_TestSet.BioC.xml"
    )

    if not dictionary_path.exists():
        raise FileNotFoundError(
            f"Dictionary not found: {dictionary_path}"
        )
    if not test_path.exists():
        raise FileNotFoundError(f"Test set not found: {test_path}")

    with dictionary_path.open("r", encoding="utf-8") as file:
        dictionary = json.load(file)

    documents = load_bc5cdr(str(test_path))
    gold_spans = extract_gold_location_spans(documents)

    predicted_spans = []
    for doc in documents:
        for passage in doc["passages"]:
            matches = extract_entities_from_text(
                passage["text"], dictionary, min_length=4
            )
            for match in matches:
                predicted_spans.append({
                    **match,
                    "doc_id": doc["id"],
                    "passage_type": passage["type"],
                })

    gold_keys = {
        entity_to_key(span): span for span in gold_spans
    }
    predicted_keys = {
        entity_to_key(span): span for span in predicted_spans
    }

    false_negative_keys = set(gold_keys) - set(predicted_keys)

    predictions_by_document = defaultdict(list)
    for span in predicted_spans:
        predictions_by_document[
            (span["doc_id"], span["passage_type"])
        ].append(span)

    annotation_location_counts = {}
    for doc in documents:
        for passage in doc["passages"]:
            for annotation_index, annotation in enumerate(
                passage["annotations"]
            ):
                key = (
                    doc["id"],
                    passage["type"],
                    annotation_index,
                )
                annotation_location_counts[key] = len(
                    annotation["locations"]
                )

    category_counts = defaultdict(int)
    fn_records = []
    missed_form_counts = defaultdict(int)

    for key in sorted(false_negative_keys):
        gold = gold_keys[key]
        normalized = normalize_text(gold["text"])

        same_document_predictions = predictions_by_document[
            (gold["doc_id"], gold["passage_type"])
        ]

        overlapping = [
            prediction
            for prediction in same_document_predictions
            if (
                prediction["offset"]
                < gold["offset"] + gold["length"]
                and prediction["offset"] + prediction["length"]
                > gold["offset"]
            )
        ]

        exact_location_type_mismatch = any(
            prediction["offset"] == gold["offset"]
            and prediction["length"] == gold["length"]
            and prediction["type"] != gold["type"]
            for prediction in overlapping
        )

        location_count = annotation_location_counts.get(
            (
                gold["doc_id"],
                gold["passage_type"],
                gold["annotation_index"],
            ),
            1,
        )

        tags = []

        if exact_location_type_type_mismatch if False else exact_location_type_mismatch:
            tags.append("type_mismatch")

        if overlapping and not exact_location_type_mismatch:
            tags.append("partial_overlap")

        if location_count > 1:
            tags.append("multi_location")

        if normalized not in dictionary:
            tags.append("unseen_normalized_form")

        if is_abbreviation_like(gold["text"]):
            tags.append("abbreviation_like")

        if not tags:
            tags.append("other")

        primary_category = (
            "type_mismatch"
            if "type_mismatch" in tags
            else
            "partial_overlap"
            if "partial_overlap" in tags
            else
            "multi_location"
            if "multi_location" in tags
            else
            "abbreviation_like"
            if "abbreviation_like" in tags
            else
            "unseen_normalized_form"
            if "unseen_normalized_form" in tags
            else
            "other"
        )

        category_counts[primary_category] += 1
        missed_form_counts[normalized] += 1

        fn_records.append({
            "doc_id": gold["doc_id"],
            "passage_type": gold["passage_type"],
            "text": gold["text"],
            "normalized_text": normalized,
            "type": gold["type"],
            "offset": gold["offset"],
            "length": gold["length"],
            "mesh_id": gold["mesh_id"],
            "annotation_index": gold["annotation_index"],
            "location_index": gold["location_index"],
            "is_multi_location": location_count > 1,
            "in_dictionary": normalized in dictionary,
            "overlapping_prediction_count": len(overlapping),
            "tags": tags,
            "primary_category": primary_category,
        })

    top_missed_forms = sorted(
        missed_form_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[:50]

    summary = {
        "date": "2026-10-10",
        "evaluation_policy": (
            "Gate C-2 location-level, type-aware exact-span matching"
        ),
        "gold_location_spans": len(gold_spans),
        "predicted_entities": len(predicted_spans),
        "false_negatives": len(false_negative_keys),
        "primary_category_counts": dict(category_counts),
        "top_missed_normalized_forms": [
            {"normalized_form": form, "missed_count": count}
            for form, count in top_missed_forms
        ],
        "false_negatives": fn_records,
    }

    output_directory = Path("output/evaluation")
    output_directory.mkdir(parents=True, exist_ok=True)

    json_path = output_directory / "false_negative_analysis.json"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    markdown_path = output_directory / "false_negative_analysis.md"
    with markdown_path.open("w", encoding="utf-8") as file:
        file.write("# False-Negative Analysis — Gate C-2\n\n")
        file.write(
            "This analysis categorizes the 4,339 false-negative "
            "location spans from the Gate C-2 dictionary baseline.\n\n"
        )
        file.write(
            "It is diagnostic evidence only; no accuracy claim is "
            "implied.\n\n"
        )
        file.write("## Primary categories\n\n")
        file.write("| Category | False negatives |\n")
        file.write("|---|---:|\n")
        for category, count in sorted(
            category_counts.items(),
            key=lambda item: -item[1],
        ):
            file.write(f"| {category} | {count} |\n")

        file.write("\n## Top missed normalized forms\n\n")
        file.write("| Normalized form | Missed count |\n")
        file.write("|---|---:|\n")
        for form, count in top_missed_forms:
            file.write(f"| {form} | {count} |\n")

    print(f"Gold location spans: {len(gold_spans)}")
    print(f"Predicted entities: {len(predicted_spans)}")
    print(f"False negatives: {len(false_negative_keys)}")
    print("\nPrimary categories:")
    for category, count in sorted(
        category_counts.items(), key=lambda item: -item[1]
    ):
        print(f"  {category}: {count}")

    print(f"\nJSON written to: {json_path}")
    print(f"Markdown written to: {markdown_path}")


if __name__ == "__main__":
    main()
