# Feature System

## Authoritative Registry

`code/thesis_pipeline/features/registry.py` is the typed authority for schema-v2 feature ordering, statuses, family membership, display metadata, exclusions, configured representatives, benchmark aliases, feature-level evidence and citations, and the orientation-confidence threshold. It exposes frozen `FeatureSpec` and `FamilySpec` values plus immutable query results.

`extract_icon_features.py` remains authoritative for measurement implementations, but validates its extractor-column order against the registry at import time. The dashboard, similarity pipeline, and feature-v2 benchmark builder consume the registry directly instead of redefining families or importing one another. The frozen characterization fixture is `code/tests/fixtures/feature_registry_v2.json`.

## Schema v2 extraction repair (2026-07-20)

`features.csv` now uses `feature_schema_version: 2` and retains every schema-v1 measurement for reproducibility. Seven legacy columns are deprecated and inactive; the active 81-feature registry replaces them one-for-one with:

| Family | Schema-v2 replacement column | Definition |
|---|---|---|
| Complexity | `quadtree_structural_variability_v2` | Quadtree subdivision density of grayscale intensity inside the active foreground box. |
| Shape/silhouette | `enclosure_score_v2` | External-contour area divided by active bounding-box area. |
| Stroke/structure | `principal_axis_orientation_v2` | PCA axis over 0–180°; `orientation_confidence_v2` is eigenvalue anisotropy and values below 0.20 are undefined. |
| Density/fill | `solid_fill_ratio_v2` | Mean foreground survival after erosion at 1%, 2%, and 4% of the shorter active-box dimension. |
| Balance/layout | `horizontal_symmetry_v2` | Left-right Dice-style overlap with two-pixel tolerance. |
| Color/contrast | `mean_saturation_v2` | Mean HSV saturation over corrected foreground pixels. |
| Texture | `local_texture_variation_v2` | Normalized 7×7 grayscale variation inside a two-pixel-eroded foreground. |

Auxiliary v2 channels are `orientation_confidence_v2`, `red_pixel_ratio_v2`, and `strict_red_flag_v2`. Strict red requires hue 345°–15°, saturation at least 0.50, value at least 0.20, and at least 90% qualifying foreground pixels. These auxiliary channels do not increase active-family dimensionality.

Foreground masks use alpha greater than 0.05 for transparent images. Opaque images estimate the median border color in CIELAB and remove only border-connected pixels within ΔE76 10. Per-icon metadata records mode, coverage, border contact, confidence, and an uncertainty flag. Uncertain masks remain inspectable but must not be silently treated as validated evidence.

The frozen benchmark is `icon_data/analysis/feature_v2_benchmark.csv`: 50 examples per family (30 calibration, 20 held out) plus 100 strict-red candidates. The engineering schema is active for analysis and review, but the human-study pilot remains blocked by `feature_v2_release_gate.json` until two independent raters satisfy every acceptance threshold.

[Wiki home](README.md) · [Pipeline](pipeline.md) · [Similarity](similarity-and-clustering.md)

## Feature Layers

The repository distinguishes four different things:

1. **Extractor output:** 110 raw numeric image-feature columns retained for traceability.
2. **Active visual mapping:** 81 interpretable features organized into seven literature-mapped families.
3. **Code-selected analysis layer:** a named preset chooses features for dashboard clustering, Feature Review, and similarity. The current preset contains seven features.
4. **Metadata/identity fields:** 23 columns used for labels, joining, filtering, OCR/semantic context, and mask diagnostics; these are not visual-distance features.

Do not use “feature” without making the layer clear. In thesis claims, “active registry features” means the 81 image-derived features in the seven visual families; “analysis features” means the code-selected preset, which contains seven features by default.

## Code-Only Analysis Preset

`ANALYSIS_FEATURE_PRESET` in `code/thesis_pipeline/features/registry.py` is the single switch for the
default computational selection:

- `"representatives"` — the seven configured family representatives; current default;
- `"full_registry"` — all 81 active registry features.

