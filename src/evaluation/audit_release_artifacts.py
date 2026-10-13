"""Audit tracked repository artifacts for public-release and provenance risks."""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RISKY_PATTERNS = [
    "data/raw/",
    "data/terminology/omop_exercise_vocabulary.json",
    "output/",
    ".venv/",
    "__pycache__/",
    ".env",
]

def tracked_files():
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def main():
    files = tracked_files()
    failures = []
    warnings = []

    for path in files:
        for pattern in RISKY_PATTERNS:
            if path.startswith(pattern) or path == pattern:
                if pattern == "data/terminology/omop_exercise_vocabulary.json":
                    failures.append(
                        f"ASSESSMENT VOCABULARY TRACKED: {path}"
                    )
                elif pattern == "data/raw/":
                    failures.append(f"RAW DATASET TRACKED: {path}")
                elif pattern == "output/":
                    failures.append(f"GENERATED OUTPUT TRACKED: {path}")
                else:
                    warnings.append(f"REVIEW TRACKED PATH: {path}")

    readme = PROJECT_ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8").lower()
        if "redistribution" not in text:
            warnings.append("README.md does not mention redistribution review")

    if failures:
        print("Release-artifact audit: FAIL")
        for failure in failures:
            print(f"- {failure}")
    else:
        print("Release-artifact audit: PASS")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()