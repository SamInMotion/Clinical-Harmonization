from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NER_DIR = PROJECT_ROOT / "src" / "ner"
sys.path.insert(0, str(NER_DIR))

from load_bc5cdr import load_bc5cdr
from transformer_ner import BC5CDRDataset
from transformers import AutoTokenizer

DATA_DIR = PROJECT_ROOT / "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516"
XML_PATH = DATA_DIR / "CDR_DevelopmentSet.BioC.xml"
MODEL_PATH = PROJECT_ROOT / "models/pubmedbert-local"

print(f"Project root: {PROJECT_ROOT}")
print(f"Development XML exists: {XML_PATH.exists()}")
print(f"Development XML path: {XML_PATH}")

if not XML_PATH.is_file():
    raise SystemExit(f"Development XML file not found: {XML_PATH}")

documents = load_bc5cdr(str(XML_PATH))

print(f"\nLoaded development documents: {len(documents)}")

if not documents:
    raise SystemExit("No documents were loaded from the development XML.")

document = documents[0]

print("\nFirst document keys:")
print(sorted(document.keys()))

print("\nFirst document:")
for key, value in document.items():
    if key == "passages":
        print(f"{key}: {len(value)} passages")
        if value:
            print("First passage:")
            for passage_key, passage_value in value[0].items():
                if passage_key == "text":
                    print(f"  {passage_key}: {str(passage_value)[:300]}")
                else:
                    print(f"  {passage_key}: {passage_value}")
    else:
        print(f"{key}: {value}")

tokenizer = AutoTokenizer.from_pretrained(
    str(MODEL_PATH),
    use_fast=True,
    local_files_only=True,
)

print(f"\nTokenizer class: {tokenizer.__class__.__name__}")
print(f"Fast tokenizer: {tokenizer.is_fast}")

if not tokenizer.is_fast:
    raise SystemExit(
        "A fast tokenizer is required for character-offset alignment."
    )

dataset = BC5CDRDataset(
    documents=documents[:1],
    tokenizer=tokenizer,
    max_length=512,
)

print(f"\nDataset examples from first document: {len(dataset)}")

if len(dataset) == 0:
    raise SystemExit("The dataset produced no examples.")

example = dataset[0]

print("\nDataset example keys:")
print(sorted(example.keys()))

for key, value in example.items():
    if isinstance(value, list):
        print(
            f"{key}: list with {len(value)} items; "
            f"first 10: {value[:10]}"
        )
    else:
        print(f"{key}: {value}")

print("\nDevelopment-data diagnostic passed.")
