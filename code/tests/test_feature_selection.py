from __future__ import annotations

import sys
import unittest
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from thesis_pipeline.dashboard.feature_selection import select_strong_family_features


class FeatureSelectionTests(unittest.TestCase):
    def test_selects_strongest_candidate_then_skips_directly_redundant_second(self) -> None:
        rows = [
            {"feature_id": "strong", "group": "a", "label": "Strong", "std": 1.0},
            {"feature_id": "duplicate", "group": "a", "label": "Duplicate", "std": 1.0},
            {"feature_id": "complement", "group": "a", "label": "Complement", "std": 1.0},
        ]
        pairs = [
            {"feature_a": "strong", "feature_b": "duplicate", "correlation": 0.91, "abs_correlation": 0.91},
            {"feature_a": "strong", "feature_b": "complement", "correlation": -0.20, "abs_correlation": 0.20},
            {"feature_a": "duplicate", "feature_b": "complement", "correlation": 0.10, "abs_correlation": 0.10},
        ]
        selected = select_strong_family_features(
            rows,
            pairs,
            ["a"],
            {"a": ["strong", "duplicate", "complement"]},
            per_family=2,
            max_abs_spearman=0.70,
        )
        self.assertEqual([row["feature_id"] for row in selected], ["strong", "complement"])
        self.assertEqual([row["selection_rank_in_family"] for row in selected], [1, 2])
        self.assertEqual([row["strength_priority_rank"] for row in selected], [1, 3])
        self.assertEqual([row["pair_abs_correlation"] for row in selected], [0.20, 0.20])
        self.assertEqual([row["companion_feature_id"] for row in selected], ["complement", "strong"])

    def test_constant_priority_candidate_is_not_selected(self) -> None:
        rows = [
            {"feature_id": "flat", "group": "a", "label": "Flat", "std": 0.0},
            {"feature_id": "useful", "group": "a", "label": "Useful", "std": 0.5},
        ]
        selected = select_strong_family_features(
            rows,
            [],
            ["a"],
            {"a": ["flat", "useful"]},
            per_family=1,
        )
        self.assertEqual([row["feature_id"] for row in selected], ["useful"])

    def test_does_not_claim_a_second_feature_without_pairwise_evidence(self) -> None:
        rows = [
            {"feature_id": "first", "group": "a", "label": "First", "std": 1.0},
            {"feature_id": "second", "group": "a", "label": "Second", "std": 1.0},
        ]
        selected = select_strong_family_features(
            rows,
            [],
            ["a"],
            {"a": ["first", "second"]},
            per_family=2,
        )
        self.assertEqual([row["feature_id"] for row in selected], ["first"])
        self.assertIsNone(selected[0]["pair_abs_correlation"])


if __name__ == "__main__":
    unittest.main()
