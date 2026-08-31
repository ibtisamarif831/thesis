# Dashboard Implementation

## Schema-v2 payload contract

`dashboard_data.json.metadata` includes `feature_schema_version`, `analysis_feature_preset`, `orientation_confidence_threshold`, and `feature_group_excludes_uncertain_masks`. The dashboard contract exposes exactly seven configured family representatives: each `image_feature_sections` section contains only its representative, and generated dashboard records contain those seven values plus the four auxiliary classification/orientation fields required by the UI. The broader 81-feature registry and raw feature corpus remain available for offline extraction and analysis but are not serialized as dashboard choices. Each compact `feature_group_records` item carries the seven v2 representative values, `orientation_confidence_v2`, `red_pixel_ratio_v2`, `strict_red_flag_v2`, and certain-mask diagnostics. Rows with `mask_is_uncertain == true` are omitted while the complete feature corpus remains unchanged.

Client behavior derives Red solely from `strict_red_flag_v2`, computes scalar arithmetic means, computes orientation with a doubled-angle axial mean, and excludes confidence-undefined records before building an orientation-family sample. Missing/non-finite representative values serialize as `null` instead of being coerced to zero. The shared feature registry is authoritative for feature/family definitions; the generator remains authoritative for dashboard assembly. Regenerate `index.html` and `dashboard_data.json` after changes.

[Wiki home](README.md) · [Dashboard UI](dashboard-ui.md) · [Artifacts](artifacts-and-data-contracts.md)

## Generator and Output

`code/build_analysis_dashboard.py` is the source of truth for dashboard computation, HTML, CSS, and JavaScript. It adapts feature definitions from `code/thesis_pipeline/features/registry.py` and writes generated artifacts to `icon_data/analysis/analysis_dashboard/`.

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
| Image Clustering records and browser projection | Active cached Feature Groups family/cohort sample | Up to 20; can be lower for sparse bins |
| Metadata/Combined records and precomputed projections | Random per-set sample from `dataset.csv` | 129 |
| Feature Groups sampling pool | Certain-mask identity/path/color/representative-feature payload from `features.csv` | 28,260 |
| Feature Review correlations | Complete `features.csv` corpus | 28,749 |
| Feature Values examples/statistics | Complete `features.csv` corpus | 28,749 |

This distinction matters when reconciling example icons, summary counts, or correlations with clustering results. The 129 generated records are used only by Metadata and Combined projections; image-family interactions use the compact full-corpus payload and its fixed seven representatives.

## `dashboard_data.json` Contract

Top-level keys:

| Key | Content |
|---|---|
| `metadata` | Row/sample configuration, variants, cluster values, raw/active/excluded features, family definitions, McDougall columns. |
| `records` | One dashboard-sample record per icon. |
| `feature_group_records` | Compact certain-mask pool used to draw independent Feature Groups samples of up to 20 icons and populate three-icon comparisons. |
| `clusters` | PCA coordinates and method/count labels for each variant. |
| `feature_review` | Metadata, summary, per-feature redundancy statistics, and all pair correlations. |
| `feature_explorer` | Selection metadata and low/mean-nearest/high examples for the seven Feature Groups representatives. |

Each `records` item contains:

- `icon_id`, `label`, `set_id`, `set_name`, and source format;
- dashboard-relative `normalized_path`;
- `metadata_tokens`;
- `image_features` mapping;
- `mcdougall` rating mapping when applicable.

The front end should access feature definitions through `metadata.image_feature_sections` so label, family, meaning, interpretation, evidence, and feature ID remain aligned. Every feature object carries `evidence_scope`, `evidence`, and `citation` from the typed registry. Each section also carries `representative_feature_id`, the resolved `representative_feature` object, `representative_interpretation`, `representative_rationale`, `representative_evidence`, and `representative_citation`.

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

The Clustering grid can switch from three columns to two by applying `controls-collapsed`; the left controls sidebar is then removed from layout, its toolbar toggle updates `aria-expanded`, and Plotly is resized on the next animation frame. AI Clustering independently applies `ai-sidebar-collapsed` to its workspace to hide the right analysis sidebar and expand the embedding plot; its external toggle remains reachable and resizes that Plotly chart. Both cluster-summary sidebars render **Show heatmap** followed by one `cluster-sidebar-entry` button for every assigned cluster. A button opens the shared fullscreen cluster modal with only that cluster's detail card; the complete all-cluster modal path and old icon-card gallery are removed. `clusterIconValuesTableHtml` renders every assigned icon with thumbnail, label, set, and all seven confidence-aware representative values. The modal uses the full viewport (`100vw` by `100dvh`, with `100vh` fallback), scrolls only its body, closes with its close button or **Escape**, and restores focus to the originating cluster entry.

