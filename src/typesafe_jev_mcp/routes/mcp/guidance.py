"""Shared guidance for MCP tool descriptions and on-demand resources."""

import json


IMAGE_INPUT_GUIDANCE = (
    "To inspect pixels, supply images in `assets`; a filename, path, or reference in `state` "
    "alone does not upload an image. Use `state={\"photo\":\"img_1\"}` with "
    "`assets={\"img_1\":{\"path\":\"/absolute/photo.png\"}}`, then ask about `photo`. "
    "The asset key `img_1` must occur in a string value of state, instructions, or criteria; "
    "object keys do not count. Attach every image needed for a comparison. "
    "A textual image summary is evidence about that summary, not unseen pixels."
)

QUESTION_GUIDANCE = (
    "Every jev_evaluate question requires type and nonempty instructions; single-question "
    "tools infer type from their name and also require instructions. Define neutral criteria: "
    "describe alternatives or rubric levels, without asserting which answer is correct; "
    "put observations in state. If the evidence may be insufficient, include an unknown "
    "choice or ask a separate evidence-sufficiency question. A binary false result is not "
    "automatically proof of the opposite claim."
)

DECISION_GUIDANCE = (
    "Before acting, check that the necessary evidence was supplied. With low confidence, "
    "obtain missing input, verify independently, or abstain; choose a threshold only with "
    "an explicit fallback. High confidence and valid JSON do not establish correctness. "
    "Keep the final identifier consistent with the decision you support; explain an "
    "evidence-based override instead of silently changing the selected option. "
    "On validation errors or HTTP 400, check required arguments and exact asset references "
    "before retrying; changing path separators does not repair a reference mismatch. "
    "If an upstream failure persists, report that evaluation is unavailable rather than inventing a result."
)

BOX_GUIDANCE = (
    "A returned box does not establish object presence; box has no explicit absent-object "
    "output. Check presence with noul or choice including absent/unknown. You may batch "
    "presence and box, but discard the box when presence is absent or unresolved. "
    "Normalized coordinates and low-confidence regions alone are not successful localization."
)

VISUAL_BATCH_EXAMPLE = {
    "state": {"photo": "img_1"},
    "assets": {"img_1": {"path": "/absolute/photo.png"}},
    "questions": {
        "present": {
            "type": "noul",
            "instructions": "Is a red square visible in `photo`?",
            "criteria": {"true": "A red square is visible", "false": "No red square is visible"},
        },
        "location": {"type": "box", "instructions": "The red square in `photo`"},
    },
}

UNKNOWN_CHOICE_EXAMPLE = {
    "state": {"request": "The blue one, please.", "items": {"A": "blue mug", "B": "blue bowl"}},
    "questions": {
        "item": {
            "type": "choice",
            "instructions": "Which item does the request uniquely identify?",
            "criteria": {
                "A": "The request uniquely identifies item A",
                "B": "The request uniquely identifies item B",
                "unknown": "The request does not distinguish the items",
            },
        },
    },
}

GUIDANCE_REFERENCE = "\n\n".join((
    "## Reliable requests and decisions",
    QUESTION_GUIDANCE,
    IMAGE_INPUT_GUIDANCE,
    DECISION_GUIDANCE,
    BOX_GUIDANCE,
    "### Image presence and localization\n\nReplace the placeholder with an absolute path on the MCP host. "
    "Use location only if present is true and adequately supported.\n\n```json\n"
    + json.dumps(VISUAL_BATCH_EXAMPLE, indent=2) + "\n```",
    "### Missing or ambiguous evidence\n\nRepresent insufficient evidence explicitly rather than forcing A or B.\n\n```json\n"
    + json.dumps(UNKNOWN_CHOICE_EXAMPLE, indent=2) + "\n```",
))
