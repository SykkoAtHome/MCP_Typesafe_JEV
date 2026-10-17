# MEMORY.md

## STATE
- **Project**: `typesafe-jev-mcp` — domain-agnostic, cross-harness MCP server implementing the TypeSafe Jev (`jev-latest` / `jev-preview`) System One evaluation API (`https://docs.typesafe.ai`).
- **Status**: Implemented and verified with unit tests and live API integration tests.
- **Supported Harnesses**: Claude Code (`.mcp.json` / `~/.claude.json`), OpenAI Codex (`~/.codex/config.toml`), Gemini CLI (`~/.gemini/settings.json`), and Google Antigravity (`~/.gemini/antigravity/mcp_config.json`).
- **Core MCP Tools**:
  - `jev_evaluate`: Parallel speculative fan-out (`POST /v1/systemone`) over any JSON/text `state` and dictionary of `questions` (`noul`, `choice`, `score`, `box`), with optional `assets`, `weights` for composite scoring, `confidence_threshold`, and `long_context`.
  - `jev_choice`: Single categorical choice across 1..255 agent-supplied options (`criteria`).
  - `jev_score`: Single ordinal rubric evaluation across 2..10 ordered levels (`criteria`).
  - `jev_noul`: Single binary probability evaluation returning $P(\text{true}) \in [0, 1]$, `verdict`, and derived confidence $|2p - 1|$.
  - `jev_box`: Single bounding-box evaluation (`jev-preview`) over base64 image `assets` returning normalized `top`, `bottom`, `left`, `right` coordinates and `confidence`.
  - `jev_status`: Verifies credential status (masked key & fingerprint only) and live `/v1/models` connectivity.
- **Embedded Official Skill (Progressive Disclosure)**:
  - On-demand MCP Resource `jev://skill` (and `jev://guide`) + Prompt `typesafe_ai_skill` (and `jev_usage_guide`) in `routes.mcp.prompts`, loaded only when requested by the agent without adding token overhead to tool calls.


## Architecture
- Strict layered dependency order: `routes` → `services` → `repositories` → `db`.
- Credential lookup priority in `db.credentials.store.CredentialStore`:
  1. Explicit key argument (for isolated tests)
  2. `TYPESAFE_API_KEY` environment variable
  3. `TYPESAFE_API_KEY_FILE` path pointing to a single-line secret file
  4. Local `.env` file (`TYPESAFE_API_KEY=...`)
  5. User-scoped OS config (`%APPDATA%/typesafe-jev-mcp/credentials.json` on Windows, `~/.config/typesafe-jev-mcp/credentials.json` on POSIX, `0600` permissions).

## Traps
- **Noul Confidence**: The TypeSafe `/v1/systemone` endpoint returns `confidence` natively for `choice`, `score`, and `box` answers, but **not** for `noul` answers (`{"type": "noul", "noul": 0.95}`). Always compute derived Noul confidence in code as $|2p - 1|$ where $p$ is the `noul` probability.
- **Image Assets & Box Questions**: Images in `assets` must be PNG/JPEG with width and height between `280` and `1568` pixels each (raw `data_base64` without `data:` prefix), every asset key must be referenced in `state`/`instructions`/`criteria`, and `TypeSafe-Danger-Zone-Images: true` header is required (`box` also requires `jev-preview` / `jev-1.14.0` and returns `{"top", "bottom", "left", "right"}`).
- **Numeric Constraints**: `/v1/systemone` rejects `NaN` and `Infinity` anywhere in `state` and limits JSON nesting depth to 64 levels. Validate payloads in `db.schemas.primitives` before sending HTTP requests.
- **Secret Redaction**: Never interpolate `SecretApiKey.get_secret_value()` into logs, exception messages, or MCP tool responses. Always use `str(secret_key)` (which masks the middle) and pass error text through `redact_secrets()`.
