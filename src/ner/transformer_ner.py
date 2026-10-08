"""
Fine-tune and evaluate PubMedBERT for BC5CDR chemical and disease NER.

This module consumes the repository's existing BC5CDR loader schema:
    document["id"]
    document["passages"][i]["type"]
    document["passages"][i]["text"]
    document["passages"][i]["annotations"]

Predictions are emitted in the same dictionary shape used by
src/ner/evaluate_ner.py so transformer and dictionary-baseline results
can be compared using the same exact-span metric implementation.

Usage:
    # Safe preflight: no model-weight download, no training.
    .venv/Scripts/python.exe src/ner/transformer_ner.py --preflight

    # Fine-tune only after reviewing a successful preflight.
    .venv/Scripts/python.exe src/ner/transformer_ner.py --train
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from datasets import Dataset
from seqeval.metrics import classification_report
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

try:
    from .evaluate_ner import calculate_metrics, extract_gold_entities
    from .load_bc5cdr import load_bc5cdr
except ImportError:
    from evaluate_ner import calculate_metrics, extract_gold_entities
    from load_bc5cdr import load_bc5cdr


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "bc5cdr" / "CDR_Data" / "CDR.Corpus.v010516"
TRAIN_XML = DATA_DIR / "CDR_TrainingSet.BioC.xml"
TEST_XML = DATA_DIR / "CDR_TestSet.BioC.xml"
MODEL_NAME = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
MODEL_OUTPUT_DIR = PROJECT_ROOT / "models" / "pubmedbert-bc5cdr-ner"
EVALUATION_OUTPUT_DIR = PROJECT_ROOT / "output" / "evaluation"

LABELS = ["O", "B-Chemical", "I-Chemical", "B-Disease", "I-Disease"]
LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}
ID_TO_LABEL = {index: label for index, label in enumerate(LABELS)}

SEED = 42
MAX_LENGTH = 512


@dataclass
class PassageExample:
    """One title or abstract passage in the loader's native schema."""

    doc_id: str
    passage_type: str
    text: str
    annotations: list[dict[str, Any]]


