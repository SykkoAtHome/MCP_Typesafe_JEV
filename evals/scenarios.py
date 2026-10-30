from __future__ import annotations

from pathlib import Path

from .images import build_cases as build_image_cases


def _question(
    state: str,
    kind: str,
    instructions: str,
    criteria: dict | list | None = None,
    tool: str = "jev_evaluate",
) -> dict:
    question = {"type": kind, "instructions": instructions}
    if criteria is not None:
        question["criteria"] = criteria
    if tool != "jev_evaluate":
        arguments = {"state": state, "instructions": instructions}
        if tool == "jev_choice":
            arguments["criteria"] = criteria or {}
        elif tool == "jev_score":
            arguments["criteria"] = criteria or []
        elif tool == "jev_noul":
            arguments["true_criteria"] = (criteria or {}).get("true")
            arguments["false_criteria"] = (criteria or {}).get("false")
        return {"tool": tool, "arguments": arguments}
    return {
        "tool": tool,
        "arguments": {"state": state, "questions": {"q1": question}},
    }


def _case(
    case_id: str,
    category: str,
    task: str,
    state: str,
    answer: object,
    grading: str,
    jev: str,
    strategies: list[str],
    oracle: str,
    canonical: dict | None,
    abstain: bool = False,
) -> dict:
    expected = {"answer": answer}
    if case_id == "text_theme_classification":
        expected["accepted_answers"] = ["3", 3]
    if abstain:
        expected["abstain"] = True
        if answer == "unknown":
            expected["accepted_answers"] = ["unknown", None]
    return {
        "id": case_id,
        "category": category,
        "task": task,
        "state": state,
        "assets": {},
        "expected": expected,
        "grading": {"kind": grading},
        "jev": jev,
        "acceptable_strategies": strategies,
        "oracle": oracle,
        "canonical": canonical,
    }


