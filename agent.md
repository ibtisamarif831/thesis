# Thesis Repository Agent Guide

This file is the first-stop orientation map for future agents working in this repository. Use it to route questions to the relevant area before searching broadly.

## Repository Purpose

This workspace supports a thesis on icon/glyph perception, visual complexity, similarity, clustering, and evidence-based symbol-set design.

Working thesis direction:

> Build and evaluate a computational icon/glyph analysis pipeline that measures visual features, metadata features, similarity, and clustering structure across research-relevant icon sets, with McDougall norm ratings as the strongest validation anchor.

The repo is not mainly a generic icon collection. It is an empirical/computational thesis workspace for comparing symbol-like visual stimuli.

## Route Queries Here First

| Query type | Start here | Then check |
|---|---|---|
| Thesis framing, research questions, paper themes | `agent.md`, `THESIS_CHECKLIST.md` | `tasks/*.md`, `papers/` |
| Which icon sets exist locally | `icon_data/MANIFEST.md` | `icon_data/iconsets/README.md`, `data/10 icons.md` |
| Canonical icon dataset rows | `icon_data/analysis/dataset.csv` | `code/build_icon_dataset.py` |
| Normalized image generation | `code/build_icon_dataset.py` | `icon_data/analysis/README.md`, `icon_data/normalized_256/` |
| Visual feature extraction | `code/extract_icon_features.py` | `icon_data/analysis/features.csv`, `features_metadata.json`, `feature_failures.json` |
| Similarity / nearest-neighbor analysis | `code/compute_icon_similarity.py` | `icon_data/analysis/similarity/` |
| Feature visual reports | `code/visualize_icon_features.py` | `icon_data/analysis/visualizations/` if present |
| Metadata enrichment for clustering | `code/build_clustering_metadata_sample.py` | `icon_data/analysis/clustering_metadata_sample.csv`, `clustering_metadata_missing_report.json` |
| Interactive analytics dashboard | `code/build_analysis_dashboard.py` | `icon_data/analysis/analysis_dashboard/README.md`, `index.html`, `dashboard_data.json` |
| McDougall extracted ratings | `icon_data/iconsets/01_mcdougall_symbol_icon_set/metadata/mcdougall_ratings.csv` | `code/extract_mcdougall_metadata.py` |
| McDougall extracted icons | `icon_data/iconsets/01_mcdougall_symbol_icon_set/extracted_icons_png/` | `code/extract_mcdougall_icons.py` |
| ARASAAC download issues | `code/download_arasaac.py` | `icon_data/iconsets/07_arasaac_pictograms/metadata/download_failures.json` |
| Blissymbolics rendering | `code/render_blissymbolics_images.js` | `icon_data/iconsets/06_blissymbolics/rendered_svg/`, `metadata/rendered_symbols.json` |
| Source provenance / old source plan | `data/10 icons.md`, `icon_data/MANIFEST.md` | `git show HEAD:source.md` if `source.md` is absent/deleted |
| Generated output status | `icon_data/analysis/README.md` | specific subfolder READMEs |

## Current Working State To Know

- The active canonical dataset is `icon_data/analysis/dataset.csv`.
- Normalized PNGs are generated under `icon_data/normalized_256/`; this directory is large/generated and may be ignored by git.
- The interactive dashboard is generated under `icon_data/analysis/analysis_dashboard/`.
- As of the latest dashboard change, the dashboard sample is **up to 10 random icons from each dataset**, using fixed `RANDOM_SEED = 42` in `code/build_analysis_dashboard.py`.
- The dashboard currently supports:
  - image, metadata, and combined feature variants;
  - k-means and hierarchical clustering;
  - k/cut values 3, 5, 7, and 10;
  - coloring by cluster, set, category, style, or numeric image feature;
  - filtering by icon set, category, and style;
  - selected icon details and cluster summaries.
