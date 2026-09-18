# Artifacts and Data Contracts

## Feature Registry Contract

`code/thesis_pipeline/features/registry.py` is the executable authority for the ordered 110 raw feature IDs, seven thesis representatives, literature-informed families, exclusions, aliases, schema version, and orientation-confidence threshold. `code/tests/fixtures/feature_registry_v2.json` freezes the raw schema-v2 contract so consumer refactors cannot silently reorder or reclassify extractor outputs.

## Feature schema v2 artifacts

- `features.csv`: 23 metadata columns plus 110 numeric feature columns. Mask diagnostics are metadata; ten `_v2` numeric channels are finite. Schema-v1 measurements remain present.
- `features_metadata.json`: declares `feature_schema_version: 2`, foreground thresholds/rules, orientation-confidence threshold, and deprecated inactive representatives.
- `feature_v2_benchmark.csv`: frozen 450-row two-rater sheet (seven families × 50 plus 100 strict-red candidates).
- `feature_v2_mask_overlays/`: generated side-by-side source/mask overlays keyed by `icon_id`.
- `feature_v2_release_gate.json`: authoritative pending/passed/failed all-family release status. `pilot_enabled` may be true only after every gate passes.

[Wiki home](README.md) · [Repository architecture](repository-architecture.md) · [Pipeline](pipeline.md)

## Authoring Versus Generation

| Kind | Examples | Change policy |
|---|---|---|
| Human-authored direction | `THESIS_STATUS.md`, task tickets, notes, wiki | Edit deliberately and keep aligned with evidence. |
| Source data | `icon_data/iconsets/`, papers | Preserve provenance/licenses; refresh intentionally. |
| Generator code | `code/*.py`, `code/thesis_pipeline/` | Primary location for behavior changes. |
| Generated artifacts | normalized PNGs, analysis CSV/JSON/HTML/PNG | Regenerate from code; avoid hand edits. |

## Canonical Dataset Contract

`icon_data/analysis/dataset.csv` has 12 columns. Its stable join key is `icon_id`, derived from the repository-relative canonical source path. `normalized_path` points to the generated analysis image.

Breaking changes include altering canonical source selection, moving source files, changing ID construction, renaming columns, or changing normalization paths.

## Feature Contract

`icon_data/analysis/features.csv` currently has:

- 28,749 rows;
- 23 metadata/identity/mask-diagnostic columns;
- 110 raw numeric image-feature columns;
- 133 columns total.

`features_metadata.json` records the last extraction configuration and extractor registry. `feature_failures.json` must exist even when it contains `[]`.

Analysis selection is a separate contract from raw-column presence: the current thesis profile contains seven representatives. Never infer thesis membership merely from presence in the CSV; all other numeric columns are retained extraction data.

## Similarity Contract

`icon_data/analysis/similarity/similarity_metadata.json` is the reproducibility manifest. It declares:

- source row count and raw columns;
- selected analysis preset;
- transformed and active columns;
- exclusions and reasons;
- circular preprocessing;
- robust scaling and clipping;
- feature/family weights;
- metrics and output limits.

Distance-matrix row and column order must match the source feature-frame order. Nearest-neighbor and closest-pair tables carry explicit source/target identities for safer consumption.

## Dashboard Contract

`dashboard_data.json` is the runtime API for the static UI. Its top-level `metadata`, `records`, `clusters`, `feature_review`, and `feature_explorer` keys are documented in [Dashboard implementation](dashboard-implementation.md). `metadata.included_set_ids` and `metadata.included_set_names` record the five-source dashboard boundary without changing the canonical corpus. `metadata.analysis_feature_preset` records the code-selected profile, while `metadata.image_feature_columns` records the seven resolved representatives. Each section under `metadata.image_feature_sections` contains only its configured representative, including registry-owned `evidence_scope`, `evidence`, and `citation` fields. Generated `records[].image_features` likewise contain only those seven representatives plus the auxiliary monochrome, orientation-confidence, red-ratio, and strict-red fields required by the UI; raw registry columns are not a browser API.

