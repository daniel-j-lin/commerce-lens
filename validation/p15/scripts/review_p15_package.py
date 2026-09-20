#!/usr/bin/env python3
"""Review P15 package separation and required observer material."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PARTICIPANT_FILES = (
    "consent.md", "task-s1.md", "task-s2.md", "task-s3.md", "task-s4.md", "task-s5.md",
)
REQUIRED_OBSERVER_FILES = (
    "oracle.md", "intervention-script.md", "comprehension-rubric.md",
    "value-interview.md", "session-template.md", "pilot-checklist.md",
)
LEAKS = (
    "12000.00", "10800.00", "-1200.00", "250.00", "240.00",
    "USER_DECLARED", "Insufficient evidence to conclude why Revenue declined.",
    "private oracle", "observer-only",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).parents[1])
    args = parser.parse_args()
    participant_dir = args.package / "participant"
    observer_dir = args.package / "observer"
    data_dir = args.package / "data"

    missing_participant = [name for name in PARTICIPANT_FILES if not (participant_dir / name).is_file()]
    missing_observer = [name for name in REQUIRED_OBSERVER_FILES if not (observer_dir / name).is_file()]
    if missing_participant or missing_observer:
        raise AssertionError({"missing_participant": missing_participant, "missing_observer": missing_observer})

    leaked: dict[str, list[str]] = {}
    for path in sorted(participant_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        matches = [item for item in LEAKS if item.lower() in text.lower()]
        if matches:
            leaked[path.name] = matches
    if leaked:
        raise AssertionError(f"participant material oracle leakage: {leaked}")

    oracle = (observer_dir / "oracle.md").read_text(encoding="utf-8")
    required_oracle_terms = (
        "12000.00", "10800.00", "-1200.00", "48", "45", "250.00", "240.00",
        "USER_DECLARED", "Insufficient evidence to conclude why Revenue declined.",
    )
    missing_terms = [term for term in required_oracle_terms if term not in oracle]
    if missing_terms:
        raise AssertionError(f"observer oracle missing required terms: {missing_terms}")

    manifest = json.loads((data_dir / "DATASET_MANIFEST.json").read_text(encoding="utf-8"))
    for key in ("A", "B"):
        dataset = manifest["datasets"][key]
        if not dataset["sha256"] or dataset["byte_size"] <= 0 or dataset["validation"]["rows"] <= 0:
            raise AssertionError(f"dataset manifest incomplete for {key}")

    result = {
        "participant_materials": "passed",
        "oracle_leakage_check": "passed",
        "observer_materials": "passed",
        "dataset_manifest_check": "passed",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
