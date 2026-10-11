# Thesis Status

Updated: 2026-09-29

Meeting evidence and verification: [Meeting decisions and current state](wiki/meeting-decisions-and-status.md).

## Thesis Statement

This thesis investigates how visual factors identified in glyph/icon perception literature can be organized into computer-measurable feature families, and compares those computational feature scores with human identification/perception scores to determine which visual factors influence agreement, mismatch, distinguishability, and confusability between humans and computer-based glyph analysis.

## Current State

The project has a working computer-side pipeline:

- Local icon/glyph datasets are collected and normalized.
- Literature papers are stored locally in `papers/` with extracted text in `papers/extracted_text/`.
- Visual features are extracted for all 28,749 canonical icons, with zero failures in the verified full-corpus run.
- Active visual feature families are defined and used consistently by the dashboard and similarity outputs.
- Weak/non-interpretable raw channels have been removed from active feature-family analysis.
- Similarity preprocessing is implemented; checked-in similarity outputs cover the earlier 1,038-row cohort and predate the current seven-representative preset. They are not full-corpus or final-study score exports.
- Evaluation layers are specified in `code/evaluation/evaluation_layers.md`.
- The dashboard is now scoped to five human-study source sets: AIGA/DOT, OCHA, Universal Symbols Healthcare Webfont, ISO 7010, and ISO 15223. The complete 13-set canonical corpus remains preserved outside the dashboard.
- The public dashboard now includes an access-controlled internal stimulus-selection workspace: each reviewer nominates 1–100 icons, with at most 20 from each of the five sets, and submissions are stored pseudonymously in an EU-jurisdiction D1 database for consensus review. This is stimulus preparation, not participant-response evidence.
- Feature Groups exposes one literature-backed representative for each of the seven families, with evidence citations and independent randomizable samples drawn from the 397 quality-eligible icons in the five-set scope; scalar samples show arithmetic means and numeric ordering; orientation uses an axial circular mean and angular ordering, and supports exact-three icon comparison across all seven representatives.
- Feature Values uses the same seven representatives as Feature Groups and shows selected-source low, mean-nearest, and high examples with correlation context across all 649 scoped feature rows.
- Feature schema v2 repairs foreground masking and six current representative measurements while retaining legacy measurements. Complexity now uses Canny edge density after the visual audit found source-rendering inflation in grayscale quadtree variability; quadtree is retained only as a raw traceability column. Scalar families use arithmetic means; orientation uses confidence-aware angular ordering and an axial circular mean; Red is pixel-derived. The engineering pipeline is complete, but the feature-validation pilot remains blocked until the rebuilt two-rater benchmark passes every release gate.
- README/guide files now describe the current thesis direction.

## Active Visual Families

- Complexity
- Shape/silhouette
- Stroke/structure
- Density/fill
- Balance/layout
- Color/contrast
- Texture

The thesis analysis uses seven representative measurements, one per family. Other raw extracted columns are retained only for traceability and reproducibility.

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

## Nominations and usability prototype

Production D1 was checked on 2026-09-29. The two supervisor-associated submissions contain 100 (`droa`) and 80 (`pr77`) nominations. `ibtisam` contains 100 algorithm-assisted nominations and must be compared separately from human reviews. Smaller `test*` entries contain 17 additional rows and remain unclassified. Nominations have not established consensus stimuli.

The deployed recognition pilot implements three practice and 100 randomized recorded trials: five options, assigned 6/8/10/12/14 CSS-pixel candidate sizes, 1.5-second 128-pixel target exposure, confidence, keyboard/mouse input, interruptions and protected exports. The previous enlargement workflow is removed, and old production pilots/results were deleted at the user’s request. Migration 0003 is applied. Production deployment `ec45d507` was verified on 2026-10-11: 649 catalog icons, three reviewer submissions, 280 nominations, zero pilots/sessions/attempts after synthetic verification cleanup. No research participant evidence or threshold estimate is established.

## What Is Not Done Yet

- Human-study stimulus subset is not finalized.
- A usability-task protocol exists; the final thesis protocol, operational identification/discrimination definition, size conditions, exposure/memory controls and approval remain unfinished.
- A separate icon-recognition usability/task-design pilot now implements anonymous sessions, attempts and progressive response storage; the final-study response schema and analysis remain unfinished. See [pilot operations](wiki/icon-recognition-pilot.md). This does not change the feature-v2 gate or establish human validation.
- Human identification/perception scores have not been collected.
- Statistical comparison between human scores and computer scores has not been performed.
- Pairwise explainability through quasi-Hamming-style channel differences is not implemented yet.

## Immediate Next Step

Complete the meeting-to-study decisions:

1. Compare the submitted nominations and agree a controlled same-set stimulus subset.
2. Agree the primary task and useful thesis outcome; size is a central study condition, but exact task and threshold definitions remain provisional.
3. Complete the two-rater feature benchmark and distinguish it from usability checks.
4. Review the existing prototype, finish the final response/analysis specification and export matching computer scores.
5. Freeze the protocol and required approval/consent, then conduct the approved pilot and main study.

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
