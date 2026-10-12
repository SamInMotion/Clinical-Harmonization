"""Diagnose why EXP-009 extracts more occurrences than the submitted MVP.

Compares unrestricted dictionary matching with whole-word-boundary matching
and reports the most frequent extracted normalized mentions.
"""

import argparse
import json
from collections import Counter
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from dictionary_baseline import load_dictionary, extract_entities_from_text


def word_boundary_matches(text, dictionary, min_length=4):
    matches = []

    for raw_match in re.finditer(r"[A-Za-z][A-Za-z0-9\-\+]*", text):
        pass

    # Reuse the existing extractor, then reject matches that are not
    # delimited by non-word characters or text boundaries.
    candidates = extract_entities_from_text(
        text, dictionary, min_length=min_length
    )

    for match in candidates:
        start = match["offset"]
        end = start + match["length"]

        before_ok = start == 0 or not (
            text[start - 1].isalnum() or text[start - 1] == "_"
        )
        after_ok = end == len(text) or not (
            text[end].isalnum() or text[end] == "_"
        )

        if before_ok and after_ok:
            matches.append(match)

    return matches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        default=str(PROJECT_ROOT / "data" / "raw" / "raw_json"),
    )
    parser.add_argument(
        "--dictionary",
        default=str(
            PROJECT_ROOT
            / "data"
            / "terminology"
            / "bc5cdr_dictionary.json"
        ),
    )
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    dictionary = load_dictionary(args.dictionary)

    current_total = 0
    boundary_total = 0
    current_mentions = Counter()
    boundary_mentions = Counter()

    json_paths = sorted(input_dir.glob("*.json"))

    for json_path in json_paths:
        document = json.loads(json_path.read_text(encoding="utf-8"))

        for passage in document["passages"]:
            text = passage.get("text") or ""

            current = extract_entities_from_text(
                text, dictionary, min_length=4
            )
            boundary = word_boundary_matches(
                text, dictionary, min_length=4
            )

            current_total += len(current)
            boundary_total += len(boundary)

            for match in current:
                current_mentions[
                    " ".join(match["text"].lower().split())
                ] += 1

            for match in boundary:
                boundary_mentions[
                    " ".join(match["text"].lower().split())
                ] += 1

    print(f"Documents: {len(json_paths)}")
    print(f"Current extractor occurrences: {current_total}")
    print(f"Word-boundary occurrences: {boundary_total}")
    print(f"Removed occurrences: {current_total - boundary_total}")

    print("\nTop current mentions:")
    for mention, count in current_mentions.most_common(args.limit):
        print(f"  {count:5d}  {mention}")

    print("\nTop word-boundary mentions:")
    for mention, count in boundary_mentions.most_common(args.limit):
        print(f"  {count:5d}  {mention}")


if __name__ == "__main__":
    main()