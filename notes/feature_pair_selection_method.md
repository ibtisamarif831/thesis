# Feature-Pair Selection Method

## Purpose

The dashboard selects up to two representative features from each visual feature family. The method is **strength first, redundancy second**:

- **1st** means the strongest defensible, non-constant feature in the family.
- **2nd** means the strongest remaining feature that is sufficiently different from the 1st.

The implementation is split between:

- `code/build_analysis_dashboard.py`, which defines strength priorities and computes feature statistics and correlations.
- `code/thesis_pipeline/dashboard/feature_selection.py`, which performs the final family-by-family selection.

## 1. Definition of feature strength

Each family has an explicitly ordered list in `FEATURE_STRENGTH_PRIORITY` in `code/build_analysis_dashboard.py`.

For example:

```python
"complexity": [
    "canny_edge_density",              # priority 1
    "connected_components",            # priority 2
    "quadtree_structural_variability", # priority 3
    "holes_count",
    "perimeter_area_ratio",
    "corner_count",
    "contour_count",
]
```

This order represents the current substantive definition of strength:

1. Literature support.
2. Interpretability.
3. How directly the feature measures the intended visual concept.
4. Observed measurement quality across the icon sample.

Strength is not currently calculated from variance, standard deviation, isolation, or Spearman correlation. It is a curated, literature-informed ranking. Human-study outcomes could later provide additional empirical evidence for revising this order.

## 2. Statistical preparation

The dashboard normally reads the complete `icon_data/analysis/features.csv`, currently containing 1,038 icons.

For every active feature, it calculates:

- Standard deviation.
- Variance.
- Missing-value count.
- Spearman correlation with every other active feature.

For each pair, Spearman correlation is calculated by:

1. Keeping rows where both feature values are finite.
2. Converting each feature's values to ranks.
3. Giving tied values their average rank.
4. Calculating Pearson correlation between the two rank vectors.

The stored pair record includes the signed correlation, absolute correlation, shared observation count, and redundancy band.

## 3. Selecting the 1st feature

For each family, the selector examines candidates in strength-priority order.

A candidate is skipped when:

- It is absent from the active feature data.
- Its standard deviation is effectively zero: `std <= 1e-12`.

The first remaining candidate becomes the family's 1st representative. No Spearman condition is needed because it has no companion yet.

This is why selecting only one feature is straightforward: choose the strongest valid, non-constant candidate.

## 4. Selecting the 2nd feature

After choosing the 1st feature, the selector continues down the strength-priority list. Each candidate is compared directly with the already selected representative.

A candidate is accepted only when:

```text
|Spearman rho| < 0.70
```

A candidate is rejected when:

```text
|Spearman rho| >= 0.70
```

Exactly `0.70` is rejected. A candidate is also rejected if no pairwise correlation record exists, because the system should not claim complementarity without evidence.

With the current limit of two features per family, a prospective 2nd feature is compared only with the selected 1st feature. If the limit were increased, a new candidate would have to pass the threshold against every already selected representative.

Simplified pseudocode:

```text
for each family:
    selected = []

    for feature in strength-priority order:
        if feature is missing or constant:
            continue

        if selected is empty:
            select feature as 1st
        else if every required pair exists
                and every |Spearman rho| is below 0.70:
            select feature as the next representative

        stop after selecting two features
```

## 5. Why absolute Spearman is used

Strong positive and strong negative correlations can both indicate redundancy:

- `rho = +0.90`: the two features usually rank icons in the same direction.
- `rho = -0.90`: the two features usually rank icons in opposite directions.

Both retain almost the same ordering information. Therefore, both have `|rho| = 0.90` and are rejected.

## 6. Example of skipping a redundant candidate

Suppose a family has this strength order:

```text
1. Strong feature
2. Duplicate feature
3. Complementary feature
```

The measured correlations are:

```text
Strong <-> Duplicate:       rho = 0.91
Strong <-> Complementary:   rho = -0.20
```

The result is:

1. Strong becomes the 1st feature.
2. Duplicate is tested next and rejected because `|0.91| >= 0.70`.
3. Complementary is tested and accepted because `|-0.20| = 0.20 < 0.70`.

The complementary feature has final selection rank 2 even though its original strength-priority rank is 3. This distinction is preserved in the generated dashboard data.

## 7. Current selected representatives

The current generated dashboard contains these selections:

| Family | 1st feature | 2nd feature | Spearman rho |
|---|---|---|---:|
| Complexity | Canny edge density | Connected components | 0.220037 |
| Shape/silhouette | Bounding-box aspect ratio | Circularity | -0.052247 |
| Stroke/structure | Horizontal line orientation | Skeleton junctions | -0.066270 |
| Density/fill | Foreground area ratio | Stroke-width variation | 0.008231 |
| Balance/layout | Horizontal symmetry | Bounding-box width ratio | 0.049202 |
| Color/contrast | Mean saturation | Foreground-background contrast | 0.034124 |
| Texture | Texture entropy | Texture coarseness | -0.028712 |

All currently selected features have values for all 1,038 icons.

Texture now has two validated representatives:

```python
"texture": [
    "texture_entropy",
    "texture_coarseness",
]
```

## 8. Tamura coarseness activation

Tamura coarseness was implemented and validated before being added to the active priority list:

```python
"texture": [
    "texture_entropy",
    "texture_coarseness",
]
```

The completed acceptance process was:

1. Entropy remained the 1st Texture representative.
2. Coarseness produced valid, non-constant values for all 1,038 icons.
3. Its Spearman correlation with entropy was `rho = -0.028712`.
4. It passed the `|rho| < 0.70` rule.
5. Low and high examples were visually inspected and showed fine/repeated versus large/simple intensity structure.

See `notes/tamura_coarseness_validation.md` for the literature definition, glyph adaptation, statistics, visual-audit summary, and limitations.

## 9. Visual example bands

Low, nearest-mean, and high icon examples are produced only after the representative features have been selected. They do not influence the selection.

For each selected feature, the dashboard shows:

- The six smallest values.
- The six values nearest the arithmetic mean.
- The six largest values.

These examples provide a visual validity check and can reveal when a statistically acceptable feature is actually measuring an unwanted rendering artifact.

## 10. Build-time enforcement

After selection, the dashboard checks the number of representatives produced for each family. Every current family has at least two validated priority candidates and is expected to produce two representatives.

If a future candidate is added to a priority list before validation and then fails the Spearman screen, dashboard generation will raise a `ValueError` instead of silently presenting a questionable pair.

The safe sequence is therefore:

1. Implement the feature.
2. Extract it for the icon sample.
3. Verify its distribution and visual meaning.
4. Verify `|rho| < 0.70` against entropy.
5. Add it to the active Texture strength-priority list.
