"""
Focused regression tests for BioC location preservation.

These tests verify Gate C-1: every annotation location must be preserved,
converted to a passage-local offset, and exposed with its observed text.
"""

import textwrap
from pathlib import Path

from src.ner.load_bc5cdr import load_bc5cdr


def write_bioc(tmp_path: Path, xml: str) -> str:
    path = tmp_path / "sample.BioC.xml"
    path.write_text(textwrap.dedent(xml), encoding="utf-8")
    return str(path)


def test_single_location_annotation(tmp_path):
    xml = """
    <collection>
      <document>
        <id>DOC1</id>
        <passage>
          <infon>Title</infon>
          <offset>0</offset>
          <text>Aspirin reduces pain.</text>
          <annotation>
            <infon>Chemical</infon>
            <infon key="MESH">D001249</infon>
            <location offset="0" length="7"/>
            <text>Aspirin</text>
          </annotation>
        </passage>
      </document>
    </collection>
    """
    documents = load_bc5cdr(write_bioc(tmp_path, xml))
    annotation = documents[0]["passages"][0]["annotations"][0]

    assert annotation["text"] == "Aspirin"
    assert annotation["type"] == "Chemical"
    assert annotation["mesh_id"] == "D001249"
    assert annotation["offset"] == 0
    assert annotation["local_offset"] == 0
    assert annotation["length"] == 7
    assert len(annotation["locations"]) == 1
    assert annotation["locations"][0]["observed_text"] == "Aspirin"


def test_passage_local_offset_conversion(tmp_path):
    xml = """
    <collection>
      <document>
        <id>DOC2</id>
        <passage>
          <infon>Abstract</infon>
          <offset>60</offset>
          <text>The patient had hypertensive disease.</text>
          <annotation>
            <infon>Disease</infon>
            <infon key="MESH">D001249</infon>
            <location offset="76" length="12"/>
            <text>hypertensive</text>
          </annotation>
        </passage>
      </document>
    </collection>
    """
    documents = load_bc5cdr(write_bioc(tmp_path, xml))
    annotation = documents[0]["passages"][0]["annotations"][0]

    assert annotation["local_offset"] == 16
    assert annotation["locations"][0]["local_offset"] == 16
    assert annotation["locations"][0]["observed_text"] == "hypertensive"


def test_multi_location_annotation_preserves_all_spans(tmp_path):
    xml = """
    <collection>
      <document>
        <id>DOC3</id>
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
    documents = load_bc5cdr(write_bioc(tmp_path, xml))
    annotation = documents[0]["passages"][0]["annotations"][0]

    assert len(annotation["locations"]) == 2

    first, second = annotation["locations"]
    assert first["local_offset"] == 0
    assert first["observed_text"] == "Cerebellar"

    assert second["local_offset"] == 11
    assert second["observed_text"] == "dysfunction"

    # Backward-compatible first-location fields remain available.
    assert annotation["local_offset"] == 0
    assert annotation["length"] == 10


def test_multiple_annotations_are_preserved(tmp_path):
    xml = """
    <collection>
      <document>
        <id>DOC4</id>
        <passage>
          <infon>Abstract</infon>
          <offset>0</offset>
          <text>Aspirin treats pain and inflammation.</text>
          <annotation>
            <infon>Chemical</infon>
            <infon key="MESH">D001249</infon>
            <location offset="0" length="7"/>
            <text>Aspirin</text>
          </annotation>
          <annotation>
            <infon>Disease</infon>
            <infon key="MESH">D001249</infon>
            <location offset="15" length="4"/>
            <text>pain</text>
          </annotation>
        </passage>
      </document>
    </collection>
    """
    documents = load_bc5cdr(write_bioc(tmp_path, xml))
    annotations = documents[0]["passages"][0]["annotations"]

    assert len(annotations) == 2
    assert annotations[0]["locations"][0]["observed_text"] == "Aspirin"
    assert annotations[1]["locations"][0]["observed_text"] == "pain"