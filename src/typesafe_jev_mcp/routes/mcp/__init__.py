"""MCP server package facade."""

from typesafe_jev_mcp.routes.mcp.prompts import JEV_QUICK_GUIDE, TYPESAFE_AI_SKILL
from typesafe_jev_mcp.routes.mcp.server import create_mcp_server, run_mcp_server

__all__ = [
    "JEV_QUICK_GUIDE",
    "TYPESAFE_AI_SKILL",
    "create_mcp_server",
    "run_mcp_server",
]

