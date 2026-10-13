"""Export EXP-012 dictionary, PubMedBERT, and gold predictions.

All spans are emitted as document-level character offsets and entity types.
This prevents a repeat of the earlier document-global versus passage-local
offset mismatch.
"""

import argparse
import json
from pathlib import Path
import sys

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

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

BASE_DICTIONARY = (
    PROJECT_ROOT
    / "data"
    / "terminology"
    / "bc5cdr_dictionary.json"
)

PUBMEDBERT_MODEL = (
    PROJECT_ROOT
    / "output"
    / "training"
    / "pubmedbert_bc5cdr"
    / "epoch_3"
)

OUTPUT_DIR = PROJECT_ROOT / "output" / "evaluation" / "exp012"

MAX_LENGTH = 512
BATCH_SIZE = 8


def gold_records(documents):
    records = []

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

                    records.append(
                        {
                            "document_id": document["id"],
                            "start": start,
                            "end": end,
                            "entity_type": entity_type,
                            "mention": annotation["text"],
                            "source": "gold",
                        }
                    )

    return records


def dictionary_records(documents, dictionary):
    records = []

    for document in documents:
        for passage in document["passages"]:
            passage_offset = passage["offset"]
            text = passage["text"] or ""

            for match in extract_entities_from_text(
                text,
                dictionary,
                min_length=4,
            ):
                start = passage_offset + match["offset"]
                end = start + match["length"]

                records.append(
                    {
                        "document_id": document["id"],
                        "start": start,
                        "end": end,
                        "entity_type": match["type"],
                        "mention": match["text"],
                        "source": "dictionary",
                    }
                )

    return records


def decode_bio_predictions(label_ids, offsets, id2label):
    entities = []
    current_start = None
    current_end = None
    current_type = None

    for label_id, (start, end) in zip(label_ids, offsets):
        label = id2label[int(label_id)]

        if start == end:
            continue

        if label == "O":
            if current_type is not None:
                entities.append(
                    (current_start, current_end, current_type)
                )
                current_start = current_end = current_type = None
            continue

        if label.startswith("B-"):
            if current_type is not None:
                entities.append(
                    (current_start, current_end, current_type)
                )

            current_start = start
            current_end = end
            current_type = label[2:]

        elif label.startswith("I-"):
            entity_type = label[2:]

            if current_type == entity_type and current_end == start:
                current_end = end
            else:
                if current_type is not None:
                    entities.append(
                        (current_start, current_end, current_type)
                    )

                current_start = start
                current_end = end
                current_type = entity_type

    if current_type is not None:
        entities.append((current_start, current_end, current_type))

    return entities


def transformer_records(documents, model_path):
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        use_fast=True,
        local_files_only=True,
    )

    if not tokenizer.is_fast:
        raise RuntimeError("EXP-012 requires a fast tokenizer.")

    model = AutoModelForTokenClassification.from_pretrained(
        str(model_path),
        local_files_only=True,
    )
    model.eval()

    id2label = {
        int(index): label
        for index, label in model.config.id2label.items()
    }

    passages = []

    for document in documents:
        for passage in document["passages"]:
            passages.append(
                {
                    "document_id": document["id"],
                    "passage_offset": passage["offset"],
                    "text": passage["text"] or "",
                }
            )

    records = []

    with torch.no_grad():
        for batch_start in range(0, len(passages), BATCH_SIZE):
            batch = passages[
                batch_start : batch_start + BATCH_SIZE
            ]

            encoded = tokenizer(
                [passage["text"] for passage in batch],
                add_special_tokens=True,
                return_offsets_mapping=True,
                return_special_tokens_mask=True,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )

            offsets = encoded.pop("offset_mapping")
            encoded.pop("special_tokens_mask")

            outputs = model(**encoded)
            predictions = torch.argmax(outputs.logits, dim=-1)

            for row, passage in enumerate(batch):
                passage_offset = passage["passage_offset"]
                row_offsets = [
                    (int(start), int(end))
                    for start, end in offsets[row].tolist()
                ]

                local_entities = decode_bio_predictions(
                    predictions[row].tolist(),
                    row_offsets,
                    id2label,
                )

                for local_start, local_end, entity_type in local_entities:
                    records.append(
                        {
                            "document_id": passage["document_id"],
                            "start": passage_offset + local_start,
                            "end": passage_offset + local_end,
                            "entity_type": entity_type,
                            "mention": passage["text"][
                                local_start:local_end
                            ],
                            "source": "pubmedbert",
                        }
                    )

            completed = min(
                batch_start + BATCH_SIZE, len(passages)
            )
            print(f"Transformer passages: {completed}/{len(passages)}")

    return records


def write_json(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)

    print(f"Wrote {len(records)} records to {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--xml-path",
        default=str(TEST_XML),
    )
    parser.add_argument(
        "--dictionary",
        default=str(BASE_DICTIONARY),
    )
    parser.add_argument(
        "--model-dir",
        default=str(PUBMEDBERT_MODEL),
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
    )
    args = parser.parse_args()

    documents = load_bc5cdr(args.xml_path)
    dictionary = load_dictionary(args.dictionary)
    output_dir = Path(args.output_dir)

    gold = gold_records(documents)
    dictionary_predictions = dictionary_records(
        documents, dictionary
    )
    transformer_predictions = transformer_records(
        documents, Path(args.model_dir)
    )

    write_json(output_dir / "gold_entities.json", gold)
    write_json(
        output_dir / "dictionary_predictions.json",
        dictionary_predictions,
    )
    write_json(
        output_dir / "pubmedbert_epoch3_predictions.json",
        transformer_predictions,
    )


if __name__ == "__main__":
    main()