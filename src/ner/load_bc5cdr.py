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
                    'type': str,  # 'title' or 'abstract'
                    'text': str,
                    'offset': int,  # document-global offset where this passage starts
                    'annotations': [
                        {
                            'text': str,
                            'type': str,  # 'Chemical' or 'Disease'
                            'mesh_id': str,
                            'offset': int,  # document-global offset
                            'local_offset': int,  # passage-local offset (offset - passage_offset)
                            'length': int
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
                
                location = ann_elem.find('location')
                doc_offset = int(location.get('offset'))  # document-global
                length = int(location.get('length'))
                
                # Calculate passage-local offset
                local_offset = doc_offset - passage_offset
                
                # Validate: annotation text should match passage text at local offset
                observed_text = passage_text[local_offset:local_offset + length]
                entity_text = ann_elem.find('text').text
                
                if observed_text != entity_text:
                    # Try to handle minor mismatches (whitespace, etc.)
                    if observed_text.strip() != entity_text.strip():
                        print(f"WARNING: Annotation/text mismatch in doc {doc_id}:")
                        print(f"  Passage type: {passage_type}")
                        print(f"  Document offset: {doc_offset}, length: {length}")
                        print(f"  Annotation text: '{entity_text}'")
                        print(f"  Observed text: '{observed_text}'")
                        # Still use the annotation text, but this is a data quality issue
                
                entity_text = ann_elem.find('text').text
                
                annotations.append({
                    'text': entity_text,
                    'type': entity_type,
                    'mesh_id': mesh_id,
                    'offset': doc_offset,  # document-global (for provenance)
                    'local_offset': local_offset,  # passage-local (for matching)
                    'length': length
                })
            
            passages.append({
                'type': passage_type,
                'text': passage_text,
                'offset': passage_offset,  # document-global offset where passage starts
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
    # Path to BC5CDR training set
    data_path = Path("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TrainingSet.BioC.xml")
    
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
        for ann in passage['annotations'][:5]:  # Show first 5
            print(f"  - {ann['text']} ({ann['type']}) @ doc_offset {ann['offset']}, local_offset {ann['local_offset']}, length {ann['length']}, MESH: {ann['mesh_id']}")
            
            # Verify offset
            observed = passage['text'][ann['local_offset']:ann['local_offset'] + ann['length']]
            match = observed == ann['text']
            print(f"    Verification: '{observed}' == '{ann['text']}'? {match}")


if __name__ == "__main__":
    main()
