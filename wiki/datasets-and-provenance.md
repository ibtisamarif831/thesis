# Datasets and Provenance

[Wiki home](README.md) · [Pipeline](pipeline.md) · [Artifacts](artifacts-and-data-contracts.md)

## Canonical Dataset

`icon_data/analysis/dataset.csv` is the canonical cross-dataset table. The current file contains **28,749 rows across 13 icon sets**.

| Set | Canonical rows | Purpose and provenance |
|---|---:|---|
| AIGA/DOT Symbol Signs | 80 | Public-information and transportation signs; AIGA/Wikimedia source. |
| ARASAAC Pictograms | 13,798 | Large AAC pictogram collection; ARASAAC API and static image service. |
| Blissymbolics | 5,825 | Constructed AAC symbol system; rendered locally from the source database/viewer. |
| GHS Hazard Pictograms | 9 | OSHA public-domain chemical hazard pictograms. |
| ISO 15223 Medical Device Symbols | 29 | Public GitHub implementation of medical-device labeling symbols; not an official ISO distribution. |
| ISO 7010 Safety Signs | 37 | Public ISO-7010-style font implementation; not an official ISO distribution. |
| Mapbox Maki | 215 | Consistent map and point-of-interest icon system from GitHub. |
| McDougall Symbol/Icon Set | 239 | Icons extracted from public appendix pages; original standalone stimuli remain request-only. |
| Mulberry Symbols | 3,436 | AAC communication symbols from the Mulberry source repository. |
| OCHA Humanitarian Icons | 359 | Humanitarian operations icon system from MapAction/OCHA source material. |
| OpenMoji | 4,495 | Color OpenMoji pictographs used as a broad pictorial baseline. |
| USP Pictograms | 83 | Medication-instruction GIFs obtained after USP license acceptance. |
| Universal Symbols Healthcare Webfont | 144 | Healthcare and hospital wayfinding symbols. |

`icon_data/MANIFEST.md` is the authoritative prose manifest for acquisition status, source URLs, local-media counts, caveats, and checksums.

## Canonical Row Schema

| Column | Meaning |
|---|---|
| `icon_id` | Stable 16-character SHA-1 prefix derived from the repository-relative source path. |
| `set_id` | Stable dataset-folder identifier. |
| `set_name` | Human-readable dataset name. |
| `relative_path` | Repository-relative canonical source-media path. |
| `filename` | Original source filename. |
| `label` | Best available human-readable label. |
| `category` | Source-derived or inferred category where available. |
| `format` | Canonical source extension without the leading dot. |
| `source` | Source name. |
| `source_url` | Provenance URL. |
| `normalized_path` | Repository-relative generated PNG path. |
| `notes` | Dataset-specific metadata fragments or identifiers. |

The row builder scans source folders, applies dataset-specific canonical-selection rules, enriches labels/categories for supported sets, and writes a deterministic path-derived identity. A moved source file receives a different `icon_id`, so path changes are data-contract changes.

## Canonical Selection Principles

The builder avoids duplicate sizes, helper assets, documentation images, and alternate representations. Examples include:

- extracted McDougall icons instead of full appendix pages;
- ARASAAC 300-pixel PNGs;
- selected canonical SVG/PNG branches for downloaded repositories;
- OpenMoji color SVGs rather than every style/export;
- ISO 7010 warning SVGs excluding `_Original` duplicates;
- USP GIF stimuli rather than duplicate EPS versions.

The executable truth is `is_canonical_icon()` in `code/build_icon_dataset.py`.

## Normalization

Normalized analysis images live under:

```text
icon_data/normalized_256/<set_id>/<slug>__<12-char-path-hash>.png
```

ImageMagick performs auto-orientation, fits the source inside 256 × 256 pixels, centers it on a transparent canvas, and preserves aspect ratio. For GIF files, only the first frame is used. Existing non-empty normalized files are skipped unless `--force` is supplied.

Normalization failures are written to `icon_data/analysis/normalization_failures.json`.

## Metadata Quality

Metadata richness differs sharply by source:

- **Very rich:** ARASAAC and OpenMoji.
- **Rich:** Mulberry and source-level OCHA metadata.
- **Good:** Blissymbolics.
- **Moderate:** healthcare webfont and AIGA.
- **Minimal but clean:** GHS and the public ISO implementations.
- **Important but partially structured:** McDougall and USP.

Known propagation gaps include OCHA categories/tags, Mulberry grammar and multilingual fields, USP human-readable instructions, AIGA category normalization, and ISO 7010 meanings. McDougall ratings are now available separately in `icon_data/iconsets/01_mcdougall_symbol_icon_set/metadata/mcdougall_ratings.csv` and are joined into selected analysis views.

Do not infer missing metadata from visual appearance without a documented rule. Metadata enrichment must remain distinguishable from pixel-derived measurements.

## Feature-Corpus Coverage

The current `features.csv` covers all 28,749 canonical rows across all 13 sets. The verified run used neither `--limit` nor `--per-set-limit`, and `feature_failures.json` is empty. Feature Groups filters the corpus to the 28,260 certain-mask rows before building its compact pool for transient equal-width stratified family samples and three-icon comparisons. Image and AI Clustering use the unique composite of all seven family samples, normally 140 icons for the All cohort. The separate deterministic 129-row generated sample remains authoritative for Metadata/Combined projections and exploratory-representative fallback, as described in [Dashboard implementation](dashboard-implementation.md).

## Provenance and Legal Caveats

- Preserve each source's license and attribution files in its dataset folder.
- Do not describe public GitHub implementations of ISO symbol systems as official ISO distributions.
- McDougall standalone originals are not present; the local stimuli were extracted from public appendix pages.
- USP files were obtained through the license-acceptance workflow and should not be redistributed casually.
- Checksums are stored under `icon_data/metadata/sha256sums.txt`; consult the manifest before regenerating them.