`featureDistribution` calculates the valid sorted values, minimum, quartiles, median, and maximum for one representative over the complete current clustering record set. `featureComparisonCardHtml` retains its full statistical rendering for contexts that need it, but its compact mode renders only the feature name, inspected value, middle-50% band, and subject/global-median markers; the full values remain encoded in the track's accessible label and marker titles. Manual hover and click request compact mode with `clusteringRecords()`; AI hover and click request it with the loaded run items. `comparisonFeatureValue` preserves genuine zeros and excludes confidence-undefined principal-axis orientations. `lassoFeatureComparisonHtml` calculates each selected-group median, uses compact bars, and retains the complete current record set as the global baseline, so icon-set filtering or lasso membership never silently redefines “all icons.”

The generated browser application keeps these related state objects:

- clustering state: variant, method, count, color choice, selected image features, set filter, and current chart drag mode;
- lasso state: selected icon IDs, selected detail icon, a projection/filter context key, and the current plotted coordinates/ranges;
- shared representative configuration: one fixed registry-owned representative feature per visible family;
- review state: active view, sort, threshold, and selected feature;
- explorer state: search and selected feature.

Image projections are cached by method, count, ordered selected-feature list, and the shared sample's ordered icon IDs. Any feature selection or shared-sample change clears the cache. Metadata and Combined projections always use the precomputed 129-row arrays.

Clustering derives its seven-entry allow-list, sidebar sections, selected-feature order, presets, numeric Color-by choices, and selected-icon detail rows directly from the fixed representatives in `metadata.image_feature_sections`. No browser representative map or alternate-feature selector exists. Image Clustering initializes all seven Feature Groups draws for the active cohort and concatenates them into one composite. When a family sample is created or randomized, icons already present in the other six cached family samples are excluded before equal-width sampling, keeping the composite unique and normally at 140 icons for All. Randomize replaces only the active family's contribution. Image projection cache keys include the ordered composite icon IDs, ensuring any replacement draw recomputes PCA and labels. Metadata and Combined keep their generated 129-row matrices. Reloading discards transient samples and restores the configured representatives.

Before Feature Groups sampling, `build_feature_group_payload()` applies the documented quality gate: identity and normalized-path fields must be present, the foreground mask must not be uncertain, and all seven representative values must be finite. It writes `feature_group_quality_audit.json` with exclusion counts, bottom-1% diagnostic thresholds, and the narrower extreme visual-review set. Low values are not automatically removed. Browser-side image projection and cluster profiles use `requiredRepresentativeValue()` so a later malformed payload fails explicitly instead of silently converting missing data to zero.

The code-only registry preset is therefore the sole authority for which features may participate in Clustering. No UI profile switch is exposed.

The four original analysis views fetch generated local data and assets. AI Clustering uses the local-only service described below. Browser session selections still reset on reload, while AI embeddings and valid completed/failed runs persist in SQLite.

### AI Clustering service and persistence

`code/serve_analysis_dashboard.py` serves the generated dashboard, normalized images under both `/normalized_256/` and the legacy nested `/icon_data/normalized_256/` URL, and four JSON routes: `GET /api/ai-clustering/status`, `POST /api/ai-clustering/runs`, `GET /api/ai-clustering/runs`, and `GET /api/ai-clustering/runs/{run_id}`. The legacy `/icon_data/analysis/analysis_dashboard/` URL is also served so old bookmarks do not break relative image paths. Reusable logic lives in `code/thesis_pipeline/ai_clustering/`; shared PCA, k-means, and hierarchical functions live in `code/thesis_pipeline/clustering/algorithms.py`.

The browser sends the ordered seven-family composite icon IDs, cohort, all seven representative IDs, current method, requested `k`, seed 42, feature labels, and feature PCA coordinates; stored runs use `family_id=all_families`. The server validates unique IDs against `dashboard_data.json`, resolves paths only under `icon_data/normalized_256`, and ignores all client path claims. Only cache-missing normalized PNG bytes are sent as base64 image inputs through the official OpenRouter Python SDK. No names, labels, feature values, metadata, or explanatory prompts enter the provider request. `ServiceConfig.from_environment` loads the ignored repository-root `.env` file while preserving any variables already exported by the shell.

The server L2-normalizes embeddings without z-scoring or family weights and applies the selected clustering family. `k` is capped at sample size with a warning. The browser-provided feature labels and coordinates reflect the currently checked Clustering features; changing that selection marks the displayed comparison stale and requires an explicit run. Feature selection never enters the image-embedding request, so the AI side continues to use the full learned image embeddings for the same sample. The service records adjusted Rand index, normalized mutual information, pairwise same-cluster agreement, the cross-table, and an embedding-space cluster-variance profile. The current UI intentionally hides ARI and NMI while retaining them in saved run data.

