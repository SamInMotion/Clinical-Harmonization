"""
Build abbreviation aliases for the BC5CDR dictionary from training data.

Gate D-2 policy:
- Use training-set text and annotations only.
- Add an acronym alias only when a plausible long-form expansion matches
  an existing dictionary entry with the same entity type.
- Preserve provenance for every generated alias.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from load_bc5cdr import load_bc5cdr
from dictionary_baseline import normalize_text


ACRONYM_EXPANSION_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z0-9\-]+(?:\s+[A-Za-z][A-Za-z0-9\-]+){0,7})"
    r"\s*\(\s*([A-Z][A-Za-z0-9\-]{1,9})\s*\)"
)


def is_acronym_like(text: str) -> bool:
    stripped = text.strip()
    return (
        1 <= len(stripped) <= 9
        and stripped.isupper()
        and any(character.isalpha() for character in stripped)
    )


def build_abbreviation_aliases(
    documents,
    base_dictionary,
):
    """
    Build acronym aliases from training documents.

    Returns:
        Tuple of (expanded_dictionary, alias_records)
    """
    expanded_dictionary = defaultdict(list, base_dictionary)
    alias_records = []

    for doc in documents:
        for passage in doc["passages"]:
            passage_text = passage["text"]

            expansion_candidates = {}
            for match in ACRONYM_EXPANSION_PATTERN.finditer(
                passage_text
            ):
                expansion = match.group(1).strip()
                acronym = match.group(2).strip()
                expansion_candidates[acronym] = expansion

            for annotation in passage["annotations"]:
                acronym = annotation["text"].strip()

                if not is_acronym_like(acronym):
                    continue

                expansion = expansion_candidates.get(acronym)
                if not expansion:
                    continue

                normalized_expansion = normalize_text(expansion)
                normalized_acronym = normalize_text(acronym)

                compatible_entries = [
                    entry
                    for entry in base_dictionary.get(
                        normalized_expansion, []
                    )
                    if entry["type"] == annotation["type"]
                ]

                if not compatible_entries:
                    continue

                existing_entries = expanded_dictionary[
                    normalized_acronym
                ]

                for entry in compatible_entries:
                    alias_entry = {
                        "original": entry["original"],
                        "type": entry["type"],
                        "mesh_id": entry["mesh_id"],
                    }

                    already_present = any(
                        existing["original"] == alias_entry["original"]
                        and existing["type"] == alias_entry["type"]
                        and existing["mesh_id"] == alias_entry["mesh_id"]
                        for existing in existing_entries
                    )

                    if already_present:
                        continue

                    existing_entries.append(alias_entry)

                    alias_records.append({
                        "doc_id": doc["id"],
                        "passage_type": passage["type"],
                        "acronym": acronym,
                        "normalized_acronym": normalized_acronym,
                        "expansion": expansion,
                        "normalized_expansion": normalized_expansion,
                        "entity_type": annotation["type"],
                        "mesh_id": annotation["mesh_id"],
                    })

    return expanded_dictionary, alias_records


def save_expanded_dictionary(dictionary, output_path: str):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            {key: value for key, value in dictionary.items()},
            file,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    from dictionary_baseline import build_dictionary

    training_path = Path(
        "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        "CDR_TrainingSet.BioC.xml"
    )
    base_dictionary_path = Path(
        "data/terminology/bc5cdr_dictionary.json"
    )
    expanded_dictionary_path = Path(
        "data/terminology/"
        "bc5cdr_dictionary_abbreviation_expanded.json"
    )
    aliases_path = Path(
        "data/terminology/"
        "bc5cdr_abbreviation_aliases.json"
    )

    if not training_path.exists():
        raise FileNotFoundError(f"Training set not found: {training_path}")
    if not base_dictionary_path.exists():
        raise FileNotFoundError(
            f"Base dictionary not found: {base_dictionary_path}"
        )

    with base_dictionary_path.open("r", encoding="utf-8") as file:
        base_dictionary = defaultdict(list, json.load(file))

    documents = load_bc5cdr(str(training_path))
    expanded_dictionary, alias_records = build_abbreviation_aliases(
        documents, base_dictionary
    )

    save_expanded_dictionary(
        expanded_dictionary, str(expanded_dictionary_path)
    )

    with aliases_path.open("w", encoding="utf-8") as file:
        json.dump(alias_records, file, indent=2, ensure_ascii=False)

    print(f"Base dictionary keys: {len(base_dictionary)}")
    print(f"Expanded dictionary keys: {len(expanded_dictionary)}")
    print(f"Generated alias records: {len(alias_records)}")
    print(f"Expanded dictionary: {expanded_dictionary_path}")
    print(f"Alias provenance: {aliases_path}")
