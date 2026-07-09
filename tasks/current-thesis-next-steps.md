# Current Thesis Next Steps

Updated: 2026-07-08

## Current Thesis Direction

The thesis compares literature-derived visual feature families with human identification/perception scores for the same icon/glyph stimuli.

Computer-side scores come from active visual feature families. Human-side scores still need to be collected through a study or structured qualitative evaluation.

## Completed

- Local literature papers were reviewed and mapped to computable visual families.
- Active visual families were corrected:
  - Complexity
  - Shape/silhouette
  - Stroke/structure
  - Density/fill
  - Balance/layout
  - Color/contrast
  - Texture
- Weak/non-interpretable channels were removed from active mapping:
  - Hu moments
  - LBP histogram bins
  - `text_or_letter_presence`
  - `crush_test_stability`
- Dashboard, feature review, feature explorer, clustering, and similarity now use active visual families.
- Similarity math now handles circular orientation and hue correctly.
- Project README/guide files were aligned with the current thesis direction.
- Evaluation layers were documented in `code/evaluation/evaluation_layers.md`.

## Immediate Next Tasks

1. Select the human-study stimulus subset.
   - Choose a manageable set of icons with good coverage across active visual families.
   - Include visually close pairs and visually distant pairs.
   - Avoid relying on semantic category as the main sampling logic.

2. Define human-study scores.
   - Identification accuracy or label choice.
   - Confidence.
   - Perceived similarity or confusability.
   - Optional perceived complexity.

3. Build the participant response table/schema.
   - One row per participant-stimulus or participant-pair response.
   - Include `icon_id` or pair IDs so responses can join to computed feature-family scores.

4. Add computer-side family score exports.
   - Export per-icon active family summaries.
   - Export pairwise family distances for selected study pairs.
   - Keep raw feature columns separate from active family scores.

5. Validate feature examples visually.
   - For each active family, inspect low/high examples.
   - Mark any feature that behaves unexpectedly before using it in the human comparison.

6. Plan the analysis.
   - Correlate human scores with feature-family scores.
   - Compare agreement and mismatch cases.
   - Report which visual families most influence identification, similarity, and confusability.

7. Implement evaluation scripts under `code/evaluation/`.
   - Start with stimulus selection and feature-family score exports.
   - Then add human-response joins and agreement/mismatch analysis.

## Not Current Scope

- Semantic image understanding from pixels.
- Cultural/historical interpretation as computer features.
- Familiarity or meaningfulness as image-derived features.
- Learned embeddings as the main thesis model.
- Generic icon clustering as the final contribution.

## Files To Treat As Current

- `agent.md`
- `THESIS_CHECKLIST.md`
- `icon_data/analysis/README.md`
- `icon_data/analysis/analysis_dashboard/README.md`
- `notes/human_to_computer_glyph_feature_mapping.md`
- `notes/literature_mapping_deep_pass_2026-07-08.md`
- `tasks/current-thesis-next-steps.md`
- `code/evaluation/evaluation_layers.md`
