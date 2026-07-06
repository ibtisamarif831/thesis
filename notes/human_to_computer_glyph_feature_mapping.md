# Human-To-Computer Glyph Feature Mapping

This note maps the visual factors humans use when identifying, distinguishing, and classifying glyphs/icons to measurable computer-vision feature sets. It is based on the papers in `papers/` and the current extracted feature pipeline in `code/extract_icon_features.py`.

The key distinction is that some human factors are directly measurable from pixels, some are good computational proxies, and some are not visual features at all. Concreteness, familiarity, meaning, and metaphor usually require metadata, labels, or human responses in addition to image features.

## Paper Basis

| Paper | What it contributes to the mapping |
|---|---|
| Forsythe et al., `Measuring Icon Complexity` | Strongest support for automated visual-complexity features: foreground amount, object count, holes, perimeter/edges, Canny edges, quadtree structural variability. It also warns that object and hole counts can diverge from human grouping. |
| Garcia et al., `Development and validation of icons varying in abstractness` | Supports a component taxonomy for abstractness/concreteness: closed figures, open figures, letters, special characters, horizontal/vertical/diagonal lines, arrowheads, arcs. It also shows context and subjective grouping effects. |
| Fuchs et al., `Influence of Contour on Similarity Perception of Star Glyphs` | Supports contour, closure, filled/outline state, data-line vs shape perception, and the task-specific difference between data similarity and shape similarity. |
| Legg et al., `Fail-Safe Design Scheme Based on Quasi-Hamming Distances` | Provides the pairwise distinguishability framework: compare glyphs by separable visual channels and estimate perceptual distance. Human-rated channels include hue, shape, components, connection lines, luminance, size, texture, and orientation. |
| Borgo et al., `Glyph-Based Visualization` | Provides broad design principles: visual channels, Gestalt grouping, proximity, similarity, continuity, closure, figure-ground, symmetry, semantic relevance, learnability, searchability, and perceptual channel choice. |
| Maguire et al., `Taxonomy-Based Glyph Design` | Supports mapping semantic/category taxonomies to visual channels ordered by discriminative capacity: color, size, shape, orientation, texture, and planar position. |
| Fuchs et al., `Systematic Review of Experimental Studies on Data Glyphs` | Supports the study-design side: task type, dimensionality, number of glyphs, layout, and encoding choice moderate human performance. |

## Current Computer Feature Sets

The current pipeline already extracts these feature groups:

| Feature set | Columns |
|---|---|
| Foreground amount | `foreground_area_ratio` |
| Edge/detail load | `canny_edge_density` |
| Components | `connected_components` |
| Quadtree structure | `quadtree_leaf_count`, `quadtree_structural_variability`, `quadtree_mean_leaf_size` |
| Geometry and contour | `bounding_box_occupancy`, `bounding_box_aspect_ratio`, `solidity`, `centroid_distance_from_center`, `horizontal_symmetry`, `vertical_symmetry`, `perimeter_area_ratio`, `filled_vs_outline_proxy`, `contour_count`, `holes_count`, `closed_contour_ratio` |
| Line orientation | `line_orientation_0`, `line_orientation_45`, `line_orientation_90`, `line_orientation_135` |
| Color | `is_monochrome`, `color_count`, `mean_saturation`, `colorfulness`, `foreground_background_contrast` |
| Spatial layout | `grid_foreground_0_0` through `grid_foreground_3_3` |

## One-To-One Mapping

