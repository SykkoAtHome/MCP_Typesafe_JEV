"""Repeatable pilot/full behavioral evaluation runner."""

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .agent import AgentTrial
from .bridge import call_mcp, mcp_session, read_resource
from .grading import canonical_final, grade, IOU_THRESHOLD, SCORE_TOLERANCE, LOW_CONFIDENCE
from .rpc import CodexRPC, codex_binary
from .scenarios import build_cases
from typesafe_jev_mcp.errors import redact_secrets
from .storage import records, assert_same_measurement
from .absence import probe_absence

ROOT = Path(__file__).resolve().parents[1]
ARMS = ["descriptions", "guide", "skill", "no_jev"]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def source_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "src").rglob("*.py")}


def prepare_cases(output, args):
    if args.resume:
        cases = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        if args.cases and set(args.cases.split(",")) != {case["id"] for case in cases}:
            raise ValueError("Cannot resume a different case selection")
        return cases
    if args.phase == "robustness":
        from .robustness import replay_cases
        return select_cases(replay_cases(), args)
    return select_cases(build_cases(output / "assets"), args)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8").stdout


def snapshot(args, cases):
    return {"started_utc": datetime.now(timezone.utc).isoformat(),
            "model": args.model, "effort": args.effort, "repeats": args.repeats,
            "arms": args.arms, "seed": args.seed, "phase": args.phase,
            "thresholds": {"iou": IOU_THRESHOLD, "score_tolerance": SCORE_TOLERANCE,
                           "low_confidence": LOW_CONFIDENCE},
            "source_hashes": source_hashes(), "git_head": git("rev-parse", "HEAD").strip(),
            "runner_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (ROOT / "evals").glob("*.py")},
            "git_branch": git("branch", "--show-current").strip(),
            "git_status": git("status", "--short"), "git_diff_stat": git("diff", "--stat"),
            "mcp_version": importlib.metadata.version("typesafe-jev-mcp"),
            "codex_binary": codex_binary(),
            "codex_version": subprocess.run([codex_binary(), "--version"], capture_output=True, text=True).stdout.strip(),
            "manifest_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
            "isolation": "Ephemeral fresh threads, empty capability roots, synthetic workspace; clean temporary CODEX_HOME; shell/app/skills/web disabled.",
            "resource_treatment": "Harness reads actual MCP resource and adds its content before the task. All Jev arms may read resources on demand.",
            "agent_usage": "RPC thread/tokenUsage totals; usage can be absent. No monetary estimate."}


async def canonical_runs(session, cases, args, output):
    path = output / "canonical.jsonl"
    completed = {(r["case_id"], r["repeat"]) for r in records(path) if r["success"]}
    with path.open("a", encoding="utf-8") as stream:
        for repeat in range(args.repeats):
            for case in cases:
                if case.get("canonical") is None:
                    continue
                if (case["id"], repeat) in completed:
                    continue
                spec = case["canonical"]
                call = await call_mcp(session, spec["tool"], spec["arguments"])
                record = {"case_id": case["id"], "repeat": repeat, **call}
                record["grade"] = grade(case, canonical_final(call["response"]), require_behavior=False) if call["success"] else None
                stream.write(json.dumps(record) + "\n")
                stream.flush()
    print(f"Canonical track saved: {path}", flush=True)


async def agent_runs(session, rpc, tools, cases, args, output, runtime, instructions):
    workspace = runtime / "workspace"
    workspace.mkdir(exist_ok=True)
    trial = AgentTrial(rpc, session, tools, workspace, args.model, args.effort, instructions)
    jobs = [(c, a, r) for r in range(args.repeats) for c in cases for a in args.arms]
    completed = {(r["case_id"], r["arm"], r["repeat"]) for r in records(output / "agents.jsonl")
                 if r.get("turn_status") == "completed"}
    jobs = [job for job in jobs if (job[0]["id"], job[1], job[2]) not in completed]
    random.Random(args.seed).shuffle(jobs)
    semaphore = asyncio.Semaphore(args.concurrency)
    with (output / "agents.jsonl").open("a", encoding="utf-8") as stream:
        async def execute(index, case, arm, repeat):
            async with semaphore:
                try:
                    record = await trial.run(case, arm, repeat)
                except Exception as exc:
                    record = {"case_id": case["id"], "arm": arm, "repeat": repeat,
                              "environment_error": redact_secrets(f"{type(exc).__name__}: {exc}")}
                stream.write(json.dumps(record) + "\n")
                stream.flush()
                print(f"{index+1}/{len(jobs)} {case['id']} {arm} r{repeat}: "
                      f"{record.get('turn_status', 'environment_error')} {record.get('grade', {})}", flush=True)
        await asyncio.gather(*(execute(i, *job) for i, job in enumerate(jobs)))


async def run(args):
    output = (ROOT / args.output).resolve()
    output.mkdir(parents=True, exist_ok=args.resume)
    runtime = ROOT / "evals/.runtime"
    runtime.mkdir(exist_ok=True)
    cases = prepare_cases(output, args)
    metadata = snapshot(args, cases)
    if args.resume:
        previous = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
        assert_same_measurement(previous, metadata)
        previous.setdefault("resumed_utc", []).append(metadata["started_utc"])
        metadata = previous
    else:
        dump(output / "manifest.json", cases)
    dump(output / "metadata.json", metadata)
    async with mcp_session(ROOT) as (session, initialization):
        listed = await session.list_tools()
        dump(output / "mcp-tools.json", [t.model_dump(mode="json") for t in listed.tools])
        dump(output / "mcp-resources.json", {uri: await read_resource(session, uri)
             for uri in ("jev://guide", "jev://skill")})
        dump(output / "mcp-initialize.json", initialization.model_dump(mode="json"))
        await canonical_runs(session, cases, args, output)
        await probe_absence(session, cases, args.repeats, output)
        if not args.canonical_only:
            tools = [{"type": "function", "name": t.name, "description": t.description or "",
                      "inputSchema": t.input_schema} for t in listed.tools]
            async with CodexRPC(runtime) as rpc:
                await agent_runs(session, rpc, tools, cases, args, output, runtime, initialization.instructions or "")
                dump(output / "codex-diagnostics.json", rpc.stderr)
    metadata["finished_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["source_unchanged"] = metadata["source_hashes"] == source_hashes()
    dump(output / "metadata.json", metadata)
    from .report import write_report
    write_report(output)


def select_cases(cases, args):
    if args.cases:
        selected = set(args.cases.split(","))
        unknown = selected - {case["id"] for case in cases}
        if unknown:
            raise ValueError(f"Unknown case IDs: {sorted(unknown)}")
        return [case for case in cases if case["id"] in selected]
    if args.phase == "pilot":
        indices = [0, 7, 10, 16, 20, 25]
        return [cases[i] for i in indices]
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["pilot", "full", "robustness"], default="pilot")
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--effort", default="low")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20261029)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=ARMS)
    parser.add_argument("--cases")
    parser.add_argument("--canonical-only", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Append missing or failed trials; keep completed measurements")
    args = parser.parse_args()
    if args.repeats < 1 or args.concurrency < 1:
        parser.error("repeats and concurrency must be positive")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
