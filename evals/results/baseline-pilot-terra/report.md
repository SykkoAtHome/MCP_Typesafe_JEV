# Behavioral evaluation results

Model: `gpt-5.6-terra`; effort: `low`; repeats: 2.
Cases: 6. Source unchanged during run: True. Boundaries and limitations: see ../README.md.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 10/12 | 9/10 | 2 | 5 | 0 | 0 | 4825 |
| guide | 11/12 | 11/11 | 1 | 8 | 0 | 0 | 6148 |
| skill | 7/12 | 7/7 | 5 | 6 | 0 | 0 | 8473 |
| no_jev | 10/12 | 8/10 | 2 | 0 | 0 | 0 | 3952 |

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

- image_locate_blue_circle / no_jev / r0: outcome={'passed': False, 'iou': 0.0}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- ambiguous_conflicting_reviewers / no_jev / r1: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': True, 'low_confidence_or_error_handling': 'not_exercised'}.
- ambiguous_conflicting_reviewers / descriptions / r0: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': True, 'low_confidence_or_error_handling': 'not_exercised'}.
- text_sentiment_mixed / no_jev / r1: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / skill / r1: environment or turn failure; inspect trace.
- image_count_green_circles / no_jev / r0: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / skill / r0: environment or turn failure; inspect trace.
- text_rubric_priority / guide / r1: environment or turn failure; inspect trace.
- deterministic_sort / skill / r0: environment or turn failure; inspect trace.
- ambiguous_conflicting_reviewers / descriptions / r1: environment or turn failure; inspect trace.
- image_locate_blue_circle / skill / r0: environment or turn failure; inspect trace.
- text_rubric_priority / descriptions / r1: environment or turn failure; inspect trace.
- image_count_green_circles / skill / r1: environment or turn failure; inspect trace.

## Repeat instability

Observed changes in answer/box/abstention/call count: 5 case-arm pairs.
- text_sentiment_mixed / descriptions
- image_locate_blue_circle / no_jev
- ambiguous_conflicting_reviewers / no_jev
- image_count_green_circles / descriptions
- ambiguous_conflicting_reviewers / guide

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
