# Thesis Repository Agent Guide

This file is the first-stop orientation map for future agents working in this repository. Use it to route questions to the relevant area before searching broadly. The comprehensive organized knowledge base is [`wiki/README.md`](wiki/README.md); use the wiki for subsystem explanations, workflows, data contracts, dashboard behavior, and verification guidance.

## After Each Task

The root `AGENTS.md` defines a mandatory wiki completion gate. Before closing any repository-changing task:

1. review the wiki pages for the affected subsystem;
2. update them to match any changed behavior, UI, pipeline, schema, data, feature, command, dependency, output, status, limitation, or verification workflow;
3. verify affected links and current-state facts;
4. state which wiki pages were updated in the final handoff;
5. review `agent.md` and add any concise, durable routing rule or pitfall that would help the next agent.

A task is not complete while its wiki documentation is stale. Do not add filler edits when nothing durable changed; a read-only task may leave the wiki unchanged after confirming it is still accurate.

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
| Full repository orientation and workflows | `wiki/README.md` | Relevant topic page, then the linked script/artifact |
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
- Canonical dataset metadata contains non-ASCII labels; keep JSON/CSV reads and writes explicitly UTF-8. Serialize repository-relative paths with POSIX `/` separators before hashing so `icon_id` values remain stable across Windows and macOS/Linux.
- Current visual-feature corpus: **28,749** rows in `icon_data/analysis/features.csv`, with **110 raw numeric image-feature columns** plus 23 metadata columns under feature schema v2. The active literature-mapped visual family set remains **81** columns: seven legacy representatives are retained but inactive and replaced one-for-one by v2 measurements. The two-rater release gate is still pending, so the pilot is blocked.
- Current feature extraction failures: `[]` in `icon_data/analysis/feature_failures.json`.
- Current Feature Groups Complexity representative: `canny_edge_density`. Grayscale quadtree variability remains active for broader analysis but is not the one-feature representative after cross-source visual-audit failures.
- The interactive dashboard is generated under `icon_data/analysis/analysis_dashboard/`.
- Current dashboard sample: **129** rows in `icon_data/analysis/analysis_dashboard/dashboard_data.json`.
- As of the latest dashboard change, the dashboard sample is **up to 10 random icons from each dataset**, using fixed `RANDOM_SEED = 42` in `code/build_analysis_dashboard.py`.
- The dashboard currently supports:
  - four views: Clustering, Feature Groups, Feature Values, and Feature Review;
  - image, metadata, and combined feature variants;
  - k-means and hierarchical clustering;
  - k/cut values 3, 5, 7, and 10;
  - a Color By selector for cluster, set, or numeric image feature, although the current image-overlay renderer does not visibly apply the selected color;
  - filtering by icon set;
  - selected icon details and cluster summaries;
  - a fullscreen Feature Groups detail workflow with one configured literature-backed representative per family, per-icon values, the average of the shown scores, and All/B/W/Red/Colored cohorts; configured defaults independently show 10 dataset-balanced icons drawn from the complete certain-mask corpus, sorted low-to-high by the representative value, and can be refreshed with **Randomize icons**; selecting exactly three current-sample icons opens a separate fullscreen comparison modal across all seven representatives; this display selection does not reduce the 81-feature analytical registry;
  - a Feature Values tab restricted to the seven configured Feature Groups representative features, one per visual family, with searchable low/mean-nearest/high examples and correlation context.
  - browser-session representative selectors in Feature Groups; changing one synchronizes the Clustering view to the current seven representatives and recomputes it without reload. Exploratory overrides use the 129-row clustering sample for family details because the compact full-corpus payload carries only the configured seven representatives.
- Existing similarity outputs in `icon_data/analysis/similarity/` remain based on the earlier 1,038-row pilot. Do not run the current quadratic pairwise implementation directly on all 28,749 rows without a scalable rewrite.
- Similarity and dashboard image-feature clustering use the active visual feature families from `code/build_analysis_dashboard.py`. Excluded raw channels are not used for active visual-family clustering or similarity ranking.
- The 7 thesis PDFs have extracted page-marked text under `papers/extracted_text/`; regenerate with `code/extract_paper_text.py`.
- Static feature visualizations under `icon_data/analysis/visualizations/` are summary-only when `matplotlib` is unavailable in the runtime. The interactive Plotly dashboard is the stronger current visual interface.
- Treat `THESIS_STATUS.md`, `icon_data/analysis/README.md`, generated metadata JSON files, and current scripts as the source of truth for current state.
- `source.md` is tracked historically but may be deleted in the working tree. Do not restore it unless explicitly asked; use `git show HEAD:source.md` for its last committed content.

## Runtime Notes

Run analysis scripts with the configured Python environment. On Windows use `python`; on systems that expose Python 3 as `python3`, substitute that executable. Dependency availability varies, so check the missing package before switching runtimes or installing anything.

Common examples:

```powershell
python code/build_analysis_dashboard.py
python code/extract_icon_features.py --workers 12 --executor process
python code/compute_icon_similarity.py
```

The verified Windows Python has NumPy/Pandas/Pillow and pytest, but currently lacks `pdfplumber`. Matplotlib and OpenCV remain optional for selected workflows. Current similarity, dashboard, and PCA helpers do not require `sklearn`. `code/visualize_icon_features.py` writes a summary-only report if `matplotlib` is missing. See `wiki/commands-and-scripts.md` and `wiki/verification-and-troubleshooting.md` for current commands and dependency notes.

For static dashboard verification:

```powershell
python -m http.server 8765 --bind 127.0.0.1
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
| `wiki/` | Comprehensive organized repository knowledge base for humans and AI agents. |
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
- `features.csv`: complete 28,749-row schema-v2 visual-feature corpus with 110 raw numeric image-feature columns and 23 metadata columns.
- `features_metadata.json`: feature extraction settings and registry.
- `feature_failures.json`: latest visual-feature extraction failures.
- `normalization_failures.json`: latest normalization/conversion failures.
- `clustering_metadata_sample.csv`: metadata-enriched sample from the earlier 1,038-row feature pilot; it does not currently match the complete `features.csv` corpus.
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
- This 129-row sample is primarily for Clustering. With configured representatives, Feature Groups uses a separate compact pool containing only rows with a certain foreground mask (currently 28,128 of 28,749) and draws 10 transient dataset-balanced icons independently for each family and color treatment. If a browser-session representative override is active, Feature Groups temporarily falls back to the 129-row clustering sample because it contains all selectable feature values.

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

The extractor stores 110 raw numeric image-feature columns for traceability. The active thesis mapping currently uses 81 of those columns, grouped into literature-aligned visual feature families:

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
- The dashboard Color By control is not currently applied to the visible icon-image overlays.
- The current dashboard filters only by icon set; older documentation that mentions category/style filters is stale.
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

```powershell
python -c "import csv,json; d=list(csv.DictReader(open('icon_data/analysis/dataset.csv',encoding='utf-8'))); f=list(csv.DictReader(open('icon_data/analysis/features.csv',encoding='utf-8'))); x=json.load(open('icon_data/analysis/analysis_dashboard/dashboard_data.json',encoding='utf-8')); print('dataset',len(d)); print('features',len(f)); print('dashboard',x['metadata']['row_count'])"
```

Check Python generator syntax:

```powershell
python -m py_compile code/extract_icon_features.py code/compute_icon_similarity.py code/build_analysis_dashboard.py code/visualize_icon_features.py
```

Check feature extraction failures:

```powershell
Get-Content icon_data/analysis/feature_failures.json
```

Check working tree before editing:

```bash
git status --short
```
