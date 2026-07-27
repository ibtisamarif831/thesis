# Review, Feature Pipeline, and Dashboard Refactoring Plan

Status: proposed

Audit date: 2026-07-28

## Objective

Make the feature-review pipeline and dashboard easier to change without broad ripple effects. The target architecture should have:

- one authoritative feature and family registry;
- explicit data populations and transformation profiles;
- pure, testable analysis services;
- a thin dashboard-generation entrypoint;
- separately maintainable HTML, CSS, JavaScript, and browser state;
- versioned, stable artifact contracts.

This plan preserves current thesis behavior before changing architecture. It does not propose a wholesale UI rewrite or changes to the scientific interpretation of existing features.

## Current Architecture

The current end-to-end path is:

```text
dataset.csv + normalized PNGs
  -> extract_icon_features.py
  -> features.csv
  -> dashboard review, Feature Values, clustering, and Feature Groups payloads
  -> generated dashboard_data.json and index.html

features.csv
  -> compute_icon_similarity.py
  -> transformed and weighted similarity outputs

features.csv
  -> evaluation/build_feature_v2_benchmark.py
  -> evaluation/evaluate_feature_v2_benchmark.py
  -> feature_v2_release_gate.json
```

The pipeline works, but important definitions and transformations are owned by multiple consumers.

## Prioritized Findings

### P1: Feature definitions have multiple authorities

Evidence:

- `code/extract_icon_features.py` owns extractor columns and measurement thresholds.
- `code/build_analysis_dashboard.py` owns active families, exclusions, labels, meanings, configured representatives, and citations.
- `code/evaluation/build_feature_v2_benchmark.py` duplicates representative mappings under different family identifiers.
- `code/compute_icon_similarity.py` imports `build_analysis_dashboard` to recover active family membership.

Impact:

- changing a family or representative can require edits across extraction, dashboard, evaluation, similarity, tests, artifacts, and documentation;
- dependency direction is inverted when a general similarity pipeline imports a UI generator;
- family identifiers can drift between analytical and evaluation code.

Target:

Create `code/thesis_pipeline/features/registry.py` containing typed `FeatureSpec` and `FamilySpec` definitions. It should own:

- feature IDs and display metadata;
- family membership and ordering;
- active, auxiliary, deprecated, and excluded status;
- configured representatives;
- interpretation and evidence metadata;
- shared measurement thresholds that are part of the feature contract.

Extraction, similarity, evaluation, dashboard generation, and tests should depend on this registry rather than on each other.

### P1: `build_analysis_dashboard.py` is the main change hotspot

Evidence:

- the script is about 3,570 lines;
- `write_index_html()` is about 1,927 lines;
- the file combines CSV I/O, metadata enrichment, feature review, example selection, transformations, clustering, payload construction, HTML, CSS, JavaScript, state, and rendering.

Impact:

- small UI changes require editing a large Python string;
- analysis behavior and presentation behavior cannot be tested independently;
- merge conflicts are likely when concurrent tasks touch unrelated dashboard concerns;
- generated HTML substring tests provide weak behavioral protection.

Target:

Keep `code/build_analysis_dashboard.py` as a compatibility CLI wrapper and extract:

```text
code/thesis_pipeline/dashboard/
  config.py
  populations.py
  review.py
  explorer.py
  payload.py
  build.py

code/thesis_pipeline/analysis/
  transforms.py
  clustering.py
  statistics.py

code/dashboard_ui/
  index.template.html
  dashboard.css
  app.js
  state.js
  clustering.js
  feature_groups.js
  feature_review.js
```

The exact file names can change, but analysis, serialization, state, and rendering should remain separate responsibilities.

### P1: Numerical and missing-value semantics are inconsistent

Evidence:

- dashboard Python uses mean/standard-deviation scaling;
- dashboard matrix construction maps missing or non-finite values to zero;
- browser code independently implements standardization, PCA, K-means, and hierarchical clustering;
- similarity uses median/IQR scaling, clipping, circular hue smoothing, confidence-scaled axial orientation, and family weighting;
- dashboard review and evaluation each implement separate ranking and Spearman helpers.

