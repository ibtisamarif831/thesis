# Literature Mapping Deep Pass - Current State

This note summarizes the local-literature pass after the visual-family cleanup. It uses only the papers and extracted text stored in this project.

## Verdict

The thesis direction is now:

> Derive visual feature families from glyph/icon perception literature, compute those families from icon images, collect human identification/perception scores for the same stimuli, and compare where human perception agrees or disagrees with computer-based visual analysis.

Safe claim:

> Computer features can model visible structure, visual-channel differences, and set-level distinguishability. They cannot directly model semantic meaning, familiarity, history, metaphor, cultural convention, or learned meaning without metadata or human-response data.

## Local Literature Basis

| Source | What it supports | Mapping consequence |
|---|---|---|
| `papers/Forsythe-Measuring_cion_complexity_automated.pdf` | Automated icon complexity from foreground area, component/object count, holes, edge information, and structural variability. | Strong support for Complexity and parts of Density/fill. |
| `papers/Garcia-Development_validation_icons_abstractness.pdf` | Component taxonomy: closed/open figures, letters/special characters, horizontal/vertical/diagonal lines, arrowheads, arcs. Also shows context and subjective grouping limits. | Supports visible primitives, but not pure image-based abstractness/concreteness. |
| `papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf` | Contour and closure affect similarity strategy, but effects are task-specific. | Supports contour, closure, shape, and filled/outline proxies with careful wording. |
| `papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf` | Pairwise distinguishability through visual channels: hue, shape, components, connection lines, luminance, size, texture, orientation. | Supports family-weighted similarity and future quasi-Hamming explanations. |
| `papers/Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf` | Visual channels, Gestalt principles, area, symmetry, simplicity, channel selection, and separation from semantic concerns. | Supports visual-family grouping and the boundary against semantic overclaiming. |
| `papers/A_Systematic_Review_of_Experimental_Studies_on_Data_Glyphs.pdf` | Glyph performance depends on task, display, number of glyphs, encodings, and human outcome measures. | Requires human-study validation of computer scores. |
| `papers/Taxonomy-Based_Glyph_Designwith_a_Case_Study_on_Visualizing_Workflows_of_Biological_Experiments.pdf` | Taxonomy/category mapping to visual channels with domain conventions and metaphors. | Useful for study framing and metadata, not proof that semantics are computable from pixels. |

## Active App Families

| Active family | Include | Status |
|---|---|---|
| Complexity | Edge density, quadtree variability, components, contours, holes, perimeter/area, corners | Keep. Strongest paper-backed family. |
| Shape/silhouette | Aspect ratio, solidity, closure proxy, circularity, rectangularity, curvature | Keep. Hu moments removed from active mapping. |
| Stroke/structure | Line orientation, circular principal-axis orientation, skeleton endpoints/junctions, arrowhead proxy, arc proxy | Keep. Text/letter heuristic removed from active mapping. |
| Density/fill | Foreground area, bbox occupancy, filled/outline proxy, stroke width | Keep. |
| Balance/layout | Symmetry, centroid, bbox center/size, 4x4 grid occupancy | Keep. |
| Color/contrast | Monochrome flag, color count, saturation, colorfulness, contrast, hue histogram, dominant Lab colors | Keep with circular hue handling and careful `is_monochrome` wording. |
| Texture | Texture entropy | Keep narrowly. LBP bins removed from active mapping. |

## Removed From Active Families

| Removed raw channel | Reason |
|---|---|
| Hu moments | Advanced machine descriptor; not human-readable enough for active perceptual-family claims. |
| LBP histogram bins | Often capture antialiasing/rendering artifacts in flat vector icons. |
| `text_or_letter_presence` | Current heuristic is too indirect and can blur visual structure with text identity. |
| `crush_test_stability` | Robustness/degradation processing measure, not a direct visible identification feature. |

These columns can remain in raw exports for traceability, but they should not drive the active dashboard, similarity ranking, feature review, or thesis feature-family claims.

## Non-Visual Boundary

Keep outside the active image-feature family list:

| Non-visual or mixed factor | Use as |
|---|---|
| Exact text identity | OCR/metadata annotation or human-study variable |
| Semantic identity | Label/category metadata |
| Abstractness/concreteness | Metadata-supported or human-rated outcome |
| Meaningfulness/familiarity/semantic distance/metaphor/history | Human-study variables or domain metadata |
| Learnability/context sensitivity | Experiment design and human outcome variables |

## Current Improvements Already Applied

- Active families reduced to 81 mapped visual features.
- Weak/non-interpretable raw channels excluded from active dashboard, feature review, feature explorer, clustering, and similarity ranking.
- Similarity now uses active visual families rather than extractor groups.
- Principal-axis orientation is encoded circularly over 180 degrees.
- Hue bins are treated with circular wraparound.
- `is_monochrome` is documented as a monochrome flag, not a color-amount feature.

## Remaining Work

1. Design the human study and decide which human scores to collect.
2. Select a controlled stimulus subset from the current icon datasets.
3. Build a participant-response logging workflow.
4. Compare human scores with active feature-family scores.
5. Add explainable pairwise/channel-level outputs, such as quasi-Hamming family differences.
6. Visually validate high/low examples for each active family.

## Thesis Claim To Use

> This system maps human glyph-identification factors only where they have computable visual correlates: complexity, shape/silhouette, stroke/structure, density/fill, balance/layout, color/contrast, texture, and set-level distinguishability. Semantic interpretation, familiarity, historical meaning, metaphor, and learned convention are intentionally excluded from computer-vision feature families and treated as metadata or human-study outcomes.
