"""
Shared gold-span extraction for BC5CDR BioC annotations.

Gate C-2 policy:
- One gold span is emitted for every BioC <location>.
- Annotation-level text and MeSH ID are retained as provenance.
- Exact matching includes document, passage, local offset, length, and type.
"""

from typing import List, Dict


def extract_gold_location_spans(documents: List[Dict]) -> List[Dict]:
    """
    Convert BioC annotations into location-level gold spans.

    Args:
        documents: Documents returned by load_bc5cdr().

    Returns:
        List of gold-span dictionaries.
    """
    gold_spans = []

    for doc in documents:
        for passage in doc["passages"]:
            for annotation_index, annotation in enumerate(
                passage["annotations"]
            ):
                for location_index, location in enumerate(
                    annotation["locations"]
                ):
                    gold_spans.append({
                        "text": annotation["text"],
                        "type": annotation["type"],
                        "mesh_id": annotation["mesh_id"],
                        "offset": location["local_offset"],
                        "length": location["length"],
                        "doc_id": doc["id"],
                        "passage_type": passage["type"],
                        "annotation_index": annotation_index,
                        "location_index": location_index,
                        "doc_offset": location["doc_offset"],
                        "observed_text": location["observed_text"],
                    })

    return gold_spans


def entity_to_key(entity: Dict) -> tuple:
    """
    Create the type-aware exact-match key for a gold or predicted entity.
    """
    return (
        entity["doc_id"],
        entity["passage_type"],
        entity["offset"],
        entity["length"],
        entity["type"],
    )
