from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import extract_icon_features as features


def save_rgba(path: Path, rgb: np.ndarray, alpha: np.ndarray | None = None) -> None:
    if alpha is None:
        alpha = np.full(rgb.shape[:2], 255, dtype=np.uint8)
    Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA").save(path)


def test_foreground_masks_transparent_white_black_and_nonuniform(tmp_path: Path) -> None:
    transparent_rgb = np.zeros((32, 32, 3), dtype=np.uint8)
    transparent_alpha = np.zeros((32, 32), dtype=np.uint8)
    transparent_alpha[8:24, 8:24] = 255
    transparent = tmp_path / "transparent.png"
    save_rgba(transparent, transparent_rgb, transparent_alpha)
    transparent_context = features.load_image(transparent, 245)
    assert transparent_context.mask_mode == "alpha"
    assert transparent_context.foreground.sum() == 16 * 16

    for name, background, foreground_color in (
        ("white", 255, 0),
        ("black", 0, 255),
    ):
        rgb = np.full((32, 32, 3), background, dtype=np.uint8)
        rgb[8:24, 8:24] = foreground_color
        path = tmp_path / f"{name}.png"
        save_rgba(path, rgb)
        context = features.load_image(path, 245)
        assert context.mask_mode == "opaque_border_lab"
        assert context.foreground.sum() == 16 * 16
        assert not context.mask_is_uncertain

    nonuniform = np.zeros((32, 32, 3), dtype=np.uint8)
    nonuniform[:, :, 0] = np.linspace(0, 255, 32, dtype=np.uint8)[None, :]
    path = tmp_path / "nonuniform.png"
    save_rgba(path, nonuniform)
    assert features.load_image(path, 245).mask_is_uncertain


def test_enclosure_fill_orientation_symmetry_and_texture() -> None:
    filled = np.zeros((64, 64), dtype=bool)
    filled[12:52, 12:52] = True
    outline = np.zeros_like(filled)
    outline[12:52, 12:15] = outline[12:52, 49:52] = True
    outline[12:15, 12:52] = outline[49:52, 12:52] = True
    open_shape = outline.copy()
    open_shape[12:15, 28:40] = False

    assert features.enclosure_score(filled) > features.enclosure_score(open_shape)
    assert features.solid_fill_ratio(filled) > features.solid_fill_ratio(outline)

    horizontal = np.zeros((64, 64), dtype=bool)
    horizontal[29:35, 8:56] = True
    vertical = horizontal.T
    horizontal_angle, horizontal_confidence = features.principal_axis_orientation_with_confidence(horizontal)
    vertical_angle, vertical_confidence = features.principal_axis_orientation_with_confidence(vertical)
    assert min(horizontal_angle, 180.0 - horizontal_angle) < 2.0
    assert abs(vertical_angle - 90.0) < 2.0
    assert horizontal_confidence > 0.8 and vertical_confidence > 0.8
    _, square_confidence = features.principal_axis_orientation_with_confidence(filled)
    assert square_confidence < features.ORIENTATION_CONFIDENCE_THRESHOLD

    asymmetric = filled.copy()
    asymmetric[20:30, 45:60] = True
    assert features.tolerant_symmetry_score(filled) > features.tolerant_symmetry_score(asymmetric)

    flat_gray = np.full((64, 64), 0.4, dtype=np.float32)
    textured_gray = flat_gray.copy()
    yy, xx = np.indices((64, 64))
    textured_gray[(yy + xx) % 2 == 0] = 0.1
    textured_gray[(yy + xx) % 2 == 1] = 0.9
    assert features.local_texture_variation(textured_gray, filled) > features.local_texture_variation(flat_gray, filled)


def test_strict_red_rejects_borders_and_multicolor_icons() -> None:
    foreground = np.ones((20, 20), dtype=bool)
    red = np.zeros((20, 20, 3), dtype=np.float32)
    red[:, :, 0] = 1.0
    ratio, flag = features.strict_red_stats(red, foreground)
    assert ratio == 1.0 and flag == 1.0

    red_border = np.zeros_like(red)
    red_border[[0, -1], :, 0] = 1.0
    red_border[:, [0, -1], 0] = 1.0
    ratio, flag = features.strict_red_stats(red_border, foreground)
    assert ratio < 0.9 and flag == 0.0

    multicolor = red.copy()
    multicolor[:, :5] = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    ratio, flag = features.strict_red_stats(multicolor, foreground)
    assert ratio == 0.75 and flag == 0.0