`analysis_feature_ids()` and `analysis_feature_groups()` validate and expose the selected preset.
Dashboard clustering, combined clustering, Feature Review, and pairwise similarity consume these
queries. Raw extraction still writes all 110 columns, the active registry still contains 81 features,
and feature metadata remains available for inspection. To add a different manual seven-feature set,
add a named immutable tuple to `_ANALYSIS_FEATURE_PRESETS`, then change the one preset constant. No UI
profile switch is provided.

## Image Loading and Foreground Detection

`code/extract_icon_features.py` loads each normalized image as RGBA. Transparent images normally use alpha greater than 0.05. If that alpha mask forms a nearly solid rectangle, the extractor checks for a border-connected, near-white, low-chroma panel inside it and removes that panel before computing features. This prevents white page backgrounds in transparent PNGs from becoming false filled silhouettes. Genuine solid dark alpha shapes remain unchanged. Opaque images use the border-connected CIELAB rule documented above. Grayscale uses standard RGB luminance weights and sets detected background pixels to white.

OpenCV is optional. When present, it is used for selected operations such as Canny edges; NumPy/Pillow fallbacks preserve operation when OpenCV is unavailable. Tesseract is optional and only supports gated exact-text annotation, not the active visual-family computation.

The extractor is plugin-style: every metric group subclasses `FeatureExtractor`, declares its output columns, and is registered in `FEATURE_EXTRACTORS`.

## Active Families

| Family | Active columns | Human-facing interpretation |
|---|---:|---|
| Complexity | 9 | Detail load, subdivisions, separate parts, contours, holes, perimeter load, corners. |
| Shape/silhouette | 8 | Overall form, closure proxy, roundness, rectangularity, curvature. |
| Stroke/structure | 9 raw columns | Directional lines, dominant axis, arrow/arc cues, skeleton endpoints and junctions. |
| Density/fill | 5 | Foreground amount, occupancy, filled/outline behavior, stroke width. |
| Balance/layout | 23 | Centering, symmetry, bounding-box position/size, and 4 × 4 spatial mass. |
| Color/contrast | 26 | Monochrome/color, saturation, colorfulness, contrast, hue, dominant Lab colors. |
| Texture | 1 | Local interior grayscale variation with the silhouette edge excluded. |

The active raw total is 81. In pairwise similarity, `principal_axis_orientation_v2` is replaced by confidence-scaled doubled-angle cosine/sine components, so the transformed matrix has one additional numeric channel while representing the same conceptual axis.

## Current One-Feature Representatives

Feature Groups currently exposes one literature-backed representative per family for stimulus review. Feature Values intentionally reuses exactly these seven representatives for low/mean-nearest/high examples. The 81-feature active registry remains intact, while the current code-only analysis preset deliberately uses these same seven features for clustering, similarity, and Feature Review.

| Family | Current representative | Selection basis |
|---|---|---|
| Complexity | `canny_edge_density` | Smoothed Canny edge density; selected after the visual audit exposed raster and antialias inflation in grayscale quadtree variability. |
| Shape/silhouette | `enclosure_score_v2` | UI interpretation: lower usually means thin, open, or spread out; higher usually means large, compact, or closed. Technically, the score is external-contour enclosure within the active box. |
| Stroke/structure | `principal_axis_orientation_v2` | PCA axis with explicit anisotropy confidence and undefined handling. |
| Density/fill | `solid_fill_ratio_v2` | Multi-scale erosion survival separating solid interiors from outlines. |
| Balance/layout | `horizontal_symmetry_v2` | Tolerant left-right Dice overlap. |
| Color/contrast | `mean_saturation_v2` | Saturation over the corrected foreground. |
| Texture | `local_texture_variation_v2` | Local interior variation rather than global tonal entropy. |

These are the most defensible current representatives, not universal causal rankings. Complexity is the first family to move away from its schema-v2 replacement after full-corpus visual review; `quadtree_structural_variability_v2` remains active for analysis but is no longer the one-feature representative. The papers study different tasks and do not compare every implemented feature in one experiment. Each selection, rationale, evidence statement, and citation is defined in the shared registry and serialized into `metadata.image_feature_sections` within `dashboard_data.json`.

