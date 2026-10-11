
"""Full PubMedBERT fine-tuning for BC5CDR NER."""

import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from load_bc5cdr import load_bc5cdr
from transformer_ner import BC5CDRDataset, LABEL2ID, ID2LABEL
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    get_linear_schedule_with_warmup,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

XML_PATH = (
    PROJECT_ROOT
    / "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
    "CDR_TrainingSet.BioC.xml"
)
MODEL_PATH = PROJECT_ROOT / "models/pubmedbert-local"
OUTPUT_DIR = PROJECT_ROOT / "output/training/pubmedbert_bc5cdr"
LOG_PATH = PROJECT_ROOT / "output/logs/pubmedbert_bc5cdr_training.json"

SEED = 42
EPOCHS = 3
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
MAX_LENGTH = 512
WARMUP_RATIO = 0.1


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def main():
    set_seed(SEED)
    device = torch.device("cpu")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_PATH),
        use_fast=True,
        local_files_only=True,
    )

    if not tokenizer.is_fast:
        raise RuntimeError(
            "A fast tokenizer is required for character-offset alignment."
        )

    documents = load_bc5cdr(str(XML_PATH))
    print(f"Loaded training documents: {len(documents)}")

    dataset = BC5CDRDataset(
        documents=documents,
        tokenizer=tokenizer,
        max_length=MAX_LENGTH,
    )

    print(f"Training examples: {len(dataset)}")

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

    generator = torch.Generator().manual_seed(SEED)

    data_loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        collate_fn=collate,
        generator=generator,
    )

    model = AutoModelForTokenClassification.from_pretrained(
        str(MODEL_PATH),
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=0.01,
    )

    total_steps = len(data_loader) * EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATIO)

    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    history = {
        "experiment": "EXP-006",
        "purpose": "Full three-epoch PubMedBERT BC5CDR fine-tuning",
        "seed": SEED,
        "device": "cpu",
        "model_path": str(MODEL_PATH),
        "training_xml": str(XML_PATH),
        "training_examples": len(dataset),
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "max_length": MAX_LENGTH,
        "epochs": EPOCHS,
        "total_optimizer_steps": total_steps,
        "warmup_steps": warmup_steps,
        "epoch_losses": [],
        "epoch_runtimes_seconds": [],
        "checkpoints": [],
    }

    model.train()
    overall_start = time.perf_counter()

    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.perf_counter()
        running_loss = 0.0
        batch_count = 0

        for batch in data_loader:
            optimizer.zero_grad()
            outputs = model(**batch)
            outputs.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            running_loss += outputs.loss.item()
            batch_count += 1

        average_loss = running_loss / batch_count
        epoch_seconds = time.perf_counter() - epoch_start

        checkpoint_dir = OUTPUT_DIR / f"epoch_{epoch}"
        model.save_pretrained(checkpoint_dir)
        tokenizer.save_pretrained(checkpoint_dir)

        history["epoch_losses"].append(average_loss)
        history["epoch_runtimes_seconds"].append(epoch_seconds)
        history["checkpoints"].append(str(checkpoint_dir))

        LOG_PATH.write_text(
            json.dumps(history, indent=2),
            encoding="utf-8",
        )

        print(
            f"Epoch {epoch}/{EPOCHS}: "
            f"average loss={average_loss:.4f}, "
            f"runtime={epoch_seconds / 60:.2f} minutes"
        )
        print(f"Checkpoint saved: {checkpoint_dir}")

    history["total_runtime_seconds"] = time.perf_counter() - overall_start
    history["loss_decreased"] = (
        history["epoch_losses"][-1] < history["epoch_losses"][0]
    )

    LOG_PATH.write_text(
        json.dumps(history, indent=2),
        encoding="utf-8",
    )

    print(
        "Training complete: "
        f"total runtime={history['total_runtime_seconds'] / 3600:.2f} hours"
    )
    print(f"Loss trajectory: {history['epoch_losses']}")
    print(f"Training record written to: {LOG_PATH}")


if __name__ == "__main__":
    main()
