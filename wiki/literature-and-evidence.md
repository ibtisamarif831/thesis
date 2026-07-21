# Literature and Evidence

[Wiki home](README.md) · [Thesis overview](thesis-overview.md) · [Feature system](feature-system.md)

## Local Literature Corpus

Seven core PDFs are stored under `papers/`. Page-marked extracted text is stored under `papers/extracted_text/` and indexed by `papers/extracted_text/README.md` and `manifest.json`.

| Local paper | Primary use in this project |
|---|---|
| *A Systematic Review of Experimental Studies on Data Glyphs* | Study-design landscape, task dependence, human outcome measures, and need for user validation. |
| Forsythe et al., automated icon complexity | Strongest support for foreground amount, parts/components, holes, edges, and structural variability. |
| Garcia et al., icons varying in abstractness | Visible primitive taxonomy: components, open/closed figures, line directions, arrows, arcs; also demonstrates subjective/context limits. |
| *Glyph-based Visualization: Foundations, Design Guidelines, Techniques and Applications* | Visual channels, Gestalt grouping, symmetry, simplicity, area, and separation of perceptual from semantic concerns. |
| *Fail-Safe Design Scheme Based on Quasi-Hamming Distances* | Set-relative distinguishability and separation across visual channels. |
| *Taxonomy-Based Glyph Design* | Category-to-channel and domain-convention framing; useful for metadata and design context, not pixel-semantic claims. |
| *Influence of Contour on Similarity Perception of Star Glyphs* | Contour/closure influence on human similarity strategy, with task-specific caveats. |

## Evidence-to-Family Map

| Family | Main local support | Supported interpretation |
|---|---|---|
| Complexity | Forsythe; broader glyph-design review | Visual busyness, detail load, parts, edges, structural subdivision. |
| Shape/silhouette | Contour paper; Garcia; glyph foundations | Form, closure, contour strategy, roundness/angularity. |
| Stroke/structure | Garcia; quasi-Hamming; glyph foundations | Directional primitives, lines, arrows, arcs, graph-like structure. |
| Density/fill | Forsythe; contour paper; glyph foundations | Foreground amount, outline/fill behavior, visual weight. |
| Balance/layout | Glyph foundations | Symmetry, spatial grouping, centering, distribution of visual mass. |
| Color/contrast | Quasi-Hamming; glyph foundations | Hue, luminance/contrast, separable visual channels. |
| Texture | Quasi-Hamming; glyph foundations | Texture as a visual channel, kept narrow because flat icons produce artifact risk. |

No single paper validates every implemented metric. The mapping is a reasoned operationalization: literature supports a human-relevant visual construct, and the code implements measurable proxies. Each proxy still requires visual and human validation.

## Evidence Used For The Current Representatives

The one-feature-per-family selection in Feature Groups applies the following evidence hierarchy:

1. Prefer a metric with direct human-performance or human-rating evidence.
2. If the literature validates a visual channel rather than an exact formula, choose the most interpretable continuous implementation and label that choice as project inference.
3. Avoid pixel measures that the source itself found unreliable, such as foreground area as a complexity estimate.
4. Preserve task-specific caveats; an effect on similarity strategy is not automatically an accuracy benefit.

Key decisions:

- Forsythe et al. page 6 supports `quadtree_structural_variability` with Spearman ρ = .65 against human-rated complexity.
- Fuchs et al. pages 5-8 support closure and fill as influential similarity-strategy factors, while warning that contour can reduce task accuracy in some conditions.
- Legg et al. page 5 reports human quasi-Hamming averages of 3.0 for orientation and 2.2 for texture; these support the constructs represented by `principal_axis_orientation_v2` and `local_texture_variation_v2`, not the exact formulas.
- Borgo et al. pages 7, 12, and 16 support symmetry as perceptual organization and performance-relevant glyph structure.
- Borgo et al. pages 7-10 describe color as a dominant pop-out channel. Mapping that construct to corrected-foreground `mean_saturation_v2` is a project inference chosen to avoid selecting one arbitrary hue bin.

See [Feature system](feature-system.md#current-one-feature-representatives) for the complete seven-feature table. These choices must be re-evaluated after human-study data exists; they are evidence-backed starting predictors, not confirmed causal determinants for this corpus.

## Claim Discipline

Use wording such as:

> The feature approximates a visible construct discussed in the literature.

Avoid wording such as:

> The feature measures human perception directly.

Particularly careful cases:

- `enclosure_score_v2` is an external-contour enclosure proxy, not a direct Gestalt-closure score.
- arrowheads and arcs are approximate image primitives.
- connected components and contours are pixel-level groupings, which may not match human grouping.
- texture entropy measures tonal variation, not every human notion of texture.
- abstractness, concreteness, familiarity, meaningfulness, metaphor, and culture require ratings, metadata, or study responses.

## Research Notes

The main human-authored syntheses are:

- `notes/human_to_computer_glyph_feature_mapping.md` — current conceptual boundary.
- `notes/literature_mapping_deep_pass_2026-07-08.md` — latest local-literature audit and safe claim.
- `notes/paper_feature_review.md` — paper-by-paper feature and distinguishability review.
- `notes/feature_visual_categorization_tables.md` — visual categorization mappings.
- `notes/feature_extraction_taxonomies.md` — feature taxonomy context.

Prefer the latest deep-pass and human-to-computer mapping over older proposal language.

## Extracted Text Workflow

```powershell
python code/extract_paper_text.py
```

This requires `pdfplumber`, which is not installed in every local Python environment. The current Windows `python` runtime in the verified workspace raises `ModuleNotFoundError: pdfplumber`; use the configured bundled dependency runtime or install the missing package before regeneration.

Extracted text is a search aid, not a substitute for the original PDF when quoting, checking tables, or establishing page-specific evidence.

## Adding Literature Evidence

1. Preserve the original PDF and provenance.
2. Extract page-marked text and update the manifest.
3. Record what construct the source supports and its experimental context.
4. Distinguish direct evidence from project inference.
5. Map only visible/computable factors into active computer families.
6. Put non-visual constructs into metadata or human-study design.
7. Update the active-family mapping only if the new evidence materially changes it.

## Citation Verification Checklist

- Verify the exact claim in the original PDF.
- Record the page number.
- Avoid using a secondary note as the cited source.
- Separate the paper's finding from the repository's implementation decision.
- Do not generalize task-specific contour or glyph results to all icon perception without qualification.
- Confirm that a metric name used in the code does not overstate the construct measured in the paper.
