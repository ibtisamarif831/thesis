# Dashboard Implementation

## Schema-v2 payload contract

`dashboard_data.json.metadata` includes `feature_schema_version` and `orientation_confidence_threshold`. Each compact `feature_group_records` item carries the seven v2 representative values, `orientation_confidence_v2`, `red_pixel_ratio_v2`, `strict_red_flag_v2`, and mask mode/coverage/contact/confidence/uncertainty. Legacy representatives remain in the full raw feature export but are excluded from the active 81-feature registry and from Feature Groups.

Client behavior derives Red solely from `strict_red_flag_v2`, computes scalar arithmetic means, computes orientation with a doubled-angle axial mean, and sorts undefined orientations after defined angles. The generator remains authoritative; regenerate `index.html` and `dashboard_data.json` after changes.

[Wiki home](README.md) · [Dashboard UI](dashboard-ui.md) · [Artifacts](artifacts-and-data-contracts.md)

## Generator and Output

`code/build_analysis_dashboard.py` is the source of truth for dashboard computation, HTML, CSS, and JavaScript. It writes generated artifacts to `icon_data/analysis/analysis_dashboard/`.

Do not edit the generated `index.html` alone. Change the generator, run it, and commit both source and intended generated outputs.

## Generation Sequence

The builder:

1. reads `icon_data/analysis/dataset.csv`;
2. randomly samples up to 10 rows per set with seed 42;
3. enriches metadata and McDougall ratings;
4. extracts visual features for the sampled normalized images;
5. drops rows whose extraction failed;
6. builds image, metadata, and combined matrices;
7. writes feature tables;
8. computes K-means and hierarchical labels for 3, 5, 7, and 10 clusters;
9. writes assignments and summaries;
10. builds feature-review and feature-explorer payloads from the complete 28,749-row `features.csv` corpus;
11. writes `dashboard_data.json` and generated HTML;
12. ensures a local Plotly asset placeholder exists if the real bundle is missing.

## Two Sample Populations

| Dashboard component | Source | Current rows |
|---|---|---:|
| Clustering records and projections | Random per-set sample from `dataset.csv` | 129 |
| Feature Groups random pool | Compact identity/path/color/representative-feature payload from `features.csv` | 28,749 |
| Feature Review correlations | Complete `features.csv` corpus | 28,749 |
| Feature Values examples/statistics | Complete `features.csv` corpus | 28,749 |

This distinction matters when reconciling example icons, summary counts, or correlations with clustering results.

## `dashboard_data.json` Contract

Top-level keys:

| Key | Content |
|---|---|
| `metadata` | Row/sample configuration, variants, cluster values, raw/active/excluded features, family definitions, McDougall columns. |
| `records` | One dashboard-sample record per icon. |
| `feature_group_records` | Compact full-corpus pool used to draw independent 20-icon Feature Groups samples. |
| `clusters` | PCA coordinates and method/count labels for each variant. |
| `feature_review` | Metadata, summary, per-feature redundancy statistics, and all pair correlations. |
| `feature_explorer` | Selection metadata and low/mean-nearest/high examples for 13 features. |

Each `records` item contains:

- `icon_id`, `label`, `set_id`, `set_name`, and source format;
- dashboard-relative `normalized_path`;
- `metadata_tokens`;
- `image_features` mapping;
- `mcdougall` rating mapping when applicable.

The front end should access feature definitions through `metadata.image_feature_sections` so label, family, meaning, interpretation, and feature ID remain aligned. Each section also carries `representative_feature_id`, the resolved `representative_feature` object, `representative_interpretation`, `representative_rationale`, `representative_evidence`, and `representative_citation`.

## CSV Contracts

| File | Role |
|---|---|
| `sample_metadata.csv` | Enriched 129-row dashboard sample and path-coverage flags. |
| `features_image.csv` | Sample identity/context plus extracted image features. |
| `features_metadata.csv` | Encoded metadata matrix used by the metadata variant. |
| `features_combined.csv` | Concatenated image and metadata matrix. |
| `cluster_assignments.csv` | All variant × method × count labels. |
| `clusters_kmeans.csv` | K-means-only subset. |
| `clusters_hierarchical.csv` | Hierarchical-only subset. |
| `cluster_summary.csv` | Cluster counts, dominant sets/categories, and representatives. |
| `feature_failures.json` | Dashboard-sample feature extraction failures. |
| `analysis_dashboard_metadata_report.json` | Sample coverage and expected-output report. |

