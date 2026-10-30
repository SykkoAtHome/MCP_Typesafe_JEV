# Behavioral evaluation results

Model: `gpt-6-luna`; effort: `low`; repeats: 2.
Cases: 1. Source unchanged during run: True. Boundaries and limitations: see ../../README.md.
Raw agent attempts: 8; canonical attempts: 2. Tables use the latest checkpoint for each case/arm/repeat; earlier attempts remain in JSONL.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 2/2 | 1/2 | 0 | 2 | 0 | 0 | 5508 |
| guide | 2/2 | 2/2 | 0 | 2 | 0 | 0 | 4299 |
| skill | 2/2 | 1/2 | 0 | 1 | 0 | 0 | 3003 |
| no_jev | 2/2 | 0/2 | 0 | 0 | 0 | 0 | 2098 |

## Fixed-question Jev track

Successful transport: 2/2. Correct task outcomes: 2/2.

| Case | Correct / successful | Transport failures | IoU per repeat |
|---|---:|---:|---|
| image_compare_blue_count | 2/2 | 0 | [] |

## Agent failures requiring attribution

- image_compare_blue_count / descriptions / r1: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / skill / r1: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / no_jev / r0: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / no_jev / r1: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.

## Repeat instability

Observed changes in answer/box/abstention/call count: 2 case-arm pairs.
- image_compare_blue_count / descriptions
- image_compare_blue_count / skill

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
