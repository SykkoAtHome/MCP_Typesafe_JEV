"""MCP tool registrations for TypeSafe Jev (System One)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typesafe_jev_mcp.errors import JevError
from typesafe_jev_mcp.services.evaluation import EvaluationService

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer


def register_tools(mcp: MCPServer, service: EvaluationService) -> None:
    """Register domain-agnostic TypeSafe Jev System One tools on the MCPServer."""

    @mcp.tool(
        name="jev_evaluate",
        description=(
            "Evaluate one or many structured System One questions (`noul`, `choice`, `score`, `box`) "
            "in parallel over `state` via a single `POST /v1/systemone` call (~100-150ms). "
            "All questions execute simultaneously with zero extra latency (Speculative Fan-Out). "
            "Each entry in `questions` maps a question ID to:\n"
            "- Noul (binary probability): `{\"type\": \"noul\", \"instructions\": \"...\", "
            "\"criteria\": {\"true\": \"...\", \"false\": \"...\"}}`\n"
            "- Choice (1 of up to 255 options): `{\"type\": \"choice\", \"instructions\": \"...\", "
            "\"criteria\": {\"opt_a\": \"...\", \"opt_b\": \"...\"}}`\n"
            "- Score (2-10 ordered rubric levels): `{\"type\": \"score\", \"instructions\": \"...\", "
            "\"criteria\": [\"level 0 (lowest)\", \"level 1\", \"level 2 (highest)\"]}`\n"
            "- Box (bounding box on image asset, requires `jev-preview`): "
            "`{\"type\": \"box\", \"instructions\": \"the object in `photo`\"}`"
        ),
    )
    async def jev_evaluate(
        state: Any,
        questions: dict[str, dict[str, Any]],
        model: str = "jev-latest",
        weights: dict[str, float] | None = None,
        confidence_threshold: float | None = None,
        assets: dict[str, dict[str, str]] | None = None,
        long_context: bool = False,
    ) -> dict[str, Any]:
        try:
            return await service.evaluate(
                state=state,
                questions=questions,
                model=model,
                weights=weights,
                confidence_threshold=confidence_threshold,
                assets=assets,
                long_context=long_context,
            )
        except JevError as exc:
            return {"error": exc.code, "message": exc.message}

    @mcp.tool(
        name="jev_choice",
        description=(
            "Evaluate a single categorical `choice` question over `state`. Picks 1 of up to 255 "
            "named options defined in `criteria` (mapping option key -> description/criteria or null) "
            "and returns the winning `choice`, full `probabilities` distribution, and `confidence`."
        ),
    )
    async def jev_choice(
        state: Any,
        instructions: Any,
        criteria: dict[str, Any],
        assets: dict[str, dict[str, str]] | None = None,
        model: str = "jev-latest",
        long_context: bool = False,
    ) -> dict[str, Any]:
        try:
            return await service.choice(
                state=state,
                instructions=instructions,
                criteria=criteria,
                assets=assets,
                model=model,
                long_context=long_context,
            )
        except JevError as exc:
            return {"error": exc.code, "message": exc.message}

    @mcp.tool(
        name="jev_score",
        description=(
            "Evaluate a single ordinal `score` rubric question over `state`. `criteria` must be an "
            "ordered list of 2 to 10 rubric levels from lowest (index 0) to highest (index n-1). "
            "Returns the expected `score`, `normalized` value in [0.0, 1.0], `probabilities`, "
            "`legend`, and calibrated `confidence`."
        ),
    )
    async def jev_score(
        state: Any,
        instructions: Any,
        criteria: list[Any],
        assets: dict[str, dict[str, str]] | None = None,
        model: str = "jev-latest",
        long_context: bool = False,
    ) -> dict[str, Any]:
        try:
            return await service.score(
                state=state,
                instructions=instructions,
                criteria=criteria,
                assets=assets,
                model=model,
                long_context=long_context,
            )
        except JevError as exc:
            return {"error": exc.code, "message": exc.message}

    @mcp.tool(
        name="jev_noul",
        description=(
            "Evaluate a single binary `noul` (yes/no probability) question over `state`. "
            "Returns `noul` probability P(true) in [0.0, 1.0], boolean `verdict`, and derived "
            "`confidence` |2p - 1|."
        ),
    )
    async def jev_noul(
        state: Any,
        instructions: Any,
        true_criteria: Any | None = None,
        false_criteria: Any | None = None,
        assets: dict[str, dict[str, str]] | None = None,
        model: str = "jev-latest",
        long_context: bool = False,
    ) -> dict[str, Any]:
        try:
            return await service.noul(
                state=state,
                instructions=instructions,
                true_criteria=true_criteria,
                false_criteria=false_criteria,
                assets=assets,
                model=model,
                long_context=long_context,
            )
        except JevError as exc:
            return {"error": exc.code, "message": exc.message}

    @mcp.tool(
        name="jev_box",
        description=(
            "Evaluate a single `box` bounding-box detection question on an image asset using "
            "`jev-preview` (`jev-1.14.0`). Reference the asset key in `state` or `instructions` "
            "and pass `assets={\"<ref>\": {\"type\": \"image\", \"format\": \"png\", \"data_base64\": \"...\"}}`. "
            "Returns normalized [0.0, 1.0] edges (`top`, `bottom`, `left`, `right`) and `confidence`."
        ),
    )
    async def jev_box(
        state: Any,
        instructions: Any,
        assets: dict[str, dict[str, str]],
        model: str = "jev-preview",
        long_context: bool = False,
    ) -> dict[str, Any]:
        try:
            return await service.box(
                state=state,
                instructions=instructions,
                assets=assets,
                model=model,
                long_context=long_context,
            )
        except JevError as exc:
            return {"error": exc.code, "message": exc.message}

    @mcp.tool(
        name="jev_status",
        description=(
            "Check TypeSafe API credential status (masked key and fingerprint only) and "
            "list available upstream Jev models (`jev-latest`, `jev-preview`, etc.) via `GET /v1/models`."
        ),
    )
    async def jev_status(verify_upstream: bool = True) -> dict[str, Any]:
        return await service.check_health(verify_upstream=verify_upstream)