- Older task notes may still mention the previous 1,038-icon dashboard sample. Treat `icon_data/analysis/analysis_dashboard/README.md` and `code/build_analysis_dashboard.py` as the current source of truth.
- `source.md` is tracked historically but may be deleted in the working tree. Do not restore it unless explicitly asked; use `git show HEAD:source.md` for its last committed content.

## Runtime Notes

Prefer the bundled Python runtime for analysis scripts because the local `.venv` may not have NumPy/Pillow/sklearn installed:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

Common examples:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/build_analysis_dashboard.py
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/extract_icon_features.py --per-set-limit 100 --workers 8
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/compute_icon_similarity.py
```

For static dashboard verification:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html
```

## Top-Level Layout

| Path | Purpose |
|---|---|
| `agent.md` | This routing/orientation guide for agents. |
| `THESIS_CHECKLIST.md` | Thesis roadmap and high-level completion checklist. |
| `data/10 icons.md` | Thesis-aligned icon/glyph source plan and rationale. |
| `papers/` | Core literature PDFs. Treat these as the thesis literature backbone. |
| `notes/` | Short explanatory notes, especially feature-taxonomy provenance. |
| `tasks/` | Weekly planning/progress notes. Some contain older status and should be read as historical context. |
| `code/` | Download, extraction, normalization, feature, similarity, metadata, and dashboard builders. |
| `icon_data/` | Main data area: raw icon sets, canonical CSVs, generated analysis outputs, metadata, checksums. |
| `tmp/` | Temporary OCR/crop/debug images. Do not treat as canonical output. |

## Data Areas

### `icon_data/iconsets/`

One folder per downloaded source icon set. Current local set inventory is best documented in `icon_data/MANIFEST.md`.

The 13 current sets are:

1. `01_mcdougall_symbol_icon_set` - normed HCI/interface symbols; strongest validation anchor.
2. `02_aiga_dot_symbol_signs` - AIGA/DOT wayfinding symbols.
3. `03_mapbox_maki_icons` - map/POI icons; useful modern baseline, not strongly normed.
4. `04_ocha_humanitarian_icons` - humanitarian response icons.
5. `05_mulberry_symbols` - AAC symbols.
6. `06_blissymbolics` - Blissymbolics AAC/symbolic-language set.
7. `07_arasaac_pictograms` - large AAC pictogram set.
8. `08_ghs_hazard_pictograms` - nine OSHA/GHS chemical hazard pictograms.
9. `09_universal_symbols_healthcare_webfont` - healthcare wayfinding webfont icons.
10. `10_openmoji` - large emoji/pictographic baseline.
11. `11_iso_7010_safety_signs` - public ISO 7010-style implementation, not official ISO source.
12. `12_iso_15223_medical_device_symbols` - public medical-device symbol implementation, not official ISO source.
13. `13_usp_pictograms_manual` - USP medication pictograms downloaded after license acceptance.

### `icon_data/analysis/`

This is the main canonical analysis area.

Important files:

- `dataset.csv`: one row per canonical icon selected for analysis.
- `features.csv`: older balanced pilot visual-feature sample.
- `features_metadata.json`: feature extraction settings and registry.
- `feature_failures.json`: latest visual-feature extraction failures.
- `normalization_failures.json`: latest normalization/conversion failures.
- `clustering_metadata_sample.csv`: metadata-enriched sample matching the older `features.csv` pilot.
- `clustering_metadata_missing_report.json`: metadata coverage report.
- `similarity/`: pairwise distance matrices, nearest-neighbor CSVs, visual similarity reports.
- `analysis_dashboard/`: current interactive dashboard outputs.

### `icon_data/analysis/analysis_dashboard/`

Generated by `code/build_analysis_dashboard.py`.

Important files:

