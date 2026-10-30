"""Fresh-context agent trials with only the declared synthetic inputs."""

import asyncio
import json
import time
import re
from pathlib import Path

from .bridge import call_mcp, compute, read_resource, resource_tool, COMPUTE_TOOL
from .grading import behavior, grade, parse_final

BASE = ("You solve the user's task using the supplied tools when useful. "
        "You have no repository work to do. Return ONLY a JSON object with fields "
        "answer (the requested value or null), box (normalized top,bottom,left,right or null), "
        "abstain (boolean), reason (brief explanation including any material uncertainty). "
        "Do not fabricate observations or tool results.")

OUTPUT_SCHEMA = {"type": "object", "additionalProperties": False,
    "required": ["answer", "box", "abstain", "reason"], "properties": {
        "answer": {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "boolean"},
                    {"type": "array", "items": {"type": "number"}}, {"type": "null"}]},
        "box": {"anyOf": [{"type": "null"}, {"type": "object", "additionalProperties": False,
                "properties": {k: {"type": "number"} for k in ("top", "bottom", "left", "right")},
                "required": ["top", "bottom", "left", "right"]}]},
        "abstain": {"type": "boolean"}, "reason": {"type": "string"}}}


def task_input(case):
    prompt = case["task"] + "\nInput data: " + json.dumps(case["state"])
    images = []
    for ref, asset in case.get("assets", {}).items():
        prompt += f"\nImage reference {ref}: {asset['path']}"
        images.append({"type": "localImage", "path": asset["path"]})
    return [{"type": "text", "text": prompt, "text_elements": []}] + images


class AgentTrial:
    def __init__(self, rpc, session, tools, workspace, model, effort, server_instructions=""):
        self.rpc, self.session, self.tools = rpc, session, tools
        self.workspace, self.model, self.effort = workspace, model, effort
        self.server_instructions = server_instructions

    async def run(self, case, arm, repeat):
        start = time.perf_counter()
        trace = {"case_id": case["id"], "arm": arm, "repeat": repeat,
                 "model_requested": self.model, "reasoning_effort": self.effort,
                 "tool_calls": [], "resource_treatment": None, "events": []}
        tools = [COMPUTE_TOOL]
        developer = ""
        if arm != "no_jev":
            tools += self.tools + [resource_tool()]
            developer = self.server_instructions
        if arm in ("guide", "skill"):
            uri = f"jev://{arm}"
            content = await read_resource(self.session, uri)
            developer += f"\nMCP resource {uri}, read before task:\n{content}"
            trace["resource_treatment"] = {"uri": uri, "content": content, "reader": "harness"}
        response = await self.rpc.request("thread/start", {
            "model": self.model, "cwd": str(self.workspace), "ephemeral": True,
            "baseInstructions": BASE, "developerInstructions": developer,
            "approvalPolicy": "never", "sandbox": "read-only", "dynamicTools": tools,
            "config": {"model_reasoning_effort": self.effort}, "selectedCapabilityRoots": []})
        return await self._turn(case, arm, trace, response, start)

    async def _turn(self, case, arm, trace, response, start):
        thread_id = response["thread"]["id"]
        trace["thread_id"] = thread_id
        trace["model_resolved"] = response.get("model")
        queue = self.rpc.queues[thread_id] = asyncio.Queue()
        self.rpc.handlers[thread_id] = lambda params: self.handle(params, case, trace)
        await self.rpc.request("turn/start", {"threadId": thread_id, "input": task_input(case),
                                             "outputSchema": OUTPUT_SCHEMA})
        final_text = ""
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), 180)
                method, params = event["method"], event["params"]
                if method in ("item/completed", "turn/completed", "thread/tokenUsage/updated", "error"):
                    trace["events"].append(event)
                if method == "item/completed" and params["item"]["type"] == "agentMessage":
                    final_text = params["item"]["text"]
                if method == "thread/tokenUsage/updated":
                    trace["usage"] = params["tokenUsage"]
                if method == "turn/completed":
                    trace["turn_status"] = params["turn"]["status"]
                    break
        except asyncio.TimeoutError:
            trace["turn_status"] = "timeout"
        trace.update(final_text=final_text, elapsed_ms=round((time.perf_counter()-start)*1000, 2))
        final = trace["final"] = parse_final(final_text)
        trace["grade"] = grade(case, final)
        trace["behavior"] = behavior(case, trace["tool_calls"], final, arm)
        self.rpc.handlers.pop(thread_id, None)
        self.rpc.queues.pop(thread_id, None)
        await self.rpc.request("thread/unsubscribe", {"threadId": thread_id})
        return trace

    async def handle(self, params, case, trace):
        try:
            return await self._dispatch(params, case, trace)
        except Exception as exc:
            from typesafe_jev_mcp.errors import redact_secrets
            response = {"error": "tool_dispatch_error", "message": redact_secrets(str(exc))}
            trace["tool_calls"].append({"tool": params.get("tool"),
                "arguments": params.get("arguments"), "response": response, "success": False})
            return {"success": False, "contentItems": [{"type": "inputText", "text": json.dumps(response)}]}

    async def _dispatch(self, params, case, trace):
        name, arguments = params["tool"], params["arguments"]
        if len(trace["tool_calls"]) >= 8:
            call = {"tool": name, "arguments": arguments, "response": {"error": "call_budget"}, "success": False}
        elif name == "compute":
            call = self._compute(arguments)
        elif name == "read_resource":
            content = await read_resource(self.session, arguments["uri"])
            call = {"tool": name, "arguments": arguments, "response": {"text": content}, "success": True}
        else:
            call = await self._evaluation(name, arguments, case)
        trace["tool_calls"].append(call)
        return {"success": call["success"], "contentItems": [
            {"type": "inputText", "text": json.dumps(call["response"])}]}

    def _compute(self, arguments):
        try:
            result = {"value": compute(**arguments)}
        except (ValueError, TypeError, KeyError, SyntaxError, ZeroDivisionError, re.error) as exc:
            result = {"error": type(exc).__name__, "message": str(exc)}
        return {"tool": "compute", "arguments": arguments, "response": result, "success": "error" not in result}

    async def _evaluation(self, name, arguments, case):
        allowed = {str(Path(a["path"]).resolve()) for a in case.get("assets", {}).values()}
        for asset in (arguments.get("assets") or {}).values():
            if "path" in asset and str(Path(asset["path"]).resolve()) not in allowed:
                return {"tool": name, "arguments": arguments, "success": False,
                        "response": {"error": "asset_outside_synthetic_allowlist"}}
        if case.get("replay"):
            from .robustness import replay_response
            response = replay_response(case["replay"], name, arguments)
            return {"tool": name, "arguments": arguments, "success": "error" not in response,
                    "response": response, "source": "controlled_replay"}
        return await call_mcp(self.session, name, arguments)
