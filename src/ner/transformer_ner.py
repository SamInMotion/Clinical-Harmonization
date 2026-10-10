"""
Fine-tune BioBERT for BC5CDR NER.

Usage:
    python src/ner/transformer_ner.py --preflight   # Validate data and labels
    python src/ner/transformer_ner.py --train       # Fine-tune model
    python src/ner/transformer_ner.py --evaluate    # Evaluate on test set

Output:
    - Model checkpoints in models/
    - Evaluation results in output/evaluation/
"""

import argparse
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer
from transformers import DataCollatorForTokenClassification
import numpy as np
from seqeval.metrics import classification_report

from load_bc5cdr import load_bc5cdr


# Label mapping for BC5CDR
LABEL2ID = {
    "O": 0,
    "B-Chemical": 1,
    "I-Chemical": 2,
    "B-Disease": 3,
    "I-Disease": 4,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
NUM_LABELS = len(LABEL2ID)


class BC5CDRDataset(Dataset):
    """BC5CDR dataset for token classification."""
    
    def __init__(self, documents, tokenizer, max_length=512):
        self.examples = []
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        for doc in documents:
            for passage in doc['passages']:
                # Tokenize passage text
                tokens = tokenizer.tokenize(passage['text'])
                
                # Build BIO labels
                labels = self._build_bio_labels(passage, tokens)
                
                # Truncate if necessary
                if len(tokens) > max_length - 2:  # [CLS] and [SEP]
                    tokens = tokens[:max_length - 2]
                    labels = labels[:max_length - 2]
                
                # Add special tokens
                tokens = ['[CLS]'] + tokens + ['[SEP]']
                labels = [-100] + labels + [-100]  # Ignore [CLS] and [SEP] in loss
                
                # Convert to input IDs
                input_ids = tokenizer.convert_tokens_to_ids(tokens)
                attention_mask = [1] * len(input_ids)
                
                self.examples.append({
                    'input_ids': input_ids,
                    'attention_mask': attention_mask,
                    'labels': labels,
                    'doc_id': doc['id'],
                    'passage_type': passage['type'],
                    'text': passage['text']
                })
    
    def _build_bio_labels(self, passage, tokens):
        """
        Build BIO labels for tokens.
        
        Args:
            passage: Passage dict with 'text', 'annotations', 'offset'
            tokens: List of token strings
        
        Returns:
            List of label IDs (one per token)
        """
        # Initialize all tokens as O
        labels = ['O'] * len(tokens)
        
        # Get token offsets from tokenizer
        # We need to map character offsets to token indices
        
        # Re-tokenize to get offset mapping
        token_offsets = []
        current_pos = 0
        for token in tokens:
            # Find token in passage text starting from current_pos
            pos = passage['text'].find(token, current_pos)
            if pos == -1:
                # Token not found (might be special token or subword)
                token_offsets.append((current_pos, current_pos + len(token)))
            else:
                token_offsets.append((pos, pos + len(token)))
                current_pos = pos + len(token)
        
        # Assign labels based on every BioC annotation location.
        # Gate C-3: the first location receives a B label; subsequent
        # locations of the same annotation receive I labels.
        for ann in passage['annotations']:
            ann_type = ann['type']

            for location_index, location in enumerate(
                ann['locations']
            ):
                ann_start = location['local_offset']
                ann_end = ann_start + location['length']
                location_label = (
                    f'B-{ann_type}'
                    if location_index == 0
                    else f'I-{ann_type}'
                )

                for i, (tok_start, tok_end) in enumerate(token_offsets):
                    if tok_start < ann_end and tok_end > ann_start:
                        if tok_start == ann_start:
                            labels[i] = location_label
                        else:
                            labels[i] = f'I-{ann_type}'

        # Convert to label IDs
        label_ids = [LABEL2ID.get(label, LABEL2ID['O']) for label in labels]
        
        return label_ids
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        return self.examples[idx]


def compute_metrics(eval_pred):
    """Compute NER metrics using seqeval."""
    predictions, labels = eval_pred
    
    # Convert predictions to label IDs
    predictions = np.argmax(predictions, axis=-1)
    
    # Remove ignored labels (-100)
    true_predictions = []
    true_labels = []
    
    for pred, label in zip(predictions, labels):
        for p, l in zip(pred, label):
            if l != -100:
                true_predictions.append(ID2LABEL[p])
                true_labels.append(ID2LABEL[l])
    
    # Compute metrics using seqeval
    report = classification_report([true_labels], [true_predictions], output_dict=True)
    
    # Extract overall metrics
    overall = report.get('overall', {})
    
    return {
        'precision': overall.get('precision', 0.0),
        'recall': overall.get('recall', 0.0),
        'f1': overall.get('f1', 0.0),
    }


def preflight(tokenizer_name: str = "dmis-lab/biobert-v1-base"):
    """
    Validate data loading and BIO label construction.
    
    This is a cheap check before expensive training.
    """
    print(f"=== Preflight Check ===")
    print(f"Tokenizer: {tokenizer_name}")
    
    # Load training data
    train_path = Path("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TrainingSet.BioC.xml")
    print(f"Loading data from: {train_path}")
    documents = load_bc5cdr(str(train_path))
    print(f"Loaded {len(documents)} documents")
    
    # Load tokenizer
    print(f"Loading tokenizer: {tokenizer_name}")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    print(f"✅ Tokenizer loaded")
    
    # Create dataset
    print("Building dataset...")
    dataset = BC5CDRDataset(documents, tokenizer)
    print(f"Dataset size: {len(dataset)} examples")
    
    # Check label distribution
    label_counts = defaultdict(int)
    for example in dataset.examples:
        for label_id in example['labels']:
            if label_id != -100:
                label_counts[ID2LABEL[label_id]] += 1
    
    print(f"\nLabel distribution:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count}")
    
    # Check a sample
    sample = dataset.examples[0]
    print(f"\nSample example:")
    print(f"  Doc ID: {sample['doc_id']}")
    print(f"  Passage type: {sample['passage_type']}")
    print(f"  Input length: {len(sample['input_ids'])}")
    print(f"  Labels: {[ID2LABEL[l] for l in sample['labels'] if l != -100][:20]}...")
    
    # Synthetic metrics test
    print(f"\nSynthetic metrics test:")
    true_labels = ['O', 'B-Chemical', 'I-Chemical', 'O', 'B-Disease', 'I-Disease', 'O']
    pred_labels = ['O', 'B-Chemical', 'I-Chemical', 'O', 'B-Disease', 'I-Disease', 'O']
    report = classification_report([[true_labels]], [[pred_labels]], output_dict=True)
    print(f"  Perfect match F1: {report['overall']['f1']:.4f}")
    
    print(f"\n✅ Preflight passed!")
    print(f"   - Data loads correctly")
    print(f"   - BIO labels constructed")
    print(f"   - Metrics computation works")


def train(
    tokenizer_name: str = "dmis-lab/biobert-v1-base",
    output_dir: str = "models/biobert-bc5cdr-ner",
    num_epochs: int = 5,
    batch_size: int = 4,
    learning_rate: float = 2e-5,
):
    """
    Fine-tune BioBERT for BC5CDR NER.
    """
    print(f"=== Training ===")
    print(f"Tokenizer: {tokenizer_name}")
    print(f"Output dir: {output_dir}")
    print(f"Epochs: {num_epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {learning_rate}")
    
    # Load data
    train_path = Path("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TrainingSet.BioC.xml")
    print(f"Loading training data...")
    train_docs = load_bc5cdr(str(train_path))
    print(f"Training documents: {len(train_docs)}")
    
    # Load tokenizer
    print(f"Loading tokenizer: {tokenizer_name}")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    print(f"✅ Tokenizer loaded")
    
    # Create dataset
    print("Building training dataset...")
    train_dataset = BC5CDRDataset(train_docs, tokenizer)
    print(f"Training examples: {len(train_dataset)}")
    
    # Load model
    print(f"Loading model: {tokenizer_name}")
    model = AutoModelForTokenClassification.from_pretrained(
        tokenizer_name,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    print(f"✅ Model loaded")
    
    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        save_strategy="epoch",
        logging_strategy="epoch",
        report_to="none",  # Disable wandb
        push_to_hub=False,
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    
    # Train
    print(f"Starting training...")
    trainer.train()
    
    # Save model
    print(f"Saving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"✅ Training complete!")


def evaluate(
    model_dir: str = "models/biobert-bc5cdr-ner",
    test_path: str = "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml",
):
    """
    Evaluate trained model on test set.
    """
    print(f"=== Evaluation ===")
    print(f"Model dir: {model_dir}")
    print(f"Test path: {test_path}")
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForTokenClassification.from_pretrained(model_dir)
    
    # Load test data
    test_docs = load_bc5cdr(test_path)
    print(f"Test documents: {len(test_docs)}")
    
    # Create dataset
    test_dataset = BC5CDRDataset(test_docs, tokenizer)
    print(f"Test examples: {len(test_dataset)}")
    
    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer)
    
    # Training arguments (for evaluation)
    training_args = TrainingArguments(
        output_dir="output/evaluation",
        report_to="none",
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    
    # Evaluate
    print(f"Evaluating...")
    metrics = trainer.evaluate(eval_dataset=test_dataset)
    
    print(f"\n=== Results ===")
    print(f"Precision: {metrics.get('eval_precision', 0.0):.4f}")
    print(f"Recall: {metrics.get('eval_recall', 0.0):.4f}")
    print(f"F1: {metrics.get('eval_f1', 0.0):.4f}")
    
    # Save results
    output_path = Path("output/evaluation/biobert_bc5cdr_test_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune BioBERT for BC5CDR NER")
    parser.add_argument("--preflight", action="store_true", help="Run preflight check")
    parser.add_argument("--train", action="store_true", help="Train model")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate model")
    parser.add_argument("--tokenizer", type=str, default="dmis-lab/biobert-v1-base", help="Tokenizer name")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    
    args = parser.parse_args()
    
    if args.preflight:
        preflight(args.tokenizer)
    elif args.train:
        train(
            tokenizer_name=args.tokenizer,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
        )
    elif args.evaluate:
        evaluate()
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/ner/transformer_ner.py --preflight")
        print("  python src/ner/transformer_ner.py --train --epochs 5 --batch-size 4")
        print("  python src/ner/transformer_ner.py --evaluate")


if __name__ == "__main__":
    main()
