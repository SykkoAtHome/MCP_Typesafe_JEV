# Behavioral evaluation results

Model: `gpt-6-luna`; effort: `low`; repeats: 2.
Cases: 6. Source unchanged during run: True. Boundaries and limitations: see ../../README.md.
Raw agent attempts: 48; canonical attempts: 10. Tables use the latest checkpoint for each case/arm/repeat; earlier attempts remain in JSONL.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 12/12 | 12/12 | 0 | 10 | 0 | 0 | 4507 |
| guide | 12/12 | 12/12 | 0 | 11 | 0 | 0 | 4274 |
| skill | 12/12 | 12/12 | 0 | 10 | 0 | 0 | 4536 |
| no_jev | 12/12 | 12/12 | 0 | 0 | 0 | 0 | 2667 |

## Fixed-question Jev track

Successful transport: 10/10. Correct task outcomes: 10/10.

| Case | Correct / successful | Transport failures | IoU per repeat |
|---|---:|---:|---|
| text_sentiment_mixed | 2/2 | 0 | [] |
| text_rubric_priority | 2/2 | 0 | [] |
| image_count_green_circles | 2/2 | 0 | [] |
| image_locate_blue_circle | 2/2 | 0 | [0.907, 0.907] |
| ambiguous_conflicting_reviewers | 2/2 | 0 | [] |

## Agent failures requiring attribution


## Repeat instability

Observed changes in answer/box/abstention/call count: 2 case-arm pairs.
- image_locate_blue_circle / guide
- text_rubric_priority / skill

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
