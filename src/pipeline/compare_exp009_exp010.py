"""Compare EXP-009 and EXP-010 harmonization outputs.

Reports newly mapped occurrences and the normalized mentions responsible.
"""

import csv
from collections import Counter
from pathlib import Path


def load_mapped(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def occurrence_key(record):
    return (
        record["document_id"],
        record["passage_type"],
        record["start_char"],
        record["end_char"],
        record["mention_text"],
    )


exp009 = load_mapped(
    "output/harmonization/exp009/mapped_records.csv"
)
exp010 = load_mapped(
    "output/harmonization/exp010/mapped_records.csv"
)

exp009_keys = {occurrence_key(record) for record in exp009}

new_mappings = [
    record
    for record in exp010
    if occurrence_key(record) not in exp009_keys
]

mention_counts = Counter(
    (record["mention_text"], record["concept_name"])
    for record in new_mappings
)

print(f"EXP-009 mapped: {len(exp009)}")
print(f"EXP-010 mapped: {len(exp010)}")
print(f"New mappings: {len(new_mappings)}")

print("\nNew mapped mention -> concept:")
for (mention, concept), count in mention_counts.most_common():
    print(f"  {count:4d}  {mention!r} -> {concept}")

print("\nSample new records:")
for record in new_mappings[:20]:
    print(
        f"  {record['document_id']} "
        f"{record['passage_type']} "
        f"{record['mention_text']!r} -> "
        f"{record['concept_name']} "
        f"({record['domain']})"
    )