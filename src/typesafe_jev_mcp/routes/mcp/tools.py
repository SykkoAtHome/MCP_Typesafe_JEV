"""MCP tool registrations for TypeSafe Jev (System One)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typesafe_jev_mcp.errors import JevError
from typesafe_jev_mcp.routes.mcp.guidance import BOX_GUIDANCE, IMAGE_INPUT_GUIDANCE, QUESTION_GUIDANCE
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
            "Each entry in `questions` requires `type` and nonempty `instructions`:\n"
            "- Noul (binary probability): `{\"type\": \"noul\", \"instructions\": \"...\", "
            "\"criteria\": {\"true\": \"...\", \"false\": \"...\"}}`\n"
            "- Choice (1 of up to 255 options): `{\"type\": \"choice\", \"instructions\": \"...\", "
            "\"criteria\": {\"opt_a\": \"...\", \"opt_b\": \"...\"}}`\n"
            "- Score (2-10 ordered rubric levels): `{\"type\": \"score\", \"instructions\": \"...\", "
            "\"criteria\": [\"level 0 (lowest)\", \"level 1\", \"level 2 (highest)\"]}`\n"
            "- Box (bounding box on image asset, Jev 1.14+): "
            "`{\"type\": \"box\", \"instructions\": \"the object in `photo`\"}`. "
            "All question types support images. In assets, map unique references to "
            "{\"path\": \"/absolute/photo.png\"} (local file uploaded to TypeSafe) or "
            "{\"format\": \"png\", \"data_base64\": \"...\"}. Put each reference in a string "
            "in state, instructions, or criteria. PNG/JPEG, 280..1568 px per side, <=16 MiB. "
            + IMAGE_INPUT_GUIDANCE + " " + QUESTION_GUIDANCE + " " + BOX_GUIDANCE
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
            "and returns the winning `choice`, full `probabilities` distribution, and `confidence`. "
            "Use neutral option descriptions and include unknown when evidence may not distinguish the options. "
            "Check the final identifier against the supported decision. " + IMAGE_INPUT_GUIDANCE
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
            "`legend`, and calibrated `confidence`. "
            "Define neutral ordered levels, not claims about the answer. " + IMAGE_INPUT_GUIDANCE
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
            "`confidence` |2p - 1|. "
            "For supported/refuted/unknown, use choice or a separate evidence-sufficiency question; "
            "false need not establish the opposite claim. " + IMAGE_INPUT_GUIDANCE
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
            "`jev-latest` (Jev 1.14+). Reference the asset key in `state` or `instructions` "
            "and pass `assets={\"<ref>\": {\"path\": \"/absolute/photo.png\"}}` to upload a local "
            "PNG/JPEG to TypeSafe, or use format and data_base64 for inline images. "
            "Returns normalized [0.0, 1.0] edges (`top`, `bottom`, `left`, `right`) and `confidence`. "
            + IMAGE_INPUT_GUIDANCE + " " + BOX_GUIDANCE
        ),
    )
    async def jev_box(
        state: Any,
        instructions: Any,
        assets: dict[str, dict[str, str]],
        model: str = "jev-latest",
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

