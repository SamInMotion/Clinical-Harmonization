"""Build a static HTML dashboard from EXP-010 harmonization outputs."""

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = (
    PROJECT_ROOT
    / "output"
    / "harmonization"
    / "exp010"
)

OUTPUT_HTML = (
    PROJECT_ROOT
    / "output"
    / "dashboard"
    / "clinical_harmonization_dashboard.html"
)


def load_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_document_summary(records):
    summary = defaultdict(
        lambda: {
            "extracted": 0,
            "mapped": 0,
            "unmapped": 0,
        }
    )

    for record in records:
        document_id = record["document_id"]
        summary[document_id]["extracted"] += 1

        if record["mapping_status"] == "mapped":
            summary[document_id]["mapped"] += 1
        else:
            summary[document_id]["unmapped"] += 1

    return [
        {
            "document_id": document_id,
            **counts,
        }
        for document_id, counts in sorted(summary.items())
    ]


def render_html(records, document_summary, generated_at):
    total = len(records)
    mapped = sum(
        1 for record in records if record["mapping_status"] == "mapped"
    )
    unmapped = total - mapped

    destination_counts = Counter(
        record["destination_table"]
        for record in records
        if record["destination_table"]
    )

    entity_counts = Counter(record["entity_type"] for record in records)
    method_counts = Counter(record["extraction_method"] for record in records)

    document_rows = "".join(
        f"""
        <tr>
          <td>{row['document_id']}</td>
          <td>{row['extracted']}</td>
          <td>{row['mapped']}</td>
          <td>{row['unmapped']}</td>
        </tr>
        """
        for row in document_summary
    )

    record_rows = "".join(
        f"""
        <tr class="{record['mapping_status']}">
          <td>{record['document_id']}</td>
          <td>{record['passage_type']}</td>
          <td>{record['mention_text']}</td>
          <td>{record['entity_type']}</td>
          <td>{record['start_char']}-{record['end_char']}</td>
          <td>{record['mapping_status']}</td>
          <td>{record['concept_name'] or '—'}</td>
          <td>{record['domain'] or '—'}</td>
          <td>{record['destination_table'] or '—'}</td>
          <td>{record['mapping_method']}</td>
        </tr>
        """
        for record in records
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Clinical Harmonization Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1, h2 {{ color: #173f5f; }}
    .metrics {{ display: flex; gap: 16px; margin: 24px 0; }}
    .metric {{
      background: #f4f7fa;
      border: 1px solid #d7e0ea;
      border-radius: 8px;
      padding: 16px 24px;
    }}
    .metric strong {{ display: block; font-size: 28px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 32px; }}
    th, td {{ border: 1px solid #d7e0ea; padding: 8px; text-align: left; }}
    th {{ background: #173f5f; color: white; }}
    tr.mapped td {{ background: #f0f9f1; }}
    tr.unmapped td {{ background: #fff7ed; }}
    .filters {{ margin: 16px 0; }}
    input, select {{ padding: 6px; margin-right: 12px; }}
    .note {{
      background: #fff8e6;
      border: 1px solid #e5d9a8;
      border-radius: 8px;
      padding: 16px;
      margin: 24px 0;
      max-width: 900px;
    }}
    .note p {{ margin: 8px 0; }}
  </style>
</head>
<body>
  <h1>Clinical Harmonization Dashboard</h1>
  <p>Generated {generated_at}</p>

  <div class="metrics">
    <div class="metric"><strong>{total}</strong>Extracted occurrences</div>
    <div class="metric"><strong>{mapped}</strong>Mapped occurrences</div>
    <div class="metric"><strong>{unmapped}</strong>Unmapped occurrences</div>
    <div class="metric"><strong>{mapped / total:.1%}</strong>Mapping rate</div>
  </div>

  <div class="note">
    <p>
      <strong>Mapping rate</strong> is the proportion of extracted occurrences
      assigned a concept by the deliberately incomplete 29-concept vocabulary.
      It is not vocabulary coverage, extraction accuracy, mapping precision,
      end-to-end correctness, OMOP CDM validity, or FHIR conformance.
    </p>
    <p>
      This dashboard reports the EXP-010 dictionary-based harmonization pipeline.
      It does not report the EXP-014C union-span reconciled hybrid, which remains
      an evaluated research configuration and has not been promoted to production.
    </p>
  </div>

  <h2>Routing outcomes</h2>
  <p>
    These counts describe routing behavior for mapped occurrences. They do not
    establish OMOP CDM validity, clinical correctness, or readiness for
    clinical research use.
  </p>
  <table>
    <tr><th>Destination</th><th>Records</th></tr>
    {''.join(f'<tr><td>{table}</td><td>{count}</td></tr>' for table, count in destination_counts.items())}
  </table>

  <h2>Extraction methods</h2>
  <table>
    <tr><th>Method</th><th>Occurrences</th></tr>
    {''.join(f'<tr><td>{method}</td><td>{count}</td></tr>' for method, count in method_counts.items())}
  </table>

  <h2>Entity types</h2>
  <table>
    <tr><th>Entity type</th><th>Occurrences</th></tr>
    {''.join(f'<tr><td>{entity}</td><td>{count}</td></tr>' for entity, count in entity_counts.items())}
  </table>

  <h2>Per-document summary</h2>
  <table>
    <tr><th>Document</th><th>Extracted</th><th>Mapped</th><th>Unmapped</th></tr>
    {document_rows}
  </table>

  <h2>Browsable occurrence records</h2>
  <div class="filters">
    <input id="search" placeholder="Search mention, document, concept">
    <select id="status">
      <option value="">All statuses</option>
      <option value="mapped">Mapped</option>
      <option value="unmapped">Unmapped</option>
    </select>
  </div>

  <table id="records">
    <thead>
      <tr>
        <th>Document</th><th>Passage</th><th>Mention</th><th>Type</th>
        <th>Document span</th><th>Mapping status</th><th>Concept</th><th>Domain</th>
        <th>Destination</th><th>Mapping method</th>
      </tr>
    </thead>
    <tbody>{record_rows}</tbody>
  </table>

  <script>
    const search = document.getElementById('search');
    const status = document.getElementById('status');
    const rows = Array.from(document.querySelectorAll('#records tbody tr'));

    function filter() {{
      const query = search.value.toLowerCase();
      const selectedStatus = status.value;

      rows.forEach(row => {{
        const text = row.innerText.toLowerCase();
        const rowStatus = row.classList.contains('mapped') ? 'mapped' : 'unmapped';
        const matchesQuery = text.includes(query);
        const matchesStatus = !selectedStatus || rowStatus === selectedStatus;
        row.style.display = matchesQuery && matchesStatus ? '' : 'none';
      }});
    }}

    search.addEventListener('input', filter);
    status.addEventListener('change', filter);
  </script>
</body>
</html>"""


def main():
    records_path = INPUT_DIR / "harmonized_records.csv"

    if not records_path.exists():
        raise FileNotFoundError(f"Harmonized records not found: {records_path}")

    records = load_csv(records_path)
    document_summary = build_document_summary(records)
    generated_at = datetime.now(timezone.utc).isoformat()

    html = render_html(records, document_summary, generated_at)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"Records: {len(records)}")
    print(f"Dashboard written to: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()