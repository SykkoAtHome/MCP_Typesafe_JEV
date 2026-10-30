"""MCPServer factory and runner for `typesafe-jev`."""

from __future__ import annotations

from typing import Literal

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer  # type: ignore[no-redef]

from typesafe_jev_mcp.routes.mcp.prompts import register_prompts_and_resources
from typesafe_jev_mcp.routes.mcp.guidance import DECISION_GUIDANCE
from typesafe_jev_mcp.routes.mcp.tools import register_tools
from typesafe_jev_mcp.services.evaluation import EvaluationService

SERVER_INSTRUCTIONS = (
    "TypeSafe Jev (System One) evaluation server. Use `jev_evaluate` to run parallel batches "
    "of `noul` (yes/no probability), `choice` (1..255 options), `score` (2..10 rubric levels), "
    "or `box` questions over any JSON/text `state` in a single ~100ms call. "
    "For question design patterns and System One best practices, read the embedded skill resource "
    "`jev://skill` (or compact `jev://guide`) on demand. "
    "Use deterministic code for exact arithmetic, text/structured-data counting, parsing, and lookup. "
    "For visual evaluation, attach the image in assets with matching string references. "
    "Use neutral criteria and represent missing evidence explicitly. " + DECISION_GUIDANCE
)



def create_mcp_server(service: EvaluationService | None = None) -> MCPServer:
    """Instantiate the `typesafe-jev` MCPServer with all tools, prompts, and resources."""
    eval_service = service or EvaluationService()
    mcp = MCPServer(
        name="typesafe-jev",
        instructions=SERVER_INSTRUCTIONS,
    )
    register_tools(mcp, eval_service)
    register_prompts_and_resources(mcp)
    return mcp


def run_mcp_server(transport: Literal["stdio", "sse", "streamable-http"] = "stdio") -> None:
    """Start the MCPServer loop over the selected transport."""
    server = create_mcp_server()
    server.run(transport=transport)