| Human factor used for glyph identification/classification | Human interpretation | Computer feature set | Current status | Confidence |
|---|---|---|---|---|
| Visual complexity/detail | How intricate or visually busy the glyph looks | `canny_edge_density`, `perimeter_area_ratio`, `quadtree_structural_variability`, `quadtree_leaf_count`, `foreground_area_ratio`, `connected_components`, `holes_count`, `contour_count` | Implemented | High |
| Structural variability/homogeneity | Whether the glyph has many local changes or a simple homogeneous form | `quadtree_structural_variability`, `quadtree_leaf_count`, 4x4 grid foreground distribution | Implemented | High |
| Foreground amount/density | How much visible material is present | `foreground_area_ratio`, `bounding_box_occupancy`, `filled_vs_outline_proxy` | Implemented | High |
| Sparse vs dense | Whether the glyph is light/open or visually packed | `foreground_area_ratio`, `bounding_box_occupancy`, `perimeter_area_ratio`, `canny_edge_density` | Implemented | High |
| Single object vs multi-part | Whether the glyph is one coherent object or several parts | `connected_components`, `contour_count`; future: perceptual grouping model | Implemented as proxy | Medium |
| Human perceptual grouping | Whether separate parts are seen as one unit | `connected_components`, distance between components, proximity-based grouping, grid distribution; future: Gestalt grouping features | Partial | Medium |
| Holes/enclosed spaces | Whether there are enclosed counters, loops, or internal spaces | `holes_count`, `closed_contour_ratio` | Implemented | High |
| Open vs closed shape | Whether the shape is open line art or closed form | `closed_contour_ratio`, `holes_count`, `contour_count`, `perimeter_area_ratio` | Implemented | High |
| Contour presence | Whether a boundary/outline dominates perception | `contour_count`, `perimeter_area_ratio`, `closed_contour_ratio`, `filled_vs_outline_proxy` | Implemented | High |
| Filled vs outline | Whether the glyph reads as a solid silhouette or line drawing | `filled_vs_outline_proxy`, `perimeter_area_ratio`, `foreground_area_ratio`, `canny_edge_density` | Implemented as proxy | Medium-high |
| Overall shape/geometric form | Basic silhouette category such as compact, elongated, fragmented, angular | `bounding_box_aspect_ratio`, `solidity`, `bounding_box_occupancy`, `perimeter_area_ratio`, `closed_contour_ratio`; future: Hu moments, Zernike moments, Fourier descriptors | Partial | Medium |
| Roundness vs rectangularity | Whether the glyph appears circular/rounded or box-like | Future: circularity `4*pi*area/perimeter^2`, contour curvature, corner count, ellipse fit error, rectangle fit error; current proxies: `solidity`, `perimeter_area_ratio`, `bounding_box_aspect_ratio` | Mostly missing | High need |
| Curvature/arcs | Presence of curved strokes | Future: contour curvature histogram, arc detector, Hough circle/ellipse features; current proxy: low corner count plus contour measures | Missing | High need |
| Corners/angularity | Presence of sharp angles, polygons, or corners | Future: corner count, dominant corner angles, polygon approximation vertex count | Missing | High need |
| Aspect ratio | Whether glyph is tall, wide, or square | `bounding_box_aspect_ratio` | Implemented | High |
| Compactness vs spread | Whether visual mass is tightly packed or dispersed | `solidity`, `bounding_box_occupancy`, `centroid_distance_from_center`, 4x4 grid foreground distribution | Implemented | High |
| Symmetry/balance | Left-right or top-bottom balance | `horizontal_symmetry`, `vertical_symmetry`, `centroid_distance_from_center` | Implemented | High |
| Centering | Whether the glyph mass is centered or off-center | `centroid_distance_from_center`, 4x4 grid foreground distribution | Implemented | High |
| Spatial layout/top-heavy/left-heavy | Where visual mass is distributed in the canvas | 4x4 grid foreground cells, `centroid_distance_from_center`, bounding box position if added | Implemented, except explicit bbox position | High |
| Horizontal/vertical/diagonal structure | Dominant stroke direction | `line_orientation_0`, `line_orientation_45`, `line_orientation_90`, `line_orientation_135` | Implemented | High |
| Directionality/orientation | Whether a glyph points or flows in a direction | line orientation histogram; future: principal axis orientation, arrowhead detection, endpoint direction vectors | Partial | Medium |
| Arrowheads | Presence of arrows as directional symbols | Future: contour tip detection, triangle/arrowhead classifier, Hough line intersection pattern | Missing | High need |
| Connection lines | Lines connecting subcomponents or nodes | line orientation histogram, `connected_components`, `contour_count`; future: skeleton graph endpoints/junctions | Partial | Medium |
| Stroke thickness | Whether strokes are thin or thick | Future: skeletonization plus distance transform stroke width; current proxy: `foreground_area_ratio` and `perimeter_area_ratio` | Missing | Medium-high |
| Size/scale | Whether one glyph is visually larger than another | In normalized icons: `foreground_area_ratio`, active bounding box size if added. If original scale matters, store pre-normalization size and rendered glyph size. | Partial | Medium |
| Color presence | Whether color is a visual channel | `is_monochrome`, `color_count`, `mean_saturation`, `colorfulness` | Implemented | High |
| Hue/color category | Red vs blue vs green, etc. | Future: hue histogram, dominant Lab/HSV colors, pairwise Delta E color distance; current: `color_count`, `mean_saturation`, `colorfulness` | Partial | High need for colored glyphs |
| Luminance/brightness | Light vs dark visual channel | `foreground_background_contrast`; future: foreground luminance mean/std | Partial | Medium-high |
| Contrast/legibility | Ease of separating foreground from background | `foreground_background_contrast`, `canny_edge_density`, alpha/foreground threshold quality | Implemented as proxy | High |
| Texture/pattern | Repeated marks, hatching, dotting, internal texture | Future: local binary patterns, Gabor features, entropy, repeated small-component count; current proxy: `canny_edge_density`, `quadtree_structural_variability` | Mostly missing | Medium-high |
| Figure-ground separation | Whether foreground and background are easy to parse | `foreground_background_contrast`, `foreground_area_ratio`, `bounding_box_occupancy`, `filled_vs_outline_proxy` | Implemented as proxy | Medium-high |
| Salience/popout | What visually stands out quickly | Feature z-scores within a set: color distance, size/area distance, shape distance, edge distance, contrast | Requires pairwise/set-level computation | Medium |
| Distinctiveness | Whether one glyph is visually different from others in the set | Pairwise standardized feature distance, nearest-neighbor distance, cluster isolation, quasi-Hamming channel count | Mostly implemented in analysis outputs, should formalize | High |
| Confusability | Whether two glyphs are likely to be mixed up | Low pairwise distance in shape/color/complexity/layout channels; nearest-neighbor rank | Mostly implemented in similarity analysis | High |
| Pairwise distinguishability | How easy it is to tell two glyphs apart | Quasi-Hamming feature channels: bin each visual feature family and count differing channels; also Euclidean/cosine feature distance | Needs formal channel binning | High |
| Abstractness/concreteness | Whether glyph resembles a real-world referent or is abstract | Garcia-style component count, label/category metadata, object-recognition tags, human ratings; visual features alone are insufficient | Requires metadata/human labels | Medium |
| Semantic distance | How close the glyph is to its intended meaning | Label/category embeddings, icon-name tokens, human matching responses, ontology/category distance | Metadata/human-study feature | High as non-visual |
| Meaningfulness | Whether users can infer the meaning | Human matching accuracy, label agreement, semantic metadata, concreteness rating | Human-study feature | High as non-visual |
| Familiarity | Whether users have seen the glyph or symbol before | Dataset/source frequency, user survey familiarity rating, category commonness; image features cannot measure this directly | Human-study/metadata feature | High as non-visual |
| Metaphoric/natural mapping | Whether visual form naturally maps to meaning | Domain taxonomy, labels, expert coding, human memorability/guessability; possible CV object tags as weak proxy | Metadata/human-study feature | Medium |
| Learnability/memorability | Whether a glyph can be learned and remembered | Human learning trials, recognition accuracy after delay; proxies: simplicity, distinctiveness, concreteness | Requires human data plus proxies | Medium |
| Context sensitivity | Whether identification improves in a set or application context | Study variable: isolated vs contextual display; computational proxy: semantic category neighbors and visual neighborhood | Requires study design | High as experimental factor |
| Dimensionality/cognitive load | Number of encoded dimensions or separable visual channels | Count of visual channels, components, contours, line orientations, color channels; for data glyphs, original encoded-dimension metadata | Partial | Medium |
| Resolution robustness | Whether glyph remains identifiable when small | Crush-test features: recompute features after downsampling/blur/grayscale; measure feature loss and nearest-neighbor changes | Missing | High need |

