# Dashboard UI

## Feature Groups under schema v2

Feature Groups displays schema v2 and uses the seven corrected representatives. Scalar samples are sorted numerically and use arithmetic means. Orientation is explicitly shown as angular order from 0° to 180° and uses an axial circular mean. When principal-axis orientation is selected, confidence-below-0.20 records are removed from that family's counts and sampling population, so the gallery contains only icons with defined orientations and does not show **Undefined** cards. Icons whose foreground mask is flagged uncertain are excluded from the complete Feature Groups population, so they cannot appear in samples, averages, or comparisons. Missing and non-finite representative values are also ineligible, but genuine numeric zeros remain valid measurements.

The Red cohort is pixel-derived only: `strict_red_flag_v2 == 1`. Dataset names and labels no longer classify icons as red. All/B/W/Red/Colored selection still persists across families; each family retains an independent equal-width stratified random draw.

[Wiki home](README.md) · [Dashboard implementation](dashboard-implementation.md) · [Verification](verification-and-troubleshooting.md)

## Open the Dashboard

From the repository root:

```powershell
python code/serve_analysis_dashboard.py --port 8765
```

Then open:

```text
http://127.0.0.1:8765/
```

The generated dashboard is a Plotly application. The repository service serves its JSON and normalized icons and enables the optional local AI API. Opening `index.html` directly remains unreliable.

## Views

The header contains five views:

1. **Clustering** — interactive PCA layout, feature selection, clustering, filtering, icon inspection, and cluster summaries.
2. **Feature Groups** — concise mapping from human-facing categories to computer feature families.
3. **Feature Values** — low/medium/high examples for the same seven representatives used by Feature Groups.
4. **Feature Review** — feature variance and Spearman redundancy analysis.
5. **AI Clustering** — explicit feature-versus-image-embedding comparison for the current shared sample.

## Clustering View

### Initial State

The default variant is Image, method is K-means, cluster count is the configured primary value, and all seven family representatives are selected. Its icon population is the unique composite of the seven cached equal-width-stratified family samples for the active cohort: up to 20 icons per family and 140 for the default All cohort. The header reports the shared icon count, seven families, and cohort.

### Feature Variant

| Variant | Inputs | Behavior |
|---|---|---|
| Image | Selected active image features over the shared Feature Groups icon sample | Browser recomputes standardization, PCA, and clustering after feature or shared-sample changes. |
| Metadata | Encoded set/category/style/tokens and supported ratings | Uses precomputed coordinates and labels. Image checkboxes do not change this projection. |
| Combined | Image and metadata matrices | Uses precomputed coordinates and labels. Treat as exploratory context. |

The Image variant is the primary thesis-facing view.

### Clustering Controls

- **Method:** K-Means or Hierarchical.
- **Cluster count:** 3, 5, 7, or 10.
- **Color by:** control is populated with cluster, icon set, and only the seven configured family representatives.

Current implementation caveat: icons are rendered as Plotly layout images over nearly transparent interaction markers, and `state.color` is not currently applied to the visible images. The Color By selection therefore does not visibly recolor the plot in the current generated UI. Treat this as a known UI gap, not as working behavior.

### Image Features

The sidebar exposes one current representative per family. It starts with the seven code-selected IDs in `metadata.image_feature_columns`, all checked. Choosing another representative in Feature Groups replaces that family's sidebar checkbox and, if the previous representative was checked, keeps the replacement checked. Browser-side PCA and clustering then recompute with the current representative set. The 81-feature registry remains available to the Feature Groups selectors, but only the seven current representatives can be enabled in Clustering at one time. Available actions:

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

