# Evaluation and Human Study

## Feature-v2 measurement benchmark

Before these seven representatives can be used in the pilot, two independent raters must complete the frozen `feature_v2_benchmark.csv`. Each scalar family uses five-point judgments; orientation uses an angle or `undefined`; strict-red rows use `red` or `not_red`; both raters inspect the saved mask overlay and record acceptability and gross inversion.

The benchmark builder obtains the seven family-to-representative mappings and legacy benchmark aliases from `code/thesis_pipeline/features/registry.py`. The evaluator shares the registry's schema version and orientation-confidence threshold. Gate thresholds and result-shape normalization remain a later refactoring stage.

Release requires weighted κ ≥ 0.60 for ordinal judgments, held-out Spearman ≥ 0.60 per scalar, orientation median axial error ≤ 15°, p90 ≤ 30°, undefined F1 ≥ 0.80, strict-red precision 1.00 and recall ≥ 0.80, at least 95% acceptable masks, and zero gross background inversions. Any family failure blocks all seven. The generated gate currently remains pending until ratings exist; do not describe engineering completion as human validation.

[Wiki home](README.md) · [Thesis overview](thesis-overview.md) · [Limitations](limitations-and-backlog.md)

## Status

The evaluation layer is specified but not implemented end to end. No participant-response dataset has been collected, and no statistical human-computer comparison has been completed.

The current computer pipeline supplies candidate predictors and diagnostic views. The size-controlled human study is the missing primary evidence layer.

## Literature-Backed User-Study Distinctions

The presentation's literature review separates outcomes that must not be treated as interchangeable:

- Fuchs et al. (2014), Experiment 2, used a forced-choice similarity task with ordinary online participants. Of 62 accepted Amazon Mechanical Turk workers, 36 were retained after control questions; each completed 48 trials by choosing the most similar glyph from a highlighted target and eight alternatives.
- Legg et al. (2017 issue; copyright 2016) recruited 20 Oxford students or employees and analysed 19 responses. Participants rated 104 glyph pairs on a 0-10 differentiation scale; 96 non-reference pairs were randomized, while eight reference pairs remained fixed. This produced a perceived-distance judgment rather than an identification score.
- Fuchs et al. (2017) reviewed 64 quantitative controlled data-glyph user-study papers. Accuracy appeared in 63 studies, completion time in 42, and qualitative feedback in 19; the review also reports that preference did not always match performance.

These studies support similarity choice, pairwise differentiation, and task-performance measures. They do not directly establish semantic identification or reduced-size discernibility thresholds for heterogeneous icon sets; that remains the thesis's human-evaluation gap.

## Evaluation Layers

### Human Identification

Possible measures:

- correctness or identification accuracy;
- selected/free-text label;
- wrong-label confusion choice;
- confidence;
- response time, if collected;
- minimum identifiable size across the required size conditions.

### Perceived Similarity and Confusability

Possible measures:

- pairwise similarity rating;
- most-similar choice;
- distinguishability/confusability rating;
- confusion matrix derived from identification errors.

### Computer Visual Features

Use active image-derived family values only. Keep raw features and family summaries separately available so aggregation remains auditable.

### Pairwise Distinguishability

Candidate measures:

- total active-feature distance;
- family-wise distance;
- nearest-neighbor rank;
- margin to the nearest competitor;
- future quasi-Hamming-style count of differing visual channels.

### Scale/Display Conditions

Scale is the primary experimental condition, not a new feature family. Candidate pilot sizes are 16, 24, 32, 48, 64, 128, and 256 pixels; the final set must be fixed through pilot testing. Outcomes can include accuracy, confidence, confusions, response time, and the smallest size at which a glyph set remains reliably discernible.

### Human-Computer Agreement

Candidate analysis includes correlations, regression or feature importance, agreement cases, mismatch cases, and family contribution to identification/similarity/confusability.

## Planned Study Workflow

