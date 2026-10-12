"""EXP-007: exact-span, type-aware entity evaluation for PubMedBERT BC5CDR NER.

Evaluates a fine-tuned token-classification checkpoint on the BC5CDR
development set. An entity is counted as correct only when its document-level
character span and entity type both match a gold entity exactly.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from load_bc5cdr import load_bc5cdr


DEFAULT_XML = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bc5cdr"
    / "CDR_Data"
    / "CDR.Corpus.v010516"
    / "CDR_DevelopmentSet.BioC.xml"
)

DEFAULT_MODEL = (
    PROJECT_ROOT
    / "output"
    / "training"
    / "pubmedbert_bc5cdr"
    / "epoch_3"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "evaluation"
    / "exp007_pubmedbert_bc5cdr_dev_epoch3.json"
)

MAX_LENGTH = 512
BATCH_SIZE = 8


def load_gold_entities(documents):
    """Return gold entities as (doc_id, start, end, entity_type) tuples."""
    gold = []

    for document in documents:
        doc_id = document["id"]

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

                    gold.append((doc_id, start, end, entity_type))

    return gold


def decode_bio_predictions(label_ids, offsets, id2label):
    """Decode one passage's predicted BIO labels into character spans."""
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
                entities.append((current_start, current_end, current_type))
                current_start = current_end = current_type = None
            continue

        if label.startswith("B-"):
            if current_type is not None:
                entities.append((current_start, current_end, current_type))

            current_start = start
            current_end = end
            current_type = label[2:]

        elif label.startswith("I-"):
            entity_type = label[2:]

            if current_type == entity_type and current_end == start:
                current_end = end
            else:
                if current_type is not None:
                    entities.append((current_start, current_end, current_type))

                current_start = start
                current_end = end
                current_type = entity_type

    if current_type is not None:
        entities.append((current_start, current_end, current_type))

    return entities


def overlaps(first, second):
    return first[0] < second[1] and second[0] < first[1]


def compute_metrics(gold, predicted):
    gold_set = set(gold)
    predicted_set = set(predicted)

    exact_matches = gold_set & predicted_set
    false_positives = predicted_set - gold_set
    false_negatives = gold_set - predicted_set

    partial_overlap_predictions = set()
    partial_overlap_gold = set()
    partial_overlap_examples = []

    for prediction in sorted(false_positives):
        for gold_entity in sorted(false_negatives):
            if prediction[3] != gold_entity[3]:
                continue

            if not overlaps(prediction[1:3], gold_entity[1:3]):
                continue

            partial_overlap_predictions.add(prediction)
            partial_overlap_gold.add(gold_entity)

            if len(partial_overlap_examples) < 100:
                partial_overlap_examples.append(
                    {
                        "predicted": {
                            "doc_id": prediction[0],
                            "start": int(prediction[1]),
                            "end": int(prediction[2]),
                            "type": prediction[3],
                        },
                        "gold": {
                            "doc_id": gold_entity[0],
                            "start": int(gold_entity[1]),
                            "end": int(gold_entity[2]),
                            "type": gold_entity[3],
                        },
                    }
                )

    num_gold = len(gold_set)
    num_predicted = len(predicted_set)
    num_exact = len(exact_matches)

    precision = num_exact / num_predicted if num_predicted else 0.0
    recall = num_exact / num_gold if num_gold else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "gold_entities": num_gold,
        "predicted_entities": num_predicted,
        "exact_matches": num_exact,
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "partial_overlap_predictions": len(partial_overlap_predictions),
        "partial_overlap_gold_entities": len(partial_overlap_gold),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match_details": sorted(exact_matches),
        "false_positive_details": sorted(false_positives),
        "false_negative_details": sorted(false_negatives),
        "partial_overlap_examples": partial_overlap_examples,
    }