- Hover: preview image, label, source set, cluster, and up to ten compact selected-feature rows. Each row shows the feature name, a high-contrast white raw value, middle-50% band, and icon/global-median markers without repeating the statistical prose.
- Click: select the icon and populate the right-side detail panel with one compact row per family: the representative feature name, raw value, and comparison track. The family interpretation stays in the left Feature Groups sidebar instead of being repeated here.
- **Lasso select** (the default drag mode): draw a free-form boundary around icons. The chart zooms to the selected points, dims every icon outside the selection, and changes the right panel into a scrollable selected-icon gallery. Above the gallery, seven comparison tracks place each lasso-selected group median against the full clustering sample median. Clicking a gallery icon shows its complete individual detail below the group comparison.
- **Rectangle zoom:** preserves the previous rectangular zoom interaction without changing the lasso selection.
- **Clear selection:** removes the lasso boundary, selected-marker styling, dimming, details gallery, and selection zoom, returning to the complete PCA view. **Reset view** provides the same clean full-chart reset after either lasso selection or rectangle zoom, even when there is no active selection.
- Plot axes: PCA 1 and PCA 2 for the current projection.
- Icon scale: each image occupies 5.5% of the displayed PCA span on both axes. Manual Image and AI plots use this same scale so visual density is directly comparable.

The left controls sidebar can be collapsed with **Hide sidebar** and restored with **Show sidebar** from the chart toolbar; the plot resizes to use the released width. The selected-icon panel shows the icon, label, set, cluster, and a compact value/comparison bar for each of the seven representatives, plus McDougall ratings when present and metadata tokens. It intentionally omits the repeated family description, human-perception, Low, High, percentile, quartile, range-label, and legend prose; the detailed family interpretation remains available in Feature Groups. The dark and colored markers still compare against the complete current clustering sample—140 icons for the default All Image/AI cohort—not the 28,749-row feature corpus and not only the currently icon-set-filtered subset. Principal-axis orientation remains **Undefined** when its confidence is too low and is excluded from orientation-specific sampling and summaries rather than reinterpreted as 0°. A lasso selection additionally reports its icon count and leading source sets and exposes every selected icon as an inspectable thumbnail; its seven group-median comparisons use the same compact bars. Changing the projection inputs, clustering method/count, shared sample, or icon-set filter clears a stale lasso selection automatically.

The right cluster-summary panel lists every assigned cluster as a compact button. Each entry shows its descriptive profile, full icon count, current filter-visible count when different, and variance contribution. Selecting a cluster opens a dedicated fullscreen modal for that cluster only; the sidebar never expands large statistics inline and there is no combined all-cluster detail view. Each arbitrary numeric cluster ID receives a neutral descriptive suffix from its two largest absolute deviations, such as **High Mean saturation / Low Local texture variation**. These are measured visual profiles, not semantic class names.

Every expanded cluster reports its full size, size-weighted contribution to total between-cluster variance, and size-independent separation strength. Contribution is `n_c × ||mean_c - mean_all||²` divided by that quantity summed across clusters, so large clusters can contribute more. Separation strength is the mean squared standardized centroid deviation across the selected features, so a small but unusual cluster can still score highly.

The signed-z heatmap control has been removed from both Image and AI Clustering. Cluster interpretation remains available through the descriptive labels and the feature-statistics table's cluster mean, overall mean, and signed difference.

Two statistics blocks make the cluster population explicit. **Icon statistics** reports icons in the full assigned cluster, share of the complete clustering sample, currently filter-visible icons, number of represented icon sets, dominant set, and dominant-set share. **Feature statistics** reports one row per selected Image feature with valid `N`, raw cluster mean, median, population standard deviation, minimum, maximum, full-sample mean, and the signed standardized cluster-to-overall difference. Only **Currently visible** responds to icon-set filtering; the remaining statistics continue to describe the assigned cluster. Metadata and Combined retain icon statistics but do not show feature statistics because their original feature dimensions are not available in the browser payload.

Each per-cluster modal lists the cluster metrics, icon statistics, feature statistics, standardized interpretation, and an **Icons and feature values** table. That table contains every icon assigned to the cluster—not only icons passing the current set filter—with thumbnail, label, source set, and all seven representative values; confidence-undefined orientation cells read **Undefined**. Close it with its close button or **Escape**; focus returns to that cluster's sidebar entry. All interpretations use the feature space directly responsible for manual Image clustering and remain descriptive rather than causal.

## Feature Groups View

The main view stays concise. It presents the seven human-facing categories and the fixed configured representative for each family. These mappings are read-only in the browser: alternate registry features are not offered as Feature Groups, Clustering, Color-by, detail, Feature Values, or Feature Review choices. Each family row has a **View details** button that opens a full-viewport detail workspace containing:

