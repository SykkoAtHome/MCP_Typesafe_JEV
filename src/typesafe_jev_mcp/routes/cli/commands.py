"""Command-line interface for running the MCP server, managing API keys, and installing harnesses."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import sys
from pathlib import Path
from typing import Sequence

from typesafe_jev_mcp.errors import JevError
from typesafe_jev_mcp.routes.mcp.server import run_mcp_server
from typesafe_jev_mcp.services.evaluation import EvaluationService
from typesafe_jev_mcp.services.setup import InstallerService


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for `typesafe-jev-mcp`."""
    parser = argparse.ArgumentParser(
        prog="typesafe-jev-mcp",
        description="TypeSafe Jev (System One) MCP Server & Multi-Harness Installer.",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    serve_p = subparsers.add_parser("serve", help="Run the MCP server (default command).")
    serve_p.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport protocol (default: stdio).",
    )

    auth_p = subparsers.add_parser("auth", help="Securely manage the user's TypeSafe API key.")
    auth_sub = auth_p.add_subparsers(dest="auth_action", required=True)

    set_key_p = auth_sub.add_parser(
        "set-key",
        help="Save TypeSafe API key to your private user profile (hidden prompt or --stdin).",
    )
    set_key_p.add_argument(
        "--stdin",
        action="store_true",
        help="Read the API key from standard input instead of interactive hidden prompt.",
    )
    set_key_p.add_argument(
        "--key",
        type=str,
        default=None,
        help="Pass key directly (prefer interactive prompt or --stdin to avoid shell history).",
    )

    auth_sub.add_parser("status", help="Show masked API key status and verify upstream connectivity.")
    auth_sub.add_parser("clear", help="Remove stored API key from your user profile.")

    install_p = subparsers.add_parser(
        "install",
        help="Register `typesafe-jev` in Claude Code, Codex, Gemini CLI, or Antigravity.",
    )
    install_p.add_argument(
        "--harness",
        choices=["claude-code", "codex", "gemini", "antigravity", "all"],
        default="all",
        help="Target harness to configure (default: all).",
    )
    install_p.add_argument(
        "--config-path",
        type=Path,
        default=None,
        help="Custom config file path (only when installing a single harness).",
    )
    install_p.add_argument(
        "--include-env",
        action="store_true",
        help="Include an env block placeholder for TYPESAFE_API_KEY in the generated config.",
    )
    install_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration snippets without modifying any files.",
    )

    subparsers.add_parser("doctor", help="Check API key and live TypeSafe `/v1/models` health.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint for `typesafe-jev-mcp` CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.subcommand or "serve"

    try:
        if cmd == "serve":
            transport = getattr(args, "transport", "stdio")
            run_mcp_server(transport=transport)
            return 0
        if cmd == "auth":
            return _handle_auth(args)
        if cmd == "install":
            return _handle_install(args)
        if cmd == "doctor":
            return _handle_doctor()
    except JevError as exc:
        print(json.dumps({"error": exc.code, "message": exc.message}, indent=2), file=sys.stderr)
        return 1
    return 0


def _handle_auth(args: argparse.Namespace) -> int:
    installer = InstallerService()
    if args.auth_action == "set-key":
        raw_key = _read_key_input(args)
        report = installer.save_api_key(raw_key)
        print(json.dumps(report, indent=2))
        return 0
    if args.auth_action == "clear":
        report = installer.clear_api_key()
        print(json.dumps(report, indent=2))
        return 0
    if args.auth_action == "status":
        return _handle_doctor()
    return 1


def _read_key_input(args: argparse.Namespace) -> str:
    if args.key:
        return args.key.strip()
    if args.stdin or not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return getpass.getpass("Enter TypeSafe API key (input hidden): ").strip()


def _handle_install(args: argparse.Namespace) -> int:
    installer = InstallerService()
    reports = installer.install(
        args.harness,
        config_path=args.config_path,
        include_env_placeholder=args.include_env,
        dry_run=args.dry_run,
    )
    output = [
        {
            "harness": r.harness,
            "config_path": str(r.config_path),
            "written": r.written,
            "snippet": r.snippet,
        }
        for r in reports
    ]
    print(json.dumps(output, indent=2))
    return 0


def _handle_doctor() -> int:
    service = EvaluationService()
    report = asyncio.run(service.check_health(verify_upstream=True))
    print(json.dumps(report, indent=2))
    return 0 if report.get("configured") and report.get("upstream_ok", True) else 1
