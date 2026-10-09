"""
Dictionary-based NER baseline for BC5CDR.

Builds a lookup dictionary from training data and matches entities by exact
(normalized) string matching.

Usage:
    python src/ner/dictionary_baseline.py

Output:
    - Dictionary statistics
    - Sample matches
"""

from collections import defaultdict
from pathlib import Path
import json
import sys
from typing import List, Dict

# Fix import path
sys.path.insert(0, str(Path(__file__).parent))
from load_bc5cdr import load_bc5cdr, get_corpus_stats


# Common English words to filter out (not biomedical entities)
COMMON_WORDS = {
    'all', 'and', 'any', 'are', 'but', 'can', 'for', 'from', 'has', 'have',
    'his', 'how', 'its', 'may', 'not', 'one', 'our', 'see', 'she', 'str',
    'the', 'was', 'were', 'what', 'when', 'where', 'which', 'who', 'with',
    'ist', 'use', 'used', 'using', 'two', 'three', 'four', 'five', 'new',
    'also', 'that', 'this', 'they', 'their', 'these', 'those', 'such',
    'more', 'most', 'other', 'some', 'than', 'then', 'there', 'been',
}


def normalize_text(text: str) -> str:
    """
    Normalize entity mention for dictionary lookup.
    
    Operations:
    - Lowercase
    - Strip leading/trailing whitespace
    - Normalize internal whitespace (multiple spaces → single space)
    
    Args:
        text: Raw entity mention
    
    Returns:
        Normalized text
    """
    text = text.lower().strip()
    # Normalize internal whitespace
    text = ' '.join(text.split())
    return text


def build_dictionary(documents, min_length: int = 4):
    """
    Build entity dictionary from documents.
    
    Args:
        documents: List of documents from load_bc5cdr()
        min_length: Minimum entity length (filter out very short entities)
    
    Returns:
        Dictionary: normalized_text → list of {original, type, mesh_id}
    """
    dictionary = defaultdict(list)
    
    for doc in documents:
        for passage in doc['passages']:
            for ann in passage['annotations']:
                # Filter very short entities (prone to false positives)
                if len(ann['text'].strip()) < min_length:
                    continue
                
                normalized = normalize_text(ann['text'])
                
                # Also filter if normalized form is too short
                if len(normalized) < min_length:
                    continue
                
                # Filter common English words
                if normalized in COMMON_WORDS:
                    continue
                
                entry = {
                    'original': ann['text'].strip(),  # Store stripped version
                    'type': ann['type'],
                    'mesh_id': ann['mesh_id']
                }
                
                # Avoid duplicates
                if not any(
                    e['original'] == ann['text'].strip() and e['type'] == ann['type']
                    for e in dictionary[normalized]
                ):
                    dictionary[normalized].append(entry)
    
    return dictionary


def save_dictionary(dictionary, output_path: str):
    """Save dictionary to JSON file."""
    # Convert defaultdict to regular dict for JSON serialization
    dict_to_save = {k: v for k, v in dictionary.items()}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dict_to_save, f, indent=2, ensure_ascii=False)
    
    print(f"Dictionary saved to: {output_path}")


def load_dictionary(input_path: str):
    """Load dictionary from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    
    # Convert back to defaultdict
    return defaultdict(list, dictionary)


def extract_entities_from_text(text: str, dictionary, min_length: int = 4):
    """
    Extract entities from text using dictionary matching.
    
    Strategy:
    - Slide window over text at all possible lengths
    - Normalize each span
    - Lookup in dictionary
    - Return all matches with positions (adjusted for whitespace)
    
    Args:
        text: Input text
        dictionary: Entity dictionary
        min_length: Minimum match length
    
    Returns:
        List of {text, type, mesh_id, offset, length}
    """
    matches = []
    
    # Try all possible spans
    for start in range(len(text)):
        for length in range(min_length, min(50, len(text) - start + 1)):  # Min length 4, max 50
            span = text[start:start + length]
            normalized = normalize_text(span)
            
            if normalized in dictionary:
                for entry in dictionary[normalized]:
                    # Adjust span to remove leading/trailing whitespace
                    span_stripped = span.strip()
                    if span_stripped:  # Only if non-empty after stripping
                        # Calculate new offset (accounting for leading whitespace)
                        leading_ws = len(span) - len(span.lstrip())
                        new_offset = start + leading_ws
                        new_length = len(span_stripped)
                        
                        matches.append({
                            'text': span_stripped,
                            'type': entry['type'],
                            'mesh_id': entry['mesh_id'],
                            'offset': new_offset,  # passage-local offset
                            'length': new_length
                        })
    
    # Remove overlapping matches (keep longest)
    matches = remove_overlapping(matches)
    
    return matches


def remove_overlapping(matches):
    """
    Remove overlapping matches, keeping the longest.
    
    Args:
        matches: List of matches with offset and length
    
    Returns:
        Filtered list with no overlaps
    """
    if not matches:
        return []
    
    # Sort by length (descending)
    matches = sorted(matches, key=lambda m: m['length'], reverse=True)
    
    kept = []
    for match in matches:
        # Check if this match overlaps with any kept match
        overlaps = False
        for kept_match in kept:
            # Overlap if: start1 < end2 and start2 < end1
            if (match['offset'] < kept_match['offset'] + kept_match['length'] and
                match['offset'] + match['length'] > kept_match['offset']):
                overlaps = True
                break
        
        if not overlaps:
            kept.append(match)
    
    return kept


def main():
    # Load training data
    data_path = Path("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TrainingSet.BioC.xml")
    
    if not data_path.exists():
        print(f"ERROR: File not found: {data_path}")
        return
    
    print(f"Loading BC5CDR training set...")
    documents = load_bc5cdr(str(data_path))
    
    print(f"Building dictionary (min_length=4, filtering common words)...")
    dictionary = build_dictionary(documents, min_length=4)
    
    print(f"\n=== Dictionary Statistics ===")
    print(f"Unique normalized forms: {len(dictionary)}")
    
    # Count by type
    chemicals = sum(1 for entries in dictionary.values() for e in entries if e['type'] == 'Chemical')
    diseases = sum(1 for entries in dictionary.values() for e in entries if e['type'] == 'Disease')
    print(f"Chemical entries: {chemicals}")
    print(f"Disease entries: {diseases}")
    
    # Show some examples
    print(f"\n=== Sample Dictionary Entries ===")
    for i, (normalized, entries) in enumerate(list(dictionary.items())[:10]):
        print(f"\n'{normalized}':")
        for entry in entries:
            print(f"  - {entry['original']} ({entry['type']}) - MESH: {entry['mesh_id']}")
    
    # Check if problematic words are filtered
    print(f"\n=== Checking filtered words ===")
    for word in ['ist', 'str', 'all', 'and', 'the', 'was']:
        print(f"  '{word}' in dictionary? {word in dictionary}")
    
    # Save dictionary
    output_path = Path("data/terminology/bc5cdr_dictionary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_dictionary(dictionary, str(output_path))
    
    # Test on sample text
    print(f"\n=== Test on Sample Text ===")
    sample_text = "Naloxone reverses the antihypertensive effect of clonidine."
    print(f"Text: {sample_text}")
    print(f"Expected: Naloxone (Chemical), clonidine (Chemical)")
    
    matches = extract_entities_from_text(sample_text, dictionary, min_length=4)
    print(f"Matches ({len(matches)}):")
    for match in matches:
        print(f"  - '{match['text']}' ({match['type']}) @ offset {match['offset']}, length {match['length']}, MESH: {match['mesh_id']}")


if __name__ == "__main__":
    main()
