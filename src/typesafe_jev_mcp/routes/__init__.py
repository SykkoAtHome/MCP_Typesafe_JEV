"""Routes layer facade: MCP server and CLI entrypoints."""

from typesafe_jev_mcp.routes.cli import main
from typesafe_jev_mcp.routes.mcp import create_mcp_server

__all__ = ["create_mcp_server", "main"]
