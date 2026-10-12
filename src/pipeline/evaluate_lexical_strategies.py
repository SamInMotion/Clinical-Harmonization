"""Compare dictionary extraction strategies against BC5CDR test gold.

Strategies:
1. substring: current EXP-009 dictionary matcher
2. word_boundary: dictionary matches constrained to word boundaries
3. word_boundary_aliases: word-boundary matching plus curated aliases
"""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import (
    load_dictionary,
    extract_entities_from_text,
)


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
    / "exp009_lexical_strategy_comparison.json"
)

ALIASES = {
    "hyperglycaemia": "hyperglycemia",
    "hypoglycaemia": "hypoglycemia",
}


def normalize(text):
    normalized = " ".join(text.lower().strip().split())
    return ALIASES.get(normalized, normalized)


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


def has_word_boundary(text, start, end):
    before_ok = start == 0 or not (
        text[start - 1].isalnum() or text[start - 1] == "_"
    )
    after_ok = end == len(text) or not (
        text[end].isalnum() or text[end] == "_"
    )
    return before_ok and after_ok


def extract_strategy(
    documents,
    dictionary,
    strategy,
    min_length=4,
):
    entities = []

    for document in documents:
        for passage in document["passages"]:
            text = passage["text"] or ""
            passage_offset = passage["offset"]

            matches = extract_entities_from_text(
                text,
                dictionary,
                min_length=min_length,
            )

            for match in matches:
                if strategy in (
                    "word_boundary",
                    "word_boundary_aliases",
                ):
                    start = match["offset"]
                    end = start + match["length"]

                    if not has_word_boundary(text, start, end):
                        continue

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-xml", default=str(TEST_XML))
    parser.add_argument("--dictionary", default=str(DICTIONARY))
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()

    documents = load_bc5cdr(args.test_xml)
    dictionary = load_dictionary(args.dictionary)

    gold = gold_entities(documents)

    strategies = {
        "substring": extract_strategy(
            documents, dictionary, "substring"
        ),
        "word_boundary": extract_strategy(
            documents, dictionary, "word_boundary"
        ),
        "word_boundary_aliases": extract_strategy(
            documents, dictionary, "word_boundary_aliases"
        ),
    }

    results = {
        "experiment": "EXP-009",
        "status": "completed",
        "evaluation_date_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "test_xml": str(Path(args.test_xml).resolve()),
        "dictionary_path": str(Path(args.dictionary).resolve()),
        "gold_policy": "one entity per BioC annotation location",
        "match_rule": "exact document-level character span and entity type",
        "aliases": ALIASES,
        "strategies": {},
    }

    for name, predicted in strategies.items():
        results["strategies"][name] = compute_metrics(gold, predicted)

        print(f"\n=== {name} ===")
        for key, value in results["strategies"][name].items():
            print(f"{key}: {value}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()