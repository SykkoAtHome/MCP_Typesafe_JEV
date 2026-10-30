# Agent behavior evaluation plan

**Goal:** Measure the existing 0.2.0 MCP instructions before proposing changes.

**Design:** A clean Codex app-server process runs ephemeral, independent threads. Its dynamic tools bridge verbatim MCP tool schemas to an actual stdio MCP client. Only generated inputs and images are available. Ordinary tasks never name Jev. A fixed canonical question track isolates Jev quality from agent question design. A separate replay track exercises low confidence and errors without claiming live Jev evidence.

**Decisions:** gpt-6-luna, low reasoning, bundled CLI 0.165.0-alpha.1.2; two repeats; four arms (descriptions, guide read, skill read, no Jev). Old npm CLI 0.146 runs are retained as environment diagnostics. All arms share a structured output schema. Predeclared IoU >= 0.50, absolute rubric error <= 0.50, low confidence < 0.60. Optional Jev omissions are not failures. Required external assessments need an evaluation call. Deterministic tasks must avoid Jev. No application instruction edits in this measurement.

## Execution

- [x] Snapshot source hashes, tool schemas, resources, configuration and existing diff metadata.
- [x] Implement isolated RPC/MCP bridge, safe deterministic tool, immutable case manifest, graders and JSONL traces.
- [x] Validate grader with known wrong answers/boxes and injected error/low-confidence responses.
- [x] Run six-case pilot twice in all four arms plus canonical Jev questions; save pilot results before expansion.
- [x] Freeze 30-case manifest and thresholds, then run all arms twice; preserve individual failures.
- [x] Review and simplify runner; run its checks outside tests/, then the application suite once at the end.
- [x] Produce a reproducible report with denominators, instability, limits and evidence-linked instruction proposals.

## Review focus

Never confuse valid JSON with correct localization; never treat missing tool calls as Jev failures; do not mark failed network/auth runs as quality misses; do not expose or persist credentials; never allow the agent access to expected answers or case metadata. Reading a guide is an explicit treatment, not a baseline instruction.
