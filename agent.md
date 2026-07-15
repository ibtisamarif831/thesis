# Thesis Repository Agent Guide

This file is the first-stop orientation map for future agents working in this repository. Use it to route questions to the relevant area before searching broadly.

## After Each Task

Before closing any task in this repository, review `agent.md` and improve it with any newly discovered guidance that would help the next agent start faster or avoid repeating investigation. Keep updates concise, factual, and scoped to durable repository knowledge: current generated-output state, routing hints, workflow rules, verification commands, known gaps, or pitfalls encountered during the task. Do not add transient narration or duplicate details already captured elsewhere.

## Repository Purpose

This workspace supports a thesis on human and computer-based identification of icons/glyphs through literature-derived visual feature families.

Working thesis direction:

> This thesis investigates how visual factors identified in the glyph/icon perception literature can be organized into computer-measurable feature families, and how those computational feature scores compare with human identification and perception scores. The study uses icon/glyph datasets as stimuli, extracts visual feature-family scores from each glyph, records human-study judgments, and analyzes which visual factors explain agreement or mismatch between human perception and computer-based glyph identification.

The repo is not mainly a generic icon collection, a semantic icon-understanding project, or a general clustering demo. It is an empirical/computational thesis workspace for comparing literature-grounded visual feature families against human judgments of icon/glyph identification and perception.

Boundary for future work:

- Active feature families must be visually observable and computable from the glyph image.
- Semantic meaning, historical/cultural knowledge, familiarity, metaphor, and learnability are not computer-vision feature families. They may appear only as metadata, controls, study prompts, or human-study outcomes.
- Clustering and nearest-neighbor reports are analysis tools. They are not the thesis goal by themselves; they support comparison between computer-derived visual scores and human responses.

## Route Queries Here First

| Query type | Start here | Then check |
|---|---|---|
| Thesis framing, research questions, current progress | `THESIS_STATUS.md`, `agent.md`, `THESIS_CHECKLIST.md` | `tasks/current-thesis-next-steps.md`, `papers/` |
| Which icon sets exist locally | `icon_data/MANIFEST.md` | `icon_data/iconsets/README.md`, `data/10 icons.md` |
| Canonical icon dataset rows | `icon_data/analysis/dataset.csv` | `code/build_icon_dataset.py` |
| Normalized image generation | `code/build_icon_dataset.py` | `icon_data/analysis/README.md`, `icon_data/normalized_256/` |
| Visual feature extraction | `code/extract_icon_features.py` | `icon_data/analysis/features.csv`, `features_metadata.json`, `feature_failures.json` |
| Similarity / nearest-neighbor analysis | `code/compute_icon_similarity.py` | `icon_data/analysis/similarity/` |
| Thesis evaluation layers | `code/evaluation/evaluation_layers.md` | `tasks/current-thesis-next-steps.md`, `THESIS_STATUS.md` |
| Feature visual reports | `code/visualize_icon_features.py` | `icon_data/analysis/visualizations/` if present |
| Metadata enrichment for clustering | `code/build_clustering_metadata_sample.py` | `icon_data/analysis/clustering_metadata_sample.csv`, `clustering_metadata_missing_report.json` |
| Interactive analytics dashboard | `code/build_analysis_dashboard.py` | `icon_data/analysis/analysis_dashboard/README.md`, `index.html`, `dashboard_data.json` |
| McDougall extracted ratings | `icon_data/iconsets/01_mcdougall_symbol_icon_set/metadata/mcdougall_ratings.csv` | `code/extract_mcdougall_metadata.py` |
| McDougall extracted icons | `icon_data/iconsets/01_mcdougall_symbol_icon_set/extracted_icons_png/` | `code/extract_mcdougall_icons.py` |
| ARASAAC download issues | `code/download_arasaac.py` | `icon_data/iconsets/07_arasaac_pictograms/metadata/download_failures.json` |
| Blissymbolics rendering | `code/render_blissymbolics_images.js` | `icon_data/iconsets/06_blissymbolics/rendered_svg/`, `metadata/rendered_symbols.json` |
| Source provenance / old source plan | `data/10 icons.md`, `icon_data/MANIFEST.md` | `git show HEAD:source.md` if `source.md` is absent/deleted |
| Generated output status | `icon_data/analysis/README.md` | specific subfolder READMEs |
| Extracted paper text / literature evidence | `papers/extracted_text/README.md`, `notes/paper_feature_review.md` | original PDFs in `papers/` |