- the one selected feature and its feature ID;
- how to interpret it and why it is active; configured defaults also show their supporting evidence and page-level literature citation;
- up to 20 icons drawn independently for that family from the 28,260 icons with a certain foreground mask, using 10 equal-width value bins and up to two random icons per bin;
- **All**, **B/W**, **Red**, and **Colored** icon-treatment filters with live counts.
- a **Randomize icons** action that replaces the active family's sample;
- a three-icon comparison: select exactly three cards to open a separate fullscreen modal containing their representative measurements across all seven feature families.

Each family/color-treatment combination keeps its own transient stratified random sample. The browser finds the eligible representative feature's minimum and maximum, divides that numeric range into 10 equal-width bins, and randomly selects up to two unique icons from each bin. Empty bins contribute no icons and one-record bins contribute one; the sampler does not backfill from neighboring bins, so a sparse cohort may show fewer than 20 icons. If all eligible values are identical, they form one degenerate bin and up to two icons are sampled. Dataset membership has no role in the bins. For the principal-axis orientation representative, eligibility additionally requires orientation confidence of at least 0.20 before the minimum, maximum, and bins are calculated. Before drawing a family, icons already cached for the other six families in that cohort are excluded, so the seven samples form a unique composite. The selected icons are sorted from low to high by the selected feature, and every icon card shows its raw value. Image and AI Clustering use the concatenated seven-family composite; **Randomize icons** replaces only the active family's portion and invalidates both projections. The selected representatives are Canny edge density, enclosure score v2, principal-axis orientation v2, solid-fill ratio v2, horizontal symmetry v2, foreground mean saturation v2, and local texture variation v2. The full 81-feature registry remains available, while these seven are also the current code-selected default analysis preset.

The detail view computes a cohort-level information profile without altering the underlying values. Normalized scalar representatives use 0.001 display-resolution bins and the robust spread between the 10th and 90th percentiles. Orientation uses one-degree axial bins plus doubled-angle circular dispersion, so 0° and 180° are treated as the same horizontal direction. A cohort is labeled **Low information in this cohort** when it has fewer than three rounded levels or falls below the corresponding scalar/circular spread threshold. This is a display warning, not a deletion rule: meaningful zero edge density, horizontal orientation, zero saturation, or zero texture remains in the population, sample, and average.

The 28,260-row Feature Groups payload remains compact and carries the seven configured representative values. It is the sole source for family galleries and the three-icon comparison; no 81-feature browser fallback or representative override exists. The literature rationale and citation remain attached to each fixed configured representative.

Immediately above the ordered icons, **Average of shown icons** reports the arithmetic mean of scalar representative-feature values for the currently visible icons. Orientation uses an axial circular mean over defined values instead. It is not the mean of either the full 28,749-icon corpus or the 28,260-icon certain-mask population, and recalculates after Randomize or a color-treatment change.

The B/W filter uses the extractor's `is_monochrome` value. Red uses only the pixel-derived `strict_red_flag_v2`; dataset names and labels do not classify an icon as red. The current pool contains only 10 strict-red records, and the no-backfill bin rule means a Red family sample may contain fewer than 10 when multiple records share a bin or some bins are empty. Colored contains the remaining non-monochrome icons. Color treatment is an icon-level viewing filter and does not change which measurements belong to the selected feature family. The selected treatment persists while moving among the seven family details, so choosing **Red** constrains every subsequently opened family to that cohort while still giving each family its own stratified draw.

Comparison selection is limited to the current sample. The fourth selection is disabled until one of the three selected icons is deselected. Selecting the third icon opens a new fullscreen comparison modal with the three images and all seven representative-feature values. A comparison opened from the orientation gallery therefore contains only defined orientations; a comparison opened from another family may still label that family's selected icons' low-confidence orientation cells as **Undefined**. Close that modal with its close button or **Escape** to return to the still-selected cards, then use **View fullscreen comparison** to reopen it. Changing the family, color treatment, or random sample clears the selection so stale or hidden icons are never compared.

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

Summary cards show selected analysis-feature count, high-redundancy pair count, moderate pair count, and source rows.

The ranking table shows each feature's family, redundancy band, strongest absolute correlation, strongest partner, standard deviation, and missing count. Selecting a feature opens its details and top eight correlation partners.

