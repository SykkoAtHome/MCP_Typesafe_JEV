"""Reads and writes MCP configuration files for Claude Code, Codex, Gemini CLI, and Antigravity."""

from __future__ import annotations

import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import tomli_w

from typesafe_jev_mcp.errors import ConfigurationError

HarnessTarget = Literal["claude-code", "codex", "gemini", "antigravity"]
SERVER_NAME = "typesafe-jev"


@dataclass(frozen=True, slots=True)
class HarnessInstallReport:
    """Summary of a harness MCP configuration update or dry-run snippet."""

    harness: HarnessTarget
    config_path: Path
    written: bool
    snippet: str


class HarnessConfigRepository:
    """Manages MCP server registration across major AI coding agent harnesses."""

    def __init__(self, *, home_dir: Path | None = None) -> None:
        self._home = home_dir or Path.home()

    def default_config_path(self, harness: HarnessTarget) -> Path:
        """Return the standard user-level MCP configuration file path for a harness."""
        if harness == "claude-code":
            return self._home / ".claude.json"
        if harness == "codex":
            return self._home / ".codex" / "config.toml"
        if harness == "gemini":
            return self._home / ".gemini" / "settings.json"
        if harness == "antigravity":
            return self._home / ".gemini" / "antigravity" / "mcp_config.json"
        raise ConfigurationError(f"Unsupported harness: {harness}")

    @staticmethod
    def build_server_entry(
        *,
        command: str | None = None,
        args: list[str] | None = None,
        include_env_placeholder: bool = False,
    ) -> dict[str, Any]:
        """Construct the standard command/args entry for running `typesafe-jev-mcp`."""
        resolved_cmd = command or sys.executable
        resolved_args = (
            args if args is not None else ["-m", "typesafe_jev_mcp", "serve"]
        )
        entry: dict[str, Any] = {
            "command": str(Path(resolved_cmd).as_posix()),
            "args": resolved_args,
        }
        if include_env_placeholder:
            entry["env"] = {"TYPESAFE_API_KEY": "${TYPESAFE_API_KEY}"}
        return entry

    def install_harness(
        self,
        harness: HarnessTarget,
        *,
        target_path: Path | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        include_env_placeholder: bool = False,
        dry_run: bool = False,
    ) -> HarnessInstallReport:
        """Register `typesafe-jev` in the target harness configuration file."""
        path = target_path or self.default_config_path(harness)
        entry = self.build_server_entry(
            command=command,
            args=args,
            include_env_placeholder=include_env_placeholder,
        )
        if harness == "codex":
            return self._install_toml(path, entry, dry_run=dry_run)
        return self._install_json(harness, path, entry, dry_run=dry_run)

    def _install_json(
        self,
        harness: HarnessTarget,
        path: Path,
        entry: dict[str, Any],
        *,
        dry_run: bool,
    ) -> HarnessInstallReport:
        existing: dict[str, Any] = {}
        if path.is_file():
            try:
                raw = path.read_text(encoding="utf-8").strip()
                if raw:
                    existing = json.loads(raw)
            except (OSError, json.JSONDecodeError) as exc:
                raise ConfigurationError(f"Cannot parse JSON config at {path}: {exc}") from exc

        mcp_servers = existing.get("mcpServers")
        if not isinstance(mcp_servers, dict):
            mcp_servers = {}
            existing["mcpServers"] = mcp_servers
        mcp_servers[SERVER_NAME] = entry

        snippet = json.dumps({"mcpServers": {SERVER_NAME: entry}}, indent=2)
        if not dry_run:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                raise ConfigurationError(f"Cannot write JSON config to {path}: {exc}") from exc

        return HarnessInstallReport(
            harness=harness,
            config_path=path,
            written=not dry_run,
            snippet=snippet,
        )

    def _install_toml(
        self,
        path: Path,
        entry: dict[str, Any],
        *,
        dry_run: bool,
    ) -> HarnessInstallReport:
        existing: dict[str, Any] = {}
        if path.is_file():
            try:
                raw = path.read_text(encoding="utf-8").strip()
                if raw:
                    existing = tomllib.loads(raw)
            except (OSError, tomllib.TOMLDecodeError) as exc:
                raise ConfigurationError(f"Cannot parse TOML config at {path}: {exc}") from exc

        mcp_servers = existing.get("mcp_servers")
        if not isinstance(mcp_servers, dict):
            mcp_servers = {}
            existing["mcp_servers"] = mcp_servers
        mcp_servers[SERVER_NAME] = entry

        snippet = tomli_w.dumps({"mcp_servers": {SERVER_NAME: entry}}).strip()
        if not dry_run:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(tomli_w.dumps(existing), encoding="utf-8")
            except OSError as exc:
                raise ConfigurationError(f"Cannot write TOML config to {path}: {exc}") from exc

        return HarnessInstallReport(
            harness="codex",
            config_path=path,
            written=not dry_run,
            snippet=snippet,
        )