## Current Working State To Know

- The active canonical dataset is `icon_data/analysis/dataset.csv`.
- Current dataset size: **28,749** canonical rows in `dataset.csv`.
- Normalized PNGs are generated under `icon_data/normalized_256/`; this directory is large/generated and may be ignored by git.
- Current visual-feature sample: **1,038** rows in `icon_data/analysis/features.csv`, with **100 raw numeric image-feature columns** plus metadata columns. The active literature-mapped visual family set uses **81** of those raw columns; weak/non-interpretable channels remain only for traceability.
- Current feature extraction failures: `[]` in `icon_data/analysis/feature_failures.json`.
- The interactive dashboard is generated under `icon_data/analysis/analysis_dashboard/`.
- Current dashboard sample: **129** rows in `icon_data/analysis/analysis_dashboard/dashboard_data.json`.
- As of the latest dashboard change, the dashboard sample is **up to 10 random icons from each dataset**, using fixed `RANDOM_SEED = 42` in `code/build_analysis_dashboard.py`.
- The dashboard currently supports:
  - image, metadata, and combined feature variants;
  - k-means and hierarchical clustering;
  - k/cut values 3, 5, 7, and 10;
  - coloring by cluster, set, category, style, or numeric image feature;
  - filtering by icon set, category, and style;
  - selected icon details and cluster summaries;
  - a Feature Values tab restricted to up to two non-constant, lowest-redundancy features per visual family (13 total: two for six families and the single active Texture feature), selected from Feature Review's strongest absolute Spearman correlations, with searchable low/mean-nearest/high examples.
- Similarity outputs in `icon_data/analysis/similarity/` are based on the 1,038-row feature sample.
- Similarity and dashboard image-feature clustering use the active visual feature families from `code/build_analysis_dashboard.py`. Excluded raw channels are not used for active visual-family clustering or similarity ranking.
- The 7 thesis PDFs have extracted page-marked text under `papers/extracted_text/`; regenerate with `code/extract_paper_text.py`.
- Static feature visualizations under `icon_data/analysis/visualizations/` are summary-only when `matplotlib` is unavailable in the runtime. The interactive Plotly dashboard is the stronger current visual interface.
- Treat `THESIS_STATUS.md`, `icon_data/analysis/README.md`, generated metadata JSON files, and current scripts as the source of truth for current state.
- `source.md` is tracked historically but may be deleted in the working tree. Do not restore it unless explicitly asked; use `git show HEAD:source.md` for its last committed content.

## Runtime Notes

Prefer the bundled Python runtime for analysis scripts because the local `.venv` may not have NumPy/Pillow/sklearn installed:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

Common examples:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/build_analysis_dashboard.py
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/extract_icon_features.py --per-set-limit 100 --workers 4
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 code/compute_icon_similarity.py
```

The bundled runtime has NumPy/Pandas/Pillow, but not necessarily `matplotlib` or `sklearn`. Current similarity, dashboard, and PCA helpers do not require `sklearn`. `code/visualize_icon_features.py` writes a summary-only report if `matplotlib` is missing.

For static dashboard verification:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html
```

## Python Code Organization Rules

Future Python code generated for this repository must not continue the current large single-file pattern unless the change is a tiny one-off script. Existing large scripts can remain until there is a concrete reason to refactor them, but new substantive work should be organized as importable modules with thin command-line entrypoints.

Use this preferred layout for new Python pipeline code:

```text
code/
  thesis_pipeline/
    __init__.py
    paths.py
    io.py
    features/
      __init__.py
      extraction.py
      registry.py
    clustering/
      __init__.py
      distance.py
      metadata.py
    dashboard/
      __init__.py
      build.py
      templates.py
  build_new_output.py
```

Conventions for new code:

