#!/usr/bin/env python3
"""Build Analysis clustering data and a static Plotly dashboard."""

from __future__ import annotations

import csv
import html
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import build_clustering_metadata_sample as metadata_helpers
import extract_icon_features
from thesis_pipeline.dashboard.feature_selection import select_strong_family_features


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "icon_data" / "analysis"
DATASET_PATH = ANALYSIS_DIR / "dataset.csv"
FEATURES_PATH = ANALYSIS_DIR / "features.csv"
OUTPUT_DIR = ANALYSIS_DIR / "analysis_dashboard"
ASSETS_DIR = OUTPUT_DIR / "assets"
PLOTLY_ASSET = ASSETS_DIR / "plotly.min.js"

PER_SET_SAMPLE_SIZE = 10
K_VALUES = (3, 5, 7, 10)
PRIMARY_K = 7
RANDOM_SEED = 42

METADATA_COLUMNS = [
    "icon_id",
    "set_id",
    "set_name",
    "icon_name",
    "label",
    "source",
    "source_url",
    "format",
    "filename",
    "relative_path",
    "normalized_path",
    "notes",
    "metadata_text",
    "metadata_tokens",
    "has_notes",
    "source_path_exists",
    "normalized_path_exists",
]

IMAGE_FEATURE_COLUMNS = list(extract_icon_features.FEATURE_COLUMNS)

GRID_FEATURE_COLUMNS = [f"grid_foreground_{row}_{col}" for row in range(4) for col in range(4)]
EXCLUDED_IMAGE_FEATURES = {
    *(f"hu_moment_{index}" for index in range(1, 8)),
    *(f"lbp_histogram_{index:02d}" for index in range(10)),
    "text_or_letter_presence",
    "crush_test_stability",
}
EXCLUDED_IMAGE_FEATURE_REASONS = {
    **{
        f"hu_moment_{index}": "Excluded from active visual-family mapping because Hu moments are useful for machine shape matching but do not map cleanly to an interpretable human perception cue."
        for index in range(1, 8)
    },
    **{
        f"lbp_histogram_{index:02d}": "Excluded from active visual-family mapping because local binary patterns often capture antialiasing/rendering artifacts in flat vector icons."
        for index in range(10)
    },
    "text_or_letter_presence": "Excluded from active visual-family mapping because the current heuristic is too indirect for reliable glyph-identification claims.",
    "crush_test_stability": "Excluded from active visual-family mapping because it measures processing robustness rather than a direct visible identification feature.",
}

DASHBOARD_FEATURE_SECTIONS = [
    {
        "id": "complexity",
        "title": "Complexity",
        "description": "Detail load, structural subdivision, component count, contour count, holes, perimeter load, and angular point count.",
        "human_category": "Complexity",
        "family_summary": "edge density, perimeter/area, quadtree variability, components, contours, holes",
        "perception": "This family approximates how visually busy or effortful a glyph is to parse. Component and contour counts are pixel-level proxies; human grouping can still differ.",
        "low_value": "Lower values usually mean a simpler, cleaner symbol with fewer parts, edges, holes, or sharp details.",
        "high_value": "Higher values usually mean a more intricate symbol that may take more attention to inspect and distinguish.",
        "feature_ids": [
            "canny_edge_density",
            "quadtree_leaf_count",
            "quadtree_structural_variability",
            "quadtree_mean_leaf_size",
            "connected_components",
            "contour_count",
            "holes_count",
            "perimeter_area_ratio",
            "corner_count",
        ],
    },
    {
        "id": "shape",
        "title": "Shape/silhouette",
        "description": "Silhouette, closure, roundness, rectangularity, and curvature.",
        "human_category": "Shape/silhouette",
        "family_summary": "aspect ratio, solidity, closure proxy, circularity/rectangularity, curvature",
        "perception": "This family captures the overall visible form of a glyph: roundness, box-like form, elongation, closure, curvature, and global silhouette.",
        "low_value": "Lower values depend on the feature: low circularity means less round, and low closure-proxy values suggest more open or line-like form.",
        "high_value": "Higher values indicate stronger presence of that specific shape property, such as more circular, more rectangular, or more closed by proxy.",
        "feature_ids": [
            "bounding_box_aspect_ratio",
            "solidity",
            "closed_contour_ratio",
            "circularity",
            "rectangularity",
            "curvature_histogram_straight",
            "curvature_histogram_gentle",
            "curvature_histogram_sharp",
        ],
    },
    {
        "id": "structure",
        "title": "Stroke/structure",
        "description": "Directional strokes, principal orientation, arrows, arcs, and skeleton graph structure.",
        "human_category": "Stroke/structure",
        "family_summary": "line orientation, principal axis, arrows, arcs, skeleton graph",
        "perception": "This family captures internal organization: stroke direction, branching, endpoints, arrows, and arcs. It describes visible structure, not exact text or semantic identity.",
        "low_value": "Lower values usually mean less explicit directionality, fewer skeleton branches/endpoints, or fewer arrows/arcs.",
        "high_value": "Higher values usually mean stronger directional cues, more branching structure, more endpoints/junctions, or clearer arrow components.",
        "feature_ids": [
            "line_orientation_0",
            "line_orientation_45",
            "line_orientation_90",
            "line_orientation_135",
            "principal_axis_orientation",
            "arrowhead_count",
            "arc_count",
            "skeleton_endpoints",
            "skeleton_junctions",
        ],
    },
    {
        "id": "density_fill",
        "title": "Density/fill",
        "description": "Foreground amount, bounding-box fill, outline-vs-fill behavior, and stroke thickness.",
        "human_category": "Density/fill",
        "family_summary": "foreground amount, bounding-box occupancy, filled/outline proxy, stroke width",
        "perception": "This family describes whether a glyph reads as sparse line art, a filled silhouette, or a heavy/thick mark.",
        "low_value": "Lower values usually mean a lighter, thinner, more open, or less filled glyph.",
        "high_value": "Higher values usually mean a denser, more filled, more visually heavy glyph with thicker strokes or stronger occupancy.",
        "feature_ids": [
            "foreground_area_ratio",
            "bounding_box_occupancy",
            "filled_vs_outline_proxy",
            "stroke_width_mean",
            "stroke_width_std",
        ],
    },
    {
        "id": "balance_layout",
        "title": "Balance/layout",
        "description": "Centering, symmetry, active bounding-box position/size, and 4x4 foreground grid layout.",
        "human_category": "Balance/layout",
        "family_summary": "symmetry, centroid, bounding-box position/size, 4x4 grid occupancy",
        "perception": "This family captures where visual mass sits and whether the glyph feels centered, balanced, symmetric, top-heavy, side-heavy, compact, or spread out. Grid features should be treated as one layout channel when comparing families.",
        "low_value": "Lower values often mean less offset or less occupancy in a given region; for symmetry scores, lower means less balanced.",
        "high_value": "Higher values often mean stronger occupancy in a region, larger active extent, more offset for distance features, or stronger balance for symmetry scores.",
        "feature_ids": [
            "centroid_distance_from_center",
            "horizontal_symmetry",
            "vertical_symmetry",
            "bbox_center_x",
            "bbox_center_y",
            "bbox_width_ratio",
            "bbox_height_ratio",
            *GRID_FEATURE_COLUMNS,
        ],
    },
    {
        "id": "color_contrast",
        "title": "Color/contrast",
        "description": "Color presence, saturation, colorfulness, foreground-background contrast, hue distribution, and dominant Lab colors.",
        "human_category": "Color/contrast",
        "family_summary": "monochrome flag, color count, saturation, colorfulness, foreground-background contrast, hue histogram, dominant Lab colors",
        "perception": "This family captures color channels humans use for quick grouping, salience, and foreground-background separation.",
        "low_value": "Lower values usually mean less saturation/colorfulness, weaker contrast, or less presence of a given hue bin. For `is_monochrome`, lower means color is present.",
        "high_value": "Higher values usually mean stronger signal for that specific color feature. For `is_monochrome`, higher means grayscale/monochrome rather than more color.",
        "feature_ids": [
            "is_monochrome",
            "color_count",
            "mean_saturation",
            "colorfulness",
            "foreground_background_contrast",
            *(f"hue_histogram_{index:02d}" for index in range(12)),
            "dominant_color_1_lab_l",
            "dominant_color_1_lab_a",
            "dominant_color_1_lab_b",
            "dominant_color_2_lab_l",
            "dominant_color_2_lab_a",
            "dominant_color_2_lab_b",
            "dominant_color_3_lab_l",
            "dominant_color_3_lab_a",
            "dominant_color_3_lab_b",
        ],
    },
    {
        "id": "texture",
        "title": "Texture",
        "description": "Foreground tonal entropy and the spatial scale of fine versus coarse intensity structure.",
        "human_category": "Texture",
        "family_summary": "tonal entropy and Tamura spatial coarseness",
        "perception": "Entropy captures how varied foreground tones are, while Tamura coarseness captures whether intensity structure is composed of fine/repeated or large/simple elements. Artifact-prone local binary pattern bins are excluded from the active visual-family mapping.",
        "low_value": "Lower entropy means more uniform tones; lower coarseness means finer or more frequently repeated intensity structure.",
        "high_value": "Higher entropy means more tonal variation; higher coarseness means larger, simpler intensity elements.",
        "feature_ids": [
            "texture_entropy",
            "texture_coarseness",
        ],
    },
]

FEATURE_LABELS = {
    "foreground_area_ratio": "Foreground area ratio",
    "canny_edge_density": "Edge density",
    "connected_components": "Connected components",
    "quadtree_leaf_count": "Quadtree leaf count",
    "quadtree_structural_variability": "Quadtree structural variability",
    "quadtree_mean_leaf_size": "Quadtree mean leaf size",
    "bounding_box_occupancy": "Bounding-box occupancy",
    "bounding_box_aspect_ratio": "Bounding-box aspect ratio",
    "solidity": "Solidity",
    "centroid_distance_from_center": "Center offset",
    "horizontal_symmetry": "Horizontal symmetry",
    "vertical_symmetry": "Vertical symmetry",
    "perimeter_area_ratio": "Perimeter-area ratio",
    "filled_vs_outline_proxy": "Filled-vs-outline proxy",
    "contour_count": "Contour count",
    "holes_count": "Holes count",
    "closed_contour_ratio": "Closure proxy",
    "line_orientation_0": "Horizontal line orientation",
    "line_orientation_45": "Diagonal 45 degree orientation",
    "line_orientation_90": "Vertical line orientation",
    "line_orientation_135": "Diagonal 135 degree orientation",
    "is_monochrome": "Monochrome flag",
    "color_count": "Color count",
    "mean_saturation": "Mean saturation",
    "colorfulness": "Colorfulness",
    "foreground_background_contrast": "Foreground-background contrast",
}

FEATURE_MEANINGS = {
    "foreground_area_ratio": "How much of the canvas is occupied by visible foreground pixels.",
    "canny_edge_density": "How much edge/detail structure appears in the icon.",
    "connected_components": "How many separated foreground parts the icon contains.",
    "quadtree_leaf_count": "How many spatial subdivisions are needed to describe the foreground pattern.",
    "quadtree_structural_variability": "How unevenly structure is distributed across the icon.",
    "quadtree_mean_leaf_size": "Average quadtree region size; smaller values imply more localized detail.",
    "bounding_box_occupancy": "How densely the icon fills its active bounding box.",
    "bounding_box_aspect_ratio": "Whether the active icon shape is tall, wide, or square-like.",
    "solidity": "How compactly the foreground fills its outer convex envelope.",
    "centroid_distance_from_center": "How far the icon's visual mass is from the canvas center.",
    "horizontal_symmetry": "How balanced the icon is across the left-right axis.",
    "vertical_symmetry": "How balanced the icon is across the top-bottom axis.",
    "perimeter_area_ratio": "How much boundary length exists relative to filled area.",
    "filled_vs_outline_proxy": "Whether the icon behaves more like a filled mark or an outline/line drawing.",
    "contour_count": "How many contour boundaries are present.",
    "holes_count": "How many enclosed empty spaces appear inside foreground shapes.",
    "closed_contour_ratio": "Proxy for closed-shape behavior from contours, holes, and compactness; not a direct human closure judgment.",
    "line_orientation_0": "Share of detected line structure that is mostly horizontal.",
    "line_orientation_45": "Share of detected line structure that follows a 45 degree diagonal.",
    "line_orientation_90": "Share of detected line structure that is mostly vertical.",
    "line_orientation_135": "Share of detected line structure that follows a 135 degree diagonal.",
    "is_monochrome": "Whether the icon is effectively black-and-white or grayscale.",
    "color_count": "Approximate number of distinct foreground colors.",
    "mean_saturation": "Average foreground color saturation.",
    "colorfulness": "Overall richness and variation of foreground colors.",
    "foreground_background_contrast": "How strongly the foreground separates from its background.",
}

FEATURE_CATEGORY_REASONS = {
    "foreground_area_ratio": "It belongs in Density/fill because it measures how much visible material occupies the canvas.",
    "connected_components": "It belongs in Complexity because separated foreground parts add visual structure, while remaining a pixel-level grouping proxy.",
    "quadtree_leaf_count": "It belongs in Complexity because more spatial subdivisions indicate more local structural variation.",
    "quadtree_structural_variability": "It belongs in Complexity because uneven spatial structure changes perceived visual detail.",
    "quadtree_mean_leaf_size": "It belongs in Complexity because smaller regions indicate finer localized detail.",
    "bounding_box_occupancy": "It belongs in Density/fill because it measures how tightly the visible form fills its active area.",
    "bounding_box_aspect_ratio": "It belongs in Shape/silhouette because it captures whether the active form is tall, wide, or square.",
    "solidity": "It belongs in Shape/silhouette because compactness versus gaps changes the perceived silhouette.",
    "contour_count": "It belongs in Complexity because multiple boundaries add visual detail and potential parts.",
    "holes_count": "It belongs in Complexity because enclosed empty regions add internal detail.",
    "closed_contour_ratio": "It belongs in Shape/silhouette because it approximates whether the glyph behaves like an enclosed form.",
    "is_monochrome": "It belongs in Color/contrast because it marks whether color is unavailable as a visual channel; 1 means monochrome.",
    "color_count": "It belongs in Color because it measures how many distinct colors help distinguish the icon.",
    "mean_saturation": "It belongs in Color because saturation describes how vivid or muted the icon colors are.",
    "colorfulness": "It belongs in Color because it summarizes overall color richness and variation.",
    "foreground_background_contrast": "It belongs in Color because contrast describes foreground-background separation and legibility.",
    "canny_edge_density": "It belongs in Complexity because edge load reflects visual detail and local structure.",
    "perimeter_area_ratio": "It belongs in Complexity because boundary-heavy icons often contain more contour detail relative to area.",
    "filled_vs_outline_proxy": "It belongs in Density/fill because it separates filled marks from outline-like rendering.",
    "horizontal_symmetry": "It belongs in Balance/layout because left-right symmetry affects visual balance.",
    "vertical_symmetry": "It belongs in Balance/layout because top-bottom symmetry affects visual balance.",
    "line_orientation_0": "It belongs in Stroke/structure because dominant horizontal strokes describe internal direction.",
    "line_orientation_45": "It belongs in Stroke/structure because diagonal strokes describe internal direction.",
    "line_orientation_90": "It belongs in Stroke/structure because vertical strokes describe internal direction.",
    "line_orientation_135": "It belongs in Stroke/structure because diagonal strokes describe internal direction.",
    "centroid_distance_from_center": "It belongs in Balance/layout because it measures where visual mass sits on the canvas.",
}

FEATURE_VISUAL_CATEGORIZATIONS = {
    "foreground_area_ratio": ["Sparse vs dense"],
    "canny_edge_density": ["Simple vs complex"],
    "connected_components": ["Single-object vs multi-part"],
    "quadtree_leaf_count": ["Simple vs complex"],
    "quadtree_structural_variability": ["Simple vs complex"],
    "quadtree_mean_leaf_size": ["Simple vs complex"],
    "bounding_box_occupancy": ["Sparse vs dense"],
    "bounding_box_aspect_ratio": ["Compact vs spread-out"],
    "solidity": ["Compact vs spread-out"],
    "centroid_distance_from_center": ["Centered vs off-center"],
    "horizontal_symmetry": ["Balanced vs unbalanced"],
    "vertical_symmetry": ["Balanced vs unbalanced"],
    "perimeter_area_ratio": ["Filled vs outline"],
    "filled_vs_outline_proxy": ["Filled vs outline"],
    "contour_count": ["Single-object vs multi-part"],
    "holes_count": ["Open vs closed shape"],
    "closed_contour_ratio": ["Open vs closed shape"],
    "line_orientation_0": ["Directional/geometric structure"],
    "line_orientation_45": ["Directional/geometric structure"],
    "line_orientation_90": ["Directional/geometric structure"],
    "line_orientation_135": ["Directional/geometric structure"],
    "is_monochrome": ["Black-and-white vs colored"],
    "color_count": ["Black-and-white vs colored"],
    "mean_saturation": ["Color intensity/style"],
    "colorfulness": ["Color intensity/style"],
    "foreground_background_contrast": ["High contrast vs low contrast"],
}