The dashboard folder also contains the exact CSV inputs/outputs used to audit the generated view. Do not assume all sections use the same sample size.

## Generated Output Inventory

### `icon_data/analysis/`

| Artifact | Generator |
|---|---|
| `dataset.csv` | `build_icon_dataset.py` |
| `normalization_failures.json` | `build_icon_dataset.py --normalize` |
| `features.csv` | `extract_icon_features.py` |
| `features_metadata.json` | `extract_icon_features.py` |
| `feature_failures.json` | `extract_icon_features.py` |
| `clustering_metadata_sample.csv` | `build_clustering_metadata_sample.py` |
| `clustering_metadata_missing_report.json` | `build_clustering_metadata_sample.py` |
| `similarity/` | `compute_icon_similarity.py` |
| `visualizations/` | `visualize_icon_features.py` |
| `analysis_dashboard/` | `build_analysis_dashboard.py` |
| `../../dist/dashboard/` | `build_public_dashboard.py` (ignored, deployable static bundle) |

### `papers/extracted_text/`

Generated by `extract_paper_text.py`; includes one page-marked text file per PDF plus README/manifest indexes.

### Dataset-Specific Derived Outputs

- McDougall cropped icons and OCR ratings/review tables.
- Blissymbolics rendered SVGs and rendered-symbol metadata.
- ARASAAC/API and other downloader metadata/failure logs.

Read each dataset README/source note before regeneration.

## AI Clustering SQLite Contract

`icon_data/analysis/ai_clustering/ai_clustering.sqlite3` is an intentionally tracked schema-versioned binary artifact. Version 1 contains `embeddings` (model ID, icon ID, image SHA-256, dimension, float32 vector, creation time), `runs` (status, configuration, JSON metrics including agreement and optional embedding cluster-variance profiles, usage, cache counts, warnings/errors), and `run_items` (ordered icon IDs, feature/AI labels, and both PCA coordinate pairs). The optional profile adds no columns or schema migration. Completed and failed valid runs are durable. Older completed runs can be enriched in the API response from hash-matched cached embeddings without modifying the database. The database contains neither `OPENROUTER_API_KEY` nor base64 payloads, uses rollback-journal mode, and must be closed before committing. Avoid concurrent writers and never add `-wal` or `-shm` sidecars.

The public static bundle does not copy this database. Its generated `public_data/ai_clustering.json` contains only completed runs whose complete item set is allowed by the current five-set, quality-eligible dashboard pool. `deployment_manifest.json` records compatible and excluded run counts, image/file/byte counts, and the deployed dashboard-data hash.

## Study Selection Contract

`study_selection_data.json` contains the 649-icon public selection catalog grouped by the five configured set IDs, with only `icon_id`, label, and public normalized path. Its selection protocol identifier is `five-sets-20-v1` and it requires exactly 20 unique icons per set.

The D1 schema stores one pseudonymous submission row and 100 ordered selection rows per reviewer code. `study_icons` is the authoritative server-side allow-list seeded from the same canonical rows. `study_submissions` records protocol version, optional rationale, and timestamps. `study_selections` records stable set/icon IDs and within-set selection order. These are internal stimulus-selection records, not participant responses and not evidence of human perception.

## Schema-Change Checklist

When changing a CSV or JSON contract:

1. Identify all readers with `rg`.
2. Update the producer first.
3. Update every reader and test.
4. Regenerate artifacts.
5. Compare row counts, column names, missingness, and IDs.
6. Open reports/dashboard, not just the files.
7. Update wiki pages and source-of-truth READMEs.
8. Explain migrations if existing human-response or study files depend on the old schema.

## Current-State Verification

Never use a wiki count as proof that the current artifact still has that count. Read the artifact itself. The dated snapshot on the wiki home is a convenience and an alert when values drift.
