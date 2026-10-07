"""
Golden tests for NER component.

These tests catch regressions when "improvements" break existing functionality.
Run after every meaningful change to NER code.
"""

# Sample BC5CDR abstracts with known entities
GOLDEN_ABSTRACTS = {
    "sample_1": {
        "text": "The effects of quinine and 4-aminopyridine on conditioned place preference and changes in motor activity induced by morphine in rats.",
        "expected_chemicals": ["quinine", "4-aminopyridine", "morphine"],
        "expected_diseases": [],  # This abstract may not have explicit disease mentions
        "note": "Teaching case from interview exercise — handles case variation (Quinine/quinine), single-letter symbols (K for potassium), and near-duplicates (hyperactivity/hypoactivity)",
    },
    "sample_2": {
        "text": "Acetaminophen-induced liver injury in patients with chronic hepatitis C.",
        "expected_chemicals": ["acetaminophen"],
        "expected_diseases": ["liver injury", "hepatitis C"],
        "note": "Simple case — exact matches expected",
    },
    "sample_3": {
        "text": "Aspirin therapy reduces the risk of myocardial infarction in patients with coronary artery disease.",
        "expected_chemicals": ["aspirin"],
        "expected_diseases": ["myocardial infarction", "coronary artery disease"],
        "note": "Common entities — both methods should handle",
    },
}


def test_dictionary_ner_basic():
    """Test dictionary NER on simple abstract."""
    # TODO: Implement after dictionary baseline is built
    pass


def test_transformer_ner_basic():
    """Test transformer NER on simple abstract."""
    # TODO: Implement after transformer NER is built
    pass


def test_ner_span_boundaries():
    """Test that NER correctly identifies span boundaries."""
    # TODO: Implement with examples like "4-aminopyridine" (multi-token entity)
    pass