FEATURE_VISUAL_CATEGORY_LABELS = {
    "Sparse vs dense": "sparse icon, dense icon",
    "Simple vs complex": "simple icon, complex icon",
    "Single-object vs multi-part": "single-object symbol, multi-component symbol",
    "Compact vs spread-out": "compact icon, tall icon, wide icon, fragmented icon",
    "Round vs rectangular": "round icon, rectangular icon, box-like icon",
    "Curved vs angular": "curved icon, angular icon, sharp-cornered icon",
    "Centered vs off-center": "centered icon, off-center icon",
    "Balanced vs unbalanced": "symmetric icon, asymmetric icon",
    "Filled vs outline": "filled pictogram, outline icon, line icon",
    "Open vs closed shape": "closed-shape icon, open-line icon",
    "Directional/geometric structure": "horizontal icon, vertical icon, diagonal/action icon",
    "Arrow/directional symbol": "arrow icon, pointer icon, directional symbol",
    "Black-and-white vs colored": "monochrome icon, colored icon",
    "Hue/color family": "red icon, green icon, blue icon, multicolor icon",
    "Color intensity/style": "muted icon, vivid icon, emoji-like icon",
    "High contrast vs low contrast": "high-contrast icon, low-contrast icon",
    "Thin vs thick strokes": "thin-line icon, thick-stroke icon",
    "Skeleton graph complexity": "simple line graph, branching line graph",
    "Texture/pattern": "flat icon, textured icon, hatched icon",
    "Resolution robustness": "small-size robust icon, fragile detailed icon",
    "Text-like mark": "letter icon, text-like symbol",
    "Spatial layout similarity": "top-heavy icon, left-heavy icon, central icon",
    "Global silhouette descriptor": "global-shape descriptor, advanced silhouette profile",
}

FEATURE_LABELS.update(
    {
        "bbox_center_x": "Bounding-box center x",
        "bbox_center_y": "Bounding-box center y",
        "bbox_width_ratio": "Bounding-box width ratio",
        "bbox_height_ratio": "Bounding-box height ratio",
        "circularity": "Circularity",
        "rectangularity": "Rectangularity",
        "corner_count": "Corner count",
        "curvature_histogram_straight": "Straight-contour share",
        "curvature_histogram_gentle": "Gentle-curvature share",
        "curvature_histogram_sharp": "Sharp-curvature share",
        "principal_axis_orientation": "Principal-axis orientation",
        "arrowhead_count": "Arrowhead count",
        "arc_count": "Arc count",
        "stroke_width_mean": "Mean stroke width",
        "stroke_width_std": "Stroke-width variation",
        "skeleton_endpoints": "Skeleton endpoints",
        "skeleton_junctions": "Skeleton junctions",
        "texture_entropy": "Texture entropy",
        "texture_coarseness": "Texture coarseness",
        "crush_test_stability": "Crush-test stability",
        "text_or_letter_presence": "Text/letter presence proxy",
    }
)

FEATURE_MEANINGS.update(
    {
        "bbox_center_x": "Horizontal center of the active bounding box in canvas coordinates.",
        "bbox_center_y": "Vertical center of the active bounding box in canvas coordinates.",
        "bbox_width_ratio": "Share of canvas width covered by the active bounding box.",
        "bbox_height_ratio": "Share of canvas height covered by the active bounding box.",
        "circularity": "How close the foreground silhouette is to a compact circle.",
        "rectangularity": "How densely foreground fills its minimum enclosing rectangle.",
        "corner_count": "Approximate number of polygon corners across external contours.",
        "curvature_histogram_straight": "Share of contour samples that behave like straight segments.",
        "curvature_histogram_gentle": "Share of contour samples with gradual curve behavior.",
        "curvature_histogram_sharp": "Share of contour samples with sharp turns or angular corners.",
        "principal_axis_orientation": "Dominant orientation of foreground pixels from a PCA axis; pairwise comparison should treat it as circular over 180 degrees.",
        "arrowhead_count": "Approximate count of triangular or sharp directional tips.",
        "arc_count": "Approximate count of curved arc-like contour runs.",
        "stroke_width_mean": "Average normalized stroke width estimated from the foreground skeleton.",
        "stroke_width_std": "Variation in normalized stroke width across the skeleton.",
        "skeleton_endpoints": "Number of terminal points in the foreground skeleton graph.",
        "skeleton_junctions": "Number of branching points in the foreground skeleton graph.",
        "texture_entropy": "Normalized grayscale entropy within foreground pixels.",
        "texture_coarseness": "Normalized Tamura coarseness over the scale-standardized foreground bounding-box picture; higher values indicate larger, simpler intensity elements.",
        "crush_test_stability": "How well foreground shape survives one downsampling and re-expansion crush test.",
        "text_or_letter_presence": "Heuristic score for letter-like or text-like visual structure.",
    }
)

FEATURE_CATEGORY_REASONS.update(
    {
        "bbox_center_x": "It belongs in Balance/layout because it records where the active shape sits horizontally.",
        "bbox_center_y": "It belongs in Balance/layout because it records where the active shape sits vertically.",
        "bbox_width_ratio": "It belongs in Balance/layout because it measures how much horizontal canvas span the icon uses.",
        "bbox_height_ratio": "It belongs in Balance/layout because it measures how much vertical canvas span the icon uses.",
        "circularity": "It belongs in Shape/silhouette because roundness changes the perceived silhouette.",
        "rectangularity": "It belongs in Shape/silhouette because box-like forms are a distinct shape family.",
        "corner_count": "It belongs in Complexity because corners and polygon vertices add angular detail.",
        "curvature_histogram_straight": "It belongs in Shape/silhouette because straight contour segments affect perceived geometry.",
        "curvature_histogram_gentle": "It belongs in Shape/silhouette because arcs and gentle curves affect perceived geometry.",
        "curvature_histogram_sharp": "It belongs in Shape/silhouette because sharp turns mark angular geometry.",
        "principal_axis_orientation": "It belongs in Stroke/structure because it captures the icon's dominant visual direction.",
        "arrowhead_count": "It belongs in Stroke/structure because arrowheads are visible direction cues.",
        "arc_count": "It belongs in Stroke/structure because arcs distinguish curved line construction.",
        "stroke_width_mean": "It belongs in Density/fill because line thickness changes visual weight.",
        "stroke_width_std": "It belongs in Density/fill because stroke-width variation changes visual weight and fill behavior.",
        "skeleton_endpoints": "It belongs in Stroke/structure because endpoints describe line-graph structure.",
        "skeleton_junctions": "It belongs in Stroke/structure because junctions describe branching line-graph structure.",
        "texture_entropy": "It belongs in Texture because entropy measures internal tonal variation.",
        "texture_coarseness": "It belongs in Texture because Tamura coarseness measures the perceived scale and repetition of intensity elements.",
        "crush_test_stability": EXCLUDED_IMAGE_FEATURE_REASONS["crush_test_stability"],
        "text_or_letter_presence": EXCLUDED_IMAGE_FEATURE_REASONS["text_or_letter_presence"],
    }
)

FEATURE_VISUAL_CATEGORIZATIONS.update(
    {
        "bbox_center_x": ["Spatial layout similarity"],
        "bbox_center_y": ["Spatial layout similarity"],
        "bbox_width_ratio": ["Spatial layout similarity"],
        "bbox_height_ratio": ["Spatial layout similarity"],
        "circularity": ["Round vs rectangular"],
        "rectangularity": ["Round vs rectangular"],
        "corner_count": ["Curved vs angular"],
        "curvature_histogram_straight": ["Curved vs angular"],
        "curvature_histogram_gentle": ["Curved vs angular"],
        "curvature_histogram_sharp": ["Curved vs angular"],
        "principal_axis_orientation": ["Directional/geometric structure"],
        "arrowhead_count": ["Arrow/directional symbol"],
        "arc_count": ["Curved vs angular"],
        "stroke_width_mean": ["Thin vs thick strokes"],
        "stroke_width_std": ["Thin vs thick strokes"],
        "skeleton_endpoints": ["Skeleton graph complexity"],
        "skeleton_junctions": ["Skeleton graph complexity"],
        "texture_entropy": ["Texture/pattern"],
        "texture_coarseness": ["Texture/pattern"],
        "crush_test_stability": [],
        "text_or_letter_presence": [],
    }
)

for index in range(1, 8):
    feature_id = f"hu_moment_{index}"
    FEATURE_LABELS[feature_id] = f"Hu moment {index}"
    FEATURE_MEANINGS[feature_id] = "Advanced global silhouette descriptor; useful for shape matching but not directly human-readable on its own."
    FEATURE_CATEGORY_REASONS[feature_id] = EXCLUDED_IMAGE_FEATURE_REASONS[feature_id]
    FEATURE_VISUAL_CATEGORIZATIONS[feature_id] = []

for index in range(12):
    feature_id = f"hue_histogram_{index:02d}"
    start = index * 30
    end = start + 30
    FEATURE_LABELS[feature_id] = f"Hue {start}-{end} deg"
    FEATURE_MEANINGS[feature_id] = f"Share of saturated foreground pixels with hue between {start} and {end} degrees; hue is circular, so neighboring bins wrap around at red."
    FEATURE_CATEGORY_REASONS[feature_id] = "It belongs in Color because hue bins represent color-family channels."
    FEATURE_VISUAL_CATEGORIZATIONS[feature_id] = ["Hue/color family"]

for rank in range(1, 4):
    for channel, label in [("l", "L"), ("a", "a"), ("b", "b")]:
        feature_id = f"dominant_color_{rank}_lab_{channel}"
        FEATURE_LABELS[feature_id] = f"Dominant color {rank} Lab {label}"
        FEATURE_MEANINGS[feature_id] = f"Lab {label} channel for dominant foreground color {rank}."
        FEATURE_CATEGORY_REASONS[feature_id] = "It belongs in Color because dominant Lab values encode foreground color appearance."
        FEATURE_VISUAL_CATEGORIZATIONS[feature_id] = ["Hue/color family"]

for index in range(10):
    feature_id = f"lbp_histogram_{index:02d}"
    FEATURE_LABELS[feature_id] = f"LBP texture bin {index}"
    FEATURE_MEANINGS[feature_id] = "Uniform local binary pattern texture share; bin 9 stores non-uniform patterns."
    FEATURE_CATEGORY_REASONS[feature_id] = EXCLUDED_IMAGE_FEATURE_REASONS[feature_id]
    FEATURE_VISUAL_CATEGORIZATIONS[feature_id] = []

for row in range(4):
    for col in range(4):
        feature_id = f"grid_foreground_{row}_{col}"
        FEATURE_LABELS[feature_id] = f"Grid foreground r{row + 1} c{col + 1}"
        FEATURE_MEANINGS[feature_id] = (
            f"Foreground share in the 4x4 layout grid at row {row + 1}, column {col + 1}."
        )
        FEATURE_CATEGORY_REASONS[feature_id] = (
            "It belongs in Balance/layout because it records where foreground mass appears in the icon grid."
        )
        FEATURE_VISUAL_CATEGORIZATIONS[feature_id] = ["Spatial layout similarity"]

MCDOUGALL_NUMERIC_COLUMNS = [
    "mcdougall_concreteness",
    "mcdougall_complexity",
    "mcdougall_familiarity",
    "mcdougall_meaningfulness",
    "mcdougall_semantic_distance",
    "mcdougall_concept_agreement",
    "mcdougall_name_agreement",
]

FEATURE_VARIANTS = ("image", "metadata", "combined")
REDUNDANCY_HIGH_THRESHOLD = 0.85
REDUNDANCY_MODERATE_THRESHOLD = 0.70
REPRESENTATIVE_MAX_ABS_SPEARMAN = REDUNDANCY_MODERATE_THRESHOLD

# This ordering is the substantive definition of "strongest" until human-study
# outcomes exist. It combines the local literature mapping, interpretability,
# measurement directness, and the observed quality of the 1,038-icon feature
# sample. Spearman is applied later only between representatives that would be
# selected together.
FEATURE_STRENGTH_PRIORITY = {
    "complexity": [
        "canny_edge_density",
        "connected_components",
        "quadtree_structural_variability",
        "holes_count",
        "perimeter_area_ratio",
        "corner_count",
        "contour_count",
    ],
    "shape": [
        "bounding_box_aspect_ratio",
        "circularity",
        "rectangularity",
        "curvature_histogram_sharp",
        "closed_contour_ratio",
        "solidity",
    ],
    "structure": [
        "line_orientation_0",
        "skeleton_junctions",
        "line_orientation_90",
        "skeleton_endpoints",
        "principal_axis_orientation",
        "line_orientation_45",
        "line_orientation_135",
        "arrowhead_count",
        "arc_count",
    ],
    "density_fill": [
        "foreground_area_ratio",
        "stroke_width_std",
        "stroke_width_mean",
        "bounding_box_occupancy",
        "filled_vs_outline_proxy",
    ],
    "balance_layout": [
        "horizontal_symmetry",
        "bbox_width_ratio",
        "centroid_distance_from_center",
        "vertical_symmetry",
        "bbox_height_ratio",
    ],
    "color_contrast": [
        "mean_saturation",
        "foreground_background_contrast",
        "color_count",
        "is_monochrome",
        "colorfulness",
    ],
    "texture": [
        "texture_entropy",
        "texture_coarseness",
    ],
}


def image_feature_sections() -> list[dict[str, object]]:
    expected = set(IMAGE_FEATURE_COLUMNS) - EXCLUDED_IMAGE_FEATURES
    seen = []
    sections = []
    for section in DASHBOARD_FEATURE_SECTIONS:
        feature_ids = list(section["feature_ids"])
        seen.extend(feature_ids)
        sections.append(
            {
                "id": section["id"],
                "title": section["title"],
                "description": section["description"],
                "human_category": section.get("human_category", section["title"].replace(" Features", "")),
                "family_summary": section.get("family_summary", ""),
                "perception": section.get("perception", ""),
                "low_value": section.get("low_value", ""),
                "high_value": section.get("high_value", ""),
                "visible": section.get("visible", True),
                "features": [
                    {
                        "id": feature_id,
                        "label": FEATURE_LABELS.get(feature_id, feature_id.replace("_", " ").title()),
                        "group": section["id"],
                        "group_title": section["title"],
                        "meaning": FEATURE_MEANINGS.get(feature_id, "Extracted visual feature."),
                        "visual_categorizations": FEATURE_VISUAL_CATEGORIZATIONS.get(feature_id, []),
                        "visual_category_labels": [
                            FEATURE_VISUAL_CATEGORY_LABELS[category]
                            for category in FEATURE_VISUAL_CATEGORIZATIONS.get(feature_id, [])
                            if category in FEATURE_VISUAL_CATEGORY_LABELS
                        ],
                        "category_reason": FEATURE_CATEGORY_REASONS.get(
                            feature_id,
                            f"It belongs in {section['title']} because it describes that visual channel.",
                        ),
                    }
                    for feature_id in feature_ids
                ],
            }
        )

    duplicate_features = sorted({feature_id for feature_id in seen if seen.count(feature_id) > 1})
    missing_features = sorted(expected - set(seen))
    unknown_features = sorted(set(seen) - expected)
    if duplicate_features or missing_features or unknown_features:
        raise ValueError(
            "Invalid dashboard feature sections: "
            f"duplicates={duplicate_features}, missing={missing_features}, unknown={unknown_features}"
        )
    return sections


def active_image_feature_columns() -> list[str]:
    feature_ids = []
    for section in image_feature_sections():
        feature_ids.extend(feature["id"] for feature in section["features"])
    return feature_ids


def active_image_feature_groups() -> list[list[str]]:
    return [[feature["id"] for feature in section["features"]] for section in image_feature_sections()]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sample_random_rows_per_set(rows: list[dict[str, str]], per_set_sample_size: int, seed: int) -> list[dict[str, str]]:
    rows_by_set: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    for index, row in enumerate(rows):
        rows_by_set[row["set_id"]].append((index, row))

    rng = np.random.default_rng(seed)
    indices = []
    for set_id in sorted(rows_by_set):
        set_rows = rows_by_set[set_id]
        if len(set_rows) <= per_set_sample_size:
            indices.extend(index for index, _ in set_rows)
            continue
        local_indices = rng.choice(len(set_rows), size=per_set_sample_size, replace=False).tolist()
        indices.extend(set_rows[local_index][0] for local_index in local_indices)

    indices = sorted(indices)
    return [rows[index] for index in indices]


