# Dashboard UI

## Feature Groups under schema v2

Feature Groups displays schema v2 and uses the seven corrected representatives. Scalar samples are sorted numerically and use arithmetic means. Orientation is explicitly shown as angular order from 0° to 180°, uses an axial circular mean, and places confidence-below-0.20 values last as **Undefined** with confidence shown. Icons whose foreground mask is flagged uncertain are excluded from the Feature Groups population, so they cannot appear in samples, averages, or comparisons.

The Red cohort is pixel-derived only: `strict_red_flag_v2 == 1`. Dataset names and labels no longer classify icons as red. All/B/W/Red/Colored selection still persists across families; each family retains an independent dataset-balanced draw of up to 20 icons.

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
3. **Feature Values** — low/medium/high examples for the same seven representatives used by Feature Groups.
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

The main view stays concise. It presents the seven human-facing categories and one representative selector for each family. The configured choices remain the documented study defaults. Choosing another active feature in a family is a browser-session exploratory override: the Clustering view immediately selects the current seven representatives, clears its cached projection, and recomputes PCA and K-means or hierarchical clustering without a page refresh. Reloading restores the configured defaults. Each family row also has a **View details** button that opens a full-viewport detail workspace containing:

- the one selected feature and its feature ID;
- how to interpret it and why it is active; configured defaults also show their supporting evidence and page-level literature citation;
- up to 20 dataset-balanced icons drawn independently for that family from the 28,128 icons with a certain foreground mask;
- **All**, **B/W**, **Red**, and **Colored** icon-treatment filters with live counts.
- a **Randomize icons** action that replaces the active family's sample;
- a three-icon comparison: select exactly three cards to open a separate fullscreen modal containing their representative measurements across all seven feature families.

Each family/color-treatment combination keeps its own transient random sample. Icon slots are allocated as evenly as possible across the eligible datasets before an icon is drawn within each selected dataset. With 13 eligible datasets and a 20-icon target, every dataset receives one slot before seven datasets receive a second slot. Cohorts with fewer eligible datasets distribute additional slots as evenly as dataset capacity permits. Session-level draw counts rotate exposure across repeated randomizations, while per-dataset shuffled icon queues reduce immediate icon repetition. The selected icons are then sorted from low to high by the selected feature, and every icon card shows its raw value. The selected representatives are Canny edge density, enclosure score v2, principal-axis orientation v2, solid-fill ratio v2, horizontal symmetry v2, foreground mean saturation v2, and local texture variation v2. This one-feature presentation does not shrink the full 81-feature registry used elsewhere in the dashboard.

The 28,128-row Feature Groups payload remains compact and carries the seven configured representative values. If any representative is overridden, family galleries and the three-icon comparison temporarily use the 129-row clustering sample because it contains values for all 81 selectable features. Returning all selectors to their configured defaults restores the full certain-mask population. Alternate choices are explicitly presented as exploratory; the literature rationale and citation remain attached only to each configured default.

Immediately above the ordered icons, **Average of shown icons** reports the arithmetic mean of scalar representative-feature values for the currently visible icons. Orientation uses an axial circular mean over defined values instead. It is not the mean of either the full 28,749-icon corpus or the 28,128-icon certain-mask population, and recalculates after Randomize or a color-treatment change.

The B/W filter uses the extractor's `is_monochrome` value. Red uses only the pixel-derived `strict_red_flag_v2`; dataset names and labels do not classify an icon as red. The current pool contains only 10 strict-red records, so Red displays those 10 rather than 20. Colored contains the remaining non-monochrome icons. Color treatment is an icon-level viewing filter and does not change which measurements belong to the selected feature family. The selected treatment persists while moving among the seven family details, so choosing **Red** constrains every subsequently opened family to that cohort while still giving each family its own draw of up to 20 icons.

Comparison selection is limited to the current sample. The fourth selection is disabled until one of the three selected icons is deselected. Selecting the third icon opens a new fullscreen comparison modal with the three images and all seven representative-feature values; undefined low-confidence orientations are labeled **Undefined**. Close that modal with its close button or **Escape** to return to the still-selected cards, then use **View fullscreen comparison** to reopen it. Changing the family, color treatment, or random sample clears the selection so stale or hidden icons are never compared.

The detail workspace fills the browser viewport on desktop and mobile. Its header and filter bar remain visible while the icon content area scrolls. Close it with its close button or with **Escape**. Keyboard focus returns to the family button that opened it.

Use it when explaining the thesis organization or checking that a proposed measurement belongs to a visual family.

## Feature Values View

This view uses the complete 28,749-row feature corpus rather than the 129-row clustering sample.

Controls:

- search by label, feature ID, or family;
- select from the matching feature list;
- click a correlation partner to jump to it when that partner is also one of the seven representatives.

For the selected feature the page shows:

- family and meaning;
- confirmation that it is the Feature Groups representative;
- strongest absolute Spearman correlation;
- min, mean, max, variance, standard deviation, and missing count;
- six low-value, six mean-nearest, and six high-value examples;
- strongest positive and negative correlation partners.

The current selection contains exactly seven features: the one representative used by Feature Groups for each family. Medium means nearest to the overall mean, not the middle quantile.

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
8. Change Complexity from Edge density to Quadtree leaf count. Return to Clustering and confirm exactly seven feature checkboxes are selected, Quadtree leaf count is selected instead of Edge density, and the K-means plot and summaries render without reloading.
9. Return to Feature Groups, open Complexity details, and confirm the override is described as exploratory and uses the 129-row clustering population. Restore Edge density and confirm the full certain-mask population returns.
10. With All selected, confirm the default gallery shows 20 icons spanning all 13 datasets, ordered from low to high, and that none has `mask_is_uncertain == true`. Independently calculate their arithmetic mean to confirm **Average of shown icons**. Click **Randomize icons** and confirm a different dataset-balanced set and updated average replace them.
11. Select three icons and confirm a separate fullscreen comparison modal opens with three images and seven representative-feature rows. Close it with **Escape**, confirm focus returns to the selected card, and reopen it with **View fullscreen comparison**. Confirm a fourth icon cannot be selected; deselect one and confirm another becomes selectable.
12. Switch among B/W, Red, and Colored, and confirm the population count, gallery, and comparison selection reset. Red currently shows all 10 eligible strict-red icons because that cohort is smaller than the 20-icon target. Leave Red selected, close with **Escape**, and open another family; confirm Red remains selected but the family has its own draw. Confirm focus returns to the originating button after each close.
13. Open Feature Values and confirm the selector contains exactly the seven configured Feature Groups representatives. Search for “saturation,” select Mean saturation, and confirm low/medium/high cards load.
14. Open Feature Review, change sort and threshold, select a feature, and confirm details update.
15. Record the Color By limitation if testing current behavior; do not mark visible recoloring as verified.

For automated browser work, use the repository's Playwright skill and keep the server running in a separate terminal session.

## Common Misreadings

- A cluster is not a semantic class.
- PCA proximity is not the complete high-dimensional distance.
- Metadata and combined variants are not pure visual feature spaces.
- Low and high feature values are descriptive, not quality judgments.
- Correlation is not causation and redundancy is not automatically a defect.
- The dashboard does not yet include participant-response results.
