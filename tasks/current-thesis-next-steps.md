# Current Thesis Next Steps

Updated: 2026-09-29

The [meeting evidence and verified status](../wiki/meeting-decisions-and-status.md) distinguish agreed homework from unresolved study decisions.

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
- Dashboard, Feature Values and current clustering use the seven active representatives. Similarity code supports that preset, but saved reports remain the earlier 1,038-row run described by their own metadata.
- Similarity math now handles circular orientation and hue correctly.
- Project README/guide files were aligned with the current thesis direction.
- Evaluation layers were documented in `code/evaluation/evaluation_layers.md`.
- Feature Groups now has one literature-backed representative per family, with selection rationale and citation; the same seven measurements define thesis analysis.
- Schema-v2 replacements, strict-red pixel classification, mask diagnostics, confidence-aware orientation, and frozen benchmark tooling are implemented. Human ratings are still required; the all-family feature-validation pilot gate is blocked until they pass. The separate [recognition usability pilot](../wiki/icon-recognition-pilot.md) implements task-design response storage without changing this gate.
- The dashboard source universe is reduced to AIGA/DOT, OCHA, Universal Symbols Healthcare Webfont, ISO 7010, and ISO 15223 without deleting the complete 13-set canonical corpus.
- Internal nominations have arrived: `droa` 100, `pr77` 80, and algorithm-assisted `ibtisam` 100. A final consensus set has not been recorded.
- The recognition usability prototype implements anonymous responses and private exports; production verification records are synthetic, with no recorded research trials.

## Immediate Next Tasks

The meeting-note implementation backlog is captured in [`tasks/tickets/`](tickets/README.md), with implementation progress recorded per ticket. Current priority is nomination comparison and study decisions; remaining color-cohort refinements do not automatically take priority over that meeting deliverable.

1. Select the human-study stimulus subset.
   - Choose a manageable set of icons from the five retained dashboard sources, with good coverage across active visual families.
   - Include visually close pairs and visually distant pairs.
   - Avoid relying on semantic category as the main sampling logic.
   - The live internal reviewer workspace accepts partial submissions of 1–100 nominations, capped at 20 per source, and stores structured submissions; compare the received supervisor nominations and agree on the final consensus set. Classify the smaller `test*` entries before analysis. The 2026-09-29 `ibtisam` nomination is computational and must be compared separately from independent human reviews; see `icon_data/analysis/study_selections/2026-09-29-researcher-assisted/README.md`.

2. Agree the primary task and useful thesis result.
   - Decide whether identification means visual matching, semantic naming, or a different operational task. Pairwise discrimination is a separate construct.
   - Focus on size-dependent performance within coherent sets; do not promise one global weighting across sources.
   - Identification accuracy or label choice, according to that task.
   - Confidence.
   - Perceived similarity or confusability.
   - Optional perceived complexity.

3. Complete the final-study response schema and protocol.
   - Reuse or adapt the existing recognition prototype only after reviewing its large-target-first memory effects.
   - The local controlled version assigns 6/8/10/12/14 CSS pixels over 100 trials with five choices; its old enlargement workflow is retired. Assigned CSS sizes still need display/protocol review before threshold claims.
   - One row per participant-stimulus or participant-pair response.
   - Include `icon_id` or pair IDs so responses can join to computed feature-family scores.

4. Add computer-side family score exports.
   - Export per-icon active family summaries.
   - Export pairwise family distances for selected study pairs.
   - Keep raw feature columns separate from active family scores.

5. Complete the feature-v2 two-rater benchmark and inspect feature examples.
   - For each active family, inspect low/high examples.
   - Mark any feature that behaves unexpectedly before using it in the human comparison.

6. Plan the analysis.
   - Correlate human scores with feature-family scores.
   - Compare agreement and mismatch cases.
   - Estimate feature associations with the approved human outcome, with uncertainty; avoid claiming causal influence from descriptive associations.
   - Define rendering, exclusions, qualitative coding if needed, and required approval/consent before research collection.

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

- `wiki/README.md`
- `agent.md`
- `THESIS_CHECKLIST.md`
- `icon_data/analysis/README.md`
- `icon_data/analysis/analysis_dashboard/README.md`
- `notes/human_to_computer_glyph_feature_mapping.md`
- `notes/literature_mapping_deep_pass_2026-07-08.md`
- `tasks/current-thesis-next-steps.md`
- `code/evaluation/evaluation_layers.md`
