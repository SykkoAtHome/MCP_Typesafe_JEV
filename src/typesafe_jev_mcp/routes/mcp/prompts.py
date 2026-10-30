"""MCP resources and prompts exposing the adapted TypeSafe Jev agent skill."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typesafe_jev_mcp.routes.mcp.guidance import GUIDANCE_REFERENCE

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

TYPESAFE_AI_SKILL = """---
name: typesafe-ai
license: MIT
source: https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md
---

# Build & Evaluate with TypeSafe Jev (System One)

Adapted for this MCP server from the upstream TypeSafe skill, including local guidance validated against agent-evaluation findings.

TypeSafe makes units of AI intelligence usable like programming primitives: small judgments you can compose into larger capabilities. Its **System One models** (`jev-latest`, `jev-preview`) return fast (~100-150ms), focused judgments that software and agents can consume directly. **Jev** understands natural language and structured JSON state and returns typed answers, calibrated probabilities, and confidence scores rather than generating prose.

Code (or the calling agent) owns the workflow and control flow; Jev supplies programmable common sense where semantic understanding is needed.

---

## 1. Using Jev via This MCP Server (Zero-Boilerplate Live Execution)

You have direct access to Jev through this MCP server's tools. Tool calls return **only** the compact evaluation JSON (this skill is never re-sent on tool calls):

- **`jev_evaluate` (Preferred — Speculative Fan-Out)**: Evaluate a batch of multiple independent questions (`noul`, `choice`, `score`, `box`) over `state` in a **single parallel HTTP call** (`POST /v1/systemone`). Supports optional `assets`, `weights` (composite score in `[0, 1]`), `confidence_threshold`, and `long_context`.
- **`jev_choice`**: Single categorical choice across 1..255 agent-defined options (`criteria`).
- **`jev_score`**: Single ordinal rubric evaluation across 2..10 ordered levels (`criteria`, index `0` lowest to `n-1` highest).
- **`jev_noul`**: Single binary probability evaluation returning `noul` $P(\\text{true}) \\in [0, 1]$, `verdict` (`bool`), and derived `confidence = |2*noul - 1|`.
- **`jev_box`**: Single image bounding-box evaluation (`jev-latest`, Jev 1.14+) returning normalized `[0, 1]` edges (`top`, `bottom`, `left`, `right`) and `confidence`.
- **`jev_status`**: Inspect API key readiness (masked) and `/v1/models` availability.

---

## 2. Primitives & Output Contracts

1. **`noul` (Binary Probability)**
   - Input: `{"type": "noul", "instructions": "...", "criteria": {"true": "...", "false": "..."}}` (`criteria` optional).
   - Output: `noul` in `[0.0, 1.0]`, `verdict` (`bool`), and derived `confidence = |2*noul - 1|`.
2. **`choice` (Categorical Selection, 1..255 options)**
   - Input: `{"type": "choice", "instructions": "...", "criteria": {"opt_a": "Description A", "opt_b": "Description B"}}` (option descriptions may also be `null` when keys are self-explanatory).
   - Output: winning `choice` key, full `probabilities` distribution, and RLCD `confidence`.
3. **`score` (Ordinal Rubric, 2..10 ordered levels)**
   - Input: `{"type": "score", "instructions": "...", "criteria": ["Level 0 (lowest)", "Level 1", "Level 2 (highest)"]}`.
   - Output: continuous expected `score` in `[0, n-1]`, `normalized` score in `[0.0, 1.0]`, `probabilities`, `legend`, and `confidence`.
4. **`box` (Image Bounding Box, Jev 1.14+, including `jev-latest`)**
   - Input: `{"type": "box", "instructions": "..."}` with `assets={"<ref_uuid>": {"type": "image", "format": "png", "data_base64": "<raw_base64>"}}` (each side 280..1568 px) and `<ref_uuid>` referenced inside `state` or `instructions`.
   - Output: normalized `[0, 1]` coordinates `{"top", "bottom", "left", "right"}` and `confidence`.

### Images in every question type

All five evaluation tools accept `assets`. Map a unique reference (prefer a UUID) to either:
- `{"path": "/absolute/path/photo.png"}`: the MCP server reads a local file and uploads it to TypeSafe using multipart. The path is on the MCP server host. Use only files the user intends to send for evaluation.
- `{"format": "png", "data_base64": "<raw_base64>"}`: inline JSON upload, with format `png`, `jpg`, or `jpeg`; `type: "image"` is optional. Use padded base64 without whitespace or a `data:` prefix.

Each asset reference must occur in a string value in `state`, `instructions`, or `criteria`, including nested JSON or mid-sentence references. Object keys are not replaced. Images can define Choice options, Score levels, or Noul true/false criteria. Put a shared image in `state` and refer to its field by name to avoid repeated image expansion.

Images and Box are experimental. The server automatically sends `TypeSafe-Danger-Zone-Images: true`. PNG/JPEG only, 280..1568 pixels per side, at most 16 MiB per file. The API enforces dimensions and the 32 MiB body, processed-image, and expanded-request limits. Image references are limited to 1024 UTF-8 bytes each and 65536 bytes combined. No remote URLs or pre-existing multipart `part` names are accepted as image sources by this MCP.

Example `jev_evaluate`: `{"state": {"photo": "unique-photo-ref"}, "assets": {"unique-photo-ref": {"path": "/absolute/photo.png"}}, "questions": {"red": {"type": "noul", "instructions": "Is there a red object in `photo`?"}, "location": {"type": "box", "instructions": "the red object in `photo`"}}}`.

Official image contract: https://docs.typesafe.ai/images

---

