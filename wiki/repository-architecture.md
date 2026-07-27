# Repository Architecture

[Wiki home](README.md) · [Pipeline](pipeline.md) · [Artifacts](artifacts-and-data-contracts.md)

## Top-Level Map

| Path | Responsibility |
|---|---|
| `AGENTS.md` | Repository-wide AI-agent instructions, including the mandatory wiki completion gate. |
| `agent.md` | First-stop orientation and durable repository rules for AI agents. |
| `THESIS_STATUS.md` | Concise current thesis status and boundaries. |
| `THESIS_CHECKLIST.md` | Broader completion checklist; verify against newer status files. |
| `code/` | Dataset, extraction, similarity, visualization, dashboard, literature, and evaluation code. |
| `data/` | Source-selection planning and historical dataset notes. |
| `icon_data/iconsets/` | Downloaded or locally rendered source collections. |
| `icon_data/normalized_256/` | Generated normalized PNGs used by analysis. |
| `icon_data/analysis/` | Canonical table, features, reports, similarity outputs, and dashboard artifacts. |
| `papers/` | Local thesis literature PDFs and extracted text. |
| `notes/` | Literature mapping, feature taxonomy, and research notes. |
| `tasks/` | Current plan and repo-local tickets. |
| `wiki/` | Organized operational and conceptual documentation. |
| `.agents/`, `.claude/` | Local agent skills/configuration; not thesis data. |

## Code Map

| Script/module | Role | Primary output |
|---|---|---|
| `code/build_icon_dataset.py` | Select canonical source media, create stable rows, optionally normalize images. | `dataset.csv`, `normalized_256/`, normalization failure report |
| `code/extract_icon_features.py` | Extract 110 raw numeric image measurements plus identity/context/mask metadata. | `features.csv`, `features_metadata.json`, feature failure report |
| `code/build_clustering_metadata_sample.py` | Add style, token, category, and McDougall context to feature rows. | `clustering_metadata_sample.csv`, missing report |
| `code/compute_icon_similarity.py` | Transform active features, robust-scale, weight families, compute distances and neighbors. | `analysis/similarity/` |
| `code/visualize_icon_features.py` | Create static feature distributions, correlations, PCA, and contact sheets where dependencies permit. | `analysis/visualizations/` |
| `code/build_analysis_dashboard.py` | Sample icons, compute feature variants/clusters/review data, and generate static UI. | `analysis/analysis_dashboard/` |
| `code/thesis_pipeline/dashboard/feature_selection.py` | Optional low-redundancy feature-selection utility; current Feature Values uses Feature Groups representatives instead. | Importable helper; covered by focused tests |
| `code/extract_paper_text.py` | Extract page-marked text from local PDFs. | `papers/extracted_text/` |
| `code/extract_mcdougall_icons.py` | Crop individual stimuli from appendix page renderings. | McDougall extracted PNG folder |
| `code/extract_mcdougall_metadata.py` | OCR and validate McDougall appendix ratings. | McDougall ratings and review CSVs |
| `code/download_*.py` | Acquire selected remote datasets. | Dataset-specific folders and metadata |
| `code/evaluation/` | Evaluation specifications and future human-computer comparison scripts. | Currently documentation only |

## Data and Generated-Output Boundaries

Treat downloaded source files and human-authored notes as inputs. Treat normalized images, analysis CSVs, JSON reports, HTML pages, plots, and pair sheets as generated artifacts unless a page explicitly says otherwise.

When both a generator and artifact exist:

1. Change the generator.
2. Regenerate the artifact.
3. Verify the artifact.
4. Update documentation if behavior, schema, or current-state facts changed.

Do not manually patch generated `index.html` when the same markup is emitted by `code/build_analysis_dashboard.py`.

## Preferred Direction for New Python Code

Large existing scripts may remain, but new substantial behavior should be moved into importable modules under `code/thesis_pipeline/`, with thin scripts in `code/*.py` for command-line orchestration.

Preferred separation:

```text
code/
  thesis_pipeline/
    paths.py
    io.py
    features/
    clustering/
    dashboard/
    evaluation/
  build_or_run_something.py
```

Keep transformations testable and mostly pure; keep filesystem writes near orchestration; use `pathlib`, type hints, explicit configuration, deterministic random seeds, and focused tests.

## Routing Questions

| Question | Inspect first |
|---|---|
| Why is an icon in or out of the canonical table? | `is_canonical_icon()` in `build_icon_dataset.py` |
| What does a feature mean? | `dashboard_data.json` feature sections, then `extract_icon_features.py` |
| Is a feature active? | `DASHBOARD_FEATURE_SECTIONS` and exclusion rules in `build_analysis_dashboard.py` |
| How is distance calculated? | `compute_icon_similarity.py` and `similarity_metadata.json` |
| Why does the dashboard look or behave this way? | `write_index_html()` in `build_analysis_dashboard.py` |
| What is in the current generated run? | The corresponding generated JSON/CSV report |
| What work is next? | `tasks/current-thesis-next-steps.md` and `tasks/tickets/` |
