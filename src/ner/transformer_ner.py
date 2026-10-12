
"""Fine-tune and evaluate a BERT-family model for BC5CDR NER."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from seqeval.metrics import precision_score, recall_score, f1_score
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

from load_bc5cdr import load_bc5cdr


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bc5cdr"
    / "CDR_Data"
    / "CDR.Corpus.v010516"
)

TRAIN_PATH = DATA_DIR / "CDR_TrainingSet.BioC.xml"
TEST_PATH = DATA_DIR / "CDR_TestSet.BioC.xml"

DEFAULT_MODEL = "models/pubmedbert-local"

LABEL2ID = {
    "O": 0,
    "B-Chemical": 1,
    "I-Chemical": 2,
    "B-Disease": 3,
    "I-Disease": 4,
}

ID2LABEL = {value: key for key, value in LABEL2ID.items()}
NUM_LABELS = len(LABEL2ID)


def resolve_model_path(model_reference):
    """Resolve project-relative local model paths without breaking Hub IDs."""
    candidate = Path(model_reference)

    if candidate.is_absolute():
        return str(candidate)

    project_candidate = PROJECT_ROOT / candidate

    if project_candidate.is_dir():
        return str(project_candidate)

    # Keep remote repository identifiers unchanged.
    return model_reference


def load_tokenizer(model_reference):
    """Load a fast tokenizer for character-offset entity alignment."""
    resolved = resolve_model_path(model_reference)

    tokenizer = AutoTokenizer.from_pretrained(
        resolved,
        use_fast=True,
    )

    if not tokenizer.is_fast:
        raise RuntimeError(
            f"Tokenizer loaded from {resolved!r} is not a fast tokenizer. "
            "BC5CDRDataset requires offset mappings. Check that the model "
            "directory contains compatible tokenizer files."
        )

    return tokenizer


def load_documents(xml_path):
    """Load BC5CDR documents and validate the input file."""
    if not xml_path.is_file():
        raise FileNotFoundError(
            f"BC5CDR XML file not found: {xml_path}"
        )

    documents = load_bc5cdr(str(xml_path))

    if not documents:
        raise ValueError(f"No documents loaded from {xml_path}")

    return documents




class BC5CDRDataset(Dataset):
    """Convert BC5CDR documents into token-classification examples."""

    def __init__(self, documents, tokenizer, max_length=512):
        if not tokenizer.is_fast:
            raise ValueError(
                "A fast tokenizer is required for character-offset alignment."
            )

        self.examples = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        for document in documents:
            for passage in document["passages"]:
                text = passage["text"] or ""

                encoded = tokenizer(
                    text,
                    add_special_tokens=True,
                    return_offsets_mapping=True,
                    return_special_tokens_mask=True,
                    truncation=True,
                    max_length=max_length,
                )

                input_ids = encoded["input_ids"]
                attention_mask = encoded["attention_mask"]
                offsets = encoded["offset_mapping"]
                special_tokens_mask = encoded["special_tokens_mask"]

                # Build labels against the offsets returned by this exact
                # tokenization, including the special-token positions.
                labels = self._build_bio_labels(passage, offsets)

                # CLS, SEP, and other special tokens must not contribute
                # to the training loss.
                labels = [
                    -100 if is_special else label
                    for label, is_special in zip(
                        labels, special_tokens_mask
                    )
                ]

                if not (
                    len(input_ids)
                    == len(attention_mask)
                    == len(labels)
                    == len(offsets)
                ):
                    raise ValueError(
                        f"Token-label length mismatch in document "
                        f"{document['id']}, passage {passage['type']}."
                    )

                self.examples.append({
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "labels": labels,
                    "doc_id": document["id"],
                    "passage_type": passage["type"],
                    "text": text,
                })

    def _build_bio_labels(self, passage, token_offsets):
        """Map annotation character spans to BIO token labels."""
        labels = ["O"] * len(token_offsets)
        text = passage["text"] or ""
        text_length = len(text)

        for annotation in passage["annotations"]:
            entity_type = annotation["type"]

            if entity_type not in ("Chemical", "Disease"):
                continue

            for location in annotation["locations"]:
                start = location["local_offset"]
                end = start + location["length"]

                if start < 0 or end > text_length or start >= end:
                    continue

                overlapping_tokens = [
                    i
                    for i, (token_start, token_end) in enumerate(
                        token_offsets
                    )
                    if token_start < token_end
                    and token_start < end
                    and token_end > start
                ]

                for position, token_index in enumerate(overlapping_tokens):
                    prefix = "B" if position == 0 else "I"
                    labels[token_index] = f"{prefix}-{entity_type}"

        return [
            -100 if start == end else LABEL2ID.get(label, LABEL2ID["O"])
            for label, (start, end) in zip(labels, token_offsets)
        ]

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, index):
        return self.examples[index]



def compute_metrics(eval_pred):
    """Compute entity-level metrics while preserving passage boundaries."""
    predictions, labels = eval_pred

    if isinstance(predictions, tuple):
        predictions = predictions[0]

    predictions = np.argmax(predictions, axis=-1)

    true_predictions = []
    true_labels = []

    for prediction_sequence, label_sequence in zip(
        predictions, labels
    ):
        passage_predictions = []
        passage_labels = []

        for prediction_id, label_id in zip(
            prediction_sequence, label_sequence
        ):
            if label_id == -100:
                continue

            passage_predictions.append(ID2LABEL[int(prediction_id)])
            passage_labels.append(ID2LABEL[int(label_id)])

        if passage_labels:
            true_predictions.append(passage_predictions)
            true_labels.append(passage_labels)

    if not true_labels:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

    return {
        "precision": float(
            precision_score(true_labels, true_predictions, zero_division=0)
        ),
        "recall": float(
            recall_score(true_labels, true_predictions, zero_division=0)
        ),
        "f1": float(
            f1_score(true_labels, true_predictions, zero_division=0)
        ),
    }


def preflight(model_reference=DEFAULT_MODEL):
    """Validate XML loading, tokenizer alignment, and metrics."""
    print("=== Preflight Check ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Training XML: {TRAIN_PATH}")
    print(f"Model/tokenizer: {model_reference}")

    documents = load_documents(TRAIN_PATH)
    print(f"Loaded documents: {len(documents)}")

    tokenizer = load_tokenizer(model_reference)
    print(f"Tokenizer class: {type(tokenizer).__name__}")

    dataset = BC5CDRDataset(
        documents=documents,
        tokenizer=tokenizer,
    )

    if len(dataset) == 0:
        raise ValueError("The tokenized dataset is empty.")

    print(f"Dataset examples: {len(dataset)}")

    label_counts = Counter()

    for example in dataset.examples:
        if not (
            len(example["input_ids"])
            == len(example["attention_mask"])
            == len(example["labels"])
        ):
            raise AssertionError("Input, mask, and label lengths differ.")

        for label_id in example["labels"]:
            if label_id != -100:
                label_counts[ID2LABEL[label_id]] += 1

    print("\nLabel distribution:")
    for label in LABEL2ID:
        print(f"  {label}: {label_counts[label]}")

    # Verify that metric calculation handles sequence boundaries correctly.
    synthetic_labels = np.array([[
        LABEL2ID["O"],
        LABEL2ID["B-Chemical"],
        LABEL2ID["I-Chemical"],
        LABEL2ID["O"],
        LABEL2ID["B-Disease"],
        LABEL2ID["I-Disease"],
        LABEL2ID["O"],
    ]])

    synthetic_logits = np.full(
        (1, 7, NUM_LABELS),
        -10.0,
    )

    for position, label_id in enumerate(synthetic_labels[0]):
        synthetic_logits[0, position, label_id] = 10.0

    metrics = compute_metrics(
        (synthetic_logits, synthetic_labels)
    )

    print("\nSynthetic metric test:")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")
    print(f"  F1: {metrics['f1']:.4f}")

    if not np.isclose(metrics["f1"], 1.0):
        raise AssertionError("Synthetic metric test failed.")

    print("\nPreflight passed.")


def train(
    model_reference=DEFAULT_MODEL,
    output_dir="models/pubmedbert-bc5cdr-ner",
    num_epochs=5,
    batch_size=4,
    learning_rate=2e-5,
):
    """Fine-tune a BERT-family model for BC5CDR NER."""
    if num_epochs < 1 or batch_size < 1:
        raise ValueError("Epochs and batch size must be positive.")

    resolved_model = resolve_model_path(model_reference)
    output_path = PROJECT_ROOT / output_dir

    print("=== Training ===")
    print(f"Model: {resolved_model}")
    print(f"Output directory: {output_path}")
    print(f"Epochs: {num_epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {learning_rate}")

    train_documents = load_documents(TRAIN_PATH)
    tokenizer = load_tokenizer(model_reference)

    train_dataset = BC5CDRDataset(
        documents=train_documents,
        tokenizer=tokenizer,
    )

    print(f"Training documents: {len(train_documents)}")
    print(f"Training examples: {len(train_dataset)}")

    model = AutoModelForTokenClassification.from_pretrained(
        resolved_model,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    data_collator = DataCollatorForTokenClassification(tokenizer)

    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        save_strategy="epoch",
        logging_strategy="epoch",
        report_to="none",
        push_to_hub=False,
        use_cpu=not torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving model to: {output_path}")
    trainer.save_model(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    print("Training complete.")


def evaluate(
    model_dir="models/pubmedbert-bc5cdr-ner",
    test_path=None,
):
    """Evaluate a saved model on the BC5CDR test set."""
    model_path = PROJECT_ROOT / model_dir

    test_xml_path = (
        Path(test_path)
        if test_path is not None
        else TEST_PATH
    )

    if not test_xml_path.is_absolute():
        test_xml_path = PROJECT_ROOT / test_xml_path

    if not model_path.is_dir():
        raise FileNotFoundError(
            f"Model directory not found: {model_path}"
        )

    print("=== Evaluation ===")
    print(f"Model: {model_path}")
    print(f"Test XML: {test_xml_path}")

    tokenizer = load_tokenizer(str(model_path))

    model = AutoModelForTokenClassification.from_pretrained(
        str(model_path)
    )

    test_documents = load_documents(test_xml_path)

    test_dataset = BC5CDRDataset(
        documents=test_documents,
        tokenizer=tokenizer,
    )

    print(f"Test documents: {len(test_documents)}")
    print(f"Test examples: {len(test_dataset)}")

    training_args = TrainingArguments(
        output_dir=str(
            PROJECT_ROOT / "output" / "evaluation" / "trainer"
        ),
        per_device_eval_batch_size=8,
        report_to="none",
        use_cpu=not torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    metrics = trainer.evaluate(eval_dataset=test_dataset)

    print("\n=== Results ===")
    print(f"Precision: {metrics.get('eval_precision', 0.0):.4f}")
    print(f"Recall: {metrics.get('eval_recall', 0.0):.4f}")
    print(f"F1: {metrics.get('eval_f1', 0.0):.4f}")

    results_path = (
        PROJECT_ROOT
        / "output"
        / "evaluation"
        / "pubmedbert_bc5cdr_test_results.json"
    )
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    print(f"Results saved to: {results_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune a BERT-family model for BC5CDR NER"
    )

    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--preflight",
        action="store_true",
        help="Validate data, tokenization, labels, and metrics",
    )
    actions.add_argument(
        "--train",
        action="store_true",
        help="Fine-tune the model",
    )
    actions.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate a saved model",
    )

    parser.add_argument(
        "--tokenizer",
        default=DEFAULT_MODEL,
        help="Local model directory or Hugging Face model identifier",
    )
    parser.add_argument(
        "--output-dir",
        default="models/pubmedbert-bc5cdr-ner",
        help="Output directory for training",
    )
    parser.add_argument(
        "--model-dir",
        default="models/pubmedbert-bc5cdr-ner",
        help="Saved model directory for evaluation",
    )
    parser.add_argument(
        "--test-path",
        default=None,
        help="Optional path to the BC5CDR test XML",
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-5)

    args = parser.parse_args()

    if args.preflight:
        preflight(args.tokenizer)

    elif args.train:
        train(
            model_reference=args.tokenizer,
            output_dir=args.output_dir,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
        )

    elif args.evaluate:
        evaluate(
            model_dir=args.model_dir,
            test_path=args.test_path,
        )


if __name__ == "__main__":
    main()
