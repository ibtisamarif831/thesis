# Feature Mapping For Visual Categorization

This note maps icon features to the visual categories they can support. The features should be treated as measurable descriptors, not as direct semantic labels. They can explain visual grouping, distinguishability, and similarity; semantic categorization still needs icon labels, metadata, tags, or human responses.

## Table 1: Strongest Features Mapped To Visual Categorization

This table keeps the feature set compact. Each visual category has only the strongest, most interpretable features needed for analysis.

| Visual categorization | Strongest features to use | What the features capture | Example category labels |
|---|---|---|---|
| Simple vs complex | `canny_edge_density`, `quadtree_structural_variability` | Edge/detail load and spatial irregularity | simple icon, complex icon |
| Sparse vs dense | `foreground_area_ratio`, `bounding_box_occupancy` | How much of the canvas and active bounding box is occupied | sparse icon, dense icon |
| Single-object vs multi-part | `connected_components`, `contour_count` | Whether the icon is one coherent object or multiple visual parts | single-object symbol, multi-component symbol |
| Compact vs spread-out | `bounding_box_aspect_ratio`, `solidity` | Shape extent and how tightly the foreground fills its outer envelope | compact icon, tall icon, wide icon, fragmented icon |
| Centered vs off-center | `centroid_distance_from_center` | How far the visual mass is from the image center | centered icon, off-center icon |
| Balanced vs unbalanced | `horizontal_symmetry`, `vertical_symmetry` | Left-right and top-bottom visual balance | symmetric icon, asymmetric icon |
| Filled vs outline | `perimeter_area_ratio`, `filled_vs_outline_proxy` | Boundary length relative to area, and whether the icon behaves like solid fill or line art | filled pictogram, outline icon, line icon |
| Open vs closed shape | `holes_count`, `closed_contour_ratio` | Enclosed spaces and closed shape structure | closed-shape icon, open-line icon |
| Directional/geometric structure | line orientation histogram | Dominant horizontal, vertical, and diagonal structure | horizontal icon, vertical icon, diagonal/action icon |
| Black-and-white vs colored | `is_monochrome`, `color_count` | Whether color is present and how many colors are used | monochrome icon, colored icon |
| Color intensity/style | `mean_saturation`, `colorfulness` | Vividness and overall color richness | muted icon, vivid icon, emoji-like icon |
| High contrast vs low contrast | `foreground_background_contrast` | Legibility of foreground against background | high-contrast icon, low-contrast icon |
| Spatial layout similarity | foreground ratio in 4x4 grid cells | Coarse distribution of visual mass across the icon | top-heavy icon, left-heavy icon, central icon |
| Visually distinctive vs confusable | overall feature distance, nearest-neighbor rank, cluster isolation score | How close or far an icon is from others in feature space | distinctive icon, confusable icon |
| Explainable pairwise distinguishability | shape distance, color distance, complexity distance, number of different feature channels | Which visual channels differ between two icons | shape-distinct pair, color-distinct pair, visually similar pair |
| Semantic-category alignment check | visual cluster id, metadata category, label tokens | Whether visual clusters overlap with meaning labels | healthcare cluster, hazard cluster, transport cluster |

## Table 2: Reasoning Behind Strongest Core Features