def per_type_metrics(gold, predicted, entity_type):
    type_gold = [entity for entity in gold if entity[3] == entity_type]
    type_predicted = [
        entity for entity in predicted if entity[3] == entity_type
    ]
    metrics = compute_metrics(type_gold, type_predicted)

    return {
        "gold_entities": metrics["gold_entities"],
        "predicted_entities": metrics["predicted_entities"],
        "exact_matches": metrics["exact_matches"],
        "false_positives": metrics["false_positives"],
        "false_negatives": metrics["false_negatives"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="EXP-007 PubMedBERT BC5CDR development-set evaluation"
    )
    parser.add_argument(
        "--model-dir",
        default=str(DEFAULT_MODEL),
        help="Fine-tuned token-classification checkpoint directory",
    )
    parser.add_argument(
        "--xml-path",
        default=str(DEFAULT_XML),
        help="BC5CDR development BioC XML file",
    )
    parser.add_argument(
        "--output-path",
        default=str(DEFAULT_OUTPUT),
        help="Machine-readable EXP-007 result path",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="Number of passages per inference batch",
    )
    args = parser.parse_args()

    model_path = Path(args.model_dir)
    xml_path = Path(args.xml_path)
    output_path = Path(args.output_path)

    if not model_path.is_dir():
        raise FileNotFoundError(f"Model directory not found: {model_path}")
    if not xml_path.is_file():
        raise FileNotFoundError(f"Development XML not found: {xml_path}")

    print(f"Model: {model_path}")
    print(f"Development XML: {xml_path}")

    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        use_fast=True,
        local_files_only=True,
    )

    if not tokenizer.is_fast:
        raise RuntimeError("EXP-007 requires a fast tokenizer.")

    model = AutoModelForTokenClassification.from_pretrained(
        str(model_path),
        local_files_only=True,
    )
    model.eval()

    id2label = {
        int(index): label for index, label in model.config.id2label.items()
    }

    documents = load_bc5cdr(str(xml_path))
    print(f"Loaded development documents: {len(documents)}")

    passages = []

    for document in documents:
        doc_id = document["id"]

        for passage in document["passages"]:
            gold_entities = []

            for annotation in passage["annotations"]:
                entity_type = annotation["type"]

                if entity_type not in ("Chemical", "Disease"):
                    continue

                for location in annotation["locations"]:
                    start = location["doc_offset"]
                    end = start + location["length"]

                    if start >= end:
                        continue

                    gold_entities.append(
                        (doc_id, start, end, entity_type)
                    )

            passages.append(
                {
                    "doc_id": doc_id,
                    "passage_offset": passage["offset"],
                    "text": passage["text"] or "",
                    "gold_entities": gold_entities,
                }
            )

    print(f"Loaded development passages: {len(passages)}")

    predicted_entities = []
    gold_entities = []

    with torch.no_grad():
        for batch_start in range(0, len(passages), args.batch_size):
            batch = passages[
                batch_start : batch_start + args.batch_size
            ]
            texts = [passage["text"] for passage in batch]

            encoded = tokenizer(
                texts,
                add_special_tokens=True,
                return_offsets_mapping=True,
                return_special_tokens_mask=True,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )

            offsets = encoded.pop("offset_mapping")
            special_tokens_mask = encoded.pop("special_tokens_mask")

            outputs = model(**encoded)
            predictions = torch.argmax(outputs.logits, dim=-1)

            for row, passage in enumerate(batch):
                passage_offset = passage["passage_offset"]
                row_offsets = [
                    (int(start), int(end))
                    for start, end in offsets[row].tolist()
                ]
                row_predictions = predictions[row].tolist()
                

                local_entities = decode_bio_predictions(
                    row_predictions, row_offsets, id2label
                )

                for local_start, local_end, entity_type in local_entities:
                    predicted_entities.append(
                        (
                            passage["doc_id"],
                            passage_offset + local_start,
                            passage_offset + local_end,
                            entity_type,
                        )
                    )

                gold_entities.extend(passage["gold_entities"])

            completed = min(
                batch_start + args.batch_size, len(passages)
            )
            print(f"Evaluated passages: {completed}/{len(passages)}")

    overall = compute_metrics(gold_entities, predicted_entities)

    results = {
        "experiment": "EXP-007",
        "status": "completed",
        "evaluation_date_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "model_path": str(model_path),
        "development_xml": str(xml_path),
        "development_documents": len(documents),
        "development_passages": len(passages),
        "max_length": MAX_LENGTH,
        "batch_size": args.batch_size,
        "match_rule": "exact document-level character span and entity type",
        "overall": {
            key: value
            for key, value in overall.items()
            if not key.endswith("_details")
            and key != "partial_overlap_examples"
        },
        "chemical": per_type_metrics(
            gold_entities, predicted_entities, "Chemical"
        ),
        "disease": per_type_metrics(
            gold_entities, predicted_entities, "Disease"
        ),
                "error_analysis": {
            "partial_overlap_examples": overall[
                "partial_overlap_examples"
            ],
            "false_positive_examples": [
                {
                    "doc_id": entity[0],
                    "start": int(entity[1]),
                    "end": int(entity[2]),
                    "type": entity[3],
                }
                for entity in overall["false_positive_details"][:100]
            ],
            "false_negative_examples": [
                {
                    "doc_id": entity[0],
                    "start": int(entity[1]),
                    "end": int(entity[2]),
                    "type": entity[3],
                }
                for entity in overall["false_negative_details"][:100]
            ],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== EXP-007 exact-span entity evaluation ===")
    print(f"Gold entities: {overall['gold_entities']}")
    print(f"Predicted entities: {overall['predicted_entities']}")
    print(f"Exact matches: {overall['exact_matches']}")
    print(f"Precision: {overall['precision']:.4f}")
    print(f"Recall: {overall['recall']:.4f}")
    print(f"F1: {overall['f1']:.4f}")
    print(
        "Partial-overlap predictions: "
        f"{overall['partial_overlap_predictions']}"
    )
    print(
        "Partial-overlap gold entities: "
        f"{overall['partial_overlap_gold_entities']}"
    )
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()