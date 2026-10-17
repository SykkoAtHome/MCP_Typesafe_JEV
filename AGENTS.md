# AGENTS.md — Repository Rules & Architecture (Single Source of Truth)

## 1. Purpose
`typesafe-jev-mcp` is a domain-agnostic Model Context Protocol (MCP) server implementing the **TypeSafe Jev** (`https://api.typesafe.ai/v1/systemone`) non-generative System One evaluation engine. It gives any agent in any harness (**Claude Code, Codex, Gemini CLI, Google Antigravity**) direct, low-latency (~100–150ms) access to Jev's calibrated primitives (`noul`, `choice`, `score`, `box`) and parallel speculative fan-out batches. How Jev is used (e.g. routing tasks to the agent's own models, intent classification, candidate ranking, or pre-execution guardrails) is decided entirely by the calling agent.

## 2. Layered Architecture
Strict dependency direction: `routes` → `services` → `repositories` → `db`.
Inside each layer, maintain one package per domain with an `__init__.py` facade:

- `src/typesafe_jev_mcp/routes/`:
  - `mcp/`: FastMCP tool handlers (`jev_evaluate`, `jev_choice`, `jev_score`, `jev_noul`, `jev_box`, `jev_status`), prompts/resources (`jev://skill`, `jev://guide`), and server bootstrap.
  - `cli/`: Command-line interface (`serve`, `auth`, `install`, `doctor`).
- `src/typesafe_jev_mcp/services/`:
  - `evaluation/`: Domain-agnostic System One evaluation service (`EvaluationService`: batch `evaluate`, `noul`, `choice`, `score`, optional composite weighting, and `check_health`).
  - `setup/`: Multi-harness installer and credential setup service (`InstallerService`).
- `src/typesafe_jev_mcp/repositories/`:
  - `jev/`: Async HTTP gateway (`JevGateway`) talking to `https://api.typesafe.ai/v1/systemone` and `/v1/models` with `429`/`529` retry-after backoff and zero-leak error redaction.
  - `harness/`: Configuration reader/writer (`HarnessConfigRepository`) for Claude Code, Codex CLI, Gemini CLI, and Antigravity.
- `src/typesafe_jev_mcp/db/`:
  - `credentials/`: `SecretApiKey` value object, secret redaction utilities, and multi-source `CredentialStore` (env var, secret file, `.env`, or OS user config).
  - `schemas/`: Pydantic models for TypeSafe System One primitives (`NoulQuestion`, `ChoiceQuestion`, `ScoreQuestion`, `BoxQuestion`, answers, and payload validators).

## 3. Coding & Security Standards
- **Python Environment**: Always use `.venv/Scripts/python.exe` with pytest flags `-p no:cacheprovider --basetemp=.pytest-tmp` and clean up `.pytest-tmp*` after running tests.
- **Secret Hygiene**:
  - Never hardcode real API keys in source files or committed tests.
  - Always pass API keys through `SecretApiKey` and scrub strings via `redact_secrets()` before raising errors or returning diagnostics.
- **Code Modularity**:
  - Keep functions under ~30 lines and files under ~300 lines.
  - Never swallow exceptions with bare `except:`; raise domain errors from `typesafe_jev_mcp.errors`.
  - Write comments and docstrings in English; keep only concise "why" comments without decorative banners.
