# MEMORY.md

## STATE
- **Project**: `typesafe-jev-mcp` — domain-agnostic, cross-harness MCP server implementing the TypeSafe Jev (`jev-latest` / `jev-preview`) System One evaluation API (`https://docs.typesafe.ai`).
- **Status**: Version 0.2.0; 58 deterministic tests pass after the MCP guidance update. The 7 existing live API tests passed before that update; newer live agent checks are stored separately in `evals/results/`. Local multipart uploads were also checked against Jev 1.14. Live tests can use `CredentialStore` resolution by setting `TYPESAFE_API_KEY` only inside the test process.
- **Supported Harnesses**: Claude Code (`.mcp.json` / `~/.claude.json`), OpenAI Codex (`~/.codex/config.toml`), Gemini CLI (`~/.gemini/settings.json`), and Google Antigravity (`~/.gemini/config/mcp_config.json`).
- **Core MCP Tools**:
  - `jev_evaluate`: Parallel speculative fan-out (`POST /v1/systemone`) over any JSON/text `state` and dictionary of `questions` (`noul`, `choice`, `score`, `box`), with optional `assets`, `weights` for composite scoring, `confidence_threshold`, and `long_context`.
  - `jev_choice`: Single categorical choice across 1..255 agent-supplied options (`criteria`).
  - `jev_score`: Single ordinal rubric evaluation across 2..10 ordered levels (`criteria`).
  - `jev_noul`: Single binary probability evaluation returning $P(\text{true}) \in [0, 1]$, `verdict`, and derived confidence $|2p - 1|$.
  - `jev_box`: Single bounding-box evaluation (`jev-latest`, Jev 1.14+) over local or base64 image `assets` returning normalized `top`, `bottom`, `left`, `right` coordinates and `confidence`. Explicit model selections are preserved.
  - All evaluation tools accept `assets={ref: {"path": "absolute/local/image.png"}}` (multipart upload to TypeSafe) or `{ref: {"format": "png", "data_base64": "..."}}` (JSON). References work in nested state, instructions, and criteria.
  - `jev_status`: Verifies credential status (masked key & fingerprint only) and live `/v1/models` connectivity.
- **Embedded Agent Guidance (Progressive Disclosure)**:
  - On-demand MCP Resource `jev://skill` (and `jev://guide`) + Prompt `typesafe_ai_skill` (and `jev_usage_guide`) in `routes.mcp.prompts`; the upstream TypeSafe skill is marked as an MCP adaptation. Resource contents are not repeated in tool responses.
  - Shared `routes.mcp.guidance` supplies exact image-reference examples, neutral criteria, unknown/evidence handling, confidence fallbacks, and presence-aware box use. API signatures and transport are unchanged.
- **Agent Evaluations**: `evals/` contains the fresh-context runner and preserved 30-case baseline (4 arms, 2 repeats). `evals/GUIDANCE_UPDATE.md` records applied instruction changes and separate follow-up measurements; `evals/README.md` has runner commands. Output-format adjudication is explicit and raw baseline grades remain immutable.


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
- **Image Assets & Box Questions**: Experimental PNG/JPEG inputs require 280..1568 pixels per side and <=16 MiB per file. The API enforces dimensions and 32 MiB body/processed-image/expanded-request limits. The MCP validates source/format/base64 and references' UTF-8 lengths, reads absolute local paths via the gateway, and automatically adds `TypeSafe-Danger-Zone-Images: true`. Every asset key must occur in string values in `state`/`instructions`/`criteria`; object keys do not count. Box requires Jev 1.14+ (`jev-latest` supported) and returns `{"top", "bottom", "left", "right"}`. Official contract: https://docs.typesafe.ai/images.
- **Numeric Constraints**: `/v1/systemone` rejects `NaN` and `Infinity` anywhere in `state` and limits JSON nesting depth to 64 levels. Validate payloads in `db.schemas.primitives` before sending HTTP requests.
- **Secret Redaction**: Never interpolate `SecretApiKey.get_secret_value()` into logs, exception messages, or MCP tool responses. Always use `str(secret_key)` (which masks the middle) and pass error text through `redact_secrets()`.
