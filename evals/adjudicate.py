"""Publish explicit format corrections alongside immutable baseline grades."""

import argparse
import json
from copy import deepcopy
from pathlib import Path

from .grading import grade
from .storage import records, latest


def corrected_case(original):
    case = deepcopy(original)
    expected = case["expected"]
    if case["id"] == "image_leftmost_color":
        expected["normalization"] = "casefold"
        return case, "color_label_case"
    if case["id"] == "text_theme_classification":
        expected["accepted_answers"] = ["3", 3]
        return case, "numeric_response_identifier"
    if expected.get("answer") == "unknown" and expected.get("abstain") is True:
        expected["accepted_answers"] = ["unknown", None]
        return case, "null_abstention"
    return case, None


def adjudicate(output):
    cases = {c["id"]: c for c in json.loads((output / "manifest.json").read_text(encoding="utf-8"))}
    agents = latest(records(output / "agents.jsonl"), ("case_id", "arm", "repeat"))
    with (output / "adjudicated.jsonl").open("w", encoding="utf-8") as stream:
        for row in agents:
            case, rule = corrected_case(cases[row["case_id"]])
            result = grade(case, row.get("final", {})) if row.get("turn_status") == "completed" else None
            record = {key: row[key] for key in ("case_id", "arm", "repeat")}
            record.update(strict_grade=row.get("grade"), task_grade=result, format_rule=rule,
                          changed=result != row.get("grade"))
            stream.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    adjudicate(parser.parse_args().directory)
