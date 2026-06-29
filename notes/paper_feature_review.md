# Paper Review For Feature And Distinguishability Pipeline

This note summarizes how the extracted papers support the current thesis direction:
using computational icon features to describe icons, estimate distinguishability, and compare those estimates with human perception in a quantitative study.

Full extracted text is stored in `papers/extracted_text/`.

## Most Directly Relevant Papers

### Forsythe et al. - Measuring Icon Complexity

Use this as the strongest source for automated visual-complexity features. The paper links image-processing measures to human perceived complexity judgments.

Feature support:

- foreground amount
- number of objects/components
- holes
- edge information
- structural variability / homogeneity

Pipeline implication:

- The current `foreground_area_ratio`, `canny_edge_density`, `connected_components`, and quadtree features are well aligned with this paper.
- Missing but useful additions are `holes_count`, `perimeter`, and stronger object/contour measures.

### Garcia et al. - Development And Validation Of Icons Varying In Abstractness

Use this for the claim that icon structure can be quantified and compared with subjective judgments of abstractness/concreteness.

Feature support:

- component-based complexity
- closed figures
- open figures
- letters and special characters
- horizontal, vertical, and diagonal lines
- arrowheads
- arcs

Pipeline implication:

- The current component count is only a rough proxy.
- A stronger implementation would add line orientation counts, closed/open figure counts, arrows, arcs, and text/character detection.

### Fuchs et al. - Influence Of Contour On Similarity Perception

Use this to justify contour and closed-shape features when studying human similarity judgments.

Feature support:

- contour presence changes what viewers treat as similar
- closed contours can push viewers toward shape similarity
- open/no-contour designs can change similarity strategy

Pipeline implication:

- Add contour count, contour closure, filled-vs-outline proxy, and shape-closure measures.
- These are especially relevant for distinguishability and human-pair similarity tasks.

### Legg et al. - Fail-Safe Glyph Design With Quasi-Hamming Distances

Use this for distinguishability framing. The paper treats glyph design as a problem of avoiding perceptual errors through separable visual channels and sufficient distance between encoded forms.

Pipeline implication:

- Current pairwise feature distance is compatible with this idea.
- A future quasi-Hamming feature representation could discretize visual features into bins and count how many visual channels differ between two icons.

## Broader Framing Papers

### Borgo et al. - Glyph-Based Visualization

Use this as background for glyph design principles, visual channels, Gestalt grouping, complexity, symmetry, and perceptual considerations.

Pipeline implication:

- Supports adding symmetry, closure, figure-ground, area, and visual-channel features.
- Useful for explaining why raw feature distance should be interpreted as a perceptual proxy, not a complete model of perception.

### Fuchs et al. - Systematic Review Of Experimental Studies On Data Glyphs

Use this for study-design framing. It supports the need to connect glyph/icon design choices to quantitative user studies.

Pipeline implication:

- Supports using human judgments, accuracy, response time, or similarity choices as dependent variables.
- Helps justify evaluating computational predictions against participant data.

### Maguire et al. - Taxonomy-Based Glyph Design

Use this for taxonomy and semantic design framing.

Pipeline implication:

- Useful for the metadata side of the pipeline: source set, category, semantic labels, and icon-name tokens.
- Less direct support for low-level visual feature extraction.

## Recommended Feature Additions

High priority:

- `holes_count`
- `contour_count`
- `closed_contour_ratio`
- `perimeter_area_ratio`
- `bounding_box_occupancy`
- `horizontal_symmetry`
- `vertical_symmetry`
- `filled_vs_outline_proxy`

Medium priority:

- line orientation features: horizontal, vertical, diagonal
- arrowhead count
- arc/curve proxy
- color count and color entropy
- text/letter presence
- compression ratio

## Quantitative Study Connection

Good dependent variables:

- pairwise distinguishability rating
- pairwise similarity rating
- recognition accuracy
- response time
- confidence
- perceived complexity

Good computational predictors:

- standardized feature distance between two icons
- difference in edge density
- difference in foreground area
- difference in component count
- difference in contour/closure features
- difference in symmetry
- difference in metadata category or semantic label

The key thesis claim should be modest:

> Computational visual features can describe structural differences between icons and may predict aspects of human-perceived distinguishability, but they do not fully replace human perceptual evaluation.
