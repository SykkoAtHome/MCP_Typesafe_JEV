# Behavioral evaluation results

Model: `gpt-6-luna`; effort: `low`; repeats: 2.
Cases: 6. Source unchanged during run: True. Boundaries and limitations: see ../../README.md.
Raw agent attempts: 48; canonical attempts: 12. Tables use the latest checkpoint for each case/arm/repeat; earlier attempts remain in JSONL.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 12/12 | 12/12 | 0 | 12 | 0 | 0 | 4230 |
| guide | 12/12 | 11/12 | 0 | 12 | 0 | 0 | 4169 |
| skill | 12/12 | 11/12 | 0 | 12 | 0 | 0 | 4263 |
| no_jev | 12/12 | 10/12 | 0 | 0 | 0 | 0 | 2031 |

## Fixed-question Jev track

Successful transport: 12/12. Correct task outcomes: 12/12.

| Case | Correct / successful | Transport failures | IoU per repeat |
|---|---:|---:|---|
| text_rubric_priority | 2/2 | 0 | [] |
| image_color_shape_match | 2/2 | 0 | [] |
| image_compare_blue_count | 2/2 | 0 | [] |
| image_locate_blue_circle | 2/2 | 0 | [0.907, 0.907] |
| ambiguous_conflicting_reviewers | 2/2 | 0 | [] |
| ambiguous_absent_object | 2/2 | 0 | [] |

## Agent failures requiring attribution

- image_compare_blue_count / no_jev / r1: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / skill / r0: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / guide / r0: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / no_jev / r0: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.

## Repeat instability

Observed changes in answer/box/abstention/call count: 6 case-arm pairs.
- image_locate_blue_circle / guide
- text_rubric_priority / skill
- image_compare_blue_count / guide
- image_locate_blue_circle / descriptions
- image_compare_blue_count / skill
- image_locate_blue_circle / skill

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