def enrich_metadata_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ratings = metadata_helpers.load_mcdougall_ratings()
    enriched = []
    for source in rows:
        row = source.copy()
        set_id = row["set_id"]
        label = row.get("label", "")
        notes = row.get("notes", "")
        rating = None

        if set_id == "01_mcdougall_symbol_icon_set":
            appendix_item = metadata_helpers.notes_value(notes, "appendix_item")
            rating = ratings.get(appendix_item)
            if rating:
                rating_note = (
                    "mcdougall_ratings="
                    f"concreteness:{rating.get('concreteness', '')},"
                    f"complexity:{rating.get('complexity', '')},"
                    f"familiarity:{rating.get('familiarity', '')},"
                    f"meaningfulness:{rating.get('meaningfulness', '')},"
                    f"semantic_distance:{rating.get('semantic_distance', '')},"
                    f"concept_agreement:{rating.get('concept_agreement', '')},"
                    f"name_agreement:{rating.get('name_agreement', '')},"
                    f"common_response:{rating.get('common_response', '')}"
                )
                notes = "; ".join(part for part in [notes, rating_note] if part)

        metadata_text = " | ".join(value for value in [label, row.get("set_name", ""), notes] if value)
        enriched.append(
            {
                "icon_id": row["icon_id"],
                "set_id": set_id,
                "set_name": row["set_name"],
                "icon_name": label,
                "label": label,
                "source": row.get("source", ""),
                "source_url": row.get("source_url", ""),
                "format": row.get("format", ""),
                "filename": row.get("filename", ""),
                "relative_path": row.get("relative_path", ""),
                "normalized_path": row.get("normalized_path", ""),
                "notes": notes,
                "metadata_text": metadata_text,
                "metadata_tokens": metadata_helpers.text_tokens(label, row.get("set_name", ""), notes),
                "mcdougall_concreteness": (rating or {}).get("concreteness", ""),
                "mcdougall_complexity": (rating or {}).get("complexity", ""),
                "mcdougall_familiarity": (rating or {}).get("familiarity", ""),
                "mcdougall_meaningfulness": (rating or {}).get("meaningfulness", ""),
                "mcdougall_semantic_distance": (rating or {}).get("semantic_distance", ""),
                "mcdougall_concept_agreement": (rating or {}).get("concept_agreement", ""),
                "mcdougall_name_agreement": (rating or {}).get("name_agreement", ""),
                "mcdougall_common_response": (rating or {}).get("common_response", ""),
                "has_notes": str(bool(notes)).lower(),
                "source_path_exists": str((ROOT / row.get("relative_path", "")).exists()).lower(),
                "normalized_path_exists": str((ROOT / row.get("normalized_path", "")).exists()).lower(),
            }
        )
    return enriched


def extract_features(rows: list[dict[str, str]]) -> list[dict]:
    feature_rows = []
    failures = []
    for index, row in enumerate(rows, start=1):
        values, failure = extract_icon_features.extract_row(
            row,
            extract_icon_features.FEATURE_EXTRACTORS,
            foreground_threshold=245,
        )
        if failure:
            failures.append(failure)
            continue
        feature_rows.append(values)
        if index % 250 == 0:
            print(f"Extracted features for {index}/{len(rows)} rows")

    (OUTPUT_DIR / "feature_failures.json").write_text(
        json.dumps(failures, indent=2) + "\n", encoding="utf-8"
    )
    if failures:
        print(f"Feature extraction failures: {len(failures)}")
    return feature_rows


def to_float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def standardize(matrix: np.ndarray) -> tuple[np.ndarray, list[float], list[float]]:
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds = np.where(stds == 0, 1.0, stds)
    return (matrix - means) / stds, means.tolist(), stds.tolist()


def finite_float(value: object) -> float:
    if value is None or value == "":
        return float("nan")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    if math.isnan(number) or math.isinf(number):
        return float("nan")
    return number


def average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.zeros(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        average_rank = (start + end - 1) / 2.0 + 1.0
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def spearman_correlation(left: np.ndarray, right: np.ndarray) -> tuple[float, int]:
    mask = np.isfinite(left) & np.isfinite(right)
    pair_count = int(mask.sum())
    if pair_count < 2:
        return 0.0, pair_count
    left_ranks = average_ranks(left[mask])
    right_ranks = average_ranks(right[mask])
    left_std = left_ranks.std()
    right_std = right_ranks.std()
    if left_std == 0 or right_std == 0:
        return 0.0, pair_count
    correlation = float(np.corrcoef(left_ranks, right_ranks)[0, 1])
    if math.isnan(correlation) or math.isinf(correlation):
        return 0.0, pair_count
    return correlation, pair_count


def redundancy_band(abs_correlation: float) -> str:
    if abs_correlation >= REDUNDANCY_HIGH_THRESHOLD:
        return "high"
    if abs_correlation >= REDUNDANCY_MODERATE_THRESHOLD:
        return "moderate"
    return "low"


def title_case(value: str) -> str:
    return value.replace("_", " ").title()


def feature_metadata_by_id() -> dict[str, dict[str, str]]:
    metadata = {}
    for section in image_feature_sections():
        for feature in section["features"]:
            metadata[feature["id"]] = {
                "label": feature["label"],
                "group": feature["group"],
                "group_title": feature["group_title"],
                "meaning": feature["meaning"],
            }
    return metadata


def feature_review_source_rows(feature_by_id: dict[str, dict]) -> tuple[list[dict], str]:
    if FEATURES_PATH.exists():
        rows = read_csv(FEATURES_PATH)
        if rows and all(column in rows[0] for column in IMAGE_FEATURE_COLUMNS):
            return rows, str(FEATURES_PATH.relative_to(ROOT))
    return list(feature_by_id.values()), "analysis_dashboard_sample"


def build_feature_review(feature_by_id: dict[str, dict]) -> dict:
    rows, source = feature_review_source_rows(feature_by_id)
    metadata = feature_metadata_by_id()
    active_columns = active_image_feature_columns()
    matrix = np.array(
        [[finite_float(row.get(column)) for column in active_columns] for row in rows],
        dtype=float,
    )

    feature_rows = []
    for column_index, feature_id in enumerate(active_columns):
        values = matrix[:, column_index]
        valid_values = values[np.isfinite(values)]
        feature_rows.append(
            {
                "feature_id": feature_id,
                "label": metadata.get(feature_id, {}).get("label", FEATURE_LABELS.get(feature_id, title_case(feature_id))),
                "group": metadata.get(feature_id, {}).get("group", ""),
                "group_title": metadata.get(feature_id, {}).get("group_title", ""),
                "meaning": metadata.get(feature_id, {}).get("meaning", ""),
                "std": round(float(valid_values.std()) if len(valid_values) else 0.0, 6),
                "variance": round(float(valid_values.var()) if len(valid_values) else 0.0, 6),
                "missing_count": int(len(values) - len(valid_values)),
                "strongest_abs_correlation": 0.0,
                "strongest_correlation": 0.0,
                "strongest_partner": "",
                "strongest_partner_label": "",
                "strongest_partner_group": "",
                "redundancy_band": "low",
            }
        )

    pair_rows = []
    feature_index = {row["feature_id"]: index for index, row in enumerate(feature_rows)}
    for left_index, left_feature in enumerate(active_columns):
        for right_index in range(left_index + 1, len(active_columns)):
            right_feature = active_columns[right_index]
            correlation, pair_count = spearman_correlation(matrix[:, left_index], matrix[:, right_index])
            abs_correlation = abs(correlation)
            left_meta = feature_rows[left_index]
            right_meta = feature_rows[right_index]
            pair_rows.append(
                {
                    "feature_a": left_feature,
                    "feature_a_label": left_meta["label"],
                    "feature_a_group": left_meta["group"],
                    "feature_a_group_title": left_meta["group_title"],
                    "feature_b": right_feature,
                    "feature_b_label": right_meta["label"],
                    "feature_b_group": right_meta["group"],
                    "feature_b_group_title": right_meta["group_title"],
                    "correlation": round(correlation, 6),
                    "abs_correlation": round(abs_correlation, 6),
                    "band": redundancy_band(abs_correlation),
                    "shared_group": left_meta["group"] == right_meta["group"],
                    "pair_count": pair_count,
                }
            )

            for feature_id, partner_id, partner_meta in (
                (left_feature, right_feature, right_meta),
                (right_feature, left_feature, left_meta),
            ):
                row = feature_rows[feature_index[feature_id]]
                if abs_correlation > row["strongest_abs_correlation"]:
                    row["strongest_abs_correlation"] = round(abs_correlation, 6)
                    row["strongest_correlation"] = round(correlation, 6)
                    row["strongest_partner"] = partner_id
                    row["strongest_partner_label"] = partner_meta["label"]
                    row["strongest_partner_group"] = partner_meta["group_title"]
                    row["redundancy_band"] = redundancy_band(abs_correlation)

    pair_rows.sort(key=lambda row: (-row["abs_correlation"], row["feature_a_label"], row["feature_b_label"]))
    feature_rows.sort(key=lambda row: (-row["strongest_abs_correlation"], row["label"]))
    high_pair_count = sum(1 for row in pair_rows if row["band"] == "high")
    moderate_pair_count = sum(1 for row in pair_rows if row["band"] == "moderate")
    low_pair_count = sum(1 for row in pair_rows if row["band"] == "low")

    return {
        "metadata": {
            "source": source,
            "row_count": len(rows),
            "method": "Spearman correlation over image feature columns",
            "high_threshold": REDUNDANCY_HIGH_THRESHOLD,
            "moderate_threshold": REDUNDANCY_MODERATE_THRESHOLD,
        },
        "summary": {
            "feature_count": len(feature_rows),
            "pair_count": len(pair_rows),
            "high_pair_count": high_pair_count,
            "moderate_pair_count": moderate_pair_count,
            "low_pair_count": low_pair_count,
        },
        "features": feature_rows,
        "pairs": pair_rows,
    }


def feature_explorer_source_rows(records: list[dict], feature_by_id: dict[str, dict]) -> tuple[list[dict], str]:
    if FEATURES_PATH.exists():
        rows = read_csv(FEATURES_PATH)
        if rows and all(column in rows[0] for column in IMAGE_FEATURE_COLUMNS):
            return rows, str(FEATURES_PATH.relative_to(ROOT))

    rows = []
    for record in records:
        feature_row = feature_by_id.get(record["icon_id"], {})
        rows.append(
            {
                "icon_id": record["icon_id"],
                "label": record.get("label", ""),
                "set_name": record.get("set_name", ""),
                "normalized_path": record.get("normalized_path", ""),
                **{column: feature_row.get(column, "") for column in IMAGE_FEATURE_COLUMNS},
            }
        )
    return rows, "analysis_dashboard_sample"


def explorer_icon_example(row: dict, value: float, source: str) -> dict:
    normalized_path = row.get("normalized_path", "")
    if source != "analysis_dashboard_sample" and normalized_path:
        normalized_path = relative_to_dashboard(ROOT / normalized_path)
    return {
        "icon_id": row.get("icon_id", ""),
        "label": row.get("label", ""),
        "set_name": row.get("set_name", ""),
        "normalized_path": normalized_path,
        "value": round(float(value), 6),
    }


def strongest_signed_partners(feature_id: str, pairs: list[dict]) -> dict:
    positive = None
    negative = None
    for pair in pairs:
        if pair["feature_a"] == feature_id:
            partner_id = pair["feature_b"]
            partner_label = pair["feature_b_label"]
            partner_group = pair["feature_b_group_title"]
        elif pair["feature_b"] == feature_id:
            partner_id = pair["feature_a"]
            partner_label = pair["feature_a_label"]
            partner_group = pair["feature_a_group_title"]
        else:
            continue

        partner = {
            "feature_id": partner_id,
            "label": partner_label,
            "group_title": partner_group,
            "correlation": pair["correlation"],
            "abs_correlation": pair["abs_correlation"],
            "band": pair["band"],
            "pair_count": pair["pair_count"],
        }
        if pair["correlation"] > 0 and (positive is None or pair["correlation"] > positive["correlation"]):
            positive = partner
        if pair["correlation"] < 0 and (negative is None or pair["correlation"] < negative["correlation"]):
            negative = partner
    return {"positive": positive, "negative": negative}


def build_feature_explorer(records: list[dict], feature_by_id: dict[str, dict], feature_review: dict) -> dict:
    rows, source = feature_explorer_source_rows(records, feature_by_id)
    metadata = feature_metadata_by_id()
    family_order = [section["id"] for section in image_feature_sections()]
    selected_review_rows = select_strong_family_features(
        features=feature_review.get("features", []),
        pairs=feature_review.get("pairs", []),
        family_order=family_order,
        strength_priority=FEATURE_STRENGTH_PRIORITY,
        per_family=2,
        max_abs_spearman=REPRESENTATIVE_MAX_ABS_SPEARMAN,
    )
    selected_counts = Counter(row["group"] for row in selected_review_rows)
    expected_counts = {
        family_id: min(2, len(FEATURE_STRENGTH_PRIORITY.get(family_id, ())))
        for family_id in family_order
    }
    if any(selected_counts[family_id] != expected for family_id, expected in expected_counts.items()):
        raise ValueError(
            "Feature representative selection did not produce the expected family counts: "
            f"selected={dict(selected_counts)}, expected={expected_counts}"
        )
    selected_by_id = {row["feature_id"]: row for row in selected_review_rows}
    features = []
    for feature_id in selected_by_id:
        entries = [
            (row, finite_float(row.get(feature_id)))
            for row in rows
            if math.isfinite(finite_float(row.get(feature_id)))
        ]
        values = np.array([value for _, value in entries], dtype=float)
        if len(values):
            mean = float(values.mean())
            median = float(np.median(values))
            variance = float(values.var())
            std = float(values.std())
            min_value = float(values.min())
            max_value = float(values.max())
            low_examples = sorted(entries, key=lambda item: (item[1], item[0].get("label", "")))[:6]
            mean_examples = sorted(entries, key=lambda item: (abs(item[1] - mean), item[0].get("label", "")))[:6]
            high_examples = sorted(entries, key=lambda item: (-item[1], item[0].get("label", "")))[:6]
        else:
            mean = median = variance = std = min_value = max_value = 0.0
            low_examples = mean_examples = high_examples = []

        feature_meta = metadata.get(feature_id, {})
        selection = selected_by_id[feature_id]
        partners = strongest_signed_partners(feature_id, feature_review.get("pairs", []))
        features.append(
            {
                "feature_id": feature_id,
                "label": feature_meta.get("label", FEATURE_LABELS.get(feature_id, title_case(feature_id))),
                "group": feature_meta.get("group", ""),
                "group_title": feature_meta.get("group_title", ""),
                "meaning": feature_meta.get("meaning", ""),
                "min": round(min_value, 6),
                "max": round(max_value, 6),
                "mean": round(mean, 6),
                "median": round(median, 6),
                "variance": round(variance, 6),
                "std": round(std, 6),
                "valid_count": int(len(values)),
                "missing_count": int(len(rows) - len(values)),
                "examples": {
                    "low": [explorer_icon_example(row, value, source) for row, value in low_examples],
                    "mean": [explorer_icon_example(row, value, source) for row, value in mean_examples],
                    "high": [explorer_icon_example(row, value, source) for row, value in high_examples],
                },
                "correlations": partners,
                "selection": {
                    "rank_in_family": selection["selection_rank_in_family"],
                    "strength_priority_rank": selection["strength_priority_rank"],
                    "companion_feature_id": selection["companion_feature_id"],
                    "companion_feature_label": selection["companion_feature_label"],
                    "pair_correlation": selection["pair_correlation"],
                    "pair_abs_correlation": selection["pair_abs_correlation"],
                },
            }
        )

    return {
        "metadata": {
            "source": source,
            "row_count": len(rows),
            "examples_per_band": 6,
            "feature_count": len(features),
            "features_per_family_limit": 2,
            "selection_method": "Up to two non-constant features per family ranked first by literature support, interpretability, measurement directness, and observed data quality. Direct pairwise absolute Spearman correlation must be below 0.70.",
            "max_abs_spearman": REPRESENTATIVE_MAX_ABS_SPEARMAN,
            "strength_priority": FEATURE_STRENGTH_PRIORITY,
            "method": "Low, nearest-mean, and high feature-value examples with Spearman partners",
        },
        "features": features,
    }


def apply_group_weights(matrix: np.ndarray, columns: list[str], groups: list[list[str]]) -> np.ndarray:
    weighted = matrix.copy()
    column_index = {column: index for index, column in enumerate(columns)}
    for group in groups:
        indices = [column_index[column] for column in group if column in column_index]
        if not indices:
            continue
        weighted[:, indices] /= math.sqrt(len(indices))
    return weighted


def one_hot(rows: list[dict], column: str, prefix: str, max_values: int | None = None) -> tuple[np.ndarray, list[str]]:
    counts = Counter(row.get(column, "") or "missing" for row in rows)
    values = [value for value, _ in counts.most_common(max_values)]
    matrix = np.zeros((len(rows), len(values)), dtype=float)
    index = {value: idx for idx, value in enumerate(values)}
    for row_idx, row in enumerate(rows):
        value = row.get(column, "") or "missing"
        if value in index:
            matrix[row_idx, index[value]] = 1.0
    return matrix, [f"{prefix}:{value}" for value in values]


def token_features(rows: list[dict], max_tokens: int = 80) -> tuple[np.ndarray, list[str]]:
    counts: Counter[str] = Counter()
    row_tokens = []
    for row in rows:
        tokens = sorted(set((row.get("metadata_tokens") or "").split()))
        row_tokens.append(tokens)
        counts.update(tokens)
    vocabulary = [token for token, _ in counts.most_common(max_tokens)]
    index = {token: idx for idx, token in enumerate(vocabulary)}
    matrix = np.zeros((len(rows), len(vocabulary)), dtype=float)
    for row_idx, tokens in enumerate(row_tokens):
        for token in tokens:
            if token in index:
                matrix[row_idx, index[token]] = 1.0
    return matrix, [f"token:{token}" for token in vocabulary]


def feature_matrices(rows: list[dict], feature_by_id: dict[str, dict]) -> dict[str, dict]:
    image_columns = active_image_feature_columns()
    image = np.array(
        [[to_float(feature_by_id[row["icon_id"]].get(column)) for column in image_columns] for row in rows],
        dtype=float,
    )
    image_scaled, image_means, image_stds = standardize(image)
    image_scaled = apply_group_weights(image_scaled, image_columns, active_image_feature_groups())

    set_matrix, set_columns = one_hot(rows, "set_name", "set")
    token_matrix, token_columns = token_features(rows)
    mcdougall = np.array(
        [[to_float(row.get(column)) for column in MCDOUGALL_NUMERIC_COLUMNS] for row in rows],
        dtype=float,
    )
    mcdougall_scaled, _, _ = standardize(mcdougall)

    metadata_matrix = np.hstack([set_matrix, token_matrix, mcdougall_scaled])
    metadata_columns = set_columns + token_columns + MCDOUGALL_NUMERIC_COLUMNS
    combined_matrix = np.hstack([image_scaled, metadata_matrix])

    return {
        "image": {
            "matrix": image_scaled,
            "columns": image_columns,
            "raw_matrix": image,
            "means": image_means,
            "stds": image_stds,
        },
        "metadata": {
            "matrix": metadata_matrix,
            "columns": metadata_columns,
        },
        "combined": {
            "matrix": combined_matrix,
            "columns": image_columns + metadata_columns,
        },
    }


def pca_2d(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0)
    if centered.shape[1] == 1:
        return np.column_stack([centered[:, 0], np.zeros(len(centered))])
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    components = vt[:2].T
    coords = centered @ components
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(len(coords))])
    return coords[:, :2]


