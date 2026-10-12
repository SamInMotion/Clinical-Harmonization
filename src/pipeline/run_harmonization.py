"""Run the dictionary-based BC5CDR text-to-OMOP harmonization pipeline.

Reads raw BC5CDR-style JSON abstracts, extracts Drug and Disease mentions,
matches them against a supplied OMOP vocabulary, validates concept domain,
and writes harmonized, mapped, unmapped, and summary outputs.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from dictionary_baseline import load_dictionary, extract_entities_from_text


FIELDNAMES = [
    "document_id",
    "passage_type",
    "mention_text",
    "normalized_mention",
    "start_char",
    "end_char",
    "entity_type",
    "extraction_method",
    "extraction_confidence",
    "concept_id",
    "concept_name",
    "domain",
    "vocabulary",
    "destination_table",
    "mapping_status",
    "mapping_method",
]

DOMAIN_TO_TABLE = {
    "Drug": "drug_exposure",
    "Condition": "condition_occurrence",
}

ELIGIBLE_DOMAINS = set(DOMAIN_TO_TABLE)


ALIASES = {
    "hyperglycaemia": "hyperglycemia",
    "hypoglycaemia": "hypoglycemia",
}


def normalize_mention(text):
    normalized = " ".join(text.lower().strip().split())
    return ALIASES.get(normalized, normalized)


def controlled_variants(normalized_mention):
    """Return controlled spelling and inflectional variants.

    This is not fuzzy matching. Each variant follows an explicit rule and is
    used only for exact vocabulary lookup.
    """
    variants = [normalized_mention]

    if normalized_mention.endswith("'s"):
        variants.append(normalized_mention[:-2])

    if normalized_mention.endswith("ies") and len(normalized_mention) > 4:
        variants.append(normalized_mention[:-3] + "y")

    if normalized_mention.endswith("s") and not normalized_mention.endswith(
        "ss"
    ):
        variants.append(normalized_mention[:-1])

    return variants


def load_raw_documents(input_dir):
    input_path = Path(input_dir)

    if not input_path.is_dir():
        raise FileNotFoundError(f"Raw JSON input directory not found: {input_path}")

    documents = []

    for json_path in sorted(input_path.glob("*.json")):
        with json_path.open(encoding="utf-8") as handle:
            document = json.load(handle)

        if "id" not in document or "passages" not in document:
            raise ValueError(f"Invalid raw document structure: {json_path}")

        documents.append(document)

    if not documents:
        raise ValueError(f"No JSON documents found in: {input_path}")

    return documents


def load_vocabulary(vocabulary_path):
    with Path(vocabulary_path).open(encoding="utf-8") as handle:
        vocabulary = json.load(handle)

    concepts = vocabulary["concepts"]

    if len(concepts) != 29:
        raise ValueError(
            f"Expected 29 OMOP concepts, found {len(concepts)}"
        )

    exact_lookup = {
        normalize_mention(concept["concept_name"]): concept
        for concept in concepts
    }

    return concepts, exact_lookup

def has_word_boundary(text, start, end):
    before_ok = start == 0 or not (
        text[start - 1].isalnum() or text[start - 1] == "_"
    )
    after_ok = end == len(text) or not (
        text[end].isalnum() or text[end] == "_"
    )
    return before_ok and after_ok

def build_occurrence(document, passage, match, extraction_method, confidence):
    start = int(match["offset"])
    end = start + int(match["length"])

    return {
        "document_id": document["id"],
        "passage_type": passage["infons"]["type"],
        "mention_text": match["text"],
        "normalized_mention": normalize_mention(match["text"]),
        "start_char": start,
        "end_char": end,
        "entity_type": match["type"],
        "extraction_method": extraction_method,
        "extraction_confidence": confidence,
        "concept_id": "",
        "concept_name": "",
        "domain": "",
        "vocabulary": "",
        "destination_table": "",
        "mapping_status": "unmapped",
        "mapping_method": "no_exact_match",
    }


def apply_exact_mapping(occurrence, exact_lookup):
    for variant in controlled_variants(
        occurrence["normalized_mention"]
    ):
        concept = exact_lookup.get(variant)

        if concept is None:
            continue

        occurrence.update(
            {
                "concept_id": concept["concept_id"],
                "concept_name": concept["concept_name"],
                "domain": concept["domain_id"],
                "vocabulary": concept["vocabulary_id"],
                "mapping_method": "exact_normalized_match",
            }
        )

        if concept["domain_id"] in ELIGIBLE_DOMAINS:
            occurrence["mapping_status"] = "mapped"
            occurrence["destination_table"] = DOMAIN_TO_TABLE[
                concept["domain_id"]
            ]
        else:
            occurrence["mapping_status"] = "unmapped"
            occurrence["mapping_method"] = "domain_not_eligible"

        return occurrence

    return occurrence


def write_csv(records, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(
        description="Run dictionary-based BC5CDR OMOP harmonization"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing 500 raw BC5CDR JSON abstracts",
    )
    parser.add_argument(
        "--dictionary",
        default=str(
            PROJECT_ROOT
            / "data"
            / "terminology"
            / "bc5cdr_dictionary.json"
        ),
        help="Dictionary NER lookup file",
    )
    parser.add_argument(
        "--vocabulary",
        default=str(
            PROJECT_ROOT
            / "data"
            / "terminology"
            / "omop_exercise_vocabulary.json"
        ),
        help="OMOP exercise vocabulary file",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "output" / "harmonization" / "exp009"),
        help="Output directory",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=4,
        help="Minimum extracted mention length",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    documents = load_raw_documents(input_dir)
    dictionary = load_dictionary(args.dictionary)
    concepts, exact_lookup = load_vocabulary(args.vocabulary)

    print(f"Loaded raw documents: {len(documents)}")
    print(f"Loaded dictionary forms: {len(dictionary)}")
    print(f"Loaded OMOP concepts: {len(concepts)}")

    records = []

    for document in documents:
        for passage in document["passages"]:
            text = passage.get("text") or ""

            candidates = extract_entities_from_text(
                text,
                dictionary,
                min_length=args.min_length,
            )

            matches = [
                match
                for match in candidates
                if has_word_boundary(
                    text,
                    match["offset"],
                    match["offset"] + match["length"],
                )
            ]

            for match in matches:
                occurrence = build_occurrence(
                    document,
                    passage,
                    match,
                    extraction_method="dictionary_word_boundary",
                    confidence="high",
                )
                occurrence = apply_exact_mapping(
                    occurrence, exact_lookup
                )
                records.append(occurrence)

    mapped = [record for record in records if record["mapping_status"] == "mapped"]
    unmapped = [
        record for record in records if record["mapping_status"] == "unmapped"
    ]

    document_counts = Counter(
        record["document_id"] for record in records
    )
    destination_counts = Counter(
        record["destination_table"]
        for record in mapped
        if record["destination_table"]
    )
    unmapped_reasons = Counter(
        record["mapping_method"] for record in unmapped
    )

    coverage = len(mapped) / len(records) if records else 0.0

    summary = {
        "experiment": "EXP-010",
        "status": "completed",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_directory": str(input_dir),
        "dictionary_path": args.dictionary,
        "vocabulary_path": args.vocabulary,
        "minimum_mention_length": args.min_length,
        "documents": len(documents),
        "extracted_occurrences": len(records),
        "mapped_occurrences": len(mapped),
        "unmapped_occurrences": len(unmapped),
        "vocabulary_coverage": coverage,
        "documents_with_extractions": len(document_counts),
        "destination_table_counts": dict(destination_counts),
        "unmapped_reason_counts": dict(unmapped_reasons),
        "per_document_counts": dict(document_counts),
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(records, output_dir / "harmonized_records.csv")
    write_csv(mapped, output_dir / "mapped_records.csv")
    write_csv(unmapped, output_dir / "unmapped_mentions.csv")

    with (output_dir / "summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print("\n=== EXP-009 harmonization summary ===")
    print(f"Documents: {len(documents)}")
    print(f"Extracted occurrences: {len(records)}")
    print(f"Mapped: {len(mapped)}")
    print(f"Unmapped: {len(unmapped)}")
    print(f"Vocabulary coverage: {coverage:.1%}")
    print(f"Destination tables: {dict(destination_counts)}")
    print(f"Unmapped reasons: {dict(unmapped_reasons)}")
    print(f"Outputs written to: {output_dir}")


if __name__ == "__main__":
    main()