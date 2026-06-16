# Icon Perception Metrics Pipeline Plan

## Summary

Build a focused computational pilot for the thesis question:

> Can icon perception be made more systematic by measuring visual features that affect similarity, distinguishability, and categorisation?

Use the existing normalized icon dataset as the base. The recommended contribution is a metrics-and-clustering pipeline, with McDougall's normed icon set used as the validation anchor and other icon sets used for cross-domain comparison.

Approaches considered:

- **Recommended:** automated visual-feature extraction + clustering + McDougall validation.
- **Optional later:** small human similarity study using selected icon pairs.
- **Lower priority:** taxonomy-only writeup, because it is weaker as a measurable thesis contribution.

## Key Changes

- Use `icon_data/analysis/dataset.csv` as the canonical input.
- Add a machine-readable McDougall ratings table from the appendix PDF, using OCR plus manual verification where extraction fails.
- Add feature extraction over `icon_data/normalized_256/`:
  - [x] foreground area ratio;
  - bounding-box occupancy;
  - perimeter / edge length;
  - [x] Canny edge density;
  - [x] connected components;
  - holes / enclosed regions;
  - contour count;
  - horizontal and vertical symmetry;
  - [x] quadtree structural variability;
  - compression ratio as a complexity proxy;
  - filled-vs-outline proxy.
- Add pairwise similarity and distance outputs:
  - [x] standardized numeric-feature distance;
  - [x] cosine distance over standardized feature vectors;
  - image-level similarity, preferably SSIM or HOG/cosine if available;
  - optional quasi-Hamming-style visual-channel distance using discretized feature bins.
- Add clustering outputs:
  - hierarchical clustering as the main method;
  - k-means only as a secondary comparison;
  - dendrograms, cluster labels, and nearest-neighbor examples.

## Dataset Plan

- **Validation set:** all 239 McDougall icons.
- **Primary comparison sets:** AIGA/DOT, GHS, ISO 7010, ISO 15223, Universal Healthcare, Mapbox Maki, OCHA.
- **Large-set sampling:** ARASAAC, Mulberry, and OpenMoji should be sampled rather than fully analysed first. Current feature pilot uses up to 100 icons per set.
- Use a balanced pilot sample of roughly 500-1,000 icons:
  - all small sets;
  - all McDougall;
  - stratified samples from large sets by available category metadata.
- Keep OpenMoji secondary because it is large and stylistically different from standard pictograms.

## Analysis Plan

- Validate complexity features against McDougall perceived-complexity ratings using Spearman correlation.
- Check whether feature clusters align with known set/domain labels.
- Inspect nearest-neighbor pairs for false similarity, especially across different icon sets.
- Compare visual clusters against semantic categories to separate:
  - visual similarity;
  - semantic similarity;
  - dataset/style similarity.
- Produce a short result note answering:
  - which features are most informative;
  - whether clustering produces meaningful categories;
  - where visual metrics fail;
  - whether a later human study is justified.

## Test Plan

- Verify every sampled row has an existing normalized PNG.
- Run feature extraction on a 20-icon smoke sample before the full pilot.
- Check feature values for impossible outputs, such as negative area, empty foreground, or NaN distances.
- Confirm McDougall item IDs match rating rows exactly.
- Confirm pairwise distance matrices are symmetric and have zero diagonals.
- Manually inspect at least 5 clusters and 20 nearest-neighbor pairs.
- Report McDougall correlation results even if weak; weak correlation is still a valid thesis finding.

## Assumptions

- The thesis direction is the **metrics pipeline** approach.
- McDougall ratings are not currently machine-readable and must be extracted from the appendix.
- The first deliverable should be a pilot analysis, not a participant study.
- Generated outputs should live under `icon_data/analysis/` or a new analysis/report folder, while `icon_data/normalized_256/` remains generated data.
