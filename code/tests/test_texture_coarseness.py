from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from extract_icon_features import tamura_coarseness


class TamuraCoarsenessTests(unittest.TestCase):
    def test_empty_foreground_returns_zero(self) -> None:
        gray = np.ones((32, 32), dtype=np.float32)
        foreground = np.zeros_like(gray, dtype=bool)

        self.assertEqual(tamura_coarseness(gray, foreground), 0.0)

    def test_uniform_effective_picture_uses_largest_scale(self) -> None:
        gray = np.full((64, 64), 0.25, dtype=np.float32)
        foreground = np.ones_like(gray, dtype=bool)

        self.assertAlmostEqual(tamura_coarseness(gray, foreground), 1.0, places=6)

    def test_coarse_checkerboard_scores_above_fine_checkerboard(self) -> None:
        y, x = np.indices((128, 128))
        fine = ((x + y) % 2).astype(np.float32)
        coarse = ((x // 32 + y // 32) % 2).astype(np.float32)
        foreground = np.ones_like(fine, dtype=bool)

        fine_score = tamura_coarseness(fine, foreground)
        coarse_score = tamura_coarseness(coarse, foreground)

        self.assertGreater(coarse_score, fine_score)

    def test_exterior_whitespace_does_not_change_effective_picture(self) -> None:
        y, x = np.indices((64, 64))
        pattern = ((x // 8 + y // 8) % 2).astype(np.float32)
        foreground = np.ones_like(pattern, dtype=bool)
        direct_score = tamura_coarseness(pattern, foreground)

        padded_gray = np.ones((128, 128), dtype=np.float32)
        padded_foreground = np.zeros_like(padded_gray, dtype=bool)
        padded_gray[32:96, 32:96] = pattern
        padded_foreground[32:96, 32:96] = True

        self.assertAlmostEqual(
            tamura_coarseness(padded_gray, padded_foreground),
            direct_score,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
