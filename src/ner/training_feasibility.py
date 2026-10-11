
"""EXP-005: estimate PubMedBERT fine-tuning feasibility on CPU."""

import json
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
)

from load_bc5cdr import load_bc5cdr
from transformer_ner import BC5CDRDataset, LABEL2ID, ID2LABEL


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = Path("models/pubmedbert-local")
OUTPUT_PATH = Path(
    "output/evaluation/pubmedbert_training_feasibility.json"
)

BATCH_SIZE = 16
MAX_LENGTH = 512
BENCHMARK_BATCHES = 5


def main():
    device = torch.device("cpu")

    model_path = PROJECT_ROOT / MODEL_PATH
    output_path = PROJECT_ROOT / OUTPUT_PATH

    training_path = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / "bc5cdr"
        / "CDR_Data"
        / "CDR.Corpus.v010516"
        / "CDR_TrainingSet.BioC.xml"
    )

    if not training_path.is_file():
        raise FileNotFoundError(
            f"BC5CDR training XML not found: {training_path}"
        )

    if not model_path.is_dir():
        raise FileNotFoundError(
            f"Local model directory not found: {model_path}"
        )

    print(f"Loading tokenizer from: {model_path}")

    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        use_fast=True,
        local_files_only=True,
    )

    if not tokenizer.is_fast:
        raise RuntimeError(
            "The local model loaded a slow tokenizer. "
            "BC5CDRDataset requires a fast tokenizer for "
            "character-offset alignment. Check the tokenizer "
            "files in models/pubmedbert-local and ensure a "
            "compatible fast tokenizer is available."
        )

    print(f"Tokenizer class: {type(tokenizer).__name__}")
    print(f"Loading BC5CDR data from: {training_path}")

    documents = load_bc5cdr(str(training_path))
    print(f"Loaded documents: {len(documents)}")

    if not documents:
        raise ValueError("The BC5CDR training file contains no documents.")

    dataset = BC5CDRDataset(
        documents=documents,
        tokenizer=tokenizer,
        max_length=MAX_LENGTH,
    )

    if len(dataset) == 0:
        raise ValueError("The tokenized training dataset is empty.")

    data_collator = DataCollatorForTokenClassification(tokenizer)

    def collate(batch):
        model_features = [
            {
                "input_ids": example["input_ids"],
                "attention_mask": example["attention_mask"],
                "labels": example["labels"],
            }
            for example in batch
        ]
        return data_collator(model_features)

    data_loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=collate,
    )

    print(f"Loading model from: {model_path}")

    model = AutoModelForTokenClassification.from_pretrained(
        str(model_path),
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        local_files_only=True,
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=2e-5,
    )
    model.train()

    batches_per_epoch = len(data_loader)

    if batches_per_epoch == 0:
        raise ValueError("The training DataLoader contains no batches.")

    batches_to_benchmark = min(
        BENCHMARK_BATCHES,
        batches_per_epoch,
    )

    benchmark_tokens = 0
    benchmark_seconds = 0.0

    print(
        f"Benchmarking {batches_to_benchmark} of "
        f"{batches_per_epoch} batches on {device}."
    )

    for batch_index, batch in enumerate(data_loader):
        if batch_index >= batches_to_benchmark:
            break

        benchmark_tokens += int(
            batch["attention_mask"].sum().item()
        )

        start = time.perf_counter()

        optimizer.zero_grad()
        outputs = model(**batch)
        outputs.loss.backward()
        optimizer.step()

        elapsed = time.perf_counter() - start
        benchmark_seconds += elapsed

        print(
            f"  Batch {batch_index + 1}/{batches_to_benchmark}: "
            f"{elapsed:.2f} seconds"
        )

    average_batch_seconds = (
        benchmark_seconds / batches_to_benchmark
    )

    estimated_seconds_per_epoch = (
        average_batch_seconds * batches_per_epoch
    )
    estimated_hours_per_epoch = (
        estimated_seconds_per_epoch / 3600
    )
    estimated_hours_three_epochs = (
        estimated_hours_per_epoch * 3
    )

    result = {
        "experiment": "EXP-005",
        "purpose": (
            "Estimate PubMedBERT BC5CDR fine-tuning feasibility "
            "before full training"
        ),
        "model_path": str(model_path),
        "device": str(device),
        "batch_size": BATCH_SIZE,
        "max_length": MAX_LENGTH,
        "training_documents": len(documents),
        "training_examples": len(dataset),
        "training_batches_per_epoch": batches_per_epoch,
        "benchmark_batches": batches_to_benchmark,
        "benchmark_non_padding_tokens": benchmark_tokens,
        "benchmark_seconds": benchmark_seconds,
        "average_batch_seconds": average_batch_seconds,
        "estimated_seconds_per_epoch": estimated_seconds_per_epoch,
        "estimated_hours_per_epoch": estimated_hours_per_epoch,
        "estimated_hours_three_epochs": estimated_hours_three_epochs,
        "estimated_optimizer_steps_per_epoch": batches_per_epoch,
        "estimated_optimizer_steps_three_epochs": batches_per_epoch * 3,
        "interpretation": (
            "Rough estimate based on the first benchmark batches. "
            "Runtime depends on sequence lengths, hardware load, "
            "and memory pressure. The estimate excludes tokenization, "
            "evaluation, checkpoint saving, and data-loading overhead."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print("\n=== EXP-005 Results ===")
    print(f"Training documents: {len(documents)}")
    print(f"Training examples: {len(dataset)}")
    print(f"Batches per epoch: {batches_per_epoch}")
    print(f"Benchmark batches: {batches_to_benchmark}")
    print(f"Benchmark tokens: {benchmark_tokens}")
    print(f"Average CPU batch time: {average_batch_seconds:.3f} seconds")
    print(f"Estimated time per epoch: {estimated_hours_per_epoch:.2f} hours")
    print(
        f"Estimated time for 3 epochs: "
        f"{estimated_hours_three_epochs:.2f} hours"
    )
    print(f"Result written to: {output_path}")


if __name__ == "__main__":
    main()