```mermaid
flowchart LR
    A["Select representative family features"] --> B["Browse candidate icons"]
    B --> C["Export per-icon and pair scores"]
    C --> D["Choose controlled groups and pairs"]
    D --> E["Render fixed decreasing sizes"]
    E --> F["Write and pilot protocol"]
    F --> G["Collect participant responses"]
    G --> H["Estimate discernibility thresholds"]
    H --> I["Join with computer-side predictors"]
```

## Current Ticket Sequence

| Ticket | Goal | Status |
|---|---|---|
| T-001 | Add black/white/red/other foreground-color cohorts to Feature Groups. | In progress; current brief implements All/B/W/Red/Colored, while the older five-cohort pixel-classification criteria remain unresolved. |
| T-002 | Select representative family features and browse about 20 candidates. | In progress; seven representatives selected and documented, candidate browsing remains. |
| T-003 | Export per-icon family summaries and pairwise family distances. | Todo; depends on T-002 |
| T-004 | Select controlled icon groups and matched close/distant pairs. | Todo; depends on T-002 and T-003 |
| T-005 | Design a pilot identification/similarity/confusability study. | Todo; depends on T-004 |
| T-006 | Define participant schemas, joins, exclusions, and analysis plan. | Todo; depends on T-003 and T-005 |

The detailed acceptance criteria live under `tasks/tickets/` and should be treated as the implementation contract.

## Proposed Response Schemas

These are design targets, not current artifacts.

### Participant × Icon

| Field | Purpose |
|---|---|
| `participant_id` | Pseudonymous participant key. |
| `trial_id` | Unique randomized trial key. |
| `icon_id` | Join to canonical/computer-side scores. |
| `render_size` | Required display-size condition in pixels. |
| `prompt_version` | Protocol traceability. |
| `chosen_label` / `free_label` | Identification response. |
| `correct` | Scored identification outcome. |
| `confidence` | Participant confidence scale. |
| `response_time_ms` | Optional latency. |
| `explanation` | Optional qualitative visual-detail explanation. |

### Participant × Pair

| Field | Purpose |
|---|---|
| `participant_id`, `trial_id` | Participant/trial keys. |
| `icon_id_a`, `icon_id_b` | Stable pair members. |
| `pair_id` | Order-normalized pair key. |
| `similarity_rating` | Human similarity outcome. |
| `confusability_rating` | Human confusion risk outcome. |
| `more_similar_choice` | Choice outcome where applicable. |
| `confidence`, `response_time_ms`, `explanation` | Supporting outcomes. |

Before collection, define allowable values, missing-response codes, exclusion rules, trial randomization, consent/privacy handling, and how correctness is scored for ambiguous labels.

## Computer-Side Exports Needed

- one row per `icon_id` with seven normalized family summaries;
- raw active features in a separate table;
- one row per selected pair with total distance and seven family-wise distances;
- preprocessing, scaling, aggregation, and weight metadata;
- source paths and stable identifiers;
- selected-stimulus review notes.

Do not calculate family summaries by naively averaging raw columns with incompatible scales. Define transformations and reliability weighting before aggregation and preserve the specification in metadata.

## Analysis Plan Skeleton

1. Describe participants, exclusions, trials, and missingness.
2. Report identification and similarity outcomes with uncertainty.
3. Join exact stimuli to computer-side scores.
4. Test predeclared correlations or regression models.
5. Compare close/distant controls and target-family manipulations.
6. Inspect agreement and mismatch cases qualitatively.
7. Report sensitivity to feature/family scaling and set composition.
8. Keep exploratory and confirmatory analyses distinguishable.

## Ethical and Methodological Guardrails

- Obtain the required institutional approval/consent before participant collection.
- Store pseudonymous participant identifiers and minimize personal data.
- Pilot instructions and logging before a full study.
- Avoid treating source labels as universally correct meanings when icons are culturally or contextually ambiguous.
- Predefine whether semantic correctness, visual similarity, or both are being judged.
- Do not leak metadata labels into a task intended to measure unaided identification.
