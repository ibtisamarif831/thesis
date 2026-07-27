# T-002: Add representative feature and candidate browsing to Feature Groups

Status: In progress
Priority: High  
Depends on: T-001

Linear: PER-5

## Goal

Use Feature Groups to choose one interpretable feature from each of the seven active families and inspect candidate icons for that feature.

## Acceptance criteria

- One representative feature can be selected for each family.
- The view shows icon image, feature value, and the current 10-icon sample average; distance from that average remains open.
- Exactly 10 dataset-balanced candidates can be reviewed for each selected feature and refreshed independently.
- Low, medium/mean-nearest, and high examples remain available.
- Candidate selection uses the full feature sample where possible, not only the 129-row dashboard sample.

## Current progress

The schema-v2 representative implementation is complete but human validation remains gated:

- Complexity: `canny_edge_density` (replaced grayscale quadtree variability after visual-audit failures)
- Shape/silhouette: `enclosure_score_v2`
- Stroke/structure: `principal_axis_orientation_v2` plus confidence
- Density/fill: `solid_fill_ratio_v2`
- Balance/layout: `horizontal_symmetry_v2`
- Color/contrast: `mean_saturation_v2`
- Texture: `local_texture_variation_v2`

Feature Groups displays the selected feature, rationale, evidence, citation, and an independent 10-icon dataset-balanced sample per family. Scalar values use arithmetic means and numeric ordering. Orientation uses an axial mean, angular ordering, and undefined-confidence handling. Candidate draws exclude the 621 uncertain-mask rows and cover the remaining 28,128 rows; **Randomize icons** and cohort persistence remain. The pilot cannot be released until the rebuilt two-rater benchmark passes; distance from average and the low/medium/high candidate workflow remain open.