## Recommended Feature Families For Analysis

For thesis experiments, group the features into interpretable families:

| Human category | Computer feature family |
|---|---|
| Complexity | edge density, perimeter/area, quadtree variability, components, holes |
| Shape | aspect ratio, solidity, contour closure, circularity/rectangularity, moments |
| Structure | components, contours, skeleton graph, line orientation, arrows, arcs |
| Density/fill | foreground area, bounding-box occupancy, filled/outline proxy |
| Balance/layout | symmetry, centroid, 4x4 grid occupancy |
| Color/contrast | monochrome flag, color count, saturation, colorfulness, foreground-background contrast, hue histogram |
| Texture | entropy, LBP/Gabor, repeated small components |
| Distinctiveness | pairwise feature distances, nearest-neighbor rank, quasi-Hamming channel difference count |
| Semantics | label/category tokens, metadata category, human matching/meaning ratings |

## Pairwise Mapping For Distinguishability

The Legg quasi-Hamming paper is the cleanest model for pairwise work. Convert each glyph into channel-level descriptors, discretize each channel, then count how many channels differ meaningfully.

| Pairwise human question | Pairwise computer predictor |
|---|---|
| Do these glyphs differ in color? | Delta in `is_monochrome`, `color_count`, `mean_saturation`, `colorfulness`, future hue/Lab distance |
| Do these glyphs differ in shape? | Distance over aspect ratio, solidity, contour closure, circularity, moments |
| Do these glyphs differ in complexity? | Distance over edge density, quadtree variability, components, holes, perimeter/area |
| Do these glyphs differ in orientation? | Distance over line orientation histogram, future principal-axis angle |
| Do these glyphs differ in components? | Difference in connected components, contour count, holes, skeleton endpoints/junctions |
| Do these glyphs differ in fill/outline style? | Difference in filled/outline proxy, perimeter/area, foreground density |
| Do these glyphs differ in spatial layout? | Distance over 4x4 grid cells and centroid |
| Are they likely confusable? | Low total distance, low quasi-Hamming channel count, close nearest-neighbor rank |
| Are they robustly distinguishable? | High distance across multiple independent feature channels, stable under downsampling/crush tests |

