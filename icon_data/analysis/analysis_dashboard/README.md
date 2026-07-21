# Analysis Dashboard

Feature Groups now consumes feature schema v2. The seven representatives use corrected foreground masks; strict Red is pixel-derived; orientation has confidence-aware angular ordering and an axial mean; uncertain masks are visibly flagged. Legacy representative columns remain only in the raw feature export. The interface is available for engineering review, but pilot deployment remains blocked pending the frozen two-rater release gate.

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
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html
```

Opening `index.html` directly from the filesystem may work in some browsers, but using a local server is more reliable because the dashboard loads `dashboard_data.json`, `plotly.min.js`, and normalized icon images.

## How The Dashboard Works

The dashboard loads `dashboard_data.json` and renders a Plotly scatter plot.

Each point represents one icon and is displayed using the normalized icon image. The 2D position is based on PCA coordinates for the selected feature variant. A Color By selector exists for cluster, icon set, or numeric feature value, but the current image-overlay renderer does not visibly apply that selection; this is a known UI gap.

The header exposes four views:

- **Clustering** for PCA, feature selection, clustering, filtering, and icon inspection.
- **Feature Groups** for one literature-backed representative per family, with rationale/citation, a fullscreen detail view, All/B/W/Red/Colored filters, and an independent randomizable 20-icon pilot sample per family drawn from all 28,749 feature rows. Each active sample shows its arithmetic mean and orders icons from low to high by the representative feature value.
- **Feature Values** for low, mean-nearest, and high representative examples.
- **Feature Review** for feature variance and Spearman redundancy analysis.

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
- representative icons for visible clusters.

The **Feature Values** tab contains up to two low-redundancy features from each active visual family. Selection reuses Feature Review's Spearman analysis: non-constant features are ranked within each family by their strongest absolute correlation with any other active feature, and the two lowest values are retained. Higher standard deviation and then label break ties. This produces 13 features: two from six families and the single active Texture feature, `local_texture_variation_v2`; excluded LBP channels are not reintroduced merely to fill a second Texture slot. For the selected feature, the tab shows its family uniqueness rank, strongest absolute Spearman correlation, summary statistics, and representative icons in three value bands:

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

## Current Limitations

- A separate dendrogram image has not been generated yet.
- Hierarchical clustering currently uses precomputed cluster labels/cuts, not a full interactive tree.
- The Color By selector is not currently applied to the visible icon-image overlays.
- The current Clustering filter is icon-set-only.
- Clustering uses up to 10 random icons per dataset (129 total). Feature Groups receives a compact pool covering all 28,749 feature rows and displays 20 random icons independently for each family and color treatment; **Randomize icons** replaces only the active family sample. Feature Review and Feature Values also use the complete feature corpus.
- Human-study identification/perception scores are not included in this dashboard yet.
