"""
Tiny CPU overfit preflight for BC5CDR transformer NER.

Purpose:
    Verify that the local PubMedBERT model, tokenizer, dataset, labels,
    optimizer, and training loop can perform learning steps.

This is not a model-performance evaluation. It does not establish that the
model is ready for full training or that it improves NER accuracy.
"""

import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
)

sys.path.insert(0, str(Path(__file__).parent))

from load_bc5cdr import load_bc5cdr
from transformer_ner import (
    BC5CDRDataset,
    LABEL2ID,
    ID2LABEL,
)


def main():
    model_path = Path("models/pubmedbert-local")
    development_path = Path(
        "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        "CDR_DevelopmentSet.BioC.xml"
    )

    print("Loading local PubMedBERT tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path), use_fast=True
    )
    model = AutoModelForTokenClassification.from_pretrained(
        str(model_path),
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    print("Loading a small development subset...")
    documents = load_bc5cdr(str(development_path))
    small_documents = documents[:8]

    dataset = BC5CDRDataset(
        small_documents, tokenizer, max_length=256
    )

    print(f"Overfit subset passages: {len(dataset)}")

    data_collator = DataCollatorForTokenClassification(
        tokenizer
    )

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
        batch_size=2,
        shuffle=True,
        collate_fn=collate,
    )

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=5e-5
    )

    model.train()

    losses = []

    for epoch in range(3):
        epoch_loss = 0.0
        batches = 0

        for batch in data_loader:
            optimizer.zero_grad()

            outputs = model(**batch)

            loss = outputs.loss
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            batches += 1

        average_loss = epoch_loss / batches
        losses.append(average_loss)

        print(
            f"Epoch {epoch + 1}: "
            f"average loss={average_loss:.4f}"
        )

    loss_decreased = losses[-1] < losses[0]

    output_directory = Path("output/evaluation")
    output_directory.mkdir(parents=True, exist_ok=True)

    result = {
        "date": "2026-10-11",
        "purpose": (
            "Tiny CPU overfit preflight; not an accuracy evaluation"
        ),
        "model": (
            "microsoft/BiomedNLP-PubMedBERT-base-uncased-"
            "abstract-fulltext"
        ),
        "device": "cpu",
        "passages": len(dataset),
        "epochs": 3,
        "batch_size": 2,
        "losses": losses,
        "loss_decreased": loss_decreased,
    }

    output_path = (
        output_directory / "tiny_overfit_preflight.json"
    )
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print(f"\nLoss trajectory: {losses}")
    print(f"Loss decreased: {loss_decreased}")
    print(f"Result written to: {output_path}")

    if not loss_decreased:
        print(
            "WARNING: Loss did not decrease. Do not start full "
            "training; investigate data, labels, optimizer, or "
            "hardware before proceeding."
        )
    else:
        print("E-3 TINY OVERFIT PREFLIGHT PASSED")


if __name__ == "__main__":
    main()
