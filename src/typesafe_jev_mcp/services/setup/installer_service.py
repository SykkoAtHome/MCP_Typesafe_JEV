"""Service for managing user API keys and installing MCP configs across harnesses."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from typesafe_jev_mcp.db.credentials import CredentialStore
from typesafe_jev_mcp.repositories.harness import (
    HarnessConfigRepository,
    HarnessInstallReport,
    HarnessTarget,
)

ALL_HARNESSES: tuple[HarnessTarget, ...] = (
    "claude-code",
    "codex",
    "gemini",
    "antigravity",
)


class InstallerService:
    """Handles credential persistence and multi-harness MCP configuration."""

    def __init__(
        self,
        *,
        credential_store: CredentialStore | None = None,
        harness_repo: HarnessConfigRepository | None = None,
    ) -> None:
        self._store = credential_store or CredentialStore()
        self._repo = harness_repo or HarnessConfigRepository()

    def save_api_key(self, raw_key: str) -> dict[str, Any]:
        """Validate and store the user's TypeSafe API key in their private OS profile."""
        resolution = self._store.save_key(raw_key)
        return {
            "saved": True,
            "source": resolution.source,
            "masked_key": resolution.key.masked,
            "fingerprint": resolution.key.fingerprint,
            "standard_format": resolution.key.is_standard_format,
        }

    def clear_api_key(self) -> dict[str, Any]:
        """Delete stored API key from the user profile."""
        removed = self._store.clear_key()
        return {
            "removed": removed,
            "credentials_file": str(self._store.credentials_file),
        }

    def install(
        self,
        target: HarnessTarget | Literal["all"],
        *,
        config_path: Path | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        include_env_placeholder: bool = False,
        dry_run: bool = False,
    ) -> list[HarnessInstallReport]:
        """Install `typesafe-jev` MCP server into one or all supported agent harnesses."""
        harnesses: tuple[HarnessTarget, ...] = (
            ALL_HARNESSES if target == "all" else (target,)
        )
        reports: list[HarnessInstallReport] = []
        for harness in harnesses:
            custom_path = config_path if len(harnesses) == 1 else None
            report = self._repo.install_harness(
                harness,
                target_path=custom_path,
                command=command,
                args=args,
                include_env_placeholder=include_env_placeholder,
                dry_run=dry_run,
            )
            reports.append(report)
        return reports
