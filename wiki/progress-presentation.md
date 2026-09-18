# Progress Presentation

[Wiki home](README.md) · [Literature](literature-and-evidence.md) · [Human study](evaluation-and-human-study.md)

## Authoritative Deck

The native Google Slides [Progress Presentation](https://docs.google.com/presentation/d/1JfRMxbgkq1TC0JoFUpbYyZCgINCCxYIxCmdSrcvoN4k/edit) is the presentation source of truth. Local PPTX files and builders may predate native edits; do not overwrite the live deck from them without reconciling current content and comments.

The separate [presentation-ready speaker notes](../presentations/thesis-progress-presentation-speaker-notes.md) provide a concise script and question responses for the 17-slide deck. They are a delivery aid and do not alter the native Google Slides speaker notes.

## Verified Revision: 6 September 2026

The literature/context corrections were applied in place to 17 slides, revision `KZdKxVkOrhry6A`. The deck retains its existing slide IDs, layout, images, and comment threads. All 10 comment threads retained their states: six resolved and four unresolved. Thread status is separate from whether a requested content change has been implemented.

The corrected deck:

- bounds the research gap to the reviewed papers and selected glyph sets;
- describes canonical source selection without claiming general visual deduplication;
- distinguishes exploratory glyph-review readiness from the blocked participant pilot;
- uses “left–right symmetry” visibly while identifying `horizontal_symmetry_v2` in notes;
- explains enclosure, orientation, saturation, and texture as limited computational proxies;
- removes an unqualified Fuchs (2014) trial count and documents the source inconsistency in notes;
- labels the AI comparison as a saved example, with pairwise agreement 0.783 and adjusted Rand index 0.169;
- describes visual matching and the planned human–computer comparison as provisional;
- corrects the Legg Figure 1 source note, timeline evidence, and slide 10/11 footers.

The seven families remain a thesis-specific, literature-informed synthesis. Canny has the closest measure-level precedent; the other formulas remain thesis operationalizations. No participant threshold or human–computer result is claimed.

## Numerical Evidence

All 13 displayed source counts were checked against `icon_data/analysis/dataset.csv`: 28,749 rows. `features.csv` contains 110 numeric extractor columns plus 23 metadata columns; only seven representatives define thesis analysis. The presentation's 28,260-row technical Feature Groups figure describes the earlier full-corpus dashboard pool and is not an approved study sample. After the meeting, the live dashboard was narrowed—without deleting the canonical corpus—to AIGA/DOT, OCHA, Universal Symbols Healthcare Webfont, ISO 7010, and ISO 15223: 649 feature rows, of which 397 pass the current mask-quality gate.

The slide 12 example is saved run `4292e58b-c9f5-467e-8b93-82494379534e` in `icon_data/analysis/ai_clustering/ai_clustering.sqlite3`, dated 4 August 2026: 140 icons, k-means, k=7, seed=42, model `voyageai/voyage-multimodal-3.5`. Recalculation from stored assignments gives 443 pairs together in both partitions, 7,176 apart in both, and 2,111 disagreements: 7,619 / 9,730 = 0.7830421377. Stored adjusted Rand is 0.1685853804 and normalized mutual information is 0.2523347126. Most raw agreement comes from pairs kept apart. These are partition comparisons, not human accuracy. The database does not establish feature-version equivalence with every later dashboard build.

Pilot readiness remains governed by `icon_data/analysis/feature_v2_release_gate.json`: `blocked_pending_two_rater_benchmark`, `pilot_enabled: false`. Study details also remain subject to supervisor approval and piloting.

## Verification and Future Edits

The edited native presentation was read back and checked for structural text issues (zero reported). A fresh PDF was exported from Google Slides, all 17 pages rendered, and all slides visually inspected. Content fits the retained layouts. No local PPTX was regenerated; no code, dataset, or human-study protocol was changed.

Useful future additions, not yet added as slides: a pipeline/quality diagram; one concrete feature-measurement example; and an explanation of how sampled features and image embeddings produce candidate contrasts. Keep formula details, sampling settings, and reproducibility information in notes or an appendix where they would overload the main narrative.
