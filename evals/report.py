"""Aggregate measurements without hiding transport or environment failures."""

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from .storage import records, latest


def write_report(output):
    cases = {c["id"]: c for c in json.loads((output / "manifest.json").read_text(encoding="utf-8"))}
    all_agents = records(output / "agents.jsonl")
    all_canonical = records(output / "canonical.jsonl")
    agents = latest(all_agents, ("case_id", "arm", "repeat"))
    canonical = latest(all_canonical, ("case_id", "repeat"))
    metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    rows = ["# Behavioral evaluation results", "", f"Model: `{metadata['model']}`; effort: `{metadata['effort']}`; repeats: {metadata['repeats']}.",
            f"Cases: {len(cases)}. Source unchanged during run: {metadata.get('source_unchanged')}. Boundaries and limitations: see ../../README.md.",
            f"Raw agent attempts: {len(all_agents)}; canonical attempts: {len(all_canonical)}. Tables use the latest checkpoint for each case/arm/repeat; earlier attempts remain in JSONL.", "",
            "## Agent outcomes", "", "| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for arm in metadata["arms"]:
        subset = [r for r in agents if r["arm"] == arm]
        complete = [r for r in subset if r.get("turn_status") == "completed"]
        behavior = [r.get("behavior", {}) for r in complete]
        totals = [sum(b.get(key, 0) for b in behavior) for key in
                  ("evaluation_calls", "unnecessary_calls", "required_call_omitted")]
        median = round(statistics.median(r["elapsed_ms"] for r in complete)) if complete else "n/a"
        correct = sum(r.get("grade", {}).get("passed", False) for r in complete)
        rows.append(f"| {arm} | {len(complete)}/{len(subset)} | {correct}/{len(complete)} | {len(subset)-len(complete)} | {' | '.join(map(str,totals))} | {median} |")
    successful = [r for r in canonical if r["success"]]
    rows += ["", "## Fixed-question Jev track", "",
             f"Successful transport: {len(successful)}/{len(canonical)}. Correct task outcomes: {sum(r['grade']['passed'] for r in successful)}/{len(successful)}.",
             "", "| Case | Correct / successful | Transport failures | IoU per repeat |", "|---|---:|---:|---|"]
    for case_id in cases:
        subset = [r for r in canonical if r["case_id"] == case_id]
        if not subset:
            continue
        valid = [r for r in subset if r["success"]]
        overlaps = [round(r["grade"]["iou"], 3) for r in valid if "iou" in r["grade"]]
        rows.append(f"| {case_id} | {sum(r['grade']['passed'] for r in valid)}/{len(valid)} | {len(subset)-len(valid)} | {overlaps} |")
    rows += failure_rows(agents, canonical)
    rows += stability_rows(agents)
    rows += ["", "## Interpretation limits", "",
             "Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.",
             "No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.",
             "Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time."]
    (output / "report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def failure_rows(agents, canonical):
    rows = ["", "## Agent failures requiring attribution", ""]
    for r in agents:
        if r.get("environment_error") or r.get("turn_status") != "completed":
            rows.append(f"- {r['case_id']} / {r['arm']} / r{r['repeat']}: environment or turn failure; inspect trace.")
        elif not r["grade"]["passed"] or r["behavior"]["required_call_omitted"] or r["behavior"]["unnecessary_calls"]:
            rows.append(f"- {r['case_id']} / {r['arm']} / r{r['repeat']}: outcome={r['grade']}; behavior={r['behavior']}.")
    return rows


def stability_rows(agents):
    groups = defaultdict(list)
    for record in agents:
        if record.get("turn_status") == "completed":
            groups[(record["case_id"], record["arm"])].append(record)
    unstable = [key for key, records in groups.items() if len({json.dumps(
        {"answer": r["final"].get("answer"), "box": r["final"].get("box"),
         "abstain": r["final"].get("abstain"), "calls": r["behavior"]["evaluation_calls"]}, sort_keys=True)
        for r in records}) > 1]
    return ["", "## Repeat instability", "", f"Observed changes in answer/box/abstention/call count: {len(unstable)} case-arm pairs.",
            *[f"- {case_id} / {arm}" for case_id, arm in unstable]]
