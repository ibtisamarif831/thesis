# Feature Evidence and Literature Basis

## Purpose and Claim Boundary

This document records the literature basis for the seven representative features currently defined
in `code/thesis_pipeline/features/registry.py`. Page numbers below refer to the local PDF page numbers
in `papers/`.

The papers generally support the **visual construct** represented by a feature, not the exact
computational formula used in this thesis. The safe description is therefore:

> **Literature-informed, thesis-operationalized features.**

Do not describe all seven formulas as proven or directly derived from the papers. Canny edge density
has the closest measure-level precedent. The remaining six are thesis-defined computational
operationalizations of literature-supported constructs.

## Current Representative Features

| Feature family | Current representative | Evidence status |
|---|---|---|
| Complexity | `canny_edge_density` | Closest measure-level evidence |
| Shape/silhouette | `enclosure_score_v2` | Construct-level evidence |
| Stroke/structure | `principal_axis_orientation_v2` | Construct-level evidence |
| Density/fill | `solid_fill_ratio_v2` | Construct-level evidence |
| Balance/layout | `horizontal_symmetry_v2` | Construct-level evidence |
| Color/contrast | `mean_saturation_v2` | Construct-level evidence |
| Texture | `local_texture_variation_v2` | Construct-level evidence |

## 1. Complexity — Canny Edge Density

**Feature:** `canny_edge_density`

**Primary paper:** [Forsythe, Sheehy, and Sawey — automated icon complexity](papers/Forsythe-Measuring_cion_complexity_automated.pdf)

**Basis:** Edge/perimeter information as a computational approximation of perceived icon
complexity.

**Exact locations:**

- **PDF page 5:** describes the Canny perimeter-detection calculation, including strong and weak
  thresholds and suppression of noise; Table 1 reports descriptive values for the Canny measure.
- **PDF page 6, Table 2:** reports a Spearman correlation of **rho = .49** between Canny and
  McDougall human complexity ratings, and **rho = .60** between Canny and the Garcia metric; the
  reported correlations are significant at **p < .0008**.
- **PDF page 6, Results:** states that image-processing measures can approximate more
  time-consuming judgments of icon complexity.

**Claim boundary:** This is the closest of the seven representatives to measure-level evidence.
However, the paper's Canny/perimeter score is not necessarily identical to the repository's
normalized edge-density formula.

## 2. Shape/Silhouette — Enclosure Score

**Feature:** `enclosure_score_v2`

**Papers:**

- [Garcia et al. — icons varying in abstractness](papers/Garcia-Development_validation_icons_abstractness.pdf)
- [Fuchs et al. — contour and similarity perception of star glyphs](papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf)

**Basis:** Closed figures, contour closure, containment, and the influence of contours on perceived
shape similarity.

**Exact locations:**

- **Garcia PDF pages 3–4, “Definition of metric”:** explicitly counts closed figures and open
  figures as icon components.
- **Garcia PDF page 4:** notes that people may group icon components differently, limiting a simple
  component-count metric.
- **Fuchs PDF page 2, Figure 1:** distinguishes data lines, connected contours that form a closed
  shape, contour-only glyphs, and fill styles.
- **Fuchs PDF page 3, Section 3.2, “Perception of Two-Dimensional Shapes”:** discusses contour
  closure through the Gestalt principle of closure.
- **Fuchs PDF page 5, Sections 4.4–4.5:** reports a significant effect of contour variation and
  shows that contours shifted participants toward geometric-shape similarity judgments.
- **Fuchs PDF pages 6–8, Experiment 2:** further examines contour containment and shape-similarity
  choices.

**Claim boundary:** The papers support enclosure and closure as perceptually relevant constructs.
They do not provide the thesis's enclosure-area formula.

## 3. Stroke/Structure — Principal-Axis Orientation

**Feature:** `principal_axis_orientation_v2`

**Papers:**

- [Garcia et al. — icons varying in abstractness](papers/Garcia-Development_validation_icons_abstractness.pdf)
- [Legg et al. — fail-safe glyph design using quasi-Hamming distances](papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf)

**Basis:** Directional primitives and orientation as a visual channel through which glyphs can be
distinguished.

**Exact locations:**

- **Garcia PDF pages 3–4, “Definition of metric”:** includes horizontal, vertical, and diagonal
  lines, arrowheads, and arcs in its icon-element taxonomy.
- **Legg PDF page 4:** identifies orientation as one of eight primitive visual-channel groups.
- **Legg PDF page 5, Table 1:** reports an average human quasi-Hamming distance of **3.0** for
  orientation and a computer value of **1.6**.
- **Legg PDF page 6:** discusses shape, components, and orientation as comparatively separable and
  notes human–computer disagreement for orientation.

**Claim boundary:** The papers support orientation as a visual construct. They do not specify the
thesis's principal-component axis-angle formula or its confidence threshold.

## 4. Density/Fill — Solid Fill Ratio

**Feature:** `solid_fill_ratio_v2`

**Primary paper:** [Fuchs et al. — contour and similarity perception of star glyphs](papers/The_Influence_of_Contour_on_Similarity_Perception_of_Star_Glyphs.pdf)

