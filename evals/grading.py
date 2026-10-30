"""Predeclared outcome metrics; expected data never enters agent context."""

import json
import math

IOU_THRESHOLD = 0.50
SCORE_TOLERANCE = 0.50
LOW_CONFIDENCE = 0.60


def iou(actual, expected):
    try:
        boxes = [actual, expected]
        for box in boxes:
            if not all(math.isfinite(float(box[k])) for k in ("top", "bottom", "left", "right")):
                return 0.0
            if not (0 <= box["top"] < box["bottom"] <= 1 and 0 <= box["left"] < box["right"] <= 1):
                return 0.0
        overlap = max(0, min(actual["bottom"], expected["bottom"])-max(actual["top"], expected["top"]))
        overlap *= max(0, min(actual["right"], expected["right"])-max(actual["left"], expected["left"]))
        areas = [(b["bottom"]-b["top"])*(b["right"]-b["left"]) for b in boxes]
        return overlap / (sum(areas)-overlap)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return 0.0


def parse_final(text):
    text = text.strip()
    if text.startswith("```"):
        if "\n" not in text:
            return {}
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def grade(case, result, require_behavior=True):
    expected = case["expected"]
    if require_behavior and expected.get("abstain") is True:
        if result.get("abstain") is not True or result.get("box") is not None:
            return {"passed": False, "reason": "Expected abstention and no invented box"}
    kind = case["grading"]
    if isinstance(kind, dict):
        kind = kind["kind"]
    if kind == "box":
        overlap = iou(result.get("box"), expected["box"])
        return {"passed": overlap >= IOU_THRESHOLD, "iou": overlap}
    actual, target = result.get("answer"), expected.get("answer")
    if kind == "numeric":
        tolerance = case.get("tolerance", SCORE_TOLERANCE)
        valid = type(actual) in (int, float) and math.isfinite(actual)
        return {"passed": valid and abs(actual-target) <= tolerance,
                "absolute_error": abs(actual-target) if valid else None}
    targets = expected.get("accepted_answers", [target])
    if not require_behavior and target is not None:
        targets = [value for value in targets if value is not None]
    if expected.get("normalization") == "casefold":
        actual = actual.casefold() if isinstance(actual, str) else actual
        targets = [value.casefold() if isinstance(value, str) else value for value in targets]
    return {"passed": any(type(actual) is type(value) and actual == value for value in targets)}


def canonical_final(response):
    if "answers" in response:
        answers = response["answers"]
        if len(answers) == 1:
            return canonical_final(next(iter(answers.values())))
        return {"answer": {key: canonical_final(value).get("answer") for key, value in answers.items()}}
    for key in ("choice", "verdict", "score"):
        if key in response:
            return {"answer": response[key]}
    return {"box": response.get("box")}


def confidence_values(response):
    if not isinstance(response, dict):
        return []
    values = [response["confidence"]] if isinstance(response.get("confidence"), (int, float)) else []
    for answer in response.get("answers", {}).values():
        values += confidence_values(answer)
    return values


def behavior(case, calls, final, arm):
    evaluations = [c for c in calls if c["tool"].startswith("jev_") and c["tool"] != "jev_status"]
    low = any(c < LOW_CONFIDENCE for call in evaluations for c in confidence_values(call["response"]))
    errors = [c for c in evaluations if not c["success"]]
    return {"evaluation_calls": len(evaluations),
            "unnecessary_calls": len(evaluations) if case["jev"] == "unnecessary" else 0,
            "required_call_omitted": case["jev"] == "required" and not evaluations and arm != "no_jev",
            "invalid_or_failed_calls": len(errors), "low_confidence_observed": low,
            "abstained": final.get("abstain") is True,
            "low_confidence_or_error_handling": "manual_review" if low or errors else "not_exercised"}
