# Human-To-Computer Glyph Feature Mapping

This note is the current thesis mapping boundary. It connects human icon/glyph identification factors from the local literature to computer-measurable visual feature families in the project.

## Thesis Position

The thesis does not claim that computer vision understands icon meaning. It compares two sides of the same glyph/icon stimuli:

1. Computer-derived visual feature-family scores.
2. Human identification/perception scores collected in a qualitative or mixed-methods study.

The analysis asks where these two sides agree, where they mismatch, and which visual factors explain identification, similarity, distinguishability, or confusability.

## What Can Be Mapped From Images

Active computer-vision families must be visible in the glyph image and computable from pixels.

| Active family | Human factor approximated | Current feature examples |
|---|---|---|
| Complexity | Visual busyness, detail load, number of parts | edge density, quadtree variability, connected components, contours, holes, perimeter/area, corners |
| Shape/silhouette | Overall form, closure, roundness, rectangularity, curvature | aspect ratio, solidity, closure proxy, circularity, rectangularity, curvature bins |
| Stroke/structure | Directional strokes, internal graph structure, arcs/arrows | line-orientation histogram, circular principal-axis orientation, arrowhead count, arc count, skeleton endpoints/junctions |
| Density/fill | Sparse vs filled, thin vs heavy marks | foreground area, bounding-box occupancy, filled/outline proxy, stroke width |
| Balance/layout | Centering, symmetry, top-heavy/side-heavy layout | centroid offset, horizontal/vertical symmetry, bbox center/size, 4x4 grid occupancy |
| Color/contrast | Color availability, hue channel, salience, legibility | monochrome flag, color count, saturation, colorfulness, foreground/background contrast, hue histogram, dominant Lab colors |
| Texture | Internal tonal variation | texture entropy |

These families are used by the dashboard, feature review, feature explorer, clustering, and similarity outputs.

## Excluded Raw Channels

The extractor still stores 100 raw numeric image-feature columns for traceability, but the active visual-family set uses 81 columns.

Excluded from active mapping:

- `hu_moment_1` through `hu_moment_7`: useful for machine shape matching, but not cleanly interpretable as human perception features.
- `lbp_histogram_00` through `lbp_histogram_09`: often captures antialiasing/rendering artifacts in flat vector icons.
- `text_or_letter_presence`: current heuristic is too indirect for reliable glyph-identification claims.
- `crush_test_stability`: processing robustness, not a direct visible identification feature.

## Non-Visual Or Mixed Factors

These may matter for human identification but must not be presented as computer-vision feature families:

| Factor | Use in thesis |
|---|---|
| Exact text identity | Metadata/OCR annotation or study variable |
| Semantic object/concept identity | Label/category metadata or study prompt |
| Abstractness/concreteness | Human rating or metadata-supported outcome |
| Meaningfulness | Human identification/matching outcome |
| Familiarity | Human-study question or dataset/source context |
| Metaphor, cultural convention, history | Qualitative/human-study interpretation |
| Learnability/context sensitivity | Experimental design variable |

## Pairwise Comparison

Pairwise similarity/confusability should be computed from active visual families, not from semantic labels. The current similarity pipeline:

- uses robust scaling;
- treats principal-axis orientation as circular over 180 degrees;
- treats hue as circular;
- excludes weak/non-interpretable raw channels;
- weights by active visual family.

This supports nearest-neighbor and closest-pair outputs as computer-side predictors for later human-study comparison.

## Clean Thesis Claim

> Human glyph identification relies on visible structure, perceptual grouping, visual-channel differences, set-level distinguishability, and non-visual knowledge. The current computer-vision pipeline models only the visible and computable part: complexity, shape/silhouette, stroke/structure, density/fill, balance/layout, color/contrast, and texture. Semantic interpretation, familiarity, metaphor, history, and learnability require metadata or human-response data and are evaluated separately.
