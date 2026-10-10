"""
Load BC5CDR corpus from BioC XML format.

Usage:
    python src/ner/load_bc5cdr.py

Output:
    Prints corpus statistics and sample entities.
"""

import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def load_bc5cdr(xml_path: str):
    """
    Load BC5CDR corpus from BioC XML file.

    Args:
        xml_path: Path to BioC XML file (e.g., CDR_TrainingSet.BioC.xml)

    Returns:
        List of documents, each document is a dict:
        {
            'id': str,
            'passages': [
                {
                    'type': str,
                    'text': str,
                    'offset': int,
                    'annotations': [
                        {
                            'text': str,
                            'type': str,
                            'mesh_id': str,
                            'offset': int,
                            'local_offset': int,
                            'length': int,
                            'locations': [
                                {
                                    'doc_offset': int,
                                    'local_offset': int,
                                    'length': int,
                                    'observed_text': str or None
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    documents = []

    for doc_elem in root.findall('document'):
        doc_id = doc_elem.find('id').text

        passages = []
        for passage_elem in doc_elem.findall('passage'):
            passage_type = passage_elem.find('infon').text
            passage_text = passage_elem.find('text').text
            passage_offset = int(passage_elem.find('offset').text)

            annotations = []
            for ann_elem in passage_elem.findall('annotation'):
                entity_type = ann_elem.find('infon').text
                mesh_id = ann_elem.find("infon[@key='MESH']").text
                entity_text = ann_elem.find('text').text

                locations = []
                for location_elem in ann_elem.findall('location'):
                    doc_offset = int(location_elem.get('offset'))
                    length = int(location_elem.get('length'))
                    local_offset = doc_offset - passage_offset

                    if local_offset < 0 or local_offset + length > len(passage_text):
                        observed_text = None
                        print(
                            f"WARNING: Out-of-bounds BioC location in doc {doc_id}: "
                            f"doc_offset={doc_offset}, length={length}, "
                            f"passage_offset={passage_offset}"
                        )
                    else:
                        observed_text = passage_text[local_offset:local_offset + length]

                    locations.append({
                        'doc_offset': doc_offset,
                        'local_offset': local_offset,
                        'length': length,
                        'observed_text': observed_text,
                    })

                first_location = locations[0] if locations else {
                    'doc_offset': 0,
                    'local_offset': 0,
                    'length': 0,
                    'observed_text': None,
                }

                annotations.append({
                    'text': entity_text,
                    'type': entity_type,
                    'mesh_id': mesh_id,
                    # Backward-compatible fields for the first location.
                    'offset': first_location['doc_offset'],
                    'local_offset': first_location['local_offset'],
                    'length': first_location['length'],
                    # Complete location representation introduced by Gate C-1.
                    'locations': locations,
                })

            passages.append({
                'type': passage_type,
                'text': passage_text,
                'offset': passage_offset,
                'annotations': annotations
            })

        documents.append({
            'id': doc_id,
            'passages': passages
        })

    return documents


def get_corpus_stats(documents):
    """Calculate corpus statistics."""
    num_docs = len(documents)
    num_passages = sum(len(doc['passages']) for doc in documents)

    chemicals = []
    diseases = []

    for doc in documents:
        for passage in doc['passages']:
            for ann in passage['annotations']:
                if ann['type'] == 'Chemical':
                    chemicals.append(ann['text'])
                elif ann['type'] == 'Disease':
                    diseases.append(ann['text'])

    return {
        'num_documents': num_docs,
        'num_passages': num_passages,
        'num_chemicals': len(chemicals),
        'num_diseases': len(diseases),
        'unique_chemicals': len(set(chemicals)),
        'unique_diseases': len(set(diseases)),
        'chemical_counter': Counter(chemicals),
        'disease_counter': Counter(diseases)
    }


def main():
    data_path = Path(
        "data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/"
        "CDR_TrainingSet.BioC.xml"
    )

    if not data_path.exists():
        print(f"ERROR: File not found: {data_path}")
        return

    print(f"Loading BC5CDR from: {data_path}")
    documents = load_bc5cdr(str(data_path))

    print(f"\n=== Corpus Statistics ===")
    stats = get_corpus_stats(documents)
    print(f"Documents: {stats['num_documents']}")
    print(f"Passages: {stats['num_passages']}")
    print(f"Chemical mentions: {stats['num_chemicals']}")
    print(f"Disease mentions: {stats['num_diseases']}")
    print(f"Unique chemicals: {stats['unique_chemicals']}")
    print(f"Unique diseases: {stats['unique_diseases']}")

    print(f"\n=== Sample Document ===")
    sample = documents[0]
    print(f"Document ID: {sample['id']}")
    for passage in sample['passages']:
        print(f"\nPassage type: {passage['type']}")
        print(f"Passage offset: {passage['offset']}")
        print(f"Text: {passage['text'][:200]}...")
        print(f"Annotations ({len(passage['annotations'])}):")
        for ann in passage['annotations'][:5]:
            print(
                f"  - {ann['text']} ({ann['type']}) "
                f"@ doc_offset {ann['offset']}, "
                f"local_offset {ann['local_offset']}, "
                f"length {ann['length']}, MESH: {ann['mesh_id']}"
            )
            print(f"    Locations: {len(ann['locations'])}")
            for location in ann['locations']:
                print(
                    f"      local_offset={location['local_offset']}, "
                    f"length={location['length']}, "
                    f"observed={location['observed_text']!r}"
                )


if __name__ == "__main__":
    main()
