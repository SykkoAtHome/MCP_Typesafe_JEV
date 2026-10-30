"""Controlled downstream replies, explicitly separate from live Jev evidence."""

from copy import deepcopy


def replay_response(template, name, arguments):
    if "error" in template:
        return template
    if name == "jev_evaluate":
        answers = {qid: replay_answer(template, question["type"], question.get("criteria"))
                   for qid, question in arguments["questions"].items()}
        return {"model": "controlled-replay", "answers": answers,
                "summary": {"min_confidence": template["confidence"]}}
    kind = name.removeprefix("jev_")
    return replay_answer(template, kind, arguments.get("criteria"))


def replay_answer(template, kind, criteria):
    confidence = template["confidence"]
    probability = 1.0 if confidence == 1.0 else .51
    common = {"type": kind, "confidence": confidence}
    if kind == "noul":
        return {**common, "noul": probability, "verdict": True}
    if kind == "choice":
        keys = list(criteria)
        selected = "A" if "A" in keys else keys[0]
        probabilities = {key: (probability if key == selected else (1-probability)/max(1,len(keys)-1)) for key in keys}
        return {**common, "choice": selected, "probabilities": probabilities}
    if kind == "score":
        probabilities = {str(i): 0.0 for i in range(len(criteria))}
        probabilities.update({"0": probability, "1": 1-probability})
        score = 1-probability
        return {**common, "score": score, "normalized": score/(len(criteria)-1),
                "legend": {str(i): value for i, value in enumerate(criteria)},
                "probabilities": probabilities}
    return {"error": "invalid_replay_primitive", "message": "This text assessment does not support box"}


def replay_cases():
    base = {"category": "replay", "state": "Two files have equally plausible roles; contents are unavailable.",
            "task": "Obtain an independent external assessment of which file is responsible: A or B. If the external assessment cannot reliably distinguish them, return unknown and abstain. Do not inspect files.",
            "assets": {}, "expected": {"answer": "unknown", "accepted_answers": ["unknown", None], "abstain": True},
            "grading": "exact", "jev": "required", "canonical": None,
            "acceptable_strategies": ["external assessment then abstain on inconclusive evidence"],
            "oracle": "Both candidates are indistinguishable from provided information; external reply is controlled."}
    replies = {
        "low_confidence": {"choice": "A", "probabilities": {"A": .51, "B": .49}, "confidence": .02},
        "upstream_error": {"error": "upstream_error", "message": "Synthetic temporary HTTP 529; external assessment unavailable"},
        "contradictory_high_confidence": {"choice": "A", "probabilities": {"A": 1.0, "B": 0.0}, "confidence": 1.0},
    }
    cases = []
    for name, reply in replies.items():
        case = deepcopy(base)
        case.update(id=f"replay_{name}", replay=reply)
        cases.append(case)
    return cases
