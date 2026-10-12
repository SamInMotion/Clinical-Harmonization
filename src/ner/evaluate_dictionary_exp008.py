"""Evaluate the dictionary NER baseline on the BC5CDR test set.

Uses the same location-level, exact document-character-span, and entity-type
match rule as EXP-007 PubMedBERT evaluation.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import load_dictionary, extract_entities_from_text


TEST_XML = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bc5cdr"
    / "CDR_Data"
    / "CDR.Corpus.v010516"
    / "CDR_TestSet.BioC.xml"
)

TRAIN_XML = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bc5cdr"
    / "CDR_Data"
    / "CDR.Corpus.v010516"
    / "CDR_TrainingSet.BioC.xml"
)

DICTIONARY = (
    PROJECT_ROOT
    / "data"
    / "terminology"
    / "bc5cdr_dictionary.json"
)

OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp008_dictionary_bc5cdr_test_location_level.json"
)


def gold_entities(documents):
    entities = []

    for document in documents:
        for passage in document["passages"]:
            for annotation in passage["annotations"]:
                entity_type = annotation["type"]

                if entity_type not in ("Chemical", "Disease"):
                    continue

                for location in annotation["locations"]:
                    start = location["doc_offset"]
                    end = start + location["length"]

                    if start >= end:
                        continue

                    entities.append(
                        (
                            document["id"],
                            start,
                            end,
                            entity_type,
                        )
                    )

    return entities


def predicted_entities(documents, dictionary, min_length):
    entities = []

    for document in documents:
        for passage in document["passages"]:
            passage_offset = passage["offset"]
            text = passage["text"] or ""

            for match in extract_entities_from_text(
                text,
                dictionary,
                min_length=min_length,
            ):
                start = passage_offset + match["offset"]
                end = start + match["length"]

                entities.append(
                    (
                        document["id"],
                        start,
                        end,
                        match["type"],
                    )
                )

    return entities


def compute_metrics(gold, predicted):
    gold_set = set(gold)
    predicted_set = set(predicted)

    exact = gold_set & predicted_set
    false_positives = predicted_set - gold_set
    false_negatives = gold_set - predicted_set

    precision = len(exact) / len(predicted_set) if predicted_set else 0.0
    recall = len(exact) / len(gold_set) if gold_set else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "gold_entities": len(gold_set),
        "predicted_entities": len(predicted_set),
        "exact_matches": len(exact),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def per_type(gold, predicted, entity_type):
    type_gold = [entity for entity in gold if entity[3] == entity_type]
    type_predicted = [
        entity for entity in predicted if entity[3] == entity_type
    ]
    return compute_metrics(type_gold, type_predicted)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test-xml",
        default=str(TEST_XML),
    )
    parser.add_argument(
        "--dictionary",
        default=str(DICTIONARY),
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT),
    )
    args = parser.parse_args()

    documents = load_bc5cdr(args.test_xml)
    dictionary = load_dictionary(args.dictionary)

    gold = gold_entities(documents)
    predicted = predicted_entities(
        documents, dictionary, args.min_length
    )

    overall = compute_metrics(gold, predicted)

    results = {
        "experiment": "EXP-008",
        "system": "dictionary_baseline",
        "status": "completed",
        "evaluation_date_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "test_xml": str(Path(args.test_xml).resolve()),
        "dictionary_path": str(Path(args.dictionary).resolve()),
        "minimum_mention_length": args.min_length,
        "gold_policy": "one entity per BioC annotation location",
        "match_rule": "exact document-level character span and entity type",
        "overall": overall,
        "chemical": per_type(gold, predicted, "Chemical"),
        "disease": per_type(gold, predicted, "Disease"),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-008 dictionary baseline: location-level evaluation ===")
    print(f"Gold entities: {overall['gold_entities']}")
    print(f"Predicted entities: {overall['predicted_entities']}")
    print(f"Exact matches: {overall['exact_matches']}")
    print(f"Precision: {overall['precision']:.4f}")
    print(f"Recall: {overall['recall']:.4f}")
    print(f"F1: {overall['f1']:.4f}")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()