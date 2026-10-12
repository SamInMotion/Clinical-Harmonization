"""Evaluate EXP-010 mapping quality against BC5CDR test-set gold entities.

A mapped pipeline record is gold-supported when its document-level character
span and entity type match a gold entity, and its normalized mention or a
controlled variant matches the mapped vocabulary concept.
"""

import csv
import json
from collections import Counter
from datetime import datetime, timezone
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

OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp011_mapping_quality.json"
)

ALIASES = {
    "hyperglycaemia": "hyperglycemia",
    "hypoglycaemia": "hypoglycemia",
}


def normalize(text):
    normalized = " ".join(text.lower().strip().split())
    return ALIASES.get(normalized, normalized)


def controlled_variants(normalized):
    variants = [normalized]

    if normalized.endswith("'s"):
        variants.append(normalized[:-2])

    if normalized.endswith("ies") and len(normalized) > 4:
        variants.append(normalized[:-3] + "y")

    if normalized.endswith("s") and not normalized.endswith("ss"):
        variants.append(normalized[:-1])

    return variants


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
                        {
                            "document_id": document["id"],
                            "start": start,
                            "end": end,
                            "entity_type": entity_type,
                            "mention": annotation["text"],
                            "normalized": normalize(annotation["text"]),
                            "mesh_id": annotation["mesh_id"],
                        }
                    )

    return entities


def load_mapped(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    documents = load_bc5cdr(str(TEST_XML))
    gold = gold_entities(documents)
    mapped = load_mapped(str(MAPPED_CSV))
    unique_gold_keys = {
        (
            entity["document_id"],
            entity["start"],
            entity["end"],
            entity["entity_type"],
        )
        for entity in gold
    }

    gold_by_key = {
        (
            entity["document_id"],
            entity["start"],
            entity["end"],
            entity["entity_type"],
        ): entity
        for entity in gold
    }

    gold_representable = {
        key
        for key, entity in gold_by_key.items()
        if any(
            variant in {
                normalize(concept["concept_name"])
                for concept in [
                    {
                        "concept_name": concept_name
                    }
                    for concept_name in [
                        "morphine",
                        "quinine",
                        "aspirin",
                        "ibuprofen",
                        "heparin",
                        "warfarin",
                        "prednisone",
                        "methadone",
                        "cisplatin",
                        "colchicine",
                        "baclofen",
                        "haloperidol",
                        "clozapine",
                        "ethanol",
                        "nicotine",
                        "caffeine",
                        "lithium",
                        "anxiety",
                        "seizure",
                        "nausea",
                        "vomiting",
                        "tremor",
                        "tachycardia",
                        "bradycardia",
                        "hyperglycemia",
                        "hypoglycemia",
                        "mania",
                        "hyperactive behavior",
                        "hyperactivity level",
                    ]
                ]
            }
            for variant in controlled_variants(entity["normalized"])
        )
    }

    supported_mapped = []
    unsupported_mapped = []

    for record in mapped:
        key = (
            record["document_id"],
            int(record["start_char"]),
            int(record["end_char"]),
            record["entity_type"],
        )

        gold_entity = gold_by_key.get(key)

        if gold_entity is None:
            unsupported_mapped.append(record)
            continue

        concept_variants = controlled_variants(
            normalize(gold_entity["normalized"])
        )

        if record["concept_name"].lower() in concept_variants:
            supported_mapped.append(record)
        else:
            unsupported_mapped.append(record)

    supported_keys = {
        (
            record["document_id"],
            int(record["start_char"]),
            int(record["end_char"]),
            record["entity_type"],
        )
        for record in supported_mapped
    }

    representable_mapped = supported_keys & gold_representable
    representable_unmapped = gold_representable - supported_keys

    mapping_precision = (
        len(supported_mapped) / len(mapped) if mapped else 0.0
    )

    vocabulary_recall = (
        len(representable_mapped) / len(gold_representable)
        if gold_representable
        else 0.0
    )



    results = {
        "experiment": "EXP-011",
        "status": "completed",
        "evaluation_date_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "test_xml": str(TEST_XML),
        "mapped_csv": str(MAPPED_CSV),
        "gold_entities": len(unique_gold_keys),
        "mapped_records": len(mapped),
        "gold_supported_mapped": len(supported_mapped),
        "unsupported_mapped": len(unsupported_mapped),
        "mapping_precision": mapping_precision,
        "vocabulary_representable_gold": len(gold_representable),
        "vocabulary_representable_mapped": len(representable_mapped),
        "vocabulary_representable_unmapped": len(
            representable_unmapped
        ),
        "vocabulary_recall": vocabulary_recall,
        "unsupported_examples": [
            {
                "document_id": record["document_id"],
                "mention_text": record["mention_text"],
                "concept_name": record["concept_name"],
                "start_char": record["start_char"],
                "end_char": record["end_char"],
                "entity_type": record["entity_type"],
            }
            for record in unsupported_mapped[:100]
        ],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== EXP-011 mapping-quality evaluation ===")
    print(f"Gold entities: {len(unique_gold_keys)}")
    print(f"Mapped records: {len(mapped)}")
    print(f"Gold-supported mapped: {len(supported_mapped)}")
    print(f"Unsupported mapped: {len(unsupported_mapped)}")
    print(f"Mapping precision: {mapping_precision:.4f}")
    print(f"Vocabulary-representable gold: {len(gold_representable)}")
    print(f"Vocabulary-representable mapped: {len(representable_mapped)}")
    print(f"Vocabulary recall: {vocabulary_recall:.4f}")
    print(f"Results saved to: {OUTPUT}")


if __name__ == "__main__":
    main()