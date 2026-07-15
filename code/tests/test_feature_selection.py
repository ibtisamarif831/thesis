from __future__ import annotations

import sys
import unittest
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from thesis_pipeline.dashboard.feature_selection import select_unique_family_features


class FeatureSelectionTests(unittest.TestCase):
    def test_selects_two_lowest_redundancy_features_per_family(self) -> None:
        rows = [
            {"feature_id": "a1", "group": "a", "label": "A1", "std": 1.0, "strongest_abs_correlation": 0.20},
            {"feature_id": "a2", "group": "a", "label": "A2", "std": 1.0, "strongest_abs_correlation": 0.10},
            {"feature_id": "a3", "group": "a", "label": "A3", "std": 1.0, "strongest_abs_correlation": 0.80},
            {"feature_id": "b1", "group": "b", "label": "B1", "std": 1.0, "strongest_abs_correlation": 0.30},
            {"feature_id": "b2", "group": "b", "label": "B2", "std": 1.0, "strongest_abs_correlation": 0.40},
        ]
        selected = select_unique_family_features(rows, ["a", "b"], per_family=2)
        self.assertEqual([row["feature_id"] for row in selected], ["a2", "a1", "b1", "b2"])
        self.assertEqual([row["uniqueness_rank_in_family"] for row in selected], [1, 2, 1, 2])

    def test_constant_features_are_deprioritized(self) -> None:
        rows = [
            {"feature_id": "flat", "group": "a", "label": "Flat", "std": 0.0, "strongest_abs_correlation": 0.0},
            {"feature_id": "useful", "group": "a", "label": "Useful", "std": 0.5, "strongest_abs_correlation": 0.4},
        ]
        selected = select_unique_family_features(rows, ["a"], per_family=1)
        self.assertEqual(selected[0]["feature_id"], "useful")


if __name__ == "__main__":
    unittest.main()
