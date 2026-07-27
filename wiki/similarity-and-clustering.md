# Similarity and Clustering

## Schema-v2 orientation preprocessing

Similarity uses `principal_axis_orientation_v2` as doubled-angle cosine/sine coordinates so 0° and 180° are the same axis. Both coordinates are multiplied by `orientation_confidence_v2`; confidence below 0.20 produces a zero vector (undefined orientation). The bounded similarity regeneration remains limited to the established 1,038-icon cohort. Do not run dense pairwise similarity over all 28,749 icons.

[Wiki home](README.md) · [Feature system](feature-system.md) · [Dashboard UI](dashboard-ui.md)

## Interpretation Boundary

Similarity, PCA, k-means, and hierarchical labels describe relationships in a chosen computer feature space. They are diagnostic predictors of possible visual similarity or confusability. They do not establish semantic equivalence, human agreement, or perceptual causality by themselves.

## Pairwise Similarity Pipeline

The checked-in similarity artifacts were generated from the earlier 1,038-row feature pilot and use only active visual-family channels after transformation. `features.csv` now contains all 28,749 icons; do not run the current quadratic `code/compute_icon_similarity.py` implementation directly on that full file without replacing its dense all-pairs matrices with a scalable approach.

Processing order:

1. Convert the 180-degree principal axis into `cos(2θ)` and `sin(2θ)`.
2. Circularly smooth hue histogram bins with wraparound.
3. Robust-scale continuous columns by median and IQR.
4. Clip robust z-scores to ±5.
5. Center binary flags without variance expansion.
6. Preserve bounded circular components on their native −1 to 1 scale.
7. Apply feature confidence weights.
8. Equalize/weight visual families so large families do not dominate solely by column count.
9. Compute Euclidean and cosine distance matrices.

Current reliability adjustments:

- Texture family weight: 0.75.
- Schema-v2 orientation vectors are scaled per icon by `orientation_confidence_v2` and become zero below 0.20; there is no legacy closure discount.

The exact active columns, transformations, weights, neighbor count, and pair limit are written to `icon_data/analysis/similarity/similarity_metadata.json`.

## Similarity Outputs

| Output | Meaning |
|---|---|
| `pairwise_distance_euclidean.csv` | Square Euclidean distance matrix. |
| `pairwise_distance_cosine.csv` | Square cosine distance matrix. |
| `nearest_neighbors_euclidean.csv` | Ranked nearest icons for every source icon; default five. |
| `closest_pairs_euclidean.csv` | Globally closest unique pairs. |
| `closest_same_set_pairs_euclidean.csv` | Closest pairs within the same source set. |
| `closest_cross_set_pairs_euclidean.csv` | Closest pairs from different source sets. |
| Pair PNGs/contact sheets | Visual checks for top-ranked pairs. |
| `index.html` | Static report linking tables and images. |
| `similarity_metadata.json` | Reproducibility contract for the run. |

Distance is set-relative. A glyph may be visually clear in isolation but difficult to distinguish when a competitor is nearby in the active feature space.

## Dashboard PCA

The dashboard projects the selected feature matrix to two principal components for visualization. PCA coordinates are a lossy 2D view; closeness in the plot is not a complete substitute for full-space distance.

- For the **image** variant, the browser standardizes selected active features and recomputes PCA when selection changes.
- For **metadata** and **combined** variants, PCA coordinates and labels are precomputed in `dashboard_data.json`.

Metadata/combined variants are exploratory context. They must not be described as pure visual-perception spaces.

## Dashboard Clustering

Supported methods:

- **K-means:** groups standardized rows around cluster centers.
- **Hierarchical:** constructs nearest-neighbor linkage structure and cuts it at the requested count. The browser implementation derives a minimum-spanning-tree-style cut; the UI does not show a dendrogram.

Supported counts/cuts: 3, 5, 7, and 10.

Cluster numbers are arbitrary labels, not ordered scores. A cluster explanation reports families and features whose standardized member means are farthest from zero; it is a descriptive aid, not an inferential test.

## Feature Review Correlations

Feature Review computes all pairwise Spearman correlations across 81 active features on the complete 28,749-row feature corpus: 3,240 unique feature pairs. The current artifact reports 42 high, 130 moderate, and 3,068 low pairs.

The view uses absolute correlation to rank redundancy while retaining the sign for interpretation. High correlation does not automatically justify deleting a feature: two features can be mathematically redundant yet differ in interpretability, robustness, or literature role.

## Feature Values Selection

Feature Values shows exactly the same seven representatives used by Feature Groups, one per family. Feature Review correlations remain visible as context, but redundancy ranking no longer determines which features appear in this tab.

For each selected feature, examples come from the full 28,749-row feature corpus:

- low: smallest raw values;
- medium: values nearest the arithmetic mean;
- high: largest raw values.

These bands are representative examples, not quantile bins and not claims about good/bad icons.

## Safe Interpretation Checklist

- State which feature variant, preprocessing, metric, and sample were used.
- Do not call a 2D PCA distance the full visual distance.
- Do not attach semantic meaning to arbitrary cluster numbers.
- Inspect actual icon pairs/examples before treating a metric result as plausible.
- Separate within-set and cross-set comparisons.
- Treat metadata and combined variants as exploratory controls.
- Validate computer-side predictions against human responses before making perception claims.
