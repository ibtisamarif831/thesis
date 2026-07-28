# Feature-Level Literature Evidence Pass — 2026-07-28

## Purpose

This pass audits all 81 active schema-v2 features against the seven-paper local literature corpus. It
adds page-level evidence to the typed feature registry without claiming that broad visual-channel
research validates every extraction formula.

The registry records three evidence scopes:

- `direct`: the paper evaluates a closely matching automated measure against a human outcome;
- `construct`: the paper supports the visual construct or primitive, while the exact repository
  formula remains a project operationalization;
- `cautionary`: the paper studies the measure or construct but reports limitations that materially
  constrain its interpretation.

Non-active auxiliary, deprecated, and excluded columns retain `none`: the pass concerns the current
81-feature analytical mapping.

## Outcome

| Evidence scope | Active features | Interpretation |
|---|---:|---|
| Direct | 1 | `canny_edge_density` has close measure-level evidence against subjective complexity ratings. |
| Construct | 77 | The literature supports the visible channel or primitive, not the exact implementation. |
| Cautionary | 3 | `foreground_area_ratio`, `connected_components`, and `holes_count` have explicit source limitations. |

Every active `FeatureSpec` now carries `evidence_scope`, `evidence`, and `citation`. Registry
validation requires exactly one non-empty evidence entry and citation for every active feature. The
dashboard metadata adapter serializes these fields for each feature.

## Page-Level Mapping

| Feature set | Evidence source and safe conclusion |
|---|---|
| `canny_edge_density` | Forsythe et al., pp. 5-6: Canny edge density correlated at Spearman 0.49 with McDougall subjective complexity ratings. This is the only close measure-level result in the local corpus. |
| Quadtree features | Forsythe et al., pp. 5-7: quadtree subdivision distinguishes homogeneous from highly structured icons and their quadtree measure correlated at 0.65. Exact v2 variability and leaf summaries remain project formulas. |
| `perimeter_area_ratio` | Forsythe et al., pp. 5-7: perimeter correlated at 0.64 with subjective complexity. Area normalization was not tested as the current exact ratio. |
| `connected_components`, `holes_count` | Forsythe et al., pp. 4-7, and Garcia et al., pp. 11 and 20: pixel objects and holes can diverge from human grouping and can be distorted by tiny raster regions. |
| `foreground_area_ratio` | Forsythe et al., pp. 4 and 7: foreground area was considered too crude for perceived complexity. It remains an occupancy feature, not a validated complexity predictor. |
| Contours and enclosure | Garcia et al., pp. 3-4 and 20, and Fuchs et al., pp. 2-3 and 6-8: open/closed figures are icon primitives and contour treatment affects similarity strategy. Raster contour counts and `enclosure_score_v2` are proxies. |
| Line orientations, arrowheads, arcs | Garcia et al., pp. 3-4, 11 and 20: these primitives were included in a validated abstractness metric, with viewer grouping as a caveat. Legg et al., pp. 4-6, additionally support orientation as a separable channel. |
| Global orientation and skeleton graph | Legg et al., pp. 4-6, and Borgo et al., pp. 7-10: orientation, components, connection lines, nodes, and terminators are distinguishable or recognized channels. PCA and skeleton counts are project operationalizations. |
| Shape, aspect ratio, curvature, compactness | Borgo et al., pp. 2 and 7-10, Fuchs et al., pp. 2-3, and Legg et al., pp. 4-6: shape, aspect ratio, curvature, and contour are human-relevant channels. The exact circularity, rectangularity, solidity, and histogram formulas were not tested. |
| Fill, density, and stroke width | Fuchs et al., pp. 6-8, and Borgo et al., pp. 7-10: fill type can alter similarity strategy, while area, density, width, and line style are visual channels. No general fill accuracy benefit or exact stroke-width validation was found. |
| Symmetry | Borgo et al., pp. 7, 12 and 16: symmetry is a Gestalt organization principle and symmetry-optimized star-glyph orderings improved user performance. Pixel Dice overlap is a project proxy. |
| Center, bounding box, and grid layout | Borgo et al., pp. 7-10: spatial location, distance, size, width, height, area, and density are recognized channels or grouping cues. The 4x4 subdivision itself was not evaluated. |
| Color, hue, saturation, contrast, dominant Lab | Borgo et al., pp. 7-10, and Legg et al., pp. 4-6: color, hue, saturation, intensity, brightness, and luminance are visual channels; Legg used Hunter Lab for computer codewords. The repository's summaries, binning, and dominant-color selection remain project choices. |
| `local_texture_variation_v2` | Legg et al., pp. 4-6, and Borgo et al., p. 8: texture is a human-rated visual channel. The local-interior formula was not evaluated and still requires human validation. |

## Primary Local Sources Checked

- `papers/extracted_text/forsythe-measuring-cion-complexity-automated.txt`
- `papers/extracted_text/garcia-development-validation-icons-abstractness.txt`
- `papers/extracted_text/the-influence-of-contour-on-similarity-perception-of-star-glyphs.txt`
- `papers/extracted_text/glyph-visualization-a-fail-safe-design-scheme-based-on-quasi-hamming-distances.txt`
- `papers/extracted_text/glyph-based-visualization-foundations-design-guidelines-techniques-applications.txt`
- `papers/extracted_text/a-systematic-review-of-experimental-studies-on-data-glyphs.txt`
- `papers/extracted_text/taxonomy-based-glyph-designwith-a-case-study-on-visualizing-workflows-of-biological-experiments.txt`

The extracted text was used for page routing. Claims should still be checked against the original
PDF before verbatim quotation.

## Boundary

The result establishes literature provenance for the active feature constructs. It does not establish
that all 81 metrics predict identification, similarity, or confusability in this icon corpus. That
requires the planned human study and feature-outcome analysis.
