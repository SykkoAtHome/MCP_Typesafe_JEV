# Agent behavior evaluations

This suite measures the current MCP instructions without modifying application code. The tasks, questions and images are synthetic. Expected answers, canonical questions and grading metadata never enter the agent context.

Run from `D:\code\MCP_Typesafe_JEV` in PowerShell:

```powershell
.venv/Scripts/python.exe -m evals.selfcheck
.venv/Scripts/python.exe -m evals.run --phase pilot --model gpt-6-luna --repeats 2 --concurrency 2 --output evals/results/my-pilot
.venv/Scripts/python.exe -m evals.run --phase full --model gpt-6-luna --repeats 2 --concurrency 2 --output evals/results/my-full
.venv/Scripts/python.exe -m evals.run --phase robustness --model gpt-6-luna --repeats 2 --concurrency 1 --arms descriptions guide skill --output evals/results/my-robustness
# Preserve strict baseline grades and publish documented format corrections separately:
.venv/Scripts/python.exe -m evals.adjudicate evals/results/my-full
# Resume an interrupted run with the same code, model, cases and configuration:
.venv/Scripts/python.exe -m evals.run --phase full --model gpt-6-luna --repeats 2 --concurrency 2 --output evals/results/my-full --resume
```

Each output directory must be new unless `--resume` is supplied. Resume appends missing/failed trials and preserves completed ones; the report selects the latest checkpoint while JSONL retains earlier attempts. Measurement identity checks reject changes to the model, effort, repeats, arms, manifest, application source or runner hashes. Network access and a supported, logged-in Codex CLI are required. The runner prefers the installed desktop app's bundled native executable, then the standard Windows npm location. `EVAL_CODEX_BINARY` overrides this choice. `CODEX_HOME` may identify the existing login; its configuration and history are not loaded. No automatic model substitution occurs.

The initial npm CLI 0.146 only advertised GPT-5.6 models and produced capacity/limit errors. The desktop app's bundled 0.165.0-alpha.1.2 correctly advertises GPT-6 models and successfully runs `gpt-6-luna`. Earlier attempts are preserved separately and must not be pooled with the current-runtime measurement.

The MCP child receives its key from `CredentialStore().resolve()` in its process environment. The key is never printed or stored in result artifacts. Codex receives a temporary copy of its existing login in an ignored runtime directory; cleanup runs on normal exit and initialization failures. An abrupt OS/process kill can require removal of `evals/.runtime/`. No credential value should be pasted into a command.

## What is measured

1. **Agent to MCP:** Every ordinary task runs in a new ephemeral app-server thread. Dynamic tools use the MCP server's actual tool names, descriptions and input schemas, with an actual stdio MCP client executing calls. MCP initialization instructions are supplied to every Jev arm. The agent can also read `jev://guide` or `jev://skill` on demand. Task arguments, responses, final answer, timing, RPC status and available token usage are preserved.
2. **Jev:** A separate track asks fixed, prewritten canonical questions for the 25 semantic/image/ambiguous cases. These questions are independent of agent behavior. Five deterministic cases have no canonical Jev call. Transport success and semantic outcome are reported separately.
3. **End to end:** The final answer is graded against the independently recorded expected outcome. Optional Jev omissions are accepted. A required case requests an independent external assessment without naming Jev. Deterministic cases penalize Jev use. Low-confidence and error traces require behavioral review rather than an automatic pass for using uncertainty words.

Four arms share the same model, reasoning effort, tasks, images, answer format and deterministic `compute` tool:

| Arm | Treatment |
|---|---|
| descriptions | MCP initialization instructions and verbatim tool descriptions/schemas |
| guide | Same, plus the harness reads `jev://guide` and supplies its content before the task |
| skill | Same, plus the harness reads `jev://skill` and supplies its content before the task |
| no_jev | No Jev tools, resources or server instructions |

Resource preloading estimates the effect of having read the resource. It does not estimate whether an agent would choose to read it spontaneously. On-demand reads in other arms are recorded and can reduce differences between treatments. Tool schemas are bridged as dynamic function tools, so this tests instruction comprehension and actual MCP calls, not native Codex MCP discovery UI behavior.

## Predeclared metrics

- Exact labels/booleans/collections must match the requested value. A valid JSON object alone never passes.
- Equivalent output representations are explicit in `expected.accepted_answers` or a declared case normalization. The initial baseline's strict grader had three format mismatches (numeric response IDs, null abstention and color capitalization); [ADJUDICATION.md](ADJUDICATION.md) defines their correction. Original traces/grades remain untouched; `adjudicated.jsonl` publishes both strict and corrected outcomes.
- A rubric score may differ by at most `0.50` on its original zero-based scale. Exact deterministic numeric computation uses tolerance `0`.
- Present-object localization passes at **IoU >= 0.50** against the manually recorded normalized box. Empty, invalid, nonfinite or displaced boxes fail. The literal reference coordinates are separate from the rasterizer; circle raster edges may differ by one inclusive pixel. Fixtures are synthetic and their coordinate annotations are authored by the suite author, not a separate human labeling panel.
- For absence/missing/conflicting evidence cases requesting abstention, the correct answer must accompany `abstain=true` and a null box. The absence strategy uses a presence question before localization because the box output contract has no explicit absent-object state.
- Confidence `<0.60` flags a trace for review. This threshold does not itself certify an answer, impose an unconditional refusal, or estimate calibration.
- An agent evaluation call is necessary only for cases marked `required`; status checks/resource reads do not satisfy this requirement. Calls on `unnecessary` cases are counted separately.
- Environment/turn failures are excluded from quality denominators and listed explicitly. Invalid argument, MCP transport and upstream model failures must be attributed from trace evidence rather than combined as instruction failures.

Two repeats and seed `20261029` are the defaults. Job order is shuffled deterministically; model inference is not seeded, so exact response reproduction is not promised. Concurrency affects timing and capacity. The current-runtime pilot/full runs use concurrency 2; old-runtime capacity diagnostics use 3 and 1. Repeat instability includes changes in answer, box, abstention and number of evaluation calls, with wording excluded.

## Artifacts and interpretation

`manifest.json` freezes inputs, oracles, acceptable strategies, Jev necessity and canonical questions before calls. `metadata.json` records configuration, thresholds, source hashes and git state. `mcp-tools.json`, `mcp-resources.json` and `mcp-initialize.json` preserve the measured instruction version. `agents.jsonl` and `canonical.jsonl` retain individual trials; `report.md` summarizes them. Only generated cases reach Jev; source hashes and git metadata remain local.

Agent token totals come from `thread/tokenUsage/updated`; Jev usage and resolved model come from tool responses. Missing usage is unavailable, not zero. The suite makes no monetary estimate. Wall times include resource loading, inference and round trips. Repeated input tokens across multi-call turns can be billed/served differently; inspect provider usage rather than treating every token as a unique context token.

The separate `robustness` phase injects a fixed inconclusive reply, a synthetic upstream error, and an unjustified high-confidence reply into requested external assessments. Replies are shaped to the actual primitive/question IDs chosen by the agent. These are controlled process probes, **not live Jev accuracy evidence**. The raw injected payload is retained for inspection. `absent-box-diagnostics.jsonl` separately records what a direct box request returns for the absent pink star; it is not pooled with presence-question accuracy.

The 30 cases are deliberately small and generated. Do not infer production accuracy, broad image competence or confidence calibration from this sample. A successful optional direct answer does not prove the tool instructions are adequate; required calls and trace reviews provide that evidence. The suite checks live behavior, not just HTTP/JSON contracts. Application tests remain in `tests/`; runner verification lives in `evals/selfcheck.py`.
