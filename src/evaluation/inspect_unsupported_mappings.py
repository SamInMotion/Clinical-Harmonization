"""Print all EXP-010 mapped records without gold span/type support."""

import csv
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from load_bc5cdr import load_bc5cdr


TEST_XML = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bc5cdr"
    / "CDR_Data"
    / "CDR.Corpus.v010516"
    / "CDR_TestSet.BioC.xml"
)

MAPPED_CSV = (
    PROJECT_ROOT
    / "output"
    / "harmonization"
    / "exp010"
    / "mapped_records.csv"
)


def main():
    documents = load_bc5cdr(str(TEST_XML))

    gold_by_document = {}

    for document in documents:
        entities = []

        for passage in document["passages"]:
            for annotation in passage["annotations"]:
                for location in annotation["locations"]:
                    entities.append(
                        {
                            "start": location["doc_offset"],
                            "end": location["doc_offset"]
                            + location["length"],
                            "type": annotation["type"],
                            "text": annotation["text"],
                        }
                    )

        gold_by_document[document["id"]] = entities

    with MAPPED_CSV.open(encoding="utf-8", newline="") as handle:
        mapped = list(csv.DictReader(handle))

    unsupported = []

    for record in mapped:
        start = int(record["start_char"])
        end = int(record["end_char"])
        entity_type = record["entity_type"]

        supported = any(
            entity["start"] == start
            and entity["end"] == end
            and entity["type"] == entity_type
            for entity in gold_by_document.get(
                record["document_id"], []
            )
        )

        if not supported:
            unsupported.append(record)

    print(f"Unsupported mapped records: {len(unsupported)}")

    for record in unsupported:
        print(
            f"\n{record['document_id']} "
            f"{record['passage_type']} "
            f"{record['mention_text']!r} -> "
            f"{record['concept_name']} "
            f"@ {record['start_char']}-{record['end_char']} "
            f"({record['entity_type']})"
        )

        same_type = [
            entity
            for entity in gold_by_document.get(
                record["document_id"], []
            )
            if entity["type"] == record["entity_type"]
        ]

        nearest = min(
            same_type,
            key=lambda entity: min(
                abs(entity["start"] - int(record["start_char"])),
                abs(entity["end"] - int(record["end_char"])),
            ),
            default=None,
        )

        if nearest:
            print(
                f"  nearest same-type gold: "
                f"{nearest['text']!r} "
                f"@ {nearest['start']}-{nearest['end']}"
            )
        else:
            print("  no same-type gold entity in document")


if __name__ == "__main__":
    main()