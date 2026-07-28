"""Authoritative schema-v2 visual feature and family registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Sequence

FEATURE_SCHEMA_VERSION = 2
ORIENTATION_CONFIDENCE_THRESHOLD = 0.20

# Code-only analysis switch. Keep the UI free of profile controls: add or edit a
# named preset below, then change this value to activate it for dashboard
# clustering, Feature Review, and pairwise similarity.
ANALYSIS_FEATURE_PRESET = "representatives"


class FeatureStatus(str, Enum):
    ACTIVE = "active"
    AUXILIARY = "auxiliary"
    DEPRECATED = "deprecated"
    EXCLUDED = "excluded"


class EvidenceScope(str, Enum):
    DIRECT = "direct"
    CONSTRUCT = "construct"
    CAUTIONARY = "cautionary"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    id: str
    label: str
    meaning: str
    family_id: str | None
    status: FeatureStatus
    exclusion_reason: str
    category_reason: str
    visual_categorizations: tuple[str, ...]
    evidence_scope: EvidenceScope
    evidence: str
    citation: str


@dataclass(frozen=True, slots=True)
class FamilySpec:
    id: str
    title: str
    description: str
    human_category: str
    family_summary: str
    perception: str
    low_value: str
    high_value: str
    feature_ids: tuple[str, ...]
    representative_feature_id: str
    representative_interpretation: str
    representative_rationale: str
    representative_evidence: str
    representative_citation: str
    benchmark_family_id: str
    visible: bool = True

RAW_FEATURE_IDS: tuple[str, ...] = ('foreground_area_ratio',
 'canny_edge_density',
 'connected_components',
 'quadtree_leaf_count',
 'quadtree_structural_variability',
 'quadtree_mean_leaf_size',
 'bounding_box_occupancy',
 'bounding_box_aspect_ratio',
 'bbox_center_x',
 'bbox_center_y',
 'bbox_width_ratio',
 'bbox_height_ratio',
 'solidity',
 'centroid_distance_from_center',
 'horizontal_symmetry',
 'vertical_symmetry',
 'perimeter_area_ratio',
 'filled_vs_outline_proxy',
 'contour_count',
 'holes_count',
 'closed_contour_ratio',
 'line_orientation_0',
 'line_orientation_45',
 'line_orientation_90',
 'line_orientation_135',
 'is_monochrome',
 'color_count',
 'mean_saturation',
 'colorfulness',
 'foreground_background_contrast',
 'grid_foreground_0_0',
 'grid_foreground_0_1',
 'grid_foreground_0_2',
 'grid_foreground_0_3',
 'grid_foreground_1_0',
 'grid_foreground_1_1',
 'grid_foreground_1_2',
 'grid_foreground_1_3',
 'grid_foreground_2_0',
 'grid_foreground_2_1',
 'grid_foreground_2_2',
 'grid_foreground_2_3',
 'grid_foreground_3_0',
 'grid_foreground_3_1',
 'grid_foreground_3_2',
 'grid_foreground_3_3',
 'circularity',
 'rectangularity',
 'corner_count',
 'curvature_histogram_straight',
 'curvature_histogram_gentle',
 'curvature_histogram_sharp',
 'principal_axis_orientation',
 'arrowhead_count',
 'arc_count',
 'hu_moment_1',
 'hu_moment_2',
 'hu_moment_3',
 'hu_moment_4',
 'hu_moment_5',
 'hu_moment_6',
 'hu_moment_7',
 'stroke_width_mean',
 'stroke_width_std',
 'skeleton_endpoints',
 'skeleton_junctions',
 'hue_histogram_00',
 'hue_histogram_01',
 'hue_histogram_02',
 'hue_histogram_03',
 'hue_histogram_04',
 'hue_histogram_05',
 'hue_histogram_06',
 'hue_histogram_07',
 'hue_histogram_08',
 'hue_histogram_09',
 'hue_histogram_10',
 'hue_histogram_11',
 'dominant_color_1_lab_l',
 'dominant_color_1_lab_a',
 'dominant_color_1_lab_b',
 'dominant_color_2_lab_l',
 'dominant_color_2_lab_a',
 'dominant_color_2_lab_b',
 'dominant_color_3_lab_l',
 'dominant_color_3_lab_a',
 'dominant_color_3_lab_b',
 'texture_entropy',
 'lbp_histogram_00',
 'lbp_histogram_01',
 'lbp_histogram_02',
 'lbp_histogram_03',
 'lbp_histogram_04',
 'lbp_histogram_05',
 'lbp_histogram_06',
 'lbp_histogram_07',
 'lbp_histogram_08',
 'lbp_histogram_09',
 'crush_test_stability',
 'text_or_letter_presence',
 'quadtree_structural_variability_v2',
 'enclosure_score_v2',
 'principal_axis_orientation_v2',
 'orientation_confidence_v2',
 'solid_fill_ratio_v2',
 'horizontal_symmetry_v2',
 'mean_saturation_v2',
 'local_texture_variation_v2',
 'red_pixel_ratio_v2',
 'strict_red_flag_v2')

_FAMILY_DATA = [{'id': 'complexity',
  'title': 'Complexity',
  'description': 'Detail load, structural subdivision, component count, contour count, holes, perimeter '
                 'load, and angular point count.',
  'human_category': 'Complexity',
  'family_summary': 'edge density, perimeter/area, quadtree variability, components, contours, holes',
  'perception': 'This family approximates how visually busy or effortful a glyph is to parse. Component '
                'and contour counts are pixel-level proxies; human grouping can still differ.',
  'low_value': 'Lower values usually mean a simpler, cleaner symbol with fewer parts, edges, holes, or '
               'sharp details.',
  'high_value': 'Higher values usually mean a more intricate symbol that may take more attention to '
                'inspect and distinguish.',
  'representative_feature_id': 'canny_edge_density',
  'representative_interpretation': 'Lower values indicate fewer detected edges across the canvas; higher '
                                   'values indicate more connected edge and detail structure.',
  'representative_rationale': 'Selected after the visual audit found that grayscale quadtree variability '
                              'can reward antialiasing and raster transitions in otherwise simple icons. '
                              'The current Canny implementation smooths before edge detection and aligns '
                              'better with the extracted McDougall complexity ratings.',
  'representative_evidence': "Forsythe et al. describe Canny's dual thresholds as retaining weak edges "
                             'connected to strong edges while suppressing shading and noise, and report a '
                             "Spearman correlation of 0.49 with McDougall's subjective complexity ratings.",
  'representative_citation': 'Forsythe, Sheehy & Sawey, Measuring Icon Complexity: An Automated Analysis, '
                             'pp. 5-6.',
  'feature_ids': ['canny_edge_density',
                  'quadtree_leaf_count',
                  'quadtree_structural_variability_v2',
                  'quadtree_mean_leaf_size',
                  'connected_components',
                  'contour_count',
                  'holes_count',
                  'perimeter_area_ratio',
                  'corner_count']},
 {'id': 'shape',
  'title': 'Shape/silhouette',
  'description': 'Silhouette, closure, roundness, rectangularity, and curvature.',
  'human_category': 'Shape/silhouette',
  'family_summary': 'aspect ratio, solidity, closure proxy, circularity/rectangularity, curvature',
  'perception': 'This family captures the overall visible form of a glyph: roundness, box-like form, '
                'elongation, closure, curvature, and global silhouette.',
  'low_value': 'Lower values depend on the feature: low circularity means less round, and low '
               'closure-proxy values suggest more open or line-like form.',
  'high_value': 'Higher values indicate stronger presence of that specific shape property, such as more '
                'circular, more rectangular, or more closed by proxy.',
  'representative_feature_id': 'enclosure_score_v2',
  'representative_interpretation': 'Lower values usually mean a thin, open, or spread-out shape. Higher '
                                   'values usually mean a large, compact, or closed shape.',
  'representative_rationale': 'Selected because closure changes whether viewers group a glyph as one '
                              'coherent shape, making it a direct bridge between silhouette structure and '
                              'human similarity strategy.',
  'representative_evidence': 'Fuchs et al. found a significant effect of contour variation on accuracy and '
                             'showed that contour containment shifted judgments toward geometric shape '
                             'similarity. The implemented value remains a computational proxy, not a '
                             'direct Gestalt-closure score.',
  'representative_citation': 'Fuchs et al., The Influence of Contour on Similarity Perception of Star '
                             'Glyphs, pp. 5-8.',
  'feature_ids': ['bounding_box_aspect_ratio',
                  'solidity',
                  'enclosure_score_v2',
                  'circularity',
                  'rectangularity',
                  'curvature_histogram_straight',
                  'curvature_histogram_gentle',
                  'curvature_histogram_sharp']},
 {'id': 'structure',
  'title': 'Stroke/structure',
  'description': 'Directional strokes, principal orientation, arrows, arcs, and skeleton graph structure.',
  'human_category': 'Stroke/structure',
  'family_summary': 'line orientation, principal axis, arrows, arcs, skeleton graph',
  'perception': 'This family captures internal organization: stroke direction, branching, endpoints, '
                'arrows, and arcs. It describes visible structure, not exact text or semantic identity.',
  'low_value': 'Lower values usually mean less explicit directionality, fewer skeleton branches/endpoints, '
               'or fewer arrows/arcs.',
  'high_value': 'Higher values usually mean stronger directional cues, more branching structure, more '
                'endpoints/junctions, or clearer arrow components.',
  'representative_feature_id': 'principal_axis_orientation_v2',
  'representative_interpretation': 'The value is an axial angle, not an amount: 0° is horizontal, 90° is '
                                   'vertical, and 180° wraps to horizontal. Confidence below 0.20 means '
                                   'undefined.',
  'representative_rationale': 'Selected as the clearest single summary of global stroke direction and '
                              'because orientation was one of the more separable human-rated visual '
                              'channels.',
  'representative_evidence': 'The quasi-Hamming study reports an average human perceptual-distance score '
                             'of 3.0 for orientation, above connection lines (2.8), texture (2.2), color '
                             '(2.2), size (2.1), and luminance (1.2).',
  'representative_citation': 'Legg et al., Glyph Visualization: A Fail-Safe Design Scheme Based on '
                             'Quasi-Hamming Distances, p. 5.',
  'feature_ids': ['line_orientation_0',
                  'line_orientation_45',
                  'line_orientation_90',
                  'line_orientation_135',
                  'principal_axis_orientation_v2',
                  'arrowhead_count',
                  'arc_count',
                  'skeleton_endpoints',
                  'skeleton_junctions']},
 {'id': 'density_fill',
  'title': 'Density/fill',
  'description': 'Foreground amount, bounding-box fill, outline-vs-fill behavior, and stroke thickness.',
  'human_category': 'Density/fill',
  'family_summary': 'foreground amount, bounding-box occupancy, filled/outline proxy, stroke width',
  'perception': 'This family describes whether a glyph reads as sparse line art, a filled silhouette, or a '
                'heavy/thick mark.',
  'low_value': 'Lower values usually mean a lighter, thinner, more open, or less filled glyph.',
  'high_value': 'Higher values usually mean a denser, more filled, more visually heavy glyph with thicker '
                'strokes or stronger occupancy.',
  'representative_feature_id': 'solid_fill_ratio_v2',
  'representative_interpretation': 'Lower values lose foreground quickly under 1%, 2%, and 4% erosion and '
                                   'suggest outlines; higher values retain a solid interior.',
  'representative_rationale': 'Selected because filled-versus-outline treatment directly changes '
                              'figure-ground structure and has experimental evidence of changing '
                              'similarity-choice behavior.',
  'representative_evidence': 'Fuchs et al. found significant fill-type effects on rotated and scaled '
                             'similarity choices. They did not find a general accuracy benefit, so this '
                             'feature should be interpreted as affecting strategy rather than quality.',
  'representative_citation': 'Fuchs et al., The Influence of Contour on Similarity Perception of Star '
                             'Glyphs, pp. 6-8.',
  'feature_ids': ['foreground_area_ratio',
                  'bounding_box_occupancy',
                  'solid_fill_ratio_v2',
                  'stroke_width_mean',
                  'stroke_width_std']},
 {'id': 'balance_layout',
  'title': 'Balance/layout',
  'description': 'Centering, symmetry, active bounding-box position/size, and 4x4 foreground grid layout.',
  'human_category': 'Balance/layout',
  'family_summary': 'symmetry, centroid, bounding-box position/size, 4x4 grid occupancy',
  'perception': 'This family captures where visual mass sits and whether the glyph feels centered, '
                'balanced, symmetric, top-heavy, side-heavy, compact, or spread out. Grid features should '
                'be treated as one layout channel when comparing families.',
  'low_value': 'Lower values often mean less offset or less occupancy in a given region; for symmetry '
               'scores, lower means less balanced.',
  'high_value': 'Higher values often mean stronger occupancy in a region, larger active extent, more '
                'offset for distance features, or stronger balance for symmetry scores.',
  'representative_feature_id': 'horizontal_symmetry_v2',
  'representative_interpretation': 'Lower values indicate weaker left-right correspondence; higher values '
                                   'indicate stronger bilateral Dice overlap with a two-pixel tolerance.',
  'representative_rationale': 'Selected because symmetry is a foundational perceptual-grouping cue, '
                              'horizontal symmetry has a direct implementation, and symmetry-optimized '
                              'glyph designs have reported performance benefits.',
  'representative_evidence': 'The glyph-foundations review identifies symmetry as a Gestalt organization '
                             'principle and reports improved user performance for complexity- and '
                             'symmetry-optimized star-glyph orderings.',
  'representative_citation': 'Borgo et al., Glyph-based Visualization: Foundations, Design Guidelines, '
                             'Techniques and Applications, pp. 7, 12 and 16.',
  'feature_ids': ['centroid_distance_from_center',
                  'horizontal_symmetry_v2',
                  'vertical_symmetry',
                  'bbox_center_x',
                  'bbox_center_y',
                  'bbox_width_ratio',
                  'bbox_height_ratio',
                  'grid_foreground_0_0',
                  'grid_foreground_0_1',
                  'grid_foreground_0_2',
                  'grid_foreground_0_3',
                  'grid_foreground_1_0',
                  'grid_foreground_1_1',
                  'grid_foreground_1_2',
                  'grid_foreground_1_3',
                  'grid_foreground_2_0',
                  'grid_foreground_2_1',
                  'grid_foreground_2_2',
                  'grid_foreground_2_3',
                  'grid_foreground_3_0',
                  'grid_foreground_3_1',
                  'grid_foreground_3_2',
                  'grid_foreground_3_3']},
 {'id': 'color_contrast',
  'title': 'Color/contrast',
  'description': 'Color presence, saturation, colorfulness, foreground-background contrast, hue '
                 'distribution, and dominant Lab colors.',
  'human_category': 'Color/contrast',
  'family_summary': 'monochrome flag, color count, saturation, colorfulness, foreground-background '
                    'contrast, hue histogram, dominant Lab colors',
  'perception': 'This family captures color channels humans use for quick grouping, salience, and '
                'foreground-background separation.',
  'low_value': 'Lower values usually mean less saturation/colorfulness, weaker contrast, or less presence '
               'of a given hue bin. For `is_monochrome`, lower means color is present.',
  'high_value': 'Higher values usually mean stronger signal for that specific color feature. For '
                '`is_monochrome`, higher means grayscale/monochrome rather than more color.',
  'representative_feature_id': 'mean_saturation_v2',
  'representative_interpretation': 'Lower values indicate grayscale or muted corrected foregrounds; higher '
                                   'values indicate more vivid, strongly saturated corrected foreground '
                                   'color.',
  'representative_rationale': 'Selected as a continuous, interpretable color-strength measure that works '
                              'across the B/W, red, and colored cohorts without privileging one arbitrary '
                              'hue bin.',
  'representative_evidence': 'The glyph-foundations review describes color as the strongest of the '
                             'commonly compared pop-out channels. Choosing mean saturation as its '
                             'operational measure is a project inference; the literature supports the '
                             'color channel, not this exact formula.',
  'representative_citation': 'Borgo et al., Glyph-based Visualization: Foundations, Design Guidelines, '
                             'Techniques and Applications, pp. 7-10; Legg et al., Quasi-Hamming Distances, '
                             'p. 5.',
  'feature_ids': ['is_monochrome',
                  'color_count',
                  'mean_saturation_v2',
                  'colorfulness',
                  'foreground_background_contrast',
                  'hue_histogram_00',
                  'hue_histogram_01',
                  'hue_histogram_02',
                  'hue_histogram_03',
                  'hue_histogram_04',
                  'hue_histogram_05',
                  'hue_histogram_06',
                  'hue_histogram_07',
                  'hue_histogram_08',
                  'hue_histogram_09',
                  'hue_histogram_10',
                  'hue_histogram_11',
                  'dominant_color_1_lab_l',
                  'dominant_color_1_lab_a',
                  'dominant_color_1_lab_b',
                  'dominant_color_2_lab_l',
                  'dominant_color_2_lab_a',
                  'dominant_color_2_lab_b',
                  'dominant_color_3_lab_l',
                  'dominant_color_3_lab_a',
                  'dominant_color_3_lab_b']},
 {'id': 'texture',
  'title': 'Texture',
  'description': 'Foreground tonal entropy.',
  'human_category': 'Texture',
  'family_summary': 'foreground tonal entropy',
  'perception': 'This family captures internal tonal variation that can affect perceived detail. '
                'Artifact-prone local binary pattern bins are excluded from the active visual-family '
                'mapping.',
  'low_value': 'Lower values usually mean flatter, more uniform foreground regions with little internal '
               'texture or local tonal variation.',
  'high_value': 'Higher values usually mean more internal tonal variation that can make the glyph feel '
                'more textured.',
  'representative_feature_id': 'local_texture_variation_v2',
  'representative_interpretation': 'Lower values indicate flat interiors; higher values indicate stronger '
                                   'normalized 7x7 grayscale variation inside the eroded foreground, '
                                   'excluding the silhouette edge.',
  'representative_rationale': 'Selected because local interior variation excludes the silhouette boundary '
                              'and reduces the color/global-tonal leakage found in the legacy entropy '
                              'proxy.',
  'representative_evidence': 'Texture produced an average human quasi-Hamming perceptual-distance score of '
                             '2.2, supporting the construct but not this exact local-variation formula. '
                             'Human validation remains pending.',
 'representative_citation': 'Legg et al., Glyph Visualization: A Fail-Safe Design Scheme Based on '
                             'Quasi-Hamming Distances, p. 5; Borgo et al., Glyph-based Visualization, p. '
                             '8.',
  'feature_ids': ['local_texture_variation_v2']}]

_FORSYTHE_COMPLEXITY_CITATION = (
    "Forsythe, Sheehy & Sawey, Measuring Icon Complexity: An Automated Analysis, pp. 4-7."
)
_GARCIA_PRIMITIVES_CITATION = (
    "Garcia et al., Development and Validation of Icons Varying in Abstractness, pp. 3-4, 11 and 20."
)
_FUCHS_CONTOUR_CITATION = (
    "Fuchs et al., The Influence of Contour on Similarity Perception of Star Glyphs, pp. 2-3 and 6-8."
)
_LEGG_QHD_CITATION = (
    "Legg et al., Glyph Visualization: A Fail-Safe Design Scheme Based on Quasi-Hamming Distances, "
    "pp. 4-6."
)
_BORGO_CHANNELS_CITATION = (
    "Borgo et al., Glyph-based Visualization: Foundations, Design Guidelines, Techniques and "
    "Applications, pp. 7-10, 12 and 16."
)

_FEATURE_EVIDENCE_DATA: dict[str, tuple[EvidenceScope, str, str]] = {}


def _add_feature_evidence(
    feature_ids: Sequence[str],
    scope: EvidenceScope,
    evidence: str,
    citation: str,
) -> None:
    for feature_id in feature_ids:
        if feature_id in _FEATURE_EVIDENCE_DATA:
            raise ValueError(f"Duplicate literature-evidence entry for {feature_id!r}")
        _FEATURE_EVIDENCE_DATA[feature_id] = (scope, evidence, citation)


_add_feature_evidence(
    ("canny_edge_density",),
    EvidenceScope.DIRECT,
    "Forsythe et al. used Canny edge density as an automated icon-complexity measure and reported "
    "a Spearman correlation of 0.49 with McDougall subjective complexity ratings. Their dual-threshold "
    "description also motivates suppressing isolated weak responses. This is the closest measure-level "
    "evidence in the local corpus, although the repository implementation is still its own extraction.",
    "Forsythe, Sheehy & Sawey, Measuring Icon Complexity: An Automated Analysis, pp. 5-6.",
)
_add_feature_evidence(
    (
        "quadtree_leaf_count",
        "quadtree_structural_variability_v2",
        "quadtree_mean_leaf_size",
    ),
    EvidenceScope.CONSTRUCT,
    "Forsythe et al. describe recursive quadtree subdivision as distinguishing homogeneous icons "
    "with few large blocks from highly structured icons with many small blocks, and report a 0.65 "
    "correlation for their quadtree measure with subjective complexity. The paper supports spatial "
    "subdivision as a complexity construct; these exact leaf and variability formulas are project "
    "operationalizations.",
    _FORSYTHE_COMPLEXITY_CITATION,
)
_add_feature_evidence(
    ("connected_components",),
    EvidenceScope.CAUTIONARY,
    "Forsythe et al. counted discrete foreground objects, but found that pixel-connected components "
    "can disagree with human feature integration. Garcia et al. likewise observed that viewers may "
    "group several low-level elements as one unit. The feature is therefore evidence-informed but "
    "must not be treated as a direct count of perceived parts.",
    f"{_FORSYTHE_COMPLEXITY_CITATION} {_GARCIA_PRIMITIVES_CITATION}",
)
_add_feature_evidence(
    ("holes_count",),
    EvidenceScope.CAUTIONARY,
    "Forsythe et al. included holes through an Euler-number analysis but reported that tiny raster "
    "holes and pixel enumeration can distort the relation to perceived complexity. The metric records "
    "image topology, not a validated count of human-perceived enclosed parts.",
    _FORSYTHE_COMPLEXITY_CITATION,
)
_add_feature_evidence(
    ("perimeter_area_ratio",),
    EvidenceScope.CONSTRUCT,
    "Forsythe et al. report a 0.64 correlation between perimeter and subjective icon complexity. "
    "That supports boundary load as a complexity construct; normalizing perimeter by filled area is "
    "the repository's implementation choice and was not tested as that exact ratio.",
    _FORSYTHE_COMPLEXITY_CITATION,
)
_add_feature_evidence(
    ("contour_count",),
    EvidenceScope.CONSTRUCT,
    "Garcia et al. operationalized icon structure with open and closed figures, while Fuchs et al. "
    "showed that contour treatment can change similarity judgments. Counting raster contours is a "
    "project proxy for that contour structure, not a direct perceptual count.",
    f"{_GARCIA_PRIMITIVES_CITATION} {_FUCHS_CONTOUR_CITATION}",
)
_add_feature_evidence(
    ("corner_count",),
    EvidenceScope.CONSTRUCT,
    "The glyph-design literature treats angle, shape, curvature, and salient points as visual "
    "channels. Corner count operationalizes angular point load, but the local papers do not validate "
    "this exact detector or count against human icon judgments.",
    _BORGO_CHANNELS_CITATION,
)

_add_feature_evidence(
    ("bounding_box_aspect_ratio",),
    EvidenceScope.CONSTRUCT,
    "Aspect ratio is identified as a glyph visual channel, and contour-perception research reviews "
    "evidence that closed contours affect tall-versus-wide discrimination. The active-box ratio is a "
    "computational proxy; its exact formula was not tested in those studies.",
    f"{_BORGO_CHANNELS_CITATION} {_FUCHS_CONTOUR_CITATION}",
)
_add_feature_evidence(
    (
        "solidity",
        "circularity",
        "rectangularity",
        "curvature_histogram_straight",
        "curvature_histogram_gentle",
        "curvature_histogram_sharp",
    ),
    EvidenceScope.CONSTRUCT,
    "Shape and curvature are established glyph visual channels, and the quasi-Hamming study found "
    "shape among the best-separated primitive groups in its human ratings. The repository's compactness, "
    "roundness, rectangularity, and curvature descriptors are project operationalizations; the papers "
    "did not validate these exact formulas.",
    f"{_BORGO_CHANNELS_CITATION} {_LEGG_QHD_CITATION}",
)
_add_feature_evidence(
    ("enclosure_score_v2",),
    EvidenceScope.CONSTRUCT,
    "Fuchs et al. found significant effects of contour variation and showed that contour containment "
    "can shift judgments toward geometric-shape similarity. The implemented value approximates enclosed "
    "silhouette area; it is not a direct Gestalt-closure score.",
    _FUCHS_CONTOUR_CITATION,
)

_add_feature_evidence(
    (
        "line_orientation_0",
        "line_orientation_45",
        "line_orientation_90",
        "line_orientation_135",
    ),
    EvidenceScope.CONSTRUCT,
    "Garcia et al. explicitly counted horizontal, vertical, and diagonal lines in an icon-abstractness "
    "metric that was compared with subjective classifications. Legg et al. also found orientation to "
    "be a comparatively separable human-rated glyph channel. The repository uses detected-line shares "
    "rather than Garcia's manual primitive counts.",
    f"{_GARCIA_PRIMITIVES_CITATION} {_LEGG_QHD_CITATION}",
)
_add_feature_evidence(
    ("principal_axis_orientation_v2",),
    EvidenceScope.CONSTRUCT,
    "Legg et al. report an average human quasi-Hamming distance of 3.0 for orientation, placing it "
    "among the more separable primitive groups they tested. PCA axis angle and its confidence rule are "
    "project operationalizations, not formulas evaluated in that experiment.",
    _LEGG_QHD_CITATION,
)
_add_feature_evidence(
    ("arrowhead_count", "arc_count"),
    EvidenceScope.CONSTRUCT,
    "Garcia et al. explicitly include arrowheads and arcs in a low-level icon-primitive metric and "
    "report that the overall metric tracked subjective abstractness classifications, with grouping "
    "disagreements as a caveat. The repository's detectors approximate those primitives.",
    _GARCIA_PRIMITIVES_CITATION,
)
_add_feature_evidence(
    ("skeleton_endpoints", "skeleton_junctions"),
    EvidenceScope.CONSTRUCT,
    "Connection lines and components were rated as distinguishable primitive groups in the "
    "quasi-Hamming study, and the glyph-channel taxonomy includes connections, nodes, internal nodes, "
    "and terminators. Skeleton endpoints and junctions are graph proxies for those structures; their "
    "exact counts were not human-validated.",
    f"{_LEGG_QHD_CITATION} {_BORGO_CHANNELS_CITATION}",
)

_add_feature_evidence(
    ("foreground_area_ratio",),
    EvidenceScope.CAUTIONARY,
    "Forsythe et al. measured foreground pixel area but concluded that it was too crude as an icon-"
    "complexity estimate. It remains a valid image occupancy measurement in the Density/fill family, "
    "but should not be cited as a validated complexity predictor.",
    _FORSYTHE_COMPLEXITY_CITATION,
)
_add_feature_evidence(
    ("bounding_box_occupancy",),
    EvidenceScope.CONSTRUCT,
    "Area and density are recognized visual channels, and Legg et al. used spatial occupancy when "
    "constructing computer glyph codewords. Bounding-box occupancy is the repository's density proxy; "
    "the exact ratio was not validated against human judgments.",
    f"{_BORGO_CHANNELS_CITATION} {_LEGG_QHD_CITATION}",
)
_add_feature_evidence(
    ("solid_fill_ratio_v2",),
    EvidenceScope.CONSTRUCT,
    "Fuchs et al. found significant fill-type effects for rotated and scaled similarity choices, "
    "showing that filled-versus-outline treatment can alter judgment strategy. They did not establish "
    "a general accuracy benefit, and the erosion-survival formula is a project proxy.",
    _FUCHS_CONTOUR_CITATION,
)
_add_feature_evidence(
    ("stroke_width_mean", "stroke_width_std"),
    EvidenceScope.CONSTRUCT,
    "Width and line style appear in the glyph visual-channel taxonomy, supporting stroke weight as a "
    "visible construct. Skeleton-derived mean width and width variation are project measurements; the "
    "local literature does not validate their exact formulas against human icon judgments.",
    _BORGO_CHANNELS_CITATION,
)

_add_feature_evidence(
    ("horizontal_symmetry_v2", "vertical_symmetry"),
    EvidenceScope.CONSTRUCT,
    "Symmetry is described as a Gestalt organization principle, and the glyph-foundations review "
    "reports improved user performance for complexity- and symmetry-optimized star-glyph orderings. "
    "The repository's pixel-overlap scores are computational proxies rather than the tested ordering "
    "method.",
    _BORGO_CHANNELS_CITATION,
)
_add_feature_evidence(
    (
        "centroid_distance_from_center",
        "bbox_center_x",
        "bbox_center_y",
        "bbox_width_ratio",
        "bbox_height_ratio",
        "grid_foreground_0_0",
        "grid_foreground_0_1",
        "grid_foreground_0_2",
        "grid_foreground_0_3",
        "grid_foreground_1_0",
        "grid_foreground_1_1",
        "grid_foreground_1_2",
        "grid_foreground_1_3",
        "grid_foreground_2_0",
        "grid_foreground_2_1",
        "grid_foreground_2_2",
        "grid_foreground_2_3",
        "grid_foreground_3_0",
        "grid_foreground_3_1",
        "grid_foreground_3_2",
        "grid_foreground_3_3",
    ),
    EvidenceScope.CONSTRUCT,
    "Spatial location, distance, size, width, height, area, and density are identified as visual "
    "channels or perceptual-organization cues in the glyph-design literature. The centroid, active-box, "
    "and 4x4 occupancy values operationalize layout; their exact subdivisions were not evaluated in "
    "the cited studies.",
    _BORGO_CHANNELS_CITATION,
)

_add_feature_evidence(
    ("is_monochrome", "color_count", "mean_saturation_v2", "colorfulness"),
    EvidenceScope.CONSTRUCT,
    "Color, hue, saturation, intensity, and brightness are established glyph channels, with color "
    "described as especially strong for pop-out. Legg et al. also obtained human distinguishability "
    "ratings for color. These repository summaries operationalize color presence and strength; their "
    "exact formulas were not tested by those studies.",
    f"{_BORGO_CHANNELS_CITATION} {_LEGG_QHD_CITATION}",
)
_add_feature_evidence(
    ("foreground_background_contrast",),
    EvidenceScope.CONSTRUCT,
    "Figure-ground organization and brightness or intensity are recognized perceptual and glyph "
    "channels. Legg et al. separately rated luminance as a distinguishability primitive. The current "
    "foreground-background contrast formula is a project operationalization.",
    f"{_BORGO_CHANNELS_CITATION} {_LEGG_QHD_CITATION}",
)
_add_feature_evidence(
    (
        "hue_histogram_00",
        "hue_histogram_01",
        "hue_histogram_02",
        "hue_histogram_03",
        "hue_histogram_04",
        "hue_histogram_05",
        "hue_histogram_06",
        "hue_histogram_07",
        "hue_histogram_08",
        "hue_histogram_09",
        "hue_histogram_10",
        "hue_histogram_11",
    ),
    EvidenceScope.CONSTRUCT,
    "Hue is an established optical glyph channel and color has strong pop-out behavior. Fixed "
    "30-degree hue-bin shares are the repository's representation of that channel; neither the bin "
    "count nor these boundaries were validated in the cited studies.",
    f"{_BORGO_CHANNELS_CITATION} {_LEGG_QHD_CITATION}",
)
_add_feature_evidence(
    (
        "dominant_color_1_lab_l",
        "dominant_color_1_lab_a",
        "dominant_color_1_lab_b",
        "dominant_color_2_lab_l",
        "dominant_color_2_lab_a",
        "dominant_color_2_lab_b",
        "dominant_color_3_lab_l",
        "dominant_color_3_lab_a",
        "dominant_color_3_lab_b",
    ),
    EvidenceScope.CONSTRUCT,
    "Legg et al. used Hunter Lab distances for computer color and luminance codewords alongside their "
    "human quasi-Hamming study. This supports a perceptually organized Lab representation, but selecting "
    "three dominant colors and exposing their individual channels is the repository's implementation.",
    _LEGG_QHD_CITATION,
)

_add_feature_evidence(
    ("local_texture_variation_v2",),
    EvidenceScope.CONSTRUCT,
    "Texture produced an average human quasi-Hamming distance of 2.2 in Legg et al., and texture is "
    "listed as a glyph visual channel in the foundations review. The normalized local-interior variation "
    "formula was not evaluated in those studies and still requires human validation.",
    f"{_LEGG_QHD_CITATION} {_BORGO_CHANNELS_CITATION}",
)

_FEATURE_LABELS = {'quadtree_structural_variability_v2': 'Intensity quadtree variability (v2)',
 'enclosure_score_v2': 'Enclosure score (v2)',
 'principal_axis_orientation_v2': 'Principal-axis orientation (v2)',
 'orientation_confidence_v2': 'Orientation confidence (v2)',
 'solid_fill_ratio_v2': 'Solid fill ratio (v2)',
 'horizontal_symmetry_v2': 'Horizontal symmetry (v2)',
 'mean_saturation_v2': 'Mean saturation (v2)',
 'local_texture_variation_v2': 'Local texture variation (v2)',
 'red_pixel_ratio_v2': 'Strict-red pixel ratio (v2)',
 'strict_red_flag_v2': 'Strict-red flag (v2)',
 'foreground_area_ratio': 'Foreground area ratio',
 'canny_edge_density': 'Edge density',
 'connected_components': 'Connected components',
 'quadtree_leaf_count': 'Quadtree leaf count',
 'quadtree_structural_variability': 'Quadtree structural variability',
 'quadtree_mean_leaf_size': 'Quadtree mean leaf size',
 'bounding_box_occupancy': 'Bounding-box occupancy',
 'bounding_box_aspect_ratio': 'Bounding-box aspect ratio',
 'solidity': 'Solidity',
 'centroid_distance_from_center': 'Center offset',
 'horizontal_symmetry': 'Horizontal symmetry',
 'vertical_symmetry': 'Vertical symmetry',
 'perimeter_area_ratio': 'Perimeter-area ratio',
 'filled_vs_outline_proxy': 'Filled-vs-outline proxy',
 'contour_count': 'Contour count',
 'holes_count': 'Holes count',
 'closed_contour_ratio': 'Closure proxy',
 'line_orientation_0': 'Horizontal line orientation',
 'line_orientation_45': 'Diagonal 45 degree orientation',
 'line_orientation_90': 'Vertical line orientation',
 'line_orientation_135': 'Diagonal 135 degree orientation',
 'is_monochrome': 'Monochrome flag',
 'color_count': 'Color count',
 'mean_saturation': 'Mean saturation',
 'colorfulness': 'Colorfulness',
 'foreground_background_contrast': 'Foreground-background contrast',
 'bbox_center_x': 'Bounding-box center x',
 'bbox_center_y': 'Bounding-box center y',
 'bbox_width_ratio': 'Bounding-box width ratio',
 'bbox_height_ratio': 'Bounding-box height ratio',
 'circularity': 'Circularity',
 'rectangularity': 'Rectangularity',
 'corner_count': 'Corner count',
 'curvature_histogram_straight': 'Straight-contour share',
 'curvature_histogram_gentle': 'Gentle-curvature share',
 'curvature_histogram_sharp': 'Sharp-curvature share',
 'principal_axis_orientation': 'Principal-axis orientation',
 'arrowhead_count': 'Arrowhead count',
 'arc_count': 'Arc count',
 'stroke_width_mean': 'Mean stroke width',
 'stroke_width_std': 'Stroke-width variation',
 'skeleton_endpoints': 'Skeleton endpoints',
 'skeleton_junctions': 'Skeleton junctions',
 'texture_entropy': 'Texture entropy',
 'crush_test_stability': 'Crush-test stability',
 'text_or_letter_presence': 'Text/letter presence proxy',
 'hu_moment_1': 'Hu moment 1',
 'hu_moment_2': 'Hu moment 2',
 'hu_moment_3': 'Hu moment 3',
 'hu_moment_4': 'Hu moment 4',
 'hu_moment_5': 'Hu moment 5',
 'hu_moment_6': 'Hu moment 6',
 'hu_moment_7': 'Hu moment 7',
 'hue_histogram_00': 'Hue 0-30 deg',
 'hue_histogram_01': 'Hue 30-60 deg',
 'hue_histogram_02': 'Hue 60-90 deg',
 'hue_histogram_03': 'Hue 90-120 deg',
 'hue_histogram_04': 'Hue 120-150 deg',
 'hue_histogram_05': 'Hue 150-180 deg',
 'hue_histogram_06': 'Hue 180-210 deg',
 'hue_histogram_07': 'Hue 210-240 deg',
 'hue_histogram_08': 'Hue 240-270 deg',
 'hue_histogram_09': 'Hue 270-300 deg',
 'hue_histogram_10': 'Hue 300-330 deg',
 'hue_histogram_11': 'Hue 330-360 deg',
 'dominant_color_1_lab_l': 'Dominant color 1 Lab L',
 'dominant_color_1_lab_a': 'Dominant color 1 Lab a',
 'dominant_color_1_lab_b': 'Dominant color 1 Lab b',
 'dominant_color_2_lab_l': 'Dominant color 2 Lab L',
 'dominant_color_2_lab_a': 'Dominant color 2 Lab a',
 'dominant_color_2_lab_b': 'Dominant color 2 Lab b',
 'dominant_color_3_lab_l': 'Dominant color 3 Lab L',
 'dominant_color_3_lab_a': 'Dominant color 3 Lab a',
 'dominant_color_3_lab_b': 'Dominant color 3 Lab b',
 'lbp_histogram_00': 'LBP texture bin 0',
 'lbp_histogram_01': 'LBP texture bin 1',
 'lbp_histogram_02': 'LBP texture bin 2',
 'lbp_histogram_03': 'LBP texture bin 3',
 'lbp_histogram_04': 'LBP texture bin 4',
 'lbp_histogram_05': 'LBP texture bin 5',
 'lbp_histogram_06': 'LBP texture bin 6',
 'lbp_histogram_07': 'LBP texture bin 7',
 'lbp_histogram_08': 'LBP texture bin 8',
 'lbp_histogram_09': 'LBP texture bin 9',
 'grid_foreground_0_0': 'Grid foreground r1 c1',
 'grid_foreground_0_1': 'Grid foreground r1 c2',
 'grid_foreground_0_2': 'Grid foreground r1 c3',
 'grid_foreground_0_3': 'Grid foreground r1 c4',
 'grid_foreground_1_0': 'Grid foreground r2 c1',
 'grid_foreground_1_1': 'Grid foreground r2 c2',
 'grid_foreground_1_2': 'Grid foreground r2 c3',
 'grid_foreground_1_3': 'Grid foreground r2 c4',
 'grid_foreground_2_0': 'Grid foreground r3 c1',
 'grid_foreground_2_1': 'Grid foreground r3 c2',
 'grid_foreground_2_2': 'Grid foreground r3 c3',
 'grid_foreground_2_3': 'Grid foreground r3 c4',
 'grid_foreground_3_0': 'Grid foreground r4 c1',
 'grid_foreground_3_1': 'Grid foreground r4 c2',
 'grid_foreground_3_2': 'Grid foreground r4 c3',
 'grid_foreground_3_3': 'Grid foreground r4 c4'}

_FEATURE_MEANINGS = {'quadtree_structural_variability_v2': 'Quadtree subdivision density of grayscale intensity within the '
                                       'active foreground box.',
 'enclosure_score_v2': 'Area enclosed by external foreground contours relative to the active bounding box.',
 'principal_axis_orientation_v2': 'PCA foreground-axis angle over 0-180 degrees; interpret only when '
                                  'orientation confidence is at least 0.20.',
 'orientation_confidence_v2': 'PCA eigenvalue anisotropy; values below 0.20 indicate undefined '
                              'orientation.',
 'solid_fill_ratio_v2': 'Mean foreground survival after erosion at 1%, 2%, and 4% of active-box '
                        'width/height.',
 'horizontal_symmetry_v2': 'Left-right Dice-style foreground overlap allowing a two-pixel alignment '
                           'tolerance.',
 'mean_saturation_v2': 'Mean HSV saturation over corrected foreground pixels.',
 'local_texture_variation_v2': 'Normalized 7x7 local grayscale variation within a two-pixel-eroded '
                               'foreground interior.',
 'red_pixel_ratio_v2': 'Share of corrected foreground pixels meeting the strict red hue, saturation, and '
                       'value thresholds.',
 'strict_red_flag_v2': 'One only when at least 90% of all corrected foreground pixels meet the strict-red '
                       'rule.',
 'foreground_area_ratio': 'How much of the canvas is occupied by visible foreground pixels.',
 'canny_edge_density': 'How much edge/detail structure appears in the icon.',
 'connected_components': 'How many separated foreground parts the icon contains.',
 'quadtree_leaf_count': 'How many spatial subdivisions are needed to describe the foreground pattern.',
 'quadtree_structural_variability': 'How unevenly structure is distributed across the icon.',
 'quadtree_mean_leaf_size': 'Average quadtree region size; smaller values imply more localized detail.',
 'bounding_box_occupancy': 'How densely the icon fills its active bounding box.',
 'bounding_box_aspect_ratio': 'Whether the active icon shape is tall, wide, or square-like.',
 'solidity': 'How compactly the foreground fills its outer convex envelope.',
 'centroid_distance_from_center': "How far the icon's visual mass is from the canvas center.",
 'horizontal_symmetry': 'How balanced the icon is across the left-right axis.',
 'vertical_symmetry': 'How balanced the icon is across the top-bottom axis.',
 'perimeter_area_ratio': 'How much boundary length exists relative to filled area.',
 'filled_vs_outline_proxy': 'Whether the icon behaves more like a filled mark or an outline/line drawing.',
 'contour_count': 'How many contour boundaries are present.',
 'holes_count': 'How many enclosed empty spaces appear inside foreground shapes.',
 'closed_contour_ratio': 'Proxy for closed-shape behavior from contours, holes, and compactness; not a '
                         'direct human closure judgment.',
 'line_orientation_0': 'Share of detected line structure that is mostly horizontal.',
 'line_orientation_45': 'Share of detected line structure that follows a 45 degree diagonal.',
 'line_orientation_90': 'Share of detected line structure that is mostly vertical.',
 'line_orientation_135': 'Share of detected line structure that follows a 135 degree diagonal.',
 'is_monochrome': 'Whether the icon is effectively black-and-white or grayscale.',
 'color_count': 'Approximate number of distinct foreground colors.',
 'mean_saturation': 'Average foreground color saturation.',
 'colorfulness': 'Overall richness and variation of foreground colors.',
 'foreground_background_contrast': 'How strongly the foreground separates from its background.',
 'bbox_center_x': 'Horizontal center of the active bounding box in canvas coordinates.',
 'bbox_center_y': 'Vertical center of the active bounding box in canvas coordinates.',
 'bbox_width_ratio': 'Share of canvas width covered by the active bounding box.',
 'bbox_height_ratio': 'Share of canvas height covered by the active bounding box.',
 'circularity': 'How close the foreground silhouette is to a compact circle.',
 'rectangularity': 'How densely foreground fills its minimum enclosing rectangle.',
 'corner_count': 'Approximate number of polygon corners across external contours.',
 'curvature_histogram_straight': 'Share of contour samples that behave like straight segments.',
 'curvature_histogram_gentle': 'Share of contour samples with gradual curve behavior.',
 'curvature_histogram_sharp': 'Share of contour samples with sharp turns or angular corners.',
 'principal_axis_orientation': 'Dominant orientation of foreground pixels from a PCA axis; pairwise '
                               'comparison should treat it as circular over 180 degrees.',
 'arrowhead_count': 'Approximate count of triangular or sharp directional tips.',
 'arc_count': 'Approximate count of curved arc-like contour runs.',
 'stroke_width_mean': 'Average normalized stroke width estimated from the foreground skeleton.',
 'stroke_width_std': 'Variation in normalized stroke width across the skeleton.',
 'skeleton_endpoints': 'Number of terminal points in the foreground skeleton graph.',
 'skeleton_junctions': 'Number of branching points in the foreground skeleton graph.',
 'texture_entropy': 'Normalized grayscale entropy within foreground pixels.',
 'crush_test_stability': 'How well foreground shape survives one downsampling and re-expansion crush test.',
 'text_or_letter_presence': 'Heuristic score for letter-like or text-like visual structure.',
 'hu_moment_1': 'Advanced global silhouette descriptor; useful for shape matching but not directly '
                'human-readable on its own.',
 'hu_moment_2': 'Advanced global silhouette descriptor; useful for shape matching but not directly '
                'human-readable on its own.',
 'hu_moment_3': 'Advanced global silhouette descriptor; useful for shape matching but not directly '
                'human-readable on its own.',
 'hu_moment_4': 'Advanced global silhouette descriptor; useful for shape matching but not directly '
                'human-readable on its own.',
 'hu_moment_5': 'Advanced global silhouette descriptor; useful for shape matching but not directly '
                'human-readable on its own.',
 'hu_moment_6': 'Advanced global silhouette descriptor; useful for shape matching but not directly '
                'human-readable on its own.',
 'hu_moment_7': 'Advanced global silhouette descriptor; useful for shape matching but not directly '
                'human-readable on its own.',
 'hue_histogram_00': 'Share of saturated foreground pixels with hue between 0 and 30 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_01': 'Share of saturated foreground pixels with hue between 30 and 60 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_02': 'Share of saturated foreground pixels with hue between 60 and 90 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_03': 'Share of saturated foreground pixels with hue between 90 and 120 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_04': 'Share of saturated foreground pixels with hue between 120 and 150 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_05': 'Share of saturated foreground pixels with hue between 150 and 180 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_06': 'Share of saturated foreground pixels with hue between 180 and 210 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_07': 'Share of saturated foreground pixels with hue between 210 and 240 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_08': 'Share of saturated foreground pixels with hue between 240 and 270 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_09': 'Share of saturated foreground pixels with hue between 270 and 300 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_10': 'Share of saturated foreground pixels with hue between 300 and 330 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'hue_histogram_11': 'Share of saturated foreground pixels with hue between 330 and 360 degrees; hue is '
                     'circular, so neighboring bins wrap around at red.',
 'dominant_color_1_lab_l': 'Lab L channel for dominant foreground color 1.',
 'dominant_color_1_lab_a': 'Lab a channel for dominant foreground color 1.',
 'dominant_color_1_lab_b': 'Lab b channel for dominant foreground color 1.',
 'dominant_color_2_lab_l': 'Lab L channel for dominant foreground color 2.',
 'dominant_color_2_lab_a': 'Lab a channel for dominant foreground color 2.',
 'dominant_color_2_lab_b': 'Lab b channel for dominant foreground color 2.',
 'dominant_color_3_lab_l': 'Lab L channel for dominant foreground color 3.',
 'dominant_color_3_lab_a': 'Lab a channel for dominant foreground color 3.',
 'dominant_color_3_lab_b': 'Lab b channel for dominant foreground color 3.',
 'lbp_histogram_00': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_01': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_02': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_03': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_04': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_05': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_06': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_07': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_08': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'lbp_histogram_09': 'Uniform local binary pattern texture share; bin 9 stores non-uniform patterns.',
 'grid_foreground_0_0': 'Foreground share in the 4x4 layout grid at row 1, column 1.',
 'grid_foreground_0_1': 'Foreground share in the 4x4 layout grid at row 1, column 2.',
 'grid_foreground_0_2': 'Foreground share in the 4x4 layout grid at row 1, column 3.',
 'grid_foreground_0_3': 'Foreground share in the 4x4 layout grid at row 1, column 4.',
 'grid_foreground_1_0': 'Foreground share in the 4x4 layout grid at row 2, column 1.',
 'grid_foreground_1_1': 'Foreground share in the 4x4 layout grid at row 2, column 2.',
 'grid_foreground_1_2': 'Foreground share in the 4x4 layout grid at row 2, column 3.',
 'grid_foreground_1_3': 'Foreground share in the 4x4 layout grid at row 2, column 4.',
 'grid_foreground_2_0': 'Foreground share in the 4x4 layout grid at row 3, column 1.',
 'grid_foreground_2_1': 'Foreground share in the 4x4 layout grid at row 3, column 2.',
 'grid_foreground_2_2': 'Foreground share in the 4x4 layout grid at row 3, column 3.',
 'grid_foreground_2_3': 'Foreground share in the 4x4 layout grid at row 3, column 4.',
 'grid_foreground_3_0': 'Foreground share in the 4x4 layout grid at row 4, column 1.',
 'grid_foreground_3_1': 'Foreground share in the 4x4 layout grid at row 4, column 2.',
 'grid_foreground_3_2': 'Foreground share in the 4x4 layout grid at row 4, column 3.',
 'grid_foreground_3_3': 'Foreground share in the 4x4 layout grid at row 4, column 4.'}

_FEATURE_CATEGORY_REASONS = {'foreground_area_ratio': 'It belongs in Density/fill because it measures how much visible material '
                          'occupies the canvas.',
 'connected_components': 'It belongs in Complexity because separated foreground parts add visual '
                         'structure, while remaining a pixel-level grouping proxy.',
 'quadtree_leaf_count': 'It belongs in Complexity because more spatial subdivisions indicate more local '
                        'structural variation.',
 'quadtree_structural_variability': 'It belongs in Complexity because uneven spatial structure changes '
                                    'perceived visual detail.',
 'quadtree_mean_leaf_size': 'It belongs in Complexity because smaller regions indicate finer localized '
                            'detail.',
 'bounding_box_occupancy': 'It belongs in Density/fill because it measures how tightly the visible form '
                           'fills its active area.',
 'bounding_box_aspect_ratio': 'It belongs in Shape/silhouette because it captures whether the active form '
                              'is tall, wide, or square.',
 'solidity': 'It belongs in Shape/silhouette because compactness versus gaps changes the perceived '
             'silhouette.',
 'contour_count': 'It belongs in Complexity because multiple boundaries add visual detail and potential '
                  'parts.',
 'holes_count': 'It belongs in Complexity because enclosed empty regions add internal detail.',
 'closed_contour_ratio': 'It belongs in Shape/silhouette because it approximates whether the glyph behaves '
                         'like an enclosed form.',
 'is_monochrome': 'It belongs in Color/contrast because it marks whether color is unavailable as a visual '
                  'channel; 1 means monochrome.',
 'color_count': 'It belongs in Color because it measures how many distinct colors help distinguish the '
                'icon.',
 'mean_saturation': 'It belongs in Color because saturation describes how vivid or muted the icon colors '
                    'are.',
 'colorfulness': 'It belongs in Color because it summarizes overall color richness and variation.',
 'foreground_background_contrast': 'It belongs in Color because contrast describes foreground-background '
                                   'separation and legibility.',
 'canny_edge_density': 'It belongs in Complexity because edge load reflects visual detail and local '
                       'structure.',
 'perimeter_area_ratio': 'It belongs in Complexity because boundary-heavy icons often contain more contour '
                         'detail relative to area.',
 'filled_vs_outline_proxy': 'It belongs in Density/fill because it separates filled marks from '
                            'outline-like rendering.',
 'horizontal_symmetry': 'It belongs in Balance/layout because left-right symmetry affects visual balance.',
 'vertical_symmetry': 'It belongs in Balance/layout because top-bottom symmetry affects visual balance.',
 'line_orientation_0': 'It belongs in Stroke/structure because dominant horizontal strokes describe '
                       'internal direction.',
 'line_orientation_45': 'It belongs in Stroke/structure because diagonal strokes describe internal '
                        'direction.',
 'line_orientation_90': 'It belongs in Stroke/structure because vertical strokes describe internal '
                        'direction.',
 'line_orientation_135': 'It belongs in Stroke/structure because diagonal strokes describe internal '
                         'direction.',
 'centroid_distance_from_center': 'It belongs in Balance/layout because it measures where visual mass sits '
                                  'on the canvas.',
 'bbox_center_x': 'It belongs in Balance/layout because it records where the active shape sits '
                  'horizontally.',
 'bbox_center_y': 'It belongs in Balance/layout because it records where the active shape sits vertically.',
 'bbox_width_ratio': 'It belongs in Balance/layout because it measures how much horizontal canvas span the '
                     'icon uses.',
 'bbox_height_ratio': 'It belongs in Balance/layout because it measures how much vertical canvas span the '
                      'icon uses.',
 'circularity': 'It belongs in Shape/silhouette because roundness changes the perceived silhouette.',
 'rectangularity': 'It belongs in Shape/silhouette because box-like forms are a distinct shape family.',
 'corner_count': 'It belongs in Complexity because corners and polygon vertices add angular detail.',
 'curvature_histogram_straight': 'It belongs in Shape/silhouette because straight contour segments affect '
                                 'perceived geometry.',
 'curvature_histogram_gentle': 'It belongs in Shape/silhouette because arcs and gentle curves affect '
                               'perceived geometry.',
 'curvature_histogram_sharp': 'It belongs in Shape/silhouette because sharp turns mark angular geometry.',
 'principal_axis_orientation': "It belongs in Stroke/structure because it captures the icon's dominant "
                               'visual direction.',
 'arrowhead_count': 'It belongs in Stroke/structure because arrowheads are visible direction cues.',
 'arc_count': 'It belongs in Stroke/structure because arcs distinguish curved line construction.',
 'stroke_width_mean': 'It belongs in Density/fill because line thickness changes visual weight.',
 'stroke_width_std': 'It belongs in Density/fill because stroke-width variation changes visual weight and '
                     'fill behavior.',
 'skeleton_endpoints': 'It belongs in Stroke/structure because endpoints describe line-graph structure.',
 'skeleton_junctions': 'It belongs in Stroke/structure because junctions describe branching line-graph '
                       'structure.',
 'texture_entropy': 'It belongs in Texture because entropy measures internal tonal variation.',
 'crush_test_stability': 'Excluded from active visual-family mapping because it measures processing '
                         'robustness rather than a direct visible identification feature.',
 'text_or_letter_presence': 'Excluded from active visual-family mapping because the current heuristic is '
                            'too indirect for reliable glyph-identification claims.',
 'hu_moment_1': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_2': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_3': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_4': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_5': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_6': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_7': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hue_histogram_00': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_01': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_02': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_03': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_04': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_05': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_06': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_07': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_08': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_09': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_10': 'It belongs in Color because hue bins represent color-family channels.',
 'hue_histogram_11': 'It belongs in Color because hue bins represent color-family channels.',
 'dominant_color_1_lab_l': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_1_lab_a': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_1_lab_b': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_2_lab_l': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_2_lab_a': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_2_lab_b': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_3_lab_l': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_3_lab_a': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'dominant_color_3_lab_b': 'It belongs in Color because dominant Lab values encode foreground color '
                           'appearance.',
 'lbp_histogram_00': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_01': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_02': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_03': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_04': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_05': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_06': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_07': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_08': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_09': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'grid_foreground_0_0': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_0_1': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_0_2': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_0_3': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_1_0': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_1_1': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_1_2': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_1_3': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_2_0': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_2_1': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_2_2': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_2_3': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_3_0': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_3_1': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_3_2': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.',
 'grid_foreground_3_3': 'It belongs in Balance/layout because it records where foreground mass appears in '
                        'the icon grid.'}

_FEATURE_VISUAL_CATEGORIZATIONS = {'foreground_area_ratio': ['Sparse vs dense'],
 'canny_edge_density': ['Simple vs complex'],
 'connected_components': ['Single-object vs multi-part'],
 'quadtree_leaf_count': ['Simple vs complex'],
 'quadtree_structural_variability': ['Simple vs complex'],
 'quadtree_mean_leaf_size': ['Simple vs complex'],
 'bounding_box_occupancy': ['Sparse vs dense'],
 'bounding_box_aspect_ratio': ['Compact vs spread-out'],
 'solidity': ['Compact vs spread-out'],
 'centroid_distance_from_center': ['Centered vs off-center'],
 'horizontal_symmetry': ['Balanced vs unbalanced'],
 'vertical_symmetry': ['Balanced vs unbalanced'],
 'perimeter_area_ratio': ['Filled vs outline'],
 'filled_vs_outline_proxy': ['Filled vs outline'],
 'contour_count': ['Single-object vs multi-part'],
 'holes_count': ['Open vs closed shape'],
 'closed_contour_ratio': ['Open vs closed shape'],
 'line_orientation_0': ['Directional/geometric structure'],
 'line_orientation_45': ['Directional/geometric structure'],
 'line_orientation_90': ['Directional/geometric structure'],
 'line_orientation_135': ['Directional/geometric structure'],
 'is_monochrome': ['Black-and-white vs colored'],
 'color_count': ['Black-and-white vs colored'],
 'mean_saturation': ['Color intensity/style'],
 'colorfulness': ['Color intensity/style'],
 'foreground_background_contrast': ['High contrast vs low contrast'],
 'bbox_center_x': ['Spatial layout similarity'],
 'bbox_center_y': ['Spatial layout similarity'],
 'bbox_width_ratio': ['Spatial layout similarity'],
 'bbox_height_ratio': ['Spatial layout similarity'],
 'circularity': ['Round vs rectangular'],
 'rectangularity': ['Round vs rectangular'],
 'corner_count': ['Curved vs angular'],
 'curvature_histogram_straight': ['Curved vs angular'],
 'curvature_histogram_gentle': ['Curved vs angular'],
 'curvature_histogram_sharp': ['Curved vs angular'],
 'principal_axis_orientation': ['Directional/geometric structure'],
 'arrowhead_count': ['Arrow/directional symbol'],
 'arc_count': ['Curved vs angular'],
 'stroke_width_mean': ['Thin vs thick strokes'],
 'stroke_width_std': ['Thin vs thick strokes'],
 'skeleton_endpoints': ['Skeleton graph complexity'],
 'skeleton_junctions': ['Skeleton graph complexity'],
 'texture_entropy': ['Texture/pattern'],
 'crush_test_stability': [],
 'text_or_letter_presence': [],
 'hu_moment_1': [],
 'hu_moment_2': [],
 'hu_moment_3': [],
 'hu_moment_4': [],
 'hu_moment_5': [],
 'hu_moment_6': [],
 'hu_moment_7': [],
 'hue_histogram_00': ['Hue/color family'],
 'hue_histogram_01': ['Hue/color family'],
 'hue_histogram_02': ['Hue/color family'],
 'hue_histogram_03': ['Hue/color family'],
 'hue_histogram_04': ['Hue/color family'],
 'hue_histogram_05': ['Hue/color family'],
 'hue_histogram_06': ['Hue/color family'],
 'hue_histogram_07': ['Hue/color family'],
 'hue_histogram_08': ['Hue/color family'],
 'hue_histogram_09': ['Hue/color family'],
 'hue_histogram_10': ['Hue/color family'],
 'hue_histogram_11': ['Hue/color family'],
 'dominant_color_1_lab_l': ['Hue/color family'],
 'dominant_color_1_lab_a': ['Hue/color family'],
 'dominant_color_1_lab_b': ['Hue/color family'],
 'dominant_color_2_lab_l': ['Hue/color family'],
 'dominant_color_2_lab_a': ['Hue/color family'],
 'dominant_color_2_lab_b': ['Hue/color family'],
 'dominant_color_3_lab_l': ['Hue/color family'],
 'dominant_color_3_lab_a': ['Hue/color family'],
 'dominant_color_3_lab_b': ['Hue/color family'],
 'lbp_histogram_00': [],
 'lbp_histogram_01': [],
 'lbp_histogram_02': [],
 'lbp_histogram_03': [],
 'lbp_histogram_04': [],
 'lbp_histogram_05': [],
 'lbp_histogram_06': [],
 'lbp_histogram_07': [],
 'lbp_histogram_08': [],
 'lbp_histogram_09': [],
 'grid_foreground_0_0': ['Spatial layout similarity'],
 'grid_foreground_0_1': ['Spatial layout similarity'],
 'grid_foreground_0_2': ['Spatial layout similarity'],
 'grid_foreground_0_3': ['Spatial layout similarity'],
 'grid_foreground_1_0': ['Spatial layout similarity'],
 'grid_foreground_1_1': ['Spatial layout similarity'],
 'grid_foreground_1_2': ['Spatial layout similarity'],
 'grid_foreground_1_3': ['Spatial layout similarity'],
 'grid_foreground_2_0': ['Spatial layout similarity'],
 'grid_foreground_2_1': ['Spatial layout similarity'],
 'grid_foreground_2_2': ['Spatial layout similarity'],
 'grid_foreground_2_3': ['Spatial layout similarity'],
 'grid_foreground_3_0': ['Spatial layout similarity'],
 'grid_foreground_3_1': ['Spatial layout similarity'],
 'grid_foreground_3_2': ['Spatial layout similarity'],
 'grid_foreground_3_3': ['Spatial layout similarity']}

_FEATURE_VISUAL_CATEGORY_LABELS = {'Sparse vs dense': 'sparse icon, dense icon',
 'Simple vs complex': 'simple icon, complex icon',
 'Single-object vs multi-part': 'single-object symbol, multi-component symbol',
 'Compact vs spread-out': 'compact icon, tall icon, wide icon, fragmented icon',
 'Round vs rectangular': 'round icon, rectangular icon, box-like icon',
 'Curved vs angular': 'curved icon, angular icon, sharp-cornered icon',
 'Centered vs off-center': 'centered icon, off-center icon',
 'Balanced vs unbalanced': 'symmetric icon, asymmetric icon',
 'Filled vs outline': 'filled pictogram, outline icon, line icon',
 'Open vs closed shape': 'closed-shape icon, open-line icon',
 'Directional/geometric structure': 'horizontal icon, vertical icon, diagonal/action icon',
 'Arrow/directional symbol': 'arrow icon, pointer icon, directional symbol',
 'Black-and-white vs colored': 'monochrome icon, colored icon',
 'Hue/color family': 'red icon, green icon, blue icon, multicolor icon',
 'Color intensity/style': 'muted icon, vivid icon, emoji-like icon',
 'High contrast vs low contrast': 'high-contrast icon, low-contrast icon',
 'Thin vs thick strokes': 'thin-line icon, thick-stroke icon',
 'Skeleton graph complexity': 'simple line graph, branching line graph',
 'Texture/pattern': 'flat icon, textured icon, hatched icon',
 'Resolution robustness': 'small-size robust icon, fragile detailed icon',
 'Text-like mark': 'letter icon, text-like symbol',
 'Spatial layout similarity': 'top-heavy icon, left-heavy icon, central icon',
 'Global silhouette descriptor': 'global-shape descriptor, advanced silhouette profile'}

_EXCLUDED_FEATURE_REASONS = {'hu_moment_1': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_2': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_3': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_4': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_5': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_6': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'hu_moment_7': 'Excluded from active visual-family mapping because Hu moments are useful for machine '
                'shape matching but do not map cleanly to an interpretable human perception cue.',
 'lbp_histogram_00': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_01': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_02': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_03': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_04': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_05': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_06': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_07': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_08': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'lbp_histogram_09': 'Excluded from active visual-family mapping because local binary patterns often '
                     'capture antialiasing/rendering artifacts in flat vector icons.',
 'text_or_letter_presence': 'Excluded from active visual-family mapping because the current heuristic is '
                            'too indirect for reliable glyph-identification claims.',
 'crush_test_stability': 'Excluded from active visual-family mapping because it measures processing '
                         'robustness rather than a direct visible identification feature.',
 'quadtree_structural_variability': 'Deprecated schema-v1 representative retained only for '
                                    'reproducibility; active analysis uses the versioned v2 replacement.',
 'closed_contour_ratio': 'Deprecated schema-v1 representative retained only for reproducibility; active '
                         'analysis uses the versioned v2 replacement.',
 'principal_axis_orientation': 'Deprecated schema-v1 representative retained only for reproducibility; '
                               'active analysis uses the versioned v2 replacement.',
 'filled_vs_outline_proxy': 'Deprecated schema-v1 representative retained only for reproducibility; active '
                            'analysis uses the versioned v2 replacement.',
 'horizontal_symmetry': 'Deprecated schema-v1 representative retained only for reproducibility; active '
                        'analysis uses the versioned v2 replacement.',
 'mean_saturation': 'Deprecated schema-v1 representative retained only for reproducibility; active '
                    'analysis uses the versioned v2 replacement.',
 'texture_entropy': 'Deprecated schema-v1 representative retained only for reproducibility; active '
                    'analysis uses the versioned v2 replacement.',
 'orientation_confidence_v2': 'Auxiliary confidence channel used to define whether the v2 orientation is '
                              'meaningful; it is not an independent family feature.',
 'red_pixel_ratio_v2': 'Auxiliary cohort diagnostic used by the strict-red classifier, not an active '
                       'family feature.',
 'strict_red_flag_v2': 'Auxiliary dashboard cohort flag, not an active family feature.'}

_LEGACY_BENCHMARK_ALIASES = {'complexity': 'complexity',
 'shape': 'closure',
 'structure': 'orientation',
 'density_fill': 'fill',
 'balance_layout': 'symmetry',
 'color_contrast': 'saturation',
 'texture': 'texture'}

_AUXILIARY_FEATURE_IDS = frozenset({
    "orientation_confidence_v2",
    "red_pixel_ratio_v2",
    "strict_red_flag_v2",
})
_DEPRECATED_FEATURE_IDS = frozenset({
    "quadtree_structural_variability",
    "closed_contour_ratio",
    "principal_axis_orientation",
    "filled_vs_outline_proxy",
    "horizontal_symmetry",
    "mean_saturation",
    "texture_entropy",
})


def _build_family_specs() -> tuple[FamilySpec, ...]:
    return tuple(
        FamilySpec(
            id=str(item["id"]),
            title=str(item["title"]),
            description=str(item["description"]),
            human_category=str(item.get("human_category", item["title"])),
            family_summary=str(item.get("family_summary", "")),
            perception=str(item.get("perception", "")),
            low_value=str(item.get("low_value", "")),
            high_value=str(item.get("high_value", "")),
            feature_ids=tuple(item["feature_ids"]),
            representative_feature_id=str(item["representative_feature_id"]),
            representative_interpretation=str(item.get("representative_interpretation", "")),
            representative_rationale=str(item.get("representative_rationale", "")),
            representative_evidence=str(item.get("representative_evidence", "")),
            representative_citation=str(item.get("representative_citation", "")),
            benchmark_family_id=_LEGACY_BENCHMARK_ALIASES[str(item["id"])],
            visible=bool(item.get("visible", True)),
        )
        for item in _FAMILY_DATA
    )


FAMILY_SPECS = _build_family_specs()
_FAMILY_BY_ID = MappingProxyType({family.id: family for family in FAMILY_SPECS})
_ACTIVE_FAMILY_BY_FEATURE = {
    feature_id: family.id
    for family in FAMILY_SPECS
    for feature_id in family.feature_ids
}
_ANALYSIS_FEATURE_PRESETS = MappingProxyType(
    {
        "representatives": tuple(
            family.representative_feature_id for family in FAMILY_SPECS
        ),
        "full_registry": tuple(
            feature_id for family in FAMILY_SPECS for feature_id in family.feature_ids
        ),
    }
)


def _feature_status(feature_id: str) -> FeatureStatus:
    if feature_id in _ACTIVE_FAMILY_BY_FEATURE:
        return FeatureStatus.ACTIVE
    if feature_id in _AUXILIARY_FEATURE_IDS:
        return FeatureStatus.AUXILIARY
    if feature_id in _DEPRECATED_FEATURE_IDS:
        return FeatureStatus.DEPRECATED
    return FeatureStatus.EXCLUDED


def _build_feature_specs() -> tuple[FeatureSpec, ...]:
    specs = []
    for feature_id in RAW_FEATURE_IDS:
        evidence_scope, evidence, citation = _FEATURE_EVIDENCE_DATA.get(
            feature_id,
            (EvidenceScope.NONE, "", ""),
        )
        specs.append(
            FeatureSpec(
                id=feature_id,
                label=_FEATURE_LABELS.get(feature_id, feature_id.replace("_", " ").title()),
                meaning=_FEATURE_MEANINGS.get(feature_id, "Extracted visual feature."),
                family_id=_ACTIVE_FAMILY_BY_FEATURE.get(feature_id),
                status=_feature_status(feature_id),
                exclusion_reason=_EXCLUDED_FEATURE_REASONS.get(feature_id, ""),
                category_reason=_FEATURE_CATEGORY_REASONS.get(feature_id, ""),
                visual_categorizations=tuple(_FEATURE_VISUAL_CATEGORIZATIONS.get(feature_id, ())),
                evidence_scope=evidence_scope,
                evidence=evidence,
                citation=citation,
            )
        )
    return tuple(specs)


FEATURE_SPECS = _build_feature_specs()
_FEATURE_BY_ID = MappingProxyType({feature.id: feature for feature in FEATURE_SPECS})
_EXCLUDED_REASONS_VIEW = MappingProxyType(dict(_EXCLUDED_FEATURE_REASONS))
_FEATURE_LABELS_VIEW = MappingProxyType(dict(_FEATURE_LABELS))
_FEATURE_MEANINGS_VIEW = MappingProxyType(dict(_FEATURE_MEANINGS))
_FEATURE_CATEGORY_REASONS_VIEW = MappingProxyType(dict(_FEATURE_CATEGORY_REASONS))
_FEATURE_EVIDENCE_VIEW = MappingProxyType(
    {feature.id: feature.evidence for feature in FEATURE_SPECS if feature.evidence}
)
_FEATURE_CITATIONS_VIEW = MappingProxyType(
    {feature.id: feature.citation for feature in FEATURE_SPECS if feature.citation}
)
_FEATURE_VISUAL_CATEGORIZATIONS_VIEW = MappingProxyType(
    {key: tuple(value) for key, value in _FEATURE_VISUAL_CATEGORIZATIONS.items()}
)
_FEATURE_VISUAL_CATEGORY_LABELS_VIEW = MappingProxyType(dict(_FEATURE_VISUAL_CATEGORY_LABELS))


def raw_feature_ids() -> tuple[str, ...]:
    return RAW_FEATURE_IDS


def active_feature_ids() -> tuple[str, ...]:
    return tuple(feature_id for family in FAMILY_SPECS for feature_id in family.feature_ids)


def analysis_feature_presets() -> Mapping[str, tuple[str, ...]]:
    return _ANALYSIS_FEATURE_PRESETS


def analysis_feature_ids(preset: str | None = None) -> tuple[str, ...]:
    return _ANALYSIS_FEATURE_PRESETS[preset or ANALYSIS_FEATURE_PRESET]


def analysis_feature_groups(preset: str | None = None) -> tuple[tuple[str, ...], ...]:
    selected = frozenset(analysis_feature_ids(preset))
    return tuple(
        tuple(feature_id for feature_id in family.feature_ids if feature_id in selected)
        for family in FAMILY_SPECS
        if any(feature_id in selected for feature_id in family.feature_ids)
    )


def excluded_feature_ids() -> tuple[str, ...]:
    return tuple(feature.id for feature in FEATURE_SPECS if feature.status is not FeatureStatus.ACTIVE)


def auxiliary_feature_ids() -> tuple[str, ...]:
    return tuple(feature.id for feature in FEATURE_SPECS if feature.status is FeatureStatus.AUXILIARY)


def deprecated_feature_ids() -> tuple[str, ...]:
    return tuple(feature.id for feature in FEATURE_SPECS if feature.status is FeatureStatus.DEPRECATED)


def family_specs() -> tuple[FamilySpec, ...]:
    return FAMILY_SPECS


def feature_specs() -> tuple[FeatureSpec, ...]:
    return FEATURE_SPECS


def family_spec(family_id: str) -> FamilySpec:
    return _FAMILY_BY_ID[family_id]


def feature_spec(feature_id: str) -> FeatureSpec:
    return _FEATURE_BY_ID[feature_id]


def feature_groups() -> tuple[tuple[str, ...], ...]:
    return tuple(family.feature_ids for family in FAMILY_SPECS)


def representative_feature_ids() -> tuple[str, ...]:
    return tuple(family.representative_feature_id for family in FAMILY_SPECS)


def benchmark_family_features() -> Mapping[str, str]:
    return MappingProxyType(
        {family.benchmark_family_id: family.representative_feature_id for family in FAMILY_SPECS}
    )


def excluded_feature_reasons() -> Mapping[str, str]:
    return _EXCLUDED_REASONS_VIEW


def feature_labels() -> Mapping[str, str]:
    return _FEATURE_LABELS_VIEW


def feature_meanings() -> Mapping[str, str]:
    return _FEATURE_MEANINGS_VIEW


def feature_category_reasons() -> Mapping[str, str]:
    return _FEATURE_CATEGORY_REASONS_VIEW


def feature_evidence() -> Mapping[str, str]:
    return _FEATURE_EVIDENCE_VIEW


def feature_citations() -> Mapping[str, str]:
    return _FEATURE_CITATIONS_VIEW


def feature_visual_categorizations() -> Mapping[str, tuple[str, ...]]:
    return _FEATURE_VISUAL_CATEGORIZATIONS_VIEW


def feature_visual_category_labels() -> Mapping[str, str]:
    return _FEATURE_VISUAL_CATEGORY_LABELS_VIEW


def dashboard_sections() -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    for family in FAMILY_SPECS:
        features = []
        for feature_id in family.feature_ids:
            feature = feature_spec(feature_id)
            visual_categories = list(feature.visual_categorizations)
            features.append(
                {
                    "id": feature.id,
                    "label": feature.label,
                    "group": family.id,
                    "group_title": family.title,
                    "meaning": feature.meaning,
                    "visual_categorizations": visual_categories,
                    "visual_category_labels": [
                        _FEATURE_VISUAL_CATEGORY_LABELS[category]
                        for category in visual_categories
                        if category in _FEATURE_VISUAL_CATEGORY_LABELS
                    ],
                    "category_reason": feature.category_reason
                    or f"It belongs in {family.title} because it describes that visual channel.",
                    "evidence_scope": feature.evidence_scope.value,
                    "evidence": feature.evidence,
                    "citation": feature.citation,
                }
            )
        representative = next(
            feature for feature in features if feature["id"] == family.representative_feature_id
        )
        sections.append(
            {
                "id": family.id,
                "title": family.title,
                "description": family.description,
                "human_category": family.human_category,
                "family_summary": family.family_summary,
                "perception": family.perception,
                "low_value": family.low_value,
                "high_value": family.high_value,
                "visible": family.visible,
                "features": features,
                "representative_feature_id": family.representative_feature_id,
                "representative_feature": representative,
                "representative_interpretation": family.representative_interpretation,
                "representative_rationale": family.representative_rationale,
                "representative_evidence": family.representative_evidence,
                "representative_citation": family.representative_citation,
            }
        )
    return sections


def validate_registry(extractor_columns: Sequence[str] | None = None) -> None:
    raw = raw_feature_ids()
    active = active_feature_ids()
    excluded = excluded_feature_ids()
    if len(raw) != len(set(raw)):
        raise ValueError("Feature registry contains duplicate raw feature IDs")
    if len(FAMILY_SPECS) != 7:
        raise ValueError(f"Expected seven feature families, found {len(FAMILY_SPECS)}")
    if len(active) != len(set(active)):
        raise ValueError("An active feature belongs to more than one family")
    if set(raw) != set(active) | set(excluded) or set(active) & set(excluded):
        raise ValueError("Active and non-active features do not partition the raw registry")
    if set(_EXCLUDED_FEATURE_REASONS) != set(excluded):
        raise ValueError("Every non-active feature must have exactly one exclusion reason")
    if set(_FEATURE_EVIDENCE_DATA) != set(active):
        raise ValueError("Every active feature must have exactly one literature-evidence entry")
    if ANALYSIS_FEATURE_PRESET not in _ANALYSIS_FEATURE_PRESETS:
        raise ValueError(f"Unknown analysis feature preset {ANALYSIS_FEATURE_PRESET!r}")
    for preset_id, feature_ids in _ANALYSIS_FEATURE_PRESETS.items():
        if not feature_ids:
            raise ValueError(f"Analysis feature preset {preset_id!r} is empty")
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError(f"Analysis feature preset {preset_id!r} contains duplicates")
        if not set(feature_ids).issubset(active):
            raise ValueError(f"Analysis feature preset {preset_id!r} contains non-active features")
    if analysis_feature_ids("representatives") != representative_feature_ids():
        raise ValueError("Representative analysis preset must match configured family representatives")
    for family in FAMILY_SPECS:
        if family.representative_feature_id not in family.feature_ids:
            raise ValueError(
                f"Representative {family.representative_feature_id!r} is not in family {family.id!r}"
            )
    for feature_id in active:
        feature = feature_spec(feature_id)
        if (
            feature.evidence_scope is EvidenceScope.NONE
            or not feature.evidence
            or not feature.citation
        ):
            raise ValueError(f"Active feature {feature_id!r} lacks literature evidence metadata")
    if extractor_columns is not None and tuple(extractor_columns) != raw:
        raise ValueError("Extractor feature columns do not match the authoritative registry order")


validate_registry()
