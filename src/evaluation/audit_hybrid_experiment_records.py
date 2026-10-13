"""Audit EXP-012 and EXP-013 experiment records for correct status labels."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPERIMENTS_DIR = PROJECT_ROOT / "docs" / "experiments"

REQUIRED = {
    "EXP-012-hybrid-extraction-evaluation.md": [
        "EXP-012",
        "0.6328",
        "0.8157",
        "0.7127",
        "not promoted",
    ],
    "EXP-013-hybrid-confidence-sweep.md": [
        "EXP-013",
        "exploratory",
        "test set",
        "0.95",
        "0.7664",
        "not independently selected",
    ],
}

def main():
    failures = []

    for filename, phrases in REQUIRED.items():
        path = EXPERIMENTS_DIR / filename

        if not path.exists():
            failures.append(f"MISSING FILE: {path}")
            continue

        text = path.read_text(encoding="utf-8").lower()

        for phrase in phrases:
            if phrase.lower() not in text:
                failures.append(f"{filename}: missing phrase: {phrase}")

    if failures:
        print("Hybrid experiment-record audit: FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("Hybrid experiment-record audit: PASS")


if __name__ == "__main__":
    main()