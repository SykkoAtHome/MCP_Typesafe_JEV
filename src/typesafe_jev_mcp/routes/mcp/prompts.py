"""MCP resources and prompts embedding the official TypeSafe Jev Agent Skill (on-demand via Progressive Disclosure)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.mcpserver import MCPServer

TYPESAFE_AI_SKILL = """---
name: typesafe-ai
license: MIT
source: https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md
---

# Build & Evaluate with TypeSafe Jev (System One)

TypeSafe makes units of AI intelligence usable like programming primitives: small judgments you can compose into larger capabilities. Its **System One models** (`jev-latest`, `jev-preview`) return fast (~100-150ms), focused judgments that software and agents can consume directly. **Jev** understands natural language and structured JSON state and returns typed answers, calibrated probabilities, and confidence scores rather than generating prose.

Code (or the calling agent) owns the workflow and control flow; Jev supplies programmable common sense where semantic understanding is needed.

---

## 1. Using Jev via This MCP Server (Zero-Boilerplate Live Execution)

You have direct access to Jev through this MCP server's tools. Tool calls return **only** the compact evaluation JSON (this skill is never re-sent on tool calls):

- **`jev_evaluate` (Preferred — Speculative Fan-Out)**: Evaluate a batch of multiple independent questions (`noul`, `choice`, `score`, `box`) over `state` in a **single parallel HTTP call** (`POST /v1/systemone`). Supports optional `assets`, `weights` (composite score in `[0, 1]`), `confidence_threshold`, and `long_context`.
- **`jev_choice`**: Single categorical choice across 1..255 agent-defined options (`criteria`).
- **`jev_score`**: Single ordinal rubric evaluation across 2..10 ordered levels (`criteria`, index `0` lowest to `n-1` highest).
- **`jev_noul`**: Single binary probability evaluation returning `noul` $P(\\text{true}) \\in [0, 1]$, `verdict` (`bool`), and derived `confidence = |2*noul - 1|`.
- **`jev_box`**: Single image bounding-box evaluation (`jev-preview`) returning normalized `[0, 1]` edges (`top`, `bottom`, `left`, `right`) and `confidence`.
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
4. **`box` (Image Bounding Box, `jev-preview` / `jev-1.14.0`)**
   - Input: `{"type": "box", "instructions": "..."}` with `assets={"<ref_uuid>": {"type": "image", "format": "png", "data_base64": "<raw_base64>"}}` (each side 280..1568 px) and `<ref_uuid>` referenced inside `state` or `instructions`.
   - Output: normalized `[0, 1]` coordinates `{"top", "bottom", "left", "right"}` and `confidence`.

---

## 3. Core Architectural Patterns

- **Speculative Fan-Out**: Every question in `jev_evaluate` is evaluated independently and in parallel — one question's result never leaks into or biases another question. Pack all relevant and speculative questions into a single `jev_evaluate` call instead of making sequential requests.
- **Agent-Controlled Routing (Models, Subagents, Tools)**: When deciding which of your own harness models (e.g. `haiku`/`sonnet`/`opus` in Claude Code, `flash_lite`/`flash`/`pro` in Gemini/Antigravity, or Codex profiles), tools, or subagents to use, pass **your own available candidates** in `criteria` of a `choice` question alongside atomic `score`/`noul` risk questions.
- **Confidence-Gated Routing**: Use `confidence` as a second decision axis. Act automatically when confidence is high; escalate to a stronger model, deeper verification, or human review when confidence falls below your threshold.
- **Composite Scoring**: Decompose subjective quality/risk into 3–6 narrow `score` or `noul` questions and pass `weights` to `jev_evaluate` to compute a deterministic weighted score in `[0.0, 1.0]`.
- **Parallel Candidate Reranking**: Evaluate $N$ candidate files, diffs, or plans in one `jev_evaluate` call (`cand_0`, `cand_1`, ...) and sort by `score` or `noul`.

---

## 4. State & Question Design Rules

1. **Keep deterministic rules in code**: Do not ask Jev to do arithmetic, regex matching, date math, or exact string lookups. Compute those in code and pass only semantic judgments to Jev.
2. **Send only relevant context in `state`**: Avoid dumping unrelated files into `state`. Use structured nested JSON and point questions at specific fields using backticked dot-paths in `instructions` (e.g. ``Does `ticket.message` qualify under `policy.refund_rules`?``).
3. **If you only need the best option, pick the highest probability/choice**: Do not add arbitrary confidence thresholds everywhere unless you have a fallback/escalation path when confidence is low.
4. **Live Documentation Index (when building SDK integrations)**:
   - Docs index: `https://docs.typesafe.ai/llms.txt` (append `.md` to any doc path for clean Markdown, e.g. `https://docs.typesafe.ai/primitives.md`, `https://docs.typesafe.ai/confidence.md`, `https://docs.typesafe.ai/patterns.md`, `https://docs.typesafe.ai/api.md`).
"""

JEV_QUICK_GUIDE = """# TypeSafe Jev — Quick Reference (`jev://guide`)

- **Batch evaluation (`jev_evaluate`)**: Send `state` (JSON/str) + `questions` (`dict[qid, spec]`) in a single parallel call (~100ms).
- **Primitives**:
  - `noul`: `{"type": "noul", "instructions": "...", "criteria": {"true": "...", "false": "..."}}` -> `noul` in `[0, 1]`, `verdict`, `confidence = |2p - 1|`.
  - `choice`: `{"type": "choice", "instructions": "...", "criteria": {"k1": "desc1", "k2": "desc2"}}` (1..255 options) -> `choice`, `probabilities`, `confidence`.
  - `score`: `{"type": "score", "instructions": "...", "criteria": ["lvl0", "lvl1", ...]}` (2..10 ordered levels) -> `score`, `normalized`, `confidence`.
  - `box`: `{"type": "box", "instructions": "..."}` (`model="jev-preview"`, `assets={"<ref>": {"type": "image", "format": "png", "data_base64": "..."}}`) -> `box` (`top`, `bottom`, `left`, `right`), `confidence`.
- **Full official TypeSafe Agent Skill**: Read MCP resource `jev://skill` or invoke prompt `typesafe_ai_skill`.
"""


def register_prompts_and_resources(mcp: MCPServer) -> None:
    """Register on-demand MCP resources (`jev://skill`, `jev://guide`) and prompts."""

    @mcp.resource(
        "jev://skill",
        name="TypeSafe Official Agent Skill (SKILL.md)",
        description=(
            "Complete TypeSafe System One (Jev) agent skill: primitives, parallel fan-out, "
            "confidence-gated routing, composite scoring, state design, and live doc references."
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