- Keep command-line scripts in `code/*.py` as thin wrappers: parse arguments, call a `main()` function from `code/thesis_pipeline/...`, and exit.
- Put reusable logic in modules under `code/thesis_pipeline/`.
- Do not put downloading, parsing, feature extraction, clustering, HTML generation, and file writing in one file.
- Split code by responsibility: paths/configuration, input/output, data normalization, feature computation, clustering/statistics, visualization/dashboard assembly, and reporting.
- Prefer pure functions for transformations: input data in, output data out, no hidden file writes.
- Keep file-system writes near the orchestration layer, not inside low-level feature/statistics functions.
- Use `dataclasses.dataclass(frozen=True)` for small configuration and result objects when dictionaries become unclear.
- Use `pathlib.Path` instead of string path manipulation.
- Use `argparse` for command-line options; do not hard-code new experiment parameters unless they are true repo constants.
- Add type hints to new public functions and return values.
- Keep functions short enough to inspect easily. If a function needs several phases, split it into named helpers.
- Name generated outputs explicitly in constants or config objects so it is easy to see what a script creates.
- Use structured readers/writers (`csv.DictReader`, `csv.DictWriter`, `json`, `pandas` when already appropriate) instead of ad hoc string parsing.
- Avoid global mutable state. Constants are fine; caches and accumulators should live inside functions/classes.
- Make random sampling deterministic with an explicit seed in config.
- Keep generated HTML/CSS/JS templates separate from Python computation when the template is more than a small literal.
- Add focused tests or smoke checks for new shared modules when behavior is non-trivial.

Refactoring guidance:

- When touching an existing large script for a small bug, make the smallest safe change.
- When adding a substantial feature to an existing large script, first extract the relevant reusable pieces into `code/thesis_pipeline/`, then keep the old script as a compatibility wrapper if needed.
- Do not rewrite every existing script just for style. Prefer incremental extraction that reduces real complexity.
- After moving code, run `py_compile` on both the wrapper and the new modules, then run the specific generator or a small sample mode if available.

## Top-Level Layout

| Path | Purpose |
|---|---|
| `agent.md` | This routing/orientation guide for agents. |
| `THESIS_CHECKLIST.md` | Thesis roadmap and high-level completion checklist. |
| `THESIS_STATUS.md` | Current thesis state, completed work, open gaps, and next step. |
| `data/10 icons.md` | Thesis-aligned icon/glyph source plan and rationale. |
| `papers/` | Core literature PDFs plus extracted text under `papers/extracted_text/`. Treat these as the thesis literature backbone. |
| `notes/` | Short explanatory notes, especially feature-taxonomy provenance. |
| `tasks/` | Current task tracker. Historical weekly planning files were removed after the July 2026 thesis-direction cleanup. |
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
- `features.csv`: current balanced pilot visual-feature sample, 1,038 rows and 100 raw numeric image-feature columns.
- `features_metadata.json`: feature extraction settings and registry.
- `feature_failures.json`: latest visual-feature extraction failures.
- `normalization_failures.json`: latest normalization/conversion failures.
- `clustering_metadata_sample.csv`: metadata-enriched sample from the earlier feature pilot; regenerate if it needs to match the current 1,038-row `features.csv` exactly.
- `clustering_metadata_missing_report.json`: metadata coverage report.
- `similarity/`: pairwise distance matrices, nearest-neighbor CSVs, visual similarity reports using active visual feature families.
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
| `code/extract_icon_features.py` | Extracts raw visual measurements from normalized PNGs for the thesis feature-family pipeline. | `icon_data/analysis/features.csv`, `feature_failures.json`, `features_metadata.json` |
| `code/visualize_icon_features.py` | Creates static visual reports from `features.csv`; writes summary-only output when `matplotlib` is unavailable. | `icon_data/analysis/visualizations/` |
| `code/compute_icon_similarity.py` | Computes Euclidean/cosine distances and nearest-neighbor outputs from active visual feature families. | `icon_data/analysis/similarity/` |
| `code/build_clustering_metadata_sample.py` | Enriches feature sample with metadata tokens/categories and McDougall ratings. | `clustering_metadata_sample.csv`, `clustering_metadata_missing_report.json` |
| `code/build_analysis_dashboard.py` | Builds current static Plotly clustering dashboard. | `icon_data/analysis/analysis_dashboard/` |
| `code/extract_mcdougall_icons.py` | Crops McDougall appendix icons from rendered appendix pages. | `01_mcdougall_symbol_icon_set/extracted_icons_png/` |
| `code/extract_mcdougall_metadata.py` | OCR/manual correction pipeline for McDougall ratings. | `mcdougall_ratings.csv`, `mcdougall_ratings_review.csv` |
| `code/render_blissymbolics_images.js` | Renders Blissymbolics char/word SVGs from local JS database/viewer. | `06_blissymbolics/rendered_svg/`, `metadata/rendered_symbols.json` |
| `code/download_arasaac.py` | Downloads ARASAAC English metadata and 300px PNGs. | `07_arasaac_pictograms/metadata/`, `png_300/` |
| `code/download_commons_category.py` | Generic Wikimedia Commons category downloader. | caller-specified output |
| `code/download_ghs_standard.py` | Downloads standard GHS hazard pictograms. | `08_ghs_hazard_pictograms/` |
| `code/extract_paper_text.py` | Extracts page-marked text from thesis PDFs. | `papers/extracted_text/` |

