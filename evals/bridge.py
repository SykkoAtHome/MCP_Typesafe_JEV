"""Actual MCP stdio transport and a bounded deterministic alternative."""

import ast
import asyncio
import json
import operator
import os
import re
import sys
import time
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typesafe_jev_mcp.db.credentials import CredentialStore
from typesafe_jev_mcp.errors import redact_secrets


@asynccontextmanager
async def mcp_session(root):
    key = CredentialStore().resolve().key.get_secret_value()
    params = StdioServerParameters(command=sys.executable,
        args=["-m", "typesafe_jev_mcp", "serve"], cwd=str(root),
        env=dict(os.environ, TYPESAFE_API_KEY=key))
    with open(os.devnull, "w") as errors:
        async with stdio_client(params, errlog=errors) as (read, write):
            async with ClientSession(read, write) as session:
                initialization = await session.initialize()
                yield session, initialization


def payload(result):
    if result.structured_content:
        return result.structured_content
    for item in result.content:
        if item.type == "text":
            try:
                return json.loads(item.text)
            except json.JSONDecodeError:
                return {"error": "mcp_error", "message": item.text}
    return {"error": "empty_mcp_response"}


async def call_mcp(session, name, arguments):
    start = time.perf_counter()
    try:
        response = await session.call_tool(name, arguments)
        result = payload(response)
        status = not response.is_error and "error" not in result
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": redact_secrets(str(exc))}
        status = False
    return {"tool": name, "arguments": arguments, "response": result,
            "success": status, "elapsed_ms": round((time.perf_counter()-start)*1000, 2)}


COMPUTE_TOOL = {"type": "function", "name": "compute",
    "description": "Exact deterministic computation: arithmetic, sort, date_difference (days), regex findall, lookup, character_count (non-space), median, binary_to_int, or double_positive (list comprehension x*2 for x>0). No semantic evaluation.",
    "inputSchema": {"type": "object", "properties": {
        "operation": {"type": "string", "enum": ["arithmetic", "sort", "date_difference", "regex", "lookup", "character_count", "median", "binary_to_int", "double_positive"]},
        "data": {"description": "Expression string, list, [ISO start,end], {pattern,text}, or {mapping,key}."}},
        "required": ["operation", "data"]}}


def arithmetic(expression):
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                  ast.Div: operator.truediv, ast.Mod: operator.mod, ast.USub: operator.neg}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return operations[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        raise ValueError("Only numeric arithmetic is supported")
    if len(expression) > 300:
        raise ValueError("Expression too long")
    return visit(ast.parse(expression, mode="eval").body)


def compute(operation, data):
    if operation == "arithmetic":
        return arithmetic(data)
    if operation == "sort":
        return sorted(data)
    if operation == "date_difference":
        return (date.fromisoformat(data[1])-date.fromisoformat(data[0])).days
    if operation == "regex":
        return re.findall(data["pattern"], data["text"])
    if operation == "lookup":
        return data["mapping"][data["key"]]
    if operation == "character_count":
        return len(data.replace(" ", ""))
    if operation == "median":
        import statistics
        return statistics.median(data)
    if operation == "binary_to_int":
        return int(data, 2)
    if operation == "double_positive":
        return [x * 2 for x in data if x > 0]
    raise ValueError("Unknown operation")


async def read_resource(session, uri):
    result = await session.read_resource(uri)
    return "\n".join(item.text for item in result.contents if hasattr(item, "text"))


def resource_tool():
    return {"type": "function", "name": "read_resource",
        "description": "Read an MCP usage resource: jev://guide or jev://skill.",
        "inputSchema": {"type": "object", "properties": {
            "uri": {"type": "string", "enum": ["jev://guide", "jev://skill"]}},
            "required": ["uri"]}}
