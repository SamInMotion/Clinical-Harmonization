"""Diagnose unsupported EXP-010 mappings against BC5CDR test gold."""

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

    gold_by_doc = {}

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

        gold_by_doc[document["id"]] = entities

    with MAPPED_CSV.open(encoding="utf-8", newline="") as handle:
        mapped = list(csv.DictReader(handle))

    unsupported = []

    for record in mapped:
        key = (
            int(record["start_char"]),
            int(record["end_char"]),
            record["entity_type"],
        )

        gold_entities = gold_by_doc.get(record["document_id"], [])

        if not any(
            entity["start"] == key[0]
            and entity["end"] == key[1]
            and entity["type"] == key[2]
            for entity in gold_entities
        ):
            unsupported.append(record)

    print(f"Mapped records: {len(mapped)}")
    print(f"Unsupported mapped records: {len(unsupported)}")

    print("\nFirst 30 unsupported mappings:")

    for record in unsupported[:30]:
        document_id = record["document_id"]
        start = int(record["start_char"])
        end = int(record["end_char"])

        print(
            f"\n{document_id} "
            f"{record['passage_type']} "
            f"{record['mention_text']!r} -> "
            f"{record['concept_name']} "
            f"@ {start}-{end} "
            f"({record['entity_type']})"
        )

        matching_type = [
            entity
            for entity in gold_by_doc.get(document_id, [])
            if entity["type"] == record["entity_type"]
        ]

        nearest = min(
            matching_type,
            key=lambda entity: min(
                abs(entity["start"] - start),
                abs(entity["end"] - end),
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