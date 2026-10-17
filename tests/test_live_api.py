"""End-to-end live MCP server tests against `https://api.typesafe.ai` covering all Jev tools, primitives, resources, prompts, image assets, and error handling."""

from __future__ import annotations

import base64
import json
import os
import struct
import zlib
from typing import Any

import pytest

from typesafe_jev_mcp.routes.mcp import create_mcp_server

pytestmark = pytest.mark.skipif(
    not os.environ.get("TYPESAFE_API_KEY"),
    reason="TYPESAFE_API_KEY not set in environment; skipping live MCP integration tests.",
)


async def _call_mcp_tool(server: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Invoke a tool through the MCPServer interface and decode its JSON payload."""
    raw = await server.call_tool(name, arguments)
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, tuple) and len(raw) == 2 and isinstance(raw[1], dict) and raw[1]:
        structured = raw[1]
        if "result" in structured and isinstance(structured["result"], dict):
            return structured["result"]
        return structured
    blocks = raw[0] if isinstance(raw, tuple) else getattr(raw, "content", raw)
    for block in blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return json.loads(text)
    raise AssertionError(f"Unexpected MCP call_tool output for {name}: {raw!r}")


def _make_red_square_png_base64(size: int = 300) -> str:
    """Create a valid RGB PNG >=280x280 (white background with a red square in bottom-right quadrant)."""

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    white_row = b"\x00" + (b"\xff\xff\xff" * size)
    red_row = (
        b"\x00"
        + (b"\xff\xff\xff" * 150)
        + (b"\xdc\x14\x14" * 100)
        + (b"\xff\xff\xff" * (size - 250))
    )
    raw_rows = (white_row * 150) + (red_row * 100) + (white_row * (size - 250))
    idat = zlib.compress(raw_rows)
    png_bytes = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")
    return base64.b64encode(png_bytes).decode("ascii")


async def test_mcp_live_status_resources_and_prompts() -> None:
    server = create_mcp_server()
    api_key = os.environ["TYPESAFE_API_KEY"]

    status = await _call_mcp_tool(server, "jev_status", {"verify_upstream": True})
    assert status["configured"] is True
    assert status["upstream_ok"] is True
    model_names = {m.get("name") or m.get("id") for m in status["available_models"]}
    assert {"jev-latest", "jev-preview"} <= model_names
    assert "..." in status["masked_key"]
    assert api_key not in json.dumps(status)

    skill_contents = await server.read_resource("jev://skill")
    skill_text = str(skill_contents)
    assert "Speculative Fan-Out" in skill_text
    assert "jev_box" in skill_text

    guide_contents = await server.read_resource("jev://guide")
    assert "jev_evaluate" in str(guide_contents)

    prompt_result = await server.get_prompt("typesafe_ai_skill")
    assert "System One" in str(prompt_result)


async def test_mcp_live_noul_tool_variants() -> None:
    server = create_mcp_server()

    # 1. Noul without explicit criteria
    simple = await _call_mcp_tool(
        server,
        "jev_noul",
        {
            "state": {"message": "Please cancel my subscription immediately and refund my last charge."},
            "instructions": "Is the user asking to cancel their subscription in `message`?",
        },
    )
    assert simple["noul"] > 0.7
    assert simple["verdict"] is True
    assert simple["confidence"] > 0.4
    assert "Speculative Fan-Out" not in json.dumps(simple)

    # 2. Noul with explicit true/false criteria + structured instructions
    guardrail = await _call_mcp_tool(
        server,
        "jev_noul",
        {
            "state": {"command": "DROP TABLE production_users CASCADE;", "env": "production"},
            "instructions": {
                "question": "Is executing `command` in `env` destructive to production data?",
                "focus": "Data loss risk",
            },
            "true_criteria": "Deletes, drops, or truncates persistent production tables or files.",
            "false_criteria": "Read-only query or safe non-destructive operation.",
        },
    )
    assert guardrail["noul"] > 0.8
    assert guardrail["verdict"] is True
    assert guardrail["confidence"] > 0.6


async def test_mcp_live_choice_tool_variants() -> None:
    server = create_mcp_server()

    # 1. Agent model routing across harness tiers
    routing = await _call_mcp_tool(
        server,
        "jev_choice",
        {
            "state": {
                "task": "Fix a typo in the README.md installation heading.",
                "files_changed": 1,
            },
            "instructions": "Pick the most cost-effective model tier for `task`.",
            "criteria": {
                "flash_lite": "Fastest and cheapest tier for trivial typos, formatting, and one-line docs edits",
                "flash": "Standard daily coding tier for single-module features and unit tests",
                "pro": "Heavy architectural reasoning tier for complex multi-file concurrency and security refactors",
            },
        },
    )
    assert routing["choice"] in {"flash_lite", "flash"}
    assert abs(sum(routing["probabilities"].values()) - 1.0) < 0.05
    assert 0.0 <= routing["confidence"] <= 1.0

    # 2. Choice with null (None) option descriptions (self-explanatory option keys)
    null_criteria = await _call_mcp_tool(
        server,
        "jev_choice",
        {
            "state": {"ticket": "App crashes with NullPointerException when clicking Export PDF."},
            "instructions": "Classify `ticket` into the best category.",
            "criteria": {
                "bug_report": None,
                "billing_question": None,
                "account_deletion": None,
            },
        },
    )
    assert null_criteria["choice"] == "bug_report"
    assert null_criteria["probabilities"]["bug_report"] > 0.5


async def test_mcp_live_score_tool_ordinal_rubric() -> None:
    server = create_mcp_server()
    rubric = [
        "Trivial typo, comment, or formatting tweak",
        "Simple single-function bugfix or unit test",
        "Multi-file feature with database migration",
        "High-risk distributed consensus or cryptographic protocol redesign",
    ]

    low_res = await _call_mcp_tool(
        server,
        "jev_score",
        {
            "state": {"task": "Fix spelling of 'recieve' in README.md."},
            "instructions": "Rate the engineering complexity of `task`.",
            "criteria": rubric,
        },
    )
    high_res = await _call_mcp_tool(
        server,
        "jev_score",
        {
            "state": {
                "task": "Redesign Raft leader election and zero-knowledge key rotation across 5 microservices."
            },
            "instructions": "Rate the engineering complexity of `task`.",
            "criteria": rubric,
        },
    )

    assert 0.0 <= low_res["score"] <= 3.0
    assert 0.0 <= low_res["normalized"] <= 1.0
    assert high_res["score"] > low_res["score"] + 1.0
    assert high_res["normalized"] > low_res["normalized"]


async def test_mcp_live_box_and_image_assets() -> None:
    server = create_mcp_server()
    png_b64 = _make_red_square_png_base64()
    assets = {
        "img_canvas_01": {
            "type": "image",
            "format": "png",
            "data_base64": png_b64,
        }
    }

    box_res = await _call_mcp_tool(
        server,
        "jev_box",
        {
            "state": {"canvas": "img_canvas_01"},
            "instructions": "Locate the red square inside `canvas`.",
            "assets": assets,
            "model": "jev-preview",
        },
    )
    assert "box" in box_res
    coords = box_res["box"]
    assert 0.0 <= coords["top"] < coords["bottom"] <= 1.0
    assert 0.0 <= coords["left"] < coords["right"] <= 1.0
    assert 0.0 <= box_res["confidence"] <= 1.0

    img_noul = await _call_mcp_tool(
        server,
        "jev_noul",
        {
            "state": {"canvas": "img_canvas_01"},
            "instructions": "Does `canvas` contain a red square?",
            "assets": assets,
            "model": "jev-preview",
        },
    )
    assert img_noul["noul"] > 0.5
    assert img_noul["verdict"] is True


async def test_mcp_live_evaluate_fanout_composite_weights_and_reranking() -> None:
    server = create_mcp_server()

    # 1. Speculative fan-out combining noul + choice + score + weights + confidence_threshold + long_context
    fanout = await _call_mcp_tool(
        server,
        "jev_evaluate",
        {
            "state": {
                "pr_title": "Add parameterized SQL query for user lookup",
                "diff": "cursor.execute('SELECT id, email FROM users WHERE id = ?', (user_id,))",
            },
            "questions": {
                "is_sql_injection_safe": {
                    "type": "noul",
                    "instructions": "Does `diff` use parameterized queries instead of string interpolation?",
                },
                "code_quality": {
                    "type": "score",
                    "instructions": "Rate the security and clarity of `diff`.",
                    "criteria": [
                        "Vulnerable to SQL injection or broken syntax",
                        "Acceptable but messy",
                        "Clean, idiomatic, parameterized SQL query",
                    ],
                },
                "review_action": {
                    "type": "choice",
                    "instructions": "Choose the appropriate PR review decision for `diff`.",
                    "criteria": {
                        "approve": "Safe, clean, parameterized query ready to merge",
                        "request_changes": "Contains SQL injection or critical bug",
                    },
                },
            },
            "weights": {"is_sql_injection_safe": 0.6, "code_quality": 0.4},
            "confidence_threshold": 0.2,
            "long_context": True,
        },
    )
    assert fanout["answers"]["is_sql_injection_safe"]["verdict"] is True
    assert fanout["answers"]["review_action"]["choice"] == "approve"
    assert fanout["composite_score"] is not None and fanout["composite_score"] > 0.6
    assert fanout["confidence_gate_passed"] is True
    assert "usage" in fanout

    # 2. Parallel candidate reranking in one batch call
    rerank = await _call_mcp_tool(
        server,
        "jev_evaluate",
        {
            "state": {
                "goal": "Safely parse an integer from user input with a fallback default of 0.",
                "candidates": {
                    "cand_eval": "return eval(user_input)",
                    "cand_try_int": "try:\n    return int(user_input)\nexcept (ValueError, TypeError):\n    return 0",
                    "cand_crash": "return int(user_input) / 0",
                },
            },
            "questions": {
                "score_eval": {
                    "type": "noul",
                    "instructions": "Is `candidates.cand_eval` a safe and correct implementation of `goal`?",
                },
                "score_try_int": {
                    "type": "noul",
                    "instructions": "Is `candidates.cand_try_int` a safe and correct implementation of `goal`?",
                },
                "score_crash": {
                    "type": "noul",
                    "instructions": "Is `candidates.cand_crash` a safe and correct implementation of `goal`?",
                },
            },
        },
    )
    p_eval = rerank["answers"]["score_eval"]["noul"]
    p_try_int = rerank["answers"]["score_try_int"]["noul"]
    p_crash = rerank["answers"]["score_crash"]["noul"]
    assert p_try_int > p_eval
    assert p_try_int > p_crash


async def test_mcp_live_error_handling_and_secret_redaction() -> None:
    server = create_mcp_server()
    api_key = os.environ["TYPESAFE_API_KEY"]

    # Trigger validation error via MCP tool (invalid question type)
    bad_type = await _call_mcp_tool(
        server,
        "jev_evaluate",
        {
            "state": {"x": 1},
            "questions": {"q1": {"type": "invalid_primitive", "instructions": "Test"}},
        },
    )
    assert "error" in bad_type
    assert api_key not in json.dumps(bad_type)

    # Trigger upstream 400 error via MCP tool (unreferenced asset key in `assets`)
    unreferenced_asset = await _call_mcp_tool(
        server,
        "jev_noul",
        {
            "state": {"text": "No reference to the image key here"},
            "instructions": "Is this valid?",
            "assets": {
                "unused_img_id": {
                    "type": "image",
                    "format": "png",
                    "data_base64": _make_red_square_png_base64(),
                }
            },
        },
    )
    assert "error" in unreferenced_asset
    assert api_key not in json.dumps(unreferenced_asset)
