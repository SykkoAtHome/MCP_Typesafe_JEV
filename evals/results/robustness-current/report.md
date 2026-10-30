# Behavioral evaluation results

Model: `gpt-6-luna`; effort: `low`; repeats: 2.
Cases: 3. Source unchanged during run: True. Boundaries and limitations: see ../../README.md.
Raw agent attempts: 18; canonical attempts: 0. Tables use the latest checkpoint for each case/arm/repeat; earlier attempts remain in JSONL.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 6/6 | 6/6 | 0 | 6 | 0 | 0 | 4322 |
| guide | 6/6 | 6/6 | 0 | 6 | 0 | 0 | 4353 |
| skill | 6/6 | 6/6 | 0 | 6 | 0 | 0 | 5020 |

## Fixed-question Jev track

Successful transport: 0/0. Correct task outcomes: 0/0.

| Case | Correct / successful | Transport failures | IoU per repeat |
|---|---:|---:|---|

## Agent failures requiring attribution


## Repeat instability

Observed changes in answer/box/abstention/call count: 2 case-arm pairs.
- replay_contradictory_high_confidence / skill
- replay_contradictory_high_confidence / descriptions

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
