"""Verify one real inference before scheduling the evaluation matrix."""

import asyncio
import json
import sys
from pathlib import Path

from .agent import AgentTrial
from .bridge import mcp_session
from .rpc import CodexRPC


async def main():
    root = Path(__file__).resolve().parents[1]
    runtime = root / "evals/.runtime"
    workspace = runtime / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    case = {"id": "smoke", "task": "Compute 17 * (23 + 9). Return an integer.",
            "state": {}, "assets": {}, "expected": {"answer": 544},
            "grading": "exact", "jev": "unnecessary"}
    async with mcp_session(root) as (session, _):
        async with CodexRPC(runtime) as rpc:
            trial = AgentTrial(rpc, session, [], workspace, sys.argv[1] if len(sys.argv) > 1 else "gpt-5.6-luna", "low")
            result = await trial.run(case, "no_jev", 0)
            print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
