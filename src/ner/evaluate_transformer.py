"""
Evaluation script for transformer NER.
Compares transformer predictions against dictionary baseline and gold standard.
"""

import json
from typing import List, Dict
from pathlib import Path
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ner.evaluate_ner import (
    Span, evaluate_ner, evaluate_by_type, print_results,
    gold_to_spans,
)
from ner.load_bc5cdr import load_bc5cdr


@dataclass
class EvaluationReport:
    dataset_name: str
    gold_total: int
    pred_total: int
    overall: Dict
    by_type: Dict[str, Dict]
    unseen_entities: Dict


def evaluate_transformer_ner(
    model,
    tokenizer,
    test_docs,
    train_docs=None,
) -> EvaluationReport:
    """Evaluate transformer NER model."""
    from ner.transformer_ner import predict_ner
    
    print("Predicting on test set...")
    pred_spans = predict_ner(model, tokenizer, test_docs)
    
    print("Loading gold standard...")
    gold_spans = gold_to_spans(test_docs)
    
    overall = evaluate_ner(gold_spans, pred_spans)
    by_type = evaluate_by_type(gold_spans, pred_spans)
    
    unseen_entities = {}
    if train_docs is not None:
        train_entity_texts = set()
        for doc in train_docs:
            for entity in doc.all_entities:
                train_entity_texts.add(entity["text"].lower())
        
        unseen_gold = [s for s in gold_spans if s.text.lower() not in train_entity_texts]
        unseen_pred = [p for p in pred_spans if p.text.lower() not in train_entity_texts]
        
        if unseen_gold:
            unseen_results = evaluate_ner(unseen_gold, unseen_pred)
            unseen_entities = {
                "count": len(unseen_gold),
                "results": unseen_results,
            }
    
    return EvaluationReport(
        dataset_name="BC5CDR Test Set",
        gold_total=len(gold_spans),
        pred_total=len(pred_spans),
        overall=overall,
        by_type=by_type,
        unseen_entities=unseen_entities,
    )


def compare_baseline_vs_transformer(
    baseline_results: Dict,
    transformer_results: EvaluationReport,
) -> str:
    """Generate comparison report."""
    report = []
    report.append("\n" + "="*70)
    report.append("BASELINE VS TRANSFORMER COMPARISON")
    report.append("="*70)
    
    report.append("\nOverall Performance:")
    report.append(f"  {'Metric':<15} {'Baseline':<12} {'Transformer':<12} {'Improvement':<12}")
    report.append("-" * 55)
    
    metrics = ["precision", "recall", "f1"]
    for metric in metrics:
        baseline_val = baseline_results.get(metric, 0.0)
        transformer_val = transformer_results.overall.get(metric, 0.0)
        improvement = transformer_val - baseline_val
        report.append(f"  {metric.capitalize():<15} {baseline_val:<12.4f} {transformer_val:<12.4f} {improvement:+.4f}")
    
    report.append("\nBy Entity Type (F1):")
    all_types = set(baseline_results.get("by_type", {}).keys()) | set(transformer_results.by_type.keys())
    
    for entity_type in sorted(all_types):
        baseline_f1 = baseline_results.get("by_type", {}).get(entity_type, {}).get("f1", 0.0)
        transformer_f1 = transformer_results.by_type.get(entity_type, {}).get("f1", 0.0)
        improvement = transformer_f1 - baseline_f1
        report.append(f"  {entity_type:<15} {baseline_f1:<12.4f} {transformer_f1:<12.4f} {improvement:+.4f}")
    
    if transformer_results.unseen_entities:
        report.append("\nUnseen Entities (generalization):")
        unseen = transformer_results.unseen_entities["results"]
        report.append(f"  Count: {transformer_results.unseen_entities['count']} entities")
        report.append(f"  F1: {unseen['f1']:.4f} (vs 0.000 for dictionary baseline)")
    
    report.append("="*70)
    
    return "\n".join(report)


def save_evaluation_report(report: EvaluationReport, filepath: Path):
    """Save evaluation report to JSON."""
    data = {
        "dataset_name": report.dataset_name,
        "gold_total": report.gold_total,
        "pred_total": report.pred_total,
        "overall": report.overall,
        "by_type": report.by_type,
        "unseen_entities": report.unseen_entities,
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved evaluation report to {filepath}")


if __name__ == "__main__":
    print("This script is meant to be imported after training.")
    print("See transformer_ner.py for training and evaluation example.")
