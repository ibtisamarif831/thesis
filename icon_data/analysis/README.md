# Icon Analysis Dataset

Generated: 2026-06-15

## Thesis Role

This analysis folder supports the thesis comparison between human icon/glyph perception and computer-measured visual feature families.

The intended workflow is:

1. Use the literature to identify visual factors involved in glyph/icon identification, distinguishability, similarity, and confusability.
2. Organize those factors into computer-measurable feature families.
3. Extract feature-family scores from normalized glyph/icon images.
4. Record human-study identification/perception scores for the same stimuli.
5. Compare human scores with computer-derived visual scores to find agreement, mismatch, and the visual factors that influence both.

Semantic meaning, historical/cultural interpretation, familiarity, metaphor, and learnability are not active computer-vision feature families here. They may be retained as metadata or human-study variables, but they should not be treated as image-derived visual features.

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
python3 code/build_icon_dataset.py --normalize --workers 8
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
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/extract_icon_features.py --per-set-limit 100 --workers 4
```

The extractor reads normalized 256x256 PNGs from `icon_data/normalized_256/` and writes a balanced pilot sample to `features.csv`. The current run uses up to 100 icons per icon set, producing 1,038 feature rows because some sets contain fewer than 100 canonical icons.

OpenCV is used for Canny/contour helpers when available; the script keeps local NumPy/Pillow fallbacks for portability.

Current active visual feature families:

- Complexity: edge density, quadtree structure, components, contours, holes, perimeter load, and corner count.
- Shape/silhouette: aspect ratio, solidity, closure proxy, circularity, rectangularity, and curvature bins.
- Stroke/structure: line orientation, principal-axis orientation, arrowheads, arcs, skeleton endpoints, and skeleton junctions.
- Density/fill: foreground amount, bounding-box occupancy, filled/outline proxy, and stroke width.
- Balance/layout: centroid offset, symmetry, bounding-box position/size, and 4x4 foreground grid layout.
- Color/contrast: monochrome status, color count, saturation, colorfulness, foreground/background contrast, hue histogram, and dominant Lab colors.
- Texture: foreground tonal entropy.

The raw extractor still preserves additional columns for traceability, but the active literature-mapped visual family set excludes weak or non-interpretable channels such as Hu moments, local binary pattern bins, text/letter heuristic scores, and crush-test stability.

The feature CSV also includes non-distance metadata identity columns:

- exact text identity when available from labels or gated Tesseract OCR: `recognized_text`, `recognized_text_source`, `recognized_text_confidence`, `ocr_text_raw`, `ocr_text_confidence`;
- semantic identity from labels/categories: `semantic_symbol_type`, `semantic_is_arrow`, `semantic_arrow_direction`, `semantic_is_object`, `semantic_object_label`, and `semantic_object_category`.

These metadata columns are not part of the active visual feature-family comparison. They can support filtering, controls, or later human-study interpretation, but they should not be presented as computer-vision evidence for semantic understanding.

The authoritative column registry is written to `features_metadata.json` on every extraction run.

The extractor is plugin-style: each metric is a `FeatureExtractor` subclass registered in `FEATURE_EXTRACTORS`.

## Feature Visualization

Generate the current visual report with:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/visualize_icon_features.py
```

The report is written to:

`icon_data/analysis/visualizations/index.html`

Current outputs include feature distributions by icon set, a Spearman feature-correlation heatmap, a PCA feature scatterplot, sample icon contact sheets, and low/high example sheets for each main feature.

## Pairwise Similarity