| Feature or feature family | Applies to | Reason for including | Main use |
|---|---|---|---|
| `foreground_area_ratio` | All icons | Measures how much visible material the icon contains. It is a simple density and salience descriptor. | Sparse vs dense, complexity |
| `canny_edge_density` | All icons | Captures edge/detail load. Edge-heavy icons often appear more visually complex. | Complexity, distinguishability |
| `connected_components` | All icons | Counts separated visual parts. Multi-part icons can be harder to process and easier to distinguish from single-object icons. | Object structure |
| `quadtree_structural_variability` | All icons | Captures spatial irregularity. This is one of the strongest literature-aligned complexity features. | Complexity, human-perception overlap |
| `bounding_box_occupancy` | All icons | Measures how much of the active bounding box is filled. It helps separate sparse outlines from filled shapes. | Density, filled-vs-outline |
| `bounding_box_aspect_ratio` | All icons | Separates tall, wide, and square icons. Shape extent is easy to interpret and useful for clustering. | Shape category |
| `solidity` | All icons | Foreground area divided by convex hull area. Low solidity indicates gaps, branches, or fragmented structure. | Compact vs fragmented |
| `centroid_distance_from_center` | All icons | Summarizes how centered or displaced the visual mass is. | Centered vs off-center |
| `horizontal_symmetry` | All icons | Measures left-right balance, which is perceptually salient and common in icon design. | Balance, style |
| `vertical_symmetry` | All icons | Measures top-bottom balance and complements horizontal symmetry. | Balance, style |
| `perimeter_area_ratio` | All icons | High values indicate many boundaries relative to filled area, often line-art or detailed outlines. | Filled vs outline, complexity |
| `filled_vs_outline_proxy` | All icons | Converts area/perimeter/edge relationships into an interpretable style descriptor. | Style categorization |
| `contour_count` | All icons | Counts separate contours, which helps distinguish simple silhouettes from multi-shape icons. | Shape parts, complexity |
| `holes_count` | All icons | Counts enclosed empty spaces. It is important for closure, letters, signs, wheels, and many symbols. | Open vs closed, complexity |
| `closed_contour_ratio` | All icons | Measures how much the icon is composed of closed shapes. This is important for human similarity judgments. | Shape similarity |
| Line orientation histogram | All icons | Captures horizontal, vertical, and diagonal structure without needing many separate line features. | Directional grouping |
| `is_monochrome` | All icons | Identifies whether color is available as a visual channel, which matters because the dataset mixes colored and black-and-white icons. | Color-aware comparison |
| `color_count` | Colored icons | Counts distinct or quantized colors. It separates simple flat symbols from richer color icons. | Color complexity |
| `mean_saturation` | Colored icons | Separates vivid icons from muted or grayscale-like icons. | Color style |
| `colorfulness` | Colored icons | Summarizes saturation and color variation into one interpretable color-richness measure. | Emoji-like vs symbol-like |
| `foreground_background_contrast` | All icons | Measures how clearly the foreground separates from the background. This is relevant to legibility and recognition. | Visibility |
| Foreground ratio in 4x4 grid cells | All icons | Encodes coarse spatial layout while remaining interpretable. | Spatial similarity |
| Overall feature distance | Icon pairs | Combines standardized visual differences into one machine distinguishability score. | Human-study predictor |
| Shape distance | Icon pairs | Separates shape-based distinguishability from color-based distinguishability. | Human-study predictor |
| Color distance | Icon pairs with color | Captures cases where icons are similar in shape but distinguishable by color. | Human-study predictor |
| Complexity distance | Icon pairs | Measures whether two icons differ in visual complexity. | Human-study predictor |
| Nearest-neighbor rank | Icon pairs or individual icons | Identifies icons that are visually close to others and may be confusable. | Confusability analysis |
| Cluster isolation score | Individual icons | Measures whether an icon stands apart from nearby icons in feature space. | Distinctiveness score |
| Number of different feature channels | Icon pairs | An explainable quasi-Hamming-style score: how many visual channels differ meaningfully. | Explainable distinguishability |

## Practical Interpretation

For thesis analysis, use interpretable features as the main model and advanced features as comparison baselines. A good structure is:

1. Shape and structure features for explainable visual categorization.
2. Color features to handle the mixed colored and black-and-white dataset.
3. Pairwise distances to estimate distinguishability.
4. Metadata/text features only when testing semantic category alignment.

The strongest claim should be:

> Visual features can categorize icons by appearance and estimate distinguishability. Semantic categorization requires metadata or labels, but visual clusters can be compared against semantic categories and human quantitative judgments.
