# Verification and Troubleshooting

[Wiki home](README.md) · [Commands](commands-and-scripts.md) · [Dashboard UI](dashboard-ui.md)

## Verification Levels

| Change type | Minimum evidence |
|---|---|
| Documentation only | Link/heading checks, source fact checks, diff review. |
| Python logic | Focused tests plus `py_compile`. |
| Generator | Logic checks, successful generation, schema/count validation. |
| Dashboard | Generator checks plus served browser walkthrough and console/network inspection. |
| Dataset/source | Provenance, canonical counts, normalization/failure report, downstream impact. |
| Thesis/evaluation claim | Direct literature or collected-data evidence and explicit boundary review. |

## Current Snapshot Checks

Run from the repository root:

```powershell
python -c "import csv,collections; r=list(csv.DictReader(open('icon_data/analysis/dataset.csv',encoding='utf-8'))); print('rows',len(r),'sets',len(set(x['set_id'] for x in r))); print(collections.Counter(x['set_name'] for x in r))"
```

```powershell
python -c "import csv; r=list(csv.DictReader(open('icon_data/analysis/features.csv',encoding='utf-8'))); print('rows',len(r),'columns',len(r[0]))"
```

```powershell
python -c "import json; x=json.load(open('icon_data/analysis/analysis_dashboard/dashboard_data.json',encoding='utf-8')); m=x['metadata']; print('rows',m['row_count'],'active',len(m['image_feature_columns']),'families',len(m['image_feature_sections'])); print('review',x['feature_review']['summary']); print('explorer',x['feature_explorer']['metadata'])"
```

Expected for the current schema-v2 snapshot: 28,749 canonical rows, 13 sets, 28,749 feature rows, 133 feature-table columns, 129 dashboard rows, 81 active registry features, seven selected analysis features under the `representatives` preset, seven families, and seven Feature Values explorer features matching the Feature Groups representatives.

For schema v2, expect 28,749 feature rows, 133 columns (23 metadata + 110 numeric), `feature_schema_version == 2`, ten finite `_v2` columns, and zero feature failures. Also verify mask modes/flags, `strict_red_flag_v2` is binary, orientation confidence lies in 0–1, and the active registry remains exactly 81.

Run the benchmark tooling after extraction:

```powershell
python code/evaluation/build_feature_v2_benchmark.py
python code/evaluation/evaluate_feature_v2_benchmark.py
```

The second command must report a pending/blocked gate until two raters complete every required field. That is correct behavior, not an engineering failure.

## Python Checks

```powershell
python -m py_compile code/build_icon_dataset.py code/extract_icon_features.py code/compute_icon_similarity.py code/build_analysis_dashboard.py code/visualize_icon_features.py
python -m pytest code/tests
```

`build_icon_dataset.py` must use explicit UTF-8 for ARASAAC/OpenMoji metadata and canonical CSV output, and must hash/serialize repository paths with POSIX `/` separators. Cross-platform regressions are included in the test suite above; Windows default encodings or native backslashes can otherwise break a full scan or change every stable `icon_id`.

Full feature extraction records unexpected worker exceptions per icon instead of terminating the run. Verify that `feature rows + feature failures == selected_row_count`; for a clean accepted run, the failure list should be empty.

The extractor defaults to multiprocessing for full-corpus throughput. If process creation is restricted in a particular environment, rerun with `--executor thread`, understanding that CPU-bound extraction may be substantially slower.

`extract_paper_text.py` imports `pdfplumber`; syntax compilation can succeed while execution fails if the dependency is absent. Test actual entry points whose imports matter.

## Dashboard Runtime Check

Start the server:

```powershell
python code/serve_analysis_dashboard.py --port 8765
```

Verify:

- `index.html`, `dashboard_data.json`, and `assets/plotly.min.js` return HTTP 200;
- normalized icon requests return HTTP 200;
- no JavaScript errors appear;
- the interaction walkthrough in [Dashboard UI](dashboard-ui.md) succeeds;
- missing `OPENROUTER_API_KEY` disables only AI execution and shows a configuration message;
- a budget-approved or mocked AI run renders the same ordered icon IDs in both plots, reports metrics and cache counts, and appears in recent history;
- repeating the unchanged sample reports cache hits, while changing the sample/settings marks the display stale without an automatic request;
- `ai_clustering.sqlite3` reports schema version 1 and `journal_mode=delete`, with no `-wal` or `-shm` sidecars;
- all seven v2 families, four cohorts, independent up-to-20-icon Randomize state, strict-red contents, orientation ordering/mean/undefined state, uncertain-mask exclusion, live representative-to-Image-Clustering synchronization, and the separate fullscreen exact-three icon comparison modal behave correctly;
- the Color By control is recorded as a known gap until rendering actually uses it.