## Front-End State

The generated browser application keeps three state objects:

- clustering state: variant, method, count, color choice, selected image features, and set filter;
- review state: active view, sort, threshold, and selected feature;
- explorer state: search and selected feature.

Image projections are cached by method, count, and ordered selected-feature list. Any feature selection change clears the cache. Metadata and combined projections always use precomputed arrays.

The application fetches only local data and assets. There is no server-side API and no persistence; a page reload resets UI state.

### Feature-family fullscreen detail

The Feature Groups view derives each family row from `metadata.image_feature_sections`. Its fullscreen detail view renders only the section's single `representative_feature`, together with the section's interpretation, selection rationale, evidence, and citation. The remaining `features` array stays intact for the 81-feature analytical registry; representative selection is a study-review layer, not a clustering change. The dialog uses the full viewport (`100vw` by `100dvh`, with `100vh` fallback); its header and filter toolbar occupy fixed grid rows while only the detail body scrolls.

The fullscreen gallery uses `feature_group_records`, a compact pool spanning all 28,749 feature rows. It carries only icon identity, label/set, normalized path, monochrome status, and the seven representative values. The browser keeps an independent random 20-icon sample for every family and color-treatment combination. **Randomize icons** replaces only the active combination; a reload clears all transient samples. Its icon-treatment classification is computed in the browser:

- B/W: `image_features.is_monochrome >= 0.5`;
- Red: records with `image_features.strict_red_flag_v2 >= 0.5`;
- Colored: all other non-monochrome records.

The Red rule is derived from foreground pixels, not dataset names or labels. The browser computes the arithmetic mean of scalar representative values across the current sample and uses an axial circular mean for orientation. It displays the result as **Sample average**, sorts scalar cards numerically from low to high, and sorts defined orientations angularly before low-confidence **Undefined** cards. Each card displays its raw value; orientation cards also display confidence, and uncertain masks display a warning. The selected family and color mode are transient UI state. Color mode persists across family openings during the page session, while each family receives its own sample from that cohort. Clicking All changes the cohort and reloading the page resets the state. Closing restores focus to the button that opened the detail.

## PCA and Browser Clustering

For image-feature selection, the browser:

- builds the selected feature matrix from `records[*].image_features`;
- standardizes columns;
- computes a 2D PCA projection;
- runs either deterministic browser K-means or the hierarchical/MST cut;
- caches the result.

The browser image-view computation is intended for interactive diagnostics. The exported precomputed tables are the more stable evidence for reproducible reporting.

## Feature Review Data

The generator computes summary variance/missingness and Spearman correlations for all active feature pairs. Bands separate high, moderate, and low redundancy. The shared helper `code/thesis_pipeline/dashboard/feature_selection.py` selects low-redundancy representatives for Feature Values and has focused tests under `code/tests/`.

## Asset and Path Rules

- `assets/plotly.min.js` is vendored so the dashboard can run offline.
- Paths in JSON are relative to the dashboard directory.
- Normalized images are referenced under `../../normalized_256/...`.
- Serve from the repository root so these relative paths resolve.
- If the Plotly bundle is absent, the builder writes a throwing placeholder; a generated page can exist but still fail at runtime, so browser verification is required.

## Known Implementation Gaps

- The visible plot uses image overlays, while the marker is transparent; the Color By state is currently unused in rendering.
- The current UI filters only by icon set although older docs mention category/style filters.
- Hierarchical clustering has no dendrogram.
- Browser-computed image clusters are not exported after interactive feature changes.
- UI state is not encoded in the URL or persisted.
- The dashboard has no human-response layer yet.

## Safe Change Workflow

1. Read the relevant computation and UI function in `build_analysis_dashboard.py`.
2. Check `dashboard_data.json` before assuming a field exists.
3. Change reusable logic in `code/thesis_pipeline/` where appropriate.
4. Add or update focused tests.
5. Run `py_compile` and tests.
6. Regenerate the dashboard.
7. Inspect JSON/CSV counts and schemas.
8. Serve the repository and complete the UI walkthrough.
9. Update this wiki when behavior or the data contract changes.
