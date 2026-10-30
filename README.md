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
| **`jev_box`** | Single bounding-box `box` question (`jev-latest`, Jev 1.14+) over local or base64 image `assets` (280..1568 px), returning normalized `top`, `bottom`, `left`, `right` coordinates and `confidence`. |
| **`jev_status`** | Safe diagnostic check returning masked API key status, key fingerprint, latency, and available Jev models (`jev-latest`, `jev-preview`). |
| **`jev://skill` / `jev://guide`** | MCP-adapted TypeSafe Agent Skill and quick-reference guide, with complete request examples, exposed as on-demand Resources & Prompts (`typesafe_ai_skill`, `jev_usage_guide`). Resource contents are not repeated in tool responses. |

### Images: local files or inline base64

All evaluation tools (`jev_evaluate`, `jev_noul`, `jev_choice`, `jev_score`, `jev_box`) accept images. For a local file, pass its **absolute path on the MCP server host**. The server uploads the bytes to TypeSafe using multipart; the local path is not sent in the API payload. Only select files intended for evaluation.

Example `jev_evaluate` arguments (replace the path with an existing image):

```json
{
  "state": {"photo": "2af4a6bd-2d30-4b70-b750-93739757e3e0"},
  "assets": {
    "2af4a6bd-2d30-4b70-b750-93739757e3e0": {"path": "D:/images/photo.png"}
  },
  "questions": {
    "present": {"type": "noul", "instructions": "Is there a red object in `photo`?"},
    "location": {"type": "box", "instructions": "the red object in `photo`"}
  }
}
```

Existing base64 callers remain supported: replace the asset value with `{"type": "image", "format": "png", "data_base64": "<raw_base64>"}`. Use `png`, `jpg`, or `jpeg`, standard padded base64 without whitespace or a `data:` prefix. Each asset needs exactly one source (`path` or `data_base64`). Remote URLs and raw multipart `part` names are not accepted by this MCP.

References can appear anywhere in string values in `state`, question `instructions`, and `criteria`, including nested JSON and the middle of a sentence. Images can also define Choice options, Score levels, and Noul true/false criteria. Object keys do not count as references. Prefer UUIDs to avoid accidental substring matches; every asset must be referenced. Shared images should be placed once in `state` and referred to by field name in questions.

To have Jev inspect pixels, attach each relevant image in `assets`; a path or filename in `state` does not upload it. Keep the mapping exact, for example `state={"photo":"img_1"}` with `assets={"img_1":{"path":"/absolute/photo.png"}}`. A deliberately supplied textual summary supports evaluation of that summary, rather than the unseen pixels. After a validation error or HTTP 400, check required arguments and reference names before retrying.

A box does not prove that an object exists. Ask about presence and use the location only when presence is adequately supported; presence and location may run in the same batch. Discard location when presence is absent or unresolved. Use neutral criteria, represent missing evidence with an unknown option or a sufficiency question, and choose a confidence threshold together with its verification or abstention fallback. Check that the final identifier matches the decision you actually support. The embedded guide and skill include complete image and ambiguous-evidence examples.

The server automatically enables the required `TypeSafe-Danger-Zone-Images: true` header. Images and Box are experimental. PNG/JPEG images must be 280..1568 pixels per side and at most 16 MiB each. The API enforces dimensions, still-image decoding, and the 32 MiB limits on request body, processed images, and expanded request content. Each repeated reference expands the image again. References may use at most 1024 UTF-8 bytes each and 65536 bytes combined. Box requires Jev 1.14 or newer; its default is `jev-latest`, and an explicitly selected model is preserved.

See the [official Images documentation](https://docs.typesafe.ai/images) and [Box contract](https://docs.typesafe.ai/primitives/box).

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
