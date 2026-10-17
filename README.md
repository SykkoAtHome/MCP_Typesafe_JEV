# TypeSafe JEV MCP Server (`typesafe-jev-mcp`)

Domain-agnostic Model Context Protocol (MCP) server for **TypeSafe Jev (System One)** (`https://docs.typesafe.ai`).

Exposes Jev's non-generative, calibrated evaluation primitives (`noul`, `choice`, `score`, `box`) and parallel **Speculative Fan-Out** (`POST /v1/systemone`) to any AI coding agent in **Claude Code, OpenAI Codex, Gemini CLI, and Google Antigravity**.

How Jev is used — whether for routing tasks across the agent's own models, classifying intent, reranking candidate files/plans in parallel, or gating risky actions — is decided entirely by the calling agent.

---

## 1. Agent Self-Installation Playbook (Single Source of Truth — SSOT)

> **CRITICAL SSOT RULE FOR AGENTS**:
> The directory where the user cloned this repository (`<SSOT_DIR>`, e.g. `D:\code\MCP_Typesafe_JEV`) is the **Single Source of Truth (SSOT)** for every harness on the machine.
> - **NEVER** clone duplicate copies of this repository into other project workspaces or into harness config folders (`~/.claude`, `~/.codex`, `~/.gemini`).
> - **NEVER** copy source files across harnesses.
> - `pip install -e <SSOT_DIR>` links `<SSOT_DIR>\.venv` directly to `<SSOT_DIR>\src\typesafe_jev_mcp` in-place, and `typesafe-jev-mcp install --harness ...` automatically resolves `sys.executable` inside `<SSOT_DIR>\.venv` and writes a lightweight command pointer into each harness's config file. Any edit or `git pull` inside `<SSOT_DIR>` immediately updates all harnesses at once.

### Step 1: Locate (or Clone Once) the Canonical `<SSOT_DIR>` & Install Editable `.venv`

**Windows (PowerShell):**
```powershell
$SSOT_DIR = "D:\code\MCP_Typesafe_JEV" # Or the path where the user cloned this repo
if (-not (Test-Path "$SSOT_DIR\.git")) {
    git clone https://github.com/SykkoAtHome/MCP_Typesafe_JEV.git "$SSOT_DIR"
} else {
    git -C "$SSOT_DIR" pull --ff-only
}

if (-not (Test-Path "$SSOT_DIR\.venv\Scripts\python.exe")) {
    uv venv "$SSOT_DIR\.venv"
}
# Editable install (-e) links directly to $SSOT_DIR\src\typesafe_jev_mcp without copying files
& "$SSOT_DIR\.venv\Scripts\python.exe" -m pip install -e "$SSOT_DIR"
```

**macOS / Linux (Bash):**
```bash
SSOT_DIR="${SSOT_DIR:-$HOME/code/MCP_Typesafe_JEV}" # Or the path where the user cloned this repo
if [ ! -d "$SSOT_DIR/.git" ]; then
    git clone https://github.com/SykkoAtHome/MCP_Typesafe_JEV.git "$SSOT_DIR"
else
    git -C "$SSOT_DIR" pull --ff-only
fi

[ -x "$SSOT_DIR/.venv/bin/python" ] || uv venv "$SSOT_DIR/.venv"
"$SSOT_DIR/.venv/bin/python" -m pip install -e "$SSOT_DIR"
```

---

### Step 2: Check API Key Readiness (Never Read or Echo the Raw Key)

Run the built-in diagnostic command from `<SSOT_DIR>`:

```powershell
# Windows
& "$SSOT_DIR\.venv\Scripts\typesafe-jev-mcp.exe" doctor

# macOS / Linux
"$SSOT_DIR/.venv/bin/typesafe-jev-mcp" doctor
```