Compute pairwise feature similarity with:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/compute_icon_similarity.py
```

The report is written to:

`icon_data/analysis/similarity/index.html`

The script uses the active visual feature families from the dashboard metadata. It applies robust scaling, handles circular orientation and hue channels, excludes weak/non-interpretable raw channels, weights by visual family, and then computes Euclidean and cosine distance matrices. It writes nearest-neighbor tables and visual sheets for the closest all-set, same-set, and cross-set icon pairs.

## Canonical Selection Rules

The script avoids duplicate/helper assets where possible. For example, it uses extracted McDougall icons rather than full appendix pages, ARASAAC 300px PNGs, OpenMoji color SVGs, and non-original ISO 7010 warning SVGs.

## Metadata Coverage Review

Reviewed: 2026-06-22

Most icon sets have at least labels in `dataset.csv`, but source-level metadata quality varies substantially. The richest metadata is not always fully propagated into the unified analysis table yet.

| Dataset | Local normalized icons | Metadata quality | Useful metadata found |
|---|---:|---|---|
| `07_arasaac_pictograms` | 13,798 | Very rich | Categories, keywords, tags, synsets, created/updated dates, AAC flags. |
| `10_openmoji` | 4,495 | Very rich | Group, subgroup, annotation, tags, OpenMoji author/date, Unicode and skintone fields. |
| `05_mulberry_symbols` | 3,436 | Rich | Symbol name, grammar, category ID/name, rated flag, tags, English/French labels. |
| `06_blissymbolics` | 5,825 | Good | Label, symbol kind (`char` or `word`), source file/id. |
| `04_ocha_humanitarian_icons` | 359 | Rich source metadata, weakly imported | Name, Unicode, filename, category, tags in the lookup table. |
| `09_universal_symbols_healthcare_webfont` | 144 | Moderate | Icon names and webfont codepoints. |
| `02_aiga_dot_symbol_signs` | 80 | Moderate | Wikimedia titles, source URLs, local file mapping. |
| `08_ghs_hazard_pictograms` | 9 | Minimal but clean | Name, OSHA source URL, file path, content type. |
| `12_iso_15223_medical_device_symbols` | 29 | Minimal/moderate | Meaningful filenames and component/icon names. |
| `11_iso_7010_safety_signs` | 37 | Minimal | ISO code IDs and webfont codepoints. |
| `13_usp_pictograms_manual` | 83 | Weak structured metadata | Numeric IDs in `dataset.csv`; index PDFs may contain meanings that still need extraction. |
| `03_mapbox_maki_icons` | 215 | Weak/moderate | Icon names and broad point-of-interest category. |
| `01_mcdougall_symbol_icon_set` | 239 | Weak locally, important externally | Local rows have appendix item numbers only; the source study reports norm ratings but they are not structured locally. |

### Rich Source Metadata Files

- `icon_data/iconsets/07_arasaac_pictograms/metadata/arasaac_all_en.json`
- `icon_data/iconsets/10_openmoji/data/openmoji.csv`
- `icon_data/iconsets/10_openmoji/data/openmoji.json`
- `icon_data/iconsets/05_mulberry_symbols/scripts/data/symbol-info-en.csv`
- `icon_data/iconsets/05_mulberry_symbols/scripts/data/symbol-info.csv`
- `icon_data/iconsets/06_blissymbolics/metadata/rendered_symbols.json`
- `icon_data/iconsets/04_ocha_humanitarian_icons/documentation/icon-lookup-table.md`
- `icon_data/iconsets/09_universal_symbols_healthcare_webfont/packages/webfont-medical-icons/selection.json`
- `icon_data/iconsets/02_aiga_dot_symbol_signs/aiga_thumbnail_metadata.json`
- `icon_data/iconsets/02_aiga_dot_symbol_signs/aiga_wikimedia_metadata.json`
- `icon_data/iconsets/08_ghs_hazard_pictograms/metadata/osha_ghs_pictograms.json`
- `icon_data/iconsets/11_iso_7010_safety_signs/Webfont/config.json`

### Current Unified CSV Gaps

- OCHA source metadata has real categories and tags, but `dataset.csv` currently uses generic categories for many rows.
- Mulberry source metadata has grammar, category, tags, and multilingual labels, but `dataset.csv` currently collapses this into a generic category.
- USP pictograms have numeric labels only in `dataset.csv`; human-readable medication instructions may need to be extracted from the included index PDFs.
- McDougall has valuable normative ratings in the study context, but the local structured data only records appendix item numbers.
- AIGA can likely be enriched from Wikimedia titles and thumbnail metadata, but current categories are blank.
- ISO 7010 rows currently preserve ISO code IDs, not human-readable warning meanings.

### Recommended Enrichment Order

1. Parse OCHA `icon-lookup-table.md` into `dataset.csv` categories and tags.
2. Import Mulberry `symbol-info-en.csv` fields: grammar, category, rated flag, and tags.
3. Extract USP index PDF labels into a structured lookup keyed by pictogram number.
4. Normalize AIGA Wikimedia titles into labels/categories where possible.
5. Add human-readable ISO 7010 meanings for W001-W038 if a reliable source is available.
6. Investigate whether McDougall normative ratings can be captured from the public paper tables or require separate request-only stimulus metadata.