## Feature Gaps To Add

Implementation note: the high- and medium-priority visual gaps below are now represented in `code/extract_icon_features.py` and included in the regenerated `icon_data/analysis/features.csv`. Histogram-like features are stored as scalar CSV columns, for example `hue_histogram_00` through `hue_histogram_11` and `curvature_histogram_straight`, `curvature_histogram_gentle`, `curvature_histogram_sharp`.

High priority additions:

1. `circularity`: `4*pi*area/perimeter^2`.
2. `rectangularity`: foreground area divided by minimum bounding rectangle area.
3. `corner_count`: number of polygon/corner points after contour approximation.
4. `curvature_histogram`: contour curvature bins for straight vs curved glyphs.
5. `principal_axis_orientation`: PCA orientation of foreground pixels.
6. `stroke_width_mean` and `stroke_width_std`: skeleton plus distance transform.
7. `skeleton_endpoints` and `skeleton_junctions`: line-graph structure.
8. `hue_histogram` and `dominant_colors_lab`: stronger color-channel representation.
9. `texture_entropy` or `lbp_histogram`: texture/pattern channel.
10. `crush_test_stability`: feature/distance stability after downsampling.

Medium priority additions:

1. `arrowhead_count`: directional tip/triangle detection.
2. `arc_count`: circular/elliptical arc detection.
3. `text_or_letter_presence`: OCR or character-shape classifier.
4. `bbox_center_x`, `bbox_center_y`, `bbox_width_ratio`, `bbox_height_ratio`.
5. Hu/Zernike moment descriptors for shape matching.

## Clean Thesis Claim

Use this wording:

> Human glyph identification relies on a mixture of low-level visual factors, perceptual grouping, set-level distinctiveness, and semantic/contextual interpretation. The current computer-vision feature set can directly approximate many low-level and structural factors such as complexity, density, contours, closure, symmetry, orientation, color, and spatial layout. It cannot directly measure familiarity, meaningfulness, semantic distance, or metaphor without metadata or human-response data. Therefore, the thesis should model visual distinguishability with image features and validate it against human judgments rather than claiming that image features fully replace human perception.
