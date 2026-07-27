# Thesis Status

Updated: 2026-07-27

## Thesis Statement

This thesis investigates how visual factors identified in glyph/icon perception literature can be organized into computer-measurable feature families, and compares those computational feature scores with human identification/perception scores to determine which visual factors influence agreement, mismatch, distinguishability, and confusability between humans and computer-based glyph analysis.

## Current State

The project has a working computer-side pipeline:

- Local icon/glyph datasets are collected and normalized.
- Literature papers are stored locally in `papers/` with extracted text in `papers/extracted_text/`.
- Visual features are extracted for all 28,749 canonical icons, with zero failures in the verified full-corpus run.
- Active visual feature families are defined and used consistently by the dashboard and similarity outputs.
- Weak/non-interpretable raw channels have been removed from active feature-family analysis.
- Similarity outputs are rebuilt using the active visual families.
- Evaluation layers are specified in `code/evaluation/evaluation_layers.md`.
- Feature Groups exposes one literature-backed representative for each of the seven families, with evidence citations and an independent, randomizable 10-icon pilot sample drawn from the complete corpus; each sample shows its arithmetic mean, is sorted low-to-high, and supports exact-three icon comparison across all seven representatives while preserving all 81 active analytical features.
- Feature Values uses the same seven representatives as Feature Groups and shows full-corpus low, mean-nearest, and high examples with correlation context.
- Feature schema v2 repairs foreground masking and six current representative measurements while retaining legacy measurements. Complexity now uses Canny edge density after the visual audit found source-rendering inflation in grayscale quadtree variability; quadtree remains active as a secondary analytical feature. Scalar families use arithmetic means; orientation uses confidence-aware angular ordering and an axial circular mean; Red is pixel-derived. The engineering pipeline is complete, but the pilot remains blocked until the rebuilt two-rater benchmark passes every release gate.
- README/guide files now describe the current thesis direction.

## Active Visual Families

- Complexity
- Shape/silhouette
- Stroke/structure
- Density/fill
- Balance/layout
- Color/contrast
- Texture

Raw extracted columns are retained for traceability, but the active mapped family set uses 81 visual features.

## Excluded From Active Mapping

- Hu moments
- Local binary pattern histogram bins
- `text_or_letter_presence`
- `crush_test_stability`

These are not deleted from raw exports, but they should not drive the thesis claims, dashboard active feature families, similarity ranking, feature review, or human/computer comparison.

## What Is Done

- Literature-to-feature-family mapping reviewed.
- Feature-family descriptions corrected.
- Similarity math corrected for circular orientation and hue.
- Weak channels removed from active mapping.
- Dashboard and similarity outputs regenerated.
- Project documentation aligned with the current thesis direction.
- Old historical task files removed and replaced with a current next-step tracker.
- Initial representative-feature selection completed for all seven families; candidate-stimulus review remains open.

## What Is Not Done Yet

- Human-study stimulus subset is not finalized.
- Human-study protocol is not written.
- Participant-response schema is not implemented.
- Human identification/perception scores have not been collected.
- Statistical comparison between human scores and computer scores has not been performed.
- Pairwise explainability through quasi-Hamming-style channel differences is not implemented yet.

## Immediate Next Step

Design the human-study layer:

1. Select a controlled stimulus subset.
2. Define the human scores to collect.
3. Create the response table/schema.
4. Export matching computer-side family scores for the same stimuli.
5. Run a small pilot before collecting full data.

Use `code/evaluation/evaluation_layers.md` as the evaluation-layer reference.

## Current Source Of Truth

- `wiki/README.md` and its topic pages for organized subsystem documentation
- `agent.md`
- `THESIS_CHECKLIST.md`
- `THESIS_STATUS.md`
- `icon_data/analysis/README.md`
- `icon_data/analysis/analysis_dashboard/README.md`
- `notes/human_to_computer_glyph_feature_mapping.md`
- `notes/literature_mapping_deep_pass_2026-07-08.md`
- `tasks/current-thesis-next-steps.md`