- `README.md`: current dashboard state and open instructions.
- `index.html`: static dashboard UI.
- `dashboard_data.json`: compact data loaded by `index.html`.
- `sample_metadata.csv`: metadata rows for current dashboard sample.
- `features_image.csv`: image features for dashboard sample.
- `features_metadata.csv`: encoded metadata features.
- `features_combined.csv`: combined image + metadata features.
- `clusters_kmeans.csv`: k-means assignments.
- `clusters_hierarchical.csv`: hierarchical assignments.
- `cluster_assignments.csv`: all assignments.
- `cluster_summary.csv`: cluster sizes, dominant sets/categories, representative icon IDs.
- `analysis_dashboard_metadata_report.json`: sample and metadata summary.
- `assets/plotly.min.js`: vendored Plotly bundle.

Current dashboard sample:

- Up to 10 random icons per dataset.
- Fixed seed: `RANDOM_SEED = 42`.
- Change the per-dataset sample size in `PER_SET_SAMPLE_SIZE` inside `code/build_analysis_dashboard.py`, then regenerate.

## Script Map

| Script | Purpose | Primary outputs |
|---|---|---|
| `code/build_icon_dataset.py` | Builds canonical dataset rows and can normalize icon media to 256x256 PNGs. | `icon_data/analysis/dataset.csv`, `icon_data/normalized_256/`, normalization failure logs |
| `code/extract_icon_features.py` | Extracts small explicit set of visual complexity/structure features from normalized PNGs. | `icon_data/analysis/features.csv`, `feature_failures.json`, `features_metadata.json` |
| `code/visualize_icon_features.py` | Creates static visual reports from `features.csv`. | `icon_data/analysis/visualizations/` |
| `code/compute_icon_similarity.py` | Computes standardized Euclidean/cosine distances and nearest-neighbor outputs. | `icon_data/analysis/similarity/` |
| `code/build_clustering_metadata_sample.py` | Enriches feature sample with metadata tokens/categories and McDougall ratings. | `clustering_metadata_sample.csv`, `clustering_metadata_missing_report.json` |
| `code/build_analysis_dashboard.py` | Builds current static Plotly clustering dashboard. | `icon_data/analysis/analysis_dashboard/` |
| `code/extract_mcdougall_icons.py` | Crops McDougall appendix icons from rendered appendix pages. | `01_mcdougall_symbol_icon_set/extracted_icons_png/` |
| `code/extract_mcdougall_metadata.py` | OCR/manual correction pipeline for McDougall ratings. | `mcdougall_ratings.csv`, `mcdougall_ratings_review.csv` |
| `code/render_blissymbolics_images.js` | Renders Blissymbolics char/word SVGs from local JS database/viewer. | `06_blissymbolics/rendered_svg/`, `metadata/rendered_symbols.json` |
| `code/download_arasaac.py` | Downloads ARASAAC English metadata and 300px PNGs. | `07_arasaac_pictograms/metadata/`, `png_300/` |
| `code/download_commons_category.py` | Generic Wikimedia Commons category downloader. | caller-specified output |
| `code/download_ghs_standard.py` | Downloads standard GHS hazard pictograms. | `08_ghs_hazard_pictograms/` |

## Feature Set

Current visual features are:

- `foreground_area_ratio`
- `canny_edge_density`
- `connected_components`
- `quadtree_leaf_count`
- `quadtree_structural_variability`
- `quadtree_mean_leaf_size`

Feature provenance:

- Strongly paper-backed by Forsythe-style complexity measurement: foreground amount, object/component count, edge detection, quadtree structural variability.
- Compatible with Garcia-style abstractness/component analysis, but not a full implementation of Garcia's exact taxonomy.
- Additional engineering proxies are acceptable if described as proxies, not as direct paper replications.

See `notes/feature_extraction_taxonomies.md` before making strong claims about feature origin.

## Literature Backbone

Use `papers/` for the thesis literature review. Core roles:

| Paper | Use |
|---|---|
| `Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf` | Broad glyph visualization foundation and design guidelines. |
| `A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.pdf` | Empirical glyph-study landscape and research-gap framing. |
| `The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf` | Perceptual similarity task model and contour evidence. |
| `Forsythe-Measuring_cion_complexity_automated.pdf` | Automated icon complexity metrics. |
| `Garcia-Development_validation_icons_abstractness.pdf` | Icon abstractness/concreteness measurement and validation. |
| `Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf` | Distinguishability/fail-safe glyph design concept. |
| `Taxonomy-Based_Glyph_Designwith_a_Case_Study_on_Visualizing_Workflows_of_Biological_Experiments.pdf` | Taxonomy-driven glyph construction and semantic mapping. |

## Research Direction

Recommended narrow thesis direction:

> Compare icon/glyph sets through automated visual complexity features, metadata features, pairwise similarity, and clustering, then discuss whether these metrics align with known human-facing properties such as McDougall complexity and semantic categories.

Good research questions:

1. Can automated visual complexity metrics predict perceived complexity or related McDougall norm ratings?
2. Do visual-feature clusters align more strongly with dataset/style, semantic category, or neither?
3. Where do visual nearest neighbors reveal potential confusion across different icon sets?
4. Can metadata and image features be combined to produce more interpretable icon groupings?

Avoid broad claims that the pipeline fully measures perception. The current repo supports computational pilot analysis; human validation is still a future step unless a study is added.

## Known Gaps And Missing Pieces

Current important gaps:

- OCHA has richer source metadata than currently propagated into `dataset.csv`.
- Mulberry has grammar/category/tag metadata that is only partly reflected in unified rows.
- USP pictograms still need stronger human-readable medication-instruction labels from the included index PDFs.
- AIGA categories can likely be improved from Wikimedia/local titles.
- ISO 7010 rows preserve code-like IDs more than human-readable warning meanings.
- McDougall ratings have been extracted locally, but the original standalone stimulus files remain request-only.
- The dashboard has no dendrogram visualization; hierarchical clustering is exposed as precomputed cuts/labels.
- The dashboard is a computational visualization only; it does not include human verification or participant-study results.
- `icon_data/iconsets/README.md` is older and incomplete compared with `icon_data/MANIFEST.md`; prefer the manifest.
- `tasks/week-2026-06-22-machine-clustering-visualization.md` is historical and may mention the old 1,038-row dashboard sample.

Recommended metadata enrichment order:

1. Parse OCHA `documentation/icon-lookup-table.md` into categories/tags.
2. Import Mulberry `icon_data/iconsets/05_mulberry_symbols/scripts/data/symbol-info-en.csv` fields.
3. Extract USP index PDF labels into a structured lookup keyed by pictogram number.
4. Normalize AIGA Wikimedia titles into categories where possible.
5. Add human-readable ISO 7010 meanings from a reliable source.
6. Continue verifying McDougall ratings against source-visible tables if using them for statistical claims.

## Safe Working Rules

- Do not treat generated outputs as hand-authored unless the user asks to edit them directly. Prefer changing scripts and regenerating.
- If both a generator and generated artifact exist, update the generator first.
- Use `rg` before broad file inspection.
- Do not restore or revert deleted/modified files unless explicitly asked.
- `icon_data/normalized_256/` is generated and large. Avoid committing or manually editing normalized images unless the task requires it.
- For dashboard changes, update both `code/build_analysis_dashboard.py` and regenerated files under `icon_data/analysis/analysis_dashboard/`.
- Verify dashboard changes with a local HTTP server because `index.html` loads JSON, Plotly, and image assets.
- For claims about current state, prefer generated metadata reports and current README files over older task notes.

## Quick Verification Recipes

Count current dashboard rows:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('icon_data/analysis/analysis_dashboard/dashboard_data.json').read_text())
print(data['metadata']['row_count'])
PY
```

Check Python generator syntax:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m py_compile code/build_analysis_dashboard.py
```

Check for stale dashboard sample text:

```bash
rg -n "1038|1,038|100 max|per_set_limit|max per set" code/build_analysis_dashboard.py icon_data/analysis/analysis_dashboard -g '!assets/**'
```

Check working tree before editing:

```bash
git status --short
```
