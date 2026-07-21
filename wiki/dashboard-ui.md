# Dashboard UI

## Feature Groups under schema v2

Feature Groups displays schema v2 and uses the seven corrected representatives. Scalar samples are sorted numerically and use arithmetic means. Orientation is explicitly shown as angular order from 0° to 180°, uses an axial circular mean, and places confidence-below-0.20 values last as **Undefined** with confidence shown. An uncertain foreground mask adds a visible warning to the icon card.

The Red cohort is pixel-derived only: `strict_red_flag_v2 == 1`. Dataset names and labels no longer classify icons as red. All/B/W/Red/Colored selection still persists across families; each family retains an independent random 20-icon draw.

[Wiki home](README.md) · [Dashboard implementation](dashboard-implementation.md) · [Verification](verification-and-troubleshooting.md)

## Open the Dashboard

From the repository root:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html
```

The dashboard is a static Plotly application. It fetches `dashboard_data.json` and local icon images, so a local HTTP server is more reliable than opening `index.html` directly.

## Views

The header contains four views:

1. **Clustering** — interactive PCA layout, feature selection, clustering, filtering, icon inspection, and cluster summaries.
2. **Feature Groups** — concise mapping from human-facing categories to computer feature families.
3. **Feature Values** — representative low/medium/high examples for selected low-redundancy features.
4. **Feature Review** — feature variance and Spearman redundancy analysis.

## Clustering View

### Initial State

The default variant is Image, method is K-means, cluster count is the configured primary value, and no image features are selected. The plot therefore initially asks the user to select one or more features. Use **All** or a family preset to populate it.

### Feature Variant

| Variant | Inputs | Behavior |
|---|---|---|
| Image | Selected active image features | Browser recomputes standardization, PCA, and clustering after selection changes. |
| Metadata | Encoded set/category/style/tokens and supported ratings | Uses precomputed coordinates and labels. Image checkboxes do not change this projection. |
| Combined | Image and metadata matrices | Uses precomputed coordinates and labels. Treat as exploratory context. |

The Image variant is the primary thesis-facing view.

### Clustering Controls

- **Method:** K-Means or Hierarchical.
- **Cluster count:** 3, 5, 7, or 10.
- **Color by:** control is populated with cluster, icon set, and numeric image features.

Current implementation caveat: icons are rendered as Plotly layout images over nearly transparent interaction markers, and `state.color` is not currently applied to the visible images. The Color By selection therefore does not visibly recolor the plot in the current generated UI. Treat this as a known UI gap, not as working behavior.

### Image Features

The sidebar exposes all 81 active features, grouped into seven families. Available actions:

- **All** preset;
- one preset per visual family;
- **Select all** or **Clear** within a family;
- individual feature checkboxes;
- hover/focus tooltips with meaning, visual categorization, examples, and grouping rationale.

Any image-feature selection change clears the computed projection cache and recomputes the image view. Selecting zero image features returns the empty-state message.

### Filters

The current UI filters by **icon set only**. The multi-select supports toggling multiple options; chosen sets appear as removable pills. **Clear sets** and **Reset filters** both return to all sets.

Some older documentation mentions category and style filters. Those controls are not present in the current generated HTML and should not be described as current UI behavior.

### Plot Interaction

Each icon is displayed at its PCA coordinates as the normalized image itself, with a transparent marker underneath for Plotly interaction.

- Hover: preview image, label, source set, cluster, and up to ten selected feature values.
- Click: select the icon and populate the right-side detail panel.
- Plot axes: PCA 1 and PCA 2 for the current projection.

The selected-icon panel shows the icon, label, set, cluster, values for all visible active features, family interpretations, McDougall ratings when present, and metadata tokens.

The cluster-summary panel lists visible clusters, current filtered counts, dominant sets, standardized distinctive families/features, and up to twelve representative icons. “Distinctive” means far from the sample mean in standardized feature space; it is descriptive, not causal.

## Feature Groups View

The main view stays concise. It presents the seven human-facing categories and exactly one current representative feature for each family. Each family row has a **View details** button that opens a full-viewport detail workspace containing:

- the one selected feature and its feature ID;
- how to interpret it, why it was selected, the supporting evidence, and a page-level literature citation;
- 20 random icons drawn independently for that family from the complete 28,749-icon feature corpus;
- **All**, **B/W**, **Red**, and **Colored** icon-treatment filters with live counts.
- a **Randomize icons** action that replaces the active family's 20-icon sample.

Each family/color-treatment combination keeps its own transient random sample. The 20 selected icons are sorted from low to high by the selected feature, and every icon card shows its raw value. The selected representatives are intensity quadtree variability v2, enclosure score v2, principal-axis orientation v2, solid-fill ratio v2, horizontal symmetry v2, foreground mean saturation v2, and local texture variation v2. This one-feature presentation does not shrink the full 81-feature registry used elsewhere in the dashboard.

Immediately above the ordered icons, **Sample average** reports the arithmetic mean of scalar representative-feature values for the currently visible 20 icons. Orientation uses an axial circular mean over defined values instead. It is a sample statistic, not the mean of the full 28,749-icon population, and recalculates after Randomize or a color-treatment change.

The B/W filter uses the extractor's `is_monochrome` value. Red uses only the pixel-derived `strict_red_flag_v2`; dataset names and labels do not classify an icon as red. The current full-corpus pool contains 10 strict-red records. Colored contains the remaining non-monochrome icons. Color treatment is an icon-level viewing filter and does not change which measurements belong to the selected feature family. The selected treatment persists while moving among the seven family details, so choosing **Red** constrains every subsequently opened family to that cohort while still giving each family its own draw of up to 20 icons.

The detail workspace fills the browser viewport on desktop and mobile. Its header and filter bar remain visible while the icon content area scrolls. Close it with its close button or with **Escape**. Keyboard focus returns to the family button that opened it.

Use it when explaining the thesis organization or checking that a proposed measurement belongs to a visual family.

## Feature Values View

This view uses the complete 28,749-row feature corpus rather than the 129-row clustering sample.

Controls:

- search by label, feature ID, or family;
- select from the matching feature list;
- click a correlation partner to jump to that feature when it is one of the included explorer features.

For the selected feature the page shows:

- family and meaning;
- uniqueness rank within the family;
- strongest absolute Spearman correlation;
- min, mean, max, variance, standard deviation, and missing count;
- six low-value, six mean-nearest, and six high-value examples;
- strongest positive and negative correlation partners.

The current selection includes up to two low-redundancy features from each family, 13 total. Medium means nearest to the overall mean, not the middle quantile.

## Feature Review View

This view also uses the complete 28,749-row feature corpus.

Controls:

- **Feature ranking:** strongest redundancy, group, or feature name.
- **Pair threshold:** high only, moderate and high, or all pairs.

Summary cards show active feature count, high-redundancy pair count, moderate pair count, and source rows.

The ranking table shows each feature's family, redundancy band, strongest absolute correlation, strongest partner, standard deviation, and missing count. Selecting a feature opens its details and top eight correlation partners.

The pair table shows both features, redundancy band, signed Spearman rho, whether they share a family, and pairwise sample size.

## Agent-Oriented UI Walkthrough

For a basic browser verification:

1. Confirm the dataset summary reports 129 icons and 10 random per dataset.
2. In Clustering, click **All** and confirm icon images and both PCA axes appear.
3. Switch between K-Means and Hierarchical, then between two cluster counts; confirm summaries change without console errors.
4. Select one icon set and confirm the plot and cluster counts shrink; remove its pill and confirm all icons return.
5. Hover and click an icon; confirm preview and details include a valid image.
6. Open Feature Groups and confirm seven representative-feature mappings and seven **View details** buttons appear.
7. Open every family and confirm exactly one selected-feature panel, an evidence citation, and per-icon values appear; confirm the feature matches the representative table in [Feature system](feature-system.md#current-one-feature-representatives).
8. Confirm the gallery shows 20 icons ordered from low to high, and independently calculate their arithmetic mean to confirm **Sample average**. Click **Randomize icons** and confirm a different 20-icon set and updated average replace them.
9. Switch among B/W, Red, and Colored, and confirm the population count and gallery change. Leave Red selected, close with **Escape**, and open another family; confirm Red remains selected but the family has its own 20-icon draw. Confirm focus returns to the originating button after each close.
10. Open Feature Values, search for “edge,” select Edge density, and confirm low/medium/high cards load.
11. Open Feature Review, change sort and threshold, select a feature, and confirm details update.
12. Record the Color By limitation if testing current behavior; do not mark visible recoloring as verified.

For automated browser work, use the repository's Playwright skill and keep the server running in a separate terminal session.

## Common Misreadings

- A cluster is not a semantic class.
- PCA proximity is not the complete high-dimensional distance.
- Metadata and combined variants are not pure visual feature spaces.
- Low and high feature values are descriptive, not quality judgments.
- Correlation is not causation and redundancy is not automatically a defect.
- The dashboard does not yet include participant-response results.
