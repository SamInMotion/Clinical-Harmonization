"""
Compare baseline and abbreviation-expanded dictionaries on BC5CDR development.

Gate D-2 evaluation uses the same location-level, type-aware exact-span
policy as Gate C-2. No test-set data is used.
"""

import json
from collections import defaultdict
from pathlib import Path

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import extract_entities_from_text
from gold_spans import extract_gold_location_spans, entity_to_key


def load_dictionary(path):
    with path.open("r", encoding="utf-8") as file:
        return defaultdict(list, json.load(file))


def extract_predictions(documents, dictionary):
    predictions = []

    for doc in documents:
        for passage in doc["passages"]:
            matches = extract_entities_from_text(
                passage["text"], dictionary, min_length=4
            )

            for match in matches:
                predictions.append({
                    **match,
                    "doc_id": doc["id"],
                    "passage_type": passage["type"],
                })

    return predictions


def calculate_metrics(gold_spans, predicted_spans):
    gold_keys = set(entity_to_key(span) for span in gold_spans)
    predicted_keys = set(
        entity_to_key(span) for span in predicted_spans
    )

    tp_keys = gold_keys & predicted_keys
    fp_keys = predicted_keys - gold_keys
    fn_keys = gold_keys - predicted_keys

    tp = len(tp_keys)
    fp = len(fp_keys)
    fn = len(fn_keys)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "gold_spans": len(gold_spans),
        "predicted_entities": len(predicted_spans),
    }


def main():
    development_path = Path(
        "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        "CDR_DevelopmentSet.BioC.xml"
    )
    baseline_path = Path(
        "data/terminology/bc5cdr_dictionary.json"
    )
    expanded_path = Path(
        "data/terminology/"
        "bc5cdr_dictionary_abbreviation_expanded.json"
    )
    output_path = Path(
        "output/evaluation/"
        "development_abbreviation_expansion_comparison.json"
    )
    markdown_path = Path(
        "output/evaluation/"
        "development_abbreviation_expansion_comparison.md"
    )

    documents = load_bc5cdr(str(development_path))
    gold_spans = extract_gold_location_spans(documents)

    baseline_dictionary = load_dictionary(baseline_path)
    expanded_dictionary = load_dictionary(expanded_path)

    baseline_predictions = extract_predictions(
        documents, baseline_dictionary
    )
    expanded_predictions = extract_predictions(
        documents, expanded_dictionary
    )

    baseline_metrics = calculate_metrics(
        gold_spans, baseline_predictions
    )
    expanded_metrics = calculate_metrics(
        gold_spans, expanded_predictions
    )

    results = {
        "date": "2026-10-11",
        "dataset": "BC5CDR development set",
        "evaluation_policy": (
            "Gate C-2 location-level, type-aware exact-span matching"
        ),
        "baseline": baseline_metrics,
        "abbreviation_expanded": expanded_metrics,
        "differences": {
            "precision": (
                expanded_metrics["precision"]
                - baseline_metrics["precision"]
            ),
            "recall": (
                expanded_metrics["recall"]
                - baseline_metrics["recall"]
            ),
            "f1": (
                expanded_metrics["f1"] - baseline_metrics["f1"]
            ),
            "true_positives": (
                expanded_metrics["tp"] - baseline_metrics["tp"]
            ),
            "false_positives": (
                expanded_metrics["fp"] - baseline_metrics["fp"]
            ),
            "false_negatives": (
                expanded_metrics["fn"] - baseline_metrics["fn"]
            ),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    with markdown_path.open("w", encoding="utf-8") as file:
        file.write(
            "# Development Comparison: "
            "Baseline vs Abbreviation-Expanded Dictionary\n\n"
        )
        file.write(
            "Evaluation policy: Gate C-2 location-level, "
            "type-aware exact-span matching.\n\n"
        )
        file.write("| Metric | Baseline | Expanded | Difference |\n")
        file.write("|---|---:|---:|---:|\n")

        for metric in (
            "precision", "recall", "f1",
            "tp", "fp", "fn",
            "gold_spans", "predicted_entities",
        ):
            baseline_value = baseline_metrics[metric]
            expanded_value = expanded_metrics[metric]
            difference = expanded_value - baseline_value

            if metric in {
                "precision", "recall", "f1"
            }:
                file.write(
                    f"| {metric} | {baseline_value:.4f} | "
                    f"{expanded_value:.4f} | {difference:+.4f} |\n"
                )
            else:
                file.write(
                    f"| {metric} | {baseline_value} | "
                    f"{expanded_value} | {difference:+d} |\n"
                )

    print(f"Gold location spans: {len(gold_spans)}")
    print("\nBaseline:")
    print(json.dumps(baseline_metrics, indent=2))
    print("\nAbbreviation-expanded:")
    print(json.dumps(expanded_metrics, indent=2))
    print("\nDifferences:")
    print(json.dumps(results["differences"], indent=2))
    print(f"\nJSON written to: {output_path}")
    print(f"Markdown written to: {markdown_path}")


if __name__ == "__main__":
    main()
