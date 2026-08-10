# Analysis Dashboard

Feature Groups consumes the current active feature registry and corrected foreground masks. Complexity now uses Canny edge density after the visual audit found raster and antialias inflation in grayscale quadtree variability; quadtree remains available as a secondary Complexity feature. Strict Red is pixel-derived, orientation has confidence-aware angular ordering and an axial mean, and uncertain masks are visibly flagged. The interface is available for engineering review, but pilot deployment remains blocked pending the rebuilt two-rater release gate.

For the comprehensive agent- and contributor-oriented guides, see [Dashboard UI](../../../wiki/dashboard-ui.md) and [Dashboard implementation](../../../wiki/dashboard-implementation.md).

This folder contains the current interactive Plotly dashboard for exploring literature-mapped icon/glyph visual feature families and the computer-side outputs that will be compared against human identification/perception scores.

The dashboard is a static HTML artifact generated from the thesis icon dataset. It is an analysis view for checking whether the current computer-measured visual families behave plausibly before they are compared with human-study scores.

Thesis boundary:

- Active image features are visual factors that can be computed from the glyph image.
- Metadata, semantic labels, familiarity, and historical/cultural meaning are supporting context only.
- Clustering and nearest-neighbor views are diagnostic tools for computer-based similarity/confusability, not the final thesis claim.

## Current State

- Sample size: up to 10 icons per dataset.
- Sampling rule: random sample within each icon set using the fixed dashboard seed.
- Included icon sets in current sample: 13.
- Missing categories: 0.
- Missing metadata tokens: 0.
- Missing normalized image paths: 0.
- Feature extraction failures: 0.
- Clustering methods included:
  - k-means;
  - hierarchical clustering.
- Cluster counts/cuts included:
  - 3;
  - 5;
  - 7;
  - 10.
- Feature variants included:
  - image features only;
  - metadata features only;
  - combined image and metadata features.

The image-feature variant is the primary thesis view. Metadata and combined variants are retained as exploratory/context views and should not be described as visual perception feature families.

## How To Open

From the repository root, start a local server:

```bash
python3 code/serve_analysis_dashboard.py --port 8765
```

Then open:

```text
http://127.0.0.1:8765/
```

Opening `index.html` directly from the filesystem may work in some browsers, but using a local server is more reliable because the dashboard loads `dashboard_data.json`, `plotly.min.js`, and normalized icon images.

## How The Dashboard Works

The dashboard loads `dashboard_data.json` and renders a Plotly scatter plot.

Each point represents one icon and is displayed using the normalized icon image. The 2D position is based on PCA coordinates for the selected feature variant. A Color By selector exists for cluster, icon set, or numeric feature value, but the current image-overlay renderer does not visibly apply that selection; this is a known UI gap.

The header exposes five views:

- **Clustering** for PCA, feature selection, clustering, filtering, and icon inspection.
- **Feature Groups** for one literature-backed representative per family, with rationale/citation, a fullscreen detail view, All/B/W/Red/Colored filters, and an independent randomizable stratified sample drawn from the 28,260 rows with a certain foreground mask. The 489 uncertain-mask rows are excluded before display. For each family/cohort, the eligible feature range is divided into 10 equal-width bins and up to two icons are selected randomly from each bin; empty or undersized bins are not backfilled, so the sample can contain fewer than 20 icons. Genuine zeros remain valid. Cohorts with too little robust variation receive a visible low-information warning. Each active sample shows the average of its visible scores, orders icons from low to high by the representative feature value, and allows exactly three icons to be compared across all seven representative features in a separate fullscreen modal. Representative dropdown changes also replace the corresponding Clustering checkbox and Color-by choice and recompute the Image variant during the current browser session.
- **Feature Values** for low, mean-nearest, and high representative examples.
- **Feature Review** for feature variance and Spearman redundancy analysis.
- **AI Clustering** for explicit OpenRouter image embeddings, paired plots, agreement metrics, and saved run loading.

The left sidebar controls the analysis view:

- **Feature Variant** switches between image-only, metadata-only, and combined feature spaces.
- **Clustering Method** switches between k-means and hierarchical clustering.
- **Cluster Count** switches between the precomputed values 3, 5, 7, and 10.
- **Color By** changes how points are colored.
- **Image Features** lets image features be selected or deselected.
- **Filters** currently restrict the view by icon set. Selected sets appear as pills, and each pill can be removed with its `x` button.

The right sidebar shows:

- selected icon preview and metadata;
- selected feature values;
- McDougall ratings when available;
- cluster summaries;
- up to twelve representative icons for each visible cluster, plus a fullscreen gallery containing all icons in that cluster under the current filter.

The **Feature Values** tab contains exactly the same seven representative features used by Feature Groups, one from each active visual family. Feature Review's Spearman analysis still supplies correlation context for those representatives, but it no longer determines which features appear in Feature Values. For the selected representative, the tab shows its family, strongest absolute Spearman correlation, summary statistics, and representative icons in three value bands:

