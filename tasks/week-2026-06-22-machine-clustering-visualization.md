# Weekly Task: Machine-Based Icon Clustering and Visualization

Date: 2026-06-22

## Summary

This week focuses on improving the icon/glyph similarity work by replacing score-only outputs with clustering-based visualizations. The scope is machine-only for now: use computed image features, embeddings, and available metadata to group icons, interpret clusters, and produce clearer figures for discussion with the supervisor.

The working goal is:

> Use metadata and machine clustering to discover, visualize, and explain structure in the icon dataset.

Human verification is explicitly out of scope for this week.

## Main Deliverable

Prepare a small clustering report with:

- a cleaned metadata table for the selected icon sample;
- k-means clustering results;
- hierarchical clustering results;
- 2D cluster visualizations;
- cluster summaries using metadata;
- representative icon examples for each cluster.

## Current Progress

Updated: 2026-06-22

- Task 1 is complete.
- Created a reproducible metadata builder:
  - `scripts/build_clustering_metadata_sample.py`
- Generated the clustering metadata sample:
  - `icon_data/analysis/clustering_metadata_sample.csv`
- Generated the metadata coverage report:
  - `icon_data/analysis/clustering_metadata_missing_report.json`
- The clustering sample contains 855 rows, matching the current `features.csv` balanced pilot sample.
- All source image paths and normalized image paths resolve.
- McDougall and AIGA category gaps were checked and fixed in the clustering metadata sample:
  - McDougall rows are enriched from `icon_data/iconsets/01_mcdougall_symbol_icon_set/metadata/mcdougall_ratings.csv`.
  - AIGA rows are categorized from available local labels/Wikimedia metadata into wayfinding groups.
  - McDougall missing categories: 0 of 100 sample rows.
  - AIGA missing categories: 0 of 80 rows.
- McDougall rows now include rating fields for later analysis:
  - concreteness;
  - complexity;
  - familiarity;
  - meaningfulness;
  - semantic distance;
  - concept agreement;
  - name agreement;
  - common response.
- Remaining metadata gaps are notes-only gaps in some sets; these do not block clustering because every row has category information and `metadata_tokens`.
- Analysis dashboard implementation has started and the proposed Plotly direction is implemented as a first working static dashboard.
- Added a new analysis dashboard builder:
  - `scripts/build_analysis_dashboard.py`
- Generated new dashboard outputs under:
  - `icon_data/analysis/analysis_dashboard/`
- The analysis sample uses max 100 icons per set and now includes all 13 icon sets:
  - McDougall;
  - AIGA;
  - Mapbox;
  - OCHA;
  - Mulberry;
  - Blissymbolics;
  - ARASAAC;
  - GHS;
  - Healthcare webfont;
  - OpenMoji;
  - ISO 7010;
  - ISO 15223;
  - USP.
- Analysis dashboard sample size: 1,038 icons.
- Analysis dashboard data checks:
  - missing categories: 0;
  - missing metadata tokens: 0;
  - missing normalized paths: 0;
  - feature extraction failures: 0.
- Generated analysis dashboard feature representations:
  - `icon_data/analysis/analysis_dashboard/features_image.csv`
  - `icon_data/analysis/analysis_dashboard/features_metadata.csv`
  - `icon_data/analysis/analysis_dashboard/features_combined.csv`
- Generated k-means outputs for image, metadata, and combined feature variants:
  - `icon_data/analysis/analysis_dashboard/clusters_kmeans.csv`
  - k values: 3, 5, 7, 10.
- Generated hierarchical clustering outputs for image, metadata, and combined feature variants:
  - `icon_data/analysis/analysis_dashboard/clusters_hierarchical.csv`
  - k/cut values: 3, 5, 7, 10.
- Generated dashboard files:
  - `icon_data/analysis/analysis_dashboard/dashboard_data.json`
  - `icon_data/analysis/analysis_dashboard/index.html`
  - `icon_data/analysis/analysis_dashboard/assets/plotly.min.js`
- The Plotly dashboard supports:
  - image feature selection/deselection;
  - image-only, metadata-only, and combined variants;
  - k-means and hierarchical cluster switching;
  - k/cut selection;
  - coloring by cluster, icon set, category, style label, or numeric image feature;
  - multi-select filtering by icon set, category, and style;
  - selected-filter pills with `x` removal for icon sets, categories, and styles;
  - clearing individual filters and resetting all filters;
  - icon detail inspection;
  - cluster summary panels.
- Local verification server:
  - `http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html`
- Validation completed:
  - JavaScript syntax check passed;
  - dashboard data contains 1,038 rows;
  - k-means assignment rows: 12,456;
  - hierarchical assignment rows: 12,456;
  - local Plotly asset is vendored.
- Dashboard image path issue was fixed after local server logs showed normalized icon image 404s.
- Final HTTP checks passed:
  - `dashboard_data.json` serves 1,038 rows;
  - normalized icon PNG URLs return `200 OK`;
  - `plotly.min.js` is available locally.

## Task 1: Prepare The Icon Metadata Table

- [x] Identify the current canonical dataset file, expected to be `icon_data/analysis/dataset.csv`.
- [x] Confirm that every selected icon row has an accessible image path.
- [x] Collect useful metadata fields where available:
  - icon id;
  - icon name;
  - file path;
  - source icon set;
  - category or domain label;
  - style label, if available;
  - tags or keywords, if available;
  - file format;
  - normalized image path.
- [x] Create or update a machine-readable metadata table for the clustering sample.
- [x] Record missing metadata fields so they are visible in the final report.

