"""Unit tests for EvaluationService, multi-harness config installer, and FastMCP server."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import httpx

from typesafe_jev_mcp.repositories.harness import HarnessConfigRepository
from typesafe_jev_mcp.repositories.jev import JevGateway
from typesafe_jev_mcp.routes.mcp import create_mcp_server
from typesafe_jev_mcp.services.evaluation import EvaluationService
from typesafe_jev_mcp.services.setup import InstallerService

SYNTHETIC_KEY = "apikey_0000111122223333444455556666_aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff6666"


async def test_evaluation_service_batch_and_composite_weights() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "eval_batch",
                "created_at": 1760000000,
                "model": "jev-1.13.0",
                "answers": {
                    "model_pick": {
                        "type": "choice",
                        "choice": "flash",
                        "probabilities": {"flash": 0.8, "pro": 0.2},
                        "confidence": 0.65,
                    },
                    "complexity": {
                        "type": "score",
                        "score": 1.0,
                        "legend": {"0": "low", "1": "med", "2": "high"},
                        "probabilities": {"0": 0.1, "1": 0.8, "2": 0.1},
                        "confidence": 0.72,
                    },
                    "is_safe": {
                        "type": "noul",
                        "noul": 0.9,
                    },
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        gateway = JevGateway(explicit_api_key=SYNTHETIC_KEY, http_client=client)
        service = EvaluationService(gateway=gateway)
        out = await service.evaluate(
            state={"task": "Add unit test"},
            questions={
                "model_pick": {
                    "type": "choice",
                    "instructions": "Select model",
                    "criteria": {"flash": "fast", "pro": "deep"},
                },
                "complexity": {
                    "type": "score",
                    "instructions": "Rate complexity",
                    "criteria": ["low", "med", "high"],
                },
                "is_safe": {
                    "type": "noul",
                    "instructions": "Is it safe?",
                },
            },
            weights={"complexity": 0.5, "is_safe": 0.5},
            confidence_threshold=0.6,
        )

    assert out["answers"]["model_pick"]["choice"] == "flash"
    assert out["answers"]["complexity"]["normalized"] == 0.5
    assert out["answers"]["is_safe"]["confidence"] == 0.8
    assert out["composite_score"] == 0.7
    assert out["confidence_gate_passed"] is True


def test_multi_harness_installer_writes_json_and_toml(tmp_path: Path) -> None:
    repo = HarnessConfigRepository(home_dir=tmp_path)
    installer = InstallerService(harness_repo=repo)

    reports = installer.install("all", command="/usr/bin/python3")
    assert len(reports) == 4

    claude_cfg = json.loads((tmp_path / ".claude.json").read_text(encoding="utf-8"))
    assert "typesafe-jev" in claude_cfg["mcpServers"]

    gemini_cfg = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))
    assert "typesafe-jev" in gemini_cfg["mcpServers"]

    agy_cfg = json.loads(
        (tmp_path / ".gemini" / "antigravity" / "mcp_config.json").read_text(encoding="utf-8")
    )
    assert "typesafe-jev" in agy_cfg["mcpServers"]

    codex_cfg = tomllib.loads((tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8"))
    assert "typesafe-jev" in codex_cfg["mcp_servers"]


async def test_mcp_server_registers_all_jev_tools_and_embedded_skill() -> None:
    server = create_mcp_server()
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert {"jev_evaluate", "jev_choice", "jev_score", "jev_noul", "jev_box", "jev_status"} <= tool_names

    resources = await server.list_resources()
    resource_uris = {str(r.uri) for r in resources}
    assert {"jev://skill", "jev://guide"} <= resource_uris

    prompts = await server.list_prompts()
    prompt_names = {p.name for p in prompts}
    assert {"typesafe_ai_skill", "jev_usage_guide"} <= prompt_names