## 3. Core Architectural Patterns

- **Speculative Fan-Out**: Every question in `jev_evaluate` is evaluated independently and in parallel — one question's result never leaks into or biases another question. Pack all relevant and speculative questions into a single `jev_evaluate` call instead of making sequential requests.
- **Agent-Controlled Routing (Models, Subagents, Tools)**: When deciding which of your own harness models (e.g. `haiku`/`sonnet`/`opus` in Claude Code, `flash_lite`/`flash`/`pro` in Gemini/Antigravity, or Codex profiles), tools, or subagents to use, pass **your own available candidates** in `criteria` of a `choice` question alongside atomic `score`/`noul` risk questions.
- **Confidence-Gated Routing**: Verify that the required evidence is available before using confidence. With low confidence, obtain missing evidence, verify independently, or abstain. Define a threshold together with its fallback. High confidence cannot compensate for missing or contradictory evidence.
- **Composite Scoring**: Decompose subjective quality/risk into 3–6 narrow `score` or `noul` questions and pass `weights` to `jev_evaluate` to compute a deterministic weighted score in `[0.0, 1.0]`.
- **Parallel Candidate Reranking**: Evaluate $N$ candidate files, diffs, or plans in one `jev_evaluate` call (`cand_0`, `cand_1`, ...) and sort by `score` or `noul`.

---

## 4. State & Question Design Rules

1. **Keep deterministic rules in code**: Do not ask Jev to do arithmetic, regex matching, date math, or exact string lookups. Compute those in code and pass only semantic judgments to Jev.
2. **Send only relevant context in `state`**: Avoid dumping unrelated files into `state`. Use structured nested JSON and point questions at specific fields using backticked dot-paths in `instructions` (e.g. ``Does `ticket.message` qualify under `policy.refund_rules`?``).
3. **Use the selected option only when supported by the available evidence**: Do not add arbitrary confidence thresholds without a fallback. Check that the final identifier matches the decision you actually support, including any independently verified override.
4. **Live Documentation Index (when building SDK integrations)**:
   - Docs index: `https://docs.typesafe.ai/llms.txt` (append `.md` to any doc path for clean Markdown, e.g. `https://docs.typesafe.ai/primitives.md`, `https://docs.typesafe.ai/confidence.md`, `https://docs.typesafe.ai/patterns.md`, `https://docs.typesafe.ai/api.md`).
"""

TYPESAFE_AI_SKILL += "\n\n" + GUIDANCE_REFERENCE

JEV_QUICK_GUIDE = """# TypeSafe Jev — Quick Reference (`jev://guide`)

- **Batch evaluation (`jev_evaluate`)**: Send `state` (JSON/str) + `questions` (`dict[qid, spec]`) in a single parallel call (~100ms).
- **Primitives**:
  - `noul`: `{"type": "noul", "instructions": "...", "criteria": {"true": "...", "false": "..."}}` -> `noul` in `[0, 1]`, `verdict`, `confidence = |2p - 1|`.
  - `choice`: `{"type": "choice", "instructions": "...", "criteria": {"k1": "desc1", "k2": "desc2"}}` (1..255 options) -> `choice`, `probabilities`, `confidence`.
  - `score`: `{"type": "score", "instructions": "...", "criteria": ["lvl0", "lvl1", ...]}` (2..10 ordered levels) -> `score`, `normalized`, `confidence`.
  - `box`: `{"type": "box", "instructions": "..."}` (`model="jev-latest"`, Jev 1.14+) -> `box` (`top`, `bottom`, `left`, `right`), `confidence`.
- **Images (all primitives)**: `assets={"<unique-ref>": {"path": "/absolute/photo.png"}}` uploads a local file to TypeSafe via multipart; alternatively use `{"format": "png", "data_base64": "..."}` for inline JSON. Put each ref in string values in state, instructions, or criteria. PNG/JPEG, 280..1568 px per side, <=16 MiB per file. The image opt-in header is automatic. See `jev://skill` for limits.
- **MCP-adapted TypeSafe Agent Skill**: Read MCP resource `jev://skill` or invoke prompt `typesafe_ai_skill`.
"""

JEV_QUICK_GUIDE += "\n\n" + GUIDANCE_REFERENCE


def register_prompts_and_resources(mcp: MCPServer) -> None:
    """Register on-demand MCP resources (`jev://skill`, `jev://guide`) and prompts."""

    @mcp.resource(
        "jev://skill",
        name="TypeSafe Agent Skill (MCP adaptation)",
        description=(
            "MCP-adapted TypeSafe System One skill: primitives, fan-out, evidence and confidence, "
            "matching image references, neutral criteria, absence handling, and complete request examples."
        ),
        mime_type="text/markdown",
    )
    def get_typesafe_skill() -> str:
        return TYPESAFE_AI_SKILL

    @mcp.resource(
        "jev://guide",
        name="TypeSafe Jev Quick Reference",
        description="Compact cheatsheet for `noul`, `choice`, `score`, and `box` primitives.",
        mime_type="text/markdown",
    )
    def get_jev_guide() -> str:
        return JEV_QUICK_GUIDE

    @mcp.prompt(
        name="typesafe_ai_skill",
        description="Load the embedded TypeSafe Agent Skill (`SKILL.md`) for designing Jev workflows and questions.",
    )
    def typesafe_skill_prompt() -> str:
        return TYPESAFE_AI_SKILL

    @mcp.prompt(
        name="jev_usage_guide",
        description="Load the compact quick-reference guide for `jev_evaluate` primitives.",
    )
    def jev_usage_prompt() -> str:
        return JEV_QUICK_GUIDE

