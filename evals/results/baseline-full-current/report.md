# Behavioral evaluation results

Model: `gpt-6-luna`; effort: `low`; repeats: 2.
Cases: 30. Source unchanged during run: True. Boundaries and limitations: see ../../README.md.
Raw agent attempts: 240; canonical attempts: 50. Tables use the latest checkpoint for each case/arm/repeat; earlier attempts remain in JSONL.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 60/60 | 57/60 | 0 | 51 | 0 | 0 | 4424 |
| guide | 60/60 | 57/60 | 0 | 48 | 0 | 0 | 4397 |
| skill | 60/60 | 58/60 | 0 | 49 | 0 | 0 | 4667 |
| no_jev | 60/60 | 57/60 | 0 | 0 | 0 | 0 | 2597 |

## Fixed-question Jev track

Successful transport: 50/50. Correct task outcomes: 50/50.

| Case | Correct / successful | Transport failures | IoU per repeat |
|---|---:|---:|---|
| text_sentiment_mixed | 2/2 | 0 | [] |
| text_aspect_sentiment | 2/2 | 0 | [] |
| text_rank_material | 2/2 | 0 | [] |
| text_policy_eligibility | 2/2 | 0 | [] |
| text_semantic_match | 2/2 | 0 | [] |
| text_study_design | 2/2 | 0 | [] |
| text_entailment | 2/2 | 0 | [] |
| text_rubric_priority | 2/2 | 0 | [] |
| text_headline_ranking | 2/2 | 0 | [] |
| text_theme_classification | 2/2 | 0 | [] |
| image_count_green_circles | 2/2 | 0 | [] |
| image_color_shape_match | 2/2 | 0 | [] |
| image_leftmost_color | 2/2 | 0 | [] |
| image_compare_blue_count | 2/2 | 0 | [] |
| image_compare_red_circle | 2/2 | 0 | [] |
| image_locate_red_square | 2/2 | 0 | [0.941, 0.868] |
| image_locate_blue_circle | 2/2 | 0 | [0.907, 0.907] |
| image_locate_yellow_rectangle | 2/2 | 0 | [0.94, 0.94] |
| image_locate_green_circle | 2/2 | 0 | [0.848, 0.872] |
| image_locate_purple_square | 2/2 | 0 | [0.907, 0.874] |
| ambiguous_conflicting_reviewers | 2/2 | 0 | [] |
| ambiguous_similar_options | 2/2 | 0 | [] |
| ambiguous_conflicting_receipts | 2/2 | 0 | [] |
| ambiguous_conflicting_notes | 2/2 | 0 | [] |
| ambiguous_absent_object | 2/2 | 0 | [] |

## Agent failures requiring attribution

- text_theme_classification / skill / r1: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / guide / r0: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': True, 'abstained': False, 'low_confidence_or_error_handling': 'manual_review'}.
- text_theme_classification / descriptions / r1: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- deterministic_character_count / guide / r0: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- text_theme_classification / no_jev / r0: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- text_theme_classification / descriptions / r0: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_compare_blue_count / guide / r1: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': True, 'abstained': False, 'low_confidence_or_error_handling': 'manual_review'}.
- ambiguous_conflicting_reviewers / no_jev / r0: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': True, 'low_confidence_or_error_handling': 'not_exercised'}.
- deterministic_character_count / descriptions / r0: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- text_theme_classification / no_jev / r1: outcome={'passed': False}; behavior={'evaluation_calls': 0, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.
- image_leftmost_color / skill / r0: outcome={'passed': False}; behavior={'evaluation_calls': 1, 'unnecessary_calls': 0, 'required_call_omitted': False, 'invalid_or_failed_calls': 0, 'low_confidence_observed': False, 'abstained': False, 'low_confidence_or_error_handling': 'not_exercised'}.

## Repeat instability

Observed changes in answer/box/abstention/call count: 20 case-arm pairs.
- image_compare_red_circle / descriptions
- image_compare_blue_count / descriptions
- image_leftmost_color / skill
- text_theme_classification / skill
- image_locate_blue_circle / guide
- image_locate_green_circle / descriptions
- deterministic_character_count / descriptions
- deterministic_character_count / guide
- image_locate_blue_circle / descriptions
- image_locate_red_square / guide
- text_rubric_priority / skill
- image_locate_green_circle / guide
- image_locate_yellow_rectangle / skill
- image_compare_red_circle / skill
- image_locate_yellow_rectangle / descriptions
- image_locate_red_square / descriptions
- ambiguous_conflicting_reviewers / no_jev
- image_locate_purple_square / skill
- image_locate_red_square / skill
- image_locate_green_circle / skill

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