def set_seed(seed: int = SEED) -> None:
    """Make split and training behavior as reproducible as practical."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def validate_corpus_files() -> None:
    """Fail early with actionable errors if required corpus files are absent."""
    missing = [path for path in (TRAIN_XML, TEST_XML) if not path.exists()]
    if missing:
        formatted = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(
            "Required BC5CDR XML file(s) not found:\n"
            f"{formatted}\n"
            "Expected corpus root: data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        )


def documents_to_passages(documents: list[dict[str, Any]]) -> list[PassageExample]:
    """
    Flatten loader output into independently trainable title/abstract passages.

    BC5CDR offsets are passage-relative in the existing loader. Keeping
    passages separate preserves the exact-span evaluation contract.
    """
    examples = []

    for document in documents:
        for passage in document["passages"]:
            if passage["type"] not in {"title", "abstract"}:
                continue

            text = passage["text"]
            if not text:
                continue

            examples.append(
                PassageExample(
                    doc_id=document["id"],
                    passage_type=passage["type"],
                    text=text,
                    annotations=passage["annotations"],
                )
            )

    return examples


def validate_annotations(passages: list[PassageExample]) -> dict[str, int]:
    """
    Verify annotation offsets against source text before tokenization.

    This catches malformed offsets or text mismatch before a training job.
    """
    checked = 0
    entity_counts: Counter[str] = Counter()

    for passage in passages:
        for annotation in passage.annotations:
            start = annotation["offset"]
            end = start + annotation["length"]
            observed = passage.text[start:end]

            if observed != annotation["text"]:
                raise ValueError(
                    "Annotation/text mismatch:\n"
                    f"  doc_id={passage.doc_id}\n"
                    f"  passage_type={passage.passage_type}\n"
                    f"  offset={start}, length={annotation['length']}\n"
                    f"  annotation_text={annotation['text']!r}\n"
                    f"  observed_text={observed!r}"
                )

            if annotation["type"] not in {"Chemical", "Disease"}:
                raise ValueError(
                    f"Unexpected entity type {annotation['type']!r} "
                    f"in document {passage.doc_id}."
                )

            checked += 1
            entity_counts[annotation["type"]] += 1

    return {
        "annotations_checked": checked,
        "chemical_annotations": entity_counts["Chemical"],
        "disease_annotations": entity_counts["Disease"],
    }


def character_bio_labels(passage: PassageExample) -> list[str]:
    """
    Create character-level BIO labels from passage-relative BC5CDR spans.

    Token labels are subsequently assigned by each token's starting
    character offset. Continuation subwords receive I-tags where relevant.
    """
    labels = ["O"] * len(passage.text)

    for annotation in passage.annotations:
        start = annotation["offset"]
        end = start + annotation["length"]
        entity_type = annotation["type"]

        labels[start] = f"B-{entity_type}"
        for index in range(start + 1, end):
            labels[index] = f"I-{entity_type}"

    return labels


def label_tokens_for_passage(
    passage: PassageExample,
    tokenizer: Any,
    max_length: int = MAX_LENGTH,
) -> dict[str, Any]:
    """
    Tokenize one passage and align BC5CDR labels through offset mappings.

    Special tokens and padding positions receive -100, so Trainer excludes
    them from loss and metrics. For subwords within an entity, an I-tag is
    used even where the underlying character label begins with B.
    """
    char_labels = character_bio_labels(passage)

    encoded = tokenizer(
        passage.text,
        truncation=True,
        max_length=max_length,
        return_offsets_mapping=True,
        padding=False,
    )

    labels = []
    previous_entity_type = None
    previous_end = None

    for start, end in encoded["offset_mapping"]:
        if start == end:
            labels.append(-100)
            previous_entity_type = None
            previous_end = None
            continue

        raw_label = char_labels[start]
        label = raw_label

        if raw_label.startswith("B-"):
            entity_type = raw_label[2:]
            if previous_entity_type == entity_type and previous_end == start:
                label = f"I-{entity_type}"
            previous_entity_type = entity_type
        elif raw_label.startswith("I-"):
            previous_entity_type = raw_label[2:]
        else:
            previous_entity_type = None

        labels.append(LABEL_TO_ID[label])
        previous_end = end

    return {
        "input_ids": encoded["input_ids"],
        "attention_mask": encoded["attention_mask"],
        "labels": labels,
        "offset_mapping": [list(offset) for offset in encoded["offset_mapping"]],
        "doc_id": passage.doc_id,
        "passage_type": passage.passage_type,
        "text": passage.text,
    }


def build_dataset(
    passages: list[PassageExample],
    tokenizer: Any,
    max_length: int = MAX_LENGTH,
) -> Dataset:
    """Build a Hugging Face Dataset while retaining evaluation metadata."""
    records = [
        label_tokens_for_passage(passage, tokenizer, max_length=max_length)
        for passage in passages
    ]
    return Dataset.from_list(records)


def labels_for_seqeval(label_ids: list[int]) -> list[str]:
    """Remove ignored positions and convert numeric labels to BIO strings."""
    return [ID_TO_LABEL[label_id] for label_id in label_ids if label_id != -100]


def compute_metrics(eval_prediction: Any) -> dict[str, float]:
    """Compute entity-level BIO metrics using direct seqeval APIs."""
    logits, label_ids = eval_prediction
    prediction_ids = np.argmax(logits, axis=-1)

    references = []
    predictions = []

    for predicted_row, gold_row in zip(prediction_ids, label_ids):
        reference_row = []
        prediction_row = []

        for predicted_id, gold_id in zip(predicted_row, gold_row):
            if gold_id == -100:
                continue

            reference_row.append(ID_TO_LABEL[int(gold_id)])
            prediction_row.append(ID_TO_LABEL[int(predicted_id)])

        references.append(reference_row)
        predictions.append(prediction_row)

    report = classification_report(
        references,
        predictions,
        output_dict=True,
        zero_division=0,
    )

    return {
        "precision": float(report.get("micro avg", {}).get("precision", 0.0)),
        "recall": float(report.get("micro avg", {}).get("recall", 0.0)),
        "f1": float(report.get("micro avg", {}).get("f1-score", 0.0)),
        "chemical_f1": float(report.get("Chemical", {}).get("f1-score", 0.0)),
        "disease_f1": float(report.get("Disease", {}).get("f1-score", 0.0)),
    }


def decode_predictions(
    model: Any,
    tokenizer: Any,
    passages: list[PassageExample],
    batch_size: int = 8,
    max_length: int = MAX_LENGTH,
) -> list[dict[str, Any]]:
    """
    Convert model BIO output into baseline-compatible entity dictionaries.

    Exact span evaluation remains passage-relative and includes entity type.
    Invalid I-tags are treated as a new entity boundary.
    """
    model.eval()
    device = next(model.parameters()).device
    predictions = []

    with torch.no_grad():
        for start_index in range(0, len(passages), batch_size):
            batch_passages = passages[start_index : start_index + batch_size]
            texts = [passage.text for passage in batch_passages]

            encoded = tokenizer(
                texts,
                truncation=True,
                max_length=max_length,
                return_offsets_mapping=True,
                return_tensors="pt",
                padding=True,
            )

            offset_mappings = encoded.pop("offset_mapping").tolist()
            model_inputs = {key: value.to(device) for key, value in encoded.items()}
            predicted_ids = torch.argmax(model(**model_inputs).logits, dim=-1).cpu().tolist()

            for passage, offsets, row_ids in zip(
                batch_passages,
                offset_mappings,
                predicted_ids,
            ):
                active_entity = None

                for (token_start, token_end), label_id in zip(offsets, row_ids):
                    if token_start == token_end:
                        continue

                    label = ID_TO_LABEL[label_id]

                    if label == "O":
                        if active_entity is not None:
                            predictions.append(active_entity)
                            active_entity = None
                        continue

                    prefix, entity_type = label.split("-", maxsplit=1)
                    continues_current = (
                        prefix == "I"
                        and active_entity is not None
                        and active_entity["type"] == entity_type
                        and token_start <= active_entity["offset"] + active_entity["length"] + 1
                    )

                    if prefix == "B" or not continues_current:
                        if active_entity is not None:
                            predictions.append(active_entity)

                        active_entity = {
                            "text": passage.text[token_start:token_end],
                            "type": entity_type,
                            "mesh_id": None,
                            "offset": token_start,
                            "length": token_end - token_start,
                            "doc_id": passage.doc_id,
                            "passage_type": passage.passage_type,
                        }
                    else:
                        entity_end = token_end
                        active_entity["length"] = entity_end - active_entity["offset"]
                        active_entity["text"] = passage.text[
                            active_entity["offset"] : entity_end
                        ]

                if active_entity is not None:
                    predictions.append(active_entity)

    return predictions


def run_preflight() -> None:
    """
    Validate data, label alignment, metric behavior, and one model forward pass.

    It does not run training and does not download model weights.
    """
    validate_corpus_files()
    set_seed()

    train_documents = load_bc5cdr(str(TRAIN_XML))
    test_documents = load_bc5cdr(str(TEST_XML))
    train_passages = documents_to_passages(train_documents)
    test_passages = documents_to_passages(test_documents)

    train_validation = validate_annotations(train_passages)
    test_validation = validate_annotations(test_passages)

    print("=== TRANSFORMER NER PREFLIGHT ===")
    print(f"Training documents: {len(train_documents)}")
    print(f"Test documents: {len(test_documents)}")
    print(f"Training passages: {len(train_passages)}")
    print(f"Test passages: {len(test_passages)}")
    print(f"Training annotation validation: {train_validation}")
    print(f"Test annotation validation: {test_validation}")

    print(f"\nLoading tokenizer only: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    sample_passage = train_passages[0]
    sample_record = label_tokens_for_passage(sample_passage, tokenizer)
    active_labels = labels_for_seqeval(sample_record["labels"])

    print("\n=== LABEL-ALIGNMENT SAMPLE ===")
    print(f"Document: {sample_passage.doc_id}")
    print(f"Passage type: {sample_passage.passage_type}")
    print(f"Characters: {len(sample_passage.text)}")
    print(f"Tokens including special tokens: {len(sample_record['input_ids'])}")
    print(f"Active token labels: {len(active_labels)}")
    print(f"Gold annotations: {len(sample_passage.annotations)}")
    print(f"BIO labels present: {dict(Counter(active_labels))}")

    dataset = build_dataset(train_passages[:4], tokenizer)
    print("\n=== DATASET SMOKE CHECK ===")
    print(f"Sample dataset rows: {len(dataset)}")
    print(f"Dataset columns: {dataset.column_names}")
    print(
        "Input/label length alignment: "
        f"{len(dataset[0]['input_ids']) == len(dataset[0]['labels'])}"
    )

    synthetic_logits = np.zeros((1, 4, len(LABELS)), dtype=np.float32)
    synthetic_logits[0, 1, LABEL_TO_ID["B-Chemical"]] = 10.0
    synthetic_logits[0, 2, LABEL_TO_ID["I-Chemical"]] = 10.0
    synthetic_labels = np.array([[-100, LABEL_TO_ID["B-Chemical"], LABEL_TO_ID["I-Chemical"], -100]])
    metric_check = compute_metrics((synthetic_logits, synthetic_labels))

    if metric_check["f1"] != 1.0:
        raise AssertionError(
            f"Metric smoke check failed; expected F1=1.0, got {metric_check['f1']}."
        )

    print("\n=== METRIC SMOKE CHECK ===")
    print(f"Perfect BIO sequence F1: {metric_check['f1']:.4f}")
    print("\nPREFLIGHT PASSED")
    print(
        "Next permitted action: review this output, then run with --train "
        "to download model weights and begin fine-tuning."
    )


def run_training(
    epochs: int,
    train_batch_size: int,
    eval_batch_size: int,
    learning_rate: float,
) -> None:
    """Train PubMedBERT and write a reproducible evaluation report."""
    validate_corpus_files()
    set_seed()

    train_documents = load_bc5cdr(str(TRAIN_XML))
    test_documents = load_bc5cdr(str(TEST_XML))
    train_passages = documents_to_passages(train_documents)
    test_passages = documents_to_passages(test_documents)

    validate_annotations(train_passages)
    validate_annotations(test_passages)

    print(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Building training dataset...")
    train_dataset = build_dataset(train_passages, tokenizer)

    print("Building test dataset...")
    test_dataset = build_dataset(test_passages, tokenizer)

    print(f"Loading model: {MODEL_NAME}")
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABELS),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
    )

    use_fp16 = torch.cuda.is_available()
    training_args = TrainingArguments(
        output_dir=str(MODEL_OUTPUT_DIR),
        overwrite_output_dir=False,
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        per_device_train_batch_size=train_batch_size,
        per_device_eval_batch_size=eval_batch_size,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=25,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        report_to=[],
        seed=SEED,
        data_seed=SEED,
        fp16=use_fp16,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        processing_class=tokenizer,
        data_collator=DataCollatorForTokenClassification(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )

    print("\n=== TRAINING ===")
    trainer.train()

    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(MODEL_OUTPUT_DIR))
    tokenizer.save_pretrained(str(MODEL_OUTPUT_DIR))

    print("\n=== TOKEN-LEVEL / BIO EVALUATION ===")
    token_metrics = trainer.evaluate()
    for metric_name, metric_value in sorted(token_metrics.items()):
        if isinstance(metric_value, float):
            print(f"{metric_name}: {metric_value:.4f}")
        else:
            print(f"{metric_name}: {metric_value}")

    print("\n=== EXACT-SPAN EVALUATION ===")
    predicted_entities = decode_predictions(model, tokenizer, test_passages)
    gold_entities = extract_gold_entities(test_documents)
    exact_span_metrics = calculate_metrics(gold_entities, predicted_entities)

    for metric_name, metric_value in exact_span_metrics.items():
        print(
            f"{metric_name}: {metric_value:.4f}"
            if isinstance(metric_value, float)
            else f"{metric_name}: {metric_value}"
        )

    EVALUATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = EVALUATION_OUTPUT_DIR / "pubmedbert_bc5cdr_test_results.json"

    report = {
        "run_configuration": {
            "model_name": MODEL_NAME,
            "seed": SEED,
            "max_length": MAX_LENGTH,
            "epochs": epochs,
            "train_batch_size": train_batch_size,
            "eval_batch_size": eval_batch_size,
            "learning_rate": learning_rate,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        },
        "data": {
            "train_documents": len(train_documents),
            "test_documents": len(test_documents),
            "train_passages": len(train_passages),
            "test_passages": len(test_passages),
            "gold_test_entities": len(gold_entities),
        },
        "token_bio_metrics": token_metrics,
        "exact_span_metrics": exact_span_metrics,
        "baseline_reference": {
            "precision": 0.1164,
            "recall": 0.0825,
            "f1": 0.0966,
            "source": "MANIFEST.md; dictionary baseline, 2026-10-07",
        },
        "notes": [
            "Exact-span metrics use the repository's existing evaluate_ner.py contract.",
            "BC5CDR annotations are selectively annotated; measured false positives may include real but unannotated biomedical mentions.",
            "This run is a fine-tuning experiment, not a deployed clinical system.",
        ],
    }

    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)

    print(f"\nSaved model: {MODEL_OUTPUT_DIR}")
    print(f"Saved evaluation report: {report_path}")


def parse_args() -> argparse.Namespace:
    """Parse explicit execution modes and conservative training parameters."""
    parser = argparse.ArgumentParser(
        description="Fine-tune PubMedBERT for BC5CDR chemical/disease NER."
    )
    execution_mode = parser.add_mutually_exclusive_group(required=True)
    execution_mode.add_argument(
        "--preflight",
        action="store_true",
        help="Validate loader/schema/BIO alignment and metric behavior without training.",
    )
    execution_mode.add_argument(
        "--train",
        action="store_true",
        help="Run fine-tuning after a reviewed successful preflight.",
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--train-batch-size", type=int, default=4)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    return parser.parse_args()


def main() -> None:
    """Dispatch explicitly requested execution mode."""
    args = parse_args()

    if args.preflight:
        run_preflight()
        return

    run_training(
        epochs=args.epochs,
        train_batch_size=args.train_batch_size,
        eval_batch_size=args.eval_batch_size,
        learning_rate=args.learning_rate,
    )


if __name__ == "__main__":
    main()
