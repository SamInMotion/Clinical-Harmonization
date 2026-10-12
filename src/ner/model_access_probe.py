"""
Check whether candidate biomedical transformer models are accessible.

This probe queries Hugging Face model metadata only. It does not download
model weights, train a model, or modify the active NER pipeline.
"""

import json
from pathlib import Path

from huggingface_hub import HfApi


CANDIDATE_MODELS = [
    "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
    "dmis-lab/biobert-v1.1",
    "dmis-lab/biobert-base-cased-v1.2",
    "cambridgeltl/BioMedBERT-base-uncased-abstract-fulltext",
]


def main():
    api = HfApi()
    results = []

    for model_id in CANDIDATE_MODELS:
        record = {
            "model_id": model_id,
            "accessible": False,
            "gated": None,
            "private": None,
            "error": None,
        }

        try:
            info = api.model_info(model_id)
            record["accessible"] = True
            record["gated"] = info.gated
            record["private"] = info.private
        except Exception as error:
            record["error"] = f"{type(error).__name__}: {error}"

        results.append(record)

        status = (
            "ACCESSIBLE"
            if record["accessible"]
            else "NOT ACCESSIBLE"
        )
        print(f"{status}: {model_id}")
        if record["error"]:
            print(f"  {record['error']}")

    output_path = Path(
        "output/evaluation/model_access_probe.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "date": "2026-10-11",
                "purpose": (
                    "Identify an accessible biomedical transformer "
                    "candidate; no weights downloaded"
                ),
                "models": results,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nProbe written to: {output_path}")


if __name__ == "__main__":
    main()