The pair table shows both features, redundancy band, signed Spearman rho, whether they share a family, and pairwise sample size.

## Agent-Oriented UI Walkthrough

For a basic browser verification:

1. Confirm the Image dataset summary reports `140 shared icons · 7 feature families · All` and that switching to Metadata or Combined reports 129 generated icons.
2. In Clustering, confirm exactly seven checked feature controls, seven numeric **Color by** choices, icon images, and both PCA axes appear without first selecting a preset.
3. Switch between K-Means and Hierarchical, then between two cluster counts; confirm summaries change without console errors.
4. Select one icon set and confirm the plot and cluster counts shrink; remove its pill and confirm all icons return.
5. Hover and click an icon; confirm preview and details include a valid image.
6. Open Feature Groups and confirm seven representative-feature mappings and seven **View details** buttons appear.
7. Open every family and confirm exactly one selected-feature panel, an evidence citation, and per-icon values appear; confirm the feature matches the representative table in [Feature system](feature-system.md#current-one-feature-representatives).
8. Confirm Feature Groups contains no representative dropdowns and that alternate registry names such as Quadtree leaf count, bounding-box ratios, grid cells, and vertical symmetry do not appear in any dashboard feature control or selected-icon detail.
9. With All selected, confirm each family gallery is ordered from low to high, contains no more than two icons from each of the 10 equal-width bins, and that none has `mask_is_uncertain == true`. Independently calculate its arithmetic mean to confirm **Average of shown icons**. Confirm the seven family samples have unique icon IDs and their composite contains 140 icons. Click **Randomize icons** in one family, confirm only that 20-icon portion changes, and return to Clustering to confirm the composite remains unique and contains the replacement IDs.
10. Inspect `feature_group_quality_audit.json`: confirm 28,260 eligible rows, 489 uncertain-mask exclusions, no low-value exclusions, bottom-1% diagnostic thresholds, and the 35-row extreme visual-review set. Confirm malformed representative values are excluded by the builder and are never rendered as zero.
10. Select three icons and confirm a separate fullscreen comparison modal opens with three images and seven representative-feature rows. Close it with **Escape**, confirm focus returns to the selected card, and reopen it with **View fullscreen comparison**. Confirm a fourth icon cannot be selected; deselect one and confirm another becomes selectable.
11. Switch among B/W, Red, and Colored, and confirm the population count, gallery, comparison selection, and shared Image Clustering population reset together. For Red, confirm the population remains 10 but the gallery can contain fewer records under the no-backfill equal-width bin rule. Leave Red selected, close with **Escape**, and open another family; confirm Red remains selected, the family has its own draw, and Clustering follows that draw. Confirm focus returns to the originating button after each close.
12. Open Feature Values and confirm the selector contains exactly the seven configured Feature Groups representatives. Search for “saturation,” select Mean saturation, and confirm low/medium/high cards load.
13. Open Feature Review, change sort and threshold, select a feature, and confirm details update.
14. Record the Color By limitation if testing current behavior; do not mark visible recoloring as verified.
15. In Image Clustering, collapse and restore the left sidebar and confirm the plot resizes. Confirm the right sidebar contains **Show heatmap** plus one entry for every assigned cluster. Open the heatmap and verify one row per cluster and one column per selected feature. Open one cluster entry and confirm only that cluster appears, with variance contribution, separation strength, six icon statistics, one feature-statistics row per selected feature, and an icon table whose row count equals the full cluster size and whose columns include all seven representatives. Apply an icon-set filter and confirm every cluster entry remains present, only the visible counts change, and the modal table still contains every assigned cluster icon.
16. In AI Clustering, collapse and restore the analysis sidebar and confirm the embedding plot resizes. Load a saved run without clicking **Run AI Clustering**. Confirm its cluster-summary section contains **Show heatmap** plus one entry per AI cluster. Confirm the heatmap has seven representative columns and an individual cluster modal reports separate embedding and measured contribution/strength values, six icon statistics, seven feature-statistics rows, and a seven-value row for every cluster icon. Both contribution columns should total approximately 100% across the sidebar entries/modals, and no provider request should occur. For an intentionally cache-missing old run, confirm embedding metrics say **Unavailable** rather than falling back to two-dimensional PCA.

For automated browser work, use the repository's Playwright skill and keep the server running in a separate terminal session.

## AI Clustering View

The fifth top-level view provides a manual-clustering-style workspace for learned image-embedding clusters over the exact current seven-family composite used by Image Clustering. Start `.venv/bin/python code/serve_analysis_dashboard.py --port 8765` and open `http://127.0.0.1:8765/`. Put `OPENROUTER_API_KEY` in the ignored repository-root `.env` file or server environment. If it is absent, normal dashboard views and saved-run inspection remain usable, while **Run AI Clustering** is disabled with a configuration message.

The AI tab exposes synchronized Method and Cluster count controls, one large image-embedding plot, and a collapsible analysis sidebar containing selected-icon details, the measured-feature ranking, and the cluster-information section. **Hide sidebar** releases the full workspace width for the AI plot; **Show sidebar** restores it and the plot resizes after either action. AI hover and click use the loaded run's icon set as the global baseline and show the same compact feature value/comparison bars as manual Clustering. The cluster-information section mirrors Image Clustering: **Show heatmap** plus one compact entry per cluster, each opening a dedicated fullscreen modal for that cluster. Its plot icons use the same 5.5%-of-axis-span scale as manual Image clustering, including both plots in the comparison modal. Image and AI cluster-detail cards share one renderer and the same ordering: **Variance contribution**, **Separation strength**, **Full cluster size**, icon statistics, feature statistics, interpretation, and the complete icon-value table. In AI, the first two metrics are calculated in the model's full embedding space; additional **Post-hoc measured variance** and **Post-hoc measured strength** values describe how the seven thesis features align with those AI clusters. The feature-statistics table remains identical, with valid `N`, raw cluster mean, median, population standard deviation, minimum, maximum, full-sample mean, and signed standardized difference. The icon table contains every icon and all seven representative values. These measured-feature statistics are post-hoc descriptions of the AI clusters, not embedding dimensions or model attribution. Clicking a plot icon populates the same kind of compact measurement detail used by manual Clustering. AI retains its explicit Run and Recent Runs controls because embedding requests and saved results require an explicit lifecycle.

Embedding contribution uses the complete L2-normalized embedding vectors, not the two-dimensional PCA display. Previously saved completed runs are enriched on read from their hash-matched local embedding cache; loading them does not call OpenRouter or rewrite the saved run. If matching cached embeddings are unavailable, the UI labels those embedding metrics unavailable while retaining the measured-feature profile.

The global **Which measured feature separates these clusters most?** ranking standardizes the seven current representative values, calculates each feature's between-cluster variance divided by its total variance, then reports that feature's share of the seven scores. This is a post-hoc descriptive association with the AI labels, not a causal explanation or model attribution: OpenRouter receives normalized image pixels only and never receives these feature values.

**Open feature vs AI comparison** opens a separate fullscreen modal containing the paired feature and embedding plots, synchronized hover/selection, pairwise agreement, cache counts, and the feature-versus-AI cross-table. Closing the modal with its close button or **Escape** returns focus to the comparison button. The main AI workspace therefore remains focused on inspecting the AI result rather than permanently showing two plots. ARI, NMI, and provider usage remain stored with the run but are intentionally hidden from the UI. These are agreement measurements, not proof that either clustering is better.

**Run AI Clustering** is the only action that may spend provider credits. Randomizing a sample or changing feature selection, method, or `k` marks the visible result stale and never triggers an automatic request. If only two image features are selected, the next explicit run recomputes the feature-based PCA and labels from those two features. The AI side still uses the full learned image embeddings for the same icon sample; feature selection does not enter the embedding request or alter a cached embedding. Recent runs persist in SQLite. **Load** restores a stored AI workspace and enables its comparison modal without calling OpenRouter or mutating the current Feature Groups sample.

## Common Misreadings

- A cluster is not a semantic class.
- PCA proximity is not the complete high-dimensional distance.
- Metadata and combined variants are not pure visual feature spaces.
- Low and high feature values are descriptive, not quality judgments.
- Correlation is not causation and redundancy is not automatically a defect.
- The dashboard does not yet include participant-response results.
