# Behavioral evaluation results

Model: `gpt-5.6-luna`; effort: `low`; repeats: 2.
Cases: 6. Source unchanged during run: True. Boundaries and limitations: see ../README.md.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 1/12 | 1/1 | 11 | 0 | 0 | 2 | 4703 |
| guide | 2/12 | 2/2 | 10 | 0 | 0 | 2 | 4266 |
| skill | 1/12 | 1/1 | 11 | 0 | 0 | 2 | 3391 |
| no_jev | 4/12 | 4/4 | 8 | 0 | 0 | 0 | 3022 |

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

- image_count_green_circles / no_jev / r1: environment or turn failure; inspect trace.
- image_locate_blue_circle / guide / r1: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / no_jev / r0: environment or turn failure; inspect trace.
- text_rubric_priority / descriptions / r0: environment or turn failure; inspect trace.
- text_sentiment_mixed / guide / r0: environment or turn failure; inspect trace.
- text_sentiment_mixed / skill / r1: environment or turn failure; inspect trace.
- image_locate_blue_circle / guide / r0: environment or turn failure; inspect trace.
- image_count_green_circles / guide / r1: environment or turn failure; inspect trace.
- image_locate_blue_circle / descriptions / r1: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / no_jev / r1: environment or turn failure; inspect trace.
- image_locate_blue_circle / descriptions / r0: environment or turn failure; inspect trace.
- image_count_green_circles / descriptions / r1: environment or turn failure; inspect trace.
- text_rubric_priority / skill / r0: environment or turn failure; inspect trace.
- text_rubric_priority / skill / r1: environment or turn failure; inspect trace.
- image_count_green_circles / skill / r0: environment or turn failure; inspect trace.
- deterministic_sort / descriptions / r0: environment or turn failure; inspect trace.
- text_sentiment_mixed / skill / r0: environment or turn failure; inspect trace.
- text_rubric_priority / no_jev / r0: environment or turn failure; inspect trace.
- text_sentiment_mixed / descriptions / r1: environment or turn failure; inspect trace.
- text_sentiment_mixed / no_jev / r0: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / guide / r1: environment or turn failure; inspect trace.
- text_rubric_priority / no_jev / r1: environment or turn failure; inspect trace.
- image_count_green_circles / descriptions / r0: environment or turn failure; inspect trace.
- deterministic_sort / descriptions / r1: environment or turn failure; inspect trace.
- deterministic_sort / guide / r1: environment or turn failure; inspect trace.
- image_locate_blue_circle / skill / r1: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / descriptions / r0: environment or turn failure; inspect trace.
- image_count_green_circles / guide / r0: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / guide / r0: environment or turn failure; inspect trace.
- text_rubric_priority / guide / r0: environment or turn failure; inspect trace.
- text_sentiment_mixed / no_jev / r1: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / skill / r1: environment or turn failure; inspect trace.
- image_count_green_circles / no_jev / r0: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / skill / r0: environment or turn failure; inspect trace.
- text_rubric_priority / guide / r1: environment or turn failure; inspect trace.
- deterministic_sort / skill / r0: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / descriptions / r1: environment or turn failure; inspect trace.
- text_rubric_priority / descriptions / r1: environment or turn failure; inspect trace.
- image_count_green_circles / skill / r1: environment or turn failure; inspect trace.
- image_locate_blue_circle / skill / r0: environment or turn failure; inspect trace.

## Repeat instability

Observed changes in answer/box/abstention/call count: 0 case-arm pairs.

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
