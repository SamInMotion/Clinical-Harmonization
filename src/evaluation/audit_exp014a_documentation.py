"""Audit documentation for consistent EXP-014A evidence claims."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FILES = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "PROJECT_STATE.md",
    PROJECT_ROOT / "docs" / "PROJECT_CLOSEOUT.md",
    PROJECT_ROOT / "MANIFEST.md",
    PROJECT_ROOT
    / "docs"
    / "experiments"
    / "EXP-014A-development-threshold-selection-and-frozen-test-evaluation.md",
]

REQUIRED_POSITIVE = [
    "0.95",
    "0.7609",
    "0.7719",
    "0.7664",
    "development",
    "frozen",
]

FORBIDDEN_IN_FINAL_RESULT_CONTEXT = [
    "EXP-013 establishes evaluated hybrid operating points",
    "best F1 0.7664 at threshold 0.95",
]

def main():
    failures = []

    for path in FILES:
        if not path.exists():
            failures.append(f"MISSING FILE: {path}")
            continue

        text = path.read_text(encoding="utf-8")
        name = path.name

        if name == "EXP-014A-development-threshold-selection-and-frozen-test-evaluation.md":
            for phrase in REQUIRED_POSITIVE:
                if phrase not in text:
                    failures.append(f"{name}: missing required phrase: {phrase}")

        if "EXP-013" in text and "exploratory" not in text.lower():
            failures.append(
                f"{name}: mentions EXP-013 but does not label it exploratory"
            )

        for phrase in FORBIDDEN_IN_FINAL_RESULT_CONTEXT:
            if phrase in text:
                failures.append(
                    f"{name}: contains outdated EXP-013 final-result wording: {phrase}"
                )

    if failures:
        print("EXP-014A documentation audit: FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("EXP-014A documentation audit: PASS")


if __name__ == "__main__":
    main()