- **If `"configured": true` and `"upstream_ok": true`**: The user's TypeSafe API key is already stored in the OS user profile (`%APPDATA%\typesafe-jev-mcp\credentials.json` on Windows or `~/.config/typesafe-jev-mcp/credentials.json` on POSIX). **Proceed directly to Step 3 without asking the user for a key.**
- **If `"configured": false`**: Ask the user to run the interactive hidden-input command once in their terminal (or pass `--api-key` if they provided one):
  ```powershell
  & "$SSOT_DIR\.venv\Scripts\typesafe-jev-mcp.exe" auth set-key
  ```

---

### Step 3: Register the SSOT Pointer in Your Harness

When you run `typesafe-jev-mcp install` from `<SSOT_DIR>\.venv`, it automatically records the exact absolute path to `<SSOT_DIR>\.venv` in the target harness configuration (zero file copying):

#### A. Claude Code (`~/.claude.json` or project `.mcp.json`)
- **Automated installer (User scope `~/.claude.json`):**
  ```powershell
  & "$SSOT_DIR\.venv\Scripts\typesafe-jev-mcp.exe" install --harness claude-code --scope user
  ```
- **Or via native `claude` CLI:**
  ```powershell
  claude mcp add --scope user typesafe-jev -- "$SSOT_DIR/.venv/Scripts/python.exe" -m typesafe_jev_mcp serve
  ```

#### B. Google Antigravity (`~/.gemini/config/mcp_config.json`)
- **Automated installer (safely merges into `~/.gemini/config/mcp_config.json` without overwriting other MCP servers):**
  ```powershell
  & "$SSOT_DIR\.venv\Scripts\typesafe-jev-mcp.exe" install --harness antigravity
  ```

#### C. OpenAI Codex (`~/.codex/config.toml`)
- **Automated installer (safely updates `[mcp_servers.typesafe-jev]` in `~/.codex/config.toml`):**
  ```powershell
  & "$SSOT_DIR\.venv\Scripts\typesafe-jev-mcp.exe" install --harness codex
  ```

#### D. Install Pointer into All Harnesses at Once (Claude Code + Antigravity + Codex + Gemini CLI)
```powershell
& "$SSOT_DIR\.venv\Scripts\typesafe-jev-mcp.exe" install --harness all
```

---

### Step 4: How the Agent Should Use `typesafe-jev` After Connecting

1. **Verify connection**: Call the MCP tool `jev_status` (`verify_upstream=true`).
2. **Load the embedded official TypeSafe Agent Skill on demand (Progressive Disclosure)**:
   - Read the MCP resource **`jev://skill`** (or compact cheatsheet **`jev://guide`**) — or invoke the MCP prompt **`typesafe_ai_skill`** — **once** when designing your first Jev evaluation in a session.
   - Tool calls (`jev_evaluate`, `jev_choice`, `jev_score`, `jev_noul`, `jev_box`) never re-send the skill text, keeping token usage minimal.
3. **Prefer `jev_evaluate` (Speculative Fan-Out)**: Pack multiple independent `noul`, `choice`, `score`, or `box` questions into a single `jev_evaluate` call (~100–150ms).

---

## 2. Secure API Key Resolution Order

The server never exposes raw API keys to the LLM context, logs, or error tracebacks (`SecretApiKey` masks keys as `apikey_0000****...****0000`, and `redact_secrets()` scrubs all exception messages).

Credentials are resolved in the following order:
1. **`TYPESAFE_API_KEY`** environment variable (passed via harness `env` config or shell).
2. **`TYPESAFE_API_KEY_FILE`** environment variable pointing to a file containing the key.
3. **Local `.env`** file (ignored by git).
4. **OS User Credential Store** (`%APPDATA%\typesafe-jev-mcp\credentials.json` on Windows, `~/.config/typesafe-jev-mcp/credentials.json` with `0600` permissions on Linux/macOS), created via `typesafe-jev-mcp auth set-key`. Using `auth set-key` means you do **not** need to put your plaintext API key inside `.mcp.json`, `config.toml`, or `mcp_config.json`.

---

## 3. Exposed MCP Tools & Embedded Skill (Progressive Disclosure)

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
