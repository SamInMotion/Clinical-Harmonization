"""
Regression test for Gate C-3: BIO labels must cover every BioC location.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src" / "ner"))

from transformer_ner import BC5CDRDataset, LABEL2ID


def test_bio_labels_cover_both_locations():
    dataset = BC5CDRDataset.__new__(BC5CDRDataset)

    passage = {
        "text": "Cerebellar dysfunction was observed.",
        "offset": 0,
        "annotations": [
            {
                "text": "Cerebellar dysfunction",
                "type": "Disease",
                "mesh_id": "D001249",
                "offset": 0,
                "local_offset": 0,
                "length": 10,
                "locations": [
                    {
                        "doc_offset": 0,
                        "local_offset": 0,
                        "length": 10,
                        "observed_text": "Cerebellar",
                    },
                    {
                        "doc_offset": 11,
                        "local_offset": 11,
                        "length": 11,
                        "observed_text": "dysfunction",
                    },
                ],
            }
        ],
    }

    tokens = ["Cerebellar", "dysfunction", "was", "observed", "."]
    labels = dataset._build_bio_labels(passage, tokens)

    assert labels == [
        LABEL2ID["B-Disease"],
        LABEL2ID["I-Disease"],
        LABEL2ID["O"],
        LABEL2ID["O"],
        LABEL2ID["O"],
    ]


def test_single_location_bio_labels_unchanged():
    dataset = BC5CDRDataset.__new__(BC5CDRDataset)

    passage = {
        "text": "Aspirin reduces pain.",
        "offset": 0,
        "annotations": [
            {
                "text": "Aspirin",
                "type": "Chemical",
                "mesh_id": "D001249",
                "offset": 0,
                "local_offset": 0,
                "length": 7,
                "locations": [
                    {
                        "doc_offset": 0,
                        "local_offset": 0,
                        "length": 7,
                        "observed_text": "Aspirin",
                    }
                ],
            }
        ],
    }

    tokens = ["Aspirin", "reduces", "pain", "."]
    labels = dataset._build_bio_labels(passage, tokens)

    assert labels == [
        LABEL2ID["B-Chemical"],
        LABEL2ID["O"],
        LABEL2ID["O"],
        LABEL2ID["O"],
    ]