`cluster_variance_profile` calculates each cluster centroid against the overall centroid in the complete supplied matrix. It returns size, `n_c × squared_distance`, that value's share of total between-cluster variance, and mean squared centroid deviation per dimension as separation strength. New runs persist this profile inside `metrics_json`. `get_run` enriches older completed runs in memory by resolving every run icon's current normalized-image hash and reading the matching cached embedding; it never sends a provider request and does not rewrite the database. Missing or hash-stale embeddings leave the old run unchanged.

The signed-z heatmap control and rendering path have been removed from both clustering views. The shared cluster modal remains the source for variance, separation, icon counts, cluster means, overall means, and signed differences.

The AI tab renders the stored embedding coordinates as its primary interactive plot. Plot clicks populate selected-icon detail using the seven current representatives. Its cluster-analysis sidebar uses the same heatmap and per-cluster modal entries as manual Clustering instead of inline statistics. Both modes call `clusterDetailCardHtml`, which fixes one shared order for primary variance contribution, separation strength, full size, icon statistics, feature statistics, interpretation, and the complete icon-value table. Manual Image supplies primary metrics from the standardized selected-feature matrix; AI supplies those same primary labels from the full model-embedding profile stored with the run, then appends explicitly post-hoc measured-feature variance and strength. `clusterInterpretationProfile` builds both raw and standardized representative matrices and provides full-sample statistics, per-cluster raw feature statistics, signed standardized means, measured-feature variance contribution, separation strength, and neutral two-feature high/low labels. `numericSummary` returns valid count, mean, median, population standard deviation, minimum, and maximum. `clusterIconStatisticsHtml` renders full size/sample share, filter-visible count, represented-set count, and dominant-set statistics; `clusterFeatureStatisticsHtml` adds the raw per-feature values, overall mean, and signed standardized difference. `clusterIconValuesTableHtml` deliberately uses all seven configured representatives for every mode, preserving genuine zeros and displaying confidence-undefined orientation as **Undefined**. `clusterHeatmapHtml` renders the standardized profiles as an accessible signed-z table. Manual Image clustering invokes the profile helpers with its selected input features; AI invokes them with all seven current representatives as a post-hoc profile. Metadata and Combined can render icon statistics and the seven-value icon table but not aggregate raw-feature statistics because those dimensions were not their clustering inputs. The global feature-contribution panel remains a different question: it ranks features rather than clusters. None of these browser-derived measurements alter persisted runs, and AI measured-feature values must never be called model inputs, causal importance, or ground truth.

The feature-based plot, embedding plot, pairwise agreement, cache counts, and cross-table are rendered only in the fullscreen AI comparison modal opened by **Open feature vs AI comparison**. Its two plots share the stored icon order and synchronize hover/selection. Close and Escape both restore focus to the trigger. Method and `k` selectors appear in the AI tab and mirror the manual Clustering controls because both views use the same session state; changing either marks the loaded result stale but never sends a provider request.

`icon_data/analysis/ai_clustering/ai_clustering.sqlite3` is schema-versioned and intentionally tracked. Its `embeddings`, `runs`, and `run_items` tables store hash-keyed float32 vectors, completed/failed experiment metadata, labels, and both plots' coordinates. It uses rollback-journal mode. API keys and base64 images are never stored or returned. Treat the database as a single-writer team artifact and never commit `-wal` or `-shm` sidecars.

### Feature-family fullscreen detail

The Feature Groups view derives each family row from `metadata.image_feature_sections`. Each row displays its configured `representative_feature` as a static label and ID; its one-item `features` array contains that representative only. Alternate members of the broader 81-feature registry are deliberately absent from dashboard runtime metadata and controls. The representative retains its documented interpretation, rationale, evidence, and citation. The dialog uses the full viewport (`100vw` by `100dvh`, with `100vh` fallback); its header and filter toolbar occupy fixed grid rows while only the detail body scrolls.

The fullscreen gallery uses `feature_group_records`, a compact pool containing the 28,260 feature rows whose foreground mask is not flagged uncertain. The generator excludes all 489 uncertain-mask rows before writing the payload, so those icons cannot enter the gallery population, samples, displayed averages, or three-icon comparisons. It carries only icon identity, label/set, normalized path, monochrome status, certain-mask diagnostics, and the seven representative values. Missing or non-finite payload values remain `null`; the browser excludes those measurements without confusing them with genuine zero.

The browser keeps an independent stratified random sample for every family and color-treatment combination. It calculates the minimum and maximum eligible representative values, divides that range into 10 equal-width bins, and uses an in-place partial shuffle to choose up to two unique records from each bin. The maximum value is explicitly clamped into the tenth bin. Empty bins are not backfilled, bins containing one record contribute one, and an all-equal cohort is handled as a single degenerate bin, so the visible total can be below 20. Dataset membership has no role in this sampling rule. Repeated valid values, including zero, remain eligible. **Randomize icons** replaces only the active combination; a reload clears all transient samples. Its icon-treatment classification is computed in the browser:

