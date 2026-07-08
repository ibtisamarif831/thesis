# Analysis Dashboard

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
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html
```

Opening `index.html` directly from the filesystem may work in some browsers, but using a local server is more reliable because the dashboard loads `dashboard_data.json`, `plotly.min.js`, and normalized icon images.

## How The Dashboard Works

The dashboard loads `dashboard_data.json` and renders a Plotly scatter plot.

Each point represents one icon. The 2D position is based on PCA coordinates for the selected feature variant. The point color can represent a cluster, icon set, category, style label, or numeric feature value.

The left sidebar controls the analysis view:

- **Feature Variant** switches between image-only, metadata-only, and combined feature spaces.
- **Clustering Method** switches between k-means and hierarchical clustering.
- **Cluster Count** switches between the precomputed values 3, 5, 7, and 10.
- **Color By** changes how points are colored.
- **Image Features** lets image features be selected or deselected.
- **Filters** restrict the view by icon set, category, or style. Selected filters appear as pills below each filter, and each pill can be removed with its `x` button.

The right sidebar shows:

- selected icon preview and metadata;
- selected feature values;
- McDougall ratings when available;
- cluster summaries;
- representative icons for visible clusters.

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

The dashboard is generated by:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/build_analysis_dashboard.py
```

The script writes outputs back into this folder:

```text
icon_data/analysis/analysis_dashboard/
```

It does not overwrite the older `icon_data/analysis/features.csv` or `icon_data/analysis/similarity/` outputs.

## Current Limitations

- A separate dendrogram image has not been generated yet.
- Hierarchical clustering currently uses precomputed cluster labels/cuts, not a full interactive tree.
- The dashboard is currently generated from up to 10 random icons per dataset, not the full 28,749-icon dataset.
- Human-study identification/perception scores are not included in this dashboard yet.
