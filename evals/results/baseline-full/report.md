# Behavioral evaluation results

Model: `gpt-5.6-terra`; effort: `low`; repeats: 2.
Cases: 30. Source unchanged during run: True. Boundaries and limitations: see ../README.md.

## Agent outcomes

| Arm | Completed | Task correct | Environment/turn failures | Evaluation calls | Unnecessary | Required omitted | Median ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| descriptions | 0/0 | 0/0 | 0 | 0 | 0 | 0 | n/a |
| guide | 0/0 | 0/0 | 0 | 0 | 0 | 0 | n/a |
| skill | 0/0 | 0/0 | 0 | 0 | 0 | 0 | n/a |
| no_jev | 0/0 | 0/0 | 0 | 0 | 0 | 0 | n/a |

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
| image_locate_red_square | 2/2 | 0 | [0.868, 0.901] |
| image_locate_blue_circle | 2/2 | 0 | [0.907, 0.907] |
| image_locate_yellow_rectangle | 2/2 | 0 | [0.939, 0.94] |
| image_locate_green_circle | 2/2 | 0 | [0.848, 0.848] |
| image_locate_purple_square | 2/2 | 0 | [0.906, 0.874] |
| ambiguous_conflicting_reviewers | 2/2 | 0 | [] |
| ambiguous_similar_options | 2/2 | 0 | [] |
| ambiguous_conflicting_receipts | 2/2 | 0 | [] |
| ambiguous_conflicting_notes | 2/2 | 0 | [] |
| ambiguous_absent_object | 2/2 | 0 | [] |

## Agent failures requiring attribution


## Repeat instability

Observed changes in answer/box/abstention/call count: 0 case-arm pairs.

## Interpretation limits

Argument success is structural evidence only; semantic criterion quality needs trace review. Low-confidence/error behavior is marked for manual review, not automatically passed for saying 'uncertain'.
No confidence calibration claim is made. Two repeats on synthetic cases measure observed instability, not a population confidence interval. Guide/skill arms are resource-preload interventions. No-Jev still sees the same images and deterministic compute tool.
Agent and Jev usage are separate in JSONL; missing usage is unavailable, never zero. Timing includes resource loading and agent tool round trips; concurrency affects wall time.
