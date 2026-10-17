# TypeSafe JEV MCP Server (`typesafe-jev-mcp`)

Domain-agnostic Model Context Protocol (MCP) server for **TypeSafe Jev (System One)** (`https://docs.typesafe.ai`).

Exposes Jev's non-generative, calibrated evaluation primitives (`noul`, `choice`, `score`, `box`) and parallel **Speculative Fan-Out** (`POST /v1/systemone`) to any AI coding agent in **Claude Code, OpenAI Codex, Gemini CLI, and Google Antigravity**.

How Jev is used — whether for routing tasks across the agent's own models, classifying intent, reranking candidate files/plans in parallel, or gating risky actions — is decided entirely by the calling agent.

---

## 1. Quick Installation

```powershell
# 1. Create virtualenv and install package
uv venv .venv
.venv\Scripts\python.exe -m pip install -e .

# 2. Save your TypeSafe API key securely in your OS user profile (hidden prompt)
.venv\Scripts\typesafe-jev-mcp.exe auth set-key

# 3. Verify connectivity with api.typesafe.ai
.venv\Scripts\typesafe-jev-mcp.exe doctor

# 4. Auto-configure your harness (claude-code | codex | gemini | antigravity | all)
.venv\Scripts\typesafe-jev-mcp.exe install --harness all
```

---

## 2. Secure API Key Consumption

The server never exposes raw API keys to the LLM context, logs, or error tracebacks (`SecretApiKey` masks keys as `apikey_0000****...****0000`, and `redact_secrets()` scrubs all exception messages).

Credentials are resolved in the following order:
1. **`TYPESAFE_API_KEY`** environment variable (passed via harness `env` config or shell).
2. **`TYPESAFE_API_KEY_FILE`** environment variable pointing to a file containing the key.
3. **Local `.env`** file (ignored by git).
4. **OS User Credential Store** (`%APPDATA%\typesafe-jev-mcp\credentials.json` on Windows, `~/.config/typesafe-jev-mcp/credentials.json` with `0600` permissions on Linux/macOS), created via:
   ```powershell
   typesafe-jev-mcp auth set-key
   ```
   Using `auth set-key` means you do **not** need to put your plaintext API key inside `.mcp.json`, `config.toml`, or `settings.json`.

---

## 3. Multi-Harness Configuration

You can auto-install into any harness via `typesafe-jev-mcp install --harness <name>`, or add the snippet manually:

### Claude Code (`~/.claude.json` or `.mcp.json`)
```json
{
  "mcpServers": {
    "typesafe-jev": {
      "command": "D:/code/MCP_Typesafe_JEV/.venv/Scripts/python.exe",
      "args": ["-m", "typesafe_jev_mcp", "serve"]
    }
  }
}
```

### OpenAI Codex (`~/.codex/config.toml`)
```toml
[mcp_servers.typesafe-jev]
command = "D:/code/MCP_Typesafe_JEV/.venv/Scripts/python.exe"
args = ["-m", "typesafe_jev_mcp", "serve"]
```

### Gemini CLI (`~/.gemini/settings.json`) & Google Antigravity (`~/.gemini/antigravity/mcp_config.json`)
```json
{
  "mcpServers": {
    "typesafe-jev": {
      "command": "D:/code/MCP_Typesafe_JEV/.venv/Scripts/python.exe",
      "args": ["-m", "typesafe_jev_mcp", "serve"]
    }
  }
}
```

---

## 4. Exposed MCP Tools & Embedded Skill (Progressive Disclosure)

| Tool / Resource | Description |
| :--- | :--- |
| **`jev_evaluate`** | Parallel batch evaluation (`POST /v1/systemone`). Evaluates any dictionary of `questions` (`noul`, `choice`, `score`, `box`) against `state` in a single ~100–150ms call. Supports optional `assets`, `weights` (for composite scoring), `confidence_threshold`, and `long_context`. |
| **`jev_choice`** | Single categorical `choice` question (picks 1 of up to 255 agent-supplied options in `criteria`, returning `choice`, `probabilities`, and `confidence`). |
| **`jev_score`** | Single ordinal `score` rubric question (2 to 10 ordered rubric levels in `criteria`, returning `score`, `normalized` in `[0, 1]`, `probabilities`, `legend`, and `confidence`). |
| **`jev_noul`** | Single binary `noul` probability question (returning `noul` in `[0, 1]`, `verdict`, and derived `confidence = \|2p - 1\|`). |
| **`jev_box`** | Single bounding-box `box` question (`jev-preview`) over base64 image `assets` (280..1568 px), returning normalized `top`, `bottom`, `left`, `right` coordinates and `confidence`. |
| **`jev_status`** | Safe diagnostic check returning masked API key status, key fingerprint, latency, and available Jev models (`jev-latest`, `jev-preview`). |
| **`jev://skill` / `jev://guide`** | Embedded official TypeSafe Agent Skill (`SKILL.md`) and quick-reference guide exposed as on-demand MCP Resources & Prompts (`typesafe_ai_skill`, `jev_usage_guide`) with zero token overhead on tool calls. |

### Example: Agent Routing a Task Across Its Own Models via `jev_evaluate`

```json
{
  "state": {
    "task": "Rename the local variable `usr_id` to `user_id` inside `format_profile()`."
  },
  "questions": {
    "selected_model": {
      "type": "choice",
      "instructions": "Which model from criteria is most cost-effective for `task`?",
      "criteria": {
        "haiku": "Fast, cheap model for mechanical edits, search, and simple formatting",
        "sonnet": "Balanced model for standard feature implementation and bugfixes",
        "opus": "Deep reasoning flagship model for architecture, concurrency, and subtle bugs"
      }
    },
    "has_security_risk": {
      "type": "noul",
      "instructions": "Does `task` touch authentication, secrets, or concurrency locks?"
    }
  }
}
```