Impact:

- two views can give different answers for the same apparent feature selection;
- missingness may mean zero, exclusion, or pairwise omission depending on the consumer;
- scientific differences between exploratory clustering and thesis similarity are implicit rather than declared.

Target:

Define named, immutable `AnalysisProfile` configurations, for example:

- `dashboard_exploratory`;
- `similarity_thesis`;
- `review_correlation`;
- `evaluation_gate`.

Each profile should explicitly declare:

- included feature registry query;
- missing-value policy;
- scalar scaling method;
- circular and axial transformations;
- confidence handling;
- feature and family weighting;
- clipping and constant-column behavior.

Shared implementations should live in `thesis_pipeline/analysis/`, with golden fixtures proving intentional differences between profiles.

### P1: Data populations and fallbacks are implicit

Evidence:

- the dashboard re-extracts its 129 sampled icons even though `features.csv` is the authoritative feature corpus;
- Feature Review and Feature Values silently fall back to the dashboard sample if the full feature file is absent or incomplete;
- Feature Groups normally uses 28,128 certain-mask records, but a session representative override makes all family details use the 129-row clustering sample because alternate values are absent from the compact payload.

Impact:

- a dashboard rebuild depends on normalized images even when current feature values already exist;
- the same view can silently change its statistical population;
- counts and example selection are difficult to reason about from the UI alone;
- rebuilds can partially write outputs before failing.

Target:

- join the clustering sample from `features.csv` by `icon_id` by default;
- make re-extraction an explicit `--refresh-sample-features` mode;
- represent every population with a stable ID, source artifact, row count, eligibility rule, and schema version;
- reject incomplete inputs with a clear preflight error;
- make fallback behavior explicit in configuration and payload metadata rather than automatic;
- write generated outputs transactionally through a temporary directory and promote them only after validation.

### P1: Browser state ownership is distributed

Evidence:

- clustering, review, explorer, family selection, comparison selection, samples, sampling queues, and projection caches live in separate mutable objects and globals;
- changing a representative mutates representative state, family samples, comparison state, clustering features, projection cache, and multiple renderers;
- session representatives affect clustering and Feature Groups, while Feature Values and evaluation remain tied to configured representatives.

Impact:

- state transitions have broad side effects;
- cache invalidation depends on callers remembering every affected cache;
- configured and exploratory representative concepts can be confused;
- a representative change currently replaces manual clustering selections with the seven current representatives.

Target:

Introduce a single `AppState` and explicit actions such as:

```text
SELECT_REPRESENTATIVE
SET_CLUSTERING_FEATURES
SET_COLOR_COHORT
REPLACE_FAMILY_SAMPLE
SELECT_COMPARISON_ICON
SET_ACTIVE_VIEW
```

Pure selectors should derive:

- configured representative IDs;
- session representative IDs;
- clustering feature IDs;
- active population;
- cache keys;
- visible family records.

Before implementation, decide the product rule for how representative changes affect manual clustering selections: replace, merge, or activate a dedicated representatives preset.

### P2: Evaluation configuration and result schemas are duplicated

Evidence:

- benchmark generation writes gate thresholds;
- evaluation repeats those thresholds as literals;
- dashboard and evaluation family IDs differ;
- `feature_v2_release_gate.json` has different field shapes for initial, pending, and evaluated states.

Target:

Create a typed `EvaluationSpec` shared by benchmark generation and evaluation. Always emit a versioned result schema containing:

- status;
- thresholds;
- completeness;
- metrics;
- failures;
- source benchmark identity;
- feature schema version.

Fields should remain present when values are unavailable.

### P2: Tests protect strings more than boundaries

Evidence:

- several dashboard tests assert that JavaScript or markup substrings exist in generated HTML;
- browser state transitions and Python/browser algorithm parity lack direct unit coverage;
- `code/thesis_pipeline/dashboard/feature_selection.py` is only used by tests and documentation.

