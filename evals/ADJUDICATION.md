# Output-format corrections discovered during baseline

The initial baseline grader compared exact JSON types and the literal word `unknown`. This conflicts with two task/output contracts. Preserve the original manifest, raw traces and strict grades; publish any corrected grades in a separate sidecar with explicit rule IDs.

1. **numeric_response_identifier**: `text_theme_classification` asks to return the response's *number*, while its canonical choice key/expected value is the string `"3"`. Both numeric `3` and the choice identifier `"3"` represent the same independently established answer. Accept exactly these two representations, not arbitrary numbers or prose.
2. **null_abstention**: The common output contract permits `answer=null`. For cases whose expected answer is `unknown` and that explicitly require abstention, also accept null **only** with `abstain=true` and no box. Keep the requirement to acknowledge missing/conflicting evidence. This does not change an A/B guess into a correct answer.
3. **color_label_case**: `image_leftmost_color` asks for a color name without specifying capitalization. Compare the supplied color name case-insensitively; `Yellow` and `yellow` denote the same color. Do not normalize arbitrary A/B identifiers or accept a different color.

These are corrections to format handling, not changes to the answer key or the predeclared IoU, rubric-error or confidence thresholds. Do not repair a wrong structured answer merely because its explanation mentions the correct option. Primary baseline strict results remain reportable alongside the corrected task-outcome figures.
