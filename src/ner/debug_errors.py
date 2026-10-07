"""
Debug dictionary baseline errors.

Usage:
    python src/ner/debug_errors.py
"""

from pathlib import Path
import json
from load_bc5cdr import load_bc5cdr
from dictionary_baseline import build_dictionary, extract_entities_from_text, normalize_text


def main():
    # Load dictionary
    dict_path = Path("data/terminology/bc5cdr_dictionary.json")
    with open(dict_path, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    
    # Check for "famotidine"
    print("=== Checking 'famotidine' in dictionary ===")
    for key in dictionary:
        if 'famotidine' in key.lower():
            print(f"  Found: '{key}' -> {dictionary[key]}")
    
    # Check for "Famotidine" (capitalized)
    print("\n=== Checking 'Famotidine' (capitalized) ===")
    for key in dictionary:
        if 'Famotidine' in key or key.startswith('Famotidine'):
            print(f"  Found: '{key}' -> {dictionary[key]}")
    
    # Load test document 8701013
    test_path = Path("data/raw/bc5cdr/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml")
    documents = load_bc5cdr(str(test_path))
    
    # Find document 8701013
    doc_8701013 = None
    for doc in documents:
        if doc['id'] == '8701013':
            doc_8701013 = doc
            break
    
    if doc_8701013:
        print(f"\n=== Document 8701013 ===")
        for passage in doc_8701013['passages']:
            print(f"\nPassage type: {passage['type']}")
            print(f"Text: {passage['text'][:200]}...")
            
            # Show gold annotations
            print(f"Gold annotations ({len(passage['annotations'])}):")
            for ann in passage['annotations'][:10]:
                print(f"  - '{ann['text']}' ({ann['type']}) @ offset {ann['offset']}, MESH: {ann['mesh_id']}")
            
            # Try extraction
            matches = extract_entities_from_text(passage['text'], dictionary, min_length=3)
            print(f"\nPredicted matches ({len(matches)}):")
            for match in matches[:10]:
                print(f"  - '{match['text']}' ({match['type']}) @ offset {match['offset']}, MESH: {match['mesh_id']}")
    
    # Test on simple sentence with famotidine
    print(f"\n=== Test on simple sentence ===")
    test_text = "Famotidine reduces ulcers."
    print(f"Text: {test_text}")
    
    matches = extract_entities_from_text(test_text, dictionary, min_length=3)
    print(f"Matches ({len(matches)}):")
    for match in matches:
        print(f"  - '{match['text']}' ({match['type']}) @ offset {match['offset']}, MESH: {match['mesh_id']}")
    
    # Check if "famotidine" is in dictionary
    normalized = normalize_text("Famotidine")
    print(f"\nNormalized 'Famotidine': '{normalized}'")
    print(f"'{normalized}' in dictionary? {normalized in dictionary}")
    
    # Check all keys
    print(f"\n=== All dictionary keys containing 'famotid' ===")
    for key in dictionary:
        if 'famotid' in key.lower():
            print(f"  '{key}' -> {dictionary[key]}")


if __name__ == "__main__":
    main()