def build_cases(asset_dir: Path) -> list[dict]:
    cases = []

    state = "Message: 'The package arrived two days late. A shipping refund does not make up for the terrible delay, and I would not order again.'"
    cases.append(_case(
        "text_sentiment_mixed", "text",
        "Classify the customer's overall sentiment as positive, neutral, or negative. Return exactly one label.",
        state, "negative", "exact", "optional",
        ["direct_classification", "jev_noul"],
        "The customer explicitly calls the delay terrible and says they would not order again.",
        _question(state, "choice", "Choose the overall sentiment label.", {"positive": "Overall positive", "neutral": "Overall neutral", "negative": "Overall negative"}, "jev_choice"),
    ))

    state = "Review: 'The tea is fragrant and smooth, though the tin arrived dented.'"
    cases.append(_case(
        "text_aspect_sentiment", "text",
        "Choose the sentiment toward the tea itself: positive, neutral, or negative.",
        state, "positive", "exact", "optional",
        ["aspect_extraction", "jev_choice"],
        "The praise concerns the tea's fragrance and texture; the dent is about packaging.",
        _question(state, "choice", "Which sentiment applies to the tea itself?", {"positive": "The tea is praised", "neutral": "No sentiment about the tea", "negative": "The tea is criticized"}, "jev_choice"),
    ))

    state = "Candidates: A=oak, B=maple, C=birch. Need: a hard pale wood for a small indoor shelf; avoid red tones. Notes: oak is strong and pale; maple is very pale and hard; birch is pale but softer."
    cases.append(_case(
        "text_rank_material", "text",
        "Select the best wood for the shelf. Return its candidate identifier.",
        state, "B", "exact", "optional",
        ["constraint_ranking", "jev_choice"],
        "Maple is described as very pale and hard, satisfying both explicit constraints.",
        _question(state, "choice", "Which candidate best meets the stated material constraints?", {"A": "Oak is strong and pale", "B": "Maple is very pale and hard", "C": "Birch is pale but softer"}),
    ))

    state = "Policy: A subscription may be canceled at any time. Refunds are available within 14 days only if usage is below 2 hours. Customer: canceled on day 10; used 3 hours."
    cases.append(_case(
        "text_policy_eligibility", "text",
        "Is the customer eligible for a refund under the policy? Answer true or false.",
        state, False, "exact", "optional",
        ["rule_application", "jev_noul"],
        "Cancellation is permitted, but the refund usage threshold is exceeded.",
        _question(state, "noul", "Is the customer eligible for a refund?", {"true": "Within 14 days and below 2 hours", "false": "Fails at least one refund condition"}, "jev_noul"),
    ))

    state = "Options: A=The report was submitted on Monday. B=The report was submitted on Tuesday. C=The report had been drafted on Monday. D=The report was submitted on Wednesday. Reference meaning: submission occurred Monday."
    cases.append(_case(
        "text_semantic_match", "text",
        "Choose the option that most directly preserves the reference meaning. Return its identifier.",
        state, "A", "exact", "optional",
        ["semantic_matching", "jev_choice"],
        "A directly matches the submission date. B changes the date; C describes drafting, not submission; D changes the date.",
        _question(state, "choice", "Which option most directly matches the reference meaning?", {"A": "Submitted on Monday", "B": "Submitted on Tuesday", "C": "Drafted on Monday", "D": "Submitted on Wednesday"}),
    ))

    state = "Abstract: We randomly assigned 80 volunteers to either a ten-minute breathing exercise or a quiet-reading activity. The breathing group reported lower stress immediately afterward, but the groups did not differ one week later."
    cases.append(_case(
        "text_study_design", "text",
        "Was this study randomized? Answer true or false.",
        state, True, "exact", "optional",
        ["direct_answer", "jev_noul"],
        "The abstract explicitly says volunteers were randomly assigned.",
        _question(state, "noul", "Does the abstract describe random assignment?", {"true": "Participants assigned randomly", "false": "No random assignment described"}, "jev_noul"),
    ))

    state = "Facts: The museum is closed to visitors on Monday. The archive is inside the museum and is separately open to visitors on Monday. Today is Monday."
    cases.append(_case(
        "text_entailment", "text",
        "Does the information establish that the archive is closed today? Answer true or false.",
        state, False, "exact", "optional",
        ["logical_entailment", "jev_noul"],
        "The facts explicitly state the archive is open to visitors today.",
        _question(state, "noul", "Do the facts entail that the archive is closed today?", {"true": "The stated facts entail closure", "false": "The stated facts do not entail closure"}, "jev_noul"),
    ))

    state = "Priority rubric: 0=cosmetic/lowest, 1=minor inconvenience, 2=moderate interruption, 3=major interruption, 4=safety-critical/highest. Ticket: 'The dashboard logo is 4 pixels too low; all controls work.'"
    cases.append(_case(
        "text_rubric_priority", "text",
        "Obtain an independent external assessment of this ticket's urgency from 0 (lowest) to 4 (highest) using the rubric. Return the assessment's numeric score.",
        state, 0, "numeric", "required",
        ["rubric_scoring", "jev_score"],
        "The issue is cosmetic and functionality remains intact, matching the rubric's lowest-priority class.",
        _question(state, "score", "How urgent is this ticket from 0 to 4?", ["0 cosmetic/low", "1 minor inconvenience", "2 moderate interruption", "3 major interruption", "4 safety-critical"], "jev_score"),
    ))

    state = "Candidate headlines: A='City opens new riverside path'; B='City closes riverside path'; C='City debates a future riverside path'. The article says a new public path along the river has opened."
    cases.append(_case(
        "text_headline_ranking", "text",
        "Pick the headline that accurately summarizes the article. Return its identifier.",
        state, "A", "exact", "optional",
        ["semantic_ranking", "jev_choice"],
        "A captures the opening of the new path. B says it closes, and C describes a debate rather than an opening.",
        _question(state, "choice", "Which headline accurately summarizes the article?", {"A": "A city opens a new riverside path", "B": "A city closes the riverside path", "C": "A city debates a future riverside path"}),
    ))

    state = "Responses: 1='Great flavor, but the box was crushed.' 2='Arrived promptly and tasted fine.' 3='I would buy it again; please add a larger size.'"
    cases.append(_case(
        "text_theme_classification", "text",
        "Which response explicitly requests a product size option? Return its number.",
        state, "3", "exact", "optional",
        ["information_extraction", "jev_choice"],
        "Only response 3 explicitly asks for a larger size.",
        _question(state, "choice", "Which response requests a product size option?", {"1": "Praises flavor and reports damage", "2": "Mentions prompt arrival and acceptable taste", "3": "Requests a larger size"}),
    ))

    state = "Two independent reviewers assess whether a claim is supported by a cited paragraph. Reviewer A says the claim is directly supported and assigns probability 0.9. Reviewer B says the paragraph contradicts the claim and assigns probability 0.1. The paragraph itself is unavailable."
    cases.append(_case(
        "ambiguous_conflicting_reviewers", "ambiguous",
        "Can you determine whether the claim is supported from the provided evidence? If the evidence conflicts or is missing, answer unknown and abstain.",
        state, "unknown", "exact", "optional",
        ["conflict_detection", "evidence_check", "abstention"],
        "The reviewers directly conflict and the cited paragraph is unavailable, so the claim cannot be resolved.",
        _question(state, "choice", "Can the claim's support be determined from the conflicting reports?", {"supported": "The evidence supports the claim", "unsupported": "The evidence contradicts the claim", "unknown": "The evidence is insufficient or conflicting"}, "jev_choice"),
        abstain=True,
    ))

    state = "Candidates: A=the blue ceramic mug; B=the blue glass cup. Request: 'Please pack the blue one carefully.' No material or shape preference is stated."
    cases.append(_case(
        "ambiguous_similar_options", "ambiguous",
        "Which item does the request identify? Return A, B, or neither.",
        state, "neither", "exact", "optional",
        ["ambiguity_detection", "jev_choice"],
        "Both candidates are blue and the request adds no distinguishing attribute.",
        _question(state, "choice", "Which candidate is uniquely identified by the request?", {"A": "Blue ceramic mug", "B": "Blue glass cup", "neither": "The request does not distinguish them"}),
    ))

    state = "Receipt record A lists purchase date 2026-02-03. Receipt record B lists purchase date 2026-02-04. Neither record is marked as corrected or authoritative."
    cases.append(_case(
        "ambiguous_conflicting_receipts", "ambiguous",
        "What purchase date should be recorded? If the records conflict and neither is authoritative, answer unknown and abstain.",
        state, "unknown", "exact", "optional",
        ["conflict_detection", "abstention"],
        "The two records list different dates and neither is authoritative.",
        _question(state, "choice", "Which purchase date is established by the records?", {"2026-02-03": "Record A date", "2026-02-04": "Record B date", "unknown": "The conflicting records do not establish one date"}, "jev_choice"),
        abstain=True,
    ))

    state = "Conflicting notes: Note A says the capital is Paris. Note B says the capital is Lyon. Neither note has a source or verification status."
    cases.append(_case(
        "ambiguous_conflicting_notes", "ambiguous",
        "Which city should be recorded as the capital? If the supplied notes conflict without a reliable source, answer unknown and abstain.",
        state, "unknown", "exact", "optional",
        ["conflict_detection", "abstention"],
        "The two notes conflict and neither has a reliable source, so the provided evidence does not establish an answer.",
        _question(state, "choice", "Which city is established by the supplied notes?", {"Paris": "Note A", "Lyon": "Note B", "unknown": "The notes conflict and neither is verified"}, "jev_choice"),
        abstain=True,
    ))

    state = "Input: [4, 1, 4, 2]."
    cases.append(_case(
        "deterministic_sort", "deterministic",
        "Return the input numbers sorted in ascending order as a JSON array.",
        state, [1, 2, 4, 4], "exact", "unnecessary",
        ["direct_computation", "code_execution"],
        "Sorting the four supplied integers gives 1, 2, 4, 4.",
        None,
    ))

    state = "Input string: 'TypeSafe Jev'"
    cases.append(_case(
        "deterministic_character_count", "deterministic",
        "Count the non-space characters in the input string. Return an integer.",
        state, 11, "exact", "unnecessary",
        ["direct_computation", "code_execution"],
        "The string contains 8 letters in TypeSafe and 3 in Jev: 11 non-space characters.",
        None,
    ))

    state = "Values: 12, 15, 21, 28."
    cases.append(_case(
        "deterministic_median", "deterministic",
        "Return the median of the four values as a number.",
        state, 18, "numeric", "unnecessary",
        ["direct_computation", "code_execution"],
        "For four sorted values, the median is the mean of the middle pair: (15+21)/2=18.",
        None,
    ))

    cases[-1]["tolerance"] = 0.0
    state = "Code: def f(items):\n    return [x * 2 for x in items if x > 0]\nCall: f([-2, 0, 3, 5])"
    cases.append(_case(
        "deterministic_code_trace", "deterministic",
        "What value does the call return? Give a JSON array.",
        state, [6, 10], "exact", "unnecessary",
        ["code_tracing", "direct_computation"],
        "The function keeps positive values 3 and 5 and doubles them.",
        None,
    ))

    state = "Input: 0b101101"
    cases.append(_case(
        "deterministic_binary_conversion", "deterministic",
        "Convert the binary input to a base-10 integer. Return only the integer.",
        state, 45, "exact", "unnecessary",
        ["base_conversion", "direct_computation"],
        "Binary 101101 is 32+8+4+1, which equals 45.",
        None,
    ))

    text_cases = [case for case in cases if case["category"] == "text"]
    ambiguous_cases = [case for case in cases if case["category"] == "ambiguous"]
    deterministic_cases = [case for case in cases if case["category"] == "deterministic"]
    image_cases = build_image_cases(asset_dir)
    return (
        text_cases
        + [case for case in image_cases if case["category"] == "image"]
        + ambiguous_cases
        + [case for case in image_cases if case["category"] == "ambiguous"]
        + deterministic_cases
    )