The compact full-corpus payload intentionally contains only the seven configured representatives and is the sole source for Feature Groups details and comparisons. There is no exploratory representative override or 129-row fallback.

- B/W: `image_features.is_monochrome >= 0.5`;
- Red: records with `image_features.strict_red_flag_v2 >= 0.5`;
- Colored: all other non-monochrome records.

The Red rule is derived from foreground pixels, not dataset names or labels. Before building a principal-axis orientation sample, the browser removes records whose `orientation_confidence_v2` is below `metadata.orientation_confidence_threshold` (currently 0.20); the family/color counts use the same eligible population. It then computes the arithmetic mean of scalar representative values across the currently shown icons and an axial circular mean for orientation. It displays the result as **Average of shown icons**, sorts scalar cards numerically from low to high, and sorts orientation cards angularly. This is the mean of the visible scores, not a corpus-wide or dataset-size-weighted statistic. Each card displays its raw value; orientation cards also display confidence.

For interpretation, the browser profiles normalized scalar representatives at a 0.001 resolution and labels them low-information when they have fewer than three rounded levels or a 10th-to-90th-percentile spread below 0.002. Orientation uses one-degree bins modulo 180° and doubled-angle circular dispersion; its two-degree dispersion threshold respects the 0°/180° wrap. Orientation value bands are likewise unwrapped around the axial mean before sampling. The warning does not exclude values or alter averages; it prevents a uniform cohort from being presented as a meaningful low-to-high comparison.

The browser also keeps a transient set of up to three selected card IDs. The third selection opens a separate fullscreen modal (`100vw` by `100dvh`, with `100vh` fallback) containing the chosen images and a seven-row comparison table using the representative feature from every family; the active family row is highlighted and low-confidence orientation is shown as undefined. The Feature Groups detail remains underneath and is temporarily hidden from assistive technology. Closing the comparison with its close button or **Escape** restores the detail modal and returns focus to the selection control; a visible action can reopen the comparison while all three remain selected. Selection is cleared when the user opens another family, changes color treatment, or randomizes the sample. The selected family and color mode are transient UI state. Color mode persists across family openings during the page session, while each family receives its own sample from that cohort. Clicking All changes the cohort and reloading the page resets the state. Closing the family detail restores focus to the button that opened it.

## PCA and Browser Clustering

For image-feature selection, the browser:

- builds the selected feature matrix from `records[*].image_features`;
- standardizes columns;
- computes a 2D PCA projection;
- runs either deterministic browser K-means or the hierarchical/MST cut;
- caches the result.

The browser image-view computation is intended for interactive diagnostics. The exported precomputed tables are the more stable evidence for reproducible reporting.

The main clustering scatter starts in Plotly `lasso` drag mode and keeps rectangle zoom available through the visible chart toolbar and Plotly modebar. `plotly_selected` supplies the selected transparent interaction markers; the browser maps them back to icon IDs, sets `selectedpoints`, dims non-selected layout images, calculates padded ranges around the selected coordinates, and updates the right-side gallery/detail panel. Plotly retains transient lasso paths and selected-marker styling outside application state, so **Clear selection** and **Reset view** clear the application selection and rebuild the scatter from the authoritative projection instead of applying partial `restyle`/`relayout` updates. This reliably removes the boundary, marker styling, dimming, detail gallery, and zoom; Reset remains available after rectangle zoom even when no lasso selection exists. A context key covering variant, method, cluster count, selected features, icon-set filter, and ordered plotted icon IDs prevents a selection from leaking into a changed projection.

## Feature Review Data

The generator computes summary variance/missingness and Spearman correlations for the code-selected analysis preset. With the current seven-feature preset this produces 21 pairs; `full_registry` produces the earlier 3,240-pair review. Bands separate high, moderate, and low redundancy. Feature Values takes its seven feature IDs directly from the Feature Groups representatives and adds correlation context from Feature Review; low-redundancy ranking no longer controls the Feature Values selection.

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

1. Read the shared feature registry first for definition changes, then the relevant computation or UI function in `build_analysis_dashboard.py`.
2. Check `dashboard_data.json` before assuming a field exists.
3. Change reusable logic in `code/thesis_pipeline/` where appropriate.
4. Add or update focused tests.
5. Run `py_compile` and tests.
6. Regenerate the dashboard.
7. Inspect JSON/CSV counts and schemas.
8. Serve the repository and complete the UI walkthrough.
9. Update this wiki when behavior or the data contract changes.