The registry also carries evidence for every active feature, not only the seven representatives.
`FeatureSpec.evidence_scope` separates close measure-level evidence (`direct`) from support for the
visual construct while the formula remains a project inference (`construct`) and source findings that
constrain interpretation (`cautionary`). The 2026-07-28 pass yielded 1 direct, 77 construct, and 3
cautionary entries. Each dashboard feature object includes `evidence_scope`, `evidence`, and
`citation`. See [Literature and evidence](literature-and-evidence.md#feature-level-evidence-registry)
and `notes/feature_literature_evidence_pass_2026-07-28.md`.

## Complete Active Feature Reference

The definitions below are mirrored into `dashboard_data.json`. For machine-readable meaning, grouping, human categorization, and low/high interpretation, read `metadata.image_feature_sections` in that file.

### Complexity (9)

- `canny_edge_density` — amount of edge/detail structure.
- `quadtree_leaf_count` — number of spatial subdivisions needed to describe foreground.
- `quadtree_structural_variability_v2` — intensity quadtree subdivision density across the active box.
- `quadtree_mean_leaf_size` — average quadtree region size; smaller implies finer local detail.
- `connected_components` — separated foreground parts.
- `contour_count` — contour boundaries.
- `holes_count` — enclosed background regions inside foreground shapes.
- `perimeter_area_ratio` — boundary length relative to filled area.
- `corner_count` — approximate polygon-corner count across external contours.

### Shape/silhouette (8)

- `bounding_box_aspect_ratio` — tall, wide, or square-like active shape.
- `solidity` — foreground compactness inside its convex envelope.
- `enclosure_score_v2` — external-contour enclosure relative to the active box; not a direct human closure judgment.
- `circularity` — similarity of the foreground silhouette to a compact circle.
- `rectangularity` — foreground occupancy of its minimum enclosing rectangle.
- `curvature_histogram_straight` — share of straight contour samples.
- `curvature_histogram_gentle` — share of gradually curved contour samples.
- `curvature_histogram_sharp` — share of sharp turns/angular samples.

### Stroke/structure (9)

- `line_orientation_0` — mostly horizontal detected line structure.
- `line_orientation_45` — 45-degree diagonal structure.
- `line_orientation_90` — mostly vertical structure.
- `line_orientation_135` — 135-degree diagonal structure.
- `principal_axis_orientation_v2` — dominant foreground axis over 180 degrees, defined only with confidence at least 0.20.
- `arrowhead_count` — approximate triangular or sharp directional tips.
- `arc_count` — approximate curved arc-like contour runs.
- `skeleton_endpoints` — terminal points in the foreground skeleton graph.
- `skeleton_junctions` — branch points in the foreground skeleton graph.

### Density/fill (5)

- `foreground_area_ratio` — visible foreground share of the full canvas.
- `bounding_box_occupancy` — foreground density within the active bounding box.
- `solid_fill_ratio_v2` — foreground survival under three active-box-scaled erosions.
- `stroke_width_mean` — normalized mean stroke width estimated from the skeleton. Distance transforms use an explicit one-pixel background border so full-canvas foreground masks remain finite.
- `stroke_width_std` — normalized stroke-width variation.

### Balance/layout (23)

- `centroid_distance_from_center` — visual-mass offset from canvas center.
- `horizontal_symmetry_v2` — left-right overlap with two-pixel tolerance.
- `vertical_symmetry` — top-bottom balance.
- `bbox_center_x`, `bbox_center_y` — active bounding-box center in normalized canvas coordinates.
- `bbox_width_ratio`, `bbox_height_ratio` — bounding-box coverage of the canvas.
- `grid_foreground_0_0` through `grid_foreground_3_3` — foreground share in each cell of a 4 × 4 row-major layout grid.

### Color/contrast (26)

- `is_monochrome` — effective black-and-white/grayscale flag.
- `color_count` — approximate distinct foreground colors.
- `mean_saturation_v2` — corrected-foreground average saturation.
- `colorfulness` — overall foreground color richness/variation.
- `foreground_background_contrast` — foreground/background separation.
- `hue_histogram_00` through `hue_histogram_11` — 12 circular 30-degree saturated-foreground hue bins.
- `dominant_color_1_lab_l`, `_a`, `_b` — first dominant foreground color in Lab.
- `dominant_color_2_lab_l`, `_a`, `_b` — second dominant foreground color in Lab.
- `dominant_color_3_lab_l`, `_a`, `_b` — third dominant foreground color in Lab.

### Texture (1)

- `local_texture_variation_v2` — normalized local grayscale variation within the eroded foreground interior.

## Excluded Raw Channels

The following remain in `features.csv` for traceability but are excluded from active family mapping, dashboard family analysis, and similarity ranking:

| Columns | Reason |
|---|---|
| `hu_moment_1` … `hu_moment_7` | Useful for machine shape matching but difficult to interpret as human perception cues. |
| `lbp_histogram_00` … `lbp_histogram_09` | Often capture antialiasing/rendering artifacts in flat vector icons. |
| `text_or_letter_presence` | Current heuristic is too indirect for a reliable identification claim. |
| `crush_test_stability` | Processing robustness rather than a directly visible identification feature. |
| Seven schema-v1 representatives | Deprecated but retained for reproducibility; replaced one-for-one by v2. |
| `orientation_confidence_v2`, `red_pixel_ratio_v2`, `strict_red_flag_v2` | Auxiliary interpretation/cohort channels, not independent active family evidence. |

Exclusion does not mean the raw values are deleted. It means they must not drive the active thesis comparison unless the research mapping is deliberately revised and documented.

## Metadata and Semantic Annotation

The 23 metadata columns are:

| Group | Columns |
|---|---|
| Identity and source context | `icon_id`, `set_id`, `set_name`, `label`, `category`, `normalized_path` |
| Text annotation | `recognized_text`, `recognized_text_source`, `recognized_text_confidence`, `ocr_text_raw`, `ocr_text_confidence` |
| Foreground-mask diagnostics | `mask_mode`, `mask_coverage`, `mask_border_contact`, `mask_confidence`, `mask_is_uncertain` |
| Semantic annotation | `semantic_symbol_type`, `semantic_identity_source`, `semantic_is_arrow`, `semantic_arrow_direction`, `semantic_is_object`, `semantic_object_label`, `semantic_object_category` |

These fields can be used for:

- joining tables by `icon_id`;
- filtering and inspecting examples;
- study prompts and controls;
- interpreting human responses;
- checking whether a result is semantically confounded.

They cannot be used as evidence that pixels alone produced semantic understanding.

## Feature Metadata Artifact

`icon_data/analysis/features_metadata.json` records the last extraction run: input/output paths, row count, per-set limit, dependency availability, metadata columns, and extractor grouping. `dashboard_data.json` serializes the registry's current active-family definitions and human-facing descriptions.

Use both artifacts together:

- extractor registry and runtime state: `features_metadata.json`;
- authoritative feature/family mapping and descriptions: `code/thesis_pipeline/features/registry.py`;
- generated dashboard serialization: `dashboard_data.json`;
- executable formulas: `extract_icon_features.py`;
- frozen schema-v2 characterization: `code/tests/fixtures/feature_registry_v2.json`.

## Adding or Changing a Feature

1. Define the extraction behavior and column in a focused extractor class.
2. Register it in `FEATURE_EXTRACTORS`.
3. Decide whether it is raw-only or belongs to an active literature-mapped family.
4. Add a clear meaning, grouping reason, low/high interpretation, and literature rationale for active features.
5. Update exclusion rules if replacing or retiring a channel.
6. Add focused tests for reusable selection/transformation behavior.
7. Regenerate features, similarity outputs, dashboard outputs, and metadata.
8. Visually inspect low/medium/high examples and redundancy evidence.
9. Update this page and related research notes if the conceptual mapping changed.
