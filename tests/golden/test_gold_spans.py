"""
Regression tests for Gate C-2 location-level, type-aware gold spans.
"""

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src" / "ner"))

from load_bc5cdr import load_bc5cdr
from gold_spans import extract_gold_location_spans, entity_to_key


def load_sample(tmp_path):
    xml = """
    <collection>
      <document>
        <id>DOC1</id>
        <passage>
          <infon>Abstract</infon>
          <offset>0</offset>
          <text>Cerebellar dysfunction was observed.</text>
          <annotation>
            <infon>Disease</infon>
            <infon key="MESH">D001249</infon>
            <location offset="0" length="10"/>
            <location offset="11" length="11"/>
            <text>Cerebellar dysfunction</text>
          </annotation>
        </passage>
      </document>
    </collection>
    """
    path = tmp_path / "sample.BioC.xml"
    path.write_text(textwrap.dedent(xml).strip(), encoding="utf-8")
    return load_bc5cdr(str(path))


def test_each_location_becomes_one_gold_span(tmp_path):
    documents = load_sample(tmp_path)
    spans = extract_gold_location_spans(documents)

    assert len(spans) == 2

    assert spans[0]["offset"] == 0
    assert spans[0]["length"] == 10
    assert spans[0]["observed_text"] == "Cerebellar"

    assert spans[1]["offset"] == 11
    assert spans[1]["length"] == 11
    assert spans[1]["observed_text"] == "dysfunction"

    assert spans[0]["annotation_index"] == 0
    assert spans[1]["annotation_index"] == 0
    assert spans[0]["location_index"] == 0
    assert spans[1]["location_index"] == 1


def test_entity_type_is_part_of_match_key(tmp_path):
    documents = load_sample(tmp_path)
    spans = extract_gold_location_spans(documents)

    chemical_span = dict(spans[0])
    chemical_span["type"] = "Chemical"

    assert entity_to_key(spans[0]) != entity_to_key(chemical_span)
