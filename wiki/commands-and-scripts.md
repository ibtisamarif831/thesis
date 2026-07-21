# Commands and Scripts

## Schema-v2 measurement repair

```powershell
python code/extract_icon_features.py --per-set-limit 3 --workers 4 --executor thread --output tmp/features_v2_limited.csv --failures tmp/features_v2_limited_failures.json
python code/extract_icon_features.py --workers 12 --executor process
python code/evaluation/build_feature_v2_benchmark.py
python code/evaluation/evaluate_feature_v2_benchmark.py
python code/build_analysis_dashboard.py
```

The benchmark builder deterministically freezes 50 rows per family plus 100 strict-red cases and writes side-by-side mask overlays. The evaluator never enables the pilot with incomplete ratings.

[Wiki home](README.md) · [Pipeline](pipeline.md) · [Verification](verification-and-troubleshooting.md)

Run commands from the repository root. On Windows, use `python`; on systems where Python 3 is exposed as `python3`, substitute that executable. The environment must include the required libraries and external tools.

## Core Pipeline

### Canonical Dataset and Normalization

```powershell
python code/build_icon_dataset.py
python code/build_icon_dataset.py --normalize --workers 8
```

Options:

- `--normalize` generates/checks normalized images after rebuilding the CSV.
- `--workers N` controls normalization threads; default 8.
- `--limit N` limits normalization only, useful for smoke testing.
- `--force` overwrites existing normalized targets; use intentionally.

External requirement: ImageMagick `magick` on `PATH`.

### Feature Extraction

```powershell
python code/extract_icon_features.py --workers 12 --executor process
```

Options:

- `--dataset PATH`
- `--output PATH`
- `--failures PATH`
- `--limit N`
- `--per-set-limit N`
- `--workers N`
- `--executor process|thread`
- `--foreground-threshold N`

`--limit` truncates after per-set sampling. The current canonical full-corpus artifact uses neither limit; `--per-set-limit` remains available for smoke tests or balanced pilots. Multiprocessing is the default executor, and the verified run used 12 workers.

### Metadata-Enriched Feature Sample

```powershell
python code/build_clustering_metadata_sample.py
```

This script has no command-line options.

### Similarity

```powershell
python code/compute_icon_similarity.py
```

Options:

- `--features PATH`
- `--output-dir PATH`
- `--neighbors N` (default 5)
- `--closest-pairs N` (default 100)

### Static Feature Visualizations

```powershell
python code/visualize_icon_features.py
```

Options: `--features PATH`, `--output-dir PATH`. Matplotlib is optional; output is reduced when it is unavailable.

### Dashboard

```powershell
python code/build_analysis_dashboard.py
```

The builder currently has no command-line options. Sample size, seed, cluster counts, and paths are module constants.

Serve it with:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/icon_data/analysis/analysis_dashboard/index.html`.

## Literature and McDougall Utilities

```powershell
python code/extract_paper_text.py
python code/extract_mcdougall_icons.py
python code/extract_mcdougall_metadata.py
```

Paper extraction supports `--papers-dir` and `--output-dir` but imports `pdfplumber` at startup. McDougall metadata supports `--output`, `--review-output`, and `--no-fallback`; it requires Tesseract OCR.

McDougall icon extraction uses geometry calibrated to the current appendix page renderings. Treat source-page size changes as breaking inputs and visually inspect crops.

## Source Acquisition Utilities

These commands make network or source-data changes and should be run only for an intentional refresh:

| Script | Purpose |
|---|---|
| `download_arasaac.py` | Download English ARASAAC metadata and 300-pixel PNGs. |
| `download_ghs_standard.py` | Download the nine OSHA GHS pictograms. |
| `download_commons_category.py` | Download files and metadata from a Wikimedia Commons category. |
| `render_blissymbolics_images.js` | Render Blissymbolics source data into standalone SVG stimuli. |

Commons downloader required options are `--category` and `--out`; optional flags are `--recursive` and repeatable `--mime`.

Before refreshing a dataset, record the reason, inspect its README/source note, preserve license/provenance, and expect canonical identities or counts to change.

## Tests and Syntax Checks

```powershell
python -m pytest code/tests
python -m py_compile code/build_icon_dataset.py code/extract_icon_features.py code/compute_icon_similarity.py code/build_analysis_dashboard.py code/visualize_icon_features.py
```

If `pytest` is unavailable, install/use the configured project runtime or run the focused test through a compatible environment. Syntax success does not replace generator and browser verification.

## Inspection Recipes

Dataset and feature counts:

```powershell
python -c "import csv; print(sum(1 for _ in open('icon_data/analysis/dataset.csv', encoding='utf-8'))-1); print(sum(1 for _ in open('icon_data/analysis/features.csv', encoding='utf-8'))-1)"
```

Dashboard metadata:

```powershell
python -c "import json; x=json.load(open('icon_data/analysis/analysis_dashboard/dashboard_data.json', encoding='utf-8')); print(x['metadata']['row_count']); print(len(x['metadata']['image_feature_columns']))"
```

Git scope:

```powershell
git status --short
git diff --stat
```

## Regeneration Order After Common Changes

| Changed | Regenerate |
|---|---|
| Source media/canonical selection | Dataset → normalization → features → metadata → similarity/visuals/dashboard |
| Normalization behavior | Normalized images → features → downstream analysis |
| Raw feature extraction | Features → metadata enrichment → similarity → visualizations → dashboard |
| Active family mapping | Similarity → dashboard → documentation |
| Similarity preprocessing/weights | Similarity outputs and metadata |
| Dashboard UI/data contract | Dashboard outputs |
| Literature PDFs | Extracted text and literature index |