- low values (smallest measurements);
- medium values (measurements nearest the dataset mean);
- high values (largest measurements).

For the image-only variant, the dashboard can recompute PCA and clustering in the browser when image features are selected or deselected. Metadata-only and combined variants use the precomputed coordinates and cluster labels from `dashboard_data.json`.

## Files

| File | Purpose |
|---|---|
| `index.html` | Main static Plotly dashboard. |
| `assets/plotly.min.js` | Local Plotly bundle so the dashboard works offline. |
| `dashboard_data.json` | Compact data file loaded by the dashboard. |
| `sample_metadata.csv` | Metadata table for the per-dataset random analysis sample. |
| `features_image.csv` | Image feature table. |
| `features_metadata.csv` | Encoded metadata feature table. |
| `features_combined.csv` | Combined image and metadata feature table. |
| `clusters_kmeans.csv` | K-means cluster assignments for all variants and k values. |
| `clusters_hierarchical.csv` | Hierarchical cluster assignments for all variants and cut values. |
| `cluster_assignments.csv` | Combined cluster assignment table for both methods. |
| `cluster_summary.csv` | Cluster size, dominant sets/categories, and representative icon IDs. |
| `feature_failures.json` | Feature extraction failures; currently empty. |
| `analysis_dashboard_metadata_report.json` | Summary of sample coverage and metadata quality. |

## Feature Inputs

Active image feature families currently include:

- Complexity: edge density, quadtree structure, components, contours, holes, perimeter load, and corner count.
- Shape/silhouette: aspect ratio, solidity, closure proxy, circularity, rectangularity, and curvature bins.
- Stroke/structure: line orientation, principal-axis orientation, arrowheads, arcs, skeleton endpoints, and skeleton junctions.
- Density/fill: foreground amount, bounding-box occupancy, filled/outline proxy, and stroke width.
- Balance/layout: centroid offset, symmetry, bounding-box position/size, and 4x4 foreground grid layout.
- Color/contrast: monochrome status, color count, saturation, colorfulness, foreground/background contrast, hue histogram, and dominant Lab colors.
- Texture: foreground tonal entropy.

Excluded raw channels are preserved in source exports but are not active visual-family features: Hu moments, local binary pattern bins, text/letter heuristic scores, and crush-test stability.

Metadata features include encoded values derived from:

- icon set;
- category;
- style label;
- metadata tokens;
- McDougall numeric ratings where available.

Use these metadata fields as context or controls. They are not evidence that the computer has identified semantic meaning in the glyph image.

McDougall rows are enriched from:

```text
icon_data/iconsets/01_mcdougall_symbol_icon_set/metadata/mcdougall_ratings.csv
```

AIGA rows are assigned inferred wayfinding categories from their local labels/Wikimedia metadata.

## Regeneration

The dashboard is generated from the repository root by:

```bash
python code/build_analysis_dashboard.py
```

The script writes outputs back into this folder:

```text
icon_data/analysis/analysis_dashboard/
```

It does not overwrite the older `icon_data/analysis/features.csv` or `icon_data/analysis/similarity/` outputs.

## AI Clustering

The fifth tab uses `code/serve_analysis_dashboard.py` and the exact shared Feature Groups sample. Install `requirements-ai-clustering.txt`, put `OPENROUTER_API_KEY=...` in the ignored repository-root `.env` file (or export it), optionally set `OPENROUTER_AI_CLUSTERING_MODEL`, then open `http://127.0.0.1:8765/`. The server also accepts the older nested dashboard URL and serves its `/icon_data/normalized_256/` image paths. The official OpenRouter Python SDK sends normalized pixels only, compares feature and embedding clusterings side by side, and stores cache/history in `../ai_clustering/ai_clustering.sqlite3`. Checked Clustering features affect only the feature-based half of the next explicit comparison run; the AI half continues to use full image embeddings. ARI, NMI, and provider usage are stored but currently hidden in the UI. Agreement metrics do not establish that either result is objectively better.

## Current Limitations

- A separate dendrogram image has not been generated yet.
- Hierarchical clustering currently uses precomputed cluster labels/cuts, not a full interactive tree.
- The Color By selector is not currently applied to the visible icon-image overlays.
- The current Clustering filter is icon-set-only.
- Image and AI Clustering use a unique seven-family composite: up to 20 equal-width-stratified icons from each family, verified as 140 icons for the default All cohort. Feature Groups receives a compact pool covering the 28,260 certain-mask feature rows, makes 10 equal-width bins across each family range, and randomly selects up to two icons per bin; **Randomize icons** replaces only the active family's contribution. Metadata/Combined keep the generated 129-row projections, comparison selection is limited to three active-family icons, and Feature Review/Values use the complete feature corpus.
- Human-study identification/perception scores are not included in this dashboard yet.