## Feature Set

The extractor stores 100 raw numeric image-feature columns for traceability. The active thesis mapping currently uses 81 of those columns, grouped into literature-aligned visual feature families:

- Complexity.
- Shape/silhouette.
- Stroke/structure.
- Density/fill.
- Balance/layout.
- Color/contrast.
- Texture.

Excluded raw channels are retained in exports but not used as active visual-family evidence: Hu moments, local binary pattern bins, `text_or_letter_presence`, and `crush_test_stability`.

Feature provenance:

- Stronger paper support exists for complexity, contour/closure, visual channels, distinguishability, and glyph-design taxonomies.
- Engineering proxies such as grid layout, stroke skeletons, and closure approximation must be described as computational proxies, not direct human-perception measurements.
- Similarity and dashboard image-feature clustering should use active visual feature families, not raw extractor groups or semantic metadata.

See `notes/feature_extraction_taxonomies.md` and `notes/literature_mapping_deep_pass_2026-07-08.md` before making strong claims about feature origin.

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

Current thesis statement:

> From the literature on glyph/icon perception, identify the visual factors humans use when distinguishing and identifying glyphs; organize those factors into computer-measurable feature families; compute those family scores for icon/glyph stimuli; collect human identification/perception scores for the same stimuli; and compare the two sets of scores to determine which visual factors influence agreement, mismatch, confusability, and distinguishability between humans and computer-based analysis.

Core research questions:

1. Which visual feature families from the literature can be measured reliably from glyph/icon images?
2. Which computed visual feature-family scores align with human identification or perception scores?
3. Where do humans and computer-based visual analysis disagree, and which feature families explain those mismatches?
4. Which feature families most influence perceived distinguishability, similarity, or confusability between glyphs?
5. How should semantic meaning, familiarity, and cultural/historical knowledge be separated from computable visual features in the analysis?

Avoid broad claims that the pipeline fully measures perception or semantic understanding. The current repo supports literature-backed visual feature extraction, feature-family organization, similarity/confusability reports, and dashboard exploration. Human-study data collection and statistical comparison against those computed scores still need to be added.

## Known Gaps And Missing Pieces

Current important gaps:

- OCHA has richer source metadata than currently propagated into `dataset.csv`.
- Mulberry has grammar/category/tag metadata that is only partly reflected in unified rows.
- USP pictograms still need stronger human-readable medication-instruction labels from the included index PDFs.
- AIGA categories can likely be improved from Wikimedia/local titles.
- ISO 7010 rows preserve code-like IDs more than human-readable warning meanings.
- McDougall ratings have been extracted locally, but the original standalone stimulus files remain request-only.
- The dashboard has no dendrogram visualization; hierarchical clustering is exposed as precomputed cuts/labels.
- The dashboard is a computational visualization only; it does not include quantitative human-study results yet.
- `icon_data/iconsets/README.md` is older and incomplete compared with `icon_data/MANIFEST.md`; prefer the manifest.
- `tasks/current-thesis-next-steps.md` is the current task tracker; old weekly plans were removed because they contradicted the current thesis direction.

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

Count current generated rows:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 - <<'PY'
import csv, json
from pathlib import Path
for path in [
    'icon_data/analysis/dataset.csv',
    'icon_data/analysis/features.csv',
    'icon_data/analysis/analysis_dashboard/features_image.csv',
    'icon_data/analysis/similarity/nearest_neighbors_euclidean.csv',
]:
    with open(path, newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = sum(1 for _ in reader)
    print(path, rows, len(header))
dashboard = json.loads(Path('icon_data/analysis/analysis_dashboard/dashboard_data.json').read_text())
print('dashboard row_count', dashboard['metadata']['row_count'])
PY
```

Check Python generator syntax:

```bash
/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m py_compile code/extract_icon_features.py code/compute_icon_similarity.py code/build_analysis_dashboard.py code/visualize_icon_features.py
```

Check feature extraction failures:

```bash
cat icon_data/analysis/feature_failures.json
```

Check working tree before editing:

```bash
git status --short
```