Expected output:

- `icon_data/analysis/clustering_metadata_sample.csv`
- `icon_data/analysis/clustering_metadata_missing_report.json`

## Task 2: Define Machine Feature Representations

- [x] Select the feature inputs to use for clustering.
- [x] Include image-based features already used in the metrics pipeline where available:
  - foreground area ratio;
  - bounding-box occupancy;
  - edge density;
  - connected components;
  - quadtree structural variability;
  - symmetry metrics;
  - contour or perimeter features;
  - compression ratio;
  - filled-vs-outline proxy.
- [x] Include metadata-derived features where available:
  - source set;
  - category label;
  - icon name tokens;
  - tags or keywords.
- [x] Build three feature variants if feasible:
  - image features only;
  - metadata/text features only;
  - combined image and metadata features.
- [x] Standardize numeric features before distance computation or clustering.

Expected outputs:

- `icon_data/analysis/clustering_features_image.csv`
- `icon_data/analysis/clustering_features_metadata.csv`
- `icon_data/analysis/clustering_features_combined.csv`

## Task 3: Run K-Means Clustering

- [x] Run k-means on the selected feature representation.
- [x] Test several values of `k`, such as 3, 5, 7, and 10.
- [x] Compute an internal quality score for each `k`, preferably silhouette score.
- [x] Select one primary `k` for the report and keep the alternatives for comparison.
- [x] Save cluster assignments for each icon.
- [x] Summarize cluster sizes and dominant metadata fields.

Expected outputs:

- `icon_data/analysis/kmeans_cluster_assignments.csv`
- `icon_data/analysis/kmeans_cluster_summary.csv`
- `icon_data/analysis/kmeans_model_selection.csv`

## Task 4: Run Hierarchical Clustering

- [x] Compute pairwise distances between selected icons.
- [x] Run hierarchical clustering using an appropriate linkage method.
- [ ] Generate a dendrogram for the selected sample.
- [x] Cut the hierarchy at one or more levels to produce cluster labels.
- [x] Save hierarchical cluster assignments.
- [x] Compare the hierarchical grouping with the k-means grouping.

Expected outputs:

- `icon_data/analysis/hierarchical_cluster_assignments.csv`
- `icon_data/analysis/hierarchical_cluster_summary.csv`
- `icon_data/analysis/figures/hierarchical_dendrogram.png`

## Task 5: Create Better Visualizations

- [ ] Reduce the feature space to 2D using PCA, UMAP, or t-SNE.
- [ ] Create a 2D scatter plot colored by k-means cluster.
- [ ] Create a 2D scatter plot colored by icon source set or metadata category.
- [ ] Create a cluster summary grid with representative icons per cluster.
- [ ] Create a distance or similarity heatmap for a small readable subset.
- [ ] Add clear captions explaining what each visualization shows.

Recommended primary figures:

- 2D embedding plot colored by machine cluster;
- 2D embedding plot colored by metadata category or source set;
- hierarchical dendrogram;
- representative-icon grid per cluster.

Expected outputs:

- `icon_data/analysis/figures/kmeans_embedding_plot.png`
- `icon_data/analysis/figures/metadata_embedding_plot.png`
- `icon_data/analysis/figures/cluster_representatives.png`
- `icon_data/analysis/figures/similarity_heatmap_subset.png`

## Task 6: Interpret Clusters Using Metadata

- [ ] For each cluster, count the most common source sets.
- [ ] For each cluster, count the most common categories, tags, or name tokens.
- [ ] Identify whether clusters mainly reflect:
  - visual structure;
  - semantic category;
  - source dataset or style;
  - mixed or unclear grouping.
- [ ] Select representative icons closest to each cluster centroid.
- [ ] Write a short interpretation for each cluster.

Expected output:

- `icon_data/analysis/cluster_interpretation.md`

Suggested cluster interpretation format:

```text
Cluster 1:
- Size:
- Dominant metadata:
- Representative icons:
- Interpretation:
- Notes:
```

## Task 7: Compare Feature Variants

- [ ] Compare image-only clustering against metadata-only clustering.
- [ ] Compare image-only clustering against combined image-plus-metadata clustering.
- [ ] Note whether metadata improves interpretability.
- [ ] Identify cases where metadata dominates the grouping too strongly.
- [ ] Select the most useful feature representation for the supervisor-facing figures.

Expected output:

- `icon_data/analysis/feature_variant_comparison.md`

## Task 8: Prepare Supervisor-Facing Summary

- [ ] Write a concise summary of what changed after supervisor feedback.
- [ ] Explain why clustering is more informative than raw cosine or Euclidean scores alone.
- [ ] Describe the role of metadata in interpreting machine clusters.
- [ ] Include the final figures and a short caption for each.
- [ ] State the next possible step after machine analysis, without including human verification yet.

Expected output:

- `tasks/week-2026-06-22-machine-clustering-supervisor-summary.md`

## Priority Order

1. Prepare the metadata table.
2. Select image and metadata feature representations.
3. Run k-means clustering.
4. Run hierarchical clustering.
5. Generate 2D clustering visualizations.
6. Summarize clusters using metadata.
7. Compare image-only, metadata-only, and combined clustering.
8. Prepare the supervisor-facing summary.

## Success Criteria

- The work produces visual outputs, not only numerical distance tables.
- Every cluster can be inspected through representative icons.
- Metadata is used to explain clusters rather than manually judge them.
- K-means and hierarchical clustering are both attempted.
- The final figures make the icon groupings easier to understand at a glance.
- Human verification remains a future step, not part of this week's scope.
