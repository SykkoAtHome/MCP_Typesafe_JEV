"""Diagnostic for the box primitive's missing explicit no-object state."""

import json

from .bridge import call_mcp
from .storage import records


async def probe_absence(session, cases, repeats, output):
    path = output / "absent-box-diagnostics.jsonl"
    done = {(row["case_id"], row["repeat"]) for row in records(path) if row["success"]}
    with path.open("a", encoding="utf-8") as stream:
        for case in cases:
            if case["id"] != "ambiguous_absent_object":
                continue
            for repeat in range(repeats):
                if (case["id"], repeat) in done:
                    continue
                call = await call_mcp(session, "jev_box", {"state": case["state"],
                    "assets": case["assets"], "instructions": "Locate the pink star in the image."})
                record = {"case_id": case["id"], "repeat": repeat, **call,
                    "expected_object_present": False,
                    "returned_box_despite_absence": call["response"].get("box") is not None,
                    "interpretation": "Diagnostic only: box has no explicit absence result. Presence must be checked separately."}
                stream.write(json.dumps(record) + "\n")