Target:

- add registry invariant tests;
- add population and missing-value policy tests;
- add transformation-profile golden tests;
- add `dashboard_data.json` contract tests;
- test extracted JavaScript state/actions without Plotly;
- keep one end-to-end browser smoke flow;
- either integrate the optional feature-selection helper as a declared strategy or remove it.

## Staged Delivery Plan

### Stage 0: Characterize and freeze current behavior

Deliverables:

- golden registry snapshot;
- fixtures for the 129-row, 28,128-row, and 28,749-row populations;
- transformation and clustering fixtures;
- versioned dashboard payload schema;
- explicit decision on representative-to-clustering behavior.

Exit criteria:

- existing generated outputs can be compared structurally and numerically;
- all intentional behavior differences are documented;
- no architecture movement begins without regression protection.

### Stage 1: Establish shared authorities

Quick wins:

1. Add the typed feature/family registry.
2. Add `EvaluationSpec`.
3. Centralize UTF-8 CSV/JSON I/O and numeric parsing.
4. Replace the similarity-to-dashboard import with a registry dependency.
5. Add explicit population metadata and preflight validation.
6. Read sample feature values from `features.csv` by default.

Exit criteria:

- changing a configured representative requires one registry edit plus evidence/docs;
- similarity and evaluation no longer import dashboard implementation;
- a missing or incomplete full-corpus input cannot silently change a view's population.

### Stage 2: Extract pure analysis services

Move review statistics, example selection, sampling, transforms, PCA, K-means, hierarchical clustering, and payload construction into importable modules. Keep filesystem writes in the build/orchestration layer.

Exit criteria:

- pure services accept data/configuration and return values without hidden writes;
- focused tests cover each service;
- the compatibility script produces the same versioned payload and CSV contracts.

### Stage 3: Separate the browser application

Move HTML, CSS, and JavaScript out of the Python f-string. Introduce `AppState`, actions, selectors, and adapter modules for Plotly and DOM rendering.

Exit criteria:

- UI modules can be tested without regenerating the entire dashboard;
- state transitions have explicit cache invalidation;
- a styling or copy change does not touch analytical Python;
- generated output remains offline-capable.

### Stage 4: Make pipeline execution explicit

Add a thin pipeline orchestrator or manifest that records:

- input artifacts and checksums;
- schema versions;
- selected populations;
- configuration and random seeds;
- output artifacts;
- verification status and freshness.

Use transactional output generation so failed builds leave the last valid dashboard intact.

Exit criteria:

- one command can explain which artifacts are stale and why;
- rebuilds fail before writing when required inputs are missing;
- downstream artifacts record the exact feature registry and analysis profile used.

## Recommended First Implementation Slice

The first refactoring task should be deliberately small:

1. add registry characterization tests;
2. extract the existing feature/family registry without changing values;
3. make dashboard, similarity, and benchmark generation import it;
4. verify unchanged active-feature order, representatives, similarity groups, benchmark mappings, and generated payload metadata.

This removes the most harmful dependency inversion while keeping numerical and UI behavior stable.

## Non-Goals

- changing the seven configured study representatives;
- changing feature formulas or release thresholds;
- redesigning the dashboard appearance;
- scaling pairwise similarity to the full corpus;
- implementing the human study;
- replacing Plotly solely for architectural style.

## Risks and Controls

| Risk | Control |
|---|---|
| Numerical drift during extraction | Golden fixtures and tolerance-based comparisons before moving code |
| Generated payload incompatibility | Versioned schema and contract tests |
| Large merge conflicts | Move one responsibility at a time and retain thin wrappers |
| Hidden population changes | Required population IDs and source metadata |
| Browser/Python divergence | Shared fixtures and explicit profile parity tests |
| Refactor delaying thesis work | Deliver Stage 1 as quick wins; schedule Stages 2–4 around thesis milestones |
