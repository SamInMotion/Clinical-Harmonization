"""Export EXP-014A development-set dictionary, PubMedBERT, and gold predictions.

This script supports development-only confidence-threshold selection for the
hybrid extraction configuration. It deliberately does not read or modify the
BC5CDR test set.

All spans are emitted as document-level character offsets and entity types.
"""

import json
from pathlib import Path
import sys

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForTokenClassification

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import load_dictionary, extract_entities_from_text


DEVELOPMENT_XML = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bc5cdr"
    / "CDR_Data"
    / "CDR.Corpus.v010516"
    / "CDR_DevelopmentSet.BioC.xml"
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

OUTPUT_DIR = PROJECT_ROOT / "output" / "evaluation" / "exp014a"

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
        raise RuntimeError("EXP-014A requires a fast tokenizer.")

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
            batch = passages[batch_start : batch_start + BATCH_SIZE]

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
            probabilities = F.softmax(outputs.logits, dim=-1)
            predictions = torch.argmax(probabilities, dim=-1)

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

                row_labels = predictions[row].tolist()
                row_probabilities = probabilities[row].tolist()

                for local_start, local_end, entity_type in local_entities:
                    span_token_indexes = [
                        index
                        for index, (token_start, token_end) in enumerate(
                            row_offsets
                        )
                        if token_start < token_end
                        and token_start < local_end
                        and token_end > local_start
                    ]

                    if not span_token_indexes:
                        continue

                    span_confidence = max(
                        row_probabilities[index][
                            int(predictions[row][index])
                        ]
                        for index in span_token_indexes
                    )

                    records.append(
                        {
                            "document_id": passage["document_id"],
                            "start": passage_offset + local_start,
                            "end": passage_offset + local_end,
                            "entity_type": entity_type,
                            "mention": passage["text"][
                                local_start:local_end
                            ],
                            "confidence": span_confidence,
                            "source": "pubmedbert",
                        }
                    )

    return records


def write_json(path, records):
    path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main():
    if not DEVELOPMENT_XML.exists():
        raise FileNotFoundError(f"Development XML not found: {DEVELOPMENT_XML}")

    if not BASE_DICTIONARY.exists():
        raise FileNotFoundError(f"Base dictionary not found: {BASE_DICTIONARY}")

    if not PUBMEDBERT_MODEL.exists():
        raise FileNotFoundError(
            f"PubMedBERT epoch-3 checkpoint not found: {PUBMEDBERT_MODEL}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading BC5CDR development set: {DEVELOPMENT_XML}")
    documents = load_bc5cdr(str(DEVELOPMENT_XML))

    print("Exporting gold entities...")
    gold = gold_records(documents)
    write_json(OUTPUT_DIR / "gold_entities.json", gold)

    print("Exporting base-dictionary predictions...")
    dictionary = load_dictionary(str(BASE_DICTIONARY))
    dictionary_predictions = dictionary_records(documents, dictionary)
    write_json(
        OUTPUT_DIR / "dictionary_predictions.json",
        dictionary_predictions,
    )

    print("Exporting PubMedBERT epoch-3 predictions with confidence...")
    transformer_predictions = transformer_records(
        documents,
        str(PUBMEDBERT_MODEL),
    )
    write_json(
        OUTPUT_DIR / "pubmedbert_epoch3_predictions.json",
        transformer_predictions,
    )

    missing_confidence = sum(
        1
        for prediction in transformer_predictions
        if "confidence" not in prediction
    )

    if missing_confidence:
        raise ValueError(
            f"{missing_confidence} PubMedBERT predictions lack confidence."
        )

    print("\n=== EXP-014A development-set export ===")
    print(f"Documents: {len(documents)}")
    print(f"Gold entities: {len(gold)}")
    print(f"Dictionary predictions: {len(dictionary_predictions)}")
    print(f"PubMedBERT predictions: {len(transformer_predictions)}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()