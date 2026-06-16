# Icon Analysis Dataset

Generated: 2026-06-15

## Files

- `dataset.csv`: one row per canonical icon selected for analysis.
- `features.csv`: extracted visual features for the current balanced pilot sample.
- `features_metadata.json`: feature extraction settings and active feature registry.
- `feature_failures.json`: feature extraction failures from the latest run.
- `visualizations/`: generated visual report, plots, contact sheets, and feature summaries.
- `similarity/`: pairwise feature-distance matrices, nearest-neighbor CSVs, and visual pair sheets.
- `normalization_failures.json`: conversion failures from the latest normalization run.

## Normalized Images

Normalized 256x256 PNGs are written to:

`icon_data/normalized_256/`

This folder is intentionally ignored by git because it is generated and large. Regenerate it with:

```bash
python3 scripts/build_icon_dataset.py --normalize --workers 8
```

## Dataset Columns

- `icon_id`: stable hash of the source relative path.
- `set_id`: local icon-set folder ID.
- `set_name`: readable icon-set name.
- `relative_path`: original source icon path.
- `filename`: source filename.
- `label`: best available label, from metadata or filename.
- `category`: best available category, from metadata or folder structure.
- `format`: source file extension.
- `source`: short source name.
- `source_url`: source URL.
- `normalized_path`: generated 256x256 PNG path.
- `notes`: extra metadata, such as ARASAAC IDs or OpenMoji tags.

## Feature Extraction

Feature extraction is implemented in:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/extract_icon_features.py --per-set-limit 100 --workers 8
```

The extractor reads normalized 256x256 PNGs from `icon_data/normalized_256/` and writes a balanced pilot sample to `features.csv`. The current run uses up to 100 icons per icon set, producing 855 feature rows because some sets contain fewer than 100 canonical icons.

OpenCV is used for Canny edge detection when available; the script keeps a local NumPy/Pillow fallback for portability.

Current feature columns:

- `foreground_area_ratio`
- `canny_edge_density`
- `connected_components`
- `quadtree_leaf_count`
- `quadtree_structural_variability`
- `quadtree_mean_leaf_size`

The extractor is plugin-style: each metric is a `FeatureExtractor` subclass registered in `FEATURE_EXTRACTORS`.

## Feature Visualization

Generate the current visual report with:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/visualize_icon_features.py
```

The report is written to:

`icon_data/analysis/visualizations/index.html`

Current outputs include feature distributions by icon set, a Spearman feature-correlation heatmap, a PCA feature scatterplot, sample icon contact sheets, and low/high example sheets for each main feature.

## Pairwise Similarity

Compute pairwise feature similarity with:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/compute_icon_similarity.py
```

The report is written to:

`icon_data/analysis/similarity/index.html`

The script standardizes the extracted feature columns, computes Euclidean and cosine distance matrices, writes nearest-neighbor tables, and generates visual sheets for the closest all-set, same-set, and cross-set icon pairs.

## Canonical Selection Rules

The script avoids duplicate/helper assets where possible. For example, it uses extracted McDougall icons rather than full appendix pages, ARASAAC 300px PNGs, OpenMoji color SVGs, and non-original ISO 7010 warning SVGs.