Opening `index.html` with a filesystem URL can trigger fetch/CORS/path failures and is not sufficient verification.

## Failure Reports

Check these after relevant runs:

- `icon_data/analysis/normalization_failures.json`
- `icon_data/analysis/feature_failures.json`
- `icon_data/analysis/analysis_dashboard/feature_failures.json`
- `icon_data/analysis/clustering_metadata_missing_report.json`
- `icon_data/analysis/analysis_dashboard/analysis_dashboard_metadata_report.json`
- dataset-specific downloader failure logs, especially ARASAAC.

An empty list is meaningful evidence only when it was produced by the run being evaluated.

## Common Problems

### `ModuleNotFoundError`

The local environment may lack `pdfplumber`, Matplotlib, OpenCV, scikit-learn, or pytest. Use the configured bundled workspace runtime when available or install the specific missing dependency. Do not assume every script needs scikit-learn: current PCA, clustering, and similarity helpers implement required operations directly.

### ImageMagick `magick` Not Found

Normalization requires ImageMagick on `PATH`. Check:

```powershell
magick -version
```

Do not run a forced full normalization until a small limited sample succeeds.

### Missing Dashboard Images

Check:

1. server started from repository root;
2. `normalized_path` begins with the expected dashboard-relative `../../normalized_256/` path;
3. `analysis_dashboard_metadata_report.json` reports zero missing normalized paths;
4. the requested file exists and returns 200.

### Plot Is Empty

In the default Image view no active features are selected. Click **All** or a family preset. If features are selected, inspect the console and confirm Plotly/data loaded.

### Color By Does Nothing

This is a current implementation gap: visible icons are layout images and the selected color state is not applied. See [Dashboard implementation](dashboard-implementation.md).

### Counts Differ Between Views

Image and AI Clustering use the unique composite of all seven Feature Groups samples for the active cohort, while Metadata/Combined use the generated 129-row sample. Feature Groups draws from the 28,260 rows that pass the technical-quality gate. Verify `feature_group_excludes_uncertain_masks == true`, `feature_group_requires_finite_representatives == true`, that no `feature_group_records` item has an uncertain mask or a null representative, and that `feature_group_quality_audit.json` reports 489 uncertain-mask exclusions and zero low-value exclusions. Each family sample must contain no more than two records in each of the 10 equal-width bins computed from its eligible family/cohort range. For the default All cohort, verify 20 unique icons per family and 140 unique composite IDs; sparse cohorts can correctly produce fewer because empty bins are not backfilled. Feature Review/Values use the complete corpus directly. This distinction is intentional and should remain explicit in labels and verification.

### AI Comparison Does Not Match the Current Feature Selection

Changing checked Clustering features marks any loaded AI comparison stale but does not call the provider automatically. Verify that selecting only two features recomputes the ordinary Image Clustering view, then open AI Clustering and confirm the stale message remains until **Run AI Clustering** is explicitly pressed. The new comparison's feature-side PCA and labels must use those two features; the AI side must continue to use the full cached image embeddings for the same icon IDs. For a loaded completed run, confirm the visible cards include only pairwise agreement and cache. ARI, NMI, and provider usage remain available only in stored run data.

### Similarity Results Look Implausible

Verify active columns and preprocessing in `similarity_metadata.json`, then visually inspect pairs. Common causes include stale outputs after feature changes, source/rendering artifacts, family imbalance, a proxy behaving poorly, or confusion between semantic and visual similarity.

## Documentation Link Check

Wiki links are repository-relative Markdown paths. After editing, search every Markdown link target and confirm the referenced local file exists. Also search for stale UI claims such as category/style filters or visible Color By behavior.

## Diff Review

```powershell
git status --short
git diff -- wiki agent.md
```

Generated folders can create large diffs. Confirm every changed artifact was intended and do not revert unrelated user work.
