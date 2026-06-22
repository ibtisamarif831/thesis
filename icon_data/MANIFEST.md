# Icon Data Manifest

Generated: 2026-06-22

Source list: `/Users/macbook/thesis/data/10 icons.md`

The current local data is focused on thesis-aligned icon/glyph sets. Weakly related photo, food, affective-picture, and 3D-object datasets were removed earlier on 2026-06-09.

## Current Local Icon Sets

| # | Folder | Source | Description | Local source/package status | Usable local icon media | Media/icon files |
|---:|---|---|---|---|---|---:|
| 1 | `01_mcdougall_symbol_icon_set/` | McDougall et al. BURO eprint | Normed interface symbols with ratings for concreteness, complexity, familiarity, meaningfulness, semantic distance, and agreement. Strong benchmark for icon perception. | Downloaded public PDF, 25 rendered appendix pages, and 239 extracted appendix-icon PNGs; standalone original stimulus files remain request-only | Yes | 265 |
| 2 | `02_aiga_dot_symbol_signs/` | Wikimedia Commons AIGA category plus supplemental `Symbol Sets.pdf` | Public-information and transportation pictograms designed for wayfinding and cross-language communication. Useful for standardized real-world symbols. | Downloaded as 80 Commons 512px PNG renderings; 8 SVG originals also retained; 3-page AIGA symbols PDF saved locally | Yes | 89 |
| 3 | `03_mapbox_maki_icons/` | `https://github.com/mapbox/maki` | Map and point-of-interest icons for cartography, navigation, places, transport, amenities, and services. Useful as a consistent modern icon system. | Downloaded from GitHub shallow clone; `.git` removed | Yes | 430 |
| 4 | `04_ocha_humanitarian_icons/` | `https://github.com/mapaction/ocha-humanitarian-icons-for-gis` | Humanitarian-response symbols for crises, disasters, logistics, health, shelter, infrastructure, and population needs. Useful for domain-specific operational icons. | Downloaded from GitHub shallow clone; `.git` removed | Yes | 721 |
| 5 | `05_mulberry_symbols/` | `https://github.com/mulberrysymbols/mulberry-symbols` | AAC communication symbols designed for adults with language difficulties. Useful for accessibility and pictorial communication research. | Downloaded from GitHub shallow clone; `.git` removed | Yes | 3447 |
| 6 | `06_blissymbolics/` | `https://github.com/blissymbolics/blissymbols` | Symbolic-language database for Blissymbolics, a constructed AAC symbol system. Useful as a symbolic-language reference and AAC comparison set. | Source package downloaded from GitHub shallow clone; `.git` removed; rendered locally from the included database/viewer into standalone SVG stimuli; normalized to 256px PNGs | Yes | 5825 |
| 7 | `07_arasaac_pictograms/` | ARASAAC API and static image service | Large AAC pictogram set for communication, education, accessibility, autism support, and daily activities. Useful for broad pictogram analysis. | Downloaded English metadata and 300px PNG pictograms; 2 image IDs unavailable and logged | Yes | 13798 |
| 8 | `08_ghs_hazard_pictograms/` | OSHA Hazard Communication Pictograms | Standard chemical hazard pictograms for safety communication. Small, highly standardized set useful as a controlled safety-symbol category. | Downloaded the nine standard OSHA public-domain PNG pictograms | Yes | 9 |
| 9 | `09_universal_symbols_healthcare_webfont/` | `https://github.com/samcome/webfont-medical-icons` | Healthcare and hospital wayfinding icons for departments, services, accessibility, and facilities. Useful for medical/public-service icon comparison. | Downloaded from GitHub shallow clone; `.git` removed; SVG assets under `packages/svg/` | Yes | 299 |
| 10 | `10_openmoji/` | `https://github.com/hfg-gmuend/openmoji` | Open-source emoji and pictographic communication set covering faces, objects, activities, symbols, places, and concepts. Useful as a large pictorial baseline. | Downloaded from GitHub shallow clone; `.git` removed | Yes | 29456 |
| 11 | `11_iso_7010_safety_signs/` | `https://github.com/Adewra/ISO7010-Font` | Safety-sign symbols, mainly warning signs, based on ISO 7010-style conventions. Useful for safety and hazard-perception comparison. | Downloaded from GitHub shallow clone; `.git` and embedded `.svn` metadata removed; public implementation, not official ISO source | Yes | 79 |
| 12 | `12_iso_15223_medical_device_symbols/` | `https://github.com/t4dhg/medical-device-symbols` | Medical-device labelling symbols for manufacturer, sterility, batch, temperature, warnings, UDI, and related device-package meanings. | Downloaded from GitHub shallow clone; `.git` removed; public implementation, not official ISO source | Yes | 29 |
| 13 | `13_usp_pictograms_manual/` | `https://www.usp.org/health-quality-safety/usp-pictograms` | Medication-instruction pictograms for patient communication and health literacy. Potentially useful for medication-use and health-literacy comprehension research. | Downloaded after license acceptance via USP email links; ZIP archives preserved under `downloads/`; extracted GIF and EPS libraries plus index PDFs retained; canonical GIF rows normalized to 256px PNGs | Yes | 169 |

Media/icon files count SVG, PNG, GIF, EPS, PDF, OTF, TTF, WOFF, WOFF2, and EOT files. Rows with `0` are intentional and mean no usable local media files are present, not an unknown count.

## Preserved Download Archives

No download archives are currently preserved in `icon_data/downloads/`.

## Verification

- `.git` directories were removed from the downloaded repository folders.
- Checksums are stored in `icon_data/metadata/sha256sums.txt` and were regenerated after the 2026-06-22 USP and Blissymbolics normalization updates.
- USP and Blissymbolics canonical dataset rows have normalized 256px PNGs in `icon_data/normalized_256/` with zero normalization failures.
- Total local icon data size is now larger because ARASAAC and Mulberry were added.

## Notes

- McDougall public source material is downloaded as the BURO article PDF plus rendered appendix pages. Standalone original icon files still require an author/institutional request.
- AIGA/DOT is complete as local 512px PNG renderings for the 80 SVG files listed in the Commons AIGA category. Commons rate-limited original SVG downloads, so only 8 SVG originals are retained alongside the PNG set and `Symbol_Sets_AIGA.pdf`.
- Blissymbolics is rendered from the local JavaScript database/viewer into 1,150 character SVGs and 4,675 word SVGs under `06_blissymbolics/rendered_svg/`; all 5,825 canonical rows are normalized to PNG.
- ARASAAC is large: 13,800 metadata records and 13,798 downloaded PNGs. Missing image IDs are recorded in `07_arasaac_pictograms/metadata/download_failures.json`.
- GHS was downloaded from OSHA rather than Wikimedia Commons because Commons throttled bulk file retrieval.
- ISO 7010 and ISO 15223 folders are practical public implementations, not official ISO distributions.
- USP pictograms were downloaded after license acceptance from USP email links. The extracted local library includes 83 GIF files, 84 EPS files, and 2 index PDFs; ZIP archives are preserved separately under `13_usp_pictograms_manual/downloads/`. The 83 canonical GIF rows are normalized to PNG.