**Secondary caution:** [Forsythe, Sheehy, and Sawey — automated icon complexity](papers/Forsythe-Measuring_cion_complexity_automated.pdf)

**Basis:** Filled versus outlined glyph appearance and the role of fill in foreground/background
contrast and perceived shape.

**Exact locations:**

- **Fuchs PDF page 2, Figure 1:** shows filled, outline, and contour variants.
- **Fuchs PDF page 6, Section 5.1, “Fill vs. No-Fill”:** proposes that fill reinforces the
  perception of closed shapes through foreground/background contrast.
- **Fuchs PDF page 7, Section 5.3:** reports significant effects of fill type on rotated/scaled
  similarity choices.
- **Fuchs PDF page 8, Section 5.4:** reports no general improvement in data-similarity choices;
  fill instead affected which shape-related similarities participants selected.
- **Forsythe PDF page 4:** defines foreground pixel amount as a possible computational measure.
- **Forsythe PDF page 7, Discussion:** cautions that foreground amount is too crude to estimate
  perceived complexity reliably.

**Claim boundary:** The literature supports fill as a visual factor, with task-specific effects. The
erosion-survival formula used by `solid_fill_ratio_v2` is a thesis operationalization, not a formula
from these papers.

## 5. Balance/Layout — Horizontal Symmetry

**Feature:** `horizontal_symmetry_v2`

**Primary paper:** [Borgo et al. — glyph-based visualization foundations and guidelines](papers/Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf)

**Basis:** Symmetry as a Gestalt organization principle and as a design property that can facilitate
pattern perception.

**Exact locations:**

- **PDF page 7, Section 3.1.1 and Figure 6(e):** presents symmetry as a Gestalt principle of
  perceptual organization.
- **PDF page 12, Section 3.4, “Complexity and Symmetry-driven”:** discusses dimension orderings
  that produce simpler or more symmetric star glyphs and reports improved performance.
- **PDF page 15, design guideline DG8, “Simplicity and Symmetry”:** states that simple and symmetric
  forms facilitate pattern perception and specifically mentions horizontally symmetric glyphs.

**Claim boundary:** The paper supports the perceptual relevance of symmetry. The implementation's
left–right Dice overlap and two-pixel tolerance are thesis-defined choices, not formulas from the
paper.

## 6. Color/Contrast — Mean Saturation

**Feature:** `mean_saturation_v2`

**Papers:**

- [Borgo et al. — glyph-based visualization foundations and guidelines](papers/Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf)
- [Legg et al. — fail-safe glyph design using quasi-Hamming distances](papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf)

**Basis:** Color, hue, and saturation as strong visual channels for pop-out and glyph
distinguishability.

**Exact locations:**

- **Borgo PDF page 8, Table 1:** lists color, hue, and saturation as optical visual channels.
- **Borgo PDF page 8, text below Table 1:** describes color as particularly strong for pop-out
  compared with size, shape, and orientation.
- **Borgo PDF page 9, “Guideline on Pop-out Effects”:** repeats the visual-channel ordering and the
  strength of color.
- **Borgo PDF page 15, Section 3.5.2, “Other Visual Properties / Glyph Appearance”:** includes
  color/hue and color saturation in the perceptual ordering.
- **Legg PDF page 4:** identifies color as a primitive visual channel.
- **Legg PDF page 5, Table 1:** reports an average human quasi-Hamming distance of **2.2** for color.

**Claim boundary:** These sources support color and saturation as visual constructs. Mean HSV
saturation over the corrected foreground is a thesis-defined implementation.

## 7. Texture — Local Texture Variation

**Feature:** `local_texture_variation_v2`

**Papers:**

- [Legg et al. — fail-safe glyph design using quasi-Hamming distances](papers/Glyph_Visualization_A_Fail-Safe_Design_Scheme_Based_on_Quasi-Hamming_Distances.pdf)
- [Borgo et al. — glyph-based visualization foundations and guidelines](papers/Glyph-based_Visualization_Foundations_Design_Guidelines_Techniques_Applications.pdf)

**Basis:** Texture as a visual channel, including density and regularity of texture patterns.

**Exact locations:**

- **Legg PDF page 4:** identifies texture as one of eight primitive visual-channel groups.
- **Legg PDF page 5, Table 1:** reports an average human quasi-Hamming distance of **2.2** for
  texture.
- **Legg PDF page 6:** shows that texture was not among the channels reaching a human
  quasi-Hamming distance of 3 or more, so this evidence is supportive but not among the paper's
  strongest separation results.
- **Borgo PDF page 8, Table 1:** lists texture as an optical and partly geometric visual channel.
- **Borgo PDF page 15, Section 3.5.2:** discusses perceptual texture patterns through dimensions
  including density, regularity, and height.

**Claim boundary:** The papers support texture as a visible construct. They do not define the
normalized 7-by-7 grayscale-variation formula used by this thesis.

## Safe Summary for the Presentation or Thesis

> The literature provides empirical or theoretical support for the seven visual constructs. Canny
> edge density has the closest measure-level precedent; the other six measurements are
> thesis-defined computational operationalizations of those constructs.

In short, the features are **literature-informed**, but their formulas are not all
**literature-derived**.