def kmeans(matrix: np.ndarray, k: int, seed: int, iterations: int = 80) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed + k)
    if k >= len(matrix):
        labels = np.arange(len(matrix), dtype=int)
        return labels, matrix.copy()
    centers = matrix[rng.choice(len(matrix), size=k, replace=False)].copy()
    labels = np.zeros(len(matrix), dtype=int)
    for _ in range(iterations):
        distances = squared_distances(matrix, centers)
        new_labels = distances.argmin(axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for cluster in range(k):
            members = matrix[labels == cluster]
            if len(members):
                centers[cluster] = members.mean(axis=0)
            else:
                centers[cluster] = matrix[rng.integers(0, len(matrix))]
    return labels, centers


def squared_distances(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)


def silhouette_proxy(matrix: np.ndarray, labels: np.ndarray, centers: np.ndarray) -> float:
    own = np.linalg.norm(matrix - centers[labels], axis=1)
    distances = np.linalg.norm(matrix[:, None, :] - centers[None, :, :], axis=2)
    if centers.shape[0] > 1:
        distances[np.arange(len(matrix)), labels] = np.inf
        nearest_other = distances.min(axis=1)
    else:
        nearest_other = np.zeros(len(matrix))
    denom = np.maximum(own, nearest_other)
    scores = np.where(denom > 0, (nearest_other - own) / denom, 0.0)
    return float(scores.mean())


def pairwise_distances(matrix: np.ndarray) -> np.ndarray:
    norms = (matrix**2).sum(axis=1)
    squared = norms[:, None] + norms[None, :] - 2 * matrix @ matrix.T
    squared = np.maximum(squared, 0.0)
    return np.sqrt(squared)


def hierarchical_single_linkage_labels(matrix: np.ndarray, k_values: tuple[int, ...]) -> dict[int, np.ndarray]:
    distances = pairwise_distances(matrix)
    edges = []
    for i in range(len(matrix)):
        row = distances[i, i + 1 :]
        for offset, distance in enumerate(row, start=i + 1):
            edges.append((float(distance), i, offset))
    edges.sort(key=lambda item: item[0])

    parent = list(range(len(matrix)))
    size = [1] * len(matrix)
    mst_edges = []

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for distance, left, right in edges:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            continue
        if size[root_left] < size[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        size[root_left] += size[root_right]
        mst_edges.append((distance, left, right))
        if len(mst_edges) == len(matrix) - 1:
            break

    labels_by_k = {}
    for k in k_values:
        labels_by_k[k] = labels_from_mst(len(matrix), mst_edges, k)
    return labels_by_k


def labels_from_mst(node_count: int, mst_edges: list[tuple[float, int, int]], k: int) -> np.ndarray:
    kept_edges = sorted(mst_edges, key=lambda item: item[0])[: max(0, node_count - k)]
    parent = list(range(node_count))
    size = [1] * node_count

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return
        if size[root_left] < size[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        size[root_left] += size[root_right]

    for _, left, right in kept_edges:
        union(left, right)

    cluster_index: dict[int, int] = {}
    labels = np.zeros(node_count, dtype=int)
    for item in range(node_count):
        root = find(item)
        if root not in cluster_index:
            cluster_index[root] = len(cluster_index)
        labels[item] = cluster_index[root]
    return labels


def representative_indices(matrix: np.ndarray, labels: np.ndarray, limit: int = 8) -> dict[int, list[int]]:
    representatives: dict[int, list[int]] = {}
    for cluster in sorted(set(labels.tolist())):
        indices = np.where(labels == cluster)[0]
        center = matrix[indices].mean(axis=0)
        distances = np.linalg.norm(matrix[indices] - center, axis=1)
        ordered = indices[np.argsort(distances)[:limit]]
        representatives[int(cluster)] = [int(index) for index in ordered]
    return representatives


def cluster_summary(rows: list[dict], matrix: np.ndarray, labels: np.ndarray, method: str, variant: str, k: int) -> list[dict]:
    reps = representative_indices(matrix, labels)
    summaries = []
    for cluster in sorted(set(labels.tolist())):
        indices = [idx for idx, label in enumerate(labels) if label == cluster]
        subset = [rows[idx] for idx in indices]
        set_counts = Counter(row["set_name"] for row in subset).most_common(5)
        summaries.append(
            {
                "method": method,
                "variant": variant,
                "k": k,
                "cluster": int(cluster),
                "size": len(indices),
                "top_sets": json.dumps(set_counts, ensure_ascii=False),
                "representative_icon_ids": " ".join(rows[idx]["icon_id"] for idx in reps[int(cluster)]),
            }
        )
    return summaries


def build_clusters(rows: list[dict], matrices: dict[str, dict]) -> tuple[dict, list[dict], list[dict]]:
    clusters: dict[str, dict] = {}
    assignment_rows = []
    summary_rows = []
    for variant in FEATURE_VARIANTS:
        matrix = matrices[variant]["matrix"]
        clusters[variant] = {"pca": pca_2d(matrix).round(6).tolist(), "kmeans": {}, "hierarchical": {}}

        for k in K_VALUES:
            labels, centers = kmeans(matrix, k, RANDOM_SEED)
            score = silhouette_proxy(matrix, labels, centers)
            clusters[variant]["kmeans"][str(k)] = {
                "labels": labels.astype(int).tolist(),
                "score": round(score, 6),
                "representatives": representative_indices(matrix, labels),
            }
            for idx, row in enumerate(rows):
                assignment_rows.append(
                    {
                        "icon_id": row["icon_id"],
                        "method": "kmeans",
                        "variant": variant,
                        "k": k,
                        "cluster": int(labels[idx]),
                        "quality_score": round(score, 6),
                    }
                )
            summary_rows.extend(cluster_summary(rows, matrix, labels, "kmeans", variant, k))

        hierarchical = hierarchical_single_linkage_labels(matrix, K_VALUES)
        for k, labels in hierarchical.items():
            clusters[variant]["hierarchical"][str(k)] = {
                "labels": labels.astype(int).tolist(),
                "representatives": representative_indices(matrix, labels),
            }
            for idx, row in enumerate(rows):
                assignment_rows.append(
                    {
                        "icon_id": row["icon_id"],
                        "method": "hierarchical",
                        "variant": variant,
                        "k": k,
                        "cluster": int(labels[idx]),
                        "quality_score": "",
                    }
                )
            summary_rows.extend(cluster_summary(rows, matrix, labels, "hierarchical", variant, k))
    return clusters, assignment_rows, summary_rows


def write_feature_tables(rows: list[dict], feature_by_id: dict[str, dict], matrices: dict[str, dict]) -> None:
    image_rows = []
    metadata_rows = []
    combined_rows = []
    for index, row in enumerate(rows):
        base = {column: row.get(column, "") for column in METADATA_COLUMNS}
        image_rows.append(
            base | {column: feature_by_id[row["icon_id"]].get(column, "") for column in IMAGE_FEATURE_COLUMNS}
        )
        metadata_rows.append(
            base
            | {
                column: round(float(matrices["metadata"]["matrix"][index, col_idx]), 6)
                for col_idx, column in enumerate(matrices["metadata"]["columns"])
            }
        )
        combined_rows.append(
            base
            | {
                column: round(float(matrices["combined"]["matrix"][index, col_idx]), 6)
                for col_idx, column in enumerate(matrices["combined"]["columns"])
            }
        )
    write_rows(OUTPUT_DIR / "features_image.csv", image_rows)
    write_rows(OUTPUT_DIR / "features_metadata.csv", metadata_rows)
    write_rows(OUTPUT_DIR / "features_combined.csv", combined_rows)


def write_dashboard_data(rows: list[dict], feature_by_id: dict[str, dict], matrices: dict[str, dict], clusters: dict) -> None:
    records = []
    for row in rows:
        image_features = {
            column: round(to_float(feature_by_id[row["icon_id"]].get(column)), 6)
            for column in IMAGE_FEATURE_COLUMNS
        }
        mcdougall = {column: row.get(column, "") for column in MCDOUGALL_NUMERIC_COLUMNS}
        mcdougall["mcdougall_common_response"] = row.get("mcdougall_common_response", "")
        records.append(
            {
                "icon_id": row["icon_id"],
                "label": row.get("label", ""),
                "set_id": row.get("set_id", ""),
                "set_name": row.get("set_name", ""),
                "format": row.get("format", ""),
                "normalized_path": relative_to_dashboard(ROOT / row.get("normalized_path", "")),
                "metadata_tokens": row.get("metadata_tokens", ""),
                "image_features": image_features,
                "mcdougall": mcdougall,
            }
        )

    feature_review = build_feature_review(feature_by_id)
    data = {
        "metadata": {
            "generated_from": str(DATASET_PATH.relative_to(ROOT)),
            "row_count": len(records),
            "per_set_sample_size": PER_SET_SAMPLE_SIZE,
            "random_seed": RANDOM_SEED,
            "k_values": list(K_VALUES),
            "primary_k": PRIMARY_K,
            "feature_variants": list(FEATURE_VARIANTS),
            "image_feature_columns": matrices["image"]["columns"],
            "raw_image_feature_columns": IMAGE_FEATURE_COLUMNS,
            "excluded_image_features": sorted(EXCLUDED_IMAGE_FEATURES),
            "excluded_image_feature_reasons": EXCLUDED_IMAGE_FEATURE_REASONS,
            "image_feature_groups": {
                extractor.name: list(extractor.columns) for extractor in extract_icon_features.FEATURE_EXTRACTORS
            },
            "image_feature_sections": image_feature_sections(),
            "mcdougall_numeric_columns": MCDOUGALL_NUMERIC_COLUMNS,
        },
        "records": records,
        "feature_columns": {variant: matrices[variant]["columns"] for variant in FEATURE_VARIANTS},
        "clusters": clusters,
        "feature_review": feature_review,
        "feature_explorer": build_feature_explorer(records, feature_by_id, feature_review),
    }
    (OUTPUT_DIR / "dashboard_data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def relative_to_dashboard(path: Path) -> str:
    return os.path.relpath(path, OUTPUT_DIR)


def write_index_html() -> None:
    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analysis Icon Clustering Dashboard</title>
  <script src="assets/plotly.min.js"></script>
  <style>
    :root {{ color-scheme: light; --border: #d8dde6; --muted: #5d6675; --panel: #f7f8fb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18202f; background: white; }}
    header {{ padding: 10px 18px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 18px; }}
    h1 {{ font-size: 18px; margin: 0; font-weight: 650; }}
    header span {{ color: var(--muted); font-size: 13px; }}
    .tab-nav {{ display: flex; gap: 6px; margin-left: auto; }}
    .tab-nav button {{ font-size: 13px; padding: 6px 10px; }}
    .tab-nav button.active {{ background: #18202f; color: white; border-color: #18202f; }}
    .view {{ display: none; }}
    .view.active {{ display: block; }}
    #clusteringView.active {{ display: grid; grid-template-columns: 300px minmax(520px, 1fr) 330px; min-height: calc(100vh - 52px); }}
    aside {{ border-right: 1px solid var(--border); padding: 14px; overflow: auto; max-height: calc(100vh - 52px); }}
    aside.right {{ border-left: 1px solid var(--border); border-right: 0; }}
    section.control {{ margin-bottom: 18px; }}
    h2 {{ font-size: 13px; margin: 0 0 8px; text-transform: uppercase; color: #3d4656; letter-spacing: .04em; }}
    label {{ display: block; font-size: 13px; margin: 7px 0; }}
    select, input[type="range"], input[type="search"] {{ width: 100%; }}
    select, input[type="search"] {{ min-height: 30px; border: 1px solid var(--border); border-radius: 6px; background: white; padding: 4px 6px; }}
    button {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 6px 9px; color: #18202f; cursor: pointer; }}
    button:hover {{ background: var(--panel); }}
    .button-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }}
    .selected-pills {{ display: flex; gap: 5px; flex-wrap: wrap; margin: 6px 0 10px; min-height: 20px; }}
    .filter-pill {{ display: inline-flex; align-items: center; gap: 5px; max-width: 100%; padding: 3px 7px; border: 1px solid #cbd2de; border-radius: 999px; background: #eef2f7; font-size: 12px; color: #18202f; }}
    .filter-pill button {{ border: 0; background: transparent; padding: 0; width: 16px; height: 16px; line-height: 14px; font-size: 14px; color: #4d5665; }}
    .filter-pill button:hover {{ background: #dde3ec; border-radius: 999px; }}
    .checklist {{ display: grid; gap: 8px; }}
    .preset-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }}
    .feature-section {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 8px; }}
    .feature-head {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
    .feature-head b {{ font-size: 13px; }}
    .feature-description {{ color: var(--muted); font-size: 12px; line-height: 1.35; margin: 4px 0 6px; }}
    .feature-interpretation {{ color: #3d4656; font-size: 12px; line-height: 1.35; margin: 6px 0 8px; padding: 6px 7px; border-left: 3px solid #d8dde6; background: #fbfcfe; }}
    .feature-interpretation div + div {{ margin-top: 3px; }}
    .feature-interpretation b {{ font-weight: 650; }}
    .feature-actions {{ display: flex; gap: 4px; flex-shrink: 0; }}
    .feature-actions button, .preset-row button {{ padding: 3px 6px; font-size: 12px; }}
    .feature-list {{ max-height: 150px; overflow: auto; border-top: 1px solid #edf0f4; padding-top: 4px; }}
    .feature-list label {{ margin: 4px 0; line-height: 1.3; }}
    .feature-choice {{ position: relative; display: flex; align-items: flex-start; gap: 6px; padding: 3px 4px; border-radius: 4px; }}
    .feature-choice:hover, .feature-choice:focus-within {{ background: #f3f5f9; }}
    .feature-tooltip {{ display: none; position: fixed; z-index: 30; width: 280px; padding: 9px 10px; border-radius: 6px; background: #18202f; color: white; font-size: 12px; line-height: 1.35; box-shadow: 0 8px 24px rgba(24,32,47,.22); pointer-events: none; }}
    .feature-tooltip b {{ display: block; font-size: 13px; margin-bottom: 4px; }}
    .feature-tooltip .tooltip-section {{ color: #c8d2e2; margin-bottom: 5px; }}
    .feature-tooltip .tooltip-label {{ color: #c8d2e2; margin-top: 7px; }}
    .method-note {{ margin-top: 5px; font-size: 12px; line-height: 1.35; color: var(--muted); }}
    .plot-wrap {{ padding: 10px; min-width: 0; }}
    #scatter {{ width: 100%; height: calc(100vh - 76px); }}
    #hoverPreview {{ position: fixed; z-index: 20; display: none; pointer-events: none; max-width: 360px; max-height: calc(100vh - 16px); overflow: hidden; padding: 8px 10px; border-radius: 0; background: #a000a8; color: white; box-shadow: none; font-size: 18px; line-height: 1.28; }}
    #hoverPreview img {{ width: 84px; height: 84px; object-fit: contain; border: 1px solid rgba(255,255,255,.65); background: white; margin: 8px 10px 2px 0; vertical-align: top; }}
    #hoverPreview b {{ font-size: 18px; }}
    #hoverPreview .hover-grid {{ display: grid; grid-template-columns: 94px minmax(0, 1fr); align-items: start; gap: 0; margin-bottom: 4px; }}
    #hoverPreview .hover-meta {{ min-width: 0; }}
    #hoverPreview .hover-features {{ clear: both; }}
    #hoverPreview .feature-group-detail h4 {{ color: white; }}
    #hoverPreview .feature-group-detail p, #hoverPreview .muted {{ color: rgba(255,255,255,.82); }}
    #hoverPreview table {{ color: white; }}
    #hoverPreview td {{ border-bottom: 1px solid rgba(255,255,255,.42); }}
    #hoverPreview td:last-child {{ color: white; font-variant-numeric: tabular-nums; }}
    .detail-img {{ width: 96px; height: 96px; object-fit: contain; border: 1px solid var(--border); background: white; }}
    .muted {{ color: var(--muted); }}
    .pill {{ display: inline-block; padding: 2px 6px; border: 1px solid var(--border); border-radius: 999px; margin: 2px; font-size: 12px; background: var(--panel); }}
    .summary-cluster {{ border: 1px solid var(--border); border-radius: 8px; margin: 8px 0; background: white; overflow: hidden; }}
    .summary-cluster summary {{ cursor: pointer; padding: 8px; list-style-position: inside; }}
    .summary-cluster summary:hover {{ background: var(--panel); }}
    .summary-cluster[open] summary {{ border-bottom: 1px solid var(--border); background: #fbfcfe; }}
    .summary-details {{ padding: 8px; }}
    .summary-explain {{ margin-top: 4px; font-size: 12px; color: #3d4656; }}
    .rep-icons {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(72px, 1fr)); gap: 8px; margin-top: 8px; }}
    .rep-icon {{ min-width: 0; }}
    .rep-icon img {{ width: 72px; height: 72px; object-fit: contain; border: 1px solid var(--border); background: white; display: block; }}
    .rep-icon span {{ display: block; margin-top: 3px; font-size: 11px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .feature-group-detail {{ margin: 10px 0; }}
    .feature-group-detail h4 {{ font-size: 13px; margin: 0 0 2px; }}
    .feature-group-detail p {{ margin: 0 0 4px; font-size: 12px; color: var(--muted); line-height: 1.35; }}
    .feature-group-detail .family-reading {{ color: #3d4656; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    td {{ border-bottom: 1px solid #edf0f4; padding: 4px 0; vertical-align: top; }}
    td:last-child {{ text-align: right; color: #334; }}
    .feature-review, .feature-explorer, .feature-groups {{ padding: 16px 18px 24px; }}
    .review-toolbar, .explorer-toolbar {{ display: flex; align-items: end; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }}
    .review-toolbar label, .explorer-toolbar label {{ min-width: 180px; margin: 0; }}
    .explorer-toolbar label:nth-child(2) {{ min-width: 240px; }}
    .explorer-toolbar label:nth-child(3) {{ min-width: 280px; flex: 1; }}
    .feature-groups-header {{ max-width: 980px; margin-bottom: 16px; }}
    .feature-groups-header h2 {{ margin: 0 0 6px; font-size: 20px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .feature-groups-header p {{ margin: 0; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .feature-groups-content {{ display: grid; gap: 14px; max-width: 1280px; }}
    .feature-family-overview {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 14px; }}
    .feature-family-overview h2 {{ margin: 0 0 6px; font-size: 18px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .feature-family-overview p {{ margin: 0 0 10px; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .family-overview-table-wrap {{ overflow: auto; border: 1px solid var(--border); border-radius: 6px; }}
    .family-overview-table {{ min-width: 760px; }}
    .family-overview-table th {{ background: #f4f6fa; border-bottom: 1px solid var(--border); padding: 7px 8px; text-align: left; font-size: 12px; color: #3d4656; }}
    .family-overview-table td {{ padding: 10px 8px; text-align: left; vertical-align: top; font-size: 13px; line-height: 1.45; }}
    .family-overview-table td:last-child {{ text-align: left; color: #334; }}
    .family-overview-table b {{ color: #18202f; }}
    .feature-group-panel {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 14px; }}
    .feature-group-panel h2 {{ margin: 0; font-size: 16px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .feature-group-panel p {{ margin: 7px 0 0; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .feature-group-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; margin-bottom: 10px; }}
    .feature-group-count {{ flex-shrink: 0; color: var(--muted); font-size: 12px; }}
    .feature-reading-grid {{ display: grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap: 10px; margin: 12px 0; }}
    .feature-reading-item {{ border-left: 3px solid #d8dde6; background: #fbfcfe; padding: 8px 9px; font-size: 12px; line-height: 1.4; color: #3d4656; }}
    .feature-reading-item b {{ display: block; margin-bottom: 3px; color: #18202f; }}
    .feature-group-table-wrap {{ overflow: auto; border: 1px solid var(--border); border-radius: 6px; }}
    .feature-group-table {{ min-width: 920px; }}
    .feature-group-table th {{ background: #f4f6fa; border-bottom: 1px solid var(--border); padding: 7px 8px; text-align: left; font-size: 12px; color: #3d4656; }}
    .feature-group-table td {{ padding: 7px 8px; text-align: left; }}
    .feature-group-table td:last-child {{ text-align: left; color: #334; }}
    .feature-id {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; color: var(--muted); }}
    .review-summary {{ display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px; }}
    .review-metric {{ border: 1px solid var(--border); border-radius: 6px; padding: 10px; background: #fbfcfe; }}
    .review-metric b {{ display: block; font-size: 22px; margin-bottom: 2px; }}
    .review-metric span {{ color: var(--muted); font-size: 12px; }}
    .review-layout {{ display: grid; grid-template-columns: minmax(560px, 1fr) 340px; gap: 16px; align-items: start; }}
    .review-panel {{ min-width: 0; }}
    .review-panel h2 {{ margin-top: 0; }}
    .review-table-wrap {{ overflow: auto; border: 1px solid var(--border); border-radius: 6px; background: white; margin-bottom: 16px; max-height: 360px; }}
    .review-table {{ min-width: 760px; }}
    .review-table th {{ position: sticky; top: 0; background: #f4f6fa; border-bottom: 1px solid var(--border); padding: 7px 8px; text-align: left; font-size: 12px; color: #3d4656; }}
    .review-table td {{ padding: 6px 8px; text-align: left; }}
    .review-table td:last-child {{ text-align: left; }}
    .review-row-button {{ border: 0; background: transparent; padding: 0; color: #18202f; text-align: left; font-weight: 600; }}
    .review-row-button:hover {{ background: transparent; text-decoration: underline; }}
    .band {{ display: inline-block; min-width: 70px; padding: 2px 6px; border-radius: 999px; font-size: 11px; text-align: center; border: 1px solid var(--border); }}
    .band-high {{ background: #ffe8e1; border-color: #f0b7a6; color: #8d2e16; }}
    .band-moderate {{ background: #fff4d7; border-color: #e6cd86; color: #725300; }}
    .band-low {{ background: #edf7ef; border-color: #b7d9bf; color: #245b31; }}
    .review-detail {{ border: 1px solid var(--border); border-radius: 6px; padding: 12px; background: white; position: sticky; top: 12px; }}
    .review-detail h3 {{ margin: 0 0 4px; font-size: 16px; }}
    .review-detail p {{ font-size: 13px; line-height: 1.4; }}
    .partner-list {{ margin-top: 10px; }}
    .partner-list div {{ display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid #edf0f4; padding: 5px 0; font-size: 12px; }}
    .explorer-content {{ max-width: 1280px; }}
    .explorer-layout {{ display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }}
    .explorer-main, .explorer-side {{ min-width: 0; }}
    .explorer-header {{ margin-bottom: 14px; }}
    .explorer-header h2 {{ margin: 0 0 6px; font-size: 20px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .explorer-header p {{ max-width: 820px; margin: 8px 0 0; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .explorer-stats {{ display: grid; grid-template-columns: repeat(6, minmax(100px, 1fr)); gap: 8px; margin-bottom: 14px; }}
    .explorer-stat {{ border: 1px solid var(--border); border-radius: 6px; background: #fbfcfe; padding: 8px; min-width: 0; }}
    .explorer-stat b {{ display: block; font-size: 14px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .explorer-stat span {{ color: var(--muted); font-size: 11px; }}
    .example-section {{ margin-bottom: 18px; }}
    .example-section h3 {{ display: flex; align-items: center; gap: 7px; margin: 0 0 8px; font-size: 14px; }}
    .value-band-dot {{ width: 9px; height: 9px; border-radius: 999px; background: #8a94a5; flex: 0 0 auto; }}
    .example-section[data-band="low"] .value-band-dot {{ background: #2f855a; }}
    .example-section[data-band="medium"] .value-band-dot {{ background: #d69e2e; }}
    .example-section[data-band="high"] .value-band-dot {{ background: #c53030; }}
    .example-strip {{ display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 10px; }}
    .example-card {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 8px; min-width: 0; }}
    .example-card img {{ width: 100%; aspect-ratio: 1; object-fit: contain; border: 1px solid #edf0f4; background: white; display: block; }}
    .example-card b {{ display: block; margin-top: 6px; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .example-card span {{ display: block; color: var(--muted); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .example-card code {{ display: block; margin-top: 4px; font-size: 11px; color: #18202f; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .correlation-panel {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 12px; position: sticky; top: 12px; }}
    .correlation-panel h3 {{ margin: 0 0 8px; font-size: 15px; }}
    .correlation-item {{ border-top: 1px solid #edf0f4; padding: 9px 0; }}
    .correlation-item:first-of-type {{ border-top: 0; }}
    .correlation-item span {{ display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }}
    .correlation-item button {{ margin: 3px 0; border: 0; background: transparent; padding: 0; color: #18202f; font-weight: 650; text-align: left; }}
    .correlation-item button:hover {{ background: transparent; text-decoration: underline; }}
    .correlation-item b {{ display: block; font-size: 13px; font-variant-numeric: tabular-nums; }}
    @media (max-width: 980px) {{
      #clusteringView.active {{ grid-template-columns: 1fr; }}
      aside, aside.right {{ max-height: none; border: 0; border-bottom: 1px solid var(--border); }}
      .review-layout, .explorer-layout {{ grid-template-columns: 1fr; }}
      .review-detail, .correlation-panel {{ position: static; }}
      .feature-reading-grid {{ grid-template-columns: 1fr; }}
      .explorer-stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .example-strip {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Analysis Icon Clustering Dashboard</h1>
    <span id="datasetSummary">Loading data...</span>
    <nav class="tab-nav" aria-label="Dashboard views">
      <button type="button" class="active" data-view="clustering">Clustering</button>
      <button type="button" data-view="featureGroups">Feature Groups</button>
      <button type="button" data-view="featureExplorer">Feature Values</button>
      <button type="button" data-view="featureReview">Feature Review</button>
    </nav>
  </header>
  <main id="clusteringView" class="view active">
    <aside>
      <section class="control">
        <h2>Feature Variant</h2>
        <label><select id="variantSelect"></select></label>
      </section>
      <section class="control">
        <h2>Clustering</h2>
        <label>Method<select id="methodSelect"><option value="kmeans">K-Means clustering</option><option value="hierarchical">Hierarchical clustering</option></select></label>
        <div class="method-note" id="methodNote"></div>
        <label>Cluster count<select id="kSelect"></select></label>
        <label>Color by<select id="colorSelect"></select></label>
      </section>
      <section class="control">
        <h2>Image Features</h2>
        <div class="preset-row" id="featurePresets"></div>
        <div class="checklist" id="featureChecks"></div>
      </section>
      <section class="control">
        <h2>Filters</h2>
        <label>Icon sets<select id="setFilter" multiple size="8"></select></label>
        <div class="selected-pills" id="setFilterPills"></div>
        <div class="button-row">
          <button type="button" id="clearSetFilter">Clear sets</button>
          <button type="button" id="resetFilters">Reset filters</button>
        </div>
      </section>
    </aside>
    <div class="plot-wrap"><div id="scatter"></div></div>
    <aside class="right">
      <section class="control">
        <h2>Selected Icon</h2>
        <div id="iconDetail" class="muted">Click a point to inspect an icon.</div>
      </section>
      <section class="control">
        <h2>Cluster Summary</h2>
        <div id="clusterSummary"></div>
      </section>
    </aside>
  </main>
  <section id="featureReviewView" class="view feature-review">
    <div class="review-toolbar">
      <label>Feature ranking<select id="featureReviewSort">
        <option value="redundancy">Strongest redundancy</option>
        <option value="group">Group</option>
        <option value="label">Feature name</option>
      </select></label>
      <label>Pair threshold<select id="featureReviewThreshold">
        <option value="high">High only</option>
        <option value="moderate" selected>Moderate+</option>
        <option value="all">All pairs</option>
      </select></label>
    </div>
    <div class="review-summary" id="featureReviewSummary"></div>
    <div class="review-layout">
      <div class="review-panel">
        <h2>Feature Ranking</h2>
        <div class="review-table-wrap"><table class="review-table" id="featureRankingTable"></table></div>
        <h2>Redundant Feature Pairs</h2>
        <div class="review-table-wrap"><table class="review-table" id="featurePairTable"></table></div>
      </div>
      <aside class="review-detail" id="featureReviewDetail">
        <span class="muted">Select a feature to inspect redundancy evidence.</span>
      </aside>
    </div>
  </section>
  <section id="featureGroupsView" class="view feature-groups">
    <div class="feature-groups-header">
      <h2>Feature Groups</h2>
      <p>Each visual family shows only its selected 1st and 2nd representative.</p>
    </div>
    <div class="feature-groups-content" id="featureGroupsContent">
      <span class="muted">Loading feature groups...</span>
    </div>
  </section>
  <section id="featureExplorerView" class="view feature-explorer">
    <div class="explorer-header">
      <h2>Feature Values</h2>
      <p>Browse the 1st and 2nd strength-ranked complementary representatives from each visual family and compare icons with low, medium, and high values.</p>
    </div>
    <div class="explorer-toolbar">
      <label>Search feature<input id="featureExplorerSearch" type="search" placeholder="Search by name"></label>
      <label>Feature<select id="featureExplorerFeature"></select></label>
    </div>
    <div class="explorer-content" id="featureExplorerContent">
      <span class="muted">Loading feature examples...</span>
    </div>
  </section>
  <div id="hoverPreview"></div>
  <script>
    let dashboard = null;
    let selectedIconId = null;
    const computedCache = new Map();

    const state = {{
      variant: "image",
      method: "kmeans",
      k: "{PRIMARY_K}",
      color: "cluster",
      activeFeatures: new Set(),
      setFilter: new Set()
    }};
    const reviewState = {{
      view: "clustering",
      group: "all",
      sort: "redundancy",
      threshold: "moderate",
      selectedFeatureId: null
    }};
    const explorerState = {{
      group: "all",
      search: "",
      selectedFeatureId: null
    }};

    fetch("dashboard_data.json").then(r => r.json()).then(data => {{
      dashboard = data;
      initializeControls();
      render();
    }});

    function initializeControls() {{
      document.getElementById("datasetSummary").textContent =
        `${{dashboard.metadata.row_count}} icons, ${{dashboard.metadata.per_set_sample_size}} random per dataset`;

      installViewTabs();
      fillSelect("variantSelect", dashboard.metadata.feature_variants.map(v => [v, title(v)]), state.variant);
      fillSelect("kSelect", dashboard.metadata.k_values.map(k => [String(k), String(k)]), state.k);
      fillColorSelect("colorSelect", state.color);
      renderMethodNote();

      renderFeatureControls();
      initializeFeatureReviewControls();
      initializeFeatureExplorerControls();

      const sets = unique(dashboard.records.map(r => r.set_name)).sort();
      fillSelect("setFilter", sets.map(v => [v, v]), "", true);
      installToggleMultiSelect("setFilter", "setFilter");

      document.getElementById("variantSelect").addEventListener("change", e => {{ state.variant = e.target.value; render(); }});
      document.getElementById("methodSelect").addEventListener("change", e => {{ state.method = e.target.value; renderMethodNote(); render(); }});
      document.getElementById("kSelect").addEventListener("change", e => {{ state.k = e.target.value; render(); }});
      document.getElementById("colorSelect").addEventListener("change", e => {{ state.color = e.target.value; render(); }});
      document.getElementById("setFilter").addEventListener("change", e => {{
        state.setFilter = new Set(Array.from(e.target.selectedOptions).map(o => o.value));
        renderFilterPills();
        render();
      }});
      document.getElementById("clearSetFilter").addEventListener("click", () => clearSelectFilter("setFilter", "setFilter"));
      document.getElementById("resetFilters").addEventListener("click", resetFilters);
      renderFilterPills();
      renderFeatureGroups();
      renderFeatureReview();
      renderFeatureExplorer();
    }}

    function installViewTabs() {{
      document.querySelectorAll(".tab-nav button").forEach(button => {{
        button.addEventListener("click", () => activateView(button.dataset.view));
      }});
    }}

    function activateView(view) {{
      reviewState.view = view;
      document.querySelectorAll(".tab-nav button").forEach(item => item.classList.toggle("active", item.dataset.view === view));
      document.getElementById("clusteringView").classList.toggle("active", view === "clustering");
      document.getElementById("featureGroupsView").classList.toggle("active", view === "featureGroups");
      document.getElementById("featureReviewView").classList.toggle("active", view === "featureReview");
      document.getElementById("featureExplorerView").classList.toggle("active", view === "featureExplorer");
      hideHoverPreview();
      if (view === "clustering") render();
      if (view === "featureGroups") renderFeatureGroups();
      if (view === "featureReview") renderFeatureReview();
      if (view === "featureExplorer") renderFeatureExplorer();
    }}

    function initializeFeatureReviewControls() {{
      document.getElementById("featureReviewSort").addEventListener("change", event => {{
        reviewState.sort = event.target.value;
        renderFeatureReview();
      }});
      document.getElementById("featureReviewThreshold").addEventListener("change", event => {{
        reviewState.threshold = event.target.value;
        renderFeatureReview();
      }});
    }}

    function initializeFeatureExplorerControls() {{
      document.getElementById("featureExplorerSearch").addEventListener("input", event => {{
        explorerState.search = event.target.value;
        explorerState.selectedFeatureId = null;
        renderFeatureExplorer();
      }});
      document.getElementById("featureExplorerFeature").addEventListener("change", event => {{
        explorerState.selectedFeatureId = event.target.value;
        renderFeatureExplorerDetail();
      }});
    }}

    function renderMethodNote() {{
      const note = document.getElementById("methodNote");
      if (!note) return;
      note.textContent = state.method === "hierarchical"
        ? "Hierarchical clustering builds nearest-neighbor links between icons, then cuts the tree at the selected cluster count."
        : "K-Means clustering groups icons around cluster centers at the selected cluster count.";
    }}

    function featureSections() {{
      return dashboard.metadata.image_feature_sections || [{{
        id: "image",
        title: "Image Features",
        description: "Extracted visual features.",
        features: dashboard.metadata.image_feature_columns.map(feature => ({{
          id: feature,
          label: title(feature),
          group: "image",
          group_title: "Image Features",
          meaning: "Extracted visual feature."
        }}))
      }}];
    }}

    function visibleFeatureSections() {{
      return featureSections().filter(section => section.visible !== false);
    }}

    function allFeatureIds() {{
      return featureSections().flatMap(section => section.features.map(feature => feature.id));
    }}

    function visibleFeatureIds() {{
      return visibleFeatureSections().flatMap(section => section.features.map(feature => feature.id));
    }}

    function selectedFeatureIds() {{
      const ordered = visibleFeatureIds().filter(feature => state.activeFeatures.has(feature));
      return ordered;
    }}

    function sectionById(sectionId) {{
      return visibleFeatureSections().find(section => section.id === sectionId);
    }}

    function featureInfo(featureId) {{
      for (const section of featureSections()) {{
        const feature = section.features.find(item => item.id === featureId);
        if (feature) return feature;
      }}
      return {{id: featureId, label: title(featureId), group: "", group_title: "", meaning: ""}};
    }}

    function renderFeatureControls() {{
      const presets = document.getElementById("featurePresets");
      const checks = document.getElementById("featureChecks");
      presets.innerHTML = [
        '<button type="button" data-feature-preset="all">All</button>',
        ...visibleFeatureSections().map(section => `<button type="button" data-feature-preset="${{section.id}}">${{escapeHtml(section.title.replace(" Features", ""))}}</button>`)
      ].join("");
      checks.innerHTML = visibleFeatureSections().map(section => `
        <div class="feature-section" data-section-id="${{escapeHtml(section.id)}}">
          <div class="feature-head">
            <b>${{escapeHtml(section.title)}}</b>
            <span class="feature-actions">
              <button type="button" data-feature-action="select" data-section-id="${{escapeHtml(section.id)}}">Select all</button>
              <button type="button" data-feature-action="clear" data-section-id="${{escapeHtml(section.id)}}">Clear</button>
            </span>
          </div>
          <div class="feature-description">${{escapeHtml(section.description)}}</div>
          <div class="feature-interpretation">
            <div><b>Human perception:</b> ${{escapeHtml(section.perception || "This family describes a perceptual visual channel.")}}</div>
            <div><b>Low:</b> ${{escapeHtml(section.low_value || "Lower values mean less of this family signal.")}}</div>
            <div><b>High:</b> ${{escapeHtml(section.high_value || "Higher values mean more of this family signal.")}}</div>
          </div>
          <div class="feature-list">
            ${{section.features.map(feature => `
              <label class="feature-choice" data-feature-id="${{escapeHtml(feature.id)}}" data-feature-label="${{escapeHtml(feature.label)}}" data-feature-group="${{escapeHtml(feature.group_title)}}" data-feature-meaning="${{escapeHtml(feature.meaning)}}" data-feature-visual="${{escapeHtml((feature.visual_categorizations || []).join(", "))}}" data-feature-examples="${{escapeHtml((feature.visual_category_labels || []).join("; "))}}" data-feature-reason="${{escapeHtml(feature.category_reason)}}">
                <input class="feature-toggle" type="checkbox" value="${{escapeHtml(feature.id)}}" data-feature-id="${{escapeHtml(feature.id)}}">
                <span>${{escapeHtml(feature.label)}}</span>
              </label>`).join("")}}
          </div>
        </div>`).join("");

      presets.addEventListener("click", event => {{
        const button = event.target.closest("button[data-feature-preset]");
        if (!button) return;
        const preset = button.dataset.featurePreset;
        const section = sectionById(preset);
        setActiveFeatures(preset === "all" ? visibleFeatureIds() : section.features.map(feature => feature.id));
      }});

      checks.addEventListener("click", event => {{
        const button = event.target.closest("button[data-feature-action]");
        if (!button) return;
        const section = sectionById(button.dataset.sectionId);
        if (!section) return;
        const next = new Set(state.activeFeatures);
        section.features.forEach(feature => {{
          if (button.dataset.featureAction === "select") next.add(feature.id);
          if (button.dataset.featureAction === "clear") next.delete(feature.id);
        }});
        setActiveFeatures(Array.from(next));
      }});

      checks.addEventListener("change", event => {{
        if (!event.target.classList.contains("feature-toggle")) return;
        state.activeFeatures = new Set(Array.from(checks.querySelectorAll(".feature-toggle:checked")).map(input => input.value));
        computedCache.clear();
        render();
      }});

      checks.addEventListener("mouseover", event => {{
        const choice = event.target.closest(".feature-choice");
        if (choice) showFeatureTooltip(choice, event);
      }});
      checks.addEventListener("mousemove", event => {{
        if (event.target.closest(".feature-choice")) moveFeatureTooltip(event);
      }});
      checks.addEventListener("mouseout", event => {{
        if (event.target.closest(".feature-choice")) hideFeatureTooltip();
      }});
      checks.addEventListener("focusin", event => {{
        const choice = event.target.closest(".feature-choice");
        if (choice) showFeatureTooltip(choice, null);
      }});
      checks.addEventListener("focusout", hideFeatureTooltip);

      syncFeatureCheckboxes();
    }}

    function showFeatureTooltip(choice, event) {{
      let tooltip = document.getElementById("featureTooltip");
      if (!tooltip) {{
        tooltip = document.createElement("div");
        tooltip.id = "featureTooltip";
        tooltip.className = "feature-tooltip";
        document.body.appendChild(tooltip);
      }}
      tooltip.innerHTML = `
        <b>${{escapeHtml(choice.dataset.featureLabel)}}</b>
        <div class="tooltip-section">${{escapeHtml(choice.dataset.featureGroup)}}</div>
        <div>${{escapeHtml(choice.dataset.featureMeaning)}}</div>
        ${{choice.dataset.featureVisual ? `<div class="tooltip-label">Visual categorization</div><div>${{escapeHtml(choice.dataset.featureVisual)}}</div>` : ""}}
        ${{choice.dataset.featureExamples ? `<div class="tooltip-label">Example labels</div><div>${{escapeHtml(choice.dataset.featureExamples)}}</div>` : ""}}
        <div style="margin-top:6px;">${{escapeHtml(choice.dataset.featureReason)}}</div>`;
      tooltip.style.display = "block";
      if (event) {{
        moveFeatureTooltip(event);
      }} else {{
        const rect = choice.getBoundingClientRect();
        placeFeatureTooltip(rect.right + 12, rect.top);
      }}
    }}

    function moveFeatureTooltip(event) {{
      placeFeatureTooltip(event.clientX + 14, event.clientY + 14);
    }}

    function placeFeatureTooltip(x, y) {{
      const tooltip = document.getElementById("featureTooltip");
      if (!tooltip) return;
      const width = tooltip.offsetWidth || 280;
      const height = tooltip.offsetHeight || 120;
      const left = Math.min(x, window.innerWidth - width - 8);
      const top = Math.min(y, window.innerHeight - height - 8);
      tooltip.style.left = `${{Math.max(8, left)}}px`;
      tooltip.style.top = `${{Math.max(8, top)}}px`;
    }}

    function hideFeatureTooltip() {{
      const tooltip = document.getElementById("featureTooltip");
      if (tooltip) tooltip.style.display = "none";
    }}

    function renderFeatureGroups() {{
      const container = document.getElementById("featureGroupsContent");
      if (!container) return;
      const sections = visibleFeatureSections();
      if (!sections.length) {{
        container.innerHTML = '<span class="muted">No feature group metadata is available.</span>';
        return;
      }}
      const representatives = (dashboard.feature_explorer && dashboard.feature_explorer.features) || [];
      const representativesByFamily = new Map();
      representatives.forEach(feature => {{
        if (!representativesByFamily.has(feature.group)) representativesByFamily.set(feature.group, []);
        representativesByFamily.get(feature.group).push(feature);
      }});
      const overview = `
        <section class="feature-family-overview">
          <h2>Selected Family Representatives</h2>
          <p>Strength sets the order; direct pairwise Spearman only screens redundancy.</p>
          <div class="family-overview-table-wrap">
            <table class="family-overview-table">
              <thead><tr><th>Feature family</th><th>1st feature</th><th>2nd feature</th><th>Pair |ρ|</th></tr></thead>
              <tbody>
                ${{sections.map(section => {{
                  const selected = (representativesByFamily.get(section.id) || [])
                    .slice()
                    .sort((a, b) => Number(a.selection.rank_in_family) - Number(b.selection.rank_in_family));
                  const first = selected.find(feature => Number(feature.selection.rank_in_family) === 1);
                  const second = selected.find(feature => Number(feature.selection.rank_in_family) === 2);
                  return `
                    <tr>
                      <td><b>${{escapeHtml(section.human_category || section.title.replace(" Features", ""))}}</b></td>
                      <td>${{first ? escapeHtml(first.label) : "—"}}</td>
                      <td>${{second ? escapeHtml(second.label) : "—"}}</td>
                      <td>${{first && first.selection.pair_abs_correlation !== null ? formatNumber(first.selection.pair_abs_correlation) : "—"}}</td>
                    </tr>`;
                }}).join("")}}
              </tbody>
            </table>
          </div>
        </section>`;
      container.innerHTML = overview;
    }}

    function setActiveFeatures(featureIds) {{
      state.activeFeatures = new Set(featureIds);
      syncFeatureCheckboxes();
      computedCache.clear();
      render();
    }}

    function syncFeatureCheckboxes() {{
      document.querySelectorAll(".feature-toggle").forEach(input => {{
        input.checked = state.activeFeatures.has(input.value);
      }});
    }}

    function renderFeatureReview() {{
      const review = dashboard.feature_review;
      if (!review) {{
        document.getElementById("featureReviewSummary").innerHTML = "";
        document.getElementById("featureRankingTable").innerHTML = "";
        document.getElementById("featurePairTable").innerHTML = "";
        document.getElementById("featureReviewDetail").innerHTML = '<span class="muted">No feature review data is available.</span>';
        return;
      }}
      renderFeatureReviewSummary(review);
      const features = filteredReviewFeatures(review);
      const pairs = filteredReviewPairs(review);
      if (!reviewState.selectedFeatureId || !features.some(feature => feature.feature_id === reviewState.selectedFeatureId)) {{
        reviewState.selectedFeatureId = features[0] ? features[0].feature_id : null;
      }}
      renderFeatureRankingTable(features);
      renderFeaturePairTable(pairs);
      renderFeatureReviewDetail(review);
    }}

    function renderFeatureReviewSummary(review) {{
      const summary = review.summary || {{}};
      document.getElementById("featureReviewSummary").innerHTML = [
        ["Features", summary.feature_count || 0],
        ["High redundancy pairs", summary.high_pair_count || 0],
        ["Moderate pairs", summary.moderate_pair_count || 0],
        ["Source rows", (review.metadata || {{}}).row_count || 0]
      ].map(([label, value]) => `<div class="review-metric"><b>${{escapeHtml(value)}}</b><span>${{escapeHtml(label)}}</span></div>`).join("");
    }}

    function filteredReviewFeatures(review) {{
      const sorted = review.features.slice();
      sorted.sort((a, b) => {{
        if (reviewState.sort === "label") return a.label.localeCompare(b.label);
        if (reviewState.sort === "group") return (a.group_title || "").localeCompare(b.group_title || "") || a.label.localeCompare(b.label);
        return Number(b.strongest_abs_correlation || 0) - Number(a.strongest_abs_correlation || 0) || a.label.localeCompare(b.label);
      }});
      return sorted;
    }}

    function filteredReviewPairs(review) {{
      return review.pairs.filter(pair => {{
        if (reviewState.threshold === "high") return pair.band === "high";
        if (reviewState.threshold === "moderate") return pair.band === "high" || pair.band === "moderate";
        return true;
      }});
    }}

    function renderFeatureRankingTable(features) {{
      const table = document.getElementById("featureRankingTable");
      if (!features.length) {{
        table.innerHTML = '<tbody><tr><td class="muted">No features match this filter.</td></tr></tbody>';
        return;
      }}
      const rows = features.map(feature => `
        <tr>
          <td><button class="review-row-button" type="button" data-feature-id="${{escapeHtml(feature.feature_id)}}">${{escapeHtml(feature.label)}}</button></td>
          <td>${{escapeHtml(feature.group_title || "")}}</td>
          <td><span class="band band-${{escapeHtml(feature.redundancy_band)}}">${{escapeHtml(bandLabel(feature.redundancy_band))}}</span></td>
          <td>${{formatNumber(feature.strongest_abs_correlation)}}</td>
          <td>${{escapeHtml(feature.strongest_partner_label || "")}}</td>
          <td>${{formatNumber(feature.std)}}</td>
          <td>${{escapeHtml(feature.missing_count)}}</td>
        </tr>`).join("");
      table.innerHTML = `
        <thead><tr>
          <th>Feature</th><th>Group</th><th>Band</th><th>Strongest |rho|</th><th>Strongest partner</th><th>Std</th><th>Missing</th>
        </tr></thead><tbody>${{rows}}</tbody>`;
      table.querySelectorAll("button[data-feature-id]").forEach(button => {{
        button.addEventListener("click", () => {{
          reviewState.selectedFeatureId = button.dataset.featureId;
          renderFeatureReviewDetail(dashboard.feature_review);
        }});
      }});
    }}

    function renderFeaturePairTable(pairs) {{
      const table = document.getElementById("featurePairTable");
      if (!pairs.length) {{
        table.innerHTML = '<tbody><tr><td class="muted">No feature pairs match this threshold.</td></tr></tbody>';
        return;
      }}
      const rows = pairs.map(pair => `
        <tr>
          <td>${{escapeHtml(pair.feature_a_label)}}</td>
          <td>${{escapeHtml(pair.feature_b_label)}}</td>
          <td><span class="band band-${{escapeHtml(pair.band)}}">${{escapeHtml(bandLabel(pair.band))}}</span></td>
          <td>${{formatSigned(pair.correlation)}}</td>
          <td>${{pair.shared_group ? "Same" : "Different"}}</td>
          <td>${{escapeHtml(pair.pair_count)}}</td>
        </tr>`).join("");
      table.innerHTML = `
        <thead><tr>
          <th>Feature A</th><th>Feature B</th><th>Band</th><th>Spearman rho</th><th>Group</th><th>N</th>
        </tr></thead><tbody>${{rows}}</tbody>`;
    }}

    function renderFeatureReviewDetail(review) {{
      const feature = review.features.find(item => item.feature_id === reviewState.selectedFeatureId);
      const detail = document.getElementById("featureReviewDetail");
      if (!feature) {{
        detail.innerHTML = '<span class="muted">Select a feature to inspect redundancy evidence.</span>';
        return;
      }}
      const partners = review.pairs
        .filter(pair => pair.feature_a === feature.feature_id || pair.feature_b === feature.feature_id)
        .sort((a, b) => Number(b.abs_correlation) - Number(a.abs_correlation))
        .slice(0, 8)
        .map(pair => {{
          const partnerLabel = pair.feature_a === feature.feature_id ? pair.feature_b_label : pair.feature_a_label;
          return `<div><span>${{escapeHtml(partnerLabel)}}</span><b>${{formatSigned(pair.correlation)}}</b></div>`;
        }}).join("");
      detail.innerHTML = `
        <h3>${{escapeHtml(feature.label)}}</h3>
        <span class="pill">${{escapeHtml(feature.group_title || "Image feature")}}</span>
        <span class="band band-${{escapeHtml(feature.redundancy_band)}}">${{escapeHtml(bandLabel(feature.redundancy_band))}}</span>
        <p>${{escapeHtml(feature.meaning || "Extracted image feature.")}}</p>
        <table>
          <tr><td>Strongest absolute correlation</td><td>${{formatNumber(feature.strongest_abs_correlation)}}</td></tr>
          <tr><td>Strongest partner</td><td>${{escapeHtml(feature.strongest_partner_label || "")}}</td></tr>
          <tr><td>Signed correlation</td><td>${{formatSigned(feature.strongest_correlation)}}</td></tr>
          <tr><td>Variance</td><td>${{formatNumber(feature.variance)}}</td></tr>
          <tr><td>Std</td><td>${{formatNumber(feature.std)}}</td></tr>
          <tr><td>Missing values</td><td>${{escapeHtml(feature.missing_count)}}</td></tr>
        </table>
        <div class="partner-list">
          <h2>Top Partners</h2>
          ${{partners || '<span class="muted">No correlation partners available.</span>'}}
        </div>`;
    }}

    function renderFeatureExplorer() {{
      const explorer = dashboard.feature_explorer;
      const container = document.getElementById("featureExplorerContent");
      if (!explorer) {{
        container.innerHTML = '<span class="muted">No feature explorer data is available.</span>';
        return;
      }}
      const features = filteredExplorerFeatures();
      if (!features.length) {{
        explorerState.selectedFeatureId = null;
        renderFeatureExplorerControls(features);
        container.innerHTML = '<span class="muted">No features match this filter.</span>';
        return;
      }}
      if (!explorerState.selectedFeatureId || !features.some(feature => feature.feature_id === explorerState.selectedFeatureId)) {{
        explorerState.selectedFeatureId = features[0].feature_id;
      }}
      renderFeatureExplorerControls(features);
      renderFeatureExplorerDetail();
    }}

    function filteredExplorerFeatures() {{
      const explorer = dashboard.feature_explorer;
      const query = explorerState.search.trim().toLowerCase();
      return (explorer.features || [])
        .filter(feature => !query || `${{feature.label}} ${{feature.feature_id}} ${{feature.group_title}}`.toLowerCase().includes(query));
    }}

    function renderFeatureExplorerControls(features) {{
      const options = features.map(feature => {{
        const rank = Number(feature.selection.rank_in_family) === 1 ? "1st" : "2nd";
        return [feature.feature_id, `${{feature.group_title || "Image feature"}} — ${{rank}}: ${{feature.label}}`];
      }});
      fillSelect("featureExplorerFeature", options, explorerState.selectedFeatureId || "");
    }}

    function renderFeatureExplorerDetail() {{
      const explorer = dashboard.feature_explorer;
      const feature = (explorer.features || []).find(item => item.feature_id === explorerState.selectedFeatureId);
      const container = document.getElementById("featureExplorerContent");
      if (!feature) {{
        container.innerHTML = '<span class="muted">Select a feature to inspect visual examples.</span>';
        return;
      }}
      const stats = [
        ["Min", feature.min],
        ["Mean", feature.mean],
        ["Max", feature.max],
        ["Variance", feature.variance],
        ["Std", feature.std],
        ["Missing", feature.missing_count]
      ].map(([label, value]) => `<div class="explorer-stat"><b>${{label === "Missing" ? escapeHtml(value) : formatNumber(value)}}</b><span>${{escapeHtml(label)}}</span></div>`).join("");
      const rankNumber = Number(feature.selection.rank_in_family);
      const rankLabel = rankNumber === 1 ? "1st" : rankNumber === 2 ? "2nd" : `#${{escapeHtml(rankNumber)}}`;
      const pairSummary = feature.selection.companion_feature_label
        ? ` · |ρ| with ${{escapeHtml(feature.selection.companion_feature_label)}} ${{formatNumber(feature.selection.pair_abs_correlation)}}`
        : "";
      container.innerHTML = `
        <div class="explorer-layout">
          <div class="explorer-main">
            <div class="explorer-header">
              <h2>${{escapeHtml(feature.label)}}</h2>
              <span class="pill">${{escapeHtml(feature.group_title || "Image feature")}}</span>
              <p>${{escapeHtml(feature.meaning || "Extracted image feature.")}}</p>
              <p class="muted">Selected ${{rankLabel}} in family${{pairSummary}}</p>
            </div>
            <div class="explorer-stats">${{stats}}</div>
            ${{exampleSectionHtml("Low Values", feature.examples.low, "Icons with the smallest raw values for this feature.", "low")}}
            ${{exampleSectionHtml("Medium Values", feature.examples.mean, "Icons closest to the average feature value.", "medium")}}
            ${{exampleSectionHtml("High Values", feature.examples.high, "Icons with the largest raw values for this feature.", "high")}}
          </div>
          <aside class="explorer-side">
            <div class="correlation-panel">
              <h3>Correlation Partners</h3>
              <p class="muted">Spearman rho values show how this feature moves with other features.</p>
              ${{correlationPartnerHtml("Strongest positive", feature.correlations.positive)}}
              ${{correlationPartnerHtml("Strongest negative", feature.correlations.negative)}}
            </div>
          </aside>
        </div>`;
      container.querySelectorAll("button[data-explorer-partner]").forEach(button => {{
        button.addEventListener("click", () => openFeatureInExplorer(button.dataset.explorerPartner));
      }});
    }}

    function exampleSectionHtml(titleText, examples, description, band) {{
      const cards = (examples || []).map(example => `
        <div class="example-card">
          <img src="${{escapeHtml(example.normalized_path)}}" alt="">
          <b title="${{escapeHtml(example.label)}}">${{escapeHtml(example.label || example.icon_id)}}</b>
          <span title="${{escapeHtml(example.set_name)}}">${{escapeHtml(example.set_name || "Unknown set")}}</span>
          <code>${{formatFeatureValue(example.value)}}</code>
        </div>`).join("");
      return `<section class="example-section" data-band="${{escapeHtml(band || "")}}">
        <h3><span class="value-band-dot" aria-hidden="true"></span>${{escapeHtml(titleText)}}</h3>
        <p class="muted">${{escapeHtml(description)}}</p>
        <div class="example-strip">${{cards || '<span class="muted">No examples available.</span>'}}</div>
      </section>`;
    }}

    function correlationPartnerHtml(label, partner) {{
      if (!partner) {{
        return `<div class="correlation-item"><span>${{escapeHtml(label)}}</span><p class="muted">No partner available.</p></div>`;
      }}
      return `<div class="correlation-item">
        <span>${{escapeHtml(label)}}</span>
        <button type="button" data-explorer-partner="${{escapeHtml(partner.feature_id)}}">${{escapeHtml(partner.label)}}</button>
        <b>rho ${{formatSigned(partner.correlation)}} · ${{escapeHtml(bandLabel(partner.band))}}</b>
        <p class="muted">${{escapeHtml(partner.group_title || "Image feature")}} · N=${{escapeHtml(partner.pair_count)}}</p>
      </div>`;
    }}

    function openFeatureInExplorer(featureId) {{
      explorerState.group = "all";
      explorerState.search = "";
      explorerState.selectedFeatureId = featureId;
      document.getElementById("featureExplorerSearch").value = "";
      activateView("featureExplorer");
    }}

    function bandLabel(band) {{
      if (band === "high") return "High";
      if (band === "moderate") return "Moderate";
      return "Low";
    }}

    function render() {{
      if (state.variant === "image" && selectedFeatureIds().length === 0) {{
        renderNoFeatureSelection();
        return;
      }}
      const projection = getProjection();
      const labels = projection.labels;
      const coords = projection.coords;
      const filtered = dashboard.records.map((record, index) => ({{record, index}})).filter(item => passesFilters(item.record));
      const customData = filtered.map(item => [item.record.icon_id]);
      const plotPoints = filtered.map(item => [coords[item.index][0], coords[item.index][1]]);
      const ranges = plotRanges(plotPoints);

      Plotly.react("scatter", [{{
        x: filtered.map(item => coords[item.index][0]),
        y: filtered.map(item => coords[item.index][1]),
        mode: "markers",
        type: "scatter",
        marker: interactionMarker(),
        customdata: customData,
        hoverinfo: "none"
      }}], {{
        margin: {{l: 42, r: 14, t: 16, b: 42}},
        xaxis: {{title: "PCA 1", zeroline: false, range: ranges.x}},
        yaxis: {{title: "PCA 2", zeroline: false, range: ranges.y}},
        images: plotImages(filtered, coords, ranges),
        showlegend: false
      }}, {{responsive: true}});

      document.getElementById("scatter").on("plotly_click", event => {{
        selectedIconId = event.points[0].customdata[0];
        renderDetail(labels);
      }});
      document.getElementById("scatter").on("plotly_hover", event => {{
        const point = event.points[0];
        const iconId = point.customdata[0];
        const record = dashboard.records.find(item => item.icon_id === iconId);
        if (record) renderHoverPreview(record, labels[dashboard.records.indexOf(record)], event.event);
      }});
      document.getElementById("scatter").on("plotly_unhover", hideHoverPreview);
      renderDetail(labels);
      renderClusterSummary(labels, filtered);
    }}

    function renderNoFeatureSelection() {{
      hideHoverPreview();
      selectedIconId = null;
      Plotly.react("scatter", [], {{
        margin: {{l: 42, r: 14, t: 16, b: 42}},
        xaxis: {{title: "PCA 1", zeroline: false, visible: false}},
        yaxis: {{title: "PCA 2", zeroline: false, visible: false}},
        annotations: [{{
          text: "Select one or more image features to compute PCA and clustering.",
          xref: "paper",
          yref: "paper",
          x: 0.5,
          y: 0.5,
          showarrow: false,
          font: {{size: 16, color: "#5d6675"}}
        }}],
        showlegend: false
      }}, {{responsive: true}});
      document.getElementById("iconDetail").innerHTML =
        '<span class="muted">Select one or more image features, then click a point to inspect an icon.</span>';
      document.getElementById("clusterSummary").innerHTML =
        '<p class="muted">No feature-based clusters yet. Select features from the sidebar or use a preset.</p>';
    }}

    function getProjection() {{
      if (state.variant !== "image") {{
        return {{
          coords: dashboard.clusters[state.variant].pca,
          labels: dashboard.clusters[state.variant][state.method][state.k].labels
        }};
      }}
      const features = selectedFeatureIds();
      const key = `${{state.method}}|${{state.k}}|${{features.join(",")}}`;
      if (computedCache.has(key)) return computedCache.get(key);
      const matrix = standardize(dashboard.records.map(record => features.map(feature => Number(record.image_features[feature] || 0))));
      const coords = pca2d(matrix);
      const labels = state.method === "hierarchical" ? hierarchicalLabels(matrix, Number(state.k)) : kmeansLabels(matrix, Number(state.k));
      const projection = {{coords, labels}};
      computedCache.set(key, projection);
      return projection;
    }}

    function passesFilters(record) {{
      if (state.setFilter.size && !state.setFilter.has(record.set_name)) return false;
      return true;
    }}

    function clearSelectFilter(selectId, stateKey) {{
      Array.from(document.getElementById(selectId).options).forEach(option => option.selected = false);
      state[stateKey] = new Set();
      renderFilterPills();
      render();
    }}

    function resetFilters() {{
      clearSelectFilter("setFilter", "setFilter");
    }}

    function installToggleMultiSelect(selectId, stateKey) {{
      const select = document.getElementById(selectId);
      select.addEventListener("mousedown", event => {{
        if (event.target.tagName !== "OPTION") return;
        event.preventDefault();
        event.target.selected = !event.target.selected;
        state[stateKey] = new Set(Array.from(select.selectedOptions).map(option => option.value));
        renderFilterPills();
        render();
      }});
    }}

    function removeFilterValue(selectId, stateKey, value) {{
      const select = document.getElementById(selectId);
      Array.from(select.options).forEach(option => {{
        if (option.value === value) option.selected = false;
      }});
      state[stateKey].delete(value);
      renderFilterPills();
      render();
    }}

    function renderFilterPills() {{
      renderPillGroup("setFilterPills", "setFilter", "setFilter");
    }}

    function renderPillGroup(containerId, selectId, stateKey) {{
      const container = document.getElementById(containerId);
      const values = Array.from(state[stateKey]).sort();
      if (!values.length) {{
        container.innerHTML = '<span class="muted">All</span>';
        return;
      }}
      container.innerHTML = values.map(value => `
        <span class="filter-pill">
          <span>${{escapeHtml(value)}}</span>
          <button type="button" aria-label="Remove ${{escapeHtml(value)}}" data-value="${{escapeHtml(value)}}">x</button>
        </span>`).join("");
      container.querySelectorAll("button").forEach(button => {{
        button.addEventListener("click", () => removeFilterValue(selectId, stateKey, button.dataset.value));
      }});
    }}

    function interactionMarker() {{
      return {{
        size: 30,
        color: "rgba(24,32,47,0.01)",
        line: {{width: 0}},
        opacity: 0.01
      }};
    }}

    function plotRanges(points) {{
      if (!points.length) return {{x: [-1, 1], y: [-1, 1], spanX: 2, spanY: 2}};
      const xs = points.map(point => point[0]);
      const ys = points.map(point => point[1]);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      const spanX = Math.max(maxX - minX, 1);
      const spanY = Math.max(maxY - minY, 1);
      const padX = spanX * 0.12;
      const padY = spanY * 0.12;
      return {{
        x: [minX - padX, maxX + padX],
        y: [minY - padY, maxY + padY],
        spanX,
        spanY
      }};
    }}

    function plotImages(filtered, coords, ranges) {{
      const sizeX = ranges.spanX * 0.055;
      const sizeY = ranges.spanY * 0.055;
      return filtered.map(item => ({{
        source: item.record.normalized_path,
        xref: "x",
        yref: "y",
        x: coords[item.index][0],
        y: coords[item.index][1],
        sizex: sizeX,
        sizey: sizeY,
        xanchor: "center",
        yanchor: "middle",
        sizing: "contain",
        layer: "above",
        opacity: 0.96
      }}));
    }}

    function renderHoverPreview(record, cluster, event) {{
      const preview = document.getElementById("hoverPreview");
      const features = groupedFeatureHtml(record, selectedFeatureIds(), false, 10);
      preview.innerHTML = `
        <div class="hover-grid">
          <img src="${{record.normalized_path}}" alt="">
          <div class="hover-meta">
            <b>${{escapeHtml(record.label)}}</b><br>
            ${{escapeHtml(record.set_name)}}<br>
            <b>Cluster: ${{cluster}}</b>
          </div>
        </div>
        <div class="hover-features">${{features}}</div>`;
      preview.style.display = "block";
      placeHoverPreview(event);
    }}

    function placeHoverPreview(event) {{
      const preview = document.getElementById("hoverPreview");
      if (!preview || !event) return;
      const margin = 8;
      const offset = 14;
      const width = preview.offsetWidth || 360;
      const height = preview.offsetHeight || 180;
      let left = event.clientX + offset;
      let top = event.clientY + offset;
      if (left + width + margin > window.innerWidth) left = event.clientX - width - offset;
      if (top + height + margin > window.innerHeight) top = event.clientY - height - offset;
      left = Math.min(Math.max(margin, left), Math.max(margin, window.innerWidth - width - margin));
      top = Math.min(Math.max(margin, top), Math.max(margin, window.innerHeight - height - margin));
      preview.style.left = `${{left}}px`;
      preview.style.top = `${{top}}px`;
    }}

    function hideHoverPreview() {{
      document.getElementById("hoverPreview").style.display = "none";
    }}

    function renderDetail(labels) {{
      const detail = document.getElementById("iconDetail");
      const record = dashboard.records.find(r => r.icon_id === selectedIconId);
      if (!record) return;
      const index = dashboard.records.indexOf(record);
      const featureGroups = groupedFeatureHtml(record, visibleFeatureIds(), true, null);
      const mcdougallRows = Object.entries(record.mcdougall || {{}})
        .filter(([, value]) => value !== "")
        .map(([key, value]) => `<span class="pill">${{title(key)}}: ${{escapeHtml(String(value))}}</span>`).join("");
      detail.innerHTML = `
        <img class="detail-img" src="${{record.normalized_path}}" alt="">
        <h3>${{escapeHtml(record.label)}}</h3>
        <p class="muted">${{escapeHtml(record.set_name)}}<br>Cluster: ${{labels[index]}}</p>
        ${{featureGroups}}
        <p>${{mcdougallRows}}</p>
        <p class="muted">${{escapeHtml(record.metadata_tokens).slice(0, 300)}}</p>`;
    }}

    function renderClusterSummary(labels, filtered) {{
      const container = document.getElementById("clusterSummary");
      const byCluster = new Map();
      filtered.forEach(item => {{
        const cluster = labels[item.index];
        if (!byCluster.has(cluster)) byCluster.set(cluster, []);
        byCluster.get(cluster).push(item);
      }});
      container.innerHTML = Array.from(byCluster.entries()).sort((a,b) => a[0]-b[0]).map(([cluster, items]) => {{
        const topSets = topCounts(items.map(item => item.record.set_name), 2).join(", ");
        const explanation = clusterExplanation(labels, cluster, selectedFeatureIds());
        const icons = items.slice(0, 12).map(item => `
          <div class="rep-icon">
            <img src="${{item.record.normalized_path}}" title="${{escapeHtml(item.record.label)}}" alt="">
            <span title="${{escapeHtml(item.record.label)}}">${{escapeHtml(item.record.label)}}</span>
          </div>`).join("");
        return `<details class="summary-cluster">
          <summary><b>${{methodLabel()}} cluster ${{cluster}}</b> <span class="muted">(${{items.length}} icons)</span><br>
            <span class="muted">Sets: ${{escapeHtml(topSets)}}</span></summary>
          <div class="summary-details">
            ${{explanation}}
            <div class="rep-icons">${{icons}}</div>
          </div>
        </details>`;
      }}).join("");
    }}

    function methodLabel() {{
      return state.method === "hierarchical" ? "Hierarchical" : "K-Means";
    }}

    function groupedFeatureHtml(record, featureIds, includeDescriptions=true, maxFeatures=null) {{
      const selected = new Set(featureIds);
      const featureLimit = maxFeatures === null ? featureIds.length : maxFeatures;
      let shown = 0;
      const html = visibleFeatureSections().map(section => {{
        const features = section.features.filter(feature => selected.has(feature.id));
        if (!features.length || shown >= featureLimit) return "";
        const visible = features.slice(0, Math.max(0, featureLimit - shown));
        shown += visible.length;
        const rows = visible.map(feature => `
          <tr>
            <td title="${{escapeHtml(feature.meaning)}}">${{escapeHtml(feature.label)}}</td>
            <td>${{formatFeatureValue(record.image_features[feature.id])}}</td>
          </tr>`).join("");
        const description = includeDescriptions ? `<p>${{escapeHtml(section.description)}}</p>` : "";
        const familyReading = includeDescriptions ? `
          <p class="family-reading"><b>Human perception:</b> ${{escapeHtml(section.perception || "This family describes a perceptual visual channel.")}}</p>
          <p class="family-reading"><b>Low:</b> ${{escapeHtml(section.low_value || "Lower values mean less of this family signal.")}}</p>
          <p class="family-reading"><b>High:</b> ${{escapeHtml(section.high_value || "Higher values mean more of this family signal.")}}</p>` : "";
        return `<div class="feature-group-detail">
          <h4>${{escapeHtml(section.title)}}</h4>
          ${{description}}
          ${{familyReading}}
          <table>${{rows}}</table>
        </div>`;
      }}).join("");
      const omitted = featureIds.length - shown;
      return html + (omitted > 0 ? `<p class="muted">${{omitted}} more selected features.</p>` : "");
    }}

    function featureSummaryLines(record, featureIds, maxFeatures) {{
      const selected = new Set(featureIds);
      const lines = [];
      for (const section of visibleFeatureSections()) {{
        for (const feature of section.features) {{
          if (!selected.has(feature.id)) continue;
          if (lines.length >= maxFeatures) {{
            lines.push(`${{featureIds.length - maxFeatures}} more selected features`);
            return lines;
          }}
          lines.push(`${{escapeHtml(feature.label)}}: ${{formatFeatureValue(record.image_features[feature.id])}}`);
        }}
      }}
      return lines;
    }}

    function clusterExplanation(labels, cluster, featureIds) {{
      if (!featureIds.length) return '<div class="summary-explain">No image features selected for cluster explanation.</div>';
      const features = featureIds;
      const matrix = standardizedImageMatrix(features);
      const members = labels.map((label, index) => label === cluster ? index : -1).filter(index => index >= 0);
      if (!members.length) return "";
      const featureIndex = new Map(features.map((feature, index) => [feature, index]));
      const sectionScores = visibleFeatureSections().map(section => {{
        const entries = section.features
          .filter(feature => featureIndex.has(feature.id))
          .map(feature => {{
            const column = featureIndex.get(feature.id);
            const mean = members.reduce((sum, index) => sum + matrix[index][column], 0) / members.length;
            return {{feature, score: Math.abs(mean)}};
          }});
        const score = entries.length ? entries.reduce((sum, entry) => sum + entry.score, 0) / entries.length : 0;
        return {{section, score, entries: entries.sort((a,b) => b.score - a.score)}};
      }}).filter(item => item.entries.length).sort((a,b) => b.score - a.score);
      const groups = sectionScores.slice(0, 2).map(item => `${{item.section.title.replace(" Features", "")}} (${{item.score.toFixed(2)}}z)`).join(", ");
      const topFeatures = sectionScores.flatMap(item => item.entries.slice(0, 3))
        .sort((a,b) => b.score - a.score)
        .slice(0, 3)
        .map(item => `${{item.feature.label}} (${{item.score.toFixed(2)}}z)`)
        .join(", ");
      return `<div class="summary-explain">Distinctive groups: ${{escapeHtml(groups)}}<br>Top features: ${{escapeHtml(topFeatures)}}</div>`;
    }}

    function standardizedImageMatrix(features) {{
      return standardize(dashboard.records.map(record => features.map(feature => Number(record.image_features[feature] || 0))));
    }}

    function formatFeatureValue(value) {{
      if (typeof value === "number") {{
        const rounded = Math.round(value * 10000) / 10000;
        return escapeHtml(String(rounded));
      }}
      return escapeHtml(String(value ?? ""));
    }}

    function formatNumber(value) {{
      const number = Number(value);
      if (!Number.isFinite(number)) return "";
      return escapeHtml(number.toFixed(3));
    }}

    function formatSigned(value) {{
      const number = Number(value);
      if (!Number.isFinite(number)) return "";
      const formatted = `${{number >= 0 ? "+" : ""}}${{number.toFixed(3)}}`;
      return escapeHtml(formatted);
    }}

    function fillColorSelect(id, selected) {{
      const select = document.getElementById(id);
      select.innerHTML = "";
      appendOption(select, "cluster", "Cluster", selected);
      appendOption(select, "set_name", "Icon set", selected);
      visibleFeatureSections().forEach(section => {{
        const group = document.createElement("optgroup");
        group.label = section.title;
        section.features.forEach(feature => appendOption(group, feature.id, feature.label, selected));
        select.appendChild(group);
      }});
    }}

    function appendOption(parent, value, label, selected) {{
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      option.selected = value === selected;
      parent.appendChild(option);
    }}

    function fillSelect(id, options, selected, multiple=false) {{
      const select = document.getElementById(id);
      select.innerHTML = "";
      select.multiple = multiple;
      options.forEach(([value, label]) => {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        option.selected = value === selected;
        select.appendChild(option);
      }});
    }}
    function unique(values) {{ return Array.from(new Set(values.filter(v => v !== undefined && v !== null && v !== ""))); }}
    function topCounts(values, limit) {{
      const counts = new Map();
      values.forEach(v => counts.set(v, (counts.get(v) || 0) + 1));
      return Array.from(counts.entries()).sort((a,b) => b[1]-a[1]).slice(0, limit).map(([v,n]) => `${{v}} (${{n}})`);
    }}
    function title(value) {{ return String(value).replaceAll("_", " ").replace(/\\b\\w/g, c => c.toUpperCase()); }}
    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#039;"}}[c]));
    }}
    function standardize(matrix) {{
      const rows = matrix.length;
      const cols = matrix[0].length;
      const means = Array(cols).fill(0);
      const stds = Array(cols).fill(0);
      matrix.forEach(row => row.forEach((value, col) => means[col] += value / rows));
      matrix.forEach(row => row.forEach((value, col) => stds[col] += Math.pow(value - means[col], 2) / rows));
      for (let col = 0; col < cols; col++) stds[col] = Math.sqrt(stds[col]) || 1;
      return matrix.map(row => row.map((value, col) => (value - means[col]) / stds[col]));
    }}
    function pca2d(matrix) {{
      const rows = matrix.length;
      const cols = matrix[0].length;
      if (cols === 1) return matrix.map(row => [row[0], 0]);
      const cov = Array.from({{length: cols}}, () => Array(cols).fill(0));
      for (const row of matrix) {{
        for (let i = 0; i < cols; i++) {{
          for (let j = i; j < cols; j++) cov[i][j] += row[i] * row[j] / Math.max(1, rows - 1);
        }}
      }}
      for (let i = 0; i < cols; i++) for (let j = 0; j < i; j++) cov[i][j] = cov[j][i];
      const eig = jacobiEigen(cov);
      const order = eig.values.map((value, index) => [value, index]).sort((a,b) => b[0] - a[0]).slice(0, 2).map(item => item[1]);
      return matrix.map(row => order.map(index => row.reduce((sum, value, col) => sum + value * eig.vectors[col][index], 0)));
    }}
    function jacobiEigen(input) {{
      const n = input.length;
      const a = input.map(row => row.slice());
      const v = Array.from({{length: n}}, (_, i) => Array.from({{length: n}}, (_, j) => i === j ? 1 : 0));
      for (let iter = 0; iter < 80; iter++) {{
        let p = 0, q = 1, max = 0;
        for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {{
          const value = Math.abs(a[i][j]);
          if (value > max) {{ max = value; p = i; q = j; }}
        }}
        if (max < 1e-10) break;
        const theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
        const c = 1 / Math.sqrt(t * t + 1);
        const s = t * c;
        const app = a[p][p], aqq = a[q][q], apq = a[p][q];
        a[p][p] = app - t * apq;
        a[q][q] = aqq + t * apq;
        a[p][q] = 0; a[q][p] = 0;
        for (let r = 0; r < n; r++) if (r !== p && r !== q) {{
          const arp = a[r][p], arq = a[r][q];
          a[r][p] = a[p][r] = c * arp - s * arq;
          a[r][q] = a[q][r] = s * arp + c * arq;
        }}
        for (let r = 0; r < n; r++) {{
          const vrp = v[r][p], vrq = v[r][q];
          v[r][p] = c * vrp - s * vrq;
          v[r][q] = s * vrp + c * vrq;
        }}
      }}
      return {{values: a.map((row, i) => row[i]), vectors: v}};
    }}
    function kmeansLabels(matrix, k) {{
      const centers = matrix.slice(0, k).map(row => row.slice());
      let labels = Array(matrix.length).fill(0);
      for (let iter = 0; iter < 60; iter++) {{
        let changed = false;
        labels = matrix.map((row, rowIndex) => {{
          let best = 0, bestDistance = Infinity;
          centers.forEach((center, index) => {{
            const distance = squaredDistance(row, center);
            if (distance < bestDistance) {{ best = index; bestDistance = distance; }}
          }});
          if (best !== labels[rowIndex]) changed = true;
          return best;
        }});
        const sums = Array.from({{length: k}}, () => Array(matrix[0].length).fill(0));
        const counts = Array(k).fill(0);
        matrix.forEach((row, rowIndex) => {{
          counts[labels[rowIndex]]++;
          row.forEach((value, col) => sums[labels[rowIndex]][col] += value);
        }});
        for (let cluster = 0; cluster < k; cluster++) {{
          if (counts[cluster]) centers[cluster] = sums[cluster].map(value => value / counts[cluster]);
        }}
        if (!changed) break;
      }}
      return labels;
    }}
    function hierarchicalLabels(matrix, k) {{
      const edges = [];
      for (let i = 0; i < matrix.length; i++) {{
        for (let j = i + 1; j < matrix.length; j++) edges.push([Math.sqrt(squaredDistance(matrix[i], matrix[j])), i, j]);
      }}
      edges.sort((a,b) => a[0] - b[0]);
      const parent = Array.from({{length: matrix.length}}, (_, i) => i);
      const size = Array(matrix.length).fill(1);
      const mst = [];
      function find(x) {{ while (parent[x] !== x) {{ parent[x] = parent[parent[x]]; x = parent[x]; }} return x; }}
      for (const [, left, right] of edges) {{
        let a = find(left), b = find(right);
        if (a === b) continue;
        if (size[a] < size[b]) [a,b] = [b,a];
        parent[b] = a; size[a] += size[b]; mst.push([left, right]);
        if (mst.length === matrix.length - 1) break;
      }}
      return labelsFromMst(matrix.length, mst.slice(0, Math.max(0, matrix.length - k)));
    }}
    function labelsFromMst(count, edges) {{
      const parent = Array.from({{length: count}}, (_, i) => i);
      const size = Array(count).fill(1);
      function find(x) {{ while (parent[x] !== x) {{ parent[x] = parent[parent[x]]; x = parent[x]; }} return x; }}
      function union(left, right) {{
        let a = find(left), b = find(right);
        if (a === b) return;
        if (size[a] < size[b]) [a,b] = [b,a];
        parent[b] = a; size[a] += size[b];
      }}
      edges.forEach(([left, right]) => union(left, right));
      const map = new Map();
      return parent.map((_, index) => {{
        const root = find(index);
        if (!map.has(root)) map.set(root, map.size);
        return map.get(root);
      }});
    }}
    function squaredDistance(a, b) {{ return a.reduce((sum, value, index) => sum + Math.pow(value - b[index], 2), 0); }}
  </script>
</body>
</html>
"""
    (OUTPUT_DIR / "index.html").write_text(index, encoding="utf-8")


def write_metadata_report(rows: list[dict], failures: list[dict] | None = None) -> None:
    report = {
        "rows": len(rows),
        "per_set_sample_size": PER_SET_SAMPLE_SIZE,
        "random_seed": RANDOM_SEED,
        "set_counts": dict(sorted(Counter(row["set_id"] for row in rows).items())),
        "missing_metadata_tokens": sum(1 for row in rows if not row.get("metadata_tokens")),
        "missing_normalized_paths": sum(1 for row in rows if row.get("normalized_path_exists") != "true"),
        "expected_outputs": [
            "sample_metadata.csv",
            "features_image.csv",
            "features_metadata.csv",
            "features_combined.csv",
            "clusters_kmeans.csv",
            "clusters_hierarchical.csv",
            "cluster_summary.csv",
            "dashboard_data.json",
            "index.html",
        ],
    }
    (OUTPUT_DIR / "analysis_dashboard_metadata_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_plotly_placeholder_if_missing() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if PLOTLY_ASSET.exists():
        return
    PLOTLY_ASSET.write_text(
        "throw new Error('Missing Plotly asset. Replace assets/plotly.min.js with a local Plotly.js bundle.');\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = read_csv(DATASET_PATH)
    sampled_source_rows = sample_random_rows_per_set(all_rows, PER_SET_SAMPLE_SIZE, RANDOM_SEED)
    metadata_rows = enrich_metadata_rows(sampled_source_rows)
    write_rows(OUTPUT_DIR / "sample_metadata.csv", metadata_rows)
    write_metadata_report(metadata_rows)

    feature_rows = extract_features(sampled_source_rows)
    feature_by_id = {row["icon_id"]: row for row in feature_rows}
    metadata_rows = [row for row in metadata_rows if row["icon_id"] in feature_by_id]

    matrices = feature_matrices(metadata_rows, feature_by_id)
    write_feature_tables(metadata_rows, feature_by_id, matrices)

    clusters, assignment_rows, summary_rows = build_clusters(metadata_rows, matrices)
    write_rows(OUTPUT_DIR / "cluster_assignments.csv", assignment_rows)
    write_rows(OUTPUT_DIR / "clusters_kmeans.csv", [row for row in assignment_rows if row["method"] == "kmeans"])
    write_rows(
        OUTPUT_DIR / "clusters_hierarchical.csv",
        [row for row in assignment_rows if row["method"] == "hierarchical"],
    )
    write_rows(OUTPUT_DIR / "cluster_summary.csv", summary_rows)
    write_dashboard_data(metadata_rows, feature_by_id, matrices, clusters)
    write_index_html()
    write_plotly_placeholder_if_missing()
    print(f"Wrote analysis dashboard outputs to {OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
