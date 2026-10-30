"""Append-only checkpoints and immutable measurement identity."""

import json


def records(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest(rows, fields):
    return list({tuple(row[key] for key in fields): row for row in rows}.values())


def assert_same_measurement(previous, current):
    for key in ("model", "effort", "repeats", "arms", "manifest_sha256", "source_hashes", "runner_hashes", "phase"):
        if previous[key] != current[key]:
            raise ValueError(f"Cannot resume with changed {key}; use a new output directory")
